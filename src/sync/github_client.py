from __future__ import annotations

import base64
from collections import defaultdict
import json
import logging
import os
import re
import urllib.error
import urllib.request

from profile_sync.config import DEVICON_META_URL, GITHUB_API_URL, REPO_ROOT, TOKEN

logger = logging.getLogger(__name__)
SIMPLE_ICONS_META_URLS = (
    '.'.join(('https://raw', 'githubusercontent', 'com/simple-icons/simple-icons/develop/data/simple-icons.json')),
    '.'.join(('https://raw', 'githubusercontent', 'com/simple-icons/simple-icons/develop/_data/simple-icons.json')),
)


def get_username() -> str:
    owner = os.getenv('GITHUB_REPOSITORY_OWNER')
    return owner if owner else REPO_ROOT.name


def github_request(url: str, method: str = 'GET', payload: dict | None = None) -> list | dict:
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'Profile-Stack-Sync',
    }
    if TOKEN:
        headers['Authorization'] = f'Bearer {TOKEN}'

    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    if data is not None:
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read().decode('utf-8')
        return json.loads(body) if body else {}


def fetch_metadata() -> tuple[dict[str, str], dict[str, str]]:
    colors: dict[str, str] = {}
    for meta_url in SIMPLE_ICONS_META_URLS:
        try:
            si_data = github_request(meta_url)
            icons_list = si_data.get('icons', []) if isinstance(si_data, dict) else si_data
            if isinstance(icons_list, list) and icons_list:
                for item in icons_list:
                    slug = re.sub(r'[^a-z0-9]', '', item.get('title', '').lower())
                    hex_color = item.get('hex', '').lstrip('#')
                    if slug and len(hex_color) == 6:
                        colors[slug] = f'#{hex_color}'
                break
        except Exception:
            continue

    try:
        dev_data = github_request(DEVICON_META_URL)
        if isinstance(dev_data, list):
            for item in dev_data:
                name = item.get('name', '')
                hex_color = item.get('color', '').lstrip('#')
                if name and len(hex_color) == 6:
                    colors[name] = f'#{hex_color}'
    except Exception as exc:
        logger.warning('Could not fetch devicon.json colors: %s', exc)

    return colors, {}


def collect_repositories_data(username: str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Return (topic_to_repos, repo_to_topics) across public non-fork repositories."""
    logger.info('Fetching repositories for user: %s', username)
    repos = github_request(f'{GITHUB_API_URL}/users/{username}/repos?per_page=100')
    topic_repos: dict[str, list[str]] = defaultdict(list)
    repo_topics: dict[str, list[str]] = {}

    if isinstance(repos, list):
        for repo in repos:
            repo_name = repo.get('name', '')
            if repo.get('fork') or repo_name == username:
                continue
            topics = repo.get('topics', [])
            repo_topics[repo_name] = topics
            for topic in topics:
                topic_repos[topic].append(repo_name)

    sorted_topics = dict(sorted(topic_repos.items(), key=lambda item: (-len(item), item)))
    logger.info('Collected %d unique topics across %d repos.', len(sorted_topics), len(repo_topics))
    return sorted_topics, repo_topics


def update_remote_repo_readme(username: str, repo_name: str, rendered_block: str, start_marker: str, end_marker: str) -> bool:
    """Update README.md in a target repository if markers are present."""
    api_url = f'{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/README.md'
    try:
        file_meta = github_request(api_url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            logger.debug('Repo %s has no README.md, skipping.', repo_name)
            return False
        logger.warning('Failed to read README.md in %s: %s', repo_name, exc)
        return False

    if not isinstance(file_meta, dict) or 'content' not in file_meta:
        return False

    sha = file_meta['sha']
    current_text = base64.b64decode(file_meta['content']).decode('utf-8')

    pattern = re.compile(rf'({re.escape(start_marker)})(.*?)({re.escape(end_marker)})', flags=re.DOTALL)
    if not pattern.search(current_text):
        return False

    updated_text = pattern.sub(rf'\1\n{rendered_block}\n\3', current_text)
    if updated_text == current_text:
        logger.info('Repo %-32s -> README already up to date.', repo_name)
        return False

    payload = {
        'message': 'DOCS | update repository tech stack badges',
        'content': base64.b64encode(updated_text.encode('utf-8')).decode('ascii'),
        'sha': sha,
    }
    github_request(api_url, method='PUT', payload=payload)
    logger.info('Repo %-32s -> README.md UPDATED.', repo_name)
    return True
