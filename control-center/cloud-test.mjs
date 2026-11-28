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
