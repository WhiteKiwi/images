"""Small shared image catalog; no third-party Python dependencies."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


def image_dir(name, root=ROOT):
    if not SLUG.fullmatch(name):
        raise ValueError("Invalid image name")
    path = root / "images" / name
    if path.is_symlink() or not (path / "Dockerfile").is_file():
        raise ValueError("Unknown image: " + name)
    return path


def catalog(root=ROOT):
    return sorted(p.name for p in (root / "images").iterdir()
                  if p.is_dir() and not p.is_symlink() and (p / "Dockerfile").is_file()
                  and SLUG.fullmatch(p.name))


def load_base(name, root=ROOT):
    config = json.loads((image_dir(name, root) / "base-image.json").read_text())
    if set(config) != {"image", "tracking_tag", "platform", "digest"}:
        raise ValueError("Unexpected base image fields")
    if not re.fullmatch(r"[a-z0-9.-]+/[a-z0-9_./-]+", config["image"]):
        raise ValueError("Invalid registry image")
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", config["tracking_tag"]):
        raise ValueError("Invalid tracking tag")
    if config["platform"] != "linux/amd64" or not DIGEST.fullmatch(config["digest"]):
        raise ValueError("Invalid platform or digest")
    return config


def valid_base_update(before, after):
    return (set(before) == set(after) == {"image", "tracking_tag", "platform", "digest"}
            and before["digest"] != after["digest"]
            and bool(DIGEST.fullmatch(after["digest"]))
            and all(before[k] == after[k] for k in before if k != "digest"))
