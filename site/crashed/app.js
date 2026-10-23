(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const page = document.body.dataset.page || 'index';
  const settings = 'qtb-crashed-v1-';
  const prefix = 'qtb-crashed-series-v3-' + page + '-';
  const get = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const put = (key, value) => { try { localStorage.setItem(key, value); return true; } catch { return false; } };
  const theme = $('theme');
  const setTheme = dark => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    if (theme) { theme.textContent = dark ? '日读' : '夜读'; theme.setAttribute('aria-pressed', String(dark)); theme.setAttribute('aria-label', dark ? '切换浅色模式' : '切换深色模式'); }
  };
  setTheme(get(settings + 'theme') === 'dark');
  if (theme) theme.addEventListener('click', () => { const dark = document.documentElement.dataset.theme !== 'dark'; setTheme(dark); put(settings + 'theme', dark ? 'dark' : 'light'); });
  const size = $('font-size');
  if (size) {
    const saved = Number(get(settings + 'font'));
    if (saved >= 16 && saved <= 24) size.value = String(saved);
    const apply = () => document.documentElement.style.setProperty('--size', size.value + 'px');
    apply(); size.addEventListener('input', () => { apply(); put(settings + 'font', size.value); });
  }
  const note = $('note');
  if (note) {
    note.value = get(prefix + 'note') || '';
    note.addEventListener('input', () => { $('note-status').textContent = put(prefix + 'note', note.value) ? '已保存到当前浏览器，不跨设备同步。' : '当前浏览器无法保存，请导出笔记备份。'; });
  }
  const download = (text, filename) => {
    const url = URL.createObjectURL(new Blob([text], {type:'text/markdown;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = filename; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  if ($('export') && note) $('export').addEventListener('click', () => download('# ' + document.title + '\n\n' + note.value + '\n', '崩盘-第' + page + '期-笔记.md'));
  if ($('print')) $('print').addEventListener('click', () => window.print());
  if ($('copy')) $('copy').addEventListener('click', async () => {
    const article = $('reading');
    const text = [...article.querySelectorAll('h2,h3,p')].filter(el => !el.closest('.inset')).map(el => el.innerText.replace(/\[[A-Z]\d+\]/g, '').trim()).filter(Boolean).join('\n\n');
    const status = $('tool-status');
    try { await navigator.clipboard.writeText(text); status.textContent = '已复制正文。'; }
    catch {
      const area = document.createElement('textarea'); area.value = text; area.style.position = 'fixed'; area.style.left = '-9999px'; document.body.append(area); area.select();
      let ok = false; try { ok = document.execCommand('copy'); } catch {}
      area.remove(); status.textContent = ok ? '已复制正文。' : '浏览器未允许复制，请使用阅读稿下载。';
    }
  });
  const read = $('read-toggle');
  if (read) { read.checked = get(prefix + 'read') === 'true'; read.addEventListener('change', () => put(prefix + 'read', String(read.checked))); }
  document.querySelectorAll('[data-read]').forEach(el => { el.textContent = get('qtb-crashed-series-v3-' + el.dataset.read + '-read') === 'true' ? '· 已读' : ''; });
  const previousY = Number(get(prefix + 'position'));
  if ($('resume') && previousY > 150) {
    $('resume').hidden = false;
    $('resume').addEventListener('click', () => { window.scrollTo({top:previousY, behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'}); $('resume').hidden = true; });
  }
  const nav = [...document.querySelectorAll('.sidebar nav a[href^="#"]')];
  const update = () => {
    const range = document.documentElement.scrollHeight - innerHeight;
    if ($('progress-bar')) $('progress-bar').style.width = (range > 0 ? Math.min(100, scrollY / range * 100) : 100) + '%';
    let current = nav[0];
    for (const link of nav) { const target = document.getElementById(link.hash.slice(1)); if (target && target.getBoundingClientRect().top <= 140) current = link; }
    nav.forEach(link => { const active = link === current; link.classList.toggle('active', active); if (active) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current'); });
  };
  let timer, frame;
  addEventListener('scroll', () => { if (!frame) frame = requestAnimationFrame(() => { update(); frame = null; }); clearTimeout(timer); timer = setTimeout(() => put(prefix + 'position', String(Math.round(scrollY))), 300); }, {passive:true});
  addEventListener('resize', update); update();
})();

