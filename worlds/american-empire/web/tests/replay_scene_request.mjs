// P10: replay a browser-prepared scene request using the actual JS engines.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
const base=process.env.AE_BASE_URL||'http://127.0.0.1:8765';
const dir=process.env.AE_SCENE_OUTPUT||'dist/scene-job';
const raw=process.env.AE_SCENE_REQUEST_JSON||'';
if(raw.length>21000)throw Error('Scene request input too long');
const input=raw?JSON.parse(raw):null;
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
try {
 const page=await browser.newPage();
 await page.goto(base,{waitUntil:'load'});
 await page.waitForFunction(()=>document.querySelector('#peopleStatus')?.textContent?.includes('P7 VERIFIED'),null,{timeout:35000});
 const data=await page.evaluate(async input=>{
   const $=id=>document.getElementById(id);
   const [world,model,geo,manifest]=await Promise.all(
     ['world.json','model.json','geo.json','inhabitants.json'].map(async x=>{
       const response=await fetch('./data/'+x);
       if(!response.ok)throw Error('Missing verification input: '+x);
       return response.json();
     })
   );
   const actors=[...manifest.protagonists,...manifest.organizations,...manifest.film_cast].map(x=>x.id);
   const places=geo.nodes.map(x=>x.id);
   let req=input;
   if(req===null){
     const p3=window.AE_Live.current().run,p6=window.AE_Geo.getRun(),p7=window.AE_People.getRun();
     req={
       schema:'american-empire.scene-request.v1',authority_layer:'scenario_only',
       actor:'claire',year:2027,observer_place:'paris',scenario:p3.scenario,
       regional_events:p6.events,interventions:p7.interventions,
       source:{
         p3_run_sha256:p3.run_sha256,p7_run_sha256:p7.run_sha256,
         p7_snapshot_sha256:p7.snapshots[1].sha256,
         p7_manifest_sha256:p7.manifest_sha256,p6_event_sha256:p7.p6_event_sha256
       }
     };
   }
   const allowed=['schema','authority_layer','actor','year','observer_place','scenario','regional_events','interventions','source'];
   if(!req||typeof req!=='object'||Array.isArray(req)||Object.keys(req).sort().join('|')!==allowed.sort().join('|')
    ||req.schema!=='american-empire.scene-request.v1'||req.authority_layer!=='scenario_only')
     throw Error('Request schema or authority invalid');
   if(!actors.includes(req.actor)||!places.includes(req.observer_place)||
      !Number.isInteger(req.year)||req.year<2026||req.year>2037)
      throw Error('Invalid actor, year, or observed place');
   if(!Array.isArray(req.regional_events)||req.regional_events.length>40||
      !Array.isArray(req.interventions)||req.interventions.length>20)
      throw Error('Intervention count exceeded');
   if(!req.source||typeof req.source!=='object'||
      Object.keys(req.source).sort().join('|')!==
      ['p3_run_sha256','p7_run_sha256','p7_snapshot_sha256','p7_manifest_sha256','p6_event_sha256'].sort().join('|'))
      throw Error('Incomplete source attestation');
   const simulation=new window.AE_Sim.Simulation({model,graphDigest:world.source.world_graph_sha256,world});
   await simulation.initialize();
   const p3=await simulation.run(req.scenario);
   const p6=new window.AE_Regions.RegionModel(geo,p3).run(req.regional_events);
   const people=new window.AE_Inhabitants.Engine(manifest,p3,p6,geo);
   const p7=await people.run(req.interventions);
   const links=[
     [p3.run_sha256,req.source.p3_run_sha256,'P3 run'],
     [p7.run_sha256,req.source.p7_run_sha256,'P7 run'],
     [p7.snapshots[req.year-2026].sha256,req.source.p7_snapshot_sha256,'P7 year'],
     [p7.manifest_sha256,req.source.p7_manifest_sha256,'Actor manifest'],
     [p7.p6_event_sha256,req.source.p6_event_sha256,'P6 interventions']
   ];
   for(const [actual,expected,name]of links){
     if(!/^[a-f0-9]{64}$/.test(expected)||actual!==expected)
       throw Error('Scene source mismatch: '+name);
   }
   return {request:req,receipt:p7,source:{p3_run_sha256:p3.run_sha256,p7_run_sha256:p7.run_sha256}};
 },input);
 await fs.mkdir(dir,{recursive:true});
 await fs.writeFile(path.join(dir,'scene_request.json'),JSON.stringify(data.request,null,2)+'\n');
 await fs.writeFile(path.join(dir,'ae-p7-receipt.json'),JSON.stringify(data.receipt,null,2)+'\n');
 console.log('AE_SCENE_REQUEST_REPLAY_PASS '+JSON.stringify({
   actor:data.request.actor,year:data.request.year,place:data.request.observer_place,
   p7_run_sha256:data.source.p7_run_sha256,regional_events:data.request.regional_events.length,
   directives:data.request.interventions.length
 }));
}finally{await browser.close()}
