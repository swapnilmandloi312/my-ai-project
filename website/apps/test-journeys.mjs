import assert from "node:assert/strict";
import {journeys,route,execute} from "./journeys.mjs";
for(const j of journeys){const r=execute(j.id,j.sample);assert.ok(r.metrics.length&&r.sections.length&&r.limit);assert.throws(()=>execute(j.id,{}));}
assert.deepEqual(route("I have an exam"),["learn"]);assert.deepEqual(route("मुझे पढ़ाई करनी है"),["learn"]);assert.deepEqual(route("xyz"),[]);assert.deepEqual(route("exam invoice"),["learn","business"]);
assert.equal(execute("business",journeys[1].sample).metrics[2][1],"INR 19000.00");
assert.equal(execute("developer",journeys[3].sample).metrics[2][1],"BLOCK");
assert.throws(()=>execute("developer",{cases:"a,1,1,1\na,0,0,0"}),/unique/);
assert.throws(()=>execute("learn",{topics:"A\nB",days:"1",minutes:"15"}),/Not enough/);
assert.throws(()=>execute("business",{sales:"x,-1",expenses:"x,2",currency:"INR"}));
assert.match(execute("document",journeys[2].sample).sections[0].items.join(" "),/\[3\].*deposit/);
assert.equal(execute("research",journeys[4].sample).metrics[0][1],"1");
assert.throws(()=>execute("research",{question:"q",evidence:"A | verified | note",limits:"x"}));
console.log("5 guided workflows, validation, routing ambiguity, evidence provenance and calculations passed.");
