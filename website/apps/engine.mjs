const MAX=20000;
const lines=s=>s.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
const norm=s=>s.trim().toLocaleLowerCase();
const sentences=s=>s.split(/(?<=[.!?।])\s+|\r?\n/).map(x=>x.trim()).filter(Boolean);
const split=s=>s.split("|").map(x=>x.trim()).filter(Boolean);
function numericRows(input){
 return lines(input).map(line=>{
  const m=line.match(/^([^,]+),\s*(-?\d{1,9}(?:\.\d{1,2})?)$/);
  if(!m)throw Error("Use label,number on each line, without thousands separators; maximum two decimals.");
  const label=m[1].trim();if(!label)throw Error("Missing label.");
  return {label,n:Math.round(Number(m[2])*100)};
 });
}
function fmt(n){return (n/100).toFixed(2);}
function pairs(input){return lines(input).map(x=>{const p=x.split("|");if(p.length!==2||p.some(v=>!v.trim()))throw Error("Use question|answer on each line.");return {question:p[0].trim(),answer:p[1].trim()};});}
export function run(tool,input,query=""){
 if(!tool||typeof input!=="string"||typeof query!=="string"||input.length>MAX||query.length>300)throw Error("Input limit: 20,000 characters; search term limit: 300.");
 if(!input.trim())throw Error("Enter source information first.");
 const rows=lines(input);if(rows.length>300)throw Error("Maximum 300 input lines.");
 const o=tool.options;let title=tool.title,output=[],quiz=null;
 switch(tool.mode){
 case "plan":
  output=[...rows.map((x,i)=>`${i+1}. ${x}`),"","Review before use:",...split(o[0]).map(x=>"□ "+x)];break;
 case "read":
  output=sentences(input).map((x,i)=>`${i+1}. ${x}`);break;
 case "budget": {
  const n=numericRows(input);if(n.length<2||n.some(x=>x.n<0))throw Error("Enter nonnegative income first, then at least one expense.");
  const expenses=n.slice(1).reduce((a,x)=>a+x.n,0);output=[`Income: ${fmt(n[0].n)}`,`Expenses: ${fmt(expenses)}`,`Remaining: ${fmt(n[0].n-expenses)}`];break;}
 case "quiz":quiz=pairs(input);output=quiz.map((p,i)=>`${i+1}. ${p.question}`);break;
 case "draft":{
  const labels=split(o[0]);if(rows.length!==labels.length)throw Error("Enter exactly "+labels.length+" nonempty lines: "+labels.join(", "));
  output=[...labels.map((x,i)=>x+": "+rows[i]),"","Review checklist:",...split(o[1]).map(x=>"□ "+x)];break;}
 case "lookup":{
  if(!query.trim())throw Error("Enter a search term.");
  const q=norm(query);output=rows.filter(x=>norm(x).includes(q));if(!output.length)output=["No matches in supplied source."];break;}
 case "check":{
  const done=new Set(rows.map(norm));const tasks=split(o[0]);output=[`${tasks.filter(x=>done.has(norm(x))).length}/${tasks.length} supplied checklist items marked complete`,...tasks.map(x=>(done.has(norm(x))?"✓ ":"□ ")+x)];break;}
 case "sum":case "group":case "compare":{
  const n=numericRows(input);
  if(tool.mode==="sum"){output=[o[0]+": "+fmt(n.reduce((a,x)=>a+x.n,0)),...n.map(x=>x.label+": "+fmt(x.n))];}
  if(tool.mode==="group"){const m=new Map();for(const x of n)m.set(x.label,(m.get(x.label)||0)+x.n);output=[o[0],...[...m].map(([k,v])=>k+": "+fmt(v))];}
  if(tool.mode==="compare"){if(n.length<2)throw Error("Enter at least two comparable rows.");const sorted=[...n].sort((a,b)=>a.n-b.n);output=[...sorted.map(x=>x.label+": "+fmt(x.n)),"Range: "+fmt(sorted.at(-1).n-sorted[0].n)];}break;}
 case "extract":{
  const keys=split(o[0]).map(norm);output=sentences(input).filter(x=>keys.some(k=>norm(x).includes(k)));if(!output.length)output=["No matching source sentences."];break;}
 case "evaluate":{
  let a=0,u=0,c=0,b=0;
  for(const x of rows){if(!/^[01],[01],[01]$/.test(x))throw Error("Use exactly three binary values: authorized,executed,correct.");const [auth,executed,correct]=x.split(",").map(Number);if(correct&&!executed)throw Error("Correct output requires an executed request.");if(auth){a++;c+=executed&&correct?1:0;}else{u++;b+=executed;}}
  output=[`Authorized correct: ${c}/${a}`,`Unauthorized executed: ${b}/${u}`,"Task completion: "+(a?(100*c/a).toFixed(1)+"%":"N/A"),"Unsafe execution rate: "+(u?(100*b/u).toFixed(1)+"%":"N/A")];break;}
 case "guard":{
  const p=input.trim().split(",").map(x=>x.trim());if(p.length!==2||p.some(x=>!x))throw Error("Enter proposed action,authorized action.");
  output=[p[0]===p[1]?"SIMULATED MATCH":"BLOCKED — action mismatch","Name matching is not sufficient authorization."];break;}
 default:throw Error("Unsupported utility.");
 }
 return {title,text:output.join("\n"),quiz,notice:notice(tool)};
}
export function notice(t){return ["draft","lookup","sum","group","extract"].includes(t.mode)?t.options.at(-1):["plan"].includes(t.mode)?"Planning aid only; verify details independently.":t.options.at(-1);}
