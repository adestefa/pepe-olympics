# Pole-grip copy

- Editable asset: `blender/pepe-tripo-grip.blend`
- Browser asset: `public/assets/pepe-tripo-grip.glb`
- Interactive preview: http://127.0.0.1:5189/output/hand-grips/index.html
- Rebuild: Blender in background with `--python-exit-code 1 --python blender/create_grip_hands.py`
- Verify: Blender in background with `--python-exit-code 1 --python blender/verify_grip_hands.py`

Both distal hands were replaced with modeled palms, four curled fingers, and opposed thumbs. The hand surfaces were remeshed into quads, locally subdivided for smooth curves, and stitched to the retained wrist loops. A narrow wrist band is relaxed; the remaining body, UVs, and baked materials are retained. New skin material is sampled from the original wrists. The final Blender surface has 40,167 faces and exports to 80,088 triangles.

The Blender collection `GRIP_REFERENCE_POLES__not_exported` contains removable fitting cylinders. Their radius is 0.008 in this approximately one-unit-tall asset. Empty nodes `GripSocket_Left` and `GripSocket_Right` are included in the GLB, with local +X along the pole axis. Blender uses Z up; the exported GLB uses Y up. Match pole dimensions to model scale when integrating.

This is a hand geometry edit. The original flexing arm pose remains; there is no skeleton, skin weighting, or animation yet. Placing both grips on a single pole requires a later arm rig/pose integration step. The running game has not been switched to this asset.

Validation: closed consistently oriented mesh, 309 bore rays per hand with no obstructions at pole radius, GLB reimport with two sockets and no gauge meshes. Original Tripo GLB and both prior retopology assets retain their SHA-256 checksums. Full details are in `report.json`.
