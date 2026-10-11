"""Turn a developer's 3D model into a web-ready virtual tour.

Input: one 3D file (GLB/GLTF, FBX, OBJ, USD, STL, PLY or .blend).
Output directory:
    model.glb         compressed model for the in-browser 3D viewer
    panos/<id>.jpg    equirectangular 360 renders from auto-placed viewpoints
    stills/<id>.jpg   exterior hero shots
    manifest.json     viewpoints, links between them (for hotspots) and metadata

Run with Blender in background mode:
    blender -b -P pipeline/blender/process_model.py -- --input villa.fbx --output out/villa
or with the `bpy` Python module:
    python pipeline/blender/process_model.py --input villa.fbx --output out/villa

Viewpoints are found automatically: the model is sampled on a grid, points that stand on a floor
under a ceiling and are enclosed by walls are kept, and a greedy visibility cover picks the few
points that together see most of the interior (roughly one per room).
"""

import argparse
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

EYE_HEIGHT = 1.6
H_DIRS = [Vector((math.cos(a), math.sin(a), 0.0)) for a in (i * math.pi / 4 for i in range(8))]


def log(msg):
    print(f"[process_model] {msg}", flush=True)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--max-views", type=int, default=12, help="maximum number of interior 360 viewpoints")
    p.add_argument("--coverage", type=float, default=0.95, help="stop adding viewpoints at this share of interior seen")
    p.add_argument("--pano-width", type=int, default=4096, help="360 image width (height is half)")
    p.add_argument("--still-width", type=int, default=1920)
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--device", choices=["auto", "gpu", "cpu"], default="auto")
    p.add_argument("--unit-scale", type=float, default=0.0, help="scale to metres; 0 = auto-detect")
    p.add_argument("--grid", type=float, default=0.0, help="viewpoint search grid spacing in metres; 0 = auto")
    p.add_argument("--no-stills", action="store_true")
    p.add_argument("--no-aerial", action="store_true")
    p.add_argument("--no-interior-lights", action="store_true", help="don't add fill lights at viewpoints")
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Import & normalise
# ---------------------------------------------------------------------------

def import_model(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=path)
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    importers = {
        ".glb": lambda: bpy.ops.import_scene.gltf(filepath=path),
        ".gltf": lambda: bpy.ops.import_scene.gltf(filepath=path),
        ".fbx": lambda: bpy.ops.import_scene.fbx(filepath=path),
        ".obj": lambda: bpy.ops.wm.obj_import(filepath=path),
        ".stl": lambda: bpy.ops.wm.stl_import(filepath=path),
        ".ply": lambda: bpy.ops.wm.ply_import(filepath=path),
        ".usd": lambda: bpy.ops.wm.usd_import(filepath=path),
        ".usda": lambda: bpy.ops.wm.usd_import(filepath=path),
        ".usdc": lambda: bpy.ops.wm.usd_import(filepath=path),
        ".usdz": lambda: bpy.ops.wm.usd_import(filepath=path),
    }
    if ext not in importers:
        raise SystemExit(f"Unsupported format '{ext}'. Supported: {', '.join(sorted(importers))}, .blend")
    importers[ext]()


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH" and o.visible_get()]


def world_bounds(objs):
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for o in objs:
        for corner in o.bound_box:
            w = o.matrix_world @ Vector(corner)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def focus_objects(objs):
    """Drop ground/terrain planes: flat objects covering most of the footprint. They would
    otherwise inflate the bounds used for the viewpoint grid and camera framing."""
    lo, hi = world_bounds(objs)
    footprint = max((hi.x - lo.x) * (hi.y - lo.y), 1e-6)
    keep = []
    for o in objs:
        olo, ohi = world_bounds([o])
        flat = (ohi.z - olo.z) < 0.5
        if not (flat and (ohi.x - olo.x) * (ohi.y - olo.y) > 0.5 * footprint):
            keep.append(o)
    return keep or objs


