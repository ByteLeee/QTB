(() => {
  'use strict';
  const {chapters, sources} = window.BOOK; const totalChars=window.BOOK.totalChars+Depth.data.reduce((n,e,i)=>n+Depth.count(i),0);chapters.forEach((c,i)=>c.minutes=Math.ceil(((c.body.match(/[\u4e00-\u9fff]/g)||[]).length+Depth.count(i))/300));
  const $ = (s, root=document) => root.querySelector(s);
  const esc = value => String(value).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const parts = ['追赶的起点','重建与增长','泡沫与修复','回到人的生活'];
  const key = 'jieshu-japan-v1';
  let saved = {};
  let storageOK = true;
  try { saved = JSON.parse(localStorage.getItem(key) || '{}') || {}; } catch { storageOK = false; }
  if (typeof saved !== 'object' || Array.isArray(saved)) saved = {};
  const validId = id => Number.isInteger(id) && id >= 1 && id <= chapters.length;
  const state = {
    done: Array.isArray(saved.done) ? [...new Set(saved.done.filter(validId))] : [],
    notes: saved.notes && typeof saved.notes==='object' && !Array.isArray(saved.notes) ? saved.notes : {},
    last: saved.last && validId(saved.last.id) ? saved.last : null,
    theme: saved.theme === 'dark' ? 'dark' : 'light',
    font: [17,19,21,23].includes(saved.font) ? saved.font : 19
  };
  let current = null, currentPage = '', filter = 0, query = '', recital = false, restoring = false, toastTimer;
  const main = $('#main');
  function persist() { try {localStorage.setItem(key,JSON.stringify(state)); return true;} catch {storageOK=false;return false;} }
  function toast(message) { $('#toast').textContent=message;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),2800); }
  function applySettings() {
    document.body.classList.toggle('dark',state.theme==='dark');
    document.documentElement.style.setProperty('--read-size',state.font+'px');
    $('#theme').setAttribute('aria-label',state.theme==='dark'?'切换日间模式':'切换夜间模式');
    $('#theme').title=state.theme==='dark'?'切换日间模式':'切换夜间模式';
  }
  function sourceLink(id, detail=false) {
    const s=sources[id];
    if(!s) return '';
    return `<div class="${detail?'source-item':'source-mini'}" id="${detail?'source-':'cite-'}${id}">${detail?`<span>${id.slice(1).padStart(2,'0')}</span><div>`:''}<${detail?'h3':'div'}><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a></${detail?'h3':'div'}>${detail?`<small>${esc(s.author)}</small>`:''}<p>${detail?'':esc(s.author)+' · '}${esc(s.note)}</p>${detail?'</div>':''}</div>`;
  }
  function bodyHTML(body) {
    return body.split(/\n\s*\n/).map(block=>{
      if(block.startsWith('## ')) return `<h2>${esc(block.slice(3).split('\n')[0])}</h2>`+block.split('\n').slice(1).filter(Boolean).map(x=>'<p>'+esc(x)+'</p>').join('');
      return `<p>${esc(block).replace(/\[(S\d+)\]/g,(_,id)=>`<a class="citation" href="#cite-${id}" data-cite="${id}" title="查看资料：${esc(sources[id]?.title||id)}" aria-label="查看资料${id.slice(1)}">[${id.slice(1)}]</a>`)}</p>`;
    }).join('');
  }
  function chapterRows(list) {
    if(!list.length) return '<p class="empty">没有找到相应内容。试试“工作”“泡沫”或“明治”。</p>';
    let html='';
    parts.forEach((p,i)=>{
      const group=list.filter(c=>c.part===i+1);if(!group.length)return;
      html+=`<div class="part-heading"><span>PART ${String(i+1).padStart(2,'0')}</span><h3>${p}</h3></div>`;
      html+=group.map(c=>`<a class="chapter-row" href="#read/${c.id}"><span class="chapter-number">${String(c.id).padStart(2,'0')}</span><div><h4>${esc(c.title)}</h4><p>${esc(c.question)}</p></div><div class="chapter-info">${esc(c.era)}<br>约 ${c.minutes} 分钟${state.done.includes(c.id)?'<span class="read-tag">✓ 已读</span>':''}</div><span class="arrow" aria-hidden="true">↗</span></a>`).join('');
    });return html;
  }
  function catalogHTML(standalone=false) {
    return `<section class="section catalog" id="catalog-section"><div class="section-heading"><div><span class="eyebrow">THE READING JOURNEY</span><h2>十二次追问，一段长路。</h2></div><label class="search"><span class="sr-only" hidden>搜索分期正文</span><input id="search" type="search" aria-label="搜索标题与正文" placeholder="搜索问题、关键词……" value="${esc(query)}"></label></div><p class="count" id="result-count">十二期完整原创讲述 · 已读 ${state.done.length} / 12</p><div class="parts" role="group" aria-label="按篇章筛选"><button data-filter="0" class="${filter===0?'selected':''}" aria-pressed="${filter===0}">全部篇章</button>${parts.map((p,i)=>`<button data-filter="${i+1}" class="${filter===i+1?'selected':''}" aria-pressed="${filter===i+1}">${p}</button>`).join('')}</div><div id="chapter-list">${chapterRows(filtered())}</div>${standalone?'<p class="site-stats">阅读位置与已读记录仅保存在当前浏览器，不会跨设备同步。</p>':''}</section>`;
  }
  function filtered() {const q=query.trim().toLowerCase();return chapters.filter(c=>(!filter||c.part===filter)&&(!q||[c.title,c.question,c.body,c.era,Depth.text(c.id-1)].join(' ').toLowerCase().includes(q)));}
  function refreshCatalog() {
    const list=filtered();$('#chapter-list').innerHTML=chapterRows(list);
    $('#result-count').textContent=(query.trim()||filter)?`找到 ${list.length} 期讲述`:`十二期完整原创讲述 · 已读 ${state.done.length} / 12`;
    main.querySelectorAll('[data-filter]').forEach(b=>{const selected=Number(b.dataset.filter)===filter;b.classList.toggle('selected',selected);b.setAttribute('aria-pressed',String(selected));});
  }
  function homeHTML() {
    const continuation=state.last?`<a class="textlink" href="#read/${state.last.id}?resume=1">继续第 ${String(state.last.id).padStart(2,'0')} 期 →</a>`:'<a class="textlink" href="#catalog">浏览全部目录 →</a>';
    return `<section class="hero"><div class="hero-text"><p class="eyebrow">借书之问 / 历史 × 经济 × 日常生活</p><h1><span>日本</span>增长之后，<br>人如何生活。</h1><p class="hero-description">从追赶世界到重新理解生活。<br>借几本书，走过日本百余年的历史，<br>追问时代的变化，如何进入一个人的命运。</p><div class="hero-actions"><a class="primary" href="#read/1">从第一期读起 <span aria-hidden="true">↗</span></a>${continuation}</div><p class="hero-meta">12 期原创讲述　/　约 ${(totalChars/10000).toFixed(2)} 万字　/　每期约 8—12 分钟</p></div><div class="cover" aria-label="日本历史与经济，第一季"><div class="cover-label"><span>JAPAN, THROUGH QUESTIONS</span><span>VOL. 01</span></div><svg class="cover-art" viewBox="0 0 600 650" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><pattern id="lines" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M0 8L8 0" stroke="#d59472" stroke-width=".6" opacity=".4"/></pattern></defs><circle cx="240" cy="245" r="146" fill="#b9694d"/><circle cx="240" cy="245" r="146" fill="url(#lines)"/><path d="M0 510H600M0 530H600M0 550H600" stroke="#62777c" stroke-width=".7" opacity=".5"/><g fill="#203c48" stroke="#60767a" stroke-width=".8"><path d="M30 510V421H85V510M85 510V360H138V510M138 510V389H164V510M164 510V301H215V510M215 510V370H269V510M269 510V330H301V510M301 510V397H349V510M349 510V260H393V510M393 510V352H428V510M428 510V405H486V510M486 510V315H529V510M529 510V452H575V510"/><path d="M357 260V240H385V260M370 240V203" fill="none"/></g><g stroke="#a78e70" stroke-width="2" opacity=".75"><path d="M101 380V395M117 380V395M101 410V425M117 410V425M181 323V338M197 352V367M181 384V399M197 416V431M365 280V295M379 310V325M365 340V355M379 370V385M503 335V350M517 365V380M503 395V410"/></g><path d="M0 574C140 545 310 602 600 550" fill="none" stroke="#c5b496" stroke-width="1.3"/><path d="M0 583C140 554 310 611 600 559" fill="none" stroke="#798783" stroke-width=".5"/></svg><div class="cover-quote">时代向前，<br>生活向何处。</div><div class="cover-bottom"><span>历史里有制度，也有普通人。</span><span>1853 — 之后</span></div></div></section><section class="section intro"><div><p class="eyebrow">A QUESTION TO BEGIN WITH</p><h2>当“明天会更好”<br>不再理所当然。</h2></div><div class="intro-copy"><p>一个国家怎样形成持续增长的信念？当这种信念受到冲击，企业、家庭和普通人，会怎样重新安排未来？</p><p>我们沿着历史走，但每一期都围绕一个问题展开。<strong>从制度看见生活，从个人处境理解经济。</strong>日本的经验是一组可供思考的材料；它与其他社会的相似和差异，都需要具体辨认。</p><div class="route-line"><span>追赶</span><i>→</i><span>重建</span><i>→</i><span>增长</span><i>→</i><span>泡沫</span><i>→</i><span>重新生活</span></div></div></section>${catalogHTML()}<section class="section"><div class="closing"><div><p class="eyebrow">READ, THEN ASK</p><h2>读过之后，<br>把问题带回生活。</h2></div><div><p>如果暂时放下与别人比较的那把尺子，你希望接下来的一年，在哪一种具体意义上变得更好？</p><a class="textlink" href="#sources">看看这段旅程借了哪些书 ↗</a></div></div></section>`;
  }
  function sidebarHTML(c) {
    return `<aside class="sidebar" aria-label="十二期目录"><p class="eyebrow">日本 · 增长之后</p>${parts.map((p,i)=>`<p class="side-part">0${i+1} / ${p}</p>${chapters.filter(x=>x.part===i+1).map(x=>`<a class="side-link ${c.id===x.id?'current':''}" href="#read/${x.id}" ${c.id===x.id?'aria-current="page"':''}><b>${String(x.id).padStart(2,'0')}</b><span>${esc(x.title)}</span>${state.done.includes(x.id)?'<em aria-label="已读">✓</em>':''}</a>`).join('')}`).join('')}<div class="reading-summary">已读 ${state.done.length} / 12 期<br>每天一问，也可以慢慢读。</div></aside>`;
  }
  function readerHTML(c) {
    return `<div class="reader-layout">${sidebarHTML(c)}<article class="reader"><div class="reader-toolbar"><a href="#catalog">← 全部目录</a><div class="reader-controls"><button data-action="smaller" aria-label="缩小正文字号" ${state.font<=17?'disabled':''}>A−</button><button data-action="larger" aria-label="放大正文字号" ${state.font>=23?'disabled':''}>A＋</button><button data-action="recital" aria-pressed="${recital}">${recital?'退出朗读排版':'朗读排版'}</button><button data-action="print">打印文稿</button></div></div><header class="reader-header"><p class="eyebrow">PART 0${c.part} · ${parts[c.part-1]} / EP. ${String(c.id).padStart(2,'0')}</p><h1>${esc(c.title)}</h1><p class="era">${esc(c.era)}　/　约 ${c.minutes} 分钟　/　原创讲述</p></header><div class="chapter-question">${esc(c.question)}</div><div class="prose">${bodyHTML(c.body)}${Depth.render(c.id-1)}</div><div class="takeaway"><p class="eyebrow">留下一句话</p><p>${esc(c.idea)}</p></div><section class="reflection"><h2>把问题带回生活</h2><p>${esc(c.reflection)}</p><p class="exercise"><strong>一个小练习</strong><br>${esc(c.exercise)}</p><label class="note-label" for="note">留几句自己的想法</label><textarea id="note" placeholder="不必写出标准答案，记下此刻想到的就好……">${esc(typeof state.notes[c.id]==='string'?state.notes[c.id]:'')}</textarea><p class="note-meta" id="note-status">${storageOK?'自动保存在当前浏览器，不会跨设备同步。':'当前浏览器无法持久保存，离开前请自行复制笔记。'}</p></section><details class="chapter-sources"><summary>本期资料与阅读线索 · ${c.sources.length} 项</summary>${c.sources.map(id=>sourceLink(id)).join('')}</details><div class="chapter-end"><button class="done-button ${state.done.includes(c.id)?'is-done':''}" data-action="done" aria-pressed="${state.done.includes(c.id)}">${state.done.includes(c.id)?'✓ 已读完本期':'标记本期已读'}</button><span class="reader-bottom-note">本期 ${c.id} / 12 · 可随时从首页继续阅读</span></div><nav class="chapter-pagination" aria-label="前后期切换">${c.id>1?`<a href="#read/${c.id-1}"><small>← 上一期</small>${esc(chapters[c.id-2].title)}</a>`:'<a href="#home"><small>← 返回</small>本季首页</a>'}${c.id<12?`<a href="#read/${c.id+1}"><small>下一期 →</small>${esc(chapters[c.id].title)}</a>`:'<a href="#sources"><small>继续阅读 →</small>书目与资料</a>'}</nav></article></div>`;
  }
  function sourcesHTML() {
    return `<section class="sources-page"><div class="page-intro"><p class="eyebrow">BOOKS & RESEARCH</p><h1>借来的书，<br>留下的问题。</h1><p>以历史建立背景，用研究检验解释，再把问题带回普通人的生活。以下区分主线书目与可核查的公开资料。</p></div><div class="book-shelf"><a class="book" href="${sources.S3.url}" target="_blank" rel="noopener noreferrer"><div><small>01 / 历史的骨架</small><h2>日本的<br>起起落落</h2></div><p>安德鲁·戈登<br>A Modern History of Japan ↗</p></a><a class="book" href="${sources.S4.url}" target="_blank" rel="noopener noreferrer"><div><small>02 / 战后的生活</small><h2>拥抱战败</h2></div><p>约翰·W. 道尔<br>Embracing Defeat ↗</p></a><a class="book" href="${sources.S14.url}" target="_blank" rel="noopener noreferrer"><div><small>03 / 经济的机制</small><h2>大衰退</h2></div><p>辜朝明<br>The Holy Grail of Macroeconomics ↗</p></a></div><div class="editorial-note"><strong>关于这组讲述</strong><br>十二期为围绕问题创作的原创讲述，并非原书全文、逐章摘要或作者原话。书籍介绍页仅作为书目入口；具体历史与经济背景另列公开研究。文中假设、数字模型和合成场景均作了标注。文中的机制解释与价值讨论属于本系列的分析，不代表存在唯一结论。<br><br>历史研究有不同视角：央行演讲、政府历史页面、劳动研究与经济史著作，各有观察位置。阅读时可以互相参照。本季覆盖历史经验，不提供日本经济的实时判断。</div><h2>资料索引 <span class="count">${Object.keys(sources).length} 项</span></h2><div class="source-list">${Object.keys(sources).map(id=>sourceLink(id,true)).join('')}</div><p class="site-stats">整理日期：2026-10-19 · 可通过正文上标跳转至本期对应资料。</p><a class="textlink" href="#catalog">返回十二期讲述 →</a></section>`;
  }
  function savePosition() {
    if(!current||restoring)return;
    const span=Math.max(1,document.documentElement.scrollHeight-innerHeight);
    state.last={id:current.id,ratio:Math.min(1,Math.max(0,scrollY/span))};persist();
  }
  function updateProgress() {
    if(!current)return;
    const prose=$('.prose');if(!prose)return;
    const rect=prose.getBoundingClientRect();const progress=Math.min(100,Math.max(0,((innerHeight-rect.top)/Math.max(1,rect.height))*100));
    $('#reading-progress span').style.width=progress+'%';$('#reading-progress').setAttribute('aria-valuenow',Math.round(progress));
  }
  function route() {
    const resumeData=state.last?{...state.last}:null;
    savePosition();restoring=true;
    const hash=location.hash.slice(1)||'home';
    const match=hash.match(/^read\/(\d+)(\?resume=1)?$/);
    const sourceMatch=hash.match(/^sources(?:\/(S\d+))?$/);
    current=null;
    if(match&&validId(Number(match[1]))) {
      current=chapters[Number(match[1])-1];currentPage='read';main.innerHTML=readerHTML(current);document.title=`${current.title} · 借书之问`;
    } else if(sourceMatch) {currentPage='sources';main.innerHTML=sourcesHTML();document.title='书目与资料 · 借书之问';}
    else if(hash==='catalog') {currentPage='catalog';main.innerHTML=catalogHTML(true);document.title='十二期讲述 · 借书之问';}
    else {currentPage='home';filter=0;query='';main.innerHTML=homeHTML();document.title='借书之问 · 日本：增长之后，人如何生活';}
    document.body.classList.toggle('recital',recital&&!!current);
    $('#reading-progress').style.display=current?'block':'none';
    document.querySelectorAll('[data-nav]').forEach(a=>{a.classList.toggle('active',a.dataset.nav===currentPage||(currentPage==='read'&&a.dataset.nav==='catalog'));if(a.classList.contains('active'))a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
    if($('#menu-dialog').open)$('#menu-dialog').close();
    main.focus({preventScroll:true});
    requestAnimationFrame(()=>{
      if(match?.[2]&&resumeData?.id===current?.id)window.scrollTo({top:resumeData.ratio*Math.max(0,document.documentElement.scrollHeight-innerHeight),behavior:'instant'});
      else if(sourceMatch?.[1]&&sources[sourceMatch[1]])$('#source-'+sourceMatch[1])?.scrollIntoView({behavior:'instant'});
      else window.scrollTo({top:0,behavior:'instant'});
      setTimeout(()=>{restoring=false;savePosition();updateProgress();},80);
    });
    if(currentPage==='catalog')refreshCatalog();
  }
  main.addEventListener('input',e=>{
    if(e.target.id==='search'){query=e.target.value;refreshCatalog();}
    if(e.target.id==='note'&&current){state.notes[current.id]=e.target.value;const ok=persist();$('#note-status').textContent=ok?'已保存 · 仅保存在当前浏览器':'无法持久保存，请在离开前自行复制笔记。';}
  });
  main.addEventListener('click',e=>{
    const filterButton=e.target.closest('[data-filter]');if(filterButton){filter=Number(filterButton.dataset.filter);refreshCatalog();return;}
    const cite=e.target.closest('[data-cite]');if(cite){e.preventDefault();const details=$('.chapter-sources');if(details){details.open=true;$('#cite-'+cite.dataset.cite)?.scrollIntoView({behavior:'smooth',block:'center'});}return;}
    const b=e.target.closest('[data-action]');if(!b||!current)return;
    const action=b.dataset.action;
    if(action==='smaller'||action==='larger'){
      state.font=Math.min(23,Math.max(17,state.font+(action==='larger'?2:-2)));applySettings();persist();
      $('[data-action="smaller"]').disabled=state.font<=17;$('[data-action="larger"]').disabled=state.font>=23;toast('正文字号 '+state.font+' px');updateProgress();
    }
    if(action==='recital'){recital=!recital;document.body.classList.toggle('recital',recital);b.textContent=recital?'退出朗读排版':'朗读排版';b.setAttribute('aria-pressed',String(recital));toast(recital?'已隐藏注释与练习，方便亲自朗读':'已恢复完整阅读排版');updateProgress();}
    if(action==='print')window.print();
    if(action==='done'){
      const done=state.done.includes(current.id);state.done=done?state.done.filter(id=>id!==current.id):[...state.done,current.id];persist();b.classList.toggle('is-done',!done);b.setAttribute('aria-pressed',String(!done));b.textContent=done?'标记本期已读':'✓ 已读完本期';
      $('.sidebar').outerHTML=sidebarHTML(current);toast(done?'已取消本期已读标记':'已记录：读完第 '+String(current.id).padStart(2,'0')+' 期');
    }
  });
  $('#theme').addEventListener('click',()=>{state.theme=state.theme==='dark'?'light':'dark';applySettings();persist();});
  $('#dialog-links').innerHTML='<a href="#home">本季首页</a>'+chapters.map(c=>`<a href="#read/${c.id}">${String(c.id).padStart(2,'0')}　${esc(c.title)}</a>`).join('')+'<a href="#sources">书目与资料 ↗</a>';
  $('#menu').addEventListener('click',()=>$('#menu-dialog').showModal());
  $('#close-menu').addEventListener('click',()=>$('#menu-dialog').close());
  $('#dialog-links').addEventListener('click',e=>{if(e.target.closest('a'))$('#menu-dialog').close();});
  $('#menu-dialog').addEventListener('click',e=>{if(e.target===$('#menu-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});
  let scrollTimer;
  addEventListener('scroll',()=>{updateProgress();clearTimeout(scrollTimer);scrollTimer=setTimeout(savePosition,200);},{passive:true});
  addEventListener('resize',updateProgress);
  addEventListener('pagehide',savePosition);
  addEventListener('hashchange',route);
  applySettings();route();
})();
