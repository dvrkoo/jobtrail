from __future__ import annotations

import streamlit as st

from jobtrail.config import settings
from jobtrail.db import session
from jobtrail.models import Status
from jobtrail.ui.state import export_action


def render() -> None:
    st.header("Exports")
    st.write(f"Output directory: {settings().data_dir / 'exports'}")
    fmt = st.selectbox("Format", ["csv", "markdown", "xlsx", "latex", "all"])
    status_value = st.selectbox("Status", ["all"] + [item.value for item in Status])
    if st.button("Generate export"):
        with session() as db:
            kind, value = export_action(db, fmt, None if status_value == "all" else Status(status_value))
        if kind == "text":
            st.code(value)
        else:
            st.success(f"Generated: {value}")
