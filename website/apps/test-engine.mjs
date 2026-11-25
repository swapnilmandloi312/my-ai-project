import assert from "node:assert/strict";
import {catalog} from "./catalog.mjs";
import {run} from "./engine.mjs";
assert.equal(catalog.tools.length,72);
assert.equal(new Set(catalog.tools.map(t=>t.id)).size,72);
for(const t of catalog.tools){const r=run(t,t.example,t.mode==="lookup"?t.options[0]:"");assert.ok(r.text.length>0,t.id);assert.ok(r.notice,t.id);assert.throws(()=>run(t,""),/Enter/);}
const get=id=>catalog.tools.find(x=>x.id===id);
assert.match(run(get("finance-1"),"A,125.00\nB,75.00").text,/200.00/);
assert.match(run(get("finance-2"),"Travel,250\nTravel,50").text,/Travel: 300.00/);
assert.match(run(get("everyday-3"),"Income,10\nCost,15").text,/-5.00/);
assert.throws(()=>run(get("finance-1"),"A,NaN"),/label,number/);
assert.match(run(get("software-1"),"1,1,1\n0,1,0").text,/Unsafe execution rate: 100.0%/);
assert.throws(()=>run(get("software-1"),"1,0,1"),/requires/);
assert.match(run(get("software-2"),"write,read").text,/BLOCKED/);
assert.equal(run(get("education-1"),"Q|A").quiz[0].answer,"A");
assert.match(run(get("logistics-1"),"A: open","missing").text,/No matches/);
assert.match(run(get("legal-2"),"Payment due. No other detail.").text,/Payment due/);
assert.throws(()=>run(get("legal-2"),"x".repeat(20001)),/Input limit/);
console.log("72 sample execution + 72 empty-input checks + 11 behavioral assertions passed.");
