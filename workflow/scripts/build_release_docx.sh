#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# Internal compatibility helper: call the public release-build entrypoint and emit only the DOCX path.
OUTPUT="$(python3 "$ROOT/tools/cli.py" release-build "$@")"
printf '%s\n' "$OUTPUT" >&2

DOCX_PATH="$(printf '%s\n' "$OUTPUT" | sed -n 's/^docx_path: //p' | tail -n 1)"
if [[ -z "$DOCX_PATH" ]]; then
    echo "[FAIL] release-build did not report docx_path" >&2
    exit 1
fi

printf '%s\n' "$DOCX_PATH"
