"""单文件实验二：最速下降法、精确线搜索和基本牛顿法。

默认在 PyCharm 控制台显示首轮和周期性迭代信息，避免长迭代刷屏。
实际函数 f1、f2、f3 及梯度/Hessian 写在文件顶部，之后是求解算法。
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

Q1 = np.array([[21.0, 4.0], [4.0, 15.0]])
Q2 = np.array([[21.0, 4.0], [4.0, 1.0]])
C12 = np.array([2.0, 3.0])

# 问题 I、II 的公式直接写在这里；改题目时同步修改梯度与 Hessian 参数。
def f1(x):
    """问题 I：1/2*(21*x1²+8*x1*x2+15*x2²)+2*x1+3*x2。"""
    x1, x2 = x
    return float(0.5 * (21*x1*x1 + 8*x1*x2 + 15*x2*x2) + 2*x1 + 3*x2)


def g1(x):
    """问题 I 梯度：(21*x1+4*x2+2, 4*x1+15*x2+3)。"""
    return Q1 @ x + C12


def h1(x):
    """问题 I Hessian，恒为 Q1。"""
    return Q1


def f2(x):
    """问题 II：1/2*(21*x1²+8*x1*x2+x2²)+2*x1+3*x2。"""
    x1, x2 = x
    return float(0.5 * (21*x1*x1 + 8*x1*x2 + x2*x2) + 2*x1 + 3*x2)


def g2(x):
    """问题 II 梯度：(21*x1+4*x2+2, 4*x1+x2+3)。"""
    return Q2 @ x + C12


def h2(x):
    """问题 II Hessian，恒为 Q2。"""
    return Q2


# 先对一元中间变量 t 求导，再借助链式法则处理二维变量 x。
def radial(t):
    """h(t), h'(t), h''(t), t=(x1+3)^2+x2^2/2 >= 0。"""
    # 通过 t 构造 h(t)，并返回 h、h'、h''；下游函数应用链式法则。
    u, r = (1 + t, math.exp(-t))
    L = t + math.log1p(u * r)
    Lp = (1 + r) / (1 + u * r)
    Lpp = ((t - 1) * r - r * r) / (1 + u * r) ** 2
    return (L / u, Lp / u - L / u ** 2, Lpp / u - 2 * Lp / u ** 2 + 2 * L / u ** 3)

def f3(x):
    """问题III：ln(1+t+exp(t))/(1+t)，t=(x1+3)²+x2²/2；radial为稳定实现。"""
    return radial((x[0] + 3) ** 2 + x[1] ** 2 / 2)[0]

def g3(x):
    """问题 III 的梯度，由 h'(t) 乘以 t 的梯度得到。"""
    t = (x[0] + 3) ** 2 + x[1] ** 2 / 2
    return radial(t)[1] * np.array([2 * (x[0] + 3), x[1]])

def h3(x):
    """问题 III 的 Hessian：h''(t)∇t∇t^T+h'(t)∇²t。"""
    t = (x[0] + 3) ** 2 + x[1] ** 2 / 2
    _, hp, hpp = radial(t)
    v = np.array([2 * (x[0] + 3), x[1]])
    return hpp * np.outer(v, v) + hp * np.diag([2.0, 1.0])




