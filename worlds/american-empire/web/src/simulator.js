/* P5 browser-native deterministic P3 simulation. No network, workers, or canon mutation.
 * All decisions are scenario_only; results must match the Python P3 reference hashes.
 */
(function(global){
'use strict';
const YEAR0=2026,YEAR1=2037,VARIABLES=['V1','V2','V3','V4','V5','V6','V7'];
const SCHEMA='american-empire.scenario.v1';
const RUN_SCHEMA='american-empire.scenario-run.v1';
const LIMITATIONS=[
 'Not established history: variables seeded from original Reality Matrix but evolved only under illustrative P3 rules',
 'Historical titles are fixed reference anchors; model outcomes are fictional counterfactual projections',
 'Subject tags do not currently produce geographic or individual effects',
 'No P1 or P2 canon source was changed'
];
function fail(message){throw new Error('P5 scenario rejected: '+message);}
function cloned(value){return JSON.parse(JSON.stringify(value));}
function canonical(value){
 if(value===null||typeof value!=='object')return JSON.stringify(value);
 if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
 return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
}
async function hash(value){
 if(!global.crypto||!global.crypto.subtle)fail('SHA-256 unavailable in this browser context');
 const bytes=new TextEncoder().encode(canonical(value));
 const digest=await global.crypto.subtle.digest('SHA-256',bytes);
 return [...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');
}
function allowedFields(object,required,optional=[],label='object'){
 if(!object||typeof object!=='object'||Array.isArray(object))fail(label+' must be an object');
 const allowed=[...required,...optional];
 for(const key of Object.keys(object))if(!allowed.includes(key))fail('unexpected '+label+' field '+key);
 for(const key of required)if(!Object.hasOwn(object,key))fail('missing '+label+' field '+key);
}
function strictInt(v,low,high,label){if(!Number.isInteger(v)||v<low||v>high)fail(label+' must be integer '+low+'..'+high);return v;}
function bounds(x){return Math.max(0,Math.min(100,x));}
function indicators(v){
 const gap=100-v.V1,trust=100-v.V2;
 return {service_gap_proxy:gap,elite_defection_proxy:v.V3,security_futility_proxy:v.V5,
  local_trust_proxy:trust,viable_alternatives_proxy:v.V4,
  accession_pressure_raw:gap+v.V3+v.V5-trust-v.V4,dependency_gap:v.V1-v.V6};
}
function feedback(v){
 const d={V1:0,V2:0,V3:0,V4:0,V5:0,V6:0,V7:0};
 if(v.V7>=65)d.V1+=1;else if(v.V7<35)d.V1-=1;
 if(v.V1>=60)d.V2+=2;else if(v.V1<40)d.V2-=2;
 if(v.V6<30)d.V2-=1;
 if(v.V1>=65)d.V3+=1;
 if(v.V4>60)d.V3-=1;
 if(v.V3>65)d.V4-=2;
 if(v.V5>60)d.V5+=1;
 if(v.V3>60)d.V6-=1;
 if(v.V2<30)d.V7-=1;
 if(v.V6<20)d.V7-=1;
 return Object.fromEntries(Object.entries(d).filter(([k,v])=>v!==0));
}
function apply(state,delta){
 const next={},realized={};
 for(const k of VARIABLES){next[k]=bounds(state[k]+(delta[k]||0));if(next[k]!==state[k])realized[k]=next[k]-state[k];}
 return {state:next,realized};
}
function validate(spec,sim){
 allowedFields(spec,['schema','id','events'],['description','source_world_sha256','branch'],'scenario');
 if(spec.schema!==SCHEMA)fail('scenario schema mismatch');
 if(typeof spec.id!=='string'||!/^[a-z][a-z0-9-]{0,63}$/.test(spec.id))fail('invalid scenario ID');
 if(Object.hasOwn(spec,'source_world_sha256')&&spec.source_world_sha256!==sim.graphDigest)fail('source world hash mismatch');
 if(Object.hasOwn(spec,'description')&&(typeof spec.description!=='string'||spec.description.length>500))fail('description invalid');
 if(Object.hasOwn(spec,'branch')){
  const b=spec.branch;allowedFields(b,['parent_scenario_id','parent_run_sha256','fork_year'],[],'branch');
  if(typeof b.parent_scenario_id!=='string'||!/^[a-z][a-z0-9-]{0,63}$/.test(b.parent_scenario_id))fail('invalid parent ID');
  if(typeof b.parent_run_sha256!=='string'||!/^[a-f0-9]{64}$/.test(b.parent_run_sha256))fail('invalid parent hash');
  strictInt(b.fork_year,YEAR0,YEAR1-1,'fork year');
 }
 if(!Array.isArray(spec.events)||spec.events.length>100)fail('at most 100 events');
 const seen=new Set(),events=[];
 for(const original of spec.events){
  allowedFields(original,['id','year','type','intensity'],['subject','note'],'event');
  if(typeof original.id!=='string'||!/^[a-z][a-z0-9_-]{0,63}$/.test(original.id)||seen.has(original.id))fail('invalid/duplicate event ID');
  seen.add(original.id);strictInt(original.year,YEAR0,YEAR1,'year');strictInt(original.intensity,1,3,'intensity');
  if(typeof original.type!=='string'||!Object.hasOwn(sim.model.actions,original.type))fail('unknown action');
  if(Object.hasOwn(original,'subject')&&(!sim.entityIds.has(original.subject)))fail('unresolved entity subject');
  if(Object.hasOwn(original,'note')&&(typeof original.note!=='string'||original.note.length>300))fail('note invalid');
  events.push(cloned(original));
 }
 const result=cloned(spec);result.events=events.sort((a,b)=>a.year-b.year||(a.id<b.id?-1:a.id>b.id?1:0));
 return result;
}
class Simulation{
 constructor({model,graphDigest,world}){
  this.model=cloned(model);this.graphDigest=graphDigest;this.world=world;
  if(model.schema!=='american-empire.simulation-model.v1'||model.classification!=='illustrative_mechanics_not_established_history'
   ||model.annual_feedback_algorithm!=='simultaneous_p3_feedback_v1'
   ||model.initial_year!==YEAR0||model.last_year!==YEAR1
   ||canonical(model.variable_ids)!==canonical(VARIABLES))fail('unknown P3 model rules');
  this.entityIds=new Set([...world.nodes,...world.people,...world.variables].map(x=>x.id));
  for(const year of world.years)this.entityIds.add('event:'+year.year);
  this.seed=Object.fromEntries(world.variables.map(n=>[n.attributes.id,n.attributes.initial]));
  if(canonical(Object.keys(this.seed).sort())!==canonical(VARIABLES))fail('missing source variable');
  this.modelHash=null;
 }
 async initialize(){
  this.modelHash=await hash(this.model);
  if(this.modelHash!==this.world.source.simulation_model_sha256)fail('P3 source model hash mismatch');
  if(this.world.source.world_graph_sha256!==this.graphDigest)fail('P2 world graph hash mismatch');
  return this;
 }
 validate(spec){return validate(spec,this);}
 async run(scenario){
  if(!this.modelHash)fail('initialize before running');
  const spec=validate(scenario,this);
  let current=cloned(this.seed),history=[],receipts=[];
  let previous=await hash({genesis:'american-empire.p3.v1',source:this.graphDigest,model:this.modelHash,scenario_id:spec.id});
  for(let year=YEAR0;year<=YEAR1;year++){
   const fb=year>YEAR0?feedback(current):{};
   const step=apply(current,fb);current=step.state;
   const yearEvents=spec.events.filter(e=>e.year===year);
   for(const event of yearEvents){
    const declared=Object.fromEntries(Object.entries(this.model.actions[event.type].deltas).map(([k,v])=>[k,v*event.intensity]));
    const before=cloned(current),stepEvent=apply(current,declared);current=stepEvent.state;
    receipts.push({event_id:event.id,year,type:event.type,intensity:event.intensity,subject:event.subject??null,
     declared_delta:declared,applied_delta:stepEvent.realized,before,after:cloned(current),authority_layer:'scenario_only'});
   }
   const anchor=this.world.years[year-YEAR0];
   const snap={year,canon_anchor:{event_id:'event:'+year,title:anchor.title,source:anchor.source,is_historical_reference_only:true},
    state:cloned(current),indicators:indicators(current),feedback_applied:step.realized,
    scenario_event_ids:yearEvents.map(e=>e.id),previous_sha256:previous,authority_layer:'scenario_only'};
   snap.sha256=await hash(snap);previous=snap.sha256;history.push(snap);
  }
  const out={schema:RUN_SCHEMA,authority_layer:'scenario_only',
    source_world_sha256:this.graphDigest,model_sha256:this.modelHash,model_id:this.model.id,
    scenario:spec,initial_seed:cloned(this.seed),snapshots:history,event_receipts:receipts,
    final_state:cloned(current),final_indicators:indicators(current),final_snapshot_sha256:previous,
    limitations:cloned(LIMITATIONS)};
  out.run_sha256=await hash(out);return out;
 }
 async replay(receipt){
  if(!receipt||receipt.schema!==RUN_SCHEMA)fail('invalid run receipt');
  if(receipt.source_world_sha256!==this.graphDigest||receipt.model_sha256!==this.modelHash)fail('source drift');
  const result=await this.run(receipt.scenario);
  if(canonical(result)!==canonical(receipt))fail('receipt differs from deterministic replay');
  return {verified:true,run_sha256:result.run_sha256,final_snapshot_sha256:result.final_snapshot_sha256,
   snapshots:result.snapshots.length,events:result.event_receipts.length};
 }
 async fork(parent,name,year,event){
  if(typeof name!=='string'||!/^[a-z][a-z0-9-]{0,63}$/.test(name)||name===parent.id)fail('invalid fork name');
  strictInt(year,YEAR0+1,YEAR1,'fork event year');
  const original=validate(parent,this),receipt=await this.run(original);
  const child={schema:SCHEMA,id:name,
   description:'Counterfactual branch of '+original.id+' after '+(year-1)+'; no canon promotion',
   source_world_sha256:this.graphDigest,
   branch:{parent_scenario_id:original.id,parent_run_sha256:receipt.run_sha256,fork_year:year-1},
   events:[...original.events.filter(x=>x.year<year),cloned(event)]};
  const actual=await this.run(child);
  for(let i=0;i<year-YEAR0;i++){
   if(canonical(actual.snapshots[i].state)!==canonical(receipt.snapshots[i].state))fail('fork rewrote earlier state');
  }
  return {spec:child,run:actual,parent:receipt};
 }
 async compare(left,right){
  const a=await this.run(left),b=await this.run(right);
  let first=null;
  for(let i=0;i<a.snapshots.length;i++){
   if(canonical(a.snapshots[i].state)!==canonical(b.snapshots[i].state)){first=a.snapshots[i].year;break;}
  }
  return {schema:'american-empire.scenario-comparison.v1',authority_layer:'scenario_only',
   source_world_sha256:this.graphDigest,model_sha256:this.modelHash,
   left:{id:a.scenario.id,run_sha256:a.run_sha256},right:{id:b.scenario.id,run_sha256:b.run_sha256},
   first_divergent_year:first,
   final_variable_deltas_right_minus_left:Object.fromEntries(VARIABLES.map(k=>[k,b.final_state[k]-a.final_state[k]])),
   final_indicator_deltas_right_minus_left:Object.fromEntries(Object.keys(a.final_indicators).map(k=>[k,b.final_indicators[k]-a.final_indicators[k]])),
   not_a_canon_revision:true};
 }
}
global.AE_Sim=Object.freeze({Simulation,hash,canonical,SCHEMA,RUN_SCHEMA});
})(typeof window!=='undefined'?window:globalThis);
