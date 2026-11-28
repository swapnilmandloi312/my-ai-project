"""Run a single approved, leased evidence job using the scoped PostgreSQL login."""

import argparse
import json
from subprocess import TimeoutExpired
from uuid import UUID

from swapnil_ai_labs.cloud_worker import sql
from swapnil_ai_labs.crossref_evidence import bibliography
from swapnil_ai_labs.evidence_tools import encode_deliverable, execute_read_only


def operations_deliverable(job):
    job_id = UUID(job["id"])
    lease = UUID(job["lease_id"])
    measured = json.loads(sql(f"SELECT sal_ops.operations_evidence('{job_id}','{lease}')::text;"))
    return {
        "category": job["category"], "tool": job["tool"], "kind": "evidence_review",
        "recorded_evidence": job["evidence"], "requires_review": True,
        "source_evidence": measured,
    }


def crossref_deliverable(job):
    evidence = job["evidence"]
    if job["category"] != "research" or not isinstance(evidence, dict) or set(evidence) != {"doi"}:
        raise ValueError("approved Research DOI required")
    return {
        "category": "research", "tool": "crossref_doi", "kind": "evidence_review",
        "recorded_evidence": evidence, "requires_review": True,
        "source_evidence": bibliography(evidence["doi"]),
    }


def run_one(checkout=None, *, public_github=False, operations=False, crossref=False):
    claim = (
        "SELECT coalesce(sal_ops.claim_github_evidence_job()::text,'null');"
        if public_github else "SELECT coalesce(sal_ops.claim_evidence_job()::text,'null');"
    )
    if operations:
        claim = "SELECT coalesce(sal_ops.claim_operations_evidence_job()::text,'null');"
    if crossref:
        claim = "SELECT coalesce(sal_ops.claim_crossref_evidence_job()::text,'null');"
    job = json.loads(sql(claim))
    if job is None:
        return "idle"
    try:
        if job["tool"] == "workspace_operations":
            result = operations_deliverable(job)
        elif job["tool"] == "crossref_doi":
            result = crossref_deliverable(job)
        else:
            result = execute_read_only(
                job["category"], job["tool"], job["evidence"], checkout=checkout,
                public_github=public_github,
            )
        body = encode_deliverable(result)
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
    source.add_argument("--operations", action="store_true")
    source.add_argument("--crossref", action="store_true")
    parser.add_argument("--batch", type=int, choices=range(1, 5), default=1)
    args = parser.parse_args()
    try:
        for _ in range(args.batch):
            outcome = run_one(args.checkout, public_github=args.public_github, operations=args.operations,
                              crossref=args.crossref)
            if outcome != "stored":
                break
    except (RuntimeError, TimeoutExpired, ValueError, KeyError, OSError):
        raise SystemExit("evidence worker failed") from None
    if outcome == "adapter failed":
        raise SystemExit("evidence adapter failed")
    print("evidence worker finished")


if __name__ == "__main__":
    main()
