"""Reference-driven carry, plant and loaded-takeoff pose solver. Coordinates: Blender Z up, -Y forward."""
import math
import numpy as np
from mathutils import Vector,Matrix,Quaternion
V=lambda p:Vector(p)
ARM_REST={
 'Right':(V((-.118,.020,.714)),V((-.230,.063,.785)),V((-.25462395,.06046958,.894))),
 'Left':(V((.120,-.035,.657)),V((.259,-.105,.640)),V((.24924102,-.11639388,.754)))
}
LEG_REST={
 'Right':(V((-.080,-.035,.422)),V((-.116,.042,.246)),V((-.157,.100,.055))),
 'Left':(V((.063,-.048,.422)),V((.067,-.078,.245)),V((.052,-.023,.054)))
}
# The four poses correspond to the supplied plant diagram. Positions are adapted
# to this frog's asymmetric arm lengths, not biomechanical measurements.
KEYS=[
 (1,(-.155,-.015,.548),(.47,-.855,.215),0.0),
 (25,(-.132,-.093,.752),(.46,-.878,-.13),.25),
 (49,(-.095,-.084,.926),(.48,-.82,-.30),.72),
 (73,(-.085,-.092,1.014),(.43,-.719,-.546),1.0),
 (89,(-.085,-.092,1.014),(.43,-.719,-.546),1.0)
]
GRIP_SPACING=.195;BACK_OFFSET=.105;POLE_LENGTH=1.95;FRAME_END=217;BEND_START=.34

def ease(t):return t*t*(3-2*t)
def pole_curve(s,bend):
 if s<=BEND_START or abs(bend)<1e-8:return V((0,0,s))
 k=bend/(POLE_LENGTH-BEND_START);t=s-BEND_START
 return V(((1-math.cos(k*t))/k,0,BEND_START+math.sin(k*t)/k))
def frame_motion(frame):
 if frame<=73:
  back,axis,lift=motion(frame);bend=0.;delta=V((0,0,0))
 else:
  plant_back,plant_axis,_=motion(73);anchor=plant_back+plant_axis*(POLE_LENGTH-BACK_OFFSET)
  p=ease(max(0,min(1,(frame-73)/48)));horizontal=V((plant_axis.x,plant_axis.y,0)).normalized();pitch=math.asin(plant_axis.z)+(math.radians(-36)-math.asin(plant_axis.z))*p
  # Hold the loaded pole while the athlete swings about the shoulder line.
  axis=horizontal*math.cos(pitch)+V((0,0,math.sin(pitch)));bend=.95*p;down=(V((0,0,-1))-axis*axis.dot(V((0,0,-1)))).normalized();basis=Matrix((down,axis.cross(down),axis)).transposed()
  back=anchor-basis@pole_curve(POLE_LENGTH,bend)+axis*BACK_OFFSET;delta=back-plant_back;lift=1.
 down=(V((0,0,-1))-axis*axis.dot(V((0,0,-1)))).normalized();basis=Matrix((down,axis.cross(down),axis)).transposed()
 return back,axis,lift,bend,delta,basis
def motion(frame):
 for j in range(len(KEYS)-1):
  if frame<=KEYS[j+1][0]:break
 f0,p0,a0,u0=KEYS[j];f1,p1,a1,u1=KEYS[j+1];t=ease(max(0,min(1,(frame-f0)/(f1-f0))))
 back=V(p0).lerp(V(p1),t);axis=V(a0).lerp(V(a1),t).normalized();lift=u0+(u1-u0)*t
 return back,axis,lift

def candidates(side,grip,axis,shoulder,lift):
 rs,re,rw=ARM_REST[side];l1=(re-rs).length;l2=(rw-re).length;x=-axis
 z0=(V((0,0,1))-x*x.z).normalized();y0=z0.cross(x).normalized();phis=np.linspace(-math.pi,math.pi,120,endpoint=False)
 preferred=V((-1 if side=='Right' else 1,.45,-.8+lift*.6)).normalized();out=[]
 for roll in np.linspace(-math.pi,math.pi,120,endpoint=False):
  z=z0*math.cos(roll)+y0*math.sin(roll);y=z.cross(x).normalized();R=Matrix((x,y,z)).transposed();q=R.to_quaternion();w=grip-R@V((0,-.014,.028));dv=w-shoulder;d=dv.length
  if d>=l1+l2-.0005 or d<=abs(l1-l2)+.0005:continue
  n=dv/d;a=(l1*l1-l2*l2+d*d)/(2*d);h=math.sqrt(max(0,l1*l1-a*a));base=preferred-n*preferred.dot(n)
  if base.length<.01:continue
  base.normalize();b=n.cross(base).normalized();es=np.array(shoulder+n*a)[None,:]+h*(np.cos(phis)[:,None]*np.array(base)+np.sin(phis)[:,None]*np.array(b));ls=(np.array(w)-es)/l2;us=(es-np.array(shoulder))/l1
  wrist=np.arccos(np.clip(ls@np.array(z),-1,1));bends=np.arccos(np.clip(np.sum(us*ls,axis=1),-1,1));cost=35*wrist*wrist+(1-np.cos(phis))*.15
  valid=(wrist<math.radians(30))&(bends>math.radians(3))&(bends<math.radians(148));cost[~valid]=1e9
  # Keep both elbow branches and a little width around each candidate minimum.
  chosen=[]
  for k in np.argsort(cost):
   if cost[k]>1e8:break
   if any(min(abs(k-j),len(phis)-abs(k-j))<8 for j in chosen):continue
   chosen.append(int(k));out.append({'cost':float(cost[k]),'hand_q':q,'wrist':w,'elbow':V(es[k]),'shoulder':shoulder,'roll':roll,'phi':float(phis[k]),'wrist_angle_deg':math.degrees(float(wrist[k])),'elbow_bend_deg':math.degrees(float(bends[k]))})
   if len(chosen)==3:break
 if not out:raise RuntimeError(f'No bounded-wrist solution for {side}, grip {list(grip)}')
 return out

