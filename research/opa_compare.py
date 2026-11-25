"""Equivalent policy decision comparison; not a benchmark of OPA tool execution."""
import itertools, json, subprocess, sys
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gateway import Gateway
cases=[]; results=[]
for action, tenant_ok, shape_ok, evidence_ok, approval_mode, budget_ok in itertools.product(['lookup_invoice','prepare_report','send_email'],[True,False],[True,False],[True,False],['bound','missing','wrong'],[True,False]):
    g=Gateway(budget=Decimal('.10' if budget_ok else '0'))
    args={'tenant':'demo' if tenant_ok else 'other', ('invoice_id' if action=='lookup_invoice' else 'report_id'):'INV-1' if action=='lookup_invoice' else 'R-1'}
    if not shape_ok: args['extra']='untrusted'
    if evidence_ok: g.register_evidence('A'); g.register_evidence('B')
    token=g.approve(action,args if approval_mode=='bound' else {**args,'tenant':'different'}) if approval_mode!='missing' else None
    expected=action in ['lookup_invoice','prepare_report'] and tenant_ok and shape_ok and budget_ok and (action=='lookup_invoice' or (evidence_ok and approval_mode=='bound'))
    actual=g.dispatch(action,args,token)['status']=='executed_mock'
    cases.append({'action':action,'tenant':args['tenant'],'exact_shape':shape_ok,'within_budget':budget_ok,'evidence_count':2 if evidence_ok else 0,'approval_matches':approval_mode=='bound'})
    results.append({'expected':expected,'gateway':actual})
out=subprocess.run(['opa','eval','--stdin-input','--format','json','--data',str(ROOT/'research/opa/policy.rego'),'data.gateway_benchmark.decisions'],input=json.dumps(cases),text=True,capture_output=True,check=True)
decisions=json.loads(out.stdout)['result'][0]['expressions'][0]['value']
assert len(decisions)==len(results)
for r,d in zip(results,decisions): r['opa']=d
summary={'cases':len(results),'valid':sum(r['expected'] for r in results),'invalid':sum(not r['expected'] for r in results),'gateway_matches':sum(r['gateway']==r['expected'] for r in results),'opa_matches':sum(r['opa']==r['expected'] for r in results),'disagreements':sum(r['gateway']!=r['opa'] for r in results),'scope':'same synthetic fixture family, OPA receives trusted host facts; policy decision only, not equivalent end-to-end systems'}
print(json.dumps(summary,indent=2))
(ROOT/'research/opa-results.json').write_text(json.dumps({'summary':summary,'cases':[{**c,**r} for c,r in zip(cases,results)]},indent=2)+'\n')
assert summary['gateway_matches']==summary['opa_matches']==144 and summary['disagreements']==0
