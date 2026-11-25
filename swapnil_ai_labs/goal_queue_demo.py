"""Exercise all 14 categories with durable local jobs and a restart."""
import json,tempfile,secrets
from pathlib import Path
from swapnil_ai_labs.goal_agents import GoalAgents,GOALS
from swapnil_ai_labs.goal_queue import GoalQueue
def run():
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/"jobs.db";key=secrets.token_bytes(32)
        agents=GoalAgents(path,key);queue=GoalQueue(agents)
        for cat,spec in GOALS.items():
            task="task-"+cat;rev=agents.set_task("demo",task,cat,{spec.checks[0]:"synthetic-ref"},0)
            queue.enqueue("demo","job-"+cat,task,cat,rev)
        queue.pause("demo");assert queue.tick("demo")==[]
        queue.pause("demo",False)
        first=queue.tick("demo",limit=7);assert len(first)==7
        queue=GoalQueue(GoalAgents(path,key));second=queue.tick("demo",limit=14);assert len(second)==7
        state=queue.snapshot("demo")
        assert all(j["status"]=="evaluated" and j["result"]["verified_completion"] is False and j["result"]["external_action"] is False for j in state["jobs"])
        assert queue.tick("demo")==[]
        return {"scope":"synthetic deterministic evaluations only, not autonomous AI agents", "evaluated":len(first)+len(second),"restart_verified":True,"pause_verified":True,"state":state}
if __name__=="__main__":print(json.dumps(run(),indent=2))
