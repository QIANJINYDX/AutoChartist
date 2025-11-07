"""数据理解模块：类型推断、缺失值检测、异常检测"""

import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype, is_datetime64_any_dtype, is_string_dtype
from typing import Dict, List, Any, Optional
import warnings


def profile_df(df: pd.DataFrame, sample_size: int = 5000) -> Dict[str, Any]:
    """
    对 DataFrame 进行全面的数据体检
    
    Args:
        df: 输入的 DataFrame
        sample_size: 采样行数（用于类型推断）
    
    Returns:
        包含字段信息、统计信息、异常检测结果的字典
    """
    if df.empty:
        return {
            "rows": 0,
            "cols": 0,
            "schema": [],
            "warnings": ["数据框为空"],
        }
    
    # 采样数据用于分析（如果数据量太大）
    sample_df = df.head(sample_size) if len(df) > sample_size else df
    
    schema = []
    warnings_list = []
    
    # 检查重复列名
    if len(df.columns) != len(set(df.columns)):
        warnings_list.append("存在重复的列名")
    
    for col in df.columns:
        s = df[col]
        
        # 检测空列
        if s.isna().all():
            warnings_list.append(f"列 '{col}' 完全为空")
            schema.append({
                "name": col,
                "dtype": "empty",
                "n_missing": len(s),
                "missing_pct": 100.0,
                "sample": [],
            })
            continue
        
        # 类型推断
        dtype = infer_dtype(s, sample_df[col])
        
        # 缺失值统计
        n_missing = int(s.isna().sum())
        missing_pct = (n_missing / len(s)) * 100
        
        # 采样数据（非空值）
        sample_values = s.dropna().head(5).tolist()
        # 转换 numpy 类型为 Python 原生类型
        sample_values = [convert_to_python_type(v) for v in sample_values]
        
        col_info = {
            "name": col,
            "dtype": dtype,
            "n_missing": n_missing,
            "missing_pct": round(missing_pct, 2),
            "sample": sample_values,
        }
        
        # 数值列的统计信息
        if dtype == "numeric":
            numeric_col = pd.to_numeric(s, errors="coerce")
            col_info["stats"] = {
                "min": float(numeric_col.min()) if not pd.isna(numeric_col.min()) else None,
                "max": float(numeric_col.max()) if not pd.isna(numeric_col.max()) else None,
                "mean": float(numeric_col.mean()) if not pd.isna(numeric_col.mean()) else None,
                "median": float(numeric_col.median()) if not pd.isna(numeric_col.median()) else None,
                "std": float(numeric_col.std()) if not pd.isna(numeric_col.std()) else None,
            }
            # 检测离群点（IQR 方法）
            q1 = numeric_col.quantile(0.25)
            q3 = numeric_col.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = ((numeric_col < lower_bound) | (numeric_col > upper_bound)).sum()
                if outliers > 0:
                    col_info["outliers"] = int(outliers)
                    warnings_list.append(f"列 '{col}' 检测到 {outliers} 个离群点")
        
        # 分类列的统计信息
        elif dtype == "categorical":
            value_counts = s.value_counts()
            col_info["n_unique"] = int(s.nunique())
            col_info["top_values"] = value_counts.head(5).to_dict()
            if s.nunique() > 100:
                warnings_list.append(f"列 '{col}' 唯一值过多 ({s.nunique()})，可能不适合作为分类变量")
        
        # 时间列的统计信息
        elif dtype == "datetime":
            try:
                datetime_col = pd.to_datetime(s, errors="coerce")
                col_info["date_range"] = {
                    "min": str(datetime_col.min()) if not pd.isna(datetime_col.min()) else None,
                    "max": str(datetime_col.max()) if not pd.isna(datetime_col.max()) else None,
                }
            except Exception:
                pass
        
        schema.append(col_info)
    
    return {
        "rows": len(df),
        "cols": len(df.columns),
        "schema": schema,
        "warnings": warnings_list,
        "sample_data": df.head(100).to_dict("records") if len(df) > 0 else [],
    }


