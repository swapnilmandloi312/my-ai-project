import tempfile,unittest,json
from pathlib import Path
from secure_service.service import Service,Principal,digest,CATEGORIES
from swapnil_ai_labs.work_relay import WorkRelay,RelayPrincipal,REQUIRED,RelayError
from swapnil_ai_labs.trusted_runtime import TrustedRuntime,fixture_provider
from swapnil_ai_labs.relay_evidence import RelayEvidence,EVIDENCE_CATEGORY
class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name);self.a="a"*40;self.r="r"*40;self.o="o"*40;self.s="s"*40;self.other="b"*40
        ps=[RelayPrincipal(i,"tenant-a",digest(t),role,frozenset(REQUIRED)) for i,t,role in [("requester",self.a,"requester"),("reviewer",self.r,"reviewer"),("operator",self.o,"operator")]]
        self.relay=WorkRelay(p/"relay.db",ps,b"r"*32)
        self.service=Service(p/"read.db",[Principal("reviewer","tenant-a",digest(self.s),CATEGORIES),Principal("reviewer-b","tenant-b",digest(self.other),CATEGORIES)],b"s"*32)
        self.calls=[]
        def provider(expected,intent):self.calls.append(expected);return json.dumps(expected)
        self.runtime=TrustedRuntime(self.service,provider);self.bridge=RelayEvidence(self.relay,self.runtime)
    def tearDown(self):self.tmp.cleanup()
    def cmd(self,token,item,action,rev,data=None):
        return self.relay.command("Bearer "+token,{"command_id":item+"-"+action+"-"+str(rev),"item_id":item,"action":action,"revision":rev,"data":data or {}})
    def ready(self,dep="finance",acl=True):
        item="case-"+dep;row=self.cmd(self.a,item,"create",0,{"department":dep})
        for k in sorted(REQUIRED[dep]):
            rid=dep+"-"+k;row=self.cmd(self.a,item,"attach",row["revision"],{"key":k,"reference":rid})
            self.service.seed_record("tenant-a",EVIDENCE_CATEGORY[dep],rid,{"synthetic":True,"value":"not exposed"},["reviewer"] if acl else [])
        return self.cmd(self.a,item,"submit",row["revision"])
    def inspect(self,row,**kw):
        args={"item_id":row["id"],"evidence_key":row["evidence_keys"][0],"revision":row["revision"],"request_id":row["id"]+"-inspect"};args.update(kw)
        return self.bridge.inspect("Bearer "+self.r,"Bearer "+self.s,**args)
    def test_four_departments(self):
        for dep in REQUIRED:
            row=self.ready(dep);out=self.inspect(row)
            self.assertEqual(out["status"],"retrieved");self.assertFalse(out["approval_granted"]);self.assertNotIn("not exposed",str(out))
            self.assertEqual(self.relay.get("Bearer "+self.r,row["id"]),row)
        self.assertEqual(len(self.calls),4);self.assertTrue(self.service.verify_audit());self.assertTrue(self.relay.verify_audit())
    def test_acl_denied_before_inference(self):
        out=self.inspect(self.ready(acl=False));self.assertEqual(out["reason"],"scope_denied");self.assertFalse(self.calls)
    def test_wrong_principal(self):
        row=self.ready()
        with self.assertRaises(RelayError) as ctx:self.bridge.inspect("Bearer "+self.r,"Bearer "+self.other,item_id=row["id"],evidence_key="invoice",revision=row["revision"],request_id="wrong")
        self.assertEqual(ctx.exception.reason,"principal_mismatch");self.assertFalse(self.calls)
    def test_requester_cannot_infer(self):
        row=self.ready()
        with self.assertRaises(RelayError) as ctx:self.bridge.inspect("Bearer "+self.a,"Bearer "+self.s,item_id=row["id"],evidence_key="invoice",revision=row["revision"],request_id="wrong")
        self.assertEqual(ctx.exception.reason,"role_denied");self.assertFalse(self.calls)
    def test_revision_and_key(self):
        row=self.ready()
        for kw in ({"revision":0},{"evidence_key":"other-record"}):
            with self.assertRaises(RelayError):self.inspect(row,**kw)
        self.assertFalse(self.calls)
    def test_provider_cannot_change_target(self):
        row=self.ready();self.runtime.provider=lambda e,i:json.dumps({**e,"record_id":"other"})
        self.assertEqual(self.inspect(row)["reason"],"proposal_mismatch")
    def test_replay(self):
        row=self.ready();self.inspect(row);self.assertEqual(self.inspect(row)["reason"],"replay");self.assertEqual(len(self.calls),1)
    def test_stale_review(self):
        row=self.ready()
        def provider(e,i):self.cmd(self.r,row["id"],"reject",row["revision"]);return json.dumps(e)
        self.runtime.provider=provider
        self.assertEqual(self.inspect(row)["reason"],"stale_review")
if __name__=="__main__":unittest.main()
