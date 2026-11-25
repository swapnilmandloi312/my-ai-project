import unittest
from decimal import Decimal
from gateway import Gateway
class GatewayTests(unittest.TestCase):
    def setUp(self):self.g=Gateway(); self.a={'tenant':'demo','report_id':'R-1'}; self.g.register_evidence('a');self.g.register_evidence('b')
    def test_compiled_contract(self):
        from pathlib import Path
        c=Path('product.agent').read_text().replace('allow lookup_invoice\n','')
        g=Gateway.from_contract(c);self.assertEqual(g.dispatch('lookup_invoice',{'tenant':'demo','invoice_id':'INV-1'})['status'],'blocked')
    def test_valid(self):self.assertEqual(self.g.dispatch('lookup_invoice',{'tenant':'demo','invoice_id':'INV-1'})['status'],'executed_mock')
    def test_wrong_tenant(self):self.assertEqual(self.g.dispatch('lookup_invoice',{'tenant':'other','invoice_id':'INV-1'})['status'],'blocked')
    def test_unknown(self):self.assertEqual(self.g.dispatch('send_email',{})['status'],'blocked')
    def test_extra(self):self.assertEqual(self.g.dispatch('lookup_invoice',{'tenant':'demo','invoice_id':'INV-1','extra':1})['status'],'blocked')
    def test_approval(self):self.assertEqual(self.g.dispatch('prepare_report',self.a,self.g.approve('prepare_report',self.a))['status'],'executed_mock')
    def test_changed_argument(self):self.assertEqual(self.g.dispatch('prepare_report',{**self.a,'report_id':'R-2'},self.g.approve('prepare_report',self.a))['status'],'blocked')
    def test_replay(self):
        t=self.g.approve('prepare_report',self.a); self.g.dispatch('prepare_report',self.a,t);self.assertEqual(self.g.dispatch('prepare_report',self.a,t)['status'],'blocked')
    def test_evidence_dedup(self):
        g=Gateway();g.register_evidence('a');g.register_evidence('a');self.assertEqual(g.dispatch('prepare_report',self.a,g.approve('prepare_report',self.a))['status'],'blocked')
    def test_budget(self):
        g=Gateway(budget=Decimal('.009'));self.assertEqual(g.dispatch('lookup_invoice',{'tenant':'demo','invoice_id':'INV-1'})['status'],'blocked')
    def test_steps(self):
        g=Gateway(max_steps=1);a={'tenant':'demo','invoice_id':'INV-1'};g.dispatch('lookup_invoice',a);self.assertEqual(g.dispatch('lookup_invoice',a)['status'],'blocked')
    def test_halt(self):
        self.g.dispatch('send_email',{});self.assertEqual(self.g.dispatch('lookup_invoice',{'tenant':'demo','invoice_id':'INV-1'})['reason'],'session halted')
    def test_bad_type(self):self.assertEqual(self.g.dispatch([],[])['status'],'blocked')
if __name__=='__main__':unittest.main()
