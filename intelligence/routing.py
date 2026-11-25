"""Constrained deterministic model routing using user-supplied estimates."""
from dataclasses import dataclass
import math
@dataclass(frozen=True)
class Candidate:
    name:str
    cost:float
    predicted_success:float
    latency_ms:int
def route(candidates, budget, minimum_success=.9, max_latency_ms=2000):
    if not all(math.isfinite(x) for x in (budget,minimum_success,max_latency_ms)) or budget<0 or not 0<=minimum_success<=1 or max_latency_ms<0: raise ValueError("invalid constraints")
    eligible=[]
    for c in candidates:
        if not all(math.isfinite(x) for x in (c.cost,c.predicted_success,c.latency_ms)) or c.cost<0 or not 0<=c.predicted_success<=1 or c.latency_ms<0: raise ValueError("invalid model estimates")
        if c.cost<=budget and c.predicted_success>=minimum_success and c.latency_ms<=max_latency_ms: eligible.append(c)
    return min(eligible,key=lambda c:(c.cost,-c.predicted_success,c.latency_ms,c.name),default=None)
