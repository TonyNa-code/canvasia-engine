#!/bin/sh
cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1; then
  exec python3 tools/ci/github_status.py "$@"
fi

exec python tools/ci/github_status.py "$@"
