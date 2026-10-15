"""Reopen both saved scenes and compare all data, poses and rear apertures.

Allowed differences from revision 15: the mesh datablocks of the declared part
objects of the 25 updated references; the 14 declared terminal part objects,
their collection links and displayed instances; five provenance properties on
the 25 reference roots; the added terminal material; the new opening guide text
and revision scene properties. Anything else fails, including any change to a
replaced object's pose, parent, collections, flags or properties.

Objects hidden from the viewport in a frame are not evaluated by Blender, so
their stored matrix_world there is stale data rather than displayed geometry;
those entries are judged by matrix_basis and counted. Tolerance 1e-7 m.

Run from the repository root:
  Blender --background --python-exit-code 1 --python \
    kicad-working/visualization/blender-case-revision-16/verification/audit_saved_scene.py
"""
import ast
import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
BASELINE = HERE.parents[1] / 'blender-case-revision-15/x0xb0x-populated-with-case.blend'
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
from scene_snapshot import capture, sha, write_snapshot  # noqa: E402

record = json.loads((HERE.parent / 'revision-16-change-record.json').read_text())
ADDED = set(record['added_objects'])
REPLACED = set(record['replaced_mesh_objects'])
ROOTS = {r['root'] for r in record['references']}
ROOT_KEYS = {'model_classification', 'model_limitations', 'detailed_model_revision',
             'selected_native_source_glb_sha256', 'source_geometry_basis'}
TIN = record['terminal_material']
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
native_roots = len([o for o in bpy.data.objects if o.get('source_reference')])
siblings = {}
for name in ADDED:
    obj = bpy.data.objects[name]
    siblings[name] = sorted(o.name for o in obj.parent.children if o.name != name)
write_snapshot(HERE / 'before-scene.json.gz', before)
write_snapshot(HERE / 'after-scene.json.gz', after)
save('rear-openings-audit.json', final_openings)

check('Change record pins the saved scene and its revision-15 baseline',
      record['stable_scene_sha256'] == final_hash and record['baseline_sha256'] == baseline_hash)
check('All revision-15 objects retained; only the 14 declared terminal objects added; 491 roots',
      set(before['objects']) <= set(after['objects']) and set(after['objects']) - set(before['objects']) == ADDED
      and len(ADDED) == 14 and native_roots == 491,
      before_count=len(before['objects']), after_count=len(after['objects']), native_reference_count=native_roots)

REV_PROPS = {'visualization_revision', 'opening_notes_text'}
added_links = {}
for name in ADDED:
    for c in after['objects'][name]['collections']:
        added_links.setdefault(c, set()).add(name)
unexpected, stale_entries, replaced_seen = [], 0, set()
for path in diff(before, after):
    head = path[0]
    if stale(path, after) and stale(path, before):
        stale_entries += 1
        continue
    if head == 'scene_props' and (path[1] in REV_PROPS or str(path[1]).startswith('revision_16_')):
        continue
    if head == 'texts' and path[1:] == (GUIDE,):
        continue
    if head == 'materials' and path[1:] == (TIN,):
        continue
    if head == 'objects' and path[1] in ADDED and len(path) == 2:
        continue
    if head == 'objects' and path[1] in REPLACED and path[2] == 'data':
        replaced_seen.add(path[1])
        continue
    if head == 'objects' and path[1] in ROOTS and path[2] == 'props' and path[3] in ROOT_KEYS:
        continue
    if head == 'collections' and path[2:] == ('objects',) and path[1] in added_links:
        continue
    if head == 'frames' and path[2] in ('objects', 'displayed') and path[3] in ADDED and len(path) == 4:
        continue
    unexpected.append([str(p) for p in path])
check('No undeclared differences from revision 15', not unexpected,
      unexpected_count=len(unexpected), first_unexpected=unexpected[:20],
      ignored_stale_hidden_object_matrix_entries=stale_entries)
check('Every declared part object received its new native mesh and nothing else changed on it',
      replaced_seen == REPLACED and all(
          after['objects'][n]['data']['hash'] == s['new_mesh']['hash'] and
          before['objects'][n]['data']['hash'] == s['old_mesh']['hash']
          for r in record['references'] for s in r['replaced_meshes'] for n in [s['object']]),
      replaced=len(REPLACED))
check('Collection membership changes are exactly the added terminal objects',
      all(sorted(set(before['collections'][c]['objects']) | names) == after['collections'][c]['objects']
          for c, names in added_links.items()),
      collections=sorted(added_links))
check('Only the terminal material is added; every previous material identical',
      set(after['materials']) - set(before['materials']) == {TIN}
      and all(before['materials'][m] == after['materials'][m] for m in before['materials']))
check('Opening guide and revision properties are the only scene-level additions',
      after['scene_props']['visualization_revision'] == 16
      and after['scene_props']['opening_notes_text'] == GUIDE and GUIDE in after['texts']
      and set(after['texts']) - set(before['texts']) == {GUIDE})
bad = []
for name in sorted(ADDED):
    o = after['objects'][name]
    sib = after['objects'][siblings[name][0]]
    if not (o['parent'] == sib['parent'] and o['collections'] == sib['collections']
            and o['hide_render'] == sib['hide_render'] and o['hide_viewport'] == sib['hide_viewport']
            and o['data']['materials'] == [TIN]):
        bad.append([name, 'attachment'])
    for frame, data in after['frames'].items():
        if len(data['displayed'].get(name, [])) != len(data['displayed'].get(siblings[name][0], [])):
            bad.append([frame, name, 'display'])
check('Terminal objects attach, link and display exactly like their sibling parts in all four views',
      not bad, failures=bad[:20])
check('Rear apertures pass on revision 15 and revision 16',
      baseline_openings['passed'] and final_openings['passed']
      and final_openings['check_count'] == 44 and final_openings['ray_count'] == 974,
      baseline=[baseline_openings['check_count'], baseline_openings['ray_count']],
      final=[final_openings['check_count'], final_openings['ray_count']])
check('Read-only audit left both saved scenes unchanged',
      sha(BASELINE) == baseline_hash and sha(FINAL) == final_hash)

failures = [c for c in checks if not c['passed']]
report = dict(passed=not failures, check_count=len(checks), failures=failures, checks=checks,
              stable_scene_sha256=final_hash, baseline_sha256=baseline_hash,
              native_reference_count=native_roots, added_objects=sorted(ADDED), replaced_mesh_objects=len(REPLACED),
              frames=4, snapshot_sha256={n: sha(HERE / n) for n in ('before-scene.json.gz', 'after-scene.json.gz')},
              read_only=True, physical_fit_qualified=False,
              method='Fresh saved-file snapshots of revisions 15 and 16 compare all stored data and evaluated '
                     'instance poses in four views; current 974 rear rays are replayed on both.')
save('final-saved-scene-audit.json', report)
print(json.dumps({k: report[k] for k in ('passed', 'check_count', 'failures')}, indent=2))
assert report['passed'], 'Revision 16 saved-scene audit failed'
