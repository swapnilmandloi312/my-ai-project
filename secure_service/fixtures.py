"""Synthetic dataset: all names, identifiers, amounts and statuses are fabricated."""
from secure_service.service import CATEGORIES,Principal,digest
TOKEN_A="fixture-only-"+"a"*40
TOKEN_B="fixture-only-"+"b"*40
def principals(limit=10000,budget=100000):
    return [Principal("reader-a","tenant-a",digest(TOKEN_A),CATEGORIES,limit,budget),Principal("reader-b","tenant-b",digest(TOKEN_B),CATEGORIES,limit,budget)]
def seed(service,n=12):
    for category in sorted(CATEGORIES):
        for i in range(n):
            rid=f"{category}-{i:03d}"
            for tenant,pid,value in [("tenant-a","reader-a",i+100),("tenant-b","reader-b",i+900)]:
                fields={"finance":{"amount_cents":value*100,"currency":"USD","status":"open"},"support":{"ticket_number":value,"priority":"normal","status":"resolved"},"operations":{"shipment_number":value,"status":"in_transit"},"knowledge":{"document_number":value,"text":"Synthetic policy reference "+str(value)}}
                payload={"synthetic":True,"category":category,"value":value,**fields[category]}
                service.seed_record(tenant,category,rid,payload,[pid] if i%2==0 else [])
def request(category,rid,request_id):
    return {"version":"1.0","request_id":request_id,"category":category,"record_id":rid,"proposal":{"version":"1.0","action":"read_record","category":category,"record_id":rid}}
