"""Build a simple furnished test apartment and export it as GLB.

Used to exercise process_model.py without needing a real developer file.

    blender -b -P pipeline/blender/make_test_apartment.py -- --output test_apartment.glb
    python pipeline/blender/make_test_apartment.py --output test_apartment.glb   # with the bpy module
"""

import argparse
import sys

import bpy

WALL_T = 0.15
WALL_H = 3.0


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    return p.parse_args(argv)


def material(name, color, roughness=0.6, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        bsdf.inputs["Transmission Weight"].default_value = 1.0
    return mat


def box(name, x0, y0, z0, x1, y1, z1, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(mat)
    return obj


def wall(name, a, b, fixed, axis, openings, mat, glass):
    """Axis-aligned wall from a to b along `axis` ('x' or 'y'), at `fixed` on the other axis.

    openings: list of (start, end, bottom, top) along the wall; top < WALL_H adds a lintel,
    bottom > 0 adds a sill and a glass pane (a window).
    """
    def seg(n, s0, s1, z0, z1, m):
        if s1 - s0 < 1e-3 or z1 - z0 < 1e-3:
            return
        h = WALL_T / 2
        if axis == "x":
            box(n, s0, fixed - h, z0, s1, fixed + h, z1, m)
        else:
            box(n, fixed - h, s0, z0, fixed + h, s1, z1, m)

    cursor = a
    for i, (s, e, bottom, top) in enumerate(sorted(openings)):
        seg(f"{name}_{i}", cursor, s, 0, WALL_H, mat)
        seg(f"{name}_{i}_sill", s, e, 0, bottom, mat)
        seg(f"{name}_{i}_lintel", s, e, top, WALL_H, mat)
        if bottom > 0:
            h = 0.01
            if axis == "x":
                box(f"{name}_{i}_glass", s, fixed - h, bottom, e, fixed + h, top, glass)
            else:
                box(f"{name}_{i}_glass", fixed - h, s, bottom, fixed + h, e, top, glass)
        cursor = e
    seg(f"{name}_end", cursor, b, 0, WALL_H, mat)


def main():
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)

    m_wall = material("Wall", (0.85, 0.83, 0.78))
    m_floor = material("Floor_Wood", (0.45, 0.30, 0.18), 0.4)
    m_ceiling = material("Ceiling", (0.95, 0.95, 0.95))
    m_glass = material("Glass", (0.8, 0.9, 1.0), 0.05, alpha=0.2)
    m_sofa = material("Sofa", (0.15, 0.25, 0.45))
    m_wood = material("Wood", (0.35, 0.22, 0.12), 0.5)
    m_bed = material("Bedding", (0.9, 0.88, 0.85))
    m_ground = material("Ground", (0.30, 0.42, 0.22), 0.9)

    # 12 x 8 m apartment: living room on the left (x 0-6), two bedrooms on the right.
    box("Ground", -20, -20, -0.2, 32, 28, -0.1, m_ground)
    box("Floor", 0, 0, -0.1, 12, 8, 0, m_floor)
    box("Ceiling", 0, 0, WALL_H, 12, 8, WALL_H + 0.1, m_ceiling)

    door = (0.0, 2.1)  # bottom, top
    win = (0.9, 2.3)
    wall("Wall_S", 0, 12, 0, "x", [(1.5, 4.5, *win), (8.0, 10.0, *win)], m_wall, m_glass)
    wall("Wall_N", 0, 12, 8, "x", [(2.0, 3.0, *door), (8.0, 10.0, *win)], m_wall, m_glass)
    wall("Wall_W", 0, 8, 0, "y", [(2.5, 5.5, *win)], m_wall, m_glass)
    wall("Wall_E", 0, 8, 12, "y", [(1.0, 3.0, *win), (5.0, 7.0, *win)], m_wall, m_glass)
    wall("Wall_Mid", 0, 8, 6, "y", [(1.5, 2.4, *door), (5.5, 6.4, *door)], m_wall, m_glass)
    wall("Wall_Beds", 6, 12, 4, "x", [], m_wall, m_glass)

    # Living room furniture
    box("Sofa_Base", 0.6, 4.5, 0, 1.5, 6.8, 0.45, m_sofa)
    box("Sofa_Back", 0.3, 4.5, 0, 0.6, 6.8, 0.9, m_sofa)
    box("Coffee_Table", 2.3, 5.0, 0, 3.3, 6.3, 0.4, m_wood)
    box("Dining_Table", 2.5, 1.0, 0.72, 4.5, 2.0, 0.76, m_wood)
    for i, (x, y) in enumerate([(2.6, 1.1), (4.4, 1.1), (2.6, 1.9), (4.4, 1.9)]):
        box(f"Table_Leg_{i}", x - 0.04, y - 0.04, 0, x + 0.04, y + 0.04, 0.72, m_wood)
    box("TV_Unit", 5.3, 4.8, 0, 5.85, 6.6, 0.5, m_wood)

    # Bedrooms
    box("Bed_1", 9.0, 0.3, 0, 11.0, 2.4, 0.55, m_bed)
    box("Bed_1_Head", 9.0, 0.15, 0, 11.0, 0.3, 1.1, m_wood)
    box("Wardrobe_1", 6.2, 0.2, 0, 6.8, 2.0, 2.2, m_wood)
    box("Bed_2", 9.5, 5.6, 0, 11.5, 7.8, 0.55, m_bed)
    box("Bed_2_Head", 11.5, 5.6, 0, 11.85, 7.8, 1.1, m_wood)
    box("Desk_2", 6.2, 6.6, 0.72, 7.6, 7.3, 0.76, m_wood)

    bpy.ops.export_scene.gltf(filepath=args.output, export_format="GLB")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
