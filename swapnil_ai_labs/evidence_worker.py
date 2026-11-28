"""Run a single approved, leased evidence job using the scoped PostgreSQL login."""

import argparse
import json
from subprocess import TimeoutExpired
from uuid import UUID

from swapnil_ai_labs.cloud_worker import sql
from swapnil_ai_labs.evidence_tools import encode_deliverable, execute_read_only


def run_one(checkout=None, *, public_github=False):
    job = json.loads(sql("SELECT coalesce(sal_ops.claim_evidence_job()::text,'null');"))
    if job is None:
        return "idle"
    try:
        body = encode_deliverable(execute_read_only(
            job["category"], job["tool"], job["evidence"], checkout=checkout,
            public_github=public_github,
        ))
    except ValueError:
        body = ""
    job_id = UUID(job["id"])
    lease = UUID(job["lease_id"])
    # Encode restricted characters and send evidence over stdin, outside argv.
    encoded = body.encode().hex()
    accepted = sql(
        f"SELECT sal_ops.finish_evidence_job('{job_id}'::uuid,'{lease}'::uuid,"
        f"NULLIF(convert_from(decode('{encoded}','hex'),'UTF8'),'')::jsonb);"
    )
    if accepted != "t":
        raise RuntimeError("evidence lease rejected")
    return "stored" if body else "adapter failed"


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--checkout")
    source.add_argument("--public-github", action="store_true")
    args = parser.parse_args()
    try:
        outcome = run_one(args.checkout, public_github=args.public_github)
    except (RuntimeError, TimeoutExpired, ValueError, KeyError, OSError):
        raise SystemExit("evidence worker failed") from None
    if outcome == "adapter failed":
        raise SystemExit("evidence adapter failed")
    print("evidence worker " + outcome)


if __name__ == "__main__":
    main()
