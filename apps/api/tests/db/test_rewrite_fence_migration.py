from importlib import import_module
from unittest.mock import patch


def test_daily_ledger_and_parent_erasure_links_keep_spend_private() -> None:
    migration = import_module("migrations.versions.20261008_0030_rewrite_fences")
    with (
        patch.object(migration.op, "create_table") as table,
        patch.object(migration.op, "execute") as execute,
        patch.object(migration.op, "add_column"),
        patch.object(migration.op, "create_foreign_key") as foreign_key,
        patch.object(migration.op, "create_index"),
    ):
        migration.upgrade()
    assert table.call_args.args[0] == "content_rewrite_spend_days"
    sql = "\n".join(call.args[0] for call in execute.call_args_list)
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "REVOKE ALL" in sql
    assert sql.index("INSERT INTO public.content_rewrite_spend_days") < sql.index(
        "DELETE FROM public.content_rewrite_jobs"
    )
    assert "DELETE FROM public.content_rewrite_spend" not in sql
    assert {call.args[2] for call in foreign_key.call_args_list} == {
        "guest_sessions",
        "reading_plans",
        "tarot_sessions",
        "radar_requests",
    }
    assert all(call.kwargs["ondelete"] == "CASCADE" for call in foreign_key.call_args_list)
    with patch.object(migration.op, "execute") as execute:
        migration.downgrade()
    execute.assert_not_called()
