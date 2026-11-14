"""实验三：BFGS、DFP 和 PRP+ 非线性共轭梯度法。

默认打印迭代进度与每种方法的最终结果；--quiet 仅保存文件。
实际函数 f4、f5 及梯度/Hessian 写在文件顶部；各方法的算法分别在 methods/ 目录。
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
# 算法已按方法拆到 code/methods/；目标函数仍在本文件顶部。
if __package__:
    from .methods.bfgs import bfgs
    from .methods.dfp import dfp
    from .methods.conjugate_gradient import conjugate_gradient
else:
    from methods.bfgs import bfgs
    from methods.dfp import dfp
    from methods.conjugate_gradient import conjugate_gradient

if __package__:
    from .plot_style import configure_chinese_plotting
else:
    from plot_style import configure_chinese_plotting


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
    configure_chinese_plotting()
    data = {"exp3": {}}

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
            progress = (lambda row: print_progress(row, every=1000)) if verbose else None
            if method == "bfgs":
                r = bfgs(f, g, x0, max_iter=20000, progress=progress)
            elif method == "dfp":
                r = dfp(f, g, x0, max_iter=20000, progress=progress)
            else:
                r = conjugate_gradient(f, g, x0, max_iter=20000, progress=progress)
            data["exp3"][f"{label}_{method}"] = r
            write_csv(out / f"exp3_{label}_{method}.csv", r["history"])
            if verbose:
                print_summary(r)

    # 使用梯度范数展示算法是否持续向驻点收敛。
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    for name, r in data["exp3"].items():
        if "history" not in r:
            continue
        iterations = [row["k"] for row in r["history"]]
        gradient_norms = [max(row["grad_norm"], 1e-16)
                          for row in r["history"]]
        problem, method = name.rsplit("_", 1)
        problem_text = {"IV_a": "问题Ⅳ 初值(1,0.7)", "IV_b": "问题Ⅳ 初值(1,2)", "V": "问题Ⅴ"}[problem]
        method_text = {"bfgs": "BFGS拟牛顿法", "dfp": "DFP拟牛顿法", "prp": "PRP+共轭梯度法"}[method]
        ax.semilogy(iterations, gradient_norms, label=f"{problem_text} {method_text}")
    ax.set(xlabel="迭代次数 k", ylabel="梯度范数", title="拟牛顿法与共轭梯度法收敛对比")
    ax.set_xscale("symlog", linthresh=10)
    ax.set_xlabel("迭代次数 k（对称对数刻度）")
    ax.legend(fontsize=8.5, ncol=2, loc="upper center",
              bbox_to_anchor=(0.5, -0.19), frameon=False)
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
