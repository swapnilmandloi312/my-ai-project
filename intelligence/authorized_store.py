"""Persistent synthetic invoice read boundary; trusted host grants one-use scoped capabilities."""
import sqlite3,secrets,hashlib,time,json
from pathlib import Path
class AuthorizedStore:
    def __init__(self,path):
        self.db=sqlite3.connect(path,timeout=5,isolation_level=None)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS invoices(tenant TEXT,id TEXT,amount INTEGER,PRIMARY KEY(tenant,id));
        CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,tenant TEXT,remaining INTEGER,expires INTEGER);
        CREATE TABLE IF NOT EXISTS grants(digest TEXT PRIMARY KEY,session TEXT,invoice TEXT,expires INTEGER,used INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,session TEXT,decision TEXT,reason TEXT,ts INTEGER);
        INSERT OR IGNORE INTO invoices VALUES('demo','INV-001',12500),('other','INV-001',99999);
        """)
    def create_session(self,tenant,budget,expires,now):
        if tenant not in {"demo","other"} or type(budget) is not int or budget<0 or expires<=now: raise ValueError("invalid session")
        sid=secrets.token_hex(16)
        self.db.execute("INSERT INTO sessions VALUES(?,?,?,?)",(sid,tenant,budget,expires));return sid
    def grant(self,sid,invoice,expires,now):
        # Trusted host only; no public endpoint exposes this function.
        s=self.db.execute("SELECT expires FROM sessions WHERE id=?",(sid,)).fetchone()
        if not s or not now<expires<=s[0] or type(invoice) is not str or not invoice.startswith("INV-") or len(invoice)>32: raise ValueError("invalid grant")
        token=secrets.token_urlsafe(32); digest=hashlib.sha256(token.encode()).hexdigest()
        self.db.execute("INSERT INTO grants(digest,session,invoice,expires) VALUES(?,?,?,?)",(digest,sid,invoice,expires));return token
    def read(self,sid,token,proposal,now=None):
        now=int(time.time()) if now is None else now
        self.db.execute("BEGIN IMMEDIATE")
        try:
            def finish(ok,reason,output=None):
                self.db.execute("INSERT INTO audit(session,decision,reason,ts) VALUES(?,?,?,?)",(sid if type(sid) is str else "", "allow" if ok else "deny",reason,now))
                self.db.commit();return {"allowed":ok,"reason":reason,"output":output}
            if type(sid) is not str or type(token) is not str or len(token)>128 or type(proposal) is not dict or set(proposal)!={"action","invoice"} or proposal["action"]!="lookup_invoice" or type(proposal["invoice"]) is not str: return finish(False,"invalid proposal")
            s=self.db.execute("SELECT tenant,remaining,expires FROM sessions WHERE id=?",(sid,)).fetchone()
            if not s or s[2]<=now:return finish(False,"invalid or expired session")
            g=self.db.execute("SELECT session,invoice,expires,used FROM grants WHERE digest=?",(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
            if not g or g[0]!=sid or g[1]!=proposal["invoice"] or g[2]<=now or g[3]:return finish(False,"invalid expired or consumed grant")
            if s[1]<1:return finish(False,"budget exhausted")
            self.db.execute("UPDATE grants SET used=1 WHERE digest=?",(hashlib.sha256(token.encode()).hexdigest(),))
            self.db.execute("UPDATE sessions SET remaining=remaining-1 WHERE id=?",(sid,))
            row=self.db.execute("SELECT amount FROM invoices WHERE tenant=? AND id=?",(s[0],g[1])).fetchone()
            return finish(True,"authorized synthetic read",{"amount_cents":row[0]} if row else None)
        except BaseException:
            self.db.rollback();raise
    def close(self):self.db.close()
