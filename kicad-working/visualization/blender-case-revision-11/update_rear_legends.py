"""Reseat eleven rear legends on the panel without changing any FONT data."""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
BASELINE=HERE.parent/'blender-case-revision-10/x0xb0x-populated-with-case.blend'
OUTPUT=HERE/'x0xb0x-populated-with-case.blend'
sys.path.insert(0,str(HERE.parent/'blender-case-revision-10/verification'))
from scene_snapshot import props,sha

REFERENCES=('POWER0','HEADPHONE0','GATE0','CV0','USB0','MIXOUT0','DIN1','DIN2','DIN3','MIXIN0','DIN4')
NAMES=[ref+' label'for ref in REFERENCES]
TARGET_BACK_GAP_MM=.01


def matrix(value):
    return[list(row)for row in value]


def font_signature(data):
    return dict(body=data.body,size=data.size,extrude=data.extrude,offset=data.offset,
        align_x=data.align_x,align_y=data.align_y,
        fonts=[getattr(data,key).name if getattr(data,key)else None
               for key in('font','font_bold','font_italic','font_bold_italic')],
        materials=[material.name if material else None for material in data.materials],
        props=props(data))


def evaluated_surfaces():
    graph=bpy.context.evaluated_depsgraph_get()
    wanted=set(NAMES)|{'iopanel — exact DXF profile'}
    meshes={}
    matrices={}
    for inst in graph.object_instances:
        obj=inst.object
        name=obj.original.name
        if name not in wanted or name in meshes:
            continue
        mesh=obj.to_mesh()
        meshes[name]=[inst.matrix_world@vertex.co for vertex in mesh.vertices]
        matrices[name]=inst.matrix_world.copy()
        obj.to_mesh_clear()
    assert set(meshes)==wanted
    panel='iopanel — exact DXF profile'
    normal=(matrices[panel].to_3x3()@Vector((0,0,1))).normalized()
    front=max(point.dot(normal)for point in meshes[panel])
    return normal,{name:dict(back_gap_mm=(min(point.dot(normal)for point in meshes[name])-front)*1000,
                            front_gap_mm=(max(point.dot(normal)for point in meshes[name])-front)*1000,
                            displayed_matrix=matrix(matrices[name]))for name in NAMES}


assert not OUTPUT.exists(),'Refusing to overwrite an existing saved scene'
baseline_sha=sha(BASELINE)
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
scene=bpy.context.scene
original_objects=set(bpy.data.objects.keys())
original_materials=set(bpy.data.materials.keys())
ownership=[]
for frame in(1,80,120,160):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    faces=bpy.data.objects['Rear faces — presentation proxies']
    panel=bpy.data.objects['Rear panel — original DXF']
    residual=max(abs(a-b)for left,right in zip(faces.matrix_world,panel.matrix_world)
                 for a,b in zip(left,right))
    assert residual<1e-7,'Rear legend ownership differs from panel; stop before mutation'
    ownership.append(dict(frame=frame,rear_faces_matrix=matrix(faces.matrix_world),
                          panel_matrix=matrix(panel.matrix_world),maximum_matrix_residual=residual))
scene.frame_set(1)
bpy.context.view_layer.update()
normal,before=evaluated_surfaces()
source_axis=bpy.data.objects['Rear faces — presentation proxies'].matrix_world.to_3x3()@Vector((0,0,1))
axis_projection=source_axis.dot(normal)
assert abs(axis_projection-1)<1e-7
changes=[]
for name in NAMES:
    obj=bpy.data.objects[name]
    assert obj.type=='FONT'and obj.parent is None
    original_location=list(obj.location)
    original_matrix=matrix(obj.matrix_world)
    original_data=obj.data
    signature=font_signature(original_data)
    rotation,scale=list(obj.rotation_euler),list(obj.scale)
    original_collections=sorted(collection.name for collection in obj.users_collection)
    assert obj.animation_data is None,'Unexpected per-label animation'
    delta_mm=TARGET_BACK_GAP_MM-before[name]['back_gap_mm']
    obj.location.z+=delta_mm/1000/axis_projection
    bpy.context.view_layer.update()
    assert list(obj.location)[:2]==original_location[:2]
    assert list(obj.rotation_euler)==rotation and list(obj.scale)==scale
    assert obj.data==original_data and font_signature(obj.data)==signature
    assert sorted(collection.name for collection in obj.users_collection)==original_collections
    changes.append(dict(object=name,body=obj.data.body,
        original_location_m=original_location,saved_location_m=list(obj.location),
        original_matrix=original_matrix,saved_matrix=matrix(obj.matrix_world),
        translation_along_panel_normal_mm=delta_mm,
        actual_original_back_gap_mm=before[name]['back_gap_mm'],
        actual_original_front_gap_mm=before[name]['front_gap_mm'],
        target_actual_back_gap_mm=TARGET_BACK_GAP_MM,
        unchanged_font_signature=signature,unchanged_collection_links=original_collections,
        in_plane_position_rotation_scale_and_FONT_data_preserved=True))
normal_after,after=evaluated_surfaces()
assert(normal_after-normal).length<1e-7
for row in changes:
    actual=after[row['object']]
    assert abs(actual['back_gap_mm']-TARGET_BACK_GAP_MM)<.0001,actual
    row['actual_saved_back_gap_mm']=actual['back_gap_mm']
    row['actual_saved_front_gap_mm']=actual['front_gap_mm']
    row['saved_displayed_matrix']=actual['displayed_matrix']
assert set(bpy.data.objects.keys())==original_objects
assert set(bpy.data.materials.keys())==original_materials
assert sum(bool(obj.get('source_reference'))for obj in bpy.data.objects)==491
guide_name='00 START HERE — revision 11 assembly'
guide=(HERE/'README.md').read_text()
assert guide_name not in bpy.data.texts
bpy.data.texts.new(guide_name).write(guide)
scene['visualization_revision']=11
scene['opening_notes_text']=guide_name
scene['revision_11_baseline_scene_sha256']=baseline_sha
scene['revision_11_geometry_basis']='Preserved revision10 complete assembly; only eleven original rear legend objects translated along panel normal so actual rear-most glyph surface is0.01mm above panel. FONT geometry/materials,in-plane poses and every other scene object are unchanged.'
scene['revision_11_reseated_legend_count']=len(changes)
scene.frame_set(1)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False)
assert sha(BASELINE)==baseline_sha
record=dict(visualization_revision=11,kicad_revision=11,
    preserved_baseline_scene='blender-case-revision-10/'+BASELINE.name,
    preserved_baseline_sha256=baseline_sha,saved_scene=OUTPUT.name,
    saved_scene_sha256=sha(OUTPUT),saved_scene_bytes=OUTPUT.stat().st_size,
    reseated_legend_count=len(changes),reseated_objects=NAMES,legend_changes=changes,
    original_four_view_panel_ownership=ownership,panel_outward_normal=list(normal),
    target_actual_glyph_back_gap_mm=TARGET_BACK_GAP_MM,
    current_opening_notes_text=guide_name,current_opening_notes_sha256=hashlib.sha256(guide.encode()).hexdigest(),
    native_geometry_changed=False,kicad_files_changed=False,
    hardware_changed=False,case_or_panel_geometry_changed=False,
    offset_classification='Display offset to prevent coincident surfaces; not physical ink thickness',
    physical_fit_qualified=False)
(HERE/'revision-11-change-record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({key:value for key,value in record.items()if key not in{'legend_changes','original_four_view_panel_ownership'}},indent=2))
