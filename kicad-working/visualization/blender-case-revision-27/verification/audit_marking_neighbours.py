"""Record IC contacts with every other visible mesh, before and after the markings (read-only).

Tests the evaluated instances of the 17 marked ICs at frame 1 against every other visible
component, panel and enclosure mesh within 2 mm, excluding their own geometry and the
PCB layers. Each contact reports how far the other mesh's vertices reach inside the
reference's own bounding box (reference frame). It also records the free height above
each chip along the board normal. Contacts are recorded, not corrected.
"""
import hashlib, json
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = Path(__file__).resolve().parent
BASELINE = HERE.parents[1] / 'blender-case-revision-26/x0xb0x-populated-with-case.blend'
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
record = json.loads((HERE.parent / 'revision-27-change-record.json').read_text())
TARGETS = {n.rsplit('/', 1)[0] for n in record['changes']}
assert len(TARGETS) == 17
DECLARED = set()   # reviewed contacts that appear only with the markings: (target, other)


def screen(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    items = []
    for inst in bpy.context.evaluated_depsgraph_get().object_instances:
        obj = inst.object
        if obj.type != 'MESH' or obj.original.hide_render or (inst.parent and inst.parent.original.hide_render) or not obj.data.polygons:
            continue
        m = np.array(inst.matrix_world)
        co = np.array([v.co[:] for v in obj.data.vertices])
        world = co @ m[:3, :3].T + m[:3, 3]
        items.append(dict(name=obj.original.name, world=world, polys=[tuple(p.vertices) for p in obj.data.polygons],
                          matrix=m @ np.array(obj.original.matrix_world.inverted()), lo=world.min(0), hi=world.max(0)))
    contacts, headroom, near = [], {}, 0
    rest = [i for i in items if i['name'].rsplit('/', 1)[0] not in TARGETS and '/PCB layers/' not in i['name']]
    verts, polys = [], []
    for i in rest:
        base = len(verts)
        verts += [tuple(v) for v in i['world']]
        polys += [tuple(base + k for k in p) for p in i['polys']]
    world_tree = BVHTree.FromPolygons(verts, polys)
    for u in [i for i in items if i['name'].rsplit('/', 1)[0] in TARGETS]:
        owner = u['name'].rsplit('/', 1)[0]
        frame = u['matrix'] @ np.array(bpy.data.objects[owner].matrix_world)
        to_local = np.linalg.inv(frame)
        own = (u['world'] @ to_local[:3, :3].T + to_local[:3, 3]) * 1000
        box_lo, box_hi = own.min(0), own.max(0)
        tree = BVHTree.FromPolygons([tuple(v) for v in u['world']], u['polys'])
        for item in items:
            if item is u or item['name'].startswith(owner + '/') or '/PCB layers/' in item['name']:
                continue
            if not (np.all(item['lo'] <= u['hi'] + .002) and np.all(item['hi'] >= u['lo'] - .002)):
                continue
            near += 1
            pairs = tree.overlap(BVHTree.FromPolygons([tuple(v) for v in item['world']], item['polys']))
            if not pairs:
                continue
            local = (item['world'] @ to_local[:3, :3].T + to_local[:3, 3]) * 1000
            inside = np.all((local > box_lo) & (local < box_hi), axis=1)
            depth = float(np.minimum(local[inside] - box_lo, box_hi - local[inside]).min(1).max()) if inside.any() else 0.0
            contacts.append(dict(target=owner, other=item['name'], triangle_pairs=len(pairs), depth_inside_bbox_mm=round(depth, 3)))
        axis = Vector(frame[:3, 2]).normalized()
        top = u['world'][np.argsort(u['world'] @ np.array(axis))[-60:]]
        hits = [world_tree.ray_cast(Vector(p) + axis * 1e-6, axis, 0.3) for p in top]
        dist = [h[3] for h in hits if h[0] is not None]
        headroom[owner] = round(min(dist) * 1000, 2) if dist else None
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    return dict(scene_sha256=digest, nearby_meshes_tested=near, contacts=contacts, headroom=headroom)


before, after = screen(BASELINE), screen(FINAL)
key = lambda c: (c['target'], c['other'])  # noqa: E731
old = {key(c): c for c in before['contacts']}
now = {key(c): c for c in after['contacts']}
new = sorted(set(now) - set(old))
out = dict(passed=set(new) == DECLARED, frame=1, declared=sorted(f'{t} | {o}' for t, o in DECLARED),
           new_contacts=[now[k] for k in new], retained_contacts=[dict(now=now[k], before=old[k]) for k in sorted(set(now) & set(old))],
           removed_contacts=[old[k] for k in sorted(set(old) - set(now))],
           headroom_above_chip_mm=dict(before=before['headroom'], after=after['headroom']),
           baseline=dict(scene_sha256=before['scene_sha256'], nearby_meshes_tested=before['nearby_meshes_tested']),
           current=dict(scene_sha256=after['scene_sha256'], nearby_meshes_tested=after['nearby_meshes_tested']),
           read_only=True, physical_fit_qualified=False,
           method='Rendered marked IC meshes versus other component, panel and enclosure meshes within a 2 mm bbox at frame 1; '
                  'own geometry and PCB layers excluded. Depth = deepest reach of the other mesh inside the reference bounding box. '
                  'Headroom = free distance along the board normal from the 60 highest vertices to any other visible mesh.')
(HERE / 'marking-neighbour-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: out[k] for k in ('passed', 'new_contacts', 'retained_contacts', 'removed_contacts', 'headroom_above_chip_mm')}, indent=1), flush=True)
assert out['passed']
