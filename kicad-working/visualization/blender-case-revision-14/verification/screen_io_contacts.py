"""List every triangle-level contact between the I/O board and the rest.

Frame 1 (assembled), rendered instances only. Each I/O instance is tested
against every non-I/O instance whose world bounding box comes within the
search margin; BVH overlap counts touching or intersecting triangle pairs.
Running it on revision 13 and on the candidate shows which contacts the
0.508 mm shift creates or removes. Touching counts as overlap, so seated
faces appear in both scenes; volumes are measured separately.

Run:
  Blender --background <scene.blend> --python-exit-code 1 \
      --python screen_io_contacts.py -- <output.json>
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / sys.argv[sys.argv.index('--') + 1]
IO_EMPTY = 'I/O board — rear mounting approximation'
MARGIN_M = 0.002


def main():
    source = Path(bpy.data.filepath).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    io_items, other_items = [], []
    for inst in bpy.context.evaluated_depsgraph_get().object_instances:
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
        co = co.reshape(-1, 3)
        m = np.array(inst.matrix_world)
        world = co @ m[:3, :3].T + m[:3, 3]
        parent = inst.parent.original.name if inst.parent else ''
        item = dict(name=obj.original.name, parent=parent, world=world,
                    polys=[tuple(p.vertices) for p in mesh.polygons],
                    lo=world.min(0), hi=world.max(0))
        (io_items if parent == IO_EMPTY else other_items).append(item)
    lo = np.array([o['lo'] for o in other_items])
    hi = np.array([o['hi'] for o in other_items])
    trees = {}

    def tree(item):
        key = id(item)
        if key not in trees:
            trees[key] = BVHTree.FromPolygons([tuple(v) for v in item['world']], item['polys'])
        return trees[key]

    contacts = []
    for a in io_items:
        near = np.all(lo <= a['hi'] + MARGIN_M, axis=1) & np.all(hi >= a['lo'] - MARGIN_M, axis=1)
        for idx in np.nonzero(near)[0]:
            b = other_items[idx]
            pairs = tree(a).overlap(tree(b))
            if pairs:
                contacts.append(dict(io=a['name'], other=b['name'], other_parent=b['parent'],
                                     triangle_pairs=len(pairs)))
    contacts.sort(key=lambda c: (c['io'], c['other']))
    report = dict(scene=source.name, scene_sha256=digest, frame=1,
                  io_instances=len(io_items), other_instances=len(other_items),
                  search_margin_mm=MARGIN_M * 1000, contact_pairs=contacts,
                  scene_bytes_unchanged=hashlib.sha256(source.read_bytes()).hexdigest() == digest)
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n')
    print('CONTACTS', len(contacts), 'io', len(io_items), 'other', len(other_items))
    assert report['scene_bytes_unchanged']


main()
