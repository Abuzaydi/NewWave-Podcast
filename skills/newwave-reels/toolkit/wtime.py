"""Exact word times with Whisper, aligned onto the Descript transcript words."""
import json,os,re,difflib,subprocess
def norm(w):
    w=re.sub(r"[^a-z0-9]",'',w.lower().replace('’',"'"))
    if not w: return w
    sk=w[0]+re.sub(r'[aeiouwhy]','',w[1:])
    return re.sub(r'(.)\1+',r'\1',sk)
def whisper_words(clip,cache):
    if os.path.exists(cache): return json.load(open(cache))
    os.environ['NO_PROXY']='';os.environ['no_proxy']=''
    from faster_whisper import WhisperModel
    wav=cache.replace('.json','.wav')
    subprocess.run(['ffmpeg','-v','error','-y','-i',clip,'-ac','1','-ar','16000',wav],check=True)
    m=WhisperModel('small.en',device='cpu',compute_type='int8')
    from scipy.io import wavfile; import numpy as np
    sr,au=wavfile.read(wav); au=(au.astype(np.float32)/32768.0)
    segs,_=m.transcribe(au,word_timestamps=True,vad_filter=False,beam_size=5,condition_on_previous_text=False)
    out=[[w.start,w.end,w.word.strip()] for s in segs for w in s.words]
    json.dump(out,open(cache,'w')); return out
def refine(desc,ww):
    """desc: [[s,e,word],...] estimated; ww: whisper [[s,e,word]]. Returns desc with whisper times where words match."""
    A=[norm(w) for _,_,w in desc]; B=[norm(w) for _,_,w in ww]
    sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
    got=[None]*len(desc)
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal':
            for k in range(i2-i1): got[i1+k]=(ww[j1+k][0],ww[j1+k][1])
        elif tag=='replace' and (i2-i1)==(j2-j1):
            for k in range(i2-i1): got[i1+k]=(ww[j1+k][0],ww[j1+k][1])
        elif tag=='replace':
            # spread the whisper span over the descript words
            s0,e0=ww[j1][0],ww[j2-1][1]; n=i2-i1
            for k in range(n): got[i1+k]=(s0+(e0-s0)*k/n,s0+(e0-s0)*(k+1)/n)
    # interpolate gaps
    out=[]; matched=sum(1 for g in got if g)
    for k,(s,e,w) in enumerate(desc):
        if got[k]: out.append([got[k][0],got[k][1],w]); continue
        prv=next((got[j][1] for j in range(k-1,-1,-1) if got[j]),None)
        nxt=next((got[j][0] for j in range(k+1,len(got)) if got[j]),None)
        if prv is not None and nxt is not None and nxt>prv: out.append([prv,min(nxt,prv+0.25),w])
        else: out.append([s,e,w])
    return out,matched
