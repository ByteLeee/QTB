(() => {
  'use strict';
  const key = 'qtb-geb-v1';
  const byId = id => document.getElementById(id);
  const read = (name, fallback = '') => { try { return localStorage.getItem(`${key}:${name}`) ?? fallback; } catch { return fallback; } };
  const save = (name, value) => { try { localStorage.setItem(`${key}:${name}`, value); return true; } catch { return false; } };
  let size = Number(read('size', '20'));
  if (!Number.isFinite(size)) size = 20;
  size = Math.min(26, Math.max(16, size));
  function applySize() {
    document.documentElement.style.setProperty('--size', `${size}px`);
    byId('smaller').disabled = size <= 16;
    byId('larger').disabled = size >= 26;
  }
  applySize();
  byId('smaller').addEventListener('click', () => { size = Math.max(16, size - 2); applySize(); save('size', String(size)); });
  byId('larger').addEventListener('click', () => { size = Math.min(26, size + 2); applySize(); save('size', String(size)); });
  function theme(dark) {
    document.body.classList.toggle('dark', dark);
    byId('theme').textContent = dark ? '日间阅读' : '夜间阅读';
    byId('theme').setAttribute('aria-pressed', String(dark));
  }
  theme(read('theme') === 'dark');
  byId('theme').addEventListener('click', () => { const dark = !document.body.classList.contains('dark'); theme(dark); save('theme', dark ? 'dark' : 'light'); });
  byId('focus').addEventListener('click', () => {
    const focus = document.body.classList.toggle('focus');
    byId('focus').textContent = focus ? '退出专注' : '专注阅读';
    byId('focus').setAttribute('aria-pressed', String(focus));
    byId('reading').scrollIntoView({behavior: 'instant'});
    progress();
  });
  byId('print').addEventListener('click', () => window.print());
  document.querySelectorAll('a[href="#route"]').forEach(link => link.addEventListener('click', () => {
    document.body.classList.remove('focus');
    byId('focus').textContent = '专注阅读';
    byId('focus').setAttribute('aria-pressed', 'false');
  }));
  byId('notes').value = read('notes');
  byId('notes').addEventListener('input', () => {
    const ok = save('notes', byId('notes').value);
    byId('note-status').textContent = ok ? '已保存到当前浏览器 · 不会自动跨设备同步。' : '浏览器暂时无法保存，请使用“导出笔记”保留内容。';
  });
  byId('export').addEventListener('click', () => {
    const content = '# 借书之问 · 集异璧之大成\n\n## 第一期：当你打开自己的源代码，会在哪里找到“我”？\n\n观察问题：我对自己的描述，是在总结过去，还是正在规定未来？\n\n' + byId('notes').value + '\n';
    const url = URL.createObjectURL(new Blob([content], {type: 'text/markdown;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = 'geb-episode-01-notes.md'; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  function progress() {
    const article = byId('prose');
    const start = article.getBoundingClientRect().top + window.scrollY;
    const end = start + article.offsetHeight - window.innerHeight * .65;
    const percent = Math.max(0, Math.min(100, (window.scrollY - start + 70) / Math.max(1, end - start) * 100));
    byId('progress').style.width = `${percent}%`;
  }
  let queued = false;
  window.addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(() => { progress(); queued = false; }); } }, {passive: true});
  window.addEventListener('resize', progress);
  progress();
})();
