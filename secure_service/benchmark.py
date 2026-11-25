"""Authored stratified cases. Compare independent explicit rule baseline and weak name check."""
import copy,json,tempfile
from pathlib import Path
from collections import Counter
from secure_service.service import Service,CATEGORIES
from secure_service.fixtures import principals,seed,request,TOKEN_A,TOKEN_B
def run():
    rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        s=Service(str(Path(tmp)/"db.sqlite"),principals(),b"b"*32,lambda:120);seed(s,24)
        for cat in sorted(CATEGORIES):
            for i in range(12):
                for variant in ("valid_a","valid_b","no_acl","wrong_record","wrong_category","unauthorized_action","unknown_version","extra_tenant","invalid_token","unknown_record"):
                    rid=f"{cat}-{i*2:03d}";body=request(cat,rid,f"{cat}-{i}-{variant}");auth="Bearer "+(TOKEN_B if variant=="valid_b" else TOKEN_A)
                    if variant=="no_acl":body=request(cat,f"{cat}-{i*2+1:03d}",body["request_id"])
                    elif variant=="wrong_record":body["proposal"]["record_id"]="different"
                    elif variant=="wrong_category":body["proposal"]["category"]="other"
                    elif variant=="unauthorized_action":body["proposal"]["action"]="write_record"
                    elif variant=="unknown_version":body["version"]="2.0"
                    elif variant=="extra_tenant":body["tenant"]="tenant-b"
                    elif variant=="invalid_token":auth="Bearer "+"x"*40
                    elif variant=="unknown_record":body=request(cat,f"{cat}-999",body["request_id"])
                    label=variant in ("valid_a","valid_b")
                    status,result=s.read(auth,body);allowed=status==200
                    correct_output=allowed and result["output"]["value"]==(i*2+(900 if variant=="valid_b" else 100))
                    weak=body["proposal"]["action"]=="read_record"
                    # Explicit rule baseline, independently specified from implementation; same fixture design.
                    strong=(auth in ("Bearer "+TOKEN_A,"Bearer "+TOKEN_B) and set(body)=={"version","request_id","category","record_id","proposal"} and body["version"]=="1.0" and body["proposal"]=={"version":"1.0","action":"read_record","category":cat,"record_id":rid} and body["record_id"]==rid)
                    rows.append({"category":cat,"case":i,"variant":variant,"authorized":label,"service_executed":allowed,"correct_output":correct_output,"name_only":weak,"explicit_rule":strong,"status":status})
        assert s.verify_audit()
    summary={}
    for name in ("service_executed","name_only","explicit_rule"):
        summary[name]={"authorized":sum(r["authorized"] for r in rows),"allowed_authorized":sum(r["authorized"] and r[name] for r in rows),"unauthorized":sum(not r["authorized"] for r in rows),"unsafe_executions":sum(not r["authorized"] and r[name] for r in rows)}
    summary["service_correct_outputs"]=sum(r["authorized"] and r["correct_output"] for r in rows)
    return {"scope":"480 authored deterministic fixtures; not independent holdout, real model inference, or security certification","summary":summary,"rows":rows}
if __name__=="__main__":
    r=run();print(json.dumps(r["summary"],indent=2));Path("secure-service-results.json").write_text(json.dumps(r,indent=2)+"\n")
    assert r["summary"]["service_correct_outputs"]==96 and r["summary"]["service_executed"]["unsafe_executions"]==0
