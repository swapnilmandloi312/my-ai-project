import assert from "node:assert/strict";
import {spawn} from "node:child_process";
import {chromium} from "playwright";
const server=spawn("python",["-m","http.server","8769","--bind","127.0.0.1","--directory","website"],{stdio:"ignore"});let browser;
try{
 const url="http://127.0.0.1:8769/apps/";
 for(let i=0;i<40;i++){try{if((await fetch(url)).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 const m=await(await fetch(url+"manifest.webmanifest")).json();assert.equal(m.display,"standalone");assert.equal(m.scope,"./");
 for(const icon of m.icons){const b=Buffer.from(await(await fetch(url+icon.src)).arrayBuffer());assert.equal(b.subarray(0,8).toString("hex"),"89504e470d0a1a0a");assert.equal(b.readUInt32BE(16),Number(icon.sizes.split("x")[0]));assert.equal(b.readUInt32BE(20),Number(icon.sizes.split("x")[1]));}
 browser=await chromium.launch({headless:true});const c=await browser.newContext({viewport:{width:390,height:844}});const p=await c.newPage();await p.goto(url);await p.waitForFunction(()=>!!navigator.serviceWorker.controller);await p.waitForFunction(()=>document.querySelector("#install-state").textContent.includes("Offline shell ready"));
 const keys=await p.evaluate(async()=>{const c=await caches.open("swapnil-ai-labs-apps-v0.11.0");return (await c.keys()).map(x=>x.url);});assert.equal(keys.length,10);assert.ok(keys.every(x=>x.startsWith("http://127.0.0.1:8769/apps/")));
 await c.setOffline(true);await p.reload();await p.locator('[data-id="finance-1"]').click();await p.locator("#example").click();await p.locator("#run").click();assert.match(await p.locator("#output").innerText(),/200.00/);
 await p.locator('[data-id="education-1"]').click();await p.locator("#example").click();await p.locator("#run").click();await p.locator("#reveal").click();assert.match(await p.locator("#output").innerText(),/4$/);
 assert.match(await p.locator("#network-state").innerText(),/Offline/);assert.equal(await p.evaluate(()=>localStorage.length),0);
 await p.screenshot({path:"apps-offline-preview.png",fullPage:true});console.log("Manifest, two PNG icons, scoped cache, offline reload, finance and education tools, network state and no localStorage persistence passed.");
}finally{if(browser)await browser.close();server.kill();}
