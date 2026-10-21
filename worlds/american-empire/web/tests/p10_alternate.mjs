// P10 regression: altered modeled Paris supplies and Claire directive, remote Geneva viewpoint.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const base=process.env.AE_BASE_URL||'http://127.0.0.1:8765';
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
try{
 const page=await browser.newPage();
 await page.goto(base,{waitUntil:'load'});
 await page.waitForFunction(()=>document.querySelector('#peopleStatus')?.textContent?.includes('P7 VERIFIED'),null,{timeout:30000});
 const request=await page.evaluate(async()=>{
  const [geo,manifest]=await Promise.all(['geo.json','inhabitants.json'].map(async p=>{
   const r=await fetch('./data/'+p);if(!r.ok)throw Error('Missing built '+p);return r.json();
  }));
  const p3=window.AE_Live.current().run;
  const region=[{id:'local-1',year:2027,type:'independent_supply',place:'paris',intensity:2}];
  const directives=[{id:'directive-1',year:2027,agent:'claire',priority:'liberty'}];
  const p6=new window.AE_Regions.RegionModel(geo,p3).run(region);
  const p7=await new window.AE_Inhabitants.Engine(manifest,p3,p6,geo).run(directives);
  const year=2028;
  const req={
   schema:'american-empire.scene-request.v1',authority_layer:'scenario_only',
   actor:'claire',year,observer_place:'geneva',
   scenario:p3.scenario,regional_events:region,interventions:directives,
   source:{
    p3_run_sha256:p3.run_sha256,p7_run_sha256:p7.run_sha256,
    p7_snapshot_sha256:p7.snapshots[year-2026].sha256,
    p7_manifest_sha256:p7.manifest_sha256,p6_event_sha256:p7.p6_event_sha256,
   }
  };
  return {req,baseline:window.AE_People.getRun().run_sha256,
    home:p7.snapshots[year-2026].people.claire.place};
 });
 assert.equal(request.home,'paris');
 assert.notEqual(request.req.source.p7_run_sha256,request.baseline);
 assert.equal(request.req.regional_events.length,1);
 assert.equal(request.req.interventions.length,1);
 assert.equal(request.req.observer_place,'geneva');
 const serialized=JSON.stringify(request.req);
 assert.ok(serialized.length<21000);
 if(process.env.AE_ALT_OUTPUT)await fs.writeFile(process.env.AE_ALT_OUTPUT,JSON.stringify(request.req,null,2)+'\n');
 console.log('AE_ALTERNATE_REQUEST_JSON='+serialized);
 console.log('AE_P10_ALTERNATE_PASS: 2028 Geneva remote observer, Paris relief variant, Claire liberty directive, source '+request.req.source.p7_run_sha256);
}finally{await browser.close()}
