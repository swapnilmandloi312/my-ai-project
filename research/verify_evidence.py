"""Aggregate the committed synthetic evidence, fail if documented counts disagree."""
import json
from pathlib import Path
from collections import Counter
rows=[json.loads(x) for x in (Path(__file__).parent/'raw-results.jsonl').read_text().splitlines()]
assert Counter(r['track'] for r in rows)=={'gateway':144,'context':360,'memory':120,'intent':120,'routing':600}
g=[r for r in rows if r['track']=='gateway']; assert sum(not r['expected'] and r['allowlist'] for r in g)==89; assert sum(not r['expected'] and r['gateway'] for r in g)==0; assert sum(r['expected'] and r['gateway'] for r in g)==7
for method,hits,words in [('full',120,11280),('first4',27,2826),('lexical4',118,2644)]:
    q=[r for r in rows if r['track']=='context' and r['method']==method]; assert sum(r['hit'] for r in q)==hits; assert sum(r['words'] for r in q)==words
m=[r for r in rows if r['track']=='memory']; assert sum(r['scoped']==r['expected'] for r in m)==120; assert sum(r['latest']==r['expected'] for r in m)==0
i=[r for r in rows if r['track']=='intent'];assert sum(r['learned']==r['expected'] for r in i)==70;assert sum(r['keyword']==r['expected'] for r in i)==110
for method,n,c in [('cheap',149,200),('strong',191,1000),('heuristic',184,572)]:
    q=[r for r in rows if r['track']=='routing' and r['method']==method]; assert sum(r['success'] for r in q)==n;assert sum(r['cost_units'] for r in q)==c
print('Verified 1,344 committed synthetic evidence records across five tracks. Not independent evaluation.')
