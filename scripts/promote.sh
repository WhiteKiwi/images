#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image=${1:?image name required}
python3 scripts/base-ref.py "$image" >/dev/null
IMAGE_NAME="$image" python3 - <<'PY'
import json, os, pathlib, re, subprocess

p = pathlib.Path('.build', os.environ['IMAGE_NAME'] + '.json')
d = json.loads(p.read_text())
repository = 'ghcr.io/whitekiwi/images/' + os.environ['IMAGE_NAME']
if not re.fullmatch(re.escape(repository) + r'@sha256:[0-9a-f]{64}', d.get('published_ref', '')):
    raise SystemExit('A published image receipt is required')
current = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', d['tag']], text=True).strip()
if current != d.get('verified_image_id') or current != d['image_id']:
    raise SystemExit('Image changed after verification')
main = subprocess.check_output(['git', 'ls-remote', 'https://github.com/WhiteKiwi/images.git',
                                'refs/heads/main'], text=True).split()[0]
if main != d['source_revision']:
    print('Main advanced; retained build tag but skipped latest promotion.')
    raise SystemExit(0)
latest = repository + ':latest'
subprocess.run(['docker', 'tag', d['tag'], latest], check=True)
subprocess.run(['docker', 'push', latest], check=True)
d['promoted_tag'] = latest
p.write_text(json.dumps(d, indent=2) + '\n')
print('Promoted ' + d['published_ref'] + ' to ' + latest)
if os.environ.get('GITHUB_STEP_SUMMARY'):
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
        f.write('\nPromoted `' + latest + '` to `' + d['published_ref'] + '`\n')
PY
