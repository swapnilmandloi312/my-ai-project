"""Host-authorized model proposal runtime. Read-only, local reference implementation."""
from dataclasses import dataclass
from contextlib import closing
import json,sqlite3,time,uuid
from secure_service.service import Service,CATEGORIES,valid_id,strict_json

@dataclass(frozen=True)
class HostTask:
    """The trusted application host selects a record and supplies user intent separately."""
    request_id: str
    category: str
    record_id: str
    intent: str

class TrustedRuntime:
    def __init__(self, service: Service, provider, *, clock=time.perf_counter):
        self.service=service
        self.provider=provider
        self.clock=clock
        with closing(service.connect()) as db:
            db.executescript("""
              CREATE TABLE IF NOT EXISTS inference_requests(
                principal TEXT NOT NULL,id TEXT NOT NULL,PRIMARY KEY(principal,id));
              CREATE TABLE IF NOT EXISTS inference_usage(
                principal TEXT PRIMARY KEY,count INTEGER NOT NULL);
              CREATE TABLE IF NOT EXISTS inference_quotas(
                principal TEXT NOT NULL,minute INTEGER NOT NULL,count INTEGER NOT NULL,
                PRIMARY KEY(principal,minute));
            """)
    def _reserve(self,auth,task):
        p=self.service.authenticate(auth)
        if p is None:return 401,"authentication_required"
        now=int(self.service.clock())
        db=self.service.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            def finish(code,reason):
                self.service._audit(db,p.id,reason,code,now)
                db.commit()
                return code,reason
            minute=now//60
            db.execute("INSERT INTO inference_quotas VALUES(?,?,1) ON CONFLICT(principal,minute) DO UPDATE SET count=count+1",(p.id,minute))
            q=db.execute("SELECT count FROM inference_quotas WHERE principal=? AND minute=?",(p.id,minute)).fetchone()[0]
            if q>p.limit:return finish(429,"inference_rate_limit")
            if not isinstance(task,HostTask) or not valid_id(task.request_id) or not valid_id(task.record_id) or type(task.category) is not str or type(task.intent) is not str or not 1<=len(task.intent)<=1000:
                return finish(400,"invalid_host_task")
            if task.category not in CATEGORIES or task.category not in p.categories:return finish(403,"scope_denied")
            if not db.execute("SELECT 1 FROM acl JOIN records USING(tenant,category,id) WHERE principal=? AND tenant=? AND category=? AND id=?",(p.id,p.tenant,task.category,task.record_id)).fetchone():
                return finish(403,"scope_denied")
            if db.execute("SELECT 1 FROM inference_requests WHERE principal=? AND id=?",(p.id,task.request_id)).fetchone() or db.execute("SELECT 1 FROM requests WHERE principal=? AND id=?",(p.id,task.request_id)).fetchone():
                return finish(409,"replay")
            used=db.execute("SELECT count FROM inference_usage WHERE principal=?",(p.id,)).fetchone()
            read=db.execute("SELECT count FROM usage WHERE principal=?",(p.id,)).fetchone()
            if (used and used[0]>=p.budget) or (read and read[0]>=p.budget):return finish(429,"inference_budget_exhausted")
            db.execute("INSERT INTO inference_requests VALUES(?,?)",(p.id,task.request_id))
            db.execute("INSERT INTO inference_usage VALUES(?,1) ON CONFLICT(principal) DO UPDATE SET count=count+1",(p.id,))
            return finish(200,"inference_reserved")
        except BaseException:db.rollback();raise
        finally:db.close()
    def _denial(self,auth,reason):
        p=self.service.authenticate(auth)
        if not p:return
        db=self.service.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            self.service._audit(db,p.id,reason,403,int(self.service.clock()))
            db.commit()
        except BaseException:db.rollback();raise
        finally:db.close()
    def run(self,auth,task):
        started=self.clock(); trace_id=uuid.uuid4().hex; called=False
        def finish(status,reason,output=None):
            return {"status":status,"reason":reason,"output":output,"trace":{"id":trace_id,"provider_called":called,"elapsed_ms":round((self.clock()-started)*1000,3)}}
        try:
            code,reason=self._reserve(auth,task)
            if code!=200:return finish("blocked",reason)
            # Only the approved public operation description and caller-supplied intent.
            # No record payload, auth token, tenant id, audit key or permission lists.
            called=True
            try:
                raw=self.provider({"version":"1.0","action":"read_record","category":task.category,"record_id":task.record_id},task.intent)
                if type(raw) is not str or len(raw)>4096:raise ValueError("invalid proposal")
                proposal=strict_json(raw)
            except Exception:
                self._denial(auth,"provider_or_proposal_failure")
                return finish("blocked","provider_or_proposal_failure")
            expected={"version":"1.0","action":"read_record","category":task.category,"record_id":task.record_id}
            if type(proposal) is not dict or proposal!=expected:
                self._denial(auth,"proposal_mismatch")
                return finish("blocked","proposal_mismatch")
            # Recheck the exact host-bound proposal and ACL inside existing transaction.
            status,result=self.service.read(auth,{"version":"1.0","request_id":task.request_id,"category":task.category,"record_id":task.record_id,"proposal":proposal})
            return finish(result["status"],result["reason"],result["output"])
        except (sqlite3.Error,OSError):
            return finish("blocked","storage_unavailable")

def fixture_provider(expected,intent):
    """Deterministic control, not a model."""
    return json.dumps(expected)
