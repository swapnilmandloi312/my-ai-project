import assert from "node:assert/strict";import {cloudClient,validateConfig} from "./cloud-core.mjs";
const c={url:"https://example.supabase.co",key:"sb_publishable_test"};assert.throws(()=>validateConfig({...c,key:"sb_secret_bad"}));assert.throws(()=>validateConfig({...c,url:"https://evil.example"}));assert.throws(()=>validateConfig(null));let calls=[];const fake=async(u,o)=>{calls.push([u,o]);return {ok:true,status:200,json:async()=>u.includes("token?")?{access_token:"fixture"}:u.includes("logout")?{}:{workspace:"Demo",tasks:[],reports:[]}}};const api=cloudClient(c,fake);await assert.rejects(()=>api.snapshot(""));const token=await api.signIn("a@example.invalid","fixture-pass");assert.equal(token,"fixture");await api.snapshot(token);await api.logout(token);assert.equal(calls.length,3);assert.equal(calls[1][1].headers.Authorization,"Bearer fixture");assert.equal(calls[1][1].redirect,"error");const denied=cloudClient(c,async()=>({ok:false,status:403}));await assert.rejects(()=>denied.snapshot(token),/Access denied/);const noMembership=cloudClient(c,async()=>({ok:true,status:200,json:async()=>null}));await assert.rejects(()=>noMembership.snapshot(token),/membership/);console.log("Cloud client tests passed");

const queueCalls=[];const queue=cloudClient(c,async(u,o)=>{queueCalls.push([u,o]);return {ok:true,status:200,json:async()=>({role:"founder",limits:{stopped:true},profiles:[],jobs:[],events:[]})}});await assert.rejects(()=>queue.jobCommand("","snapshot"));await assert.rejects(()=>queue.jobCommand(token,"arbitrary"));assert.equal((await queue.jobCommand(token,"snapshot")).role,"founder");await queue.jobCommand(token,"approve",{id:"fixture"});assert.equal(queueCalls[1][0],c.url+"/rest/v1/rpc/sal_job_command");assert.equal(queueCalls[1][1].headers.Authorization,"Bearer fixture");assert.equal(JSON.parse(queueCalls[1][1].body).p_action,"approve");await assert.rejects(()=>noMembership.jobCommand(token,"snapshot"));console.log("Synthetic queue client tests passed");

const deliverableApi=cloudClient(c,async(u,o)=>{
  assert.equal(u,c.url+"/rest/v1/rpc/sal_agent_deliverable_index");
  assert.equal(o.headers.Authorization,"Bearer fixture");
  assert.equal(o.cache,"no-store");
  return {ok:true,status:200,json:async()=>[{job_id:"fixture-job",category:"research",tool:"research_export",stored_at:"2026-11-28T00:00:00Z"}]};
});
await assert.rejects(()=>deliverableApi.deliverables(""),/Sign in/);
assert.equal((await deliverableApi.deliverables(token))[0].job_id,"fixture-job");
await assert.rejects(()=>noMembership.deliverables(token),/Invalid deliverable index/);
console.log("Authenticated deliverable index tests passed");

const scheduleApi=cloudClient(c,async(u,o)=>{
  assert.equal(u,c.url+"/rest/v1/rpc/sal_evidence_schedule_index");
  assert.equal(o.headers.Authorization,"Bearer fixture");
  return {ok:true,status:200,json:async()=>[{schedule_key:"engineering-hourly",category:"engineering",enabled:true,interval_hours:1,next_due:"2026-11-28T00:00:00Z",last_job:"fixture-job",dependency_state:"succeeded"}]};
});
await assert.rejects(()=>scheduleApi.schedules(""),/Sign in/);
assert.equal((await scheduleApi.schedules(token))[0].last_job,"fixture-job");
await assert.rejects(()=>noMembership.schedules(token),/Invalid schedule index/);
console.log("Authenticated schedule index tests passed");

