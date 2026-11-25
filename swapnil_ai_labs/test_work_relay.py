import json,tempfile,unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from secure_service.service import digest
from swapnil_ai_labs.work_relay import WorkRelay,RelayPrincipal,RelayError,REQUIRED
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/"relay.db";self.key=b"x"*32
        self.tokens={k:"fixture-"+k+"-"+"x"*40 for k in ["a","b","r","o","other"]}
        self.ps=[RelayPrincipal(k,"tenant-b" if k=="other" else "tenant-a",digest(v),{"a":"requester","b":"requester","r":"reviewer","o":"operator","other":"requester"}[k],frozenset(REQUIRED)) for k,v in self.tokens.items()]
        self.s=WorkRelay(self.path,self.ps,self.key)
    def tearDown(self):self.tmp.cleanup()
    def auth(self,k):return "Bearer "+self.tokens[k]
    def cmd(self,k,action,rev,data=None,item="case-1",cid=None):
        return self.s.command(self.auth(k),{"command_id":cid or action+"-"+str(rev),"item_id":item,"action":action,"revision":rev,"data":data or {}})
    def expect(self,reason,fn):
        with self.assertRaises(RelayError) as e:fn()
        self.assertEqual(e.exception.reason,reason)
    def ready(self,dep="finance",item="case-1"):
        r=self.cmd("a","create",0,{"department":dep},item,cid="create-"+item)
        for key in sorted(REQUIRED[dep]):
            r=self.cmd("a","attach",r["revision"],{"key":key,"reference":"ref-"+key},item,cid=item+"-"+key)
        return self.cmd("a","submit",r["revision"],item=item,cid="submit-"+item)
    def test_all_departments(self):
        for i,dep in enumerate(REQUIRED):
            item="item-"+str(i);r=self.ready(dep,item)
            self.assertEqual(r["state"],"awaiting_review")
            r=self.cmd("r","approve",r["revision"],item=item,cid="ap-"+item)
            r=self.cmd("o","resolve",r["revision"],item=item,cid="res-"+item)
            self.assertEqual(r["state"],"resolved_local");self.assertFalse(r["external_action"])
    def test_missing_evidence(self):
        self.cmd("a","create",0,{"department":"finance"})
        r=self.cmd("a","submit",1);self.assertEqual(r["state"],"needs_evidence")
        self.assertEqual(len(r["missing"]),2)
        self.expect("invalid_state",lambda:self.cmd("r","approve",2))
    def test_creator_cannot_approve(self):
        r=self.ready();self.expect("role_denied",lambda:self.cmd("a","approve",r["revision"]))
    def test_no_approval_no_resolution(self):
        r=self.ready();self.expect("approval_required",lambda:self.cmd("o","resolve",r["revision"]))
    def test_rejected_terminal(self):
        r=self.ready();r=self.cmd("r","reject",r["revision"])
        self.expect("approval_required",lambda:self.cmd("o","resolve",r["revision"]))
        self.expect("invalid_state",lambda:self.cmd("a","attach",r["revision"],{"key":"invoice","reference":"new"}))
    def test_cross_tenant(self):
        self.ready();self.expect("not_found",lambda:self.s.get(self.auth("other"),"case-1"))
    def test_same_tenant_requester_isolation(self):
        self.ready();self.expect("not_found",lambda:self.s.get(self.auth("b"),"case-1"))
    def test_idempotency_restart(self):
        r=self.cmd("a","create",0,{"department":"finance"})
        self.s=WorkRelay(self.path,self.ps,self.key)
        self.assertEqual(self.cmd("a","create",0,{"department":"finance"}),r)
        self.expect("idempotency_conflict",lambda:self.cmd("a","create",0,{"department":"it"}))
    def test_stale_revision(self):
        self.ready();self.expect("revision_conflict",lambda:self.cmd("r","approve",1))
    def test_concurrent_approval(self):
        r=self.ready()
        def call(i):
            try:return self.cmd("r","approve",r["revision"],cid="ap-"+str(i))["state"]
            except RelayError as e:return e.reason
        with ThreadPoolExecutor(max_workers=8) as ex:out=list(ex.map(call,range(8)))
        self.assertEqual(out.count("approved"),1);self.assertEqual(out.count("revision_conflict"),7)
    def test_invalid_evidence(self):
        self.cmd("a","create",0,{"department":"it"})
        self.expect("invalid_evidence",lambda:self.cmd("a","attach",1,{"key":"password","reference":"secret"}))
    def test_unknown_data(self):
        r=self.ready();self.expect("unexpected_data",lambda:self.cmd("r","approve",r["revision"],{"model_approved":True}))
    def test_unauthenticated(self):
        self.expect("authentication_required",lambda:self.s.get("bad","case-1"))
    def test_audit_tampering(self):
        self.ready();self.assertTrue(self.s.verify_audit())
        with self.s.connect() as db:
            events=str(db.execute("SELECT event FROM relay_events").fetchall())
            self.assertNotIn(self.tokens["a"],events)
            db.execute("UPDATE relay_events SET event='{}' WHERE seq=1")
        self.assertFalse(self.s.verify_audit())
    def test_evidence_immutable_after_submit(self):
        r=self.ready();self.expect("invalid_state",lambda:self.cmd("a","attach",r["revision"],{"key":"invoice","reference":"replacement"}))
if __name__=="__main__":unittest.main()
