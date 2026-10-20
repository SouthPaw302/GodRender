// P5 real Chromium smoke tests for deployed static World Explorer.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
const base = process.env.AE_BASE_URL || 'http://127.0.0.1:8765';
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1440,height:900},acceptDownloads:true});
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(base,{waitUntil:'networkidle',timeout:30000});
 await page.locator('#graph .node').first().waitFor();
 try { await page.waitForFunction(()=>document.querySelector('#liveStatus')?.textContent?.includes('P3 parity PASS'),null,{timeout:9000});
 await page.waitForFunction(()=>document.querySelector('#peopleStatus')?.textContent?.includes('P7 VERIFIED'),null,{timeout:30000}); }
 catch(e) {
   console.error('P5 OFFLINE DIAGNOSTIC:',JSON.stringify({url:page.url(),errorBanner:await page.locator('#error').textContent(),status:await page.locator('#liveStatus').textContent(),exceptions:errors,embedded:await page.evaluate(()=>['embeddedWorld','embeddedBrain','embeddedModel','embeddedReference'].map(x=>[x,!!document.getElementById(x)]))}));
   throw e;
 }
 assert.equal(await page.locator('#graph .node').count(),16);
 assert.equal(await page.locator('#scenarioSelect option').count(),3);
 assert.equal(await page.locator('#metrics .metric').count(),7);
 await page.locator('#nextYear').click();
 assert.equal(await page.locator('#yearBig').textContent(),'2028');
 await page.locator('#yearSlider').evaluate(el=>{el.value='2030';el.dispatchEvent(new Event('input',{bubbles:true}));});
 assert.equal(await page.locator('#yearBig').textContent(),'2030');
 await page.locator('#scenarioSelect').selectOption('1');
 assert.ok((await page.locator('#pressure').textContent()).length>0);
 await page.locator('#graph .node').nth(2).click();
 assert.ok((await page.locator('#entityDetail').textContent()).includes('Git blob'));
 await page.getByRole('button',{name:'Second Brain'}).click();
 await page.locator('#brainSearch').fill('FX2-ATM-001');
 assert.equal(await page.locator('.cap-card').count(),1);
 await page.locator('.cap-card').first().click();
 assert.ok((await page.locator('#brainSelected').textContent()).includes('GIT SOURCE'));
 await page.getByRole('button',{name:'Chronology'}).click();
 assert.equal(await page.locator('.time-card').count(),12);
 await page.getByRole('button',{name:'Production Desk'}).click();
 await page.locator('#briefNote').fill('Viewpoint examination; no canon promotion');
 assert.ok((await page.locator('#briefPreview').textContent()).includes('draft_handoff_only'));
 assert.ok((await page.locator('#briefPreview').textContent()).includes('studio_connected'));
 const downloadPromise=page.waitForEvent('download');
 await page.locator('#downloadBrief').click();
 const download=await downloadPromise;
 assert.ok(download.suggestedFilename().endsWith('.json'));
 await page.getByRole('button',{name:'Observer Cinema'}).click();
 await page.waitForFunction(()=>document.querySelector('#cinemaStatus')?.textContent?.includes('Catalog ready'),null,{timeout:15000});
 assert.equal(await page.locator('.cinema-item').count(),10);
 await page.locator('#cinemaFindClaire').click();
 assert.match(page.url(),/#inhabitants/);
 assert.equal(await page.locator('#personFullName').textContent(),'Claire Delacroix');
 await page.locator('[data-tab="cinema"]').click();
 assert.match(await page.locator('#cinemaTitle').textContent(),/Scenes 01–02/);
 assert.match(await page.locator('#cinemaRights').textContent(),/same|cinematic depictions/);
 assert.match(await page.locator('#cinemaOpen').getAttribute('href'),/^https:\/\/drive\.google\.com\/file\/d\//);
 assert.equal(await page.locator('#cinemaFrame iframe').count(),0,'no involuntary private-media playback');
 await page.locator('.cinema-item').nth(2).click();
 assert.match(await page.locator('#cinemaTitle').textContent(),/Scene 02/);
 if(errors.length)throw new Error('Browser runtime errors: '+errors.join('; '));
 const out=process.env.AE_SCREENSHOT;
 if(out){await page.locator('[data-tab="world"]').click();await page.screenshot({path:out,fullPage:true});}
 console.log('AMERICAN EMPIRE WEB PASS: graph, timeline, scenarios, Second Brain, production brief, no JS errors');
}finally{await browser.close();}
