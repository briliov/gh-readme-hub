from __future__ import annotations

import os
from pathlib import Path

TOKEN = os.getenv('GITHUB_TOKEN')

REPO_ROOT = Path.cwd()
README_PATH = REPO_ROOT / 'README.md'
CONFIG_PATH = REPO_ROOT / 'stack_config.yml'
BADGES_DIR = REPO_ROOT / 'assets' / 'badges'
CUSTOM_ICONS_DIR = REPO_ROOT / 'assets' / 'custom_icons'

START_MARKER = '<!-- TECH_STACK:START -->'
END_MARKER = '<!-- TECH_STACK:END -->'
ICON_SIZE = (16, 16)

GITHUB_WEB_URL = 'https://github.com'
GITHUB_API_URL = 'https://api.github.com'
RAW_GITHUB_URL = 'https://raw.githubusercontent.com'

EXPLORE_RAW_URL = f'{RAW_GITHUB_URL}/github/explore/main/topics'
DEVICON_CDN_URL = f'{RAW_GITHUB_URL}/devicons/devicon/master/icons'
DEVICON_META_URL = f'{RAW_GITHUB_URL}/devicons/devicon/master/devicon.json'
SIMPLE_ICONS_URL = f'{RAW_GITHUB_URL}/simple-icons/simple-icons/develop/icons'

PROVIDER_ORDER = ('Custom', 'Devicon', 'SimpleIcons', 'Explore')
SVG_NS = 'http://www.w3.org/2000/svg'
