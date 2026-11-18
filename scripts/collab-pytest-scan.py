"""Read pytest config and test markers with real parsers for scripts/collab-lessons.mjs (#672).

Fix-forward #672 (Codex on #668): regular expressions missed a multiline `addopts` string or
array, a blank line or comment inside a marker list, a second `pytestmark` assignment and blank
lines inside a multiline `skipif`. This helper parses the TOML with `tomllib` and the test file
with `ast`, so the lessons register counts a pytest only when CI really collects and runs it. It
reads the files it is given and prints one JSON object; no network, no imports of the code under
test.

Usage (run with `python3 -I`, Python 3.11 or newer):
  collab-pytest-scan.py config <apps/api dir>   -> {"ok": bool, "reasons": [...]}
  collab-pytest-scan.py test <file> <name>      -> {"exists", "skipped", "reasons"}
"""

from __future__ import annotations

import ast
import json
import shlex
import sys
import tomllib
from pathlib import Path

# Options that drop, select or stop collected tests. A value glued to a short option ("-kfoo") or
# given with "=" ("--deselect=x") counts too.
DROP_SHORT = ("-k", "-m")
DROP_LONG = (
    "--ignore",
    "--ignore-glob",
    "--deselect",
    "--lf",
    "--last-failed",
    "--sw",
    "--stepwise",
    "--co",
    "--collect-only",
    "--sw-skip",
    "--stepwise-skip",
)
# Config keys that change which files or functions are collected. Defaults are accepted.
COLLECT_DEFAULTS = {
    "python_files": [["test_*.py", "*_test.py"], ["test_*.py"]],
    "python_functions": [["test"], ["test_*"]],
    "python_classes": [["Test"], ["Test*"]],
}
# Files pytest reads before pyproject.toml; any of them overrides the checked config.
OVERRIDING_CONFIGS = ("pytest.ini", ".pytest.ini", "tox.ini", "setup.cfg")


def _tokens(value: object) -> list[str] | None:
    if isinstance(value, str):
        try:
            return shlex.split(value)
        except ValueError:
            return None
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        out: list[str] = []
        for v in value:
            try:
                out.extend(shlex.split(v))
            except ValueError:
                return None
        return out
    return None


def _drops(token: str) -> bool:
    if token in DROP_SHORT or any(token.startswith(s) and len(token) > 2 for s in DROP_SHORT):
        return True
    return any(token == o or token.startswith(f"{o}=") for o in DROP_LONG)


def _as_list(value: object) -> list[str] | None:
    if isinstance(value, str):
        return value.split()
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return list(value)
    return None


def scan_config(api_dir: Path) -> dict[str, object]:
    reasons: list[str] = []
    for name in OVERRIDING_CONFIGS:
        if (api_dir / name).exists():
            reasons.append(f"{name} overrides pyproject.toml")
    try:
        data = tomllib.loads((api_dir / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {"ok": False, "reasons": [f"pyproject.toml unreadable: {type(error).__name__}"]}
    options = data.get("tool", {}).get("pytest", {}).get("ini_options")
    if not isinstance(options, dict):
        return {"ok": False, "reasons": ["no [tool.pytest.ini_options]"]}
    if options.get("testpaths") != ["tests"]:
        reasons.append('testpaths is not ["tests"]')
    tokens = _tokens(options.get("addopts", ""))
    if tokens is None:
        reasons.append("addopts unreadable")
    else:
        reasons.extend(f"addopts {t} can drop tests" for t in tokens if _drops(t))
    for key, defaults in COLLECT_DEFAULTS.items():
        if key in options and _as_list(options[key]) not in defaults:
            reasons.append(f"{key} changes collection")
    return {"ok": not reasons, "reasons": reasons}


SKIP_MARKS = {"skip", "skipif", "xfail"}
SKIP_CALLS = {"skip", "xfail", "importorskip"}


def _mark_name(node: ast.AST) -> str | None:
    """`pytest.mark.skip`, `mark.skip` -> "skip"."""
    if isinstance(node, ast.Attribute) and node.attr in SKIP_MARKS:
        owner = node.value
        if isinstance(owner, ast.Attribute) and owner.attr == "mark":
            return node.attr
        if isinstance(owner, ast.Name) and owner.id == "mark":
            return node.attr
    return None


def _has_skip_mark(node: ast.AST) -> bool:
    return any(_mark_name(n) for n in ast.walk(node))


def _has_skip_call(node: ast.AST) -> bool:
    """`pytest.skip(...)`, `pytest.xfail(...)`, `pytest.importorskip(...)` anywhere inside."""
    for n in ast.walk(node):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        owner = n.func.value
        if n.func.attr in SKIP_CALLS and isinstance(owner, ast.Name) and owner.id == "pytest":
            return True
    return False


def _targets(stmt: ast.stmt) -> list[ast.expr]:
    if isinstance(stmt, ast.Assign):
        return list(stmt.targets)
    if isinstance(stmt, (ast.AnnAssign, ast.AugAssign)):
        return [stmt.target]
    return []


def scan_test(file: Path, name: str) -> dict[str, object]:
    try:
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
    except (OSError, SyntaxError, ValueError) as error:
        reason = f"unparsable: {type(error).__name__}"
        return {"exists": False, "skipped": True, "reasons": [reason]}
    reasons: list[str] = []
    found: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if stmt.name == name:
                found = stmt  # a later definition replaces an earlier one, as in Python
            continue
        if isinstance(stmt, ast.ClassDef):
            continue
        # Every module-level pytestmark assignment counts, not only the first.
        if any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in _targets(stmt)):
            value = getattr(stmt, "value", None)
            if value is not None and _has_skip_mark(value):
                reasons.append(f"module pytestmark skips (line {stmt.lineno})")
        # pytest.skip(allow_module_level=True), importorskip, also inside an `if` or assignment.
        if _has_skip_call(stmt):
            reasons.append(f"module-level pytest skip call (line {stmt.lineno})")
    if found is None:
        return {"exists": False, "skipped": False, "reasons": reasons}
    if any(_has_skip_mark(d) for d in found.decorator_list):
        reasons.append(f"decorator skips {name}")
    if any(_has_skip_call(s) for s in found.body):
        reasons.append(f"{name} calls pytest.skip/xfail")
    return {"exists": True, "skipped": bool(reasons), "reasons": reasons}


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "config":
        result = scan_config(Path(argv[1]))
    elif len(argv) == 3 and argv[0] == "test":
        result = scan_test(Path(argv[1]), argv[2])
    else:
        sys.stderr.write(__doc__ or "")
        return 2
    sys.stdout.write(json.dumps(result) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
