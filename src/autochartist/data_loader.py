"""数据加载工具：支持 CSV/Excel 文件加载"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union


def load_data_file(file_path: Union[str, Path]) -> Optional[pd.DataFrame]:
    """
    加载数据文件（CSV 或 Excel）
    
    Args:
        file_path: 文件路径
    
    Returns:
        DataFrame 或 None（如果加载失败）
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    try:
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")
        
        return df
    except Exception as e:
        raise RuntimeError(f"加载文件失败: {str(e)}") from e

