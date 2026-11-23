#!/usr/bin/env python3
"""prep.py name src ss dur speed mode [args] -> clips/name.mp4 (1080x1920, 30 fps)
mode fixed:<x>            fixed 9:16 crop at x
mode track:t:cx,t:cx,...  9:16 crop whose centre follows keyframes (times in source seconds)"""
import subprocess, sys
name, src, ss, dur, speed, mode = sys.argv[1:7]
col = (sys.argv[7] + ",") if len(sys.argv) > 7 else ""
ss, dur, speed = float(ss), float(dur), float(speed)
p = subprocess.run(["ffprobe","-v","error","-select_streams","v","-show_entries","stream=width,height","-of","csv=p=0",src],capture_output=True,text=True).stdout.strip().split(",")
W, H = int(p[0]), int(p[1]); cw = int(H*9/16)//2*2
if mode.startswith("fixed:"):
    x = str(int(mode[6:]))
else:
    k = [(float(a.split(":")[0])-ss, float(a.split(":")[1])-cw/2) for a in mode[6:].split(",")]
    x = str(k[-1][1])
    for (t0,x0),(t1,x1) in reversed(list(zip(k[:-1],k[1:]))):
        x = f"if(lt(t,{t1:.3f}),{x0:.1f}+({x1-x0:.1f})*(t-{t0:.3f})/{t1-t0:.3f},{x})"
    x = f"max(0,min({W-cw},{x}))"
vf = f"crop={cw}:{H}:x='{x}':y=0,setpts=PTS/{speed},{col}scale=1080:1920:flags=lanczos,unsharp=5:5:0.5,fps=30"
subprocess.run(["ffmpeg","-v","error","-y","-ss",str(ss),"-t",str(dur),"-i",src,"-an","-vf",vf,"-c:v","libx264","-crf","15","-preset","veryfast","-pix_fmt","yuv420p",f"clips/{name}.mp4"],check=True)
d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"clips/{name}.mp4"],capture_output=True,text=True).stdout.strip()
print(name, d)
