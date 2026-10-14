"""Read-only comparison of repository-relative revision7 and saved revision8.

This verifier opens both saved files afresh. It does not depend on any source
folder outside the repository and never saves a scene.
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scene_snapshot import capture, sha, write_snapshot

HERE = Path(__file__).resolve().parent
SCENE_DIR = HERE.parent
BASELINE = SCENE_DIR.parent / 'blender-case-revision-7/x0xb0x-populated-with-case.blend'
FINAL = SCENE_DIR / 'x0xb0x-populated-with-case.blend'
record = json.loads((SCENE_DIR / 'revision-8-change-record.json').read_text())
selected = {row['board'] + '/' + row['reference'] for row in record['references']}
checks = []


def check(label, condition):
    checks.append(dict(check=label, passed=bool(condition)))


def without(mapping, keys):
    return {k: v for k, v in mapping.items() if k not in keys}


baseline_hash, final_hash = sha(BASELINE), sha(FINAL)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
before = capture()
bpy.ops.wm.open_mainfile(filepath=str(FINAL))
after = capture()
write_snapshot(HERE / 'before-scene.json.gz', before)
write_snapshot(HERE / 'after-scene.json.gz', after)
check('Baseline revision7 hash matches preserved source', baseline_hash == record['preserved_baseline_sha256'])
check('Saved scene hash matches change record', final_hash == record['saved_scene_sha256'])
b = before['objects']
a = after['objects']
old_refs = {row['reference']: name for name, row in b.items()
            if row['props'].get('source_reference')}
new_refs = {row['reference']: name for name, row in a.items()
            if row['props'].get('source_reference')}
check('All491 original component root identities preserved', old_refs == new_refs and len(new_refs) == 491)
check('409 mainboard and82 I/O references preserved',
      sum(k.startswith('mainboard/') for k in new_refs) == 409 and
      sum(k.startswith('ioboard/') for k in new_refs) == 82)
old_selected_objects = {n for n, row in b.items() if row['reference'] in selected}
new_selected_objects = {n for n, row in a.items() if row['reference'] in selected}
check('Only selected component subtree object identities may change',
      set(b) - old_selected_objects == set(a) - new_selected_objects)
for name, original in b.items():
    if original['reference'] in selected:
        continue
    check('Unchanged object geometry, material links, stored pose, hierarchy and properties: ' + name,
          original == a.get(name))
allowed_root_props = {'model_classification', 'model_limitations', 'source_urls',
    'detailed_model_revision', 'selected_native_source_glb_sha256', 'source_geometry_basis'}
for reference in sorted(selected):
    name = old_refs[reference]
    old = b[name]
    new = a.get(name)
    check('Selected root pose, parent, collections, flags and animation retained: ' + reference,
          new is not None and without(old, {'props'}) == without(new, {'props'}))
    check('Selected root properties differ only in explicit provenance: ' + reference,
          new is not None and without(old['props'], allowed_root_props) == without(new['props'], allowed_root_props))
    check('Selected native geometry actually improves: ' + reference,
          sorted(row['data']['hash'] for row in b.values()
                 if row['reference'] == reference and row['type'] == 'MESH') !=
          sorted(row['data']['hash'] for row in a.values()
                 if row['reference'] == reference and row['type'] == 'MESH'))
for frame in ('1', '80', '120', '160'):
    for name, original in before['frames'][frame]['objects'].items():
        if name in old_selected_objects and name not in old_refs.values():
            continue
        check('Existing object evaluated pose and visibility retained frame' + frame + ': ' + name,
              original == after['frames'][frame]['objects'].get(name))
    for name, original in before['frames'][frame]['displayed'].items():
        if name in old_selected_objects:
            continue
        check('Existing displayed instances retained frame' + frame + ': ' + name,
              original == after['frames'][frame]['displayed'].get(name))
    check('No unselected displayed instance added at frame' + frame,
          set(before['frames'][frame]['displayed']) - old_selected_objects ==
          set(after['frames'][frame]['displayed']) - new_selected_objects)
for name, material in before['materials'].items():
    check('Original material and shader preserved: ' + name, material == after['materials'].get(name))
new_materials = set(after['materials']) - set(before['materials'])
allowed_materials = {material for name in new_selected_objects
                     if a[name]['type'] == 'MESH'
                     for material in a[name]['data']['materials']}
check('All additional materials belong to selected native components', new_materials <= allowed_materials)
for name in sorted(allowed_materials):
    material = after['materials'].get(name)
    role = material['props'].get('revision11_material_role') if material else None
    if not role:
        continue
    shader = material['nodes'].get('Principled BSDF', {})
    inputs = {key.split(':', 1)[-1]: value for key, value in shader.get('inputs', {}).items()}
    check('Selected shader matches its nonmetal body or metal lead role: ' + name,
          inputs.get('Metallic') == (1 if role == 'metal lead' else 0) and
          inputs.get('Emission Strength') == 0 and
          inputs.get('Transmission Weight') == 0 and
          abs(inputs.get('Roughness', -1) - .42) < 1e-6)
for reference in sorted(selected):
    roles = {after['materials'][name]['props'].get('revision11_material_role')
             for obj in a.values() if obj['reference'] == reference and obj['type'] == 'MESH'
             for name in obj['data']['materials'] if name in after['materials']}
    expected_body = 'nonmetal resonator coating' if reference.rsplit('/', 1)[-1].startswith('XTL') else 'nonmetal transistor encapsulation'
    check('Selected component has nonmetal body and metal lead shaders: ' + reference,
          expected_body in roles and 'metal lead' in roles)

check('All original actions and animation curves preserved', before['actions'] == after['actions'])
check('All earlier editable embedded texts preserved as historical evidence', all(after['texts'].get(name) == text for name, text in before['texts'].items()))
opening_name = record['current_opening_notes_text']
check('One explicit current revision8 opening guide added', set(after['texts']) - set(before['texts']) == {opening_name} and hashlib.sha256(after['texts'].get(opening_name, '').encode()).hexdigest() == record['current_opening_notes_sha256'] and 'KiCad revision 11' in after['texts'].get(opening_name, ''))
check('All cameras, timeline bindings and render settings preserved',
      all(before[key] == after[key] for key in ('scene_camera', 'markers', 'render')))
check('No source or display collection identities lost or added', set(before['collections']) == set(after['collections']))
for name, original in before['collections'].items():
    new = after['collections'].get(name, {})
    check('Collection linkage, visibility and source retention preserved: ' + name,
          without(original, {'objects', 'props'}) == without(new, {'objects', 'props'}) and
          set(original['objects']) - old_selected_objects == set(new.get('objects', [])) - new_selected_objects and
          without(original['props'], {'revision_8_content_basis'}) == without(new.get('props', {}), {'revision_8_content_basis'}))
allowed_scene_props = {'visualization_revision', 'native_PCB_model_count',
    'selected_native_revision_11_reference_count', 'revision_8_geometry_basis',
    'revision_8_baseline_scene_sha256', 'opening_notes_text'}
check('Only explicit revision8 scene metadata changes',
      without(before['scene_props'], allowed_scene_props) == without(after['scene_props'], allowed_scene_props))
check('Composite source basis explicitly documented',
      'selected' in after['scene_props'].get('revision_8_geometry_basis', '') and
      after['scene_props'].get('revision_8_baseline_scene_sha256') == baseline_hash)
for row in record['references']:
    for mesh in row['new_meshes']:
        obj = a.get(mesh['object'])
        check('Selected saved mesh equals imported native geometry/material assignment: ' + mesh['object'],
              obj is not None and obj.get('data') == mesh['signature'])
        check('Selected saved mesh remains in all original source/display collections: ' + mesh['object'],
              obj is not None and obj['collections'] == sorted(row['collections']))
        check('Selected saved mesh preserves native board transform: ' + mesh['object'],
              obj is not None and max(abs(x-y) for p, q in zip(obj['matrix_world'], mesh['native_board_matrix']) for x, y in zip(p, q)) < 1e-7)
led_roots = {key for key in new_refs if key.startswith('mainboard/LED')}
check('Exactly40 complete native LED roots and no standalone lens proxies',
      len(led_roots) == 40 and not any(name.endswith(' / visible lens proxy') for name in a))
cap_names = {f'S{i} / switch cap proxy' for i in range(5, 28)}
board_name = 'Mainboard — B.Cu outward in assembled view'
check('Exactly23 preserved PCB-parented caps', cap_names <= set(a) and
      all(a[name]['parent'] == board_name for name in cap_names))
for frame in ('1', '80', '120', '160'):
    for name in sorted(cap_names):
        displayed = after['frames'][frame]['displayed'].get(name, [])
        state = after['frames'][frame]['objects'][name]
        visible = frame in {'1', '80'}
        check('PCB cap original displayed or hidden contract frame' + frame + ': ' + name,
              (len(displayed) == 1 and not state['hide_render'] and not state['hide_viewport']) if visible else
              (not displayed and state['hide_render'] and state['hide_viewport']))
check('Every original curve, wire and label object preserved',
      all(a.get(name) == row for name, row in b.items() if row['type'] in {'CURVE', 'FONT'}))
check('Read-only inspection leaves both saved files unchanged', sha(BASELINE) == baseline_hash and sha(FINAL) == final_hash)
failures = [row for row in checks if not row['passed']]
result = dict(passed=not failures, check_count=len(checks), failures=failures,
    native_reference_count=len(new_refs), selected_reference_count=len(selected),
    selected_references=sorted(selected), baseline_scene_sha256=baseline_hash,
    stable_scene_sha256=final_hash, stable_scene_bytes=FINAL.stat().st_size,
    geometry_basis=after['scene_props'].get('revision_8_geometry_basis'),
    physical_fit_qualified=False, checks=checks)
(HERE / 'final-saved-scene-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: val for key, val in result.items() if key != 'checks'}, indent=2))
assert not failures, 'Saved scene preservation audit failed'
