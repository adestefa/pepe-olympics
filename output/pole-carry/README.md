# Full pole and carry pose

Outputs:
- `blender/pepe-pole-carry.blend`: separate editable scene with a seven-bone torso/arm rig and posed hands.
- `public/assets/pepe-pole-carry.glb`: evaluated static character + separate pole objects, no baked animation.
- `public/assets/vault-pole.glb`: reusable pole with local +Y from butt to planting tip.
- `output/pole-carry/index.html`: orbitable asset preview and closeups.

The pole has a tapered fiberglass shaft, dark grip wrap, spiral tape seam, lime shaft markers, and a rubber planting plug. Its nominal source length is 1.95 and radius 0.0078; game scale is 5.58 / 1.95. The shaft has 96 axial divisions so skinning can follow bending physics.

`src/pole-visual.js` loads the standalone asset, scales it, reverses its length axis to match the game's tip-first section ordering, and skins it to the existing nine Cannon physics bodies. The new pole is live in the game. The new high-detail character is currently the Blender/GLB carry asset; the running game still uses the existing physics character. The carry rig covers the arms only, not a complete physics-ready character skeleton. Grip socket empties mark the delivered pose; they are static markers and must be updated if the arm pose is edited.

Rebuild with Blender `--background --python-exit-code 1 --python blender/build_pole_carry.py`.
Validate with Blender `--background --python-exit-code 1 --python blender/verify_pole_carry.py`.
Original hand-edit Blender and GLB files are preserved and checked by SHA-256.
