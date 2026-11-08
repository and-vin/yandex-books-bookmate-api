# AGENTS.md — AI usage guide

Machine-oriented shortcut. Source of truth: `openapi.yaml` (contract) and `API.md` (prose detail). This file duplicates nothing new — only surfaces the facts most needed to call the API without reading both in full.

## Base URLs

- REST: `https://api.bookmate.ru/api/v5` (same backend as `api.bookmate.yandex.net/api/v5`)
- GraphQL (mobile): `https://api-gateway.bookmate.yandex.net/graphql` — persisted-query whitelist only, arbitrary queries rejected
- GraphQL (web search): `https://books.yandex.ru/node-api/p-graphql/` — use the exact `Search` request in `examples/search.json`, changing only `variables`.

## Authentication

- Header: `Auth-Token: y0_AgAAAA...` (Yandex OAuth token, see API.md §2)
- Anonymous (no header) works for web GraphQL `Search`, `/users/{id}` and its subresources, `/books/{uuid}`, `/catalog`.
- Legacy REST `/<resource>/search` and `/search` return HTTP 200 with `{}` instead of results. Adding a valid token does not repair the tested books/authors searches.
- Anonymous REST requests require: `User-Agent: okhttp/4.12.0`, `Accept-Encoding: identity` (not `gzip`). Web search needs a JSON request body and `Content-Type: application/json`.
- Anonymous REST responses do not reflect your `in_library`/`in_wishlist`; web search returns `progress: null`.

## Most useful operations

- `POST /node-api/p-graphql/` on `books.yandex.ru` with `examples/search.json`: `variables.search` is the text, `variables.type` is `TEXTBOOK|AUDIOBOOK|COMICBOOK|SERIES|AUTHOR` (omit/null for mixed results), `variables.cursor` starts as `""`. Results: `data.search.page`; carry forward `data.search.cursor` unchanged. Reject `errors` even with HTTP 200.
- Web search items differ from REST: books use `item.book.initUuid` / `item.book.name`; authors use `item.uuid` / `item.name`. Do not read `.objects` from a GraphQL response.
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

- Search may return similar titles — normalize/filter client-side.
- For exact matching, search by title and compare the returned title and authors locally.
- Web search has cursor pagination. Do not send REST `page`/`per_page` parameters to it.

## Error shape

`{"error": {"code": N, "message": "..."}}` for most resource errors (`components/schemas/Error` in `openapi.yaml`). Some write endpoints return a flat `{"errors": "..."}` instead — documented per-endpoint, not a general schema.

## Verification semantics

`x-verified-status` on an `openapi.yaml` operation, one of:

- `live` + `x-verified-date` = confirmed against a live response.
- `extrapolated` + `x-source` = not requested directly, shape inferred from another confirmed operation in this API.
- `third-party` + `x-source` = sourced from a third-party client (see API.md §7), not independently confirmed.
- `untested` = not run live to avoid mutating account data; path/params taken from documented app behavior.

## Task recipes

- **Find a book:** web `Search`, `variables.search=<title>`, `variables.type=TEXTBOOK`; open the REST card using `book.initUuid`.
- **Find all books by an author:** web `Search`, `variables.type=AUTHOR` → `GET /authors/{uuid}/books?role=author` (`role` required, else `422`).
- **Export own library:** `GET /profile` → `GET /profile/library_cards?page=&per_page=` → `GET /books/{uuid}` per item for extra metadata if needed.

## Out of scope

No SDK/client library in this repo — language-agnostic OpenAPI, Markdown and a JSON request fixture. Python scripts are validation/smoke checks.
