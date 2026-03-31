#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "$ROOT/workflow_bundle/workflow/scripts/root_compat_manifest.sh"
SOURCE_DIR="$ROOT/workflow_bundle/tools/core/"
TARGET_DIR="$ROOT/tools/core/"

write_python_wrapper() {
    local target_path="$1"
    local bundle_rel="$2"

    mkdir -p "$(dirname "$target_path")"
    cat > "$target_path" <<EOF
from __future__ import annotations

# $ROOT_COMPAT_GENERATOR_MARKER

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    bundle_entry = repo_root / "$bundle_rel"
    if not bundle_entry.exists():
        print(f"workflow bundle entry not found: {bundle_entry}", file=sys.stderr)
        return 1
    print("[compat] delegating to \`python3 $bundle_rel ...\`", file=sys.stderr)
    completed = subprocess.run([sys.executable, str(bundle_entry), *sys.argv[1:]], check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
EOF
    echo "[PASS] regenerated python wrapper: ${target_path#$ROOT/}"
}

write_shell_wrapper() {
    local target_path="$1"
    local bundle_rel="$2"

    mkdir -p "$(dirname "$target_path")"
    cat > "$target_path" <<EOF
#!/usr/bin/env bash
set -euo pipefail

# $ROOT_COMPAT_GENERATOR_MARKER

ROOT="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")/../.." && pwd)"
exec bash "\$ROOT/$bundle_rel" "\$@"
EOF
    chmod +x "$target_path"
    echo "[PASS] regenerated shell wrapper: ${target_path#$ROOT/}"
}

if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "[FAIL] authoritative bundle core directory not found: $SOURCE_DIR"
    exit 1
fi

mkdir -p "$TARGET_DIR"

echo "[INFO] syncing root compatibility mirror from bundle"
echo "[INFO] source: $SOURCE_DIR"
echo "[INFO] target: $TARGET_DIR"

rsync -av --delete --exclude='__pycache__/' --exclude='*.pyc' "$SOURCE_DIR" "$TARGET_DIR"

echo "[PASS] root tools/core mirror refreshed from workflow_bundle/tools/core"

echo "[INFO] regenerating root compatibility wrappers"
for entry in "${ROOT_COMPAT_PY_WRAPPERS[@]}"; do
    IFS='|' read -r target_rel bundle_rel <<< "$entry"
    write_python_wrapper "$ROOT/$target_rel" "$bundle_rel"
done

for entry in "${ROOT_COMPAT_SH_WRAPPERS[@]}"; do
    IFS='|' read -r target_rel bundle_rel <<< "$entry"
    write_shell_wrapper "$ROOT/$target_rel" "$bundle_rel"
done

echo "[PASS] root compatibility wrappers refreshed from manifest"
