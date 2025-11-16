"""
Activity Log Component

Display and filter structured CSV logs.
"""

import streamlit as st
from pathlib import Path
import pandas as pd
from typing import Optional, List


def render_activity_log(logs_dir: str | Path = "logs"):
    """
    Render activity log viewer with filters.

    Args:
        logs_dir: Directory containing CSV logs
    """
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        st.info("Logs directory not found")
        return

    files = sorted(logs_path.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        st.info("No log files yet")
        return

    sel = st.selectbox("Log file", [p.name for p in files])
    path = logs_path / sel

    try:
        df = pd.read_csv(path)
    except Exception:
        st.error("Failed to read log CSV")
        return

    # Normalize expected columns
    # Expected: timestamp, level, module, request_id, operation, message
    for col in ["timestamp", "level", "module", "request_id", "operation", "message"]:
        if col not in df.columns:
            df[col] = ""

    with st.expander("Filters", expanded=False):
        cols1 = st.columns(3)
        with cols1[0]:
            lvl = st.multiselect("Level", sorted(df["level"].astype(str).unique().tolist()))
        with cols1[1]:
            mod = st.multiselect("Module", sorted(df["module"].astype(str).unique().tolist()))
        with cols1[2]:
            op = st.multiselect("Operation", sorted(df["operation"].astype(str).unique().tolist()))
        q = st.text_input("Search text")

    filt = df
    if lvl:
        filt = filt[filt["level"].astype(str).isin(lvl)]
    if mod:
        filt = filt[filt["module"].astype(str).isin(mod)]
    if op:
        filt = filt[filt["operation"].astype(str).isin(op)]
    if q:
        mask = (
            filt["message"].astype(str).str.contains(q, case=False, na=False)
            | filt["module"].astype(str).str.contains(q, case=False, na=False)
            | filt["operation"].astype(str).str.contains(q, case=False, na=False)
        )
        filt = filt[mask]

    st.dataframe(
        filt[["timestamp", "level", "module", "operation", "message", "request_id"]].tail(1000),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download filtered CSV",
        data=filt.to_csv(index=False).encode("utf-8"),
        file_name=f"filtered_{sel}",
        mime="text/csv",
    )

