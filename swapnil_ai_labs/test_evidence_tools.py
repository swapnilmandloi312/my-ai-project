import json
import unittest
from unittest.mock import patch

from swapnil_ai_labs.evidence_tools import EXPORT_SCHEMAS, encode_deliverable, execute_read_only
from swapnil_ai_labs.forty_profiles import PROFILES


class EvidenceToolsTests(unittest.TestCase):
    def test_each_export_category(self):
        for category, tool in EXPORT_SCHEMAS.items():
            with self.subTest(category=category):
                check = PROFILES[category].checks[0]
                inputs = {check: "approved-export:record-1"}
                result = json.loads(encode_deliverable(execute_read_only(category, tool, inputs)))
                self.assertEqual(result["recorded_evidence"], inputs)
                self.assertEqual(set(result["missing_checks"]), set(PROFILES[category].checks) - {check})
                self.assertTrue(result["requires_review"])

    def test_rejects_unregistered_tools_and_invalid_references(self):
        category = "research"
        tool = EXPORT_SCHEMAS[category]
        for args in (
            (category, "git_revision", {}),
            ("security", tool, {}),
            (category, tool, {"unknown": "reference"}),
            (category, tool, {"hypothesis": "synthetic:fixture"}),
            (category, tool, {"hypothesis": "a\nb"}),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                execute_read_only(*args)
        with self.assertRaises(ValueError):
            encode_deliverable({"body": "x" * 16384})

    @patch("swapnil_ai_labs.public_github_evidence.http.client.HTTPSConnection")
    def test_public_github_yields_separate_deliverables(self, connect):
        revision = "f" * 40
        response = connect.return_value.getresponse.return_value
        response.status = 200
        response.getheader.return_value = '<next>; rel="next"'
        response.read.return_value = json.dumps({
            "sha": revision,
            "files": [{"filename": "docs/runbook.md"}, {"filename": "src/main.py"}],
            "stats": {"additions": 4, "deletions": 1},
        }).encode()
        refs = {"source_revision": revision}
        engineering = execute_read_only("engineering", "git_revision", refs, public_github=True)
        writing = execute_read_only("technical_writing", "git_revision", refs, public_github=True)
        self.assertEqual(engineering["recorded_evidence"], refs)
        self.assertEqual(engineering["source_evidence"]["line_changes"], {"additions": 4, "deletions": 1})
        self.assertTrue(engineering["source_evidence"]["paths_truncated"])
        self.assertEqual(writing["source_evidence"]["documentation_paths"], ["docs/runbook.md"])
        self.assertEqual(writing["source_evidence"]["other_paths_reviewed"], 1)
        connect.assert_called_with("api.github.com", timeout=5)
        method, path = connect.return_value.request.call_args.args
        self.assertEqual(method, "GET")
        self.assertTrue(path.startswith("/repos/swapnilmandloi312/my-ai-project/commits/"))
        self.assertNotIn("Authorization", connect.return_value.request.call_args.kwargs["headers"])
        response.status = 302
        with self.assertRaisesRegex(ValueError, "unavailable"):
            execute_read_only("engineering", "git_revision", refs, public_github=True)
