from __future__ import annotations

import streamlit as st

from jobtrail.db import session
from jobtrail.models import Status
from jobtrail.services.applications import set_archived
from jobtrail.ui.state import followup_rows


def render() -> None:
    st.header("Followups")
    include_all = st.checkbox("Show all active applications")
    include_archived = st.checkbox("Include archived")
    days = st.number_input("Override stale-days threshold", min_value=0, value=0)
    status_value = st.selectbox("Status", ["all"] + [item.value for item in Status])
    with session() as db:
        rows = followup_rows(
            db,
            include_all=include_all,
            include_archived=include_archived,
            status=None if status_value == "all" else Status(status_value),
            days=None if days == 0 else int(days),
        )
        st.dataframe(rows, width="stretch")
        if rows:
            markdown = "| ID | Company | Role | Status | Days | Action |\n|---:|---|---|---|---:|---|\n"
            markdown += "\n".join(f"| {row['id']} | {row['company']} | {row['role']} | {row['status']} | {row['days_stale']} | {row['suggested_action']} |" for row in rows)
            st.text_area("Markdown", markdown, height=180)
        app_id = st.number_input("Archive application ID", min_value=1, step=1)
        if st.button("Archive selected"):
            set_archived(db, int(app_id), True)
            st.rerun()
