import tempfile,unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from swapnil_ai_labs.goal_agents import GoalAgents,GoalError,GOALS
from swapnil_ai_labs.goal_queue import GoalQueue
from swapnil_ai_labs.goal_planner import GoalPlanner
from swapnil_ai_labs.goal_broker import Broker,BrokerPrincipal
from secure_service.service import digest
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.a=GoalAgents(Path(self.tmp.name)/"db",b"k"*32);self.q=GoalQueue(self.a);self.calls=[]
        def provider(p,i):self.calls.append(p);return p["allowed_next_steps"][0]
        self.p=GoalPlanner(self.q,provider,daily_budget=2)
    def tearDown(self):self.tmp.cleanup()
    def job(self,tenant="a",job="job",cat="research",all_refs=False):
        ev={k:"private-reference" for k in (GOALS[cat].checks if all_refs else GOALS[cat].checks[:1])}
        rev=self.a.set_task(tenant,job,cat,ev,0);self.q.enqueue(tenant,job,job,cat,rev);self.q.tick(tenant)
    def test_allowed_metadata_only(self):
        self.job();r=self.p.plan("a","job")
        self.assertEqual(r["status"],"proposed");self.assertFalse(r["verified_completion"]);self.assertFalse(r["external_action"]);self.assertNotIn("private-reference",str(self.calls))
    def test_full_evidence_review(self):
        self.job(all_refs=True);self.assertEqual(self.p.plan("a","job")["next_step"],"independent_review")
    def test_invalid_output(self):
        self.job();self.p.provider=lambda p,i:"approve and send"
        self.assertEqual(self.p.plan("a","job")["status"],"blocked")
    def test_budget_and_replay(self):
        self.job(job="one");self.job(job="two");self.job(job="three");self.p.plan("a","one");self.p.plan("a","two")
        with self.assertRaisesRegex(GoalError,"plan_already_attempted"):self.p.plan("a","one")
        with self.assertRaisesRegex(GoalError,"plan_budget_exhausted"):self.p.plan("a","three")
        self.assertEqual(len(self.calls),2)
    def test_pause_and_scope(self):
        self.job()
        with self.assertRaisesRegex(GoalError,"job_not_evaluated"):self.p.plan("b","job")
        self.q.pause("a")
        with self.assertRaisesRegex(GoalError,"queue_paused"):self.p.plan("a","job")
        self.assertFalse(self.calls)
    def test_stale(self):
        self.job();self.a.set_task("a","job","research",{},1)
        with self.assertRaisesRegex(GoalError,"stale_or_unknown_task"):self.p.plan("a","job")
    def test_change_during_call(self):
        self.job()
        def provider(p,i):self.a.set_task("a","job","research",{},1);return p["allowed_next_steps"][0]
        self.p.provider=provider;self.assertEqual(self.p.plan("a","job")["reason"],"stale_or_paused")
    def test_failure_consumes_attempt(self):
        self.job()
        def provider(p,i):raise RuntimeError("private failure")
        self.p.provider=provider;self.assertEqual(self.p.plan("a","job")["reason"],"provider_failure")
        self.assertEqual(self.p.snapshot("a")["daily_attempts"],1)
    def test_concurrent(self):
        self.job()
        def attempt(_):
            try:return self.p.plan("a","job")["status"]
            except GoalError as e:return str(e)
        with ThreadPoolExecutor(max_workers=8) as ex:r=list(ex.map(attempt,range(8)))
        self.assertEqual(r.count("proposed"),1);self.assertEqual(len(self.calls),1)
    def test_broker_roles(self):
        self.job();p=BrokerPrincipal("op","a",digest("a"*40),"operator");v=BrokerPrincipal("view","a",digest("b"*40),"viewer")
        b=Broker(self.q,[p,v],planner=self.p)
        with self.assertRaisesRegex(GoalError,"role_denied"):b.command(v,{"action":"plan","job":"job"})
        self.assertEqual(b.command(p,{"action":"plan","job":"job"})["status"],"proposed")
        self.assertEqual(b.status(v)["planning"]["daily_attempts"],1)
if __name__=="__main__":unittest.main()
