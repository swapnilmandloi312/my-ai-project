"""Local explicit delegated read authority; trusted issuer, no public endpoint."""
from contextlib import closing
import hashlib,hmac,json,time
from secure_service.service import canonical,valid_id,strict_json,CATEGORIES
from swapnil_ai_labs.trusted_runtime import HostTask

class IntentAuthority:
    def __init__(self,runtime,key,clock=time.time):
        if type(key) is not bytes or len(key)<32:raise ValueError("key")
        self.runtime=runtime;self.key=key;self.clock=clock
        with closing(runtime.service.connect()) as db:db.executescript("""
        CREATE TABLE IF NOT EXISTS intent_grants_used(principal TEXT,nonce TEXT,PRIMARY KEY(principal,nonce));
        CREATE TABLE IF NOT EXISTS intent_grants_revoked(principal TEXT,nonce TEXT,PRIMARY KEY(principal,nonce));
        """)
    def _mac(self,body):
        return hmac.new(self.key,canonical(body).encode(),hashlib.sha256).hexdigest()
    def _valid_task(self,t):
        return isinstance(t,HostTask) and valid_id(t.request_id) and valid_id(t.record_id) and type(t.category) is str and t.category in CATEGORIES and type(t.intent) is str and 1<=len(t.intent)<=1000
    def _binding(self,p,t):
        return {"principal":p.id,"tenant":p.tenant,"request":t.request_id,"category":t.category,"record":t.record_id,"intent_mac":hmac.new(self.key,t.intent.encode(),hashlib.sha256).hexdigest(),"audience":"trusted-runtime","purpose":"read_record"}
    def issue(self,auth,task,nonce,*,ttl=60):
        """Trusted human/host approval path only. Caller must verify consent independently."""
        p=self.runtime.service.authenticate(auth)
        if p is None or not self._valid_task(task) or not valid_id(nonce) or type(ttl) is not int or not 1<=ttl<=300:raise ValueError("invalid grant")
        body={**self._binding(p,task),"nonce":nonce,"expires":int(self.clock())+ttl}
        return canonical({"body":body,"mac":self._mac(body)})
    def revoke(self,principal,nonce):
        """Trusted administrator only; does not cancel inference already admitted."""
        if not valid_id(principal) or not valid_id(nonce):raise ValueError("invalid revocation")
        with closing(self.runtime.service.connect()) as db:db.execute("INSERT OR IGNORE INTO intent_grants_revoked VALUES(?,?)",(principal,nonce))
    def run(self,auth,task,grant):
        def blocked(reason):
            return {"status":"blocked","reason":reason,"output":None,"trace":{"provider_called":False}}
        p=self.runtime.service.authenticate(auth)
        if p is None:return blocked("authentication_required")
        if not self._valid_task(task) or type(grant) is not str or len(grant)>4096:return blocked("invalid_grant")
        binding=self._binding(p,task)
        try:
            e=strict_json(grant);b=e["body"]
            if type(e) is not dict or set(e)!={"body","mac"} or type(b) is not dict or set(b)!=set(binding)|{"nonce","expires"} or type(e["mac"]) is not str or not hmac.compare_digest(e["mac"],self._mac(b)):return blocked("invalid_grant")
            if any(b[k]!=v for k,v in binding.items()) or not valid_id(b["nonce"]) or type(b["expires"]) is not int:return blocked("grant_scope_denied")
        except (TypeError,ValueError,KeyError,RecursionError):return blocked("invalid_grant")
        with closing(self.runtime.service.connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                reason=None
                if int(self.clock())>=b["expires"]:reason="expired_grant"
                elif db.execute("SELECT 1 FROM intent_grants_revoked WHERE principal=? AND nonce=?",(p.id,b["nonce"])).fetchone():reason="revoked_grant"
                elif db.execute("SELECT 1 FROM intent_grants_used WHERE principal=? AND nonce=?",(p.id,b["nonce"])).fetchone():reason="grant_replay"
                if reason:
                    self.runtime.service._audit(db,p.id,reason,403,int(self.clock()));db.commit();return blocked(reason)
                db.execute("INSERT INTO intent_grants_used VALUES(?,?)",(p.id,b["nonce"]))
                self.runtime.service._audit(db,p.id,"intent_grant_consumed",200,int(self.clock()));db.commit()
            except BaseException:db.rollback();raise
        # Independent runtime still enforces record ACL, budget and request replay.
        # The grant is consumed even when the runtime fails or denies.
        return self.runtime.run(auth,task)
