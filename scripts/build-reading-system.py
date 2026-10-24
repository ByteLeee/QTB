"""Build every reading surface from content/themes/*.json. Legacy pages are archives."""
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';SOURCE=ROOT/'content/themes'
def slugtext(t):return unescape(re.sub('<[^>]+>','',t)).strip()
class Narration(HTMLParser):
 def __init__(self,body):
  super().__init__();self.stack=[];self.parts=[];self.buf=[];self.capture=0;self.feed(body)
 def handle_starttag(self,tag,attrs):
  d=dict(attrs);skip=(self.stack[-1][1] if self.stack else False) or bool(set(d.get('class','').split())&{'references','depth-sources','source-note','depth-note','inset'}) or 'data-no-speech' in d or d.get('id')=='sources'
  if tag not in ['br','hr','img','input','meta','link']:self.stack.append((tag,skip))
  if tag in ['h2','h3','p'] and not skip:self.capture+=1
 def handle_endtag(self,tag):
  while self.stack:
   t,skip=self.stack.pop()
   if t in ['h2','h3','p'] and not skip:
    self.capture=max(0,self.capture-1)
    if self.capture==0:
     text=re.sub(r'\[[A-Z]?\d+\]|〔\d+〕','',''.join(self.buf)).strip()
     if text:self.parts.append(text)
     self.buf=[]
   if t==tag:break
 def handle_data(self,t):
  if self.capture and not(self.stack and self.stack[-1][1]):self.buf.append(t)
def enhance(body):
 body=re.sub(r'<(?:script|style|button|textarea|label)\b[^>]*>.*?</(?:script|style|button|textarea|label)>','',body,flags=re.S|re.I)
 body=re.sub(r'<input\b[^>]*>','',body,flags=re.I)
 ids=set(re.findall(r'\bid="([^"]+)"',body));body=re.sub(r'href="[^"#]*#([^"]+)"',lambda m:'href="#'+m[1]+'"' if m[1] in ids else m[0],body)
 # Make plain source markers in the migrated content usable in-place.
 def source_id(m):
  content=m[1];label=re.search(r'\[(S\d+)\]',content)
  return '<li id="evidence-'+label[1]+'">'+content+'</li>' if label else m[0]
 body=re.sub(r'<li>(.*?)</li>',source_id,body,flags=re.S)
 available=set(re.findall(r'\bid="([^"]+)"',body));parts=re.split(r'(<[^>]+>)',body);inside=0
 for i,part in enumerate(parts):
  if part.startswith('<a '):inside+=1
  elif part.startswith('</a'):inside=max(0,inside-1)
  elif not part.startswith('<') and not inside:
   parts[i]=re.sub(r'\[(S\d+)\]',lambda m: '<a href="#evidence-'+m[1]+'">['+m[1]+']</a>' if 'evidence-'+m[1] in available else m[0],part)
 body=''.join(parts);body=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',body)
 counts={}
 def anchor(m):
  tag,attrs,t=m.groups();base='p-'+hashlib.sha256(slugtext(t).encode()).hexdigest()[:12];counts[base]=counts.get(base,0)+1;id=base+('-'+str(counts[base]) if counts[base]>1 else '')
  if not re.search(r'\bid=',attrs):attrs+=' id="'+id+'"'
  return '<'+tag+attrs+' data-paragraph="'+id+'" tabindex="-1">'+t+'</'+tag+'>'
 return re.sub(r'<(p|h2|h3)([^>]*)>(.*?)</\1>',anchor,body,flags=re.S)
books=[];allids=set()
for p in sorted(SOURCE.glob('*.json')):
 b=json.loads(p.read_text());episodes=b['episodes'];assert episodes
 for i,e in enumerate(episodes):
  assert e['id'] not in allids,e['id'];allids.add(e['id']);assert e['id'].startswith(b['id']+':')
  assert e.get('question') and len(e['body'])>1000
  e['number']=i+1;e['version']=hashlib.sha256(e['body'].encode()).hexdigest()[:12];e['body']=enhance(e['body']);e['minutes']=max(1,round(len(slugtext(e['body']))/300));e.setdefault('changeNote','统一段落定位与资料阅读入口。')
  e.setdefault('evidenceStatus','沿用现有资料说明；本期尚未按新样板逐项复核。')
  text='\n\n'.join(Narration(e['body']).parts)
  (SITE/'downloads'/f'{b["id"]}-{e["id"].split(":")[1]}.txt').write_text(e['title']+'\n\n'+text)
  # Plain, printable current edition; generated rather than hand-edited.
  printbody=re.sub(r'href="([^"]+)"',lambda m: m[0] if m[1].startswith(('https:','http:','#','mailto:')) else 'href="../'+m[1]+'"',e['body'])
  out=f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(e["title"])}</title><link rel="stylesheet" href="../reading.css"></head><body class="qtb-app"><main class="rs-main rs-reader"><nav><a href="../">← 全站书架</a> · <a href="../read.html?id={escape(e["id"])}">互动阅读与听读</a></nav><h1>{escape(e["title"])}</h1><p class="rs-meta">{escape(e["evidenceStatus"])}</p><article class="rs-prose">{printbody}</article></main></body></html>'
  (SITE/b['id']/f'current-{i+1:02}.html').write_text(out)
 meta={k:v for k,v in b.items() if k!='episodes'};meta['count']=len(episodes);meta['episodes']=[{k:v for k,v in e.items() if k!='body'} for e in episodes];books.append(meta)
 (SITE/'reading-data'/f'{b["id"]}.json').write_text(json.dumps(episodes,ensure_ascii=False))
 overview=b.get('map',{});rows=''.join(f'<li><a href="../read.html?id={escape(e["id"])}">{escape(e["title"])}</a><p class="rs-meta">{escape(e["question"])}</p></li>' for e in episodes)
 guide=f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(b["title"])} · 思想地图</title><link rel="stylesheet" href="../reading.css"></head><body class="qtb-app"><main class="rs-main rs-reader"><nav><a href="../">← 全站书架</a> · <a href="./">原版主题存档</a></nav><div class="rs-eyebrow">READING MAP</div><h1>{escape(b["title"])}</h1><p>{escape(overview.get("core",""))}</p><section class="rs-question"><h2>带着这条线索读</h2><p>{escape(overview.get("thread",""))}</p><h3>保留的争议与边界</h3><p>{escape(overview.get("limits",""))}</p></section><h2>问题链 · {len(episodes)} 个阅读单元</h2><ol class="rs-catalog">{rows}</ol><section><h2>读完以后留下什么</h2><p>{escape(overview.get("output","用自己的例子解释一个机制，并指出它可能失效的条件。"))}</p></section></main></body></html>'
 (SITE/b['id']/'guide.html').write_text(guide)
order=['systems','antifragile','infinite-games','extraordinary-lives','saturn','japan','agent','geb','deluge','crashed','four-thousand-weeks'];books.sort(key=lambda b:order.index(b['id']))
(SITE/'reading-data/catalog.json').write_text(json.dumps(books,ensure_ascii=False,indent=2))
print(f'Built {len(books)} themes / {len(allids)} permanent reading identities')
