

import argparse
import csv
import json
import math
import platform
import random
import statistics
import sys
from pathlib import Path
from time import perf_counter_ns

import matplotlib
matplotlib.use("Agg")  # 适用于 PyCharm：图片保存为 PNG，不强制弹出窗口。
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq  # 只用于计算高精度参照解，不代替实验算法。

# f 是目标函数，输入和输出都是标量。
def scalar_f(x):
    """原题f(x)=ln(1+x+x²+exp(x+x²))/(1+x²)+ln(1+2exp(x−7))；稳定计算。"""
    u = 1 + x * x
    first = np.logaddexp(math.log(1 + x + x * x), x + x * x) / u
    second = np.logaddexp(0.0, math.log(2.0) + x - 7)
    return float(first + second)

# 直接写出解析导数，比有限差分更准确，避免差分步长误差。
def scalar_g(x):
    """f(x) 的一阶导数 f'(x)，用于参考解和 Armijo 搜索。"""
    u, p, t = (1 + x * x, 1 + x + x * x, x + x * x)
    L = float(np.logaddexp(math.log(p), t))
    w = math.exp(t - L)
    Lp = (1 - w) * (1 + 2 * x) / p + w * (1 + 2 * x)
    z = math.log(2.0) + x - 7
    sig = math.exp(-float(np.logaddexp(0.0, -z)))
    return Lp / u - 2 * x * L / u ** 2 + sig

def phi(x):
    """实验一第二个一元测试函数 phi(x)。"""
    return 2 * math.exp(math.sin(math.pi * x ** 5 / 6)) + 3 * x * x + 2 * x

def phi_g(x):
    """phi(x) 的一阶导数。"""
    t = math.pi * x ** 5 / 6
    return 2 * math.exp(math.sin(t)) * math.cos(t) * 5 * math.pi * x ** 4 / 6 + 6 * x + 2


# ==============================================================================
# 公共：输出格式化工具
# ==============================================================================


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


# 2. 算法实现
# ==============================================================================

# 先判断初始步长是否使函数下降；若没有，就反向试探，再按倍增步长寻找拐回上升的位置。
# 算法已按方法拆到 code/methods/；目标函数仍在本文件顶部。
if __package__:
    from .methods.bracketing import bracket
    from .methods.golden_section import golden
    from .methods.parabolic_interpolation import parabolic
    from .methods.armijo_search import steepest_descent
else:
    from methods.bracketing import bracket
    from methods.golden_section import golden
    from methods.parabolic_interpolation import parabolic
    from methods.armijo_search import steepest_descent

if __package__:
    from .plot_style import configure_chinese_plotting
