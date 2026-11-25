"""Local WSGI interface. Production requires independent identity/TLS/rate limits."""
import json,sqlite3,os
from secure_service.service import strict_json
from swapnil_ai_labs.work_relay import WorkRelay,RelayPrincipal,RelayError

def make_app(relay):
    def app(env,start):
        def send(code,obj):
            reasons={200:"OK",400:"Bad Request",401:"Unauthorized",403:"Forbidden",404:"Not Found",405:"Method Not Allowed",409:"Conflict",413:"Payload Too Large",415:"Unsupported Media Type",503:"Service Unavailable"}
            data=json.dumps(obj,separators=(",",":")).encode()
            start(str(code)+" "+reasons[code],[("Content-Type","application/json"),("Content-Length",str(len(data))),("Cache-Control","no-store"),("X-Content-Type-Options","nosniff")]);return [data]
        path=env.get("PATH_INFO","");method=env.get("REQUEST_METHOD");auth=env.get("HTTP_AUTHORIZATION")
        if path=="/healthz" and method=="GET":return send(200,{"status":"ok"})
        if env.get("HTTP_ORIGIN"):return send(403,{"reason":"browser_origin"})
        try:
            if path=="/v1/relay/commands":
                if method!="POST":return send(405,{"reason":"method"})
                if env.get("CONTENT_TYPE","").split(";")[0].strip().lower()!="application/json":return send(415,{"reason":"content_type"})
                if relay.auth(auth) is None:return send(401,{"reason":"authentication_required"})
                try:
                    n=int(env.get("CONTENT_LENGTH",""))
                    if n>8192:return send(413,{"reason":"size"})
                    if n<1:raise ValueError()
                    raw=env["wsgi.input"].read(n)
                    if len(raw)!=n:raise ValueError()
                    body=strict_json(raw.decode("utf-8"))
                except (ValueError,UnicodeError,RecursionError):return send(400,{"reason":"malformed_json"})
                return send(200,relay.command(auth,body))
            if path.startswith("/v1/relay/items/"):
                if method!="GET":return send(405,{"reason":"method"})
                return send(200,relay.get(auth,path.removeprefix("/v1/relay/items/")))
            return send(404,{"reason":"not_found"})
        except RelayError as e:return send(e.code,{"reason":e.reason})
        except sqlite3.Error:return send(503,{"reason":"storage_unavailable"})
    return app
def from_env():
    ps=json.loads(os.environ["RELAY_PRINCIPALS"])
    principals=[RelayPrincipal(x["id"],x["tenant"],x["token_hash"],x["role"],frozenset(x["departments"])) for x in ps]
    return make_app(WorkRelay(os.environ["RELAY_DB"],principals,bytes.fromhex(os.environ["RELAY_AUDIT_KEY"])))
