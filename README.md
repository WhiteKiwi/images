# WhiteKiwi images

Public container image definitions, smoke tests, and image build automation.

| Image | Contract | Platform |
| --- | --- | --- |
| [ubuntu-ci](images/ubuntu-ci/README.md) | General-purpose non-root Actions runner; no sudo or Docker | `linux/amd64` |

## Repository layout

Each `images/<name>/` owns its Dockerfile, package list, upstream base pin, documentation and smoke tests. `docker-bake.hcl` owns build targets. Shared scripts are used by both Docker Desktop and GitHub Actions. Actual ARC/K3s deployments, proxy rules, volumes and credentials remain in private infrastructure configuration.

Image-local changes build only that image. Shared scripts, workflows, Bake or build-context policy changes test all image definitions. README-only changes do not build images. Initial pushes build all images. Add new image definitions and Bake targets together; image inheritance is not configured today.

## Build and verify locally

From a committed checkout with Docker Desktop running:

```sh
bash scripts/build.sh ubuntu-ci whitekiwi/ubuntu-ci:local
bash scripts/verify.sh ubuntu-ci whitekiwi/ubuntu-ci:local
python3 -m unittest discover -s tests -v
```

`BUILDX_BUILDER` optionally selects an existing builder. Credentials are not needed to build or verify the public base. Build and verification receipts are temporary local `.build/` files and are excluded from Git. Publishing refuses an image whose ID differs from the verified build receipt.

## CI and publication

PRs build and smoke-test affected images with read-only permissions. Main pushes and explicit trusted-main dispatches build, verify and publish affected images using the workflow `GITHUB_TOKEN` with `packages: write`. Each image is built once for that publication run; the exact locally tested image is pushed without rebuilding.

Published references use `ghcr.io/whitekiwi/images/<name>:build-<run-id>-<attempt>`. Source commit, pinned upstream reference and final registry digest are recorded in image metadata and the Actions publication summary. Consumers should select an accepted digest. Image publication does not deploy or restart Kubernetes runners. New GHCR packages initially default to Private; the owner must explicitly make the intended image packages Public before anonymous consumers can pull them.

## Base image updates

`Check base images` runs once daily at approximately 06:23 Asia/Seoul (21:23 UTC), or manually. GitHub schedules may be delayed. It resolves the selected platform of each tracked public base and compares its digest with `base-image.json`. Unchanged bases do not trigger builds. A changed base produces a commit on `automation/base-images`, opens/updates a PR, and explicitly dispatches `Verify images` on that branch.

Automatic merging is **off unless repository variable `AUTO_MERGE_BASE_UPDATES=true` is set**. When enabled, the default-branch merge workflow only accepts a repository-owned, successful verification run for the current bot-created update PR. It checks that the branch is based on current main, only existing base lock files changed, and only their digest values changed. It merges the exact tested head and explicitly dispatches publication for the merge commit. General code/package/workflow changes are never automatically merged by this mechanism.

Explicit dispatch is required because ordinary events created using `GITHUB_TOKEN` do not start another workflow. If checks, merging or publication fail, the workflow fails visibly and no deployment is performed. A stale update branch must be refreshed and reverified. Automatic publication and actual cluster activation are separate responsibilities.

The repository must permit Actions to create PRs for the scheduled updater. The initial implementation does not add a weekly APT refresh, registry cleanup, or Kubernetes deployment automation.

## Operator controls

The daily updater can also be started with `gh workflow run update-base.yml --repo WhiteKiwi/images`. A manual poll with unchanged upstream digests completes without opening a PR or rebuilding an image.

`AUTO_MERGE_BASE_UPDATES` is a repository Actions variable, initially `false`. Leaving it false still allows update PR creation and verification; the owner then merges the PR. Setting it to `true` enables only the guarded digest-update merge path described above. Verify build/publication and review the merge guard before changing this switch.

README-only PRs still run selector/unit validation and the final `verify` result, while their image build job is skipped. Their merge likewise runs publication planning without publishing another image.
