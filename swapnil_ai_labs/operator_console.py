"""Loopback-only operator console; no model inference or external actions."""
import argparse,os,secrets
from pathlib import Path
from wsgiref.simple_server import make_server,WSGIRequestHandler
from secure_service.service import digest,canonical
from swapnil_ai_labs.goal_agents import GoalAgents,GOALS
from swapnil_ai_labs.goal_queue import GoalQueue
from swapnil_ai_labs.goal_broker import Broker,BrokerPrincipal,make_app
HTML='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Swapnil AI Labs | Operator Console</title><link rel="stylesheet" href="/style.css"></head><body><main><header><small>SWAPNIL AI LABS / LOCAL OPERATIONS</small><h1>Agent execution console</h1><p>Authenticated local queue. No LLM inference or external actions.</p></header><section><h2>Connect</h2><label>Temporary operator token <input id="token" type="password" autocomplete="off"></label><button id="connect">Connect / refresh</button><button id="disconnect">Disconnect</button><p id="message" role="status">Disconnected.</p></section><section><h2>Queue control</h2><p id="summary">No state loaded.</p><button id="pause" disabled>Pause</button><button id="resume" disabled>Resume</button><button id="tick" disabled>Run up to 14 jobs</button></section><section><h2>Assign goal</h2><label>Category <select id="category"></select></label><label>Task ID <input id="task" maxlength="64"></label><label>Expected revision <input id="revision" type="number" min="0" value="0"></label><label>Evidence references (JSON) <textarea id="evidence" rows="4">{}</textarea></label><p id="required"></p><button id="save" disabled>Save task</button><label>Job ID <input id="job" maxlength="64"></label><button id="enqueue" disabled>Enqueue saved revision</button></section><section><h2>Latest 100 jobs</h2><div id="jobs"></div></section><footer>Pause stops new admissions, not in-flight work. Evidence references are not verified truth.</footer></main><script src="/app.js" defer></script></body></html>'''
CSS='''*{box-sizing:border-box}body{margin:0;background:#0e1020;color:#edeef6;font:15px/1.5 system-ui,sans-serif}main{max-width:860px;margin:auto;padding:24px}header{padding:24px;background:#22213e;border-radius:16px}small{letter-spacing:2px;color:#b4a6ff}h1{font-size:clamp(28px,6vw,46px);line-height:1.1}h2{font-size:20px}section{border-bottom:1px solid #35374b;padding:12px 0 22px}label{display:block;margin:8px 0;color:#c6c8d8}input,select,textarea{display:block;width:100%;padding:10px;border:1px solid #4b4d66;background:#171a2d;color:white;border-radius:7px;font:inherit}button{background:#7564e6;color:white;border:none;border-radius:7px;padding:10px 14px;margin:5px 6px 5px 0;cursor:pointer;font:inherit}button:disabled{opacity:.4;cursor:default}#message,#required,footer{color:#b5b7cc;font-size:13px}.job{border:1px solid #35374b;border-radius:9px;padding:12px;margin:10px 0;overflow-wrap:anywhere}footer{margin-top:24px}'''
JS='''"use strict";
const $=id=>document.getElementById(id);let token="",connected=false,busy=false,goals={};
function msg(s){$("message").textContent=s}
function controls(){for(const id of ["pause","resume","tick","save","enqueue"])$(id).disabled=!connected||busy}
async function req(path,body){const r=await fetch(path,{method:body?"POST":"GET",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:body?JSON.stringify(body):undefined,cache:"no-store",credentials:"omit"});const x=await r.json();if(!r.ok)throw Error(x.reason||"Request failed");return x}
async function refresh(){const s=await req("/v1/goals/status");$("summary").textContent=(s.paused?"Paused":"Admissions enabled")+" · "+JSON.stringify(s.counts);$("jobs").replaceChildren();for(const j of s.jobs){const d=document.createElement("article");d.className="job";const h=document.createElement("strong");h.textContent=j.id+" · "+j.category+" · "+j.status;const p=document.createElement("p");p.textContent=j.result?JSON.stringify(j.result):"Awaiting evaluation";d.append(h,p);$("jobs").append(d)}}
async function act(fn){if(busy)return;busy=true;controls();try{await fn();msg("Request completed.")}catch(e){msg("Request failed: "+e.message+"; inspect state before retry.")}finally{busy=false;controls()}}
$("connect").onclick=()=>act(async()=>{if($("token").value){token=$("token").value;$("token").value=""}connected=false;await refresh();connected=true});
$("disconnect").onclick=()=>{if(busy)return;token="";connected=false;$("token").value="";$("jobs").replaceChildren();$("summary").textContent="No state loaded.";controls();msg("Disconnected.")};
async function cmd(action,extra={}){return req("/v1/goals/commands",{action,...extra})}
for(const id of ["pause","resume","tick"])$(id).onclick=()=>act(async()=>{await cmd(id,id==="tick"?{limit:14}:{});await refresh()});
function fields(){const task=$("task").value.trim(),category=$("category").value,revision=Number($("revision").value);if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(task)||!Number.isInteger(revision)||revision<0||revision>999999)throw Error("Invalid task or revision");return {task,category,revision}}
$("save").onclick=()=>act(async()=>{const r=await cmd("set_task",{...fields(),evidence:JSON.parse($("evidence").value)});$("revision").value=r.revision;await refresh()});
$("enqueue").onclick=()=>act(async()=>{await cmd("enqueue",{...fields(),job:$("job").value.trim()});await refresh()});
function required(){$("required").textContent="Expected evidence keys: "+(goals[$("category").value]||[]).join(", ")}
fetch("/goals.json",{cache:"no-store"}).then(r=>r.json()).then(g=>{goals=g;for(const k of Object.keys(g)){const o=document.createElement("option");o.value=k;o.textContent=k;$("category").append(o)}required()}).catch(()=>msg("Goal catalog unavailable."));$("category").onchange=required;
'''
def console_app(broker,origin):
    inner=make_app(broker);host=origin.removeprefix("http://")
    assets={"/":("text/html; charset=utf-8",HTML),"/style.css":("text/css; charset=utf-8",CSS),"/app.js":("application/javascript; charset=utf-8",JS),"/goals.json":("application/json",canonical({k:list(v.checks) for k,v in GOALS.items()}))}
    def app(env,start):
        def send(code,ctype,data):
            raw=data.encode()
            start(code,[("Content-Type",ctype),("Content-Length",str(len(raw))),("Cache-Control","no-store"),("X-Content-Type-Options","nosniff"),("Referrer-Policy","no-referrer"),("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")]);return [raw]
        if env.get("HTTP_HOST")!=host or env.get("HTTP_ORIGIN") not in (None,"",origin):return send("403 Forbidden","application/json",'{"reason":"origin_denied"}')
        if env.get("PATH_INFO") in assets:
            if env.get("REQUEST_METHOD")!="GET":return send("405 Method Not Allowed","application/json",'{"reason":"method"}')
            return send("200 OK",*assets[env["PATH_INFO"]])
        scoped=dict(env);scoped.pop("HTTP_ORIGIN",None);return inner(scoped,start)
    return app
