"""BFGS 拟牛顿法：逆 Hessian 近似的 BFGS 校正。"""
import numpy as np
from .common import record
from .line_search import armijo


def bfgs(f, g, x0, tol=1e-06, max_iter=20000, bounds=None, progress=None):
    """BFGS 拟牛顿法：逆 Hessian 近似的 BFGS 校正。 返回完整结果和 history，支持 progress 回调。"""
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
        # H 近似 Hessian 的逆矩阵，拟牛顿方向为 -H g。
        d = -H @ gx
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
        if sy > 1e-12 * np.linalg.norm(s) * np.linalg.norm(y):
            # BFGS 逆矩阵校正，rho=1/(s^T y)。
            V = np.eye(len(x)) - np.outer(s, y) / sy
            H = V @ H @ V.T + np.outer(s, s) / sy
            H = (H + H.T) / 2
        old = hist[-1]['f']
        x = xn
        iteration = record(k + 1, x, f, g, old, alpha=alpha)
        hist.append(iteration)
        if progress is not None:
            progress(iteration)
    return {'method': 'bfgs', 'status': status, 'x': x.tolist(), 'f': float(f(x)), 'grad_norm': float(np.linalg.norm(g(x))), 'iterations': len(hist) - 1, 'history': hist}
