"""Read-only Git evidence and durable local receipts for revision reviews."""

import json
import re
import sqlite3
import subprocess
from contextlib import closing


CATEGORIES = frozenset({"engineering", "technical_writing"})


def revision_receipt(checkout, category, revision):
    """Resolve an immutable commit in a host-selected checkout."""
    if category not in CATEGORIES:
        raise ValueError("category has no revision adapter")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise ValueError("full commit object ID required")
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", "-C", checkout, "cat-file", "-t", revision],
            check=True, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        raise ValueError("commit unavailable") from None
    if result.stdout.strip() != "commit":
        raise ValueError("object is not a commit")
    return {
        "category": category,
        "tool": "git",
        "source_revision": revision,
        "kind": "revision_receipt",
    }


def persist_receipt(database, checkout, category, revision):
    """Store an idempotent receipt in a private, workspace-local database."""
    receipt = revision_receipt(checkout, category, revision)
    with closing(sqlite3.connect(database, timeout=5)) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS revision_receipts (
                category TEXT NOT NULL,
                revision TEXT NOT NULL,
                receipt TEXT NOT NULL,
                PRIMARY KEY (category, revision)
            )
        """)
        db.execute(
            "INSERT INTO revision_receipts VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
            (category, revision, json.dumps(receipt, sort_keys=True)),
        )
    return receipt
