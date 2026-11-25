"""Run all 14 bounded goal agents on synthetic evidence."""
import json,tempfile,secrets
from pathlib import Path
from swapnil_ai_labs.goal_agents import GoalAgents,GOALS
def run():
    results=[]
    with tempfile.TemporaryDirectory() as d:
        a=GoalAgents(Path(d)/"goals.db",secrets.token_bytes(32))
        for category,spec in GOALS.items():
            revision=a.set_task("demo","task-"+category,category,{spec.checks[0]:"synthetic-reference"},0)
            grant=a.grant("demo","task-"+category,category,revision,"nonce-"+category)
            result=a.run(grant,tenant="demo",category=category)
            assert result["status"]=="needs_evidence" and not result["external_action"]
            results.append(result)
    return {"scope":"synthetic local goal evaluation only; no external tool calls or AI inference","agents":results}
if __name__=="__main__":print(json.dumps(run(),indent=2))
