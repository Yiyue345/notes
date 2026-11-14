"""中文绘图字体：优先使用 Windows 微软雅黑，并兼容已安装的中文字体。"""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager


def configure_chinese_plotting():
    font_path = Path("C:/Windows/Fonts/msyh.ttc")
    if font_path.is_file():
        font_manager.fontManager.addfont(str(font_path))
        family = font_manager.FontProperties(fname=str(font_path)).get_name()
    else:
        available = {font.name for font in font_manager.fontManager.ttflist}
        candidates = ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC")
        family = next((name for name in candidates if name in available), None)
        if family is None:
            raise RuntimeError("未找到中文字体，请安装微软雅黑、黑体或 Noto Sans CJK SC 后重试。")
    plt.rcParams.update({"font.family": family, "font.size": 10,
                         "axes.unicode_minus": False, "axes.grid": True, "grid.alpha": 0.25})
