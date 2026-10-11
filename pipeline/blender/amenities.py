"""Amenity detection, camera placement and fly-in clips for process_model.py.

Amenities are found from object, parent and collection names (pool, gym, مسبح, ...), which is how
architects usually organise a site model. Each amenity gets:
  - a hero still from a camera with a clear view of it (inside, for indoor amenities)
  - a 360 panorama at standing height next to / inside it
  - a fly-in clip from the site overview to the hero view, and the same clip reversed (fly-out)
The viewer chains fly-out(A) + fly-in(B) to move between amenities through the overview.
"""

import math
import os
import shutil

import bpy
from mathutils import Vector

# (type, English, Arabic, keywords). Matching runs in this order, so more specific types come
# first ("parking" before "garden", whose keyword "park" it contains).
AMENITY_TYPES = [
    ("parking", "Parking", "المواقف", ["parking", "garage", "carport", "estacionamento", "مواقف"]),
    ("playground", "Kids' play area", "ألعاب الأطفال", ["playground", "kids", "parquinho", "ألعاب", "اطفال"]),
    ("lobby", "Lobby", "الاستقبال", ["lobby", "reception", "foyer", "majlis", "salão", "استقبال", "مجلس", "ردهة"]),
    ("pool", "Swimming pool", "المسبح", ["pool", "swim", "piscina", "مسبح"]),
    ("gym", "Gym", "النادي الرياضي", ["gym", "fitness", "academia", "نادي", "رياضي"]),
    ("court", "Sports court", "الملعب", ["court", "tennis", "padel", "basket", "quadra", "ملعب"]),
    ("bbq", "BBQ area", "منطقة الشواء", ["bbq", "barbecue", "grill", "gourmet", "churrasq", "شواء"]),
    ("mosque", "Mosque", "المسجد", ["mosque", "masjid", "prayer", "musalla", "مسجد", "مصلى"]),
    ("garden", "Garden", "الحديقة", ["garden", "park", "lawn", "jardim", "حديقة"]),
    ("tower", "Tower", "البرج", ["tower", "block", "bloco", "torre", "برج", "عمارة"]),
]
# Menu order in the viewer
MENU_ORDER = ["tower", "lobby", "pool", "gym", "court", "playground", "bbq", "garden", "mosque", "parking"]
# Types that can legitimately appear several times (Tower A, B, C); others keep the largest cluster
MULTI = {"tower"}


def classify(obj):
    names = [obj.name]
    p = obj.parent
    while p is not None:
        names.append(p.name)
        p = p.parent
    names += [c.name for c in obj.users_collection]
    text = " ".join(names).lower()
    for type_id, _en, _ar, keywords in AMENITY_TYPES:
        if any(k in text for k in keywords):
            return type_id
    return None


