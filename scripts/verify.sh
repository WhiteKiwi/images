#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image=${1:?image name required}
tag=${2:?image tag required}
python3 scripts/base-ref.py "$image" >/dev/null
docker run --rm --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$PWD/images/$image/tests,dst=/image-tests,readonly" \
  --entrypoint /bin/bash "$tag" /image-tests/smoke.sh
IMAGE_NAME="$image" IMAGE_TAG="$tag" python3 - <<'PY'
import datetime, json, os, pathlib, subprocess
p = pathlib.Path('.build', os.environ['IMAGE_NAME'] + '.json')
d = json.loads(p.read_text())
current = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}',
                                   os.environ['IMAGE_TAG']], text=True).strip()
if d['tag'] != os.environ['IMAGE_TAG'] or d['image_id'] != current:
    raise SystemExit('Built image changed before verification')
d['verified_image_id'] = current
d['verified_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
p.write_text(json.dumps(d, indent=2) + '\n')
PY
