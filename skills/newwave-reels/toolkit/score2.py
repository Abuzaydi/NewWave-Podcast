"""Original music + cinematic SFX. usage: python3 score2.py plan.json out.wav"""
import numpy as np,json,sys
from scipy.signal import butter,sosfilt,fftconvolve
from scipy.io import wavfile
SR=48000; P=json.load(open(sys.argv[1])); D=P['dur']; N=int(SR*(D+3))
rng=np.random.default_rng(11)
def f(n): return 440*2**((n-69)/12)
def lp(x,fc,o=4): return sosfilt(butter(o,fc,'low',fs=SR,output='sos'),x)
def hp(x,fc,o=2): return sosfilt(butter(o,fc,'high',fs=SR,output='sos'),x)
def bp(x,a,b): return sosfilt(butter(2,[a,min(b,SR/2-100)],'band',fs=SR,output='sos'),x)
ML=np.zeros(N);MR=np.zeros(N);SL=np.zeros(N);SR_=np.zeros(N)
def add(sig,start,gain=1.0,pan=0.0,sfx=False):
    i=int(start*SR)
    if i<0: sig=sig[-i:]; i=0
    sig=sig[:max(0,N-i)]*gain
    L,R=(SL,SR_) if sfx else (ML,MR)
    L[i:i+len(sig)]+=sig*(1-pan); R[i:i+len(sig)]+=sig*(1+pan)
def tt(d): return np.arange(int(d*SR))/SR
def env(n,a,r):
    e=np.ones(n); a=max(1,int(a*SR)); r=max(1,int(r*SR)); e[:a]=np.linspace(0,1,a); e[-r:]*=np.linspace(1,0,r); return e
# ---------------- MUSIC
for sec in P['sections']:
    s0,s1=sec['s'],sec['e']; ch=sec['chords']; step=(s1-s0)/len(ch)
    for k,notes in enumerate(ch):
        cs=s0+k*step; d=step+1.0; t=tt(d); sig=np.zeros(len(t))
        for m in notes:
            for det in (-0.06,0,0.05):
                fr=f(m)*2**(det/12)
                for h in range(1,6): sig+=np.sin(2*np.pi*fr*h*t+rng.uniform(0,6))/(h**1.4)
        sig=lp(sig,sec.get('bright',900))*env(len(t),0.5 if k else 0.9,0.9)
        add(sig/len(notes),cs,sec.get('pad',0.05),rng.uniform(-0.2,0.2))
        add(np.sin(2*np.pi*f(notes[0]-12)*t)*env(len(t),0.4,0.9),cs,sec.get('sub',0.09))
    if sec.get('kick'):
        per=60/sec['kick']; x=s0
        while x<s1-0.1:
            t=tt(0.4); k_=np.sin(2*np.pi*np.cumsum(np.linspace(120,45,len(t)))/SR)*np.exp(-t*12)
            add(lp(k_,220),x,sec.get('kick_gain',0.25))
            t=tt(0.08); hh=hp(rng.standard_normal(len(t)),7000)*np.exp(-t*60)
            add(hh,x+per/2,0.012,0.3)
            x+=per
    if sec.get('pulse'):
        per=60/sec['pulse']; x=s0
        while x<s1-0.2:
            for off,g in ((0,1.0),(0.22,0.6)):
                t=tt(0.35); k_=np.sin(2*np.pi*np.cumsum(np.linspace(85,42,len(t)))/SR)*np.exp(-t*14)
                add(lp(k_,180),x+off,0.24*g)
            x+=per
    for bs,m in sec.get('bells',[]):
        t=tt(2.4); b=(np.sin(2*np.pi*f(m)*t)+0.35*np.sin(2*np.pi*f(m)*2.01*t))*np.exp(-t*2.4)*np.minimum(1,t/0.004)
        add(b,bs,0.045,rng.uniform(-0.4,0.4))
    if sec.get('arp'):
        a=sec['arp']; per=a['step']; x=s0; j=0
        while x<s1-0.1:
            notes=ch[min(int((x-s0)/step),len(ch)-1)]; m=notes[j%len(notes)]+12
            t=tt(0.5); pl=np.sin(2*np.pi*f(m)*t)*np.exp(-t*9)+0.3*np.sin(2*np.pi*f(m)*2*t)*np.exp(-t*14)
            add(lp(pl,3500),x,a.get('gain',0.035),0.35*np.sin(j)); x+=per; j+=1
