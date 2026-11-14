"""三点抛物线插值法：不含黄金分割或 Brent 保底。"""
import math
import numpy as np


def parabolic(f, a, b, tol=1e-06, max_iter=1000, middle=None):
    """抛物线插值法"""
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
        # 课件的三点插值公式：先计算 B1、B2、B3 和 C1、C2、C3。
        B1 = (x2**2 - x3**2) * f1
        B2 = (x3**2 - x1**2) * f2
        B3 = (x1**2 - x2**2) * f3
        C1 = (x2 - x3) * f1
        C2 = (x3 - x1) * f2
        C3 = (x1 - x2) * f3
        B = math.fsum((B1, B2, B3))
        C = math.fsum((C1, C2, C3))
        D = (x1 - x2) * (x2 - x3) * (x3 - x1)
        # 课件中二次项系数为 -C/D；必须向上开口才能求极小值。
        if not math.isfinite(C) or C == 0 or not math.isfinite(D) or D == 0:
            raise RuntimeError('interpolation denominator is zero or nonfinite')
        quad_a = -C / D
        if not math.isfinite(quad_a) or quad_a <= 0:
            raise RuntimeError('interpolation parabola does not open upwards')
        # 顶点直接使用课件公式：x_bar=(B1+B2+B3)/(2*(C1+C2+C3))。
        x_bar = B / (2 * C)
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
