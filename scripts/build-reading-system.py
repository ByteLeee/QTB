"""Build the shared reader from existing published content; no new book text is generated."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape, unescape
import json, subprocess, re
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'site'
class Node:
 def __init__(self,tag='',attrs=(),parent=None):self.tag=tag;self.attrs=dict(attrs);self.children=[];self.parent=parent
 def find(self,p):
  out=[]
  for c in self.children:
   if isinstance(c,Node):
    if p(c):out.append(c)
    out+=c.find(p)
  return out
 def text(self):return ''.join(c.text() if isinstance(c,Node) else unescape(c) for c in self.children)
 def html(self):
  if not self.tag:return ''.join(c.html() if isinstance(c,Node) else c for c in self.children)
  a=''.join(' '+k+'="'+escape(v or '',quote=True)+'"' for k,v in self.attrs.items() if not k.startswith('on'))
  return '<'+self.tag+a+'>'+('' if self.tag in ['br','hr','img','input','meta','link'] else ''.join(c.html() if isinstance(c,Node) else c for c in self.children)+'</'+self.tag+'>')
class Parser(HTMLParser):
 def __init__(self,t):super().__init__(convert_charrefs=False);self.root=Node();self.cur=self.root;self.feed(t)
 def handle_starttag(self,t,a):
  n=Node(t,a,self.cur);self.cur.children.append(n)
  if t not in ['br','hr','img','input','meta','link','source','wbr']:self.cur=n
 def handle_endtag(self,t):
  n=self.cur
  while n.parent:
   if n.tag==t:self.cur=n.parent;return
   n=n.parent
 def handle_data(self,d):self.cur.children.append(d)
 def handle_entityref(self,n):self.cur.children.append('&'+n+';')
 def handle_charref(self,n):self.cur.children.append('&#'+n+';')
def doc(p):return Parser(p.read_text()).root
def get(n,id):return n.find(lambda x:x.attrs.get('id')==id)[0]
def cls(n,c):return n.find(lambda x:c in x.attrs.get('class','').split())
def inner(n):return ''.join(c.html() if isinstance(c,Node) else c for c in n.children)
def text(n,tag):return n.find(lambda x:x.tag==tag)[0].text().strip()
def clean(body,base):
 # Resolve references against the source document, including its anchors.
 def link(m):
  v=m[2]
  if re.match(r'^(https?:|mailto:|data:)',v):return m[0]
  from urllib.parse import urljoin
  return m[1]+'"'+urljoin(base,v)+'"'
 body=re.sub(r'<input\b[^>]*>|<label\b[^>]*>.*?</label>', '', body, flags=re.S)
 return re.sub(r'(href=)"([^"]+)"',link,body)
def dynamic(slug):
 p=SITE/slug/'content.js'
 code="const fs=require('fs'),vm=require('vm');const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync(process.argv[1],'utf8')+';globalThis.RESULT=chapters;',ctx);process.stdout.write(JSON.stringify(ctx.RESULT));"
 return json.loads(subprocess.check_output(['node','-e',code,str(p)]))
identity_path=ROOT/'scripts/reading-identities.json'
identities=json.loads(identity_path.read_text()) if identity_path.exists() else {}
books=[]
names={'systems':'系统之美','antifragile':'反脆弱','infinite-games':'有限与无限的游戏','extraordinary-lives':'格外的活法','saturn':'土星之环','japan':'日本历史与经济','agent':'机器如何学会做事','geb':'集异璧之大成','deluge':'滔天洪水','crashed':'崩盘','four-thousand-weeks':'四千周'}
for slug,title in names.items():
 episodes=[]
 if (SITE/slug/'deep-reading.html').exists():
  for i,n in enumerate(doc(SITE/slug/'deep-reading.html').find(lambda x:x.tag=='article' and x.attrs.get('id','').startswith('ep-'))):
   heading=text(n,'h1');body=inner(n);body=re.sub(r'<h1.*?</h1>','',body,count=1,flags=re.S)
   route={'systems':f'#/read/{i+1:02}','antifragile':f'#chapter-{i+1:02}','agent':f'#deep-{i+1}'}.get(slug,f'#read/{i+1}')
   episodes.append(dict(title=heading,question=heading,body=clean(body,f'{slug}/deep-reading.html'),original=f'{slug}/index.html{route}'))
 elif slug in ['infinite-games','extraordinary-lives','four-thousand-weeks']:
  for i,c in enumerate(dynamic(slug)):
   body='<p class="lead">'+escape(c.get('lead',''))+'</p>'
   if c.get('original'):body+='<p class="source-note">'+escape(c['original'])+'</p>'
   for h,paras in c['sections']:body+='<h2>'+escape(h)+'</h2>'+''.join('<p>'+escape(p)+'</p>' for p in paras.split('\n') if p.strip())
   body+='<h2>把问题带回生活</h2><p>'+escape(c.get('practice',''))+'</p><section class="references"><h2>参考与讨论边界</h2><ul>'
   for r in c.get('sources',[]):body+='<li><a href="'+escape(r['url'],quote=True)+'">'+escape(r.get('label','参考资料'))+'</a><p>'+escape(r.get('note',''))+'</p></li>'
   body+='</ul></section>'
   episodes.append(dict(title=c['title'],question=c.get('prompt') or c.get('question') or c['title'],body=body,original=f'{slug}/index.html#chapter-{i+1}'))
 elif slug=='geb':
  for i in range(1,9):
   p=SITE/slug/('index.html' if i==1 else f'episode-{i:02}.html');d=doc(p);a=cls(d,'article')[0];body=inner(get(d,'prose'))
   for c in ['exercise','references']:
    nodes=cls(a,c)
    if nodes:body+=nodes[0].html()
   episodes.append(dict(title=text(a,'h1'),question=text(a,'h1'),body=clean(body,str(p.relative_to(SITE))),original=str(p.relative_to(SITE))+('#reading' if i==1 else '')))
 elif slug=='crashed':
  for p in sorted((SITE/slug).glob('[0-9][0-9]-*.html')):
   d=doc(p);body=inner(get(d,'reading'))+get(d,'basis').html()+get(d,'sources').html();q=get(d,'notes').find(lambda n:n.tag=='label')
   episodes.append(dict(title=text(d,'h1'),question=q[0].text() if q else text(d,'h1'),body=clean(body,str(p.relative_to(SITE))),original=str(p.relative_to(SITE))))
 else:
  p=SITE/slug/'index.html';d=doc(p);body=inner(get(d,'article'))+get(d,'sources').html()
  episodes.append(dict(title='导读：为什么赢得战争，不等于赢得和平？',question='拥有力量，为什么仍可能无法建立持久的和平？',body=clean(body,str(p.relative_to(SITE))),original=f'{slug}/index.html#reading'))
 assert episodes,slug
 for i,e in enumerate(episodes):
  key=e['original'];identities.setdefault(key,f'{slug}:{i+1}' if not any(v==f'{slug}:{i+1}' for k,v in identities.items() if k!=key) else f'{slug}:u'+__import__('hashlib').sha256(key.encode()).hexdigest()[:12]);e['id']=identities[key];e['number']=i+1;e['minutes']=max(1,round(len(re.sub('<[^>]+>','',e['body']))/300));e['title']=unescape(e['title'])
 meta=dict(id=slug,title=title,count=len(episodes),description='现有完整导读 · 后续八期仅为阅读路线' if slug=='deluge' else f'{len(episodes)} 期主题阅读',episodes=[{k:v for k,v in e.items() if k!='body'} for e in episodes])
 books.append(meta);(SITE/'reading-data'/f'{slug}.json').write_text(json.dumps(episodes,ensure_ascii=False))
identity_path.write_text(json.dumps(identities,ensure_ascii=False,indent=2))
(SITE/'reading-data/catalog.json').write_text(json.dumps(books,ensure_ascii=False,indent=2))
# Inject shared, buildless navigation into every original page. Idempotent.
for p in SITE.glob('*/*.html'):
 if p.parent.name in ['reading-data','assets']:continue
 s=p.read_text();s=re.sub(r'<nav aria-label="系列导航".*?</nav>','',s,flags=re.S)
 if 'data-qtb-nav' not in s:
  nav='<link data-qtb-nav rel="stylesheet" href="../reading.css?v=1"><script defer src="../reading-core.js?v=1"></script><script defer src="../reading-nav.js?v=1"></script>'
  s=s.replace('</head>',nav+'</head>')
 p.write_text(s)
print(f'Built {len(books)} themes / {sum(b["count"] for b in books)} reading units')
