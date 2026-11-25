"""Runs actual HTTP requests against isolated Gunicorn container; random credentials only."""
import concurrent.futures,hashlib,json,os,secrets,statistics,subprocess,tempfile,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    suffix=secrets.token_hex(6);name="swapnil-research-"+suffix;volume=name+"-data"
    token_a=secrets.token_urlsafe(48);token_b=secrets.token_urlsafe(48);key=secrets.token_hex(32)
    cats=["finance","support","operations","knowledge"]
    cfg=[{"id":"reader-"+x,"tenant":"tenant-"+x,"token_hash":hashlib.sha256(t.encode()).hexdigest(),"categories":cats,"limit":10000,"budget":1000} for x,t in [("a",token_a),("b",token_b)]]
    def docker(*args,**kw):return subprocess.run(["docker",*args],check=True,**kw)
    with tempfile.TemporaryDirectory() as tmp:
        env=Path(tmp)/"env";env.write_text("SWAPNIL_AI_LABS_DB=/data/service.db\nSWAPNIL_AI_LABS_STAGING=1\nSWAPNIL_AI_LABS_PRINCIPALS="+json.dumps(cfg,separators=(",",":"))+"\nSWAPNIL_AI_LABS_AUDIT_KEY="+key+"\n");env.chmod(0o600)
        # No credentials logged. The container is accessible only on runner loopback.
        mount=["--mount",f"type=volume,src={volume},dst=/data","--env-file",str(env),"--read-only","--tmpfs","/tmp:rw,noexec,nosuid,size=32m","--cap-drop=ALL","--security-opt=no-new-privileges"]
        try:
            docker("build","-f","deployment/Dockerfile","-t",name,".",cwd=ROOT)
            docker("volume","create",volume,stdout=subprocess.DEVNULL)
            docker("run","--rm",*mount,"--entrypoint","python",name,"-m","deployment.seed_staging")
            docker("run","-d","--name",name,*mount,"-p","127.0.0.1::8080",name,stdout=subprocess.DEVNULL)
            port=docker("port",name,"8080/tcp",capture_output=True,text=True).stdout.strip().split(":")[-1]
            url="http://127.0.0.1:"+port
            for i in range(60):
                try:
                    with urllib.request.urlopen(url+"/healthz",timeout=1) as r:
                        if r.status==200:break
                except OSError:time.sleep(.2)
            else:raise RuntimeError("staging did not become healthy")
            def call(i,token,cat,request_id=None,mismatch=False):
                rid=cat+"-001";body={"version":"1.0","request_id":request_id or "r-"+str(i),"category":cat,"record_id":rid,"proposal":{"version":"1.0","action":"read_record","category":cat,"record_id":"wrong" if mismatch else rid}}
                req=urllib.request.Request(url+"/v1/read",json.dumps(body).encode(),{"Authorization":"Bearer "+token,"Content-Type":"application/json"})
                start=time.perf_counter()
                try:
                    with urllib.request.urlopen(req,timeout=10) as r:code=r.status;payload=json.loads(r.read())
                except urllib.error.HTTPError as e:code=e.code;payload=json.loads(e.read())
                return code,payload,round((time.perf_counter()-start)*1000,3)
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                rs=list(pool.map(lambda i:call(i,token_a if i%2==0 else token_b,cats[i%4]),range(64)))
            assert all(r[0]==200 and r[1]["output"]["value"]==(100 if i%2==0 else 900) for i,r in enumerate(rs))
            assert call(100,token_a,"finance","r-0")[0]==409
            assert call(101,token_a,"finance",mismatch=True)[0]==403
            assert call(102,secrets.token_urlsafe(48),"finance")[0]==401
            docker("exec",name,"python","deployment/backup.py","/data/service.db","/data/backup.db")
            docker("exec",name,"python","-c","import os; from secure_service.service import Service,Principal; import json; p=[Principal(x['id'],x['tenant'],x['token_hash'],frozenset(x['categories']),x['limit'],x['budget']) for x in json.loads(os.environ['SWAPNIL_AI_LABS_PRINCIPALS'])]; s=Service('/data/backup.db',p,bytes.fromhex(os.environ['SWAPNIL_AI_LABS_AUDIT_KEY'])); assert s.verify_audit(); print('Backup audit chain verified')")
            docker("restart",name,stdout=subprocess.DEVNULL)
            for i in range(60):
                try:
                    with urllib.request.urlopen(url+"/healthz",timeout=1) as r:
                        if r.status==200:break
                except OSError:time.sleep(.2)
            else:raise RuntimeError("restart failed")
            assert call(103,token_a,"finance","r-0")[0]==409
            times=sorted(r[2] for r in rs);result={"scope":"isolated synthetic single-node Gunicorn container; not capacity benchmark or production deployment","concurrent_reads":64,"correct_reads":64,"negative_http_checks":4,"backup_integrity":True,"backup_audit_verified":True,"restart_replay_blocked":True,"median_ms":statistics.median(times),"p95_ms":times[60]}
            print(json.dumps(result,indent=2));(ROOT/"staging-results.json").write_text(json.dumps(result,indent=2)+"\n")
        finally:
            subprocess.run(["docker","rm","-f",name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            subprocess.run(["docker","volume","rm",volume],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
if __name__=="__main__":main()
