"""实验四：一般凸二次规划的有效集方法。

默认显示工作集 W、搜索方向、步长、约束增加/移除事件和 KKT 检查结果。
实际函数 f6、f7 与约束数据 QP 写在文件顶部；约束统一为 A @ x >= b。
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np


# 下面是原题的显式目标函数；修改题目时须同步更新 QP 中的 Q/c/c0。
def f6(x):
    """问题 VI：1/2*x1²+x2²-x1*x2-6*x1-2*x2。"""
    x1, x2 = x
    return float(0.5*x1*x1 + x2*x2 - x1*x2 - 6*x1 - 2*x2)


def f7(x):
    """问题 VII：2*x1²+2*x2²+x3²+2*x1*x2+2*x1*x3-8*x1-6*x2-4*x3+9。"""
    x1, x2, x3 = x
    return float(2*x1*x1 + 2*x2*x2 + x3*x3 + 2*x1*x2 + 2*x1*x3
                 - 8*x1 - 6*x2 - 4*x3 + 9)


# 预设两道二次规划题，包含 Hessian Q、线性系数 c、常数项 c0、约束矩阵 A、右端项 b、可行初始点 x0。
QP = {
    # 每项依次为 (Q, c, 常数项 c0, A, b, 可行初始点 x0)。
    # 统一约束 Ax>=b。constant 不影响最优解，只影响最终函数值。
    "VI": (
        np.array([[1.0, -1.0], [-1.0, 2.0]]),
        np.array([-6.0, -2.0]),
        0.0,
        np.array([
            [-2.0, -1.0],
            [1.0, -1.0],
            [-1.0, -2.0],
            [1.0, 0.0],
            [0.0, 1.0],
        ]),
        np.array([-3.0, -1.0, -2.0, 0.0, 0.0]),
        np.zeros(2),
    ),
    "VII": (
        np.array([
            [4.0, 2.0, 2.0],
            [2.0, 4.0, 0.0],
            [2.0, 0.0, 2.0],
        ]),
        np.array([-8.0, -6.0, -4.0]),
        9.0,
        np.array([
            [-1.0, -1.0, -2.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]),
        np.array([-3.0, 0.0, 0.0, 0.0]),
        np.array([0.5, 0.5, 0.5]),
    ),
}


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



# 将碰到边界的约束纳入工作集，在当前等式约束下求搜索方向，再增删工作集。
# 算法已按方法拆到 code/methods/；目标函数仍在本文件顶部。
if __package__:
    from .methods.active_set import active_set
else:
    from methods.active_set import active_set


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
    """运行两道二次规划问题，并展示工作集更新及 KKT 检验。"""
    out.mkdir(parents=True, exist_ok=True)
    data = {"exp4": {}}


    objectives = {"VI": f6, "VII": f7}

    for name, (Q, c, c0, A, b, x0) in QP.items():
        if verbose:
            print(f"\n[问题 {name}] 初始可行点={fmt_vector(x0)}", flush=True)

        result = active_set(Q, c, A, b, x0)

        # Q/c 决定通用有效集的方向；结果直接调用顶部题目函数，包含常数项。
        objective = objectives[name]
        result["f"] = objective(np.asarray(result["x"]))
        for row in result["history"]:
            row["f"] = objective(np.asarray(row["x"]))

        result["hessian_eigenvalues"] = np.linalg.eigvalsh(Q).tolist()
        data["exp4"][name] = result
        write_csv(out / f"exp4_{name}.csv", result["history"])

        if verbose:
            for item in result["history"]:
                print(
                    f"  k={item['k']:>2}  x={fmt_vector(item['x'])}  "
                    f"W={item['working_set']}  "
                    f"d={fmt_vector(item['direction'])}  "
                    f"alpha={item['alpha']:.4g}  {item['event']}",
                    flush=True,
                )
            print(f"  -> 最优点={fmt_vector(result['x'])}, "
                  f"f={result['f']:.9g}, 迭代={result['iterations']}")
            print("  KKT 残差：" + ", ".join(
                f"{key}={value:.3e}" for key, value in result["kkt"].items()
            ))

    (out / "results.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    if verbose:
        print(f"\n实验四完成，结果已保存到：{out}\n", flush=True)
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
