import unittest,tempfile,io,json,threading
from pathlib import Path
from secure_service.service import Service,strict_json
from secure_service.fixtures import principals,seed,request,TOKEN_A,TOKEN_B
from secure_service.http import make_app
class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/"data.db");self.s=Service(self.path,principals(),b"k"*32,lambda:120);seed(self.s,4)
        self.a="Bearer "+TOKEN_A;self.b="Bearer "+TOKEN_B;self.req=request("finance","finance-000","req1")
    def tearDown(self):self.tmp.cleanup()
    def test_categories(self):
        for c in ["finance","support","operations","knowledge"]:self.assertEqual(self.s.read(self.a,request(c,c+"-000","req-"+c))[0],200)
    def test_tenant_same_id(self):
        self.assertEqual(self.s.read(self.a,self.req)[1]["output"]["value"],100);self.assertEqual(self.s.read(self.b,self.req)[1]["output"]["value"],900)
    def test_auth(self):self.assertEqual(self.s.read("Bearer "+"x"*40,self.req)[0],401)
    def test_missing_acl(self):self.assertEqual(self.s.read(self.a,request("finance","finance-001","r2"))[0],403)
    def test_mismatch(self):self.assertEqual(self.s.read(self.a,{**self.req,"proposal":{**self.req["proposal"],"record_id":"finance-002"}})[0],403)
    def test_extra_tenant(self):self.assertEqual(self.s.read(self.a,{**self.req,"tenant":"tenant-b"})[0],400)
    def test_replay(self):self.assertEqual(self.s.read(self.a,self.req)[0],200);self.assertEqual(self.s.read(self.a,self.req)[0],409)
    def test_concurrency(self):
        b=threading.Barrier(2);result=[]
        def run():b.wait(timeout=3);result.append(self.s.read(self.a,self.req)[0])
        a=threading.Thread(target=run);c=threading.Thread(target=run);a.start();c.start();a.join(5);c.join(5);self.assertEqual(sorted(result),[200,409])
    def test_budget(self):
        s=Service(self.path,principals(budget=1),b"k"*32,lambda:120);self.assertEqual(s.read(self.a,self.req)[0],200);self.assertEqual(s.read(self.a,request("finance","finance-002","req2"))[0],429)
    def test_rate(self):
        s=Service(self.path,principals(limit=1),b"k"*32,lambda:120);s.read(self.a,self.req);self.assertEqual(s.read(self.a,request("finance","finance-002","r2"))[0],429)
    def test_restart(self):
        self.s.read(self.a,self.req);s=Service(self.path,principals(),b"k"*32,lambda:120);self.assertEqual(s.read(self.a,self.req)[0],409)
    def test_audit(self):
        self.s.read(self.a,self.req);self.assertTrue(self.s.verify_audit());db=self.s.connect()
        try:db.execute("UPDATE audit SET event='tampered' WHERE seq=1")
        finally:db.close()
        self.assertFalse(self.s.verify_audit())
    def test_json(self):
        with self.assertRaises(ValueError):strict_json('{"x":1,"x":2}')
        with self.assertRaises(ValueError):strict_json('{"x":NaN}')
    def http(self,body,auth=None,**env):
        raw=body if type(body) is bytes else json.dumps(body).encode();start=[]
        e={"PATH_INFO":"/v1/read","REQUEST_METHOD":"POST","CONTENT_TYPE":"application/json","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw),"HTTP_AUTHORIZATION":auth or self.a,**env}
        out=b"".join(make_app(self.s)(e,lambda status,headers:start.append((status,headers))))
        return int(start[0][0].split()[0]),json.loads(out),dict(start[0][1])
    def test_http_success(self):
        status,r,h=self.http(self.req);self.assertEqual(status,200);self.assertEqual(h["Cache-Control"],"no-store")
    def test_http_duplicate(self):self.assertEqual(self.http(b'{"x":1,"x":2}')[0],400)
    def test_http_size(self):self.assertEqual(self.http(b"x"*8193)[0],413)
    def test_http_origin(self):self.assertEqual(self.http(self.req,HTTP_ORIGIN="https://example.invalid")[0],403)
    def test_http_content(self):self.assertEqual(self.http(self.req,CONTENT_TYPE="text/plain")[0],415)
    def test_http_method(self):self.assertEqual(self.http(self.req,REQUEST_METHOD="GET")[0],405)
    def test_unknown_record(self):self.assertEqual(self.s.read(self.a,request("finance","finance-999","r2"))[0],403)
