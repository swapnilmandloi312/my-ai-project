"""Explicitly synthetic staging seed; never run against an existing production DB."""
import json,os,time
from pathlib import Path
from secure_service.service import Service,Principal,CATEGORIES
if os.environ.get("SWAPNIL_AI_LABS_STAGING")!="1":raise SystemExit("synthetic staging mode required")
p=Path(os.environ["SWAPNIL_AI_LABS_DB"])
if p.exists():raise SystemExit("refusing to overwrite an existing database")
cfg=json.loads(os.environ["SWAPNIL_AI_LABS_PRINCIPALS"])
principals=[Principal(x["id"],x["tenant"],x["token_hash"],frozenset(x["categories"]),x.get("limit",60),x.get("budget",100)) for x in cfg]
s=Service(p,principals,bytes.fromhex(os.environ["SWAPNIL_AI_LABS_AUDIT_KEY"]))
for principal in principals:
    for category in sorted(principal.categories):
        s.seed_record(principal.tenant,category,category+"-001",{"synthetic":True,"category":category,"value":100 if principal.tenant=="tenant-a" else 900},[principal.id])
print("Synthetic staging records provisioned.")
