"""单文件实验一：进退法、黄金分割法、课堂三点抛物线法与 Armijo 线搜索。

PyCharm 直接运行本文件即可。默认显示关键迭代过程；添加 --quiet 可关闭输出。
实际函数 scalar_f、phi 及其导数写在导入语句后；算法实现位于其后。
"""

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


# ==============================================================================
# 1. 实际问题的目标函数与导数  修改题目先看这里
# ==============================================================================

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

# 先判断初始步长是否使函数下降；若没有，就反向试探，再按倍增步长寻找拐回上升的位置。
def bracket(f, x0=0.0, step=0.1, bounds=(-20.0, 20.0), max_iter=100):
    """进退法：从初始点 x0 向函数值下降的方向扩展，找到包含极小点的三点区间。

    x0：起始搜索点；step：初始试探步长；bounds：允许的搜索范围。
    返回 (a, m, b)，其中 a < m < b，且 f(m) 不大于两侧函数值。
    """
    if step <= 0 or not bounds[0] <= x0 <= bounds[1]:
        raise ValueError('invalid initial point or step')
    # 第一阶段：先沿初始方向试探。如果函数值不降反升，再试反方向。
    a = x0
    b = a + step
    if not bounds[0] <= b <= bounds[1]:
        raise ValueError('trial outside bounds')
    fa, fb = (f(a), f(b))
    if fb >= fa:
        b = a - step
        if not bounds[0] <= b <= bounds[1]:
            raise ValueError('trial outside bounds')
        fb = f(b)
        if fb >= fa:
            return (a - step, a, a + step)
        step = -step
    # 第二阶段：每次将步长扩大为原来的 2 倍，直到遇到函数值回升。
    for _ in range(max_iter):
        step *= 2
        c = b + step
        if not bounds[0] <= c <= bounds[1]:
            raise RuntimeError('cannot bracket within bounds')
        fc = f(c)
        if fc >= fb:
            return tuple(sorted([a, b, c]))
        a, b, fa, fb = (b, c, fb, fc)
    raise RuntimeError('bracketing iteration limit')

# 每轮比较两个内部点的函数值，删除不可能包含最优点的一侧区间。
def golden(f, a, b, tol=1e-06, max_iter=1000):
    """黄金分割法：使用 0.618 比例不断缩小单峰区间。

    tau = (sqrt(5) - 1)/2；每轮复用一个旧试探点，避免重复计算函数值。
    返回 (近似极小点, 每轮迭代记录)。
    """
    if not a < b or tol <= 0:
        raise ValueError('invalid interval/tolerance')
    # tau≈0.618；两个内部试探点关于区间中心对称。
    tau = (math.sqrt(5) - 1) / 2
    c = b - tau * (b - a)
    d = a + tau * (b - a)
    fc, fd = (f(c), f(d))
    hist = [dict(k=0, x=(a + b) / 2, width=b - a)]
    for k in range(1, max_iter + 1):
        if b - a <= tol:
            return ((a + b) / 2, hist)
        # f(c) 更小，极小点不可能在 (d, b)；否则去掉左侧 (a, c)。
        if fc <= fd:
            b, d, fd = (d, c, fc)
            c = b - tau * (b - a)
            fc = f(c)
        else:
            a, c, fc = (c, d, fd)
            d = a + tau * (b - a)
            fd = f(d)
        hist.append(dict(k=k, x=(a + b) / 2, width=b - a))
    raise RuntimeError('golden section iteration limit')

