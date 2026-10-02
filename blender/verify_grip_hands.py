import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];out=root/'output/hand-grips'
bpy.ops.wm.open_mainfile(filepath=str(root/'blender/pepe-tripo-grip.blend'))
o=bpy.data.objects['Pepe_Retopo_Pole_Grip_Copy'];bm=bmesh.new();bm.from_mesh(o.data);tree=BVHTree.FromBMesh(bm)
report=json.loads((out/'report.json').read_text());checks=[]
assert all(e.is_manifold and e.is_contiguous for e in bm.edges), 'Non-manifold or inconsistent mesh'
import hashlib
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in report['source_hashes'].items()), 'Original source changed'
for sock in report['sockets']:
 c=Vector(sock['position']);hits=0;rays=0
 for iy in range(-10,11):
  for iz in range(-10,11):
   dy=iy*.0008;dz=iz*.0008
   if dy*dy+dz*dz>.008**2:continue
   origin=c+Vector((-.065,dy,dz));hit=tree.ray_cast(origin,Vector((1,0,0)),.13);rays+=1;hits+=hit[0] is not None
 checks.append({'socket':sock['name'],'bore_rays':rays,'obstructed_rays':hits})
report['pole_clearance_checks']=checks
assert all(c['obstructed_rays']==0 for c in checks),checks
# Re-import the actual delivered GLB, verify socket nodes and mesh contents.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(root/'public/assets/pepe-tripo-grip.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];report['glb_reimport']={'meshes':len(meshes),'polygons':sum(len(o.data.polygons) for o in meshes),'grip_sockets':[o.name for o in bpy.context.scene.objects if o.name.startswith('GripSocket_')],'gauge_meshes':len([o for o in meshes if o.name.startswith('Gauge_')])}
assert len(report['glb_reimport']['grip_sockets'])==2 and report['glb_reimport']['gauge_meshes']==0
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
