#!/usr/bin/env python3
"""Resolve official tracked tags, pin the selected platform, and update locks."""
import argparse
import json
import subprocess
from image_lib import ROOT, catalog, load_base, DIGEST


def resolve(config):
    reference = config['image'] + ':' + config['tracking_tag']
    data = json.loads(subprocess.check_output(
        ['docker', 'buildx', 'imagetools', 'inspect', reference, '--format', '{{json .Manifest}}'],
        text=True))
    if 'manifests' in data:
        matches = [m['digest'] for m in data['manifests'] if
                   m.get('platform', {}).get('os') == 'linux' and
                   m.get('platform', {}).get('architecture') == 'amd64']
        if len(matches) != 1:
            raise ValueError('Expected exactly one linux/amd64 upstream manifest')
        digest = matches[0]
    else:
        digest = data.get('digest', '')
    if not DIGEST.fullmatch(digest):
        raise ValueError('Registry did not return a valid digest')
    return digest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    changed = []
    for name in catalog():
        config = load_base(name)
        digest = resolve(config)
        if digest != config['digest']:
            changed.append(name)
            config['digest'] = digest
            if args.write:
                (ROOT / 'images' / name / 'base-image.json').write_text(
                    json.dumps(config, indent=2) + '\n')
    print(json.dumps({'image': changed}, separators=(',', ':')))
