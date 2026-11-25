import unittest,tempfile,threading
from pathlib import Path
from intelligence.authorized_store import AuthorizedStore
class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/"test.db");self.s=AuthorizedStore(self.path);self.sid=self.s.create_session("demo",1,30,10);self.t=self.s.grant(self.sid,"INV-001",20,10);self.p={"action":"lookup_invoice","invoice":"INV-001"}
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def test_persist(self):
        self.s.close();self.s=AuthorizedStore(self.path);self.assertEqual(self.s.read(self.sid,self.t,self.p,11)["output"],{"amount_cents":12500})
    def test_replay(self):
        self.assertTrue(self.s.read(self.sid,self.t,self.p,11)["allowed"]);self.assertFalse(self.s.read(self.sid,self.t,self.p,11)["allowed"])
    def test_bound(self):self.assertFalse(self.s.read(self.sid,self.t,{**self.p,"invoice":"INV-002"},11)["allowed"])
    def test_cross_session(self):
        sid=self.s.create_session("other",2,30,10);self.assertFalse(self.s.read(sid,self.t,self.p,11)["allowed"])
    def test_extra_tenant(self):self.assertFalse(self.s.read(self.sid,self.t,{**self.p,"tenant":"other"},11)["allowed"])
    def test_expiry(self):self.assertFalse(self.s.read(self.sid,self.t,self.p,20)["allowed"])
    def test_budget(self):
        t2=self.s.grant(self.sid,"INV-001",20,10);self.s.read(self.sid,self.t,self.p,11);self.assertFalse(self.s.read(self.sid,t2,self.p,11)["allowed"])
    def test_parallel(self):
        barrier=threading.Barrier(2);res=[]
        def run():
            db=AuthorizedStore(self.path)
            try:barrier.wait(timeout=5);res.append(db.read(self.sid,self.t,self.p,11)["allowed"])
            finally:db.close()
        a=threading.Thread(target=run);b=threading.Thread(target=run);a.start();b.start();a.join(10);b.join(10)
        self.assertEqual(sorted(res),[False,True])
    def test_audit(self):
        self.s.read(self.sid,self.t,self.p,11);self.s.read(self.sid,self.t,self.p,11);self.assertEqual(self.s.db.execute("SELECT decision FROM audit ORDER BY id").fetchall(),[("allow",),("deny",)])
