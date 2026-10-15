"""Record electrolytic contacts with every other visible mesh, before and after (read-only).

Tests the actual evaluated instances of the 39 electrolytic meshes at frame 1 against
every other visible component, panel and enclosure mesh within 2 mm, excluding their
own geometry and the PCB layers. A contact is reported with the deepest penetration of
the other mesh's vertices into the can cylinder (radial depth inside the sleeve, between
the seat and the top). Contacts present only after the change must match the
DECLARED list; they are recorded, not corrected, because placement and transforms
are original.
"""
import hashlib, json, math
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = Path(__file__).resolve().parent
BASELINE = HERE.parents[1] / 'blender-case-revision-23/x0xb0x-populated-with-case.blend'
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
record = json.loads((HERE.parent / 'revision-24-change-record.json').read_text())
plan = json.loads((HERE.parents[2] / 'validation/models-review-21/combined-model-plan.json').read_text())
CANS = {}
# Revision-5 XRL geometry kept for the recoloured references (passive-dimensional-records.json).
RECOLOURED = {'C17': dict(diameter=5.0, seat_gap=2.0, top_z=13.0),
              'C3': dict(diameter=13.0, seat_gap=0.8, top_z=20.8), 'C5': dict(diameter=13.0, seat_gap=0.8, top_z=20.8)}
for row in plan['updated_assignments']:
    dims = row.get('model_nominal_dimensions_mm')
    for ref in row['references']:
        prefix = 'MAINBOARD/' if row['board'] == 'mainboard' else 'IOBOARD/'
        CANS[prefix + ref] = dims or RECOLOURED[ref]
TARGETS = {n.rsplit('/', 1)[0] for n in record['changes']}
assert TARGETS == set(CANS) and len(TARGETS) == 39
# Reviewed contacts that appear only with the new bodies (owner reference -> other object).
DECLARED = {'IOBOARD/C8': 'IOBOARD/TM6/mesh.001'}   # 6.3 mm can (100uF 25V) reaches the 2k trimmer by ~0.09 mm


