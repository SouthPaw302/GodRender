/* P10: source-bound scene requests and public-display ONLY of derived Godot proofs.
   No Drive media, secrets or original footage enters this browser. */
(function(root){
'use strict';
const $=id=>document.getElementById(id);
const status=(s,bad=false)=>{const el=$('forgeStatus');el.textContent=s;el.classList.toggle('error-state',bad)};
const requestSchema='american-empire.scene-request.v1';
const actionUrl='https://github.com/SouthPaw302/GodRender/tree/world/american-empire/worlds/american-empire/scene_requests';
const copy=async text=>{if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(text)}else{
 const b=$('forgeJSON');b.focus();b.select();document.execCommand('copy');
}};
let registry=[],actors=[],places=[];
function validSelection(){
 const actor=$('forgeActor').value,year=Number($('forgeYear').value),place=$('forgePlace').value;
 if(!actors.includes(actor)||!places.includes(place)||!Number.isInteger(year)||year<2026||year>2037)throw Error('Invalid actor, region or year');
 return {actor,year,place};
}
async function build(){
 await root.AE_People.refresh();
 const {actor,year,place}=validSelection();
 const p3=root.AE_Live.current().run,p6=root.AE_Geo.getRun(),p7=root.AE_People.getRun();
 if(!p3||!p6||!p7||p7.p3_run_sha256!==p3.run_sha256||p6.p3_run_sha256!==p3.run_sha256)
  throw Error('P5/P6/P7 world state has not synchronized');
 if(p7.snapshots[year-2026].people[actor]===undefined)throw Error('Actor is missing from selected year');
 if(p7.interventions.length>20||p6.events.length>40)throw Error('Intervention limits exceeded');
 const req={
  schema:requestSchema,authority_layer:'scenario_only',
  actor,year,observer_place:place,
  scenario:p3.scenario,regional_events:p6.events,interventions:p7.interventions,
  source:{
   p3_run_sha256:p3.run_sha256,
   p7_run_sha256:p7.run_sha256,
   p7_snapshot_sha256:p7.snapshots[year-2026].sha256,
   p7_manifest_sha256:p7.manifest_sha256,
   p6_event_sha256:p7.p6_event_sha256
  }
 };
 if(JSON.stringify(req).length>21000)throw Error('Scene request exceeds GitHub input limit');
 $('forgeJSON').value=JSON.stringify(req);
 const same=p7.snapshots[year-2026].people[actor].place===place;
 status('Ready: '+actor+' · '+year+' · '+place+'. '+(same?'Actor modeled locally.':'Actor is elsewhere: observer viewpoint only, no teleportation.')+' Source run '+p7.run_sha256.slice(0,12)+'…. Paste the request into GitHub Actions to render.');
 return req;
}
function selectProof(item){
 if(!item||item.classification!=='technical_geometry_proof_not_approved_film')return;
 const panel=$('forgePlayer');panel.replaceChildren();
 const vid=document.createElement('video');
 vid.controls=true;vid.preload='none';vid.playsInline=true;
 // Server-local checked paths only, NEVER arbitrary remote URLs.
 if(!/^proofs\/[a-z0-9-]{1,95}\.mp4$/.test(item.video))return;
 const source=document.createElement('source');source.src='./'+item.video;source.type='video/mp4';vid.append(source);
 panel.append(vid);
 const detail=$('forgeProofDetails');
 detail.textContent=item.actor+' · '+item.year+' · '+item.place+' · '+item.frames+' frames / 24 fps · source '+item.p7_snapshot_sha256.slice(0,14)+'… · technical proof only';
}
function renderRegistry(){
 const host=$('forgeProofList');host.replaceChildren();
 if(!registry.length){
  host.textContent='No approved technical proof has been published to this deployment yet. The verified P9 proof is available from GitHub Actions.';
  return;
 }
 for(const entry of registry){
  if(entry.classification!=='technical_geometry_proof_not_approved_film')continue;
  const btn=document.createElement('button');btn.className='flat-button';btn.type='button';
  btn.textContent=entry.actor+' · '+entry.year+' · '+entry.place+' · '+entry.contract_sha256.slice(0,9);
  btn.addEventListener('click',()=>selectProof(entry));
  host.append(btn);
 }
 const first=registry.find(x=>x.classification==='technical_geometry_proof_not_approved_film');
 if(first)selectProof(first);
}
async function init({geo,manifest,proofs}){
 actors=[...manifest.protagonists,...manifest.organizations,...manifest.film_cast].map(x=>x.id);
 places=geo.nodes.map(x=>x.id);registry=Array.isArray(proofs)?proofs:[];
 for(const a of actors){const o=document.createElement('option');o.value=a;o.textContent=a;$('forgeActor').append(o)}
 for(const city of geo.nodes){const o=document.createElement('option');o.value=city.id;o.textContent=city.name;$('forgePlace').append(o)}
 $('forgeActor').value='claire';$('forgePlace').value='paris';$('forgeYear').value='2027';
 $('forgeYearValue').textContent='2027';
 $('forgeYear').addEventListener('input',e=>$('forgeYearValue').textContent=e.target.value);
 $('forgeBuild').addEventListener('click',()=>build().catch(e=>status('Cannot prepare request: '+e.message,true)));
 $('forgeDownload').addEventListener('click',async()=>{
  try{
   const req=await build();
   const name='request-'+req.year+'-'+req.actor+'-'+req.observer_place+'-'+req.source.p7_run_sha256.slice(0,12)+'.json';
   const url=URL.createObjectURL(new Blob([JSON.stringify(req,null,2)+'\n'],{type:'application/json'}));
   const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
   setTimeout(()=>URL.revokeObjectURL(url),1200);
   status('Downloaded '+name+'. Upload this JSON into AE scene_requests/ and commit to the existing AE branch.');
  }catch(e){status('Download rejected: '+e.message,true)}
 });
 $('forgeCopy').addEventListener('click',async()=>{
  try{if(!$('forgeJSON').value)await build();await copy($('forgeJSON').value);status('Scene request copied. Open the Actions workflow, choose Run workflow, paste into scene_request.')}catch(e){status('Copy failed: '+e.message,true)}
 });
 $('forgeRun').href=actionUrl;
 renderRegistry();
 status('Choose actor/year/place, download the source-bound request JSON, then upload and commit it to the AE GitHub request folder. GitHub Actions will verify and process the job.');
}
root.AE_Forge={init,build,renderRegistry};
})(window);
