"""Install the native KiCad revision-17 TL1100F meshes (metal legs) at 23 references.

Revision 17 recolours the TL1100F leg faces outside the housing as terminal metal;
the geometry is unchanged. Every object, pose, collection link, material and property
of revision 19 is retained; only the mesh datablocks whose native tessellation
differs are replaced. Parts are matched to the native export by identical body
geometry; the one remaining part per assembly is its terminal object. No object
or material is added.

Run from the repository root:
  Blender --background --factory-startup \
      kicad-working/visualization/blender-case-revision-19/x0xb0x-populated-with-case.blend \
      --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-20/update_tl1100_colour.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
BASELINE = HERE.parent / 'blender-case-revision-19/x0xb0x-populated-with-case.blend'
OUTPUT = HERE / 'x0xb0x-populated-with-case.blend'
REVIEW = WORK / 'validation/models-review-17'
PLAN = REVIEW / 'combined-model-plan.json'
EXPORTS = json.loads((REVIEW / 'native-export-record.json').read_text())
INSTALL = json.loads((REVIEW / 'installation-audit.json').read_text())
sys.path.insert(0, str(HERE / 'verification'))
from scene_snapshot import sha, matrix, mesh_signature, material_signature  # noqa: E402

TIN_NAME = 'Terminal tin — revision 16 (native KiCad colour)'   # unused by TL1100F; checked still present
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
assert len(rows) == 23
roots = {(o['source_board'], o['source_reference']): o for o in bpy.data.objects if o.get('source_reference')}
old_objects = set(bpy.data.objects)
old_materials = {m.name: material_signature(m) for m in bpy.data.materials}
original_sets = {name: set(getattr(bpy.data, name)) for name in
                 ('objects', 'collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions')}
tin = bpy.data.materials[TIN_NAME]


def base(name):
    return re.sub(r'\.\d{3}$', '', name)


def rgb(material):
    return tuple(material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)


def close(a, b, tol=1e-6):
    return max(abs(x - y) for x, y in zip(a, b)) <= tol


def delta(a, b):
    return max(abs(x - y) for p, q in zip(a, b) for x, y in zip(p, q))


records = []
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
        root, source = roots[(board, ref)], native_roots[ref]
        frame_scene = root.parent.matrix_world.inverted() @ root.matrix_world
        frame_native = glb_base.matrix_world.inverted() @ source.matrix_world
        assert delta(frame_scene, frame_native) < 1e-6, (ref, 'placement frame differs')
        (new_top,), (old_top,) = source.children, root.children
        assert delta(new_top.matrix_basis, old_top.matrix_basis) < TOL
        if new_top.type == 'MESH':
            pairs, kind = [(old_top, new_top)], 'single mesh'
        else:
            olds, news = list(old_top.children), list(new_top.children)
            assert len(olds) == len(news)
            by_hash = {}
            for n in news:
                by_hash.setdefault(mesh_signature(n.data)['hash'], []).append(n)
            pairs, unmatched_old = [], []
            for o in olds:
                hits = by_hash.get(mesh_signature(o.data)['hash'])
                if hits:
                    hits.pop(0)
                else:
                    unmatched_old.append(o)
            unmatched_new = [n for v in by_hash.values() for n in v]
            assert len(unmatched_old) == len(unmatched_new) == 1, (ref, [o.name for o in unmatched_old])
            assert unmatched_old[0].get('drawing_derived_terminals') and base(unmatched_new[0].name) == 'DrawingDerivedTerminals'
            pairs, kind = [(unmatched_old[0], unmatched_new[0])], 'named assembly terminal part'
        swaps = []
        for old, new in pairs:
            assert delta(new.matrix_basis, old.matrix_basis) < TOL
            assert delta(new.matrix_parent_inverse, old.matrix_parent_inverse) < TOL
            palette = list(old.data.materials)
            mesh = new.data.copy()
            mesh.name = f'{old.name}/revision20 native mesh'
            mapping = []
            for index, material in enumerate(mesh.materials):
                matches = [m for m in palette if close(rgb(m), rgb(material))]
                assert len(matches) == 1, (ref, rgb(material), [m.name for m in palette])
                mesh.materials[index] = matches[0]
                mapping.append(dict(slot=index, native_colour=rgb(material), scene_material=matches[0].name))
            previous = old.data
            swaps.append(dict(object=old.name, old_mesh=mesh_signature(previous), new_mesh=mesh_signature(mesh),
                              material_mapping=mapping))
            old.data = mesh
            if previous.users == 0:
                bpy.data.meshes.remove(previous)
        root['model_classification'] = rows[ref]['classification']
        root['model_limitations'] = str(root.get('model_limitations', '')) + (
            ' | KiCad revision 17 colours the leg faces outside the housing as terminal metal; geometry unchanged')
        root['detailed_model_revision'] = 17
        root['selected_native_source_glb_sha256'] = EXPORTS['boards'][board]['glb_sha256']
        root['source_geometry_basis'] = ('Preserved component root and object; exact native KiCad revision17 mesh '
                                         '(publisher CAD geometry, leg faces coloured as terminal metal)')
        records.append(dict(board=board, reference=ref, root=root.name, kind=kind,
                            root_frame=matrix(root.matrix_world), replaced_meshes=swaps))
    for obj in incoming:
        bpy.data.objects.remove(obj, do_unlink=True)
    for category in ('collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions'):
        block = getattr(bpy.data, category)
        for datablock in set(block) - original_sets[category]:
            if datablock.users == 0:
                block.remove(datablock)

assert len(records) == 23
assert set(bpy.data.objects) == old_objects
assert {m.name: material_signature(m) for m in bpy.data.materials} == old_materials
assert len([o for o in bpy.data.objects if o.get('source_reference')]) == 491
assert tin.users > 0
guide_name = '00 START HERE — revision 20 assembly'
guide = bpy.data.texts.new(guide_name)
guide.write('''x0xb0x enclosure assembly — Blender revision 20 / KiCad revision 17

The 23 TL1100F tact switches (S5-S27) now show metal legs. The publisher CAD is
one grey solid; revision 8 coloured its faces by position and left the leg faces
that rise above the board, outside the 12 x 12 mm housing, black. Those 24 faces
per switch are now terminal metal. The geometry is unchanged.

Every object, pose, material, the case, LEDs, caps, hardware, wiring study,
cameras and the four assembly views are preserved from revision 19.

Frames: 1 assembled; 80 exploded; 120 control-side switch inspection;
160 illustrative wiring study.

See revision-20-change-record.json and verification for exact provenance.
This scene does not qualify physical assembly or fabrication.
''')
scene['visualization_revision'] = 20
scene['opening_notes_text'] = guide_name
scene['revision_20_baseline_scene_sha256'] = baseline_sha
scene['revision_20_geometry_basis'] = ('TL1100F mesh datablocks at 23 references replaced from KiCad17 (leg faces '
                                       'coloured as metal, geometry unchanged); all other scene data preserved')
scene['revision_20_corrected_reference_count'] = 23
scene['revision_20_KiCad_revision'] = 17
scene.frame_set(1)
bpy.context.view_layer.update()
assert sha(BASELINE) == baseline_sha
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True, check_existing=False)
record = dict(passed=True, visualization_revision=20, kicad_revision=17,
              baseline_sha256=baseline_sha, stable_scene_sha256=sha(OUTPUT), stable_scene_bytes=OUTPUT.stat().st_size,
              source_glb_sha256={b: EXPORTS['boards'][b]['glb_sha256'] for b in EXPORTS['boards']},
              source_plan_sha256=sha(PLAN), references=records, added_objects=[],
              replaced_mesh_objects=[s['object'] for r in records for s in r['replaced_meshes']],
              terminal_material=TIN_NAME, stored_object_count=len(bpy.data.objects), native_reference_count=491,
              all_previous_materials_retained_exactly=True, opening_guide=guide_name,
              opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(),
              downloaded_CAD_geometry_incorporated=False, physical_fit_qualified=False)
(HERE / 'revision-20-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k != 'references'}, indent=2))
