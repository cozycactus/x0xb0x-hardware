"""Record what the two SC-59 chips touch, and what the removed TO-92 JFETs touched (read-only).

Tests the evaluated instances at frame 1 against every other visible component, panel and
enclosure mesh within a 2 mm box, excluding own geometry and the PCB layers: the chips in
revision 29, the JFETs in revision 28. A contact is a triangle overlap. For each chip the
smallest gap to every neighbour within the box is measured both ways with a nearest-surface
search, from the vertices and from points on the surfaces 0.02 mm apart, so a neighbour that only
grazes the chip is reported too, and two edges passing each other are not missed. It also records
the free height above each chip along the board normal, and how far each land's plan outline
stands from each neighbour. Contacts are recorded, not corrected.

kicad-working/smd-sites/fit-check.json measures from a neighbour to boxes around the chip's body
and leads, using the largest sizes in the Toshiba S-Mini drawing, and to the land rectangles, up to
the chip's height plus 0.3 mm. This screen measures to the stock SC-59 mesh in 3D, and its land
figures use fit_check.py's rule, from the PCB file's pad rectangles, with the neighbour's own mesh.
"""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'kicad-import/validation'))
sys.dont_write_bytecode = True
from verify_native_projects import children, one, parse_sexpr, property_value  # noqa: E402

BASELINE = HERE.parents[1] / 'blender-case-revision-28/x0xb0x-populated-with-case.blend'
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
record = json.loads((HERE.parent / 'revision-29-change-record.json').read_text())
CHIPS = set(record['added_references'])
JFET = set(record['removed_do_not_place_references'])
assert len(CHIPS) == len(JFET) == 2
fit = json.loads((REPO / 'kicad-working/smd-sites/fit-check.json').read_text())
TOUCHING = 0.005   # mm: closer than this counts as touching, the same figure as verify_terminal_joins.py
DECLARED = set()   # reviewed mesh contacts of the chips: none
PITCH = 2e-5       # surface sample spacing, metres
CHIP_TOP = 1.3     # the SC-59 model's height above its seat, mm
IRON = 0.3         # fit_check.py's room above the chip for an iron tip, mm
SEAT = 1.595e-3    # the chips' seat above the board's underside, metres


def owner_of(name):
    return '/'.join(name.split('/')[:2])


def triangles_of(obj, world):
    mesh = obj.data
    mesh.calc_loop_triangles()
    tri = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
    mesh.loop_triangles.foreach_get('vertices', tri)
    return world[tri.reshape(-1, 3)]


def surface_points(tris, lo, hi):
    """Points on the triangles that come within the box lo..hi, PITCH apart, with the vertices."""
    keep = np.all(tris.max(1) >= lo, axis=1) & np.all(tris.min(1) <= hi, axis=1)
    points = []
    for a, b, c in tris[keep]:
        n = max(1, min(int(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / PITCH) + 1, 400))
        i, j = np.mgrid[0:n + 1, 0:n + 1]
        ok = i + j <= n
        i, j = i[ok, None] / n, j[ok, None] / n
        points.append(a + i * (b - a) + j * (c - a))
    return np.vstack(points) if points else np.empty((0, 3))


def nearest(points, tree):
    best = math.inf
    for p in points:
        hit = tree.find_nearest(Vector(p))
        if hit[3] is not None and hit[3] < best:
            best = hit[3]
    return best


