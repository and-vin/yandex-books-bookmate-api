# Yandex Books / Bookmate API (unofficial)

**Language:** English | [Русский](./README.ru.md)

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![OpenAPI valid](https://github.com/and-vin/yandex-books-bookmate-api/actions/workflows/validate.yml/badge.svg)](https://github.com/and-vin/yandex-books-bookmate-api/actions/workflows/validate.yml)
[![Smoke test](https://github.com/and-vin/yandex-books-bookmate-api/actions/workflows/smoke-test.yml/badge.svg)](https://github.com/and-vin/yandex-books-bookmate-api/actions/workflows/smoke-test.yml)
[![Docs](https://img.shields.io/badge/docs-interactive%20reference-blue)](https://and-vin.github.io/yandex-books-bookmate-api/)

An unofficial, reverse-engineered reference for the Yandex Books / Bookmate REST and GraphQL API. There is no official public API or documentation for this service — this repository documents what has been observed in real client traffic (mobile app and web reader).

**[Browse the interactive API reference →](https://and-vin.github.io/yandex-books-bookmate-api/)** (rendered from `openapi.yaml` with [Redoc](https://redocly.com/redoc))

## What's here

- **[`openapi.yaml`](./openapi.yaml)** — an [OpenAPI 3.0](https://spec.openapis.org/oas/v3.0.3) specification covering REST paths, request/response shapes, and model schemas. Validated with [`openapi-spec-validator`](https://github.com/python-openapi/openapi-spec-validator) and a [consistency check](./scripts/check_openapi_consistency.py) on every push. Every path carries `x-verified-status` (`live` / `extrapolated` / `third-party` / `untested`), so you can tell a fact confirmed against a live response from an assumption carried over from another project.
- **[`API.md`](./API.md)** — everything an OpenAPI document can't express: hosts, authentication (OAuth token vs. cookie session), the two separate GraphQL gateways, response-format gotchas, rate limits, known error shapes, and a list of endpoints that were probed and confirmed **not** to exist.
- **[`AGENTS.md`](./AGENTS.md)** — compact, machine-oriented usage guide for AI agents/LLM clients: base URLs, auth, most-used operations, known-broken endpoints, error shape, task recipes.
- **[`CHANGELOG.md`](./CHANGELOG.md)** — record of changes to this documentation.
- **[`.github/workflows/smoke-test.yml`](./.github/workflows/smoke-test.yml)** — biweekly (and on `openapi.yaml` change) live check of the anonymous endpoints; opens a GitHub issue on failure.

## Why this exists

Yandex Books (the Russian-market side of Bookmate, backend split from international Bookmate since 2022-02-24) has no published API. Existing third-party clients disagree with each other on field names, response shapes, and even whether certain endpoints work at all. This repository cross-checks those claims against live responses wherever possible and records the actual, current behavior — including a documented list of discrepancies found against other open-source clients (see `API.md`, §5).

## Who this is for

Developers building personal tools around a Yandex Books / Bookmate account: library export/sync scripts, reading-stats dashboards, backup tools, bots, or clients in any language — this repo is language-agnostic (plain OpenAPI + Markdown, no code).

## Scope and limits

- **Unofficial and unstable.** This is a private API with no stability guarantees — paths, fields, and the GraphQL operation whitelist can change without notice.
- **Content-decryption endpoints are intentionally not documented** (`content/v4`, `metadata/v4`, `playlists.json`, comicbook `metadata.json`, and the EPUB content-file paths). Formalizing a decrypt contract for paid content would mean documenting a way to circumvent access restrictions and would violate the service's terms of use — see `x-content-extraction-excluded` in `openapi.yaml`.
- Not every path has been verified live; unverified entries are explicitly marked (`x-verified-status: extrapolated` / `third-party` / `untested`) and, where applicable, cite the third-party client or analogous operation they were sourced from (`x-source`).
- Using this API, especially write operations or bulk requests, is entirely at your own risk and subject to the service's terms of use.

## Related open-source clients

`API.md` (§7) lists other independent client implementations this documentation was cross-checked against, covering both the Russian side (`api.bookmate.ru` / `api.bookmate.yandex.net`) and international Bookmate (`bookmate.com`).

## License

See [`LICENSE`](./LICENSE).
