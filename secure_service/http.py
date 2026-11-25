"""WSGI application; use a hardened production server/TLS proxy, not wsgiref, externally."""
import json,os,sqlite3
from secure_service.service import Service,Principal,strict_json
def make_app(service):
    def app(env,start):
        def reply(code,payload):
            reasons={200:"OK",400:"Bad Request",401:"Unauthorized",403:"Forbidden",404:"Not Found",405:"Method Not Allowed",409:"Conflict",413:"Payload Too Large",415:"Unsupported Media Type",429:"Too Many Requests",503:"Service Unavailable"}
            b=json.dumps(payload,separators=(",",":")).encode()
            headers=[("Content-Type","application/json"),("Content-Length",str(len(b))),("Cache-Control","no-store"),("X-Content-Type-Options","nosniff")]
            if code==401:headers.append(("WWW-Authenticate","Bearer"))
            start(f"{code} {reasons[code]}",headers);return [b]
        if env.get("PATH_INFO")=="/healthz" and env.get("REQUEST_METHOD")=="GET":return reply(200,{"status":"ok"})
        if env.get("PATH_INFO")!="/v1/read":return reply(404,{"status":"blocked","reason":"not_found"})
        if env.get("REQUEST_METHOD")!="POST":return reply(405,{"status":"blocked","reason":"method"})
        if env.get("CONTENT_TYPE","").split(";")[0].strip().lower()!="application/json":return reply(415,{"status":"blocked","reason":"content_type"})
        if env.get("HTTP_ORIGIN"):return reply(403,{"status":"blocked","reason":"browser_origin"})
        auth=env.get("HTTP_AUTHORIZATION")
        try:
            n=int(env.get("CONTENT_LENGTH",""))
            if n>8192:return reply(413,{"status":"blocked","reason":"size"})
            if n<1:raise ValueError()
            data=env["wsgi.input"].read(n)
            if len(data)!=n:raise ValueError()
            body=strict_json(data.decode("utf-8"))
        except (ValueError,UnicodeError,RecursionError):return reply(400,{"status":"blocked","reason":"malformed_json"})
        try:status,result=service.read(auth,body);return reply(status,result)
        except sqlite3.Error:return reply(503,{"status":"blocked","reason":"storage_unavailable"})
    return app
def from_env():
    values=json.loads(os.environ["SWAPNIL_AI_LABS_PRINCIPALS"])
    principals=[Principal(x["id"],x["tenant"],x["token_hash"],frozenset(x["categories"]),x.get("limit",60),x.get("budget",100)) for x in values]
    return make_app(Service(os.environ["SWAPNIL_AI_LABS_DB"],principals,bytes.fromhex(os.environ["SWAPNIL_AI_LABS_AUDIT_KEY"])))
