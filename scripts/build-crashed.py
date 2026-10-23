#!/usr/bin/env python3
"""Build the static Crashed reading series from its editorial source."""
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site' / 'crashed'
DATA = json.loads((OUT / 'series.json').read_text())
SOURCES = {s['id']: s for s in DATA['sources']}
ESC = html.escape
METHOD = ('本辑依据可核验的原著目录、图兹本人公开论述及列明的一手资料写作。'
          '书内定位是主题阅读入口；尚未完成原著全文逐页核对，不提供未经核实的页码或引语。'
          '作者论点、外部研究和本系列的机制推演分别注明。')

def cite(text):
    def sub(m):
        sid = m[1]
        assert sid in SOURCES, sid
        return f'<sup><a class="ref" href="#source-{sid}" aria-label="资料 {sid}">[{sid}]</a></sup>'
    return re.sub(r'\[([A-Z]\d+)\]', sub, text)

def sources(ids):
    return '<ol class="source-list">' + ''.join(
        f'<li id="source-{sid}"><span class="source-code">{sid} · {ESC(SOURCES[sid]["type"])}</span>'
        f'<a href="{ESC(SOURCES[sid]["url"])}" target="_blank" rel="noopener noreferrer">{ESC(SOURCES[sid]["title"])} ↗</a>'
        f'<p>{ESC(SOURCES[sid]["note"])}</p></li>' for sid in ids) + '</ol>'

def head(title, desc, page):
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{ESC(desc, quote=True)}"><meta name="theme-color" content="#203b46"><title>{ESC(title)} · 崩盘 · 借书之问</title><link rel="stylesheet" href="style.css"><script src="app.js" defer></script></head><body data-page="{page}"><a class="skip" href="#reading">跳到正文</a><div class="progress" aria-hidden="true"><div id="progress-bar"></div></div><header class="top"><a class="brand" href="../"><span>问</span>借书之问</a><a class="top-label" href="./">崩盘 · 八期目录</a><button id="theme" type="button" aria-pressed="false" aria-label="切换深色模式">夜读</button></header>'''

def tools():
    return '''<div class="tools"><label for="font-size">正文字号</label><input id="font-size" type="range" min="16" max="24" value="19"><button id="resume" type="button" hidden>继续上次阅读</button><button id="copy" type="button">复制口播正文</button><button id="print" type="button">打印 / 保存 PDF</button><small id="tool-status" role="status"></small></div>'''

def notes(page):
    return '''<section id="notes" class="supplement"><div class="eyebrow">READ & REFLECT</div><h2>把问题留给自己</h2><label for="note">我的理解、异议与待验证的问题</label><textarea id="note" rows="6" placeholder="我原本怎样理解？哪个环节改变了我的判断？什么证据会让我修正？"></textarea><div class="note-actions"><small id="note-status" role="status">笔记仅保存在当前浏览器，不跨设备同步。</small><button id="export" type="button">导出笔记</button></div></section>'''

def footer():
    return '<footer><a href="./">← 崩盘 · 八期目录</a><a href="../">借书之问总目录 ↗</a><p>八期原创主题阅读 · 亲自朗读，也保留自己的异议。<br>阅读进度与笔记仅保存在当前浏览器。</p></footer>'

def sections(ep, prefix='part'):
    chunks = re.split(r'<h3>(.*?)</h3>', ep['body'])
    result = []
    for n in range(1, len(chunks), 2):
        idx = (n+1)//2
        result.append(f'<section id="{prefix}-{idx}"><h3>{chunks[n]}</h3>{cite(chunks[n+1])}</section>')
    return ''.join(result)

def markdown_body(ep):
    s = ep['body']
    s = re.sub(r'<h3>(.*?)</h3>', r'\n\n## \1\n\n', s)
    s = re.sub(r'<strong>(.*?)</strong>', r'**\1**', s)
    s = s.replace('</p>', '\n\n')
    s = html.unescape(re.sub(r'<[^>]+>', '', s))
    return re.sub(r'\n{3,}', '\n\n', s).strip()

def md_sources(ids):
    return '\n\n'.join(f'[{sid}] [{SOURCES[sid]["title"]}]({SOURCES[sid]["url"]})\n\n{SOURCES[sid]["type"]}。{SOURCES[sid]["note"]}' for sid in ids)

