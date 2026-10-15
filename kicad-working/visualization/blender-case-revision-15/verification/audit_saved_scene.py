"""Reopen both saved scenes and compare all data, poses and rear apertures.

Allowed differences from revision 14: the declared vertical delta on the I/O
board placement, its 24 wiring-study endpoint ghosts and 5 labels; objects
parented to the I/O placement and every displayed I/O instance, each moving
by exactly that delta in all four views; the three audio nut proxies, whose
displayed instances move by the same world delta; the last 20 mm of the 24
conductors; the new opening guide text and revision scene properties.
Anything else fails.

Objects hidden from the viewport in a frame are not evaluated by Blender, so
their stored matrix_world there is stale data rather than displayed geometry;
those entries are judged by matrix_basis and by the frames in which the
object is visible, and are counted. Tolerance 1e-7 m is above float32
storage resolution near 0.2 m.

Run from the repository root:
  Blender --background --python-exit-code 1 --python \
    kicad-working/visualization/blender-case-revision-15/verification/audit_saved_scene.py
"""
import ast
import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
BASELINE = HERE.parents[1] / 'blender-case-revision-14/x0xb0x-populated-with-case.blend'
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
from scene_snapshot import capture, sha, write_snapshot  # noqa: E402

record = json.loads((HERE.parent / 'revision-15-change-record.json').read_text())
DELTA = [x / 1000.0 for x in record['world_delta_mm']]
MOVED = set(record['moved_objects'])
HARDWARE = set(record['moved_hardware'])
HW_LOCAL = [x / 1000.0 for x in record['hardware_collection_delta_mm']]
WIRES = {w['name'] for w in record['wires']}
BLEND_M = record['wire_end_blend_length_mm'] / 1000.0
IO_EMPTY = 'I/O board — rear mounting approximation'
GUIDE = record['opening_guide']
TOL = 1e-7
checks = []


def check(name, passed, **details):
    checks.append(dict(check=name, passed=bool(passed), **details))


def save(name, report):
    (HERE / name).write_text(json.dumps(report, indent=2) + '\n')


def diff(a, b, path=(), out=None):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(path + (k,))
            else:
                diff(a[k], b[k], path + (k,), out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(path)
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                diff(x, y, path + (i,), out)
    elif isinstance(a, float) and isinstance(b, float):
        if not (a == b or abs(a - b) <= TOL):
            out.append(path)
    elif a != b:
        out.append(path)
    return out


def translated(m, d):
    return [[m[r][c] + (d[r] if c == 3 and r < 3 else 0.0) for c in range(4)] for r in range(4)]


def same(a, b):
    return all(abs(a[r][c] - b[r][c]) <= TOL for r in range(4) for c in range(4))


def stale(path, snap):
    if path[:1] == ('objects',) and len(path) > 2 and path[2] == 'matrix_world':
        return snap['frames']['1']['objects'][path[1]]['hide_viewport']
    if path[:1] == ('frames',) and len(path) > 4 and path[2] == 'objects' and path[4] == 'matrix_world':
        return snap['frames'][path[1]]['objects'][path[3]]['hide_viewport']
    return False


# Load the read-only rear verifier's definitions without its CLI wrapper.
source = REPO / 'scripts/verify_rear_openings.py'
tree = ast.parse(source.read_text(), filename=str(source))
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'original_frame'
                                            for t in node.targets):
        break
    nodes.append(node)
namespace = {'__file__': str(source), '__name__': 'rear_opening_definitions'}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)

baseline_hash, final_hash = sha(BASELINE), sha(FINAL)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
before = json.loads(json.dumps(capture()))
baseline_openings = namespace['verify']()
bpy.ops.wm.open_mainfile(filepath=str(FINAL))
after = json.loads(json.dumps(capture()))
final_openings = namespace['verify']()
io_empty = bpy.data.objects[IO_EMPTY]
io_names = {o.name for o in io_empty.instance_collection.all_objects}
followers = {o.name for o in io_empty.children_recursive}
for o in io_empty.children_recursive:
    if o.instance_collection:
        io_names |= {x.name for x in o.instance_collection.all_objects}
moving = MOVED | followers
native_roots = len([o for o in bpy.data.objects if o.get('source_reference')])
write_snapshot(HERE / 'before-scene.json.gz', before)
write_snapshot(HERE / 'after-scene.json.gz', after)
save('rear-openings-audit.json', final_openings)

check('Change record pins the saved scene and its revision-14 baseline',
      record['stable_scene_sha256'] == final_hash and record['baseline_sha256'] == baseline_hash)
check('Object identities and native reference roots are retained',
      set(before['objects']) == set(after['objects']) and native_roots == 491,
      object_count=len(after['objects']), native_reference_count=native_roots)

REV_PROPS = {'visualization_revision', 'opening_notes_text'}
unexpected, stale_entries, moved_world = [], 0, set()
for path in diff(before, after):
    head = path[0]
    if stale(path, after) and stale(path, before):
        stale_entries += 1
        continue
    if head == 'scene_props' and (path[1] in REV_PROPS or str(path[1]).startswith('revision_15_')):
        continue
    if head == 'texts' and path[1:] == (GUIDE,):
        continue
    if head == 'objects' and path[1] in MOVED and path[2] in ('matrix_basis', 'matrix_world'):
        moved_world.add(path[1])
        continue
    if head == 'objects' and path[1] in followers and path[2] == 'matrix_world':
        continue
    if head == 'objects' and path[1] in HARDWARE and path[2] in ('matrix_basis', 'matrix_world'):
        continue
    if head == 'frames' and path[2] in ('objects', 'displayed') and path[3] in HARDWARE:
        continue
    if head == 'objects' and path[1] in WIRES and path[2:4] == ('data', 'splines'):
        continue
    if head == 'frames' and path[2] == 'objects' and path[3] in moving:
        continue
    if head == 'frames' and path[2] == 'displayed' and (path[3] in io_names or path[3] in moving):
        continue
    unexpected.append([str(p) for p in path])
