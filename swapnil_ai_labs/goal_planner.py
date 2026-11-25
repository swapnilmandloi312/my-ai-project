"""Optional, advisory-only model planner with persisted admission and finite choices."""
from contextlib import closing
from secure_service.service import canonical,strict_json,valid_id
from swapnil_ai_labs.goal_agents import GOALS,require

class GoalPlanner:
    def __init__(self,queue,provider,*,daily_budget=28):
        require(type(daily_budget) is int and 1<=daily_budget<=1000,"invalid_budget")
        self.queue=queue;self.agents=queue.agents;self.provider=provider;self.budget=daily_budget
        with closing(self.agents.connect()) as db:db.executescript("""
        CREATE TABLE IF NOT EXISTS goal_plan_attempts(tenant TEXT,job TEXT,day INTEGER,state TEXT,result TEXT,PRIMARY KEY(tenant,job));
        CREATE TABLE IF NOT EXISTS goal_plan_usage(tenant TEXT,day INTEGER,count INTEGER,PRIMARY KEY(tenant,day));
        """)
    def plan(self,tenant,job):
        require(valid_id(tenant) and valid_id(job),"invalid_job")
        with closing(self.agents.connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                ctl=db.execute("SELECT paused FROM goal_queue_control WHERE tenant=?",(tenant,)).fetchone()
                require(not ctl or not ctl[0],"queue_paused")
                row=db.execute("SELECT * FROM goal_jobs WHERE tenant=? AND id=? AND status='evaluated'",(tenant,job)).fetchone()
                require(row is not None,"job_not_evaluated")
                task=db.execute("SELECT revision,evidence FROM goal_tasks WHERE tenant=? AND id=?",(tenant,row["task"])).fetchone()
                require(task is not None and task["revision"]==row["revision"],"stale_or_unknown_task")
                require(not db.execute("SELECT 1 FROM goal_plan_attempts WHERE tenant=? AND job=?",(tenant,job)).fetchone(),"plan_already_attempted")
                day=int(self.agents.clock())//86400
                usage=db.execute("SELECT count FROM goal_plan_usage WHERE tenant=? AND day=?",(tenant,day)).fetchone()
                require(not usage or usage[0]<self.budget,"plan_budget_exhausted")
                spec=GOALS[row["category"]];evidence=strict_json(task["evidence"])
                missing=[k for k in spec.checks if k not in evidence]
                # Only metadata and fixed host instructions, never reference values, secrets, user text or files.
                choices=missing or ["independent_review"]
                prompt={"objective":spec.objective,"allowed_next_steps":choices}
                db.execute("INSERT INTO goal_plan_attempts VALUES(?,?,?,'admitted',NULL)",(tenant,job,day))
                db.execute("INSERT INTO goal_plan_usage VALUES(?,?,1) ON CONFLICT(tenant,day) DO UPDATE SET count=count+1",(tenant,day));db.commit()
            except BaseException:db.rollback();raise
        result={"status":"blocked","reason":"invalid_model_choice","next_step":None,"external_action":False,"verified_completion":False}
        try:
            raw=self.provider(prompt,"Return exactly one allowed next-step identifier, without prose.")
            if type(raw) is str and len(raw)<=128 and raw.strip() in choices:
                result={**result,"status":"proposed","reason":"allowed_choice","next_step":raw.strip()}
        except Exception:
            result["reason"]="provider_failure"
        with closing(self.agents.connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                latest=db.execute("SELECT revision FROM goal_tasks WHERE tenant=? AND id=?",(tenant,row["task"])).fetchone()
                ctl=db.execute("SELECT paused FROM goal_queue_control WHERE tenant=?",(tenant,)).fetchone()
                if latest is None or latest[0]!=row["revision"] or ctl and ctl[0]:
                    result={**result,"status":"blocked","reason":"stale_or_paused","next_step":None}
                db.execute("UPDATE goal_plan_attempts SET state=?,result=? WHERE tenant=? AND job=?",(result["status"],canonical(result),tenant,job));db.commit()
            except BaseException:db.rollback();raise
        return result
    def snapshot(self,tenant):
        with closing(self.agents.connect()) as db:
            rows=db.execute("SELECT job,state,result FROM goal_plan_attempts WHERE tenant=? ORDER BY rowid DESC LIMIT 100",(tenant,)).fetchall()
            day=int(self.agents.clock())//86400
            u=db.execute("SELECT count FROM goal_plan_usage WHERE tenant=? AND day=?",(tenant,day)).fetchone()
            return {"daily_attempts":u[0] if u else 0,"daily_limit":self.budget,"plans":[{"job":r[0],"state":r[1],"result":strict_json(r[2]) if r[2] else None} for r in rows]}