def lands_from_pcb():
    """{chip: [(pad, centre x, centre y, half x, half y)]} in scene coordinates, metres, frame 1."""
    tree = parse_sexpr((REPO / record['pcb']).read_text(encoding='utf-8'))
    atoms = lambda node: [x for x in node[1:] if not isinstance(x, list)]  # noqa: E731
    out = {}
    for fp in children(tree, 'footprint'):
        ref = 'MAINBOARD/' + str(property_value(fp, 'Reference', 'reference'))
        if ref not in CHIPS:
            continue
        at = atoms(one(fp, 'at'))
        fx, fy, angle = float(at[0]), float(at[1]), float(at[2]) if len(at) > 2 else 0.0
        a = math.radians(angle)
        turned = round(angle) % 180 != 0
        rows = []
        for pad in children(fp, 'pad'):
            pa, size = atoms(one(pad, 'at')), atoms(one(pad, 'size'))
            px, py, sx, sy = float(pa[0]), float(pa[1]), float(size[0]), float(size[1])
            x, y = fx + px * math.cos(a) + py * math.sin(a), fy - px * math.sin(a) + py * math.cos(a)
            hx, hy = (sy / 2, sx / 2) if turned else (sx / 2, sy / 2)
            rows.append((str(pad[1]), x * 1e-3, -y * 1e-3, hx * 1e-3, hy * 1e-3))
        out[ref] = rows
    assert set(out) == CHIPS and all(len(v) == 3 for v in out.values())
    return out


def land_gaps(lands, items, chip_item):
    """Plan distance from each land rectangle to each neighbour, up to the chip's height plus room for an iron.

    The lands come from the PCB file in the board's own frame; the meshes are as displayed at frame 1,
    so every mesh is taken back through the chip's displayed board transform first."""
    to_board = np.linalg.inv(chip_item['matrix'])
    boarded = []
    for item in items:
        tris = item['tris'] @ to_board[:3, :3].T + to_board[:3, 3]
        boarded.append(dict(name=item['name'], tris=tris, lo=tris.min((0, 1)), hi=tris.max((0, 1))))
    rows = []
    for owner, pads in lands.items():
        for number, x, y, hx, hy in pads:
            lo = np.array([x - hx - .002, y - hy - .002, -1.])
            hi = np.array([x + hx + .002, y + hy + .002, SEAT + (CHIP_TOP + IRON) * 1e-3])
            for item in boarded:
                if owner_of(item['name']) == owner:
                    continue
                if not (np.all(item['lo'][:2] <= hi[:2]) and np.all(item['hi'][:2] >= lo[:2]) and item['lo'][2] <= hi[2]):
                    continue
                p = surface_points(item['tris'], lo, hi)
                p = p[(p[:, 2] > SEAT + .05e-3) & (p[:, 2] <= hi[2])]
                if not len(p):
                    continue
                ex, ey = np.abs(p[:, 0] - x) - hx, np.abs(p[:, 1] - y) - hy
                gap = float(np.hypot(np.maximum(ex, 0), np.maximum(ey, 0)).min()) * 1000
                if gap > 2:      # a large far mesh whose bounds happen to span the search box
                    continue
                rows.append(dict(chip=owner, land=number, other=owner_of(item['name']), mesh=item['name'], plan_gap_mm=round(gap, 3)))
    return sorted(rows, key=lambda r: r['plan_gap_mm'])


def screen(path, targets, lands=None):
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
        items.append(dict(name=obj.original.name, world=world, polys=[tuple(p.vertices) for p in obj.data.polygons], tris=triangles_of(obj, world),
                          matrix=m @ np.array(obj.original.matrix_world.inverted()), lo=world.min(0), hi=world.max(0)))
    contacts, near, headroom, overhead = [], [], {}, {}
    rest = [i for i in items if owner_of(i['name']) not in targets]
    verts, polys, poly_owner = [], [], []
    for i in rest:
        base = len(verts)
        verts += [tuple(v) for v in i['world']]
        polys += [tuple(base + k for k in p) for p in i['polys']]
        poly_owner += [i['name']] * len(i['polys'])
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
            forward = nearest(surface_points(u['tris'], item['lo'] - .002, item['hi'] + .002), other)
            backward = nearest(surface_points(item['tris'], u['lo'] - .002, u['hi'] + .002), tree)
            gap = round(min(forward, backward) * 1000, 3)
            near.append(dict(target=owner, other=owner_of(item['name']), mesh=item['name'], gap_mm=gap, triangle_pairs=len(pairs)))
            if pairs or gap < TOUCHING:
                contacts.append(dict(target=owner, other=owner_of(item['name']), mesh=item['name'], triangle_pairs=len(pairs), gap_mm=gap))
        axis = Vector(frame[:3, 2]).normalized()
        top = u['world'][np.argsort(u['world'] @ np.array(axis))[-60:]]
        hits = [world_tree.ray_cast(Vector(p) + axis * 1e-6, axis, 0.3) for p in top]
        dist = [h for h in hits if h[0] is not None]
        lowest = min(dist, key=lambda h: h[3]) if dist else None
        headroom[owner] = round(lowest[3] * 1000, 2) if dist else None
        overhead[owner] = owner_of(poly_owner[lowest[2]]) if dist else None
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    report = dict(scene_sha256=digest, contacts=contacts, near=near, headroom=headroom, overhead=overhead)
    if lands:
        report['land_gaps'] = land_gaps(lands, items, next(i for i in items if owner_of(i['name']) in targets))
    return report


