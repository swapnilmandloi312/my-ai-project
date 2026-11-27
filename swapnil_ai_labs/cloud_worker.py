"""Synthetic-only PostgreSQL worker. Uses psql and external PG* credentials."""
import argparse
import json
import subprocess
import time
from swapnil_ai_labs.forty_profiles import evaluate

def sql(query, **variables):
    args = ["psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1"]
    for key, value in variables.items():
        args.extend(["-v", key+"="+str(value)])
    run = subprocess.run(args, input=query, text=True, capture_output=True, timeout=20)
    if run.returncode:
        # Never print SQL, credentials or arbitrary database error text.
        raise RuntimeError("database command failed")
    return run.stdout.strip()

class Queue:
    def __init__(self, workspace=None, scoped=False):
        self.workspace = workspace
        self.scoped = scoped

    def claim(self):
        raw = sql("SELECT coalesce(sal_ops.hourly_claim()::text,'null');") if self.scoped else sql("SELECT coalesce(sal_ops.claim_job(:'ws')::text,'null');", ws=self.workspace)
        return json.loads(raw)

    def finish(self, job, result):
        values = dict(id=job['id'],lease=job['lease_id'],result=json.dumps(result) if result is not None else '')
        raw = sql("SELECT sal_ops.hourly_finish(:'id'::uuid,:'lease'::uuid,NULLIF(:'result','')::jsonb);",**values) if self.scoped else sql("SELECT sal_ops.finish_job(:'ws',:'id'::uuid,:'lease'::uuid,NULLIF(:'result','')::jsonb);",ws=self.workspace,**values)
        return raw == "t"

def execute_one(queue, quiet=False):
    job = queue.claim()
    if job is None:
        return None
    try:
        result = evaluate(job["category"], job["evidence"])
    except (ValueError, KeyError, TypeError):
        result = None
    accepted = queue.finish(job, result)
    if not quiet:
        print(json.dumps({"job_id":job["id"],"accepted":accepted,
                          "result":"synthetic" if result else "evaluation_failed"}), flush=True)
    return accepted, result is None

def tick(queue):
    return execute_one(queue) is not None

def batch(queue, max_jobs):
    if type(max_jobs) is not int or not 1 <= max_jobs <= 40:
        raise ValueError('batch size must be 1..40')
    counts = dict(claimed=0, accepted=0, rejected=0, evaluation_failed=0, max_jobs=max_jobs)
    for _ in range(max_jobs):
        outcome = execute_one(queue, quiet=True)
        if outcome is None:
            break
        accepted, failed = outcome
        counts['claimed'] += 1
        counts['accepted' if accepted else 'rejected'] += 1
        counts['evaluation_failed'] += int(failed)
    return counts

def record_batch(run_id, counts):
    return sql("SELECT sal_ops.hourly_worker_report(:'run'::text,:'counts'::jsonb);",run=run_id,counts=json.dumps(counts)) == 't'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace")
    parser.add_argument("--scoped",action="store_true")
    parser.add_argument("--batch",type=int)
    parser.add_argument("--record-run")
    parser.add_argument("--loop",action="store_true")
    args = parser.parse_args()
    if args.scoped == bool(args.workspace):
        parser.error('choose --scoped or --workspace')
    if args.scoped and (args.loop or args.batch is None or not args.record_run):
        parser.error('scoped mode requires bounded batch and run ID')
    if args.record_run and not args.scoped:
        parser.error('reporting requires scoped mode')
    queue = Queue(args.workspace,scoped=args.scoped)
    if args.batch is not None:
        if args.loop or not 1 <= args.batch <= 40:
            parser.error('batch must be 1..40 and cannot loop')
        try:
            counts = batch(queue,args.batch)
            if args.record_run: record_batch(args.record_run,counts)
        except (RuntimeError,subprocess.TimeoutExpired,json.JSONDecodeError,KeyError,ValueError,TypeError):
            raise SystemExit('bounded worker failed; inspect private queue state') from None
        # Public CI logs must not contain private job IDs, counts or evidence.
        print('bounded worker finished',flush=True)
        return
    if not args.loop:
        tick(queue)
        return
    delay = 1
    while True:
        try:
            worked = tick(queue)
            delay = 1
            if not worked: time.sleep(2)
        except (RuntimeError,subprocess.TimeoutExpired,json.JSONDecodeError):
            print("worker database unavailable",flush=True)
            time.sleep(delay)
            delay = min(delay*2,60)

if __name__ == "__main__":
    main()
