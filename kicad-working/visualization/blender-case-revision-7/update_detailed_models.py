"""Replace board assets with fresh native exports of populated KiCad projects.

Run on preserved revision6 scene. Electrical and source model geometry is
never edited here. The detached historical I/O outline stays a hidden reference.
"""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Matrix

HERE = Path(__file__).resolve().parent
scene = bpy.context.scene
scene.frame_set(1)
plan = json.loads((HERE / 'board-meshes/source-model-plan.json').read_text())
new = {(r['board'], ref): r for r in plan['updated_assignments'] for ref in r['references']}
allrows = {(r['board'], ref): r for r in plan['assignments'] for ref in r['references']}
instances = {
    'mainboard': bpy.data.objects['Mainboard — B.Cu outward in assembled view'],
    'ioboard': bpy.data.objects['I/O board — rear mounting approximation'],
}
poses = {k: [list(r) for r in o.matrix_world] for k, o in instances.items()}

# Caps physically belong to PCB switches. Preserve their assembled geometry,
# then let them follow the board in the exploded view. Remove old lens doubles;
# replacement native LED models contain the complete raised body and leads.
cap_names = [f'S{i} / switch cap proxy' for i in range(5, 28)]
cap_world = {}
cap_visibility = {}
front_instance = bpy.data.objects['Front controls — presentation proxies']
front_source_collection = front_instance.instance_collection
def effective_hidden(obj, attribute):
    while obj:
        if getattr(obj, attribute):
            return True
        obj = obj.parent
    return False
for frame in [1, 80, 120, 160]:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    cap_visibility[frame] = {name: {key: (frame == 120 or
                                        effective_hidden(front_instance, key) or
                                        effective_hidden(bpy.data.objects[name], key))
                                   for key in ['hide_render', 'hide_viewport']}
                             for name in cap_names}
scene.frame_set(1)
bpy.context.view_layer.update()
# A source object inside an instanced collection does not itself have the
# displayed world transform. Capture the evaluated collection instance, which
# includes the front-panel transform exactly once.
cap_instances = {name: [] for name in cap_names}
for evaluated_instance in bpy.context.evaluated_depsgraph_get().object_instances:
    name = evaluated_instance.object.original.name
    if name in cap_instances:
        cap_instances[name].append(evaluated_instance.matrix_world.copy())
assert all(len(rows) == 1 for rows in cap_instances.values()), cap_instances
cap_world = {name: rows[0] for name, rows in cap_instances.items()}
for name in cap_names:
    expected = front_instance.matrix_world @ bpy.data.objects[name].matrix_world
    assert max(abs(a-b) for x,y in zip(cap_world[name],expected)
               for a,b in zip(x,y)) < 1e-7, name
removed_lenses = []
for obj in list(bpy.data.objects):
    if obj.name.startswith('LED') and obj.name.endswith(' / visible lens proxy'):
        removed_lenses.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)
assert len(removed_lenses) == 40


# Remove superseded board data; earlier deliverables retain the original assets.
for obj in list(bpy.data.objects):
    if obj.get('source_board') in instances or obj.name.startswith('Historical detached Dimension outline') or 'separate Grayhill review envelope' in obj.name or obj.name.startswith('Grayhill published envelope'):
        bpy.data.objects.remove(obj, do_unlink=True)
for c in list(bpy.data.collections):
    if any(s in c.name for s in ['immutable native KiCad GLB', 'DISPLAY / I/O populated PCB', 'REFERENCE / Historical detached Dimension outline', 'REVIEW / Grayhill']):
        bpy.data.collections.remove(c)

def move(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)

def ancestor_reference(obj):
    while obj:
        if obj.get('source_reference'):
            return obj['source_reference']
        obj = obj.parent
    return None

