"""Local, bounded goal-agent control plane. No external tools or self-granted authority."""
from dataclasses import dataclass
from contextlib import closing
from types import MappingProxyType
import hashlib,hmac,json,sqlite3,time
from secure_service.service import canonical,valid_id,strict_json

@dataclass(frozen=True)
class GoalSpec:
    objective:str
    checks:tuple
    next_action:str

GOALS=MappingProxyType({
    "ceo":GoalSpec("Prioritize verified company milestones",("roadmap","dependency_review","owner_assignment"),"Review unresolved dependencies and assign a human-approved owner"),
    "research":GoalSpec("Produce reproducible research",("hypothesis","prior_art","dataset_rights","baseline","raw_results","limitations"),"Prepare or verify experiment protocol and evidence"),
    "engineering":GoalSpec("Deliver tested engineering changes",("source_revision","test_results","review","rollback"),"Prepare an isolated implementation or fix"),
    "model_eval":GoalSpec("Compare models under equivalent conditions",("model_revision","dataset_revision","baseline","raw_results","failure_analysis"),"Run a scoped benchmark with approved data and compute"),
    "security":GoalSpec("Identify and mitigate release risks",("threat_model","negative_tests","independent_review","incident_plan"),"Document risks and block release until reviewed"),
    "product":GoalSpec("Validate a usable business outcome",("customer_problem","acceptance_criteria","pilot_permission","measured_outcome"),"Obtain design-partner evidence and permission"),
    "growth":GoalSpec("Identify qualified distribution opportunities",("audience","fit_evidence","message_review","permission"),"Draft a targeted opportunity for human review"),
    "partnership":GoalSpec("Find relevant collaborators",("organization","fit_evidence","proposal_review","permission"),"Prepare a collaboration proposal for review"),
    "finance":GoalSpec("Track sustainable unit economics",("cost_evidence","usage_evidence","margin_analysis"),"Measure cost per verified outcome"),
    "quality":GoalSpec("Verify deliverables against acceptance criteria",("acceptance_criteria","independent_checks","evidence_links","limitations"),"Request missing evidence and independent checks"),
    "finance_ops":GoalSpec("Resolve invoice exceptions with human approval",("invoice","purchase_order","reviewer_decision"),"Route missing evidence or review request"),
    "hr_ops":GoalSpec("Coordinate onboarding with human approval",("employee_ref","manager_confirmation","reviewer_decision"),"Route missing evidence or review request"),
    "it_ops":GoalSpec("Coordinate scoped access requests",("resource","owner_confirmation","reviewer_decision"),"Route missing evidence or review request"),
    "support_ops":GoalSpec("Coordinate support resolution",("ticket","resolution_evidence","reviewer_decision"),"Route missing evidence or review request"),
})

class GoalError(Exception):pass

def require(ok,reason):
    if not ok:raise GoalError(reason)

class GoalAgents:
    """Trusted local host owns this object, keys and evidence. Agents never get keys.
    Only evaluates evidence references; no external network, arbitrary code, approval,
    scheduling or model inference. Not a production authentication boundary.
    """
    def __init__(self,path,secret,clock=time.time):
        require(type(secret) is bytes and len(secret)>=32,"invalid_key")
        self.path=str(path);self._key=secret;self.clock=clock
        with closing(self.connect()) as db:db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS goal_tasks(tenant TEXT, id TEXT, category TEXT, revision INTEGER, evidence TEXT, PRIMARY KEY(tenant,id));
        CREATE TABLE IF NOT EXISTS goal_runs(tenant TEXT, nonce TEXT, task TEXT, result TEXT, PRIMARY KEY(tenant,nonce));
        """)
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5,isolation_level=None)
        db.row_factory=sqlite3.Row;return db
    def set_task(self,tenant,task,category,evidence,expected_revision):
        """Trusted host only: records evidence references, not verified claims."""
        require(valid_id(tenant) and valid_id(task) and type(category) is str and category in GOALS,"invalid_task")
        require(type(expected_revision) is int and 0<=expected_revision<1000000,"invalid_revision")
        require(type(evidence) is dict and set(evidence)<=set(GOALS[category].checks) and all(valid_id(v) for v in evidence.values()),"invalid_evidence")
        with closing(self.connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row=db.execute("SELECT * FROM goal_tasks WHERE tenant=? AND id=?",(tenant,task)).fetchone()
                require((row is None and expected_revision==0) or (row is not None and row["revision"]==expected_revision and row["category"]==category),"revision_conflict")
                rev=expected_revision+1
                db.execute("INSERT INTO goal_tasks VALUES(?,?,?,?,?) ON CONFLICT(tenant,id) DO UPDATE SET revision=excluded.revision,evidence=excluded.evidence",(tenant,task,category,rev,canonical(evidence)))
                db.commit();return rev
            except BaseException:db.rollback();raise
    def _mac(self,body):
        return hmac.new(self._key,canonical(body).encode(),hashlib.sha256).hexdigest()
    def grant(self,tenant,task,category,revision,nonce,*,ttl=60):
        """Host-only explicit purpose grant, binds task, category, revision and expiry."""
        require(all(valid_id(x) for x in (tenant,task,nonce)) and type(category) is str and category in GOALS,"invalid_grant")
        require(type(revision) is int and revision>0 and type(ttl) is int and 1<=ttl<=300,"invalid_grant")
        body={"tenant":tenant,"task":task,"category":category,"revision":revision,"nonce":nonce,"purpose":"evaluate_goal","expires":int(self.clock())+ttl}
        return canonical({"body":body,"mac":self._mac(body)})
    def run(self,grant,*,tenant,category):
        require(type(grant) is str and len(grant)<=2048,"invalid_grant")
        try:
            env=strict_json(grant);body=env["body"];mac=env["mac"]
            require(type(env) is dict and set(env)=={"body","mac"} and type(body) is dict and set(body)=={"tenant","task","category","revision","nonce","purpose","expires"} and type(mac) is str,"invalid_grant")
            require(hmac.compare_digest(mac,self._mac(body)),"invalid_signature")
        except (KeyError,TypeError,ValueError,RecursionError):raise GoalError("invalid_grant")
        require(body["tenant"]==tenant and body["category"]==category and body["purpose"]=="evaluate_goal" and category in GOALS,"scope_denied")
        require(int(self.clock())<body["expires"],"expired_grant")
        with closing(self.connect()) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                require(int(self.clock())<body["expires"],"expired_grant")
                row=db.execute("SELECT * FROM goal_tasks WHERE tenant=? AND id=?",(tenant,body["task"])).fetchone()
                require(row is not None and row["category"]==category and row["revision"]==body["revision"],"stale_or_unknown_task")
                require(not db.execute("SELECT 1 FROM goal_runs WHERE tenant=? AND nonce=?",(tenant,body["nonce"])).fetchone(),"replay")
                evidence=strict_json(row["evidence"]);spec=GOALS[category]
                missing=[k for k in spec.checks if k not in evidence]
                result={"task":body["task"],"category":category,"objective":spec.objective,"revision":row["revision"],"present_refs":len(evidence),"required_refs":len(spec.checks),"missing":missing,"status":"needs_evidence" if missing else "ready_for_independent_review","next_action":spec.next_action if missing else "Independently verify supplied evidence and record a human decision","verified_completion":False,"external_action":False}
                db.execute("INSERT INTO goal_runs VALUES(?,?,?,?)",(tenant,body["nonce"],body["task"],canonical(result)))
                db.commit();return result
            except BaseException:db.rollback();raise