after, before = screen(FINAL, CHIPS, lands_from_pcb()), screen(BASELINE, JFET)
pairs = {f"{c['target']} | {c['other']}" for c in after['contacts']}
closest = {}
for row in after['near']:
    if row['target'] not in closest or row['gap_mm'] < closest[row['target']]['gap_mm']:
        closest[row['target']] = dict(other=row['other'], gap_mm=row['gap_mm'])
closest_land = {}
for row in after['land_gaps']:
    closest_land.setdefault(row['chip'], dict(land=row['land'], other=row['other'], plan_gap_mm=row['plan_gap_mm']))
q128_r105 = [r for r in after['near'] if r['target'] == 'MAINBOARD/Q128' and r['other'] == 'MAINBOARD/R105']
q128_r105_land = [r for r in after['land_gaps'] if r['chip'] == 'MAINBOARD/Q128' and r['other'] == 'MAINBOARD/R105']
q128_fit = fit['chips']['Q128']
fit_r105 = next(r for r in q128_fit['nearest'] if r['ref'] == 'R105')
out = dict(passed=pairs == DECLARED, frame=1, declared=sorted(DECLARED),
           q128_r105=dict(chip_mesh_gap_mm=min(r['gap_mm'] for r in q128_r105), triangle_pairs=sum(r['triangle_pairs'] for r in q128_r105),
                          nearest_land_plan_gap_mm=min(r['plan_gap_mm'] for r in q128_r105_land), nearest_land=min(q128_r105_land, key=lambda r: r['plan_gap_mm'])['land'],
                          fit_check_body_gap_mm=fit_r105['body_gap_mm'], fit_check_land_gap_mm=fit_r105['land_gap_mm']),
           fit_check_touching_the_chip_box=fit['touching_in_the_models'],
           fit_check_difference='fit_check.py measures from a neighbour to boxes built from the largest sizes in the Toshiba S-Mini drawing. '
                                'The chip-mesh gap here is to the stock KiCad SC-59 model, whose body is a little smaller, so it can read wider.',
           chip_contacts=after['contacts'], removed_with_the_jfets=before['contacts'], smallest_gap_per_chip=closest, smallest_land_gap_per_chip=closest_land,
           neighbours=after['near'], land_gaps=after['land_gaps'], headroom_above_chip_mm=after['headroom'], part_above_chip=after['overhead'],
           baseline_scene_sha256=before['scene_sha256'], current_scene_sha256=after['scene_sha256'],
           read_only=True, physical_fit_qualified=False,
           method='Rendered chip meshes versus other component, panel and enclosure meshes within a 2 mm box at frame 1; own geometry and PCB layers excluded. '
                  'Contact = triangle overlap, or a nearest-surface gap under 0.005 mm, from the vertices and from surface points 0.02 mm apart, both ways. '
                  'Headroom = free distance along the board normal from the 60 highest vertices to any other visible mesh. '
                  'Land gap = plan distance from the PCB file\'s pad rectangle, corners not rounded, to the neighbour\'s surface up to the chip\'s height plus 0.3 mm, as in fit_check.py.')
(HERE / 'chip-neighbour-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: out[k] for k in ('passed', 'chip_contacts', 'removed_with_the_jfets', 'smallest_gap_per_chip', 'smallest_land_gap_per_chip', 'q128_r105', 'headroom_above_chip_mm', 'part_above_chip')}, indent=1), flush=True)
assert out['passed']
