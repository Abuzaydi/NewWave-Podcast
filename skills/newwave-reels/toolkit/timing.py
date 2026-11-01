"""Estimated word timings for a slice of the episode, using Descript cue times + pauses in the clip audio."""
import re,subprocess
FILLERS={'um','uh','umm','erm'}
def ts(s):
    h,m,r=s.split(':');sec,ms=r.split(',');return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
CUES=[]
for b in open('/home/claude/newwave/episode.srt').read().strip().split('\n\n'):
    l=b.strip().split('\n')
    if len(l)>=3 and '-->' in l[1]:
        a,c=l[1].split(' --> ');CUES.append((ts(a),ts(c),' '.join(l[2:])))
def norm(w): return re.sub(r"[^a-z0-9$%']",'',w.lower().replace('’',"'"))
def words(start,end,clip):
    log=subprocess.run(['ffmpeg','-i',clip,'-af','silencedetect=noise=-35dB:d=0.12','-f','null','-'],capture_output=True,text=True).stderr
    sil=list(zip([float(x) for x in re.findall(r'silence_start: ([\d.]+)',log)],[float(x) for x in re.findall(r'silence_end: ([\d.]+)',log)]))
    out=[]
    for a,c,t in CUES:
        if c<=start or a>=end: continue
        a,c=a-start,c-start
        t=re.sub(r"-\s*(Yeah|Mm|Nice|Wow|Totally|That's it|Of course|Right)[^…]*…",' ',t)
        t=re.sub(r'\s+-\s+',' ',t).replace('…',' ')
        ws=[w for w in t.split() if re.search(r'[A-Za-z0-9]',w)]
        if not ws: continue
        inside=[(s,e) for s,e in sil if s>a+0.1 and e<c-0.1]
        spans=[];x=a
        for s,e in inside: spans.append((x,s)); x=e
        spans.append((x,c)); n=len(spans); groups=[[] for _ in range(n)]
        if n==1: groups[0]=ws
        else:
            tot=sum(e-s for s,e in spans); cum=0; bounds=[]
            for s,e in spans[:-1]: cum+=e-s; bounds.append(cum/tot)
            L=sum(len(w)+1 for w in ws); pos=[];acc=0
            for w in ws: acc+=len(w)+1; pos.append(acc/L)
            cuts=[]
            for bd in bounds:
                cand=range(len(ws)-1)
                i=min(cand,key=lambda i:abs(pos[i]-bd)+(0 if ws[i].endswith((',','.','?','!')) else 0.08))
                cuts.append(i+1)
            prev=0
            for gi,ct in enumerate(sorted(set(cuts))+[len(ws)]):
                groups[min(gi,n-1)]+=ws[prev:ct]; prev=ct
        for (s,e),g in zip(spans,groups):
            if not g: continue
            wt=[len(w)+2 for w in g]; T=sum(wt); x=s
            for w,k in zip(g,wt):
                d=(e-s)*k/T; out.append([x,x+d,w]); x+=d
    out=[o for o in out if o[1]>0.05 and o[0]<end-start-0.05]
    for o in out: o[0]=max(o[0],0); o[1]=min(o[1],end-start)
    clean=[]
    for s,e,w in out:
        if norm(w) in FILLERS:
            if clean: clean[-1][1]=e
            continue
        clean.append([s,e,w])
    return clean
