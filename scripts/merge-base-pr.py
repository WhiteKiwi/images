#!/usr/bin/env python3
"""Merge only a successful exact-head, digest-only automation PR."""
import base64
import json
import os
import re
from urllib.parse import quote
from github_api import api, repository, full_sha
from image_lib import valid_base_update


if __name__ == '__main__':
    event = json.load(open(os.environ['GITHUB_EVENT_PATH']))
    run = event['workflow_run']
    repo = repository()
    if (run['conclusion'] != 'success' or run['event'] != 'workflow_dispatch'
            or run['head_branch'] != 'automation/base-images'
            or run['head_repository']['full_name'].lower() != repo.lower()):
        raise SystemExit('Not a successful repository-owned update verification')
    head = full_sha(run['head_sha'])
    prs = api('repos/' + repo + '/pulls?state=open&head=WhiteKiwi:automation/base-images')
    if len(prs) != 1:
        raise SystemExit('Expected one open automation PR')
    pr = prs[0]
    if (pr['user']['login'] != 'github-actions[bot]' or pr['base']['ref'] != 'main'
            or pr['head']['sha'] != head or pr['head']['repo']['full_name'].lower() != repo.lower()):
        raise SystemExit('PR author, scope or tested head no longer matches')
    main = api('repos/' + repo + '/git/ref/heads/main')['object']['sha']
    commit = api('repos/' + repo + '/commits/' + head)
    if len(commit['parents']) != 1 or commit['parents'][0]['sha'] != main:
        raise SystemExit('Main moved; a fresh update branch and CI run are required')
    files = api('repos/' + repo + '/pulls/' + str(pr['number']) + '/files?per_page=100')
    if not files or len(files) != pr['changed_files']:
        raise SystemExit('Missing or truncated changed-file evidence')
    for changed in files:
        path = changed['filename']
        if changed['status'] != 'modified' or not re.fullmatch(
                r'images/[a-z0-9]+(?:-[a-z0-9]+)*/base-image\.json', path):
            raise SystemExit('Automatic merging only allows existing base locks')
        def read(ref):
            response = api('repos/' + repo + '/contents/' + quote(path, safe='/') + '?ref=' + ref)
            return json.loads(base64.b64decode(response['content']))
        if not valid_base_update(read(main), read(head)):
            raise SystemExit('Only the pinned digest may change')
    result = api('repos/' + repo + '/pulls/' + str(pr['number']) + '/merge', 'PUT',
                 {'sha': head, 'merge_method': 'squash'})
    if not result.get('merged'):
        raise SystemExit('GitHub did not merge the verified head')
    merged = full_sha(result['sha'])
    # Explicitly chain publication; do not depend on a token-generated push event.
    api('repos/' + repo + '/actions/workflows/publish.yml/dispatches', 'POST',
        {'ref': 'main', 'inputs': {'source_sha': merged, 'base_sha': main}})
    print('Merged ' + pr['html_url'] + ' at ' + merged + '; dispatched publication.')
