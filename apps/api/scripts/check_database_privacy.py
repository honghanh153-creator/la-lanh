"""Fail releases when backend tables are reachable by browser database roles."""

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check_database_privacy() -> None:
    engine = create_async_engine(os.environ["LA_LANH_DATABASE_URL"], pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            violations = await connection.scalar(
                text("""
                SELECT count(*) FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relkind = 'r'
                AND (NOT c.relrowsecurity OR EXISTS (
                    SELECT 1 FROM pg_roles r WHERE r.rolname IN ('anon', 'authenticated')
                    AND has_table_privilege(r.oid, c.oid,
                        'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
                ))
            """)
            )
            if violations:
                raise RuntimeError("backend tables lack Data API isolation")
            defaults = await connection.scalar(
                text("""
                SELECT count(*) FROM pg_default_acl d
                JOIN pg_namespace n ON n.oid = d.defaclnamespace
                CROSS JOIN LATERAL aclexplode(d.defaclacl) a
                WHERE n.nspname = 'public' AND d.defaclobjtype = 'r'
                AND d.defaclrole = (SELECT oid FROM pg_roles WHERE rolname = current_user)
                AND (a.grantee = 0 OR a.grantee IN (
                    SELECT oid FROM pg_roles WHERE rolname IN ('anon', 'authenticated')
                ))
                """)
            )
            if defaults:
                raise RuntimeError("new backend tables inherit browser access")
    finally:
        await engine.dispose()


def main() -> int:
    try:
        asyncio.run(check_database_privacy())
    except Exception as error:
        print(f"database-privacy-check-failed:{type(error).__name__}")
        return 1
    print("database-privacy-isolation-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
