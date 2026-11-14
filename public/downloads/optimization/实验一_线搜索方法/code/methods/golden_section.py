"""黄金分割法：按固定比例收缩搜索区间。"""
import math
import numpy as np


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