def episode_page(ep, i):
    chars = len(re.sub('<[^>]+>', '', ep['body']))
    mins = math.ceil(chars / 240)
    headings = re.findall(r'<h3>(.*?)</h3>', ep['body'])
    nav = ''.join(f'<a href="#part-{j}">{ESC(t)}</a>' for j,t in enumerate(headings,1))
    previous = DATA['episodes'][i-1] if i else None
    following = DATA['episodes'][i+1] if i+1<len(DATA['episodes']) else None
    sibling = '<nav class="episode-turn" aria-label="前后期">'
    sibling += f'<a href="{previous["slug"]}.html">← 第{previous["id"]}期</a>' if previous else '<a href="./">← 本辑目录</a>'
    sibling += f'<a href="{following["slug"]}.html">第{following["id"]}期 →</a>' if following else '<a href="all.html">整辑连读 →</a>'
    sibling += '</nav>'
    text = head(ep['title'], ep['deck'], ep['id'])
    text += f'''<main><section class="episode-hero"><div class="eyebrow">CRASHED / 第 {ep['id']} 期 · 八期主题阅读</div><h1>{ESC(ep['title'])}</h1><p class="deck">{ESC(ep['deck'])}</p><p class="edition">完整正文 · 约 {mins} 分钟朗读 · {ESC(ep['concept'])}</p><div class="hero-actions"><a class="primary" href="#reading">开始阅读 ↓</a><a href="manuscripts/{ep['slug']}.md" download>下载本期阅读稿 ↓</a></div></section><div class="layout"><aside class="sidebar"><nav aria-label="本期目录"><p class="eyebrow">本期叙事线索</p>{nav}<a href="#basis">论证与资料核对</a><a href="#notes">我的问题与笔记</a><a href="#sources">本期来源</a></nav>{tools()}</aside><div class="reading-column"><article id="reading">{sections(ep)}</article><section id="basis" class="supplement"><div class="eyebrow">BACK TO THE ARGUMENT</div><h2>把论证放回依据</h2><p><b>原著阅读入口：</b>{ESC(ep['book'])}。[<a href="sources.html#source-B1">B1</a>]</p><details><summary>作者依据、推演与适用边界</summary><p>{ESC(ep['author'])}</p><ol>{''.join('<li>'+ESC(x)+'</li>' for x in ep['chain'])}</ol><p><b>跨学科解释：</b>{ESC(ep['cross'])}</p><p><b>反例与边界：</b>{ESC(ep['counter'])}</p></details><p class="method-note">{METHOD}</p><p class="reflection">{ESC(ep['exercise'])}</p><label class="read-control"><input id="read-toggle" type="checkbox">我已读完本期</label></section>{sibling}{notes(ep['id'])}<section id="sources" class="supplement sources"><div class="eyebrow">SOURCES / 本期可追溯依据</div><h2>资料与定位</h2>{sources(ep['sources'])}<p><a href="sources.html">查看全辑资料与阅读方法 ↗</a></p></section>{footer()}</div></div></main></body></html>'''
    (OUT/(ep['slug']+'.html')).write_text(text)
    md = f'# 第{ep["id"]}期 · {ep["title"]}\n\n{ep["deck"]}\n\n'+markdown_body(ep)+f'\n\n## 论证与依据\n\n原著主题入口：{ep["book"]}。\n\n{ep["author"]}\n\n{METHOD}\n\n## 留给自己的问题\n\n{ep["exercise"]}\n\n## 本期来源\n\n'+md_sources(ep['sources'])+'\n'
    (OUT/'manuscripts'/(ep['slug']+'.md')).write_text(md)
    return md

