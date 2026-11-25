import tempfile,unittest,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from secure_service.service import Service,Principal,digest,CATEGORIES
from swapnil_ai_labs.trusted_runtime import TrustedRuntime,HostTask,fixture_provider
from swapnil_ai_labs.intent_authority import IntentAuthority
from swapnil_ai_labs.evidence_integrity import manifest,verify_manifest,checkpoint,verify_checkpoint
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/"s.db";self.now=100
        self.token="a"*40;self.auth="Bearer "+self.token;self.other="Bearer "+"b"*40
        self.ps=[Principal("a","tenant-a",digest(self.token),CATEGORIES),Principal("b","tenant-b",digest("b"*40),CATEGORIES)]
        self.s=Service(self.path,self.ps,b"s"*32,clock=lambda:self.now)
        self.s.seed_record("tenant-a","finance","record",{"synthetic":True},["a"])
        self.calls=[]
        def provider(e,i):self.calls.append(e);return json.dumps(e)
        self.r=TrustedRuntime(self.s,provider);self.g=IntentAuthority(self.r,b"g"*32,clock=lambda:self.now)
        self.t=HostTask("request","finance","record","Read this specific record")
    def tearDown(self):self.tmp.cleanup()
    def grant(self,nonce="nonce",ttl=60):return self.g.issue(self.auth,self.t,nonce,ttl=ttl)
    def test_authorized(self):
        r=self.g.run(self.auth,self.t,self.grant());self.assertEqual(r["status"],"executed_read_only");self.assertEqual(len(self.calls),1)
    def test_no_grant(self):
        self.assertEqual(self.g.run(self.auth,self.t,"{}")["reason"],"invalid_grant");self.assertFalse(self.calls)
    def test_altered_intent(self):
        t=HostTask("request","finance","record","Delete this record")
        self.assertEqual(self.g.run(self.auth,t,self.grant())["reason"],"grant_scope_denied");self.assertFalse(self.calls)
    def test_altered_target(self):
        t=HostTask("request","finance","other","Read this specific record")
        self.assertEqual(self.g.run(self.auth,t,self.grant())["reason"],"grant_scope_denied");self.assertFalse(self.calls)
    def test_other_principal(self):
        self.assertEqual(self.g.run(self.other,self.t,self.grant())["reason"],"grant_scope_denied");self.assertFalse(self.calls)
    def test_expiry(self):
        g=self.grant(ttl=1);self.now=101
        self.assertEqual(self.g.run(self.auth,self.t,g)["reason"],"expired_grant");self.assertFalse(self.calls)
    def test_revocation(self):
        g=self.grant();self.g.revoke("a","nonce")
        self.assertEqual(self.g.run(self.auth,self.t,g)["reason"],"revoked_grant");self.assertFalse(self.calls)
    def test_tamper(self):
        g=json.loads(self.grant());g["body"]["expires"]=999999
        self.assertEqual(self.g.run(self.auth,self.t,json.dumps(g))["reason"],"invalid_grant");self.assertFalse(self.calls)
    def test_independent_acl(self):
        t=HostTask("another","finance","unknown","Read selected record")
        g=self.g.issue(self.auth,t,"two")
        self.assertEqual(self.g.run(self.auth,t,g)["reason"],"scope_denied")
        self.assertEqual(self.g.run(self.auth,t,g)["reason"],"grant_replay");self.assertFalse(self.calls)
    def test_concurrent(self):
        g=self.grant()
        with ThreadPoolExecutor(max_workers=8) as pool:r=list(pool.map(lambda _:self.g.run(self.auth,self.t,g),range(8)))
        self.assertEqual(sum(x["status"]=="executed_read_only" for x in r),1);self.assertEqual(len(self.calls),1)
        self.assertEqual(sum(x["reason"]=="grant_replay" for x in r),7)
    def test_restart(self):
        g=self.grant();self.g.run(self.auth,self.t,g)
        self.g=IntentAuthority(TrustedRuntime(Service(self.path,self.ps,b"s"*32,clock=lambda:self.now),fixture_provider),b"g"*32,clock=lambda:self.now)
        self.assertEqual(self.g.run(self.auth,self.t,g)["reason"],"grant_replay")
    def test_manifest(self):
        m=manifest("tenant-a","doc","source","v1",b"original")
        self.assertTrue(verify_manifest(m,"tenant-a","doc","source","v1",b"original"))
        self.assertFalse(verify_manifest(m,"tenant-a","doc","source","v1",b"tampered"))
        self.assertFalse(verify_manifest(m,"tenant-b","doc","source","v1",b"original"))
    def test_checkpoint_tail(self):
        self.g.run(self.auth,self.t,self.grant());a=checkpoint(self.s,b"c"*32)
        self.assertTrue(verify_checkpoint(self.s,b"c"*32,a))
        with self.s.connect() as db:db.execute("DELETE FROM audit WHERE seq=(SELECT MAX(seq) FROM audit)")
        self.assertTrue(self.s.verify_audit());self.assertFalse(verify_checkpoint(self.s,b"c"*32,a))
    def test_checkpoint_extension(self):
        a=checkpoint(self.s,b"c"*32);self.g.run(self.auth,self.t,self.grant())
        self.assertTrue(verify_checkpoint(self.s,b"c"*32,a))
        self.assertFalse(verify_checkpoint(self.s,b"d"*32,a))
if __name__=="__main__":unittest.main()