else:
    from plot_style import configure_chinese_plotting




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
    """依次执行进退法、黄金分割法、三点插值法及 Armijo，并输出实验数据。"""
    out.mkdir(parents=True, exist_ok=True)
    configure_chinese_plotting()

    data = {
        "environment": {
            "python": sys.version,
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "timer": "perf_counter_ns",
            "repeats": 50,
            "variance_ddof": 1,
        },
        "exp1": {},
    }

    # 1. 先使用进退法找单峰区间。
    if verbose:
        print("\n========== 实验一：一维线搜索方法 ==========", flush=True)
        print("[1/4] 进退法：寻找单峰区间", flush=True)
    a, m, b = bracket(scalar_f)

    # 使用 SciPy 的 Brent 根查找计算参照值，仅用于评价误差。
    # 注意：真正的课堂三点插值算法在上面的 parabolic() 中。
    xref = brentq(scalar_g, a, b, xtol=1e-14)
    data["exp1"]["bracket"] = [a, m, b]
    data["exp1"]["reference"] = xref
    scalar_runs = {}

    if verbose:
        print(f"  区间=[{a:.8g}, {b:.8g}]，中间点={m:.8g}", flush=True)
        print(f"  高精度参考极小点={xref:.10g}", flush=True)
        print("[2/4] 黄金分割法与课堂三点抛物线插值法", flush=True)

    # 2. 在两个一元目标函数上分别运行两种算法。
    # tuple: (名称, 函数, 导数, 左边界, 右边界, 参考解, 中间点)
    cases = [("f", scalar_f, scalar_g, a, b, xref, m)]
    for i, (lo, hi) in enumerate([(1.29, 1.72)], start=1):
        reference = brentq(phi_g, lo, hi, xtol=1e-14)
        cases.append((f"phi_{i}", phi, phi_g, lo, hi, reference, (lo + hi) / 2))

    for name, fun, grad, lo, hi, reference, middle in cases:
        fig, ax = plt.subplots(figsize=(6.4, 3.5))
        if verbose:
            print(f"\n  目标函数：{name}，区间=[{lo:.6g}, {hi:.6g}]", flush=True)

        for method, solver in [("golden", golden), ("parabolic", parabolic)]:
            calls = [0]  # 用可变列表记录函数调用次数。

            def counted(x):
                calls[0] += 1
                return fun(x)

            if method == "parabolic":
                x, history = solver(counted, lo, hi, middle=middle)
            else:
                x, history = solver(counted, lo, hi)

            row = {
                "method": method,
                "x": x,
                "f": fun(x),
                "reference": reference,
                "abs_error": abs(x - reference),
                "iterations": len(history) - 1,
                "function_calls": calls[0],
                "history": history,
            }
            scalar_runs[f"{name}_{method}"] = row
            write_csv(out / f"exp1_{name}_{method}.csv", history)

            # 画 ln(|x_k-x_ref|)，观察收敛趋势。
            error = [max(abs(item["x"] - reference), np.finfo(float).eps)
                     for item in history]
            ax.plot([item["k"] for item in history], np.log(error), label={"golden": "黄金分割法", "parabolic": "三点抛物线插值法"}[method])

            if verbose:
                print(f"    {method}: 迭代={len(history)-1}, "
                      f"x={x:.10g}, 绝对误差={abs(x-reference):.3e}, "
                      f"函数调用={calls[0]}", flush=True)
                checkpoints = [item for item in history
                               if item["k"] in (0, 1, 2, 3)
                               or item["k"] % 10 == 0
                               or item is history[-1]]
                # 相同迭代记录只输出一次。
                seen = set()
                for item in checkpoints:
                    if item["k"] in seen:
                        continue
                    seen.add(item["k"])
                    print(f"      k={item['k']:>3}  x={item['x']:.9g}  "
                          f"区间长度={item['width']:.3e}", flush=True)

        ax.set(
            xlabel="迭代次数 k",
            ylabel=r"位置误差的自然对数 $\ln|x_k-x_{\mathrm{ref}}|$",
            title="函数 f 的一维搜索误差对比" if name == "f" else "函数 φ 的一维搜索误差对比",
        )
        ax.legend()
        fig.tight_layout()
        fig.savefig(out / f"exp1_{name}.png", dpi=180)
        plt.close(fig)

    # 3. 最速下降方向结合 Armijo 回溯搜索。
    if verbose:
        print("\n[3/4] Armijo 最速下降法", flush=True)
    af = lambda z: scalar_f(float(z[0]))
    ag = lambda z: np.array([scalar_g(float(z[0]))])
    ar = steepest_descent(af, ag, [m], tol=1e-8, bounds=(-20.0, 20.0),
                  progress=(lambda row: print_progress(row, every=10)) if verbose else None)
    ar["reference"] = xref
    ar["abs_error"] = abs(ar["x"][0] - xref)
    scalar_runs["f_armijo"] = ar
    write_csv(out / "exp1_f_armijo.csv", ar["history"])
    data["exp1"]["runs"] = scalar_runs
    if verbose:
        print_summary(ar)

    # 4. 重复计时：先预热，再随机打乱顺序测量 50 次。
    if verbose:
        print("[4/4] 50 次运行时间测量（关闭逐轮输出）", flush=True)
    tasks = {
        "golden": lambda: golden(scalar_f, a, b)[0],
        "parabolic": lambda: parabolic(scalar_f, a, b, middle=m)[0],
        "armijo": lambda: steepest_descent(af, ag, [m], tol=1e-8,
                                   bounds=(-20.0, 20.0))["x"][0],
    }

    for task in tasks.values():
        for _ in range(5):
            task()

    samples = {name: [] for name in tasks}
    raw = []
    rng = random.Random(20261105)

    for repeat in range(50):
        order = list(tasks)
        rng.shuffle(order)
        for name in order:
            start = perf_counter_ns()
            x = tasks[name]()
            elapsed = (perf_counter_ns() - start) / 1_000_000.0
            if abs(x - xref) > 1e-6:
                raise AssertionError(f"{name}: accuracy requirement not met")
            samples[name].append(elapsed)
            raw.append({
                "repeat": repeat + 1,
                "method": name,
                "time_ms": elapsed,
                "x": x,
                "abs_error": abs(x - xref),
            })

    data["exp1"]["timing"] = {
        name: {
            "mean_ms": statistics.mean(values),
            "sample_variance_ms2": statistics.variance(values),
            "min_ms": min(values),
            "max_ms": max(values),
        }
        for name, values in samples.items()
    }
    write_csv(out / "exp1_timing_50.csv", raw)

    (out / "results.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    if verbose:
        for name, stats in data["exp1"]["timing"].items():
            print(f"  {name}: 平均={stats['mean_ms']:.4f} ms，"
                  f"样本方差={stats['sample_variance_ms2']:.6g} ms²")
        print(f"实验一完成，结果已保存到：{out}\n", flush=True)
    return data



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
