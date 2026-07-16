"""Export or verify Papervault's canonical OpenAPI document."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "frontend" / "src" / "lib" / "openapi.json"


def _openapi_json() -> str:
    sys.path.insert(0, str(BACKEND_ROOT))
    os.environ.setdefault(
        "DOCUSENSE_DATA_DIR",
        str(BACKEND_ROOT / ".docsense_data" / "openapi-export"),
    )
    from app.main import app

    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    output = args.output.resolve()
    generated = _openapi_json()

    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != generated:
            print(f"OpenAPI contract is out of date: {output}", file=sys.stderr)
            return 1
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
