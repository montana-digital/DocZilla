"""
Table Components

Reusable table and data display components with Streamlit fragments for performance.
"""

import streamlit as st
import pandas as pd
from typing import Optional


@st.fragment
def render_data_table(df: pd.DataFrame, max_rows: int = 1000, key: Optional[str] = None):
    """
    Render data table with pagination for large datasets.
    Uses @st.fragment to prevent unnecessary reruns.
    
    Args:
        df: DataFrame to display
        max_rows: Maximum rows to display (default: 1000)
        key: Optional key for widget state
    """
    if len(df) > max_rows:
        st.dataframe(df.head(max_rows), use_container_width=True)
        st.caption(f"Showing first {max_rows} of {len(df)} rows. Use slider to adjust.")
        
        # Slider to adjust display range
        start_row = st.slider(
            "Start row",
            min_value=0,
            max_value=len(df) - 1,
            value=0,
            step=100,
            key=f"{key}_start" if key else None
        )
        
        end_row = min(start_row + max_rows, len(df))
        st.dataframe(df.iloc[start_row:end_row], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)


def render_data_editor(
    df: pd.DataFrame,
    num_rows: Optional[str] = "dynamic",
    key: Optional[str] = None
):
    """
    Render editable data table using st.data_editor.
    
    Args:
        df: DataFrame to display
        num_rows: Number of rows ("dynamic", "fixed", or int)
        key: Optional key for widget state
    
    Returns:
        Edited DataFrame or None
    """
    edited_df = st.data_editor(
        df,
        num_rows=num_rows,
        use_container_width=True,
        key=key
    )
    
    return edited_df if edited_df is not None else df