def normalise_units(unit_scale):
    lo, hi = world_bounds(mesh_objects())
    size = max(hi - lo)
    if unit_scale <= 0:
        # A building is not kilometres across: anything that big was modelled in millimetres
        # (common for CAD/Revit exports) or centimetres.
        unit_scale = 0.001 if size > 5000 else 0.01 if size > 1500 else 1.0
    if unit_scale != 1.0:
        log(f"scaling model by {unit_scale} (raw size {size:.1f})")
        for o in bpy.context.scene.objects:
            if o.parent is None:
                o.location *= unit_scale
                o.scale *= unit_scale
        bpy.context.view_layer.update()
    return unit_scale


def build_bvh(objs):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in objs:
        ev = o.evaluated_get(depsgraph)
        mesh = ev.to_mesh()
        offset = len(verts)
        mw = o.matrix_world
        verts.extend(mw @ v.co for v in mesh.vertices)
        polys.extend([offset + i for i in p.vertices] for p in mesh.polygons)
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)


# ---------------------------------------------------------------------------
# Viewpoint search
# ---------------------------------------------------------------------------

def hit_distance(bvh, origin, direction, max_dist):
    loc, _normal, _idx, dist = bvh.ray_cast(origin, direction, max_dist)
    return dist if loc is not None else None


def find_floor_hits(bvh, lo, hi, step):
    """All upward-facing surfaces under each grid column: (x, y, z) per hit."""
    hits = []
    top = hi.z + 1.0
    down = Vector((0, 0, -1))
    nx = int((hi.x - lo.x) / step)
    ny = int((hi.y - lo.y) / step)
    for i in range(nx + 1):
        for j in range(ny + 1):
            origin = Vector((lo.x + i * step + step / 2, lo.y + j * step + step / 2, top))
            remaining = top - lo.z + 1.0
            while remaining > 0:
                loc, normal, _idx, dist = bvh.ray_cast(origin, down, remaining)
                if loc is None:
                    break
                if normal.z > 0.7:
                    hits.append((origin.x, origin.y, loc.z, i, j))
                origin = loc + down * 0.02
                remaining -= dist + 0.02
    return hits


def floor_levels(cands):
    """Cluster candidate floor heights; keep only levels with a large area (real floors, not bed
    or table tops). Done after the interior test so an outdoor ground plane doesn't dominate."""
    buckets = {}
    for c in cands:
        buckets.setdefault(round(c["floor"] * 10), []).append(c)
    # Merge neighbouring 10 cm buckets into levels
    levels = []
    for key in sorted(buckets):
        if levels and key - levels[-1]["last"] <= 1:
            levels[-1]["hits"].extend(buckets[key])
            levels[-1]["last"] = key
        else:
            levels.append({"hits": list(buckets[key]), "last": key})
    largest = max((len(l["hits"]) for l in levels), default=0)
    return [l["hits"] for l in levels if len(l["hits"]) >= 0.25 * largest]


def interior_candidates(bvh, hits):
    up = Vector((0, 0, 1))
    out = []
    for x, y, z, i, j in hits:
        floor_pt = Vector((x, y, z + 0.05))
        eye = Vector((x, y, z + EYE_HEIGHT))
        # Nothing standing between floor and eye (furniture, stairs)
        if hit_distance(bvh, floor_pt, up, EYE_HEIGHT - 0.05) is not None:
            continue
        # A ceiling above, at a plausible storey height
        ceiling = hit_distance(bvh, eye, up, 6.0)
        if ceiling is None or ceiling < 0.3:
            continue
        # Enclosed by walls in every direction, with some clearance around the eye
        enclosed = True
        for d in H_DIRS:
            dist = hit_distance(bvh, eye, d, 40.0)
            if dist is None or dist < 0.6:
                enclosed = False
                break
        if enclosed:
            out.append({"eye": eye, "floor": z, "cell": (i, j)})
    return out


