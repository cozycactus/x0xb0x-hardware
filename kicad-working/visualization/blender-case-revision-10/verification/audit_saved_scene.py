"""Independently compare freshly reopened Blender revisions 9 and 10.

Only the three NYS216 nut mesh datablocks and explicit revision metadata/guide
may change. Neither saved scene is written by this inspection.
"""
import bpy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent.parent / 'blender-case-revision-9/x0xb0x-populated-with-case.blend'
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
sys.path.insert(0, str(HERE))
from scene_snapshot import capture, sha, write_snapshot

NUTS = {ref + ' / black PA6 nut proxy' for ref in
        ('HEADPHONE0', 'MIXIN0', 'MIXOUT0')}
EXPECTED_BASELINE_SHA256 = '96c57c42b2019abb3d4431b63b363587c509890185e0ed895436f103cd535158'
checks = []


def check(name, passed, **details):
    checks.append(dict(check=name, passed=bool(passed), **details))


def without(mapping, excluded):
    return {key: value for key, value in mapping.items() if key not in excluded}


baseline_sha, final_sha = sha(BASELINE), sha(FINAL)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
before = capture()
bpy.ops.wm.open_mainfile(filepath=str(FINAL))
after = capture()
write_snapshot(HERE / 'before-scene.json.gz', before)
write_snapshot(HERE / 'after-scene.json.gz', after)
check('Baseline revision 9 is the previously frozen saved scene',
      baseline_sha == EXPECTED_BASELINE_SHA256)
b, a = before['objects'], after['objects']
check('All original object identities retained, with none added', set(a) == set(b))
changed = {name for name in a if a[name].get('data') != b[name].get('data')}
check('Exactly the three named audio nut mesh datablocks change', changed == NUTS,
      changed_objects=sorted(changed))
for name, original in b.items():
    current = a.get(name)
    check('Stored pose, hierarchy, visibility and provenance preserved: ' + name,
          current is not None and without(original, {'data'}) == without(current, {'data'}))
    if name not in NUTS:
        check('Original geometry and material assignment preserved: ' + name,
              current is not None and original.get('data') == current.get('data'))
    else:
        check('Refined nut retains original material links and mesh properties: ' + name,
              original['data']['materials'] == current['data']['materials']
              and original['data']['props'] == current['data']['props'])

old_refs = {row['reference']: name for name, row in b.items()
            if row['props'].get('source_reference')}
new_refs = {row['reference']: name for name, row in a.items()
            if row['props'].get('source_reference')}
check('All 491 original fitted native component identities retained',
      old_refs == new_refs and len(new_refs) == 491)
check('Native component split remains 409 mainboard and 82 I/O',
      sum(k.startswith('mainboard/') for k in new_refs) == 409
      and sum(k.startswith('ioboard/') for k in new_refs) == 82)
check('All native component mesh signatures unchanged',
      all(a[name] == row for name, row in b.items() if row['reference']))
for frame in ('1', '80', '120', '160'):
    old_frame, new_frame = before['frames'][frame], after['frames'][frame]
    check('Evaluated object identity set retained at frame ' + frame,
          set(old_frame['objects']) == set(new_frame['objects']))
    for name, original in old_frame['objects'].items():
        check('Evaluated pose and visibility retained frame ' + frame + ': ' + name,
              original == new_frame['objects'].get(name))
    check('Displayed instance identity set retained at frame ' + frame,
          set(old_frame['displayed']) == set(new_frame['displayed']))
    for name, original in old_frame['displayed'].items():
        check('Displayed instance matrices retained frame ' + frame + ': ' + name,
              original == new_frame['displayed'].get(name))

check('All original materials and shader graphs retained', before['materials'] == after['materials'])
check('All original actions and animation curves retained', before['actions'] == after['actions'])
check('All collection links, visibility and source retention unchanged',
      before['collections'] == after['collections'])
check('All existing editable embedded texts retained unchanged',
      all(after['texts'].get(name) == text for name, text in before['texts'].items()))
guide = '00 START HERE — revision 10 assembly'
check('Exactly one explicit revision 10 opening guide added',
      set(after['texts']) - set(before['texts']) == {guide}
      and 'KiCad revision 11' in after['texts'].get(guide, ''))
check('All cameras, timeline bindings and render settings retained',
      all(before[key] == after[key] for key in ('scene_camera', 'markers', 'render')))
allowed_props = {'visualization_revision', 'opening_notes_text',
                 'revision_10_baseline_scene_sha256', 'revision_10_geometry_basis',
                 'revision_10_refined_nut_count'}
check('Only explicit revision 10 scene metadata changes',
      without(before['scene_props'], allowed_props) == without(after['scene_props'], allowed_props))
check('Revision 10 metadata declares the actual baseline and three nut refinements',
      after['scene_props'].get('visualization_revision') == 10
      and after['scene_props'].get('revision_10_baseline_scene_sha256') == baseline_sha
      and after['scene_props'].get('revision_10_refined_nut_count') == 3
      and after['scene_props'].get('opening_notes_text') == guide)
check('Every editable label and wire curve remains byte-equivalent in the snapshot',
      all(a.get(name) == row for name, row in b.items() if row['type'] in {'FONT', 'CURVE'}))
check('All 40 complete native LED assemblies and no duplicate lenses retained',
      sum(k.startswith('mainboard/LED') for k in new_refs) == 40
      and not any(name.endswith(' / visible lens proxy') for name in a))
caps = {f'S{i} / switch cap proxy' for i in range(5, 28)}
check('All 23 original PCB-parented caps retained', caps <= set(a)
      and all(a[name] == b[name] and a[name]['parent'] ==
              'Mainboard — B.Cu outward in assembled view' for name in caps))
check('Read-only fresh-file inspection leaves both saved scenes unchanged',
      sha(BASELINE) == baseline_sha and sha(FINAL) == final_sha)
failures = [row for row in checks if not row['passed']]
result = dict(passed=not failures, check_count=len(checks), failures=failures,
              changed_objects=sorted(changed), refined_nut_count=3,
              native_reference_count=len(new_refs), native_LED_count=40,
              button_cap_count=23, baseline_scene_sha256=baseline_sha,
              stable_scene_sha256=final_sha, stable_scene_bytes=FINAL.stat().st_size,
              physical_fit_qualified=False, read_only=True, checks=checks)
(HERE / 'final-saved-scene-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2))
assert not failures, 'Saved-scene preservation audit failed'
