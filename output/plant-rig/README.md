# Pepe: carry, plant and inverted swing

Open `http://127.0.0.1:5189/output/plant-rig/index.html` with the Vite development server running. Drag to orbit, scrub the timeline, choose a stage, or press P to pause. The Hands view centers on the rear/right hand at the currently selected pose.

This is an editable Blender motion study based on the supplied plant and takeoff images. It corrects the rear/right grip direction, keeps both hands attached, and demonstrates the pole bending with its tip fixed in the plant box. The game now imports this rig and lets D/L, H, Space, J and K control its motion. Release and failure switch the character to a physical ragdoll.

## Assets

- `blender/pepe-plant-rig.blend`: copied character with 27 bones, shoulder/hip corrective shapes, joint edit guards, timeline markers, and a 21-bone pole rig.
- `public/assets/pepe-plant-animated.glb`: both skins and the `PolePlant_ReferenceStudy` clip, 30 fps, 217 Blender frames, 7.2 seconds.
- `public/assets/pepe-carry-ready.glb`: evaluated static meshes at frame 1.
- `public/assets/pepe-plant-ready.glb`: evaluated static meshes at frame 73.
- `public/assets/pepe-takeoff-ready.glb`: evaluated static meshes at frame 121, including the bent pole.
- `public/assets/pepe-inverted-ready.glb`: evaluated static meshes at frame 193, feet above head.
- `public/assets/pepe-joint-limits.json`: initial game-tuning joint bounds and bind information.
- `src/joint-limits.js`: quaternion clamp helper for a future bone/physics controller; available for future active joint motors. The current game ragdoll has its own Cannon constraint bounds.

All earlier retopology, hand-grip and carry assets remain intact. Their hashes are recorded in `report.json` and checked by the audit.

## Blender editing

The timeline marks Carry (1), Raise (25), Extend (49), Plant (73), and Loaded takeoff (121), Swing (145), Rock back (169), and Inverted (193), followed by a hold through frame 217. The frog faces Blender -Y with Z up. GLB converts the scene to Y up. The study stays in place during the approach steps; it includes swing-up and inversion but not release or landing; the game handles those with physics.

Select **Pepe_Plant_Rig**, enter Pose Mode, and adjust its keyed bones. Wrist, elbow and knee Limit Rotation constraints are enabled as edit guards. The forearm twist bones let palm rotation occur along the forearm rather than by sharply bending the wrist. The nearby `*_swing` bones and shoulder-cap bones distribute deformation without winding the shoulder twice. The mesh keeps its original bind; no deformed carry mesh is baked into a second bind. Seven keyed corrective shapes soften those joint seams.

The hands are spaced 0.195 source units along the pole. The right hand is the rear/top grip, with its thumb direction reversed from the prior carry asset. `GripSocket_Right` and `GripSocket_Left` follow the straight grip section. Edit the hand targets and pole together to preserve contact; the animation is sampled FK, not a live hand-target IK setup.

The pole is 1.95 source units long, with its first 0.34 units straight. Beyond the grips, a constant-length circular arc bends progressively to about 54 degrees. From frame 73 onward the endpoint is fixed at the plant box. The 21 pole bones approximate the smooth curve without stretching the pole's centerline. This is an authored deformation reference, not a Blender rigid-body spring simulation. At runtime, the same skin can be driven by a physical pole chain.

To regenerate the study and check its evaluated mesh:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python blender/build_plant_rig.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python blender/audit_plant_rig.py
node --test src/joint-limits.test.js
```

`plant_motion.py` contains target poses, pole geometry and the arm solver. `pole_flex.py` builds and keys the flexible shaft. `build_plant_rig.py` skins the copied mesh, generates the clip, exports poses, and renders the review images.

## Runtime joint limits

GLB carries skinning and animation; it does not enforce Blender constraints. Feed a **bone-local quaternion delta from its bind orientation** to `constrainJointRotation`. Elbow/knee bends use `bind_bend_degrees`; axial ranges use `neutral_twist_from_bind_degrees` to handle quaternion wrapping. Shoulder and ankle envelopes are centered on the reviewed motion so switching to the limits does not snap the pose. The sidecar's bind matrices use Blender model coordinates; do not treat them as Three.js world matrices without converting the scene axes.

For an actual ragdoll, apply these limits to the physics constraints/motors. Do not clamp rendered bones independently of their physical bodies. `physics_parent` identifies the intended hierarchy when deformation-only swing helper bones are omitted. These are initial gameplay bounds, not anatomical measurements. They can be tightened after checking the athlete's full vault and crash motion.

## Verification

`audit.json` records every Blender frame: wrist bend, hand/socket drift, planted-tip drift, shaft/body intersection sampling, ground clearance and per-frame joint rotation. The source files are hash-checked. Browser checks validate the exported skins, playback, frame selection and pause behavior. The latest renders show the actual evaluated rig, including the corrected grip and bent pole.

The current exhaustive shaft/body check still finds rockback intersections at frames 169–183; see `geometry-status.md`. Grip, anchor and rotation-continuity checks pass.
