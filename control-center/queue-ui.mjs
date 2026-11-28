// Synthetic queue is opt-in via deployment config; no credentials are persisted.
const $=id=>document.getElementById(id);
const text=(tag,value)=>{const x=document.createElement(tag);x.textContent=value;return x};
const option=(value,label)=>{const x=text("option",label);x.value=value;return x};
export function clearQueue(){
 $("job-workspace").hidden=true;
 for(const id of ["job-results","job-events","job-profiles","job-category","job-parent"])$(id).replaceChildren();
}
export async function renderQueue(client,token,act){
 const s=await client.jobCommand(token,"snapshot");
 const founder=s.role==="founder",writer=founder||s.role==="operator";
 $("job-workspace").hidden=false;
 $("job-founder").hidden=!founder;$("job-submit").hidden=!writer;
 $("job-limits").textContent=(s.limits.stopped?"STOPPED":"EXECUTION ENABLED")+" · "+s.limits.attempts_used+"/"+s.limits.attempt_limit+" lifetime attempts";
 $("attempt-limit").value=s.limits.attempt_limit;
 const command=(action,args)=>act(async()=>{
   await client.jobCommand(token,action,args);await renderQueue(client,token,act);
   $("job-notice").textContent="Command accepted by server.";
 });
 $("resume-jobs").onclick=()=>{
  const n=Number($("attempt-limit").value);
  if(!Number.isInteger(n)||n<0||n>1000){$("job-notice").textContent="Invalid attempt limit";return}
  if(confirm("Enable approved execution with this lifetime budget?"))command("configure",{stopped:false,attempt_limit:n});
 };
 $("stop-jobs").onclick=()=>command("configure",{stopped:true,attempt_limit:0});
 const profiles=$("job-profiles");profiles.replaceChildren();
 $("job-category").replaceChildren();
 for(const p of s.profiles){
  $("job-category").append(option(p.category,p.category+(p.paused?" (paused)":"")));
  if(founder){const row=document.createElement("article");row.className="gate";row.append(text("strong",p.category));const button=text("button",p.paused?"Enable profile":"Pause and cancel");button.type="button";button.onclick=()=>command("agent_pause",{category:p.category,paused:!p.paused});row.append(button);profiles.append(row)}
 }
 $("job-parent").replaceChildren(option("","No parent"));
 const root=$("job-results");root.replaceChildren();
 for(const j of s.jobs){
   if(j.state==="succeeded")$("job-parent").append(option(j.id,j.category+" · "+j.id));
   const row=document.createElement("article");row.className="gate";
   row.append(text("strong",j.category+" · "+j.state),text("span","Job "+j.id+" · attempts "+j.attempts+(j.parent_id?" · parent "+j.parent_id:"")));
   if(j.result)row.append(text("pre",JSON.stringify(j.result,null,2)));
   if(founder&&j.state==="pending"){
    const button=text("button","Approve job");button.type="button";button.onclick=()=>command("approve",{id:j.id});row.append(button);
   }
   root.append(row);
 }
 $("job-submit").onsubmit=e=>{e.preventDefault();if(!writer)return;command("submit",{category:$("job-category").value,request_key:crypto.randomUUID(),evidence:{},parent_id:$("job-parent").value||null})};
 const events=$("job-events");events.replaceChildren();
 for(const e of s.events){const row=document.createElement("article");row.className="gate";row.append(text("strong",e.event),text("span",e.recorded_at+" · "+(e.job_id||"workspace")+" · "+JSON.stringify(e.detail)));events.append(row)}
 return s;
}
