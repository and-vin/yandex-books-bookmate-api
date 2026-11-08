#!/usr/bin/env python3
"""Check public metadata operations; never use account credentials or print payloads."""

import json
import http.client
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SEARCH_URL = "https://books.yandex.ru/node-api/p-graphql/"
REST_URL = "https://api.bookmate.ru/api/v5"
BOOK_UUID = "EyUhheJW"  # Public catalogue fixture, independent of search.
HEADERS = {"User-Agent": "okhttp/4.12.0", "Accept-Encoding": "identity"}


class CheckFailure(Exception):
    pass


def shape(payload):
    description = f"JSON {type(payload).__name__}"
    if isinstance(payload, dict):
        description += f", keys={sorted(payload)}"
    return description


def request_json(url, payload=None):
    headers = dict(HEADERS)
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=25)
    except urllib.error.HTTPError as error:
        # Do not print the error body, which may contain unrelated server data.
        with error:
            raise CheckFailure(f"HTTP {error.code}") from None
    except (urllib.error.URLError, OSError) as error:
        raise CheckFailure(f"transport error ({type(error).__name__})") from None
    with response:
        try:
            body = response.read()
        except (OSError, http.client.HTTPException) as error:
            raise CheckFailure(f"response read error ({type(error).__name__})") from None
        if response.status != 200:
            raise CheckFailure(f"HTTP {response.status}")
        try:
            return json.loads(body)
        except (ValueError, UnicodeError):
            content_type = response.headers.get("Content-Type", "unknown")
            raise CheckFailure(
                f"HTTP 200, invalid JSON ({len(body)} bytes, {content_type})"
            ) from None


def search(term, resource_type):
    try:
        payload = json.loads((ROOT / "examples/search.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CheckFailure(f"cannot load search request ({type(error).__name__})") from None
    payload["variables"] = {"search": term, "cursor": "", "type": resource_type}
    response = request_json(SEARCH_URL, payload)
    if not isinstance(response, dict):
        raise CheckFailure(f"expected GraphQL object; {shape(response)}")
    if response.get("errors") not in (None, []):
        raise CheckFailure(f"GraphQL errors in HTTP 200 response; {shape(response)}")
    data = response.get("data")
    result = data.get("search") if isinstance(data, dict) else None
    page = result.get("page") if isinstance(result, dict) else None
    if not isinstance(page, list) or not page:
        raise CheckFailure(f"expected nonempty data.search.page array; {shape(response)}")
    if not isinstance(result.get("cursor"), str):
        raise CheckFailure("expected data.search.cursor string")
    for item in page:
        expected = "TextBook" if resource_type == "TEXTBOOK" else "Person"
        if not isinstance(item, dict) or item.get("__typename") != expected:
            raise CheckFailure(f"expected {expected} search items")
        record = item.get("book") if resource_type == "TEXTBOOK" else item
        uuid_key = "initUuid" if resource_type == "TEXTBOOK" else "uuid"
        if not isinstance(record, dict) or not all(
            isinstance(record.get(key), str) and record[key] for key in (uuid_key, "name")
        ):
            raise CheckFailure("search item has no usable UUID/name")
    return f"{len(page)} {resource_type} results"


def catalog():
    payload = request_json(REST_URL + "/catalog")
    if not isinstance(payload, dict) or not isinstance(payload.get("topics"), list):
        raise CheckFailure(f"expected topics array; {shape(payload)}")
    return "topics array"


def book_card():
    payload = request_json(REST_URL + "/books/" + BOOK_UUID)
    book = payload.get("book") if isinstance(payload, dict) else None
    if (not isinstance(book, dict) or book.get("uuid") != BOOK_UUID
            or not isinstance(book.get("title"), str) or not book["title"]):
        raise CheckFailure(f"expected public book card; {shape(payload)}")
    return "public book card"


def main():
    checks = [
        ("books search (web GraphQL)", lambda: search("Дюна", "TEXTBOOK")),
        ("authors search (web GraphQL)", lambda: search("Толстой", "AUTHOR")),
        ("catalog (REST)", catalog),
        ("book card (REST)", book_card),
    ]
    failed = 0
    for description, check in checks:
        try:
            detail = check()
        except CheckFailure as error:
            print(f"FAIL: {description}: {error}")
            failed += 1
        else:
            print(f"OK: {description}: {detail}")
    print(f"{len(checks) - failed}/{len(checks)} checks passed")
    return int(failed > 0)


if __name__ == "__main__":
    raise SystemExit(main())
