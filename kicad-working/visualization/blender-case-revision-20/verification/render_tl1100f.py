"""Render a TL1100F tact switch (S19) close up, from the front and three-quarter, read-only.

Uses the scene's own S3 meshes in a temporary in-memory scene (model frame) and
writes ../tl1100f.png; the saved scene is never written.

Run:
  Blender --background --factory-startup kicad-working/visualization/blender-case-revision-20/x0xb0x-populated-with-case.blend \
      --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-20/verification/render_tl1100f.py
"""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REV = HERE.parent
SOURCE = Path(bpy.data.filepath)
source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
tmp = Path(tempfile.mkdtemp(prefix='tl1100f-'))
root = next(o for o in bpy.data.objects if o.get('source_reference') == 'S19')
sc = bpy.data.scenes.new('TEMP tl1100f')
sc.render.engine = bpy.context.scene.render.engine
sc.render.resolution_x, sc.render.resolution_y = 700, 900
sc.world = bpy.data.worlds.new('TEMP world')
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.86, 0.87, 0.89, 1)
inv = root.matrix_world.inverted()
pts = []
for o in root.children_recursive:
    if o.type != 'MESH':
        continue
    c = bpy.data.objects.new('TEMP ' + o.name, o.data)
    c.matrix_world = inv @ o.matrix_world
    sc.collection.objects.link(c)
    pts += [c.matrix_world @ v.co for v in o.data.vertices]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
ctr = (lo + hi) / 2
for e, a in ((3, (0.3, 0.8, -1)), (1.5, (-0.5, 0.2, -0.6))):
    ld = bpy.data.lights.new('TEMP light', 'SUN')
    ld.energy = e
    lo_ = bpy.data.objects.new('TEMP light', ld)
    lo_.rotation_euler = Vector(a).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(lo_)
images = []
for name, d in (('front', Vector((0, 1, -0.35))), ('three-quarter', Vector((0.6, 1, -0.45)))):
    cd = bpy.data.cameras.new('TEMP camera')
    cd.lens = 60
    cd.clip_start = 0.001          # the camera is closer than Blender's 0.1 m default
    cam = bpy.data.objects.new('TEMP camera', cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    d = d.normalized()
    cam.location = ctr - d * 0.075
    cam.rotation_euler = d.to_track_quat('-Z', 'Z').to_euler()
    sc.render.filepath = str(tmp / f'{name}.png')
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    images.append(tmp / f'{name}.png')
tiles = []
for path in images:
    img = bpy.data.images.load(str(path))
    w, h = img.size
    tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4))
sheet = bpy.data.images.new('TEMP sheet', 2 * w, h, alpha=False)
sheet.pixels = np.concatenate(tiles, axis=1).ravel()
sheet.filepath_raw = str(REV / 'tl1100f.png')
sheet.file_format = 'PNG'
sheet.save()
shutil.rmtree(tmp)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_sha, 'Rendering changed the saved scene'
(HERE / 'tl1100f-render.json').write_text(json.dumps(dict(
    source_scene_sha256=source_sha, image='tl1100f.png',
    image_sha256=hashlib.sha256((REV / 'tl1100f.png').read_bytes()).hexdigest(),
    views=['front', 'three-quarter'], reference='S19', saved_scene_unchanged=True, read_only=True), indent=2) + '\n')
