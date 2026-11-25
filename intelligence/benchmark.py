"""Small synthetic evaluation; not a scientific novelty claim or model accuracy benchmark."""
import json,random
from intelligence.context import select
from intelligence.memory import Memory
from intelligence.routing import Candidate,route
def run():
    rng=random.Random(20261125); rows=[]
    for i in range(100):
        docs=[{"id":str(j),"text":f"project code P{j} invoice amount {j*7+4} status paid"} for j in range(20)]
        target=rng.randrange(20); rng.shuffle(docs); q=f"invoice P{target}"
        picked=select(q,docs,word_budget=8)
        rows.append({"track":"context","case":i,"expected":str(target),"first":docs[0]["id"],"selected":picked[0]["id"] if picked else None})
    m=Memory()
    try:
        for i in range(100):
            key=f"key{i}";m.put("tenant-a",key,"A","verified_host",20,10);m.put("tenant-b",key,"B","user_confirmed",30,10)
            tenant=rng.choice(["tenant-a","tenant-b","tenant-c"]);now=rng.choice([11,20,30])
            expected="A" if tenant=="tenant-a" and now<20 else "B" if tenant=="tenant-b" and now<30 else None
            actual=m.get(tenant,key,now)
            rows.append({"track":"memory","case":i,"expected":expected,"latest":"B","selected":actual["value"] if actual else None})
    finally:m.close()
    candidates=[Candidate("small",1,.75,100),Candidate("medium",3,.92,300),Candidate("large",5,.98,500)]
    for i in range(100):
        threshold=rng.choice([.7,.9,.95]);budget=rng.choice([1,3,5]);latency=rng.choice([100,300,500])
        actual=route(candidates,budget,threshold,latency)
        acceptable=[x for x in candidates if x.cost<=budget and x.predicted_success>=threshold and x.latency_ms<=latency]
        expected=sorted(acceptable,key=lambda x:x.cost)[0].name if acceptable else None
        rows.append({"track":"routing","case":i,"expected":expected,"selected":actual.name if actual else None,"always_large":"large"})
    summary={}
    for track,base in [("context","first"),("memory","latest"),("routing","always_large")]:
        r=[x for x in rows if x["track"]==track]
        summary[track]={"n":len(r),"candidate_correct":sum(x["selected"]==x["expected"] for x in r),"simple_baseline_correct":sum(x[base]==x["expected"] for x in r)}
    return {"seed":20261125,"scope":"authored synthetic records, no external model quality or cost claims","summary":summary,"rows":rows}
if __name__=="__main__":
    from pathlib import Path
    result=run(); print(json.dumps(result["summary"],indent=2))
    Path("intelligence-results.json").write_text(json.dumps(result,indent=2)+"\n")
