"""单文件实验三：BFGS、DFP 和 PRP+ 非线性共轭梯度法。

默认打印迭代进度与每种方法的最终结果；--quiet 仅保存文件。
实际函数 f4、f5 及梯度/Hessian 写在文件顶部；算法在后面。
"""

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


# ==============================================================================
# 1. 实际问题的目标函数与导数  修改题目先看这里
# ==============================================================================

# 目标函数不只包含多项式，还包含 arctan 与 log。
def f4(x):
    """实验三问题 IV 的二维目标函数。"""
    a, b = x
    return a ** 4 / 12 + a * a / 2 + b * math.atan(b) - math.log1p(b * b) / 2

# 拟牛顿法和共轭梯度法使用一阶梯度，不要求显式求二阶导数。
def g4(x):
    """问题 IV 的解析梯度。"""
    return np.array([x[0] ** 3 / 3 + x[0], math.atan(x[1])])

# Hessian 只用于验证梯度推导，不直接参加拟牛顿迭代。
def h4(x):
    """问题 IV 的解析 Hessian（用于理解和独立验证，并非 BFGS 必需输入）。"""
    return np.diag([1 + x[0] ** 2, 1 / (1 + x[1] ** 2)])

# 三维问题的目标极小点位于 (1, 1, 1)。
def f5(x):
    """实验三问题 V 的三维目标函数。"""
    a, b, c = x
    return 5 * (b * b - c) ** 2 + 4 * (a * a - b) ** 2 + 3 * (a - 1) ** 2

def g5(x):
    """问题 V 的解析梯度。"""
    a, b, c = x
    return np.array([
        16 * a * (a * a - b) + 6 * (a - 1),
        20 * b * (b * b - c) - 8 * (a * a - b),
        -10 * (b * b - c),
    ])

def h5(x):
    """问题 V 的解析 Hessian（用于验证）。"""
    a, b, c = x
    return np.array([
        [48 * a * a - 16 * b + 6, -16 * a, 0],
        [-16 * a, 60 * b * b - 20 * c + 8, -20 * b],
        [0, -20 * b, 10.0],
    ])


# ==============================================================================
# 公共：输出格式化工具
# ==============================================================================


def fmt_vector(values, precision=5):
    """统一格式化迭代点或搜索方向，避免 NumPy 的浮点表示占满控制台。"""
    arr = np.asarray(values, dtype=float)
    return "[" + ", ".join(f"{value:.{precision}g}" for value in arr) + "]"


def print_progress(row, every=1000):
    """长迭代过程只打印前 3 次、整百/整千次，减少刷屏。"""
    k = row["k"]
    if k <= 3 or k % every == 0:
        alpha = row.get("alpha")
        alpha_text = f"  alpha={alpha:.3g}" if alpha is not None else ""
        print(
            f"    k={k:>6}  f={row['f']:.9g}  "
            f"||g||={row['grad_norm']:.3e}{alpha_text}",
            flush=True,
        )


def print_summary(result):
    """用统一格式概括目标函数值、迭代次数与最终状态。"""
    print(
        f"  -> 状态={result.get('status', 'completed')}；"
        f"迭代={result['iterations']}；"
        f"x={fmt_vector(result['x'])}；"
        f"f={result['f']:.10g}；"
        f"||g||={result.get('grad_norm', float('nan')):.3e}",
        flush=True,
    )


# 2. 算法实现
# ==============================================================================

# 只负责选步长，不负责更新 x；适用于最速下降法、拟牛顿法等。
def armijo(f, x, g, d, alpha0=1.0, c1=0.0001, rho=0.5, bounds=None):
    """Armijo 回溯线搜索：逐步缩小 alpha，直到目标函数有足够的下降量。

    f：目标函数；x：当前位置；g：当前位置的梯度；d：下降方向。
    c1：充分下降系数；rho：每次回溯后步长乘以 rho。
    返回满足 f(x+alpha*d) <= f(x)+c1*alpha*(g·d) 的 alpha。
    """
    slope = float(g @ d)
    if slope >= 0:
        raise ValueError('direction is not descending')
    alpha = alpha0
    fx = f(x)
    for _ in range(100):
        trial = x + alpha * d
        if bounds is None or np.all((trial >= bounds[0]) & (trial <= bounds[1])):
            val = f(trial)
            if np.isfinite(val) and val <= fx + c1 * alpha * slope:
                return alpha
        alpha *= rho
    raise RuntimeError('Armijo line search failed')

