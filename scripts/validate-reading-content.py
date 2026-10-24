from pathlib import Path
from urllib.parse import urlsplit,unquote
from html.parser import HTMLParser
import json,re
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
class Links(HTMLParser):
 def __init__(self,t):super().__init__();self.hrefs=[];self.ids=[];self.stack=[];self.unlinked=[];self.feed(t)
 def handle_starttag(self,t,a):
  d=dict(a)
  if d.get('href'):self.hrefs.append(d['href'])
  if d.get('id'):self.ids.append(d['id'])
  skip=(self.stack[-1][1] if self.stack else False) or t in ['a','pre','code'] or 'references' in d.get('class','').split() or d.get('id')=='sources'
  if t not in ['br','hr','img','input','meta','link']:self.stack.append((t,skip))
 def handle_endtag(self,t):
  while self.stack:
   tag,_=self.stack.pop()
   if tag==t:break
 def handle_data(self,t):
  if not(self.stack and self.stack[-1][1]):self.unlinked.extend(re.findall(r'\[(?:S)?\d+\]|〔\d+〕',t))
books=json.loads((SITE/'reading-data/catalog.json').read_text());count=0
for b in books:
 source=json.loads((ROOT/'content/themes'/f'{b["id"]}.json').read_text());out=json.loads((SITE/'reading-data'/f'{b["id"]}.json').read_text())
 assert [e['id'] for e in source['episodes']]==[e['id'] for e in out]
 assert len({e['question'] for e in out})==len(out),b['id']
 for e in out:
  count+=1;doc=Links(e['body']);assert len(doc.ids)==len(set(doc.ids)),e['id']
  assert not doc.unlinked,(e['id'],doc.unlinked)
  assert e['editorialReview']['argument'] and e['editorialReview']['boundary'] and e['editorialReview']['sourceScope'],e['id']
  assert 'depth-study' not in e['body'],e['id']
  for href in doc.hrefs:
   u=urlsplit(href)
   if u.scheme:assert u.scheme in ['http','https','mailto'],href;continue
   if not u.path:assert not u.fragment or unquote(u.fragment) in doc.ids,(e['id'],href)
   else:
    target=SITE/unquote(u.path);assert target.is_file(),(e['id'],href)
    if u.fragment and target.suffix=='.html':assert unquote(u.fragment) in Links(target.read_text()).ids,(e['id'],href)
  assert e['title']!=e['question'],e['id']
  for suffix in [f'{b["id"]}/current-{e["number"]:02}.html',f'downloads/{e["id"].replace(":","-")}.txt']:assert (SITE/suffix).exists()
  narration=(SITE/f'downloads/{e["id"].replace(":","-")}.txt').read_text()
  assert len(narration)>400,e['id']
  for excluded in ['出处与适用范围','资料与定位','参考与讨论边界','下载十二期实验脚本','可选：看看这一步推演怎样检验']:
   assert excluded not in narration,(e['id'],excluded)
  if b['id']=='agent':assert f'agent-reading-labs.py --episode {e["number"]}' in e['body'],e['id']
for slug,n in [('systems',0),('saturn',0),('agent',1)]:
 e=json.loads((SITE/'reading-data'/f'{slug}.json').read_text())[n];assert e['evidence'] and all(s['checked']=='2026-10-24' for s in e['evidence']);assert e['edition']
assert count==83
legacy=set(json.loads((ROOT/'scripts/reading-identities.json').read_text()).values());current={e['id'] for b in books for e in b['episodes']};assert legacy<=current,'A legacy identity was removed or regenerated'
review=json.loads((ROOT/'content/editorial-review.json').read_text());reviewids=[row[0] for theme in review['themes'].values() for row in theme['episodes']]
assert len(reviewids)==len(set(reviewids))==83 and set(reviewids)==current
print('Validated 83 permanent units, distinct questions, local citations, narration exclusions, editorial records, 12 lab entries and 3 original samples.')
