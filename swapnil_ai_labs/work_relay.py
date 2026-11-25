"""Transactional synthetic request-to-resolution reference. No external side effects."""
from dataclasses import dataclass
from contextlib import closing
import sqlite3,json,hashlib,hmac,time,re
from secure_service.service import valid_id,canonical,digest,strict_json

REQUIRED={"finance":frozenset({"invoice","purchase_order"}),"hr":frozenset({"employee_ref","manager_confirmation"}),"it":frozenset({"resource","owner_confirmation"}),"support":frozenset({"ticket","resolution_evidence"})}
ROLES=frozenset({"requester","reviewer","operator"})
@dataclass(frozen=True)
class RelayPrincipal:
    id:str
    tenant:str
    token_hash:str
    role:str
    departments:frozenset

class RelayError(Exception):
    def __init__(self,code,reason):self.code=code;self.reason=reason;super().__init__(reason)

def require(ok,code,reason):
    if not ok:raise RelayError(code,reason)

class WorkRelay:
    def __init__(self,path,principals,audit_key,clock=time.time):
        if not isinstance(audit_key,bytes) or len(audit_key)<32:raise ValueError("audit key required")
        self.path=str(path);self.principals=tuple(principals);self.key=audit_key;self.clock=clock
        if len({p.id for p in self.principals})!=len(self.principals) or len({p.token_hash for p in self.principals})!=len(self.principals):raise ValueError("duplicate principal")
        for p in self.principals:
            if not valid_id(p.id) or not valid_id(p.tenant) or not re.fullmatch("[0-9a-f]{64}",p.token_hash) or p.role not in ROLES or not isinstance(p.departments,frozenset) or not p.departments<=REQUIRED.keys():raise ValueError("invalid principal")
        with closing(self.connect()) as db:db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS relay_items(tenant TEXT,id TEXT,department TEXT,creator TEXT,state TEXT,revision INTEGER,evidence TEXT,approved_by TEXT,PRIMARY KEY(tenant,id));
        CREATE TABLE IF NOT EXISTS relay_commands(principal TEXT,id TEXT,fingerprint TEXT,result TEXT,PRIMARY KEY(principal,id));
        CREATE TABLE IF NOT EXISTS relay_events(seq INTEGER PRIMARY KEY,event TEXT NOT NULL,mac TEXT NOT NULL);
        """)
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5,isolation_level=None);db.row_factory=sqlite3.Row;db.execute("PRAGMA busy_timeout=5000");return db
    def auth(self,auth):
        if not isinstance(auth,str) or not auth.startswith("Bearer ") or not 32<=len(auth[7:])<=256:return None
        target=digest(auth[7:]);return next((p for p in self.principals if hmac.compare_digest(p.token_hash,target)),None)
    def _event(self,db,p,item,action,reason):
        prior=db.execute("SELECT seq,mac FROM relay_events ORDER BY seq DESC LIMIT 1").fetchone()
        seq=prior["seq"]+1 if prior else 1;prev=prior["mac"] if prior else "0"*64
        event=canonical({"seq":seq,"actor":hmac.new(self.key,p.id.encode(),hashlib.sha256).hexdigest(),"item":hmac.new(self.key,(p.tenant+":"+item).encode(),hashlib.sha256).hexdigest(),"action":action,"reason":reason,"ts":int(self.clock())})
        mac=hmac.new(self.key,(prev+"\n"+event).encode(),hashlib.sha256).hexdigest()
        db.execute("INSERT INTO relay_events VALUES(?,?,?)",(seq,event,mac))
    def verify_audit(self):
        prev="0"*64
        with closing(self.connect()) as db:
            for i,row in enumerate(db.execute("SELECT * FROM relay_events ORDER BY seq"),1):
                if row["seq"]!=i or not hmac.compare_digest(row["mac"],hmac.new(self.key,(prev+"\n"+row["event"]).encode(),hashlib.sha256).hexdigest()):return False
                prev=row["mac"]
        return True
    @staticmethod
    def public(row):
        ev=json.loads(row["evidence"]);required=REQUIRED[row["department"]]
        return {"id":row["id"],"department":row["department"],"state":row["state"],"revision":row["revision"],"evidence_keys":sorted(ev),"missing":sorted(required-ev.keys()),"approved":row["approved_by"] is not None,"external_action":False}
    def _lookup(self,db,p,item):
        row=db.execute("SELECT * FROM relay_items WHERE tenant=? AND id=?",(p.tenant,item)).fetchone()
        require(row is not None and row["department"] in p.departments and (p.role!="requester" or row["creator"]==p.id),404,"not_found")
        return row
    def get(self,auth,item):
        p=self.auth(auth);require(p is not None,401,"authentication_required");require(valid_id(item),400,"invalid_id")
        with closing(self.connect()) as db:return self.public(self._lookup(db,p,item))
    def command(self,auth,body):
        p=self.auth(auth);require(p is not None,401,"authentication_required")
        require(type(body) is dict and set(body)=={"command_id","item_id","action","revision","data"},400,"invalid_command")
        cid,item,action,rev,data=(body[x] for x in ("command_id","item_id","action","revision","data"))
        require(valid_id(cid) and valid_id(item) and type(action) is str and action in {"create","attach","submit","approve","reject","resolve"} and type(rev) is int and 0<=rev<=1000000 and type(data) is dict,400,"invalid_command")
        try:encoded=canonical(body)
        except (TypeError,ValueError,RecursionError):raise RelayError(400,"invalid_command")
        require(len(encoded)<=8192,413,"size")
        fp=digest(encoded);db=self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT fingerprint,result FROM relay_commands WHERE principal=? AND id=?",(p.id,cid)).fetchone()
            if old:
                require(hmac.compare_digest(fp,old["fingerprint"]),409,"idempotency_conflict")
                db.commit();return json.loads(old["result"])
            try:
                result=self._apply(db,p,item,action,rev,data)
            except RelayError as exc:
                self._event(db,p,item,action,exc.reason);db.commit();raise
            self._event(db,p,item,action,"accepted")
            db.execute("INSERT INTO relay_commands VALUES(?,?,?,?)",(p.id,cid,fp,canonical(result)))
            db.commit();return result
        except BaseException:
            db.rollback();raise
        finally:db.close()
    def _apply(self,db,p,item,action,rev,data):
        if action=="create":
            require(p.role=="requester",403,"role_denied")
            require(rev==0 and set(data)=={"department"} and type(data["department"]) is str,400,"invalid_create")
            dep=data["department"];require(dep in p.departments,403,"scope_denied")
            require(not db.execute("SELECT 1 FROM relay_items WHERE tenant=? AND id=?",(p.tenant,item)).fetchone(),409,"already_exists")
            db.execute("INSERT INTO relay_items VALUES(?,?,?,?,?,?,?,?)",(p.tenant,item,dep,p.id,"received",1,"{}",None))
            return self.public(self._lookup(db,p,item))
        row=self._lookup(db,p,item)
        require(row["revision"]==rev,409,"revision_conflict")
        state=row["state"];ev=json.loads(row["evidence"]);approved=row["approved_by"]
        if action=="attach":
            require(p.role=="requester" and row["creator"]==p.id,403,"role_denied")
            require(state in {"received","needs_evidence"},409,"invalid_state")
            require(set(data)=={"key","reference"} and type(data["key"]) is str and data["key"] in REQUIRED[row["department"]] and valid_id(data["reference"]),400,"invalid_evidence")
            ev[data["key"]]=data["reference"];state="received"
        elif action=="submit":
            require(p.role=="requester" and row["creator"]==p.id,403,"role_denied")
            require(not data,400,"unexpected_data");require(state in {"received","needs_evidence"},409,"invalid_state")
            state="needs_evidence" if REQUIRED[row["department"]]-ev.keys() else "awaiting_review"
        elif action in {"approve","reject"}:
            require(p.role=="reviewer" and row["creator"]!=p.id,403,"role_denied")
            require(not data,400,"unexpected_data");require(state=="awaiting_review",409,"invalid_state")
            require(not REQUIRED[row["department"]]-ev.keys(),409,"missing_evidence")
            state="approved" if action=="approve" else "rejected";approved=p.id if action=="approve" else None
        elif action=="resolve":
            require(p.role=="operator" and p.id!=approved and p.id!=row["creator"],403,"role_denied")
            require(not data,400,"unexpected_data");require(state=="approved" and approved is not None,409,"approval_required")
            state="resolved_local"
        db.execute("UPDATE relay_items SET state=?,revision=?,evidence=?,approved_by=? WHERE tenant=? AND id=?",(state,rev+1,canonical(ev),approved,p.tenant,item))
        return self.public(self._lookup(db,p,item))
