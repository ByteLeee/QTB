"""Build GEB episodes 02–08 from their editable Markdown manuscripts (stdlib only)."""
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'site' / 'geb'
EPISODES = json.loads((BOOK / 'episodes.json').read_text())
INDEX = (BOOK / 'index.html').read_text()
HEADER = re.search(r'<header>.*?</header>', INDEX, re.S).group()
HEADER = HEADER.replace('href="#route"', 'href="index.html#route"')


def inline(text):
    text = escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'\[(\d+)\]', lambda m: f'<a class="cite" href="#source-{m[1]}" aria-label="参考资料{m[1]}">[{m[1]}]</a>', text)


def render_markdown(text):
    chunks, outline = [], []
    n = 0
    for block in text.strip().split('\n\n'):
        if block.startswith('# '):
            continue
        if block.startswith('## '):
            n += 1
            title = block[3:].strip()
            outline.append((f's{n}', title))
            chunks.append(f'<h2 id="s{n}">{escape(title)}</h2>')
        else:
            chunks.append(f'<p>{inline(block)}</p>')
    return '\n'.join(chunks), outline


def source_html(ep):
    items = ''.join(f'<li id="source-{i}"><a href="{escape(ref["url"], quote=True)}">{escape(ref["title"])}</a><br>{escape(ref["note"])}</li>' for i, ref in enumerate(ep['refs'], 1))
    return f'<section class="references" id="sources" aria-labelledby="sources-title"><h2 id="sources-title">原著依据与参考资料</h2><p>原著定位：{escape(ep["chapters"])}。按章节与小节核对，避免不同版本页码混淆。正文使用原创表述；自拟场景与分析性延伸已在文中标明。数学内容为概念讲解，完整证明须查阅原始文献。</p><ol>{items}</ol></section>'


def chapter_links(active):
    entries = [('01', '当你打开自己的源代码，会在哪里找到“我”？', 'index.html#reading')]
    entries += [(ep['id'], ep['title'], f'episode-{ep["id"]}.html') for ep in EPISODES]
    return ''.join(f'<a href="{href}"' + (' aria-current="page" class="active"' if num == active else '') + f'><small>{num}</small>{escape(title)}</a>' for num, title, href in entries)


for i, ep in enumerate(EPISODES):
    text = (BOOK / 'manuscripts' / f'{ep["id"]}.md').read_text()
    downloads = BOOK / 'downloads'
    downloads.mkdir(exist_ok=True)
    download = text + '\n\n## 原著与参考资料\n\n原著定位：' + ep['chapters'] + '。\n\n'
    for j, ref in enumerate(ep['refs'], 1):
        download += f'[{j}] {ref["title"]}\n{ref["url"]}\n{ref["note"]}\n\n'
    (downloads / f'{ep["id"]}.md').write_text(download)
    prose, outline = render_markdown(text)
    chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    minutes = max(1, round(chars / 210))
    prev_href = 'index.html#reading' if i == 0 else f'episode-{EPISODES[i-1]["id"]}.html'
    next_html = f'<a href="episode-{EPISODES[i+1]["id"]}.html">下一期 · {escape(EPISODES[i+1]["title"])} →</a>' if i < len(EPISODES)-1 else '<a href="index.html#route">八期读毕 · 返回系列目录 ↑</a>'
    section_links = ''.join(f'<a href="#{ident}">{escape(title)}</a>' for ident, title in outline)
    page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f5f3ea"><meta name="description" content="借书之问《集异璧之大成》第{int(ep['id'])}期：{escape(ep['title'], quote=True)}。含原著论证、案例、反例、边界与可追溯参考资料。"><title>第{int(ep['id'])}期 · {escape(ep['title'])}｜借书之问·集异璧</title><link rel="stylesheet" href="style.css"><script src="app.js" defer></script></head>
