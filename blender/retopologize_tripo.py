"""Rebuild a lower-density quad surface from the untouched original and bake its PBR detail.
Blender --background --python blender/retopologize_tripo.py
"""
import bpy, json, math, hashlib, time
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'muscular frog 3d model.glb'
OUT=ROOT/'output/model-optimization';TEX=OUT/'textures';TEX.mkdir(parents=True,exist_ok=True)
DEST=ROOT/'public/assets/pepe-tripo-retopo.glb';BLEND=ROOT/'blender/pepe-tripo-retopo.blend'
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest();start=time.time()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(SOURCE))
sources=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(sources)==1,'Expected one source mesh'
source=sources[0];source.name='Original_Tripo_Surface';source_triangles=sum(len(p.vertices)-2 for p in source.data.polygons)
source_materials=[m for m in source.data.materials]
lo=Vector((float('inf'),)*3);hi=Vector((float('-inf'),)*3)
for v in source.bound_box:
    w=source.matrix_world@Vector(v)
    for k in range(3):lo[k]=min(lo[k],w[k]);hi[k]=max(hi[k],w[k])
height=hi.z-lo.z;center=(lo+hi)/2
obj=source.copy();obj.data=source.data.copy();obj.name='Pepe_Tripo_Quad_Retopology';bpy.context.collection.objects.link(obj)
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
# GLB UV/normal seams can split coincident vertices. Weld only the working copy.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=height*.000001);bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
import numpy as np
edge_ids=np.empty(len(obj.data.loops),dtype=np.int32);obj.data.loops.foreach_get('edge_index',edge_ids);edge_uses=np.bincount(edge_ids,minlength=len(obj.data.edges));print('WORKING_COPY_EDGE_USES',int(np.sum(edge_uses==1)),int(np.sum(edge_uses>2)),flush=True)
# Blender rejects edges whose coordinate deltas are <=1e-4 as zero-length.
# Solve in millimeter-scale coordinates, then restore the source scale.
obj.data.transform(Matrix.Scale(1000,4));obj.data.update()
print('QUADRIFLOW_START',source_triangles,flush=True)
# Rebuild connectivity as quads, directly from the full-resolution original.
bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=False,use_preserve_sharp=False,use_preserve_boundary=True,preserve_attributes=False,smooth_normals=True,mode='FACES',target_faces=35000,seed=69)
quad_count=sum(len(p.vertices)==4 for p in obj.data.polygons)
if quad_count<10000:
    obj.data.transform(Matrix.Scale(.001,4));obj.data.update()
    print('REPAIRING_WORKING_COPY_FOR_QUAD_REMESH',flush=True)
    repair=obj.modifiers.new('Watertight working surface','REMESH');repair.mode='VOXEL';repair.voxel_size=height*.0012;repair.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=repair.name)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.transform(Matrix.Scale(1000,4));obj.data.update()
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.0002);bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
    print('REPAIRED_FACES',len(obj.data.polygons),flush=True)
    bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=False,use_preserve_sharp=False,use_preserve_boundary=True,preserve_attributes=False,smooth_normals=True,mode='FACES',target_faces=35000,seed=69)
    quad_count=sum(len(p.vertices)==4 for p in obj.data.polygons)
assert 10000<quad_count<100000,'Quad remeshing failed; target topology not produced'
obj.data.transform(Matrix.Scale(.001,4));obj.data.update()
print('QUADRIFLOW_DONE',len(obj.data.polygons),quad_count,'seconds',time.time()-start,flush=True)
# Project the new surface back to the source to retain silhouette, lips and fingers.
mod=obj.modifiers.new('Surface projection onto original','SHRINKWRAP');mod.target=source;mod.wrap_method='NEAREST_SURFACEPOINT';mod.wrap_mode='ON_SURFACE';mod.offset=0
bpy.ops.object.modifier_apply(modifier=mod.name)
for p in obj.data.polygons:p.use_smooth=True
obj.data.materials.clear();target_mat=bpy.data.materials.new('Pepe_Retopo_Baked_PBR');target_mat.use_nodes=True;obj.data.materials.append(target_mat)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.006,area_weight=.2,correct_aspect=True,scale_to_bounds=False);bpy.ops.object.mode_set(mode='OBJECT')
print('UV_UNWRAP_DONE',flush=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.bake.use_selected_to_active=True;scene.render.bake.use_clear=True;scene.render.bake.margin=12;scene.render.bake.cage_extrusion=height*.007;scene.render.bake.max_ray_distance=height*.015
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'retopo-checkpoint.blend'),compress=True)
texnode=target_mat.node_tree.nodes.new('ShaderNodeTexImage');images={}
def bake(name,kind,colorspace,passes=None):
    image=bpy.data.images.new(name,width=2048,height=2048,alpha=False);image.colorspace_settings.name=colorspace;image.generated_color=(.5,.5,1,1) if kind=='NORMAL' else (0,0,0,1)
    texnode.image=image;target_mat.node_tree.nodes.active=texnode;texnode.select=True
    bpy.ops.object.select_all(action='DESELECT');source.hide_set(False);source.hide_render=False;source.select_set(True);obj.select_set(True);bpy.context.view_layer.objects.active=obj
    print('BAKE_START',name,flush=True)
    kwargs={'type':kind}
    if passes is not None:kwargs['pass_filter']=passes
    bpy.ops.object.bake(**kwargs)
    image.filepath_raw=str(TEX/(name+'.png'));image.file_format='PNG';image.save();image.pack();images[name]=image
    print('BAKE_DONE',name,flush=True)
    return image
