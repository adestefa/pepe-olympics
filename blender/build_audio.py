"""Generate short game effects only. Crowd MP3s are separate generated assets; see audio/README.md."""
import math,random,wave,struct,os
random.seed(69)
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=os.path.join(ROOT,'public','assets','audio');os.makedirs(OUT,exist_ok=True);SR=22050

def save(name,seconds,fn):
    with wave.open(os.path.join(OUT,name+'.wav'),'w') as w:
        w.setparams((1,2,SR,0,'NONE','not compressed'))
        w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,fn(i/SR,i)))*28000)) for i in range(int(seconds*SR))))
save('countdown',.2,lambda t,i:math.sin(t*math.tau*550)*math.exp(-t*19)*.4)
save('go',.5,lambda t,i:math.sin(t*math.tau*960)*math.exp(-t*8)*.5)
save('landing',.5,lambda t,i:(math.sin(math.tau*(90*t-65*t*t))*.6+random.uniform(-.15,.15))*math.exp(-t*13))
save('pole-spring',.65,lambda t,i:math.sin(math.tau*(170*t+650*t*t))*math.exp(-t*6)*.3)
save('cartoon-crack',.22,lambda t,i:random.uniform(-1,1)*math.exp(-t*30)*.55)
print('Original sound effects written to',OUT)
