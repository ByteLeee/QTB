/* Shared state and deterministic weekly planning. No account or network writes. */
(function(root){
'use strict';
const KEY='qtb-reading-system-v1',statuses=['want','reading','done'];
const blank=()=>({version:1,books:{},episodes:{},last:null,goal:3,week:null});
function normalize(raw,catalog){
 const s=blank();if(!raw||raw.version!==1||typeof raw!=='object')return s;
 const ids=new Set(catalog.flatMap(b=>b.episodes.map(e=>e.id)));
 for(const b of catalog){const v=raw.books?.[b.id];if(statuses.includes(v?.status))s.books[b.id]={status:v.status};}
 for(const id of ids){const e=raw.episodes?.[id];if(!e||typeof e!=='object')continue;s.episodes[id]={done:e.done===true,note:typeof e.note==='string'?e.note.slice(0,100000):'',history:Array.isArray(e.history)?e.history.filter(x=>typeof x.note==='string').slice(-50):[],position:Math.max(0,Math.min(1,Number(e.position)||0)),updated:typeof e.updated==='string'?e.updated:''};}
 s.goal=[1,2,3,4,5].includes(raw.goal)?raw.goal:3;
 if(ids.has(raw.last?.id))s.last={id:raw.last.id,at:typeof raw.last.at==='string'?raw.last.at:''};
 if(typeof raw.week?.key==='string'&&Array.isArray(raw.week.ids))s.week={key:raw.week.key,ids:[...new Set(raw.week.ids)].filter(id=>ids.has(id)).slice(0,5)};
 return s;
}
function weekKey(date=new Date()) {const d=new Date(date.getFullYear(),date.getMonth(),date.getDate());d.setDate(d.getDate()-(d.getDay()+6)%7);return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');}
function plan(s,books,date=new Date()){
 const key=weekKey(date),eligible=id=>s.books[id.split(':')[0]]?.status==='reading'||(s.books[id.split(':')[0]]?.status==='done'&&s.episodes[id]?.done);
 if(s.week?.key===key){s.week.ids=s.week.ids.filter(eligible);return s.week.ids;}
 const active=books.filter(b=>s.books[b.id]?.status==='reading');
 active.sort((a,b)=>Number(s.last?.id?.startsWith(b.id+':'))-Number(s.last?.id?.startsWith(a.id+':')));
 const queues=active.map(b=>b.episodes.filter(e=>!s.episodes[e.id]?.done));const ids=[];
 for(let i=0;ids.length<s.goal&&queues.some(q=>q.length);i++)for(const q of queues){if(q.length&&ids.length<s.goal)ids.push(q.shift().id);}
 s.week={key,ids};return ids;
}
function complete(s,book,id,done){s.episodes[id]={...s.episodes[id],done};s.books[book.id]={status:book.episodes.every(e=>s.episodes[e.id]?.done)?'done':'reading'};}
function migrateLegacy(s,books,storage){
 const read=k=>{try{return storage.getItem(k);}catch{return null;}},json=k=>{try{return JSON.parse(read(k)||'{}')||{};}catch{return {};}};
 const configs={'infinite-games':['jieshu-infinite-v1',0],'extraordinary-lives':['jieshu-extraordinary-v1',0],'four-thousand-weeks':['jieshu-four-thousand-weeks-v1',0],'antifragile':['jieshu-antifragile-v1',0],'saturn':['saturn-walk-v1',0],'japan':['jieshu-japan-v1',1]};
 for(const b of books){const conf=configs[b.id],old=conf?json(conf[0]):{},offset=conf?.[1]||0;
 for(const e of b.episodes){if(s.episodes[e.id])continue;const i=e.number-1+offset;let note=old.notes?.[i]||'',done=Array.isArray(old.done)?old.done.includes(i):Boolean((old.read||old.done)?.[i]);
 if(b.id==='systems'){note=read('jzw_note_'+String(e.number).padStart(2,'0'))||'';const d=json('jzw_done');done=Array.isArray(d)&&d.includes(String(e.number).padStart(2,'0'));}
 if(b.id==='geb')note=read('qtb-geb-v1:'+(e.number===1?'notes':'notes:'+String(e.number).padStart(2,'0')))||'';
 if(b.id==='crashed'){const prefix='qtb-crashed-series-v3-'+String(e.number).padStart(2,'0')+'-';note=read(prefix+'note')||'';done=read(prefix+'read')==='true';}
 if(b.id==='agent')note=read('agent-deep-note-'+(e.number-1))||'';
 if(note||done)s.episodes[e.id]={note:typeof note==='string'?note:'',done,position:0,updated:''};
 }
 if(!s.books[b.id]&&b.episodes.some(e=>s.episodes[e.id]))s.books[b.id]={status:b.episodes.every(e=>s.episodes[e.id]?.done)?'done':'reading'};
 }
 return s;
}
function mergeBackup(current,incoming,catalog){
 const a=normalize(current,catalog),b=normalize(incoming,catalog);let conflicts=0,added=0;
 for(const [id,e] of Object.entries(b.episodes)){const old=a.episodes[id];if(!old){a.episodes[id]=e;added++;continue;}
 const both=old.note&&e.note&&old.note!==e.note;const newer=(e.updated||'')>(old.updated||'');const selected=newer?e:old,other=newer?old:e;
 const history=[...(old.history||[]),...(e.history||[])];if(both){conflicts++;history.push({note:other.note,updated:other.updated||'',reason:'导入冲突保留'});}
 a.episodes[id]={...selected,done:old.done||e.done,history:history.filter((x,i,all)=>all.findIndex(y=>y.note===x.note&&y.updated===x.updated)===i).slice(-50)};
 }
 for(const [id,v] of Object.entries(b.books))if(!a.books[id])a.books[id]=v;
 return {state:a,conflicts,added};
}
function setStatus(s,id,status){if(statuses.includes(status))s.books[id]={status};s.week=null;}
function recordAnswer(s,id,note){const old=s.episodes[id]||{};const history=[...(old.history||[])];if(old.note&&old.note!==note)history.push({note:old.note,updated:old.updated||'',reason:'修改前回答'});s.episodes[id]={...old,note,updated:new Date().toISOString(),history:history.slice(-50)};}
const api={KEY,blank,normalize,weekKey,plan,complete,migrateLegacy,mergeBackup,setStatus,recordAnswer};root.QTB=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);
