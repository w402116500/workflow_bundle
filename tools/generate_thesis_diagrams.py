from __future__ import annotations

import sys

from examples.health_record.generate_thesis_diagrams import main as generate_diagrams_main


def main() -> int:
    print("[compat] use `python3 tools/cli.py example generate-diagrams --example health_record`", file=sys.stderr)
    generate_diagrams_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
