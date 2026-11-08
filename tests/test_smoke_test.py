"""Regression checks: HTTP 200 alone must never make a broken search pass."""

import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import smoke_test


class Response:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, payload):
        self.body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class SmokeTests(unittest.TestCase):
    def run_smoke(self, replacements=None):
        replies = [
            {"data": {"search": {"cursor": "1,25", "page": [
                {"__typename": "TextBook", "book": {"initUuid": "public-id", "name": "Book"}}
            ]}}},
            {"data": {"search": {"cursor": "1,25", "page": [
                {"__typename": "Person", "uuid": "author-id", "name": "Author"}
            ]}}},
            {"topics": []},
            {"book": {"uuid": smoke_test.BOOK_UUID, "title": "Public book"}},
        ]
        for index, value in (replacements or {}).items():
            replies[index] = copy.deepcopy(value)
        def respond(*args, **kwargs):
            reply = replies.pop(0)
            if isinstance(reply, Exception):
                raise reply
            return Response(reply)
        output = io.StringIO()
        with patch("smoke_test.urllib.request.urlopen", side_effect=respond) as request:
            with contextlib.redirect_stdout(output):
                status = smoke_test.main()
        self.assertEqual(request.call_count, 4, "Card/catalog must run even when search fails")
        return status, output.getvalue(), request.call_args_list

    def test_healthy_metadata_and_correct_request(self):
        status, output, requests = self.run_smoke()
        self.assertEqual(status, 0)
        self.assertIn("4/4 checks passed", output)
        for call, kind in zip(requests[:2], ("TEXTBOOK", "AUTHOR")):
            request = call.args[0]
            self.assertEqual(request.full_url, smoke_test.SEARCH_URL)
            self.assertEqual(request.get_method(), "POST")
            self.assertNotIn("auth-token", {key.lower() for key in request.headers})
            payload = json.loads(request.data)
            self.assertEqual(payload["operationName"], "Search")
            self.assertEqual(payload["variables"]["type"], kind)
            self.assertEqual(payload["variables"]["cursor"], "")

    def test_200_empty_object_is_failure_and_card_still_runs(self):
        status, output, _ = self.run_smoke({0: {}, 1: {}})
        self.assertEqual(status, 1)
        self.assertIn("keys=[]", output)
        self.assertIn("OK: book card", output)
        self.assertIn("2/4 checks passed", output)

    def test_graphql_errors_with_partial_data_fail(self):
        payload = {"errors": [{"message": "Whitelist: query not found"}],
                   "data": {"search": {"cursor": "", "page": []}}}
        status, output, _ = self.run_smoke({0: payload})
        self.assertEqual(status, 1)
        self.assertIn("GraphQL errors", output)

    def test_empty_or_wrong_shape_results_fail(self):
        for page in ([], {}, "results", None):
            with self.subTest(page=page):
                status, _, _ = self.run_smoke({0: {"data": {"search": {"cursor": "", "page": page}}}})
                self.assertEqual(status, 1)

    def test_invalid_json_and_transport_errors_fail(self):
        for reply in (b"<html>unavailable</html>", urllib.error.URLError("unavailable")):
            with self.subTest(reply=reply):
                status, _, _ = self.run_smoke({0: reply})
                self.assertEqual(status, 1)

    def test_wrong_metadata_shapes_fail(self):
        for replacements in ({2: {"topics": {}}}, {3: {"book": {"uuid": "other"}}}):
            with self.subTest(replacements=replacements):
                status, _, _ = self.run_smoke(replacements)
                self.assertEqual(status, 1)


if __name__ == "__main__":
    unittest.main()