# 使用区间内的三个试点拟合二次函数，取其顶点为新的试探点。
def parabolic(f, a, b, tol=1e-06, max_iter=1000, middle=None):
    """课堂版三点抛物线插值法（2026-10-16 课件，第118张）。

    取 x1 < x2 < x3，且 f(x2) 小于两侧函数值。用三点构造
       q(x) = A*x**2 + B*x + C
    并取抛物线驻点 x_bar = -B/(2*A)。教材公式是：
       B_i = (x_j**2 - x_k**2)*f(x_i)
       C_i = (x_j - x_k)*f(x_i)
       x_bar = sum(B_i) / (2*sum(C_i))
    这里将坐标原点移至 x2，用等价的差商形式计算，避免直接平方
    相近的 x1、x2、x3 造成相减消去误差。

    当 |x_bar - x2| < tol 时停止；否则在四点中按函数值更新
    中心最优点及其左右邻点。不调用 Brent，也不以黄金分割兜底。
    """
    if not a < b or tol <= 0:
        raise ValueError('invalid interval/tolerance')
    x1, x2, x3 = (float(a), float((a + b) / 2 if middle is None else middle), float(b))
    if not x1 < x2 < x3:
        raise ValueError('middle point must lie strictly inside the interval')
    f1, f2, f3 = (f(x1), f(x2), f(x3))
    if not (f2 <= f1 and f2 <= f3):
        raise ValueError('initial middle point must bracket a minimum')
    hist = [dict(k=0, x=x2, width=x3 - x1, x1=x1, x2=x2, x3=x3)]
    for k in range(1, max_iter + 1):
        left_dx, right_dx = (x1 - x2, x3 - x2)
        # 用一阶差商估计二次拟合的系数，数值上等价于课堂三点插值公式。
        slope_l = (f1 - f2) / left_dx
        slope_r = (f3 - f2) / right_dx
        quad_a = (slope_r - slope_l) / (right_dx - left_dx)
        quad_b = slope_l - quad_a * left_dx
        if not np.isfinite(quad_a) or quad_a <= 0:
            raise RuntimeError('interpolation parabola does not open upwards')
        # 拟合二次函数 q(z)=A(z-x2)^2+B(z-x2)+C。
        # 令 q'(z)=0，可得到抛物线顶点 x_bar=x2-B/(2A)。
        x_bar = x2 - quad_b / (2 * quad_a)
        if not x1 < x_bar < x3:
            raise RuntimeError('interpolated point left the bracketing interval')
        if abs(x2 - x_bar) < tol:
            hist.append({
                "k": k,
                "x": x_bar,
                "width": x3 - x1,
                "x1": x1,
                "x2": x2,
                "x3": x3,
                "x_bar": x_bar,
                "stop": "abs(x_bar-x2)<tol",
            })
            return (x_bar, hist)
        f_bar = f(x_bar)
        # 根据新点位于中心 x2 的哪一侧，以及目标函数是否更小，
        # 更新 x1 < x2 < x3，并保持 f(x2) <= f(x1), f(x3)。
        if x_bar < x2:
            if f_bar <= f2:
                x3, f3 = (x2, f2)
                x2, f2 = (x_bar, f_bar)
            else:
                x1, f1 = (x_bar, f_bar)
        elif f_bar <= f2:
            x1, f1 = (x2, f2)
            x2, f2 = (x_bar, f_bar)
        else:
            x3, f3 = (x_bar, f_bar)
        hist.append(dict(k=k, x=x2, width=x3 - x1, x1=x1, x2=x2, x3=x3, x_bar=x_bar))
    raise RuntimeError('parabolic interpolation iteration limit')

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
def optimize(f, g, x0, method='sd', tol=1e-06, max_iter=20000, bounds=None, progress=None):
    """实验一专用：最速下降方向 + Armijo 非精确线搜索。"""
    if method != 'sd':
        raise ValueError('实验一只支持 sd 方法')
    x = np.array(x0, dtype=float)
    hist = [record(0, x, f, g)]
    status = 'iteration_limit'
    for k in range(max_iter):
        gx = g(x)
        if np.linalg.norm(gx) <= tol:
            status = 'gradient_tolerance'
            break
        # 实验一中 d=-∇f(x)，即沿着目标函数最快下降的方向移动。
        d = -gx
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
    """依次执行进退法、黄金分割法、三点插值法及 Armijo，并输出实验数据。"""
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.25,
    })

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
            ax.plot([item["k"] for item in history], np.log(error), label=method)

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
            xlabel="Iteration k",
            ylabel="ln |x_k - x_ref|",
            title=f"Line search: {name}",
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
    ar = optimize(af, ag, [m], tol=1e-8, bounds=(-20.0, 20.0),
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
        "armijo": lambda: optimize(af, ag, [m], tol=1e-8,
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
