"""Render one New Wave clip in the reference style.
usage: python3 make_clip.py spec.json"""
import json,sys,re,subprocess,os
from PIL import ImageFont
from timing import words,norm
from shots import layout
S=json.load(open(sys.argv[1])); name=S['name']
VERT=len(sys.argv)>2 and sys.argv[2]=='vertical'
W,H=(1080,1920) if VERT else (1920,1080)
oname=name+('_vertical' if VERT else '')
src,ss,dur=S['src'],S['src_start'],S['dur']
ep0=S['ep_start']
os.makedirs('build',exist_ok=True); os.makedirs('out',exist_ok=True)
cut=f'build/{name}_cut.mp4'
if not os.path.exists(cut):
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(ss),'-i',src,'-t',str(dur),'-c:v','libx264','-preset','veryfast','-crf','12','-c:a','aac','-b:a','256k',cut],check=True)
WT=words(ep0,ep0+dur,cut)
import wtime,wtime2
from timing import CUES as _CUES
_cues=[[max(a_-ep0,0),min(c_-ep0,dur),re.sub(r"\s*-\s*(Yeah|Mm|Nice|Wow|Totally|That's it|Of course|Right)[^…]*…",' ',t_).replace('…',' ')] for a_,c_,t_ in _CUES if c_>ep0 and a_<ep0+dur]
_full=wtime2.run(cut,f'build/{name}_whisper_full.json',[[0,dur,'']],model='medium.en')
_win=wtime2.run(cut,f'build/{name}_whisper_win.json',_cues,model='medium.en')
WT=wtime2.combine(WT,_full,_win,_cues); print('  exact word timing: verbatim-aligned'); json.dump(WT,open(f'build/{name}_words.json','w'))
SH=layout(cut)
for ov in ([] if VERT else S.get('layout_override',[])):
    for sh in SH:
        if abs(sh['start']-ov['at'])<0.3: sh['x']=ov['x']; sh['y']=ov['y']; sh['kind']=ov.get('kind',sh['kind']); sh['locked']=1
for sh in SH:
    if sh['kind']=='wide' and not sh.get('locked'): sh['y']=S.get('wide_y',0.17)
    if VERT:
        sh['cx']=(sh['face'][0] if sh['kind']=='close' and sh['face'] else S.get('wide_focus_x',0.5))
        for ov in S.get('vcx_override',[]):
            if abs(sh['start']-ov['at'])<0.3: sh['cx']=ov['cx']
        sh['x']=0.5; sh['y']=0.575 if sh['kind']=='close' else 0.68
# --- match phrases to timed words
ALIAS={'paps':'perps','moritz':'maurits','mauriz':'maurits','zach':'zec'}
toks=[[s,e,w,ALIAS.get(norm(w),norm(w))] for s,e,w in WT]; i=0; phrases=[]
for ph in S['phrases']:
    flag='!' if ph.startswith('!') else ''; ph=ph.lstrip('!')
    parts=re.findall(r'\*[^*]+\*|[^\s*]+',ph); items=[]
    for p in parts:
        emph=p.startswith('*')
        for w in p.strip('*').split():
            hero=w.startswith('#'); w=w.lstrip('#')
            if not re.search(r'[A-Za-z0-9]',w): continue
            n=norm(w)
            while i<len(toks) and toks[i][3]!=n:
                print('  skipped transcript word:',toks[i][2]); i+=1
            if i>=len(toks): sys.exit(f'could not match "{w}" in phrase "{ph}"')
            items.append(dict(t=toks[i][0],e=toks[i][1],w=w,emph=emph,hero=hero)); i+=1
    phrases.append(dict(items=items,flag=flag))
if i<len(toks): print('  unused words at end:',' '.join(t[2] for t in toks[i:]))
for k,p in enumerate(phrases[:-1]):
    em=[it for it in p['items'] if it['emph']]
    if em and S.get('hold_emphasis',False):
        nxt=phrases[k+1]['items'][0]
        want=em[0]['t']+0.6
        if nxt['t']<want: nxt['t']=min(want,nxt['t']+0.3)
        # keep later words in order
        for it in phrases[k+1]['items'][1:]:
            if it['t']<nxt['t']: it['t']=nxt['t']
for k,p in enumerate(phrases):
    p['start']=p['items'][0]['t']; last=p['items'][-1]['e']
    nxt=phrases[k+1]['items'][0]['t'] if k+1<len(phrases) else dur
    p['end']=nxt if nxt-last<0.7 else last+0.45