def _bounds(objs):
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for o in objs:
        for corner in o.bound_box:
            w = o.matrix_world @ Vector(corner)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def _cluster(objs, gap):
    """Group objects whose bounding boxes come within `gap` metres of each other."""
    boxes = [_bounds([o]) for o in objs]
    parent = list(range(len(objs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            (alo, ahi), (blo, bhi) = boxes[i], boxes[j]
            if all(alo[k] - gap <= bhi[k] and blo[k] - gap <= ahi[k] for k in range(2)):
                parent[find(i)] = find(j)
    groups = {}
    for i, o in enumerate(objs):
        groups.setdefault(find(i), []).append(o)
    return list(groups.values())


def detect(objs, gap=6.0):
    by_type = {}
    for o in objs:
        t = classify(o)
        if t:
            by_type.setdefault(t, []).append(o)
    names = {t: (en, ar) for t, en, ar, _k in AMENITY_TYPES}
    found = []
    for t in MENU_ORDER:
        if t not in by_type:
            continue
        clusters = _cluster(by_type[t], gap)
        clusters = [(c, *_bounds(c)) for c in clusters]
        area = lambda c: (c[2].x - c[1].x) * (c[2].y - c[1].y)
        if t in MULTI:
            clusters = sorted((c for c in clusters if area(c) > 25), key=lambda c: (c[1].x, c[1].y))
        else:
            clusters = [max(clusters, key=area)]
        for n, (members, lo, hi) in enumerate(clusters):
            en, ar = names[t]
            suffix = f" {chr(65 + n)}" if len(clusters) > 1 else ""
            found.append({"id": f"{t}{'-' + chr(97 + n) if len(clusters) > 1 else ''}", "type": t,
                          "name": {"en": en + suffix, "ar": ar + suffix},
                          "lo": lo, "hi": hi, "objects": len(members)})
    return found


# ---------------------------------------------------------------------------
# Geometry queries
# ---------------------------------------------------------------------------

def _ray(bvh, origin, direction, dist):
    loc, normal, _i, d = bvh.ray_cast(origin, direction.normalized(), dist)
    return (loc, normal, d) if loc is not None else None


def is_free(bvh, p):
    """True if p is in open space, not inside a closed mesh: from inside a solid every ray
    hits the back of a face (normal pointing the same way as the ray)."""
    back = 0
    for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)),
              Vector((0, 0, -1))):
        hit = _ray(bvh, p, d, 500)
        if hit and hit[1].dot(d) > 0:
            back += 1
        if hit and hit[2] < 0.3:
            return False
    return back < 3


def clear_line(bvh, a, b, margin=0.3):
    d = b - a
    if d.length < margin:
        return True
    return _ray(bvh, a, d, d.length - margin) is None


def ground_at(bvh, x, y, top):
    hit = _ray(bvh, Vector((x, y, top)), Vector((0, 0, -1)), top + 1000)
    return hit[0].z if hit else 0.0


def is_indoor(bvh, lo, hi):
    """Is there walkable, roofed space inside the amenity's footprint (lobby, gym)?"""
    c = (lo + hi) / 2
    floor = ground_at(bvh, c.x, c.y, lo.z + 1.2)
    p = Vector((c.x, c.y, floor + 1.4))
    if not is_free(bvh, p):
        return False
    roof = _ray(bvh, p, Vector((0, 0, 1)), 12)
    walls = sum(1 for a in range(8)
                if _ray(bvh, p, Vector((math.cos(a * math.pi / 4), math.sin(a * math.pi / 4), 0)), 40))
    return roof is not None and walls >= 7


def look_rotation(location, target):
    return (target - location).to_track_quat("-Z", "Y").to_euler()


# ---------------------------------------------------------------------------
# Camera placement
# ---------------------------------------------------------------------------

