"""Skinned constant-length pole; straight grip section and an anchored bending shaft."""
import bpy, math
from mathutils import Vector, Matrix, Quaternion
from plant_motion import POLE_LENGTH, BEND_START, pole_curve

def build_flex_rig(root, scene, count=21):
    bpy.context.view_layer.update()
    inverse = root.matrix_world.inverted()
    pieces = [o for o in root.children_recursive if o.type == 'MESH']
    transforms = {o: inverse @ o.matrix_world for o in pieces}
    bpy.ops.object.select_all(action='DESELECT')
    for o in pieces:
        o.parent = None
        o.matrix_world = transforms[o]
        o.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    mesh = bpy.context.object
    mesh.name = 'VaultPole_FlexibleShaft'
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    root.matrix_world = Matrix.Identity(4)
    data = bpy.data.armatures.new('VaultPole_FlexRig')
    rig = bpy.data.objects.new('VaultPole_FlexRig', data)
    scene.collection.objects.link(rig)
    rig.parent = root
    mesh.parent = rig
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    stations = [POLE_LENGTH * i / (count - 1) for i in range(count)]
    for i, s in enumerate(stations):
        b = data.edit_bones.new(f'PoleFlex_{i:02d}')
        b.head = (0, 0, s)
        b.tail = (0, 0, s + .04)
    bpy.ops.object.mode_set(mode='OBJECT')
    binds = [b.matrix_local.copy() for b in data.bones]
    groups = [mesh.vertex_groups.new(name=b.name) for b in data.bones]
    for v in mesh.data.vertices:
        t = max(0, min(count - 1, v.co.z / POLE_LENGTH * (count - 1)))
        lo = min(count - 2, int(t))
        f = t - lo
        if f < 1: groups[lo].add([v.index], 1 - f, 'REPLACE')
        if f > 0: groups[lo + 1].add([v.index], f, 'REPLACE')
    modifier = mesh.modifiers.new('Pole flex skin', 'ARMATURE')
    modifier.object = rig
    rig.show_in_front = True
    for b in rig.pose.bones: b.rotation_mode = 'QUATERNION'
    rig['shaft_arc_length'] = POLE_LENGTH
    rig['straight_grip_length'] = BEND_START
    rig['note'] = 'Authored bend study. Runtime physics can drive these bones; the GLB itself is not a spring simulation.'
    return rig, mesh, stations, binds

def key_bend(rig, stations, binds, bend, frame):
    for b, s, bind in zip(rig.pose.bones, stations, binds):
        angle = bend * max(0, s - BEND_START) / (POLE_LENGTH - BEND_START)
        q = Quaternion((0, 1, 0), angle)
        b.matrix = Matrix.Translation(pole_curve(s, bend)) @ q.to_matrix().to_4x4() @ Matrix.Translation(Vector((0, 0, -s))) @ bind
        b.keyframe_insert('location', frame=frame, group=b.name)
        b.keyframe_insert('rotation_quaternion', frame=frame, group=b.name)

def make_box(scene, anchor):
    material = bpy.data.materials.new('Plant box • recessed steel')
    material.diffuse_color = (.12, .17, .15, 1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=anchor + Vector((0, 0, -.008)))
    box = bpy.context.object
    box.name = 'PlantBox_Anchor'
    box.dimensions = (.09, .12, .017)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    box.data.materials.append(material)
    bevel = box.modifiers.new('Soft steel edge', 'BEVEL')
    bevel.width = .003
    bevel.segments = 3
    box['pole_tip_anchor'] = list(anchor)
    return box
