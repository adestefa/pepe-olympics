import bpy,bmesh,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];out=root/'output/pole-carry';report=json.loads((out/'report.json').read_text())
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in report['source_hashes'].items())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(root/'public/assets/pepe-pole-carry.glb'))
body=next(o for o in bpy.context.scene.objects if o.name=='Pepe_Posed_Carry');bm=bmesh.new();bm.from_mesh(body.data)
# GLB duplicates seam vertices; weld coincident vertices for topology inspection only.
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);tree=BVHTree.FromBMesh(bm)
axis=Vector(report['pole_axis']);start=Vector(report['pole_butt']);side=Vector((0,0,1)).cross(axis).normalized();up=axis.cross(side).normalized();hits=[];rays=0
for i in range(-8,9):
 for j in range(-8,9):
  a=i*.00097;b=j*.00097
  if a*a+b*b>.0078**2:continue
  origin=start+side*a+up*b;hit=tree.ray_cast(origin,axis,report['pole_length']);rays+=1
  if hit[0] is not None:hits.append(list(hit[0]))
report['validation']={'reimported_character_triangles':len(bm.faces),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'full_shaft_clearance_rays':rays,'obstructed_rays':len(hits),'hit_examples':hits[:3],'grip_socket_count':sum(o.name.startswith('GripSocket_') for o in bpy.context.scene.objects)}
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['validation'],indent=2));assert not hits,'Pole intersects character';assert report['validation']['nonmanifold_edges']==0
