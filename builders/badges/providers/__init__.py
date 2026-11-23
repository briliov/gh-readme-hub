from __future__ import annotations

from profile_sync.config import PROVIDER_ORDER
from profile_sync.providers.base import IconProvider, IconResult
from profile_sync.providers.custom import CustomProvider
from profile_sync.providers.devicon import DeviconProvider
from profile_sync.providers.explore import ExploreProvider
from profile_sync.providers.simple_icons import SimpleIconsProvider

_REGISTRY: dict[str, type[IconProvider]] = {
    CustomProvider.name: CustomProvider,
    DeviconProvider.name: DeviconProvider,
    SimpleIconsProvider.name: SimpleIconsProvider,
    ExploreProvider.name: ExploreProvider,
}


def build_pipeline() -> list[IconProvider]:
    """Instantiate active providers in the order specified in config."""
    return [_REGISTRY[name]() for name in PROVIDER_ORDER if name in _REGISTRY]


def resolve_icon_info(
    topic: str,
    brand_colors: dict[str, str],
    pipeline: list[IconProvider],
) -> IconResult | None:
    """Run topic through the configured provider chain."""
    for provider in pipeline:
        result = provider.fetch(topic, brand_colors)
        if result:
            return result
    return None
