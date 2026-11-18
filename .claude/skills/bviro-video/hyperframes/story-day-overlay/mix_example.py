import subprocess,os,sys
X=os.path.expanduser("~/.claude/skills/media-use/audio/assets/sfx"); D=32.5
ev=[("impact-bass-1",0.0,-10,None),("sparkle",0.15,-17,None),
("whoosh",2.68,-11,None),("glitch-2",2.8,-20,(0,1.7)),
("whoosh-short",4.8,-13,None),("pop",4.95,-14,None),("whoosh",6.6,-13,None),("pop",6.7,-14,None),("whoosh-short",8.5,-14,None),
("whoosh-short",9.48,-14,None),("pop",9.56,-14,None),("whoosh-short",11.42,-14,None),("click",12.34,-10,None),("click",12.92,-10,None),
("whoosh-short",14.02,-14,None),("pop",14.15,-16,None),("pop",14.35,-16,None),("pop",14.55,-16,None),("pop",14.75,-16,None),
("whoosh-short",15.62,-14,None),("pop",16.4,-13,None),("typing",16.7,-15,(0,0.85)),
("whoosh",17.62,-12,None),("riser",17.9,-15,(8.9,1.1)),("click",18.78,-5,None),
("impact-bass-2",19.0,-7,None),("sparkle",19.1,-15,None),("ping",19.55,-16,None),("ping",19.8,-16,None),("ping",20.05,-16,None),
("pop",20.78,-14,None),("pop",22.24,-13,None),("whoosh",23.35,-12,None),
("whoosh",24.22,-10,None),("impact-bass-1",25.3,-15,None),("chime",27.45,-13,None),("pop",27.5,-15,None),("pop",27.68,-15,None)]
inp=["-i",sys.argv[1],"-i","music_raw.mp3"]; fc=[]; labs=[]
for i,(n,t,g,cut) in enumerate(ev):
    inp+=(["-ss",str(cut[0]),"-t",str(cut[1])] if cut else [])+["-i",f"{X}/{n}.mp3"]
    d=int(t*1000); f=",afade=t=in:d=0.3,afade=t=out:st=%.2f:d=0.25"%(cut[1]-0.25) if cut else ""
    fc.append(f"[{i+2}:a]aresample=48000,aformat=channel_layouts=stereo{f},volume={g}dB,adelay={d}|{d}[s{i}]"); labs.append(f"[s{i}]")
fc.append(f"[0:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=75,equalizer=f=3000:t=q:w=1.2:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=3,loudnorm=I=-16:TP=-2:LRA=7,apad=whole_dur={D},asplit=2[vo][sc]")
fc.append(f"[1:a]aresample=48000,aformat=channel_layouts=stereo,dynaudnorm=f=400:g=25:m=6,loudnorm=I=-18:TP=-2,adelay=800|800,atrim=0:{D},afade=t=out:st={D-2.2}:d=2.2[m0];[m0][sc]sidechaincompress=threshold=0.03:ratio=7:attack=20:release=450[mu]")
fc.append("[vo][mu]"+"".join(labs)+f"amix=inputs={len(labs)+2}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{D}[a]")
subprocess.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[a]","-ar","48000","mix.wav"],check=True)
