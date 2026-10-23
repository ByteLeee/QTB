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
  const capital = $('capital');
  const loss = $('asset-loss');
  const updateBalance = () => {
    const initialCapital = Number(capital.value);
    const assetLoss = Number(loss.value);
    const debt = 100 - initialCapital;
    const remaining = initialCapital - assetLoss;
    $('capital-value').textContent = String(initialCapital);
    $('asset-loss-value').textContent = assetLoss + '%';
    $('remaining-assets').textContent = String(100 - assetLoss);
    $('fixed-debt').textContent = String(debt);
    $('remaining-capital').textContent = String(remaining);
    $('remaining-capital').dataset.negative = String(remaining < 0);
    const percent = Math.round(assetLoss / initialCapital * 1000) / 10;
    $('lab-explanation').textContent = remaining < 0
      ? '账面资本为负，资产比债务少' + Math.abs(remaining) + '。这是简化模型中的资不抵债，不是对真实银行的破产判断。'
      : remaining === 0
      ? '初始资本全部耗尽，资产恰好等于债务。模型不判断到期现金是否足够。'
      : '资产跌' + assetLoss + '%，初始资本损失了' + percent + '%。剩余资本' + remaining + '；模型不判断到期现金是否足够。';
  };
  if (capital && loss) {
    capital.addEventListener('input', updateBalance);
    loss.addEventListener('input', updateBalance);
    $('lab-reset').addEventListener('click', () => { capital.value = '5'; loss.value = '3'; updateBalance(); });
    updateBalance();
  }
  const storedY = Number(get('position'));
  if (storedY > 150) { $('resume').hidden = false; $('resume').addEventListener('click', () => { window.scrollTo({top:storedY, behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}); $('resume').hidden = true; }); }
  let timer;
  const navLinks = [...document.querySelectorAll('.sidebar nav a')];
  const updateNavigation = () => {
    let current = navLinks[0];
    for (const link of navLinks) {
      const section = document.getElementById(link.hash.slice(1));
      if (section && section.getBoundingClientRect().top <= 140) current = link;
    }
    navLinks.forEach(link => {
      const active = link === current;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  };
  const progress = () => { updateNavigation(); const range = document.documentElement.scrollHeight - innerHeight; $('progress-bar').style.width = (range > 0 ? Math.min(100, scrollY / range * 100) : 100) + '%'; };
  addEventListener('scroll', () => { progress(); clearTimeout(timer); timer = setTimeout(() => put('position', String(Math.round(scrollY))), 250); }, {passive:true});
  addEventListener('resize', progress); progress();
})();

