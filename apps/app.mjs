import {catalog} from "./catalog.mjs";
import {run,notice} from "./engine.mjs";
const el=id=>document.getElementById(id);
const names=new Map(catalog.industries.map(x=>[x.id,x.name]));
let active=catalog.tools[0],result=null,cardIndex=0,revealed=false;
function option(value,label){const e=document.createElement("option");e.value=value;e.textContent=label;return e;}
el("industry").append(option("all","All industries"),...catalog.industries.map(x=>option(x.id,x.name)));
const locale={en:["Intelligence for everyone.","Practical tools for life, learning and work. Run locally in your browser, without an account or model API.","Find a tool"],hi:["हर किसी के लिए एआई","जीवन, पढ़ाई और काम के लिए स्थानीय टूल। खाते या मॉडल API की ज़रूरत नहीं।","टूल खोजें"],hinglish:["Har kisi ke liye AI","Life, learning aur work ke liye local tools. Account ya model API ki zaroorat nahi.","Tool dhoondhein"]};
el("locale").addEventListener("change",()=>{const copy=locale[el("locale").value];el("headline").textContent=copy[0];el("intro").textContent=copy[1];el("browse").textContent=copy[2];document.documentElement.lang=el("locale").value==="hi"?"hi":el("locale").value==="hinglish"?"hi-Latn":"en";});
function render(){
 const q=el("search").value.trim().toLowerCase(),industry=el("industry").value;
 const found=catalog.tools.filter(x=>(industry==="all"||x.industry===industry)&&[x.title,names.get(x.industry)].join(" ").toLowerCase().includes(q));
 el("count").textContent=found.length+" tools found";el("cards").replaceChildren();
 for(const t of found){const b=document.createElement("button");b.type="button";b.textContent=t.title+" · "+names.get(t.industry);b.dataset.id=t.id;b.setAttribute("aria-pressed",String(t===active));b.addEventListener("click",()=>{choose(t);render();});el("cards").append(b);}
}
function resetResult(){result=null;el("output").textContent="Enter your information or load a sample.";el("quiz").hidden=true;el("save").disabled=true;}
function choose(t){active=t;el("category").textContent=names.get(t.industry)+" / "+t.risk.toUpperCase()+" RISK";el("tool-title").textContent=t.title;el("scope").textContent=t.scope;el("input-label").textContent=t.inputLabel;el("source").value="";el("query").value="";el("query-wrap").hidden=t.mode!=="lookup";el("warning").textContent=notice(t);resetResult();}
function showCard(){const p=result.quiz[cardIndex];el("output").textContent=`Card ${cardIndex+1} of ${result.quiz.length}\n\n${p.question}`+(revealed?"\n\n"+p.answer:"");}
el("search").addEventListener("input",render);el("industry").addEventListener("change",render);
el("example").addEventListener("click",()=>{el("source").value=active.example;el("query").value=active.mode==="lookup"?active.options[0]:"";resetResult();});
el("clear").addEventListener("click",()=>choose(active));
el("run").addEventListener("click",()=>{try{result=run(active,el("source").value,el("query").value);el("output").textContent=result.text;el("save").disabled=false;el("quiz").hidden=!result.quiz;if(result.quiz){cardIndex=0;revealed=false;showCard();}}catch(e){resetResult();el("output").textContent=e.message;}});
el("reveal").addEventListener("click",()=>{revealed=!revealed;showCard();});el("next").addEventListener("click",()=>{cardIndex=(cardIndex+1)%result.quiz.length;revealed=false;showCard();});
el("save").addEventListener("click",()=>{if(!result)return;const text=result.title+"\n\n"+(result.quiz?result.quiz.map(p=>p.question+"\n"+p.answer).join("\n\n"):result.text)+"\n\n"+result.notice;const u=URL.createObjectURL(new Blob([text],{type:"text/plain;charset=utf-8"}));const a=document.createElement("a");a.href=u;a.download=active.id+"-result.txt";a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
choose(active);render();
