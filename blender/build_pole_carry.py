"""Create a separate posed Pepe and full vault pole, preserving grip-source assets."""
import bpy, bmesh, math, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/pole-carry';OUT.mkdir(exist_ok=True,parents=True)
inputs=[ROOT/'blender/pepe-tripo-grip.blend',ROOT/'public/assets/pepe-tripo-grip.glb']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
bpy.ops.wm.open_mainfile(filepath=str(inputs[0]));scene=bpy.context.scene
body=bpy.data.objects['Pepe_Retopo_Pole_Grip_Copy'];body.name='Pepe_Pole_Carry';body.data=body.data.copy()
for o in list(scene.objects):
 if o.name.startswith(('Gauge_','GripSocket_')):bpy.data.objects.remove(o,do_unlink=True)
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def smooth(a,b,t):
 t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
def frame_matrix(q,src,dst):return Matrix.Translation(dst)@q.to_matrix().to_4x4()@Matrix.Translation(-src)
def segment(p,a,b):
 t=max(0,min(1,(p-a).dot(b-a)/(b-a).length_squared));near=a+(b-a)*t;return (p-near).length,t
report0=json.loads((ROOT/'output/hand-grips/report.json').read_text());socks={s['name'].split('_')[-1]:s for s in report0['sockets']}
back=Vector((-.050,-.155,.660));front=Vector((.060,-.245,.705));axis=(front-back).normalized();up=Vector((0,0,1));hz=(up-axis*up.dot(axis)).normalized()
rest={
 'Right':(Vector((-.118,.020,.714)),Vector((-.230,.063,.785))),
 'Left':(Vector((.120,-.035,.657)),Vector((.259,-.105,.640)))
}
armdata=bpy.data.armatures.new('Pepe_Carry_Arm_Rig');rig=bpy.data.objects.new('Pepe_Carry_Arm_Rig',armdata);scene.collection.objects.link(rig);rig.show_in_front=True;active(rig);bpy.ops.object.mode_set(mode='EDIT');root=armdata.edit_bones.new('torso');root.head=(0,0,.45);root.tail=(0,0,.65)
transforms={};arm_info={}
for label,grip in [('Right',back),('Left',front)]:
 s,e=rest[label];w=Vector(socks[label]['position'])-Vector((0,-.014,.028));oldgrip=Vector(socks[label]['position'])
 x=axis if label=='Right' else -axis;y=hz.cross(x).normalized();R=Matrix((x,y,hz)).transposed();hq=R.to_quaternion();nw=grip-R@Vector((0,-.014,.028))
 l1=(e-s).length;l2=(w-e).length;d=(nw-s).length;assert abs(l1-l2)<d<l1+l2,(label,d,l1+l2)
 direction=(nw-s).normalized();a=(l1*l1-l2*l2+d*d)/(2*d);h=math.sqrt(max(0,l1*l1-a*a))
 bend=Vector((-1 if label=='Right' else 1,.2,-.9));bend=(bend-direction*bend.dot(direction)).normalized();ne=s+direction*a+bend*h
 uq=(e-s).rotation_difference(ne-s);lq=(hq@(w-e)).rotation_difference(nw-ne)@hq
 transforms[label]=[frame_matrix(uq,s,s),frame_matrix(lq,e,ne),frame_matrix(hq,w,nw)]
 arm_info[label]={'shoulder':list(s),'elbow':list(ne),'wrist':list(nw),'grip':list(grip),'pole_axis':list(x),'rest_wrist':list(w)}
 parent=root
 for part,start,end in [('upper',s,e),('forearm',e,w),('hand',w,w+Vector((0,0,.04)))]:
  b=armdata.edit_bones.new(label+'_'+part);b.head=start;b.tail=end;b.parent=parent;parent=b
bpy.ops.object.mode_set(mode='OBJECT')
for label,mats in transforms.items():
 for part,M in zip(['upper','forearm','hand'],mats):
  bone=rig.pose.bones[label+'_'+part];bone.matrix=M@bone.bone.matrix_local;bpy.context.view_layer.update()
