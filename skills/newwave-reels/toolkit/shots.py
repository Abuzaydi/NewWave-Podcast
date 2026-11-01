"""Detect shots in a clip and decide where captions go (empty side away from the speaker's face)."""
import cv2,sys,json,subprocess,re
def shots(path,thr=0.35):
    log=subprocess.run(['ffmpeg','-i',path,'-vf',f"select='gt(scene,{thr})',showinfo",'-f','null','-'],capture_output=True,text=True).stderr
    cuts=[float(x) for x in re.findall(r'pts_time:([\d.]+)',log)]
    dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',path],capture_output=True,text=True).stdout)
    b=[0.0]+[c for c in cuts if c>0.3]+[dur]; return [(b[i],b[i+1]) for i in range(len(b)-1) if b[i+1]-b[i]>0.2]
fc=cv2.CascadeClassifier('cascades/haarcascade_frontalface_default.xml')
pc=cv2.CascadeClassifier('cascades/haarcascade_profileface.xml')
def layout(path):
    cap=cv2.VideoCapture(path); res=[]
    for a,b in shots(path):
        faces=[]
        for f in (0.3,0.5,0.7):
            cap.set(cv2.CAP_PROP_POS_MSEC,(a+(b-a)*f)*1000); ok,img=cap.read()
            if not ok: continue
            H,W=img.shape[:2]; g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            for det in (fc.detectMultiScale(g,1.1,6,minSize=(W//40,W//40)),pc.detectMultiScale(g,1.1,6,minSize=(W//40,W//40))):
                for (x,y,w,h) in det: faces.append(((x+w/2)/W,(y+h/2)/H,w/W))
        big=max(faces,key=lambda t:t[2]) if faces else None
        if big and big[2]>0.09:   # close-up
            fx,fy,fw=big
            side='right' if fx<0.56 else 'left'
            x=0.73 if side=='right' else 0.27
            if 0.42<fx<0.58: x=0.76 if side=='right' else 0.24
            y=min(max(fy+0.05,0.38),0.55)
            res.append(dict(start=a,end=b,kind='close',face=[round(fx,2),round(fy,2),round(fw,2)],x=x,y=y))
        else:
            res.append(dict(start=a,end=b,kind='wide',face=big and [round(v,2) for v in big],x=0.5,y=0.40))
    return res
if __name__=='__main__': print(json.dumps(layout(sys.argv[1]),indent=1))
