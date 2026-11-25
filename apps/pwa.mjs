const el=id=>document.getElementById(id);let promptEvent=null,reload=false;
function state(){el("network-state").textContent=navigator.onLine?"Online":"Offline — cached tools remain usable";}
state();window.addEventListener("online",state);window.addEventListener("offline",state);
window.addEventListener("beforeinstallprompt",e=>{e.preventDefault();promptEvent=e;el("install-app").hidden=false;});
window.addEventListener("appinstalled",()=>{promptEvent=null;el("install-app").hidden=true;el("install-state").textContent="App installed.";});
el("install-app").onclick=async()=>{if(!promptEvent)return;const e=promptEvent;promptEvent=null;el("install-app").hidden=true;try{await e.prompt();await e.userChoice;}catch{}};
if("serviceWorker" in navigator&&isSecureContext){
 navigator.serviceWorker.addEventListener("controllerchange",()=>{if(reload)location.reload();});
 navigator.serviceWorker.register("./sw.js",{scope:"./"}).then(reg=>{
 const update=()=>{if(reg.waiting&&navigator.serviceWorker.controller){el("update-app").hidden=false;el("update-app").onclick=()=>{if(confirm("Reload to update? Unsaved input will be cleared.")){reload=true;reg.waiting?.postMessage("ACTIVATE_UPDATE");}};}};
 update();reg.addEventListener("updatefound",()=>reg.installing?.addEventListener("statechange",update));
 navigator.serviceWorker.ready.then(()=>el("install-state").textContent="Offline shell ready. Install using your browser menu (if supported).");
 }).catch(()=>el("install-state").textContent="Offline caching unavailable; online tools still work.");
}else el("install-state").textContent="Offline installation requires HTTPS or localhost and a compatible browser.";
