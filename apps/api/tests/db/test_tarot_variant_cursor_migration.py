from importlib import import_module
from unittest.mock import MagicMock, patch


def test_tarot_variant_cursor_is_private_and_goes_with_the_guest() -> None:
    migration = import_module("migrations.versions.20261018_0037_tarot_variant_cursors")
    assert migration.down_revision == "20261011_0036"
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    with (
        patch.object(migration.op, "create_table") as table,
        patch.object(migration.op, "execute") as execute,
        patch.object(migration.op, "get_bind", return_value=bind),
    ):
        migration.upgrade()
    assert table.call_args.args[0] == "tarot_variant_cursors"
    columns = {column.name: column for column in table.call_args.args[1:]}
    assert set(columns) == {"guest_id", "next_position"}
    assert columns["guest_id"].primary_key
    (foreign_key,) = columns["guest_id"].foreign_keys
    assert foreign_key.target_fullname == "guest_sessions.id" and foreign_key.ondelete == "CASCADE"
    sql = "\n".join(call.args[0] for call in execute.call_args_list)
    assert "ENABLE ROW LEVEL SECURITY" in sql and "REVOKE ALL" in sql
    with patch.object(migration.op, "execute") as execute:
        migration.downgrade()
    execute.assert_not_called()