class Quiet(WSGIRequestHandler):
    def log_message(self,*args):pass
def load_key(path):
    path=Path(path)
    try:fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        if path.is_symlink() or not path.is_file():raise ValueError("unsafe key file")
        if os.name=="posix" and path.stat().st_mode&0o077:raise ValueError("key must be private")
        key=path.read_bytes()
    else:
        key=secrets.token_bytes(32)
        with os.fdopen(fd,"wb") as f:f.write(key)
    if len(key)!=32:raise ValueError("invalid key file")
    return key
def main():
    p=argparse.ArgumentParser(description="Loopback-only synthetic operator console")
    p.add_argument("--directory",default=str(Path.home()/".swapnil-ai-labs"/"operations"));p.add_argument("--port",type=int,default=8765)
    a=p.parse_args()
    if not 1024<=a.port<=65535:p.error("invalid port")
    directory=Path(a.directory);directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    if directory.is_symlink() or (os.name=="posix" and directory.stat().st_mode&0o077):p.error("directory must be private and not a symlink")
    key=load_key(directory/"goal.key");token=secrets.token_urlsafe(32)
    broker=Broker(GoalQueue(GoalAgents(directory/"goals.db",key)),[BrokerPrincipal("founder","local",digest(token),"operator")])
    origin="http://127.0.0.1:"+str(a.port)
    with make_server("127.0.0.1",a.port,console_app(broker,origin),handler_class=Quiet) as server:
        print("Open "+origin+"\nTemporary local operator token: "+token+"\nKeep private; changes on restart.",flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
if __name__=="__main__":main()
