#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${EFFORT_LANES_WSL_IMAGE:-node:22-bookworm-slim}"

command -v docker >/dev/null || { echo "ERROR: Docker is required for the WSL userland regression" >&2; exit 1; }
docker info >/dev/null

# ponytail: this covers the Linux userland contract only; use real WSL when Windows-path interop enters scope.
docker run --rm -v "$ROOT:/src:ro" "$IMAGE" bash -lc '
  set -e
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq bash ca-certificates coreutils findutils git jq python3 >/tmp/apt.log
  cp -a /src /work
  cd /work
  . /etc/os-release
  printf "WSL proxy: %s %s, " "$NAME" "$VERSION_ID"
  bash --version | sed -n "1p"
  python3 --version
  node --version
  bash scripts/check.sh
'