def add_rotations(a,side):
 rs,re,rw=ARM_REST[side];s,e,w=a['shoulder'],a['elbow'],a['wrist'];u=(e-s).normalized();l=(w-e).normalized();ru=(re-rs).normalized();rl=(rw-re).normalized();hn=u.cross(l).normalized();rh=ru.cross(rl).normalized()
 def basis(h,d):return Matrix((h,d,h.cross(d))).transposed()
 a['upper_q']=(basis(hn,u)@basis(rh,ru).transposed()).to_quaternion();a['forearm_q']=(basis(hn,l)@basis(rh,rl).transposed()).to_quaternion();hq=a['hand_q'];a['twist_q']=(hq@rl).rotation_difference(l)@hq
 return a

def all_frames():
 frames=[]
 for frame in range(1,FRAME_END+1):
  back,axis,lift,bend,delta,basis=frame_motion(frame)
  swing=ease(max(0,min(1,(frame-121)/72)));body_angle=-math.radians(172)*swing
  shoulder_axis=(ARM_REST['Left'][0]-ARM_REST['Right'][0]).normalized();body_q=Quaternion(shoulder_axis,body_angle)
  pivot=(ARM_REST['Left'][0]+ARM_REST['Right'][0])*.5+V((0,-.014*lift,.023*lift));base=V((0,-.025*lift,.012*lift))+delta+V((-.17,-.02,.12))*math.sin(math.pi*swing)
  torso=Matrix.Translation(base+pivot)@body_q.to_matrix().to_4x4()@Matrix.Translation(-pivot)
  frames.append({'frame':frame,'back':back,'axis':axis,'lift':lift,'bend':bend,'root_delta':delta,'pole_basis':basis,'torso':torso,'body_q':body_q,'body_angle_deg':abs(math.degrees(body_angle)),'arms':{}})
 for side in ARM_REST:
  options=[];pointers=[];costs=None;previous=None
  for f in frames:
   shoulder=f['torso']@ARM_REST[side][0]+f['body_q']@V((0,-.014*f['lift'],.023*f['lift']));grip=f['back'] if side=='Right' else f['back']+f['axis']*GRIP_SPACING
   try:cs=candidates(side,grip,f['axis'],shoulder,f['lift'])
   except RuntimeError as error:raise RuntimeError(f"Frame {f['frame']}: {error}") from error
   q=np.array([list(c['hand_q']) for c in cs]);e=np.array([list(c['elbow']) for c in cs]);local=np.array([c['cost'] for c in cs])
   if previous is None:costs=local;pointers.append(None)
   else:
    pq,pe=previous;angles=2*np.arccos(np.clip(np.abs(q@pq.T),0,1));distance=np.sum((e[:,None,:]-pe[None,:,:])**2,axis=2)
    total=costs[None,:]+angles**2*2+distance*12000;best=np.argmin(total,axis=1);costs=local+total[np.arange(len(cs)),best];pointers.append(best)
   options.append(cs);previous=(q,e)
  index=int(np.argmin(costs))
  for i in reversed(range(len(frames))):
   frames[i]['arms'][side]=add_rotations(options[i][index],side)
   if i:index=int(pointers[i][index])
 # Remove the small angular stair steps of the candidate grid, then project
 # elbows back to their two-bone circles so limb lengths stay exact.
 for side in ARM_REST:
  rolls=np.unwrap([f['arms'][side]['roll'] for f in frames]);es=np.array([list(f['arms'][side]['elbow']) for f in frames])
  for _ in range(3):
   rolls[1:-1]=.25*rolls[:-2]+.5*rolls[1:-1]+.25*rolls[2:];es[1:-1]=.25*es[:-2]+.5*es[1:-1]+.25*es[2:]
  rs,re,rw=ARM_REST[side];l1=(re-rs).length;l2=(rw-re).length
  for i,f in enumerate(frames):
   a=f['arms'][side];x=-f['axis'];z0=(V((0,0,1))-x*x.z).normalized();y0=z0.cross(x).normalized();z=z0*math.cos(rolls[i])+y0*math.sin(rolls[i]);y=z.cross(x).normalized();R=Matrix((x,y,z)).transposed();g=f['back'] if side=='Right' else f['back']+f['axis']*GRIP_SPACING;w=g-R@V((0,-.014,.028));s=a['shoulder'];n=(w-s).normalized();d=(w-s).length;along=(l1*l1-l2*l2+d*d)/(2*d);h=math.sqrt(max(0,l1*l1-along*along));center=s+n*along;v=V(es[i])-center;v=(v-n*v.dot(n)).normalized();e=center+v*h
   a.update(hand_q=R.to_quaternion(),wrist=w,elbow=e,roll=float(rolls[i]),wrist_angle_deg=math.degrees((w-e).angle(z)),elbow_bend_deg=math.degrees((e-s).angle(w-e)));add_rotations(a,side)
 return frames
if __name__=='__main__':
 import json
 frames=all_frames();print(json.dumps([{'frame':f['frame'],'wrists':{s:round(a['wrist_angle_deg'],2) for s,a in f['arms'].items()},'elbows':{s:round(a['elbow_bend_deg'],1) for s,a in f['arms'].items()}} for f in frames],indent=2))
