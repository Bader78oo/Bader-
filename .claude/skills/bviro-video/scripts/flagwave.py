import cv2, numpy as np, subprocess, sys
src=cv2.imread("flag_aerial.jpg"); H,W=src.shape[:2]
out,dur,z0,z1,cx,cy=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),float(sys.argv[6])
x0,y0,x1,y1=440,246,650,486; pole=436.0   # flag box in the 1080x1920 crop
m=np.zeros((H,W),np.float32); m[y0:y1,x0:x1]=1; m=cv2.GaussianBlur(m,(0,0),10)
xx,yy=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(H,dtype=np.float32))
wgt=np.clip((xx-pole)/210.0,0,1)*m
N=int(dur*30)
p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s","1080x1920","-r","30","-i","-","-c:v","libx264","-crf","14","-preset","fast","-pix_fmt","yuv420p",out],stdin=subprocess.PIPE)
for i in range(N):
    t=i/30.0
    ph=2*np.pi*(xx-pole)/130.0-2*np.pi*0.9*t+(yy-y0)/90.0
    dy=6.0*wgt*np.sin(ph); dx=3.0*wgt*np.sin(ph+1.1)
    fr=cv2.remap(src,xx-dx,yy-dy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    k=i/max(1,N-1); k=k*k*(3-2*k); z=z0+(z1-z0)*k
    w,h=W/z,H/z; ax=min(max(cx-w/2,0),W-w); ay=min(max(cy-h/2,0),H-h)
    M=np.float32([[z,0,-ax*z],[0,z,-ay*z]])
    fr=cv2.warpAffine(fr,M,(1080,1920),flags=cv2.INTER_LANCZOS4)
    p.stdin.write(fr.tobytes())
p.stdin.close(); p.wait()
