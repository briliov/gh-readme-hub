from __future__ import annotations

from profile_sync.config import CUSTOM_ICONS_DIR
from profile_sync.providers.base import IconProvider, IconResult
from profile_sync.svg_builder import colorize_svg


class CustomProvider(IconProvider):
    name = 'Custom'

    def fetch(self, topic: str, brand_colors: dict[str, str]) -> IconResult | None:
        custom_path = CUSTOM_ICONS_DIR / f'{topic}.svg'
        if custom_path.is_file():
            clean_name = topic.replace('-', '')
            target_color = brand_colors.get(clean_name, '#ffffff')
            data_uri = colorize_svg(custom_path.read_bytes(), target_color)
            return IconResult(self.name, data_uri, f'custom_icons/{topic}.svg', target_color)
        return None
