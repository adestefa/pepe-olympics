"""Build pole-grip hands on a NEW copy of the retopologized Pepe.
Original GLB and retopology files are read-only inputs. No game integration.
Run: Blender --background --python blender/create_grip_hands.py
"""
import bpy, bmesh, math, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/hand-grips';OUT.mkdir(parents=True,exist_ok=True)
INPUTS=[ROOT/'muscular frog 3d model.glb',ROOT/'blender/pepe-tripo-retopo.blend',ROOT/'public/assets/pepe-tripo-retopo.glb']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
bpy.ops.wm.open_mainfile(filepath=str(INPUTS[1]))
body=bpy.data.objects['Pepe_Tripo_Quad_Retopology'];body.name='Pepe_Retopo_Pole_Grip_Copy';body.data=body.data.copy()
scene=bpy.context.scene
# Sample the retained wrist colors from the original baked UV map.
base=bpy.data.images['pepe_basecolor_2k'];pixels=list(base.pixels);uvs=body.data.uv_layers.active.data
colors=[]
for poly in body.data.polygons:
    c=poly.center
    if (c.x<-.22 and .875<c.z<.895) or (c.x>.23 and .74<c.z<.755):
        for li in poly.loop_indices:
            uv=uvs[li].uv;x=min(base.size[0]-1,max(0,int(uv.x*base.size[0])));y=min(base.size[1]-1,max(0,int(uv.y*base.size[1])));idx=(y*base.size[0]+x)*4;colors.append(pixels[idx:idx+3])
import statistics
color=[statistics.median(c[k] for c in colors) for k in range(3)]
# Pixel access returns the encoded sRGB values for the packed base-color image.
color=[((c+.055)/1.055)**2.4 if c>.04045 else c/12.92 for c in color]
mat=bpy.data.materials.new('Grip_skin_matched_to_original_wrist');mat.diffuse_color=(*color,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.39
print('WRIST_COLOR_LINEAR',color,flush=True)

def activate(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def sphere(name,center,scale,parts):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=center)
    o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);parts.append(o)

def tube(name,points,radii,parts):
    # Cross sections perpendicular to the centerline; rounded caps via spheres.
    vs=[];fs=[];N=12
    for i,p in enumerate(points):
        tangent=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized()
        a=tangent.cross(Vector((1,0,0)))
        if a.length<.01:a=tangent.cross(Vector((0,1,0)))
        a.normalize();b=tangent.cross(a).normalized()
        for j in range(N):vs.append(Vector(p)+radii[i]*(a*math.cos(j*math.tau/N)+b*math.sin(j*math.tau/N)))
    for i in range(len(points)-1):
        for j in range(N):a=i*N+j;b=i*N+(j+1)%N;fs.append((a,b,b+N,a+N))
    fs.extend([tuple(reversed(range(N))),tuple((len(points)-1)*N+j for j in range(N))])
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);parts.append(o)
    sphere(name+'_tip',points[-1],(radii[-1],)*3,parts)

