-- Narrow repair applied through Supabase migration pin_existing_content_guard_search_paths
-- on 2026-10-11. Does not advance the repository's Alembic head.
-- Both functions were verified SECURITY INVOKER with no unqualified object references.
ALTER FUNCTION public.guard_content_revision_history() SET search_path = pg_catalog;
ALTER FUNCTION public.guard_content_audit_history() SET search_path = pg_catalog;

-- Expected: both proconfig={search_path=pg_catalog}, prosecdef=false.
SELECT p.proname, p.proconfig, p.prosecdef
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname IN ('guard_content_revision_history', 'guard_content_audit_history');
