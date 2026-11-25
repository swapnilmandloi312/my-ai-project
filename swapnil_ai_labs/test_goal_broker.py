import json,tempfile,unittest,threading,urllib.request,urllib.error
from pathlib import Path
from wsgiref.simple_server import make_server
from secure_service.service import digest
from swapnil_ai_labs.goal_agents import GoalAgents
from swapnil_ai_labs.goal_queue import GoalQueue
from swapnil_ai_labs.goal_broker import Broker,BrokerPrincipal,make_app
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/"jobs.db";self.clock=lambda:120
        self.tokens={"op":"a"*40,"view":"b"*40,"other":"c"*40}
        self.ps=[BrokerPrincipal(k,"tenant-b" if k=="other" else "tenant-a",digest(v),"viewer" if k=="view" else "operator") for k,v in self.tokens.items()]
        self.b=Broker(GoalQueue(GoalAgents(self.path,b"k"*32,clock=self.clock)),self.ps)
        self.server=make_server("127.0.0.1",0,make_app(self.b));self.t=threading.Thread(target=self.server.serve_forever,daemon=True);self.t.start();self.root="http://127.0.0.1:"+str(self.server.server_port)
    def tearDown(self):self.server.shutdown();self.server.server_close();self.t.join();self.tmp.cleanup()
    def call(self,path,who="op",body=None,raw=None,headers=None):
        h={"Content-Type":"application/json"}
        if who:h["Authorization"]="Bearer "+self.tokens[who]
        h.update(headers or {})
        data=raw if raw is not None else json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(self.root+path,data=data,headers=h)
        try:
            with urllib.request.urlopen(req,timeout=5) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)
    def cmd(self,body,who="op"):return self.call("/v1/goals/commands",who,body)
    def status(self,who="op"):return self.call("/v1/goals/status",who)
    def create(self,who="op"):
        self.assertEqual(self.cmd({"action":"set_task","task":"task","category":"research","evidence":{"hypothesis":"ref-1"},"revision":0},who),(200,{"revision":1}))
        self.assertEqual(self.cmd({"action":"enqueue","job":"job","task":"task","category":"research","revision":1},who),(200,{"job":"job"}))
    def test_real_http_lifecycle(self):
        self.create();self.assertEqual(self.cmd({"action":"pause"}),(200,{"paused":True}))
        self.assertEqual(self.cmd({"action":"tick","limit":14})[1]["evaluated"],0)
        self.assertEqual(self.cmd({"action":"resume"}),(200,{"paused":False}))
        r=self.cmd({"action":"tick","limit":14});self.assertEqual(r[1]["evaluated"],1);self.assertFalse(r[1]["results"][0]["verified_completion"])
        self.assertEqual(self.cmd({"action":"tick","limit":14})[1]["evaluated"],0)
        self.assertEqual(self.status("view")[1]["counts"],{"evaluated":1})
        restarted=Broker(GoalQueue(GoalAgents(self.path,b"k"*32,clock=self.clock)),self.ps)
        self.assertEqual(restarted.status(self.ps[0])["counts"],{"evaluated":1})
    def test_tenant(self):
        self.create();self.assertEqual(self.status("other")[1]["jobs"],[])
        self.assertEqual(self.cmd({"action":"enqueue","job":"other","task":"task","category":"research","revision":1},"other")[0],409)
        self.create("other");self.assertEqual(self.status("other")[1]["counts"],{"queued":1})
        self.cmd({"action":"tick","limit":1});self.assertEqual(self.status("other")[1]["counts"],{"queued":1})
    def test_viewer_denied(self):
        self.assertEqual(self.cmd({"action":"pause"},"view")[0],403);self.assertFalse(self.status()[1]["paused"])
    def test_auth(self):
        self.assertEqual(self.status(None)[0],401);self.assertEqual(self.call("/v1/goals/status",headers={"Authorization":"Bearer "+"z"*40})[0],401)
    def test_origin(self):self.assertEqual(self.call("/v1/goals/status",headers={"Origin":"https://example.org"})[0],403)
    def test_unknown_action(self):
        self.assertEqual(self.cmd({"action":"execute_shell","code":"anything"})[0],400)
        self.assertEqual(self.cmd({"action":"pause","tenant":"tenant-b"})[0],400)
    def test_input(self):
        self.assertEqual(self.call("/v1/goals/commands",raw=b'{"action":"pause","action":"resume"}')[0],400)
        self.assertEqual(self.call("/v1/goals/commands",raw=b"x"*8193)[0],413)
        self.assertEqual(self.call("/v1/goals/commands",body={"action":"pause"},headers={"Content-Type":"text/plain"})[0],415)
        self.assertEqual(self.cmd({"action":"tick","limit":15})[0],400)
    def test_rate(self):
        for _ in range(60):self.assertEqual(self.status()[0],200)
        self.assertEqual(self.status()[0],429);self.assertEqual(self.status("view")[0],200)
    def test_audit_no_payload(self):
        self.create();self.cmd({"action":"tick","limit":1})
        with self.b.agents.connect() as db:rows=[tuple(r) for r in db.execute("SELECT actor,tenant,action,outcome,ts FROM broker_events")]
        self.assertEqual(len(rows),3);self.assertNotIn(self.tokens["op"],str(rows));self.assertNotIn("ref-1",str(rows))
if __name__=="__main__":unittest.main()
