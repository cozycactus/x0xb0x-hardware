"""Render each terminal-completed model with its real KiCad drill outlines (read-only).

For one placed reference of each of the 12 models, the scene's own mesh datablocks
are shown in a temporary in-memory scene in the model frame (Z up from the seat), with the
footprint's drill circles drawn as rings on both board faces: red where the
nominal-fit audit records interference, green otherwise. The saved scene is never
written; the temporary scene exists only in memory.

Run:
  Blender --background --factory-startup kicad-working/visualization/blender-case-revision-16/x0xb0x-populated-with-case.blend \
      --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-16/verification/render_terminal_sheet.py
"""
import hashlib
import json
import math
import shutil
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REV = HERE.parent
WORK = HERE.parents[2]
OUT = Path(tempfile.mkdtemp(prefix='terminal-views-'))   # individual views are not kept
SOURCE = Path(bpy.data.filepath)
source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
record = json.loads((REV / 'revision-16-change-record.json').read_text())
audit = json.loads((WORK / 'validation/models-review-13/native-terminal-audit.json').read_text())
pads = json.loads((WORK / 'validation/models-review-13/native-probes/pads.json').read_text())
THICKNESS = 1.6e-3
original = bpy.context.scene
original.frame_set(1)
bpy.context.view_layer.update()


def material(name, rgb, emission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = emission
    return m


LABEL = material('TEMP label', (0.02, 0.02, 0.02))
PANEL = material('TEMP label panel', (0.82, 0.83, 0.85), 0.9)
RING = {'fits': material('TEMP ring fits', (0.05, 0.6, 0.15), 2.0),
        'interferes': material('TEMP ring interferes', (0.9, 0.08, 0.05), 2.0),
        'empty by design': material('TEMP ring empty', (0.4, 0.4, 0.45), 1.0)}


def ring(name, centre, radius, z, mat, sc):
    segments, width = 48, 0.0002
    verts, faces = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        for r in (radius, radius + width):
            verts.append((centre[0] + r * math.cos(a), centre[1] + r * math.sin(a), z))
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    sc.collection.objects.link(obj)
    return obj


rows = []
fit = {key: next(iter(refs.values())) for key, refs in audit['models'].items()}
by_root = {r['root']: r for r in record['references']}
for key, refs in audit['models'].items():
    ref = sorted(refs)[0]
    row = next(r for r in record['references'] if r['reference'] == ref)
    root = bpy.data.objects[row['root']]
    board_node = root.parent
    sc = bpy.data.scenes.new('TEMP terminals ' + key)
    sc.render.engine = original.render.engine
    sc.render.resolution_x, sc.render.resolution_y = 900, 700
    sc.render.film_transparent = False
    sc.world = bpy.data.worlds.new('TEMP world ' + key)
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.82, 0.83, 0.85, 1)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    to_model = root.matrix_world.inverted()
    points = []
    for obj in root.children_recursive:
        if obj.type != 'MESH':
            continue
        copy = bpy.data.objects.new('TEMP ' + obj.name, obj.data)
        copy.matrix_world = to_model @ obj.matrix_world
        sc.collection.objects.link(copy)
        points += [copy.matrix_world @ v.co for v in obj.data.vertices]
    # Pads in the board-node frame are (x, -y, top) mm; express them in the model frame.
    to_model_from_board = to_model @ board_node.matrix_world
    footprint = next(f for f in pads[row['board']]['footprints'] if f['reference'] == ref)
    top = audit['boards'][row['board']]['board_top_mm'] / 1000
    results = {p['pad']: p['result'] for p in fit[key]['pads']}
    for p in footprint['pads']:
        if p['attribute'] not in ('PTH', 'NPTH'):
            continue
        for face, z in (('top', top), ('bottom', top - THICKNESS)):
            c = to_model_from_board @ Vector((p['x_mm'] / 1000, -p['y_mm'] / 1000, z))
            ring(f"TEMP {p['number']} {face}", c, min(p['drill_mm']) / 2000, c.z,
                 RING['fits' if results[p['number']] == 'fits' else results[p['number']]], sc)
    lo = Vector([min(q[i] for q in points) for i in range(3)])
    hi = Vector([max(q[i] for q in points) for i in range(3)])
    centre = (lo + hi) / 2
    size = max(hi - lo)
    cam_data = bpy.data.cameras.new('TEMP camera ' + key)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = size * 1.45
    cam = bpy.data.objects.new('TEMP camera ' + key, cam_data)
    direction = Vector((-0.45, 0.8, 0.75)).normalized()   # camera below the seat, front-right, looking up
    cam.location = centre - direction * size * 4
    cam.rotation_euler = direction.to_track_quat('-Z', 'Z').to_euler()
    cam_data.clip_start, cam_data.clip_end = 0.0001, size * 10
    sc.collection.objects.link(cam)
    sc.camera = cam
    label = bpy.data.curves.new('TEMP label ' + key, 'FONT')
    label.body = f"{key}  ({ref})"
    label.size = cam_data.ortho_scale * 0.045
    label.materials.append(LABEL)
    text = bpy.data.objects.new('TEMP label ' + key, label)
    text.parent = cam
    text.location = (-0.47 * cam_data.ortho_scale, 0.33 * cam_data.ortho_scale, -size)
    sc.collection.objects.link(text)
    width, height = len(label.body) * 0.62 * label.size, 1.5 * label.size
    panel_mesh = bpy.data.meshes.new('TEMP label panel ' + key)
    panel_mesh.from_pydata([(-0.3 * label.size, -0.4 * label.size, 0), (width, -0.4 * label.size, 0),
                            (width, height - 0.4 * label.size, 0), (-0.3 * label.size, height - 0.4 * label.size, 0)],
                           [], [(0, 1, 2, 3)])
    panel_mesh.materials.append(PANEL)
    panel = bpy.data.objects.new('TEMP label panel ' + key, panel_mesh)
    panel.parent = cam
    panel.location = (text.location.x, text.location.y, text.location.z - 0.01 * size)
    sc.collection.objects.link(panel)
    for energy, aim in ((3.0, (0.3, 0.6, -1.0)), (1.5, (-0.5, -0.4, 0.8))):
        light_data = bpy.data.lights.new('TEMP light', 'SUN')
        light_data.energy = energy
        light = bpy.data.objects.new('TEMP light', light_data)
        light.rotation_euler = Vector(aim).to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(light)
    image = OUT / f'{key}.png'
    sc.render.filepath = str(image)
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    rows.append(dict(model=key, reference=ref, board=row['board'], image=image.name,
                     drill_rings={r: n for r, n in results.items()}))
    print('rendered', key, ref, flush=True)

