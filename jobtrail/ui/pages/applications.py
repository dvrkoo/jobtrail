from __future__ import annotations

import streamlit as st

from jobtrail.db import session
from jobtrail.models import Application, Status
from jobtrail.services.applications import set_archived, update_application
from jobtrail.ui.state import filtered_applications


def render() -> None:
    st.header("Applications")
    status_value = st.selectbox("Status", ["all"] + [item.value for item in Status])
    archived = st.selectbox("Archived", ["active", "archived", "all"])
    company = st.text_input("Company search")
    role = st.text_input("Role search")
    with session() as db:
        rows = filtered_applications(
            db,
            status=None if status_value == "all" else Status(status_value),
            archived=False if archived == "active" else True if archived == "archived" else None,
            company=company,
            role=role,
        )
        st.dataframe(rows, width="stretch")
        app_id = st.number_input("Application ID", min_value=1, step=1)
        app = db.get(Application, int(app_id))
        if app:
            with st.form("edit-app"):
                new_company = st.text_input("Company", app.company)
                new_role = st.text_input("Role", app.role)
                new_status = st.selectbox("Status", [item.value for item in Status], index=[item.value for item in Status].index(app.status.value))
                notes = st.text_area("Notes", app.notes or "")
                archived_value = st.checkbox("Archived", app.archived)
                verified = st.checkbox("Manually verified", app.manually_verified)
                if st.form_submit_button("Save"):
                    update_application(db, app.id, company=new_company, role=new_role, status=new_status, notes=notes)
                    app.manually_verified = verified or app.manually_verified
                    app.archived = archived_value
                    db.add(app)
                    db.commit()
                    st.success("Saved")
                    st.rerun()
            if st.button("Archive" if not app.archived else "Unarchive"):
                set_archived(db, app.id, not app.archived)
                st.rerun()
