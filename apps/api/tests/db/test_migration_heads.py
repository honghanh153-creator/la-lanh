from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

API_ROOT = Path(__file__).resolve().parents[2]


def test_migrations_have_a_single_head() -> None:
    # Two branches merged on 02.11.2026 left 0040 and 0041 both revising 0038, and
    # `alembic upgrade head` refuses to run with two heads, so a deploy would stop there.
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    heads = ScriptDirectory.from_config(config).get_heads()
    assert len(heads) == 1, f"multiple Alembic heads: {sorted(heads)}"


def test_every_revision_id_is_unique_and_matches_its_file_name() -> None:
    # Two stacked branches both added `20261120_0043` (same id, same parent) on 20.11.2026.
    # Alembic only warns about a duplicate id and then reports two heads, so check the id and the
    # file name directly and say which files clash.
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    revisions = list(ScriptDirectory.from_config(config).walk_revisions())
    ids = [revision.revision for revision in revisions]
    assert len(ids) == len(set(ids)), f"duplicate revision ids: {sorted(ids)}"
    for revision in revisions:
        name = Path(revision.path).name
        assert name.startswith(f"{revision.revision}_"), (revision.revision, name)


def test_migration_history_never_branches() -> None:
    # One head is not enough on its own: a side branch that merges back later still leaves two
    # revisions with the same parent, and `alembic upgrade head` on a half-migrated database
    # would then pick a path by accident.
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    children: dict[str, list[str]] = {}
    for revision in ScriptDirectory.from_config(config).walk_revisions():
        parents = revision.down_revision
        for parent in (parents,) if isinstance(parents, str) else (parents or ()):
            children.setdefault(parent, []).append(revision.revision)
    forks = {parent: sorted(kids) for parent, kids in children.items() if len(kids) > 1}
    assert not forks, f"migrations that share a parent: {forks}"
