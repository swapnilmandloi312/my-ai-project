"""Read-only synthetic finance pilot. Host must own the gateway and database."""
import json, sqlite3
from pathlib import Path
from gateway import Gateway

class InvoicePilot:
    def __init__(self):
        self.gateway=Gateway.from_contract((Path(__file__).resolve().parents[1]/'product.agent').read_text())
        self.db=sqlite3.connect(':memory:')
        self.db.execute('CREATE TABLE invoices(tenant TEXT, id TEXT, amount_cents INTEGER, PRIMARY KEY(tenant,id))')
        self.db.executemany('INSERT INTO invoices VALUES(?,?,?)',[('demo','INV-001',12500),('other','INV-001',99999)])
        self.db.commit()
        self.db.execute('PRAGMA query_only=ON')
        self.queries=0
    def propose(self, message):
        # Model output is untrusted. No approval/evidence registration accepted here.
        try:
            if type(message) is not str or len(message)>4096: raise ValueError()
            obj=json.loads(message)
            if type(obj) is not dict or set(obj)!={'action','args'}: raise ValueError()
        except (ValueError,TypeError,RecursionError):
            return {'status':'blocked','reason':'invalid proposal'}
        if obj['action']!='lookup_invoice': return {'status':'blocked','reason':'read-only pilot'}
        decision=self.gateway.dispatch(obj['action'],obj['args'])
        if decision['status']!='executed_mock': return decision
        self.queries+=1
        row=self.db.execute('SELECT amount_cents FROM invoices WHERE tenant=? AND id=?',(self.gateway.tenant,obj['args']['invoice_id'])).fetchone()
        return {**decision,'status':'executed_read_only','output':{'amount_cents':row[0]} if row else None}
    def close(self): self.db.close()

if __name__=='__main__':
    pilot=InvoicePilot()
    try:
        print(json.dumps(pilot.propose('{"action":"lookup_invoice","args":{"tenant":"demo","invoice_id":"INV-001"}}'),indent=2))
    finally: pilot.close()
