# Changelog

## 2026-09-15

### Added
- `CHANGELOG.md`.
- `AGENTS.md` — machine-oriented API usage guide.
- `.github/workflows/smoke-test.yml` — anonymous-endpoint smoke test, biweekly + on `openapi.yaml` push to `main`, opens/updates a GitHub issue on failure.

### Fixed
- `GET /profile/library_cards` pagination: `offset`/`limit` above ~20 still do nothing, but `page`/`per_page` works correctly for full listing — documented in `API.md`, `openapi.yaml`, and `AGENTS.md`.