base=bake('pepe_basecolor_2k','DIFFUSE','sRGB',{'COLOR'})
normal=bake('pepe_normal_2k','NORMAL','Non-Color')
# Bake source roughness and metalness into GLTF's linear R=1, G=roughness, B=metalness map.
restore=[]
for material in source_materials:
    tree=material.node_tree;bsdf=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL');original=out.inputs['Surface'].links[0].from_socket
    combine=tree.nodes.new('ShaderNodeCombineColor');combine.mode='RGB';combine.inputs[0].default_value=1
    for key,index in [('Roughness',1),('Metallic',2)]:
        socket=bsdf.inputs[key]
        if socket.is_linked:tree.links.new(socket.links[0].from_socket,combine.inputs[index])
        else:combine.inputs[index].default_value=socket.default_value
    emit=tree.nodes.new('ShaderNodeEmission');tree.links.new(combine.outputs[0],emit.inputs['Color']);tree.links.new(emit.outputs[0],out.inputs['Surface']);restore.append((tree,out,original,combine,emit))
rm=bake('pepe_roughness_metallic_2k','EMIT','Non-Color')
for tree,out,original,combine,emit in restore:tree.links.new(original,out.inputs['Surface']);tree.nodes.remove(combine);tree.nodes.remove(emit)
# Final reusable PBR material on the new UV layout.
tree=target_mat.node_tree;tree.nodes.clear();out=tree.nodes.new('ShaderNodeOutputMaterial');bs=tree.nodes.new('ShaderNodeBsdfPrincipled');tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
for image,key in [(base,'Base Color'),(normal,'Normal'),(rm,'RM')]:
    n=tree.nodes.new('ShaderNodeTexImage');n.image=image;n.label=image.name
    if key=='Normal':
        convert=tree.nodes.new('ShaderNodeNormalMap');tree.links.new(n.outputs['Color'],convert.inputs['Color']);tree.links.new(convert.outputs['Normal'],bs.inputs['Normal'])
    elif key=='RM':
        sep=tree.nodes.new('ShaderNodeSeparateColor');sep.mode='RGB';tree.links.new(n.outputs['Color'],sep.inputs[0]);tree.links.new(sep.outputs[1],bs.inputs['Roughness']);tree.links.new(sep.outputs[2],bs.inputs['Metallic'])
    else:tree.links.new(n.outputs['Color'],bs.inputs[key])
source.hide_render=True;source.hide_set(True)
# Identical studio framing to the source render for visual comparison.
scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.22,.19,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.view_settings.view_transform='AgX'
def aim(o,p):o.rotation_euler=(p-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Comparison camera';scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=max(height,(hi.x-lo.x)*1.1)*1.18;cam.location=center+Vector((height*.20,-height*3,height*.10));aim(cam,center)
for name,offset,power,size in [('Key',(-2,-3,4),650,3),('Fill',(3,-2,1),300,3),('Rim',(1,3,3),800,2)]:
    bpy.ops.object.light_add(type='AREA',location=center+Vector(offset)*height/2);light=bpy.context.object;light.name=name;light.data.energy=power*(height/2)**2;light.data.shape='DISK';light.data.size=size*height/2;aim(light,center)
scene.render.filepath=str(OUT/'retopologized.png');bpy.ops.render.render(write_still=True)
# Save an actual mesh-edge wireframe preview of the retopology.
wire=obj.modifiers.new('Retopology wire preview','WIREFRAME');wire.thickness=height*.00035;wire.use_replace=False;wire.offset=1
wiremat=bpy.data.materials.new('Wire charcoal');wiremat.diffuse_color=(.005,.012,.008,1);obj.data.materials.append(wiremat);wire.material_offset=1
scene.render.filepath=str(OUT/'retopology-wire.png');bpy.ops.render.render(write_still=True);obj.modifiers.remove(wire);obj.data.materials.pop(index=1)
# GLB triangulates for rendering; .blend retains the editable quad topology.
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str(DEST),export_format='GLB',use_selection=True,export_animations=False,export_apply=True,export_image_format='AUTO',export_unused_images=False)
triangles=sum(len(p.vertices)-2 for p in obj.data.polygons)
bpy.data.objects.remove(source,do_unlink=True);bpy.ops.outliner.orphans_purge(do_recursive=True)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_distance=height*2;area.spaces.active.region_3d.view_location=center
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),compress=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
report={'method':'QuadriFlow quad retopology directly from original, shrinkwrap projection, new UVs and selected-to-active PBR baking','source':str(SOURCE.relative_to(ROOT)),'source_sha256':source_hash,'original_unchanged':True,'source_triangles':source_triangles,'retopo_faces':len(obj.data.polygons),'retopo_quads':quad_count,'render_triangles':triangles,'source_bytes':SOURCE.stat().st_size,'optimized_bytes':DEST.stat().st_size,'glb':str(DEST.relative_to(ROOT)),'blend':str(BLEND.relative_to(ROOT)),'textures':{'basecolor':[2048,2048],'normal':[2048,2048],'roughness_metallic':[2048,2048]},'elapsed_seconds':round(time.time()-start,1),'limitations':['Automatic quad retopology, not hand-authored animation edge loops.','Original flexing pose retained; model still requires rigging and joint deformation checks before gameplay.','Current game character is unchanged.']}
(OUT/'retopology-report.json').write_text(json.dumps(report,indent=2)+'\n');print('RETOPOLOGY_COMPLETE',json.dumps(report),flush=True)
