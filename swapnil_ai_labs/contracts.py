"""Stable, versioned proposal envelope; caller identity is never taken from model output."""
import json
from dataclasses import dataclass
from swapnil_ai_labs import CONTRACT_VERSION

def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise ValueError("duplicate key")
        result[key]=value
    return result

def nonfinite(_): raise ValueError("non-finite JSON")

@dataclass(frozen=True)
class Proposal:
    action:str
    invoice:str
    def payload(self): return {"action":self.action,"invoice":self.invoice}

def decode(raw):
    if type(raw) is not str or len(raw)>4096: raise ValueError("invalid payload")
    obj=json.loads(raw,object_pairs_hook=unique,parse_constant=nonfinite)
    if type(obj) is not dict or set(obj)!={"version","action","invoice"}: raise ValueError("unexpected fields")
    if obj["version"]!=CONTRACT_VERSION: raise ValueError("unsupported contract version")
    if obj["action"]!="lookup_invoice": raise ValueError("unsupported action")
    invoice=obj["invoice"]
    if type(invoice) is not str or not invoice.startswith("INV-") or not 4<len(invoice)<=32 or not all(c.isascii() and (c.isalnum() or c=="-") for c in invoice): raise ValueError("invalid invoice")
    return Proposal(obj["action"],invoice)
