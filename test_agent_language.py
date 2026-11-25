import unittest
from pathlib import Path
from agent_language import parse,simulate,ContractError
class Tests(unittest.TestCase):
    def setUp(self): self.c=parse(Path('research.agent').read_text())
    def run_action(self, action, cost='0.01', **kw): return simulate(self.c,[{'action':action,'cost_usd':cost}],**kw)
    def test_allowed(self): self.assertEqual(self.run_action('search_public',verified_sources=['a','b'])['status'],'passed_simulation')
    def test_denied(self): self.assertEqual(self.run_action('send_email')['trace'][0]['reason'],'permission denied')
    def test_default_deny(self): self.assertEqual(self.run_action('unknown')['trace'][0]['reason'],'permission denied')
    def test_budget(self): self.assertEqual(self.run_action('search_public','0.11')['trace'][0]['reason'],'budget exceeded')
    def test_approval(self): self.assertEqual(self.run_action('publish_report')['trace'][0]['reason'],'approval required')
    def test_sources(self): self.assertEqual(self.run_action('search_public',verified_sources=['a','a'])['status'],'blocked')
    def test_publish_without_evidence(self): self.assertEqual(self.run_action('publish_report',approvals=['publish_report'])['trace'][0]['reason'],'insufficient verified source fixtures')
    def test_steps(self): self.assertEqual(simulate(self.c,[{'action':'search_public','cost_usd':'0'}]*6)['trace'][-1]['reason'],'step limit')
    def test_invalid(self):
        with self.assertRaises(ContractError): parse('agent x')
    def test_negative(self):
        with self.assertRaises(ContractError): self.run_action('search_public','-1')
    def test_conflict(self):
        with self.assertRaises(ContractError): parse(Path('research.agent').read_text()+'\nallow send_email')
if __name__=='__main__': unittest.main()
