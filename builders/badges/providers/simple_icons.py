from __future__ import annotations

import logging
import urllib.error
import urllib.request

from profile_sync.config import SIMPLE_ICONS_URL
from profile_sync.providers.base import IconProvider, IconResult
from profile_sync.svg_builder import colorize_svg

logger = logging.getLogger(__name__)


class SimpleIconsProvider(IconProvider):
    name = 'SimpleIcons'

    def fetch(
        self, topic: str, brand_colors: dict[str, str]
    ) -> IconResult | None:
        clean_name = topic.replace('-', '')
        target_color = brand_colors.get(clean_name, '#ffffff')
        url = f'{SIMPLE_ICONS_URL}/{clean_name}.svg'
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    data_uri = colorize_svg(response.read(), target_color)
                    return IconResult(
                        self.name, data_uri, f'{clean_name}.svg', target_color
                    )
        except urllib.error.HTTPError:
            return None
        except Exception as exc:
            logger.warning('Error fetching SimpleIcon for %s: %s', topic, exc)
        return None
