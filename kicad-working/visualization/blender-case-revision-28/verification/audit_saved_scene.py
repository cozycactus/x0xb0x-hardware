"""Fresh saved-file comparison of revisions 27 and 28: the chips, the do-not-place pairs, the mainboard layers and metadata only."""
import ast, json, sys, hashlib, math
from pathlib import Path
import bpy
import numpy as np
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BASELINE = HERE.parents[1] / 'blender-case-revision-27/x0xb0x-populated-with-case.blend'
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / 'kicad-import/validation'))
sys.dont_write_bytecode = True
from scene_snapshot import capture, sha, write_snapshot  # noqa: E402
from verify_native_projects import children, one, parse_sexpr, property_value  # noqa: E402
record = json.loads((HERE.parent / 'revision-28-change-record.json').read_text())
SOURCE = 'SOURCE / mainboard / immutable native KiCad GLB — revision 10'
checks = []


def check(name, passed, **details):
    checks.append(dict(check=name, passed=bool(passed), **details))


def diff(a, b, path=()):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(path + (k,))
            else:
                out += diff(a[k], b[k], path + (k,))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(path)
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out += diff(x, y, path + (i,))
    elif isinstance(a, float) and isinstance(b, float):
        if abs(a - b) > 1e-7:
            out.append(path)
    elif a != b:
        out.append(path)
    return out


source = REPO / 'scripts/verify_rear_openings.py'
tree = ast.parse(source.read_text())
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'original_frame' for t in node.targets):
        break
    nodes.append(node)
ns = {'__file__': str(source)}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), ns)
bhash, fhash, pcb_hash = sha(BASELINE), sha(FINAL), sha(REPO / record['pcb'])
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
before = json.loads(json.dumps(capture()))
old_openings = ns['verify']()
bpy.ops.wm.open_mainfile(filepath=str(FINAL))
after = json.loads(json.dumps(capture()))
openings = ns['verify']()
write_snapshot(HERE / 'before-scene.json.gz', before)
write_snapshot(HERE / 'after-scene.json.gz', after)
(HERE / 'rear-openings-audit.json').write_text(json.dumps(openings, indent=2) + '\n')

guide = record['opening_guide']
added_refs, removed_refs, layers = record['added_references'], record['removed_do_not_place_references'], record['layer_changes']
added_objects = set(added_refs) | {v['mesh_object'] for v in added_refs.values()}
removed_objects = set(removed_refs) | {v['mesh_object'] for v in removed_refs.values()}
changed_objects = added_objects | removed_objects
added_materials, retired = set(record['added_materials']), set(record['retired_materials'])
layer_keys = {'selected_native_revision', 'selected_native_source_glb_sha256'}
unexpected = []
for path in diff(before, after):
    if path[0] == 'scene_props' and (path[1] in {'visualization_revision', 'opening_notes_text'} or str(path[1]).startswith('revision_28_')):
        continue
    if path[:2] == ('texts', guide):
        continue
    if path[0] == 'objects' and path[1] in changed_objects:
        continue
    if path[0] == 'objects' and path[1] in layers and (path[2] == 'data' or (path[2] == 'props' and path[3] in layer_keys)):
        continue
    if path[0] == 'frames' and path[2] in {'objects', 'displayed'} and path[3] in changed_objects:
        continue
    if path[:3] == ('collections', SOURCE, 'objects'):
        continue
    if path[0] == 'materials' and len(path) == 2 and path[1] in added_materials | retired:
        continue
    unexpected.append([str(p) for p in path])
users = {}
for name, o in before['objects'].items():
    for m in (o.get('data') or {}).get('materials', []) if o['type'] == 'MESH' else []:
        users.setdefault(m, set()).add(name)
check('Both frozen files match recorded hashes', bhash == record['baseline_sha256'] and fhash == record['stable_scene_sha256'])
check('Exactly the 8 chip objects are added and the 8 SIP pair objects removed; 1721 objects stored',
      set(after['objects']) - set(before['objects']) == added_objects and set(before['objects']) - set(after['objects']) == removed_objects
      and len(added_objects) == len(removed_objects) == 8 and len(after['objects']) == 1721)
check('The mainboard source collection lists exactly those changes',
      set(after['collections'][SOURCE]['objects']) - set(before['collections'][SOURCE]['objects']) == added_objects
      and set(before['collections'][SOURCE]['objects']) - set(after['collections'][SOURCE]['objects']) == removed_objects)
check('Only declared objects, the layer meshes, materials and metadata change', not unexpected, unexpected=unexpected[:30])
pcb = parse_sexpr((REPO / record['pcb']).read_text(encoding='utf-8'))
atoms = lambda node: [x for x in node[1:] if not isinstance(x, list)]  # noqa: E731
placed = {property_value(fp, 'Reference', 'reference'): atoms(one(fp, 'at')) for fp in children(pcb, 'footprint')}
positions = {}
for name, row in added_refs.items():
    at = placed[row['reference']]
    x, y, angle = float(at[0]), float(at[1]), float(at[2]) if len(at) > 2 else 0.0
    m = np.array(after['objects'][name]['matrix_world'])
    a = math.radians(angle)
    rotation = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    positions[row['reference']] = dict(kicad_mm=[x, y, angle], scene_mm=[float(m[0, 3] * 1000), float(m[1, 3] * 1000), float(m[2, 3] * 1000)],
                                       offset_mm=max(abs(m[0, 3] * 1000 - x), abs(m[1, 3] * 1000 + y)), rotation_error=float(np.abs(m[:2, :2] - rotation).max()))
