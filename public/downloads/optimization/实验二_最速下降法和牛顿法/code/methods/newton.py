"""基本牛顿法：解 Hessian 线性方程，固定步长为 1。"""
import numpy as np
from .common import record


def newton(f, g, x0, hess=None, tol=1e-06, max_iter=20000, bounds=None, progress=None):
    """基本牛顿法：解 Hessian 线性方程，固定步长为 1。 返回完整结果和 history，支持 progress 回调。"""
    x = np.array(x0, dtype=float)
    hist = [record(0, x, f, g)]
    status = 'iteration_limit'
    for k in range(max_iter):
        gx = g(x)
        if np.linalg.norm(gx) <= tol:
            status = 'gradient_tolerance'
            break
        try:
            # 解线性方程求牛顿方向，避免显式求逆；使用全步长。
            d = np.linalg.solve(hess(x), -gx)
        except np.linalg.LinAlgError:
            status = 'singular_hessian'
            break
        alpha = 1.0
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
    return {'method': 'newton', 'status': status, 'x': x.tolist(), 'f': float(f(x)), 'grad_norm': float(np.linalg.norm(g(x))), 'iterations': len(hist) - 1, 'history': hist}