def hero_camera(bvh, a, site_center):
    """Return (location, target, lens) for an amenity's hero view."""
    lo, hi = a["lo"], a["hi"]
    c = (lo + hi) / 2
    size = hi - lo
    diag = math.hypot(size.x, size.y)

    if a["indoor"]:
        floor = ground_at(bvh, c.x, c.y, lo.z + 1.2)
        best = None
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)):
            loc = Vector((c.x + sx * size.x * 0.38, c.y + sy * size.y * 0.38, floor + 1.7))
            target = Vector((c.x - sx * size.x * 0.3, c.y - sy * size.y * 0.3, floor + 1.3))
            if not is_free(bvh, loc) or not clear_line(bvh, loc, target):
                continue
            # Prefer the view that sees the most open space
            depth = sum((_ray(bvh, loc, (target - loc).normalized() + Vector((dx, 0, 0)), 60) or (0, 0, 60))[2]
                        for dx in (-0.4, 0, 0.4))
            if best is None or depth > best[0]:
                best = (depth, loc, target)
        if best:
            return best[1], best[2], 16

    tall = a["type"] == "tower"
    target = Vector((c.x, c.y, lo.z + (size.z * 0.45 if tall else min(size.z * 0.3, 2.0))))
    dist = max(size.z * 1.5, diag * 1.1) if tall else max(14.0, diag * 1.0)
    elevation = math.radians(12 if tall else 32)
    to_site = (site_center - c).to_2d()
    best = None
    for k in range(16):
        az = k * math.pi / 8
        horiz = Vector((math.cos(az), math.sin(az)))
        loc = Vector((target.x + horiz.x * dist * math.cos(elevation),
                      target.y + horiz.y * dist * math.cos(elevation),
                      target.z + dist * math.sin(elevation)))
        if not is_free(bvh, loc):
            continue
        # Line of sight to the centre and to the corners at mid and full height; catches
        # trees and buildings standing between the camera and the amenity
        mid = lo.z + size.z * 0.5
        probes = [target, Vector((c.x, c.y, mid))]
        for x, y in ((lo.x, lo.y), (hi.x, hi.y), (lo.x, hi.y), (hi.x, lo.y)):
            corner = Vector((x, y, 0)).lerp(Vector((c.x, c.y, 0)), 0.15)
            probes += [Vector((corner.x, corner.y, hi.z)), Vector((corner.x, corner.y, mid))]
        clear = sum(clear_line(bvh, loc, p, 1.0) for p in probes) / len(probes)
        # Prefer standing on the compound side so the background is the project, not empty land
        facing = horiz.dot(to_site.normalized()) if to_site.length > 1 else 0
        score = clear * 3 + facing * 0.5
        if best is None or score > best[0]:
            best = (score, loc)
    loc = best[1] if best else target + Vector((0, -dist, dist * 0.5))
    return loc, target, 20 if tall else 24


def pano_point(bvh, a, hero_loc, hero_target):
    """A standing position for the amenity's 360: inside it if indoor, else at its edge."""
    lo, hi = a["lo"], a["hi"]
    c = (lo + hi) / 2
    if a["indoor"]:
        floor = ground_at(bvh, c.x, c.y, lo.z + 1.2)
        p = Vector((c.x, c.y, floor + 1.6))
        return p if is_free(bvh, p) else Vector((hero_loc.x, hero_loc.y, floor + 1.6))
    horiz = (hero_loc - hero_target).to_2d()
    horiz = horiz.normalized() if horiz.length > 0 else Vector((0, -1))
    reach = math.hypot(hi.x - lo.x, hi.y - lo.y) / 2
    for f in (0.55, 0.75, 0.35, 1.0, 0.15):
        x, y = c.x + horiz.x * reach * f, c.y + horiz.y * reach * f
        p = Vector((x, y, ground_at(bvh, x, y, hi.z + 50) + 1.6))
        if is_free(bvh, p):
            return p
    return Vector((c.x, c.y, ground_at(bvh, c.x, c.y, hi.z + 50) + 1.6))


def overview_camera(lo, hi):
    c = (lo + hi) / 2
    size = hi - lo
    radius = max(size.x, size.y) / 2
    target = Vector((c.x, c.y, lo.z + size.z * 0.15))
    az = math.radians(-60)  # from the south-east, like a typical marketing aerial
    dist = radius * 1.25 + size.z * 0.5
    loc = Vector((c.x + math.cos(az) * dist, c.y + math.sin(az) * dist, lo.z + radius * 0.8 + size.z * 1.1))
    return loc, target, 28


# ---------------------------------------------------------------------------
# Fly-in path
# ---------------------------------------------------------------------------

def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return p0 * u ** 3 + p1 * 3 * u * u * t + p2 * 3 * u * t * t + p3 * t ** 3


def _ease(t):
    return t * t * (3 - 2 * t)


