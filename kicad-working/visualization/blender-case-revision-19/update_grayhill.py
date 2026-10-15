"""Install the native KiCad revision-16 Grayhill 25L meshes at S3 and S4.

The rebuilt body changes its part set: the land illustration part is replaced by
separate output-board lands, solder joints, a label band and label text. Per
reference, parts present before and after keep their objects (mesh data replaced),
the removed part's object is deleted and each new part gets an object beside its
siblings. Previous materials are never modified; parts whose native colour differs
from their old material get a new material copied from the native export. Every
other object, pose and property is retained.

Run from the repository root:
  Blender --background --factory-startup \
      kicad-working/visualization/blender-case-revision-18/x0xb0x-populated-with-case.blend \
      --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-19/update_grayhill.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
BASELINE = HERE.parent / 'blender-case-revision-18/x0xb0x-populated-with-case.blend'
OUTPUT = HERE / 'x0xb0x-populated-with-case.blend'
REVIEW = WORK / 'validation/models-review-16'
PREVIOUS = WORK / 'validation/models-review-15'
PLAN = REVIEW / 'combined-model-plan.json'
EXPORTS = json.loads((REVIEW / 'native-export-record.json').read_text())
OLD_EXPORTS = json.loads((PREVIOUS / 'native-export-record.json').read_text())
sys.path.insert(0, str(HERE / 'verification'))
from scene_snapshot import sha, matrix, mesh_signature, material_signature  # noqa: E402

TOL = 1e-7
assert Path(bpy.data.filepath).resolve() == BASELINE.resolve()
assert not OUTPUT.exists(), 'Keep the frozen saved scene immutable'
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
baseline_sha = sha(BASELINE)
plan = json.loads(PLAN.read_text())
rows = {r: row for row in plan['updated_assignments'] for r in row['references']}
assert sorted(rows) == ['S3', 'S4']
roots = {o['source_reference']: o for o in bpy.data.objects
         if o.get('source_reference') and o.get('source_board') == 'mainboard'}
old_object_names = {o.name for o in bpy.data.objects}
old_materials = {m.name: material_signature(m) for m in bpy.data.materials}
original_sets = {name: set(getattr(bpy.data, name)) for name in
                 ('objects', 'collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions')}


def base(name):
    return re.sub(r'\.\d{3}$', '', name)


def rgb(material):
    return tuple(material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)


def close(a, b, tol=1e-6):
    return max(abs(x - y) for x, y in zip(a, b)) <= tol


def delta(a, b):
    return max(abs(x - y) for p, q in zip(a, b) for x, y in zip(p, q))


def import_parts(glb, record, board='mainboard'):
    assert sha(glb) == record['boards'][board]['glb_sha256']
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    bpy.context.view_layer.update()
    incoming = set(bpy.data.objects) - before
    glb_base = next(o for o in incoming if o.parent is None)
    return incoming, glb_base, {base(o.name): o for o in glb_base.children}


# Part names of the existing objects, from the revision-15 native export they were built from.
old_incoming, _, old_roots = import_parts(PREVIOUS / OLD_EXPORTS['boards']['mainboard']['glb'], OLD_EXPORTS)
old_names = {}
for ref in rows:
    by_hash = {mesh_signature(c.data)['hash']: base(c.name) for c in old_roots[ref].children[0].children}
    for obj in roots[ref].children[0].children:
        old_names[obj.name] = by_hash[mesh_signature(obj.data)['hash']]
for obj in old_incoming:
    bpy.data.objects.remove(obj, do_unlink=True)

incoming, glb_base, native_roots = import_parts(REVIEW / EXPORTS['boards']['mainboard']['glb'], EXPORTS)
new_materials, records, added, removed, replaced = {}, [], [], [], []
for ref in sorted(rows):
    root, source = roots[ref], native_roots[ref]
    frame_scene = root.parent.matrix_world.inverted() @ root.matrix_world
    frame_native = glb_base.matrix_world.inverted() @ source.matrix_world
    assert delta(frame_scene, frame_native) < 1e-6
    (old_top,), (new_top,) = root.children, source.children
    assert delta(new_top.matrix_basis, old_top.matrix_basis) < TOL
    olds = {old_names[o.name]: o for o in old_top.children}
    news = {base(o.name): o for o in new_top.children}
    sibling = next(iter(olds.values()))
    swaps, adds, drops = [], [], []
    next_index = 1 + max(int(m.group(1)) if (m := re.search(r'\.(\d{3})$', o.name)) else 0 for o in olds.values())
    for name in sorted(set(olds) - set(news)):
        obj = olds[name]
        drops.append(dict(object=obj.name, part=name, mesh=mesh_signature(obj.data)))
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        del olds[name]
    for name in sorted(news):
        new = news[name]
        mesh = new.data.copy()
        if name in olds:
            obj = olds[name]
            keep = list(obj.data.materials)
        else:
            obj_name = f'MAINBOARD/{ref}/mesh.{next_index:03d}'
            next_index += 1
            assert obj_name not in bpy.data.objects
            obj = bpy.data.objects.new(obj_name, mesh)
            for collection in sibling.users_collection:
                collection.objects.link(obj)
            obj.parent = old_top
            obj.parent_type = sibling.parent_type
            obj.matrix_parent_inverse = new.matrix_parent_inverse.copy()
            obj.matrix_basis = new.matrix_basis.copy()
            obj.hide_render, obj.hide_viewport = sibling.hide_render, sibling.hide_viewport
            for key in sibling.keys():
                if key != 'drawing_derived_terminals':
                    obj[key] = sibling[key]
            keep = []
        assert delta(new.matrix_basis, obj.matrix_basis) < TOL
        mapping = []
        for index, material in enumerate(mesh.materials):
            match = next((m for m in keep if close(rgb(m), rgb(material))), None)
            if match is None:
                key = tuple(round(c, 6) for c in rgb(material)[:3])
                if key not in new_materials:
                    copy = material.copy()
                    copy.name = f'Grayhill 25L {name} — revision 19 (native KiCad colour)'
                    new_materials[key] = copy
                match = new_materials[key]
            mesh.materials[index] = match
            mapping.append(dict(slot=index, native_colour=rgb(material), scene_material=match.name))
        mesh.name = f'{obj.name}/revision19 native mesh'
        if name in olds:
            previous = obj.data
            swaps.append(dict(object=obj.name, part=name, old_mesh=mesh_signature(previous), new_mesh=mesh_signature(mesh),
                              material_mapping=mapping))
            obj.data = mesh
            if previous.users == 0:
                bpy.data.meshes.remove(previous)
            replaced.append(obj.name)
        else:
            obj.data = mesh
            adds.append(dict(object=obj.name, part=name, mesh=mesh_signature(mesh), material_mapping=mapping))
            added.append(obj.name)
    removed += [d['object'] for d in drops]
    root['model_classification'] = rows[ref]['classification']
    root['model_limitations'] = ('Grayhill 25L body rebuilt in KiCad revision 16 from the Series 25L drawing (printed '
                                 'dimensions and pins kept) and a product photograph (drum top, lock lugs, label band, '
                                 'green output board and solder joints are photo-derived); not manufacturer CAD')
    root['detailed_model_revision'] = 16
    root['selected_native_source_glb_sha256'] = EXPORTS['boards']['mainboard']['glb_sha256']
    root['source_geometry_basis'] = 'Preserved component root; exact native KiCad revision16 meshes of the rebuilt body'
    records.append(dict(reference=ref, root=root.name, root_frame=matrix(root.matrix_world), replaced=swaps,
                        added=adds, removed=drops))
for obj in incoming:
    bpy.data.objects.remove(obj, do_unlink=True)
for category in ('collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions'):
    block = getattr(bpy.data, category)
    for datablock in set(block) - original_sets[category]:
        if datablock.users == 0:
            block.remove(datablock)

NEW = {m.name for m in new_materials.values()}
assert {o.name for o in bpy.data.objects} == ((old_object_names - set(removed)) | set(added))
assert {m.name: material_signature(m) for m in bpy.data.materials if m.name not in NEW} == old_materials
assert {m.name for m in bpy.data.materials} - set(old_materials) == NEW
assert len([o for o in bpy.data.objects if o.get('source_reference')]) == 491
guide_name = '00 START HERE — revision 19 assembly'
guide = bpy.data.texts.new(guide_name)
guide.write('''x0xb0x enclosure assembly — Blender revision 19 / KiCad revision 16

The two Grayhill 25L rotary switches (S3, S4) are rebuilt from the Series 25L
drawing and a product photograph of the hex-output part (label 8 4 2 1 C):
a square base with a round drum top and two lock lugs, the white label band,
a green output board with gold lands and solder joints, and the non-turn tab
on the centre line opposite the pins, as the drawing's front view shows.
Printed dimensions, the shaft, bushing and pin positions are unchanged. The
four MT holes stay empty: the BOM part 25LB22-H has no -Z bracket suffix.

Every other object, pose, material, the case, LEDs, caps, hardware, wiring
study, cameras and the four assembly views are preserved from revision 18.

Frames: 1 assembled; 80 exploded; 120 control-side switch inspection;
160 illustrative wiring study.

See revision-19-change-record.json and verification for exact provenance.
This scene does not qualify physical assembly or fabrication.
''')
scene['visualization_revision'] = 19
scene['opening_notes_text'] = guide_name
scene['revision_19_baseline_scene_sha256'] = baseline_sha
scene['revision_19_geometry_basis'] = ('Grayhill 25L meshes at S3 and S4 replaced from KiCad16 (rebuilt body); '
                                       'all other scene data and all poses preserved')
scene['revision_19_KiCad_revision'] = 16
scene.frame_set(1)
bpy.context.view_layer.update()
assert sha(BASELINE) == baseline_sha
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True, check_existing=False)
record = dict(passed=True, visualization_revision=19, kicad_revision=16, baseline_sha256=baseline_sha,
              stable_scene_sha256=sha(OUTPUT), stable_scene_bytes=OUTPUT.stat().st_size,
              source_glb_sha256={b: EXPORTS['boards'][b]['glb_sha256'] for b in EXPORTS['boards']},
              source_plan_sha256=sha(PLAN), references=records, added_objects=added, removed_objects=removed,
              replaced_mesh_objects=replaced, added_materials=sorted(NEW), terminal_material=None,
              stored_object_count=len(bpy.data.objects), native_reference_count=491,
              all_previous_materials_retained_exactly=True, opening_guide=guide_name,
              opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(),
              downloaded_CAD_geometry_incorporated=False, physical_fit_qualified=False)
(HERE / 'revision-19-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k != 'references'}, indent=2))
