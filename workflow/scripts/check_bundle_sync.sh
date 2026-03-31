#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "$ROOT/workflow_bundle/workflow/scripts/root_compat_manifest.sh"
STATUS=0

check_wrapper_contains() {
    local relative_path="$1"
    local expected="$2"
    local label="$3"
    local abs_path="$ROOT/$relative_path"

    if [[ ! -f "$abs_path" ]]; then
        echo "[FAIL] missing compatibility wrapper: $relative_path"
        STATUS=1
        return
    fi

    if grep -Fq "$expected" "$abs_path"; then
        echo "[PASS] $label: $relative_path"
        return
    fi

    echo "[FAIL] missing $label: $relative_path"
    echo "       expected snippet: $expected"
    STATUS=1
}

check_directory_mirror() {
    local left="$1"
    local right="$2"
    local label="$3"
    local diff_output

    if [[ ! -d "$left" ]]; then
        echo "[FAIL] missing mirror directory: $left"
        STATUS=1
        return
    fi

    if [[ ! -d "$right" ]]; then
        echo "[FAIL] missing authoritative directory: $right"
        STATUS=1
        return
    fi

    diff_output="$(diff -qr --exclude='__pycache__' --exclude='*.pyc' "$left" "$right" || true)"
    if [[ -z "$diff_output" ]]; then
        echo "[PASS] $label"
        return
    fi

    echo "[FAIL] $label"
    printf '%s\n' "$diff_output"
    echo "       hint: run \`bash workflow_bundle/workflow/scripts/sync_root_compat.sh\` after reviewing bundle-side changes."
    STATUS=1
}

echo "[INFO] checking root compatibility wrappers"

for entry in "${ROOT_COMPAT_PY_WRAPPERS[@]}"; do
    IFS='|' read -r target_rel bundle_rel <<< "$entry"
    check_wrapper_contains "$target_rel" "$ROOT_COMPAT_GENERATOR_MARKER" "wrapper contains generator marker"
    check_wrapper_contains "$target_rel" "$bundle_rel" "wrapper points to bundle target"
done

for entry in "${ROOT_COMPAT_SH_WRAPPERS[@]}"; do
    IFS='|' read -r target_rel bundle_rel <<< "$entry"
    check_wrapper_contains "$target_rel" "$ROOT_COMPAT_GENERATOR_MARKER" "wrapper contains generator marker"
    check_wrapper_contains "$target_rel" "$bundle_rel" "wrapper points to bundle target"
done

echo "[INFO] checking mirrored core sources"
check_directory_mirror "$ROOT/tools/core" "$ROOT/workflow_bundle/tools/core" "root tools/core mirrors bundle tools/core"

if [[ "$STATUS" -ne 0 ]]; then
    echo "[FAIL] bundle sync check failed"
    exit "$STATUS"
fi

echo "[PASS] bundle sync check passed"
