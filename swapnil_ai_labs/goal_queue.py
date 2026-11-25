"""Durable local queue for deterministic goal evaluations only.

Trusted host owns DB, clock and keys. Each tick is bounded. There is no network,
model inference, arbitrary tool invocation or automatic approval.
"""
from contextlib import closing
import secrets,sqlite3
from secure_service.service import canonical,strict_json,valid_id
from swapnil_ai_labs.goal_agents import GOALS,GoalError,require

class GoalQueue:
    def __init__(self,agents):
        self.agents=agents
        with closing(agents.connect()) as db:db.executescript("""
        CREATE TABLE IF NOT EXISTS goal_jobs(
          tenant TEXT NOT NULL,id TEXT NOT NULL,task TEXT NOT NULL,category TEXT NOT NULL,
          revision INTEGER NOT NULL,nonce TEXT NOT NULL,status TEXT NOT NULL,
          attempts INTEGER NOT NULL,max_attempts INTEGER NOT NULL,due INTEGER NOT NULL,
          lease_until INTEGER,lease_token TEXT,result TEXT,
          PRIMARY KEY(tenant,id),UNIQUE(tenant,nonce));
        CREATE TABLE IF NOT EXISTS goal_queue_control(tenant TEXT PRIMARY KEY,paused INTEGER NOT NULL);
        """)
    def _now(self):return int(self.agents.clock())
    def pause(self,tenant,paused=True):
        require(valid_id(tenant) and type(paused) is bool,"invalid_control")
        with closing(self.agents.connect()) as db:
            db.execute("INSERT INTO goal_queue_control VALUES(?,?) ON CONFLICT(tenant) DO UPDATE SET paused=excluded.paused",(tenant,int(paused)))
    def enqueue(self,tenant,job,task,category,revision,*,max_attempts=3):
        require(all(valid_id(x) for x in (tenant,job,task)) and type(category) is str and category in GOALS,"invalid_job")
        require(type(revision) is int and revision>0 and type(max_attempts) is int and 1<=max_attempts<=5,"invalid_job")
        with closing(self.agents.connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                old=db.execute("SELECT * FROM goal_jobs WHERE tenant=? AND id=?",(tenant,job)).fetchone()
                if old:
                    require((old["task"],old["category"],old["revision"],old["max_attempts"])==(task,category,revision,max_attempts),"job_conflict")
                    db.commit();return job
                row=db.execute("SELECT category,revision FROM goal_tasks WHERE tenant=? AND id=?",(tenant,task)).fetchone()
                require(row is not None and (row["category"],row["revision"])==(category,revision),"stale_or_unknown_task")
                db.execute("INSERT INTO goal_jobs VALUES(?,?,?,?,?,?,'queued',0,?,?,NULL,NULL,NULL)",(tenant,job,task,category,revision,secrets.token_hex(20),max_attempts,self._now()))
                db.commit();return job
            except BaseException:db.rollback();raise
    def claim(self,tenant,*,lease_seconds=30):
        require(valid_id(tenant) and type(lease_seconds) is int and 1<=lease_seconds<=120,"invalid_claim")
        with closing(self.agents.connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE");now=self._now()
                ctl=db.execute("SELECT paused FROM goal_queue_control WHERE tenant=?",(tenant,)).fetchone()
                if ctl and ctl["paused"]:db.commit();return None
                # Recover committed evaluations before marking exhausted leases failed.
                db.execute("""UPDATE goal_jobs SET status='evaluated',result=(SELECT result FROM goal_runs WHERE goal_runs.tenant=goal_jobs.tenant AND goal_runs.nonce=goal_jobs.nonce),lease_token=NULL,lease_until=NULL
                WHERE tenant=? AND status='leased' AND lease_until<=? AND EXISTS(SELECT 1 FROM goal_runs WHERE goal_runs.tenant=goal_jobs.tenant AND goal_runs.nonce=goal_jobs.nonce)""",(tenant,now))
                db.execute("UPDATE goal_jobs SET status='failed',result=?,lease_token=NULL,lease_until=NULL WHERE tenant=? AND status='leased' AND lease_until<=? AND attempts>=max_attempts",(canonical({"reason":"retry_budget_exhausted"}),tenant,now))
                row=db.execute("""SELECT * FROM goal_jobs WHERE tenant=? AND attempts<max_attempts AND ((status='queued' AND due<=?) OR (status='leased' AND lease_until<=?)) ORDER BY due,id LIMIT 1""",(tenant,now,now)).fetchone()
                if row is None:db.commit();return None
                token=secrets.token_hex(20)
                db.execute("UPDATE goal_jobs SET status='leased',attempts=attempts+1,lease_until=?,lease_token=? WHERE tenant=? AND id=?",(now+lease_seconds,token,tenant,row["id"]))
                db.commit();return {"tenant":tenant,"id":row["id"],"lease_token":token}
            except BaseException:db.rollback();raise
    def execute(self,lease):
        """Execute only a currently valid host lease. At-most-one committed evaluation
        via GoalAgents nonce; a crashed finalizer can recover its persisted result.
        Pause stops admission of new claims, not already admitted work.
        """
        require(type(lease) is dict and set(lease)=={"tenant","id","lease_token"} and all(valid_id(v) for v in lease.values()),"invalid_lease")
        tenant,job,token=lease["tenant"],lease["id"],lease["lease_token"]
        with closing(self.agents.connect()) as db:
            row=db.execute("SELECT * FROM goal_jobs WHERE tenant=? AND id=? AND status='leased' AND lease_token=? AND lease_until>?",(tenant,job,token,self._now())).fetchone()
            require(row is not None,"lease_lost")
            prior=db.execute("SELECT result FROM goal_runs WHERE tenant=? AND nonce=?",(tenant,row["nonce"])).fetchone()
        if prior:result=strict_json(prior["result"]);status="evaluated"
        else:
            try:
                grant=self.agents.grant(tenant,row["task"],row["category"],row["revision"],row["nonce"],ttl=30)
                result=self.agents.run(grant,tenant=tenant,category=row["category"]);status="evaluated"
            except GoalError as exc:
                with closing(self.agents.connect()) as db:
                    prior=db.execute("SELECT result FROM goal_runs WHERE tenant=? AND nonce=?",(tenant,row["nonce"])).fetchone()
                if prior:result=strict_json(prior["result"]);status="evaluated"
                else:result={"reason":str(exc)};status="failed"
        with closing(self.agents.connect()) as db:
            n=db.execute("UPDATE goal_jobs SET status=?,result=?,lease_token=NULL,lease_until=NULL WHERE tenant=? AND id=? AND status='leased' AND lease_token=? AND lease_until>?",(status,canonical(result),tenant,job,token,self._now())).rowcount
            require(n==1,"lease_lost")
        return result
    def tick(self,tenant,*,limit=14):
        require(type(limit) is int and 1<=limit<=32,"invalid_limit")
        out=[]
        for _ in range(limit):
            lease=self.claim(tenant)
            if lease is None:break
            out.append(self.execute(lease))
        return out
    def snapshot(self,tenant):
        require(valid_id(tenant),"invalid_tenant")
        with closing(self.agents.connect()) as db:
            control=db.execute("SELECT paused FROM goal_queue_control WHERE tenant=?",(tenant,)).fetchone()
            rows=db.execute("SELECT id,task,category,revision,status,attempts,max_attempts,result FROM goal_jobs WHERE tenant=? ORDER BY id",(tenant,)).fetchall()
            return {"tenant":tenant,"paused":bool(control and control["paused"]),"jobs":[{**dict(r),"result":strict_json(r["result"]) if r["result"] else None} for r in rows]}
