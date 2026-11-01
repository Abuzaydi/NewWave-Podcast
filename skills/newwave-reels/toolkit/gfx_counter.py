"""Animated portfolio counter: $500,000 -> $0 with a red line falling. usage: gfx_counter.py W H out.mp4"""
import sys,os,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W,H=int(sys.argv[1]),int(sys.argv[2]); out=sys.argv[3]; FPS=25; N=int(2.3*FPS)
SER=os.path.expanduser('~/.fonts/PlayfairDisplay-Italic[wght].ttf'); SANS=os.path.expanduser('~/.fonts/Poppins-Bold.ttf')
vert=H>W; s=W/1920 if not vert else W/1080
fbig=ImageFont.truetype(SER,int((230 if not vert else 190)*s));
try: fbig.set_variation_by_name('Regular')
except Exception: pass
fsm=ImageFont.truetype(SANS,int((40 if not vert else 42)*s))
# background
yy,xx=np.mgrid[0:H,0:W]; cx,cy=W/2,H*0.45
r=np.sqrt(((xx-cx)/W)**2+((yy-cy)/H)**2)
bg=np.clip(1-r*1.6,0,1)
base=np.stack([14+28*bg,10+12*bg,10+10*bg],-1).astype(np.uint8)
rng=np.random.default_rng(3)
os.makedirs('build/cnt',exist_ok=True)
def ease(x): return x*x*(3-2*x)
# chart path (jagged down)
pts=[(0.0,0.10),(0.08,0.06),(0.16,0.14),(0.24,0.09),(0.33,0.30),(0.41,0.24),(0.50,0.48),(0.58,0.42),(0.67,0.66),(0.75,0.60),(0.84,0.84),(0.92,0.80),(1.0,0.97)]
cx0,cx1=W*0.14,W*0.86; cy0,cy1=(H*0.60,H*0.86) if not vert else (H*0.58,H*0.74)
P=[(cx0+(cx1-cx0)*x,cy0+(cy1-cy0)*y) for x,y in pts]
for f in range(N):
    t=f/FPS; p=min(max((t-0.25)/0.95,0),1); e=ease(p)
    val=int(round(500000*(1-e)/1000))*1000 if e<1 else 0
    txt=f"${val:,}"
    im=Image.fromarray(base.copy()); d=ImageDraw.Draw(im)
    # grid lines
    for k in range(5):
        y=cy0+(cy1-cy0)*k/4; d.line([(cx0,y),(cx1,y)],fill=(40,32,32),width=max(1,int(2*s)))
    # chart draw-on
    seg=e*(len(P)-1); n=int(seg)
    path=P[:n+1]
    if n<len(P)-1:
        fr=seg-n; a,b=P[n],P[n+1]; path=path+[(a[0]+(b[0]-a[0])*fr,a[1]+(b[1]-a[1])*fr)]
    if len(path)>1:
        glow=Image.new('RGBA',im.size,(0,0,0,0)); gd=ImageDraw.Draw(glow)
        gd.line(path,fill=(226,23,27,200),width=int(14*s)); glow=glow.filter(ImageFilter.GaussianBlur(10*s))
        im.paste(glow,(0,0),glow); d=ImageDraw.Draw(im)
        d.line(path,fill=(235,40,40),width=int(6*s),joint='curve')
        x,y=path[-1]; d.ellipse([x-9*s,y-9*s,x+9*s,y+9*s],fill=(255,80,80))
    # number color white->red
    c=(int(255),int(255-215*e),int(255-215*e))
    tw=d.textlength(txt,font=fbig); ty=(H*0.30 if not vert else H*0.36)
    sh=Image.new('RGBA',im.size,(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.text((W/2-tw/2,ty),txt,font=fbig,fill=(0,0,0,170),anchor='lm'); sh=sh.filter(ImageFilter.GaussianBlur(14*s)); im.paste(sh,(0,0),sh); d=ImageDraw.Draw(im)
    jit=(rng.uniform(-3,3)*s if 0.2<p<0.98 else 0)
    d.text((W/2-tw/2+jit,ty),txt,font=fbig,fill=c,anchor='lm')
    lab="MAURITS' PORTFOLIO · 2021"; lw=d.textlength(lab,font=fsm)
    d.text((W/2-lw/2,ty-(170 if not vert else 150)*s),lab,font=fsm,fill=(190,180,175),anchor='lm')
    # grain
    a=np.asarray(im).astype(np.int16); a+=rng.integers(-7,8,a.shape[:2])[...,None]; im=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
    im.save(f'build/cnt/{f:03d}.png')
subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(FPS),'-i','build/cnt/%03d.png','-vf','fade=t=in:st=0:d=0.10:color=white,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','15',out],check=True)
print('ok',out)
