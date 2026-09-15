# AGENTS.md — AI usage guide

Machine-oriented shortcut. Source of truth: `openapi.yaml` (contract) and `API.md` (prose detail). This file duplicates nothing new — only surfaces the facts most needed to call the API without reading both in full.

## Base URLs

- REST: `https://api.bookmate.ru/api/v5` (same backend as `api.bookmate.yandex.net/api/v5`)
- GraphQL (mobile): `https://api-gateway.bookmate.yandex.net/graphql` — persisted-query whitelist only, arbitrary queries rejected

## Authentication

- Header: `Auth-Token: y0_AgAAAA...` (Yandex OAuth token, see API.md §2)
- Anonymous (no header) works for: `search`, `/users/{id}` and its subresources, `/books/{uuid}`, `/catalog`
- Anonymous requests require: `User-Agent: okhttp/4.12.0`, `Accept-Encoding: identity` (not `gzip`)
- Anonymous responses always return `in_library`/`in_wishlist` as empty/`false`

## Most useful operations

- `GET /<resource>/search?query=...&page=&per_page=` — resource ∈ `books|audiobooks|comicbooks|series|authors`. Param is `query`, not `q`. `per_page` max 50.
- `GET /search?query=...` — cross-resource search, response key `search`.
- `GET /books/{uuid}` — book card, key `book`.
- `GET /users/{id}` — public profile. `{id}` = numeric id, UUID, or profile alias (response field `login`, not the Yandex account login).
- `GET /users/{id}/books` — public library.
- `GET /profile` — own profile (auth required).
- `GET /profile/library_cards?page=&per_page=` — own library cards (auth required). `per_page` sets page size, `page=2` returns a genuinely non-overlapping next page. Do not use to check "is book X already in library" — use the `POST` response below instead.
- `POST /profile/library_cards {"book_uuid":"..."}` — add book. `422 {"errors":"..."}` (not `409`) if already present — reliable "already tracked" signal.
- `PUT /profile/library_cards/{uuid} {"lc":{"uuid","progress","state","finished_at"}}` — set progress/finished state.

## Known broken / nonexistent — do not retry

- `GET /profile/reading_achievements` → `410 Gone`
- `GET /profile/series/following` (no id) → `404`
- `GET /users/{id}/library_cards` → `500` + HTML (use `/profile/library_cards` for own account)
- `/main`, `/main_screen`, `/widgets`, `/collections`, `/genres`, `/topics`, `/profile/followings`, `/profile/followers`, `/profile/subscriptions`, `/profile/devices`, `/profile/payments`, `/profile/subscription` → `404`
- Content-decryption endpoints (`content/v4`, `metadata/v4`, `playlists.json`, comicbook `metadata.json`) — intentionally out of scope, not a gap

## Search gotchas

- Fuzzy matching: `Дюна` also returns `Долина Дюн` — normalize/filter client-side.
- Do not put the author name in the query string — tokens are AND-combined and narrow results incorrectly. Search by title, filter by author locally.
- If total results < `per_page`, all results are on page 1; page 2 is empty.

## Error shape

`{"error": {"code": N, "message": "..."}}` for most resource errors (`components/schemas/Error` in `openapi.yaml`). Some write endpoints return a flat `{"errors": "..."}` instead — documented per-endpoint, not a general schema.

## Verification semantics

- `x-verified: true` + `x-verified-date` on an `openapi.yaml` operation = confirmed against a live response.
- `x-verified: false` = sourced from a third-party client (see API.md §7), not independently confirmed.

## Task recipes

- **Find a book:** `GET /books/search?query=<title>&per_page=20`.
- **Find all books by an author:** `GET /authors/search?query=<name>` → `GET /authors/{uuid}/books?role=author` (`role` required, else `422`).
- **Export own library:** `GET /profile` → `GET /profile/library_cards?page=&per_page=` → `GET /books/{uuid}` per item for extra metadata if needed.

## Out of scope

No SDK/client code in this repo — OpenAPI + Markdown only, language-agnostic.
