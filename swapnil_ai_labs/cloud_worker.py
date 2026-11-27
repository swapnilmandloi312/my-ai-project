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
    def __init__(self, workspace):
        self.workspace = workspace

    def claim(self):
        raw = sql("SELECT coalesce(sal_ops.claim_job(:'ws')::text,'null');", ws=self.workspace)
        return json.loads(raw)

    def finish(self, job, result):
        raw = sql("SELECT sal_ops.finish_job(:'ws',:'id'::uuid,:'lease'::uuid,NULLIF(:'result','')::jsonb);",
                  ws=self.workspace,id=job["id"],lease=job["lease_id"],
                  result=json.dumps(result) if result is not None else "")
        return raw == "t"

def tick(queue):
    job = queue.claim()
    if job is None:
        return False
    try:
        result = evaluate(job["category"], job["evidence"])
    except (ValueError, KeyError, TypeError):
        result = None
    accepted = queue.finish(job, result)
    print(json.dumps({"job_id":job["id"],"accepted":accepted,
                      "result":"synthetic" if result else "evaluation_failed"}), flush=True)
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace",required=True)
    parser.add_argument("--loop",action="store_true")
    args = parser.parse_args()
    queue = Queue(args.workspace)
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
