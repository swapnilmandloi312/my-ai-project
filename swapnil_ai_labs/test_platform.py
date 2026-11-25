import json,tempfile,unittest
from pathlib import Path
from intelligence.authorized_store import AuthorizedStore
from intelligence.memory import Memory
from intelligence.routing import Candidate
from swapnil_ai_labs.platform import ResearchPlatform,HostRequest,fixture_provider
from swapnil_ai_labs.contracts import decode
class Platform(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=AuthorizedStore(str(Path(self.tmp.name)/"demo.db"));self.memory=Memory()
        sid=self.store.create_session("demo",1,30,10);token=self.store.grant(sid,"INV-001",20,10)
        self.req=HostRequest(sid,"demo","INV-001",token);self.p=ResearchPlatform(self.store,self.memory)
    def tearDown(self):self.store.close();self.memory.close();self.tmp.cleanup()
    def run_demo(self,provider=fixture_provider,req=None,**kw):
        return self.p.run(self.req if req is None else req,"invoice amount",[{"text":"invoice amount private-fixture"}],[Candidate("fixture",1,.95,10)],provider,now=11,**kw)
    def test_end_to_end(self):self.assertEqual(self.run_demo()["output"],{"amount_cents":12500})
    def test_replay(self):self.run_demo();self.assertEqual(self.run_demo()["status"],"blocked")
    def test_budget(self):self.assertEqual(self.run_demo(model_budget=0)["reason"],"no eligible model")
    def test_mismatch(self):self.assertEqual(self.run_demo(lambda *x:'{"version":"1.0","action":"lookup_invoice","invoice":"INV-002"}')["reason"],"proposal does not match host request")
    def test_tenant_binding(self):self.assertEqual(self.run_demo(req=HostRequest(self.req.session_id,"other",self.req.invoice,self.req.grant))["reason"],"host tenant mismatch")
    def test_error(self):
        def fail(*a):raise RuntimeError("secret token")
        r=self.run_demo(fail);self.assertEqual(r["status"],"blocked");self.assertNotIn("secret token",json.dumps(r))
    def test_trace_redaction(self):
        trace=json.dumps(self.run_demo()["trace"]);self.assertNotIn(self.req.grant,trace);self.assertNotIn("private-fixture",trace);self.assertNotIn(self.req.session_id,trace)
    def test_version(self):
        with self.assertRaises(ValueError):decode('{"version":"2.0","action":"lookup_invoice","invoice":"INV-001"}')
    def test_duplicate(self):
        with self.assertRaises(ValueError):decode('{"version":"1.0","action":"lookup_invoice","invoice":"INV-001","invoice":"INV-002"}')
    def test_extra(self):
        with self.assertRaises(ValueError):decode('{"version":"1.0","action":"lookup_invoice","invoice":"INV-001","tenant":"other"}')
    def test_invalid_invoice(self):
        with self.assertRaises(ValueError):decode('{"version":"1.0","action":"lookup_invoice","invoice":"INV-1;"}')
if __name__=="__main__":unittest.main()
