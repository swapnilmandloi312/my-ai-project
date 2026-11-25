"""Exploratory synthetic category planning, not independent external evaluation."""
import json,sys,tempfile,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
from swapnil_ai_labs.goal_agents import GoalAgents,GOALS
from swapnil_ai_labs.goal_queue import GoalQueue
from swapnil_ai_labs.goal_planner import GoalPlanner
KEY=os.environ.get("BENCHMARK_MODEL","qwen")
MODEL,REV={"qwen":("Qwen/Qwen2.5-0.5B-Instruct","a8b602d9dafd3a75d382e62757d83d89fca3be54"),"smollm":("HuggingFaceTB/SmolLM2-360M-Instruct","c38281e01d0c0b0c36eac2f5bcb5b51fa2e803fc")}[KEY]
torch.set_num_threads(2)
tok=AutoTokenizer.from_pretrained(MODEL,revision=REV,trust_remote_code=False)
model=AutoModelForCausalLM.from_pretrained(MODEL,revision=REV,trust_remote_code=False,use_safetensors=True,torch_dtype=torch.float32).eval()
rows=[];raw=[]
def provider(p,i):
    prompt=tok.apply_chat_template([{"role":"system","content":i},{"role":"user","content":json.dumps(p)}],tokenize=False,add_generation_prompt=True)
    inputs=tok(prompt,return_tensors="pt");start=time.perf_counter()
    with torch.inference_mode():out=model.generate(**inputs,max_new_tokens=24,do_sample=False,pad_token_id=tok.eos_token_id)
    s=tok.decode(out[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True);raw.append({"output":s,"seconds":time.perf_counter()-start,"allowed":p["allowed_next_steps"]});return s
with tempfile.TemporaryDirectory() as d:
    a=GoalAgents(Path(d)/"jobs.db",b"k"*32);q=GoalQueue(a);p=GoalPlanner(q,provider,daily_budget=28)
    for cat,spec in GOALS.items():
        for full in (False,True):
            job=cat+("-full" if full else "-missing")
            rev=a.set_task("synthetic",job,cat,{k:"synthetic-reference" for k in (spec.checks if full else spec.checks[:1])},0);q.enqueue("synthetic",job,job,cat,rev)
    q.tick("synthetic",limit=28)
    for job in q.snapshot("synthetic")["jobs"]:
        result=p.plan("synthetic",job["id"]);rows.append({"job":job["id"],"category":job["category"],"result":result,**raw[-1]})
    assert len(rows)==28 and all(not r["result"]["external_action"] and not r["result"]["verified_completion"] for r in rows)
summary={"accepted_choices":sum(r["result"]["status"]=="proposed" for r in rows),"cases":len(rows),"deterministic_first_choice_baseline":len(rows),"external_actions":0}
print(json.dumps(summary));(ROOT/("research/goal-plans-"+KEY+".json")).write_text(json.dumps({"model":MODEL,"revision":REV,"scope":"28 authored category cases, advisory choices only, no independent evaluation; deterministic baseline always chooses a permitted option","summary":summary,"rows":rows},indent=2)+"\n")
