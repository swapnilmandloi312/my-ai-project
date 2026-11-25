"""Real loopback HTTP round trip through WSGI; no external deployment."""
import json,tempfile,threading,urllib.request,urllib.error
from pathlib import Path
from wsgiref.simple_server import make_server
from secure_service.service import Service
from secure_service.fixtures import principals,seed,request,TOKEN_A
from secure_service.http import make_app
def main():
    with tempfile.TemporaryDirectory() as tmp:
        service=Service(str(Path(tmp)/"test.db"),principals(),b"t"*32,lambda:120);seed(service,4)
        with make_server("127.0.0.1",0,make_app(service)) as server:
            t=threading.Thread(target=server.serve_forever);t.start()
            try:
                url=f"http://127.0.0.1:{server.server_port}/v1/read"
                def call(body,token):
                    r=urllib.request.Request(url,json.dumps(body).encode(),{"Content-Type":"application/json","Authorization":"Bearer "+token})
                    try:
                        with urllib.request.urlopen(r,timeout=3) as res:return res.status,json.loads(res.read())
                    except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
                statuses=[]
                for c in ("finance","support","operations","knowledge"):
                    status,out=call(request(c,c+"-000","http-"+c),TOKEN_A)
                    assert status==200 and out["output"]["category"]==c;statuses.append(status)
                assert call(request("finance","finance-000","http-finance"),TOKEN_A)[0]==409
                assert call(request("finance","finance-001","denied"),TOKEN_A)[0]==403
                assert call(request("finance","finance-000","unauth"),"x"*40)[0]==401
                print("7 actual HTTP checks passed:",statuses+[409,403,401])
            finally:server.shutdown();t.join()
if __name__=="__main__":main()
