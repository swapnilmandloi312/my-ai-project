import assert from "node:assert/strict";
import {spawn} from "node:child_process";import {chromium} from "playwright";
const server=spawn("python",["-m","http.server","8770","--bind","127.0.0.1","--directory","website"],{stdio:"ignore"});let browser;
try{const url="http://127.0.0.1:8770/apps/";for(let i=0;i<40;i++){try{if((await fetch(url)).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
browser=await chromium.launch({headless:true});const c=await browser.newContext({viewport:{width:390,height:844}});const p=await c.newPage();const errors=[],outside=[];p.on("pageerror",e=>errors.push(e.message));p.on("request",r=>{if(!r.url().startsWith(url))outside.push(r.url());});await p.goto(url);
await p.locator('[data-journey="learn"]').waitFor();assert.equal(await p.locator("[data-journey]").count(),5);
await p.locator("#goal").fill("I have an exam");await p.locator("#find").click();assert.match(await p.locator("#work-title").innerText(),/Study/);
await p.locator("#execute").click();assert.ok((await p.locator("#error").innerText()).length);
for(const id of ["learn","business","document","developer","research"]){await p.locator('[data-journey="'+id+'"]').click();await p.locator("#sample").click();await p.locator("#execute").click();assert.equal(await p.locator("#export").isEnabled(),true,id);assert.equal(await p.locator(".metric").count(),3);assert.ok((await p.locator(".limit").innerText()).length);}
await p.locator('[data-journey="business"]').click();await p.locator("#sample").click();await p.locator("#execute").click();assert.match(await p.locator("#result").innerText(),/INR 19000.00/);
await p.locator("#field-sales").fill("bad");assert.equal(await p.locator("#export").isEnabled(),false);
await p.locator("#goal").fill("exam invoice");await p.locator("#find").click();assert.match(await p.locator("#route-status").innerText(),/More than one/);
assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);assert.deepEqual(outside,[]);
await p.locator("#close").click();await p.screenshot({path:"experience-mobile-preview.png",fullPage:true});
await p.getByText("Offline shell ready.",{exact:false}).waitFor({timeout:30000});for(let i=0;i<50;i++){if(await p.evaluate(()=>!!navigator.serviceWorker.controller))break;await new Promise(r=>setTimeout(r,100));}assert.equal(await p.evaluate(()=>!!navigator.serviceWorker.controller),true);
await c.setOffline(true);await p.reload();await p.locator('[data-journey="business"]').click();await p.locator("#sample").click();await p.locator("#execute").click();assert.match(await p.locator("#result").innerText(),/INR 19000.00/);console.log("Five mobile browser journeys, routing, validation, privacy, layout and offline business workflow passed.");
}finally{if(browser)await browser.close();server.kill();}
