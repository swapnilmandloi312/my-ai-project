"""Immutable content fingerprints and detached audit checkpoints (local primitives)."""
import hashlib,hmac
from secure_service.service import canonical,valid_id
def fingerprint(data):
    if type(data) is not bytes or not 0<len(data)<=10*1024*1024:raise ValueError("invalid evidence bytes")
    return hashlib.sha256(data).hexdigest()
def manifest(tenant,reference,source,version,data):
    if not all(valid_id(x) for x in (tenant,reference,source,version)):raise ValueError("invalid metadata")
    return {"tenant":tenant,"reference":reference,"source":source,"version":version,"sha256":fingerprint(data),"bytes":len(data)}
def verify_manifest(expected,tenant,reference,source,version,data):
    try:return hmac.compare_digest(canonical(expected),canonical(manifest(tenant,reference,source,version,data)))
    except (TypeError,ValueError):return False
def checkpoint(service,anchor_key):
    """Snapshot after verifying chain; store result in independent trusted storage."""
    if type(anchor_key) is not bytes or len(anchor_key)<32:raise ValueError("anchor key")
    db=service.connect()
    try:
        db.execute("BEGIN")
        rows=db.execute("SELECT seq,event,mac FROM audit ORDER BY seq").fetchall()
        prev="0"*64
        for i,(seq,event,mac) in enumerate(rows,1):
            if seq!=i or not hmac.compare_digest(mac,hmac.new(service.key,(prev+"\n"+event).encode(),hashlib.sha256).hexdigest()):raise ValueError("audit invalid")
            prev=mac
        body={"sequence":len(rows),"head":prev}
        return {"body":body,"mac":hmac.new(anchor_key,canonical(body).encode(),hashlib.sha256).hexdigest()}
    finally:db.close()
def verify_checkpoint(service,anchor_key,anchor):
    """Verifies current chain includes the previously recorded head (not just its length)."""
    try:
        if type(anchor_key) is not bytes or len(anchor_key)<32:return False
        body=anchor["body"];mac=anchor["mac"];n=body["sequence"]
        if type(n) is not int or n<0 or not hmac.compare_digest(mac,hmac.new(anchor_key,canonical(body).encode(),hashlib.sha256).hexdigest()):return False
        db=service.connect()
        try:
            db.execute("BEGIN")
            prev="0"*64;head=prev if n==0 else None
            rows=db.execute("SELECT seq,event,mac FROM audit ORDER BY seq").fetchall()
            for i,(seq,event,eventmac) in enumerate(rows,1):
                if i!=seq or not hmac.compare_digest(eventmac,hmac.new(service.key,(prev+"\n"+event).encode(),hashlib.sha256).hexdigest()):return False
                prev=eventmac
                if i==n:head=prev
            return head is not None and hmac.compare_digest(head,body["head"])
        finally:db.close()
    except (TypeError,ValueError,KeyError):return False
