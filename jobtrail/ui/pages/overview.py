from __future__ import annotations

import streamlit as st

from jobtrail.db import session
from jobtrail.ui.state import export_action, overview


def render() -> None:
    st.header("Daily command center")
    with session() as db:
        data = overview(db)
        cols = st.columns(5)
        for col, key in zip(cols, ["total", "active", "followups_due", "interviews", "rejected"], strict=False):
            col.metric(key.replace("_", " ").title(), data.get(key, 0))
        st.subheader("Top followups")
        st.write(data.get("top_followups") or ["No followups due"])
        st.subheader("Recent applications")
        st.dataframe(data.get("recent_applications", []), width="stretch")
        if st.button("Export Excel"):
            _, path = export_action(db, "xlsx")
            st.success(f"Exported {path}")
        if st.button("Export LaTeX"):
            kind, text = export_action(db, "latex")
            if kind == "text":
                st.code(text)
