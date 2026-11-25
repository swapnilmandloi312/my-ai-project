"""Integrated offline reference workflow. No network services or customer data."""
import json, time, uuid
from dataclasses import dataclass
from intelligence.context import select
from intelligence.memory import Memory
from intelligence.routing import route
from intelligence.authorized_store import AuthorizedStore
from swapnil_ai_labs.contracts import decode

@dataclass(frozen=True)
class HostRequest:
    session_id:str
    tenant:str
    invoice:str
    grant:str

class ResearchPlatform:
    def __init__(self,store:AuthorizedStore,memory:Memory):
        self.store=store;self.memory=memory
    def run(self,request,query,records,candidates,provider,*,word_budget=80,model_budget=5,minimum_success=.9,now=None):
        # records and request are trusted host inputs, not data selected by a model.
        trace_id=uuid.uuid4().hex; start=time.perf_counter()
        selected=select(query,records,word_budget)
        choice=route(candidates,model_budget,minimum_success)
        def finish(status,reason,output=None):
            # Do not log raw prompts, documents, tokens, grants or tenant identifiers.
            return {"status":status,"reason":reason,"output":output,"trace":{"id":trace_id,"selected_count":len(selected),"selected_words":sum(len(r["text"].split()) for r in selected),"model":choice.name if choice else None,"elapsed_ms":round((time.perf_counter()-start)*1000,3)}}
        if not choice:return finish("blocked","no eligible model")
        if not isinstance(request,HostRequest):return finish("blocked","missing trusted request")
        stored=self.store.db.execute("SELECT tenant FROM sessions WHERE id=?",(request.session_id,)).fetchone()
        if not stored or stored[0]!=request.tenant:return finish("blocked","host tenant mismatch")
        preference=self.memory.get(request.tenant,"display_format",now)
        try:
            raw=provider(choice.name,query,tuple(r["text"] for r in selected),preference)
            proposal=decode(raw)
        except Exception:
            return finish("blocked","provider or proposal failure")
        if proposal.invoice!=request.invoice:return finish("blocked","proposal does not match host request")
        decision=self.store.read(request.session_id,request.grant,proposal.payload(),now)
        return finish("executed_read_only" if decision["allowed"] else "blocked",decision["reason"],decision["output"])

def fixture_provider(model,query,context,preference):
    # Deterministic example, explicitly not a model.
    return json.dumps({"version":"1.0","action":"lookup_invoice","invoice":"INV-001"})
