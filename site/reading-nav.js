/* One navigation and progress bridge across the original theme pages. */
(()=>{
 const root=new URL('../',document.currentScript.src),slug=location.pathname.slice(root.pathname.length).split('/')[0];
 const nav=document.createElement('nav');nav.className='rs-global-nav';nav.setAttribute('aria-label','统一阅读导航');
 nav.innerHTML='<strong>借书之问</strong><a href="'+root.href+'">← 全站首页 / 我的书架</a><a href="'+root.href+'#plan">本周计划</a><a href="'+root.href+'#notes">思想笔记</a><a id="rs-canonical" href="'+root.href+'">进入个人阅读 →</a>';
 document.body.prepend(nav);
 fetch(new URL('reading-data/catalog.json',root)).then(r=>{if(!r.ok)throw Error();return r.json();}).then(books=>{
 const b=books.find(b=>b.id===slug);if(!b)return;let current=null,timer;
 const readState=()=>{let raw;try{raw=JSON.parse(localStorage.getItem(QTB.KEY)||'null');}catch{}return QTB.migrateLegacy(QTB.normalize(raw,books),books,{getItem:k=>{try{return localStorage.getItem(k);}catch{return null;}}});};
 function write(s){try{localStorage.setItem(QTB.KEY,JSON.stringify(s));}catch{}}
 function update(){let id;
 const printed=[...document.querySelectorAll('article[id^="ep-"]')];if(printed.length){const visible=printed.filter(x=>x.getBoundingClientRect().top<innerHeight*.45).pop()||printed[0];id=Number(visible.id.slice(3));}
 else {const m=location.hash.match(/(?:chapter-|read\/|deep-)(\d+)/);if(m)id=Number(m[1]);else if(['geb','crashed','deluge'].includes(slug))id=Number(document.body.dataset.page||document.body.dataset.episode)||1;}
 current=b.episodes.find(e=>e.number===id)||null;const target=current||b.episodes[0],a=document.getElementById('rs-canonical');a.href=new URL('read.html?book='+b.id+'&episode='+target.number,root).href;a.textContent='个人阅读 · 第 '+target.number+' 期 →';
 if(current){const s=readState();s.last={id:current.id,at:new Date().toISOString()};if(!s.books[b.id]||s.books[b.id].status==='want'){s.books[b.id]={status:'reading'};s.week=null;}write(s);const note=s.episodes[current.id]?.note;const fields=[...document.querySelectorAll('textarea')].filter(x=>x.offsetParent!==null&&document.activeElement!==x);for(const field of fields){const deep=field.dataset.deepNote;const target=deep!==undefined?b.episodes[Number(deep)]:current;const value=target&&s.episodes[target.id]?.note;if(typeof value==='string')field.value=value;}}}
 function track(){update();if(!current)return;const s=readState(),section=document.getElementById('ep-'+current.number),range=Math.max(1,section?section.offsetHeight-innerHeight:document.documentElement.scrollHeight-innerHeight),offset=section?section.getBoundingClientRect().top+scrollY:0;s.episodes[current.id]={...s.episodes[current.id],position:Math.max(0,Math.min(1,(scrollY-offset)/range))};write(s);}
 document.addEventListener('input',ev=>{if(ev.target.tagName!=='TEXTAREA')return;update();let e=current;const i=ev.target.dataset.deepNote;if(i!==undefined)e=b.episodes[Number(i)];if(!e)return;const s=readState();s.episodes[e.id]={...s.episodes[e.id],note:ev.target.value,updated:new Date().toISOString()};write(s);});
 document.addEventListener('click',ev=>{const target=ev.target.closest('#done,#markRead,[onclick^="markDone"],[data-action="done"]');if(!target||!current)return;const e=current,wasDone=Boolean(readState().episodes[current.id]?.done);setTimeout(()=>{const s=readState();QTB.complete(s,b,e.id,!wasDone);write(s);},0);},true);
 document.addEventListener('change',ev=>{if(ev.target.id!=='read-toggle'||!current)return;const s=readState();QTB.complete(s,b,current.id,ev.target.checked);write(s);});
 update();addEventListener('hashchange',()=>setTimeout(update,0));addEventListener('scroll',()=>{clearTimeout(timer);timer=setTimeout(track,350);},{passive:true});addEventListener('pagehide',track);
 }).catch(()=>{document.getElementById('rs-canonical').textContent='进入全站书架 →';});
})();
