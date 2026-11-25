"""Internal reviewer-only bridge to the host-bound read runtime. Never grants approval."""
from contextlib import closing
from dataclasses import dataclass
from secure_service.service import valid_id
from swapnil_ai_labs.trusted_runtime import HostTask
from swapnil_ai_labs.work_relay import RelayError,require

EVIDENCE_CATEGORY={"finance":"finance","hr":"knowledge","it":"operations","support":"support"}

class RelayEvidence:
    def __init__(self,relay,runtime):
        self.relay=relay;self.runtime=runtime
    def inspect(self,relay_auth,read_auth,*,item_id,evidence_key,revision,request_id):
        p=self.relay.auth(relay_auth)
        require(p is not None,401,"authentication_required")
        require(p.role=="reviewer",403,"role_denied")
        q=self.runtime.service.authenticate(read_auth)
        require(q is not None and q.tenant==p.tenant and q.id==p.id,403,"principal_mismatch")
        require(valid_id(item_id) and valid_id(request_id) and type(revision) is int and type(evidence_key) is str,400,"invalid_request")
        import json
        def snapshot():
            with closing(self.relay.connect()) as db:
                row=self.relay._lookup(db,p,item_id)
                require(row["revision"]==revision,409,"revision_conflict")
                require(row["state"]=="awaiting_review",409,"invalid_state")
                ev=json.loads(row["evidence"])
                require(evidence_key in ev,404,"evidence_not_found")
                return row["department"],ev[evidence_key]
        dep,record=snapshot()
        decision=self.runtime.run(read_auth,HostTask(request_id,EVIDENCE_CATEGORY[dep],record,"Read the selected evidence record."))
        try:require(snapshot()==(dep,record),409,"evidence_changed")
        except RelayError:return {"status":"blocked","reason":"stale_review","evidence_key":evidence_key,"trace":decision["trace"],"approval_granted":False}
        # Do not expose the record payload or change workflow state. Existence and
        # authorized retrieval do not verify the truth or completeness of a document.
        return {"status":"retrieved" if decision["status"]=="executed_read_only" else "blocked","reason":decision["reason"],"evidence_key":evidence_key,"trace":decision["trace"],"approval_granted":False}
