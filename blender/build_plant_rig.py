"""Preserved-copy, keyed full-body rig to review the user-provided plant sequence.
Run Blender --background --python-exit-code 1 --python blender/build_plant_rig.py
"""
import bpy,bmesh,math,json,hashlib,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from plant_motion import ARM_REST,LEG_REST,all_frames,POLE_LENGTH,BACK_OFFSET,GRIP_SPACING,FRAME_END,BEND_START,pole_curve
from pole_flex import build_flex_rig,key_bend,make_box
from study_joint_limits import calibrate_limits
OUT=ROOT/'output/plant-rig';OUT.mkdir(parents=True,exist_ok=True)
inputs=[ROOT/'blender/pepe-tripo-grip.blend',ROOT/'blender/pepe-pole-carry.blend',ROOT/'public/assets/pepe-tripo-grip.glb']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
frames=all_frames();print('SOLVER_READY',max(a['wrist_angle_deg'] for f in frames for a in f['arms'].values()),flush=True)
bpy.ops.wm.open_mainfile(filepath=str(inputs[0]));scene=bpy.context.scene
body=bpy.data.objects['Pepe_Retopo_Pole_Grip_Copy'];body.name='Pepe_Plant_Skinned';body.data=body.data.copy();body.vertex_groups.clear()
for o in list(scene.objects):
 if o.name.startswith(('Gauge_','GripSocket_')):bpy.data.objects.remove(o,do_unlink=True)
# Append the real game pole, keeping prior Blender scenes untouched.
with bpy.data.libraries.load(str(inputs[1]),link=False) as (src,dst):dst.collections=['Vault_Pole']
scene.collection.children.link(dst.collections[0]);pole=bpy.data.objects.get('VaultPole');pole.animation_data_clear();pole.rotation_mode='QUATERNION'
V=lambda p:Vector(p)
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def smooth(a,b,t):
 t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
def affine(q,a,b):return Matrix.Translation(b)@q.to_matrix().to_4x4()@Matrix.Translation(-a)
def seg(p,a,b):
 t=max(0,min(1,(p-a).dot(b-a)/(b-a).length_squared));return (p-(a+(b-a)*t)).length,t
pole_rig,pole_mesh,pole_stations,pole_binds=build_flex_rig(pole,scene)
anchor=frames[72]['back']+frames[72]['axis']*(POLE_LENGTH-BACK_OFFSET)
plant_box=make_box(scene,anchor)
armdata=bpy.data.armatures.new('Pepe_Plant_Rig');rig=bpy.data.objects.new('Pepe_Plant_Rig',armdata);scene.collection.objects.link(rig);rig.show_in_front=True;armdata.display_type='OCTAHEDRAL';active(rig);bpy.ops.object.mode_set(mode='EDIT')
parents={};rest_points={}
def bone(name,a,b,parent=None,hinge=None):
 o=armdata.edit_bones.new(name);o.head=a;o.tail=b
 if parent:o.parent=armdata.edit_bones[parent]
 if hinge is not None:o.align_roll(hinge.cross((V(b)-V(a)).normalized()))
 parents[name]=parent;rest_points[name]=(V(a),V(b));return o
bone('hips',(0,-.035,.41),(0,-.035,.50));bone('chest',(0,-.035,.50),(0,-.015,.70),'hips');bone('head',(0,-.015,.70),(0,-.015,.85),'chest')
for side,(s,e,w) in ARM_REST.items():
 hinge=(e-s).cross(w-e).normalized()
 bone(side+'_clavicle',(0,s.y,s.z),s,'chest')
 bone(side+'_shoulder_cap',s,s+(e-s).normalized()*.04,side+'_clavicle',hinge)
 bone(side+'_upper_arm_swing',s,e,side+'_shoulder_cap',hinge)
 bone(side+'_upper_arm',s,e,side+'_upper_arm_swing',hinge)
 bone(side+'_forearm',e,w,side+'_upper_arm',hinge)
 bone(side+'_forearm_twist',e,w,side+'_forearm',hinge)
 b=bone(side+'_hand',w,w+V((0,0,.04)),side+'_forearm_twist');b.align_roll(V((0,-1,0)))