check('No undeclared differences from revision 14', not unexpected,
      unexpected_count=len(unexpected), first_unexpected=unexpected[:20],
      ignored_stale_hidden_object_matrix_entries=stale_entries)
check('Opening guide and revision properties are the only scene-level additions',
      after['scene_props']['visualization_revision'] == 15
      and after['scene_props']['opening_notes_text'] == GUIDE and GUIDE in after['texts']
      and set(after['texts']) - set(before['texts']) == {GUIDE})

bad = []
for frame, data in after['frames'].items():
    for name in moving:
        if data['objects'][name]['hide_viewport']:
            continue
        if not same(translated(before['frames'][frame]['objects'][name]['matrix_world'], DELTA),
                    data['objects'][name]['matrix_world']):
            bad.append([frame, name])
    for key in io_names:
        old = before['frames'][frame]['displayed'].get(key, [])
        new = data['displayed'].get(key, [])
        if len(old) != len(new):
            bad.append([frame, key, 'instance count'])
            continue
        pending = [translated(m, DELTA) for m in old]
        for m in new:
            hit = next((i for i, w in enumerate(pending) if same(w, m)), None)
            if hit is None:
                bad.append([frame, key])
                break
            pending.pop(hit)
    for key in HARDWARE:
        old = before['frames'][frame]['displayed'][key]
        new = data['displayed'][key]
        if len(old) != len(new) or not all(any(same(translated(o, DELTA), n) for n in new) for o in old):
            bad.append([frame, key, 'hardware'])
shifted = sum(len(after['frames']['1']['displayed'].get(k, [])) for k in io_names)
check('Every displayed I/O instance and visible moved object shifts by exactly the delta in all four views',
      not bad, frames=sorted(after['frames']), displayed_io_instances_frame1=shifted,
      parented_followers=sorted(followers), failures=bad[:20])
basis_bad = [n for n in MOVED if not same(translated(before['objects'][n]['matrix_basis'], DELTA),
                                          after['objects'][n]['matrix_basis'])]
check('All 30 declared placement/study objects move by exactly the delta in matrix_basis',
      not basis_bad and moved_world == MOVED, moved=len(moved_world), failures=basis_bad)
hw_bad = [n for n in HARDWARE if not same(translated(before['objects'][n]['matrix_basis'], HW_LOCAL),
                                          after['objects'][n]['matrix_basis'])]
check('The three audio nut proxies follow the jack axes (collection delta; displayed by world delta)',
      not hw_bad and len(HARDWARE) == 3, hardware=sorted(HARDWARE), failures=hw_bad)
check('Revision 14 axial plate datum is retained (no Y or X component in the delta)',
      DELTA[0] == 0.0 and DELTA[1] == 0.0 and DELTA[2] > 0)

wire_bad, dlen = [], math.sqrt(sum(x * x for x in DELTA))
for name in sorted(WIRES):
    pa = [p['co'][:3] for p in before['objects'][name]['data']['splines'][0]['points']]
    pb = [p['co'][:3] for p in after['objects'][name]['data']['splines'][0]['points']]
    remaining = [0.0] * len(pa)
    for i in range(len(pa) - 2, -1, -1):
        remaining[i] = remaining[i + 1] + math.dist(pa[i], pa[i + 1])
    shifts = [[y - x for x, y in zip(p, q)] for p, q in zip(pa, pb)]
    ok = (all(abs(s - d) <= TOL for s, d in zip(shifts[-1], DELTA))
          and all(abs(c) <= TOL for c in shifts[0])
          and not any(r >= BLEND_M and any(abs(c) > TOL for c in s) for s, r in zip(shifts, remaining))
          and max(math.sqrt(max(0.0, sum(c * c for c in s) - sum(c * d / dlen for c, d in zip(s, DELTA)) ** 2))
                  for s in shifts) <= TOL  # every point moves parallel to the delta
          and max(math.sqrt(sum(c * c for c in s)) for s in shifts) <= dlen + TOL)
    if not ok:
        wire_bad.append(name)
check('24 conductors: I/O end follows the delta; mainboard end and run beyond 20 mm unchanged',
      not wire_bad, failures=wire_bad)
check('Rear apertures pass on revision 14 and revision 15',
      baseline_openings['passed'] and final_openings['passed']
      and final_openings['check_count'] == 44 and final_openings['ray_count'] == 974,
      baseline=[baseline_openings['check_count'], baseline_openings['ray_count']],
      final=[final_openings['check_count'], final_openings['ray_count']])
check('Read-only audit left both saved scenes unchanged',
      sha(BASELINE) == baseline_hash and sha(FINAL) == final_hash)

failures = [c for c in checks if not c['passed']]
report = dict(passed=not failures, check_count=len(checks), failures=failures, checks=checks,
              stable_scene_sha256=final_hash, baseline_sha256=baseline_hash,
              native_reference_count=native_roots, world_delta_mm=record['world_delta_mm'],
              frames=4, snapshot_sha256={n: sha(HERE / n) for n in ('before-scene.json.gz', 'after-scene.json.gz')},
              read_only=True, physical_fit_qualified=False,
              method='Fresh saved-file snapshots of revisions 14 and 15 compare all stored data and evaluated '
                     'instance poses in four views; current 974 rear rays are replayed on both.')
save('final-saved-scene-audit.json', report)
print(json.dumps({k: report[k] for k in ('passed', 'check_count', 'failures')}, indent=2))
assert report['passed'], 'Revision 15 saved-scene audit failed'
