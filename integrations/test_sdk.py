import json, subprocess, threading, unittest, urllib.request
from pathlib import Path
from integrations.http_pilot import serve
ROOT=Path(__file__).resolve().parents[1]
class SDKTests(unittest.TestCase):
    def test_http_and_node(self):
        with serve(0) as server:
            t=threading.Thread(target=server.serve_forever);t.start()
            try:
                url=f'http://127.0.0.1:{server.server_port}/propose'
                req=urllib.request.Request(url,b'{"action":"lookup_invoice","args":{"tenant":"demo","invoice_id":"INV-001"}}',{'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=5) as r: self.assertEqual(json.load(r)['output'],{'amount_cents':12500})
                code=f"import {{lookupInvoice}} from './integrations/javascript.mjs'; const p={server.server_port}; console.log(JSON.stringify([await lookupInvoice('INV-001',{{port:p}}),await lookupInvoice('INV-001',{{port:p,tenant:'other'}})]));"
                result=json.loads(subprocess.check_output(['node','--input-type=module','-e',code],cwd=ROOT,text=True))
                self.assertEqual(result[0]['status'],'executed_read_only');self.assertEqual(result[1]['status'],'blocked')
            finally: server.shutdown();t.join()
    def test_workflow_structure(self):
        f=json.loads((ROOT/'integrations/n8n-workflow.json').read_text())
        self.assertFalse(f['active'])
        self.assertEqual(f['connections']['Manual Trigger']['main'][0][0]['node'],'Validate and read invoice')
        http=next(n for n in f['nodes'] if n['type']=='n8n-nodes-base.httpRequest')
        self.assertEqual(json.loads(http['parameters']['jsonBody'])['args']['tenant'],'demo')
if __name__=='__main__':unittest.main()
