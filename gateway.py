"""Single-process reference gateway. Mock tools only. Not a security boundary."""
import hashlib, json, secrets, threading
from decimal import Decimal
from dataclasses import dataclass, field

@dataclass
class Gateway:
    tenant: str = 'demo'
    budget: Decimal = Decimal('0.10')
    max_steps: int = 5
    spent: Decimal = field(default_factory=lambda: Decimal('0'))
    steps: int = 0
    approvals: dict = field(default_factory=dict)
    audit: list = field(default_factory=list)
    evidence: set = field(default_factory=set)
    allowed: frozenset = field(default_factory=lambda: frozenset({'lookup_invoice','prepare_report'}))
    required_evidence: int = 2
    halted: bool = False
    lock: object = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def from_contract(cls, source, tenant='demo'):
        from agent_language import parse, ContractError
        c=parse(source)
        supported={'lookup_invoice','prepare_report'}
        if not c['allow'] <= supported or c['approval'] != (c['allow'] & {'prepare_report'}):
            raise ContractError('gateway supports lookup_invoice and approved prepare_report only')
        return cls(tenant=tenant,budget=c['budget_usd'],max_steps=c['max_steps'],allowed=frozenset(c['allow']),required_evidence=max(2,c['verified_sources']))

    def _digest(self, action, args):
        return hashlib.sha256(json.dumps([self.tenant,action,args],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    def approve(self, action, args):
        # Trusted host only; never expose to agent or untrusted client.
        with self.lock:
            token=secrets.token_hex(16); self.approvals[token]=self._digest(action,args); return token
    def register_evidence(self, evidence_id):
        # Host registers IDs, does not establish source truth.
        if type(evidence_id) is not str or not evidence_id: raise ValueError('invalid evidence')
        with self.lock: self.evidence.add(evidence_id)
    def dispatch(self, action, args, approval=None):
        with self.lock:
            def finish(status,reason,output=None):
                result={'status':status,'reason':reason,'output':output,'spent':str(self.spent),'steps':self.steps}
                self.audit.append({'action':action if type(action) is str else '<invalid>', 'status':status,'reason':reason,'spent':str(self.spent)})
                if status=='blocked': self.halted=True
                return result
            if self.halted: return finish('blocked','session halted')
            if type(action) is not str or type(args) is not dict: return finish('blocked','invalid request')
            if self.steps>=self.max_steps: return finish('blocked','step limit')
            if action not in self.allowed: return finish('blocked','permission denied')
            if action=='lookup_invoice':
                if set(args)!={'tenant','invoice_id'} or type(args['invoice_id']) is not str or not args['invoice_id'].startswith('INV-') or len(args['invoice_id'])>32 or args['tenant']!=self.tenant: return finish('blocked','argument policy')
                cost=Decimal('.01')
            elif action=='prepare_report':
                if set(args)!={'tenant','report_id'} or type(args['report_id']) is not str or not args['report_id'] or len(args['report_id'])>64 or args['tenant']!=self.tenant: return finish('blocked','argument policy')
                if len(self.evidence)<self.required_evidence: return finish('blocked','evidence count')
                if type(approval) is not str or self.approvals.get(approval)!=self._digest(action,args): return finish('blocked','approval required or mismatch')
                cost=Decimal('.03')
            else: return finish('blocked','permission denied')
            if self.spent+cost>self.budget: return finish('blocked','budget exceeded')
            self.steps+=1; self.spent+=cost
            if action=='prepare_report': del self.approvals[approval]
            # Only predefined, inert mock handlers; no real invoices, files, external calls.
            return finish('executed_mock','ok',{'fixture':True,'action':action,'id':args.get('invoice_id',args.get('report_id'))})
