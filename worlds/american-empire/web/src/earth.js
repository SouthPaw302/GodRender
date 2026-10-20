/* P6 Earth Network browser renderer: real public-domain geography, scenario-only
 * dependencies and causality. No remote map API or live surveillance.
 */
(function(global){
'use strict';
const el=id=>document.getElementById(id), SVG='http://www.w3.org/2000/svg', KEY='american-empire.p6.local-events.v1';
const state={geo:null,land:null,live:null,model:null,run:null,base:null,selected:'bandar-abbas',
 year:2030,eventsByRun:{},zoom:1,panX:0,panY:0,graphic:null,places:null,status:null};
const escap=t=>String(t??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','"':'&quot;',"'":'&#39;'}[c]));
const tag=(type,attrs={},value)=>{const x=document.createElementNS(SVG,type);for(const[k,v]of Object.entries(attrs))x.setAttribute(k,String(v));if(value!==undefined)x.textContent=String(value);return x;};
const pos=(lon,lat)=>[Number(((lon+180)*1200/360).toFixed(2)),Number(((90-lat)*620/180).toFixed(2))];
const pathRing=points=>'M'+points.map(([lon,lat])=>{const p=pos(lon,lat);return p.join(',')}).join('L')+'Z';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function landPath(geo){
 const geom=geo.geometry;
 if(geom.type==='Polygon')return geom.coordinates.map(pathRing).join(' ');
 if(geom.type==='MultiPolygon')return geom.coordinates.flatMap(rings=>rings.map(pathRing)).join(' ');
 return '';
}
function note(s,error=false){const target=el('geoStatus');target.textContent=s;target.classList.toggle('error-state',error);}
function current(){
 const c=global.AE_Live?.current?.();
 if(!c?.run)throw Error('P5 history is not ready');
 return c;
}
function refreshSource(){
 const c=current();
 if(!state.model||state.run?.p3_run_sha256!==c.run.run_sha256){
  state.model=new global.AE_Regions.RegionModel(state.geo,c.run);
 }
 const saved=state.eventsByRun[c.run.run_sha256]||[];
 try{state.run=state.model.run(saved);}catch(e){
  note('Discarded invalid local geographic events: '+e.message,true);
  state.eventsByRun[c.run.run_sha256]=[];state.run=state.model.run([]);
 }
 state.base=state.model.run([]);
 el('geoScenarioText').textContent=c.run.scenario.id;
}
function save(){
 try{localStorage.setItem(KEY,JSON.stringify({
  schema:'american-empire.p6-local.v1',classification:'scenario_only',
  source_geo_hash:state.geo.source_geo_sha256,model_states:state.eventsByRun
 }));return true;}catch(e){note('Browser storage is unavailable; export your model scenarios instead.',true);return false;}
}
function load(){
 try{
  const raw=localStorage.getItem(KEY);if(!raw)return;
  const data=JSON.parse(raw);
  if(data.schema!== 'american-empire.p6-local.v1'||data.classification!=='scenario_only'
   ||data.source_geo_hash!==state.geo.source_geo_sha256)return;
  const result={};
  for(const [key,events]of Object.entries(data.model_states||{})){
   if(/^[a-f0-9]{64}$/.test(key)&&Array.isArray(events)&&events.length<=40)result[key]=events;
  }
  state.eventsByRun=result;
 }catch{}
}
function selectedNode(){return state.geo.nodes.find(x=>x.id===state.selected);}
function localNow(){return state.run.snapshots[state.year-2026];}
function baselineNow(){return state.base.snapshots[state.year-2026];}
function drawMap(){
 const svg=el('earthMap');svg.replaceChildren();
 const defs=tag('defs'),grd=tag('pattern',{id:'p6grd',width:100,height:100,patternUnits:'userSpaceOnUse'});
 grd.append(tag('path',{d:'M 100 0 L 0 0 0 100',fill:'none',stroke:'#244657','stroke-width':1}));
 defs.append(grd);svg.append(defs);
 svg.append(tag('rect',{width:1200,height:620,fill:'#091b2d'}));
 svg.append(tag('rect',{width:1200,height:620,fill:'url(#p6grd)'}));
 const grp=tag('g',{id:'geoAll'});svg.append(grp);state.graphic=grp;
 const lands=tag('g',{id:'geoLand'});
 for(const feature of state.land.features){
  const d=landPath(feature);if(!d)continue;
  lands.append(tag('path',{d,fill:'#1d4050',stroke:'#436574','stroke-width':'.55','fill-rule':'evenodd','vector-effect':'non-scaling-stroke'}));
 }
 grp.append(lands);
 const routes=tag('g',{id:'geoRoutes'});grp.append(routes);
 const places=tag('g',{id:'geoPins'});grp.append(places);state.places=places;
 for(const r of state.geo.routes){
  const from=state.geo.nodes.find(n=>n.id===r.from),to=state.geo.nodes.find(n=>n.id===r.to);
  const a=pos(from.lon,from.lat),b=pos(to.lon,to.lat),dy=Math.abs(a[0]-b[0])*0.04;
  // Curved relationship, not a navigational or geographic transit line.
  const path='M'+a.join(' ')+' Q'+((a[0]+b[0])/2).toFixed(2)+' '+(((a[1]+b[1])/2)-dy).toFixed(2)+' '+b.join(' ');
  routes.append(tag('path',{id:'route-'+r.id,d:path,fill:'none',stroke:'#c4827b','stroke-width':1.7,'stroke-dasharray':'4 5',opacity:'.38','vector-effect':'non-scaling-stroke'}));
 }
 for(const node of state.geo.nodes){
  const p=pos(node.lon,node.lat),pin=tag('g',{'data-place':node.id,role:'button',tabindex:'0',
   'aria-label':'Inspect '+node.name,transform:'translate('+p.join(' ')+')',class:'geo-pin'});
  pin.append(tag('circle',{r:15,fill:'transparent'}));
  pin.append(tag('circle',{r:6,class:'geo-pin-disc',fill:'#7cddd2',stroke:'#0b1d2c','stroke-width':2}));
  const label=tag('text',{x:11,y:-7,class:'geo-pin-label'},node.name);
  pin.append(label);pin.append(tag('title',{},node.name+' (approximate city center)'));
  const choose=()=>select(node.id);
  pin.addEventListener('click',choose);pin.addEventListener('keydown',e=>{
   if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});
  places.append(pin);
 }
 paintTransform();
}
function paintTransform(){
 if(!state.graphic)return;
 state.graphic.setAttribute('transform',
  'translate('+state.panX+' '+state.panY+') translate(600 310) scale('+state.zoom+') translate(-600 -310)');
}
function paintState(){
 if(!state.run)return;
 const now=localNow(),base=baselineNow(),node=selectedNode();
 el('geoYear').value=state.year;el('geoYearText').textContent=state.year;
 el('geoSelectedName').textContent=node.name;
 el('geoSelectedNote').textContent=node.country+' · '+node.kind.replaceAll('_',' ')+' · '+node.location_status.replaceAll('_',' ');
 const chosen=now.places[node.id],prior=base.places[node.id];
 el('geoService').textContent=chosen.service+(chosen.service!==prior.service?' ('+(chosen.service>prior.service?'+':'')+(chosen.service-prior.service)+')':'');
 el('geoAutonomy').textContent=chosen.independence+(chosen.independence!==prior.independence?' ('+(chosen.independence>prior.independence?'+':'')+(chosen.independence-prior.independence)+')':'');
 el('geoPressure').textContent=(chosen.incoming_pressure>0?'+':'')+chosen.incoming_pressure;
 el('geoSource').textContent='ORIGINAL STORY MENTION: '+node.source.path+'\n“'+node.source.locator+'”\nReference coordinates: '+node.lat.toFixed(4)+', '+node.lon.toFixed(4)+' (not fictional facility)';
 const impacts=state.geo.nodes.map(n=>({name:n.name,id:n.id,
  delta:now.places[n.id].service-base.places[n.id].service})).filter(x=>x.delta!==0);
 impacts.sort((a,b)=>Math.abs(b.delta)-Math.abs(a.delta));
 const box=el('geoConsequences');box.replaceChildren();
 if(impacts.length){
  for(const impacted of impacts.slice(0,8)){
   const line=document.createElement('div');line.className='geo-consequence-line';
   line.textContent=impacted.name+': '+(impacted.delta>0?'+':'')+impacted.delta+' service points';box.append(line);
  }
 }else box.textContent='No local interventions yet. Any regional change from P5 alone is already in the baseline.';
 const eventList=el('geoEventList');eventList.replaceChildren();
 for(const e of state.run.events){
  const p=document.createElement('div');p.textContent=e.year+' · '+state.geo.nodes.find(n=>n.id===e.place)?.name+' · '+state.geo.actions[e.type].label+' ×'+e.intensity;eventList.append(p);
 }
 for(const pin of state.places.children){
  const id=pin.getAttribute('data-place'),obs=now.places[id];
  pin.classList.toggle('selected',id===state.selected);
  pin.querySelector('.geo-pin-disc').setAttribute('fill',id===state.selected?'#e4bc79':obs.service<35?'#c9737d':'#7cddd2');
 }
 for(const link of state.geo.routes){
  const obs=now.flows.find(x=>x.id===link.id);
  const path=el('route-'+link.id);
  if(!path)continue;
  path.setAttribute('stroke-width',Math.max(1,obs.supply_proxy/16).toFixed(2));
  path.setAttribute('opacity',link.from===state.selected||link.to===state.selected?'.9':'.3');
 }
 const chip=el('geoCityStrip');chip.replaceChildren();
 for(const n of state.geo.nodes){
  const b=document.createElement('button');b.className='geo-city-button'+(n.id===state.selected?' active':'');
  b.type='button';b.textContent=n.name;b.addEventListener('click',()=>select(n.id));chip.append(b);
 }
}
function select(id){if(!state.geo.nodes.some(n=>n.id===id))return;state.selected=id;paintState();}
function setYear(y){
 state.year=clamp(Math.floor(Number(y)),2026,2037);
 if(state.run)paintState();
}
function zoom(v){state.zoom=clamp(state.zoom*v,1,3.5);paintTransform();}
function addAction(){
 try{
  refreshSource();
  const c=current(),events=state.eventsByRun[c.run.run_sha256]||[];
  const action=el('geoAction').value,intensity=Number(el('geoIntensity').value),year=state.year;
  const spec={id:'local-'+String(events.length+1),year,type:action,place:state.selected,intensity};
  const next=[...events,spec];
  state.model.validateEvents(next);
  state.eventsByRun[c.run.run_sha256]=next;save();refreshSource();paintState();
  note('Scenario-only decision applied: '+state.geo.actions[action].label+' at '+selectedNode().name+' in '+year+'. Examine later years for downstream consequences.');
 }catch(e){note(e.message,true);}
}
function undo(){
 const c=current(),events=state.eventsByRun[c.run.run_sha256]||[];
 if(!events.length)return;
 state.eventsByRun[c.run.run_sha256]=events.slice(0,-1);save();refreshSource();paintState();note('Reverted the most recent local modeled intervention.');
}
function clear(){
 const c=current();
 state.eventsByRun[c.run.run_sha256]=[];save();refreshSource();paintState();note('Cleared this scenario’s P6 interventions; original canon and P5 state remain intact.');
}
function exportJSON(){
 const c=current(),ev=state.eventsByRun[c.run.run_sha256]||[];
 const packageData={schema:'american-empire.p6-scenario.v1',authority_layer:'scenario_only',
  source_geo_sha256:state.geo.source_geo_sha256,source_p3_run_sha256:c.run.run_sha256,
  p3_scenario_id:c.run.scenario.id,events:ev,year_viewed:state.year,
  caveat:'Directed routes and local values are hypothetical and not established canon'};
 const blob=new Blob([JSON.stringify(packageData,null,2)+'\n'],{type:'application/json'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');
 a.download='american-empire-p6-'+c.run.scenario.id+'.json';a.href=url;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);
 note('Exported P6 intervention record for '+c.run.scenario.id+'. No cloud upload was made.');
}
function render(){
 if(!state.geo||!global.AE_Live?.current)return;
 try{refreshSource();paintState();}
 catch(e){note('Could not load active P5 history: '+e.message,true);}
}
function init({geo,land,live}){
 if(geo?.schema!=='american-empire.geography.v1'||land?.type!=='FeatureCollection'||land.features?.length<100)
  throw Error('P6 geographical provenance failed');
 state.geo=geo;state.land=land;state.live=live;load();
 for(const [id,a]of Object.entries(geo.actions)){
  const opt=document.createElement('option');opt.value=id;opt.textContent=a.label;el('geoAction').append(opt);
 }
 el('geoYear').addEventListener('input',e=>setYear(e.target.value));
 el('geoPrev').addEventListener('click',()=>setYear(state.year-1));
 el('geoNext').addEventListener('click',()=>setYear(state.year+1));
 el('geoZoomIn').addEventListener('click',()=>zoom(1.5));
 el('geoZoomOut').addEventListener('click',()=>zoom(1/1.5));
 el('geoZoomReset').addEventListener('click',()=>{state.zoom=1;state.panX=0;state.panY=0;paintTransform()});
 el('geoIntensity').addEventListener('input',e=>el('geoIntensityLabel').textContent=e.target.value);
 el('geoApply').addEventListener('click',addAction);
 el('geoUndo').addEventListener('click',undo);
 el('geoClear').addEventListener('click',clear);
 el('geoExport').addEventListener('click',exportJSON);
 drawMap();render();
 note('Natural Earth basemap verified; '+geo.nodes.length+' source-mentioned cities; '+geo.routes.length+' explicitly hypothetical dependencies. No geography changes the canon.');
}
global.AE_Geo={init,render,setYear,select,getSnapshot:()=>localNow(),getBase:()=>baselineNow(),model:()=>state.model};
})(window);
