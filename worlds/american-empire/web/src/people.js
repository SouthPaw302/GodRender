/* P7 explorer controls and causal replay. Browser-local persistence only. */
(function(root){
'use strict';
const $=id=>document.getElementById(id), escape=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KEY='american-empire.p7.interventions.v1';
const S={manifest:null,canon:null,geo:null,engine:null,run:null,baseline:null,year:2030,
 selected:'neda',events:[],store:{},inputHash:null,busy:false,token:0};
const clamp=(x,l=2026,h=2037)=>Math.max(l,Math.min(h,x));
function note(message,error=false){const s=$('peopleStatus');s.textContent=message;s.classList.toggle('error-state',error);}
function source(){const p3=root.AE_Live?.current?.()?.run,p6=root.AE_Geo?.getRun?.();
 if(!p3||!p6||p3.run_sha256!==p6.p3_run_sha256)throw Error('P5/P6 shared source history not available');
 return {p3,p6};
}
function slot(){return S.inputHash;}
function save(){
 try{root.localStorage.setItem(KEY,JSON.stringify({schema:'american-empire.p7-browser-saves.v1',
   manifest_sha:S.manifest.source_manifest_sha256,by_source:S.store}));}
 catch{note('Browser storage unavailable; export the P7 run JSON instead.',true);}
}
function load(){
 try{const stored=JSON.parse(root.localStorage.getItem(KEY)||'null');
 if(stored?.schema!=='american-empire.p7-browser-saves.v1'||stored.manifest_sha!==S.manifest.source_manifest_sha256)return;
 if(typeof stored.by_source==='object'&&stored.by_source!==null&&!Array.isArray(stored.by_source))
  for(const [key,v]of Object.entries(stored.by_source)){
   if(/^[a-f0-9]{64}:[a-f0-9]{64}$/.test(key)&&Array.isArray(v)&&v.length<=20)
    S.store[key]=v;
  }
 }catch{}
}
function agentProfile(){return [...S.manifest.protagonists,...S.manifest.organizations,...(S.manifest.film_cast||[])].find(a=>a.id===S.selected);}
function canonicalRecord(){
 const a=agentProfile();
 if(a.kind==='character')return S.canon.point_of_view_characters.find(p=>p.id===a.source_id);
 if(a.kind==='film_character')return S.canon.film_characters.find(p=>p.id===a.source_id);
 return S.canon.actors.find(p=>p.id===a.source_id);
}
function currentFrame(){return S.run.snapshots[S.year-2026];}
function actorState(){return currentFrame().people[S.selected];}
function indexCards(){
 const host=$('peopleCards');host.replaceChildren();
 const frame=currentFrame();
 for(const profile of [...S.manifest.protagonists,...S.manifest.organizations,...(S.manifest.film_cast||[])]){
  const source=profile.kind==='character'?
   S.canon.point_of_view_characters.find(v=>v.id===profile.source_id):profile.kind==='film_character'?
   S.canon.film_characters.find(v=>v.id===profile.source_id):S.canon.actors.find(v=>v.id===profile.source_id);
  const person=frame.people[profile.id],action=person.last_action||'Observing';
  const el=document.createElement('button');el.type='button';
  el.className='people-card'+(profile.id===S.selected?' selected':'');
  el.innerHTML='<span class="people-kind">'+escape(profile.kind)+' · '+escape(profile.place)+'</span>'+
  '<strong>'+escape(source.name)+'</strong><small>'+escape(source.role||source.goal)+'</small>'+
  '<span class="people-current">'+escape(action.replaceAll('_',' '))+'</span>';
  el.addEventListener('click',()=>{S.selected=profile.id;paint();});host.append(el);
 }
}
function memoryFeed(){
 const frame=currentFrame(),p=frame.people[S.selected],source=canonicalRecord();
 $('personFullName').textContent=source.name;
 $('personCanonRole').textContent=source.role||source.goal;
 $('personBudget').textContent=p.budget;
 $('personStanding').textContent=p.standing;
 $('personLocal').textContent=frame.places[p.place].service;
 const anchor=agentProfile();
 $('personCanonKnows').textContent=(anchor.kind==='character'||anchor.kind==='film_character')?
    (p.knowledge.includes(source.knows)?source.knows:'This established knowledge is not yet available to the character in '+S.year+'.'):'Institution goal: '+source.goal;
 const known=$('personKnowledge');known.replaceChildren();
 const accepted=p.knowledge.filter(k=>k!==source.knows);
 if(!accepted.length)known.textContent='No public reports received in this simulation.';
 for(const k of accepted.slice(-7).reverse()){
  const line=document.createElement('div');line.className='people-log-item';line.textContent=k;known.append(line);
 }
 const memory=$('personMemory');memory.replaceChildren();
 const notes=p.memory.slice(-8).reverse();
 for(const e of notes){
  const div=document.createElement('div');div.className='people-log-item';
  div.innerHTML='<small>'+e.year+' · '+escape(e.type.replaceAll('_',' '))+'</small><p>'+escape(e.text)+'</p>';
  memory.append(div);
 }
 const connections=$('peopleConnections');connections.replaceChildren();
 const peers=Object.entries(frame.trust).filter(([key])=>key.startsWith(S.selected+'>')).sort((a,b)=>b[1]-a[1]);
 if(!peers.length)connections.textContent='No direct outgoing communication links in the modeled network.';
 for(const [name,value]of peers){
  const item=document.createElement('div');item.className='people-link';const other=name.split('>')[1];
  item.innerHTML='<strong>'+escape(other)+'</strong><span>Modeled trust '+value+'/100</span>';
  connections.append(item);
 }
 $('personSourceNote').textContent='Source: '+anchor.source_pointer+'. Canonically unknown facts are sealed and cannot enter simulated knowledge automatically. Agent placement and trust values are counterfactual modeling assumptions.';
}
function showDecisions(){
 const frame=currentFrame(),list=$('peopleDecisions');list.replaceChildren();
 const all=frame.decisions;
 for(const d of all){
  const a=S.manifest.actions[d.action];
  const row=document.createElement('button');row.type='button';row.className='people-decision';
  row.innerHTML='<span>'+escape(d.id)+'</span><strong>'+escape(a?.label||'Observe')+'</strong>'+
   '<small>'+escape(d.place)+' · '+(d.influence.service>0?'+':'')+d.influence.service+' service, '+(d.influence.independence>0?'+':'')+d.influence.independence+' autonomy</small>';
  row.addEventListener('click',()=>{S.selected=d.id;paint();});list.append(row);
 }
}
function showComparison(){
 const now=currentFrame(),old=S.baseline.snapshots[S.year-2026];
 const chosen=now.people[S.selected],prior=old.people[S.selected];
 const count=now.decisions.filter((d,i)=>d.action!==old.decisions[i].action).length;
 const delta=now.places[chosen.place].service-old.places[prior.place].service;
 const trust=Object.keys(now.trust).filter(key=>now.trust[key]!==old.trust[key]).length;
 $('personComparison').innerHTML='<div class="people-compare-data"><div><strong>'+count+'</strong><small>different choices this year</small></div>'+
 '<div><strong>'+((delta>0)?'+':'')+delta+'</strong><small>local service vs baseline</small></div>'+
 '<div><strong>'+trust+'</strong><small>altered social links</small></div></div>';
}
function paint(){
 if(!S.run)return;
 $('peopleYear').value=S.year;$('peopleYearValue').textContent=S.year;
 $('peopleP5').textContent=root.AE_Live.current().run.scenario.id;
 indexCards();memoryFeed();showDecisions();showComparison();
}
function moveYear(year){S.year=clamp(Number(year));paint();}
async function refresh(){
 if(!S.manifest)return;
 const epoch=++S.token;S.busy=true;
 try{
  root.AE_Geo.render();
  const {p3,p6}=source(),p6events=await root.AE_Sim.hash(p6.events),key=p3.run_sha256+':'+p6events;
  if(epoch!==S.token)return;
  if(!S.engine||S.inputHash!==key){
   S.engine=new root.AE_Inhabitants.Engine(S.manifest,p3,p6,S.geo);
   S.inputHash=key;S.events=S.store[key]||[];
  }
  S.engine.validate(S.events);
  const [baseline,run]=await Promise.all([S.engine.run([]),S.engine.run(S.events)]);
  if(epoch!==S.token)return;
  S.baseline=baseline;S.run=run;paint();
  note('P7 VERIFIED · '+S.manifest.protagonists.length+' characters · '+S.manifest.organizations.length+' institutions · 12 annual memories · source '+run.manifest_sha256.slice(0,12)+'…');
 }catch(e){note('P7 replay unavailable: '+e.message,true);throw e;}
 finally{S.busy=false;}
}
async function intervene(){
 if(S.busy)return;
 const p=agentProfile(),mode=$('personPriority').value;
 const events=[...S.events,{id:'directive-'+(S.events.length+1),year:S.year,agent:p.id,priority:mode}];
 try{
  S.engine.validate(events);S.events=events;S.store[slot()]=events;save();await refresh();
  note('Applied '+mode+' priority to '+canonicalRecord().name+' from '+S.year+'. Scenario only. Original canon preserved.');
 }catch(e){note(e.message,true);}
}
async function undo(){
 if(!S.events.length)return;
 S.events=S.events.slice(0,-1);S.store[slot()]=S.events;save();await refresh();
 note('Removed last agent directive. Canon was not changed.');
}
async function replay(){
 try{const proof=await S.engine.replay(S.run);
 note('REPLAY VERIFIED · '+proof.years+' years · SHA '+proof.run_sha256.slice(0,20)+'…');}
 catch(e){note('Replay verification failed: '+e.message,true);}
}
function download(){
 const blob=new Blob([JSON.stringify(S.run,null,2)+'\n'],{type:'application/json'}),
  u=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=u;a.download='american-empire-p7-'+root.AE_Live.current().run.scenario.id+'.json';document.body.append(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(u),1500);
 note('Exported source-bound agent history and private simulated memories; no server or Drive upload.');
}
async function importRunnerProposal(file){
 if(!file)return;
 try{
  if(file.size>200000)throw Error('Proposal file too large');
  const data=JSON.parse(await file.text());
  if(data.schema!=='american-empire.p8-population-proposal.v1'
   ||data.authority_layer!=='scenario_only_proposal_not_applied'
   ||data.status!=='proposal_only_requires_observer_approval')
   throw Error('Unexpected proposal format or authority');
  if(data.source_p7_run_sha256!==S.run.run_sha256||data.source_manifest_sha256!==S.run.manifest_sha256)
   throw Error('Runner proposal belongs to another history or source revision');
  if(!Number.isInteger(data.year)||data.year<2026||data.year>2037)throw Error('Year outside history');
  if(!['relief','liberty','truth','order','trade'].includes(data.priority))throw Error('Invalid priority');
  if(![...S.manifest.protagonists,...S.manifest.organizations,...(S.manifest.film_cast||[])].some(a=>a.id===data.actor))
   throw Error('Unknown actor');
  if(data.source_p7_snapshot_sha256!==S.run.snapshots[data.year-2026].sha256)
   throw Error('Runner saw a different annual world state');
  const kind=String(data.backend||'');
  if(kind!=='deterministic_smoke_no_model'&&kind!=='HuggingFaceTB/SmolLM2-135M-Instruct')
   throw Error('Unapproved model backend');
  S.selected=data.actor;S.year=data.year;paint();
  $('personPriority').value=data.priority;
  const human=kind==='deterministic_smoke_no_model'?'TEST SUGGESTION — NO LANGUAGE MODEL EXECUTED':'SMALL-MODEL CANDIDATE — REVIEW BEFORE ACCEPTANCE';
  $('personProposalStatus').textContent=human+': '+data.actor+' · '+data.year+' · '+data.priority+'. Click Create alternative choice to apply it in a hypothetical branch.';
  note('Validated source-bound proposal. No action applied; operator approval required.');
 }catch(e){
  $('personProposalStatus').textContent='Proposal rejected: '+e.message;
  note('Rejected model proposal: '+e.message,true);
 }finally{$('personProposalFile').value='';}
}
async function init({manifest,geo,canon}){
 S.manifest=manifest;S.geo=geo;S.canon=canon;
 if(manifest.schema!=='american-empire.p7-inhabitants.v1'||geo.schema!=='american-empire.geography.v1'
 ||canon?.point_of_view_characters?.length!==5)throw Error('P7 manifest or original canon missing');
 for(const p of manifest.protagonists){
  const match=canon.point_of_view_characters.find(x=>x.id===p.source_id);
  if(!match||match.knows!==p.canon_knows||match.does_not_know!==p.canon_unknown_sealed)
   throw Error('P7 protagonist drift from immutable canon');
 }
 if(manifest.film_cast?.length!==2||canon.film_characters?.length!==2)throw Error('Film cast manifest not present');
 for(const p of manifest.film_cast){
  const source=canon.film_characters.find(x=>x.id===p.source_id);
  if(!source||source.knows!==p.canon_knows||source.does_not_know!==p.canon_unknown_sealed)
   throw Error('P8 same-world film source drift');
 }
 load();
 $('peopleYear').addEventListener('input',e=>moveYear(e.target.value));
 $('peoplePrev').addEventListener('click',()=>moveYear(S.year-1));
 $('peopleNext').addEventListener('click',()=>moveYear(S.year+1));
 $('personApply').addEventListener('click',intervene);
 $('personUndo').addEventListener('click',undo);
 $('personReplay').addEventListener('click',replay);
 $('personExport').addEventListener('click',download);
 $('personLoadProposal').addEventListener('click',()=>$('personProposalFile').click());
 $('personProposalFile').addEventListener('change',e=>importRunnerProposal(e.target.files[0]));
 await refresh();
}
root.AE_People={init,refresh,moveYear,select(id){if([...(S.manifest?.protagonists||[]),...(S.manifest?.organizations||[]),...(S.manifest?.film_cast||[])].some(a=>a.id===id)){S.selected=id;paint();}},getRun:()=>S.run,getBaseline:()=>S.baseline,getEngine:()=>S.engine};
})(window);
