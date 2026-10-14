"""Replace only four native DIN mesh datablocks, retaining the saved assembly."""
import hashlib
import json
import sys
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
BASELINE = HERE.parent / 'blender-case-revision-12/x0xb0x-populated-with-case.blend'
OUTPUT = HERE / 'x0xb0x-populated-with-case.blend'
GLB = WORK / 'validation/models-review-12/din-contact-quality/native-probes/final-din.glb'
PLAN = WORK / 'validation/models-review-12/combined-model-plan.json'
sys.path.insert(0, str(HERE / 'verification'))
from scene_snapshot import sha, matrix, mesh_signature, material_signature

assert Path(bpy.data.filepath).resolve() == BASELINE.resolve()
assert not OUTPUT.exists(), 'Keep the frozen saved scene immutable'
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
baseline_sha = sha(BASELINE)
plan = json.loads(PLAN.read_text())
row = next(r for r in plan['assignments'] if r['board'] == 'ioboard' and 'DIN1' in r['references'])
refs = ['DIN1', 'DIN2', 'DIN3', 'DIN4']
assert row['references'] == refs
roots = {r: bpy.data.objects['IOBOARD/' + r] for r in refs}
old_objects = set(bpy.data.objects)
old_materials = {m.name: material_signature(m) for m in bpy.data.materials}
original_sets = {name: set(getattr(bpy.data, name)) for name in
                 ('objects', 'collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions')}

def rgb(m):
    assert m and m.use_nodes
    return tuple(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)

def delta(a, b):
    return max(abs(x-y) for p, q in zip(a, b) for x, y in zip(p, q))

palette = list({m for r in refs for m in bpy.data.objects['IOBOARD/' + r + '/mesh'].data.materials})
bpy.ops.import_scene.gltf(filepath=str(GLB))
bpy.context.view_layer.update()
incoming = set(bpy.data.objects) - old_objects
records = []
for ref in refs:
    found = [o for o in incoming if o.name == ref or
             (o.name.startswith(ref + '.') and o.name[len(ref)+1:].isdigit())]
    assert len(found) == 1, (ref, [o.name for o in found])
    source = found[0]
    root = roots[ref]
    assert delta(source.matrix_world, root.matrix_world) < 1e-7
    children = [o for o in source.children_recursive if o.type == 'MESH']
    assert len(children) == 1
    native = children[0]
    original = bpy.data.objects['IOBOARD/' + ref + '/mesh']
    assert original.parent == root
    assert delta(native.matrix_basis, original.matrix_basis) < 1e-7
    assert delta(native.matrix_parent_inverse, original.matrix_parent_inverse) < 1e-7
    mesh = native.data.copy()
    mesh.name = original.name + '/revision12 native mesh'
    mapping = []
    for index, material in enumerate(mesh.materials):
        matches = [m for m in palette if max(abs(a-b) for a, b in zip(rgb(m), rgb(material))) < 1e-7]
        assert len(matches) == 1, (material.name, rgb(material), [m.name for m in matches])
        mapping.append(dict(source_color=rgb(material), retained_material=matches[0].name))
        mesh.materials[index] = matches[0]
    old = original.data
    old_signature = mesh_signature(old)
    original.data = mesh
    if old.users == 0:
        bpy.data.meshes.remove(old)
    root['model_classification'] = row['classification']
    root['model_limitations'] = ' | '.join(row['limitations'])
    root['source_urls'] = ' | '.join(row['source_urls'])
    root['detailed_model_revision'] = 12
    root['selected_native_source_glb_sha256'] = sha(GLB)
    root['source_geometry_basis'] = 'Preserved revision12 component root; exact native KiCad revision12 mesh with original drawing-derived DIN-180 contact centers corrected'
    records.append(dict(reference=ref, root=root.name, object=original.name,
                        root_matrix=matrix(root.matrix_world), old_mesh=old_signature,
                        new_mesh=mesh_signature(mesh), retained_material_mapping=mapping))
for obj in incoming:
    bpy.data.objects.remove(obj, do_unlink=True)
for category in ('collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions'):
    block = getattr(bpy.data, category)
    for datablock in set(block) - original_sets[category]:
        if datablock.users == 0:
            block.remove(datablock)
assert set(bpy.data.objects) == old_objects
assert {m.name: material_signature(m) for m in bpy.data.materials} == old_materials
assert len([o for o in bpy.data.objects if o.get('source_reference')]) == 491
guide_name = '00 START HERE — revision 13 assembly'
guide = bpy.data.texts.new(guide_name)
guide.write('''x0xb0x enclosure assembly — Blender revision 13 / KiCad revision 12

The four SDS-50J DIN meshes use corrected DIN-180 contact positions. The
two outer contacts lie on the horizontal diameter; the 25-degree leaders
on the primary drawing specify their elongated slot tilts. Their previous
raised positions were an interpretation error in our reconstruction.

All 491 fitted native component references, PCB placement and copper,
case geometry, 40 PCB LEDs, 23 button caps, hardware, wiring, shaders,
cameras and four assembly views are preserved. MIDI OUT, THRU, MIDI IN
and SYNC legends retain the original circuit-function correction.

Frames: 1 assembled; 80 exploded; 120 control-side switch inspection;
160 illustrative wiring study. The rear camera shows the connections.

The source remains our drawing-derived illustration, not manufacturer CAD.
Printed body dimensions are retained. Slot widths, cavity depths and minor
molding details are illustrative; solder terminals and locators are omitted.
The received Warehouse CAD is retained in separate local comparison scenes.
Its differing flange dimensions and uncertain pin/body datum prevent it
from establishing the exact historical part or physical assembly fit.

See revision-13-change-record.json and verification for exact provenance.
This scene does not qualify physical plug insertion or fabrication.
''')
scene['visualization_revision'] = 13
scene['opening_notes_text'] = guide_name
scene['revision_13_baseline_scene_sha256'] = baseline_sha
scene['revision_13_geometry_basis'] = 'Four native DIN mesh datablocks replaced from KiCad12; all other scene data and all poses preserved'
scene['revision_13_corrected_DIN_count'] = 4
scene['revision_13_KiCad_revision'] = 12
scene.frame_set(1)
bpy.context.view_layer.update()
assert sha(BASELINE) == baseline_sha
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True, check_existing=False)
record = dict(passed=True, visualization_revision=13, kicad_revision=12,
              baseline_sha256=baseline_sha, stable_scene_sha256=sha(OUTPUT),
              stable_scene_bytes=OUTPUT.stat().st_size, source_glb_sha256=sha(GLB),
              source_plan_sha256=sha(PLAN), corrected_native_references=refs,
              references=records, stored_object_count=len(old_objects),
              native_reference_count=491, all_materials_retained_exactly=True,
              opening_guide=guide_name, opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(),
              downloaded_CAD_geometry_incorporated=False, physical_fit_qualified=False)
(HERE / 'revision-13-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k != 'references'}, indent=2))