def drop_small_patches(cands, step, min_area=6.0):
    """Keep candidates on connected floor patches of at least `min_area` m2. Removes bed and
    table tops, which pass the interior test but are not somewhere to stand."""
    index = {(c["cell"], round(c["floor"], 1)): n for n, c in enumerate(cands)}
    seen, keep = set(), []
    for start in range(len(cands)):
        if start in seen:
            continue
        stack, patch = [start], []
        seen.add(start)
        while stack:
            n = stack.pop()
            patch.append(n)
            (i, j), z = cands[n]["cell"], cands[n]["floor"]
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    for dz in (-0.1, 0.0, 0.1):
                        m = index.get(((i + di, j + dj), round(z + dz, 1)))
                        if m is not None and m not in seen and abs(cands[m]["floor"] - z) < 0.15:
                            seen.add(m)
                            stack.append(m)
        if len(patch) * step * step >= min_area:
            keep.extend(patch)
    return [cands[n] for n in sorted(keep)]


def visible(bvh, a, b):
    d = b - a
    dist = d.length
    if dist < 1e-6:
        return True
    return hit_distance(bvh, a, d.normalized(), dist - 0.05) is None


def choose_viewpoints(bvh, cands, max_views, coverage):
    """Greedy set cover over line-of-sight visibility between candidate points."""
    n = len(cands)
    log(f"computing visibility between {n} candidate points")
    vis = [set([k]) for k in range(n)]
    for a in range(n):
        for b in range(a + 1, n):
            ea, eb = cands[a]["eye"], cands[b]["eye"]
            if abs(cands[a]["floor"] - cands[b]["floor"]) > 0.5 or (ea - eb).length > 25:
                continue
            if visible(bvh, ea, eb):
                vis[a].add(b)
                vis[b].add(a)

    uncovered = set(range(n))
    chosen = []
    while uncovered and len(chosen) < max_views and len(uncovered) > n * (1 - coverage):
        best = max(range(n), key=lambda k: len(vis[k] & uncovered))
        newly = vis[best] & uncovered
        if len(newly) < max(3, n * 0.01):
            break
        # Re-centre: the candidate nearest the centroid of what this view newly covers,
        # as long as it still sees most of it. Gives viewpoints near room centres.
        centroid = sum((cands[k]["eye"] for k in newly), Vector()) / len(newly)
        pick = min(newly, key=lambda k: (cands[k]["eye"] - centroid).length)
        if len(vis[pick] & newly) < 0.8 * len(newly):
            pick = best
        chosen.append(pick)
        uncovered -= vis[pick] | newly
    return chosen


# ---------------------------------------------------------------------------
# Lighting & rendering
# ---------------------------------------------------------------------------

def setup_world():
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    for sky_type in ("MULTIPLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try:
            sky.sky_type = sky_type
            break
        except TypeError:
            continue
    if hasattr(sky, "sun_elevation"):
        sky.sun_elevation = math.radians(45)
        sky.sun_rotation = math.radians(135)
    bg.inputs["Strength"].default_value = 0.35
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])

    sun_data = bpy.data.lights.new("AutoSun", "SUN")
    sun_data.energy = 3.0
    sun_data.angle = math.radians(1.5)
    sun = bpy.data.objects.new("AutoSun", sun_data)
    sun.rotation_euler = (math.radians(45), 0, math.radians(135))
    scene.collection.objects.link(sun)


def add_fill_light(name, location, energy):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.shadow_soft_size = 0.5
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)


def setup_render(args):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.5
    scene.render.resolution_percentage = 100

    device = "CPU"
    if args.device in ("auto", "gpu"):
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for backend in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = backend
                prefs.get_devices()
            except TypeError:
                continue
            gpus = [d for d in prefs.devices if d.type == backend]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == backend
                device = "GPU"
                log(f"rendering on {backend}: {', '.join(d.name for d in gpus)}")
                break
        if device == "CPU" and args.device == "gpu":
            raise SystemExit("--device gpu requested but no GPU backend is available")
    scene.cycles.device = device
    if device == "CPU":
        log("rendering on CPU")


def make_camera(name):
    data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(cam)
    return cam


