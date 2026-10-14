"""Replace only approved native component subtrees in the preserved scene.

Run with revision7 loaded. The plan selects updated references; all other
objects and materials are retained. Source collections become a documented
composite of preserved revision7 and selected revision11 native component
exports, rather than a new import of either complete board.
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'verification'))
from scene_snapshot import capture, sha, matrix, material_signature, mesh_signature, write_snapshot

BASELINE = HERE.parent / 'blender-case-revision-7/x0xb0x-populated-with-case.blend'
OUTPUT = HERE / 'x0xb0x-populated-with-case.blend'
PLAN = HERE / 'board-meshes/source-model-plan.json'
assert Path(bpy.data.filepath).resolve() == BASELINE.resolve(), 'Load preserved revision7 first'
assert not OUTPUT.exists(), 'Preserve saved revision8; remove only an explicitly superseded candidate before rerunning'
plan = json.loads(PLAN.read_text())
selected = {(row['board'], ref): row
            for row in plan['updated_assignments'] for ref in row['references']}
assert selected and len(selected) == plan['updated_instance_count']
assert not any(ref.startswith('LED') for _, ref in selected), 'LED installation and shaders must remain preserved'
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
baseline_sha = sha(BASELINE)
before = capture()
write_snapshot(HERE / 'verification/before-scene.json.gz', before)
all_roots = {(o.get('source_board'), o.get('source_reference')): o
             for o in bpy.data.objects if o.get('source_reference')}
assert len(all_roots) == 491 and set(selected) <= set(all_roots)
material_cache = [(material_signature(m), m) for m in bpy.data.materials]
records = []
material_roles = {}


def linear(v):
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4


def classify_selected_material(material):
    if not material or not material.use_nodes:
        return
    shader = material.node_tree.nodes.get('Principled BSDF')
    if not shader:
        return
    shader.inputs['Roughness'].default_value = .42
    rgb = shader.inputs['Base Color'].default_value[:3]
    roles = [([.075, .08, .085], 'nonmetal transistor encapsulation'),
             ([.1, .25, .65], 'nonmetal resonator coating'),
             ([.72, .73, .75], 'metal lead')]
    for source_rgb, role in roles:
        if max(abs(a-b) for a, b in zip(rgb, [linear(v) for v in source_rgb])) < 1e-6:
            shader.inputs['Metallic'].default_value = 1 if role == 'metal lead' else 0
            shader.inputs['Emission Strength'].default_value = 0
            shader.inputs['Transmission Weight'].default_value = 0
            material['revision11_material_role'] = role
            material['revision11_surface_basis'] = 'Illustrative shader role assigned from exact STEP color; roughness0.42; not material certification'
            material_roles[material.name] = role
            return



def descendants(root):
    return [child for child in root.children_recursive]


def max_matrix_delta(a, b):
    return max(abs(x-y) for p, q in zip(a, b) for x, y in zip(p, q))


for board in sorted({b for b, _ in selected}):
    source_glb = HERE / 'board-meshes' / (board + '.glb')
    original_sets = {name: set(getattr(bpy.data, name)) for name in
                     ('objects', 'collections', 'meshes', 'materials',
                      'images', 'cameras', 'lights', 'actions')}
    bpy.ops.import_scene.gltf(filepath=str(source_glb))
    bpy.context.view_layer.update()
    imported = set(bpy.data.objects) - original_sets['objects']
    kept = set()
    for key, row in sorted(selected.items()):
        if key[0] != board:
            continue
        ref = key[1]
        matches = [o for o in imported
                   if o.name == ref or (o.name.startswith(ref + '.') and
                       o.name[len(ref)+1:].isdigit())]
        assert len(matches) == 1, (key, [o.name for o in matches])
        incoming = matches[0]
        original = all_roots[key]
        delta = max_matrix_delta(incoming.matrix_world, original.matrix_world)
        assert delta < 1e-7, (key, 'Native component root pose drift', delta)
        children = descendants(incoming)
        assert children and all(o.type in {'EMPTY', 'MESH'} for o in children)
        source_collections = list(original.users_collection)
        old_children = descendants(original)
        old_meshes = {o.data for o in old_children if o.type == 'MESH'}
        old_mesh_signatures = [mesh_signature(m) for m in old_meshes]
        for child in reversed(old_children):
            bpy.data.objects.remove(child, do_unlink=True)
        for mesh in old_meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        direct = list(incoming.children)
        for child in direct:
            basis = child.matrix_basis.copy()
            inverse = child.matrix_parent_inverse.copy()
            child.parent = original
            child.matrix_parent_inverse = inverse
            child.matrix_basis = basis
        new_meshes = []
        for index, child in enumerate(sorted(children, key=lambda o: o.name)):
            for collection in list(child.users_collection):
                collection.objects.unlink(child)
            for collection in source_collections:
                collection.objects.link(child)
            child.name = original.name + ('/mesh' if child.type == 'MESH' else '/native feature') + ('' if index == 0 else f'.{index:03d}')
            child['source_board'] = board
            child['native_export_geometry_preserved'] = True
            child['selected_native_revision'] = 11
            if child.type == 'MESH':
                child.data.name = original.name + '/revision11 native mesh'
                for i, material in enumerate(child.data.materials):
                    classify_selected_material(material)
                    signature = material_signature(material) if material else None
                    reused = next((m for known, m in material_cache if known == signature), None)
                    if reused:
                        child.data.materials[i] = reused
                    elif material:
                        material_cache.append((signature, material))
                new_meshes.append(dict(object=child.name,
                    signature=mesh_signature(child.data),
                    native_board_matrix=matrix(child.matrix_world)))
            kept.add(child)
        original['model_classification'] = row.get('classification', 'Native drawing-derived component illustration')
        original['model_limitations'] = ' | '.join(row.get('limitations', []))
        original['source_urls'] = ' | '.join(row.get('source_urls', []))
        original['detailed_model_revision'] = 11
        original['selected_native_source_glb_sha256'] = sha(source_glb)
        original['source_geometry_basis'] = 'Original revision7 root pose and collection membership; descendant meshes selected unchanged from native KiCad revision11 GLB'
        for collection in source_collections:
            collection['revision_8_content_basis'] = 'Preserved revision7 scene source collection with selected revision11 component subtrees; composite source, not a byte-identical whole-board GLB import'
        records.append(dict(board=board, reference=ref, root=original.name,
            root_matrix_preserved=matrix(original.matrix_world),
            maximum_native_root_matrix_delta=delta,
            collections=[c.name for c in source_collections],
            old_meshes=old_mesh_signatures, new_meshes=new_meshes,
            source_glb_sha256=sha(source_glb), model_plan_row=row))
    for obj in imported - kept:
        bpy.data.objects.remove(obj, do_unlink=True)
    for category in ('collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions'):
        block = getattr(bpy.data, category)
        for datablock in set(block) - original_sets[category]:
            if datablock.users == 0:
                block.remove(datablock)
    bpy.context.view_layer.update()

assert len([o for o in bpy.data.objects if o.get('source_reference')]) == 491
# Preserve original shader datablocks even when a replaced subtree was their
# final user. Their shading is kept as baseline evidence; no shader is edited.
retained_unused_materials = []
for _, material in material_cache:
    if material.name in before['materials'] and material.users == 0:
        material.use_fake_user = True
        retained_unused_materials.append(material.name)
scene['visualization_revision'] = 8
scene['native_PCB_model_count'] = 491
scene['selected_native_revision_11_reference_count'] = len(selected)
scene['revision_8_geometry_basis'] = 'Preserved revision7 complete assembly plus selected native KiCad revision11 component mesh subtrees; all other objects, materials, poses and geometry retained'
scene['revision_8_baseline_scene_sha256'] = baseline_sha
opening_name = '00 START HERE — revision 8 assembly'
assert opening_name not in bpy.data.texts
opening = bpy.data.texts.new(opening_name)
opening.write(f'''x0xb0x enclosure assembly — Blender revision 8 / KiCad revision 11

This is the current opening guide for this saved scene. Earlier embedded
notes are preserved as historical evidence for the revision7 baseline.

This pass replaces {len(selected)} selected component models with meshes exported
from KiCad revision11. The other components and the original case, panels,
knobs, labels, wires, cameras and assembly positions remain preserved.
All 491 fitted component references remain in the scene.

The 40 LEDs are complete PCB-mounted components: their leads enter the PCB
and their lenses extend through the panel holes. There are no separate panel
LED lens copies. The 23 button caps follow the PCB switches in exploded view.
Clear lenses show an illustrative unlit appearance; emitted red light is not
simulated. LED height uses the named 0.24-inch BOM spacer; an older assembly
table gives 0.22 inch and that disagreement remains documented.

Choose a timeline frame:
1 — complete assembled enclosure
80 — exploded enclosure, with LED bodies and button caps following the PCB
120 — control side inspection, with button caps hidden to inspect switches
160 — wiring study, with the existing illustrative conductors visible
The rear camera provides a separate view of the rear connections at frame1.

Manufacturer drawings establish the selected models' nominal dimensional
bounds and PCB lead positions. Their unmeasured molded details, rounded
corners, markings and surface appearance remain illustrations. Historical
part identity and exact fitted geometry remain qualified in the model source
records. This view does not certify clearances, switch travel, wiring routing,
thermal performance, manufacture or physical assembly fit.

Source geometry is a composite: preserved revision7 assembly plus selected
revision11 native component meshes. It is not a newly imported whole-board
GLB. See revision-8-change-record.json and verification reports for provenance.
''')
scene['opening_notes_text'] = opening_name
scene.frame_set(1)
bpy.context.view_layer.update()
assert sha(BASELINE) == baseline_sha
material_roles = {m.name: m['revision11_material_role'] for m in bpy.data.materials
                  if m.get('revision11_material_role') and m.users > 0}
record = dict(visualization_revision=8, kicad_revision=11,
    geometry_basis=scene['revision_8_geometry_basis'],
    preserved_baseline_scene='blender-case-revision-7/x0xb0x-populated-with-case.blend',
    preserved_baseline_sha256=baseline_sha, native_reference_count=491,
    updated_reference_count=len(selected), source_plan_sha256=sha(PLAN),
    references=records, retained_unused_baseline_materials=retained_unused_materials,
    current_opening_notes_text=opening_name, current_opening_notes_sha256=hashlib.sha256(opening.as_string().encode()).hexdigest(),
    selected_material_role_assignments=material_roles,
    selected_shader_basis='Exact source colors identify nonmetal body/coating and metal leads; roughness0.42, nonemissive, nontransmissive; presentation only',
    physical_fit_qualified=False)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
record['saved_scene_sha256'] = sha(OUTPUT)
record['saved_scene_bytes'] = OUTPUT.stat().st_size
(HERE / 'revision-8-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: val for key, val in record.items() if key != 'references'}, indent=2))
