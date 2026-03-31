from __future__ import annotations

import sys

from core.build_final_thesis_docx import main as build_main


def main() -> int:
    print("[compat] use `python3 tools/cli.py build ...`", file=sys.stderr)
    build_main(sys.argv[1:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
