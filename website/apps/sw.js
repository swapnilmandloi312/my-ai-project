const PREFIX="swapnil-ai-labs-apps-",CACHE=PREFIX+"v0.11.0";
const urls=new Set(["./","index.html","style.css","app.mjs","catalog.mjs","engine.mjs","pwa.mjs","manifest.webmanifest","icon-192.png","icon-512.png"].map(x=>new URL(x,self.registration.scope).href));
self.addEventListener("install",e=>e.waitUntil((async()=>{const c=await caches.open(CACHE);await c.addAll([...urls].map(x=>new Request(x,{cache:"reload"})));})()));
self.addEventListener("activate",e=>e.waitUntil((async()=>{for(const k of await caches.keys())if(k.startsWith(PREFIX)&&k!==CACHE)await caches.delete(k);await self.clients.claim();})()));
self.addEventListener("message",e=>{if(e.data==="ACTIVATE_UPDATE")self.skipWaiting();});
self.addEventListener("fetch",e=>{if(e.request.method!=="GET"||!urls.has(e.request.url))return;e.respondWith((async()=>{const c=await caches.open(CACHE);return await c.match(e.request.url)||fetch(e.request);})());});