<body data-episode="{ep['id']}"><a class="skip" href="#reading">跳到正文</a><div class="progress-track" aria-hidden="true"><div id="progress"></div></div>{HEADER}
<main class="reading-layout" id="reading"><aside class="sidebar"><p class="sidebar-title">集异璧之大成 / 八期主题深读</p>{chapter_links(ep['id'])}<a href="index.html#route">↑ 系列目录</a></aside>
<article class="article" aria-labelledby="episode-title"><div class="reading-top"><a class="back" href="index.html#route">← 集异璧 · 八期目录</a><div class="read-tools" aria-label="阅读工具"><button id="smaller" type="button" aria-label="缩小正文字号">A−</button><button id="larger" type="button" aria-label="放大正文字号">A＋</button><button id="focus" type="button" aria-pressed="false">专注阅读</button><button id="print" type="button">打印</button></div></div>
<div class="eyebrow">GÖDEL, ESCHER, BACH / EPISODE {ep['id']}</div><h1 id="episode-title">{escape(ep['title'])}</h1><p class="article-question">{escape(ep['subtitle'])}</p><div class="article-meta">原创主题深读 · 正文约 {chars:,} 汉字 · 约 {minutes} 分钟阅读 / 朗读速度因人而异 · 2026.10.23</div>
<details class="chapter-outline"><summary>本期内容导航</summary><div>{section_links}<a href="#sources">原著与参考资料</a></div></details>
<div class="prose" id="prose">{prose}</div>
<section class="exercise" id="exercise"><h2>把问题留在生活里</h2><p id="exercise-question">{escape(ep['exercise'])}</p></section>
<section class="note"><label for="notes">第 {int(ep['id'])} 期 · 你的思考笔记</label><textarea id="notes" placeholder="我理解到的论证是……最有力的反例是……我仍然不确定的是……"></textarea><p class="note-status" id="note-status" role="status">本期笔记仅保存在当前浏览器，不会自动跨设备同步。</p><div class="end-actions"><button id="export" type="button">导出本期笔记</button><a class="download-link" href="downloads/{ep['id']}.md" download>下载本期 Markdown 稿 ↓</a></div></section>
{source_html(ep)}<div class="nextprev"><a href="{prev_href}">← 上一期</a>{next_html}</div>
<details class="chapter-outline mobile-series"><summary>八期完整目录</summary><div>{chapter_links(ep['id'])}</div></details></article></main>
<footer><a href="../">借书之问 · 返回书架 ↗</a><a href="reading.md" download>下载八期合辑 ↓</a></footer></body></html>'''
    (BOOK / f'episode-{ep["id"]}.html').write_text(page)


class ExtractArticle(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_article = False
        self.level = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id') == 'prose':
            self.in_article = True
            self.level = 1
            return
        if self.in_article:
            if tag == 'div':
                self.level += 1
            if tag == 'h2':
                self.text.append('\n\n## ')
            elif tag in ('p', 'tr'):
                self.text.append('\n\n')
            elif tag in ('th', 'td'):
                self.text.append(' | ')

    def handle_endtag(self, tag):
        if self.in_article and tag == 'div':
            self.level -= 1
            if not self.level:
                self.in_article = False

    def handle_data(self, data):
        if self.in_article:
            self.text.append(data)


first = ExtractArticle()
first.feed(INDEX)
first_text = '# 当你打开自己的源代码，会在哪里找到“我”？\n\n' + ''.join(first.text).strip() + '\n'
(BOOK / 'manuscripts' / '01.md').write_text(first_text)
all_text = '# 借书之问 · 哥德尔、艾舍尔、巴赫：集异璧之大成\n\n八期原创主题阅读。以章节定位原著，不逐章替代原著。自拟案例和外部争论已标明。\n\n'
first_refs = []
for item in re.findall(r'<li id="source-\d+">(.*?)</li>', INDEX, re.S):
    item = re.sub(r'<a href="([^"]+)">(.*?)</a>', r'\2\n\1', item)
    item = re.sub(r'<br\s*/?>', '\n', item)
    first_refs.append(unescape(re.sub(r'<[^>]+>', '', item)))
all_text += first_text + '\n\n## 第一期参考资料\n\n' + '\n\n'.join(first_refs) + '\n\n---\n\n'
for ep in EPISODES:
    all_text += (BOOK / 'manuscripts' / f'{ep["id"]}.md').read_text() + '\n\n## 原著与参考资料\n\n'
    all_text += '原著定位：' + ep['chapters'] + '。\n\n'
    for i, ref in enumerate(ep['refs'], 1):
        all_text += f'[{i}] {ref["title"]}\n{ref["url"]}\n{ref["note"]}\n\n'
    all_text += '---\n\n'
(BOOK / 'reading.md').write_text(all_text)
print('Built seven episode pages and eight-episode Markdown collection.')
