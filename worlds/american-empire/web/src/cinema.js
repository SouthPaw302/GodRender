/* Observer Cinema: a source-verifiable media archive, NOT a fictional TV broadcast.
 * Original scene masters remain private Google Drive media. Open only on user
 * interaction and never attempt remote fetching, conversion or permission bypass.
 */
(function(root){
'use strict';
const $=id=>document.getElementById(id),state={manifest:null,active:null};
const mask=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function validId(id){return typeof id==='string'&&/^[a-zA-Z0-9_-]{12,128}$/.test(id);}
function checkedLink(item){
 if(!validId(item.drive_file_id))throw Error('Invalid archived Drive ID');
 const expected='https://drive.google.com/file/d/'+item.drive_file_id+'/view';
 if(item.drive_url!==expected)throw Error('Media source link cannot be verified: '+item.id);
 return expected;
}
function selected(){
 return state.manifest.media.find(v=>v.id===state.active)||state.manifest.media[0];
}
function headline(item){
 const v=item.status.replaceAll('_',' ').toUpperCase();
 return item.scene?'SCENE '+item.scene+' · '+v:v;
}
function updateSelected(){
 const item=selected();if(!item)return;
 $('cinemaTitle').textContent=item.title;
 $('cinemaType').textContent=item.kind.toUpperCase()+' / '+headline(item);
 $('cinemaSource').textContent='Original source ID: '+(item.source_drive_file_id||item.drive_file_id)+
   ' · Curated Drive ID: '+item.drive_file_id+' · status: '+item.status;
 $('cinemaRights').textContent='Private Google Drive media. Viewing depends on your Drive access. These are cinematic depictions of life inside the American Empire universe, not literal documentary footage.';
 $('cinemaOpen').href=checkedLink(item);
 $('cinemaOpen').hidden=false;
 const frame=$('cinemaFrame');frame.replaceChildren();
 const placeholder=document.createElement('div');
 placeholder.className='cinema-placeholder';
 placeholder.textContent='Select "Preview this media" to open the original Drive player. It may require signing into Google. No streaming is requested until you choose.';
 frame.append(placeholder);
 $('cinemaPlay').disabled=false;
 document.querySelectorAll('[data-cinema-item]').forEach(el=>el.classList.toggle('selected',el.dataset.cinemaItem===item.id));
}
function preview(){
 const item=selected();const target=$('cinemaFrame');target.replaceChildren();
 const iframe=document.createElement('iframe');
 iframe.title='Google Drive preview · '+item.title;
 iframe.loading='lazy';iframe.referrerPolicy='no-referrer';
 iframe.allow='fullscreen';iframe.sandbox='allow-scripts allow-same-origin allow-popups';
 iframe.src='https://drive.google.com/file/d/'+item.drive_file_id+'/preview';
 target.append(iframe);
 $('cinemaNotice').textContent='Google Drive player requested for '+item.title+'. If access is blocked or the player remains blank, use “Open original in Drive”.';
}
function render(){
 if(!state.manifest)return;
 const list=$('cinemaItems');list.replaceChildren();
 for(const item of state.manifest.media){
   const button=document.createElement('button');button.type='button';
   button.className='cinema-item'+(state.active===item.id?' selected':'');button.dataset.cinemaItem=item.id;
   const title=document.createElement('strong'),meta=document.createElement('small');
   title.textContent=item.title;meta.textContent=headline(item);
   button.append(title,meta);button.addEventListener('click',()=>{state.active=item.id;updateSelected()});
   list.append(button);
 }
 updateSelected();
}
function init(manifest){
 if(manifest?.schema!=='american-empire.media-inventory.v1'||manifest.fictional_world_membership!=='shared_american_empire_timeline'
 ||!Array.isArray(manifest.media)||manifest.media.length<4)throw Error('AE cinema media index is incomplete');
 const names=new Set();
 for(const m of manifest.media){
   if(names.has(m.id)||!validId(m.drive_file_id))throw Error('Cinema media ID collision or invalid Drive ID');
   names.add(m.id);checkedLink(m);
 }
 state.manifest=manifest;state.active=manifest.media[0].id;
 $('cinemaPlay').addEventListener('click',preview);
 for(const [id,person] of [['cinemaFindClaire','claire'],['cinemaFindDaniel','daniel']]){
   $(id).addEventListener('click',()=>{
     if(!root.AE_People?.getRun()?.snapshots?.length)throw Error('Simulation has not initialized');
     root.AE_People.moveYear(2027);
     root.AE_People.select(person);
     document.querySelector('[data-tab="inhabitants"]').click();
   });
 }
 render();
 $('cinemaStatus').textContent='Catalog ready · '+manifest.media.length+' indexed source records · 4 curated film copies · no embedded media loaded automatically.';
}
root.AE_Cinema={init,render};
})(window);