# Cut only distal hands. Every retained body vertex and UV remains as authored.
def cut_body(side,z):
    bm=bmesh.new();bm.from_mesh(body.data)
    geom=[v for v in bm.verts if v.co.x*side>.18]
    geom+= [e for e in bm.edges if all(v.co.x*side>.18 for v in e.verts)]
    geom+= [f for f in bm.faces if all(v.co.x*side>.18 for v in f.verts)]
    bmesh.ops.bisect_plane(bm,geom=geom,dist=.0000001,plane_co=(0,0,z),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
    boundary=[v for v in bm.verts if v.co.x*side>.18 and abs(v.co.z-z)<.000001 and any(e.is_boundary for e in v.link_edges)]
    coords=[v.co.copy() for v in boundary]
    center=sum(coords,Vector())/len(coords)
    bm.to_mesh(body.data);bm.free();body.data.update()
    return center,coords

def check(stage):
    q=bmesh.new();q.from_mesh(body.data);print('TOPOLOGY_STAGE',stage,len(q.faces),sum(not e.is_manifold for e in q.edges),flush=True);q.free()

sockets=[]
for label,side,z in [('Right',-1,.894),('Left',1,.754)]:
    center,boundary=cut_body(side,z)
    check('cut '+label)
    rx=(max(v.x for v in boundary)-min(v.x for v in boundary))/2
    ry=(max(v.y for v in boundary)-min(v.y for v in boundary))/2
    print('WRIST',label,list(center),rx,ry,len(boundary),flush=True)
    # Local X = pole axis, +Y = palm side, +Z = fingers away from wrist.
    # Palm faces forward; mirrored thumb sits on the anatomical inner side.
    parts=[]
    sphere(label+'_wrist',(0,0,.007),(rx,ry,.018),parts)
    sphere(label+'_palm',(0,-.002,.018),(.019,.010,.017),parts)
    for i,x in enumerate([-.0144,-.0048,.0048,.0144]):
        # Shallow knuckle and joint bulges, four individually separated fingers.
        points=[];radii=[]
        for j in range(21):
            t=j/20;theta=t*math.radians(267)
            points.append((x,.014-.014*math.cos(theta),.028+.014*math.sin(theta)))
            radii.append((.00435 if i in [0,3] else .00455)*(1-.15*t)*(1+.055*math.cos(t*math.pi*6)))
        tube(label+'_finger_'+str(i),points,radii,parts)
    # Opposed thumb curls diagonally across the fingers on the palm side.
    h=-side
    points=[(h*.015,0,.013),(h*.022,.005,.015),(h*.025,.014,.015),(h*.023,.024,.018),(h*.018,.032,.021),(h*.010,.032,.024)]
    tube(label+'_thumb',points,[.008,.007,.0062,.0055,.005,.0045],parts)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:p.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();hand=bpy.context.object;hand.name=label+'_grip_working'
    # Work in world local coordinates before surface union.
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    rem=hand.modifiers.new('Unify palm and finger roots','REMESH');rem.mode='VOXEL';rem.voxel_size=.00065;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
    smooth=hand.modifiers.new('Soften hand surface','SMOOTH');smooth.factor=.55;smooth.iterations=3;bpy.ops.object.modifier_apply(modifier=smooth.name)
    hand.data.transform(Matrix.Scale(1000,4));hand.data.update()
    bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=False,use_preserve_sharp=False,use_preserve_boundary=True,preserve_attributes=False,smooth_normals=True,mode='FACES',target_faces=1800,seed=42)
    hand.data.transform(Matrix.Scale(.001,4));hand.data.update()
    # QuadriFlow may collapse a tiny knuckle face; close only those small holes
    # before opening the wrist, so they cannot be mistaken for wrist loops.
    repair=bmesh.new();repair.from_mesh(hand.data)
    tiny_edges=[e for e in repair.edges if e.is_boundary]
    if tiny_edges:bmesh.ops.holes_fill(repair,edges=tiny_edges,sides=8)
    bmesh.ops.recalc_face_normals(repair,faces=list(repair.faces))
    assert all(e.is_manifold for e in repair.edges),'Hand remesh must be closed before wrist cut'
    repair.to_mesh(hand.data);repair.free()
    refine=hand.modifiers.new('Smooth finger curvature','SUBSURF');refine.levels=1;refine.render_levels=1;bpy.ops.object.modifier_apply(modifier=refine.name)
    q=bmesh.new();q.from_mesh(hand.data);print('HAND_CLOSED',label,len(q.faces),sum(not e.is_manifold for e in q.edges),flush=True);q.free()
    # Wrist connection in a short transition band above the original cut.
    bm=bmesh.new();bm.from_mesh(hand.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,.004),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
    bm.to_mesh(hand.data);bm.free()
    # Rotate 180° around Z so palm opens toward camera (-Y), then mirror X
    # as needed in the thumb construction above. This is a proper rotation.
    for v in hand.data.vertices:
        v.co=Vector((-v.co.x,-v.co.y,v.co.z))+center
    hand.data.materials.clear();hand.data.materials.append(mat)
    q=bmesh.new();q.from_mesh(hand.data);print('HAND_OPEN',label,len(q.faces),sum(e.is_boundary for e in q.edges),sum(len(e.link_faces)>2 for e in q.edges),flush=True);q.free()
    # Add body and hand to one mesh and stitch the two open wrist rings.
    activate(body);hand.select_set(True);bpy.ops.object.join()
    bm=bmesh.new();bm.from_mesh(body.data)
    edges=[e for e in bm.edges if e.is_boundary and all(v.co.x*side>.18 for v in e.verts)]
    assert len(edges)>16
    result=bmesh.ops.bridge_loops(bm,edges=edges,use_pairs=False)
    for face in result['faces']:face.material_index=1;face.smooth=True
    # Relax just the wrist join, leaving the retained forearm/body unchanged.
    for iteration in range(10):
        updates={}
        for v in bm.verts:
            if v.co.x*side>.18 and z-.004<v.co.z<z+.009:
                weight=math.sin(math.pi*(v.co.z-(z-.004))/.013)**2*.4
                neighbors=[e.other_vert(v).co for e in v.link_edges]
                if neighbors:updates[v]=v.co.lerp(sum(neighbors,Vector())/len(neighbors),weight)
        for v,co in updates.items():v.co=co
    # Maintain an actual bore through the palm around the test pole.
    for v in bm.verts:
        if v.co.x*side>.18 and v.co.z>z+.008:
            dy=v.co.y-(center.y-.014);dz=v.co.z-(center.z+.028);r=math.hypot(dy,dz)
            if 0<r<.0088:
                v.co.y=center.y-.014+dy*.0088/r;v.co.z=center.z+.028+dz*.0088/r
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()
    check('stitched '+label)
    sockets.append({'name':'GripSocket_'+label,'position':list(center+Vector((0,-.014,.028))),'pole_axis':[1,0,0],'pole_radius':.008,'wrist_cut_z':z})

