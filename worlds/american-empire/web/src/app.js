/* American Empire browser — source-only; no framework, telemetry or remote scripts. */
'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const svgNS = 'http://www.w3.org/2000/svg';
const state = {world:null, brain:null, year:2027, scenario:0, entity:'system:S1', tab:'world', brainEntries:[], brainItem:null, selectedFx:null};
function svg(tag, attrs={}, value=null) {const n=document.createElementNS(svgNS, tag); for(const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v)); if(value!==null)n.textContent=String(value);return n;}
function safeLink(url){try{const u=new URL(url);return u.protocol==='https:'?u.href:'#';}catch{return '#';}}
const nodeLookup = ()=>[...state.world.nodes,...state.world.people].find(n=>n.id===state.entity);
const getSnapshot = ()=>state.world.scenarios[state.scenario].snapshots[state.year-2026];
const shortText=(value,n=19)=>String(value||'').length>n?String(value).slice(0,n-1)+'…':String(value||'');
function setTab(name){
  if(!['home','world','chronology','brain','production','simulation','earth','inhabitants','cinema'].includes(name))name='world';
  state.tab=name;document.querySelectorAll('.page').forEach(el=>el.classList.toggle('active',el.id===name));
  document.querySelectorAll('[data-tab]').forEach(el=>{el.classList.toggle('active',el.dataset.tab===name);el.setAttribute('aria-selected',String(el.dataset.tab===name));});
  if(name==='production') renderBrief(); if(name==='brain') renderBrainList(); if(name==='simulation') window.AE_Live?.render(); if(name==='earth') window.AE_Geo?.render(); if(name==='inhabitants') window.AE_People?.refresh(); if(name==='cinema') window.AE_Cinema?.render();
  if(location.protocol!=='file:')history.replaceState(null,'','#'+name);
}
function updateYear(y){state.year=Math.max(2026,Math.min(2037,Number(y)));$('yearSlider').value=state.year;$('yearBig').textContent=state.year;
  $('briefYear').value=state.year;renderYear();renderTimeline();renderBrief();window.AE_Live?.syncYear(state.year);}
