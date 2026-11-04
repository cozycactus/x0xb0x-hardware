"""Record what the four chips touch, and what the removed SIP pairs touched (read-only).

Tests the evaluated instances at frame 1 against every other visible component, panel and
enclosure mesh within a 2 mm box, excluding own geometry and the PCB layers: the chips in
revision 28, the SIP pairs in revision 27. A contact is a triangle overlap. For each chip the
smallest gap to every neighbour within the box is measured both ways with a nearest-surface
search, so a neighbour that only grazes the chip is reported too. It also records the free
height above each chip along the board normal. Contacts are recorded, not corrected.

kicad-working/smd-sites/fit-check.json lists Q126-R100A0 as touching, because fit_check.py measures
from a neighbour to the box around the chip, leads included. This screen measures to the chip's mesh,
whose body stops short of that box's corners, so both figures are kept and the difference stated.
"""
import hashlib
import json
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BASELINE = HERE.parents[1] / 'blender-case-revision-27/x0xb0x-populated-with-case.blend'
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
record = json.loads((HERE.parent / 'revision-28-change-record.json').read_text())
CHIPS = set(record['added_references'])
SIP = set(record['removed_do_not_place_references'])
assert len(CHIPS) == len(SIP) == 4
fit = json.loads((REPO / 'kicad-working/smd-sites/fit-check.json').read_text())
TOUCHING = 0.005   # mm: closer than this counts as touching, the same figure as verify_terminal_joins.py
DECLARED = set()   # reviewed mesh contacts of the chips: none


def owner_of(name):
    return '/'.join(name.split('/')[:2])


def screen(path, targets):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    items = []
    for inst in bpy.context.evaluated_depsgraph_get().object_instances:
        obj = inst.object
        if obj.type != 'MESH' or obj.original.hide_render or (inst.parent and inst.parent.original.hide_render) or not obj.data.polygons:
            continue
        if '/PCB layers/' in obj.original.name:
            continue
        m = np.array(inst.matrix_world)
        co = np.empty(len(obj.data.vertices) * 3)
        obj.data.vertices.foreach_get('co', co)
        world = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        items.append(dict(name=obj.original.name, world=world, polys=[tuple(p.vertices) for p in obj.data.polygons],
                          matrix=m @ np.array(obj.original.matrix_world.inverted()), lo=world.min(0), hi=world.max(0)))
    contacts, near, headroom = [], [], {}
    rest = [i for i in items if owner_of(i['name']) not in targets]
    verts, polys = [], []
    for i in rest:
        base = len(verts)
        verts += [tuple(v) for v in i['world']]
        polys += [tuple(base + k for k in p) for p in i['polys']]
    world_tree = BVHTree.FromPolygons(verts, polys)
    for u in [i for i in items if owner_of(i['name']) in targets]:
        owner = owner_of(u['name'])
        frame = u['matrix'] @ np.array(bpy.data.objects[owner].matrix_world)
        tree = BVHTree.FromPolygons([tuple(v) for v in u['world']], u['polys'])
        for item in items:
            if item is u or owner_of(item['name']) == owner:
                continue
            if not (np.all(item['lo'] <= u['hi'] + .002) and np.all(item['hi'] >= u['lo'] - .002)):
                continue
            other = BVHTree.FromPolygons([tuple(v) for v in item['world']], item['polys'])
            pairs = tree.overlap(other)
            forward = min(other.find_nearest(Vector(p))[3] for p in u['world'])
            backward = min(tree.find_nearest(Vector(p))[3] for p in item['world'])
            gap = round(min(forward, backward) * 1000, 3)
            near.append(dict(target=owner, other=owner_of(item['name']), mesh=item['name'], gap_mm=gap, triangle_pairs=len(pairs)))
            if pairs or gap < TOUCHING:
                contacts.append(dict(target=owner, other=owner_of(item['name']), mesh=item['name'], triangle_pairs=len(pairs), gap_mm=gap))
        axis = Vector(frame[:3, 2]).normalized()
        top = u['world'][np.argsort(u['world'] @ np.array(axis))[-60:]]
        hits = [world_tree.ray_cast(Vector(p) + axis * 1e-6, axis, 0.3) for p in top]
        dist = [h[3] for h in hits if h[0] is not None]
        headroom[owner] = round(min(dist) * 1000, 2) if dist else None
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    return dict(scene_sha256=digest, contacts=contacts, near=near, headroom=headroom)


before, after = screen(BASELINE, SIP), screen(FINAL, CHIPS)
pairs = {f"{c['target']} | {c['other']}" for c in after['contacts']}
box_touch = {'MAINBOARD/' + p.replace('-', ' | MAINBOARD/') for p in fit['touching_in_the_models']}
q126 = [r for r in after['near'] if r['target'] == 'MAINBOARD/Q126' and r['other'] == 'MAINBOARD/R100A0']
closest = {}
for row in after['near']:
    if row['target'] not in closest or row['gap_mm'] < closest[row['target']]['gap_mm']:
        closest[row['target']] = dict(other=row['other'], gap_mm=row['gap_mm'])
out = dict(passed=pairs == DECLARED, frame=1, declared=sorted(DECLARED), fit_check_touching_the_chip_box=sorted(box_touch),
           q126_r100a0_mesh_gap_mm=min(r['gap_mm'] for r in q126), q126_r100a0_triangle_pairs=sum(r['triangle_pairs'] for r in q126),
           fit_check_difference='fit_check.py measures to the box around the chip, leads included. R100A0 enters that box by 0.09 mm, just above the chip top, '
                                'where the chip body has no material. Mesh to mesh the two models do not overlap.',
           chip_contacts=after['contacts'], removed_with_the_sip_pairs=before['contacts'], smallest_gap_per_chip=closest, neighbours=after['near'],
           headroom_above_chip_mm=after['headroom'], baseline_scene_sha256=before['scene_sha256'], current_scene_sha256=after['scene_sha256'],
           read_only=True, physical_fit_qualified=False,
           method='Rendered chip meshes versus other component, panel and enclosure meshes within a 2 mm box at frame 1; own geometry and PCB layers excluded. '
                  'Contact = triangle overlap, or a nearest-surface gap under 0.005 mm. Headroom = free distance along the board normal from the 60 highest vertices to any other visible mesh.')
(HERE / 'chip-neighbour-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: out[k] for k in ('passed', 'chip_contacts', 'removed_with_the_sip_pairs', 'smallest_gap_per_chip', 'q126_r100a0_mesh_gap_mm', 'headroom_above_chip_mm')}, indent=1), flush=True)
assert out['passed']