for p in body.data.polygons:p.use_smooth=True
# Helpful attachment frames and removable gauge cylinders. Gauges excluded from game export.
helpers=bpy.data.collections.new('GRIP_REFERENCE_POLES__not_exported');scene.collection.children.link(helpers)
polemat=bpy.data.materials.new('Pole grip check');polemat.diffuse_color=(.82,.49,.095,1);polemat.use_nodes=True;polemat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.82,.49,.095,1);polemat.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value=.5;polemat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.25
for sock in sockets:
    empty=bpy.data.objects.new(sock['name'],None);bpy.context.collection.objects.link(empty);empty.location=sock['position'];empty.empty_display_type='ARROWS';empty.empty_display_size=.018;empty['pole_axis']='local +X';empty['pole_radius']=.008;empty.parent=body
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.008,depth=.115,location=sock['position'],rotation=(0,math.pi/2,0));p=bpy.context.object;p.name='Gauge_'+sock['name'];p.data.materials.append(polemat)
    for col in list(p.users_collection):col.objects.unlink(p)
    helpers.objects.link(p)
    bevel=p.modifiers.new('Soft pole ends','BEVEL');bevel.width=.0006;bevel.segments=3
    for face in p.data.polygons:face.use_smooth=True

activate(body)
final_check=bmesh.new();final_check.from_mesh(body.data)
assert all(e.is_manifold and e.is_contiguous for e in final_check.edges), 'Cannot export invalid topology'
final_check.free()
for sock in sockets:bpy.data.objects[sock['name']].select_set(True)
body['asset_notes']='Copied retopology, custom closed grip hands, retained body UVs. Original flex pose; no rig or baked animation. Pole gauges excluded from GLB.'
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/pepe-tripo-grip.glb'),export_format='GLB',use_selection=True,export_animations=False,export_apply=True,export_image_format='AUTO',export_extras=True)
check('exported')
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.cycles.samples=24;scene.cycles.use_denoising=True
cam=scene.camera
# Whole model first, with reference cylinders.
scene.render.resolution_x=1000;scene.render.resolution_y=1100
cam.data.type='ORTHO';cam.data.ortho_scale=1.14;cam.location=(.19,-2.9,.59);target=Vector((0,0,.49));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(OUT/'grip-full.png');bpy.ops.render.render(write_still=True)
for sock in sockets:
    target=Vector(sock['position'])+Vector((0,0,-.012));cam.data.ortho_scale=.14;cam.location=target+Vector((.10,-.22,.105));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=1100;scene.render.resolution_y=900;scene.render.filepath=str(OUT/(sock['name']+'.png'));bpy.ops.render.render(write_still=True)
# Save with full-character framing and reference poles visible for editing.
cam.data.ortho_scale=1.14;cam.location=(.19,-2.9,.59);target=Vector((0,0,.49));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=1000;scene.render.resolution_y=1100
activate(body)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/pepe-tripo-grip.blend'),compress=True)
bm=bmesh.new();bm.from_mesh(body.data)
report={'source_hashes':hashes,'sources_unchanged':all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))] for p in INPUTS),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),'triangles':sum(len(f.verts)-2 for f in bm.faces),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'inconsistent_edges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'sockets':sockets,'notes':'Custom curled fingers and opposed thumbs, wrist surfaces stitched to retained original quad body. Arm flex pose preserved. No skinning yet. Separate gauge poles only in Blender.'};bm.free()
(OUT/'report.json').write_text(json.dumps(report,indent=2));print('GRIP_REPORT',json.dumps(report),flush=True)
assert report['sources_unchanged'] and report['nonmanifold_edges']==0 and report['inconsistent_edges']==0
