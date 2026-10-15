#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image=${1:?image name required}
tag=${2:?local image tag required}
base=$(python3 scripts/base-ref.py "$image")
if [[ -n $(git status --porcelain) ]]; then
  echo 'Build from a clean committed checkout so the source revision is exact.' >&2
  exit 1
fi
revision=$(git rev-parse HEAD)
builder=()
if [[ -n ${BUILDX_BUILDER:-} ]]; then builder=(--builder "$BUILDX_BUILDER"); fi
docker buildx bake "${builder[@]}" "$image" --load \
  --set "$image.args.BASE_IMAGE=$base" \
  --set "$image.args.SOURCE_REVISION=$revision" \
  --set "$image.tags=$tag"
mkdir -p .build
IMAGE_NAME="$image" IMAGE_TAG="$tag" BASE_REF="$base" SOURCE_REVISION="$revision" python3 - <<'PY'
import json, os, pathlib, subprocess
name = os.environ['IMAGE_NAME']
tag = os.environ['IMAGE_TAG']
data = {'image': name, 'tag': tag, 'source_revision': os.environ['SOURCE_REVISION'],
        'base': os.environ['BASE_REF'], 'image_id': subprocess.check_output(
            ['docker', 'image', 'inspect', '--format', '{{.Id}}', tag], text=True).strip()}
pathlib.Path('.build', name + '.json').write_text(json.dumps(data, indent=2) + '\n')
PY
