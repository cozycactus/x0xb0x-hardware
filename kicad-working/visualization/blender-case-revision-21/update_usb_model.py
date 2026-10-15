"""Apply the BOM USB model to one existing mesh; preserve all assembly objects."""
import hashlib
import json
import sys
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
BASELINE=HERE.parent/'blender-case-revision-20/x0xb0x-populated-with-case.blend'
OUTPUT=HERE/'x0xb0x-populated-with-case.blend'
REVIEW=WORK/'validation/models-review-18'
sys.path.insert(0,str(HERE/'verification'))
from scene_snapshot import sha,mesh_signature,material_signature,matrix
assert Path(bpy.data.filepath).resolve()==BASELINE.resolve()
assert not OUTPUT.exists(),'Preserve frozen scenes'
export=json.loads((REVIEW/'native-export-record.json').read_text())['boards']['ioboard']
source=REVIEW/export['glb'];assert sha(source)==export['glb_sha256']
plan=json.loads((REVIEW/'combined-model-plan.json').read_text())
row=next(r for r in plan['assignments'] if r['board']=='ioboard' and r['references']==['USB0'])
scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['IOBOARD/USB0'];target=bpy.data.objects['IOBOARD/USB0/mesh']
old_objects=set(bpy.data.objects)
old_materials={m.name:material_signature(m) for m in bpy.data.materials}
old_mesh=mesh_signature(target.data)
old_sets={name:set(getattr(bpy.data,name)) for name in ('objects','collections','meshes','materials','images','cameras','lights','actions')}
baseline_hash=sha(BASELINE)
palette=list(target.data.materials)
def colour(m):return tuple(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)
def delta(a,b):return max(abs(x-y) for p,q in zip(a,b) for x,y in zip(p,q))
bpy.ops.import_scene.gltf(filepath=str(source));bpy.context.view_layer.update()
imported=set(bpy.data.objects)-old_objects
incoming=next(o for o in imported if o.name=='USB0' or o.name.startswith('USB0.'))
assert delta(incoming.matrix_world,root.matrix_world)<1e-7
parts=sorted([o for o in incoming.children_recursive if o.type=='MESH'],key=lambda o:o.name)
assert parts
vertices=[];faces=[];face_slots=[];smooth=[];normals=[];native_parts=[]
gold=None
for part in parts:
    local=target.matrix_world.inverted()@part.matrix_world
    # Each part in the canonical frame; aggregation changes only storage, not
    # the source vertices or triangles. All matrices are recorded below.
    offset=len(vertices)
    vertices.extend([local@v.co for v in part.data.vertices])
    mapping=[]
    for material in part.data.materials:
        matches=[m for m in palette if max(abs(a-b) for a,b in zip(colour(m),colour(material)))<1e-6]
        if not matches:
            assert gold is None,'Only one new material is allowed'
            gold=material.copy();gold.name='USB mating contact gold — drawing revision 18'
            shader=gold.node_tree.nodes['Principled BSDF']
            shader.inputs['Metallic'].default_value=1.
            shader.inputs['Roughness'].default_value=.35
            gold['source_basis']='Kobiconn KC-301021 specifies gold-plated contacts; shader roughness is illustrative'
            palette.append(gold);matches=[gold]
        assert len(matches)==1
        mapping.append(palette.index(matches[0]))
    transform=local.to_3x3().inverted().transposed()
    for poly in part.data.polygons:
        faces.append([offset+i for i in poly.vertices]);face_slots.append(mapping[poly.material_index]);smooth.append(poly.use_smooth)
        normals.extend([(transform@part.data.corner_normals[i].vector).normalized() for i in poly.loop_indices])
    native_parts.append(dict(name=part.name,vertices=len(part.data.vertices),polygons=len(part.data.polygons),canonical_transform=matrix(local)))
