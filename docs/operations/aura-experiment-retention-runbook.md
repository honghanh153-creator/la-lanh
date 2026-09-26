# Aura experiment retention runbook

## Promise

Held experiments and their optional outcomes are physically removed no later than 30 days after creation. The application sets `expires_at` to 29 days 18 hours, leaving a six-hour operational margin.

## Required schedule

Production must run the bounded cleanup command at least once every six hours:

```bash
uv run --directory apps/api python -m scripts.cleanup_expired --batch-size 500
```

Repeat the command while it reports a full batch. Run it with the same database and encryption-key configuration as the API. A deployment is not production-ready without this schedule.

## Monitoring and failure rule

- Record only counts, duration and success/failure; never log decrypted payloads, action text, birth data or guest identifiers.
- Alert when no successful cleanup has completed for 6 hours.
- Block a release when the scheduler cannot be verified.
- If the job misses its window, run it immediately, investigate the scheduler, and verify that no `daily_experiments.expires_at` value older than the current time remains.

## Verification

After deployment, run the cleanup command once and confirm it exits successfully. Database verification should use an aggregate count only:

```sql
SELECT count(*) FROM daily_experiments WHERE expires_at <= now();
```

The expected result after cleanup drains all batches is `0`.
