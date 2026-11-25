"""Authenticated local job control API. Host provisions credentials; never a public service."""
from dataclasses import dataclass
from contextlib import closing
import hashlib,hmac,json,re,sqlite3
from secure_service.service import canonical,digest,valid_id,strict_json
from swapnil_ai_labs.goal_agents import GoalAgents,GOALS,GoalError,require
from swapnil_ai_labs.goal_queue import GoalQueue

@dataclass(frozen=True)
class BrokerPrincipal:
    id:str
    tenant:str
    token_hash:str
    role:str

class Broker:
    def __init__(self,queue,principals):
        self.queue=queue;self.agents=queue.agents;self.principals=tuple(principals)
        if len({p.id for p in self.principals})!=len(self.principals) or len({p.token_hash for p in self.principals})!=len(self.principals):raise ValueError("duplicate credentials")
        for p in self.principals:
            if not valid_id(p.id) or not valid_id(p.tenant) or type(p.token_hash) is not str or not re.fullmatch("[0-9a-f]{64}",p.token_hash) or p.role not in {"viewer","operator"}:raise ValueError("invalid principal")
        with closing(self.agents.connect()) as db:db.executescript("""
        CREATE TABLE IF NOT EXISTS broker_quota(principal TEXT,minute INTEGER,count INTEGER,PRIMARY KEY(principal,minute));
        CREATE TABLE IF NOT EXISTS broker_events(seq INTEGER PRIMARY KEY,actor TEXT,tenant TEXT,action TEXT,outcome TEXT,ts INTEGER);
        """)
    def auth(self,value):
        if type(value) is not str or not value.startswith("Bearer ") or not 32<=len(value[7:])<=256:return None
        token=value[7:]
        if not token.isascii() or any(ord(c)<33 or ord(c)>126 for c in token):return None
        hashed=digest(token);found=None
        for p in self.principals:
            if hmac.compare_digest(hashed,p.token_hash):found=p
        return found
    def admit(self,p):
        now=int(self.agents.clock())
        with closing(self.agents.connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT INTO broker_quota VALUES(?,?,1) ON CONFLICT(principal,minute) DO UPDATE SET count=count+1",(p.id,now//60))
                n=db.execute("SELECT count FROM broker_quota WHERE principal=? AND minute=?",(p.id,now//60)).fetchone()[0]
                db.execute("DELETE FROM broker_quota WHERE minute<?",(now//60-1440,))
                db.commit();return n<=60
            except BaseException:db.rollback();raise
    def event(self,p,action,outcome):
        with closing(self.agents.connect()) as db:db.execute("INSERT INTO broker_events(actor,tenant,action,outcome,ts) VALUES(?,?,?,?,?)",(p.id,p.tenant,action,outcome,int(self.agents.clock())))
    def status(self,p):
        with closing(self.agents.connect()) as db:
            ctl=db.execute("SELECT paused FROM goal_queue_control WHERE tenant=?",(p.tenant,)).fetchone()
            counts={r[0]:r[1] for r in db.execute("SELECT status,count(*) FROM goal_jobs WHERE tenant=? GROUP BY status",(p.tenant,))}
            rows=db.execute("SELECT id,task,category,revision,status,attempts,max_attempts,result FROM goal_jobs WHERE tenant=? ORDER BY rowid DESC LIMIT 100",(p.tenant,)).fetchall()
            return {"tenant":p.tenant,"role":p.role,"paused":bool(ctl and ctl[0]),"counts":counts,"jobs":[{**dict(r),"result":strict_json(r["result"]) if r["result"] else None} for r in rows],"scope":"local_deterministic_goal_evaluation","external_actions":False}
    def command(self,p,body):
        require(p.role=="operator","role_denied")
        require(type(body) is dict and type(body.get("action")) is str,"invalid_command")
        action=body["action"]
        if action=="set_task":
            require(set(body)=={"action","task","category","evidence","revision"},"invalid_command")
            rev=self.agents.set_task(p.tenant,body["task"],body["category"],body["evidence"],body["revision"])
            return {"revision":rev}
        if action=="enqueue":
            require(set(body)=={"action","job","task","category","revision"},"invalid_command")
            return {"job":self.queue.enqueue(p.tenant,body["job"],body["task"],body["category"],body["revision"])}
        if action in {"pause","resume"}:
            require(set(body)=={"action"},"invalid_command")
            self.queue.pause(p.tenant,action=="pause");return {"paused":action=="pause"}
        if action=="tick":
            require(set(body)=={"action","limit"} and type(body["limit"]) is int and 1<=body["limit"]<=14,"invalid_command")
            results=self.queue.tick(p.tenant,limit=body["limit"])
            return {"evaluated":len(results),"results":results}
        raise GoalError("unknown_action")

def make_app(broker):
    def app(env,start):
        def respond(code,body):
            reasons={200:"OK",400:"Bad Request",401:"Unauthorized",403:"Forbidden",404:"Not Found",405:"Method Not Allowed",409:"Conflict",413:"Payload Too Large",415:"Unsupported Media Type",429:"Too Many Requests",503:"Service Unavailable"}
            raw=canonical(body).encode()
            start(str(code)+" "+reasons[code],[("Content-Type","application/json"),("Content-Length",str(len(raw))),("Cache-Control","no-store"),("X-Content-Type-Options","nosniff")]);return [raw]
        path=env.get("PATH_INFO","");method=env.get("REQUEST_METHOD")
        if env.get("HTTP_ORIGIN"):return respond(403,{"reason":"browser_origin_denied"})
        if path=="/healthz" and method=="GET":return respond(200,{"status":"ok"})
        p=broker.auth(env.get("HTTP_AUTHORIZATION"))
        if p is None:return respond(401,{"reason":"authentication_required"})
        try:
            if not broker.admit(p):return respond(429,{"reason":"rate_limit"})
            if path=="/v1/goals/status":
                if method!="GET":return respond(405,{"reason":"method"})
                return respond(200,broker.status(p))
            if path!="/v1/goals/commands":return respond(404,{"reason":"not_found"})
            if method!="POST":return respond(405,{"reason":"method"})
            if p.role!="operator":return respond(403,{"reason":"role_denied"})
            if env.get("CONTENT_TYPE","").split(";")[0].strip().lower()!="application/json":return respond(415,{"reason":"content_type"})
            try:
                n=int(env.get("CONTENT_LENGTH",""))
                if n>8192:return respond(413,{"reason":"size"})
                if n<1:raise ValueError()
                data=env["wsgi.input"].read(n)
                if len(data)!=n:raise ValueError()
                body=strict_json(data.decode("utf-8"))
            except (ValueError,UnicodeError,RecursionError):return respond(400,{"reason":"malformed_json"})
            action=body.get("action") if type(body) is dict else None
            known=action if type(action) is str and action in {"set_task","enqueue","pause","resume","tick"} else "invalid"
            try:result=broker.command(p,body)
            except GoalError as e:
                broker.event(p,known,"denied")
                reason=str(e)
                return respond(403 if reason=="role_denied" else 409 if reason in {"revision_conflict","job_conflict","stale_or_unknown_task","lease_lost"} else 400,{"reason":reason})
            broker.event(p,known,"accepted")
            return respond(200,result)
        except sqlite3.Error:return respond(503,{"reason":"storage_unavailable"})
    return app
