"""Reproducible, articulated Pepe + vault assets. Run with Blender --background --python."""
import bpy, math, os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'public','assets'); os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def mat(name, color, rough=.55, metal=0):
    color=tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in color)
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough; bs.inputs['Metallic'].default_value=metal
    return m
skin=mat('Pepe • olive green',(.35,.55,.23)); light=mat('Raised muscle planes',(.37,.58,.25)); dark=mat('Crease green',(.16,.29,.075)); lips=mat('Warm terracotta lips',(.65,.34,.19)); white=mat('Ivory eyes and shoes',(.96,.96,.87)); pupil=mat('Glossy black pupils',(.006,.012,.009),.16); blue=mat('Cobalt competition shorts',(.14,.24,.64)); sole=mat('Shoe soles',(.66,.72,.63)); yellow=mat('Volt fiberglass',(.78,.96,.12),.3); navy=mat('Midnight stadium',(.025,.065,.075)); metal=mat('Aluminum',(.46,.53,.53),.3,.7); rust=mat('Track terracotta',(.52,.19,.105)); foam=mat('Sage landing pad',(.23,.44,.34))

def empty(name, loc=(0,0,0), parent=None):
    o=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(o); o.location=loc; o.parent=parent; o.empty_display_type='PLAIN_AXES'; o.empty_display_size=.2; return o

def sphere(name,loc,scale,material,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=(0,0,0)); o=bpy.context.object; o.name=name; o.parent=parent; o.location=loc; o.scale=scale; o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    return o

