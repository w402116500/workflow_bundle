#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG=""
IS_WSL=0

if grep -qi microsoft /proc/version 2>/dev/null || [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    IS_WSL=1
fi

if [[ $IS_WSL -eq 0 && "$(uname -s)" != MINGW* && "$(uname -s)" != CYGWIN* && "$(uname -s)" != MSYS* ]]; then
    bash "$ROOT/workflow/scripts/postprocess_release_linux.sh" "$@"
    exit $?
fi

if [[ "${1:-}" == *.json ]]; then
    CONFIG="$1"
    shift
    bash "$ROOT/workflow/scripts/release_preflight.sh" "$CONFIG"
    python3 "$ROOT/tools/cli.py" postprocess --config "$CONFIG" "$@"
    exit $?
fi

if [[ -z "$CONFIG" ]]; then
    CONFIG="$(python3 "$ROOT/tools/cli.py" resolve-active-workspace --print-path)"
fi

if [[ $# -eq 0 ]]; then
    bash "$ROOT/workflow/scripts/release_preflight.sh" "$CONFIG"
    python3 "$ROOT/tools/cli.py" postprocess --config "$CONFIG"
    exit $?
fi

bash "$ROOT/workflow/scripts/check_bundle_sync.sh"
python3 "$ROOT/tools/cli.py" postprocess "$@"