# Tile the twelve views (3 rows of 4, half resolution) into one sheet beside the scene.
tiles = []
for row in rows:
    img = bpy.data.images.load(str(OUT / row['image']))
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    tiles.append(px.reshape(h // 2, 2, w // 2, 2, 4).mean(axis=(1, 3)))
th, tw = tiles[0].shape[:2]
grid = np.ones((3 * th, 4 * tw, 4), dtype=np.float32)
for i, tile in enumerate(tiles):
    r, c = divmod(i, 4)
    grid[(2 - r) * th:(3 - r) * th, c * tw:(c + 1) * tw] = tile   # Blender pixel rows run bottom-up
sheet = bpy.data.images.new('TEMP sheet', 4 * tw, 3 * th, alpha=False)
sheet.pixels = grid.ravel()
sheet.filepath_raw = str(REV / 'terminal-models.png')
sheet.file_format = 'PNG'
sheet.save()
shutil.rmtree(OUT)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_sha, 'Rendering changed the saved scene'
(HERE / 'terminal-views.json').write_text(json.dumps(dict(
    source_scene_sha256=source_sha, views=rows, sheet='terminal-models.png', sheet_layout='3 rows of 4, half resolution',
    sheet_sha256=hashlib.sha256((REV / 'terminal-models.png').read_bytes()).hexdigest(), saved_scene_unchanged=True, read_only=True,
    legend='Model frame, viewed from below the seat at front-right; drill rings on both board faces: green fits, '
           'red nominal interference, grey empty by design.'), indent=2) + '\n')
