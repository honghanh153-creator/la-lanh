from importlib import import_module
from unittest.mock import patch


def test_monthly_spend_migration_is_private_and_preserves_history() -> None:
    migration = import_module("migrations.versions.20261008_0029_rewrite_monthly_spend")
    with (
        patch.object(migration.op, "create_table") as table,
        patch.object(migration.op, "execute") as execute,
    ):
        migration.upgrade()
    assert table.call_args.args[0] == "content_rewrite_spend_months"
    sql = "\n".join(call.args[0] for call in execute.call_args_list)
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "REVOKE ALL" in sql and "['anon', 'authenticated']" in sql
    assert "coalesce(cost_nanos, 0) + coalesce(budget_reserved_cost_nanos, 0)" in sql
    assert "ON CONFLICT (month) DO NOTHING" in sql
    assert "DROP " not in sql and "DELETE " not in sql and "GRANT " not in sql
    with patch.object(migration.op, "execute") as execute:
        assert migration.downgrade() is None
    execute.assert_not_called()
