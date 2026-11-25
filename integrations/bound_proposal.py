"""Host-bound proposal recovery; trusted authorization must be independent of model output."""
import json, re
from integrations.pilot import InvoicePilot

def unique_object(pairs):
    obj={}
    for k,v in pairs:
        if k in obj: raise ValueError("duplicate key")
        obj[k]=v
    return obj

def reject_constant(value): raise ValueError("non-finite JSON")

def normalize(raw):
    if type(raw) is not str or len(raw)>4096: raise ValueError("invalid input")
    raw=raw.strip()
    fenced=re.fullmatch(r"```(?:json)?\s*\n([\s\S]*?)\n```",raw)
    if fenced: raw=fenced.group(1)
    obj=json.loads(raw,object_pairs_hook=unique_object,parse_constant=reject_constant)
    if type(obj) is not dict or set(obj)!={'action','args'} or type(obj['args']) is not dict: raise ValueError("invalid proposal")
    return obj

def execute(raw, authorized):
    if authorized is None: return {"status":"blocked","reason":"no trusted request authorization"}
    try:
        proposal=normalize(raw)
        if proposal!=authorized: return {"status":"blocked","reason":"request mismatch"}
        canonical=json.dumps(proposal,allow_nan=False)
    except (ValueError,TypeError,RecursionError): return {"status":"blocked","reason":"invalid proposal"}
    pilot=InvoicePilot()
    try: return pilot.propose(canonical)
    finally: pilot.close()
