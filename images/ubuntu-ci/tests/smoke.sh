#!/usr/bin/env bash
set -euo pipefail

test "$(id -u)" -ne 0
if command -v sudo >/dev/null 2>&1; then
  echo 'sudo must not be installed' >&2
  exit 1
fi
for binary in docker dockerd; do
  if command -v "$binary" >/dev/null 2>&1; then
    echo "$binary must not be installed" >&2
    exit 1
  fi
done
test ! -S /var/run/docker.sock
./bin/Runner.Listener --version
for binary in git curl python3 gcc g++ make tar gzip unzip zstd jq; do
  command -v "$binary" >/dev/null
done
git --version
python3 --version
gcc --version | head -n 1
for directory in "$HOME" /home/runner/_work "$RUNNER_TOOL_CACHE"; do
  scratch=$(mktemp "$directory/.image-smoke.XXXXXX")
  rm -f "$scratch"
done
echo 'Image smoke checks passed.'