records = {}
led_optical_materials = set()
def linear(v):
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
for name, instance in instances.items():
    source = bpy.data.collections.new('SOURCE / ' + name + ' / immutable native KiCad GLB — revision 10')
    source.use_fake_user = True
    before = set(bpy.data.objects)
    path = HERE / 'board-meshes' / (name + '.glb')
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = [o for o in bpy.data.objects if o not in before]
    refs = {ref for r in plan['assignments'] if r['board'] == name for ref in r['references']}
    seen = set()
    for obj in objects:
        move(obj, source)
        base = obj.name
        if '.' in base and base.rsplit('.', 1)[-1].isdigit():
            base = base.rsplit('.', 1)[0]
        if base in refs:
            obj['source_reference'] = base
            seen.add(base)
            obj.name = name.upper() + '/' + base
            if (name, base) in allrows:
                row = allrows[name, base]
                obj['model_classification'] = row.get('classification','Preserved native KiCad model')
                obj['model_limitations'] = ' | '.join(row.get('limitations',[]))
                obj['source_urls'] = ' | '.join(row.get('source_urls',[]))
                if (name, base) in new: obj['detailed_model_revision'] = 10
    assert seen == refs, (name, sorted(refs - seen))
    for obj in objects:
        obj['source_board'] = name
        obj['native_export_geometry_preserved'] = True
        if obj.type == 'MESH':
            ref = ancestor_reference(obj)
            obj.name = name.upper() + '/' + (ref or 'PCB layers') + '/mesh'
            for material in obj.data.materials:
                if material and material.use_nodes:
                    shader = material.node_tree.nodes.get('Principled BSDF')
                    if shader:
                        shader.inputs['Roughness'].default_value = .42
                        if name == 'mainboard' and ref and ref.startswith('LED'):
                            rgb = shader.inputs['Base Color'].default_value[:3]
                            lens_rgb = [linear(v) for v in [.72, .82, .85]]
                            if max(abs(a-b) for a,b in zip(rgb,lens_rgb)) < 1e-6:
                                shader.inputs['Metallic'].default_value = 0
                                shader.inputs['Transmission Weight'].default_value = .85
                                shader.inputs['IOR'].default_value = 1.5
                                shader.inputs['Roughness'].default_value = .18
                                shader.inputs['Emission Strength'].default_value = 0
                                material['optical_classification'] = 'Unlit clear LED body presentation approximation; not optical material certification'
                                led_optical_materials.add(material.name)
    instance.instance_collection = source
    records[name] = dict(expected_components=len(refs), imported_components=len(seen),
                         source_glb_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         mesh_objects=sum(o.type == 'MESH' for o in objects),
                         vertices=sum(len(o.data.vertices) for o in objects if o.type == 'MESH'))

    if name != 'ioboard':
        continue
    display = bpy.data.collections.new('DISPLAY / I/O populated PCB — revision 10')
    display.use_fake_user = True
    reference = bpy.data.collections.new('REFERENCE / Historical detached Dimension outline — revision 10')
    reference.use_fake_user = True
    splits = []
    def subset(original, indices, label, target):
        if not indices:
            return None
        old = original.data
        used = sorted({v for i in indices for v in old.polygons[i].vertices})
        remap = {v: i for i, v in enumerate(used)}
        mesh = bpy.data.meshes.new(original.name + label)
        mesh.from_pydata([old.vertices[i].co[:] for i in used], [],
                         [[remap[v] for v in old.polygons[i].vertices] for i in indices])
        mesh.update()
        for material in old.materials:
            mesh.materials.append(material)
        for poly, idx in zip(mesh.polygons, indices):
            poly.material_index = old.polygons[idx].material_index
            poly.use_smooth = old.polygons[idx].use_smooth
        va = mesh.attributes.new('original_vertex_index', 'INT', 'POINT')
        va.data.foreach_set('value', used)
        fa = mesh.attributes.new('original_polygon_index', 'INT', 'FACE')
        fa.data.foreach_set('value', indices)
        obj = bpy.data.objects.new(original.name + label, mesh)
        target.objects.link(obj)
        obj.matrix_world = original.matrix_world.copy()
        obj['source_board'] = name
        obj['original_native_mesh'] = original.name
        obj['classification'] = 'Exact source subset; original mesh retained separately'
        return obj
    for obj in source.objects:
        selected = []
        if obj.type == 'MESH' and ancestor_reference(obj) is None:
            world = [obj.matrix_world @ v.co for v in obj.data.vertices]
            for p in obj.data.polygons:
                if all(-.004065 <= world[v].x <= .218187 and -.002160 <= world[v].y <= -.000507 for v in p.vertices):
                    selected.append(p.index)
        if not selected:
            display.objects.link(obj)
            continue
        chosen = set(selected)
        retained = [p.index for p in obj.data.polygons if p.index not in chosen]
        a = subset(obj, retained, ' / populated PCB subset', display)
        b = subset(obj, selected, ' / historical reference subset', reference)
        splits.append(dict(original=obj.name, detached_polygon_indices=selected,
                           source_vertices=len(obj.data.vertices), source_polygons=len(obj.data.polygons),
                           retained_polygons=len(retained), reference_polygons=len(selected),
                           reference_vertices=len(b.data.vertices)))
    assert sum(r['reference_polygons'] for r in splits) == 92, splits
    assert sum(r['reference_vertices'] for r in splits) == 130, splits
    instance.instance_collection = display
    hidden = bpy.data.objects.new('Historical detached Dimension outline — hidden reference', None)
    hidden.instance_type = 'COLLECTION'
    hidden.instance_collection = reference
    bpy.data.collections['99 Review notes — no clearance certification'].objects.link(hidden)
    hidden.parent = instance
    hidden.matrix_basis = Matrix.Identity(4)
    hidden.hide_render = True
    hidden.hide_viewport = True
    hidden['classification'] = 'Original detached Dimension construction reference; historical identity qualified'
    records[name]['historical_reference_split'] = splits