def main():
    assert len(DATA['episodes']) == 8
    (OUT/'manuscripts').mkdir(exist_ok=True)
    all_md = ['# 借书之问 · 崩盘\n\n'+DATA['question']+'\n\n八期完整主题正文。更新：'+DATA['updated']+'。\n\n'+METHOD]
    for i,ep in enumerate(DATA['episodes']):
        assert ep['body'].count('<h3>') >= 4
        assert set(re.findall(r'\[([A-Z]\d+)\]',ep['body'])) <= set(ep['sources'])
        assert all(x in SOURCES for x in ep['sources'])
        all_md.append(episode_page(ep,i))
    (OUT/'reading.md').write_text('\n\n---\n\n'.join(all_md)+'\n')
    cards = ''.join(f'''<a class="episode-card" href="{e['slug']}.html"><span class="eyebrow">第 {e['id']} 期 <span class="read-state" data-read="{e['id']}"></span></span><h2>{ESC(e['title'])}</h2><p>{ESC(e['deck'])}</p><span class="enter">阅读全文 ↗</span></a>''' for e in DATA['episodes'])
    landing = head('八期完整主题阅读',DATA['question'],'index')+f'''<main class="series-main"><section class="hero"><div class="hero-copy"><div class="eyebrow">ADAM TOOZE / EIGHT QUESTIONS</div><h1>崩盘</h1><p class="subtitle">全球金融危机如何重塑世界</p><div class="rule"></div><p class="question">为什么金融系统被救活了，<br>危机却没有真正结束？</p><p class="byline">从一次被预判错的危机，走到融资、救援与生活。<br>八期各问一件事，让论证沿着证据向前走。</p><div class="hero-actions"><a class="primary" href="{DATA['episodes'][0]['slug']}.html">从第一期读起 ↓</a><a href="all.html">整辑连续阅读 ↗</a></div><p class="edition">八期完整正文 · 适合亲自朗读 · 更新于 {DATA['updated']}</p></div><div class="cover" aria-hidden="true"><div class="cover-top">借书之问 / 金融与社会</div><div class="cover-title">崩盘<br>之后</div><div class="cover-sub">WHO PAYS<br>FOR RESCUE?</div><div class="water"></div><div class="water water-two"></div><div class="cover-bottom">ADAM TOOZE <span>2008 →</span></div></div></section><section class="series-intro"><p class="eyebrow">READING PATH / 八个完整问题</p><p>先追踪承诺怎样断裂，再讨论谁能提供支持，最后回到损失、生活与信任。每期均有独立论证、概念深解、案例和反例；可以分别阅读，也可以按顺序连读。</p></section><section id="reading" class="episode-grid" aria-label="八期正文">{cards}</section><section class="series-method"><h2>沿着依据读，也保留异议</h2><p>{METHOD}</p><p><a href="sources.html">全辑{len(SOURCES)}项资料与阅读方法 ↗</a>　<a href="reading.md" download>下载全辑阅读稿 ↓</a>　<a href="content-review.md">本次整改与内容核查 ↗</a></p><p class="muted">原导读和资本缓冲模型仍保留在<a href="overview.html">原导读存档</a>，其中原有浏览器笔记继续可用。新八期各有独立笔记与已读标记。</p></section>{footer()}</main></body></html>'''
    (OUT/'index.html').write_text(landing)
    toc=''.join(f'<a href="#episode-{e["id"]}">第{e["id"]}期　{ESC(e["title"])}</a>' for e in DATA['episodes'])
    combined=''.join(f'<section id="episode-{e["id"]}" class="all-episode"><div class="eyebrow">第 {e["id"]} 期</div><h2>{ESC(e["title"])}</h2><p class="lead">{ESC(e["deck"])}</p>{sections(e,"ep"+e["id"])}<div class="inset"><p>原著主题入口：{ESC(e["book"])}</p><p>{ESC(e["author"])}</p><p>反例与边界：{ESC(e["counter"])}</p><p>留给自己的问题：{ESC(e["exercise"])}</p></div></section>' for e in DATA['episodes'])
    all_html=head('整辑连续阅读',DATA['question'],'all')+f'<main><section class="episode-hero"><div class="eyebrow">EIGHT QUESTIONS / 整辑全文</div><h1>崩盘之后，<br>谁的生活恢复了？</h1><p class="deck">{ESC(DATA["question"])}</p><p class="method-note">{METHOD}</p><a href="reading.md" download>下载八期阅读稿 ↓</a></section><div class="layout"><aside class="sidebar"><nav aria-label="整辑目录">{toc}<a href="#sources">全辑来源</a></nav>{tools()}</aside><div class="reading-column"><article id="reading">{combined}</article><section id="sources" class="supplement sources"><h2>全辑资料</h2>{sources(list(SOURCES))}</section>{footer()}</div></div></main></body></html>'
    (OUT/'all.html').write_text(all_html)
    source_page=head('资料与阅读方法','区分原著定位、作者论述、同期文件与本系列解释。','sources')+f'<main class="source-main"><section id="reading"><div class="eyebrow">READING & EVIDENCE</div><h1>依据从哪里来</h1><p>{METHOD}</p><p>正文中的A编号为作者亲自发表的论述或访谈；D编号为同期文件、统计或外部研究；B编号为书目。本文的算例、跨学科类比和推演在叙事中明示，不算作作者直接结论。</p><p>资料能够支持某一事实，不代表自动证明整条因果链。参与机构的回顾也有立场。每期末尾列出论证链、反例及未越过的解释边界。</p><p><b>核查范围：</b>本次没有获得原著全文完成逐页核对，故不声称已经通过“全书原文精读”的验收。没有核实的页码、原话与细节不作为证据。当前交付为八期完整的作者论述核对版主题阅读。</p><p>本辑不穷尽原著所有事件；例如东欧和乌克兰的专门历史，不以几段泛论替代。八期的选择服务于金融断裂、救援与生活修复这一总问题。</p><p><a href="content-review.md">查看逐期整改核查 ↗</a></p></section><section class="sources">{sources(list(SOURCES))}</section>{footer()}</main></body></html>'
    source_page = source_page.replace('全辑24项资料', f'全辑{len(SOURCES)}项资料')
    (OUT/'sources.html').write_text(source_page)
    print(json.dumps({'episodes':len(DATA['episodes']),'sources':len(SOURCES),'body_characters':sum(len(re.sub('<[^>]+>','',e['body'])) for e in DATA['episodes'])},ensure_ascii=False))

if __name__ == '__main__':
    main()
