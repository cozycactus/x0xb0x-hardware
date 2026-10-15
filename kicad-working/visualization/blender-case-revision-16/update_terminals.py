"""Install the native KiCad revision-13 terminal-completed meshes at 25 references.

Every existing object, pose, collection link, material and property is retained.
Per reference, only mesh datablocks change: each existing part mesh is replaced
by its exact native KiCad revision-13 tessellation, matched by part name, and each
assembly reference gains one terminal part object beside its named parts. Body
materials are the scene's existing materials; terminals use one added tin material
copied from the native export.

Run from the repository root:
  Blender --background --factory-startup \
      kicad-working/visualization/blender-case-revision-15/x0xb0x-populated-with-case.blend \
      --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-16/update_terminals.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
BASELINE = HERE.parent / 'blender-case-revision-15/x0xb0x-populated-with-case.blend'
OUTPUT = HERE / 'x0xb0x-populated-with-case.blend'
REVIEW = WORK / 'validation/models-review-13'
PLAN = REVIEW / 'combined-model-plan.json'
EXPORTS = json.loads((REVIEW / 'native-export-record.json').read_text())
INSTALL = json.loads((REVIEW / 'installation-audit.json').read_text())
sys.path.insert(0, str(HERE / 'verification'))
from scene_snapshot import sha, matrix, mesh_signature, material_signature  # noqa: E402

TIN_NAME = 'Terminal tin — revision 16 (native KiCad colour)'
TERMINAL_PART = 'DrawingDerivedTerminals'
PREFIX = {'ioboard': 'IOBOARD/', 'mainboard': 'MAINBOARD/'}
TOL = 1e-7

assert Path(bpy.data.filepath).resolve() == BASELINE.resolve()
assert not OUTPUT.exists(), 'Keep the frozen saved scene immutable'
assert INSTALL['passed']
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
baseline_sha = sha(BASELINE)
plan = json.loads(PLAN.read_text())
rows = {r: row for row in plan['updated_assignments'] for r in row['references']}
assert len(rows) == 25
roots = {(o['source_board'], o['source_reference']): o for o in bpy.data.objects if o.get('source_reference')}
old_objects = set(bpy.data.objects)
old_materials = {m.name: material_signature(m) for m in bpy.data.materials}
original_sets = {name: set(getattr(bpy.data, name)) for name in
                 ('objects', 'collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions')}


def base(name):
    return re.sub(r'\.\d{3}$', '', name)


def rgb(material):
    assert material and material.use_nodes
    return tuple(material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)


def close(a, b, tol=1e-6):
    return max(abs(x - y) for x, y in zip(a, b)) <= tol


def delta(a, b):
    return max(abs(x - y) for p, q in zip(a, b) for x, y in zip(p, q))


def shader(material):
    sig = material_signature(material)
    return {k: v for k, v in sig['nodes'].items()}, sig['links']


tin = None
tin_rgb = None
records, new_objects = [], []
for board in ('ioboard', 'mainboard'):
    glb = REVIEW / EXPORTS['boards'][board]['glb']
    assert sha(glb) == EXPORTS['boards'][board]['glb_sha256'], board
    before_import = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    bpy.context.view_layer.update()
    incoming = set(bpy.data.objects) - before_import
    glb_base = next(o for o in incoming if o.parent is None)
    native_roots = {base(o.name): o for o in glb_base.children}
    for ref in sorted(r for (b, r) in roots if b == board and r in rows):
        row = rows[ref]
        root = roots[(board, ref)]
        source = native_roots[ref]
        frame_scene = root.parent.matrix_world.inverted() @ root.matrix_world
        frame_native = glb_base.matrix_world.inverted() @ source.matrix_world
        assert delta(frame_scene, frame_native) < 1e-6, (ref, 'placement frame differs')
        new_kids = list(source.children)
        old_kids = list(root.children)
        assert len(new_kids) == len(old_kids) == 1, (ref, [o.name for o in new_kids], [o.name for o in old_kids])
        new_top, old_top = new_kids[0], old_kids[0]
        assert delta(new_top.matrix_basis, old_top.matrix_basis) < TOL
        assert delta(new_top.matrix_parent_inverse, old_top.matrix_parent_inverse) < TOL
        palette = {m for o in root.children_recursive if o.type == 'MESH' for m in o.data.materials}
        swaps, added = [], None
        if new_top.type == 'MESH':
            # Single-product model: one mesh, body colours mapped to the scene's materials, plus tin.
            assert old_top.type == 'MESH'
            pairs = [(old_top, new_top)]
            kind = 'single mesh'
        else:
            assert new_top.type == old_top.type == 'EMPTY'
            olds = {base(o.data.name): o for o in old_top.children}
            news = {base(o.name): o for o in new_top.children}
            assert len(olds) == len(old_top.children) and len(news) == len(new_top.children)
            assert set(news) == set(olds) | {TERMINAL_PART}, (ref, sorted(news), sorted(olds))
            pairs = [(olds[n], news[n]) for n in sorted(olds)]
            kind = 'named assembly'
        for old, new in pairs:
            assert delta(new.matrix_basis, old.matrix_basis) < TOL
            assert delta(new.matrix_parent_inverse, old.matrix_parent_inverse) < TOL
            mesh = new.data.copy()
            mesh.name = f'{old.name}/revision16 native mesh'
            mapping = []
            for index, material in enumerate(mesh.materials):
                colour = rgb(material)
                if kind == 'named assembly':
                    assert len(mesh.materials) == len(old.data.materials)
                    target = old.data.materials[index]
                else:
                    matches = [m for m in palette if close(rgb(m), colour)]
                    target = matches[0] if len(matches) == 1 else None
                    if target is None:
                        tin_rgb = tin_rgb or colour
                        assert close(colour, tin_rgb) and not matches, (ref, colour)
                if target is None:
                    if tin is None:
                        tin = material.copy()
                        tin.name = TIN_NAME
                    assert shader(material)[0].keys() == shader(tin)[0].keys()
                    target = tin
                mapping.append(dict(slot=index, native_colour=colour, scene_material=target.name,
                                    scene_colour=rgb(target), colour_identical=close(rgb(target), colour)))
                mesh.materials[index] = target
            previous = old.data
            swaps.append(dict(object=old.name, old_mesh=mesh_signature(previous), new_mesh=mesh_signature(mesh),
                              material_mapping=mapping))
            old.data = mesh
            if previous.users == 0:
                bpy.data.meshes.remove(previous)
        if kind == 'named assembly':
            new = news[TERMINAL_PART]
            sibling = pairs[0][0]
            index = 1 + max(int(m.group(1)) if (m := re.search(r'\.(\d{3})$', o.name)) else 0
                            for o in old_top.children)
            name = f'{PREFIX[board]}{ref}/mesh.{index:03d}'
            assert name not in bpy.data.objects
            mesh = new.data.copy()
            mesh.name = f'{name}/revision16 native terminals'
            assert len(mesh.materials) == 1
            tin_rgb = tin_rgb or rgb(mesh.materials[0])
            assert close(rgb(mesh.materials[0]), tin_rgb)
            if tin is None:
                tin = mesh.materials[0].copy()
                tin.name = TIN_NAME
            assert shader(mesh.materials[0])[0].keys() == shader(tin)[0].keys()
            mesh.materials[0] = tin
            obj = bpy.data.objects.new(name, mesh)
            for collection in sibling.users_collection:
                collection.objects.link(obj)
            obj.parent = old_top
            obj.parent_type = sibling.parent_type
            obj.matrix_parent_inverse = new.matrix_parent_inverse.copy()
            obj.matrix_basis = new.matrix_basis.copy()
            obj.hide_render, obj.hide_viewport = sibling.hide_render, sibling.hide_viewport
            for key in sibling.keys():
                obj[key] = sibling[key]
            obj['drawing_derived_terminals'] = True
            added = dict(object=name, mesh=mesh_signature(mesh), collections=sorted(c.name for c in obj.users_collection))
            new_objects.append(obj)
        terminal_note = ('Drawing-derived terminals added in KiCad revision 13; positions per manufacturer drawing '
                         'dimensions in the model frame, not moved to pads; not fit qualified')
        root['model_classification'] = row['classification']
        root['model_limitations'] = str(root.get('model_limitations', '')) + ' | ' + terminal_note
        root['detailed_model_revision'] = 13
        root['selected_native_source_glb_sha256'] = EXPORTS['boards'][board]['glb_sha256']
        root['source_geometry_basis'] = ('Preserved component root and objects; exact native KiCad revision13 meshes '
                                         'with previous body solids retained and drawing-derived terminals')
        records.append(dict(board=board, reference=ref, root=root.name, kind=kind, root_frame=matrix(root.matrix_world),
                            replaced_meshes=swaps, added_terminal_object=added))
    for obj in incoming:
        bpy.data.objects.remove(obj, do_unlink=True)
    for category in ('collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions'):
        block = getattr(bpy.data, category)
        for datablock in set(block) - original_sets[category]:
            if datablock.users == 0:
                block.remove(datablock)

assert len(records) == 25
assert set(bpy.data.objects) == old_objects | set(new_objects) and len(new_objects) == 14
assert {m.name: material_signature(m) for m in bpy.data.materials if m.name != TIN_NAME} == old_materials
assert set(m.name for m in bpy.data.materials) - set(old_materials) == {TIN_NAME}
assert len([o for o in bpy.data.objects if o.get('source_reference')]) == 491
guide_name = '00 START HERE — revision 16 assembly'
guide = bpy.data.texts.new(guide_name)
guide.write('''x0xb0x enclosure assembly — Blender revision 16 / KiCad revision 13

Twelve component models that were bodies without solder terminals now carry
terminals taken from their manufacturer drawings: NYS216 audio jacks,
SDS-50J DIN sockets, MJ-3536N and PJ-202AH jacks, the USB-B socket,
the bent-back MC78M05 regulator, LPTC thermistors, the CTS encoder, Alpha
and Panasonic potentiometers, the NKK toggle and Grayhill rotary switches
(25 placed references). Every fitted component now has a lead in every
drilled hole except the four Grayhill bracket holes, whose legs the drawing
does not define.

Terminal positions follow the drawings and were not moved to the PCB pads.
Where a drawing and the footprint disagree, the nominal hole interference is
recorded in kicad-working/validation/models-review-13 (for example the NYS216
rows, the Alpha and Panasonic bracket tabs and the USB shell forks).
Thicknesses, bends and some widths are labelled assumptions.

Previous body geometry, all 491 component roots and poses, PCB placement,
case, LEDs, caps, hardware, wiring study, shaders, cameras and the four
assembly views are preserved. Terminals use one tin material.

Frames: 1 assembled; 80 exploded; 120 control-side switch inspection;
160 illustrative wiring study.

See revision-16-change-record.json and verification for exact provenance.
This scene does not qualify physical assembly or fabrication.
''')
scene['visualization_revision'] = 16
scene['opening_notes_text'] = guide_name
scene['revision_16_baseline_scene_sha256'] = baseline_sha
scene['revision_16_geometry_basis'] = ('Native mesh datablocks of 25 references replaced from KiCad13 and 14 terminal '
                                       'part objects added; all other scene data and all poses preserved')
scene['revision_16_terminal_reference_count'] = 25
scene['revision_16_KiCad_revision'] = 13
scene.frame_set(1)
bpy.context.view_layer.update()
assert sha(BASELINE) == baseline_sha
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True, check_existing=False)
record = dict(passed=True, visualization_revision=16, kicad_revision=13,
              baseline_sha256=baseline_sha, stable_scene_sha256=sha(OUTPUT), stable_scene_bytes=OUTPUT.stat().st_size,
              source_glb_sha256={b: EXPORTS['boards'][b]['glb_sha256'] for b in EXPORTS['boards']},
              source_plan_sha256=sha(PLAN), terminal_material=TIN_NAME, terminal_material_colour=list(tin_rgb),
              references=records, added_objects=[o.name for o in new_objects],
              replaced_mesh_objects=[s['object'] for r in records for s in r['replaced_meshes']],
              stored_object_count=len(bpy.data.objects), native_reference_count=491,
              all_previous_materials_retained_exactly=True, opening_guide=guide_name,
              opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(),
              downloaded_CAD_geometry_incorporated=False, physical_fit_qualified=False)
(HERE / 'revision-16-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k not in ('references',)}, indent=2)[:3000])
