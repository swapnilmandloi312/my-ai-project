"""Local product discovery; no external data, model or actions."""
import argparse,json
from pathlib import Path
CATALOG=Path(__file__).with_name("catalog.json")
def load():return json.loads(CATALOG.read_text(encoding="utf-8"))
def search(catalog,industry=None,audience=None,risk=None):
    q=audience.casefold() if audience else None
    return [p for p in catalog["products"] if (industry is None or p["industry"]==industry) and (q is None or any(q in a.casefold() for a in p["audience"])) and (risk is None or p["risk"]==risk)]
def main():
    p=argparse.ArgumentParser(description="Discover planned Swapnil AI Labs applications")
    p.add_argument("--industry");p.add_argument("--audience");p.add_argument("--risk",choices=["low","medium","high"]);a=p.parse_args()
    print(json.dumps(search(load(),a.industry,a.audience,a.risk),indent=2,ensure_ascii=False))
if __name__=="__main__":main()
