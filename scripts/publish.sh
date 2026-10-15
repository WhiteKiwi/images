#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image=${1:?image name required}
tag=${2:?GHCR image tag required}
python3 scripts/base-ref.py "$image" >/dev/null
IMAGE_NAME="$image" IMAGE_TAG="$tag" python3 - <<'PY'
import json, os, pathlib, re, subprocess
name, tag = os.environ['IMAGE_NAME'], os.environ['IMAGE_TAG']
if not re.fullmatch('ghcr.io/whitekiwi/images/' + re.escape(name) + r':build-[0-9]+-[0-9]+', tag):
    raise SystemExit('Publish requires a unique WhiteKiwi/images build tag')
d = json.loads(pathlib.Path('.build', name + '.json').read_text())
current = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', tag], text=True).strip()
if d['tag'] != tag or d['image_id'] != current or d.get('verified_image_id') != current:
    raise SystemExit('Refusing to publish an unverified or changed image')
PY
docker push "$tag"
IMAGE_NAME="$image" IMAGE_TAG="$tag" python3 - <<'PY'
import json, os, pathlib, subprocess
p = pathlib.Path('.build', os.environ['IMAGE_NAME'] + '.json')
d = json.loads(p.read_text())
refs = json.loads(subprocess.check_output(['docker', 'image', 'inspect', '--format',
                                          '{{json .RepoDigests}}', os.environ['IMAGE_TAG']], text=True))
repository = os.environ['IMAGE_TAG'].split(':')[0]
d['published_ref'] = next(r for r in refs if r.startswith(repository + '@sha256:'))
p.write_text(json.dumps(d, indent=2) + '\n')
print(json.dumps(d, indent=2))
if os.environ.get('GITHUB_STEP_SUMMARY'):
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
        f.write('### ' + d['image'] + '\n\n' + d['published_ref'] + '\n\n')
        f.write('Source: `' + d['source_revision'] + '`\n\nBase: `' + d['base'] + '`\n')
PY