def disp(w,emph):
    w=w.replace(',','').replace(';','')
    if not w.endswith('?'): w=w.rstrip('.')
    return w
def _norm(x): return re.sub(r'[^a-z0-9 ]','',x.lower())
def emph_time0(key):
    for p in phrases:
        em=[it for it in p['items'] if it['emph']]
        if em and _norm(' '.join(disp(x['w'],True) for x in em)).startswith(_norm(key)):
            return em[0]['t']
    sys.exit('emphasis not found: '+key)
BRW=[]
for b in S.get('broll',[]):
    if os.path.exists(b['img']):
        a0=emph_time0(b['word'])-0.04+b.get('offset',0); cap=b.get('capv' if VERT else 'cap')
        BRW.append((a0,a0+b.get('len',1.4),cap))
# --- fonts / measuring
WF=ImageFont.truetype(os.path.expanduser('~/.fonts/Poppins-ExtraBold.ttf'),100)
RF=ImageFont.truetype(os.path.expanduser('~/.fonts/PlayfairDisplay-Italic[wght].ttf'),100)
try: RF.set_variation_by_name('Bold Italic')
except Exception: pass
def wid(font,txt,size,sx=1.0): return font.getlength(txt)*size/100*sx
def disp(w,emph):
    w=w.replace(',','').replace(';','')
    if not w.endswith('?'): w=w.rstrip('.')
    return w
def wrap(ws,maxch=20):
    lines=[[]]
    for w in ws:
        if lines[-1] and len(' '.join(x['d'] for x in lines[-1]+[w]))>maxch: lines.append([])
        lines[-1].append(w)
    return [l for l in lines if l]
RED='&H001B17E3&'; GLOW='&H001010C8&'
def t2(x): return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
ev=[]
def shot_at(t):
    for sh in SH:
        if sh['start']<=t+0.05<sh['end']: return sh
    return SH[-1]
bw=[]
for p in phrases:
    its=p['items']
    for it in its: it['d']=disp(it['w'],it['emph'])
    ei=[k for k,it in enumerate(its) if it['emph']]
    pre=its[:ei[0]] if ei else its; em=its[ei[0]:ei[-1]+1] if ei else []; post=its[ei[-1]+1:] if ei else []
    if p['flag'] and em: bw.append((em[0]['t'],p['end']))
    # reveal steps
    times=[it['t'] for it in its]
    # split by shot changes too
    bounds=sorted(set(times+[sh['start'] for sh in SH if p['start']<sh['start']<p['end']]+[x for a_,b2,c_ in BRW if c_ for x in (a_,b2) if p['start']<x<p['end']]+[p['end']]))
    bounds=[b for b in bounds if p['start']<=b<=p['end']]
    for a,b in zip(bounds,bounds[1:]):
        if b-a<0.02: continue
        sh=shot_at(a); X=int(sh['x']*W); Y=int(sh['y']*H)
        for a_,b2,c_ in BRW:
            if c_ and a_<=a+0.001<b2: X=int(c_[0]*W); Y=int(c_[1]*H)
        if p['flag'] and em and a>=em[0]['t'] and sh['kind']=='close' and not VERT: X,Y=W//2,int(H*0.36)
        maxw=(0.90*W) if VERT else (0.40*W if sh['kind']=='close' else 0.62*W)
        shown=lambda it: it['t']<=a+0.001
        wsz=(92 if em else 108) if VERT else (88 if em else 104)
        mc=(16 if em else 13) if VERT else (18 if em else 14)
        lines=wrap(pre,mc)
        while VERT and len(lines)>2: mc+=2; lines=wrap(pre,mc)
        lh=int(wsz*1.12)
        # emphasis size to fit
        etxt=' '.join(x['d'] for x in em)
        esz=320 if VERT else 235
        if em:
            while wid(RF,etxt,esz,0.78)>maxw and esz>110: esz-=8
            if VERT: esz=max(esz,150)
        top_y=Y-(len(lines)-1)*lh-int(lh*0.35) if em else Y-(len(lines)-1)*lh//2
        for li,l in enumerate(lines):
            txt=''
            for it in l:
                al='&H00&' if shown(it) else '&HFF&'
                fade=r'\t(0,70,\alpha&H00&)' if abs(it['t']-a)<0.001 else ''
                txt+=f"{{\\alpha{al}}}"+(f"{{\\alpha&HFF&{fade}}}" if fade else '')+it['d']+' '
            y=top_y+li*lh
            ev.append(f"Dialogue: 1,{t2(a)},{t2(b)},WGlow,,0,0,0,,{{\\an5\\pos({X},{y})\\fs{wsz}\\blur14}}{txt.strip()}")
            ev.append(f"Dialogue: 2,{t2(a)},{t2(b)},White,,0,0,0,,{{\\an5\\pos({X},{y})\\fs{wsz}}}{txt.strip()}")
        if em and a>=em[0]['t']-0.001:
            ey=Y+int(esz*0.24)
            first=abs(em[0]['t']-a)<0.001
            anim=r'\fscx92\fscy112\t(0,180,\fscx78\fscy100)' if first else r'\fscx78'
            ew=int(wid(RF,etxt,esz,0.78))+60
            clip=f"\\clip({X-ew//2-80},0,{X-ew//2-80},{H})\\t(0,200,\\clip({X-ew//2-80},0,{W},{H}))" if first else ''
            ev.append(f"Dialogue: 0,{t2(a)},{t2(b)},Glow,,0,0,0,,{{\\an5\\pos({X},{ey})\\fs{esz}\\blur22\\alpha&H70&{anim}{clip}}}{etxt}")
            ev.append(f"Dialogue: 1,{t2(a)},{t2(b)},Red,,0,0,0,,{{\\an5\\pos({X},{ey})\\fs{esz}{anim}{clip}}}{etxt}")
            for pi,it in enumerate(post):
                if shown(it):
                    pass
            pt=' '.join(it['d'] for it in post if shown(it))
            if pt:
                ev.append(f"Dialogue: 2,{t2(a)},{t2(b)},White,,0,0,0,,{{\\an5\\pos({X+int(ew*0.18)},{ey+int(esz*0.52)})\\fs66}}{pt}")

