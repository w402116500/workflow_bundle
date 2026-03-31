from __future__ import annotations

import sys

from core.verify_citation_links import main as verify_main


def main() -> int:
    print("[compat] use `python3 tools/cli.py verify ...`", file=sys.stderr)
    return verify_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
