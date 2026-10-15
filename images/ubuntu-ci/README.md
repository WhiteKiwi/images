# ubuntu-ci

An Ubuntu-based, general-purpose GitHub Actions runner derived from the official `ghcr.io/actions/actions-runner` image. The selected upstream `linux/amd64` manifest is pinned in `base-image.json`; updates follow that image's `latest` tag within this definition's configured platform.

The image provides the runner and its internal action runtimes, Git, curl, CA certificates, jq, archive tools, OpenSSH client, Python 3/venv, pkg-config and the GNU C/C++ build tools. `packages.txt` owns the actual APT package list. Repositories install and pin their own Node, Go, Rust and other project toolchains.

Jobs run as the ordinary `runner` user. Upstream sudo privileges and Docker binaries are removed. HOME, `/home/runner/_work`, and `/opt/hostedtoolcache` are writable. `/cache` is a prepared mount point; the operator must provide the actual persistent writable volume and its ownership. Cache data is not part of the image.

Smoke tests check runner/tool execution, non-root/no-sudo/no-Docker defaults, and working-directory permissions. Actual resource limits, ARC registration, proxy behavior and persistent cache mounts require deployment acceptance in K3s. The image itself does not set CPU/memory limits, enroll runners or contain authentication material.
