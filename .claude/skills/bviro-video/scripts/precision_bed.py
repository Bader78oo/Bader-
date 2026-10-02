import sys, wave, subprocess, numpy as np
SR=48000; DUR=30.0; N=int(DUR*SR)
LIB="/root/.claude/skills/media-use/audio/assets/sfx/"
def rd(f, ch=1):
    raw=subprocess.run(["ffmpeg","-v","error","-i",f,"-f","f32le","-ac",str(ch),"-ar",str(SR),"-"],capture_output=True).stdout
    return np.frombuffer(raw,np.float32).copy()
def put(buf, sig, t, g=1.0):
    i=int(t*SR); s=sig[:max(0,len(buf)-i)]*g; buf[i:i+len(s)]+=s
def rms_db(x): return 20*np.log10(np.sqrt(np.mean(x**2))+1e-12)
hook=sys.argv[1]; out=sys.argv[2]
vo=np.zeros(N)
for f,t in ((hook,0.15),("t3.wav",8.8),("t4.wav",12.0),("t5.wav",20.35),("t_ibri.wav",24.45),("t_oct.wav",27.2)):
    x=rd(f); x*=10**((-18-rms_db(x[np.abs(x)>0.01]))/20); put(vo,x,t)
mu=rd("music.wav")[:N]; mu=np.pad(mu,(0,N-len(mu))); mu*=10**((-27-rms_db(mu[:int(18*SR)]))/20)
# ticking clock, accelerating, stops at 19.2
tick=np.zeros(N); t=0.05; gap=0.5; k=0
rng=np.random.default_rng(1)
while t<19.2:
    n=int(0.05*SR); x=np.arange(n)/SR
    f=2900 if k%2==0 else 2300
    s=(np.sin(2*np.pi*f*x)*0.6+rng.standard_normal(n)*0.4)*np.exp(-x/0.006)
    put(tick,s,t,0.22); t+=gap; k+=1; gap=max(0.18,gap*0.975)
sfx=np.zeros(N)
for name,t,g in (("impact-bass-1.mp3",0.0,0.9),("whoosh-cinematic.mp3",2.85,0.5),("whoosh-cinematic.mp3",11.85,0.5),("impact-bass-2.mp3",20.0,1.0),("whoosh.mp3",26.9,0.4)):
    put(sfx,rd(LIB+name),t,g)
r=rd(LIB+"riser.mp3"); r=r[-int(2.0*SR):] if len(r)>2*SR else r; put(sfx,r,19.2-len(r)/SR,0.6)
tt=np.arange(N)/SR
# duck music+ticks under voice, hard silence 19.2-20.0
lvl=np.abs(vo); w=int(0.25*SR); act=np.convolve((lvl>0.01).astype(float),np.ones(w)/w,"same")>0.02
g=np.where(act,10**(-10/20),1.0); g=np.convolve(g,np.ones(int(0.2*SR))/int(0.2*SR),"same")
gap_=(tt>=19.2)&(tt<20.0)
bed=(mu+tick)*g; bed[gap_]=0; sfx[(tt>=19.25)&(tt<19.98)]=0
mix=vo+bed+sfx*0.8
mix/=max(1.0,np.abs(mix).max()/0.89)
st=np.stack([mix,mix],1)
with wave.open(out,"wb") as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((np.clip(st,-1,1)*32767).astype(np.int16).tobytes())
print("bed ->",out)