for side,(h,k,a) in LEG_REST.items():
 hinge=(k-h).cross(a-k).normalized();hinge=hinge if hinge.x>=0 else -hinge;bone(side+'_thigh_swing',h,k,'hips',hinge);bone(side+'_thigh',h,k,side+'_thigh_swing',hinge);bone(side+'_shin',k,a,side+'_thigh',hinge);bone(side+'_shin_swing',k,a,side+'_thigh_swing',hinge);bone(side+'_foot',a,a+V((0,-.07,-.025)),side+'_shin')
bpy.ops.object.mode_set(mode='OBJECT');bind={b.name:b.matrix_local.copy() for b in armdata.bones}
groups={b.name:body.vertex_groups.new(name=b.name) for b in armdata.bones};names=list(groups);weights=np.zeros((len(body.data.vertices),len(names)));fixed=np.zeros(len(body.data.vertices),bool)
for v in body.data.vertices:
 p=v.co;d={};armsum=0
 for side,(s,e,w) in ARM_REST.items():
  sign=-1 if side=='Right' else 1;du,tu=seg(p,s,e);dl,tl=seg(p,e,w)
  influence=smooth(.105,.165,p.x*sign)*(1-smooth(.10,.15,min(du,dl)))
  if p.x*sign>.20 and p.z>w.z-.01:influence=1
  if p.x*sign<.135 and p.z<s.z-.02:influence=0
  if not influence:continue
  path=tu*(e-s).length if du<dl else (e-s).length+tl*(w-e).length
  lower=smooth((e-s).length-.025,(e-s).length+.025,path);hand=smooth(w.z-.027,w.z+.003,p.z) if p.x*sign>.20 else 0
  collar=(1-smooth(0,.045,path))*.35
  d[side+'_clavicle']=influence*(1-lower)*(1-hand)*collar
  twist_blend=smooth((e-s).length*.70,(e-s).length,path)
  d[side+'_upper_arm_swing']=influence*(1-lower)*(1-hand)*(1-collar)*(1-twist_blend)
  d[side+'_upper_arm']=influence*(1-lower)*(1-hand)*(1-collar)*twist_blend
  d[side+'_forearm_twist']=influence*lower*(1-hand);d[side+'_hand']=influence*hand;armsum+=influence
 remaining=max(0,1-armsum)
 if p.z<.445:
  side='Right' if p.x<-.012 else 'Left';h,k,a=LEG_REST[side];du,tu=seg(p,h,k);dl,tl=seg(p,k,a)
  influence=1-smooth(.38,.448,p.z);path=tu*(k-h).length if du<dl else (k-h).length+tl*(a-k).length
  lower=smooth((k-h).length-.035,(k-h).length+.035,path);foot=1-smooth(.045,.105,p.z)
  twist_blend=0.0
  d[side+'_thigh_swing']=remaining*influence*(1-lower)*(1-foot)*(1-twist_blend);d[side+'_thigh']=remaining*influence*(1-lower)*(1-foot)*twist_blend;d[side+'_shin_swing']=remaining*influence*lower*(1-foot);d[side+'_foot']=remaining*influence*foot;remaining*=1-influence
 head=smooth(.71,.775,p.z);chest=smooth(.455,.56,p.z)*(1-head)
 d['hips']=remaining*(1-head-chest);d['chest']=remaining*chest;d['head']=remaining*head
 for side,(s,e,w) in ARM_REST.items():
  cap=(1-smooth(.032,.085,(p-s).length))*.90
  if cap>0:
   for n in list(d):d[n]*=1-cap
   d[side+'_shoulder_cap']=cap
 for name,val in d.items():weights[v.index,names.index(name)]=val
 fixed[v.index]=(abs(p.x)<.075 and p.z>.48) or (abs(p.x)<.135 and p.z>.78) or (p.x<-.20 and p.z>.897) or (p.x>.20 and p.z>.757) or p.z<.045