# Preserve the assembled cap poses and meshes; correct their exploded ownership.
scene.frame_set(1)
bpy.context.view_layer.update()
cap_records = []
cap_display = bpy.data.collections.new('DISPLAY / PCB-mounted switch caps — revision 7')
scene.collection.children.link(cap_display)
for name in cap_names:
    obj = bpy.data.objects[name]
    assert not obj.constraints
    obj.animation_data_clear()
    # Remove the source object from the panel's instanced collection. Otherwise
    # its new PCB parenting would be composed with the panel transform again.
    move(obj, cap_display)
    obj.parent = instances['mainboard']
    # Keep the full affine local matrix in parent_inverse. Decomposing a nearly
    # 180degree relative orientation into Euler TRS introduces avoidable float
    # residuals; identity basis preserves the captured matrix without that step.
    obj.matrix_parent_inverse = instances['mainboard'].matrix_world.inverted() @ cap_world[name]
    obj.matrix_basis = Matrix.Identity(4)
    obj['assembly_attachment'] = 'Cap fitted to PCB-mounted switch; follows mainboard'
    for frame, rows in cap_visibility.items():
        for key, value in rows[name].items():
            setattr(obj, key, value)
            obj.keyframe_insert(data_path=key, frame=frame)
    cap_records.append(dict(object=name, assembled_world=[list(r) for r in cap_world[name]],
                            local_to_board=[list(r) for r in obj.matrix_parent_inverse @ obj.matrix_basis],
                            ordinary_scene_collection=cap_display.name,
                            source_front_collection_removed=front_source_collection.name))
scene.frame_set(1)
bpy.context.view_layer.update()
cap_pose_residuals = []
for name in cap_names:
    actual = bpy.data.objects[name].matrix_world
    expected = cap_world[name]
    cap_pose_residuals.append(dict(
        object=name,
        maximum_matrix_residual=max(abs(a-b) for x,y in zip(actual,expected)
                                    for a,b in zip(x,y)),
        maximum_translation_residual_mm=max(abs(actual[i][3]-expected[i][3])
                                           for i in range(3))*1000,
        maximum_vertex_residual_mm=max(((actual @ v.co)-(expected @ v.co)).length
                                      for v in bpy.data.objects[name].data.vertices)*1000,
        actual_world=[list(r) for r in actual],
        original_rendered_world=[list(r) for r in expected]))
(HERE/'verification/front-cap-pose-residuals.json').write_text(
    json.dumps(cap_pose_residuals,indent=2)+'\n')
assert all(row['maximum_matrix_residual'] < 1e-7
           and row['maximum_vertex_residual_mm'] < .001
           for row in cap_pose_residuals), cap_pose_residuals
(HERE/'verification/front-control-assembly-change.json').write_text(json.dumps(
    dict(removed_duplicate_LED_lenses=removed_lenses, one_native_LED_per_reference=True,
         cap_count=len(cap_records), caps=cap_records, cap_effective_visibility=cap_visibility,
         cap_baseline_transform_basis='Actual evaluated revision6 collection-instance world matrices; front-panel transform included exactly once',
         cap_display_collection=cap_display.name,
         caps_removed_from_old_front_instance_source=True,
         cap_pose_residuals=cap_pose_residuals,
         clear_LED_optical_materials=sorted(led_optical_materials),
         clear_LED_optical_approximation=dict(metallic=0,transmission=.85,IOR=1.5,roughness=.18,emission_strength=0),
         case_panel_board_poses_preserved=True,
         LED_mounting_basis='Original BOM STD240B 0.24 inch length; older sequencer0.22inch entry remains a documented alternative',
         physical_fit_qualified=False), indent=2)+'\n')

# Preserve all existing case, panel, knob and assembled cap geometry.

assert poses == {k: [list(r) for r in o.matrix_world] for k, o in instances.items()}
scene['visualization_revision'] = 7
scene['native_PCB_model_count'] = plan['assigned_instance_count']
scene['detailed_model_count'] = plan['updated_instance_count']
scene['body_model_status'] = 'Reviewed manufacturer CAD or drawing-derived detailed replacements. Unsized details and historical revisions remain qualified per source manifest.'
report=json.loads((HERE/'scene-build-record.json').read_text())
report.update(visualization_revision=7,boards=records,native_model_count=491,detailed_replaced_references=plan['updated_instance_count'],updated_model_rows=plan['updated_assignments'],case_panels_controls_caps_preserved=True)
(HERE/'scene-build-record.json').write_text(json.dumps(report,indent=2)+'\n')
(HERE/'revision-7-change-record.json').write_text(json.dumps(dict(revision=7,native_references=491,detailed_replaced_references=plan['updated_instance_count'],boards=records,board_assembly_poses_preserved=poses,case_panels_knobs_labels_caps_preserved=True),indent=2)+'\n')
readme=bpy.data.texts.get('READ ME — assembly evidence and controls')
if readme:
 readme.clear();readme.write((HERE/'README.md').read_text())
scene.frame_set(1);scene.camera=bpy.data.objects['Camera / assembled and exploded']
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'x0xb0x-populated-with-case.blend'),compress=True)
print(json.dumps(dict(saved=True,references=491,detailed_models=plan['updated_instance_count'],boards=records),indent=2))
