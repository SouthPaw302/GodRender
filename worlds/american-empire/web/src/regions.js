/* P6 regional counterfactual service network. P3 is immutable macro input;
 * real geography supplies only approximate city-center positions. No actual
 * routes, trade volumes, or local political history inferred from it.
 */
(function(root){
'use strict';
const KEY='american-empire.p6.region.v1', Y0=2026,Y1=2037;
const clamp=(x,a=0,b=100)=>Math.max(a,Math.min(b,x)), clone=x=>JSON.parse(JSON.stringify(x));
function requireFields(obj,keys,tag){if(!obj||typeof obj!=='object'||Array.isArray(obj))throw Error(tag+' invalid');
 for(const k of keys)if(!Object.hasOwn(obj,k))throw Error(tag+' missing '+k);}
function fail(s){throw Error('P6 geographic scenario invalid: '+s)}
class RegionModel{
 constructor(geography,p3){
  requireFields(geography,['schema','nodes','routes','actions','policy'],'geography');
  if(geography.schema!=='american-empire.geography.v1')fail('schema mismatch');
  if(!p3||p3.schema!=='american-empire.scenario-run.v1'||p3.authority_layer!=='scenario_only'||p3.snapshots?.length!==12)fail('P3 receipt missing');
  this.geo=geography;this.p3=p3;
  this.nodes=new Map(geography.nodes.map(n=>[n.id,n]));
  if(this.nodes.size!==geography.nodes.length||this.nodes.size<10)fail('duplicated/missing region');
  for(const node of this.nodes.values()){
   if(!Number.isFinite(node.lat)||!Number.isFinite(node.lon)||Math.abs(node.lat)>90||Math.abs(node.lon)>180||node.numeric_authority!=='scenario_only')fail('bad real-world location');
   for(const k of ['service','independence'])if(!Number.isInteger(node.initial[k])||node.initial[k]<0||node.initial[k]>100)fail('invalid hypothetical seed');
  }
  for(const edge of geography.routes){
   if(!this.nodes.has(edge.from)||!this.nodes.has(edge.to)||!Number.isInteger(edge.weight)||edge.weight<1||edge.weight>5||edge.authority!=='proposed_model_connection_only')fail('unexpected edge');
  }
 }
 validateEvents(events){
  if(!Array.isArray(events)||events.length>40)fail('event limit exceeded');
  const ids=new Set();
  const result=events.map(e=>{
   requireFields(e,['id','year','type','place','intensity'],'event');
   const extras=Object.keys(e).filter(k=>!['id','year','type','place','intensity'].includes(k));
   if(extras.length)fail('extraneous event attributes');
   if(typeof e.id!=='string'||!/^[a-z][a-z0-9-]{0,63}$/.test(e.id)||ids.has(e.id))fail('duplicate/bad event id');
   ids.add(e.id);
   if(!Number.isInteger(e.year)||e.year<2026||e.year>2037||!Number.isInteger(e.intensity)||e.intensity<1||e.intensity>3||!this.nodes.has(e.place)||!Object.hasOwn(this.geo.actions,e.type))fail('invalid event');
   return clone(e);
  });
  return result.sort((a,b)=>a.year-b.year||(a.id<b.id?-1:a.id>b.id?1:0));
 }
 run(events=[]){
  const choices=this.validateEvents(events);
  let previous=Object.fromEntries(this.geo.nodes.map(n=>[n.id,clone(n.initial)]));
  const snapshots=[];
  for(let year=Y0;year<=Y1;year++){
   const i=year-Y0,macro=this.p3.snapshots[i].state,priorMacro=i?this.p3.snapshots[i-1].state:macro;
   const serviceMacro=i?Math.trunc((macro.V1-priorMacro.V1)/2):0;
   const independenceMacro=i?Math.trunc((macro.V6-priorMacro.V6)/3):0;
   const incoming=Object.fromEntries(this.geo.nodes.map(n=>[n.id,[]]));
   // One-year lag: a disturbed upstream port can only influence downstream
   // locations the following year, using the preceding state, not the current.
   for(const edge of this.geo.routes){
    const src=previous[edge.from],dst=previous[edge.to];
    const diffusion=clamp(Math.trunc((src.service-dst.service)*edge.weight/20),-6,6);
    incoming[edge.to].push({edge:edge.id,from:edge.from,diffusion});
   }
   let next={};
   for(const n of this.geo.nodes){
    const inputs=incoming[n.id],pressure=clamp(inputs.reduce((sum,x)=>sum+x.diffusion,0),-8,8);
    next[n.id]={
     service:clamp(previous[n.id].service+(i?serviceMacro+pressure:0)),
     independence:clamp(previous[n.id].independence+independenceMacro),
     incoming_pressure:i?pressure:0,
     links:inputs.length
    };
   }
   const receipts=[];
   for(const action of choices.filter(a=>a.year===year)){
    const delta=this.geo.actions[action.type].deltas, before=clone(next[action.place]);
    next[action.place].service=clamp(before.service+action.intensity*delta.service);
    next[action.place].independence=clamp(before.independence+action.intensity*delta.independence);
    receipts.push({id:action.id,place:action.place,type:action.type,intensity:action.intensity,
      realized_service:next[action.place].service-before.service,
      realized_independence:next[action.place].independence-before.independence,authority:'scenario_only'});
   }
   const flows=this.geo.routes.map(r=>({id:r.id,from:r.from,to:r.to,
    supply_proxy:Math.floor(Math.min(next[r.from].service,next[r.to].service)*r.weight/5)}));
   snapshots.push({year,places:next,flows,events:receipts,macro:{V1:macro.V1,V4:macro.V4,V6:macro.V6},
     canon_event_reference_only:true,authority_layer:'scenario_only'});
   previous=next;
  }
  return {schema:'american-empire.p6-regional-run.v1',authority_layer:'scenario_only',
   p3_run_sha256:this.p3.run_sha256,p3_source_world_sha256:this.p3.source_world_sha256,
   geo_classification:this.geo.classification,events:choices,snapshots,
   caveat:'All numeric indices and all network edges are fictional local modeling hypotheses.'};
 }
}
root.AE_Regions={RegionModel};
})(window);
