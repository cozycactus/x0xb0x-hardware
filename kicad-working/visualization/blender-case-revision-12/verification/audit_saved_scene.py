"""Fresh saved 11/12 comparison; only three MIDI FONT bodies may change."""
import hashlib
import gzip
import json
import sys
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent.parent / 'blender-case-revision-11/x0xb0x-populated-with-case.blend'
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
BASELINE_SHA = 'fc02d403f1bcac0aa98937fd29e5f8d77e01f69400104278ea512d36eea01ff9'
FINAL_SHA = '517da1343de66a3e3b5c4848c182bcd263cccca419d3601e5805e0d3402228e1'
GUIDE = '00 START HERE — revision 12 assembly'
GUIDE_SHA = '92e85ac0114eae659b62007cba21aa56614db2f1414265c84873f170ba0ab1f7'
CHANGED = {'DIN1 label', 'DIN2 label', 'DIN3 label'}
sys.path.insert(0, str(HERE))
from scene_snapshot import capture, sha, write_snapshot
from verify_midi_legends import verify

checks = []


def check(name, passed, **details):
    checks.append(dict(check=name, passed=bool(passed), **details))


def without(row, keys):
    return {k: v for k, v in row.items() if k not in keys}


baseline_hash, final_hash = sha(BASELINE), sha(FINAL)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
before_font_ownership = {o.name: dict(data_name=o.data.name, users=o.data.users,
    linked_library=o.data.library.filepath if o.data.library else None)
    for o in bpy.data.objects if o.type == 'FONT'}
before = json.loads(gzip.decompress((HERE / 'before-scene.json.gz').read_bytes())) if '--reuse-snapshots' in sys.argv else capture()
baseline_mapping = verify()
bpy.ops.wm.open_mainfile(filepath=str(FINAL))
after_font_ownership = {o.name: dict(data_name=o.data.name, users=o.data.users,
    linked_library=o.data.library.filepath if o.data.library else None)
    for o in bpy.data.objects if o.type == 'FONT'}
after = json.loads(gzip.decompress((HERE / 'after-scene.json.gz').read_bytes())) if '--reuse-snapshots' in sys.argv else capture()
current_mapping = verify()
write_snapshot(HERE / 'before-scene.json.gz', before)
write_snapshot(HERE / 'after-scene.json.gz', after)
for name, report in [('baseline-midi-legends-audit.json', baseline_mapping),
                     ('midi-legends-audit.json', current_mapping)]:
    (HERE / name).write_text(json.dumps(report, indent=2) + '\n')

check('Baseline11 and final12 are the frozen saved files',
      baseline_hash == BASELINE_SHA and final_hash == FINAL_SHA)
b, a = before['objects'], after['objects']
check('Every stored object identity retained with none added', set(a) == set(b),
      object_count=len(a))
changed_data = {n for n in a if a[n].get('data') != b[n].get('data')}
changed_objects = {n for n in a if a[n] != b[n]}
check('Only the three specified editable FONT objects/data change',
      changed_objects == changed_data == CHANGED,
      changed_objects=sorted(changed_objects), changed_data=sorted(changed_data))
check('Every stored object pose, hierarchy, links, properties and visibility preserved',
      all(without(a[n], {'data'}) == without(row, {'data'}) for n, row in b.items()))
check('Every other mesh, curve, FONT, camera and light data remains exact',
      all(a[n].get('data') == row.get('data') for n, row in b.items() if n not in CHANGED))
check('Every FONT datablock identity, user count and local ownership preserved',
      before_font_ownership == after_font_ownership
      and all(after_font_ownership[n]['users'] == 1 for n in CHANGED),
      font_object_count=len(after_font_ownership),
      corrected_font_ownership={n: after_font_ownership[n] for n in sorted(CHANGED)})
for name in sorted(CHANGED):
    old, new = b[name]['data'], a[name]['data']
    old_format, new_format = old['body_format'], new['body_format']
    check('FONT style/material/textbox fields preserved; only body and automatic glyph bounds change: ' + name,
          b[name]['type'] == a[name]['type'] == 'FONT'
          and without(old, {'settings', 'body_format'}) == without(new, {'settings', 'body_format'})
          and without(old['settings'], {'body', 'texspace_location', 'texspace_size'})
              == without(new['settings'], {'body', 'texspace_location', 'texspace_size'})
          and old['settings']['use_auto_texspace'] == new['settings']['use_auto_texspace'] is True
          and all(old['settings'][k][2] == new['settings'][k][2]
                  for k in ('texspace_location', 'texspace_size'))
          and old['settings']['body'] != new['settings']['body'])
    check('Uniform per-character formatting preserved for new text length: ' + name,
          bool(old_format) and bool(new_format)
          and all(row == old_format[0] for row in old_format + new_format)
          and len(new_format) == len(new['settings']['body']))
check('Electrical graph regression catches exactly three incorrect baseline11 legends',
      not baseline_mapping['passed']
      and {row['object'] for row in baseline_mapping['failures']} == CHANGED)