if S.get('cap_style')=='clean':
    ev=[]
    PRESETS={
     'approved':dict(FS=(92,82),HS=(250,210),MAXC=(20,27),reg_tag='{\\fnPlayfair Display\\b1\\i1}',bold_tag='{\\fnPoppins\\b1\\i0}',
                     close=(0.74,0.80),vy=0.585,hero_font='Playfair Display',hero_italic=1,hero_sx=78),
     'straight':dict(FS=(104,100),HS=(215,190),MAXC=(15,22),reg_tag='{\\fnPoppins SemiBold\\b0\\i0}',bold_tag='{\\fnPoppins ExtraBold\\b0\\i0}',
                     close=(0.50,0.905),vy=0.585,hero_font='Poppins ExtraBold',hero_italic=0,hero_sx=100)}
    PR=PRESETS[S.get('cap_preset','approved')]
    FS=PR['FS'][0 if VERT else 1]; HS=PR['HS'][0 if VERT else 1]; MAXC=PR['MAXC'][0 if VERT else 1]
    _FSB=ImageFont.truetype(os.path.expanduser('~/.fonts/Poppins-ExtraBold.ttf'),100); _FSS=ImageFont.truetype(os.path.expanduser('~/.fonts/Poppins-SemiBold.ttf'),100)
    def word_txt(it):
        d=disp(it['w'],it['emph'])
        if it['emph']: return PR['bold_tag']+d
        return PR['reg_tag']+d
    def place(a):
        sh=shot_at(a); X=sh['x']; Y=sh['y']
        if VERT: X,Y=0.5,PR['vy']
        elif sh['kind']=='close': X,Y=PR['close']
        else: X,Y=0.5,0.60
        for a_,b2,c_ in BRW:
            if c_ and a_<=a+0.001<b2: X,Y=c_
        return int(X*W),int(Y*H)
    for k,p in enumerate(phrases):
        its=p['items']; groups=[]
        for it in its: it['d']=disp(it['w'],it['emph'])
        # split around hero words, then chunk each run with a small DP: few chunks, no 1-word chunks,
        # prefer breaks after punctuation, never split a bold group
        runs=[]; cur=[]
        for it in its:
            if it['hero']:
                if cur: runs.append(cur); cur=[]
                runs.append([it]); continue
            cur.append(it)
        if cur: runs.append(cur)
        for run in runs:
            if run[0]['hero']: groups.append(run); continue
            n=len(run); INF=1e9; best=[INF]*(n+1); prv=[0]*(n+1); best[0]=0
            for j in range(1,n+1):
                for i in range(j-1,-1,-1):
                    ch=run[i:j]; L=len(' '.join(x['d'] for x in ch))
                    if L>MAXC and j-i>1: break
                    c=10+(14 if (j-i)==1 and n>1 else 0)
                    if j<n and not run[j-1]['w'].endswith((',','.','?','!')): c+=3
                    if j<n and run[j-1]['emph'] and run[j]['emph']: c+=25
                    if best[i]+c<best[j]: best[j]=best[i]+c; prv[j]=i
            cuts=[]; j=n
            while j>0: cuts.append((prv[j],j)); j=prv[j]
            for i,j in reversed(cuts): groups.append(run[i:j])
        for gi,g in enumerate(groups):
            g0=g[0]['t']; g1=groups[gi+1][0]['t'] if gi+1<len(groups) else p['end']
            hero=g[0]['hero']
            prev=groups[gi-1] if (hero and gi>0 and not groups[gi-1][0]['hero']) else None
            times=sorted(set([it['t'] for it in g]+[x for sh in SH for x in [sh['start']] if g0<x<g1]+[x for a_,b2,c_ in BRW if c_ for x in (a_,b2) if g0<x<g1]+[g1]))
            times=[x for x in times if x>=g0]
            for a,b in zip(times,times[1:]):
                if b-a<0.02: continue
                X,Y=place(a)
                if hero:
                    it=g[0]; first=abs(it['t']-a)<0.001
                    _sx=PR['hero_sx']; anim=('\\fscx%d\\fscy112\\t(0,180,\\fscx%d\\fscy100)'%(int(_sx*1.12),_sx)) if first else ('\\fscx%d'%_sx)
                    hy=min(Y+int(HS*0.18),H-int(HS*0.55))
                    ev.append(f"Dialogue: 0,{t2(a)},{t2(b)},Glow,,0,0,0,,{{\\an5\\pos({X},{hy})\\fs{HS}\\blur22\\alpha&H70&{anim}}}{it['d']}")
                    ev.append(f"Dialogue: 1,{t2(a)},{t2(b)},Red,,0,0,0,,{{\\an5\\pos({X},{hy})\\fs{HS}{anim}}}{it['d']}")
                    if prev:
                        pt=' '.join(word_txt(x) for x in prev)
                        ev.append(f"Dialogue: 2,{t2(a)},{t2(b)},Clean,,0,0,0,,{{\\an5\\pos({X},{hy-int(HS*0.55)})\\fs{int(FS*0.85)}}}{pt}")
                    continue
                txt=''
                for it in g:
                    shown=it['t']<=a+0.001
                    if not shown: txt+='{\\alpha&HFF&}'+word_txt(it)+' '; continue
                    if abs(it['t']-a)<0.001: txt+='{\\alpha&HFF&\\t(0,110,\\alpha&H00&)}'+word_txt(it)+' '
                    else: txt+='{\\alpha&H00&}'+word_txt(it)+' '
                _w=sum(_FSB.getlength(x['d']+' ') if x['emph'] else _FSS.getlength(x['d']+' ') for x in g)*FS/100
                X=int(min(max(X,_w/2+W*0.04),W-_w/2-W*0.04))
                ev.append(f"Dialogue: 2,{t2(a)},{t2(b)},Clean,,0,0,0,,{{\\an5\\pos({X},{Y})\\fs{FS}}}{txt.strip()}")
