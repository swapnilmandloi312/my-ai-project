import unittest,threading
from http.server import BaseHTTPRequestHandler,HTTPServer
from swapnil_ai_labs.relay_client import RelayClient,ClientError
from swapnil_ai_labs.relay_demo import run
class Tests(unittest.TestCase):
    def test_demo(self):
        r=run();self.assertEqual(len(r["cases"]),4);self.assertTrue(r["restart_persistence"]);self.assertTrue(r["audit_chain_verified"])
    def test_insecure_origin_rejected(self):
        for u in ["http://example.com","https://name:password@example.com","https://example.com/path","https://example.com?query=1"]:
            with self.assertRaises(ValueError):RelayClient(u,"x"*40)
    def test_no_redirect_or_token_forwarding(self):
        calls=[]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path);self.send_response(302);self.send_header("Location","/other");self.end_headers()
            def log_message(self,*args):pass
        s=HTTPServer(("127.0.0.1",0),Handler);t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
        try:
            c=RelayClient("http://127.0.0.1:"+str(s.server_port),"x"*40)
            with self.assertRaises(ClientError) as e:c.get("item")
            self.assertEqual(e.exception.status,302);self.assertEqual(calls,["/v1/relay/items/item"])
        finally:s.shutdown();s.server_close();t.join()
    def test_invalid_id(self):
        c=RelayClient("http://127.0.0.1:1","x"*40)
        with self.assertRaises(ValueError):c.get("../healthz")
if __name__=="__main__":unittest.main()
