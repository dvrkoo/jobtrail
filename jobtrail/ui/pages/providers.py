from __future__ import annotations

import streamlit as st

from jobtrail.db import session
from jobtrail.models import ProviderAccount
from jobtrail.providers.gmail_imap import password_env_var, store_password
from jobtrail.services.providers import add_provider_account, set_enabled, set_labels_enabled, set_provider_window
from jobtrail.services.sync import sync_provider_account
from jobtrail.ui.state import provider_rows


def render() -> None:
    st.header("Providers")
    with session() as db:
        rows = provider_rows(db)
        st.dataframe(rows, width="stretch")
        with st.form("add-provider"):
            provider = st.selectbox("Provider", ["gmail_imap", "gmail", "outlook"], format_func=lambda value: {"gmail_imap": "Gmail IMAP (App Password)", "gmail": "Gmail API OAuth", "outlook": "Outlook (planned)"}[value])
            email = st.text_input("Account email")
            window = st.selectbox("Sync window", ["last 30 days", "last 90 days", "last 6 months", "last 12 months", "last 24 months", "all available"])
            labels = False if provider == "gmail_imap" else st.checkbox("Labels enabled")
            password = st.text_input("Google App Password", type="password") if provider == "gmail_imap" else ""
            if st.form_submit_button("Add provider") and email:
                add_provider_account(db, provider, email, labels_enabled=labels, sync_choice=window)
                if provider == "outlook":
                    st.warning("Outlook is configured as a stub. Sync is not implemented yet.")
                elif provider == "gmail_imap":
                    if password and store_password(email, password):
                        st.info("App Password stored in system keyring.")
                    elif password:
                        st.warning(f"Keyring unavailable. Set {password_env_var(email)} before syncing.")
                    else:
                        st.info(f"Set {password_env_var(email)} before syncing.")
                    st.caption("Labels are only supported by the Gmail API provider for now.")
                else:
                    st.info("Gmail OAuth starts on sync. If credentials are missing, add credentials.json and run jobtrail sync.")
                st.rerun()
        selected = st.number_input("Provider account ID", min_value=1, step=1)
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("Enable"):
            set_enabled(db, int(selected), True)
            st.rerun()
        if c2.button("Disable"):
            set_enabled(db, int(selected), False)
            st.rerun()
        if c3.button("Toggle labels"):
            account = db.get(ProviderAccount, int(selected))
            if account:
                set_labels_enabled(db, int(selected), not account.labels_enabled)
                st.rerun()
        if c4.button("Sync selected"):
            account = db.get(ProviderAccount, int(selected))
            if account:
                summary = sync_provider_account(db, account)
                if summary.error:
                    st.error(summary.error)
                else:
                    st.success(f"Detected {summary.events_detected} events")
        mode = st.selectbox("Edit selected sync window", ["relative", "absolute", "all"])
        relative_window = st.selectbox("Relative window", ["last 30 days", "last 90 days", "last 6 months", "last 12 months", "last 24 months"], disabled=mode != "relative")
        start = st.date_input("Start date", disabled=mode != "absolute")
        end = st.date_input("End date", disabled=mode != "absolute")
        if st.button("Save sync window"):
            if mode == "all":
                set_provider_window(db, int(selected), all_available=True)
            elif mode == "absolute":
                set_provider_window(db, int(selected), start=start, end=end)
            else:
                parts = relative_window.removeprefix("last ").split()
                set_provider_window(db, int(selected), relative=int(parts[0]), unit=parts[1])
            st.rerun()