# Q 是 Hessian，c 是线性项系数；正定 Q 时有唯一极小点。
def quadratic(Q, c, constant=0.0):
    """构造 f(x)=1/2*x^T Q x+c^T x+constant 的函数、梯度和 Hessian。"""
    return (lambda x: float(0.5 * x @ Q @ x + c @ x + constant), lambda x: Q @ x + c, lambda x: Q)


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
def optimize(
    f, g, x0, method='sd', hess=None, Q=None,
    tol=1e-6, max_iter=20000, bounds=None, progress=None,
):
    """实验二专用：最速下降（可精确线搜索）和步长 1 的基本牛顿法。"""
    if method not in ('sd', 'newton'):
        raise ValueError('实验二只支持 sd/newton')
    x = np.array(x0, dtype=float)
    hist = [record(0, x, f, g)]
    status = 'iteration_limit'
    for k in range(max_iter):
        gx = g(x)
        if np.linalg.norm(gx) <= tol:
            status = 'gradient_tolerance'
            break
        # 牛顿法方向 d=-[∇²f(x)]^{-1}∇f(x)；最速下降法方向 d=-∇f(x)。
        if method == 'newton':
            try:
                d = np.linalg.solve(hess(x), -gx)
            except np.linalg.LinAlgError:
                status = 'singular_hessian'
                break
            # 按本实验要求使用最基本的牛顿法：固定 alpha=1，不进行阻尼。
            alpha = 1.0
        else:
            d = -gx
            if gx @ d >= -1e-12 * np.linalg.norm(gx) * max(np.linalg.norm(d), 1e-30):
                d = -gx
            # 对正定二次函数精确线搜索：alpha=-g^T d/(d^T Q d)。
            # 非二次函数不提供 Q，此时采用 Armijo 回溯选步长。
            if Q is not None:
                curvature = float(d @ Q @ d)
                if curvature <= 0:
                    status = 'unbounded_descent_ray'
                    break
                alpha = float(-gx @ d / curvature)
            else:
                try:
                    alpha = armijo(f, x, gx, d, bounds=bounds)
                except RuntimeError:
                    status = 'line_search_failed'
                    break
        xn = x + alpha * d
        if not np.all(np.isfinite(xn)):
            status = 'nonfinite'
            break
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
    """运行问题 I、II 的二次型与问题 III 的非二次函数。"""
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.25,
    })
    data = {"exp2": {}}

    if verbose:
        print("\n========== 实验二：最速下降法与牛顿法 ==========", flush=True)
        print("提示：sd=最速下降法，newton=基本牛顿法", flush=True)

    # 第一部分：两组不同的正定 Hessian，对比迭代速度。
    for prob, Q, f, g, h in [
        ("I", Q1, f1, g1, h1),
        ("II", Q2, f2, g2, h2),
    ]:
        if verbose:
            print(f"\n[问题 {prob}] 正定二次函数，初始点 [-30, 100]", flush=True)
        for method in ["sd", "newton"]:
            if verbose:
                print(f"  开始 {method}：", flush=True)
            r = optimize(
                f, g, [-30.0, 100.0], method,
                hess=h, Q=Q,
                progress=(lambda row: print_progress(row, every=1000))
                         if verbose else None,
            )
            r["hessian_eigenvalues"] = np.linalg.eigvalsh(Q).tolist()
            data["exp2"][f"{prob}_{method}"] = r
            if verbose:
                print_summary(r)

    # 第二部分：问题 III 不是简单二次函数。
    # 在不同初始点下，基本牛顿法可能停在不同的驻点。
    tstar = 0.0
    data["exp2"]["III_reference"] = {"t": tstar, "f": radial(tstar)[0]}
    for label, x0 in [("far", [-10.0, 10.0]), ("near", [-3.5, 0.5])]:
        if verbose:
            print(f"\n[问题 III / {label}] 初始点={fmt_vector(x0)}", flush=True)
        for method in ["sd", "newton"]:
            if verbose:
                print(f"  开始 {method}：", flush=True)
            r = optimize(
                f3, g3, x0, method,
                hess=h3, max_iter=50000,
                progress=(lambda row: print_progress(row, every=1000))
                         if verbose else None,
            )
            r["t"] = (r["x"][0] + 3) ** 2 + r["x"][1] ** 2 / 2
            r["optimal_value_gap"] = r["f"] - radial(tstar)[0]
            r["hessian_eigenvalues"] = np.linalg.eigvalsh(h3(np.array(r["x"]))).tolist()
            data["exp2"][f"III_{label}_{method}"] = r
            if verbose:
                print_summary(r)
                print(f"     与全局最优值差={r['optimal_value_gap']:.3e}")

    # 一次性导出所有 history，便于用 CSV 阅读、画图或复核。
    for key, r in data["exp2"].items():
        if "history" in r:
            write_csv(out / f"exp2_{key}.csv", r["history"])

    fig, ax = plt.subplots(figsize=(7, 4))
    for name, r in data["exp2"].items():
        if "history" not in r:
            continue
        iterations = [row["k"] for row in r["history"]]
        gradient_norms = [max(row["grad_norm"], 1e-16)
                          for row in r["history"]]
        ax.semilogy(iterations, gradient_norms, label=name)
    ax.set(xlabel="Iteration k", ylabel="Gradient norm", title="exp2")
    ax.set_xscale("symlog", linthresh=10)
    ax.set_xlabel("Iteration k (symlog scale)")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(out / "exp2_gradient.png", dpi=180)
    plt.close(fig)

    (out / "results.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    if verbose:
        print(f"\n实验二完成，结果已保存到：{out}\n", flush=True)
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
