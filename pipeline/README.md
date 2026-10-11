# Pipeline: 3D model → virtual tour

Converts a developer's 3D file into a web tour: a compressed model for the 3D viewer, 360°
panoramas from auto-placed viewpoints (roughly one per room, linked through doorways), an aerial
360° and exterior stills. The output is served by the `/tour/[id]` page.

## Run (on the GPU machine)

Tested with Blender 5.2 (use a recent release). Rendering uses Cycles on the GPU (OptiX on RTX cards)
when available.

```bash
# Optional: build a test apartment to try the pipeline
blender -b -P pipeline/blender/make_test_apartment.py -- --output test_apartment.glb

# Process a model; output goes straight into the site's public folder
blender -b -P pipeline/blender/process_model.py -- \
  --input test_apartment.glb --output public/tours/my-project
```

Then open `http://localhost:3000/tour/my-project` (tour ids: lowercase letters, digits, `-`).

On Windows, use the full path to Blender, e.g.
`"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P ...`.

Useful options (`--help` for all):

| Option | Default | Notes |
| --- | --- | --- |
| `--pano-width` | 4096 | 360° image width; height is half. 8192 for top quality |
| `--samples` | 128 | Cycles samples (denoised). Lower = faster, noisier |
| `--max-views` | 12 | Cap on interior viewpoints |
| `--unit-scale` | auto | Force scale to metres, e.g. `0.001` for a model in mm |
| `--device` | auto | `gpu` to fail rather than fall back to CPU |
| `--no-stills` / `--no-aerial` | | Skip exterior renders |

Supported inputs: GLB/GLTF (preferred), FBX, OBJ, USD/USDZ, STL, PLY, `.blend`. SketchUp,
3ds Max and Revit files need exporting to FBX/GLB first.

## How viewpoints are chosen

1. The model is sampled on a ~0.5 m grid; every upward-facing surface is a possible floor.
2. A point is kept if it stands on a floor with nothing up to eye height (1.6 m), has a ceiling
   above and is enclosed by walls in all directions.
3. Small patches (bed/table tops) are dropped, as are levels much smaller than the main floor.
4. A greedy visibility cover picks the fewest points that together see ~95% of the interior,
   each re-centred towards the middle of the area it covers.
5. Viewpoints are linked when they can see each other, or via a point in front of the doorway
   between two adjacent rooms.

## Known limits

- Models with no materials render grey/white; there is no automatic material enhancement yet.
- Fill lights are added at each viewpoint; models with their own lighting may look brighter.
- Exterior-only models (no ceilings) produce no interior viewpoints, only aerial/stills.
- Stairs aren't linked between floors yet.
