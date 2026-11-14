"""各方法共用的迭代记录格式，不包含算法更新公式。"""
import numpy as np


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
