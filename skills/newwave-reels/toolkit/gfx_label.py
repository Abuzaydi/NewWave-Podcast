"""Lower-third label PNG: italic name + outlined pill. usage: gfx_label.py W H name pill out.png"""
import sys,os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W,H,name,pill,out=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5]
s=(W/1920) if W>H else (W/1080)*1.15
fn=ImageFont.truetype(os.path.expanduser('~/.fonts/PlayfairDisplay-Italic[wght].ttf'),int(62*s))
fp=ImageFont.truetype(os.path.expanduser('~/.fonts/Poppins-Bold.ttf'),int(28*s))
im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
cx=W/2; y0=H*(0.80 if W>H else 0.79)
nw=d.textlength(name,font=fn); pw=d.textlength(pill,font=fp)+44*s; ph=50*s
sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
sd.text((cx-nw/2,y0),name,font=fn,fill=(0,0,0,200),anchor='lm')
sd.rounded_rectangle([cx-pw/2,y0+50*s,cx+pw/2,y0+50*s+ph],radius=ph/2,fill=(0,0,0,150))
sh=sh.filter(ImageFilter.GaussianBlur(12*s)); im=Image.alpha_composite(im,sh); d=ImageDraw.Draw(im)
d.text((cx-nw/2,y0),name,font=fn,fill=(255,255,255,255),anchor='lm')
d.rounded_rectangle([cx-pw/2,y0+50*s,cx+pw/2,y0+50*s+ph],radius=ph/2,outline=(255,255,255,235),width=max(2,int(2.5*s)),fill=(0,0,0,70))
d.text((cx,y0+50*s+ph/2),pill,font=fp,fill=(255,255,255,255),anchor='mm')
im.save(out); print('ok',out)
