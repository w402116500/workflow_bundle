#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG=""

if [[ "${1:-}" == *.json ]]; then
    CONFIG="$1"
    shift
fi

if [[ -z "$CONFIG" ]]; then
    CONFIG="$(python3 "$ROOT/tools/cli.py" resolve-active-workspace --print-path)"
fi

bash "$ROOT/workflow/scripts/release_preflight.sh" "$CONFIG"

if [[ $# -gt 0 ]]; then
    DOCX_PATH="$1"
else
    DOCX_PATH="$(python3 "$ROOT/tools/cli.py" build --config "$CONFIG" --print-output-path)"
fi

python3 "$ROOT/tools/cli.py" verify "$DOCX_PATH"

echo "[INFO] Linux 交付版校验完成：$DOCX_PATH"
echo "[INFO] Linux 路径不执行 Microsoft Word 专属终排。"
