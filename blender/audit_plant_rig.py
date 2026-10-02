"""Validate evaluated geometry, not only the input pose targets."""
import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'blender'))
from plant_motion import pole_curve,POLE_LENGTH,BEND_START
out=root/'output/plant-rig';report=json.loads((out/'report.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(root/'blender/pepe-plant-rig.blend'));rig=bpy.data.objects['Pepe_Plant_Rig'];body=bpy.data.objects['Pepe_Plant_Skinned'];pole=bpy.data.objects['VaultPole'];flex=bpy.data.objects['VaultPole_FlexRig'];scene=bpy.context.scene
rows=[];angles={};first={};step_angles={};grip_bind={};tip_anchor=Vector(report['pole']['anchor'])
scene.frame_set(1);bpy.context.view_layer.update()
for side in ['Right','Left']:
 grip_bind[side]=rig.pose.bones[side+'_hand'].matrix.inverted()@bpy.data.objects['GripSocket_'+side].matrix_world.translation
for frame in range(1,report['frames']+1):
 scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);m=evaluated.to_mesh();bm=bmesh.new();bm.from_mesh(m);bvh=BVHTree.FromBMesh(bm)
 bend=math.radians(report['frames_data'][frame-1]['pole_bend_degrees']);points=[pole.matrix_world@pole_curve(POLE_LENGTH*i/64,bend) for i in range(65)];hits=[]
 for p,q in zip(points,points[1:]):
  axis=(q-p).normalized();u=Vector((0,0,1)).cross(axis).normalized();v=axis.cross(u).normalized()
  for a,b in [(i*.002,j*.002) for i in range(-4,5) for j in range(-4,5) if i*i+j*j<=16]:
   hit=bvh.ray_cast(p+u*a+v*b,axis,(q-p).length)
   if hit[0] is not None:hits.append({'point':list(hit[0]),'segment_length':hit[3]})
 tip=pole.matrix_world@flex.pose.bones[-1].head
 row={'frame':frame,'shaft_hits':len(hits),'hit_examples':hits[:1],'min_height':min(v.co.z for v in bm.verts),'wrists':{},'grip_errors':{},'tip_anchor_error':(tip-tip_anchor).length if frame>=73 else None}
 for side in ['Right','Left']:
  hand=rig.pose.bones[side+'_hand'];fore=rig.pose.bones[side+'_forearm_twist'];row['wrists'][side]=math.degrees((hand.tail-hand.head).angle(fore.tail-fore.head));row['grip_errors'][side]=(hand.matrix@grip_bind[side]-bpy.data.objects['GripSocket_'+side].matrix_world.translation).length
  for part in ['upper_arm','forearm','forearm_twist','hand','shin']:
   p=rig.pose.bones[side+'_'+part];eu=[math.degrees(a) for a in p.matrix_basis.to_euler('XYZ')];angles.setdefault(p.name,[]).append(eu)
   if frame>1:step_angles.setdefault(p.name,[]).append(min(math.degrees(first[p.name].rotation_difference(p.rotation_quaternion).angle),360-math.degrees(first[p.name].rotation_difference(p.rotation_quaternion).angle)))
   first[p.name]=p.rotation_quaternion.copy()
 rows.append(row);bm.free();evaluated.to_mesh_clear()
result={'sources_unchanged':all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in report['source_hashes'].items()),'frames':rows,'max_wrist_angle':max(v for r in rows for v in r['wrists'].values()),'max_grip_error':max(v for r in rows for v in r['grip_errors'].values()),'max_anchor_error':max(r['tip_anchor_error'] or 0 for r in rows),'local_euler_ranges':{n:[[min(e[k] for e in es),max(e[k] for e in es)] for k in range(3)] for n,es in angles.items()},'max_frame_rotation_degrees':{n:max(es) for n,es in step_angles.items()}}
(out/'audit.json').write_text(json.dumps(result,indent=2));print('AUDIT',result['max_wrist_angle'],'COLLISIONS',[(r['frame'],r['shaft_hits']) for r in rows if r['shaft_hits']],'MIN_HEIGHT',min(r['min_height'] for r in rows),'GRIP_ERROR',result['max_grip_error'],'ANCHOR_ERROR',result['max_anchor_error'],'MAX_STEP',result['max_frame_rotation_degrees'],flush=True)
assert result['sources_unchanged']
assert result['max_wrist_angle']<35
assert result['max_grip_error']<.002, 'Exported constraint evaluation displaced a hand from the grip'
assert result['max_anchor_error']<1e-4
assert not any(r['shaft_hits'] for r in rows), 'Shaft intersects character mesh'
assert max(result['max_frame_rotation_degrees'].values())<25, 'Discontinuous joint rotation'
