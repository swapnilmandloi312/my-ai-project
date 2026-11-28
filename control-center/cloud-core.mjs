export const evidenceContracts=Object.freeze({
  ...Object.fromEntries(["architecture","automation","backend","devops","engineering","frontend","quality","technical_writing"].map(category=>[category,"source_revision"])),
  research:"doi",
  ...Object.fromEntries(["security","privacy","compliance","it_ops","observability","incident_response","integration"].map(category=>[category,"snapshot"]))
});
export function validateConfig(c){if(!c||typeof c.url!=="string"||!/^https:\/\/[a-z0-9]+\.supabase\.co$/.test(c.url)||typeof c.key!=="string"||!/^sb_publishable_[A-Za-z0-9_-]+$/.test(c.key))throw Error("Cloud configuration unavailable");return c}
export function cloudClient(config,fetcher=fetch){const c=validateConfig(config);async function call(path,body,token){const headers={"apikey":c.key,"Content-Type":"application/json"};if(token)headers.Authorization="Bearer "+token;const r=await fetcher(c.url+path,{method:"POST",headers,body:JSON.stringify(body),cache:"no-store",credentials:"omit",redirect:"error"});if(!r.ok)throw Error(r.status===401||r.status===403?"Access denied or session expired":"Cloud request failed");if(r.status===204)return null;return r.json()}return {async signIn(email,password){const r=await call("/auth/v1/token?grant_type=password",{email,password});if(typeof r?.access_token!=="string"||!r.access_token)throw Error("No session returned");return r.access_token},async snapshot(token){if(!token)throw Error("Sign in first");const r=await call("/rest/v1/rpc/sal_workspace_snapshot",{p_slug:"swapnil-ai-labs"},token);if(!r||typeof r.workspace!=="string"||!Array.isArray(r.tasks)||!Array.isArray(r.reports))throw Error("No approved workspace membership");return r},async jobCommand(token,action,args={}){if(!token)throw Error("Sign in first");if(!["snapshot","submit","approve","configure","agent_pause"].includes(action))throw Error("Unknown job command");const r=await call("/rest/v1/rpc/sal_job_command",{p_slug:"swapnil-ai-labs",p_action:action,p_args:args},token);if(!r||typeof r!=="object")throw Error("Invalid queue response");if(action==="snapshot"&&(!["founder","operator","viewer"].includes(r.role)||!Array.isArray(r.jobs)||!Array.isArray(r.events)||!Array.isArray(r.profiles)||!r.limits))throw Error("Invalid queue snapshot");return r},async approveEvidenceBatch(token,ids){
if(!token)throw Error("Sign in first");
if(!Array.isArray(ids)||ids.length<1||ids.length>8||new Set(ids).size!==ids.length||
   ids.some(id=>typeof id!=="string"||!/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(id)))
  throw Error("Enter one to eight distinct job UUIDs");
const result=await call("/rest/v1/rpc/sal_approve_readonly_evidence_batch",{
 p_slug:"swapnil-ai-labs",p_jobs:ids
},token);
if(!Array.isArray(result)||result.length!==ids.length)throw Error("Invalid batch response");
return result;
},async submitEngineeringEvidence(token,revision){
return this.submitEvidence(token,"engineering",revision);
},async submitEvidence(token,category,input){
if(!token)throw Error("Sign in first");
if(!Object.hasOwn(evidenceContracts,category))throw Error("Unsupported evidence category");
const field=evidenceContracts[category];
let value=input;
if(field==="source_revision"&&!/^[0-9a-f]{40}$/.test(value))throw Error("Enter a full GitHub commit SHA");
if(field==="doi"){
  if(typeof value!=="string"||value.length>79||!/^10\.[0-9]{4,9}\/[-._;()/:A-Z0-9]+$/i.test(value))throw Error("Enter a valid DOI of up to 79 characters");
  value=value.toLowerCase();
}
if(field==="snapshot")value="workspace";
const id=await call("/rest/v1/rpc/sal_submit_evidence_job",{
  p_slug:"swapnil-ai-labs",p_category:category,
  p_key:category+":"+(field==="snapshot"?new Date().toISOString().slice(0,13):value),
  p_refs:{[field]:value}
},token);
if(typeof id!=="string"||!/^[0-9a-f-]{36}$/.test(id))throw Error("Invalid evidence job ID");
return id;
},async deliverables(token){
if(!token)throw Error("Sign in first");
const rows=await call("/rest/v1/rpc/sal_agent_deliverable_index",{p_slug:"swapnil-ai-labs"},token);
if(!Array.isArray(rows)||rows.some(row=>!row||["job_id","category","tool","stored_at"].some(key=>typeof row[key]!=="string")))throw Error("Invalid deliverable index");
return rows;
},async authorizeEngineeringSchedule(token,{key,template,dependency,interval,occurrences,hours}){
if(!token)throw Error("Sign in first");
const uuid=/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
if(!/^[a-zA-Z0-9_-]{1,64}$/.test(key)||!uuid.test(template)||(dependency&&!uuid.test(dependency))
||!Number.isInteger(interval)||interval<1||interval>168
||!Number.isInteger(occurrences)||occurrences<1||occurrences>24
||!Number.isInteger(hours)||hours<1||hours>24)throw Error("Invalid schedule or authorization limits");
const id=await call("/rest/v1/rpc/sal_evidence_schedule",{
p_slug:"swapnil-ai-labs",p_key:key,p_template:template,p_dependency:dependency||null,p_interval_hours:interval
},token);
if(typeof id!=="string"||!uuid.test(id))throw Error("Invalid schedule response");
const accepted=await call("/rest/v1/rpc/sal_set_recurring_evidence_approval",{
p_slug:"swapnil-ai-labs",p_key:key,p_occurrences:occurrences,p_hours:hours
},token);
if(accepted!==true)throw Error("Schedule exists but authorization was declined");
return id;
},async revokeScheduleApproval(token,key){
if(!token)throw Error("Sign in first");
const accepted=await call("/rest/v1/rpc/sal_set_recurring_evidence_approval",{
p_slug:"swapnil-ai-labs",p_key:key,p_occurrences:0,p_hours:null
},token);
if(accepted!==true)throw Error("No enabled founder schedule matched");
},async schedules(token){
if(!token)throw Error("Sign in first");
const rows=await call("/rest/v1/rpc/sal_evidence_schedule_index",{p_slug:"swapnil-ai-labs"},token);
if(!Array.isArray(rows)||rows.some(row=>!row||typeof row.schedule_key!=="string"||typeof row.category!=="string"||typeof row.enabled!=="boolean"||typeof row.next_due!=="string"||!Number.isInteger(row.interval_hours)))throw Error("Invalid schedule index");
return rows;
},async logout(token){if(token)await call("/auth/v1/logout?scope=local",{},token)}}}
