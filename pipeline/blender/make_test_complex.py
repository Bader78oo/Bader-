"""Build a test residential compound with typical amenities and export it as GLB.

Object names carry amenity keywords (Pool_, Gym_, Court_, ...) the way a developer's model
usually does, so process_model.py can find each amenity.

    blender -b -P pipeline/blender/make_test_complex.py -- --output test_complex.glb
"""

import argparse
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_test_apartment import box, material  # noqa: E402

FLOOR_H = 3.2


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    return p.parse_args(argv)


def emissive(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def cylinder(name, x, y, z0, z1, r, mat, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=z1 - z0, location=(x, y, (z0 + z1) / 2))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def sphere(name, x, y, z, r, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r, location=(x, y, z))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def cone(name, x, y, z0, z1, r, mat, verts=4):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, depth=z1 - z0, location=(x, y, (z0 + z1) / 2))
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler.z = math.pi / verts
    obj.data.materials.append(mat)
    return obj


def palm(name, x, y, h, m):
    cylinder(f"{name}_Trunk", x, y, 0, h, 0.18, m["trunk"], 8)
    for k in range(6):
        a = k * math.pi / 3
        leaf = sphere(f"{name}_Frond_{k}", x + 1.2 * math.cos(a), y + 1.2 * math.sin(a), h - 0.2, 1.0,
                      m["palm"], (1.6, 0.35, 0.12))
        leaf.rotation_euler = (0, -0.35, a)


def tree(name, x, y, m):
    cylinder(f"{name}_Trunk", x, y, 0, 2.2, 0.15, m["trunk"], 8)
    sphere(f"{name}_Canopy", x, y, 3.2, 1.6, m["leaves"])


def tower(name, x0, y0, x1, y1, floors, m, lobby_h=0.0):
    """Glass tower with white floor bands. Starts at lobby_h when the ground floor is a lobby."""
    top = lobby_h + floors * FLOOR_H
    box(f"{name}_Glass", x0 + 0.3, y0 + 0.3, lobby_h, x1 - 0.3, y1 - 0.3, top, m["tower_glass"])
    for f in range(floors + 1):
        z = lobby_h + f * FLOOR_H
        box(f"{name}_Slab_{f}", x0, y0, z - 0.25, x1, y1, z + 0.05, m["slab"])
    for cx, cy in ((x0, y0), (x1 - 0.6, y0), (x0, y1 - 0.6), (x1 - 0.6, y1 - 0.6)):
        box(f"{name}_Column_{cx:.0f}_{cy:.0f}", cx, cy, 0, cx + 0.6, cy + 0.6, top, m["slab"])
    box(f"{name}_Roof_Plant", x0 + 4, y0 + 4, top, x1 - 4, y1 - 4, top + 2.5, m["slab"])


