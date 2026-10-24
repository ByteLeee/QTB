from pathlib import Path
from urllib.parse import urlsplit,unquote
from html.parser import HTMLParser
import json,re
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
class Links(HTMLParser):
 def __init__(self,t):super().__init__();self.hrefs=[];self.ids=[];self.feed(t)
 def handle_starttag(self,t,a):
  d=dict(a)
  if d.get('href'):self.hrefs.append(d['href'])
  if d.get('id'):self.ids.append(d['id'])
books=json.loads((SITE/'reading-data/catalog.json').read_text());count=0
for b in books:
 source=json.loads((ROOT/'content/themes'/f'{b["id"]}.json').read_text());out=json.loads((SITE/'reading-data'/f'{b["id"]}.json').read_text())
 assert [e['id'] for e in source['episodes']]==[e['id'] for e in out]
 for e in out:
  count+=1;doc=Links(e['body']);assert len(doc.ids)==len(set(doc.ids)),e['id']
  for href in doc.hrefs:
   u=urlsplit(href)
   if u.scheme:assert u.scheme in ['http','https','mailto'],href;continue
   if not u.path:assert not u.fragment or unquote(u.fragment) in doc.ids,(e['id'],href)
   else:
    target=SITE/unquote(u.path);assert target.is_file(),(e['id'],href)
    if u.fragment and target.suffix=='.html':assert unquote(u.fragment) in Links(target.read_text()).ids,(e['id'],href)
  assert e['title']!=e['question'],e['id']
  for suffix in [f'{b["id"]}/current-{e["number"]:02}.html',f'downloads/{e["id"].replace(":","-")}.txt']:assert (SITE/suffix).exists()
for slug,n in [('systems',0),('saturn',0),('agent',1)]:
 e=json.loads((SITE/'reading-data'/f'{slug}.json').read_text())[n];assert e['evidence'] and all(s['checked']=='2026-10-24' for s in e['evidence']);assert e['edition']
assert count==83
legacy=set(json.loads((ROOT/'scripts/reading-identities.json').read_text()).values());current={e['id'] for b in books for e in b['episodes']};assert legacy<=current,'A legacy identity was removed or regenerated'
print('Validated 83 permanent units, citation anchors, local file links and 3 evidence-backed samples.')
