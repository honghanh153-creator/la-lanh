from importlib import import_module
from io import StringIO
from unittest.mock import patch

from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_private_policy_migration_has_no_implicit_activation_or_destructive_rollback() -> None:
    migration = import_module("migrations.versions.20261010_0032_history_retention")
    assert migration.down_revision == "20261010_0031"
    with (
        patch.object(migration.op, "create_table") as table,
        patch.object(migration.op, "create_index"),
        patch.object(migration.op, "add_column") as column,
        patch.object(migration.op, "alter_column") as alter,
        patch.object(migration.op, "execute") as execute,
    ):
        migration.upgrade()
    assert table.call_args.args[0] == "history_retention_policies"
    assert column.call_args.args[0] == "mood_check_ins"
    assert column.call_args.args[1].name == "created_at"
    assert alter.call_args.kwargs["nullable"] is False
    assert str(alter.call_args.kwargs["server_default"]) == "CURRENT_TIMESTAMP"
    sql = "\n".join(call.args[0] for call in execute.call_args_list)
    assert "SET created_at = checked_in_at" in sql
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "FROM PUBLIC" in sql
    assert "'anon', 'authenticated'" in sql
    assert "INSERT" not in sql and "DELETE" not in sql
    with patch.object(migration.op, "execute") as execute:
        migration.downgrade()
    execute.assert_not_called()


def test_history_migration_compiles_postgres_sql_without_database_or_settings() -> None:
    migration = import_module("migrations.versions.20261010_0032_history_retention")
    output = StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    with Operations.context(context):
        migration.upgrade()
    sql = output.getvalue()
    assert "CREATE TABLE history_retention_policies" in sql
    assert "REFERENCES guest_sessions (id) ON DELETE CASCADE" in sql
    assert "ALTER TABLE mood_check_ins ALTER COLUMN created_at SET NOT NULL" in sql
    assert "ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP" in sql
    assert "ENABLE ROW LEVEL SECURITY" in sql and "REVOKE ALL" in sql
