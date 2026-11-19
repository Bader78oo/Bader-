import subprocess,os,sys
X=os.path.expanduser("~/.claude/skills/media-use/audio/assets/sfx"); D=44.0
ev=[("impact-bass-1",0.0,-10,None),("sparkle",0.15,-17,None),("whoosh",1.75,-11,None),("glitch-1",2.5,-18,(0,0.8)),("impact-bass-2",2.72,-9,None),
("whoosh",3.35,-11,None),("glitch-2",3.45,-20,(0,1.4)),("whoosh-short",4.95,-13,None),("pop",5.1,-14,None),
("typing",7.4,-16,(0,1.0)),("ping",8.38,-14,None),("whoosh-short",8.88,-14,None),("pop",8.96,-14,None),("impact-bass-1",10.1,-12,None),
("whoosh-short",11.85,-14,None),("pop",12.52,-14,None),("pop",13.64,-14,None),("click",14.04,-10,None),
("whoosh",15.58,-13,None),("pop",15.72,-14,None),("whoosh-short",17.26,-14,None),("click",17.34,-10,None),("error",18.28,-12,None),("impact-bass-2",18.84,-10,None),
("whoosh",19.93,-11,None),("pop",20.02,-13,None),("pop",21.34,-16,None),("pop",21.58,-16,None),("pop",21.82,-16,None),("pop",22.06,-16,None),("pop",22.3,-16,None),
("ping",22.8,-17,None),("ping",23.02,-17,None),("ping",23.24,-17,None),("ping",23.46,-17,None),("ping",23.68,-17,None),
("whoosh-short",24.2,-14,None),("sparkle",25.72,-14,None),("riser",27.25,-13,(9.0,1.0)),("impact-bass-2",28.25,-5,None),("glitch-3",28.3,-14,(0,0.8)),("error",30.14,-13,None),
("whoosh",31.75,-12,None),("pop",31.9,-14,None),("whoosh-short",34.9,-14,None),("pop",35.05,-14,None),
("whoosh",37.55,-10,None),("pop",38.6,-14,None),("pop",38.78,-14,None),("pop",38.96,-14,None),("pop",39.14,-14,None),("click",39.26,-6,None),("notification",39.45,-13,None),("pop",40.52,-12,None),("chime",41.4,-14,None)]
inp=["-i",sys.argv[1],"-i","music_raw.mp3"]; fc=[]; labs=[]
for i,(n,t,g,cut) in enumerate(ev):
    inp+=(["-ss",str(cut[0]),"-t",str(cut[1])] if cut else [])+["-i",f"{X}/{n}.mp3"]
    d=int(t*1000); f=",afade=t=in:d=0.2,afade=t=out:st=%.2f:d=0.2"%(cut[1]-0.2) if cut else ""
    fc.append(f"[{i+2}:a]aresample=48000,aformat=channel_layouts=stereo{f},volume={g}dB,adelay={d}|{d}[s{i}]"); labs.append(f"[s{i}]")
fc.append(f"[0:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=75,equalizer=f=3000:t=q:w=1.2:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=3,loudnorm=I=-16:TP=-2:LRA=7,apad=whole_dur={D},asplit=2[vo][sc]")
# music: silence for the "suddenly" beat, quieter tension afterwards, back up for the question
vol="volume='if(between(t,27.15,28.25),0.08,if(between(t,28.25,37.6),0.6,1))':eval=frame"
fc.append(f"[1:a]aresample=48000,aformat=channel_layouts=stereo,dynaudnorm=f=400:g=25:m=6,loudnorm=I=-18:TP=-2,atrim=0:{D},{vol},afade=t=out:st={D-2.5}:d=2.5[m0];[m0][sc]sidechaincompress=threshold=0.03:ratio=7:attack=20:release=450[mu]")
fc.append("[vo][mu]"+"".join(labs)+f"amix=inputs={len(labs)+2}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{D}[a]")
subprocess.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[a]","-ar","48000","mix.wav"],check=True)
