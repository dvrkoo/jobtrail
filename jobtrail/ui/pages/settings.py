from __future__ import annotations

import streamlit as st

from jobtrail.config import update_config
from jobtrail.db import session
from jobtrail.services.backup import export_backup
from jobtrail.ui.state import config_summary


def render() -> None:
    st.header("Settings")
    data = config_summary()
    st.write(f"Config: {data['config_path']}")
    st.write(f"Data: {data['data_path']}")
    st.write(f"Tokens: {data['token_path']}")
    st.info("JobTrail is local-first. Backups do not include OAuth tokens or credentials.")
    with st.form("settings"):
        name = st.text_input("Display name", str(data["display_name"]))
        greetings = st.checkbox("Motivational greetings", bool(data["motivational_greetings_enabled"]))
        tone = st.selectbox("Tone", ["calm", "aggressive", "funny", "professional"], index=["calm", "aggressive", "funny", "professional"].index(str(data["motivational_tone"])))
        ghosting = st.number_input("Ghosting threshold days", min_value=1, value=int(data["ghosting_threshold_days"]))
        default_export = st.selectbox("Default export", ["csv", "markdown"], index=["csv", "markdown"].index(str(data["default_export_format"])))
        if st.form_submit_button("Save settings"):
            update_config(
                display_name=name,
                motivational_greetings_enabled=greetings,
                motivational_tone=tone,
                ghosting_threshold_days=int(ghosting),
                default_export_format=default_export,
            )
            st.success("Saved")
    if st.button("Export backup"):
        path = data["data_path"].parent / "backups" / "jobtrail-ui-backup.json"
        with session() as db:
            export_backup(db, path)
        st.success(f"Backup written: {path}")