# 统一维护 history，便于输出过程、生成收敛曲线、后续验收分析。
def record(k, x, f, g, previous=None, **extra):
    """记录单次迭代：位置、函数值、前后函数值变化量以及梯度范数。"""
    # 将函数值、梯度范数转换成普通浮点数，方便直接写入 JSON 文件。
    fx = float(f(x))
    gradient_norm = float(np.linalg.norm(g(x)))
    delta_f = None if previous is None else abs(fx - previous)

    return {
        "k": k,                    # 从 0 开始的迭代编号
        "x": np.asarray(x).tolist(),
        "f": fx,                    # 当前目标函数值
        "delta_f": delta_f,        # 目标函数相邻两次变化量
        "grad_norm": gradient_norm, # ||∇f(x)||，常用停止判据
        **extra,                   # 如 alpha（步长）等算法专用字段
    }

# 核心迭代器：计算梯度 → 选择搜索方向 → 求步长 → 更新位置 → 判断收敛。
def optimize(f, g, x0, method='bfgs', tol=1e-06, max_iter=20000, bounds=None, progress=None):
    """实验三专用：BFGS / DFP 拟牛顿法与 PRP+ 非线性共轭梯度法。"""
    if method not in ('bfgs', 'dfp', 'prp'):
        raise ValueError('实验三只支持 bfgs/dfp/prp')
    x = np.array(x0, dtype=float)
    # H 近似 Hessian 的逆矩阵，初始取单位矩阵；每次通过 s、y 更新。
    H = np.eye(len(x))
    d = -g(x)
    hist = [record(0, x, f, g)]
    status = 'iteration_limit'
    for k in range(max_iter):
        gx = g(x)
        if np.linalg.norm(gx) <= tol:
            status = 'gradient_tolerance'
            break
        # 拟牛顿方向 d=-H*g；PRP+ 方向由上一步的 d 与 beta 递推。
        if method in ('bfgs', 'dfp'):
            d = -H @ gx
        # 若数值误差使方向不再下降，重启为最速下降方向并重置 H。
        if gx @ d >= -1e-12 * np.linalg.norm(gx) * max(np.linalg.norm(d), 1e-30):
            d = -gx
            H = np.eye(len(x))
        try:
            alpha = armijo(f, x, gx, d, bounds=bounds)
        except RuntimeError:
            status = 'line_search_failed'
            break
        xn = x + alpha * d
        if not np.all(np.isfinite(xn)):
            status = 'nonfinite'
            break
        gn = g(xn)
        # s = x_(k+1)-x_k, y = g_(k+1)-g_k 是拟牛顿更新的两个向量。
        s = xn - x
        y = gn - gx
        sy = float(s @ y)
        if method in ('bfgs', 'dfp') and sy > 1e-12 * np.linalg.norm(s) * np.linalg.norm(y):
            # BFGS、DFP 都直接更新 Hessian 的逆近似 H，避免每轮求逆。
            if method == 'bfgs':
                V = np.eye(len(x)) - np.outer(s, y) / sy
                H = V @ H @ V.T + np.outer(s, s) / sy
            else:
                Hy = H @ y
                yh = float(y @ Hy)
                if yh > 0:
                    H += np.outer(s, s) / sy - np.outer(Hy, Hy) / yh
            H = (H + H.T) / 2
        # PRP+：beta=max(0, g_(k+1)^T(g_(k+1)-g_k)/(g_k^T g_k))。
        # 这里每 n 步重启，且下一轮重新检查是否仍为下降方向。
        if method == 'prp':
            beta = max(0.0, float(gn @ y / (gx @ gx)))
            if (k + 1) % len(x) == 0:
                beta = 0.0
            d = -gn + beta * d
        old = hist[-1]['f']
        x = xn
        iteration = record(k + 1, x, f, g, old, alpha=alpha)
        hist.append(iteration)

        # 回调只负责显示信息，不修改位置 x 或更新公式。
        if progress is not None:
            progress(iteration)
    # 状态与完整 history 一并返回，方便后续对比各算法收敛情况。
    return {
        "method": method,
        "status": status,
        "x": x.tolist(),
        "f": float(f(x)),
        "grad_norm": float(np.linalg.norm(g(x))),
        "iterations": len(hist) - 1,
        "history": hist,
    }


