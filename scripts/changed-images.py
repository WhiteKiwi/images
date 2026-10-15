#!/usr/bin/env python3
"""Select affected image definitions from an exact Git diff."""
import argparse
import json
import re
import subprocess
from image_lib import ROOT, catalog


def select(names, paths):
    shared = ("scripts/", ".github/workflows/")
    if any(p.startswith(shared) or p in {"docker-bake.hcl", ".dockerignore"} for p in paths):
        return names
    return [name for name in names if any(
        p.startswith("images/" + name + "/") and not p.endswith("/README.md")
        for p in paths)]


def changed(base, head, root=ROOT):
    for ref in (base, head):
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise ValueError("Comparison requires full commit SHAs")
    if base == "0" * 40:
        return catalog(root)
    result = subprocess.run(["git", "diff", "--name-only", "-z", base, head, "--"],
                            cwd=root, check=True, stdout=subprocess.PIPE)
    paths = result.stdout.decode().split("\0")
    return select(catalog(root), paths)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--head")
    args = parser.parse_args()
    names = changed(args.base, args.head) if args.base and args.head else catalog()
    print(json.dumps({"image": names}, separators=(",", ":")))