bpy.context.view_layer.update()
groups={name:body.vertex_groups.new(name=name) for name in ['torso']+[label+'_'+p for label in rest for p in ['upper','forearm','hand']]}
import numpy as np
weight_names=list(groups);weight_values=np.zeros((len(body.data.vertices),len(weight_names)),dtype=np.float64)
fixed=np.zeros(len(body.data.vertices),dtype=bool)
for v in body.data.vertices:
 weights={};p=v.co
 for label in rest:
  sign=-1 if label=='Right' else 1;s,e=rest[label];w=Vector(arm_info[label]['rest_wrist']);du,tu=segment(p,s,e);dl,tl=segment(p,e,w)
  # Isolate each arm from the head and chest; shoulder weights blend gently.
  influence=smooth(.105,.165,p.x*sign)*(1-smooth(.10,.15,min(du,dl)))
  if p.x*sign>.20 and p.z>w.z-.01:influence=1
  if p.x*sign<.135 and p.z<s.z-.02:influence=0
  if not influence:continue
  path=tu*(e-s).length if du<dl else (e-s).length+tl*(w-e).length
  lower=smooth((e-s).length-.025,(e-s).length+.025,path)
  hand=smooth(w.z-.027,w.z+.003,p.z) if p.x*sign>.20 else 0
  weights[label+'_upper']=influence*(1-lower)*(1-hand);weights[label+'_forearm']=influence*lower*(1-hand);weights[label+'_hand']=influence*hand
 total=sum(weights.values());weights['torso']=max(0,1-total)
 for name,value in weights.items():
  if value>1e-6:weight_values[v.index,weight_names.index(name)]=value
 fixed[v.index]=(abs(p.x)<.135 and p.z<.63) or abs(p.x)<.075 or (abs(p.x)<.18 and p.z>.75) or (p.x<-.20 and p.z>.897) or (p.x>.20 and p.z>.757)
edges=np.array([list(e.vertices) for e in body.data.edges]);degree=np.bincount(edges.ravel(),minlength=len(body.data.vertices))[:,None]
for iteration in range(35):
 total=np.zeros_like(weight_values);np.add.at(total,edges[:,0],weight_values[edges[:,1]]);np.add.at(total,edges[:,1],weight_values[edges[:,0]])
 averaged=total/np.maximum(1,degree);weight_values[~fixed]=.35*weight_values[~fixed]+.65*averaged[~fixed]
for i,row in enumerate(weight_values):
 for name,value in zip(weight_names,row):
  if value>1e-6:groups[name].add([i],float(value),'REPLACE')