function renderYear(){const event=state.world.years[state.year-2026], snapshot=getSnapshot();
 $('phaseTitle').textContent=event.title;
 $('phaseSummary').textContent=event.summary;
 $('yearBig').textContent=state.year;
 $('metrics').replaceChildren();
 for(const node of state.world.variables){
    const id=node.attributes.id, n=snapshot.state[id];
    const row=document.createElement('div');row.className='metric';row.innerHTML='<div class="metric-head"><span>'+esc(node.name)+'</span><strong>'+esc(n)+'</strong></div><div class="bar-bg"><div class="bar-fill" style="width:'+Number(n)+'%"></div></div>';
    $('metrics').append(row);
 }
 $('pressure').textContent=snapshot.indicators.accession_pressure_raw;
 $('dependency').textContent=snapshot.indicators.dependency_gap;
 $('footSource').textContent='CANON '+state.world.source.canon_commit.slice(0,8)+' · MODEL '+state.world.source.simulation_model_sha256.slice(0,8);
}
function selectEntity(id){
 if(![...state.world.nodes,...state.world.people].some(n=>n.id===id))return;
 state.entity=id;
 $('briefEntity').value=id;
 renderGraph();renderEntity();renderBrief();
}
function renderGraph(){
 const root=$('graph');root.replaceChildren();
 const defs=svg('defs'), pattern=svg('pattern',{id:'network-grid',width:32,height:32,patternUnits:'userSpaceOnUse'});
 pattern.append(svg('path',{d:'M 32 0 L 0 0 0 32',fill:'none',stroke:'#1b3647','stroke-width':1}));
 defs.append(pattern);root.append(defs);
 root.append(svg('rect',{width:1100,height:650,fill:'#0c2030'}));
 root.append(svg('rect',{width:1100,height:650,fill:'url(#network-grid)'}));
 root.append(svg('line',{x1:560,y1:62,x2:560,y2:585,stroke:'#254557','stroke-dasharray':'5 12'}));
 root.append(svg('text',{x:280,y:55,class:'heading','text-anchor':'middle'},'ACTORS · FACTIONS'));
 root.append(svg('text',{x:845,y:55,class:'heading','text-anchor':'middle'},'THE IMPERIAL STACK'));
 const actors=state.world.nodes.filter(n=>n.kind==='actor'), systems=state.world.nodes.filter(n=>n.kind==='system');
 const positions={};const coords=(items,cx,cy,rx,ry)=>items.forEach((v,i)=>{const theta=-Math.PI/2+i*2*Math.PI/items.length;positions[v.id]=[cx+Math.cos(theta)*rx,cy+Math.sin(theta)*ry];});
 coords(actors,280,329,229,226);coords(systems,840,323,183,180);
 for(const edge of state.world.edges){
   const p=positions[edge.from],q=positions[edge.to];if(!p||!q)continue;
   const isActive=edge.from===state.entity||edge.to===state.entity;
   const line=svg('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],class:'edge'+(edge.strength!==null&&edge.strength<0?' negative':'')+(isActive?' emph':'')});
   const tooltip=svg('title',{},edge.from+' → '+edge.to+' : '+edge.label+' ['+edge.kind+']');
   line.append(tooltip);root.append(line);
 }
 for(const node of state.world.nodes){
   if(!positions[node.id])continue;
   const [x,y]=positions[node.id],type=node.kind, active=node.id===state.entity;
   const g=svg('g',{class:'node'+(active?' active':''),role:'button',tabindex:0,'aria-label':'Inspect '+node.name,transform:'translate('+x+' '+y+')'});
   const color=type==='system'?'#77ced2':'#d5a46d';
   if(active)g.append(svg('circle',{r:35,fill:color,'fill-opacity':.10,stroke:color,'stroke-opacity':.32}));
   g.append(svg('circle',{r:23,fill:'#10293b',stroke:color,'stroke-width':2.2,class:'disc'}));
   g.append(svg('circle',{r:9,fill:color}));
   const len=shortText(node.name,21),label=svg('text',{x:0,y:45},len);
   g.append(label);g.append(svg('text',{x:0,y:60,class:'sub'},node.id));
   g.append(svg('title',{},node.name+' — '+node.id));
   const choose=()=>selectEntity(node.id);
   g.addEventListener('click',choose);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});
   root.append(g);
 }
 $('graphCount').textContent=state.world.nodes.length;
 $('edgeCount').textContent=state.world.edges.length;
}
function renderEntity(){
 const node=nodeLookup();if(!node)return;
 const target=$('entityDetail'); target.replaceChildren();
 target.innerHTML='<div class="entity-kind">'+esc(node.kind)+' · '+esc(node.id)+'</div><h2 class="entity-name">'+esc(node.name)+'</h2>';
 const attr=node.attributes||{}; const dl=document.createElement('dl');dl.className='entity-list';
 const use=['type','role','goal','fear','benefit','control_surface','function','domain','knows','does_not_know','dramatic_question','core_activity','power'];
 for(const k of use){if(attr[k]===undefined||attr[k]===null)continue;const dt=document.createElement('div');dt.className='entity-item';dt.innerHTML='<dt>'+esc(k.replaceAll('_',' '))+'</dt><dd>'+esc(typeof attr[k]==='string'?attr[k]:JSON.stringify(attr[k]))+'</dd>';dl.append(dt);}
 target.append(dl);
 if(node.kind!=='person'){
   const rel=state.world.edges.filter(x=>x.from===node.id||x.to===node.id).slice(0,15);
   if(rel.length){const list=document.createElement('div');list.className='inspector-links';
     for(const r of rel){const other=r.from===node.id?r.to:r.from;const item=state.world.nodes.find(n=>n.id===other);
       const b=document.createElement('button');b.type='button';b.className='rel-pill';b.textContent=(item?.name||other)+' · '+r.label;b.addEventListener('click',()=>selectEntity(other));list.append(b);}target.append(list);}
 }
 const src=node.source||{};
 const detail=document.createElement('div');detail.className='source-citation';detail.textContent='ORIGINAL MATRIX: '+src.path+(src.json_pointer||'')+'\nGit blob '+(src.git_blob_sha1||'unknown');
 target.append(detail);
}
function renderTimeline(){
 const target=$('timelineList');if(!target)return;target.replaceChildren();
 state.world.years.forEach(item=>{
 const b=document.createElement('button');b.type='button';b.className='time-card'+(state.year===item.year?' active':'');
 b.innerHTML='<span class="time-year">'+esc(item.year)+'</span><span><strong>'+esc(item.title)+'</strong><p>'+esc(item.summary)+'</p></span>';
 b.addEventListener('click',()=>updateYear(item.year));target.append(b);
 });
 const chosen=state.world.years[state.year-2026];
 $('timelineDetail').innerHTML='<b>'+esc(chosen.year)+' · '+esc(chosen.title)+'</b><p>'+esc(chosen.summary)+'</p><p class="tiny muted">AUTHORITATIVE MATRIX: '+esc(chosen.source.json_pointer)+'</p>';
}
function brainRecord(type,entry){
  return {type,...entry,search:JSON.stringify(entry).toLowerCase()};
}
function setupBrain(){
 const brain=state.brain;
 const els=[];
 for(const e of brain.fx)els.push(brainRecord('fx',e));
 for(const e of brain.workflows)els.push(brainRecord('workflow',e));
 for(const e of brain.models)els.push(brainRecord('model',e));
 for(const e of brain.media_capabilities)els.push(brainRecord('media',e));
 state.brainEntries=els;
 const links=$('brainLinks');links.replaceChildren();
 for(const link of brain.drive_links){const a=document.createElement('a');a.target='_blank';a.rel='noopener noreferrer';a.href=safeLink(link.url);a.textContent=link.name+' ↗';links.append(a);}
 $('studioLink').href=safeLink(brain.native_studio.readme_url);
}
function renderBrainList(){
 if(!state.brain)return;
 const q=$('brainSearch').value.trim().toLowerCase(),kind=$('brainCategory').value,gate=$('brainGate').value;
 const results=state.brainEntries.filter(r=>(kind==='all'||r.type===kind)&&(!q||r.search.includes(q))&&(gate==='all'||r.gate_status===gate||r.status===gate)).slice(0,100);
 $('brainCount').textContent='RESULTS '+results.length+' / '+state.brainEntries.length+' REGISTERED  ·  '+state.brain.counts.fx+' FX  ·  '+state.brain.counts.workflows+' WORKFLOWS  ·  '+state.brain.counts.models+' MODELS';
 const grid=$('brainResults');grid.replaceChildren();
 results.forEach(entry=>{
 const b=document.createElement('button');b.type='button';b.className='cap-card'+(state.brainItem?.id===entry.id?' active':'');
 const label=entry.gate_status||entry.status||entry.authority||'indexed';
 b.innerHTML='<div class="card-top"><span>'+esc(entry.type.toUpperCase())+' / '+esc(entry.id)+'</span><span class="gate-tag '+esc(label)+'">'+esc(label.replaceAll('_',' '))+'</span></div><h3>'+esc(entry.name||entry.capability||entry.id)+'</h3><p>'+esc(entry.family||entry.category||entry.purpose||entry.requires||entry.runtime||'Source-traced capability')+'</p>';
 b.addEventListener('click',()=>{state.brainItem=entry;renderBrainList();renderBrainSelected();});
 grid.append(b);
 });
 if(results.length===0)grid.textContent='No matches. Try a registry ID, category or technique.';
}
function renderBrainSelected(){
 const e=state.brainItem,t=$('brainSelected'); if(!e){t.textContent='Select a capability to inspect its exact registry source.';return;}
 const parts=[
 ['ID',e.id],['KIND',e.type],['STATUS',e.gate_status||e.status||'Indexed only'],['PROOF',e.proof_ids?.join(', ')||'No proof asserted'],['MODEL RUNTIME',e.runtime||'Not a model'],['SOURCE SHA',e.source.git_blob_sha1],['SOURCE PATH',e.source.path]];
 t.replaceChildren();
 const title=document.createElement('h3');title.textContent=e.name||e.capability||e.id;t.append(title);
 const dl=document.createElement('dl');for(const [k,v]of parts){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=k;dd.textContent=v;dl.append(dt,dd);}t.append(dl);
 const a=document.createElement('a');a.className='external-link';a.target='_blank';a.rel='noopener noreferrer';a.href=safeLink(e.source.url);a.textContent='OPEN GIT SOURCE ↗';t.append(a);
 const p=document.createElement('p');p.className='tiny muted';p.textContent='Registry metadata only. A runtime result or artistic approval must be established separately.';t.append(p);
 if(e.type==='fx'&&e.gate_status==='approved'){const b=document.createElement('button');b.type='button';b.className='flat-button';b.textContent='USE IN BRIEF →';b.addEventListener('click',()=>{state.selectedFx=e.id;$('briefFx').value=e.id;setTab('production');renderBrief();});t.append(b);}
}
function populateBrief(){
 const entities=[...state.world.nodes,...state.world.people];
 for(const e of state.world.years){const o=document.createElement('option');o.value=e.year;o.textContent=e.year+' · '+e.title;$('briefYear').append(o);}
 $('briefYear').value=state.year;
 for(const e of entities){const o=document.createElement('option');o.value=e.id;o.textContent=e.name+' ('+e.kind+')';$('briefEntity').append(o);}
 $('briefEntity').value=state.entity;
 for(const fx of state.brain.fx.filter(x=>x.gate_status==='approved')){
 const o=document.createElement('option');o.value=fx.id;o.textContent=fx.name+' · '+fx.id;$('briefFx').append(o);}
}
function makeBrief(){
 const id=$('briefEntity').value;
 const entity=[...state.world.nodes,...state.world.people].find(e=>e.id===id);
 const year=Number($('briefYear').value), event=state.world.years.find(y=>y.year===year);
 const mode=$('briefMode').value, fxId=$('briefFx').value;
 const fx=state.brain.fx.find(f=>f.id===fxId);
 return {
  schema:'american-empire.production-brief.v1', status:'draft_handoff_only',
  authority_layer:mode==='canon_reference'?'historical_canon_reference_only':'counterfactual_adaptation_not_canon',
  project:'american-empire', year, canonical_event:{title:event.title,source:event.source},
  subject:{id:entity.id,name:entity.name,kind:entity.kind,source:entity.source},
  scenario_context:mode==='scenario_adaptation'?{scenario_id:state.world.scenarios[state.scenario].id,run_sha256:state.world.scenarios[state.scenario].run_sha256,authority_layer:'scenario_only'}:null,
  fx_reference:fx?{id:fx.id,name:fx.name,gate_status:fx.gate_status,registry_source:fx.source,
  warning:'Not executable from explorer. Revalidate current FX code, prerequisites, proof gate and Director approval.'}:null,
  scene_intention:$('briefNote').value.trim().slice(0,700),
  world_evidence:{canon_commit:state.world.source.canon_commit,graph_sha256:state.world.source.world_graph_sha256,bundle_sha256:state.world.bundle_sha256,
    model_sha256:state.world.source.simulation_model_sha256},
  second_brain:{source:state.brain.drive_links[0].url,contract:state.brain.drive_links[1].url,
      registry_status:'source-index only'},
  execution:{performed:false,studio_connected:false,rendered:false,canon_promoted:false},
  note:'This is a reusable GodRender Director handoff, not an Operating Order or a production branch authorization.'
 };
}
function renderBrief(){
 if(!state.world||!state.brain)return;
 const brief=makeBrief();$('briefPreview').textContent=JSON.stringify(brief,null,2);
}
function downloadJSON(name,obj){const blob=new Blob([JSON.stringify(obj,null,2)+'\n'],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function bindEvents(){
 document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>setTab(b.dataset.tab)));
 $('prevYear').addEventListener('click',()=>updateYear(state.year-1));
 $('nextYear').addEventListener('click',()=>updateYear(state.year+1));
 $('yearSlider').addEventListener('input',e=>updateYear(e.target.value));
 $('scenarioSelect').addEventListener('change',e=>{state.scenario=Number(e.target.value);renderYear();renderBrief();window.AE_Live?.syncScenario(state.scenario);});
 $('startCinema').addEventListener('click',()=>setTab('cinema'));
 $('startFilmAgain').addEventListener('click',()=>setTab('cinema'));
 $('startSimulation').addEventListener('click',()=>setTab('simulation'));
 $('startClaire').addEventListener('click',()=>{window.AE_People.moveYear(2027);window.AE_People.select('claire');setTab('inhabitants')});
 $('startEarth').addEventListener('click',()=>{window.AE_Geo.setYear(2027);window.AE_Geo.select('paris');setTab('earth')});
 $('resetGraph').addEventListener('click',()=>selectEntity('system:S1'));
 $('goChronology').addEventListener('click',()=>setTab('chronology'));
 $('timelineToWorld').addEventListener('click',()=>setTab('world'));
 $('personSelect').addEventListener('change',e=>{if(e.target.value)selectEntity(e.target.value);});
 for(const id of ['brainSearch','brainCategory','brainGate'])$(id).addEventListener(id==='brainSearch'?'input':'change',renderBrainList);
 for(const id of ['briefYear','briefEntity','briefMode','briefFx','briefNote'])$(id).addEventListener(id==='briefNote'?'input':'change',renderBrief);
 $('copyBrief').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(JSON.stringify(makeBrief(),null,2));$('briefMessage').textContent='Brief copied; no production executed.';}catch(e){$('briefMessage').textContent='Clipboard unavailable. Use Download JSON.';}});
 $('downloadBrief').addEventListener('click',()=>{const b=makeBrief();downloadJSON('american-empire-'+b.year+'-director-brief.json',b);$('briefMessage').textContent='Draft brief downloaded; original canon untouched.';});
 window.addEventListener('hashchange',()=>setTab(location.hash.slice(1)));
}
async function loadJSON(url){const tag={'world.json':'embeddedWorld','brain.json':'embeddedBrain','model.json':'embeddedModel','reference_scenarios.json':'embeddedReference','geo.json':'embeddedGeo','land.geojson':'embeddedLand','inhabitants.json':'embeddedInhabitants','people_source.json':'embeddedPeopleSource','media_inventory.json':'embeddedMediaInventory'}[url.split('/').pop()];const embedded=$(tag);if(embedded)return JSON.parse(embedded.textContent);const res=await fetch(url,{cache:'no-store'});if(!res.ok)throw Error(url+' returned HTTP '+res.status);return res.json();}
async function init(){
 try{
 const [world,brain,model,references,geo,land,inhabitants,peopleSource,mediaInventory]=await Promise.all([loadJSON('./data/world.json'),loadJSON('./data/brain.json'),loadJSON('./data/model.json'),loadJSON('./data/reference_scenarios.json'),loadJSON('./data/geo.json'),loadJSON('./data/land.geojson'),loadJSON('./data/inhabitants.json'),loadJSON('./data/people_source.json'),loadJSON('./data/media_inventory.json')]);
 if(world.schema!=='american-empire.godot-explorer-bundle.v1'||brain.schema!=='american-empire.browser-brain.v1'
 ||world.bundle_sha256!==brain.world_bundle_sha256||world.source.world_graph_sha256!==brain.world_source.world_graph_sha256)
 throw Error('World and Second Brain provenance mismatch. Refusing unverified bundle.');
 if(!world.sources_read_only||world.nodes.length!==16||world.years.length!==12||world.scenarios.some(s=>s.authority_layer!=='scenario_only'))
 throw Error('Missing provenance or unexpected canon-scene boundary.');
 state.world=world;state.brain=brain;
 $('githubTop').href=safeLink(brain.links.branch);$('canonLink').href=safeLink(brain.drive_links.find(v=>v.type==='canon_archive')?.url);
 for(const [i,s] of world.scenarios.entries()){const o=document.createElement('option');o.value=i;o.textContent=s.name+' · hypothetical';$('scenarioSelect').append(o);}
 for(const p of world.people){const o=document.createElement('option');o.value=p.id;o.textContent=p.name;$('personSelect').append(o);}
 setupBrain();populateBrief();bindEvents();updateYear(state.year);renderGraph();renderEntity();renderBrainList();renderBrainSelected();
 if(!window.AE_Live||!window.AE_Sim)throw Error('P5 native simulation runtime missing');
 await window.AE_Live.init({world,model,state,api:{updateYear,renderYear,AE_Sim:window.AE_Sim,referenceScenarios:references}});
 if(!window.AE_Geo||!window.AE_Regions)throw Error('P6 geographical runtime missing');
 window.AE_Geo.init({geo,land,live:window.AE_Live});
 if(!window.AE_People||!window.AE_Inhabitants)throw Error('P7 inhabitants runtime missing');
 await window.AE_People.init({manifest:inhabitants,geo,canon:peopleSource});
 if(!window.AE_Cinema)throw Error('Observer Cinema runtime missing');
 window.AE_Cinema.init(mediaInventory);
 setTab(location.hash.slice(1)||'home');$('error').hidden=true;
 }catch(e){$('error').hidden=false;$('error').textContent='World Explorer unavailable: '+e.message+'. Check the verified browser build.';console.error(e);}
}
// Inline standalone scripts must all initialize before asynchronous data parity.
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
else init();