def fly_path(bvh, start, end, site_top):
    """Camera keyframes from the overview (start) to an amenity view (end).

    start/end: (location, target, lens). The path arcs: it leaves the overview level, swings
    in behind the destination camera and settles into it. Raised if it would clip geometry."""
    (s_loc, s_tgt, s_lens), (e_loc, e_tgt, e_lens) = start, end
    back = (e_loc - e_tgt)
    back = Vector((back.x, back.y, 0)).normalized() if back.to_2d().length > 0 else Vector((0, -1, 0))
    lift = 0.0
    for _attempt in range(4):
        c1 = s_loc.lerp(e_loc, 0.35)
        c1.z = max(s_loc.z, site_top + 5 + lift)
        c2 = e_loc + back * max(8.0, (e_loc - e_tgt).length * 0.6) + Vector((0, 0, max(6.0, (s_loc.z - e_loc.z) * 0.3) + lift))
        pts = [_bezier(s_loc, c1, c2, e_loc, i / 40) for i in range(41)]
        if all(clear_line(bvh, pts[i], pts[i + 1], 0.0) for i in range(len(pts) - 1)):
            break
        lift += max(10.0, site_top * 0.5)
    return lambda t: (_bezier(s_loc, c1, c2, e_loc, _ease(t)),
                      s_tgt.lerp(e_tgt, _ease(min(1.0, t * 1.15))),
                      s_lens + (e_lens - s_lens) * _ease(t))


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def set_engine(engine, samples):
    scene = bpy.context.scene
    if engine == "eevee":
        for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            try:
                scene.render.engine = name
                break
            except TypeError:
                continue
        if hasattr(scene, "eevee"):
            scene.eevee.taa_render_samples = max(16, samples)
    else:
        scene.render.engine = "CYCLES"
        scene.cycles.samples = samples


def render_view(cam, view, path, width, height):
    loc, target, lens = view
    scene = bpy.context.scene
    cam.data.type = "PERSP"
    cam.data.lens = lens
    cam.location = loc
    cam.rotation_euler = look_rotation(loc, target)
    scene.camera = cam
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.image_settings.file_format = "JPEG"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_clip(cam, path_fn, frames_dir, frames, width, height):
    os.makedirs(frames_dir, exist_ok=True)
    for f in range(frames):
        t = f / (frames - 1)
        loc, target, lens = path_fn(t)
        render_view(cam, (loc, target, lens), os.path.join(frames_dir, f"{f:04d}.jpg"), width, height)


def encode_clip(frames_dir, out_path, fps, width, height, reverse=False):
    """Encode a JPEG sequence to H.264 MP4 with Blender's sequencer (no external ffmpeg needed)."""
    main_scene = bpy.context.window.scene if bpy.context.window else bpy.context.scene
    files = sorted(f for f in os.listdir(frames_dir) if f.endswith(".jpg"))
    enc = bpy.data.scenes.new("ClipEncode")
    try:
        ed = enc.sequence_editor_create()
        strips = ed.strips if hasattr(ed, "strips") else ed.sequences
        strip = strips.new_image(name="frames", filepath=os.path.join(frames_dir, files[0]), channel=1, frame_start=1)
        for f in files[1:]:
            strip.elements.append(f)
        strip.use_reverse_frames = reverse
        enc.frame_start, enc.frame_end = 1, len(files)
        enc.render.fps = fps
        enc.render.resolution_x, enc.render.resolution_y = width, height
        enc.render.resolution_percentage = 100
        im = enc.render.image_settings
        if hasattr(im, "media_type"):
            im.media_type = "VIDEO"
        im.file_format = "FFMPEG"
        enc.render.ffmpeg.format = "MPEG4"
        enc.render.ffmpeg.codec = "H264"
        enc.render.ffmpeg.constant_rate_factor = "HIGH"
        enc.render.ffmpeg.gopsize = 12  # frequent keyframes: smooth start in the browser
        enc.render.use_sequencer = True
        enc.render.filepath = out_path
        bpy.ops.render.render(animation=True, scene=enc.name)
    finally:
        bpy.data.scenes.remove(enc)
        if bpy.context.window:
            bpy.context.window.scene = main_scene


def keep_frames_dir(frames_dir, keep):
    if not keep:
        shutil.rmtree(frames_dir, ignore_errors=True)
