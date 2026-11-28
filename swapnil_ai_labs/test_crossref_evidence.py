import json
import unittest
from unittest.mock import patch

from swapnil_ai_labs.crossref_evidence import HOST, MAX_BYTES, bibliography


class CrossrefEvidenceTests(unittest.TestCase):
    @patch("swapnil_ai_labs.crossref_evidence.http.client.HTTPSConnection")
    def test_extracts_citation_from_fixed_public_endpoint(self, https):
        connection = https.return_value
        response = connection.getresponse.return_value
        response.status = 200
        response.read.return_value = json.dumps({"status": "ok", "message": {
            "DOI": "10.5555/TEST", "title": ["Evidence and methods"],
            "container-title": ["Journal"], "issued": {"date-parts": [[2024, 1]]},
            "author": [{"given": "A.", "family": "Researcher"}] * 9,
            "type": "journal-article",
        }}).encode()
        result = bibliography("10.5555/test")
        https.assert_called_once_with(HOST, timeout=6)
        self.assertEqual(connection.request.call_args.args, ("GET", "/works/10.5555%2Ftest"))
        self.assertNotIn("Authorization", connection.request.call_args.kwargs["headers"])
        response.read.assert_called_once_with(MAX_BYTES + 1)
        connection.close.assert_called_once()
        self.assertEqual(result["title"], "Evidence and methods")
        self.assertEqual(result["publication_year"], 2024)
        self.assertEqual(result["authors"], ["A. Researcher"] * 8)
        self.assertTrue(result["author_list_truncated"])

    @patch("swapnil_ai_labs.crossref_evidence.http.client.HTTPSConnection")
    def test_rejects_unapproved_inputs_and_bad_responses(self, https):
        for doi in ("", "https://example.test/10.5555/example", "10.5555/id?x=1"):
            with self.subTest(doi=doi), self.assertRaises(ValueError):
                bibliography(doi)
        https.assert_not_called()
        response = https.return_value.getresponse.return_value
        for status, body in (
            (302, b""),
            (429, b""),
            (200, b"x" * (MAX_BYTES + 1)),
            (200, b"invalid json"),
            (200, b'{"status":"ok","message":{"DOI":"10.5555/other","title":["Wrong"]}}'),
        ):
            response.status = status
            response.read.return_value = body
            with self.subTest(status=status), self.assertRaises(ValueError):
                bibliography("10.5555/test")
