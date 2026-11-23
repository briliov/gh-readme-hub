from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class IconResult:
    provider: str
    data_uri: str
    source_file: str
    color: str


class IconProvider(ABC):
    name: str

    @abstractmethod
    def fetch(self, topic: str, brand_colors: dict[str, str]) -> IconResult | None:
        """Fetch and process an icon for the given topic."""
