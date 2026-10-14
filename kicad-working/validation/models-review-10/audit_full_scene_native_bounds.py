"""Inspect saved Blender7 native component bounds, never save the scene."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import bpy

HERE = Path(__file__).resolve().parent
step = json.loads((HERE / 'full-scene-step-bounds-input.json').read_text())
path = Path(bpy.data.filepath)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = sha(path)
checks = []


def check(label, passed, detail=None):
    checks.append({'check': label, 'passed': bool(passed), 'detail': detail})


def component_root(obj):
    while obj is not None:
        if obj.get('source_reference'):
            return obj
        obj = obj.parent
    return None


roots = {}
for obj in bpy.data.objects:
    if obj.get('source_reference'):
        key = (obj.get('source_board'), obj['source_reference'])
        roots.setdefault(key, []).append(obj)
check('Native reference roots uniquely identified', all(
    len(objects) == 1 for objects in roots.values()),
    {'duplicates': {str(k): len(v) for k, v in roots.items() if len(v) != 1}})
counts = Counter(board for board, ref in roots)
check('Exactly 491 saved native reference roots', len(roots) == 491,
      dict(counts))
check('Mainboard 409 and I/O 82 saved native references',
      counts == {'mainboard': 409, 'ioboard': 82})

collections = []
for collection in bpy.data.collections:
    if collection.name.startswith('SOURCE /'):
        collections.append({
            'name': collection.name,
            'fake_user': collection.use_fake_user,
            'users': collection.users,
            'object_count': len(collection.objects),
        })
native_collections = [c for c in collections
                      if ' / immutable native KiCad GLB' in c['name']]
check('Both immutable native source collections have persistent fake users',
      len(native_collections) == 2
      and all(c['fake_user'] for c in native_collections),
      native_collections)
check('Every source collection is retained by a real or fake user',
      all(c['users'] > 0 for c in collections),
      [c['name'] for c in collections if not c['users']])

meshes = {}
ignored = []
for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    root = component_root(obj)
    if root is None:
        ignored.append(obj.name)
        continue
    key = (root.get('source_board'), root['source_reference'])
    meshes.setdefault(key, []).append(obj)

records = []
for family in step['records']:
    check('Source valid and hash preserved: ' + family['family'],
          family['valid'] and family['all_solids_valid_positive_volume']
          and family['source_hash_unchanged'])
    check('Source assignment remains canonical: ' + family['family'],
          family['assignment_scale'] == [1, 1, 1]
          and all(a['passed'] for a in family['actual_native_assignments']))
    for ref in family['references']:
        key = (family['board'], ref)
        native = next(a for a in family['actual_native_assignments']
                      if a['reference'] == ref)
        check('Actual PCB model hash and planned unchanged assignment: ' + '/'.join(key),
              native['passed'], native)
        check('Updated reference exists: ' + '/'.join(key),
              key in roots and len(roots[key]) == 1 and key in meshes)
        if key not in roots or len(roots[key]) != 1 or key not in meshes:
            continue
        root = roots[key][0]
        inverse = root.matrix_world.inverted()
        minimum = [float('inf')] * 3
        maximum = [float('-inf')] * 3
        witness_min = [None] * 3
        witness_max = [None] * 3
        vertex_count = polygon_count = 0
        for mesh in meshes[key]:
            local = inverse @ mesh.matrix_world
            vertex_count += len(mesh.data.vertices)
            polygon_count += len(mesh.data.polygons)
            for vertex in mesh.data.vertices:
                position = local @ vertex.co
                xyz = [float(v) * 1000 for v in position]
                for axis in range(3):
                    witness = {'object': mesh.name, 'vertex': vertex.index,
                               'canonical_xyz_mm': xyz}
                    if xyz[axis] < minimum[axis]:
                        minimum[axis] = xyz[axis]
                        witness_min[axis] = witness
                    if xyz[axis] > maximum[axis]:
                        maximum[axis] = xyz[axis]
                        witness_max[axis] = witness
        bounds = minimum + maximum
        residual = [a - b for a, b in zip(
            bounds, family['exact_STEP_bounds_mm'])]
        error = max(abs(x) for x in residual)
        passed = error < .01
        check('Canonical native mesh bounds within 0.01 mm: ' + '/'.join(key),
              passed, {'maximum_bounds_error_mm': error})
        check('Native updated meshes have no modifiers: ' + '/'.join(key),
              all(not obj.modifiers for obj in meshes[key]))
        records.append({
            'board': key[0], 'reference': ref, 'family': family['family'],
            'root_object': root.name,
            'source_step': family['source_step'],
            'source_sha256': family['source_sha256'],
            'STEP_exact_bounds_mm': family['exact_STEP_bounds_mm'],
            'saved_native_mesh_canonical_bounds_mm': bounds,
            'signed_bounds_residual_mm': residual,
            'maximum_bounds_error_mm': error,
            'within_0p01mm': passed,
            'mesh_objects': [obj.name for obj in meshes[key]],
            'vertices': vertex_count, 'polygons': polygon_count,
            'bounds_witnesses': witness_min + witness_max,
        })
check('All updated references measured', len(records) == step['reference_count'])
check('All frozen STEP hashes remain unchanged after inspection', all(
    sha(Path(f['source_step'])) == f['source_sha256']
    for f in step['records']))
after = sha(path)
check('Saved Blender file hash unchanged during read-only audit',
      before == after, {'before': before, 'after': after})
result = {
    'scope': 'Fresh read-only reopen of the saved Blender7. Native component '
             'meshes transformed by source_reference parent inverse, then '
             'metres to millimetres; direct comparison to fresh exact STEP '
             'BRep bounds. Presentation meshes without a source_reference '
             'ancestor are excluded.',
    'scene': str(path), 'scene_sha256': before,
    'saved_initial_frame': bpy.context.scene.frame_current,
    'reference_count': len(roots), 'reference_counts_by_board': dict(counts),
    'updated_reference_count': len(records), 'family_count': step['family_count'],
    'meshing_tolerance_mm': .01,
    'maximum_bounds_error_mm': max(
        (r['maximum_bounds_error_mm'] for r in records), default=None),
    'source_collections': collections,
    'source_collection_persistence_policy': {
        'native_board_sources': 'Both immutable native board source collections '
                                'have explicit fake users.',
        'presentation_sources': 'Case/panel/proxy collections have '
                                'ordinary instance users and no fake user. '
                                'Their retained users are recorded separately.',
        'all_SOURCE_collections_have_fake_users': all(
            c['fake_user'] for c in collections),
        'all_SOURCE_collections_have_persistent_users': all(
            c['users'] > 0 for c in collections),
    },
    'excluded_noncomponent_mesh_count': len(ignored),
    'excluded_noncomponent_meshes': ignored,
    'STEP_input_report': 'full-scene-step-bounds-input.json',
    'families': step['records'], 'records': records, 'checks': checks,
    'check_count': len(checks),
    'failures': [c for c in checks if not c['passed']],
    'limitations': [
        'AABB agreement verifies exported canonical dimensions, not exact '
        'surface equality, terminal fit, installation deformation or assembly '
        'clearance. Native placement and preserved meshes were reviewed by '
        'separate audits.',
        'Curved surfaces are tessellated. The 0.01 mm comparison tolerance '
        'allows mesh chord and float-coordinate differences.',
        'Q22 maximum body and full-diameter leads retain documented installed '
        'stand-off, fanout and trim assumptions. Nominal hole agreement does '
        'not qualify physical forming or fitted hardware.',
        'KK1 retains its full published envelope; the bent regulator pose is a qualified '
        'photo-informed installation illustration. Source seat uncertainty was not '
        'resolved by physical measurements or elastic-fit simulation. Previous source '
        'limits and full shaft dimensions remain documented.',
    ],
}
result['passed'] = not result['failures'] and step['passed']
(HERE / 'full-scene-native-bounds-audit.json').write_text(
    json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in (
    'passed', 'check_count', 'reference_count', 'updated_reference_count',
    'family_count', 'maximum_bounds_error_mm', 'scene_sha256', 'failures')},
    indent=2))
