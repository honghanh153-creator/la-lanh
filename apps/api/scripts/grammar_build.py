"""Build every content-grammar catalog (G0).

Spec: docs/foundation/la-lanh-content-grammar-spec.md §3.

uv run python -m scripts.grammar_build          # write app/domains/<surface>/grammar/build/
uv run python -m scripts.grammar_build --check  # CI: fail on a build error or committed drift
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from app.domains.grammar.build import BUILD_DIR, CATALOG_FILE, GrammarBuildError, build_surface

DOMAINS = Path(__file__).resolve().parents[1] / "app" / "domains"


def catalogs() -> list[Path]:
    return sorted(path.parent for path in DOMAINS.glob(f"*/grammar/{CATALOG_FILE}"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    problems: list[str] = []
    started = time.monotonic()
    for directory in catalogs():
        name = directory.relative_to(DOMAINS)
        try:
            build = build_surface(directory)
        except GrammarBuildError as error:
            problems += [f"{name}: {reason}" for reason in error.reasons]
            continue
        out = directory / BUILD_DIR
        for file_name, text in build.outputs.items():
            path = out / file_name
            if args.check:
                if not path.exists() or path.read_text() != text:
                    problems.append(f"{name}/{BUILD_DIR}/{file_name} drifted (run grammar:build)")
            else:
                out.mkdir(exist_ok=True)
                path.write_text(text)
        frames = len(build.frames)
        print(f"grammar {name}: {frames} frames, L={build.catalog.schedule_length}, ok")
    if problems:
        sys.exit("grammar build failed:\n- " + "\n- ".join(problems))
    state = "current" if args.check else "written"
    print(f"grammar build {state} in {time.monotonic() - started:.1f}s")


if __name__ == "__main__":
    main()
