"""Run a single approved, leased evidence job using the scoped PostgreSQL login."""

import argparse
import json
from subprocess import TimeoutExpired

from swapnil_ai_labs.cloud_worker import sql
from swapnil_ai_labs.evidence_tools import encode_deliverable, execute_read_only


def run_one(checkout=None):
    job = json.loads(sql("SELECT coalesce(sal_ops.claim_evidence_job()::text,'null');"))
    if job is None:
        return "idle"
    try:
        body = encode_deliverable(execute_read_only(
            job["category"], job["tool"], job["evidence"], checkout=checkout,
        ))
    except ValueError:
        body = ""
    accepted = sql(
        "SELECT sal_ops.finish_evidence_job(:'id'::uuid,:'lease'::uuid,NULLIF(:'body','')::jsonb);",
        id=job["id"], lease=job["lease_id"], body=body,
    )
    if accepted != "t":
        raise RuntimeError("evidence lease rejected")
    return "stored" if body else "adapter failed"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout")
    args = parser.parse_args()
    try:
        outcome = run_one(args.checkout)
    except (RuntimeError, TimeoutExpired, ValueError, KeyError, OSError):
        raise SystemExit("evidence worker failed") from None
    if outcome == "adapter failed":
        raise SystemExit("evidence adapter failed")
    print("evidence worker " + outcome)


if __name__ == "__main__":
    main()