def render_pano(cam, location, path, width):
    scene = bpy.context.scene
    cam.data.type = "PANO"
    cam.data.panorama_type = "EQUIRECTANGULAR"
    cam.location = location
    # Looking along +Y: the panorama's centre (yaw 0) faces world +Y.
    cam.rotation_euler = (math.radians(90), 0, 0)
    scene.camera = cam
    scene.render.resolution_x = width
    scene.render.resolution_y = width // 2
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_still(cam, location, target, path, width, lens=24):
    scene = bpy.context.scene
    cam.data.type = "PERSP"
    cam.data.lens = lens
    cam.location = location
    direction = target - location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.resolution_x = width
    scene.render.resolution_y = width * 9 // 16
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def room_owner(bvh, c, views):
    """The nearest viewpoint that can see candidate c: a stand-in for 'which room c is in'."""
    seen = [v for v in views if abs(v["floor"] - c["floor"]) < 0.5 and visible(bvh, v["eye"], c["eye"])]
    return min(seen, key=lambda v: (v["eye"] - c["eye"]).length)["id"] if seen else None


def link_waypoint(bvh, cands, owners, v, w, max_path=20.0):
    """Where a hotspot from viewpoint v towards w should point, or None if they aren't neighbours.

    Directly at w when it is in sight; otherwise at a point in v's or w's room that both can see,
    typically in front of the doorway between them. Rooms only reachable through a third room
    are not linked; the tour goes through that room's viewpoint instead."""
    if abs(w["floor"] - v["floor"]) > 0.5:
        return None
    if visible(bvh, v["eye"], w["eye"]):
        return w["eye"]
    best, best_len = None, max_path
    for c, owner in zip(cands, owners):
        if owner not in (v["id"], w["id"]):
            continue
        length = (c["eye"] - v["eye"]).length + (w["eye"] - c["eye"]).length
        if length < best_len and visible(bvh, v["eye"], c["eye"]) and visible(bvh, c["eye"], w["eye"]):
            best, best_len = c["eye"], length
    return best


def yaw_pitch(frm, to):
    """Direction from `frm` to `to` in viewer terms: yaw 0 = +Y, clockwise seen from above."""
    d = to - frm
    yaw = math.atan2(d.x, d.y)
    pitch = math.atan2(d.z, math.hypot(d.x, d.y))
    return round(yaw, 4), round(pitch, 4)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def draco_available():
    try:
        import io_scene_gltf2
        return bool(io_scene_gltf2.is_draco_available())
    except (ImportError, AttributeError):
        return True  # older exporter without the check; let the export itself decide


def export_web_model(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    draco = draco_available()
    if not draco:
        log("Draco compression unavailable in this Blender build; exporting uncompressed")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_draco_mesh_compression_enable=draco)
    return draco


