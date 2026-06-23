from __future__ import annotations

import streamlit as st

from jobtrail.config import init_config
from jobtrail.db import init_db
from jobtrail.ui.components.messages import demo_mode
from jobtrail.ui.pages import applications, exports, followups, overview, providers, settings


PAGES = {
    "Overview": overview.render,
    "Providers": providers.render,
    "Applications": applications.render,
    "Followups": followups.render,
    "Exports": exports.render,
    "Settings": settings.render,
}


def main() -> None:
    init_config()
    init_db()
    st.set_page_config(page_title="JobTrail", layout="wide")
    st.title("JobTrail")
    if demo_mode():
        st.warning("Demo mode: sample data only. No real email account is connected.")
    page = st.sidebar.radio("Page", list(PAGES))
    PAGES[page]()


if __name__ == "__main__":
    main()
