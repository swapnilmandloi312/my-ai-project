import json,tempfile,unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from secure_service.service import Service
from secure_service.fixtures import principals,seed,TOKEN_A,TOKEN_B
from swapnil_ai_labs.trusted_runtime import TrustedRuntime,HostTask,fixture_provider
class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.s=Service(Path(self.temp.name)/"test.db",principals(limit=100,budget=5),b"x"*32)
        seed(self.s,n=4)
        self.calls=[]
        def provider(expected,intent):
            self.calls.append((expected,intent));return json.dumps(expected)
        self.r=TrustedRuntime(self.s,provider)
        self.a="Bearer "+TOKEN_A
    def tearDown(self):self.temp.cleanup()
    def task(self,rid="finance-000",req="req-1",cat="finance",intent="Read selected record"):
        return HostTask(req,cat,rid,intent)
    def test_valid(self):
        r=self.r.run(self.a,self.task());self.assertEqual(r["status"],"executed_read_only");self.assertEqual(r["output"]["amount_cents"],10000);self.assertEqual(len(self.calls),1)
    def test_no_payload_or_credentials_in_model_context(self):
        self.r.run(self.a,self.task());expected,intent=self.calls[0];self.assertEqual(set(expected),{"version","action","category","record_id"});self.assertNotIn(TOKEN_A,str(self.calls));self.assertNotIn("amount_cents",str(self.calls))
    def test_unauthenticated(self):
        self.assertEqual(self.r.run("bad",self.task())["reason"],"authentication_required");self.assertFalse(self.calls)
    def test_invalid_record_scope(self):
        self.assertEqual(self.r.run(self.a,self.task("finance-001"))["reason"],"scope_denied");self.assertFalse(self.calls)
    def test_missing_record(self):
        self.assertEqual(self.r.run(self.a,self.task("finance-999"))["reason"],"scope_denied");self.assertFalse(self.calls)
    def test_unknown_category(self):
        self.assertEqual(self.r.run(self.a,self.task(cat="medical"))["reason"],"scope_denied");self.assertFalse(self.calls)
    def test_invalid_intent(self):
        self.assertEqual(self.r.run(self.a,self.task(intent="x"*1001))["reason"],"invalid_host_task");self.assertFalse(self.calls)
    def test_cross_tenant(self):
        a=self.r.run(self.a,self.task());b=self.r.run("Bearer "+TOKEN_B,self.task());self.assertEqual(a["output"]["value"],100);self.assertEqual(b["output"]["value"],900)
    def test_replay(self):
        self.r.run(self.a,self.task());self.assertEqual(self.r.run(self.a,self.task())["reason"],"replay");self.assertEqual(len(self.calls),1)
    def test_budget(self):
        for i in range(5):self.assertEqual(self.r.run(self.a,self.task(req="r-"+str(i)))["status"],"executed_read_only")
        self.assertEqual(self.r.run(self.a,self.task(req="extra"))["reason"],"inference_budget_exhausted");self.assertEqual(len(self.calls),5)
    def test_provider_mismatch(self):
        self.r.provider=lambda expected,intent:json.dumps({**expected,"record_id":"finance-002"})
        self.assertEqual(self.r.run(self.a,self.task())["reason"],"proposal_mismatch")
    def test_provider_write(self):
        self.r.provider=lambda expected,intent:json.dumps({**expected,"action":"write_record"})
        self.assertEqual(self.r.run(self.a,self.task())["reason"],"proposal_mismatch")
    def test_extra_fields(self):
        self.r.provider=lambda expected,intent:json.dumps({**expected,"tenant":"tenant-b"})
        self.assertEqual(self.r.run(self.a,self.task())["reason"],"proposal_mismatch")
    def test_duplicate_keys(self):
        self.r.provider=lambda expected,intent:'{"action":"write","action":"read_record"}'
        self.assertEqual(self.r.run(self.a,self.task())["reason"],"provider_or_proposal_failure")
    def test_malformed(self):
        self.r.provider=lambda expected,intent:"not json"
        self.assertEqual(self.r.run(self.a,self.task())["reason"],"provider_or_proposal_failure")
    def test_failure_consumes_reservation(self):
        self.r.provider=lambda expected,intent:"bad"
        self.r.run(self.a,self.task());self.r.provider=fixture_provider
        self.assertEqual(self.r.run(self.a,self.task())["reason"],"replay")
    def test_revocation_between_inference_and_execution(self):
        def provider(expected,intent):
            with self.s.connect() as db:db.execute("DELETE FROM acl WHERE principal='reader-a' AND category='finance' AND id='finance-000'")
            return json.dumps(expected)
        self.r.provider=provider
        self.assertEqual(self.r.run(self.a,self.task())["reason"],"scope_denied")
    def test_concurrent_replay(self):
        with ThreadPoolExecutor(max_workers=8) as pool:r=list(pool.map(lambda _:self.r.run(self.a,self.task()),range(8)))
        self.assertEqual(sum(x["status"]=="executed_read_only" for x in r),1);self.assertEqual(len(self.calls),1)
    def test_audit(self):
        self.r.run(self.a,self.task());self.assertTrue(self.s.verify_audit())
        with self.s.connect() as db:
            logs=str(db.execute("SELECT event FROM audit").fetchall())
            self.assertNotIn(TOKEN_A,logs);self.assertNotIn("Read selected record",logs)
    def test_budget_survives_restart(self):
        self.r.run(self.a,self.task());r=TrustedRuntime(self.s,fixture_provider)
        self.assertEqual(r.run(self.a,self.task())["reason"],"replay")
if __name__=="__main__":unittest.main()
