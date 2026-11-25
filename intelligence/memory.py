"""Tenant-scoped memory prototype. Tenant identity is supplied by trusted host."""
import sqlite3, time
class Memory:
    def __init__(self,path=":memory:"):
        self.db=sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS memory(tenant TEXT, key TEXT, value TEXT, source TEXT, expires INTEGER, updated INTEGER, PRIMARY KEY(tenant,key))")
    def put(self,tenant,key,value,source,expires,now=None):
        now=int(time.time()) if now is None else now
        if not all(type(x) is str and x for x in (tenant,key,value,source)) or source not in {"verified_host","user_confirmed"} or type(expires) is not int or expires<=now: raise ValueError("untrusted or expired memory")
        with self.db:
            self.db.execute("INSERT INTO memory VALUES(?,?,?,?,?,?) ON CONFLICT(tenant,key) DO UPDATE SET value=excluded.value,source=excluded.source,expires=excluded.expires,updated=excluded.updated WHERE excluded.updated>=memory.updated",(tenant,key,value,source,expires,now))
    def get(self,tenant,key,now=None):
        now=int(time.time()) if now is None else now
        r=self.db.execute("SELECT value,source FROM memory WHERE tenant=? AND key=? AND expires>?",(tenant,key,now)).fetchone()
        return {"value":r[0],"source":r[1]} if r else None
    def forget(self,tenant,key):
        with self.db: self.db.execute("DELETE FROM memory WHERE tenant=? AND key=?",(tenant,key))
    def close(self): self.db.close()
