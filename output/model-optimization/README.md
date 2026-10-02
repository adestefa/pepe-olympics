# Tripo frog retopology

The source is `muscular frog 3d model.glb` at the project root. The original is read-only throughout this workflow.

The final workflow is `blender/retopologize_tripo.py`:

1. Copy the original mesh and weld coincident import seams on the working copy.
2. Normalize the working coordinate scale for Blender's short-edge tolerance.
3. Rebuild connectivity with QuadriFlow, targeting 35,000 quads. This is a new quad surface, not triangle-collapse decimation.
4. Restore the original scale and project the new surface onto the original.
5. Create a new UV layout and bake 2K base color, tangent-space normals, and packed roughness/metalness from the full-resolution source.
6. Save editable quads in `blender/pepe-tripo-retopo.blend`; export the triangulated rendering version to `public/assets/pepe-tripo-retopo.glb`.

`retopology-report.json` contains the final measured counts, file sizes and original checksum. `compare.html` displays matching source/result renders and the actual quad wireframe.

This is automatic quad retopology. It is not a claim of hand-authored deformation loops. The supplied flexing pose is retained; rigging, joint weights and deformation checks are a separate step before replacing the live game character.

`superseded/` holds the abandoned decimation experiment. Those files are not the requested retopology deliverable and are not used by the game. Diagnostic scripts and checkpoints remain here only for reproducibility; the final exported GLB is self-contained.
