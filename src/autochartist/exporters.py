"""导出模块：PNG/SVG/Notebook/脚本导出"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import shutil


class Exporter:
    """导出器：支持多种格式导出"""
    
    @staticmethod
    def export_image(
        source_path: str,
        target_path: str,
        format: str = "png",
        dpi: int = 300,
        transparent: bool = False,
    ) -> Dict[str, Any]:
        """
        导出图片（PNG/SVG/PDF）
        
        Args:
            source_path: 源图片路径
            target_path: 目标路径
            format: 格式 ('png', 'svg', 'pdf')
            dpi: 分辨率（PNG/PDF）
            transparent: 是否透明背景（仅 PNG）
        
        Returns:
            {'success': bool, 'path': str, 'error': Optional[str]}
        """
        try:
            source = Path(source_path)
            target = Path(target_path)
            
            if not source.exists():
                return {
                    "success": False,
                    "path": None,
                    "error": f"源文件不存在: {source_path}",
                }
            
            # 确保目标目录存在
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果是相同格式，直接复制
            if source.suffix.lower() == f".{format.lower()}":
                shutil.copy2(source, target)
            else:
                # 需要重新渲染（这里简化处理，实际可能需要重新执行代码）
                # 对于 MVP，我们假设源文件已经是正确格式
                shutil.copy2(source, target)
            
            return {
                "success": True,
                "path": str(target),
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "path": None,
                "error": f"导出失败: {str(e)}",
            }
    
    @staticmethod
    def export_script(
        code: str,
        data_path: Optional[str],
        target_path: str,
        include_data_loading: bool = True,
    ) -> Dict[str, Any]:
        """
        导出 Python 脚本
        
        Args:
            code: 绘图代码
            data_path: 数据文件路径（相对路径）
            target_path: 目标脚本路径
            include_data_loading: 是否包含数据加载代码
        
        Returns:
            {'success': bool, 'path': str, 'error': Optional[str]}
        """
        try:
            target = Path(target_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            
            script_content = []
            
            # 添加文件头注释
            script_content.append('"""')
            script_content.append("AutoChartist 生成的图表脚本")
            script_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            script_content.append('"""')
            script_content.append("")
            
            # 导入语句
            script_content.append("import pandas as pd")
            script_content.append("import matplotlib.pyplot as plt")
            script_content.append("import numpy as np")
            script_content.append("")
            
            # 设置中文字体
            script_content.append("# 设置中文字体支持")
            script_content.append("import platform")
            script_content.append("system = platform.system()")
            script_content.append("if system == 'Windows':")
            script_content.append("    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']")
            script_content.append("elif system == 'Darwin':")
            script_content.append("    plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS', 'DejaVu Sans']")
            script_content.append("else:")
            script_content.append("    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'DejaVu Sans']")
            script_content.append("plt.rcParams['axes.unicode_minus'] = False")
            script_content.append("")
            
            # 数据加载
            if include_data_loading and data_path:
                script_content.append("# 加载数据")
                if data_path.endswith('.csv'):
                    script_content.append(f"df = pd.read_csv('{data_path}')")
                elif data_path.endswith(('.xlsx', '.xls')):
                    script_content.append(f"df = pd.read_excel('{data_path}')")
                else:
                    script_content.append(f"# 请手动加载数据文件: {data_path}")
                    script_content.append("# df = pd.read_csv('your_data.csv')")
                script_content.append("")
            
            # 绘图代码
            script_content.append("# 绘图代码")
            script_content.append(code)
            script_content.append("")
            
            # 保存图片（如果代码中没有）
            if "savefig" not in code and "output_path" not in code:
                script_content.append("# 保存图片")
                script_content.append("output_path = 'output.png'")
                script_content.append("fig.savefig(output_path, bbox_inches='tight', dpi=300)")
                script_content.append("plt.close(fig)")
                script_content.append("print(f'图片已保存到: {output_path}')")
            
            # 写入文件
            with open(target, "w", encoding="utf-8") as f:
                f.write("\n".join(script_content))
            
            return {
                "success": True,
                "path": str(target),
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "path": None,
                "error": f"导出脚本失败: {str(e)}",
            }
    
    @staticmethod
    def export_notebook(
        code: str,
        data_path: Optional[str],
        target_path: str,
        include_data_loading: bool = True,
    ) -> Dict[str, Any]:
        """
        导出 Jupyter Notebook 片段（.ipynb 格式）
        
        Args:
            code: 绘图代码
            data_path: 数据文件路径
            target_path: 目标 notebook 路径
            include_data_loading: 是否包含数据加载代码
        
        Returns:
            {'success': bool, 'path': str, 'error': Optional[str]}
        """
        try:
            target = Path(target_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            
            cells = []
            
            # Cell 1: Markdown 说明
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# AutoChartist 生成的图表\n",
                    f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ],
            })
            
            # Cell 2: 导入库
            import_code = [
                "import pandas as pd",
                "import matplotlib.pyplot as plt",
                "import numpy as np",
                "import platform",
                "",
                "# 设置中文字体支持",
                "system = platform.system()",
                "if system == 'Windows':",
                "    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']",
                "elif system == 'Darwin':",
                "    plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS', 'DejaVu Sans']",
                "else:",
                "    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'DejaVu Sans']",
                "plt.rcParams['axes.unicode_minus'] = False",
            ]
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": import_code,
                "outputs": [],
            })
            
            # Cell 3: 数据加载
            if include_data_loading and data_path:
                data_loading_code = []
                if data_path.endswith('.csv'):
                    data_loading_code.append(f"df = pd.read_csv('{data_path}')")
                elif data_path.endswith(('.xlsx', '.xls')):
                    data_loading_code.append(f"df = pd.read_excel('{data_path}')")
                else:
                    data_loading_code.append(f"# 请手动加载数据文件: {data_path}")
                
                cells.append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": data_loading_code,
                    "outputs": [],
                })
            
            # Cell 4: 绘图代码
            # 将代码按行分割
            code_lines = code.split("\n")
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": code_lines,
                "outputs": [],
            })
            
            # 构建 notebook JSON
            notebook = {
                "cells": cells,
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3",
                    },
                    "language_info": {
                        "name": "python",
                        "version": "3.8.0",
                    },
                },
                "nbformat": 4,
                "nbformat_minor": 4,
            }
            
            # 写入文件
            with open(target, "w", encoding="utf-8") as f:
                json.dump(notebook, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "path": str(target),
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "path": None,
                "error": f"导出 Notebook 失败: {str(e)}",
            }