HF=PR["hero_font"] if S.get("cap_style")=="clean" else "Playfair Display"; HI=PR["hero_italic"] if S.get("cap_style")=="clean" else 1
hdr=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: White,Poppins ExtraBold,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,-1,0,1,0,3,5,0,0,0,1
Style: Clean,Poppins,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H50000000,0,0,0,0,100,100,0,0,1,0,3,5,0,0,0,1
Style: CleanSh,Poppins,66,&H38000000,&H38000000,&H38000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,5,0,0,0,1
Style: Red,{HF},170,{RED},{RED},&H00000000,&H50000000,1,{HI},0,0,100,100,0,0,1,0,4,5,0,0,0,1
Style: WGlow,Poppins ExtraBold,88,&H70000000,&H70000000,&H70000000,&H00000000,0,0,0,0,100,100,-1,0,1,8,0,5,0,0,0,1
Style: Glow,{HF},170,{GLOW},{GLOW},{GLOW},&H00000000,1,{HI},0,0,100,100,0,0,1,6,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ass=f'build/{oname}.ass'; open(ass,'w').write(hdr+'\n'.join(ev)+'\n')
# ---------- helpers to find emphasis moments
def emph_time(key):
    for p in phrases:
        em=[it for it in p['items'] if it['emph']]
        if em and re.sub(r'[^a-z0-9 ]','',' '.join(x['d'] for x in em).lower()).startswith(re.sub(r'[^a-z0-9 ]','',key.lower())):
            return em[0]['t'],p['end']
    sys.exit('emphasis not found: '+key)
