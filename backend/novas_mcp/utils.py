import pandas as pd


def format_pd_dataframe_to_markdown(
    df: pd.DataFrame, name: str = None, include_index: bool = False, transpose: bool = False, column_mapping: dict[str, str] = {}
) -> str:
    """Format a pandas dataframe to markdown
    
    Args:
        df: The pandas dataframe to format
        name: Optional name/title for the dataframe
        include_index: Whether to include the index in the markdown output
        transpose: Whether to transpose the dataframe before formatting
        column_mapping: A dictionary of column names to rename
    """
    def format_number(x):
        """根据数值大小格式化数字"""
        if pd.isna(x):
            return "-"
        
        try:
            x = float(x)
        except (ValueError, TypeError):
            return str(x)
        
        abs_x = abs(x)
        if abs_x >= 1e8:  # 1亿及以上
            return f"{x/1e8:.2f}亿"
        elif abs_x >= 1e4:  # 1万及以上
            return f"{x/1e4:.2f}万"
        elif abs_x == 0:
            return "0"
        elif abs_x < 0.0001:  # 极小数值
            return f"{x:.4e}"  # 科学计数法
        else:
            return f"{x:.4f}".rstrip('0').rstrip('.') if '.' in f"{x:.4f}" else f"{x:.4f}"    
    formatted_df = df.copy()
    # 对数值列应用格式化
    for col in formatted_df.columns:
        if pd.api.types.is_numeric_dtype(formatted_df[col]):
            formatted_df[col] = formatted_df[col].apply(format_number)
    
    if column_mapping:
        formatted_df = formatted_df.rename(columns=column_mapping)
        
    if transpose:
        formatted_df = formatted_df.T
    
    if name and len(name.strip()) > 0:
        return f"{name}\n{formatted_df.to_markdown(index=include_index, tablefmt="github")}"
    else:
        return formatted_df.to_markdown(index=include_index, tablefmt="github")
