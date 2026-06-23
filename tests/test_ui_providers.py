import inspect

from jobtrail.ui.pages import providers


def test_providers_ui_includes_gmail_imap_copy() -> None:
    source = inspect.getsource(providers.render)
    assert "Gmail IMAP (App Password)" in source
    assert "Labels are only supported by the Gmail API provider for now." in source
