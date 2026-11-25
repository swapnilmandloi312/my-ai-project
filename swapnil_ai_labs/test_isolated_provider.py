import json,os,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from secure_service.fixtures import principals,seed,TOKEN_A
from secure_service.service import Service
from swapnil_ai_labs.isolated_provider import IsolatedJSONProvider,ProviderError,ProviderTimeout,ProviderOutputLimit
from swapnil_ai_labs.trusted_runtime import TrustedRuntime,HostTask

@unittest.skipUnless(os.name=="posix","POSIX worker tests")
class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.cwd=self.tmp.name
        self.service=Service(Path(self.cwd)/"test.db",principals(limit=100,budget=20),b"x"*32)
        seed(self.service,n=4)
        self.auth="Bearer "+TOKEN_A
        self.expected={"version":"1.0","action":"read_record","category":"finance","record_id":"finance-000"}
    def tearDown(self):self.tmp.cleanup()
    def provider(self,code,**kw):
        return IsolatedJSONProvider([sys.executable,"-I","-c",code],cwd=self.cwd,**kw)
    def task(self,rid="finance-000",req="one",intent="Read selected record"):
        return HostTask(req,"finance",rid,intent)
    def test_valid_transport(self):
        p=self.provider("import json,sys; print(json.dumps(json.load(sys.stdin)['expected']))")
        self.assertEqual(json.loads(p(self.expected,"read")),self.expected)
    def test_no_inherited_secret(self):
        p=self.provider("import os; print(os.environ.get('TEST_PROVIDER_SECRET','absent'))")
        with patch.dict(os.environ,{"TEST_PROVIDER_SECRET":"fixture-secret"}):
            self.assertEqual(p(self.expected,"read").strip(),"absent")
    def test_timeout(self):
        p=self.provider("import time; time.sleep(10)",timeout=.2)
        start=time.monotonic()
        with self.assertRaises(ProviderTimeout):p(self.expected,"read")
        self.assertLess(time.monotonic()-start,3)
    def test_output_cap(self):
        p=self.provider("import sys; sys.stdout.write('x'*1000000); sys.stdout.flush()",max_bytes=128)
        with self.assertRaises(ProviderOutputLimit):p(self.expected,"read")
    def test_exact_byte_cap(self):
        self.assertEqual(self.provider("print('a'*7,end='')",max_bytes=7)(self.expected,"read"),"a"*7)
    def test_bad_utf8(self):
        with self.assertRaises(ProviderError):self.provider("import os; os.write(1,b'\\xff')")(self.expected,"read")
    def test_worker_exit_error(self):
        with self.assertRaises(ProviderError):self.provider("raise SystemExit(1)")(self.expected,"read")
    def test_stdout_closed_but_worker_still_running(self):
        p=self.provider("import os,time; os.close(1); time.sleep(10)",timeout=.2)
        with self.assertRaises(ProviderTimeout):p(self.expected,"read")
    def test_group_cleanup_on_timeout(self):
        code="import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time; time.sleep(0.8); open(\\\"escaped.txt\\\",\\\"w\\\").write(\\\"x\\\")']); time.sleep(10)"
        p=self.provider(code,timeout=.2)
        with self.assertRaises(ProviderTimeout):p(self.expected,"read")
        time.sleep(.9)
        self.assertFalse((Path(self.cwd)/"escaped.txt").exists())
    def test_invalid_configuration(self):
        for kw in ({"timeout":0},{"timeout":float("nan")},{"max_bytes":4097}):
            with self.assertRaises(ValueError):self.provider("pass",**kw)
        with self.assertRaises(ValueError):IsolatedJSONProvider(["python"],cwd=self.cwd)
    def test_runtime_success(self):
        r=TrustedRuntime(self.service,self.provider("import json,sys; print(json.dumps(json.load(sys.stdin)['expected']))"))
        out=r.run(self.auth,self.task());self.assertEqual(out["status"],"executed_read_only");self.assertEqual(out["output"]["amount_cents"],10000)
    def test_runtime_timeout_audited_and_reservation_consumed(self):
        r=TrustedRuntime(self.service,self.provider("import time; time.sleep(10)",timeout=.2))
        out=r.run(self.auth,self.task());self.assertEqual(out["reason"],"provider_timeout");self.assertIsNone(out["output"])
        self.assertEqual(r.run(self.auth,self.task())["reason"],"replay");self.assertTrue(self.service.verify_audit())
        with self.service.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM requests").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT count FROM inference_usage").fetchone()[0],1)
            self.assertIn("provider_timeout",str(db.execute("SELECT event FROM audit").fetchall()))
    def test_runtime_output_limit(self):
        r=TrustedRuntime(self.service,self.provider("print('x'*10000)",max_bytes=128))
        self.assertEqual(r.run(self.auth,self.task())["reason"],"provider_output_limit")
    def test_denied_before_worker_start(self):
        r=TrustedRuntime(self.service,self.provider("open('called.txt','w').write('yes')"))
        self.assertEqual(r.run(self.auth,self.task("finance-001"))["reason"],"scope_denied")
        self.assertFalse((Path(self.cwd)/"called.txt").exists())
    def test_worker_cannot_grant_different_record(self):
        p=self.provider("import json,sys; x=json.load(sys.stdin)['expected']; x['record_id']='finance-002'; print(json.dumps(x))")
        self.assertEqual(TrustedRuntime(self.service,p).run(self.auth,self.task())["reason"],"proposal_mismatch")
if __name__=="__main__":unittest.main()
