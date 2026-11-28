import os
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from swapnil_ai_labs.forty_profiles import PROFILES, evaluate
from swapnil_ai_labs.revision_evidence import CATEGORIES, persist_receipt, revision_receipt

MATRIX = Path(__file__).resolve().parents[1] / "docs/AGENT_ACCEPTANCE_MATRIX.md"


class AcceptanceTests(unittest.TestCase):
    def test_all_profiles_and_matrix(self):
        rows = [line.split("`")[1] for line in MATRIX.read_text().splitlines()
                if line.startswith("| `")]
        self.assertEqual(rows, sorted(PROFILES))
        self.assertEqual(len(rows), 40)
        for category, profile in PROFILES.items():
            with self.subTest(category=category):
                self.assertEqual(set(evaluate(category, {})["missing"]), set(profile.checks))
                result = evaluate(category, dict.fromkeys(profile.checks, "synthetic:fixture"))
                self.assertEqual(result["status"], "ready_for_independent_review")
                self.assertEqual(result["scope"], "synthetic")
                self.assertFalse(result["verified_completion"])

    def test_git_receipts_persist_once_per_category(self):
        with tempfile.TemporaryDirectory() as checkout:
            def git(*args):
                return subprocess.check_output(["git", "-C", checkout, *args], text=True).strip()

            git("init", "-q")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "fixture")
            revision = git("rev-parse", "HEAD")
            database = Path(checkout) / "receipts.sqlite"
            for category in sorted(CATEGORIES):
                with self.subTest(category=category):
                    expected = persist_receipt(database, checkout, category, revision)
                    self.assertEqual(expected["source_revision"], revision)
                    self.assertEqual(expected, persist_receipt(database, checkout, category, revision))
                    for invalid in ("HEAD", "0" * len(revision), git("rev-parse", "HEAD^{tree}")):
                        with self.assertRaises(ValueError):
                            persist_receipt(database, checkout, category, invalid)
            with closing(sqlite3.connect(database)) as db:
                self.assertEqual(db.execute(
                    "SELECT category, revision FROM revision_receipts ORDER BY category"
                ).fetchall(), [(category, revision) for category in sorted(CATEGORIES)])

    def test_git_environment_cannot_redirect_to_a_second_repository(self):
        with tempfile.TemporaryDirectory() as root:
            first = Path(root) / "first"
            second = Path(root) / "second"

            def make_repository(path):
                path.mkdir()
                subprocess.run(["git", "-C", path, "init", "-q"], check=True)
                subprocess.run([
                    "git", "-C", path, "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.test", "-c", "commit.gpgsign=false",
                    "commit", "--allow-empty", "-qm", path.name,
                ], check=True)
                return subprocess.check_output(
                    ["git", "-C", path, "rev-parse", "HEAD"], text=True
                ).strip()

            approved = make_repository(first)
            foreign = make_repository(second)
            for override in (
                {"GIT_DIR": str(second / ".git"), "GIT_WORK_TREE": str(second)},
                {"GIT_OBJECT_DIRECTORY": str(second / ".git" / "objects")},
                {"GIT_ALTERNATE_OBJECT_DIRECTORIES": str(second / ".git" / "objects")},
            ):
                with self.subTest(override=override), patch.dict(os.environ, override):
                    self.assertEqual(revision_receipt(first, "engineering", approved)["source_revision"], approved)
                    with self.assertRaisesRegex(ValueError, "commit unavailable"):
                        revision_receipt(first, "engineering", foreign)
