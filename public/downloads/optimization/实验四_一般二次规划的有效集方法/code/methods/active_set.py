"""正定二次规划的可行有效集法：独立的完整算法实现。"""
import numpy as np


def active_set(Q, c, A, b, x0, tol=1e-06, max_iter=200):
    """min .5 x'Qx+c'x, Ax>=b，L=f-lambda'(Ax-b)。"""
    x = np.array(x0, dtype=float)
    n = len(x)
    if np.min(A @ x - b) < -tol:
        raise ValueError('initial point is infeasible')
    if np.min(np.linalg.eigvalsh(Q)) <= 0:
        raise ValueError('Q must be positive definite')
    # W 是有效集（工作集）：当前满足等号 A_i*x=b_i 的约束序号（从 0 开始）。
    W = list(np.flatnonzero(abs(A @ x - b) <= tol))
    hist = []
    f = lambda z: float(0.5 * z @ Q @ z + c @ z)
    for k in range(max_iter):
        g = Q @ x + c
        AW = A[W]
        # 固定当前工作集，构造 KKT 线性方程求 d 与拉格朗日乘子 lambda。
        # [ Q  -A_W^T] [d     ] = [-g]
        # [A_W    0  ] [lambda]   [ 0]
        if W:
            K = np.block([[Q, -AW.T], [AW, np.zeros((len(W), len(W)))]])
            sol = np.linalg.solve(K, np.r_[-g, np.zeros(len(W))])
            d = sol[:n]
            lam = sol[n:]
        else:
            d = np.linalg.solve(Q, -g)
            lam = np.array([])
        # 保存当前迭代的工作集与方向；用户界面显示时编号从 1 开始。
        row = {
            "k": k,
            "x": x.tolist(),
            "f": f(x),
            "working_set": [int(i + 1) for i in W],
            "direction": d.tolist(),
            "multipliers": lam.tolist(),
            "alpha": 0.0,
            "event": "",
        }
        # 若 d≈0，检查有效约束的 lambda：
        #   全部非负 => 满足 KKT、达到最优；有负值 => 删除最负的约束。
        if np.linalg.norm(d) <= tol:
            if not W or np.min(lam) >= -tol:
                row['event'] = 'optimal'
                hist.append(row)
                break
            j = int(np.argmin(lam))
            row['event'] = f'remove {W[j] + 1}'
            hist.append(row)
            W.pop(j)
            continue
        # 沿 d 前进时不得违反任何未激活约束，取最早碰到边界的步长。
        alpha = 1.0
        blocker = None
        Ad = A @ d
        slack = A @ x - b
        for i in range(len(b)):
            if i not in W and Ad[i] < -1e-12:
                ratio = max(0.0, float(slack[i] / -Ad[i]))
                if ratio < alpha - 1e-12:
                    alpha = ratio
                    blocker = i
        row['alpha'] = alpha
        row['event'] = 'full step' if blocker is None else f'add {blocker + 1}'
        hist.append(row)
        x = x + alpha * d
        # 若在 alpha<1 时被约束挡住，就把该约束加入工作集。
        if blocker is not None:
            W.append(blocker)
        if np.min(A @ x - b) < -10 * tol:
            raise RuntimeError('lost feasibility')
    else:
        raise RuntimeError('active set iteration limit')
    full_lam = np.zeros(len(b))
    for i, l in zip(W, lam):
        full_lam[i] = l
    slack = A @ x - b
    # KKT 残差分别对应：原始可行、乘子非负、梯度平衡、互补松弛。
    # 它们越接近 0，越说明解满足凸二次规划的最优性条件。
    kkt = {
        "primal": float(max(0.0, -np.min(slack))),
        "dual": float(max(0.0, -np.min(full_lam))),
        "stationarity": float(np.linalg.norm(Q @ x + c - A.T @ full_lam, np.inf)),
        "complementarity": float(np.max(abs(full_lam * slack))),
    }
    return {
        "x": x.tolist(),
        "f": f(x),
        "iterations": len(hist) - 1,
        "history": hist,
        "active": [int(i + 1) for i in np.flatnonzero(abs(slack) <= tol)],
        "multipliers": full_lam.tolist(),
        "kkt": kkt,
    }