edges=np.array([list(e.vertices) for e in body.data.edges]);degree=np.bincount(edges.ravel(),minlength=len(weights))[:,None]
for iteration in range(28):
 totals=np.zeros_like(weights);np.add.at(totals,edges[:,0],weights[edges[:,1]]);np.add.at(totals,edges[:,1],weights[edges[:,0]])
 weights[~fixed]=.4*weights[~fixed]+.6*(totals/np.maximum(1,degree))[~fixed]
weights/=weights.sum(axis=1)[:,None]
for i,row in enumerate(weights):
 for name,val in zip(names,row):
  if val>1e-7:groups[name].add([i],float(val),'REPLACE')
mod=body.modifiers.new('Armature','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True;body.parent=rig
# Pose transitions used to check the last steps in the reference, in place.
LEG_KEYS={
 'Right':[(1,(-.10,.17,.14)),(25,(-.10,-.12,.06)),(49,(-.10,.16,.15)),(73,(-.10,-.18,.24)),(121,(-.10,-.27,.34)),(145,(-.10,-.28,.26)),(169,(-.09,-.12,.09)),(193,(-.083,-.02,.05)),(217,(-.083,-.02,.05))],
 'Left':[(1,(.065,-.10,.06)),(25,(.065,.15,.16)),(49,(.065,-.10,.06)),(73,(.065,-.035,.069)),(121,(.065,.09,.20)),(145,(.065,-.27,.24)),(169,(.075,-.12,.08)),(193,(.08,-.02,.05)),(217,(.08,-.02,.05))]}
def leg_target(side,frame):
 keys=LEG_KEYS[side]
 for j in range(len(keys)-1):
  if frame<=keys[j+1][0]:break
 a,p=keys[j];b,q=keys[j+1];t=max(0,min(1,(frame-a)/(b-a)));t=t*t*(3-2*t);return V(p).lerp(V(q),t)
def matrices_for(f):
 T=f['torso'];M={'hips':T@bind['hips'],'chest':T@bind['chest'],'head':T@bind['head']};legs={}
 for side,a in f['arms'].items():
  rs,re,rw=ARM_REST[side];body_q=T.to_quaternion();swing_q=(body_q@(re-rs)).rotation_difference(a['elbow']-a['shoulder'])@body_q
  M[side+'_upper_arm_swing']=affine(swing_q,rs,a['shoulder'])@bind[side+'_upper_arm_swing']
  M[side+'_shoulder_cap']=affine(body_q.slerp(swing_q,.5),rs,a['shoulder'])@bind[side+'_shoulder_cap']
  M[side+'_clavicle']=T@bind[side+'_clavicle']
  for part,q,src,dst in [('upper_arm',a['upper_q'],rs,a['shoulder']),('forearm',a['forearm_q'],re,a['elbow']),('forearm_twist',a['twist_q'],re,a['elbow']),('hand',a['hand_q'],rw,a['wrist'])]:M[side+'_'+part]=affine(q,src,dst)@bind[side+'_'+part]
 for side,(rh,rk,ra) in LEG_REST.items():
  h=T@rh;a=T@(leg_target(side,f['frame'])-V((0,-.025*f['lift'],.012*f['lift'])));u=(rk-rh).length;l=(ra-rk).length;dv=a-h;dist=dv.length
  if dist>u+l-.002:a=h+dv.normalized()*(u+l-.002);dv=a-h;dist=dv.length
  axis=dv.normalized();along=(u*u-l*l+dist*dist)/(2*dist);height=math.sqrt(max(0,u*u-along*along));bend=f['body_q']@V((0,-1,.1));bend=(bend-axis*bend.dot(axis)).normalized();k=h+axis*along+bend*height
  ru=(rk-rh).normalized();rl=(ra-rk).normalized();uvec=(k-h).normalized();lvec=(a-k).normalized();rhg=ru.cross(rl).normalized();rhg=rhg if rhg.x>=0 else -rhg;hg=uvec.cross(lvec).normalized()
  def basis(hh,dd):return Matrix((hh,dd,hh.cross(dd))).transposed()
  uq=(basis(hg,uvec)@basis(rhg,ru).transposed()).to_quaternion();lq=(basis(hg,lvec)@basis(rhg,rl).transposed()).to_quaternion();footq=f['body_q']@Matrix.Rotation(math.radians(18*f['lift'] if side=='Left' else -8*f['lift']),4,'X').to_quaternion()
  M[side+'_thigh_swing']=affine((f['body_q']@(rk-rh)).rotation_difference(k-h)@f['body_q'],rh,h)@bind[side+'_thigh_swing'];M[side+'_thigh']=affine(uq,rh,h)@bind[side+'_thigh'];M[side+'_shin']=affine(lq,rk,k)@bind[side+'_shin'];M[side+'_foot']=affine(footq,ra,a)@bind[side+'_foot'];M[side+'_shin_swing']=affine((f['body_q']@(ra-rk)).rotation_difference(a-k)@f['body_q'],rk,k)@bind[side+'_shin_swing']
  legs[side]={'knee_bend_deg':math.degrees((k-h).angle(a-k)),'ankle':list(a)}
 return M,legs
all_mats=[]
for f in frames:
 M,legs=matrices_for(f);all_mats.append(M);f['legs']=legs
# Keep the source mesh and its original bind matrices. Baking a deformed carry
# mesh into another bind caused a second deformation at the right shoulder.
def set_pose(M):
 for name in names:rig.pose.bones[name].matrix=M[name];bpy.context.view_layer.update()
mod.use_deform_preserve_volume=False
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
scene.frame_start=1;scene.frame_end=FRAME_END;scene.render.fps=30;rig.animation_data_clear();pole.animation_data_clear()
# Named grip sockets follow the pole, including during animated export.
sockets=[]
for side,z in [('Right',BACK_OFFSET),('Left',BACK_OFFSET+GRIP_SPACING)]:
 o=bpy.data.objects.new('GripSocket_'+side,None);scene.collection.objects.link(o);o.parent=pole;o.location=(0,0,z);o.empty_display_type='ARROWS';o.empty_display_size=.02;sockets.append(o)
last_quaternions={}
for i,f in enumerate(frames):
 scene.frame_set(f['frame']);set_pose(all_mats[i]);pole.location=f['back']-f['axis']*BACK_OFFSET;pole.rotation_quaternion=f['pole_basis'].to_quaternion();key_bend(pole_rig,pole_stations,pole_binds,f['bend'],f['frame'])
 for name in names:
  pb=rig.pose.bones[name]
  if name in last_quaternions and pb.rotation_quaternion.dot(last_quaternions[name])<0:pb.rotation_quaternion.negate()
  last_quaternions[name]=pb.rotation_quaternion.copy()
  pb.keyframe_insert('location',frame=f['frame'],group=name);pb.keyframe_insert('rotation_quaternion',frame=f['frame'],group=name);pb.keyframe_insert('scale',frame=f['frame'],group=name)
 pole.keyframe_insert('location',frame=f['frame']);pole.keyframe_insert('rotation_quaternion',frame=f['frame'])
rig.animation_data.action.name='PolePlant_Reference_Study';pole.animation_data.action.name='PolePlant_PolePath';pole_rig.animation_data.action.name='PolePlant_Flex'
for frame,label in [(1,'01 CARRY / REAR HAND AT HIP'),(25,'02 RAISE / HAND TO SHOULDER'),(49,'03 EXTEND / BOTH HANDS UP'),(73,'04 PLANT / DRIVE KNEE'),(121,'05 TAKEOFF / POLE LOADED'),(145,'06 SWING / FEET FORWARD'),(169,'07 ROCK BACK / FEET ABOVE HEAD'),(193,'08 INVERT / EXTEND LEGS'),(217,'HOLD')]:scene.timeline_markers.new(label,frame=frame)
# Conservative game-tuning limits, separate from Blender's non-portable constraints.
limits={'version':1,'units':'degrees','coordinate_system':'Blender Z-up, forward -Y; GLB converts to Y-up','purpose':'Initial game tuning bounds, not biomechanical measurements. Apply in the runtime joint solver; GLB does not enforce Blender constraints.','joints':{},'grips':{'rear':'Right_hand','front':'Left_hand','spacing_source_units':GRIP_SPACING,'pole_radius_source_units':.0078}}
for side in ARM_REST:
 for part,kind,values in [('upper_arm','cone_twist',{'swing_cone':165,'twist':[-110,110]}),('forearm','hinge',{'bend':[3,148]}),('forearm_twist','axial_twist',{'twist':[-100,100]}),('hand','swing_twist',{'swing_cone':35,'axial_twist':[-20,20]}),('thigh','cone_twist',{'swing_cone':120,'twist':[-45,45]}),('shin','hinge',{'bend':[0,145]}),('foot','swing_twist',{'swing_cone':45,'axial_twist':[-15,15]})]:
  name=side+'_'+part;entry={'type':kind,**values,'local_long_axis':[0,1,0],'bind_matrix_column_major':[float(armdata.bones[name].matrix_local[r][c]) for c in range(4) for r in range(4)],'parent':parents[name],'physics_parent':(side+'_clavicle' if part=='upper_arm' else 'hips' if part=='thigh' else parents[name])};limits['joints'][name]=entry
  pb=rig.pose.bones[name];pb['game_joint_type']=kind
  rest=armdata.bones[name].matrix_local.copy();parent=armdata.bones[name].parent
  if parent:rest=parent.matrix_local.inverted()@rest
  q=rest.to_quaternion();entry['bind_local_rotation_xyzw']=[q.x,q.y,q.z,q.w]
  for key,value in values.items():pb['game_'+key]=value
# Enabled edit guards: these ranges match the reviewed bind and preserve the clip.
for side in ARM_REST:
 c=rig.pose.bones[side+'_hand'].constraints.new('LIMIT_ROTATION');c.name='Wrist edit limit';c.owner_space='LOCAL';c.use_limit_x=c.use_limit_y=c.use_limit_z=True;c.min_x=c.min_z=math.radians(-35);c.max_x=c.max_z=math.radians(35);c.min_y=math.radians(-20);c.max_y=math.radians(20)
 for part,bind_bend,lo,hi in [('forearm',math.degrees((ARM_REST[side][1]-ARM_REST[side][0]).angle(ARM_REST[side][2]-ARM_REST[side][1])),3,148),('shin',math.copysign(math.degrees((LEG_REST[side][1]-LEG_REST[side][0]).angle(LEG_REST[side][2]-LEG_REST[side][1])),(LEG_REST[side][1]-LEG_REST[side][0]).cross(LEG_REST[side][2]-LEG_REST[side][1]).x),0,145)]:
  c=rig.pose.bones[side+'_'+part].constraints.new('LIMIT_ROTATION');c.name='Hinge edit limit';c.owner_space='LOCAL';c.use_limit_x=c.use_limit_y=c.use_limit_z=True;c.min_x=math.radians(lo-bind_bend);c.max_x=math.radians(hi-bind_bend);c.min_y=c.max_y=c.min_z=c.max_z=0
  limits['joints'][side+'_'+part]['bind_bend_degrees']=bind_bend;limits['joints'][side+'_'+part]['local_hinge_axis']=[1,0,0]
# Axial twist limits use a neutral orientation centered on the authored range,
# so a palm-up carry can turn into an overhead plant without an arbitrary bind stop.
for side in ARM_REST:
 twists=[]
 for f in frames:
  scene.frame_set(f['frame']);q=rig.pose.bones[side+'_forearm_twist'].rotation_quaternion;twists.append(2*math.atan2(q.y,q.w))
 values=np.unwrap(twists);center=float((min(values)+max(values))/2);entry=limits['joints'][side+'_forearm_twist'];entry['neutral_twist_from_bind_degrees']=math.degrees(center);entry['observed_twist_from_bind_degrees']=[math.degrees(min(values)),math.degrees(max(values))]
# Pose-space correctives soften only the blended shoulder/hip seams. Grip
# vertices stay rigid; the shapes export alongside the bone animation.
body.shape_key_add(name='Basis');bind_positions=np.array([list(v.co) for v in body.data.vertices]);mask=np.zeros(len(weights))
for side in ARM_REST:
 upper=sum(weights[:,names.index(side+'_'+part)] for part in ['clavicle','shoulder_cap','upper_arm_swing','upper_arm'])
 leg=weights[:,names.index(side+'_thigh')]+weights[:,names.index(side+'_thigh_swing')]
 mask=np.maximum(mask,np.maximum(4*upper*(1-upper),4*leg*(1-leg)))
hand_total=sum(weights[:,names.index(side+'_hand')] for side in ARM_REST);mask*=np.maximum(0,1-hand_total*10)
# Vertices dominated by a single rigid region need no correction.
mask*=np.clip((1-weights.max(axis=1))*3,0,1)
correctives=[]
for frame,label in [(1,'Carry_joint_cleanup'),(25,'Raise_joint_cleanup'),(49,'Extend_joint_cleanup'),(73,'Plant_joint_cleanup'),(145,'Swing_joint_cleanup'),(169,'Rockback_joint_cleanup'),(193,'Inverted_joint_cleanup')]:
 scene.frame_set(frame);bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh_eval=ev.to_mesh();current=np.array([list(v.co) for v in mesh_eval.vertices]);ev.to_mesh_clear();smooth_positions=current.copy()
 for _ in range(100):
  totals=np.zeros_like(smooth_positions);np.add.at(totals,edges[:,0],smooth_positions[edges[:,1]]);np.add.at(totals,edges[:,1],smooth_positions[edges[:,0]])
  smooth_positions+=(totals/np.maximum(1,degree)-smooth_positions)*mask[:,None]*.4
 transforms=np.array([np.array(rig.pose.bones[n].matrix@armdata.bones[n].matrix_local.inverted()) for n in names]);linear=np.einsum('ij,jkl->ikl',weights,transforms[:,:3,:3]);delta=np.linalg.solve(linear+np.eye(3)[None,:,:]*1e-7,(smooth_positions-current)[:,:,None])[:,:,0];lengths=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.035/np.maximum(lengths,1e-12))[:,None]
 shape=body.shape_key_add(name=label);positions=(bind_positions+delta).astype(np.float32);shape.data.foreach_set('co',positions.ravel());correctives.append((frame,shape))
