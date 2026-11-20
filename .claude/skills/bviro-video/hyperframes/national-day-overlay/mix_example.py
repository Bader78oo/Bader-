import subprocess,os,sys
X=os.path.expanduser("~/.claude/skills/media-use/audio/assets/sfx"); D=40.0
ev=[("impact-bass-1",0.0,-12,None),("whoosh",2.12,-15,None),("whoosh-short",5.1,-17,None),("whoosh-short",7.7,-18,None),("whoosh-short",9.6,-18,None),("whoosh-short",11.75,-18,None),
("whoosh-short",13.25,-18,None),("whoosh-short",14.85,-18,None),("whoosh",17.0,-16,None),("impact-bass-2",19.55,-12,None),("whoosh-short",27.25,-18,None),("whoosh-short",28.75,-18,None),
("riser",30.2,-15,(8.9,1.1)),("impact-bass-1",31.3,-8,None),("sparkle",31.45,-15,None),("chime",35.9,-15,None)]
inp=["-i",sys.argv[1],"-ss","2.6","-i","music_raw.mp3"]; fc=[]; labs=[]
for i,(n,t,g,cut) in enumerate(ev):
    inp+=(["-ss",str(cut[0]),"-t",str(cut[1])] if cut else [])+["-i",f"{X}/{n}.mp3"]
    d=int(t*1000); f=",afade=t=in:d=0.5,afade=t=out:st=%.2f:d=0.2"%(cut[1]-0.2) if cut else ""
    fc.append(f"[{i+2}:a]aresample=48000,aformat=channel_layouts=stereo{f},volume={g}dB,adelay={d}|{d}[s{i}]"); labs.append(f"[s{i}]")
fc.append(f"[0:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=75,equalizer=f=3000:t=q:w=1.2:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=3,loudnorm=I=-16:TP=-2:LRA=7,apad=whole_dur={D},asplit=2[vo][sc]")
fc.append(f"[1:a]aresample=48000,aformat=channel_layouts=stereo,dynaudnorm=f=500:g=31:m=5,loudnorm=I=-17:TP=-2,atrim=0:{D},afade=t=in:d=0.3,afade=t=out:st={D-1.2}:d=1.2[m0];[m0][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=500[mu]")
fc.append("[vo][mu]"+"".join(labs)+f"amix=inputs={len(labs)+2}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{D}[a]")
subprocess.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[a]","-ar","48000","mix.wav"],check=True)
