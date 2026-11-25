"""Deterministic budgeted BM25 selection; budget in whitespace words, not model tokens."""
import math,re
from collections import Counter
def tokens(text): return re.findall(r"\w+",text.casefold())
def select(query, records, word_budget=100):
    if type(word_budget) is not int or word_budget<0: raise ValueError("invalid budget")
    rows=list(records); docs=[tokens(r["text"]) for r in rows]; n=len(docs)
    if not n: return []
    avg=max(1,sum(map(len,docs))/n); q=set(tokens(query))
    df=Counter(term for d in docs for term in set(d))
    ranked=[]
    for i,d in enumerate(docs):
        f=Counter(d)
        score=sum(math.log(1+(n-df[t]+.5)/(df[t]+.5))*f[t]*2.2/(f[t]+1.2*(.25+.75*len(d)/avg)) for t in q if f[t])
        ranked.append((-score,i))
    picked=[]; used=0
    for neg,i in sorted(ranked):
        size=len(rows[i]["text"].split())
        if neg>=0 or used+size>word_budget: continue
        picked.append(rows[i]); used+=size
    return picked
