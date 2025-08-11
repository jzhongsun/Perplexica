import pandas as pd


def format_pd_dataframe_to_markdown(
    df: pd.DataFrame, name: str = None, include_index: bool = False
) -> str:
    """Format a pandas dataframe to markdown"""
    if name and len(name.strip()) > 0:
        return f"{name}\n{df.to_markdown(index=include_index)}"
    else:
        return df.to_markdown(index=include_index)
