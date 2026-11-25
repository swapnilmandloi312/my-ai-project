"""Tenant-scoped exact cache plus lexical near-match suggestions. Never auto-reuse approximate answers."""
import json,hashlib,time,math
from intelligence.context import tokens
class SemanticCache:
    def __init__(self): self.rows={}
    @staticmethod
    def key(tenant,model,policy,corpus,prompt):
        values=[tenant,model,policy,corpus,prompt]
        if not all(type(x) is str and x for x in values):raise ValueError("missing cache scope")
        return hashlib.sha256(json.dumps(values,separators=(",",":")).encode()).hexdigest()
    def put(self,tenant,model,policy,corpus,prompt,answer,expires,now=None):
        now=time.time() if now is None else now
        if type(answer) is not str or not math.isfinite(expires) or expires<=now:raise ValueError("invalid cache entry")
        k=self.key(tenant,model,policy,corpus,prompt);self.rows[k]=(tenant,model,policy,corpus,prompt,answer,expires)
    def get(self,tenant,model,policy,corpus,prompt,now=None):
        now=time.time() if now is None else now
        r=self.rows.get(self.key(tenant,model,policy,corpus,prompt))
        return r[5] if r and r[6]>now else None
    def suggest(self,tenant,model,policy,corpus,prompt,minimum=.8,now=None):
        now=time.time() if now is None else now
        self.key(tenant,model,policy,corpus,prompt)
        if not 0<=minimum<=1:raise ValueError("invalid threshold")
        q=set(tokens(prompt)); found=[]
        for k,r in self.rows.items():
            if r[:4]!=(tenant,model,policy,corpus) or r[6]<=now:continue
            t=set(tokens(r[4])); score=len(q&t)/len(q|t) if q|t else 0
            if score>=minimum:found.append({"entry_id":k,"similarity":score,"requires_review":True})
        return sorted(found,key=lambda x:(-x["similarity"],x["entry_id"]))
