import json,tempfile,unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from swapnil_ai_labs.goal_agents import GoalAgents,GOALS,GoalError
from swapnil_ai_labs.goal_agent_demo import run
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/"db";self.now=100;self.key=b"x"*32
        self.a=GoalAgents(self.path,self.key,lambda:self.now)
        self.a.set_task("a","task","research",{"hypothesis":"ref-1"},0)
    def tearDown(self):self.tmp.cleanup()
    def grant(self,nonce="one",ttl=60):return self.a.grant("a","task","research",1,nonce,ttl=ttl)
    def execute(self,g,tenant="a",category="research"):return self.a.run(g,tenant=tenant,category=category)
    def expect(self,reason,fn):
        with self.assertRaises(GoalError) as e:fn()
        self.assertEqual(str(e.exception),reason)
    def test_all_categories(self):self.assertEqual(len(run()["agents"]),14)
    def test_missing(self):
        r=self.execute(self.grant());self.assertIn("raw_results",r["missing"]);self.assertFalse(r["verified_completion"])
    def test_complete_refs_not_completion(self):
        rev=self.a.set_task("a","task","research",{k:"ref-"+k for k in GOALS["research"].checks},1)
        r=self.execute(self.a.grant("a","task","research",rev,"two"))
        self.assertEqual(r["status"],"ready_for_independent_review");self.assertFalse(r["verified_completion"])
    def test_tamper(self):
        g=json.loads(self.grant());g["body"]["purpose"]="approve"
        self.expect("invalid_signature",lambda:self.execute(json.dumps(g)))
    def test_cross_category(self):self.expect("scope_denied",lambda:self.execute(self.grant(),category="security"))
    def test_cross_tenant(self):self.expect("scope_denied",lambda:self.execute(self.grant(),tenant="b"))
    def test_expiration(self):
        g=self.grant(ttl=1);self.now=101
        self.expect("expired_grant",lambda:self.execute(g))
    def test_stale_revision(self):
        g=self.grant();self.a.set_task("a","task","research",{},1)
        self.expect("stale_or_unknown_task",lambda:self.execute(g))
    def test_restart_replay(self):
        g=self.grant();self.execute(g);self.a=GoalAgents(self.path,self.key,lambda:self.now)
        self.expect("replay",lambda:self.execute(g))
    def test_concurrent_replay(self):
        g=self.grant()
        def attempt(_):
            try:self.execute(g);return "ok"
            except GoalError as e:return str(e)
        with ThreadPoolExecutor(max_workers=8) as x:r=list(x.map(attempt,range(8)))
        self.assertEqual(r.count("ok"),1);self.assertEqual(r.count("replay"),7)
    def test_unknown_evidence(self):self.expect("invalid_evidence",lambda:self.a.set_task("a","task","research",{"approve":"yes"},1))
    def test_revision_conflict(self):self.expect("revision_conflict",lambda:self.a.set_task("a","task","research",{},0))
    def test_malformed(self):
        for g in ("{}","[]","not json","x"*2049):
            self.expect("invalid_grant",lambda:self.execute(g))
    def test_invalid_grant_inputs(self):
        self.expect("invalid_grant",lambda:self.a.grant("a","task","research",1,"one",ttl=301))
if __name__=="__main__":unittest.main()
