(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const prefix = 'qtb-crashed-v1-';
  const get = key => { try { return localStorage.getItem(prefix + key); } catch { return null; } };
  const put = (key, value) => { try { localStorage.setItem(prefix + key, value); return true; } catch { return false; } };
  const theme = $('theme');
  const setTheme = dark => { document.documentElement.dataset.theme = dark ? 'dark' : 'light'; theme.textContent = dark ? '日读' : '夜读'; theme.setAttribute('aria-pressed', String(dark)); theme.setAttribute('aria-label', dark ? '切换浅色模式' : '切换深色模式'); };
  setTheme(get('theme') === 'dark');
  theme.addEventListener('click', () => { const dark = document.documentElement.dataset.theme !== 'dark'; setTheme(dark); put('theme', dark ? 'dark' : 'light'); });
  const size = $('font-size');
  const savedSize = Number(get('font'));
  if (savedSize >= 16 && savedSize <= 24) size.value = String(savedSize);
  const setSize = () => document.documentElement.style.setProperty('--size', size.value + 'px');
  setSize(); size.addEventListener('input', () => { setSize(); put('font', size.value); });
  const note = $('note'); note.value = get('note') || '';
  note.addEventListener('input', () => { $('note-status').textContent = put('note', note.value) ? '已保存到当前浏览器，不跨设备同步。' : '浏览器无法保存，请使用“导出笔记”备份。'; });
  $('export').addEventListener('click', () => { const blob = new Blob(['# 借书之问 · 崩盘\n\n' + note.value + '\n'], { type: 'text/markdown;charset=utf-8' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = '崩盘-阅读笔记.md'; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); });
  $('print').addEventListener('click', () => window.print());
  const storedY = Number(get('position'));
  if (storedY > 150) { $('resume').hidden = false; $('resume').addEventListener('click', () => { window.scrollTo({top:storedY, behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}); $('resume').hidden = true; }); }
  let timer;
  const progress = () => { const range = document.documentElement.scrollHeight - innerHeight; $('progress-bar').style.width = (range > 0 ? Math.min(100, scrollY / range * 100) : 100) + '%'; };
  addEventListener('scroll', () => { progress(); clearTimeout(timer); timer = setTimeout(() => put('position', String(Math.round(scrollY))), 250); }, {passive:true});
  addEventListener('resize', progress); progress();
  if ('IntersectionObserver' in window) { const links = [...document.querySelectorAll('.sidebar nav a')]; const observer = new IntersectionObserver(entries => { const hit = entries.filter(e => e.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top)[0]; if (!hit) return; links.forEach(a => { const current = a.hash === '#' + hit.target.id; a.classList.toggle('active', current); if(current) a.setAttribute('aria-current','location'); else a.removeAttribute('aria-current'); }); }, {rootMargin:'-5% 0px -65% 0px'}); links.forEach(a => {const section = document.querySelector(a.hash); if(section)observer.observe(section);}); }
})();