# ==============================================================================
# 3. 运行实验与导出结果
# ==============================================================================

# 一行代表一次迭代，适合在 Excel 中观察数据变化。
def write_csv(path, rows):
    """导出迭代过程到 CSV：每行一次迭代，每列一个观测量。"""
    if not rows:
        return

    # 保留字段第一次出现的顺序，并且兼容不同迭代记录包含不同字段。
    columns = list(dict.fromkeys(key for row in rows for key in row))

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for row in rows:
            # 一维数组/字典不能直接用简单的 CSV 标量表示，先序列化。
            csv_row = {
                key: json.dumps(value, ensure_ascii=False)
                if isinstance(value, (list, dict))
                else value
                for key, value in row.items()
            }
            writer.writerow(csv_row)

# 实验总控：遍历题目与算法，保存过程记录，并打印简洁的运行摘要。
def run(out, verbose=True):
    """在二维问题 IV 和三维问题 V 上分别比较 BFGS、DFP、PRP+。"""
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.25,
    })
    data = {"exp3": {}}

    if verbose:
        print("\n========== 实验三：拟牛顿法与共轭梯度法 ==========", flush=True)
        print("提示：BFGS/DFP 更新逆 Hessian；PRP 使用 PRP+ 系数", flush=True)

    # 问题 IV 使用两个不同初始点，比较收敛过程。
    # 问题 V 在三维空间求解，适合观察 PRP+ 的重启机制。
    cases = [
        ("IV_a", f4, g4, [1.0, 0.7]),
        ("IV_b", f4, g4, [1.0, 2.0]),
        ("V", f5, g5, [0.0, 0.0, 0.0]),
    ]

    for label, f, g, x0 in cases:
        if verbose:
            print(f"\n[问题 {label}] 初始点={fmt_vector(x0)}", flush=True)
        for method in ["bfgs", "dfp", "prp"]:
            if verbose:
                print(f"  开始 {method.upper()}：", flush=True)
            r = optimize(
                f, g, x0, method, max_iter=20000,
                progress=(lambda row: print_progress(row, every=1000))
                         if verbose else None,
            )
            data["exp3"][f"{label}_{method}"] = r
            write_csv(out / f"exp3_{label}_{method}.csv", r["history"])
            if verbose:
                print_summary(r)

    # 使用梯度范数展示算法是否持续向驻点收敛。
    fig, ax = plt.subplots(figsize=(7, 4))
    for name, r in data["exp3"].items():
        if "history" not in r:
            continue
        iterations = [row["k"] for row in r["history"]]
        gradient_norms = [max(row["grad_norm"], 1e-16)
                          for row in r["history"]]
        ax.semilogy(iterations, gradient_norms, label=name)
    ax.set(xlabel="Iteration k", ylabel="Gradient norm", title="exp3")
    ax.set_xscale("symlog", linthresh=10)
    ax.set_xlabel("Iteration k (symlog scale)")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(out / "exp3_gradient.png", dpi=180)
    plt.close(fig)

    (out / "results.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    if verbose:
        print(f"\n实验三完成，结果已保存到：{out}\n", flush=True)
    return data


# ==============================================================================
# 4. PyCharm 运行入口
# ==============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
        help="结果文件保存目录（默认是本实验的 results 文件夹）",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="不显示迭代过程，仅保存结果文件",
    )
    args = parser.parse_args()
    run(args.out.resolve(), verbose=not args.quiet)