def cube(name, loc, scale, material, bevel=.05,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.parent=parent;o.location=loc;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
    if bevel: m=o.modifiers.new('Soft edges','BEVEL');m.width=bevel;m.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o

def line(name,points,r,material,parent=None):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=16;c.bevel_depth=r;c.bevel_resolution=4;s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for b,co in zip(s.bezier_points,points): b.co=co;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.parent=parent;o.data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');return bpy.context.object
rig=empty('PepeRoot'); hips=empty('hips',(0,0,1.18),rig); chest=empty('chest',(0,0,.34),hips); neck=empty('head',(0,0,.69),chest)
sphere('Tapered core',(0,0,.14),(.41,.24,.43),skin,chest)
sphere('Lats',(0,.065,.34),(.54,.24,.30),skin,chest)
for s in [-1,1]:
    sphere('Pectoral',(.235*s,-.185,.37),(.29,.145,.21),light,chest)
    for z,w in [(.10,.145),(-.055,.135),(-.195,.115)]:sphere('Abdominal',(.112*s,-.222,z),(w,.075,.086),light,chest)
    sphere('Trapezius',(.21*s,.015,.60),(.26,.23,.17),skin,chest)
    leg=empty(('left' if s<0 else 'right')+'UpperLeg',(.235*s,0,-.03),hips)
    sphere('Shorts leg',(0,0,-.115),(.265,.265,.28),blue,leg)
    sphere('Powerful quadriceps',(0,-.01,-.37),(.19,.195,.34),light,leg)
    sphere('Inner thigh',(-s*.065,.06,-.38),(.135,.16,.28),skin,leg)
    low=empty(('left' if s<0 else 'right')+'LowerLeg',(0,0,-.61),leg)
    sphere('Knee',(0,-.05,0),(.135,.14,.14),skin,low)
    sphere('Calf',(0,.035,-.20),(.13,.145,.24),skin,low)
    sphere('Ankle',(0,0,-.37),(.082,.09,.15),skin,low)
    sphere('Ivory trainer',(0,-.095,-.46),(.13,.24,.10),white,low)
    cube('Sole',(0,-.095,-.51),(.245,.43,.036),sole,.03,low)
    arm=empty(('left' if s<0 else 'right')+'UpperArm',(.53*s,0,.44),chest)
    sphere('Deltoid',(s*.035,0,-.045),(.215,.225,.21),light,arm)
    sphere('Biceps',(s*.035,-.018,-.25),(.16,.185,.26),light,arm)
    sphere('Triceps',(s*.025,.07,-.24),(.155,.17,.26),skin,arm)
    fore=empty(('left' if s<0 else 'right')+'LowerArm',(s*.025,0,-.45),arm)
    sphere('Elbow',(0,0,0),(.105,.12,.12),skin,fore)
    sphere('Forearm',(s*.015,0,-.19),(.12,.13,.24),skin,fore)
    hand=empty(('left' if s<0 else 'right')+'Hand',(s*.025,0,-.40),fore)
    sphere('Palm',(0,0,-.035),(.125,.085,.13),skin,hand)
    for j in range(4):sphere('Finger',((j-1.5)*.054,-.035,-.105),(.033,.052,.077),light,hand)
    sphere('Thumb',(-s*.095,-.062,-.025),(.058,.063,.085),skin,hand)
# Broad frog head, protruding muzzle, high separated eye lobes.
sphere('Frog head',(0,.005,.23),(.43,.29,.47),skin,neck)
sphere('Frog muzzle',(0,-.195,.07),(.43,.22,.215),skin,neck)
for s in [-1,1]:
    sphere('Eye lobe',(.205*s,-.13,.49),(.25,.235,.245),skin,neck)
    sphere('Eye white',(.205*s,-.327,.435),(.208,.083,.128),white,neck)
    sphere('Pupil',(.19*s,-.402,.423),(.080,.032,.085),pupil,neck)
    sphere('Eye glint',(.19*s-.023,-.433,.453),(.023,.009,.023),white,neck)
    sphere('Small glint',(.19*s+.025,-.431,.404),(.010,.008,.010),white,neck)
    line('Heavy expressive brow',[(s*.035,-.352,.515),(s*.2,-.395,.549),(s*.387,-.32,.51)],.042,skin,neck)
    line('Lower eye crease',[(s*.04,-.346,.342),(s*.2,-.385,.310),(s*.36,-.30,.34)],.016,dark,neck)
line('Wide lower lip',[(-.355,-.347,.018),(-.23,-.425,-.035),(0,-.45,-.059),(.25,-.417,-.027),(.36,-.34,.025)],.050,lips,neck)
line('Wide upper lip',[(-.355,-.35,.054),(-.23,-.421,.018),(0,-.46,.005),(.25,-.408,.029),(.36,-.34,.069)],.039,lips,neck)
line('Mouth seam',[(-.34,-.379,.031),(-.20,-.457,-.008),(0,-.487,-.016),(.23,-.448,.004),(.345,-.37,.045)],.013,dark,neck)
sphere('Nostril L',(-.09,-.410,.17),(.021,.012,.012),dark,neck);sphere('Nostril R',(.09,-.410,.17),(.021,.012,.012),dark,neck)
# Orange competition bib on back, finished waistband.
cube('Waistband',(0,0,-.025),(.78,.46,.10),blue,.06,hips)
# Runtime exports retain the named pivot hierarchy for posing and ragdoll attachment.
def descendants(o):
    a=[o]
    for c in o.children:a+=descendants(c)
    return a

def export(root,path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in descendants(root):o.select_set(True)
    bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,export_animations=False,export_apply=True)
export(rig,os.path.join(OUT,'pepe.glb'))
pole=empty('VaultPole');line('Fiberglass pole',[(0,0,0),(0,0,5.5)],.035,yellow,pole)
for z in [3.1,3.25,3.4]:line('Grip tape',[(0,0,z),(0,0,z+.09)],.039,navy,pole)
export(pole,os.path.join(OUT,'pole.glb'))
bar=empty('Crossbar');line('Crossbar tube',[(0,-2.05,0),(0,2.05,0)],.045,yellow,bar)
export(bar,os.path.join(OUT,'crossbar.glb'))
bar.location=(3,0,4.6)
# Full editable practice facility in the .blend.
cube('Runway',(-6,0,-.11),(30,4.4,.2),rust)
for y in [-1.9,1.9]:cube('Lane stripe',(-6,y,.001),(30,.045,.012),white,.0)
for y in [-2.1,2.1]:
    cube('Vault standard',(3,y,2.8),(.13,.13,5.6),metal)
    cube('Standard base',(3,y,.10),(1,.65,.2),navy)
cube('Landing mat',(7.0,0,.38),(6.5,5,.75),foam,.20)
# Editable joint hierarchy only: no keyframes or baked animation clips.
# Live motors, hinge constraints, pole joints and gravity are implemented in src/physics.js.
rig.location.x=-8
rig.rotation_euler.z=math.pi/2
pole.location=(-3.0,0,.15);pole.rotation_euler.y=-1.30
scene=bpy.context.scene;scene.frame_end=250;scene.render.fps=60
# Blender-native rigid bodies and hinge joints, matching the runtime body decomposition.
# Collision proxies stay wireframe in the viewport and are excluded from rendering.
parts={o.name:o for o in descendants(rig)}
for side in ['left','right']:
    parts[side+'UpperArm'].rotation_euler.x=-(1.55 if side=='left' else 1.20)
    parts[side+'LowerArm'].rotation_euler.x=-.3
bpy.context.view_layer.update()
specs=[('hips',None,(.33,.16,.21),(0,-.02,0),8),('chest','hips',(.48,.34,.22),(0,.20,0),12),('head','chest',(.4,.44,.29),(0,.22,.035),4)]
for side in ['left','right']:
    specs += [(side+'UpperLeg','hips',(.18,.28,.18),(0,-.28,0),4),(side+'LowerLeg',side+'UpperLeg',(.12,.25,.14),(0,-.23,.045),2.8),(side+'UpperArm','chest',(.17,.23,.17),(0,-.22,0),2.2),(side+'LowerArm',side+'UpperArm',(.11,.21,.11),(0,-.19,0),1.4),(side+'Hand',side+'LowerArm',(.10,.105,.085),(0,-.04,0),.5)]
worlds={name:parts[name].matrix_world.copy() for name,_,_,_,_ in specs};proxies={}
for name,parent,size,center,mass in specs:
    c=Vector((center[0],-center[2],center[1]));pos=worlds[name]@c
    proxy=cube('COLLIDER • '+name,pos,(size[0]*2,size[2]*2,size[1]*2),skin,0)
    proxy.rotation_euler=worlds[name].to_euler();proxy.hide_render=True;proxy.display_type='WIRE'
    bpy.ops.rigidbody.object_add();proxy.rigid_body.mass=mass;proxy.rigid_body.collision_shape='BOX';proxy.rigid_body.friction=.55;proxy.rigid_body.linear_damping=.1;proxy.rigid_body.angular_damping=.5
    proxies[name]=proxy
for name,parent,size,center,mass in reversed(specs):
    part=parts[name];part.parent=proxies[name];part.matrix_world=worlds[name]
for name,parent,size,center,mass in specs:
    if not parent:continue
    joint=empty('HINGE • '+name,worlds[name].translation);joint.rotation_euler.x=math.pi/2
    bpy.ops.object.select_all(action='DESELECT');joint.select_set(True);bpy.context.view_layer.objects.active=joint;bpy.ops.rigidbody.constraint_add()
    c=joint.rigid_body_constraint;c.type='POINT' if name.endswith('UpperArm') else 'HINGE';c.object1=proxies[parent];c.object2=proxies[name];c.disable_collisions=True;c.use_limit_ang_z=True;c.limit_ang_z_lower=-2.8;c.limit_ang_z_upper=2.8
for name in ['Runway','Landing mat']:
    o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.rigidbody.object_add();o.rigid_body.type='PASSIVE';o.rigid_body.collision_shape='BOX'
scene.rigidbody_world.substeps_per_frame=4;scene.rigidbody_world.solver_iterations=30
bpy.ops.object.light_add(type='AREA',location=(0,-6,10));bpy.context.object.data.energy=2000;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=8
bpy.ops.object.camera_add(location=(-3,-16,8));cam=bpy.context.object;cam.rotation_euler=(Vector((-3,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam;cam.data.lens=40
scene.world.color=(.35,.35,.35)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','pepe-vault.blend'))
print('PEPE_ASSETS_READY')
