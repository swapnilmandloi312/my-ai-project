const assert=require("node:assert/strict");
const {evaluate}=require("./playground.js");
const f={action:"lookup_invoice",tenant:"demo",budget:10,evidence:2,approval:true};
assert.equal(evaluate(f).status,"SIMULATED ALLOW");
for(const v of [{tenant:"other"},{budget:0},{action:"send_email"},{action:"prepare_report",approval:false},{action:"prepare_report",evidence:1},{budget:NaN}])assert.equal(evaluate({...f,...v}).status,"BLOCKED");
assert.equal(evaluate({...f,action:"prepare_report"}).remaining_cents,7);
console.log("8 playground decision checks passed (browser UI not exercised).");
