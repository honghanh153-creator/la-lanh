"""Compare Tarot legacy copy tables with production release 836222282dfc (see ../2026-10-18-tarot-legacy-copy-pin.md).

Usage from apps/api: PYTHONPATH=. uv run python <this file> <dir containing release836/old_*.py>
"""
import importlib.util, json, sys, hashlib
from scripts.fallback_approval import canonical, _SKIP
from app.domains.tarot import meaning_brief, voice, examples
from app.domains.tarot.engine import _POSITIONS
SP = sys.argv[1]
def load(name):
    spec = importlib.util.spec_from_file_location(f"old_{name}", f"{SP}/release836/old_{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def digest(v): return hashlib.sha256(json.dumps(canonical(v), ensure_ascii=False, sort_keys=True).encode()).hexdigest()
ok = True
for name, new in (("voice", voice), ("examples", examples)):
    old = load(name)
    names = [n for n in vars(old) if n.isupper() or (n.startswith("_") and n[1:].isupper())]
    for n in sorted(names):
        o, c = getattr(old, n), getattr(new, n, None)
        if canonical(o) is _SKIP: continue
        same = digest(o) == digest(c); ok &= same
        print(f"{name}.{n}: {'identical' if same else 'DIFFERENT'}")
old = load("meaning_brief")
for n in ("_GOALS", "_DEFAULT_GOAL", "_GOAL_ACTIONS", "_LINKS"):
    same = digest(getattr(old, n)) == digest(getattr(meaning_brief, n)); ok &= same
    print(f"meaning_brief.{n}: {'identical' if same else 'DIFFERENT'}")
keys = sorted({k for p in _POSITIONS.values() for k, _ in p} | {"unknown"})
goals = [*old._GOALS, old._DEFAULT_GOAL]
same = all(old.goal_action(g, k) == meaning_brief.goal_action(meaning_brief.goal_by_key(g.key), k) for g in goals for k in keys)
ok &= same; print(f"meaning_brief.goal_action over {len(goals)} goals x {len(keys)} positions: {'identical' if same else 'DIFFERENT'}")
src = open(f"{SP}/release836/old_meaning_brief.py").read()
limits = all(l in src for l in meaning_brief.BRIEF_LIMITS); ok &= limits
print(f"meaning_brief.BRIEF_LIMITS present verbatim in release source: {limits}")
print("ALL IDENTICAL" if ok else "MISMATCH")
