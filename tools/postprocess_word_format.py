from __future__ import annotations

import sys


def main() -> int:
    print("[compat] use `python3 tools/cli.py postprocess ...`", file=sys.stderr)
    try:
        from windows.postprocess_word_format import main as postprocess_main
    except ModuleNotFoundError as exc:
        print(f"windows-only dependency unavailable: {exc}", file=sys.stderr)
        return 1
    return int(postprocess_main(sys.argv[1:]) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
