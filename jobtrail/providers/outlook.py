from __future__ import annotations

from jobtrail.providers.base import MailProvider
from jobtrail.schemas import ProviderMessage


class OutlookProvider(MailProvider):
    def search_messages(self, window_query: str | None = None) -> list[ProviderMessage]:
        raise NotImplementedError("Outlook/Microsoft Graph is a v0.2 stub")

    def label_threads(self, thread_labels: dict[str, str], dry_run: bool = True) -> list[str]:
        raise NotImplementedError("Outlook labeling is a v0.2 stub")
