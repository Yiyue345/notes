"""最速下降法：二次型精确步长，非二次函数 Armijo 回溯。"""
import numpy as np
from .common import record
from .line_search import armijo


def steepest_descent(f, g, x0, Q=None, tol=1e-06, max_iter=20000, bounds=None, progress=None):
    """最速下降法：二次型精确步长，非二次函数 Armijo 回溯。 返回完整结果和 history，支持 progress 回调。"""
    x = np.array(x0, dtype=float)
    hist = [record(0, x, f, g)]
    status = 'iteration_limit'
    for k in range(max_iter):
        gx = g(x)
        if np.linalg.norm(gx) <= tol:
            status = 'gradient_tolerance'
            break
        # 搜索方向为负梯度。
        d = -gx
        if gx @ d >= -1e-12 * np.linalg.norm(gx) * max(np.linalg.norm(d), 1e-30):
            # 搜索方向为负梯度。
            d = -gx
        if Q is not None:
            # 二次函数精确线搜索，检查方向曲率为正。
            curvature = float(d @ Q @ d)
            if curvature <= 0:
                status = 'unbounded_descent_ray'
                break
            alpha = float(-gx @ d / curvature)
        else:
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
        old = hist[-1]['f']
        x = xn
        iteration = record(k + 1, x, f, g, old, alpha=alpha)
        hist.append(iteration)
        if progress is not None:
            progress(iteration)
    return {'method': 'sd', 'status': status, 'x': x.tolist(), 'f': float(f(x)), 'grad_norm': float(np.linalg.norm(g(x))), 'iterations': len(hist) - 1, 'history': hist}
