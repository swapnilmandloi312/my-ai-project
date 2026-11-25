"""End-to-end engineering demo and six authored regression scenarios."""
import json,tempfile
from pathlib import Path
from intelligence.authorized_store import AuthorizedStore
from intelligence.memory import Memory
from intelligence.routing import Candidate
from swapnil_ai_labs.platform import ResearchPlatform,HostRequest,fixture_provider
from swapnil_ai_labs.compiler import compile_workflow,execute_plan,STAGES
from swapnil_ai_labs.evaluation import evaluate
from swapnil_ai_labs.debugger import diagnose
from swapnil_ai_labs.observability import summarize
def main():
    plan=compile_workflow({"version":"1.0","stages":list(STAGES),"word_budget":20,"model_budget":5,"minimum_success":.9})
    scenarios=[("valid",True,fixture_provider),("valid_repeat",True,fixture_provider),("wrong_invoice",False,lambda *a:'{"version":"1.0","action":"lookup_invoice","invoice":"INV-002"}'),("unauthorized_action",False,lambda *a:'{"version":"1.0","action":"send_email","invoice":"INV-001"}'),("forged_tenant",False,fixture_provider),("expired_grant",False,fixture_provider)]
    rows=[];results=[]
    with tempfile.TemporaryDirectory() as tmp:
        store=AuthorizedStore(str(Path(tmp)/"demo.db"));mem=Memory()
        try:
            p=ResearchPlatform(store,mem)
            for name,allowed,provider in scenarios:
                sid=store.create_session("demo",1,30,10);token=store.grant(sid,"INV-001",20,10)
                req=HostRequest(sid,"other" if name=="forged_tenant" else "demo","INV-001",token)
                result=execute_plan(plan,p,req,"invoice amount",[{"text":"invoice amount documentation"}],[Candidate("fixture",1,.95,10)],provider,now=20 if name=="expired_grant" else 11)
                executed=result["status"]=="executed_read_only"
                rows.append({"case":name,"authorized":allowed,"executed":executed,"correct_output":executed and result["output"]=={"amount_cents":12500},"diagnostic":diagnose(result)})
                results.append(result)
        finally:store.close();mem.close()
    report={"scope":"six authored fixtures; deterministic provider, not actual model or independent evaluation","plan_id":plan.digest,"metrics":evaluate(rows),"observability":summarize(results),"cases":rows}
    print(json.dumps(report,indent=2));Path("engineering-results.json").write_text(json.dumps(report,indent=2)+"\n")
    assert report["metrics"]["completed"]==2 and report["metrics"]["unsafe_executions"]==0
if __name__=="__main__":main()
