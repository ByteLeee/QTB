#!/usr/bin/env python3
"""Python 3 / stdlib only. A controller experiment, NOT a real LLM benchmark.
Run: python3 agent-control-experiment.py [--output trace.json]
Optional: --policy module:function replaces simulated decisions with your own
callable(observation)->{'action':'read','document':id} or {'action':'finish'}.
The controller still enforces tool scope and budget. No files except --output
are written; no network access or credentials are required.
"""
import argparse,importlib,json
DOCS={'hours':{'open':'09:00'},'fee':{'price':'5'},'old':{'price':'3'},'empty':{}}
CASES=[
 {'id':'01','key':'open','scope':['hours'],'expected':'09:00'},
 {'id':'02','key':'price','scope':['fee'],'expected':'5'},
 {'id':'03','key':'price','scope':['old','fee'],'expected':'conflict'},
 {'id':'04','key':'missing','scope':['hours'],'expected':'unknown'},
 {'id':'05','key':'open','scope':['empty','hours'],'expected':'09:00'},
 {'id':'06','key':'price','scope':['empty','fee'],'expected':'5'},
 {'id':'07','key':'open','scope':[],'expected':'unknown'},
 {'id':'08','key':'price','scope':['old','fee','empty'],'expected':'conflict'},
 {'id':'09','key':'open','scope':['fee','empty'],'expected':'unknown'},
 {'id':'10','key':'price','scope':['old','empty'],'expected':'3'}]
for case in CASES:
 case['required']=case['scope'][:]
 case['scope']=['hours','fee','old','empty']
def simulated_policy(o):
 # Deterministic stand-in: this function cannot demonstrate model intelligence.
 left=[d for d in o['required'] if d not in o['read']]
 return {'action':'read','document':left[0]} if left else {'action':'finish'}
def conclude(key,read):
 values={DOCS[d][key] for d in read if key in DOCS[d]}
 return 'unknown' if not values else next(iter(values)) if len(values)==1 else 'conflict'
def run(case,policy,budget=4):
 read=[];trace=[];stopped=False
 for turn in range(budget+1):
  decision=policy({'key':case['key'],'scope':case['scope'][:],'read':{d:DOCS[d] for d in read},'required':case['required'][:],'remaining':budget-len(read)})
  if not isinstance(decision,dict):trace.append({'error':'invalid decision'});break
  if decision.get('action')=='finish':stopped=True;trace.append({'action':'finish'});break
  d=decision.get('document')
  if decision.get('action')!='read' or d not in case['scope'] or d in read:trace.append({'error':'invalid or out-of-scope tool action','decision':decision});break
  if len(read)>=budget:trace.append({'error':'budget exceeded'});break
  read.append(d);trace.append({'action':'read','document':d,'result':DOCS[d]})
 result=conclude(case['key'],[d for d in read if d in case['required']])
 return {'id':case['id'],'result':result,'calls':len(read),'pass':stopped and result==case['expected'],'trace':trace}
def fixed_policy(case):
 # A preset order over an allowed pool; irrelevant reads are visible overhead.
 order=case['scope']+[d for d in ['hours','fee','empty'] if d not in case['scope']]
 # Fixed workflow may read only the same permitted scope as the adaptive one.
 order=[d for d in order if d in case['scope']]
 return lambda o: {'action':'read','document':next(d for d in order if d not in o['read'])} if any(d not in o['read'] for d in order) else {'action':'finish'}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output');ap.add_argument('--policy');args=ap.parse_args()
 policy=simulated_policy
 if args.policy:
  module,name=args.policy.split(':',1);policy=getattr(importlib.import_module(module),name)
 rows=[]
 for c in CASES:
  a=run(c,fixed_policy(c));b=run(c,policy)
  rows.append({'case':c['id'],'fixed':a,'adaptive':b})
 print('Simulation only; latency and token costs are NOT measured.')
 print('case fixed/pass/calls adaptive/pass/calls')
 for r in rows:print(r['case'],r['fixed']['pass'],r['fixed']['calls'],r['adaptive']['pass'],r['adaptive']['calls'])
 # Boundary checks independent of the tested policy.
 attack=run(CASES[0],lambda o:{'action':'read','document':'secret'})
 assert not attack['pass'] and attack['calls']==0
 loop=run(CASES[0],lambda o:{'action':'read','document':'hours'})
 assert not loop['pass']
 assert len(rows)==10
 if args.output:
  with open(args.output,'w',encoding='utf-8') as f:json.dump({'simulation':True,'rows':rows,'scope_test':attack,'loop_test':loop},f,ensure_ascii=False,indent=2)
 print('Scope and repeated-action rejection checks: PASS')
if __name__=='__main__':main()
