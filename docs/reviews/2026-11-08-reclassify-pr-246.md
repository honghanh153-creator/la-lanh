# PR #246 reclassified S → M (fix-forward #263)

PR #246 (`47cd41a0`) declared **S**. Its middleware in `apps/api/app/api/input_problem.py` turns
bodiless 422 answers into the documented `application/problem+json` body (`code: INPUT_INVALID`,
`Cache-Control: no-store`). The response a client sees changed, so it is at least **M**.

Affected: `apps/api/app/api/v1/routes/radar.py` (three 422 paths, e.g. rejected authorization
attestation) and `apps/api/app/api/v1/routes/la_chung.py` (one path).

## M gates

- G1: the problem body is the one already documented for every other 422 (#170). Status code stays 422.
  Clients that read only the status are unaffected.
- G4: no route, schema or OpenAPI change; one ASGI middleware.
- G6: `apps/api/tests/privacy/test_empty_domain_422_problem.py` covers these paths.
- G7: no session or permission change; the body holds no submitted value, field name or location; no log.
- G8: no new personal data; the change removes a possible leak path rather than adding one.
