import json,tempfile
from pathlib import Path
from intelligence.authorized_store import AuthorizedStore
from intelligence.memory import Memory
from intelligence.routing import Candidate
from swapnil_ai_labs.platform import ResearchPlatform,HostRequest,fixture_provider
def main():
    with tempfile.TemporaryDirectory() as tmp:
        store=AuthorizedStore(str(Path(tmp)/"demo.db")); memory=Memory()
        try:
            sid=store.create_session("demo",1,100,10);grant=store.grant(sid,"INV-001",90,10)
            req=HostRequest(sid,"demo","INV-001",grant)
            memory.put("demo","display_format","cents","user_confirmed",90,10)
            result=ResearchPlatform(store,memory).run(req,"invoice amount",[{"text":"invoice amount documentation"},{"text":"marketing overview"}],[Candidate("fixture",1,.95,10)],fixture_provider,now=11)
            print(json.dumps(result,indent=2))
            assert result["output"]=={"amount_cents":12500}
        finally:store.close();memory.close()
if __name__=="__main__":main()
