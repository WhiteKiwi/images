# syntax=docker/dockerfile:1
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

USER root
ARG BASE_IMAGE
ARG SOURCE_REVISION=local
LABEL org.opencontainers.image.source="https://github.com/WhiteKiwi/images" \
      org.opencontainers.image.revision="${SOURCE_REVISION}" \
      org.opencontainers.image.base.name="${BASE_IMAGE}" \
      org.opencontainers.image.description="General-purpose non-root Ubuntu Actions runner"

COPY images/ubuntu-ci/packages.txt /tmp/image-packages.txt
RUN apt-get update \
    && xargs -r apt-get install -y --no-install-recommends < /tmp/image-packages.txt \
    && SUDO_FORCE_REMOVE=yes apt-get purge -y sudo \
    && rm -rf /var/lib/apt/lists/* /tmp/image-packages.txt \
    && rm -f /usr/bin/docker /usr/bin/dockerd /usr/bin/docker-init /usr/bin/docker-proxy \
             /usr/bin/containerd /usr/bin/containerd-shim-runc-v2 /usr/bin/ctr /usr/bin/runc \
    && rm -rf /usr/local/lib/docker/cli-plugins \
    && usermod -G '' runner \
    && mkdir -p /home/runner/_work /opt/hostedtoolcache /cache \
    && chown runner:runner /home/runner /home/runner/_work /opt/hostedtoolcache /cache \
    && chmod 0755 /home/runner /home/runner/_work /opt/hostedtoolcache /cache

ENV HOME=/home/runner \
    LANG=C.UTF-8 \
    RUNNER_TOOL_CACHE=/opt/hostedtoolcache \
    AGENT_TOOLSDIRECTORY=/opt/hostedtoolcache
WORKDIR /home/runner
USER runner