check('All 4 chips stand at their KiCad positions and rotations',
      len(positions) == 4 and all(p['offset_mm'] < 1e-3 and p['rotation_error'] < 1e-6 and abs(p['scene_mm'][2] - 1.595) < 1e-3 for p in positions.values())
      and all(after['objects'][n]['parent'] == 'Node_0' for n in added_refs), positions=positions)
check('All 4 chip meshes and all 4 removed pairs match the recorded native geometry',
      all(after['objects'][v['mesh_object']]['data'] == v['mesh'] for v in added_refs.values())
      and all(before['objects'][v['mesh_object']]['data'] == v['mesh'] for v in removed_refs.values()))
check('All 8 mainboard layer meshes match the recorded old and new geometry and keep their scene material',
      len(layers) == 8 and all(before['objects'][n]['data'] == v['old_mesh'] and after['objects'][n]['data'] == v['new_mesh']
                               and after['objects'][n]['data']['materials'] == before['objects'][n]['data']['materials'] for n, v in layers.items()))
io_layers = [n for n in before['objects'] if n.startswith('IOBOARD/PCB layers/')]
check('Every I/O board layer mesh is unchanged', len(io_layers) > 8 and all(before['objects'][n] == after['objects'][n] for n in io_layers), count=len(io_layers))
check('Every previous material is retained exactly, except those used only by the removed pairs',
      all(before['materials'][m] == after['materials'][m] for m in before['materials'] if m not in retired) and
      all(m not in after['materials'] and users.get(m, set()) <= removed_objects for m in retired),
      retired=sorted(retired), retired_users={m: sorted(users.get(m, ())) for m in sorted(retired)})
check('Exactly 3 materials are added, used only by the chip meshes',
      set(after['materials']) - set(before['materials']) == added_materials and len(added_materials) == 3
      and {m for n, o in after['objects'].items() if n not in added_objects and o['type'] == 'MESH' for m in o['data']['materials']}.isdisjoint(added_materials))
refs = [o['props'] for o in after['objects'].values() if o['props'].get('source_reference')]
main = {p['source_reference'] for p in refs if p['source_board'] == 'mainboard'}
check('491 references (409 + 82) with the chips and without the pairs; 40 LEDs, 40 spacers and 23 caps retained',
      len(refs) == 491 and len(main) == 409 and {v['reference'] for v in added_refs.values()} <= main and not {v['reference'] for v in removed_refs.values()} & main
      and sum(r.startswith('LED') for r in main) == 40 and sum(n.endswith('/STD240B spacer') for n in after['objects']) == 40
      and sum(n.endswith(' / switch cap proxy') for n in after['objects']) == 23)
same = all({k: v for k, v in before['frames'][f]['displayed'].items() if k not in removed_objects}
           == {k: v for k, v in after['frames'][f]['displayed'].items() if k not in added_objects}
           and before['frames'][f]['glyph_geometry'] == after['frames'][f]['glyph_geometry'] for f in ['1', '80', '120', '160'])
check('Every other displayed instance pose and legend glyph retained in four frames', same)
follow = {}
for f in ['1', '80', '120', '160']:
    # The board instance's transform, from an unchanged neighbour displayed in the same frame.
    neighbour = 'MAINBOARD/IC4/mesh'
    shown = after['frames'][f]['displayed'].get(neighbour, [])
    for row in added_refs.values():
        rows = after['frames'][f]['displayed'].get(row['mesh_object'], [])
        error = 0.0
        if shown and rows:
            board = np.array(shown[0]) @ np.linalg.inv(np.array(after['objects'][neighbour]['matrix_world']))
            error = float(np.abs(np.array(rows[0]) - board @ np.array(after['objects'][row['mesh_object']]['matrix_world'])).max())
        follow[f + '/' + row['reference']] = dict(instances=len(rows), neighbour_instances=len(shown), error=error)
check('The chips follow the mainboard, shown exactly when an unchanged neighbour is, in all four frames',
      len(follow) == 16 and all(v['instances'] == v['neighbour_instances'] and v['error'] < 1e-6 for v in follow.values())
      and any(v['instances'] for v in follow.values()), follow=follow)
check('Only one current opening guide added', set(after['texts']) - set(before['texts']) == {guide} and
      hashlib.sha256(after['texts'][guide].encode()).hexdigest() == record['opening_guide_sha256'])
check('All rear passages remain clear', old_openings['passed'] and openings['passed'] and openings['check_count'] == 44 and openings['ray_count'] == 974)
check('Frozen scene files and the PCB remain byte-identical after audit', sha(BASELINE) == bhash and sha(FINAL) == fhash and sha(REPO / record['pcb']) == pcb_hash)
failures = [c for c in checks if not c['passed']]
out = dict(passed=not failures, check_count=len(checks), checks=checks, failures=failures, stable_scene_sha256=fhash,
           baseline_sha256=bhash, frames=4, native_reference_count=491, stored_object_count=len(after['objects']),
           added_references=sorted(added_refs), removed_do_not_place_references=sorted(removed_refs), changed_layer_meshes=sorted(layers),
           added_materials=sorted(added_materials), retired_materials=sorted(retired), read_only=True, physical_fit_qualified=False)
(HERE / 'final-saved-scene-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(dict(passed=out['passed'], check_count=len(checks), failures=failures), indent=2), flush=True)
assert not failures