const revision="a".repeat(40), jobId="11111111-0000-4000-8000-111111111111";
const evidenceApi=cloudClient(c,async(u,o)=>{
  assert.equal(u,c.url+"/rest/v1/rpc/sal_submit_evidence_job");
  assert.equal(o.headers.Authorization,"Bearer fixture");
  assert.deepEqual(JSON.parse(o.body),{p_slug:"swapnil-ai-labs",p_category:"engineering",
    p_key:"engineering:"+revision,p_refs:{source_revision:revision}});
  return {ok:true,status:200,json:async()=>jobId};
});
await assert.rejects(()=>evidenceApi.submitEngineeringEvidence("",revision),/Sign in/);
await assert.rejects(()=>evidenceApi.submitEngineeringEvidence(token,"main"),/commit SHA/);
assert.equal(await evidenceApi.submitEngineeringEvidence(token,revision),jobId);

const {readFile}=await import("node:fs/promises");
const elements=new Map();
globalThis.document={
  getElementById(id){
    if(!elements.has(id))elements.set(id,{hidden:true,value:"",textContent:"",
      replaceChildren(){},addEventListener(name,callback){this[name]=callback}});
    return elements.get(id);
  }
};
let role="founder";
globalThis.fetch=async url=>{
  const result=url.includes("/token?")?{access_token:"fixture"}:
    url.endsWith("sal_workspace_snapshot")?{workspace:"Demo",role,tasks:[],reports:[]}:[];
  return {ok:true,status:200,json:async()=>result};
};
const source=(await readFile(new URL("./cloud.mjs",import.meta.url),"utf8"))
  .replace(/"\.\/cloud-core\.mjs[^"]*"/,JSON.stringify(new URL("./cloud-core.mjs",import.meta.url).href))
  .replace(/import config from "[^"]+";/,"const config="+JSON.stringify({...c,queueEnabled:true})+";")
  .replace(/import \{renderQueue,clearQueue\} from "[^"]+";/,
    "const renderQueue=async()=>{throw Error('Queue unavailable')}; const clearQueue=()=>{};");
await import("data:text/javascript;base64,"+Buffer.from(source).toString("base64"));
const tick=()=>new Promise(resolve=>setImmediate(resolve));
document.getElementById("login").submit({preventDefault(){}});
await tick();
assert.equal(document.getElementById("engineering-evidence").hidden,false);
assert.match(document.getElementById("notice").textContent,/Queue unavailable/);
role="viewer";
document.getElementById("refresh-cloud").onclick();
await tick();
assert.equal(document.getElementById("engineering-evidence").hidden,true);

const policyCalls=[];
const policyApi=cloudClient(c,async(u,o)=>{
 policyCalls.push([u,JSON.parse(o.body)]);
 return {ok:true,status:200,json:async()=>policyCalls.length===1?jobId:true};
});
const policy={key:"engineering-repeat",template:jobId,dependency:"",interval:1,occurrences:2,hours:3};
await assert.rejects(()=>policyApi.authorizeEngineeringSchedule(token,{...policy,occurrences:25}),/limits/);
assert.equal(policyCalls.length,0);
assert.equal(await policyApi.authorizeEngineeringSchedule(token,policy),jobId);
assert.equal(policyCalls[0][1].p_dependency,null);
assert.equal(policyCalls[1][1].p_occurrences,2);
await policyApi.revokeScheduleApproval(token,policy.key);
assert.equal(policyCalls[2][1].p_occurrences,0);

const intakeCalls=[];
const intake=cloudClient(c,async(u,o)=>{
  intakeCalls.push(JSON.parse(o.body));
  return {ok:true,status:200,json:async()=>jobId};
});
await intake.submitEvidence(token,"research","10.1093/MIND/LIX.236.433");
await intake.submitEvidence(token,"security","");
await intake.submitEvidence(token,"backend",revision);
assert.deepEqual(intakeCalls.map(x=>x.p_refs),[{doi:"10.1093/mind/lix.236.433"},{snapshot:"workspace"},{source_revision:revision}]);
await assert.rejects(()=>intake.submitEvidence(token,"finance",""),/Unsupported/);
await assert.rejects(()=>intake.submitEvidence(token,"research","https://example.com"),/valid DOI/);
assert.equal(intakeCalls.length,3);
