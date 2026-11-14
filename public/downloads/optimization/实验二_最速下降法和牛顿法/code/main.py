

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


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
    return (lambda x: float(0.5 * x @ Q @ x + c @ x + constant), lambda x: Q @ x + c, lambda x: Q)


def fmt_vector(values, precision=5):
    arr = np.asarray(values, dtype=float)
    return "[" + ", ".join(f"{value:.{precision}g}" for value in arr) + "]"


def print_progress(row, every=1000):
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
    print(
        f"  -> 状态={result.get('status', 'completed')}；"
        f"迭代={result['iterations']}；"
        f"x={fmt_vector(result['x'])}；"
        f"f={result['f']:.10g}；"
        f"||g||={result.get('grad_norm', float('nan')):.3e}",
        flush=True,
    )



if __package__:
    from .methods.steepest_descent import steepest_descent
    from .methods.newton import newton
else:
    from methods.steepest_descent import steepest_descent
    from methods.newton import newton

if __package__:
    from .plot_style import configure_chinese_plotting
else:
    from plot_style import configure_chinese_plotting


# 一行代表一次迭代，适合在 Excel 中观察数据变化。
def write_csv(path, rows):
    """导出迭代过程到 CSV：每行一次迭代，每列一个观测量。"""
    if not rows:
        return

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

def run(out, verbose=True):
    """运行问题 I、II 的二次型与问题 III 的非二次函数。"""
    out.mkdir(parents=True, exist_ok=True)
    configure_chinese_plotting()
    data = {"exp2": {}}


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
            progress = (lambda row: print_progress(row, every=1000)) if verbose else None
            if method == "sd":
                r = steepest_descent(f, g, [-30.0, 100.0], Q=Q, progress=progress)
            else:
                r = newton(f, g, [-30.0, 100.0], hess=h, progress=progress)
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
            progress = (lambda row: print_progress(row, every=1000)) if verbose else None
            if method == "sd":
                r = steepest_descent(f3, g3, x0, max_iter=50000, progress=progress)
            else:
                r = newton(f3, g3, x0, hess=h3, max_iter=50000, progress=progress)
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

    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    for name, r in data["exp2"].items():
        if "history" not in r:
            continue
        iterations = [row["k"] for row in r["history"]]
        gradient_norms = [max(row["grad_norm"], 1e-16)
                          for row in r["history"]]
        problem, method = name.rsplit("_", 1)
        problem_text = {"I": "问题Ⅰ", "II": "问题Ⅱ", "III_far": "问题Ⅲ 远初值", "III_near": "问题Ⅲ 近初值"}[problem]
        method_text = {"sd": "最速下降法", "newton": "基本牛顿法"}[method]
        ax.semilogy(iterations, gradient_norms, label=f"{problem_text} {method_text}")
    ax.set(xlabel="迭代次数 k", ylabel="梯度范数", title="最速下降法与基本牛顿法收敛对比")
    ax.set_xscale("symlog", linthresh=10)
    ax.set_xlabel("迭代次数 k（对称对数刻度）")
    ax.legend(fontsize=8.5, ncol=2, loc="upper center",
              bbox_to_anchor=(0.5, -0.19), frameon=False)
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
