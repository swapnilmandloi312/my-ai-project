"""Loopback local broker demo; synthetic data and temporary credentials only."""
import json,secrets,tempfile,threading,urllib.request
from pathlib import Path
from wsgiref.simple_server import make_server,WSGIRequestHandler
from secure_service.service import digest
from swapnil_ai_labs.goal_agents import GoalAgents,GOALS
from swapnil_ai_labs.goal_queue import GoalQueue
from swapnil_ai_labs.goal_broker import Broker,BrokerPrincipal,make_app
class Quiet(WSGIRequestHandler):
    def log_message(self,*args):pass
def run():
    with tempfile.TemporaryDirectory() as d:
        key=secrets.token_bytes(32);token=secrets.token_urlsafe(32);path=Path(d)/"jobs.db"
        p=BrokerPrincipal("founder","demo",digest(token),"operator")
        b=Broker(GoalQueue(GoalAgents(path,key)),[p]);s=make_server("127.0.0.1",0,make_app(b),handler_class=Quiet);t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
        def call(route,body=None):
            req=urllib.request.Request("http://127.0.0.1:"+str(s.server_port)+route,data=json.dumps(body).encode() if body is not None else None,headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=10) as r:return json.load(r)
        def cmd(x):return call("/v1/goals/commands",x)
        try:
            for cat,spec in GOALS.items():
                task="task-"+cat;rev=cmd({"action":"set_task","task":task,"category":cat,"revision":0,"evidence":{spec.checks[0]:"synthetic-ref"}})["revision"]
                cmd({"action":"enqueue","job":"job-"+cat,"task":task,"category":cat,"revision":rev})
            cmd({"action":"pause"});assert cmd({"action":"tick","limit":14})["evaluated"]==0
            cmd({"action":"resume"});assert cmd({"action":"tick","limit":14})["evaluated"]==14
            result=call("/v1/goals/status")
            assert result["counts"]=={"evaluated":14}
            assert all(not j["result"]["verified_completion"] and not j["result"]["external_action"] for j in result["jobs"])
        finally:s.shutdown();s.server_close();t.join()
        assert Broker(GoalQueue(GoalAgents(path,key)),[p]).status(p)==result
        return {"scope":"local authenticated synthetic evaluations, no LLM or external actions","restart_verified":True,"pause_resume_verified":True,"result":result}
if __name__=="__main__":print(json.dumps(run(),indent=2))
