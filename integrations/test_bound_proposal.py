import json,unittest
from integrations.bound_proposal import execute,normalize
class BoundTests(unittest.TestCase):
    def setUp(self): self.auth={'action':'lookup_invoice','args':{'tenant':'demo','invoice_id':'INV-001'}}
    def test_fenced(self): self.assertEqual(execute('```json\n'+json.dumps(self.auth)+'\n```',self.auth)['status'],'executed_read_only')
    def test_no_grant(self): self.assertEqual(execute(json.dumps(self.auth),None)['status'],'blocked')
    def test_argument_mismatch(self): self.assertEqual(execute(json.dumps({'action':'lookup_invoice','args':{'tenant':'demo','invoice_id':'INV-002'}}),self.auth)['status'],'blocked')
    def test_duplicate(self):
        with self.assertRaises(ValueError): normalize('{"action":"refuse","action":"lookup_invoice","args":{}}')
    def test_extra_text(self):
        with self.assertRaises(ValueError): normalize('explanation '+json.dumps(self.auth))
    def test_nan(self):
        with self.assertRaises(ValueError): normalize('{"action":"lookup_invoice","args":{"x":NaN}}')
