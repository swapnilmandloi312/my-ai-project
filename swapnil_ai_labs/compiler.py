"""Compile a deliberately narrow declarative workflow into a deterministic plan."""
from dataclasses import dataclass
from hashlib import sha256
import json

STAGES=("context","memory","route","propose","authorize","execute","trace")
@dataclass(frozen=True)
class Plan:
    stages:tuple
    word_budget:int
    model_budget:int
    minimum_success:float
    digest:str

def compile_workflow(spec):
    if type(spec) is not dict or set(spec)!={"version","stages","word_budget","model_budget","minimum_success"} or spec["version"]!="1.0": raise ValueError("invalid specification")
    stages=spec["stages"]
    if type(stages) is not list or any(type(x) is not str for x in stages) or tuple(stages)!=STAGES: raise ValueError("required execution order; authorization cannot be bypassed")
    w,b,q=spec["word_budget"],spec["model_budget"],spec["minimum_success"]
    if type(w) is not int or not 0<=w<=10000 or type(b) is not int or not 0<=b<=10000 or type(q) not in (int,float) or not 0<=q<=1: raise ValueError("invalid limits")
    digest=sha256(json.dumps(spec,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    return Plan(tuple(stages),w,b,q,digest)

def execute_plan(plan,platform,request,query,records,candidates,provider,now=None):
    if type(plan) is not Plan: raise ValueError("compile a workflow first")
    check=compile_workflow({"version":"1.0","stages":list(plan.stages),"word_budget":plan.word_budget,"model_budget":plan.model_budget,"minimum_success":plan.minimum_success})
    if check!=plan: raise ValueError("plan integrity mismatch")
    result=platform.run(request,query,records,candidates,provider,word_budget=plan.word_budget,model_budget=plan.model_budget,minimum_success=plan.minimum_success,now=now)
    return {**result,"plan_id":plan.digest}