EMPH=[]
for p in phrases:
    em=[it for it in p['items'] if it['emph']]
    if em: EMPH.append((em[0]['t'],' '.join(x['d'] for x in em)))
json.dump(dict(emph=EMPH,dur=dur,shots=[(s_['start'],s_['end'],s_['kind']) for s_ in SH]),open(f'build/{name}_cues.json','w'))
# ---------- B-roll prerender
BR=[]
for k,b in enumerate(S.get('broll',[])):
    if not os.path.exists(b['img']): print('  (missing B-roll image, skipped)',b['img']); continue
    a,_=emph_time(b['word']); a-=0.04-b.get('offset',0); L=b.get('len',1.4)
    clipf=f"build/{oname}_br{k}.mp4"
    src=b.get('vimg') if (VERT and b.get('vimg')) else b['img']
    sh_=b.get('shade')
    extra=['-loop','1','-i',f"broll/grad_{sh_}.png"] if sh_ else []
    shade_fc=(f"[s0];[1:v]scale={W}:{H}[g];[s0][g]overlay=0:0," if sh_ else ",")
    tail="noise=alls=5:allf=t,fade=t=in:st=0:d=0.10:color=white,setsar=1,format=yuv420p[o]"
    if src.endswith(('.mp4','.mov')):
        if VERT and b.get('vmode')=='fit':
            fy=int(H*b.get('vfit_y',0.18))
            fcb=(f"[0:v]trim=0:{L:.2f},setpts=PTS-STARTPTS,fps=25,split[a][b];"
                 f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:2,eq=brightness=-0.28[bg];"
                 f"[b]scale={W}:-2:flags=lanczos[fg];[bg][fg]overlay=0:{fy},"+tail)
            extra=[]
        else:
            fx,fy=b.get('vfocus' if VERT else 'focus',[0.5,0.5])
            fcb=(f"[0:v]trim=0:{L:.2f},setpts=PTS-STARTPTS,fps=25,scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                 f"crop={W}:{H}:(iw-ow)*{fx}:(ih-oh)*{fy},eq=contrast=1.05:saturation=1.05"+shade_fc+tail)
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(b.get('ss',0)),'-i',src]+extra+['-filter_complex',fcb,'-t',f'{L:.2f}','-map','[o]','-an','-c:v','libx264','-preset','veryfast','-crf','16',clipf],check=True)
        BR.append((a,L,clipf)); continue
    pan=b.get('vpan' if VERT else 'pan')
    if pan:
        x0,y0,x1,y1=pan; z=b.get('pzoom',1.0)
        fcb=(f"[0:v]scale=w={int(2*W*z)}:h={int(2*H*z)}:force_original_aspect_ratio=increase:flags=lanczos,fps=25,"
             f"crop={2*W}:{2*H}:'(iw-ow)*({x0}+({x1}-{x0})*t/{L})':'(ih-oh)*({y0}+({y1}-{y0})*t/{L})',scale={W}:{H}:flags=lanczos,"
             f"eq=contrast=1.05:saturation=1.05,vignette=PI/5"+shade_fc+tail)
        subprocess.run(['ffmpeg','-v','error','-y','-loop','1','-t',f'{L:.2f}','-i',src]+extra+['-filter_complex',fcb,'-t',f'{L:.2f}','-map','[o]','-c:v','libx264','-preset','veryfast','-crf','16',clipf],check=True)
        BR.append((a,L,clipf)); continue
    zf=f"zoompan=z='1.0+{b.get('zoom',0.10)}*on/({L}*25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=25"
    vfb=(f"scale=w={2*W}:h={2*H}:force_original_aspect_ratio=increase:flags=lanczos,crop={2*W}:{2*H},{zf},"
         f"eq=contrast=1.06:saturation=1.08,noise=alls=7:allf=t,vignette=PI/4.5,fade=t=in:st=0:d=0.10:color=white,setsar=1,format=yuv420p")
    subprocess.run(['ffmpeg','-v','error','-y','-loop','1','-i',src,'-t',f'{L:.2f}','-vf',vfb,'-c:v','libx264','-preset','veryfast','-crf','16',clipf],check=True)
    BR.append((a,L,clipf))
