"""Persistent read-only reference service. Explicit host authorization, never model-granted."""
import hashlib,hmac,json,re,sqlite3,time
from pathlib import Path
from dataclasses import dataclass

CATEGORIES=frozenset({"finance","support","operations","knowledge"})
ID=re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
def valid_id(x):return type(x) is str and ID.fullmatch(x) is not None
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)
def digest(x):return hashlib.sha256(x.encode()).hexdigest()
def strict_json(s):
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out:raise ValueError("duplicate key")
            out[k]=v
        return out
    def reject(_):raise ValueError("non-finite")
    return json.loads(s,object_pairs_hook=unique,parse_constant=reject)
@dataclass(frozen=True)
class Principal:
    id:str
    tenant:str
    token_hash:str
    categories:frozenset
    limit:int=60
    budget:int=100

class Service:
    def __init__(self,path,principals,audit_key,clock=time.time):
        if not isinstance(audit_key,bytes) or len(audit_key)<32:raise ValueError("audit key must be >=32 bytes")
        self.path=str(path);self.principals=tuple(principals);self.key=audit_key;self.clock=clock
        if len({p.id for p in self.principals})!=len(self.principals) or len({p.token_hash for p in self.principals})!=len(self.principals):raise ValueError("duplicate principal")
        for p in self.principals:
            if not valid_id(p.id) or not valid_id(p.tenant) or not re.fullmatch("[0-9a-f]{64}",p.token_hash) or not p.categories<=CATEGORIES or type(p.limit) is not int or not 1<=p.limit<=10000 or type(p.budget) is not int or not 1<=p.budget<=1000000:raise ValueError("invalid principal")
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS records(tenant TEXT,category TEXT,id TEXT,payload TEXT,PRIMARY KEY(tenant,category,id));
            CREATE TABLE IF NOT EXISTS acl(principal TEXT,tenant TEXT,category TEXT,id TEXT,PRIMARY KEY(principal,tenant,category,id));
            CREATE TABLE IF NOT EXISTS requests(principal TEXT,id TEXT,PRIMARY KEY(principal,id));
            CREATE TABLE IF NOT EXISTS quotas(principal TEXT,minute INTEGER,count INTEGER,PRIMARY KEY(principal,minute));
            CREATE TABLE IF NOT EXISTS usage(principal TEXT PRIMARY KEY,count INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY, event TEXT NOT NULL, mac TEXT NOT NULL);
            """)
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5,isolation_level=None);db.execute("PRAGMA busy_timeout=5000");return db
    def authenticate(self,authorization):
        if type(authorization) is not str or not authorization.startswith("Bearer ") or not 32<=len(authorization[7:])<=256:return None
        hashed=digest(authorization[7:]);match=None
        for p in self.principals:
            if hmac.compare_digest(hashed,p.token_hash):match=p
        return match
    def seed_record(self,tenant,category,record_id,payload,allowed_principals):
        """Administrative host only; never exposed through HTTP."""
        if not valid_id(tenant) or category not in CATEGORIES or not valid_id(record_id) or type(payload) is not dict:raise ValueError("bad record")
        body=canonical(payload)
        if len(body)>4096:raise ValueError("record too large")
        for pid in allowed_principals:
            if not any(p.id==pid and p.tenant==tenant and category in p.categories for p in self.principals):raise ValueError("invalid ACL")
        db=self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO records VALUES(?,?,?,?)",(tenant,category,record_id,body))
            db.executemany("INSERT INTO acl VALUES(?,?,?,?)",[(p,tenant,category,record_id) for p in allowed_principals]);db.commit()
        except BaseException:db.rollback();raise
        finally:db.close()
    def _audit(self,db,pid,reason,status,now):
        prev=db.execute("SELECT seq,mac FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        seq=prev[0]+1 if prev else 1;last=prev[1] if prev else "0"*64
        event=canonical({"seq":seq,"principal":hmac.new(self.key,pid.encode(),hashlib.sha256).hexdigest() if pid else None,"reason":reason,"status":status,"ts":now})
        mac=hmac.new(self.key,(last+"\n"+event).encode(),hashlib.sha256).hexdigest()
        db.execute("INSERT INTO audit VALUES(?,?,?)",(seq,event,mac))
    def verify_audit(self):
        db=self.connect();last="0"*64;n=0
        try:
            for seq,event,mac in db.execute("SELECT seq,event,mac FROM audit ORDER BY seq"):
                n+=1
                if seq!=n or not hmac.compare_digest(mac,hmac.new(self.key,(last+"\n"+event).encode(),hashlib.sha256).hexdigest()):return False
                last=mac
            return True
        finally:db.close()
    def read(self,authorization,body):
        p=self.authenticate(authorization);now=int(self.clock());db=self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            def finish(status,reason,output=None):
                self._audit(db,p.id if p else "",reason,status,now);db.commit()
                return status,{"status":"executed_read_only" if status==200 else "blocked","reason":reason,"output":output}
            if p is None:return finish(401,"authentication_required")
            minute=now//60
            db.execute("INSERT INTO quotas VALUES(?,?,1) ON CONFLICT(principal,minute) DO UPDATE SET count=count+1",(p.id,minute))
            q=db.execute("SELECT count FROM quotas WHERE principal=? AND minute=?",(p.id,minute)).fetchone()[0]
            if q>p.limit:return finish(429,"rate_limit")
            if type(body) is not dict or set(body)!={"version","request_id","category","record_id","proposal"} or body["version"]!="1.0" or not valid_id(body["request_id"]) or not valid_id(body["record_id"]) or type(body["category"]) is not str:return finish(400,"invalid_request")
            cat,rid=body["category"],body["record_id"]
            if cat not in CATEGORIES or cat not in p.categories:return finish(403,"scope_denied")
            proposal=body["proposal"]
            if type(proposal) is not dict or proposal!={"version":"1.0","action":"read_record","category":cat,"record_id":rid}:return finish(403,"proposal_mismatch")
            if not db.execute("SELECT 1 FROM acl WHERE principal=? AND tenant=? AND category=? AND id=?",(p.id,p.tenant,cat,rid)).fetchone():return finish(403,"scope_denied")
            if db.execute("SELECT 1 FROM requests WHERE principal=? AND id=?",(p.id,body["request_id"])).fetchone():return finish(409,"replay")
            used=db.execute("SELECT count FROM usage WHERE principal=?",(p.id,)).fetchone()
            if used and used[0]>=p.budget:return finish(429,"budget_exhausted")
            row=db.execute("SELECT payload FROM records WHERE tenant=? AND category=? AND id=?",(p.tenant,cat,rid)).fetchone()
            if row is None:return finish(403,"scope_denied")
            db.execute("INSERT INTO requests VALUES(?,?)",(p.id,body["request_id"]))
            db.execute("INSERT INTO usage VALUES(?,1) ON CONFLICT(principal) DO UPDATE SET count=count+1",(p.id,))
            return finish(200,"authorized_read",json.loads(row[0]))
        except BaseException:db.rollback();raise
        finally:db.close()
