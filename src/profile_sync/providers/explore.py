from __future__ import annotations

import base64
from io import BytesIO
import logging
import urllib.error
import urllib.request

from PIL import Image

from profile_sync.config import EXPLORE_RAW_URL, ICON_SIZE
from profile_sync.providers.base import IconProvider, IconResult

logger = logging.getLogger(__name__)


class ExploreProvider(IconProvider):
    name = 'Explore'

    def fetch(
        self, topic: str, brand_colors: dict[str, str]
    ) -> IconResult | None:
        url = f'{EXPLORE_RAW_URL}/{topic}/{topic}.png'
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status != 200:
                    return None
                with Image.open(BytesIO(response.read())) as img:
                    resized = img.convert('RGBA').resize(
                        ICON_SIZE, Image.Resampling.LANCZOS
                    )
                    buffer = BytesIO()
                    resized.save(buffer, format='PNG', optimize=True)
                    encoded = base64.b64encode(buffer.getvalue()).decode(
                        'ascii'
                    )
                    return IconResult(
                        self.name,
                        f'data:image/png;base64,{encoded}',
                        f'{topic}.png',
                        'Original PNG',
                    )
        except urllib.error.HTTPError:
            return None
        except Exception as exc:
            logger.warning(
                'Error processing GitHub Explore icon for %s: %s', topic, exc
            )
        return None
