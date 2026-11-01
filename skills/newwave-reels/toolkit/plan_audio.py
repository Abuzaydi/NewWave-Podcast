"""Build the music/SFX plan from a clip's exact cue times. usage: plan_audio.py name spec.json out.json"""
import json,sys
name,spec,out=sys.argv[1],sys.argv[2],sys.argv[3]
C=json.load(open(f'build/{name}_cues.json')); F=json.load(open(f'build/{name}_fx.json')); S=json.load(open(spec))
E=C['emph']; dur=C['dur']
def t(key):
    k=key.lower()
    for a,w in E:
        if w.lower().replace(',','').startswith(k): return a
    raise SystemExit('no '+key)
A=S.get('audio',{})
br=[a for a,L in F['broll']]
bw=F['bw']
plan={"dur":dur,"sections":[],"whoosh":[],"whoosh_big":[round(a+0.04,2) for a in br],"impact":[],"cash":[],"glitch":[],"riser":[],"ticks":[],"mute":[]}
plan['whoosh']=[round(a,2) for a,w in E if all(abs(a-b-0.04)>0.4 for b in br)]
for k in A.get('impact',[]): plan['impact'].append([round(t(k[0])+k[1],2),k[2]])
for k in A.get('cash',[]): plan['cash'].append(round(t(k),2))
for k in A.get('glitch',[]): plan['glitch'].append(round(t(k),2))
for k,pre in A.get('riser',[]): z=t(k); plan['riser'].append([round(z-pre,2),round(z,2)])
for k,a0,n,step in A.get('ticks',[]): z=t(k); plan['ticks']+= [round(z+a0+i*step,2) for i in range(n)]
for k,end in A.get('mute',[]): plan['mute'].append([round(t(k),2),end])
for sec in A['sections']:
    s0=t(sec['s']) if isinstance(sec['s'],str) else sec['s']; s1=t(sec['e']) if isinstance(sec['e'],str) else sec['e']
    d={x:y for x,y in sec.items() if x not in('s','e')}; d['s']=round(s0+sec.get('s_off',0),2); d['e']=round(s1+sec.get('e_off',0),2)
    if 'bells_rel' in d: d['bells']=[[round(d['s']+r,2),m] for r,m in d.pop('bells_rel')]
    plan['sections'].append(d)
json.dump(plan,open(out,'w'),indent=1); print(json.dumps({k:v for k,v in plan.items() if k!='sections'}))
