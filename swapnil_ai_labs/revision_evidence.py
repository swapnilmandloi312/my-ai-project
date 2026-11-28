"""Read-only Git evidence and durable local receipts for revision reviews."""

import json
import os
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
    # Only pass OS variables Git needs to start. Repository selection and
    # configuration must never come from the caller's Git environment.
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR") if key in os.environ}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1",
               GIT_ALLOW_PROTOCOL="")
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", "-C", checkout, "cat-file", "-t", revision],
            check=True, capture_output=True, text=True, timeout=5, env=env,
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
