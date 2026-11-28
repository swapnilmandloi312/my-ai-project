import json
import unittest

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
