from importlib import import_module
from unittest.mock import MagicMock, patch


def test_human_tarot_tables_are_private_and_keep_the_ledger_on_guest_deletion() -> None:
    migration = import_module("migrations.versions.20261030_0041_human_tarot")
    assert migration.down_revision == "20261023_0038"
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    with (
        patch.object(migration.op, "create_table") as table,
        patch.object(migration.op, "create_index"),
        patch.object(migration.op, "execute") as execute,
        patch.object(migration.op, "get_bind", return_value=bind),
    ):
        migration.upgrade()
    tables = {call.args[0]: call.args[1:] for call in table.call_args_list}
    assert set(tables) == {"human_tarot_days", "human_tarot_requests", "human_tarot_slots"}

    def foreign_keys(name: str) -> dict[str, str | None]:
        return {
            column.name: next(iter(column.foreign_keys)).ondelete
            for column in tables[name]
            if getattr(column, "foreign_keys", None)
        }

    # The request (question, reading) goes with the guest; the slot only loses its links, so the
    # day's count stays and the Sheet bridge still knows which row to clear.
    assert foreign_keys("human_tarot_requests") == {"guest_id": "CASCADE"}
    assert foreign_keys("human_tarot_slots") == {
        "day": None,
        "guest_id": "SET NULL",
        "request_id": "SET NULL",
    }
    slot_columns = {
        column.name for column in tables["human_tarot_slots"] if hasattr(column, "name")
    }
    assert "question" not in slot_columns and "payload_ciphertext" not in slot_columns
    sql = "\n".join(call.args[0] for call in execute.call_args_list)
    for name in tables:
        assert f"ALTER TABLE public.{name} ENABLE ROW LEVEL SECURITY" in sql
        assert f"REVOKE ALL ON TABLE public.{name} FROM PUBLIC" in sql
    assert "['anon', 'authenticated']" in sql
    with patch.object(migration.op, "execute") as execute:
        migration.downgrade()
    execute.assert_not_called()