# ---------- punch-ins
PI=[]
for key in S.get('punch',[]):
    a,b_=emph_time(key)
    if any(x<=a<x+L for x,L,_ in BR): continue
    sh=shot_at(a)
    z=(1.12 if sh['kind']=='close' else 1.28) if not VERT else 1.12
    fx=0.5 if VERT else (sh['face'][0] if sh.get('face') else 0.5)
    if not VERT and sh['kind']=='wide': fx=S.get('wide_focus_x',0.5)
    PI.append((a,min(b_,a+1.6),z,fx))
# ---------- video graph
if VERT:
    SW,SHh=[int(x) for x in subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','csv=p=0',cut],capture_output=True,text=True).stdout.strip().split(',')]
    cw=int(SHh*9/16)//2*2
    parts=[(sh['end'],int(min(max(sh['cx']*SW-cw/2,0),SW-cw))) for sh in SH]
    e=str(parts[-1][1])
    for end,x in reversed(parts[:-1]): e=f"if(lt(t,{end:.2f}),{x},{e})"
    base=f"fps=25,crop={cw}:{SHh}:'{e}':0,scale={W}:{H}:flags=lanczos,unsharp=5:5:0.4,setsar=1"
else:
    base=f"fps=25,scale={W}:{H}:flags=lanczos,setsar=1"
if PI:
    zexp='1'; xexp='0'; yexp='0'
    for a,b_,z,fx in PI:
        cond=f"between(it,{a:.2f},{b_:.2f})"
        zexp=f"if({cond},{z},{zexp})"
        xexp=f"if({cond},(iw-iw/zoom)*{fx:.2f},{xexp})"
        yexp=f"if({cond},(ih-ih/zoom)*0.30,{yexp})"
    base+=f",zoompan=z='{zexp}':x='{xexp}':y='{yexp}':d=1:s={W}x{H}:fps=25"
for a,b_ in bw:
    en=f"between(t,{a:.2f},{b_:.2f})"
    base+=f",hue=s=0:enable='{en}',eq=contrast=1.15:brightness=-0.04:enable='{en}',vignette=angle=0.75:enable='{en}'"
fc=f"[0:v]{base}[v0]"; cur='v0'
for k,(a,L,f_) in enumerate(BR):
    fc+=f";[{k+1}:v]setpts=PTS-STARTPTS+{a:.3f}/TB[b{k}];[{cur}][b{k}]overlay=0:0:enable='between(t,{a:.3f},{a+L:.3f})':eof_action=pass[v{k+1}]"; cur=f'v{k+1}'
OV=S.get('overlays',[])
for m,o in enumerate(OV):
    idx=len(BR)+1+m; a0,a1=o['start'],o['end']
    fc+=f";[{idx}:v]format=rgba,fade=t=in:st={a0}:d=0.35:alpha=1,fade=t=out:st={a1-0.35}:d=0.35:alpha=1[ov{m}];[{cur}][ov{m}]overlay=0:0:enable='between(t,{a0},{a1})'[vo{m}]"; cur=f'vo{m}'
fc+=f";[{cur}]ass={ass}[vout]"
outp=f"out/{oname}.mp4" if not S.get("music") else f"build/{oname}_nomusic.mp4"
cmd=['ffmpeg','-v','error','-y','-i',cut]
for a,L,f_ in BR: cmd+=['-i',f_]
for o in S.get('overlays',[]): cmd+=['-loop','1','-t',f'{dur:.2f}','-i',o['v' if VERT else 'h']]
cmd+=['-filter_complex',fc,'-map','[vout]','-map','0:a','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-r','25','-c:a','aac','-b:a','192k','-movflags','+faststart','-t',f'{dur:.2f}',outp]
subprocess.run(cmd,check=True)
json.dump(dict(broll=[(a,L) for a,L,_ in BR],punch=[(a,b_) for a,b_,_,_ in PI],bw=bw),open(f'build/{oname}_fx.json','w'))
print('rendered',outp,'| broll:',len(BR),'| punch-ins:',len(PI),'| shots:',[(round(s_['start'],1),s_['kind'],s_['x']) for s_ in SH])