check('Final editable legends match independent PCB and original Eagle functions',
      current_mapping['passed'],
      expected={row['reference']: row['expected'] for row in current_mapping['checks']},
      original_connected_pad_memberships=current_mapping['original_connected_pad_comparison']['connected_pad_memberships_checked'])
old_refs = {row['reference']: name for name, row in b.items() if row['props'].get('source_reference')}
new_refs = {row['reference']: name for name, row in a.items() if row['props'].get('source_reference')}
check('491 fitted native roots retain identity and every native child remains exact',
      old_refs == new_refs and len(new_refs) == 491
      and all(a[n] == row for n, row in b.items() if row['reference']))
check('Native split remains409 mainboard/82 IO',
      sum(n.startswith('mainboard/') for n in new_refs) == 409
      and sum(n.startswith('ioboard/') for n in new_refs) == 82)
check('All40 native LEDs remain exact with no duplicate lens proxies',
      sum(n.startswith('mainboard/LED') for n in new_refs) == 40
      and not any(n.endswith(' / visible lens proxy') for n in a))
caps = {f'S{i} / switch cap proxy' for i in range(5, 28)}
check('All23 board-parented button caps remain exact',
      caps <= set(a) and all(a[n] == b[n]
      and a[n]['parent'] == 'Mainboard — B.Cu outward in assembled view' for n in caps))
hardware = {n for n in a if n.endswith((' / black ABS washer proxy', ' / black PA6 nut proxy'))}
check('All6 rear audio hardware meshes remain exact',
      len(hardware) == 6 and all(a[n] == b[n] for n in hardware))
for frame in ('1', '80', '120', '160'):
    old, new = before['frames'][frame], after['frames'][frame]
    check('Every evaluated object pose/visibility remains exact frame' + frame,
          old['objects'] == new['objects'], object_count=len(old['objects']))
    check('Every actual displayed instance matrix/identity remains exact frame' + frame,
          old['displayed'] == new['displayed'], instance_object_count=len(old['displayed']))
    changed_glyphs = {n for n in set(old['glyph_geometry']) | set(new['glyph_geometry'])
                      if old['glyph_geometry'].get(n) != new['glyph_geometry'].get(n)}
    check('Generated glyph geometry differs only for corrected text frame' + frame,
          changed_glyphs == CHANGED, changed_objects=sorted(changed_glyphs))
for field in ('materials', 'actions', 'collections', 'fonts'):
    check('All ' + field + ' retained exactly', before[field] == after[field])
check('All historical embedded guides retained unchanged',
      all(after['texts'].get(n) == text for n, text in before['texts'].items()))
check('Exactly one current revision12 guide added with declared content',
      set(after['texts']) - set(before['texts']) == {GUIDE}
      and hashlib.sha256(after['texts'][GUIDE].encode()).hexdigest() == GUIDE_SHA)
check('Camera bindings, timeline markers and render settings retained exactly',
      all(before[k] == after[k] for k in ('scene_camera', 'markers', 'render')))
allowed = {'visualization_revision', 'opening_notes_text',
           'revision_12_baseline_scene_sha256', 'revision_12_geometry_basis',
           'revision_12_corrected_midi_legend_count'}
check('Only declared revision12 metadata changes',
      without(before['scene_props'], allowed) == without(after['scene_props'], allowed))
check('Revision12 metadata declares actual baseline and three corrected legends',
      after['scene_props'].get('visualization_revision') == 12
      and after['scene_props'].get('opening_notes_text') == GUIDE
      and after['scene_props'].get('revision_12_baseline_scene_sha256') == baseline_hash
      and after['scene_props'].get('revision_12_corrected_midi_legend_count') == 3)
check('Read-only inspection preserves both saved files',
      sha(BASELINE) == baseline_hash and sha(FINAL) == final_hash)
failures = [row for row in checks if not row['passed']]
out = dict(passed=not failures, check_count=len(checks),
           baseline_scene_sha256=baseline_hash, stable_scene_sha256=final_hash,
           stable_scene_bytes=FINAL.stat().st_size, changed_objects=sorted(changed_objects),
           corrected_midi_legend_count=3, native_reference_count=491,
           native_LED_count=40, button_cap_count=23, stored_object_count=len(a),
           frame_count=4, failures=failures, checks=checks, read_only=True,
           physical_fit_qualified=False,
           snapshot_hashes={n: sha(HERE / n) for n in ('before-scene.json.gz', 'after-scene.json.gz')},
           method='Freshly reopen both saved files; compare complete compressed snapshots with aggregate exhaustive equality checks. Only three FONT bodies, their generated glyph meshes and automatic texture-space XY caches may differ, plus declared revision metadata/guide. Automatic caches are separately checked against actual local glyph bounds.')
(HERE / 'final-saved-scene-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'checks'}, indent=2))
assert not failures, 'Saved-scene preservation audit failed'
