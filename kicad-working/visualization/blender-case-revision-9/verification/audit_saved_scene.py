"""Read-only fresh-file preservation check for the five rear disk removals.

Six existing audio hardware meshes may change only to acquire through bores.
Every other stored object and every displayed transform remains identical.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import bmesh

HERE = Path(__file__).resolve().parent
SCENE_DIR = HERE.parent
BASELINE = SCENE_DIR.parent / 'blender-case-revision-8/x0xb0x-populated-with-case.blend'
FINAL = SCENE_DIR / 'x0xb0x-populated-with-case.blend'
sys.path.insert(0, str(HERE))
from scene_snapshot import capture, sha, write_snapshot

record = json.loads((SCENE_DIR / 'revision-9-change-record.json').read_text())
removed = set(record['removed_objects'])
hardware = {row['object'] for row in record['hardware_changes']}
checks = []


def check(label, condition):
    checks.append(dict(check=label, passed=bool(condition)))


def without(mapping, keys):
    return {key: value for key, value in mapping.items() if key not in keys}


baseline_hash, final_hash = sha(BASELINE), sha(FINAL)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
before = capture()
old_outer_vertices = {name: [list(v.co) for v in bpy.data.objects[name].data.vertices]
                      for name in hardware}
bpy.ops.wm.open_mainfile(filepath=str(FINAL))
after = capture()
write_snapshot(HERE / 'before-scene.json.gz', before)
write_snapshot(HERE / 'after-scene.json.gz', after)
check('Baseline revision8 hash matches preserved source', baseline_hash == record['preserved_baseline_sha256'])
check('Saved scene hash matches change record', final_hash == record['saved_scene_sha256'])
b, a = before['objects'], after['objects']
expected_removed = {ref + ' / jack recess proxy' for ref in
                    ('CV0', 'GATE0', 'HEADPHONE0', 'MIXIN0', 'MIXOUT0')}
expected_hardware = {ref + suffix for ref in ('HEADPHONE0', 'MIXIN0', 'MIXOUT0')
                     for suffix in (' / black ABS washer proxy', ' / black PA6 nut proxy')}
check('Exactly five named obsolete disks removed', removed == expected_removed and set(b) - set(a) == expected_removed)
check('Exactly six named hardware meshes acquire bores', hardware == expected_hardware)
check('No object identities added', not (set(a) - set(b)))
old_refs = {row['reference']: name for name, row in b.items() if row['props'].get('source_reference')}
new_refs = {row['reference']: name for name, row in a.items() if row['props'].get('source_reference')}
check('All491 original native component root identities preserved', old_refs == new_refs and len(new_refs) == 491)
check('409 mainboard and82 I/O references preserved',
      sum(k.startswith('mainboard/') for k in new_refs) == 409 and
      sum(k.startswith('ioboard/') for k in new_refs) == 82)
for name, original in b.items():
    if name in removed:
        continue
    current = a.get(name)
    check('Stored object pose hierarchy and provenance preserved: ' + name,
          current is not None and without(original, {'data'}) == without(current, {'data'}))
    if name not in hardware:
        check('Original geometry and material assignment preserved: ' + name,
              original.get('data') == current.get('data'))
for row in record['hardware_changes']:
    name = row['object']
    current = bpy.data.objects[name].data
    check('Bored hardware saved geometry matches generation record: ' + name,
          a[name]['data'] == row['saved_mesh_signature'])
    check('Bored hardware retains original material links and mesh properties: ' + name,
          b[name]['data']['materials'] == a[name]['data']['materials'] and
          b[name]['data']['props'] == a[name]['data']['props'])
    check('Every original outer vertex retained on bored hardware: ' + name,
          all(any(max(abs(x-y) for x, y in zip(vertex, v.co)) < 1e-8
                  for v in current.vertices) for vertex in old_outer_vertices[name]))
    actual_bounds = [min(v.co[i] for v in current.vertices) for i in range(3)] + [
        max(v.co[i] for v in current.vertices) for i in range(3)]
    check('Bored hardware original outer extent retained: ' + name,
          max(abs(x-y) for x, y in zip(actual_bounds, row['outer_bounds_before'])) < 1e-8)
    bm = bmesh.new()
    bm.from_mesh(current)
    check('Bored hardware remains one closed manifold mesh: ' + name,
          all(edge.is_manifold for edge in bm.edges) and bm.calc_volume(signed=False) > 0)
    bm.free()
for frame in ('1', '80', '120', '160'):
    old_frame, new_frame = before['frames'][frame], after['frames'][frame]
    for name, original in old_frame['objects'].items():
        if name not in removed:
            check('Existing evaluated pose and visibility retained frame' + frame + ': ' + name,
                  original == new_frame['objects'].get(name))
    check('Only removed objects disappear from evaluated state frame' + frame,
          set(old_frame['objects']) - removed == set(new_frame['objects']))
    for name, original in old_frame['displayed'].items():
        if name not in removed:
            check('Existing displayed instances retained frame' + frame + ': ' + name,
                  original == new_frame['displayed'].get(name))
    check('Only removed disks disappear from displayed instances frame' + frame,
          set(old_frame['displayed']) - removed == set(new_frame['displayed']))
check('All original materials and shaders preserved', before['materials'] == after['materials'])
check('All original actions and animation curves preserved', before['actions'] == after['actions'])
check('All earlier editable embedded texts preserved',
      all(after['texts'].get(name) == text for name, text in before['texts'].items()))
guide = record['current_opening_notes_text']
check('One explicit current revision9 opening guide added',
      set(after['texts']) - set(before['texts']) == {guide} and
      hashlib.sha256(after['texts'][guide].encode()).hexdigest() == record['current_opening_notes_sha256'] and
      'KiCad revision 11' in after['texts'][guide])
check('All cameras timeline bindings and render settings preserved',
      all(before[key] == after[key] for key in ('scene_camera', 'markers', 'render')))
check('No source or display collection identities lost or added', set(before['collections']) == set(after['collections']))
for name, original in before['collections'].items():
    current = after['collections'].get(name, {})
    check('Collection linkage visibility and source retention preserved: ' + name,
          without(original, {'objects'}) == without(current, {'objects'}) and
          set(original['objects']) - removed == set(current.get('objects', [])))
allowed_props = {'visualization_revision', 'opening_notes_text',
                 'revision_9_baseline_scene_sha256', 'revision_9_geometry_basis',
                 'revision_9_removed_rear_proxy_count', 'revision_9_bored_rear_hardware_count'}
check('Only explicit revision9 metadata changes',
      without(before['scene_props'], allowed_props) == without(after['scene_props'], allowed_props))
check('Revision9 basis explicitly distinguishes retained native geometry and hardware correction',
      after['scene_props'].get('visualization_revision') == 9 and
      after['scene_props'].get('revision_9_baseline_scene_sha256') == baseline_hash and
      after['scene_props'].get('revision_9_removed_rear_proxy_count') == 5 and
      after['scene_props'].get('revision_9_bored_rear_hardware_count') == 6)
check('Every original curve wire and editable label object preserved',
      all(a.get(name) == row for name, row in b.items() if row['type'] in {'CURVE', 'FONT'}))
check('Exactly40 complete native LED roots and no standalone lens proxies',
      sum(k.startswith('mainboard/LED') for k in new_refs) == 40 and
      not any(name.endswith(' / visible lens proxy') for name in a))
caps = {f'S{i} / switch cap proxy' for i in range(5, 28)}
check('Exactly23 preserved PCB-parented caps', caps <= set(a) and
      all(a[name]['parent'] == 'Mainboard — B.Cu outward in assembled view' for name in caps))
check('Read-only inspection leaves both saved files unchanged', sha(BASELINE) == baseline_hash and sha(FINAL) == final_hash)
failures = [row for row in checks if not row['passed']]
result = dict(passed=not failures, check_count=len(checks), failures=failures,
              native_reference_count=len(new_refs), removed_disk_count=len(removed),
              bored_hardware_count=len(hardware),
              baseline_scene_sha256=baseline_hash, stable_scene_sha256=final_hash,
              stable_scene_bytes=FINAL.stat().st_size, physical_fit_qualified=False,
              checks=checks)
(HERE / 'final-saved-scene-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'checks'}, indent=2))
assert not failures, 'Saved scene preservation audit failed'