assert gold is not None
mesh=bpy.data.meshes.new('IOBOARD/USB0/revision18 native aggregate')
mesh.from_pydata(vertices,[],faces);mesh.update()
for m in palette:mesh.materials.append(m)
for p,slot,shading in zip(mesh.polygons,face_slots,smooth):p.material_index=slot;p.use_smooth=shading
mesh.normals_split_custom_set(normals)
assert len(mesh.vertices)==sum(r['vertices'] for r in native_parts)
assert len(mesh.polygons)==sum(r['polygons'] for r in native_parts)
previous=target.data;target.data=mesh
if previous.users==0:bpy.data.meshes.remove(previous)
for obj in imported:bpy.data.objects.remove(obj,do_unlink=True)
for category in ('collections','meshes','materials','images','cameras','lights','actions'):
    block=getattr(bpy.data,category)
    for item in set(block)-old_sets[category]:
        if item.users==0:block.remove(item)
assert set(bpy.data.objects)==old_objects
assert all(material_signature(bpy.data.materials[n])==s for n,s in old_materials.items())
assert set(m.name for m in bpy.data.materials)-set(old_materials)=={gold.name}
root['model_classification']=row['classification']
root['model_limitations']=' | '.join(row['limitations'])
root['detailed_model_revision']=18
root['selected_native_source_glb_sha256']=sha(source)
root['source_geometry_basis']='Exact native KiCad18 USB model, parts aggregated into the preserved single mesh object; BOM standoff/projections and insulated signal exits corrected'
guide_name='00 START HERE — revision 21 assembly'
guide=bpy.data.texts.new(guide_name)
guide.write('''x0xb0x enclosure assembly — Blender revision21 / KiCad revision18

USB0 now follows the recovered original BOM Kobiconn154-2442-E drawing
KC-301021 (2006-07-19): body0.38mm above PCB, signal pins2.91mm and
mounting tabs3.72mm below PCB. The old body envelope and mating cavity,
XY axes and original component root are retained. The previous terminal
dimensions came from another connector (FCI61729).

The four signal pins no longer intersect the metal shell floor in this
illustration: insulated exits are added. Four illustrative gold-plated
mating strips follow the drawing's appearance. Exit, strip, stock and
fork dimensions and hidden internal routing remain unqualified.

Only USB0 mesh data and source metadata change. One gold shader is added;
all existing objects, materials, poses, PCB layout, case, LEDs, caps,
camera views and animation remain preserved. All491 fitted references
remain embedded. The native assembly parts are aggregated without changing
their geometry into the existing USB mesh object.

Frames1 assembled;80 exploded;120 control-side;160 wiring study.
See revision-21-change-record.json and verification for evidence.
This is drawing-derived illustration, not physical fit certification.
''')
scene['visualization_revision']=21;scene['opening_notes_text']=guide_name
scene['revision_21_baseline_scene_sha256']=baseline_hash
scene['revision_21_geometry_basis']='USB0 only, KiCad18 BOM drawing correction; all poses retained'
scene['revision_21_corrected_reference_count']=1
scene['revision_21_KiCad_revision']=18
scene.frame_set(1);bpy.context.view_layer.update();assert sha(BASELINE)==baseline_hash
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),compress=True,check_existing=False)
record=dict(passed=True,visualization_revision=21,kicad_revision=18,baseline_sha256=baseline_hash,stable_scene_sha256=sha(OUTPUT),stable_scene_bytes=OUTPUT.stat().st_size,
 source_glb_sha256=sha(source),source_plan_sha256=sha(REVIEW/'combined-model-plan.json'),
 replaced_mesh_objects=[target.name],changed_source_roots=[root.name],added_objects=[],added_materials=[gold.name],gold_material_signature=material_signature(gold),
 old_mesh=old_mesh,new_mesh=mesh_signature(mesh),native_parts=native_parts,
 native_reference_count=491,stored_object_count=len(old_objects),all_previous_materials_retained_exactly=True,
 opening_guide=guide_name,opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(),physical_fit_qualified=False)
(HERE/'revision-21-change-record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ['old_mesh','new_mesh','native_parts','gold_material_signature']},indent=2),flush=True)