def infer_dtype(series: pd.Series, sample_series: Optional[pd.Series] = None) -> str:
    """
    推断列的数据类型
    
    Returns:
        'numeric', 'datetime', 'categorical', 'empty'
    """
    if sample_series is None:
        sample_series = series
    
    # 检查是否为空
    if series.isna().all():
        return "empty"
    
    # 尝试识别时间类型
    if is_datetime64_any_dtype(series):
        return "datetime"
    
    # 尝试转换为时间类型（如果看起来像时间）
    non_null = sample_series.dropna()
    if len(non_null) > 0:
        try:
            # 采样检查前几个值是否像时间
            test_values = non_null.head(10).astype(str)
            if any(
                any(char in str(v) for char in ["-", "/", ":", "T", "Z"])
                for v in test_values
            ):
                # 使用 warnings 捕获来避免警告
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    try:
                        # 尝试解析日期，如果成功则认为是日期类型
                        pd.to_datetime(non_null.head(5), errors="raise", infer_datetime_format=False)
                        return "datetime"
                    except (ValueError, TypeError, pd.errors.ParserError):
                        pass
        except (ValueError, TypeError, pd.errors.ParserError):
            pass
    
    # 检查是否为数值类型
    if is_numeric_dtype(series):
        return "numeric"
    
    # 尝试转换为数值类型
    try:
        numeric_series = pd.to_numeric(sample_series, errors="coerce")
        if numeric_series.notna().sum() / len(sample_series) > 0.8:  # 80% 以上可以转换为数值
            return "numeric"
    except Exception:
        pass
    
    # 默认为分类/字符串类型
    return "categorical"


def convert_to_python_type(value: Any) -> Any:
    """将 numpy/pandas 类型转换为 Python 原生类型"""
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer, np.floating)):
        return float(value) if isinstance(value, np.floating) else int(value)
    if isinstance(value, pd.Timestamp):
        return str(value)
    return value


def suggest_chart_types(schema: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    根据数据模式建议图表类型
    
    Returns:
        建议的图表类型列表，每个包含 type, description, reason
    """
    suggestions = []
    
    numeric_cols = [col for col in schema if col["dtype"] == "numeric"]
    datetime_cols = [col for col in schema if col["dtype"] == "datetime"]
    categorical_cols = [col for col in schema if col["dtype"] == "categorical"]
    
    # 时间序列图
    if len(datetime_cols) >= 1 and len(numeric_cols) >= 1:
        suggestions.append({
            "type": "line",
            "description": "时间序列折线图",
            "reason": f"检测到时间列和数值列，适合展示趋势变化",
        })
        suggestions.append({
            "type": "area",
            "description": "时间序列面积图",
            "reason": f"展示时间序列的累积效果",
        })
    
    # 单变量分布
    if len(numeric_cols) >= 1:
        suggestions.append({
            "type": "hist",
            "description": "直方图",
            "reason": f"展示 {numeric_cols[0]['name']} 的分布",
        })
        suggestions.append({
            "type": "box",
            "description": "箱线图",
            "reason": f"展示 {numeric_cols[0]['name']} 的统计分布",
        })
    
    # 分类 vs 数值
    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        suggestions.append({
            "type": "bar",
            "description": "条形图",
            "reason": f"对比不同类别的数值",
        })
    
    # 双变量关系
    if len(numeric_cols) >= 2:
        suggestions.append({
            "type": "scatter",
            "description": "散点图",
            "reason": f"探索 {numeric_cols[0]['name']} 与 {numeric_cols[1]['name']} 的关系",
        })
        suggestions.append({
            "type": "heatmap",
            "description": "相关系数热力图",
            "reason": f"展示多个数值变量之间的相关性",
        })
    
    return suggestions[:5]  # 最多返回 5 个建议

