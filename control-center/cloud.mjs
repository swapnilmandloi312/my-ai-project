import {cloudClient} from "./cloud-core.mjs?v=founder-form-2";import config from "./cloud-config.mjs?v=founder-form-2";import {renderQueue,clearQueue} from "./queue-ui.mjs?v=founder-form-2";
const $=id=>document.getElementById(id);let client,token="",busy=false;
function note(s){$("notice").textContent=s}function clear(){token="";$("engineering-evidence").hidden=true;$("engineering-evidence").reset();$("founder-action-status").textContent="";clearQueue();$("workspace").hidden=true;$("cloud-tasks").replaceChildren();$("cloud-reports").replaceChildren();$("cloud-deliverables").replaceChildren();$("deliverable-status").textContent="";$("cloud-schedules").replaceChildren();$("schedule-status").textContent=""}function controls(){ $("signin").disabled=busy||!!token||!client;$("refresh-cloud").disabled=busy||!token;$("signout").disabled=busy||!token}
function render(s){$("workspace-title").textContent=s.workspace+" · "+s.role;$("counts").textContent=s.profiles+" profiles · "+s.paused+" cloud controls paused · "+s.tasks.length+" tasks";for(const [id,rows,format] of [["cloud-tasks",s.tasks,t=>[t.title,t.priority+" · "+t.status]],["cloud-reports",s.reports,r=>[r.source+" · "+r.status,JSON.stringify(r.summary)]]]){const root=$(id);root.replaceChildren();for(const item of rows){const d=document.createElement("article");d.className="gate";const [a,b]=format(item);const h=document.createElement("strong");h.textContent=a;const p=document.createElement("span");p.textContent=b;d.append(h,p);root.append(d)}}$("workspace").hidden=false}
async function renderDeliverables(){
  const root=$("cloud-deliverables");
  root.replaceChildren();
  try{
    const rows=await client.deliverables(token);
    $("deliverable-status").textContent=rows.length ? "" : "No evidence deliverables recorded.";
    for(const row of rows){
      const article=document.createElement("article");
      article.className="gate";
      const title=document.createElement("strong");
      title.textContent=row.category+" · "+row.tool;
      const detail=document.createElement("span");
      detail.textContent=row.stored_at+" · Job "+row.job_id;
      article.append(title,detail);
      root.append(article);
    }
  }catch(e){
    $("deliverable-status").textContent="Deliverable index unavailable: "+e.message;
  }
}
async function renderSchedules(){
  const root=$("cloud-schedules");
  const status=$("schedule-status");
  root.replaceChildren();
  try{
    const rows=await client.schedules(token);
    status.textContent=rows.length ? "" : "No delegation schedules recorded.";
    for(const row of rows){
      const article=document.createElement("article");
      article.className="gate";
      const title=document.createElement("strong");
      title.textContent=row.schedule_key+" · "+row.category;
      const parts=[row.enabled ? "Due "+row.next_due+" · Every "+row.interval_hours+"h" : "Disabled"];
      if(row.depends_on_job)parts.push("Dependency "+row.depends_on_job+" ("+(row.dependency_state||"unknown")+")");
      if(row.last_job)parts.push("Latest job "+row.last_job);
      const detail=document.createElement("span");
      detail.textContent=parts.join(" · ");
      article.append(title,detail);
      root.append(article);
    }
  }catch(e){
    status.textContent="Schedule index unavailable: "+e.message;
  }
}
async function refresh(){
  const snapshot=await client.snapshot(token);
  render(snapshot);
  $("engineering-evidence").hidden=!(config.queueEnabled===true && snapshot.role==="founder");
  $("founder-action-status").textContent=config.queueEnabled!==true?"Job submissions are disabled for this deployment.":snapshot.role!=="founder"?"Engineering submissions require founder access.":"";
await Promise.all([renderDeliverables(),renderSchedules()]);if(config?.queueEnabled===true){try{await renderQueue(client,token,act)}catch(e){clearQueue();note("Private report loaded; job queue unavailable: "+e.message)}}}
async function act(fn){if(busy)return;busy=true;controls();try{await fn()}catch(e){clear();note(e.message)}finally{busy=false;controls()}}
$("engineering-evidence").onsubmit=e=>{
  e.preventDefault();
  if($("engineering-evidence").hidden)return;
  const revision=$("engineering-revision").value.trim();
  act(async()=>{
    const id=await client.submitEngineeringEvidence(token,revision);
    await refresh();
    $("founder-action-status").textContent="Job "+id+" submitted for separate approval.";
  });
};
try{client=cloudClient(config);note("Sign in with your approved application account.")}catch(e){note(e.message)}
$("login").addEventListener("submit",e=>{e.preventDefault();act(async()=>{const password=$("password").value;$("password").value="";token=await client.signIn($("email").value,password);try{note("Authenticated private snapshot loaded.");await refresh()}catch(err){try{await client.logout(token)}catch{}throw err}})});
$("refresh-cloud").onclick=()=>act(async()=>{note("Private snapshot refreshed.");await refresh()});$("signout").onclick=()=>act(async()=>{try{await client.logout(token);note("Signed out.")}catch{note("Local session cleared; server sign-out could not be confirmed.")}finally{clear()}});controls();
