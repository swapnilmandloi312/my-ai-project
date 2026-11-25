import json,threading,unittest,urllib.request,urllib.error
from wsgiref.simple_server import make_server
from swapnil_ai_labs.test_work_relay import Tests
from swapnil_ai_labs.relay_http import make_app
class HTTPTests(unittest.TestCase):
    def test_loopback(self):
        fixture=Tests();fixture.setUp()
        server=make_server("127.0.0.1",0,make_app(fixture.s));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        root="http://127.0.0.1:"+str(server.server_port)
        def call(path,body=None,auth=None,raw=None):
            headers={"Content-Type":"application/json"}
            if auth:headers["Authorization"]=auth
            data=raw if raw is not None else json.dumps(body).encode() if body is not None else None
            req=urllib.request.Request(root+path,data=data,headers=headers)
            try:
                with urllib.request.urlopen(req,timeout=5) as r:return r.status,json.load(r)
            except urllib.error.HTTPError as e:return e.code,json.load(e)
        def cmd(who,action,rev,data=None):
            return call("/v1/relay/commands",{"command_id":action+str(rev),"item_id":"case","action":action,"revision":rev,"data":data or {}},fixture.auth(who))
        try:
            self.assertEqual(call("/healthz")[0],200)
            self.assertEqual(cmd("a","create",0,{"department":"finance"})[0],200)
            self.assertEqual(cmd("a","attach",1,{"key":"invoice","reference":"doc-1"})[0],200)
            self.assertEqual(cmd("a","attach",2,{"key":"purchase_order","reference":"po-1"})[0],200)
            self.assertEqual(cmd("a","submit",3)[1]["state"],"awaiting_review")
            self.assertEqual(cmd("o","resolve",4)[0],409)
            self.assertEqual(cmd("r","approve",4)[0],200)
            self.assertEqual(cmd("o","resolve",5)[1]["state"],"resolved_local")
            self.assertEqual(call("/v1/relay/items/case",auth=fixture.auth("other"))[0],404)
            self.assertEqual(call("/v1/relay/items/case")[0],401)
            self.assertEqual(call("/v1/relay/commands",auth=fixture.auth("a"),raw=b'{"a":1,"a":2}')[0],400)
        finally:server.shutdown();server.server_close();thread.join();fixture.tearDown()
if __name__=="__main__":unittest.main()
