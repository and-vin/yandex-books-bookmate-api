# Changelog

## 2026-11-08

### Fixed
- Replaced non-functional REST search examples with the anonymous web GraphQL `Search` operation and an executable JSON request fixture. Legacy REST search returns HTTP 200 with `{}`; valid authentication does not restore the tested books/authors searches.
- Smoke checks now require real GraphQL results, reject GraphQL errors and malformed JSON, and check a public REST book card independently of search. Added regression tests for empty HTTP 200 responses and partial failures.
- Documented web search response fields, content filters and cursor pagination in OpenAPI and both usage guides. Kept the historical REST search schemas, marked deprecated with their current limitation.

## 2026-09-15

### Added
- `CHANGELOG.md`.
- `AGENTS.md` — machine-oriented API usage guide.
- `.github/workflows/smoke-test.yml` — anonymous-endpoint smoke test, biweekly + on `openapi.yaml` push to `main`, opens/updates a GitHub issue on failure.
- `scripts/check_openapi_consistency.py` + a `validate.yml` step — checks `operationId` uniqueness and `x-verified-status`/`x-verified-date`/`x-source` consistency on every push/PR touching `openapi.yaml`.

### Changed
- `x-verified: true/false` replaced with `x-verified-status` (`live` / `extrapolated` / `third-party` / `untested`) across `openapi.yaml`: each unverified path now states why (not run live to avoid mutating data, inferred from an analogous operation, or sourced from a third-party client) and, for the latter two, cites its source in `x-source`.

### Fixed
- `GET /profile/library_cards` pagination: `offset`/`limit` above ~20 still do nothing, but `page`/`per_page` works correctly for full listing — documented in `API.md`, `openapi.yaml`, and `AGENTS.md`. Non-functional `offset`/`limit` params removed from `openapi.yaml`.
- `GET /profile/library_cards` `per_page` cap: silently clamps to 50 (`per_page=51` and above still return 50 cards) — documented as `maximum: 50` in `openapi.yaml`.
