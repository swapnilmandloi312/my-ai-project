"""In-memory scoped graph of host-attested facts, bounded traversal and provenance."""
from collections import deque
class KnowledgeGraph:
    def __init__(self):self.edges={}
    def add(self,tenant,subject,predicate,obj,evidence):
        if not all(type(x) is str and x and len(x)<=256 for x in (tenant,subject,predicate,obj,evidence)):raise ValueError("invalid fact")
        self.edges.setdefault(tenant,set()).add((subject,predicate,obj,evidence))
    def traverse(self,tenant,start,max_depth=2,max_edges=50):
        if type(max_depth) is not int or not 0<=max_depth<=5 or type(max_edges) is not int or not 0<=max_edges<=1000:raise ValueError("invalid graph limits")
        q=deque([(start,0)]);visited={start};out=[]
        edges=sorted(self.edges.get(tenant,()))
        while q and len(out)<max_edges:
            node,depth=q.popleft()
            if depth>=max_depth:continue
            for s,p,o,e in edges:
                if s!=node:continue
                out.append({"subject":s,"predicate":p,"object":o,"evidence":e})
                if o not in visited:visited.add(o);q.append((o,depth+1))
                if len(out)>=max_edges:break
        return out
