"""各方法共用的 Armijo 回溯步长搜索。"""
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