for frame in [1,25,49,73,121,145,169,193,FRAME_END]:
 for at,shape in correctives:
  shape.value=1 if at==frame or (at==73 and frame==121) or (at==193 and frame==FRAME_END) else 0;shape.keyframe_insert('value',frame=frame)
body.data.shape_keys.animation_data.action.name='PolePlant_JointCorrectives'
for side in ARM_REST:
 entry=limits['joints'][side+'_forearm_twist'];low,high=entry['observed_twist_from_bind_degrees'];half=max(100,math.ceil(((high-low)/2+5)/5)*5);entry['twist']=[-half,half];rig.pose.bones[side+'_forearm_twist']['game_twist']=[-half,half]
calibrate_limits(scene,rig,limits)
limits['rotation_inputs']='Bone-local quaternion delta from bind. Hinge bend adds bind_bend_degrees. Axial twist is centered at neutral_twist_from_bind_degrees. Use physics_parent when omitting skin-deformation helper bones.'
rig['instructions']='Space plays the 217-frame carry, plant, takeoff and inverted swing study. Edit keyed FK bones and VaultPole curves together. Wrist/elbow/knee edit limits are enabled. Runtime limits are in pepe-joint-limits.json; GLB does not enforce Blender constraints.'
rig['no_runtime_physics_override']=True
(ROOT/'public/assets/pepe-joint-limits.json').write_text(json.dumps(limits,indent=2))
report={'sources_unchanged':all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))] for p in inputs),'source_hashes':hashes,'fps':30,'frames':FRAME_END,'stages':[{'frame':n,'label':s} for n,s in [(1,'Carry'),(25,'Raise'),(49,'Extend'),(73,'Plant'),(121,'Takeoff'),(145,'Swing'),(169,'Rock back'),(193,'Inverted')]],'max_wrist_angle_deg':max(a['wrist_angle_deg'] for f in frames for a in f['arms'].values()),'frames_data':[{'frame':f['frame'],'body_rotation_degrees':f['body_angle_deg'],'head_position':list(f['torso']@V((0,-.015,.85))),'back_grip':list(f['back']),'axis':list(f['axis']),'pole_bend_degrees':math.degrees(f['bend']),'pole_tip':list((f['back']-f['axis']*BACK_OFFSET)+f['pole_basis']@pole_curve(POLE_LENGTH,f['bend'])),'wrists':{s:a['wrist_angle_deg'] for s,a in f['arms'].items()},'elbows':{s:a['elbow_bend_deg'] for s,a in f['arms'].items()},'legs':f['legs']} for f in frames]}
assert report['sources_unchanged'] and report['max_wrist_angle_deg']<35
(OUT/'report.json').write_text(json.dumps(report,indent=2))
report['pole']={'arc_length':POLE_LENGTH,'straight_grip_length':BEND_START,'flex_bones':len(pole_stations),'anchor':list(anchor),'anchored_from_frame':73,'max_bend_degrees':math.degrees(max(f['bend'] for f in frames))}
(OUT/'report.json').write_text(json.dumps(report,indent=2))
for action in [rig.animation_data.action,pole.animation_data.action,pole_rig.animation_data.action,body.data.shape_keys.animation_data.action]:
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
scene.name='PolePlant_ReferenceStudy'
# Export the animation and two explicit still poses as independent new files.
def select_asset():
 active(body);rig.select_set(True);pole.select_set(True);plant_box.select_set(True)
 for o in pole.children_recursive:o.select_set(True)
