#!/usr/bin/env python3
"""Commit changed base locks, open/update one PR, explicitly dispatch its CI."""
import subprocess
from github_api import api, repository
from image_lib import ROOT, catalog


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


if __name__ == '__main__':
    repo = repository()
    paths = ['images/' + name + '/base-image.json' for name in catalog()]
    if not git('diff', '--name-only', '--', *paths):
        print('No upstream base image changes.')
        raise SystemExit(0)
    branch = 'automation/base-images'
    prs = api('repos/' + repo + '/pulls?state=open&head=WhiteKiwi:' + branch)
    if prs and (len(prs) != 1 or prs[0]['user']['login'] != 'github-actions[bot]'):
        raise SystemExit('Refusing to update a branch with a non-automation PR')
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    base = git('rev-parse', 'HEAD')
    remote = git('ls-remote', '--heads', 'origin', 'refs/heads/' + branch)
    if remote:
        git('fetch', 'origin', 'refs/heads/' + branch + ':refs/remotes/origin/' + branch)
    git('checkout', '-B', branch)
    git('add', '--', *paths)
    git('commit', '-m', 'build: update official runner base image digests')
    git('push', '--force-with-lease', 'origin', 'HEAD:refs/heads/' + branch)
    if prs:
        pr = prs[0]
    else:
        pr = api('repos/' + repo + '/pulls', 'POST', {
            'title': 'build: update official runner base image digests',
            'head': branch, 'base': 'main',
            'body': 'Automated official base image digest update.\n\nOnly per-image base-image.json files may be changed. Image CI is explicitly dispatched on this branch; automatic merging remains opt-in.'})
    # GITHUB_TOKEN-generated pushes/PRs do not start ordinary push/PR workflows.
    api('repos/' + repo + '/actions/workflows/verify.yml/dispatches', 'POST',
        {'ref': branch, 'inputs': {'base_sha': base}})
    print(pr['html_url'])
    print('Dispatched image verification for ' + git('rev-parse', 'HEAD'))
