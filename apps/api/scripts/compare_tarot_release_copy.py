"""Compare pinned legacy Tarot copy with a historical release (default: production 836222282dfc).

Record: docs/reviews/2026-10-18-tarot-legacy-copy-pin.md. Usage from apps/api:

    uv run python -m scripts.compare_tarot_release_copy [--release REV] [--historical-dir DIR]

Without ``--historical-dir`` the release files are exported with ``git show`` into a temporary
directory. Historical modules resolve their Tarot sibling imports to the historical files too
(``examples`` imports ``RELATIONSHIP_EXAMPLES`` from the historical ``relationship_readings``), so
no row compares the current code with itself. Only ``app.domains.tarot.models`` (closed enums) is
taken from the current code. Exit status 1 on any mismatch, 0 when everything is identical.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import ExitStack, contextmanager
from hashlib import sha256
from pathlib import Path
from types import ModuleType
from typing import Any

from scripts.fallback_approval import _SKIP, _TABLE_NAME, canonical

RELEASE = "836222282dfc"
PACKAGE = "app.domains.tarot"
# relationship_readings first: examples imports from it.
MODULES = ("relationship_readings", "examples", "voice", "meaning_brief")
_ROOT = Path(__file__).resolve().parents[3]


def export(release: str, destination: Path) -> None:
    if not re.fullmatch(r"[0-9a-f]{7,40}", release):
        raise ValueError("release must be a commit hash")
    for name in MODULES:
        # Fixed argv, no shell; the revision is a validated hash.
        source = subprocess.run(  # noqa: S603
            ["git", "show", f"{release}:apps/api/app/domains/tarot/{name}.py"],  # noqa: S607
            cwd=_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        (destination / f"{name}.py").write_text(source)


@contextmanager
def _as_package_module(name: str, module: ModuleType) -> Iterator[None]:
    """Let historical code import ``app.domains.tarot.<name>`` as the historical module."""

    key = f"{PACKAGE}.{name}"
    saved = sys.modules.get(key)
    sys.modules[key] = module
    try:
        yield
    finally:
        if saved is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = saved


def load_historical(directory: Path) -> dict[str, ModuleType]:
    loaded: dict[str, ModuleType] = {}
    for name in MODULES:
        spec = importlib.util.spec_from_file_location(
            f"historical_{name}", directory / f"{name}.py"
        )
        if spec is None or spec.loader is None:
            raise FileNotFoundError(directory / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        with ExitStack() as stack:
            # Every historical module loaded so far answers its package import path.
            for loaded_name, loaded_module in loaded.items():
                stack.enter_context(_as_package_module(loaded_name, loaded_module))
            spec.loader.exec_module(module)
        loaded[name] = module
    return loaded


def _digest(value: Any) -> str:
    return sha256(
        json.dumps(canonical(value), ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def _tables(module: ModuleType) -> list[str]:
    return sorted(
        name
        for name, value in vars(module).items()
        if _TABLE_NAME.match(name)
        and not name.endswith("VERSION")
        and canonical(value) is not _SKIP
        and not isinstance(value, ModuleType)
    )


def compare(historical: dict[str, ModuleType], current: dict[str, ModuleType]) -> list[str]:
    """Lines "<module>.<table>: identical|DIFFERENT"; tables moved since the release are compared
    through their behaviour (``goal_action``) or verbatim source (``BRIEF_LIMITS``)."""

    lines: list[str] = []
    for name in ("relationship_readings", "examples", "voice"):
        old, new = historical[name], current[name]
        for table in _tables(old):
            if getattr(old, table) is getattr(new, table, None):
                # A row that resolves to the very same object would compare code with itself.
                lines.append(f"{name}.{table}: DIFFERENT (same object, not historical)")
                continue
            same = _digest(getattr(old, table)) == _digest(getattr(new, table, None))
            lines.append(f"{name}.{table}: {'identical' if same else 'DIFFERENT'}")
    old, new = historical["meaning_brief"], current["meaning_brief"]
    for table in ("_GOALS", "_DEFAULT_GOAL", "_GOAL_ACTIONS", "_LINKS"):
        same = _digest(getattr(old, table)) == _digest(getattr(new, table))
        lines.append(f"meaning_brief.{table}: {'identical' if same else 'DIFFERENT'}")
    from app.domains.tarot.engine import _POSITIONS

    keys = sorted({key for positions in _POSITIONS.values() for key, _ in positions} | {"unknown"})
    goals = [*old._GOALS, old._DEFAULT_GOAL]
    same = all(
        old.goal_action(goal, key) == new.goal_action(new.goal_by_key(goal.key), key)
        for goal in goals
        for key in keys
    )
    lines.append(
        f"meaning_brief.goal_action ({len(goals)} goals x {len(keys)} positions): "
        f"{'identical' if same else 'DIFFERENT'}"
    )
    source = Path(old.__file__ or "").read_text()
    same = all(limit in source for limit in new.BRIEF_LIMITS)
    verdict = "identical" if same else "DIFFERENT"
    lines.append(f"meaning_brief.BRIEF_LIMITS (verbatim in release source): {verdict}")
    return lines


def current_modules() -> dict[str, ModuleType]:
    return {name: importlib.import_module(f"{PACKAGE}.{name}") for name in MODULES}


def run(historical_dir: Path) -> int:
    lines = compare(load_historical(historical_dir), current_modules())
    for line in lines:
        print(line)
    mismatches = [line for line in lines if not line.endswith("identical")]
    print("ALL IDENTICAL" if not mismatches else f"MISMATCH ({len(mismatches)})")
    return 1 if mismatches else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--release", default=RELEASE)
    parser.add_argument("--historical-dir", type=Path)
    args = parser.parse_args(argv)
    if args.historical_dir is not None:
        return run(args.historical_dir)
    with tempfile.TemporaryDirectory() as directory:
        export(args.release, Path(directory))
        return run(Path(directory))


if __name__ == "__main__":
    raise SystemExit(main())
