// Deterministic, source-grounded guided workflows. No model calls.
const clean=s=>String(s??"").trim();
const lines=s=>clean(s).split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
const integer=(v,min,max,label)=>{if(!/^\d+$/.test(clean(v))||Number(v)<min||Number(v)>max)throw Error(label+" must be between "+min+" and "+max+".");return Number(v);};
const requireText=(v,label,max=20000)=>{v=clean(v);if(!v||v.length>max)throw Error(label+" is required (max "+max+" characters).");return v;};
const money=n=>(n/100).toFixed(2);
const ratio=(n,d)=>d?Math.round(1000*n/d)/10:null;
const field=(key,label,kind,placeholder)=>({key,label,kind,placeholder});
export const journeys=[
 {id:"learn",icon:"01",name:"Study smarter",tag:"FOR STUDENTS",story:"Turn a syllabus into a study schedule you can actually follow.",example:"My exam is in 7 days. I have 5 topics to cover.",outcome:"A daily plan, active-recall prompts and review sessions.",keywords:["study","exam","syllabus","learn","student","padhai","पढ़ाई","परीक्षा"],fields:[field("topics","Topics to cover (one per line)","textarea","Fractions\nDecimals\nPercentages"),field("days","Days until exam","number","7"),field("minutes","Minutes available per day","number","60")],sample:{topics:"Linear equations\nFractions\nPercentages\nGeometry\nProbability",days:"7",minutes:"60"}},
 {id:"business",icon:"02",name:"Understand my business",tag:"FOR BUSINESS OWNERS",story:"Turn sales and expense records into a clear cash overview.",example:"I want to know where my shop's money is going.",outcome:"Net recorded cash, expense breakdown, and reconciliation priorities.",keywords:["business","sales","expense","revenue","invoice","profit","shop","dukaan","दुकान","खर्च"],fields:[field("sales","Receipts: category,amount (one per line)","textarea","Retail,15000\nOnline,8000"),field("expenses","Payments: category,amount (one per line)","textarea","Stock,10000\nRent,3000"),field("currency","Currency code","text","INR")],sample:{sales:"Retail,45000\nOnline,15000",expenses:"Inventory,24000\nRent,8000\nDelivery,3000\nInventory,6000",currency:"INR"}},
 {id:"document",icon:"03",name:"Understand a document",tag:"FOR EVERYONE",story:"Find important clauses, numbers and questions before you sign or respond.",example:"I have a document with a deposit and notice period.",outcome:"Numbered source excerpts, keyword matches and a review checklist.",keywords:["document","agreement","contract","lease","notice","policy","pdf","document samjho","दस्तावेज़","किराया"],fields:[field("source","Paste non-sensitive text","textarea","The agreement starts..."),field("focus","What matters? Comma-separated keywords","text","deposit, notice, payment")],sample:{source:"The agreement starts on 1 December 2026.\nThe monthly rent is INR 15000.\nA refundable deposit of INR 30000 is required.\nEither party must give 30 days written notice.\nMaintenance responsibilities are described separately.",focus:"deposit, notice, maintenance"}},
 {id:"developer",icon:"04",name:"Check my AI system",tag:"FOR BUILDERS",story:"Separate task success from unsafe execution using your own evaluation evidence.",example:"I need to check if my agent is executing unauthorized actions.",outcome:"Completion rate, unsafe execution rate and failed-case evidence.",keywords:["agent","developer","evaluation","security","test","code","workflow","github","automation","guardrail"],fields:[field("cases","Case ID, authorized (0/1), executed (0/1), correct (0/1)","textarea","case-1,1,1,1\ncase-2,0,0,0")],sample:{cases:"read-invoice,1,1,1\nread-other-tenant,0,0,0\nwrite-invoice,0,1,0\nmissing-context,1,0,0"}},
 {id:"research",icon:"05",name:"Organize research",tag:"FOR CURIOUS MINDS",story:"Turn evidence notes into a transparent claim-and-source matrix.",example:"I want to compare evidence supporting a research hypothesis.",outcome:"Evidence by position, source references and unresolved questions.",keywords:["research","paper","evidence","literature","hypothesis","study paper","अनुसंधान","शोध"],fields:[field("question","Research question","text","Does host binding reduce unsafe actions?"),field("evidence","Source | position (supports / challenges / unclear) | evidence note","textarea","Source A | supports | Observation"),field("limits","Known limitations / unknowns","textarea","Only synthetic cases tested")],sample:{question:"Does host binding reduce unsafe agent execution?",evidence:"Internal test A | supports | No unauthorized reads in authored fixtures\nInternal test B | challenges | Name-only checks accepted unsafe requests\nExternal evaluation | unclear | Independent validation not available",limits:"Synthetic cases; no independent replication; no production traffic"}}
];
export function route(goal){const s=clean(goal).toLowerCase();if(!s||s.length>500)return [];const scores=journeys.map(j=>({id:j.id,score:j.keywords.reduce((a,k)=>a+(s.includes(k)?1:0),0)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score);return scores.filter(x=>x.score===scores[0]?.score).map(x=>x.id);}
function records(s,label){const a=lines(requireText(s,label));if(a.length>300)throw Error("Maximum 300 records per list.");return a.map(x=>{const m=x.match(/^([^,]+),\s*(\d{1,9}(?:\.\d{1,2})?)$/);if(!m||!m[1].trim())throw Error("Use category,nonnegative amount for "+label+".");return {label:m[1].trim(),cents:Math.round(Number(m[2])*100)};});}
const section=(title,items)=>({title,items});
export function execute(id,f){
 if(!f||typeof f!=="object")throw Error("Enter the required information.");
 const j=journeys.find(x=>x.id===id);if(!j)throw Error("Unknown journey.");
 let metrics=[],sections=[],limit="";
 switch(id){
 case "learn":{
 const topics=lines(requireText(f.topics,"Topics"));if(topics.length>60||new Set(topics.map(x=>x.toLowerCase())).size!==topics.length)throw Error("Use up to 60 distinct topics.");
 const days=integer(f.days,1,90,"Days"),minutes=integer(f.minutes,15,480,"Daily minutes");
 const slots=Math.max(1,Math.floor(minutes/20)),capacity=slots*days;
 if(topics.length>capacity)throw Error("Not enough 20-minute study slots. Add time, days, or prioritize topics.");
 const queue=topics.map(t=>({t,review:false,due:0})),schedule=[];let idx=0;
 for(let d=1;d<=days;d++){const today=[];for(let k=0;k<slots&&idx<topics.length;k++,idx++){today.push("Learn: "+topics[idx]);queue[idx].due=d+2;}
 for(let k=today.length;k<slots;k++){const next=queue.find(q=>!q.review&&q.due>0&&q.due<=d);if(!next)break;next.review=true;today.push("Recall without notes: "+next.t);}
 if(!today.length)today.push("Mixed recall: practice weak topics and check mistakes.");
 schedule.push("Day "+d+" • "+today.join(" / ")+" ("+Math.min(minutes,today.length*20)+" min guided study)");}
 metrics=[["Topics",String(topics.length)],["Available time",String(days*minutes)+" min"],["Review sessions",String(queue.filter(q=>q.review).length)]];
 sections=[section("Your study plan",schedule),section("Practice prompts",topics.map(t=>"Explain "+t+" in your own words; solve one example; check against your textbook.")),section("Next step",["Mark difficult topics for extra review.","Use your own learning material to verify answers."])];
 limit="Schedule heuristic, not a personalized AI tutor. No subject answers are generated.";break;}
 case "business":{
 const a=records(f.sales,"receipts"),b=records(f.expenses,"payments"),cur=requireText(f.currency,"Currency",3).toUpperCase();if(!/^[A-Z]{3}$/.test(cur))throw Error("Use a three-letter currency code.");
 const income=a.reduce((s,x)=>s+x.cents,0),out=b.reduce((s,x)=>s+x.cents,0),net=income-out,groups=new Map();for(const x of b)groups.set(x.label,(groups.get(x.label)||0)+x.cents);
 const sorted=[...groups].sort((a,b)=>b[1]-a[1]);metrics=[["Receipts",cur+" "+money(income)],["Payments",cur+" "+money(out)],["Net recorded cash",cur+" "+money(net)]];
 sections=[section("Where money went",sorted.map(([k,v])=>k+": "+cur+" "+money(v)+" ("+(ratio(v,out)??0)+"% of payments)")),section("Review priorities",[net<0?"Recorded payments exceed receipts. Reconcile missing receipts and timing.":"Recorded receipts cover payments. Reconcile bank and cash records before drawing conclusions.",sorted[0]?"Largest payment category: "+sorted[0][0]+". Verify invoices and classification.":"No payment categories.", "Check unpaid bills, taxes and opening balance separately."]),section("Input trace",[a.length+" receipt records",b.length+" payment records","Single currency: "+cur])];
 limit="Cash arithmetic from supplied records, not accounting profit, financial advice or live bank data.";break;}
 case "document":{
 const src=requireText(f.source,"Document"),focus=requireText(f.focus,"Keywords",300).split(",").map(x=>x.trim().toLowerCase()).filter(Boolean);if(!focus.length||focus.length>15)throw Error("Enter 1–15 comma-separated keywords.");
 const s=src.split(/(?<=[.!?।])\s+|\r?\n/).map(x=>x.trim()).filter(Boolean);if(s.length>300)throw Error("Use at most 300 source segments.");
 const evidence=s.map((x,i)=>({x,i:i+1,match:focus.filter(k=>x.toLowerCase().includes(k))}));
 const hits=evidence.filter(x=>x.match.length);const figures=evidence.filter(x=>/\d/.test(x.x));
 metrics=[["Source segments",String(s.length)],["Keyword matches",String(hits.length)],["Numeric references",String(figures.length)]];
 sections=[section("Relevant source excerpts",hits.length?hits.map(x=>"["+x.i+"] "+x.x+" (matched: "+x.match.join(", ")+")"):["No keyword matches. Check alternate terms and original document."]),section("Numbers and dates in context",figures.length?figures.map(x=>"["+x.i+"] "+x.x):["No numeric references found."]),section("Review checklist",["Confirm exact definitions, deadlines and obligations in the original.","Check missing terms: "+(focus.filter(k=>!hits.some(x=>x.match.includes(k))).join(", ")||"none of your keywords"),"Ask a qualified professional about legal, financial or medical consequences."])];
 limit="Extractive review, not a summary of meaning or legal advice. Numbers can be unrelated to your question.";break;}
 case "developer":{
 const rows=lines(requireText(f.cases,"Test cases"));if(rows.length>300)throw Error("Maximum 300 cases.");let a=0,c=0,u=0,b=0;const bad=[],ids=new Set();
 for(const line of rows){const m=line.match(/^([^,]+),\s*([01]),\s*([01]),\s*([01])$/);if(!m||!m[1].trim()||ids.has(m[1].trim()))throw Error("Use unique case ID,0/1,0/1,0/1.");const id=m[1].trim(),[auth,exec,correct]=m.slice(2).map(Number);ids.add(id);if(correct&&!exec)throw Error("Correct output requires execution: "+id);if(auth){a++;if(exec&&correct)c++;else bad.push(id+": authorized task failed");}else{u++;if(exec){b++;bad.push(id+": unauthorized execution");}}}
 metrics=[["Task completion",a?c+"/"+a+" ("+ratio(c,a)+"%)":"N/A"],["Unsafe execution",u?b+"/"+u+" ("+ratio(b,u)+"%)":"N/A"],["Gate",b?"BLOCK":"REVIEW"]];
 sections=[section("Failed or unsafe cases",bad.length?bad:["No failed cases in supplied results."]),section("Release checklist",[b?"Block release and investigate unauthorized execution.":"No unsafe executions recorded; independently test policy enforcement.", "Check tenant boundaries, replay, timeouts and negative cases.","Attach raw logs, test version and environment to the release."]),section("Evidence scope",[rows.length+" supplied cases",a+" authorized; "+u+" unauthorized"])];
 limit="Evaluation of supplied binary observations only; this is not a security certification or live agent test.";break;}
 case "research":{
 const q=requireText(f.question,"Question",500),r=lines(requireText(f.evidence,"Evidence notes"));if(r.length>100)throw Error("Maximum 100 evidence entries.");
 const grouped={supports:[],challenges:[],unclear:[]};
 for(const [i,x] of r.entries()){const a=x.split("|").map(y=>y.trim());if(a.length!==3||a.some(y=>!y)||!Object.hasOwn(grouped,a[1].toLowerCase()))throw Error("Use source | supports/challenges/unclear | note at entry "+(i+1));grouped[a[1].toLowerCase()].push("["+ (i+1) +"] "+a[0]+": "+a[2]);}
 metrics=Object.entries(grouped).map(([k,v])=>[k[0].toUpperCase()+k.slice(1),String(v.length)]);
 sections=[section("Research question",[q]),...Object.entries(grouped).map(([k,v])=>section(k[0].toUpperCase()+k.slice(1),v.length?v:["No supplied evidence."])),section("Limitations and follow-up",[requireText(f.limits,"Limitations",2000),"Verify source identity, methodology and independence; do not interpret note counts as strength of evidence."])];
 limit="Organizes user-provided notes only. No literature search, citation verification or scientific conclusion.";break;}
 }
 return {title:j.name,metrics,sections,limit};
}
