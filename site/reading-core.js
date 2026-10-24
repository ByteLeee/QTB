/* Reading state stays in this browser; no personal data is published. */
(function(root){'use strict';
const KEY='qtb-reading-system-v1',statuses=['want','reading','done'];
const blank=()=>({version:1,books:{},episodes:{},orphans:{},last:null,goal:3,budget:40,planMode:'minutes',primary:null,light:null,week:null,reviewSnooze:{},settings:{rate:1,voice:'',sleep:0}});
const string=v=>typeof v==='string'?v:'';
function entry(e){return {done:e.done===true,doneUpdated:string(e.doneUpdated),rereading:e.rereading===true,note:string(e.note),history:Array.isArray(e.history)?e.history.filter(x=>x&&typeof x.note==='string').slice(-50):[],position:Math.max(0,Math.min(1,Number(e.position)||0)),anchor:string(e.anchor),version:string(e.version),heardVersion:string(e.heardVersion),audio:Number.isInteger(e.audio)?Math.max(0,e.audio):0,updated:string(e.updated),completedAt:string(e.completedAt),reads:Number.isInteger(e.reads)?Math.max(0,e.reads):0,reviewedAt:string(e.reviewedAt)};}
function normalize(raw,catalog){const s=blank();if(!raw||raw.version!==1||typeof raw!=='object')return s;
 const ids=new Set(catalog.flatMap(b=>b.episodes.map(e=>e.id))),bookids=new Set(catalog.map(b=>b.id));
 for(const b of catalog){const v=raw.books?.[b.id];if(statuses.includes(v?.status))s.books[b.id]={status:v.status};}
 for(const [id,e] of Object.entries({...raw.orphans,...raw.episodes})){if(!e||typeof e!=='object')continue;(ids.has(id)?s.episodes:s.orphans)[id]=entry(e);}
 s.goal=[1,2,3,4,5].includes(raw.goal)?raw.goal:3;s.budget=[15,25,40,60,90].includes(raw.budget)?raw.budget:40;s.planMode=raw.planMode==='count'?'count':'minutes';
 s.primary=bookids.has(raw.primary)?raw.primary:null;s.light=bookids.has(raw.light)&&raw.light!==s.primary?raw.light:null;
 if(ids.has(raw.last?.id))s.last={id:raw.last.id,at:string(raw.last.at)};
 if(typeof raw.week?.key==='string'&&Array.isArray(raw.week.ids))s.week={key:raw.week.key,ids:[...new Set(raw.week.ids)].filter(id=>ids.has(id)).slice(0,20),deferred:Array.isArray(raw.week.deferred)?raw.week.deferred.filter(id=>ids.has(id)):[],review:ids.has(raw.week.review)?raw.week.review:null};
 for(const [id,value] of Object.entries(raw.reviewSnooze||{}))if(ids.has(id)&&typeof value==='string')s.reviewSnooze[id]=value;
 s.settings={rate:[.75,1,1.25,1.5].includes(raw.settings?.rate)?raw.settings.rate:1,voice:string(raw.settings?.voice),sleep:[0,10,20,30].includes(raw.settings?.sleep)?raw.settings.sleep:0};return s;
}
function weekKey(date=new Date()){const d=new Date(date.getFullYear(),date.getMonth(),date.getDate());d.setDate(d.getDate()-(d.getDay()+6)%7);return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');}
function dueReview(s,books,date=new Date()){return books.flatMap(b=>b.episodes).filter(e=>{const n=s.episodes[e.id];if(!n?.note?.trim())return false;const base=Date.parse(n.reviewedAt||n.updated);return Number.isFinite(base)&&date.getTime()-base>=7*86400000&&!(Date.parse(s.reviewSnooze[e.id])>date.getTime());}).sort((a,b)=>String(s.episodes[a.id].reviewedAt||s.episodes[a.id].updated).localeCompare(String(s.episodes[b.id].reviewedAt||s.episodes[b.id].updated)))[0]?.id||null;}
function plan(s,books,date=new Date()){
 const key=weekKey(date);if(s.week?.key===key)return s.week.ids;
 const active=books.filter(b=>s.books[b.id]?.status==='reading');
 const primary=active.find(b=>b.id===s.primary)||active.find(b=>s.last?.id?.startsWith(b.id+':'))||active[0];
 const light=active.find(b=>b.id===s.light&&b!==primary);let ids=[];
 if(s.planMode==='count'){const queues=active.map(b=>b.episodes.filter(e=>!s.episodes[e.id]?.done));while(ids.length<s.goal&&queues.some(q=>q.length))for(const q of queues)if(q.length&&ids.length<s.goal)ids.push(q.shift().id);}
 else {let remaining=s.budget-(dueReview(s,books,date)?5:0);const selected=[...(primary?.episodes||[]).filter(e=>!s.episodes[e.id]?.done)];let lightItem=light?.episodes.find(e=>!s.episodes[e.id]?.done);for(const e of selected){if(e.minutes>remaining)break;ids.push(e.id);remaining-=e.minutes;if(ids.length===1&&lightItem&&lightItem.minutes<=remaining){ids.push(lightItem.id);remaining-=lightItem.minutes;lightItem=null;}}}
 s.week={key,ids,deferred:[],review:dueReview(s,books,date)};return ids;
}
function complete(s,book,id,done){const old=s.episodes[id]||{};s.episodes[id]={...old,done,doneUpdated:new Date().toISOString(),rereading:false,completedAt:done?new Date().toISOString():old.completedAt,reads:(old.reads||0)+(done&&(!old.done||old.rereading)?1:0)};s.books[book.id]={status:book.episodes.every(e=>s.episodes[e.id]?.done)?'done':'reading'};}
function setStatus(s,id,status){if(statuses.includes(status))s.books[id]={status};s.week=null;}
function snapshot(s,id,reason='修改前回答'){const old=s.episodes[id];if(!old?.note)return;const h=[...(old.history||[])];if(h.at(-1)?.note!==old.note)h.push({note:old.note,updated:old.updated||'',reason});s.episodes[id]={...old,history:h.slice(-50)};}
function recordAnswer(s,id,note){snapshot(s,id);s.episodes[id]={...s.episodes[id],note,updated:new Date().toISOString()};}
function mergeBackup(current,incoming,catalog){const a=normalize(current,catalog),b=normalize(incoming,catalog),empty=!Object.keys(a.books).length&&!Object.keys(a.episodes).length&&!a.last;let conflicts=0,added=0;if(empty)for(const k of ['primary','light','budget','planMode','goal','settings','week'])a[k]=b[k];if(b.last&&(!a.last||b.last.at>a.last.at))a.last=b.last;
 for(const bucket of ['episodes','orphans'])for(const [id,e] of Object.entries(b[bucket])){const old=a[bucket][id];if(!old){a[bucket][id]=e;added++;continue;}const newer=e.updated>old.updated,selected=newer?e:old,other=newer?old:e;const history=[...old.history,...e.history];if(old.note!==e.note&&(old.note||e.note)){conflicts++;history.push({note:other.note,updated:other.updated,reason:'导入冲突保留'});}a[bucket][id]={...selected,done:old.doneUpdated||e.doneUpdated?(e.doneUpdated>old.doneUpdated?e.done:old.done):old.done||e.done,doneUpdated:e.doneUpdated>old.doneUpdated?e.doneUpdated:old.doneUpdated,history:history.filter((x,i,all)=>all.findIndex(y=>y.note===x.note&&y.updated===x.updated)===i).slice(-50)};}
 for(const [id,v] of Object.entries(b.books))if(!a.books[id])a.books[id]=v;return {state:a,conflicts,added};}
function mergeRemote(s,raw,catalog){const b=normalize(raw,catalog),out=mergeBackup(s,b,catalog).state;for(const [id,e] of Object.entries(b.episodes)){out.episodes[id].done=!s.episodes[id]||e.doneUpdated>(s.episodes[id]?.doneUpdated||'')?e.done:s.episodes[id].done;out.episodes[id].doneUpdated=e.doneUpdated>(s.episodes[id]?.doneUpdated||'')?e.doneUpdated:s.episodes[id]?.doneUpdated||'';}for(const [id,v] of Object.entries(b.books))out.books[id]=v;for(const k of ['primary','light','budget','planMode','goal','settings','week','reviewSnooze'])out[k]=b[k];return out;}
function resolve(catalog,query){const all=catalog.flatMap(book=>book.episodes.map(e=>({...e,book})));if(query.id)return all.find(e=>e.id===query.id)||null;return all.find(e=>e.id===query.book+':'+query.episode)||all.find(e=>e.book.id===query.book&&e.number===Number(query.episode))||null;}
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

const api={KEY,blank,normalize,weekKey,plan,complete,migrateLegacy,mergeBackup,mergeRemote,setStatus,recordAnswer,snapshot,dueReview,resolve};root.QTB=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);
