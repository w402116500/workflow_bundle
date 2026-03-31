#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG="${1:-}"

if [[ -z "$CONFIG" ]]; then
    CONFIG="$(python3 "$ROOT/tools/cli.py" resolve-active-workspace --print-path)"
fi

WORKSPACE_ROOT="$(python3 -c 'import json, pathlib, sys; p = pathlib.Path(sys.argv[1]).resolve(); cfg = json.loads(p.read_text(encoding="utf-8")); print((p.parent / cfg.get("workspace_root", "../..")).resolve())' "$CONFIG")"
DRAFT_DIR="$WORKSPACE_ROOT/draft"
POLISHED_DIR="$WORKSPACE_ROOT/polished_v3"

if [[ ! -d "$POLISHED_DIR" ]]; then
    echo "[ERROR] polished_v3/ 不存在: $POLISHED_DIR"
    exit 1
fi

if [[ ! -d "$DRAFT_DIR" ]]; then
    echo "[INFO] workspace draft/ 不存在；当前工作区直接以 polished_v3/ 为正文真源。"
    echo "[INFO] workspace_root: $WORKSPACE_ROOT"
    exit 0
fi

diff -qr "$DRAFT_DIR" "$POLISHED_DIR" || true
