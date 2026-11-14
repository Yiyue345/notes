"""PRP+ 非线性共轭梯度法：非负 beta 与周期重启。"""
import numpy as np
from .common import record
from .line_search import armijo


def conjugate_gradient(f, g, x0, tol=1e-06, max_iter=20000, bounds=None, progress=None):
    """PRP+ 非线性共轭梯度法：非负 beta 与周期重启。 返回完整结果和 history，支持 progress 回调。"""
    x = np.array(x0, dtype=float)
    H = np.eye(len(x))
    d = -g(x)
    hist = [record(0, x, f, g)]
    status = 'iteration_limit'
    for k in range(max_iter):
        gx = g(x)
        if np.linalg.norm(gx) <= tol:
            status = 'gradient_tolerance'
            break
        if gx @ d >= -1e-12 * np.linalg.norm(gx) * max(np.linalg.norm(d), 1e-30):
            # 搜索方向为负梯度。
            d = -gx
            H = np.eye(len(x))
        try:
            # 沿当前下降方向回溯，直到满足 Armijo 充分下降条件。
            alpha = armijo(f, x, gx, d, bounds=bounds)
        except RuntimeError:
            status = 'line_search_failed'
            break
        xn = x + alpha * d
        if not np.all(np.isfinite(xn)):
            status = 'nonfinite'
            break
        gn = g(xn)
        s = xn - x
        y = gn - gx
        sy = float(s @ y)
        # PRP+ 系数截为非负，每 n 步重启。
        beta = max(0.0, float(gn @ y / (gx @ gx)))
        if (k + 1) % len(x) == 0:
            beta = 0.0
        d = -gn + beta * d
        old = hist[-1]['f']
        x = xn
        iteration = record(k + 1, x, f, g, old, alpha=alpha)
        hist.append(iteration)
        if progress is not None:
            progress(iteration)
    return {'method': 'prp', 'status': status, 'x': x.tolist(), 'f': float(f(x)), 'grad_norm': float(np.linalg.norm(g(x))), 'iterations': len(hist) - 1, 'history': hist}