# ---------------- SFX
def whoosh(at,big=False):
    d=0.9 if big else 0.5; t=tt(d); nz=rng.standard_normal(len(t)); out=np.zeros(len(t))
    for k in range(0,len(t),1024):
        fc=400+(7000 if big else 4500)*(k/len(t)); out[k:k+1024]=bp(nz[k:k+1024],fc*0.6,fc*1.5)
    e=np.sin(np.pi*np.clip(t/d,0,1))**(1.5 if big else 2)
    add(out*e,at-d*0.78,0.03 if big else 0.015,rng.uniform(-0.5,0.5),sfx=True)
def impact(at,g=1.0):
    t=tt(2.5); boom=np.sin(2*np.pi*np.cumsum(np.linspace(70,30,len(t)))/SR)*np.exp(-t*1.8)
    crack=lp(rng.standard_normal(len(t)),1600)*np.exp(-t*9)
    add(boom,at,0.6*g,sfx=True); add(crack,at,0.18*g,sfx=True)
def cash(at):
    for k,(fr,dl) in enumerate(((2093,0),(2637,0.07))):
        t=tt(1.2); b=(np.sin(2*np.pi*fr*t)+0.5*np.sin(2*np.pi*fr*2.76*t))*np.exp(-t*4)
        add(b,at+dl,0.07,0.2*(k*2-1),sfx=True)
    t=tt(0.25); r=bp(rng.standard_normal(len(t)),3000,9000)*np.exp(-t*18); add(r,at-0.03,0.03,sfx=True)
def glitch(at):
    d=0.45; t=tt(d); out=np.zeros(len(t))
    for k in range(0,len(t),int(SR*0.03)):
        seg=int(SR*0.03)
        if rng.random()<0.65:
            fr=rng.choice([180,360,720,1440,90]); x=np.sign(np.sin(2*np.pi*fr*t[k:k+seg]))*0.5+rng.standard_normal(len(t[k:k+seg]))*0.5
            out[k:k+seg]=np.round(x*4)/4
    add(lp(out,6000),at-0.02,0.08,sfx=True)
def riser(s,e):
    d=e-s; t=tt(d); nz=hp(rng.standard_normal(len(t)),300)*(t/d)**2
    tone=np.sin(2*np.pi*np.cumsum(np.linspace(110,520,len(t)))/SR)*(t/d)**2.5
    add(nz,s,0.02,sfx=True); add(tone,s,0.035,sfx=True)
def tick(at):
    t=tt(0.05); c=hp(rng.standard_normal(len(t)),2500)*np.exp(-t*120); add(c,at,0.06,0.3,sfx=True)
for a in P.get('whoosh',[]): whoosh(a)
for a in P.get('whoosh_big',[]): whoosh(a,True)
for a in P.get('impact',[]): impact(*a) if isinstance(a,list) else impact(a)
for a in P.get('cash',[]): cash(a)
for a in P.get('glitch',[]): glitch(a)
for s,e in P.get('riser',[]): riser(s,e)
for a in P.get('ticks',[]): tick(a)
# mute windows (music only)
for s,e in P.get('mute',[]):
    i0=int(s*SR); i1=int(e*SR); r=int(0.04*SR)
    for X in (ML,MR):
        X[i0:i0+r]*=np.linspace(1,0,r); X[i0+r:i1]=0; X[i1:i1+int(0.6*SR)]*=np.linspace(0,1,int(0.6*SR))
# reverb
ir_n=int(2.0*SR); ir=lp(rng.standard_normal(ir_n)*np.exp(-np.arange(ir_n)/SR*3.2),4000); ir/=np.sqrt((ir**2).sum())
def verb(L,R,w): return L*0.78+fftconvolve(L,ir)[:N]*w, R*0.78+fftconvolve(R,ir[::-1].copy())[:N]*w
ML,MR=verb(ML,MR,0.35); SL,SR_=verb(SL,SR_,0.25)
Mx=np.stack([ML,MR],1)[:int(D*SR)]; Sx=np.stack([SL,SR_],1)[:int(D*SR)]
fd=int(0.8*SR); Mx[-fd:]*=np.linspace(1,0,fd)[:,None]
Mx/=np.abs(Mx).max()+1e-9; Sx*=0.9
wavfile.write(sys.argv[2].replace('.wav','_music.wav'),SR,(Mx*0.8*32767).astype(np.int16))
wavfile.write(sys.argv[2].replace('.wav','_sfx.wav'),SR,(Sx*0.8*32767).astype(np.int16))
print('ok')
