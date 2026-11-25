import tempfile,unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from swapnil_ai_labs.goal_agents import GoalAgents,GoalError
from swapnil_ai_labs.goal_queue import GoalQueue
from swapnil_ai_labs.goal_queue_demo import run
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/"goals.db";self.now=100;self.key=b"x"*32
        self.a=GoalAgents(self.path,self.key,lambda:self.now);self.q=GoalQueue(self.a)
        self.a.set_task("a","task","research",{},0)
    def tearDown(self):self.tmp.cleanup()
    def add(self,**kw):return self.q.enqueue("a","job","task","research",1,**kw)
    def expect(self,reason,fn):
        with self.assertRaises(GoalError) as e:fn()
        self.assertEqual(str(e.exception),reason)
    def test_all_categories(self):self.assertEqual(run()["evaluated"],14)
    def test_idempotent_enqueue(self):
        self.add();self.add();self.assertEqual(len(self.q.snapshot("a")["jobs"]),1)
        self.expect("job_conflict",lambda:self.add(max_attempts=2))
    def test_pause(self):
        self.add();self.q.pause("a");self.assertIsNone(self.q.claim("a"));self.q.pause("a",False);self.assertEqual(len(self.q.tick("a")),1)
    def test_isolation(self):
        self.add();self.assertEqual(self.q.snapshot("b")["jobs"],[]);self.assertIsNone(self.q.claim("b"))
    def test_concurrent_claim(self):
        self.add()
        with ThreadPoolExecutor(max_workers=8) as pool:r=list(pool.map(lambda _:self.q.claim("a"),range(8)))
        self.assertEqual(sum(x is not None for x in r),1)
    def test_lease_recovery(self):
        self.add();old=self.q.claim("a",lease_seconds=2);self.now=102
        self.expect("lease_lost",lambda:self.q.execute(old))
        new=self.q.claim("a");self.assertNotEqual(old["lease_token"],new["lease_token"])
        self.assertEqual(self.q.execute(new)["status"],"needs_evidence")
        self.assertEqual(self.q.snapshot("a")["jobs"][0]["attempts"],2)
    def test_exhausted(self):
        self.add(max_attempts=1);self.q.claim("a",lease_seconds=1);self.now=101
        self.assertIsNone(self.q.claim("a"));self.assertEqual(self.q.snapshot("a")["jobs"][0]["result"]["reason"],"retry_budget_exhausted")
    def test_committed_evaluation_recovery(self):
        self.add(max_attempts=1);self.q.claim("a",lease_seconds=1)
        with self.a.connect() as db:row=db.execute("SELECT nonce FROM goal_jobs").fetchone()
        self.a.run(self.a.grant("a","task","research",1,row["nonce"]),tenant="a",category="research")
        self.now=101;self.assertIsNone(self.q.claim("a"));self.assertEqual(self.q.snapshot("a")["jobs"][0]["status"],"evaluated")
    def test_stale_task(self):
        self.add();self.a.set_task("a","task","research",{},1)
        self.assertEqual(self.q.tick("a")[0]["reason"],"stale_or_unknown_task");self.assertEqual(self.q.snapshot("a")["jobs"][0]["status"],"failed")
    def test_tampered_lease(self):
        self.add();lease=self.q.claim("a");lease["lease_token"]="fake"
        self.expect("lease_lost",lambda:self.q.execute(lease))
    def test_restart(self):
        self.add();self.q=GoalQueue(GoalAgents(self.path,self.key,lambda:self.now))
        self.assertEqual(len(self.q.tick("a")),1);self.assertEqual(self.q.tick("a"),[])
    def test_limit(self):
        self.expect("invalid_limit",lambda:self.q.tick("a",limit=33))
if __name__=="__main__":unittest.main()
