/* American Empire P5 live scenario controls. Canon read-only. Browser-local storage only. */
(function(global){
'use strict';
const el=id=>document.getElementById(id);
const clone=x=>JSON.parse(JSON.stringify(x));
const STORE='american-empire.p5.scenarios.v1';
const VARS=['V1','V2','V3','V4','V5','V6','V7'];
const moduleState={sim:null,world:null,app:null,api:null,records:new Map(),saved:new Map(),
 selected:'baseline',year:2027,busy:false,lastRun:null};
const samples=new Set(['baseline','independent-corridor','high-integration']);
function status(message,error=false){const x=el('liveStatus');x.textContent=message;x.classList.toggle('error-state',error);}
function escape(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function checkedStorage(){try{return global.localStorage}catch{return null;}}
function selectOptions(){
 for(const id of ['liveScenario','liveCompare']){const select=el(id),current=select.value;
  select.replaceChildren();
  for(const [key,rec] of moduleState.records){
    const opt=document.createElement('option');opt.value=key;opt.textContent=rec.spec.id+(samples.has(key)?' · SOURCE EXAMPLE':' · CUSTOM BRANCH');select.append(opt);
  }
  select.value=id==='liveScenario'?moduleState.selected:(moduleState.records.has(current)?current:'baseline');
  if(id==='liveCompare'&&select.value===moduleState.selected)select.value='baseline';
 }
}
function renderEvents(){
 const host=el('liveEvents');host.replaceChildren();
 const receipts=moduleState.lastRun.event_receipts.filter(x=>x.year<=moduleState.year);
 if(!receipts.length){host.textContent='No interventions on this timeline through this year.';return;}
 for(const e of receipts){
   const div=document.createElement('div');div.className='sim-event';
   const action=moduleState.sim.model.actions[e.type]?.label||e.type;
   const delta=Object.entries(e.applied_delta).map(([k,v])=>k+' '+(v>0?'+':'')+v).join(' · ');
   div.innerHTML='<strong>'+escape(e.year+' · '+action)+'</strong><span>'+escape(delta||'No realized effect (bounded)')+'</span>';
   host.append(div);
 }
}
function renderMetrics(){
 const snap=moduleState.lastRun.snapshots[moduleState.year-2026];
 const title=moduleState.world.years[moduleState.year-2026];
 el('liveHeroYear').textContent=moduleState.year;
 el('liveYearDisplay').textContent=moduleState.year;
 el('livePhase').textContent=title.title;
 el('liveHeroTitle').textContent=title.title;
 el('liveScenarioCaption').textContent=moduleState.lastRun.scenario.id+' · YEAR '+moduleState.year+' · MODEL ONLY';
 el('livePressure').textContent=snap.indicators.accession_pressure_raw;
 el('liveDependency').textContent=snap.indicators.dependency_gap;
 el('liveYear').value=moduleState.year;
 const host=el('liveMetrics');host.replaceChildren();
 for(const variable of moduleState.world.variables){
   const id=variable.attributes.id,value=snap.state[id],div=document.createElement('div');
   div.className='sim-variable';
   div.innerHTML='<div><span>'+escape(variable.name)+'</span><b>'+value+'</b></div>'+
       '<div class="bar-bg"><div class="bar-fill" style="width:'+value+'%"></div></div>';
   host.append(div);
 }
 renderEvents();
}
function renderSaved(){
 const host=el('liveSavedList');host.replaceChildren();
 if(!moduleState.saved.size){host.textContent='No saved branches on this device.';return;}
 for(const [id] of moduleState.saved){
  const b=document.createElement('button');b.className='sim-save-item';b.type='button';b.textContent=id+' ↗';
  b.addEventListener('click',()=>select(id));host.append(b);
 }
}
function render(){
 if(!moduleState.sim||!moduleState.lastRun)return;
 selectOptions();renderMetrics();renderSaved();
 el('liveForkName').placeholder='new-alternative-id';
 el('liveDelete').disabled=!moduleState.saved.has(moduleState.selected);
}
function setYear(year){
 moduleState.year=Math.max(2026,Math.min(2037,Number(year)));
 renderMetrics();
 moduleState.api.updateYear(moduleState.year);
}
function syncYear(year){moduleState.year=Math.max(2026,Math.min(2037,Number(year)));if(moduleState.lastRun)renderMetrics();}
function syncScenario(index){if(!moduleState.world||!moduleState.sim||!moduleState.records.size)return;const rec=moduleState.world.scenarios[index];if(rec&&moduleState.records.has(rec.id)){
 moduleState.selected=rec.id;moduleState.lastRun=moduleState.records.get(rec.id).run;render();
}}
function syncWorld(id){
 const index=moduleState.world.scenarios.findIndex(s=>s.id===id);
 if(index>=0){moduleState.app.scenario=index;el('scenarioSelect').value=index;moduleState.api.renderYear();}
}
function register(spec,run){
 if(run.authority_layer!=='scenario_only'||run.source_world_sha256!==moduleState.sim.graphDigest||run.model_sha256!==moduleState.sim.modelHash)
  throw Error('Scenario record has mismatched authority/source');
 const id=spec.id;
 moduleState.records.set(id,{spec:clone(spec),run});
 if(!moduleState.world.scenarios.some(s=>s.id===id)){
  const option=document.createElement('option');option.value=moduleState.world.scenarios.length;option.textContent=id+' · simulated';
  el('scenarioSelect').append(option);
  moduleState.world.scenarios.push({id,name:id,authority_layer:'scenario_only',
    run_sha256:run.run_sha256,source_world_sha256:run.source_world_sha256,
    model_sha256:run.model_sha256,snapshots:run.snapshots.map(s=>({year:s.year,state:s.state,
     indicators:s.indicators,scenario_event_ids:s.scenario_event_ids,snapshot_sha256:s.sha256}))});
 }
}
function select(id){
 const rec=moduleState.records.get(id);
 if(!rec)return;
 moduleState.selected=id;moduleState.lastRun=rec.run;syncWorld(id);render();
 status('Scenario '+id+' loaded. Historical titles remain canonical; all numerical changes are hypothetical.');
}
async function verifyParent(spec){
 const branch=spec.branch;
 if(!branch)return;
 const parent=moduleState.records.get(branch.parent_scenario_id);
 if(!parent)throw Error('Missing parent scenario: '+branch.parent_scenario_id);
 if(parent.run.run_sha256!==branch.parent_run_sha256)throw Error('Parent hash mismatch; lineage cannot be verified');
 const retained=parent.spec.events.filter(x=>x.year<=branch.fork_year);
 const candidate=spec.events.filter(x=>x.year<=branch.fork_year);
 if(moduleState.api.AE_Sim.canonical(retained)!==moduleState.api.AE_Sim.canonical(candidate))
  throw Error('Branch changed historical interventions before its fork year');
 const replay=await moduleState.sim.run(spec);
 for(let i=0;i<=branch.fork_year-2026;i++){
  if(moduleState.api.AE_Sim.canonical(parent.run.snapshots[i].state)!==moduleState.api.AE_Sim.canonical(replay.snapshots[i].state))
    throw Error('Branch changed pre-fork state');
 }
}
function saveDisk(){
 const store=checkedStorage();
 if(!store){status('Local storage blocked. Export JSON for backup.',true);return false;}
 const entries=[...moduleState.saved.values()].slice(0,30);
 try{store.setItem(STORE,JSON.stringify({schema:'american-empire.p5.browser-saves.v1',
   graph_sha256:moduleState.sim.graphDigest,model_sha256:moduleState.sim.modelHash,scenarios:entries}));return true}
 catch(e){status('Cannot save to browser storage. Export your run JSON.',true);return false;}
}
async function loadDisk(){
 const store=checkedStorage();if(!store)return;
 let payload;
 try{payload=JSON.parse(store.getItem(STORE)||'null');}catch{return;}
 if(!payload)return;
 if(payload.schema!=='american-empire.p5.browser-saves.v1'||payload.graph_sha256!==moduleState.sim.graphDigest
 ||payload.model_sha256!==moduleState.sim.modelHash||!Array.isArray(payload.scenarios)){status('Saved worlds belong to another model revision. Export or restore a compatible backup.',true);return;}
 let unresolved=payload.scenarios.slice(0,30),passes=0;
 while(unresolved.length&&passes<30){
  passes++;const remaining=[];
  for(const spec of unresolved){
   try{
    if(samples.has(spec.id))throw Error('cannot overwrite built-in examples');
    if(moduleState.records.has(spec.id))throw Error('duplicate saved scenario');
    const checked=moduleState.sim.validate(spec);
    if(checked.branch&&!moduleState.records.has(checked.branch.parent_scenario_id)){remaining.push(spec);continue;}
    await verifyParent(checked);
    const run=await moduleState.sim.run(checked);
    register(checked,run);moduleState.saved.set(checked.id,checked);
   }catch(e){status('One or more saved scenarios could not be verified and were excluded: '+e.message,true);}
  }
  if(remaining.length===unresolved.length)break;
  unresolved=remaining;
 }
 if(unresolved.length)status('Some saved scenarios reference missing parent runs and were not loaded.',true);
}
async function createFork(){
 if(moduleState.busy)return;moduleState.busy=true;
 try{
  const name=el('liveForkName').value.trim(),year=moduleState.year;
  if(moduleState.records.has(name))throw Error('Choose a unique branch name');
  if(year<=2026)throw Error('Select a decision year from 2027 through 2037');
  const type=el('liveAction').value,subject=el('liveSubject').value,intensity=Number(el('liveIntensity').value);
  const event={id:'choice-'+year+'-'+type.replaceAll('_','-'),year,type,intensity};
  if(subject)event.subject=subject;
  const parent=moduleState.records.get(moduleState.selected);
  const fork=await moduleState.sim.fork(parent.spec,name,year,event);
  await verifyParent(fork.spec);
  register(fork.spec,fork.run);
  select(name);
  status('Created '+name+'. Preserved all pre-'+year+' states; '+type+' applied in '+year+'. No canon promoted.');
 }catch(e){status(e.message,true);}
 finally{moduleState.busy=false;}
}
async function runReplay(){
 try{
 const record=moduleState.records.get(moduleState.selected);
 const report=await moduleState.sim.replay(record.run);
 status('REPLAY VERIFIED · '+report.snapshots+' annual snapshots · '+report.events+' recorded interventions · SHA '+report.run_sha256.slice(0,18)+'…');
 }catch(e){status('Replay FAILED: '+e.message,true);}
}
async function compare(){
 try{
 const left=moduleState.records.get(el('liveCompare').value),right=moduleState.records.get(moduleState.selected);
 if(!left||!right)throw Error('Choose two available scenarios');
 const result=await moduleState.sim.compare(left.spec,right.spec);
 const deltas=Object.entries(result.final_variable_deltas_right_minus_left)
   .map(([k,v])=>'<div><span>'+escape(k)+'</span><b>'+((v>0)?'+':'')+v+'</b></div>').join('');
 el('liveComparison').innerHTML='<p><strong>RIGHT:</strong> '+escape(right.spec.id)+'</p><p><strong>LEFT:</strong> '+escape(left.spec.id)+'</p>'+
 '<p>First divergence: <strong>'+escape(result.first_divergent_year??'identical')+'</strong></p>'+
 '<p>2037 change, right minus left:</p><div class="sim-delta-list">'+deltas+'</div>'+
 '<p class="tiny muted">Comparison is model-only. It does not change historical canon.</p>';
 status('Comparison recomputed from exact source rules.');
 }catch(e){status(e.message,true);}
}
function save(){
 const item=moduleState.records.get(moduleState.selected);
 if(samples.has(item.spec.id)){status('Built-in examples are permanent references. Branch one to create a savable history.',true);return;}
 moduleState.saved.set(item.spec.id,clone(item.spec));
 if(saveDisk()){renderSaved();status('Saved '+item.spec.id+' locally on this device. Export JSON for durable transfer.');}
}
async function forget(){
 const id=moduleState.selected;if(!moduleState.saved.has(id))return;
 // Keep active record in memory so downstream branches remain traceable this session.
 moduleState.saved.delete(id);saveDisk();select('baseline');renderSaved();
 status('Removed saved copy of '+id+'. Session copy remains until refresh, to preserve parent lineage.');
}
function download(name,body){
 const blob=new Blob([JSON.stringify(body,null,2)+'\n'],{type:'application/json'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;
 document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);
}
async function importJSON(file){
 if(!file)return;
 try{
 if(file.size>1500000)throw Error('File exceeds 1.5 MB import limit');
 const parsed=JSON.parse(await file.text());
 const isRun=parsed.schema===moduleState.api.AE_Sim.RUN_SCHEMA;
 const spec=isRun?parsed.scenario:parsed;
 const clean=moduleState.sim.validate(spec);
 if(samples.has(clean.id))throw Error('Cannot replace a built-in source example');
 if(moduleState.records.has(clean.id))throw Error('Scenario ID exists; choose another ID in imported JSON');
 await verifyParent(clean);
 const run=await moduleState.sim.run(clean);
 if(isRun)await moduleState.sim.replay(parsed);
 register(clean,run);moduleState.saved.set(clean.id,clean);saveDisk();select(clean.id);
 status('Imported and replayed '+clean.id+'; source and lineage validated.');
 }catch(e){status('Import rejected: '+e.message,true);}
 finally{el('liveImportFile').value='';}
}
async function init({world,model,state,api}){
 moduleState.world=world;moduleState.app=state;moduleState.api=api;
 const sim=new global.AE_Sim.Simulation({model,graphDigest:world.source.world_graph_sha256,world});
 await sim.initialize();moduleState.sim=sim;
 for(const original of world.scenarios){
  // Keep original reference run hashes as the validation oracle, not generated fiction.
  const path={baseline:'baseline', 'independent-corridor':'independent-corridor','high-integration':'high-integration'}[original.id];
  if(!path)throw Error('Unexpected P4 reference scenario');
 }
 // Original input specs are shipped by build_web.py alongside the P3 model.
 const specimens=api.referenceScenarios;
 for(const reference of specimens){
   const run=await sim.run(reference);
   const locked=world.scenarios.find(x=>x.id===reference.id);
   if(!locked||run.run_sha256!==locked.run_sha256||
       run.snapshots.some((snap,i)=>snap.sha256!==locked.snapshots[i].snapshot_sha256))
     throw Error('P5 engine parity FAILED against Python P3 scenario '+reference.id);
   register(reference,run);
 }
 for(const [name,action] of Object.entries(model.actions)){
  const option=document.createElement('option');option.value=name;option.textContent=action.label;
  el('liveAction').append(option);
 }
 for(const e of [...world.nodes,...world.people]){
  const option=document.createElement('option');option.value=e.id;option.textContent=e.name+' / '+e.id;
  el('liveSubject').append(option);
 }
 el('liveSubject').value='system:S1';
 for(const id of ['liveYear','liveIntensity'])el(id).addEventListener('input',ev=>{
  if(id==='liveYear')setYear(ev.target.value);else el('liveIntensityText').textContent=ev.target.value;
 });
 el('liveScenario').addEventListener('change',e=>select(e.target.value));
 el('liveBack').addEventListener('click',()=>setYear(moduleState.year-1));
 el('liveAdvance').addEventListener('click',()=>setYear(moduleState.year+1));
 el('liveApply').addEventListener('click',createFork);
 el('liveReplay').addEventListener('click',runReplay);
 el('liveCompareButton').addEventListener('click',compare);
 el('liveSave').addEventListener('click',save);
 el('liveDelete').addEventListener('click',forget);
 el('liveExport').addEventListener('click',()=>{
  const rec=moduleState.records.get(moduleState.selected);
  download('american-empire-'+rec.spec.id+'-p5-run.json',rec.run);
  status('Exported complete deterministic receipt, including source hashes and per-year state.');
 });
 el('liveImportButton').addEventListener('click',()=>el('liveImportFile').click());
 el('liveImportFile').addEventListener('change',e=>importJSON(e.target.files[0]));
 await loadDisk();
 const current=moduleState.records.get('baseline');
 moduleState.selected='baseline';moduleState.lastRun=current.run;
 selectOptions();render();setYear(state.year);status('P3 parity PASS · 3 Python reference scenarios · all 12 snapshot digests · model '+sim.modelHash.slice(0,12)+'…');
 return true;
}
global.AE_Live={init,render,syncYear,syncScenario,select,createFork,compare,runReplay,current:()=>({run:moduleState.lastRun,year:moduleState.year,scenario_id:moduleState.selected})};
})(window);
