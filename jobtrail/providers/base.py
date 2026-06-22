from __future__ import annotations

from abc import ABC, abstractmethod

from jobtrail.schemas import ProviderMessage


class MailProvider(ABC):
    @abstractmethod
    def search_messages(self) -> list[ProviderMessage]: ...

    @abstractmethod
    def label_threads(self, thread_labels: dict[str, str], dry_run: bool = True) -> list[str]: ...
