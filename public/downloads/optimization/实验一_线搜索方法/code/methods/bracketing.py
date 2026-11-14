"""进退法：搜索并包围一维极小点。"""
import math
import numpy as np


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
