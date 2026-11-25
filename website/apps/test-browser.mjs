import assert from "node:assert/strict";
import {spawn} from "node:child_process";
import {chromium} from "playwright";
const server=spawn("python",["-m","http.server","8768","--bind","127.0.0.1","--directory","website"],{stdio:"ignore"});
let browser;
try{
 for(let i=0;i<30;i++){try{if((await fetch("http://127.0.0.1:8768/apps/")).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[],external=[];page.on("pageerror",e=>errors.push(e.message));page.on("request",r=>{if(!r.url().startsWith("http://127.0.0.1:8768/"))external.push(r.url());});
 await page.goto("http://127.0.0.1:8768/apps/tools.html");await page.locator('[data-id="finance-1"]').waitFor();
 assert.equal(await page.locator("#cards button").count(),72);
 const ids=await page.locator("#cards button").evaluateAll(ns=>ns.map(n=>n.dataset.id));
 for(const id of ids){await page.locator('[data-id="'+id+'"]').click();await page.locator("#example").click();await page.locator("#run").click();assert.equal(await page.locator("#save").isEnabled(),true,id);}
 await page.locator("#industry").selectOption("finance");assert.equal(await page.locator("#cards button").count(),3);
 await page.locator('[data-id="finance-1"]').click();await page.locator("#example").click();await page.locator("#run").click();assert.match(await page.locator("#output").innerText(),/200.00/);
 await page.locator("#source").fill("broken");await page.locator("#run").click();assert.equal(await page.locator("#save").isEnabled(),false);
 await page.locator("#industry").selectOption("education");await page.locator('[data-id="education-1"]').click();await page.locator("#example").click();await page.locator("#run").click();assert.doesNotMatch(await page.locator("#output").innerText(),/\n\n4$/);await page.locator("#reveal").click();assert.match(await page.locator("#output").innerText(),/\n\n4$/);
 await page.locator("#locale").selectOption("hi");assert.match(await page.locator("#headline").innerText(),/एआई/);
 await page.locator("#industry").selectOption("all");await page.locator("#search").fill("invoice");assert.ok(await page.locator("#cards button").count()>0);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 await page.screenshot({path:"apps-mobile-preview.png",fullPage:true});
 console.log("72 browser tool executions, industry/search, validation, flashcard interaction, Hindi interface copy, mobile layout and zero external network requests passed.");
}finally{if(browser)await browser.close();server.kill();}
