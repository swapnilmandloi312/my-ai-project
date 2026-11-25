"""Loopback-only HTTP demo. Every request gets a fresh synthetic database. No auth."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from integrations.pilot import InvoicePilot

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path!='/propose': self.send_error(404); return
        if self.headers.get_content_type()!='application/json' or self.headers.get('Origin'):
            self.send_error(415); return
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=4096: raise ValueError()
            text=self.rfile.read(n).decode('utf-8')
        except (ValueError,UnicodeError):
            self.send_error(400); return
        pilot=InvoicePilot()
        try: result=pilot.propose(text)
        finally: pilot.close()
        body=json.dumps(result).encode()
        self.send_response(200); self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*args): pass

def serve(port=8765): return HTTPServer(('127.0.0.1',port),Handler)
if __name__=='__main__':
    with serve() as server: server.serve_forever()