def main():
    args = parse_args()
    t0 = time.time()
    os.makedirs(os.path.join(args.output, "panos"), exist_ok=True)
    os.makedirs(os.path.join(args.output, "stills"), exist_ok=True)

    log(f"importing {args.input}")
    import_model(os.path.abspath(args.input))
    objs = mesh_objects()
    if not objs:
        raise SystemExit("No visible mesh objects in the file")
    unit_scale = normalise_units(args.unit_scale)
    focus = focus_objects(objs)
    lo, hi = world_bounds(focus)
    size = hi - lo
    log(f"model size {size.x:.1f} x {size.y:.1f} x {size.z:.1f} m, {len(objs)} meshes"
        + (f" ({len(objs) - len(focus)} ground plane(s) ignored for framing)" if len(focus) < len(objs) else ""))

    log("exporting web model")
    draco = export_web_model(objs, os.path.join(args.output, "model.glb"))

    bvh = build_bvh(objs)
    # ~0.5 m spacing finds every room; coarser on big sites to bound the number of rays
    step = args.grid or max(0.5, math.sqrt(size.x * size.y / 60000))
    full_lo, _ = world_bounds(objs)
    hits = find_floor_hits(bvh, Vector((lo.x, lo.y, full_lo.z)), hi, step)
    levels = floor_levels(drop_small_patches(interior_candidates(bvh, hits), step))
    cands = [c for level in levels for c in level]
    log(f"grid {step:.2f} m, {len(hits)} floor hits, {len(levels)} interior floor level(s)")
    # Keep the visibility pass tractable on large buildings
    if len(cands) > 800:
        stride = math.ceil(len(cands) / 800)
        cands = cands[::stride]
    chosen = choose_viewpoints(bvh, cands, args.max_views, args.coverage) if cands else []
    log(f"{len(cands)} interior candidates -> {len(chosen)} viewpoints")

    setup_world()
    has_lights = any(o.type == "LIGHT" and not o.name.startswith("Auto") for o in bpy.context.scene.objects)
    setup_render(args)
    cam = make_camera("AutoCamera")

    views = []
    for n, k in enumerate(chosen):
        c = cands[k]
        views.append({"id": f"p{n + 1}", "eye": c["eye"], "floor": c["floor"]})
        if not args.no_interior_lights:
            ceiling = hit_distance(bvh, c["eye"], Vector((0, 0, 1)), 6.0) or 1.2
            add_fill_light(f"AutoFill{n}", c["eye"] + Vector((0, 0, ceiling - 0.35)), 60 if has_lights else 150)

    floors = sorted({round(v["floor"], 1) for v in views})
    owners = [room_owner(bvh, c, views) for c in cands]
    panoramas = []
    for v in views:
        links = []
        for w in views:
            if w is v:
                continue
            via = link_waypoint(bvh, cands, owners, v, w)
            if via is None:
                continue
            # Hotspot sits on the floor, towards the target or the doorway leading to it
            yaw, pitch = yaw_pitch(v["eye"], via - Vector((0, 0, EYE_HEIGHT - 0.05)))
            links.append({"to": w["id"], "yaw": yaw, "pitch": pitch,
                          "distance": round((w["eye"] - v["eye"]).length, 2)})
        panoramas.append({
            "id": v["id"],
            "file": f"panos/{v['id']}.jpg",
            "kind": "interior",
            "level": floors.index(round(v["floor"], 1)),
            "position": [round(c, 3) for c in v["eye"]],
            "links": links,
        })

    for p, v in zip(panoramas, views):
        log(f"rendering 360 {p['id']} ({len(p['links'])} links)")
        render_pano(cam, v["eye"], os.path.join(args.output, p["file"]), args.pano_width)

    center = (lo + hi) / 2
    radius = max(size.x, size.y) / 2
    if not args.no_aerial:
        aerial = Vector((center.x, center.y, hi.z + max(10.0, radius * 0.6)))
        log("rendering aerial 360")
        render_pano(cam, aerial, os.path.join(args.output, "panos/aerial.jpg"), args.pano_width)
        panoramas.append({"id": "aerial", "file": "panos/aerial.jpg", "kind": "aerial", "level": None,
                          "position": [round(c, 3) for c in aerial], "links": []})

    stills = []
    if not args.no_stills:
        target = Vector((center.x, center.y, lo.z + size.z * 0.35))
        dist = max(radius * 2.2, 8.0)
        for n, angle in enumerate((45, 135, 225, 315)):
            a = math.radians(angle)
            loc = Vector((center.x + dist * math.cos(a), center.y + dist * math.sin(a), lo.z + max(size.z * 1.2, 6.0)))
            name = f"exterior_{n + 1}"
            log(f"rendering still {name}")
            render_still(cam, loc, target, os.path.join(args.output, f"stills/{name}.jpg"), args.still_width)
            stills.append({"id": name, "file": f"stills/{name}.jpg"})

    manifest = {
        "version": 1,
        "source": os.path.basename(args.input),
        "units": "m",
        "unitScale": unit_scale,
        "bounds": {"min": [round(c, 3) for c in lo], "max": [round(c, 3) for c in hi]},
        "model": {"file": "model.glb", "draco": draco},
        "levels": len(floors),
        "panoramas": panoramas,
        "stills": stills,
        "processingSeconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(args.output, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    log(f"done in {manifest['processingSeconds']} s -> {args.output}")


if __name__ == "__main__":
    main()
