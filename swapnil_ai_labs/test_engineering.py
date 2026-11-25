import unittest
from dataclasses import replace
from swapnil_ai_labs.compiler import compile_workflow,execute_plan,STAGES
from swapnil_ai_labs.evaluation import evaluate
from swapnil_ai_labs.debugger import diagnose
from swapnil_ai_labs.observability import summarize
class Engineering(unittest.TestCase):
    def setUp(self):self.s={"version":"1.0","stages":list(STAGES),"word_budget":20,"model_budget":5,"minimum_success":.9}
    def test_determinism(self):self.assertEqual(compile_workflow(self.s),compile_workflow(dict(reversed(list(self.s.items())))))
    def test_missing_auth(self):
        with self.assertRaises(ValueError):compile_workflow({**self.s,"stages":[x for x in STAGES if x!="authorize"]})
    def test_reorder(self):
        with self.assertRaises(ValueError):compile_workflow({**self.s,"stages":list(reversed(STAGES))})
    def test_version(self):
        with self.assertRaises(ValueError):compile_workflow({**self.s,"version":"2.0"})
    def test_limits(self):
        with self.assertRaises(ValueError):compile_workflow({**self.s,"minimum_success":float("nan")})
    def test_tamper(self):
        with self.assertRaises(ValueError):execute_plan(replace(compile_workflow(self.s),model_budget=99),None,None,None,None,None,None)
    def test_metrics(self):
        r=evaluate([{"authorized":True,"executed":True,"correct_output":True},{"authorized":False,"executed":False,"correct_output":False}]);self.assertEqual((r["task_completion_rate"],r["unsafe_execution_rate"]),(1,0))
    def test_all_blocked_not_success(self):
        r=evaluate([{"authorized":True,"executed":False,"correct_output":False}]);self.assertEqual(r["task_completion_rate"],0);self.assertIsNone(r["unsafe_execution_rate"])
    def test_unsafe(self):
        r=evaluate([{"authorized":False,"executed":True,"correct_output":False}]);self.assertEqual(r["unsafe_execution_rate"],1)
    def test_debugger(self):self.assertEqual(diagnose({"status":"blocked","reason":"host tenant mismatch"})["category"],"authorization")
    def test_unknown(self):self.assertEqual(diagnose({"status":"blocked","reason":"private text"})["category"],"unknown")
    def test_observability(self):
        r=summarize([{"status":"blocked","trace":{"elapsed_ms":10,"selected_words":4,"secret":"nope"}}]);self.assertEqual(r["p95_ms"],10);self.assertNotIn("nope",str(r))
