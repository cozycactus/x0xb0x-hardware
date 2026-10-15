"""Replace the 212 resistor part meshes with native KiCad revision-22 banded geometry.

Each resistor reference has one part mesh in the scene and in the native export, so
only its mesh data changes; the native mesh has one slot per body, band and lead colour. Native slot colours
that match one of the part's previous materials keep that material; the others use a
new material copied from the native export, one per colour, shared by all references.
Previous materials are never modified, and materials left unused by the replaced
meshes are dropped on save. Every object, pose, collection link and property except
the declared root source fields is retained.

Run from the repository root:
  Blender --background --factory-startup \
      kicad-working/visualization/blender-case-revision-24/x0xb0x-populated-with-case.blend \
      --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-25/update_resistors.py
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy

H = Path(__file__).resolve().parent
W = H.parents[1]
sys.path.insert(0, str(H / 'verification'))
from scene_snapshot import sha, material_signature, mesh_signature, matrix  # noqa: E402

BASE = H.parent / 'blender-case-revision-24/x0xb0x-populated-with-case.blend'
OUT = H / 'x0xb0x-populated-with-case.blend'
REVIEW = W / 'validation/models-review-22'
assert Path(bpy.data.filepath).resolve() == BASE.resolve() and not OUT.exists()
EXPORTS = json.loads((REVIEW / 'native-export-record.json').read_text())['boards']
plan = json.loads((REVIEW / 'combined-model-plan.json').read_text())
rows = {(a['board'], r): a for a in plan['updated_assignments'] for r in a['references']}
assert len(rows) == 212
audit = json.loads((REVIEW / 'resistor-quality/resistor-model-audit.json').read_text())
ROLE = {tuple(v): f'{k.lower()} band' for k, v in audit['colours'].items()}
ROLE.update({tuple(v): f'{k} body' for k, v in audit['body_colours'].items()})
ROLE[tuple(audit['lead_colour'])] = 'leads'
linear = lambda c: tuple(((v + .055) / 1.055) ** 2.4 for v in c)  # noqa: E731
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
baseline = sha(BASE)
objects = {o.name for o in bpy.data.objects}
old_materials = {m.name: material_signature(m) for m in bpy.data.materials}
old_sets = {n: set(getattr(bpy.data, n)) for n in ('collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions')}


def rgb(m):
    return tuple(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)


def close(a, b, tol=1e-6):
    return max(abs(x - y) for x, y in zip(a, b)) <= tol


def gap(a, b):
    return max(abs(v - w) for x, y in zip(a, b) for v, w in zip(x, y))


def role_of(colour):
    return next((name for c, name in ROLE.items() if close(colour[:3], linear(c), 2e-3)), None)


new_materials, changes, previous_materials = {}, {}, set()
for board, prefix in (('mainboard', 'MAINBOARD'), ('ioboard', 'IOBOARD')):
    source = REVIEW / EXPORTS[board]['glb']
    assert sha(source) == EXPORTS[board]['glb_sha256']
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(source))
    bpy.context.view_layer.update()
    imported = set(bpy.data.objects) - before
    glb_base = next(o for o in imported if o.parent is None)
    native = {o.name.split('.')[0]: o for o in glb_base.children}
    for (b, ref), row in sorted(rows.items()):
        if b != board:
            continue
        root = bpy.data.objects[f'{prefix}/{ref}']
        incoming = native[ref]
        assert gap(root.parent.matrix_world.inverted() @ root.matrix_world,
                   glb_base.matrix_world.inverted() @ incoming.matrix_world) < 1e-6, ref
        (target,) = [o for o in root.children_recursive if o.type == 'MESH']
        (part,) = [o for o in incoming.children_recursive if o.type == 'MESH']
        keep = list(target.data.materials)
        previous_materials |= {m.name for m in keep}
        local = target.matrix_world.inverted() @ part.matrix_world
        normals = [(local.to_3x3().inverted().transposed() @ n.vector).normalized() for n in part.data.corner_normals]
        mesh = part.data.copy()
        mesh.name = f'{target.name}/revision22 native'
        mesh.transform(local)
        mesh.normals_split_custom_set(normals)
        mapping = []
        for index, material in enumerate(mesh.materials):
            colour = rgb(material)
            role = role_of(colour)
            assert role, (ref, colour)
            match = next((m for m in keep if close(rgb(m), colour)), None)
            if match is None:
                key = tuple(round(c, 6) for c in colour[:3])
                if key not in new_materials:
                    copy = material.copy()
                    copy.name = f'Resistor {role} — revision 25 (native KiCad colour)'
                    new_materials[key] = copy
                match = new_materials[key]
            mesh.materials[index] = match
            mapping.append(dict(slot=index, role=role, native_colour=list(colour), scene_material=match.name))
        old_signature = mesh_signature(target.data)
        previous = target.data
        target.data = mesh
        if previous.users == 0:
            bpy.data.meshes.remove(previous)
        changes[target.name] = dict(reference=ref, board=board, model=row['local_model'], old_mesh=old_signature,
                                    new_mesh=mesh_signature(mesh), canonical_transform=matrix(local), material_mapping=mapping)
        root['model_classification'] = row['classification']
        root['model_limitations'] = ' | '.join(row['limitations'])
        root['detailed_model_revision'] = 22
        root['selected_native_source_glb_sha256'] = EXPORTS[board]['glb_sha256']
        root['source_geometry_basis'] = ('Native KiCad22 DIN0207 resistor: unchanged KiCad body and leads with flush original-kit '
                                         'colour bands; original PCB placement and model transform retained')
    for o in imported:
        bpy.data.objects.remove(o, do_unlink=True)
for name in old_sets:
    block = getattr(bpy.data, name)
    for item in set(block) - old_sets[name]:
        if item.users == 0:
            block.remove(item)
assert len(changes) == 212
NEW = {m.name for m in new_materials.values()}
assert {o.name for o in bpy.data.objects} == objects
assert {m.name: material_signature(m) for m in bpy.data.materials if m.name not in NEW} == old_materials
retired = sorted(m.name for m in bpy.data.materials if m.name in previous_materials and m.users == 0)
guide = bpy.data.texts.new('00 START HERE — revision25 assembly')
guide.write('''x0xb0x Blender25 / KiCad22
All 212 fixed resistors carry the original kit's colour bands, read from the
original parts page: tan 5% carbon-film bodies with four bands and light-blue
1% metal-film bodies (R4, R5, R106, R74-R90) with five. Body and lead geometry
are the unchanged KiCad DIN0207 models; bands are flush. Upright parts read
from the top, lying parts from the pad-1 end. R16 and R106 follow the parts
page (150 ohm, 24.0K 1%); the 40 LED resistors carry the PCB value (10K).
Band positions and colour values are illustrations. The Xicon XRL
electrolytics of revision 24 and every other object are unchanged.
Frames 1 assembled, 80 exploded, 120 control-side, 160 wiring study.
''')
scene['visualization_revision'] = 25
scene['opening_notes_text'] = guide.name
scene['revision_25_baseline_scene_sha256'] = baseline
scene['revision_25_KiCad_revision'] = 22
scene['revision_25_updated_reference_count'] = 212
scene.frame_set(1)
bpy.context.view_layer.update()
assert sha(BASE) == baseline
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True, check_existing=False)
record = dict(passed=True, visualization_revision=25, kicad_revision=22, baseline_sha256=baseline, stable_scene_sha256=sha(OUT),
              stable_scene_bytes=OUT.stat().st_size, source_glb_sha256={b: EXPORTS[b]['glb_sha256'] for b in EXPORTS},
              source_plan_sha256=sha(REVIEW / 'combined-model-plan.json'), changes=changes,
              changed_source_roots=sorted({('MAINBOARD/' if v['board'] == 'mainboard' else 'IOBOARD/') + v['reference'] for v in changes.values()}),
              added_objects=[], added_materials=sorted(NEW), retired_materials=retired, native_reference_count=491,
              stored_object_count=len(objects), opening_guide=guide.name,
              opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(), physical_fit_qualified=False)
(H / 'revision-25-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(dict(passed=True, changed_meshes=len(changes), added_materials=sorted(NEW), retired=retired,
                      scene_sha256=record['stable_scene_sha256']), indent=2), flush=True)