def screen(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    items = []
    for inst in bpy.context.evaluated_depsgraph_get().object_instances:
        obj = inst.object
        if obj.type != 'MESH' or obj.original.hide_render or (inst.parent and inst.parent.original.hide_render):
            continue
        data = obj.data
        if not data.polygons:
            continue
        co = np.empty(len(data.vertices) * 3)
        data.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        m = np.array(inst.matrix_world)
        world = co @ m[:3, :3].T + m[:3, 3]
        items.append(dict(name=obj.original.name, parent=inst.parent.original.name if inst.parent else '', world=world,
                          matrix=m @ np.array(obj.original.matrix_world.inverted()),
                          polys=[tuple(p.vertices) for p in data.polygons], lo=world.min(0), hi=world.max(0)))
    targets = [i for i in items if i['name'].rsplit('/', 1)[0] in TARGETS]
    assert len(targets) == 39, len(targets)
    contacts, near = [], 0
    for u in targets:
        owner = u['name'].rsplit('/', 1)[0]
        # Reference (footprint) frame of this displayed instance: instance offset times the source root frame.
        frame = u['matrix'] @ np.array(bpy.data.objects[owner].matrix_world)
        to_local = np.linalg.inv(frame)
        dims = CANS[owner]
        r, z0, z1 = dims['diameter'] / 2, dims['seat_gap'], dims['top_z']
        # Can axis from the target's own sleeve and top vertices (the reference root frame is not centred on the can).
        own = (u['world'] @ to_local[:3, :3].T + to_local[:3, 3]) * 1000
        body = own[own[:, 2] > z0 + 0.5]
        cx, cy = (body[:, 0].min() + body[:, 0].max()) / 2, (body[:, 1].min() + body[:, 1].max()) / 2
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
            rho = np.hypot(local[:, 0] - cx, local[:, 1] - cy)
            inside = (local[:, 2] > z0) & (local[:, 2] < z1) & (rho < r)
            contacts.append(dict(target=owner, other=item['name'], parent=item['parent'], triangle_pairs=len(pairs),
                                 radial_depth_mm=round(float((r - rho[inside]).max()), 3) if inside.any() else 0.0,
                                 z_range_mm=[round(float(local[inside, 2].min()), 2), round(float(local[inside, 2].max()), 2)]
                                 if inside.any() else None))
    # Free distance above each can top along its axis to any other visible mesh (other electrolytics excluded).
    rest = [i for i in items if i['name'].rsplit('/', 1)[0] not in TARGETS and '/PCB layers/' not in i['name']]
    verts, polys = [], []
    for i in rest:
        base = len(verts)
        verts += [tuple(v) for v in i['world']]
        polys += [tuple(base + k for k in p) for p in i['polys']]
    world_tree = BVHTree.FromPolygons(verts, polys)
    headroom = {}
    for u in targets:
        owner = u['name'].rsplit('/', 1)[0]
        frame = u['matrix'] @ np.array(bpy.data.objects[owner].matrix_world)
        axis = Vector(frame[:3, 2]).normalized()
        top = u['world'][np.argsort(u['world'] @ np.array(axis))[-40:]]
        hits = [world_tree.ray_cast(Vector(p) + axis * 1e-6, axis, 0.3) for p in top]
        dist = [h[3] for h in hits if h[0] is not None]
        headroom[owner] = round(min(dist) * 1000, 2) if dist else None
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    return dict(scene_sha256=digest, visible_mesh_instances=len(items), nearby_meshes_tested=near, contacts=contacts,
                headroom=headroom)


before = screen(BASELINE)
after = screen(FINAL)
key = lambda c: (c['target'], c['other'])  # noqa: E731
old = set(map(key, before['contacts']))
new = sorted(set(map(key, after['contacts'])) - old)
kept = sorted(set(map(key, after['contacts'])) & old)
gone = sorted(old - set(map(key, after['contacts'])))
details = {key(c): {k: c[k] for k in ('radial_depth_mm', 'z_range_mm', 'triangle_pairs')} for c in after['contacts']}
previous = {key(c): {k: c[k] for k in ('radial_depth_mm', 'z_range_mm', 'triangle_pairs')} for c in before['contacts']}
out = dict(passed=set(new) == set(DECLARED.items()) if DECLARED else None, frame=1,
           new_contacts=[dict(target=t, other=o, **details[(t, o)]) for t, o in new],
           retained_contacts=[dict(target=t, other=o, now=details[(t, o)], before=previous[(t, o)]) for t, o in kept],
           removed_contacts=[dict(target=t, other=o, before=previous[(t, o)]) for t, o in gone],
           declared=sorted(f'{t} | {o}' for t, o in DECLARED.items()),
           baseline=dict(scene_sha256=before['scene_sha256'], nearby_meshes_tested=before['nearby_meshes_tested'],
                         contact_count=len(before['contacts'])),
           current=dict(scene_sha256=after['scene_sha256'], nearby_meshes_tested=after['nearby_meshes_tested'],
                        contact_count=len(after['contacts'])),
           headroom_above_can_top_mm=dict(sorted(after['headroom'].items())),
           minimum_headroom_mm=min(v for v in after['headroom'].values() if v is not None),
           read_only=True, physical_fit_qualified=False,
           method='Rendered electrolytic meshes versus other component, panel and enclosure meshes within a 2 mm bbox at '
                  'frame 1. Own geometry and PCB layers excluded. Radial depth = how far the other mesh\'s vertices reach '
                  'inside the revision-24 nominal can cylinder between seat and top (also for the baseline contacts). Contacts are recorded, not corrected. Headroom = free distance along each can axis from its 40 highest vertices to any other visible mesh (other electrolytics excluded).')
(HERE / 'electrolytic-neighbour-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: out[k] for k in ('passed', 'new_contacts', 'removed_contacts', 'minimum_headroom_mm', 'headroom_above_can_top_mm')}, indent=1), flush=True)
assert out['passed']
