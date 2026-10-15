"""Cut the saved assembly with a vertical plane through rear-port axes.

Frame 1, rendered instances only. For each requested port the plane is
world X = port axis X; every mesh triangle crossing it inside a window
around the plate contributes one exact 2D segment (world Y, Z in mm).
Segments are grouped per source object and classified for drawing. No
geometry is changed; the output is plotting data, not a fit claim.

Run:
  Blender --background <scene.blend> --python-exit-code 1 \
      --python extract_sections.py -- <output.json> <REF> [<REF> ...]
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ARGS = sys.argv[sys.argv.index('--') + 1:]
OUTPUT = HERE / ARGS[0]
REFS = ARGS[1:]
AXIS = {'HEADPHONE0': (-8.5, 8.0), 'MIXIN0': (-8.5, 8.0), 'MIXOUT0': (-8.5, 8.0),
        'CV0': (-3.0, 5.5), 'GATE0': (-3.0, 5.5),
        'DIN1': (0.0, 10.0), 'DIN2': (0.0, 10.0), 'DIN3': (0.0, 10.0), 'DIN4': (0.0, 10.0)}
WINDOW_Y = (-13.0, 11.0)   # mm, relative to plate inner face (outward +)
WINDOW_Z = (-12.0, 12.0)   # mm, relative to port axis


def classify(name, parent):
    if parent == 'Rear panel — original DXF':
        return 'plate'
    if parent.startswith('Case /'):
        return 'case'
    if name.startswith('TRIAL/'):
        return 'downloaded'
    if name.endswith(('washer proxy', 'nut proxy')):
        return 'hardware'
    if name.startswith('IOBOARD/PCB layers'):
        return 'pcb'
    if name.startswith('IOBOARD/'):
        return 'component'
    return 'other'


def main():
    path = Path(bpy.data.filepath).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    panel = bpy.data.objects['Rear panel — original DXF']
    deps = bpy.context.evaluated_depsgraph_get()
    items = []
    for inst in deps.object_instances:
        obj = inst.object
        if obj.type != 'MESH' or obj.original.hide_render:
            continue
        if inst.parent and inst.parent.original.hide_render:
            continue
        mesh = obj.data
        if not mesh.polygons:
            continue
        co = np.empty(len(mesh.vertices) * 3)
        mesh.vertices.foreach_get('co', co)
        m = np.array(inst.matrix_world)
        world = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        mesh.calc_loop_triangles()
        tri = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
        mesh.loop_triangles.foreach_get('vertices', tri)
        parent = inst.parent.original.name if inst.parent else ''
        items.append(dict(name=obj.original.name, parent=parent, world=world * 1000,
                          tri=tri.reshape(-1, 3), lo=world.min(0) * 1000, hi=world.max(0) * 1000))
    # Plate inner face (world Y) from the actual plate mesh.
    plate = next(i for i in items if i['parent'] == 'Rear panel — original DXF')
    inner_y, outer_y = plate['world'][:, 1].min(), plate['world'][:, 1].max()
    sections = []
    for ref in REFS:
        face_y, axis_z = AXIS[ref]
        inst_matrix = next((i.matrix_world.copy() for i in deps.object_instances
                            if i.object.original.name == f'IOBOARD/{ref}/mesh'), None)
        if inst_matrix is None:  # native hidden in the downloaded-DIN trials
            board = bpy.data.objects['I/O board — rear mounting approximation']
            inst_matrix = board.matrix_world @ bpy.data.objects['TRIAL/' + ref].matrix_world
        axis = inst_matrix @ Vector((0, face_y / 1000, axis_z / 1000)) * 1000
        x0 = axis.x + 1e-6  # avoid exact vertex hits on symmetric meshes
        y_lo, y_hi = inner_y + WINDOW_Y[0], inner_y + WINDOW_Y[1]
        z_lo, z_hi = axis.z + WINDOW_Z[0], axis.z + WINDOW_Z[1]
        groups = []
        for item in items:
            lo, hi = item['lo'], item['hi']
            if not (lo[0] <= x0 <= hi[0] and hi[1] >= y_lo and lo[1] <= y_hi
                    and hi[2] >= z_lo and lo[2] <= z_hi):
                continue
            w, t = item['world'], item['tri']
            s = w[:, 0] - x0
            segs = []
            st = s[t]
            crossing = (st.min(1) < 0) & (st.max(1) > 0)
            for tri in t[crossing]:
                pts = []
                for a, b in ((0, 1), (1, 2), (2, 0)):
                    sa, sb = s[tri[a]], s[tri[b]]
                    if (sa < 0) != (sb < 0):
                        p = w[tri[a]] + (w[tri[b]] - w[tri[a]]) * (sa / (sa - sb))
                        pts.append((float(p[1]), float(p[2])))
                if len(pts) == 2:
                    segs.append(pts)
            if segs:
                groups.append(dict(name=item['name'], parent=item['parent'],
                                   cls=classify(item['name'], item['parent']), segments=segs))
        sections.append(dict(reference=ref, plane_world_x_mm=x0, axis_world_mm=list(axis),
                             plate_inner_y_mm=float(inner_y), plate_outer_y_mm=float(outer_y),
                             window_y_mm=[float(y_lo), float(y_hi)], window_z_mm=[z_lo, z_hi],
                             groups=groups))
        print('SECTION', ref, 'groups', len(groups), 'segments', sum(len(g['segments']) for g in groups))
    report = dict(scene=path.name, scene_sha256=digest, frame=1, sections=sections,
                  scene_bytes_unchanged=hashlib.sha256(path.read_bytes()).hexdigest() == digest)
    OUTPUT.write_text(json.dumps(report) + '\n')
    assert report['scene_bytes_unchanged']


main()