scene.frame_set(1);select_asset()
props=bpy.ops.export_scene.gltf.get_rna_type().properties
kwargs={'export_format':'GLB','use_selection':True,'export_animations':True,'export_skins':True,'export_extras':True,'export_force_sampling':True,'export_frame_range':True,'export_anim_slide_to_zero':True,'export_animation_mode':'SCENE','export_anim_scene_split_object':False}
kwargs={k:v for k,v in kwargs.items() if k in props}
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/pepe-plant-animated.glb'),**kwargs)
for frame,name in [(1,'pepe-carry-ready'),(73,'pepe-plant-ready'),(121,'pepe-takeoff-ready'),(193,'pepe-inverted-ready')]:
 scene.frame_set(frame);bpy.context.view_layer.update();copies=[]
 for original in [body,pole_mesh,plant_box]:
  m=bpy.data.meshes.new_from_object(original.evaluated_get(bpy.context.evaluated_depsgraph_get()));o=bpy.data.objects.new(original.name+'_Posed',m);scene.collection.objects.link(o);o.matrix_world=original.matrix_world.copy();copies.append(o)
 active(copies[0])
 for o in copies:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets'/f'{name}.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
 for o in copies:bpy.data.objects.remove(o,do_unlink=True)
scene.frame_set(1);select_asset();scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=1.3
for frame,label in [(1,'carry'),(25,'raise'),(49,'extend'),(73,'plant'),(121,'takeoff'),(145,'swing'),(169,'rockback'),(193,'inverted')]:
 scene.frame_set(frame);target=frames[frame-1]['torso']@V((-.02,-.12,.56));cam.location=target+V((-1.7,-2.0,.4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'{label}.png');bpy.ops.render.render(write_still=True)
# Save a side view of the full pole at the plant for comparison with the diagram.
scene.frame_set(73);target=V((.2,-.65,.54));cam.data.ortho_scale=2.2;cam.location=target+V((-3,-.2,.15));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'plant-side.png');bpy.ops.render.render(write_still=True)
# Full shaft view makes the tip anchor and loaded curve directly reviewable.
scene.frame_set(121);target=V((.24,-.65,.70));cam.data.ortho_scale=2.25;cam.location=target+V((-3,-.2,.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'takeoff-side.png');bpy.ops.render.render(write_still=True)
scene.frame_set(193);target=V((.30,-.65,1.05));cam.data.ortho_scale=2.75;cam.location=target+V((-3,-.2,.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'inverted-side.png');bpy.ops.render.render(write_still=True)
scene.frame_set(1);target=V((-.02,-.12,.56));cam.data.ortho_scale=1.3;cam.location=target+V((-1.7,-2.0,.4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();active(rig)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/pepe-plant-rig.blend'),compress=True)
print('PLANT_RIG_DONE',report['max_wrist_angle_deg'],flush=True)
