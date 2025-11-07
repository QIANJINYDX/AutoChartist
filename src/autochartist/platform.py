"""平台适配模块：检测操作系统、快捷键、字体等"""

import platform
import sys
from pathlib import Path
from typing import Dict, Optional


def get_platform() -> str:
    """获取当前平台名称"""
    system = platform.system()
    if system == "Darwin":
        return "macOS"
    elif system == "Windows":
        return "Windows"
    elif system == "Linux":
        return "Linux"
    return "Unknown"


def get_shortcuts() -> Dict[str, str]:
    """获取平台特定的快捷键显示"""
    if platform.system() == "Darwin":
        return {"open": "⌘O", "save": "⌘S", "copy": "⌘C", "paste": "⌘V"}
    return {"open": "Ctrl+O", "save": "Ctrl+S", "copy": "Ctrl+C", "paste": "Ctrl+V"}


def get_default_ui_font() -> str:
    """获取平台默认 UI 字体"""
    if platform.system() == "Darwin":
        return "San Francisco"
    elif platform.system() == "Windows":
        return "Segoe UI"
    return "DejaVu Sans"


def get_chart_font() -> list:
    """
    获取图表默认字体列表（确保中文支持）
    返回字体列表，按优先级排序
    """
    system = platform.system()
    
    if system == "Windows":
        # Windows 中文字体
        return ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong', 'DejaVu Sans']
    elif system == "Darwin":
        # macOS 中文字体
        return ['PingFang SC', 'Arial Unicode MS', 'STHeiti', 'STSong', 'DejaVu Sans']
    else:
        # Linux 中文字体
        return ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'DejaVu Sans']


def get_config_dir() -> Path:
    """获取配置目录路径"""
    system = platform.system()
    if system == "Windows":
        base = Path.home() / "AppData" / "Local"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux
        base = Path.home() / ".config"
    
    config_dir = base / "autochartist"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """获取数据目录路径（用于存储临时文件、缓存等）"""
    system = platform.system()
    if system == "Windows":
        base = Path.home() / "AppData" / "Local" / "Temp"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Caches"
    else:  # Linux
        base = Path.home() / ".cache"
    
    data_dir = base / "autochartist"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def is_portable() -> bool:
    """检测是否为打包后的可执行文件"""
    return getattr(sys, "frozen", False)


def get_resource_path(relative_path: str) -> Path:
    """获取资源文件路径（支持打包后的可执行文件）"""
    if is_portable():
        # PyInstaller 打包后的路径
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境路径
        base_path = Path(__file__).parent.parent.parent
    
    return base_path / relative_path


def get_output_dir() -> Path:
    """获取项目输出目录（用于存储生成的图表）"""
    # 获取项目根目录
    if is_portable():
        # 打包后的可执行文件，使用可执行文件所在目录
        base_path = Path(sys.executable).parent
    else:
        # 开发环境路径
        base_path = Path(__file__).parent.parent.parent
    
    # 创建 outputs 目录
    output_dir = base_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

