from __future__ import annotations

from collections import defaultdict
import logging
import re

from tabulate import tabulate

from profile_sync.config import (
    END_MARKER,
    GITHUB_WEB_URL,
    PROVIDER_ORDER,
    README_PATH,
    START_MARKER,
)

logger = logging.getLogger(__name__)


def print_console_report(
    username: str,
    matched_records: list[dict],
    missing_icons: dict[str, list[str]],
) -> None:
    by_provider: dict[str, list[list]] = defaultdict(list)
    for r in matched_records:
        by_provider[r['provider']].append(
            [r['topic'], r['source'], r['color'], r['count']]
        )

    idx = 1
    for provider in PROVIDER_ORDER:
        rows = by_provider.get(provider)
        if not rows:
            continue
        logger.info(
            '1.%d. Источник %s (%d шт.):\n%s',
            idx,
            provider,
            len(rows),
            tabulate(
                rows,
                headers=['Topic', 'File', 'Color / Format', 'Repos'],
                tablefmt='rounded_outline',
            ),
        )
        idx += 1

    if missing_icons:
        missing_rows = []
        repo_to_missing: dict[str, list[str]] = defaultdict(list)
        for topic, repos in missing_icons.items():
            urls = '\n'.join(f'{GITHUB_WEB_URL}/{username}/{r}' for r in repos)
            missing_rows.append([topic, urls])
            for repo in repos:
                repo_to_missing[repo].append(topic)

        repo_rows = [
            [f'{GITHUB_WEB_URL}/{username}/{repo}', ', '.join(sorted(topics))]
            for repo, topics in sorted(repo_to_missing.items())
        ]
        logger.warning(
            '2. Топики без иконок (%d шт.):\n%s',
            len(missing_rows),
            tabulate(
                missing_rows,
                headers=['Topic', 'Repositories'],
                tablefmt='rounded_outline',
            ),
        )
        logger.warning(
            '3. Репозитории с топиками без иконок (%d шт.):\n%s',
            len(repo_rows),
            tabulate(
                repo_rows,
                headers=['Repository URL', 'Missing Topics'],
                tablefmt='rounded_outline',
            ),
        )


def update_readme(rendered_block: str) -> None:
    content = README_PATH.read_text(encoding='utf-8')
    pattern = re.compile(
        rf'({re.escape(START_MARKER)})(.*?)({re.escape(END_MARKER)})',
        flags=re.DOTALL,
    )
    if not pattern.search(content):
        raise ValueError(
            f'Markers {START_MARKER} and {END_MARKER} not found in {README_PATH}'
        )
    updated = pattern.sub(rf'\1\n{rendered_block}\n\3', content)
    if updated != content:
        README_PATH.write_text(updated, encoding='utf-8')
        logger.info('README.md successfully updated.')
    else:
        logger.info('No changes detected in README.md.')
