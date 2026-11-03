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