def main():
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)

    m = {
        "sand": material("Desert_Sand", (0.76, 0.66, 0.50), 0.95),
        "grass": material("Garden_Grass", (0.22, 0.42, 0.16), 0.9),
        "paving": material("Paving", (0.80, 0.77, 0.70), 0.7),
        "road": material("Road_Asphalt", (0.12, 0.12, 0.13), 0.8),
        "wall": material("Boundary_Wall", (0.90, 0.86, 0.78), 0.8),
        "slab": material("Tower_White", (0.93, 0.93, 0.91), 0.5),
        "tower_glass": material("Tower_Glass", (0.20, 0.32, 0.42), 0.08),
        "water": material("Pool_Water", (0.03, 0.30, 0.50), 0.03),
        "tile": material("Pool_Tile", (0.55, 0.82, 0.90), 0.3),
        "court": material("Court_Green", (0.18, 0.45, 0.30), 0.8),
        "line": material("Court_Line", (0.95, 0.95, 0.95), 0.6),
        "net": material("Court_Net", (0.05, 0.05, 0.05), 0.8),
        "rubber": material("Playground_Rubber", (0.85, 0.35, 0.25), 0.9),
        "play_y": material("Playground_Yellow", (0.95, 0.75, 0.10), 0.5),
        "play_b": material("Playground_Blue", (0.15, 0.40, 0.85), 0.5),
        "wood": material("Wood", (0.40, 0.25, 0.14), 0.6),
        "metal": material("Metal_Dark", (0.08, 0.08, 0.09), 0.35),
        "glass": material("Glass_Clear", (0.80, 0.90, 1.00), 0.05, alpha=0.15),
        "marble": material("Lobby_Marble", (0.88, 0.85, 0.80), 0.15),
        "sofa": material("Sofa_Fabric", (0.55, 0.45, 0.35), 0.8),
        "dome": material("Mosque_Dome", (0.85, 0.75, 0.45), 0.3),
        "mosque": material("Mosque_White", (0.96, 0.95, 0.92), 0.6),
        "trunk": material("Palm_Trunk", (0.35, 0.26, 0.17), 0.9),
        "palm": material("Palm_Fronds", (0.20, 0.45, 0.12), 0.7),
        "leaves": material("Tree_Leaves", (0.18, 0.38, 0.12), 0.8),
        "lamp": emissive("Lamp_Light", (1.0, 0.85, 0.6), 8.0),
        "car": [material(f"Car_Paint_{i}", c, 0.25) for i, c in enumerate(
            [(0.8, 0.8, 0.8), (0.1, 0.1, 0.12), (0.6, 0.05, 0.05), (0.15, 0.25, 0.5), (0.9, 0.9, 0.88)])],
    }

    # Site: 120 x 90 m compound in a sandy surrounding, entrance from the south
    box("Terrain", -80, -80, -0.3, 200, 170, -0.2, m["sand"])
    box("Site_Paving", 0, 0, -0.2, 120, 90, -0.05, m["paving"])
    box("Garden_Lawn_West", 2, 42, -0.06, 38, 52, 0.0, m["grass"])
    box("Garden_Lawn_Central", 30, 2, -0.06, 70, 20, 0.0, m["grass"])
    box("Garden_Lawn_East", 72, 2, -0.06, 98, 16, 0.0, m["grass"])
    box("Entrance_Road", 54, -60, -0.25, 66, 0, -0.15, m["road"])
    box("Boundary_Wall_S1", 0, -0.3, 0, 54, 0, 2.4, m["wall"])
    box("Boundary_Wall_S2", 66, -0.3, 0, 120, 0, 2.4, m["wall"])
    box("Boundary_Wall_N", 0, 90, 0, 120, 90.3, 2.4, m["wall"])
    box("Boundary_Wall_W", -0.3, 0, 0, 0, 90, 2.4, m["wall"])
    box("Boundary_Wall_E", 120, 0, 0, 120.3, 90, 2.4, m["wall"])
    box("Entrance_Gate_Canopy", 53, -2, 4.0, 67, 2, 4.4, m["slab"])
    for gx in (53, 66.4):
        box(f"Entrance_Gate_Pillar_{gx:.0f}", gx, -1, 0, gx + 0.6, 1, 4.0, m["wall"])

    # Towers. Tower A has a double-height lobby on the ground floor.
    tower("Tower_A", 8, 58, 30, 80, 10, m, lobby_h=5.0)
    tower("Tower_B", 46, 62, 68, 84, 12, m)
    tower("Tower_C", 86, 58, 108, 80, 8, m)

    # Lobby: enclosed room under Tower A, glass facade to the south
    box("Lobby_Floor", 8, 58, -0.05, 30, 80, 0.05, m["marble"])
    box("Lobby_Wall_N", 8, 79.7, 0, 30, 80, 5.0, m["slab"])
    box("Lobby_Wall_W", 8, 58, 0, 8.3, 80, 5.0, m["slab"])
    box("Lobby_Wall_E", 29.7, 58, 0, 30, 80, 5.0, m["slab"])
    box("Lobby_Glass_Facade_L", 8.3, 58, 0, 17, 58.1, 5.0, m["glass"])
    box("Lobby_Glass_Facade_R", 21, 58, 0, 29.7, 58.1, 5.0, m["glass"])
    box("Lobby_Entrance_Door", 17, 58, 3.0, 21, 58.1, 5.0, m["glass"])
    box("Lobby_Reception_Desk", 16, 74, 0, 22, 75.2, 1.1, m["wood"])
    box("Lobby_Feature_Wall", 15, 79.4, 0, 23, 79.7, 5.0, m["wood"])
    for i, (sx, sy) in enumerate([(11, 63), (11, 68), (25, 63), (25, 68)]):
        box(f"Lobby_Sofa_{i}", sx - 1.2, sy - 0.5, 0, sx + 1.2, sy + 0.5, 0.45, m["sofa"])
        box(f"Lobby_Sofa_{i}_Back", sx - 1.2, sy + 0.3, 0, sx + 1.2, sy + 0.5, 0.9, m["sofa"])
    box("Lobby_Coffee_Table", 17.5, 64, 0, 20.5, 66, 0.4, m["marble"])
    sphere("Lobby_Chandelier", 19, 66, 4.0, 0.7, m["lamp"])

    # Swimming pool with deck and loungers
    box("Pool_Deck_S", 40, 24, -0.05, 68, 26, 0.05, m["paving"])
    box("Pool_Deck_N", 40, 40, -0.05, 68, 42, 0.05, m["paving"])
    box("Pool_Deck_W", 40, 26, -0.05, 42, 40, 0.05, m["paving"])
    box("Pool_Deck_E", 66, 26, -0.05, 68, 40, 0.05, m["paving"])
    box("Pool_Basin_Floor", 42, 26, -1.6, 66, 40, -1.5, m["tile"])
    box("Pool_Basin_S", 42, 26, -1.6, 66, 26.2, 0, m["tile"])
    box("Pool_Basin_N", 42, 39.8, -1.6, 66, 40, 0, m["tile"])
    box("Pool_Basin_W", 42, 26, -1.6, 42.2, 40, 0, m["tile"])
    box("Pool_Basin_E", 65.8, 26, -1.6, 66, 40, 0, m["tile"])
    box("Pool_Water", 42.2, 26.2, -0.3, 65.8, 39.8, -0.2, m["water"])
    for i in range(6):
        x = 44 + i * 3.6
        box(f"Pool_Lounger_{i}", x, 40.5, 0.05, x + 0.8, 42.4, 0.4, m["line"])
        cylinder(f"Pool_Umbrella_Pole_{i}", x + 1.8, 41.4, 0, 2.4, 0.04, m["metal"], 8)
        cone(f"Pool_Umbrella_{i}", x + 1.8, 41.4, 2.2, 2.7, 1.3, m["line"], 8)

    # Tennis / padel court with fence
    box("Court_Surface", 74, 22, -0.05, 100, 40, 0.03, m["court"])
    for (a, b, c, d) in [(76, 23.9, 98, 24.0), (76, 38.0, 98, 38.1), (75.9, 24, 76, 38), (98, 24, 98.1, 38),
                         (86.95, 24, 87.05, 38), (76, 30.95, 98, 31.05)]:
        box("Court_Line", a, b, 0.03, c, d, 0.04, m["line"])
    box("Court_Net", 86.97, 23, 0, 87.03, 39, 1.0, m["net"])
    for i in range(14):
        x = 74 + i * 2
        cylinder(f"Court_Fence_Post_S_{i}", x, 22, 0, 3.5, 0.05, m["metal"], 6)
        cylinder(f"Court_Fence_Post_N_{i}", x, 40, 0, 3.5, 0.05, m["metal"], 6)
    for i in range(10):
        y = 22 + i * 2
        cylinder(f"Court_Fence_Post_W_{i}", 74, y, 0, 3.5, 0.05, m["metal"], 6)
        cylinder(f"Court_Fence_Post_E_{i}", 100, y, 0, 3.5, 0.05, m["metal"], 6)
    for i, (lx, ly) in enumerate([(74, 22), (100, 22), (74, 40), (100, 40)]):
        cylinder(f"Court_Floodlight_Pole_{i}", lx, ly, 0, 7, 0.1, m["metal"], 8)
        box(f"Court_Floodlight_{i}", lx - 0.5, ly - 0.2, 7, lx + 0.5, ly + 0.2, 7.4, m["lamp"])

    # Kids' playground
    box("Playground_Floor", 8, 24, -0.05, 30, 38, 0.05, m["rubber"])
    box("Playground_Tower", 14, 29, 0, 17, 32, 2.0, m["play_y"])
    cone("Playground_Tower_Roof", 15.5, 30.5, 2.0, 3.6, 2.3, m["play_b"])
    slide = box("Playground_Slide", 17, 30, 0.1, 21, 31, 0.25, m["play_b"])
    slide.rotation_euler.y = math.radians(25)
    slide.location.z = 1.0
    for sx in (23, 27):
        cylinder(f"Playground_Swing_Post_{sx}_A", sx, 26, 0, 2.6, 0.08, m["play_b"], 8)
        cylinder(f"Playground_Swing_Post_{sx}_B", sx, 30, 0, 2.6, 0.08, m["play_b"], 8)
    box("Playground_Swing_Beam", 22.9, 25.9, 2.5, 27.1, 30.1, 2.65, m["play_b"])
    for i, sy in enumerate((27, 29)):
        box(f"Playground_Swing_Seat_{i}", 24.6, sy - 0.25, 0.5, 25.4, sy + 0.25, 0.55, m["play_y"])
    box("Playground_Sandbox", 10, 34, 0.05, 13, 37, 0.3, m["sand"])
    box("Playground_Bench", 20, 36.5, 0, 24, 37.2, 0.45, m["wood"])

    # BBQ / gourmet pergola
    box("BBQ_Floor", 8, 6, -0.05, 26, 18, 0.08, m["paving"])
    for px in (8.5, 14, 19.5, 25):
        for py in (6.5, 17.5):
            box(f"BBQ_Pergola_Post_{px:.0f}_{py:.0f}", px - 0.15, py - 0.15, 0, px + 0.15, py + 0.15, 3.0, m["wood"])
    for k in range(12):
        x = 8.5 + k * 1.5
        box(f"BBQ_Pergola_Slat_{k}", x, 6.3, 3.0, x + 0.15, 17.7, 3.25, m["wood"])
    box("BBQ_Grill_Counter", 9, 16, 0, 16, 17, 0.95, m["metal"])
    box("BBQ_Grill_Hood", 11, 16.2, 0.95, 13, 17, 1.6, m["metal"])
    box("BBQ_Dining_Table", 13, 10, 0.72, 21, 12, 0.78, m["wood"])
    box("BBQ_Bench_S", 13, 8.8, 0, 21, 9.3, 0.45, m["wood"])
    box("BBQ_Bench_N", 13, 12.7, 0, 21, 13.2, 0.45, m["wood"])
    for i, lx in enumerate((12, 17, 22)):
        sphere(f"BBQ_Pendant_Lamp_{i}", lx, 11, 2.6, 0.25, m["lamp"])

    # Gym pavilion: glass box with equipment
    box("Gym_Floor", 102, 4, -0.05, 117, 18, 0.1, m["rubber"])
    box("Gym_Roof", 102, 4, 4.0, 117, 18, 4.4, m["slab"])
    box("Gym_Wall_E", 116.7, 4, 0, 117, 18, 4.0, m["slab"])
    box("Gym_Wall_N", 102, 17.7, 0, 117, 18, 4.0, m["slab"])
    box("Gym_Glass_W", 102, 4, 0, 102.1, 18, 4.0, m["glass"])
    box("Gym_Glass_S_L", 102, 4, 0, 108, 4.1, 4.0, m["glass"])
    box("Gym_Glass_S_R", 110, 4, 0, 117, 4.1, 4.0, m["glass"])
    box("Gym_Door_Top", 108, 4, 2.4, 110, 4.1, 4.0, m["glass"])
    for i in range(4):
        x = 104 + i * 3
        box(f"Gym_Treadmill_{i}", x, 15, 0.1, x + 0.9, 17, 0.4, m["metal"])
        box(f"Gym_Treadmill_{i}_Console", x, 16.8, 0.1, x + 0.9, 17.0, 1.4, m["metal"])
    box("Gym_Weight_Rack", 115.8, 7, 0.1, 116.6, 13, 1.6, m["metal"])
    box("Gym_Mirror_Wall", 116.6, 6, 0.3, 116.7, 14, 3.0, m["glass"])

    # Mosque / prayer hall with dome and minaret
    box("Mosque_Hall", 72, 4, 0, 86, 16, 6, m["mosque"])
    cylinder("Mosque_Drum", 79, 10, 6, 7, 3.5, m["mosque"], 24)
    dome = sphere("Mosque_Dome", 79, 10, 7, 3.5, m["dome"], (1, 1, 1.15))
    cylinder("Mosque_Minaret", 87.5, 5.5, 0, 16, 1.0, m["mosque"], 12)
    cone("Mosque_Minaret_Top", 87.5, 5.5, 16, 18.5, 1.1, m["dome"], 12)
    box("Mosque_Door", 77.5, 3.9, 0, 80.5, 4.0, 3.5, m["wood"])
    dome.name = "Mosque_Dome"

    # Parking lot with cars
    box("Parking_Surface", 72, 44, -0.08, 118, 54, 0.0, m["road"])
    for i in range(16):
        x = 73 + i * 2.8
        box(f"Parking_Bay_Line_{i}", x, 44.5, 0.0, x + 0.1, 49.5, 0.01, m["line"])
        if i % 3 != 2 and i < 15:
            c = m["car"][i % len(m["car"])]
            box(f"Parking_Car_{i}_Body", x + 0.4, 45.3, 0.2, x + 2.3, 49.6, 0.9, c)
            box(f"Parking_Car_{i}_Cabin", x + 0.5, 46.5, 0.9, x + 2.2, 48.6, 1.45, m["glass"])
    box("Parking_Shade", 72, 44, 3.0, 118, 50.5, 3.15, m["slab"])

    # Garden: palms along the paths, trees on the lawns
    for i in range(10):
        palm(f"Garden_Palm_Entrance_{i}", 51 if i % 2 else 69, 3 + (i // 2) * 4, 7.0, m)
    for i, (x, y) in enumerate([(5, 45), (12, 49), (20, 44), (28, 49), (35, 45)]):
        palm(f"Garden_Palm_West_{i}", x, y, 6.5, m)
    for i, (x, y) in enumerate([(33, 5), (38, 15), (45, 8), (60, 12), (92, 6), (96, 13)]):
        tree(f"Garden_Tree_{i}", x, y, m)
    for i, (x, y) in enumerate([(36, 55), (40, 70), (75, 60), (80, 75), (112, 30), (112, 40)]):
        palm(f"Garden_Palm_{i}", x, y, 7.5, m)

    bpy.ops.export_scene.gltf(filepath=args.output, export_format="GLB")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
