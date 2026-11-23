from __future__ import annotations

from collections import defaultdict
import logging
import shutil
import urllib.parse

import yaml

from profile_sync.config import (
    BADGES_DIR,
    CONFIG_PATH,
    END_MARKER,
    GITHUB_WEB_URL,
    RAW_GITHUB_URL,
    START_MARKER,
)
from profile_sync.github_client import (
    collect_repositories_data,
    fetch_metadata,
    get_username,
    update_remote_repo_readme,
)
from profile_sync.providers import build_pipeline, resolve_icon_info
from profile_sync.reporter import print_console_report, update_readme
from profile_sync.svg_builder import create_svg_badge

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


def load_stack_config() -> tuple[
    set[str], dict[str, str], dict[str, list[str]]
]:
    if not CONFIG_PATH.is_file():
        return set(), {}, {}
    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8')) or {}
    ignore = {str(t).lower() for t in raw.get('ignore', [])}
    aliases = {
        str(k).lower(): str(v) for k, v in (raw.get('aliases') or {}).items()
    }
    groups = {
        str(g): [str(t).lower() for t in items]
        for g, items in (raw.get('groups') or {}).items()
    }
    return ignore, aliases, groups


def format_grouped_html(
    topics: list[str],
    valid_topics: dict[str, str],
    username: str,
    groups: dict[str, list[str]],
    base_asset_prefix: str,
) -> str:
    """Format badge links grouped by stack_config.yml for either local profile or remote repo."""
    fallback_group = list(groups.keys())[-1] if groups else 'Tools & Ecosystem'
    rendered_items: dict[str, str] = {}

    for topic in topics:
        low_topic = topic.lower()
        if low_topic not in valid_topics:
            continue
        label = valid_topics[low_topic]
        img_url = f'{base_asset_prefix}assets/badges/{topic}.svg'
        filter_url = f'{GITHUB_WEB_URL}/{username}?tab=repositories&topic={urllib.parse.quote(topic)}'
        rendered_items[low_topic] = (
            f'  <a href="{filter_url}"><img src="{img_url}" alt="{label}" vspace="4" hspace="3"></a>'
        )

    grouped_blocks: dict[str, list[str]] = defaultdict(list)
    for grp, ordered_topics in groups.items():
        for t in ordered_topics:
            if t in rendered_items:
                grouped_blocks[grp].append(rendered_items.pop(t))

    for remaining_html in rendered_items.values():
        grouped_blocks[fallback_group].append(remaining_html)

    blocks = ['\n'.join(items) for items in grouped_blocks.values() if items]
    return '\n<br><br>\n'.join(blocks)


def main() -> None:
    username = get_username()
    brand_colors, _ = fetch_metadata()
    topic_repos, repo_topics = collect_repositories_data(username)

    if BADGES_DIR.exists():
        shutil.rmtree(BADGES_DIR)
    BADGES_DIR.mkdir(parents=True, exist_ok=True)

    ignore, aliases, groups = load_stack_config()
    pipeline = build_pipeline()

    valid_topics: dict[str, str] = {}
    matched_records: list[dict] = []
    missing_icons: dict[str, list[str]] = {}
    total = len(topic_repos)

    for idx, (topic, repos) in enumerate(topic_repos.items(), start=1):
        low_topic = topic.lower()
        if low_topic in ignore:
            logger.info('[%d/%d] %-22s -> IGNORED', idx, total, topic)
            continue

        icon_res = resolve_icon_info(topic, brand_colors, pipeline)
        if not icon_res:
            missing_icons[topic] = repos
            logger.warning('[%d/%d] %-22s -> SKIPPED', idx, total, topic)
            continue

        label = aliases.get(low_topic, topic.replace('-', ' ')).upper()
        create_svg_badge(
            topic, icon_res.data_uri, icon_res.color, display_label=label
        )
        valid_topics[low_topic] = label

        logger.info(
            '[%d/%d] %-22s -> OK | %s', idx, total, topic, icon_res.provider
        )
        matched_records.append(
            {
                'topic': topic,
                'provider': icon_res.provider,
                'source': icon_res.source_file,
                'color': icon_res.color,
                'count': len(repos),
            }
        )

    print_console_report(username, matched_records, missing_icons)

    profile_html = format_grouped_html(
        list(topic_repos.keys()),
        valid_topics,
        username,
        groups,
        base_asset_prefix='',
    )
    update_readme(profile_html)

    raw_prefix = f'{RAW_GITHUB_URL}/{username}/{username}/main/'
    for repo_name, topics in sorted(repo_topics.items()):
        repo_html = format_grouped_html(
            topics,
            valid_topics,
            username,
            groups,
            base_asset_prefix=raw_prefix,
        )
        if repo_html:
            update_remote_repo_readme(
                username, repo_name, repo_html, START_MARKER, END_MARKER
            )


if __name__ == '__main__':
    main()
