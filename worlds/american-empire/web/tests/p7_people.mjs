// P7 E2E: 10 independent rule-based agents, memory/knowledge boundaries,
// branching behavior, P5/P6 propagation, exact replay, local persistence and export.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {chromium} from 'playwright';
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1512,height:950},acceptDownloads:true});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(process.env.AE_BASE_URL||'http://127.0.0.1:8765',{waitUntil:'load'});
 await page.waitForFunction(()=>document.querySelector('#peopleStatus')?.textContent?.includes('P7 VERIFIED'),null,{timeout:30000});
 await page.locator('[data-tab="inhabitants"]').click();
 assert.equal(await page.locator('.people-card').count(),10);
 assert.equal(await page.locator('.people-decision').count(),10);
 const state=await page.evaluate(()=>{
  const run=window.AE_People.getRun(),base=window.AE_People.getBaseline();
  return {len:run.snapshots.length,manifest:run.manifest_sha256,runSha:run.run_sha256,
   people:Object.keys(run.snapshots[4].people),trust:Object.keys(run.snapshots[4].trust).length,
   knowledge:run.snapshots.some(y=>y.people.neda.knowledge.includes("Her hospital's survival will be used to force her city into the first foreign accession.")),
   identical:run.run_sha256===base.run_sha256};
 });
 assert.equal(state.len,12);
 assert.equal(state.trust,30);
 assert.equal(state.people.length,10);
 assert.equal(state.manifest.length,64);
 assert.equal(state.knowledge,false,'sealed canon ignorance must never leak');
 assert.equal(state.identical,true);
 await page.locator('#peopleYear').evaluate(el=>{el.value='2030';el.dispatchEvent(new Event('input',{bubbles:true}));});
 await page.locator('#personPriority').selectOption('order');
 await page.locator('#personApply').click();
 await page.getByText(/Applied order priority/).waitFor();
 assert.match(await page.locator('#personComparison').textContent(),/different choices this year/);
 const changed=await page.evaluate(()=>{
  const r=window.AE_People.getRun(),b=window.AE_People.getBaseline();
  return {neda:r.snapshots[4].decisions.find(x=>x.id==='neda').action,
    prev:r.snapshots[3].decisions.find(x=>x.id==='neda').action,
    base:b.snapshots[4].decisions.find(x=>x.id==='neda').action,
    sha:r.run_sha256,
    prefix:r.snapshots[3].decisions.map(x=>x.action).join(',')===b.snapshots[3].decisions.map(x=>x.action).join(','),
    memory:r.snapshots[4].people.neda.memory.length
  };
 });
 assert.equal(changed.prefix,true,'interventions cannot change previous years');
 assert.notEqual(changed.neda,changed.base,'priority must cause a different 2030 decision');
 assert.equal(changed.neda,'restrict');
 assert.ok(changed.memory>0);
 await page.locator('#peopleYear').evaluate(el=>{el.value='2037';el.dispatchEvent(new Event('input',{bubbles:true}));});
 assert.equal(await page.locator('#peopleYearValue').textContent(),'2037');
 await page.locator('#personReplay').click();await page.getByText(/REPLAY VERIFIED/).waitFor();
 const download=page.waitForEvent('download');await page.locator('#personExport').click();const file=await download;
 const doc=JSON.parse(await fs.readFile(await file.path(),'utf8'));
 assert.equal(doc.schema,'american-empire.p7-run.v1');
 assert.equal(doc.authority_layer,'scenario_only');
 assert.equal(doc.interventions[0].agent,'neda');
 assert.equal(doc.interventions[0].priority,'order');
 assert.equal(doc.snapshots.length,12);
 const rejects=await page.evaluate(async()=>{const s=window.AE_People.getRun();
   const bad=structuredClone(s);bad.snapshots[2].decisions[0].action='tampered';
   try{await window.AE_People.getEngine?.().replay(bad);return false}catch{return true}
 });
 if(!rejects)throw Error('P7 replay did not reject tampered receipt');
 await page.reload({waitUntil:'load'});
 await page.waitForFunction(()=>document.querySelector('#peopleStatus')?.textContent?.includes('P7 VERIFIED'),null,{timeout:30000});
 assert.equal((await page.evaluate(()=>window.AE_People.getRun().interventions.length)),1,'local storage restore');
 await page.locator('[data-tab="inhabitants"]').click();
 await page.locator('#personUndo').click();
 await page.getByText(/Removed last agent directive/).waitFor();
 assert.equal(await page.evaluate(()=>window.AE_People.getRun().interventions.length),0);
 await page.evaluate(()=>window.AE_Live.select('high-integration'));
 await page.locator('[data-tab="inhabitants"]').click();
 await page.waitForFunction(()=>document.querySelector('#peopleP5')?.textContent?.includes('high-integration'),null,{timeout:30000});
 assert.equal(await page.evaluate(()=>window.AE_People.getRun().interventions.length),0);
 assert.deepEqual(errors,[]);
 if(process.env.AE_P7_SCREENSHOT)await page.screenshot({path:process.env.AE_P7_SCREENSHOT,fullPage:true});
 console.log('P7 INHABITANTS PASS: 10 agents, 30 relationships, sealed canon knowledge, year-fork divergence, SHA replay, export, persistence, P5 regional sync.');
}finally{await browser.close();}
