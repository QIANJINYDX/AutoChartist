"""代码执行与渲染模块：安全执行生成的代码并生成图表"""

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import warnings
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import hashlib

from .platform import get_output_dir, get_chart_font


class CodeRenderer:
    """代码渲染器：安全执行代码并生成图表"""
    
    def __init__(self):
        # 使用项目输出目录而不是临时目录
        self.output_dir = get_output_dir()
        
        # 设置 matplotlib 默认参数（支持中文）
        font_list = get_chart_font()
        plt.rcParams['font.sans-serif'] = font_list
        plt.rcParams['axes.unicode_minus'] = False
        
        # 清除字体缓存，确保使用新字体
        try:
            import matplotlib.font_manager
            matplotlib.font_manager._rebuild()
        except Exception:
            pass  # 如果重建失败，继续使用现有字体
    
    def render_code(
        self,
        code: str,
        df: pd.DataFrame,
        output_format: str = "png",  # 支持 'png', 'svg', 'pdf'
        dpi: int = 200,
        transparent: bool = False,
    ) -> Dict[str, Any]:
        """
        执行代码并渲染图表
        
        Args:
            code: 要执行的 Python 代码
            df: 数据 DataFrame
            output_format: 输出格式 ('png', 'svg')
            dpi: 分辨率
            transparent: 是否透明背景
        
        Returns:
            {
                'success': bool,
                'output_path': Optional[str],
                'error': Optional[str],
                'warnings': List[str]
            }
        """
        # 生成有意义的文件名（基于时间戳和代码哈希）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        code_hash = hashlib.md5(code.encode('utf-8')).hexdigest()[:8]
        filename = f"chart_{timestamp}_{code_hash}.{output_format}"
        output_path = str(self.output_dir / filename)
        
        # 准备安全的执行环境
        safe_globals = self._create_safe_globals()
        safe_globals['df'] = df.copy()
        safe_globals['output_path'] = output_path
        
        # 确保字体设置正确（在执行代码前）
        font_list = get_chart_font()
        plt.rcParams['font.sans-serif'] = font_list
        plt.rcParams['axes.unicode_minus'] = False
        
        # 捕获警告和错误
        warnings_list = []
        error_message = None
        
        try:
            # 捕获 stdout 和 stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    
                    # 执行代码
                    exec(code, safe_globals)
                    
                    # 收集警告
                    for warning in w:
                        warnings_list.append(str(warning.message))
            
            # 检查是否生成了 fig
            fig = safe_globals.get('fig')
            ax = safe_globals.get('ax')
            
            if fig is None:
                # 尝试从全局获取
                if 'fig' in globals():
                    fig = globals()['fig']
                else:
                    raise RuntimeError("代码执行后未生成 fig 对象。请确保代码中包含 'fig, ax = plt.subplots(...)' 或类似语句。")
            
            # 保存图片（支持 PNG、SVG、PDF）
            if output_format.lower() == 'pdf':
                fig.savefig(
                    output_path,
                    format='pdf',
                    bbox_inches='tight',
                    dpi=dpi,
                )
            elif output_format.lower() == 'svg':
                fig.savefig(
                    output_path,
                    format='svg',
                    bbox_inches='tight',
                )
            else:  # PNG
                fig.savefig(
                    output_path,
                    format=output_format,
                    bbox_inches='tight',
                    dpi=dpi,
                    transparent=transparent,
                )
            
            # 清理
            plt.close(fig)
            
            # 检查输出文件是否存在
            if not Path(output_path).exists():
                raise RuntimeError("图片文件未成功生成")
            
            return {
                "success": True,
                "output_path": output_path,
                "error": None,
                "warnings": warnings_list,
            }
            
        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e)}"
            error_traceback = traceback.format_exc()
            
            # 清理可能创建的临时文件
            if Path(output_path).exists():
                try:
                    Path(output_path).unlink()
                except Exception:
                    pass
            
            return {
                "success": False,
                "output_path": None,
                "error": error_message,
                "error_traceback": error_traceback,
                "warnings": warnings_list,
            }
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """创建安全的全局命名空间"""
        import builtins
        
        # 允许导入的模块白名单
        ALLOWED_MODULES = {'pandas', 'numpy', 'matplotlib', 'pd', 'np', 'plt'}
        
        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            """安全的导入函数，只允许导入白名单中的模块"""
            # 处理 from ... import ... 的情况
            if fromlist:
                module_name = name
            else:
                module_name = name.split('.')[0]
            
            # 检查是否在允许列表中
            if module_name in ALLOWED_MODULES or module_name in ['pandas', 'numpy', 'matplotlib']:
                return builtins.__import__(name, globals, locals, fromlist, level)
            else:
                raise ImportError(f"不允许导入模块: {name}")
        
        # 创建受限的 builtins
        restricted_builtins = {
            # 基本内置函数
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'min': min,
            'max': max,
            'sum': sum,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'print': print,
            'type': type,
            'isinstance': isinstance,
            'hasattr': hasattr,
            'getattr': getattr,
            'setattr': setattr,
            'iter': iter,
            'next': next,
            'reversed': reversed,
            'all': all,
            'any': any,
            'filter': filter,
            'map': map,
            # 允许导入（但受限制）
            '__import__': safe_import,
            # 其他安全的内置函数
            'ValueError': ValueError,
            'TypeError': TypeError,
            'KeyError': KeyError,
            'IndexError': IndexError,
        }
        
        safe_globals = {
            '__builtins__': restricted_builtins,
            # 预导入的库（避免需要 import）
            'pd': pd,
            'np': np,
            'plt': plt,
            'matplotlib': matplotlib,
            'pandas': pd,
            'numpy': np,
        }
        
        # 添加一些常用的 matplotlib 函数和类
        safe_globals.update({
            'Figure': matplotlib.figure.Figure,
            'Axes': matplotlib.axes.Axes,
        })
        
        return safe_globals
    
    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        验证代码语法（不执行）
        
        Returns:
            (is_valid, error_message)
        """
        try:
            compile(code, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"语法错误: {str(e)} (行 {e.lineno})"
        except Exception as e:
            return False, f"代码验证失败: {str(e)}"

