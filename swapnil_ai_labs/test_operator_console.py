import json,tempfile,unittest,threading,urllib.request,urllib.error
from pathlib import Path
from wsgiref.simple_server import make_server
from secure_service.service import digest
from swapnil_ai_labs.goal_agents import GoalAgents
from swapnil_ai_labs.goal_queue import GoalQueue
from swapnil_ai_labs.goal_broker import Broker,BrokerPrincipal
from swapnil_ai_labs.operator_console import console_app,load_key
class Tests(unittest.TestCase):
    def test_loopback(self):
        with tempfile.TemporaryDirectory() as d:
            a=GoalAgents(Path(d)/"db",b"k"*32);b=Broker(GoalQueue(a),[BrokerPrincipal("founder","local",digest("x"*40),"operator")])
            s=make_server("127.0.0.1",0,lambda e,start:[])
            root="http://127.0.0.1:"+str(s.server_port);s.set_app(console_app(b,root))
            t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
            def call(path,body=None,headers=None):
                h={"Authorization":"Bearer "+"x"*40,"Content-Type":"application/json"};h.update(headers or {})
                req=urllib.request.Request(root+path,headers=h,data=json.dumps(body).encode() if body is not None else None)
                try:
                    with urllib.request.urlopen(req,timeout=5) as r:return r.status,r.read().decode()
                except urllib.error.HTTPError as e:return e.code,e.read().decode()
            try:
                self.assertIn("Agent execution console",call("/")[1])
                self.assertEqual(len(json.loads(call("/goals.json")[1])),14)
                self.assertEqual(call("/app.js")[0],200)
                self.assertEqual(call("/v1/goals/status",headers={"Origin":"https://evil.example"})[0],403)
                self.assertEqual(call("/",headers={"Host":"evil.example"})[0],403)
                self.assertEqual(call("/v1/goals/status",headers={"Authorization":""})[0],401)
                def cmd(body):return call("/v1/goals/commands",body,{"Origin":root})
                self.assertEqual(cmd({"action":"set_task","task":"research","category":"research","revision":0,"evidence":{}})[0],200)
                self.assertEqual(cmd({"action":"enqueue","job":"one","task":"research","category":"research","revision":1})[0],200)
                self.assertEqual(cmd({"action":"pause"})[0],200)
                self.assertEqual(json.loads(cmd({"action":"tick","limit":14})[1])["evaluated"],0)
                self.assertEqual(cmd({"action":"resume"})[0],200)
                self.assertEqual(json.loads(cmd({"action":"tick","limit":14})[1])["evaluated"],1)
                self.assertEqual(json.loads(call("/v1/goals/status")[1])["counts"],{"evaluated":1})
            finally:s.shutdown();s.server_close();t.join()
    def test_key_restart(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"key";a=load_key(p);self.assertEqual(len(a),32);self.assertEqual(load_key(p),a)
if __name__=="__main__":unittest.main()
