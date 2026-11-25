"""Versioned local message exchange, trusted host owns the sender identity."""
import sqlite3,json,time
class AgentMailbox:
    def __init__(self,path=":memory:"):
        self.db=sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS messages(tenant TEXT,id TEXT,sender TEXT,recipient TEXT,kind TEXT,payload TEXT,expires INTEGER,PRIMARY KEY(tenant,id))")
    def send(self,tenant,authenticated_sender,allowed_recipients,envelope,now=None):
        now=int(time.time()) if now is None else now
        if type(envelope) is not dict or set(envelope)!={"version","id","recipient","kind","payload","expires"}:raise ValueError("invalid envelope")
        v=envelope
        if v["version"]!="1.0" or v["kind"] not in ("task","result") or not all(type(x) is str and 0<len(x)<=128 for x in (tenant,authenticated_sender,v["id"],v["recipient"])) or v["recipient"] not in allowed_recipients or type(v["expires"]) is not int or not now<v["expires"]<=now+3600:raise ValueError("invalid scope or expiry")
        body=json.dumps(v["payload"],allow_nan=False,separators=(",",":"))
        if len(body)>4096:raise ValueError("payload too large")
        try:
            with self.db:self.db.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?)",(tenant,v["id"],authenticated_sender,v["recipient"],v["kind"],body,v["expires"]))
        except sqlite3.IntegrityError:raise ValueError("duplicate message") from None
    def inbox(self,tenant,authenticated_recipient,now=None):
        now=int(time.time()) if now is None else now
        rows=self.db.execute("SELECT id,sender,kind,payload FROM messages WHERE tenant=? AND recipient=? AND expires>? ORDER BY id",(tenant,authenticated_recipient,now)).fetchall()
        return [{"id":i,"sender":s,"kind":k,"payload":json.loads(p)} for i,s,k,p in rows]
    def close(self):self.db.close()
