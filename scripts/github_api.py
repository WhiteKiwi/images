"""GitHub API helpers for the repository's own automation."""
import json
import os
import re
import urllib.error
import urllib.request


def repository():
    value = os.environ.get('GITHUB_REPOSITORY', '')
    if value.lower() != 'whitekiwi/images':
        raise ValueError('This automation only mutates WhiteKiwi/images')
    return value


def api(path, method='GET', body=None):
    if not path.startswith('repos/' + repository() + '/'):
        raise ValueError('API request outside the selected repository')
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError('GitHub workflow token required')
    request = urllib.request.Request('https://api.github.com/' + path, method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        message = json.loads(error.read()).get('message', 'GitHub API error')
        raise RuntimeError(str(error.code) + ': ' + message) from None


def full_sha(value):
    if not re.fullmatch('[0-9a-f]{40}', value):
        raise ValueError('Full commit SHA required')
    return value
