"""Aggregate only explicitly allowlisted numeric trace fields; no raw prompts or credentials."""
import math,statistics
def summarize(results):
    times=[];words=[];blocked=0
    for r in results:
        blocked+=int(r.get("status")!="executed_read_only")
        t=r.get("trace",{});elapsed=t.get("elapsed_ms");w=t.get("selected_words")
        if type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed>=0:times.append(elapsed)
        if type(w) is int and w>=0:words.append(w)
    times.sort()
    return {"requests":len(results),"blocked":blocked,"median_ms":statistics.median(times) if times else None,"p95_ms":times[math.ceil(.95*len(times))-1] if times else None,"selected_words":sum(words)}
