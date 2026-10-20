/* P7 deterministic agent simulation — fiction-aware autonomy, bounded knowledge,
 * private memories, budgets, relationships and local actions. NO generative
 * model or remote agent executes here. Canon "unknowns" are permanently sealed.
 */
(function(global){
'use strict';
const clone=x=>JSON.parse(JSON.stringify(x)), clamp=(v,a=0,b=100)=>Math.min(b,Math.max(a,v));
const DIM={relief:"relief",civic_rights:"liberty",coordinate:"trade",investigate:"truth",restrict:"order",independent_network:"liberty"};
const ACTIONS=["relief","civic_rights","coordinate","investigate","restrict","independent_network"];
const PRIO=["relief","liberty","truth","order","trade"];
const validateInt=(n,a,b)=>Number.isInteger(n)&&n>=a&&n<=b;
const canon=()=>global.AE_Sim?.canonical;
class InhabitantEngine{
 constructor(manifest,p3,p6,geo){
  if(manifest?.schema!=="american-empire.p7-inhabitants.v1"||manifest.authority_layer!=="scenario_only")
   throw Error('P7 actor manifest unknown');
  if(p3?.schema!=="american-empire.scenario-run.v1"||p3.authority_layer!=="scenario_only"||p3.snapshots?.length!==12)
   throw Error('P7 requires verified P3 history');
  if(p6?.schema!=="american-empire.p6-regional-run.v1"||p6.p3_run_sha256!==p3.run_sha256||p6.snapshots?.length!==12)
   throw Error('P7 requires P6 driven by same verified P3 run');
  if(geo?.schema!=="american-empire.geography.v1")throw Error('P7 geographic source missing');
  this.manifest=manifest;this.p3=p3;this.p6=p6;this.geo=geo;
  this.agents=[...manifest.protagonists,...manifest.organizations,...(manifest.film_cast||[])];this.byId=new Map(this.agents.map(a=>[a.id,a]));
  if(this.agents.length!==12||this.byId.size!==12||manifest.film_cast?.length!==2)throw Error('AE actor roster drift');
  this.places=new Set(geo.nodes.map(n=>n.id));this.edges=geo.routes;
  for(const a of this.agents){
   if(!this.places.has(a.place)||!validateInt(a.initial_budget,0,100))throw Error('Invalid agent location/resources');
   for(const p of PRIO)if(!validateInt(a.priorities[p],0,5))throw Error('Invalid agent goals');
  }
  this.linkSeed={};
  for(const e of manifest.trust_links){
   if(!this.byId.has(e.from)||!this.byId.has(e.to)||!validateInt(e.trust,0,100))
    throw Error('Bad social link');
   this.linkSeed[e.from+'>'+e.to]=e.trust;
  }
  for(const key of ACTIONS)if(!manifest.actions[key])throw Error('P7 missing action '+key);
  this.sourceSHA=manifest.source_manifest_sha256;
  if(!/^[a-f0-9]{64}$/.test(this.sourceSHA||''))throw Error('P7 manifest provenance hash absent');
 }
 validate(interventions){
  if(!Array.isArray(interventions)||interventions.length>20)throw Error('P7 intervention count limit');
  const seen=new Set();
  return interventions.map(x=>{
   if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).some(k=>!['id','agent','year','priority'].includes(k)))
    throw Error('P7 unexpected intervention fields');
   if(typeof x.id!=='string'||!/^[a-z][a-z0-9-]{0,63}$/.test(x.id)||seen.has(x.id))throw Error('P7 intervention ID invalid');
   seen.add(x.id);
   if(!this.byId.has(x.agent)||!validateInt(x.year,2026,2037)||!PRIO.includes(x.priority))
    throw Error('P7 agent, year, or priority invalid');
   return clone(x);
  }).sort((a,b)=>a.year-b.year||(a.id<b.id?-1:a.id>b.id?1:0));
 }
 async run(interventions=[]){
  const spec=this.validate(interventions);
  let people=Object.fromEntries(this.agents.map(a=>[a.id,{
   id:a.id,place:a.place,budget:a.initial_budget,standing:50,
   knowledge:(a.kind==='character'||a.kind==='film_character')&&a.known_from_year===2026?[a.canon_knows]:[],
   memory:(a.kind==='character'||a.kind==='film_character')&&a.known_from_year===2026?[{year:2026,type:a.kind==='film_character'?'film_scene_anchor':'canon_knowledge_anchor',text:a.canon_knows,source:a.source_pointer}]:[],
   last_action:null
  }]));
  let trust=clone(this.linkSeed),shift=Object.fromEntries(this.geo.nodes.map(n=>[n.id,{service:0,independence:0}]));
  let delayedMessages=[];
  let previous=await global.AE_Sim.hash({genesis:'american-empire.p7.v1',source:this.sourceSHA,
   p3:this.p3.run_sha256,p6:await global.AE_Sim.hash(this.p6.events)});
  const years=[];
  for(let year=2026;year<=2037;year++){
   const geo=this.p6.snapshots[year-2026],macro=this.p3.snapshots[year-2026].state;
   const before=clone(people);
   const observed={};
   const delivered=delayedMessages.filter(m=>m.year===year);
   for(const a of this.agents){
    const p=people[a.id],base=geo.places[a.place],carry=shift[a.place];
    if((a.kind==='character'||a.kind==='film_character')&&year===a.known_from_year&&!p.knowledge.includes(a.canon_knows)){
     p.knowledge.push(a.canon_knows);
     p.memory.push({year,type:a.kind==='film_character'?'film_scene_anchor':'canon_knowledge_anchor',text:a.canon_knows,source:a.source_pointer});
    }
    const local={service:clamp(base.service+carry.service),independence:clamp(base.independence+carry.independence)};
    const messages=delivered.filter(m=>m.to===a.id&&trust[m.from+'>'+a.id]>=42).slice(0,4);
    for(const m of messages){
     if(!p.knowledge.includes(m.fact))p.knowledge.push(m.fact);
     p.memory.push({year,type:'received_message',from:m.from,text:m.fact});
    }
    if(local.service<45)p.memory.push({year,type:'observation',text:'Material services are strained at '+a.place+' ('+local.service+'/100 simulation index).'});
    if(local.independence<40)p.memory.push({year,type:'observation',text:'Practical autonomy is constrained at '+a.place+' ('+local.independence+'/100 model).'});
    p.budget=clamp(p.budget+9);
    observed[a.id]={...local,year,message_count:messages.length};
   }
   const decisions=[];
   for(const a of this.agents){
    const person=people[a.id],v=observed[a.id],budget=person.budget;
    const active=spec.filter(e=>e.agent===a.id&&e.year<=year).at(-1);
    const best=this.choose(a,v,macro,trust,active,budget);
    const def=this.manifest.actions[best],canSpend=!!def&&budget>=def.cost;
    if(!canSpend){decisions.push({id:a.id,action:'observe',year,place:a.place,cost:0,reason:'insufficient budget',priority:active?.priority||'native',influence:{service:0,independence:0}});continue;}
    decisions.push({id:a.id,action:best,year,place:a.place,cost:def.cost,
      reason:'goal-weighted policy; observed local service='+v.service+', autonomy='+v.independence+
       '; global exit='+macro.V6+'; chosen priority='+(active?.priority||'native'),
      priority:active?.priority||'native',influence:{service:def.service,independence:def.independence}});
   }
   const yearlyShift=Object.fromEntries(this.geo.nodes.map(n=>[n.id,{
    service:Math.trunc(shift[n.id].service*0.7),independence:Math.trunc(shift[n.id].independence*0.7)}]));
   const upcoming=[];
   for(const d of decisions){
    const p=people[d.id];
    if(d.action==='observe')continue;
    const a=this.manifest.actions[d.action];p.budget-=a.cost;p.last_action=d.action;
    const local=yearlyShift[d.place];local.service=clamp(local.service+a.service,-25,25);
    local.independence=clamp(local.independence+a.independence,-25,25);
    p.standing=clamp(p.standing+a.trust);
    p.memory.push({year,type:'own_decision',text:a.label+' at '+d.place+'; scenario-only, not canon.'});
    // Only socially connected actors receive PUBLIC action summaries next year.
    // Neither internal memory nor sealed canon unknowns may be transmitted.
    const peers=Object.keys(trust).filter(k=>k.startsWith(d.id+'>')&&trust[k]>=42);
    for(const key of peers){
     const dest=key.split('>')[1];
     upcoming.push({year:year+1,from:d.id,to:dest,fact:'Public report: '+d.id+' '+a.label.toLowerCase()+' in '+d.place+' during '+year+' (simulation).'});
     trust[key]=clamp(trust[key]+(d.action==='coordinate'?3:d.action==='restrict'?-3:1));
    }
   }
   // One-year lag for downstream social and spatial effects, not free instant contagion.
   for(const edge of this.edges){
    const source=shift[edge.from];
    yearlyShift[edge.to].service=clamp(yearlyShift[edge.to].service+
      Math.trunc(source.service*edge.weight/22),-25,25);
   }
   shift=yearlyShift;
   delayedMessages=upcoming;
   for(const a of this.agents){
    const p=people[a.id];
    p.knowledge=p.knowledge.slice(-30);
    p.memory=p.memory.slice(-40);
    if(a.canon_unknown_sealed&&p.knowledge.some(k=>k===a.canon_unknown_sealed))throw Error('P7 sealed canon fact leaked');
   }
   const effects=Object.fromEntries(this.geo.nodes.map(n=>[n.id,{
    service:clamp(geo.places[n.id].service+shift[n.id].service),
    independence:clamp(geo.places[n.id].independence+shift[n.id].independence),
    delta_service:shift[n.id].service,delta_independence:shift[n.id].independence
   }]));
   const frame={year,people:clone(people),trust:clone(trust),decisions,places:effects,
     previous_sha256:previous,authority_layer:'scenario_only',
     canon_anchor_reference_only:this.p3.snapshots[year-2026].canon_anchor.title};
   frame.sha256=await global.AE_Sim.hash(frame);previous=frame.sha256;years.push(frame);
  }
  const output={schema:'american-empire.p7-run.v1',authority_layer:'scenario_only',
   manifest_sha256:this.sourceSHA,p3_run_sha256:this.p3.run_sha256,
   p6_event_sha256:await global.AE_Sim.hash(this.p6.events),
   interventions:spec,snapshots:years,final_snapshot_sha256:previous,
   limitations:['Deterministic rule-based inhabitants, not generative AI or consciousness',
    'Locations, social trust, event memories and decisions are hypothetical model state',
    'Only direct observations and modeled public action messages are shared; sealed canon unknowns remain hidden',
    'Original P1, P3, P5 and P6 source inputs are read-only']};
  output.run_sha256=await global.AE_Sim.hash(output);return output;
 }
 choose(agent,place,macro,trust,active,budget){
  const p=agent.priorities,needService=(100-place.service)/20,needAutonomy=(100-place.independence)/20;
  const scores={
   relief:p.relief*(2+needService)+needService*3,
   civic_rights:p.liberty*(2+needAutonomy)+needAutonomy*3+(100-macro.V6)/12,
   coordinate:p.trade*3+p.relief*1.5+(macro.V4)/20,
   investigate:p.truth*4+(100-macro.V2)/18,
   restrict:p.order*4+(100-place.service)/16-p.liberty*1.3,
   independent_network:p.liberty*3+needAutonomy*2+p.trade
  };
  if(active){
   for(const [name,dim]of Object.entries(DIM))if(dim===active.priority)scores[name]+=65;
  }
  // No stochastic or untrusted model output. Ties broken by stable name.
  return ACTIONS.filter(k=>budget>=this.manifest.actions[k].cost)
    .sort((a,b)=>scores[b]-scores[a]||a.localeCompare(b))[0]||'observe';
 }
 async replay(receipt){
  if(receipt?.schema!=='american-empire.p7-run.v1'||receipt.manifest_sha256!==this.sourceSHA
   ||receipt.p3_run_sha256!==this.p3.run_sha256)throw Error('P7 source mismatch');
  const actual=await this.run(receipt.interventions);
  if(canon()(actual)!==canon()(receipt))throw Error('P7 receipt tampered or incompatible');
  return {verified:true,run_sha256:actual.run_sha256,years:actual.snapshots.length};
 }
}
global.AE_Inhabitants={Engine:InhabitantEngine};
})(window);
