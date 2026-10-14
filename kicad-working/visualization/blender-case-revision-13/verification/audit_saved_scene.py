"""Reopen both saved scenes and compare all data, poses and rear apertures."""
import ast
import hashlib
import json
import sys
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
BASELINE = HERE.parents[1] / 'blender-case-revision-12/x0xb0x-populated-with-case.blend'
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
from scene_snapshot import capture, sha, write_snapshot
sys.path.insert(0, str(HERE.parents[1] / 'blender-case-revision-12/verification'))
from verify_midi_legends import verify as verify_midi

record = json.loads((HERE.parent / 'revision-13-change-record.json').read_text())
checks = []
def check(name, passed, **details):
    checks.append(dict(check=name, passed=bool(passed), **details))
def without(row, keys):
    return {k: v for k, v in row.items() if k not in keys}
def save(name, report):
    (HERE / name).write_text(json.dumps(report, indent=2) + '\n')

# Load the read-only verifier's definitions without executing its CLI wrapper.
source = REPO / 'scripts/verify_rear_openings.py'
tree = ast.parse(source.read_text(), filename=str(source))
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'original_frame' for t in node.targets):
        break
    nodes.append(node)
namespace = {'__file__': str(source), '__name__': 'rear_opening_definitions'}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
baseline_hash, final_hash = sha(BASELINE), sha(FINAL)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
before = capture()
baseline_openings = namespace['verify']()
bpy.ops.wm.open_mainfile(filepath=str(FINAL))
after = capture()
final_openings = namespace['verify']()
midi = verify_midi()
write_snapshot(HERE / 'before-scene.json.gz', before)
write_snapshot(HERE / 'after-scene.json.gz', after)
save('baseline-corrected-contact-regression.json', baseline_openings)
save('rear-openings-audit.json', final_openings)
save('midi-legends-audit.json', midi)
mesh_names = {'IOBOARD/DIN' + str(i) + '/mesh' for i in range(1, 5)}
root_names = {'IOBOARD/DIN' + str(i) for i in range(1, 5)}
root_keys = {'model_classification', 'model_limitations', 'source_urls', 'detailed_model_revision',
             'selected_native_source_glb_sha256', 'source_geometry_basis'}
b, a = before['objects'], after['objects']
changed = {n for n in a if a[n] != b.get(n)}
check('Both saved files match the frozen build record', baseline_hash == record['baseline_sha256']
      and final_hash == record['stable_scene_sha256'])
check('All1661 object identities retained', set(a) == set(b) and len(a) == 1661)
check('Exactly four mesh data and four source metadata roots change', changed == mesh_names | root_names,
      changed_objects=sorted(changed))
for name, old in b.items():
    new = a[name]
    if name in mesh_names:
        check('Only native mesh data changed: ' + name, without(old, {'data'}) == without(new, {'data'}))
        expected = next(r['new_mesh'] for r in record['references'] if r['object'] == name)
        check('Saved mesh matches the native KiCad export record: ' + name, new['data'] == expected)
    elif name in root_names:
        check('Only declared source metadata changed: ' + name,
              without(old, {'props'}) == without(new, {'props'})
              and without(old['props'], root_keys) == without(new['props'], root_keys)
              and new['props']['detailed_model_revision'] == 12)
check('All other object data, poses, hierarchy, links and visibility retained',
      all(a[n] == old for n, old in b.items() if n not in mesh_names | root_names))
refs = {v['reference'] for v in a.values() if v['props'].get('source_reference')}
check('All491 fitted references retained with native409/82 split',
      len(refs) == 491 and sum(r.startswith('mainboard/') for r in refs) == 409
      and sum(r.startswith('ioboard/') for r in refs) == 82)
check('All40 native LEDs and23 button caps retained exactly',
      sum(r.startswith('mainboard/LED') for r in refs) == 40
      and all(a[n] == b[n] for n in a if '/LED' in n or n.endswith(' / switch cap proxy'))
      and sum(n.endswith(' / switch cap proxy') for n in a) == 23)
for frame in ('1', '80', '120', '160'):
    check('All evaluated object poses and visibility retained frame' + frame,
          before['frames'][frame]['objects'] == after['frames'][frame]['objects'])
    check('Every actual displayed instance matrix retained frame' + frame,
          before['frames'][frame]['displayed'] == after['frames'][frame]['displayed'])
    check('All evaluated legend glyph geometry retained frame' + frame,
          before['frames'][frame]['glyph_geometry'] == after['frames'][frame]['glyph_geometry'])
for field in ('materials', 'actions', 'collections', 'fonts', 'scene_camera', 'markers', 'render'):
    check('All ' + field + ' retained exactly', before[field] == after[field])
check('Every historical embedded guide retained', all(after['texts'].get(n) == v for n, v in before['texts'].items()))
guide = record['opening_guide']
check('Exactly one declared current guide added', set(after['texts']) - set(before['texts']) == {guide}
      and hashlib.sha256(after['texts'][guide].encode()).hexdigest() == record['opening_guide_sha256'])
scene_keys = {'visualization_revision', 'opening_notes_text', 'revision_13_baseline_scene_sha256',
              'revision_13_geometry_basis', 'revision_13_corrected_DIN_count', 'revision_13_KiCad_revision'}
check('Only declared scene revision metadata changed',
      without(before['scene_props'], scene_keys) == without(after['scene_props'], scene_keys)
      and after['scene_props']['visualization_revision'] == 13
      and after['scene_props']['revision_13_corrected_DIN_count'] == 4)
expected_failed = {'DIN' + str(i) + ' has five open contact bores through its insert' for i in range(1, 5)}
check('Primary-drawing contact regression catches exactly four old DIN patterns',
      not baseline_openings['passed']
      and {c['check'] for c in baseline_openings['failures']} == expected_failed,
      failed_sample_count=sum(sum(not o['passed'] for o in c['observations']) for c in baseline_openings['failures']))
check('All current eleven rear connector checks pass', final_openings['passed']
      and final_openings['check_count'] == 44 and final_openings['ray_count'] == 974)
check('Four MIDI legends retain independent original circuit functions', midi['passed'])
check('Read-only audit preserves both saved files', sha(BASELINE) == baseline_hash and sha(FINAL) == final_hash)
failures = [r for r in checks if not r['passed']]
out = dict(passed=not failures, check_count=len(checks), failures=failures, checks=checks,
           stable_scene_sha256=final_hash, baseline_sha256=baseline_hash,
           native_reference_count=491, changed_objects=sorted(changed), frames=4,
           snapshot_sha256={n: sha(HERE / n) for n in ('before-scene.json.gz', 'after-scene.json.gz')},
           read_only=True, physical_fit_qualified=False,
           method='Fresh saved-file snapshots compare all stored data and evaluated poses; four native mesh datums are preserved. Primary-pattern BVH regression, current974 rear rays and original circuit-function checks are replayed.')
save('final-saved-scene-audit.json', out)
print(json.dumps({k: v for k, v in out.items() if k != 'checks'}, indent=2), flush=True)
assert not failures, 'Saved-scene preservation audit failed'
