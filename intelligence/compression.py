"""Extractive context compression; preserves complete evidence sentences and source identifiers."""
import re
from intelligence.context import select
def compress(query,records,word_budget):
    if type(word_budget) is not int or word_budget<0:raise ValueError("invalid budget")
    segments=[]
    for r in records:
        for i,s in enumerate(re.split(r"(?<=[.!?])\s+",r["text"].strip())):
            if s:segments.append({"source_id":r["id"],"sentence":i,"text":s})
    chosen=select(query,segments,word_budget)
    return {"segments":chosen,"input_words":sum(len(r["text"].split()) for r in records),"output_words":sum(len(s["text"].split()) for s in chosen),"scope":"whitespace words, not tokenizer tokens; no model answer guarantee"}
