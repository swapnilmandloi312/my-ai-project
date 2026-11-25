"""One-command loopback demonstration; random temporary credentials and synthetic records."""
import json,secrets,tempfile,threading
from pathlib import Path
from wsgiref.simple_server import make_server,WSGIRequestHandler
from secure_service.service import digest
from swapnil_ai_labs.work_relay import WorkRelay,RelayPrincipal,REQUIRED
from swapnil_ai_labs.relay_http import make_app
from swapnil_ai_labs.relay_client import RelayClient,ClientError
class Quiet(WSGIRequestHandler):
    def log_message(self,*args):pass
def run():
    results=[]
    with tempfile.TemporaryDirectory() as tmp:
        tokens={r:secrets.token_urlsafe(32) for r in ("requester","reviewer","operator")}
        principals=[RelayPrincipal(r,"synthetic",digest(t),r,frozenset(REQUIRED)) for r,t in tokens.items()]
        db=Path(tmp)/"relay.db";key=secrets.token_bytes(32)
        relay=WorkRelay(db,principals,key)
        server=make_server("127.0.0.1",0,make_app(relay),handler_class=Quiet)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            clients={r:RelayClient("http://127.0.0.1:"+str(server.server_port),t) for r,t in tokens.items()}
            for dep,keys in REQUIRED.items():
                item="demo-"+dep
                def cmd(role,action,rev,data=None):
                    return clients[role].command(dep+"-"+action+"-"+str(rev),item,action,rev,data)
                row=cmd("requester","create",0,{"department":dep})
                row=cmd("requester","submit",row["revision"])
                assert row["state"]=="needs_evidence"
                try:cmd("reviewer","approve",row["revision"])
                except ClientError as e:assert e.status==409
                else:raise AssertionError("missing evidence approval accepted")
                for k in sorted(keys):row=cmd("requester","attach",row["revision"],{"key":k,"reference":"synthetic-"+k})
                row=cmd("requester","submit",row["revision"])
                try:cmd("operator","resolve",row["revision"])
                except ClientError as e:assert e.reason=="approval_required"
                else:raise AssertionError("unapproved resolution accepted")
                row=cmd("reviewer","approve",row["revision"])
                row=cmd("operator","resolve",row["revision"])
                assert row["state"]=="resolved_local" and row["external_action"] is False
                assert clients["requester"].get(item)==row
                results.append({"department":dep,"missing_evidence_blocked":True,"unapproved_resolution_blocked":True,"final":row})
        finally:server.shutdown();server.server_close();thread.join()
        restarted=WorkRelay(db,principals,key)
        assert all(restarted.get("Bearer "+tokens["requester"],"demo-"+r["department"])==r["final"] for r in results)
        assert restarted.verify_audit()
    return {"scope":"synthetic loopback only; evidence references, not document verification; no model or external actions","cases":results,"restart_persistence":True,"audit_chain_verified":True}
def main():print(json.dumps(run(),indent=2))
if __name__=="__main__":main()
