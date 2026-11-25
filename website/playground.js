function evaluate(input) {
  const {action, tenant, budget, evidence, approval} = input;
  if(!Number.isInteger(budget)||budget<0||!Number.isInteger(evidence)||evidence<0)return {status:"BLOCKED",reason:"invalid fixture"};
  if(!["lookup_invoice","prepare_report"].includes(action))return {status:"BLOCKED",reason:"permission denied"};
  if(tenant!=="demo")return {status:"BLOCKED",reason:"tenant mismatch"};
  const cost=action==="lookup_invoice"?1:3;
  if(cost>budget)return {status:"BLOCKED",reason:"budget exceeded"};
  if(action==="prepare_report"&&(evidence<2||approval!==true))return {status:"BLOCKED",reason:"missing evidence or bound approval"};
  return {status:"SIMULATED ALLOW",cost_cents:cost,remaining_cents:budget-cost};
}
if(typeof module!=="undefined")module.exports={evaluate};
if(typeof document!=="undefined"){
 const el=id=>document.getElementById(id);
 el("evaluate").addEventListener("click",()=>{const value=evaluate({action:el("action").value,tenant:el("tenant").value,budget:el("budget").valueAsNumber,evidence:el("evidence").valueAsNumber,approval:el("approval").value==="yes"});el("result").textContent=JSON.stringify(value,null,2);});
}