mod=body.modifiers.new('Editable carry pose','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
body.parent=rig
relax=body.vertex_groups.new(name='Carry_pose_relaxation')
for i,row in enumerate(weight_values):
 hand=row[weight_names.index('Right_hand')]+row[weight_names.index('Left_hand')]
 value=(1-row[0])*(1-hand)**2
 if value>.001:relax.add([i],float(value),'REPLACE')
smoothmod=body.modifiers.new('Relax posed elbow and shoulder creases','SMOOTH');smoothmod.factor=.65;smoothmod.iterations=12;smoothmod.vertex_group=relax.name
# Attachment frames are explicit and agree with the posed channels.
for label in rest:
 o=bpy.data.objects.new('GripSocket_'+label,None);scene.collection.objects.link(o);o.location=arm_info[label]['grip'];o.rotation_mode='QUATERNION';o.rotation_quaternion=transforms[label][2].to_quaternion();o.empty_display_type='ARROWS';o.empty_display_size=.025;o['pole_radius']=.0078
# Full pole length is 1.95 at source scale (5.58m at a 2.862x character scale).
length=1.95;radius=.0078;butt=back-axis*.026
polecol=bpy.data.collections.new('Vault_Pole');scene.collection.children.link(polecol);parts=[]
def material(name,color,rough=.4,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;return m
ivory=material('Fiberglass ivory',(.73,.78,.46),.28);green=material('Deep green lacquer',(.025,.072,.045),.3);tape=material('Charcoal grip tape',(.018,.026,.022),.72);stripe=material('Lime marking',(.42,.62,.10),.4);rubber=material('Rubber planting plug',(.035,.039,.033),.86)
def cylinder(name,a,b,r1,r2,mat):
 bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=r1,radius2=r2,depth=b-a,location=(0,0,(a+b)/2));o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 parts.append(o);return o
# Axial rings allow the game skeleton to bend the shaft continuously.
vs=[];fs=[];rings=96;sides=32
for i in range(rings+1):
 t=i/rings;r=radius*(1-.28*t)
 for j in range(sides):vs.append((r*math.cos(j*math.tau/sides),r*math.sin(j*math.tau/sides),t*length))
for i in range(rings):
 for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;fs.append((a,b,b+sides,a+sides))
fs.extend([tuple(reversed(range(sides))),tuple(rings*sides+j for j in range(sides))])
mesh=bpy.data.meshes.new('Flexible shaft rings');mesh.from_pydata(vs,[],fs);mesh.update();shaft=bpy.data.objects.new('Continuous tapered fiberglass shaft',mesh);scene.collection.objects.link(shaft);shaft.data.materials.append(ivory)
for f in shaft.data.polygons:f.use_smooth=len(f.vertices)==4
parts.append(shaft)
cylinder('Tail cap',-.004,.008,radius*1.025,radius*1.025,rubber)
cylinder('Grip wrap',.003,.305,radius*1.012,radius*1.012,tape)
# Low profile helical tape edge, below the fitted bore radius.
vs=[];fs=[];turns=28;N=turns*24
for i in range(N+1):
 t=i/N;ang=t*turns*math.tau;z=.004+t*.299
 for dz in [-.0004,.0004]:vs.append((radius*1.02*math.cos(ang),radius*1.02*math.sin(ang),z+dz))
for i in range(N):fs.append((2*i,2*i+1,2*i+3,2*i+2))
me=bpy.data.meshes.new('Tape seam');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Spiral tape seam',me);scene.collection.objects.link(o);o.data.materials.append(green);parts.append(o)
for a,b in [(.310,.322),(.58,.60),(.91,.93),(1.32,1.34)]:cylinder('Lime shaft marker',a,b,radius*.995,radius*.995,stripe)
cylinder('Planting tip collar',length-.065,length-.018,radius*.82,radius*.80,green)
cylinder('Replaceable planting plug',length-.023,length+.007,radius*.84,radius*.60,rubber)
# Pole root local +Z runs from the butt to the planting tip.
rootpole=bpy.data.objects.new('VaultPole',None);polecol.objects.link(rootpole);rootpole.location=butt;rootpole.rotation_mode='QUATERNION';rootpole.rotation_quaternion=Vector((0,0,1)).rotation_difference(axis);rootpole['length']=length;rootpole['nominal_radius']=radius;rootpole['game_scale']=5.58/length
for o in parts:
 for c in list(o.users_collection):c.objects.unlink(o)
 polecol.objects.link(o);o.parent=rootpole
bpy.context.view_layer.update()
# Standalone pole at origin, GLB local +Y along shaft after Blender's conversion.
oldloc=rootpole.location.copy();oldrot=rootpole.rotation_quaternion.copy();rootpole.location=(0,0,0);rootpole.rotation_quaternion=(1,0,0,0)
bpy.ops.object.select_all(action='DESELECT');rootpole.select_set(True)
for o in parts:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/vault-pole.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
rootpole.location=oldloc;rootpole.rotation_quaternion=oldrot;bpy.context.view_layer.update()
# Export a static evaluated carry asset; keep the editable arm rig in .blend.
deps=bpy.context.evaluated_depsgraph_get();posed=bpy.data.meshes.new_from_object(body.evaluated_get(deps));copy=bpy.data.objects.new('Pepe_Posed_Carry',posed);scene.collection.objects.link(copy);body.hide_render=True;body.hide_set(True)
active(copy);rootpole.select_set(True)
for o in parts:o.select_set(True)
for label in rest:bpy.data.objects['GripSocket_'+label].select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/pepe-pole-carry.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=1500;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.type='ORTHO';target=Vector((0,-.52,.65));cam.data.ortho_scale=2.2;cam.location=target+Vector((2.7,-2.1,1.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'carry.png');bpy.ops.render.render(write_still=True)
target=(back+front)/2;cam.data.ortho_scale=.56;cam.location=target+Vector((-1,-1,.55));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'two-hand-grip.png');bpy.ops.render.render(write_still=True)
# Keep the source mesh and live armature in the editable deliverable.
bpy.data.objects.remove(copy,do_unlink=True);body.hide_render=False;body.hide_set(False);active(body)
target=Vector((0,-.52,.65));cam.data.ortho_scale=2.2;cam.location=target+Vector((2.7,-2.1,1.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/pepe-pole-carry.blend'),compress=True)
report={'source_hashes':hashes,'sources_unchanged':all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))] for p in inputs),'pole_length':length,'pole_radius':radius,'pole_axis':list(axis),'pole_butt':list(butt),'grip_spacing':(front-back).length,'arms':arm_info,'notes':'Editable arm rig in Blender; static evaluated carry GLB, separate pole GLB. No baked animation.'};(OUT/'report.json').write_text(json.dumps(report,indent=2));assert report['sources_unchanged'];print('DONE',flush=True)
