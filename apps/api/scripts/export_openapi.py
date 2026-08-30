import argparse
import json
from pathlib import Path

from app.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPOSITORY_ROOT / "packages" / "contracts" / "openapi" / "v1.json"


def render_openapi() -> str:
    schema = create_app().openapi()
    return f"{json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False)}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the canonical v1 OpenAPI contract.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the committed contract drifts.",
    )
    args = parser.parse_args()
    rendered = render_openapi()

    if args.check:
        if not CONTRACT_PATH.exists() or CONTRACT_PATH.read_text(encoding="utf-8") != rendered:
            print("OpenAPI contract drift detected; run `pnpm contracts:generate`.")
            return 1
        print("OpenAPI contract is current.")
        return 0

    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {CONTRACT_PATH.relative_to(REPOSITORY_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
