"""Verbatim word timing: Whisper per transcript window, prompted with the exact Descript text."""
import json,os,re,subprocess
import numpy as np
from scipy.io import wavfile
def run(clip,cache,desc_cues,model='medium.en'):
    """desc_cues: [[start,end,text],...] relative to the clip."""
    if os.path.exists(cache): return json.load(open(cache))
    os.environ['NO_PROXY']='';os.environ['no_proxy']=''
    from faster_whisper import WhisperModel
    wav=cache.replace('.json','.wav')
    subprocess.run(['ffmpeg','-v','error','-y','-i',clip,'-ac','1','-ar','16000',wav],check=True)
    sr,a=wavfile.read(wav); a=a.astype(np.float32)/32768
    m=WhisperModel(model,device='cpu',compute_type='int8')
    # merge cues into windows of <=10s
    wins=[]; cur=None
    for s,e,t in desc_cues:
        if cur and e-cur[0]<=10 and s-cur[1]<1.0: cur=[cur[0],e,cur[2]+' '+t]
        else:
            if cur: wins.append(cur)
            cur=[s,e,t]
    if cur: wins.append(cur)
    out=[]
    for k,(s,e,t) in enumerate(wins):
        lo=max(0,s-0.35); hi=min(len(a)/sr,e+0.35)
        seg=a[int(lo*sr):int(hi*sr)]
        segs,_=m.transcribe(seg,word_timestamps=True,beam_size=5,temperature=0,condition_on_previous_text=False,
                            initial_prompt=t,without_timestamps=False)
        ws=[[w.start+lo,w.end+lo,w.word.strip()] for sg in segs for w in sg.words]
        nxt=wins[k+1][0] if k+1<len(wins) else 1e9; prv=wins[k-1][1] if k else -1e9
        ws=[w for w in ws if (prv+e)/2 if True]  # keep all; dedupe below
        out+=ws
    out.sort(key=lambda x:x[0])
    ded=[]
    for w in out:
        if ded and abs(w[0]-ded[-1][0])<0.05 and w[2].lower()==ded[-1][2].lower(): continue
        ded.append(w)
    json.dump(ded,open(cache,'w')); return ded

def norm(w):
    w=re.sub(r"[^a-z0-9]",'',w.lower())
    if not w: return w
    sk=w[0]+re.sub(r'[aeiouwhy]','',w[1:])
    return re.sub(r'(.)\1+',r'\1',sk)
def combine(desc,full,win,desc_cues):
    """For each transcript window choose the Whisper source that matches the transcript best, then align."""
    import difflib
    from wtime import refine
    words=[]
    for s,e,t in desc_cues:
        d=[x for x in desc if s-0.05<=x[0]<e+0.05] if False else None
    out=[]; i=0
    # assign each desc word to its cue index by order
    cue_words=[]
    for s,e,t in desc_cues:
        n=len([w for w in t.split() if re.search(r'[A-Za-z0-9]',w)])
        cue_words.append((s,e))
    # group desc words by time into cue windows
    res=[None]*len(desc)
    for s,e,t in desc_cues:
        idx=[k for k,x in enumerate(desc) if s-0.01<=x[0]<e+0.01 and res[k] is None]
        if not idx: continue
        dw=[desc[k] for k in idx]
        best=None
        for name,src in (('win',win),('full',full)):
            sw=[w for w in src if s-0.4<=w[0]<e+0.4]
            if not sw: continue
            r=difflib.SequenceMatcher(None,[norm(x[2]) for x in dw],[norm(x[2]) for x in sw],autojunk=False).ratio()
            if best is None or r>best[0]+0.02: best=(r,name,sw)
        if best is None: continue
        ref,_=refine(dw,best[2])
        for k,x in zip(idx,ref): res[k]=x
    return [r if r else d for r,d in zip(res,desc)]
