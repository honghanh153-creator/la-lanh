from importlib import import_module


def test_private_table_guard_is_server_only_and_idempotent() -> None:
    migration = import_module("migrations.versions.20261008_0028_private_backend_tables")
    sql = migration.protection_sql()
    assert "content_rewrite_jobs" in migration.PRIVATE_TABLES
    assert "birth_profiles" in migration.PRIVATE_TABLES
    assert len(migration.PRIVATE_TABLES) == len(set(migration.PRIVATE_TABLES)) == 30
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "FORCE ROW LEVEL SECURITY" not in sql
    assert "to_regclass" in sql
    assert "REVOKE ALL ON TABLE" in sql
    assert "ALTER DEFAULT PRIVILEGES" in sql
    assert "['anon', 'authenticated']" in sql
    assert "DROP " not in sql and "DELETE " not in sql and "GRANT " not in sql


def test_downgrade_does_not_reopen_private_data() -> None:
    migration = import_module("migrations.versions.20261008_0028_private_backend_tables")
    assert migration.downgrade() is None
