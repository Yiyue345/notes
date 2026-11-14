"""Armijo 回溯及其负梯度外层迭代。"""
import math
import numpy as np


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


def steepest_descent(f, g, x0, tol=1e-06, max_iter=20000, bounds=None, progress=None):
    """实验一专用：最速下降方向 + Armijo 非精确线搜索。"""
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
        "method": "sd",
        "status": status,
        "x": x.tolist(),
        "f": float(f(x)),
        "grad_norm": float(np.linalg.norm(g(x))),
        "iterations": len(hist) - 1,
        "history": hist,
    }
