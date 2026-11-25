"""Swapnil AI Labs Agent Language: experimental contract parser and simulated action validator."""
import argparse, json, re, sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

class ContractError(ValueError): pass

def number(s):
    try: d = Decimal(str(s))
    except InvalidOperation: raise ContractError('invalid number') from None
    if not d.is_finite() or d < 0: raise ContractError('number must be finite and nonnegative')
    return d

def parse(source):
    c = {'allow':set(), 'deny':set(), 'approval':set(), 'verified_sources':0}
    seen=set()
    for lineno, raw in enumerate(source.splitlines(),1):
        line=raw.split('#',1)[0].strip()
        if not line: continue
        p=line.split(); key=p[0]
        try:
            if key in {'agent','model','budget_usd','max_steps','on_failure'} and len(p)==2:
                if key in seen: raise ContractError('duplicate '+key)
                seen.add(key)
                if key=='budget_usd': c[key]=number(p[1])
                elif key=='max_steps':
                    if not p[1].isdigit() or int(p[1])<1: raise ContractError('positive integer required')
                    c[key]=int(p[1])
                elif key=='on_failure':
                    if p[1]!='stop': raise ContractError('only stop supported')
                    c[key]=p[1]
                else: c[key]=p[1]
            elif key in {'allow','deny'} and len(p)==2: c[key].add(p[1])
            elif p[:2]==['require','approval'] and len(p)==3: c['approval'].add(p[2])
            elif p[:2]==['require','verified_sources'] and len(p)==3 and p[2].isdigit():
                if 'verified_sources' in seen: raise ContractError('duplicate verified_sources')
                seen.add('verified_sources'); c['verified_sources']=int(p[2])
            else: raise ContractError('unknown or malformed statement')
        except ContractError as e: raise ContractError(f'line {lineno}: {e}') from None
    missing={'agent','model','budget_usd','max_steps','on_failure'}-seen
    if missing: raise ContractError('missing '+', '.join(sorted(missing)))
    if c['allow'] & c['deny']: raise ContractError('conflicting permissions')
    if not c['approval'] <= c['allow']: raise ContractError('approval action must also be allowed')
    return c

def simulate(c, events, approvals=(), verified_sources=()):
    """Validate trusted test fixtures only. Does not execute tools or verify source claims."""
    total=Decimal(0); trace=[]; sources=set(verified_sources); approvals=set(approvals)
    for i,event in enumerate(events,1):
        action=event['action']; cost=number(event['cost_usd']); reason=None
        if i>c['max_steps']: reason='step limit'
        elif action in c['deny'] or action not in c['allow']: reason='permission denied'
        elif total+cost>c['budget_usd']: reason='budget exceeded'
        elif action in c['approval'] and action not in approvals: reason='approval required'
        elif action == 'publish_report' and len(sources)<c['verified_sources']: reason='insufficient verified source fixtures'
        if reason:
            trace.append({'action':action,'status':'blocked','reason':reason}); return {'status':'blocked','spent_usd':str(total),'trace':trace}
        total+=cost; trace.append({'action':action,'status':'simulated','cost_usd':str(cost)})
    if len(sources)<c['verified_sources']:
        return {'status':'blocked','reason':'insufficient verified source fixtures','spent_usd':str(total),'trace':trace}
    return {'status':'passed_simulation','spent_usd':str(total),'trace':trace}

def main():
    p=argparse.ArgumentParser(); p.add_argument('contract'); p.add_argument('fixture'); args=p.parse_args()
    try:
        c=parse(Path(args.contract).read_text()); f=json.loads(Path(args.fixture).read_text()); result=simulate(c,f['events'],f.get('approvals',[]),f.get('verified_sources',[])); print(json.dumps(result,indent=2)); return 0 if result['status']=='passed_simulation' else 1
    except (ValueError, KeyError, TypeError, OSError) as e: print(str(e),file=sys.stderr); return 2
if __name__=='__main__': sys.exit(main())
