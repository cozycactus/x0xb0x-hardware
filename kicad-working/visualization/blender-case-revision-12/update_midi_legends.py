"""Correct three MIDI legend strings without changing any component geometry."""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
BASELINE=HERE.parent/'blender-case-revision-11/x0xb0x-populated-with-case.blend'
OUTPUT=HERE/'x0xb0x-populated-with-case.blend'
sys.path.insert(0,str(HERE.parent/'blender-case-revision-11/verification'))
from scene_snapshot import props,sha

LABELS={'DIN1 label':('MIDI IN','MIDI OUT'),
        'DIN2 label':('MIDI OUT','THRU'),
        'DIN3 label':('THRU','MIDI IN')}


def matrix(value):
    return[list(row)for row in value]


def font_signature(data):
    return dict(body=data.body,size=data.size,extrude=data.extrude,offset=data.offset,
        align_x=data.align_x,align_y=data.align_y,
        fonts=[getattr(data,key).name if getattr(data,key)else None
               for key in('font','font_bold','font_italic','font_bold_italic')],
        materials=[material.name if material else None for material in data.materials],
        props=props(data))


def glyph_gaps():
    wanted=set(LABELS)|{'iopanel — exact DXF profile'}
    points={};matrices={}
    for inst in bpy.context.evaluated_depsgraph_get().object_instances:
        obj=inst.object;name=obj.original.name
        if name not in wanted or name in points:continue
        mesh=obj.to_mesh()
        points[name]=[inst.matrix_world@vertex.co for vertex in mesh.vertices]
        matrices[name]=inst.matrix_world.copy()
        obj.to_mesh_clear()
    assert set(points)==wanted
    panel='iopanel — exact DXF profile'
    normal=(matrices[panel].to_3x3()@Vector((0,0,1))).normalized()
    plane=max(point.dot(normal)for point in points[panel])
    return{name:dict(back_gap_mm=(min(point.dot(normal)for point in points[name])-plane)*1000,
                     front_gap_mm=(max(point.dot(normal)for point in points[name])-plane)*1000)
           for name in LABELS}


assert not OUTPUT.exists(),'Refusing to overwrite an existing saved scene'
baseline_sha=sha(BASELINE)
assert baseline_sha=='fc02d403f1bcac0aa98937fd29e5f8d77e01f69400104278ea512d36eea01ff9'
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
scene=bpy.context.scene
scene.frame_set(1);bpy.context.view_layer.update()
original_objects=set(bpy.data.objects.keys())
original_materials=set(bpy.data.materials.keys())
original_font_bodies={obj.name:obj.data.body for obj in bpy.data.objects if obj.type=='FONT'}
before_gaps=glyph_gaps()
changes=[]
for name,(old_body,new_body)in LABELS.items():
    obj=bpy.data.objects[name]
    assert obj.type=='FONT'and obj.data.users==1 and obj.data.body==old_body
    original_data=obj.data
    original_signature=font_signature(obj.data)
    original_matrix=matrix(obj.matrix_world)
    original_basis=matrix(obj.matrix_basis)
    original_collections=sorted(collection.name for collection in obj.users_collection)
    obj.data.body=new_body
    bpy.context.view_layer.update()
    updated=font_signature(obj.data)
    assert obj.data==original_data
    assert{key:value for key,value in original_signature.items()if key!='body'}=={key:value for key,value in updated.items()if key!='body'}
    assert matrix(obj.matrix_world)==original_matrix and matrix(obj.matrix_basis)==original_basis
    assert sorted(collection.name for collection in obj.users_collection)==original_collections
    changes.append(dict(object=name,reference=name.split()[0],
        original_body=old_body,corrected_body=new_body,
        unchanged_matrix=original_matrix,unchanged_matrix_basis=original_basis,
        unchanged_collection_links=original_collections,
        original_font_signature=original_signature,saved_font_signature=updated,
        original_glyph_back_gap_mm=before_gaps[name]['back_gap_mm'],
        original_glyph_front_gap_mm=before_gaps[name]['front_gap_mm']))
after_gaps=glyph_gaps()
for row in changes:
    actual=after_gaps[row['object']]
    assert abs(actual['back_gap_mm']-.01)<.0001,actual
    assert abs(actual['back_gap_mm']-row['original_glyph_back_gap_mm'])<.0001,actual
    row['saved_glyph_back_gap_mm']=actual['back_gap_mm']
    row['saved_glyph_front_gap_mm']=actual['front_gap_mm']
for name,body in original_font_bodies.items():
    if name not in LABELS:assert bpy.data.objects[name].data.body==body
assert bpy.data.objects['DIN4 label'].data.body=='SYNC'
assert set(bpy.data.objects.keys())==original_objects
assert set(bpy.data.materials.keys())==original_materials
assert sum(bool(obj.get('source_reference'))for obj in bpy.data.objects)==491
guide_name='00 START HERE — revision 12 assembly'
guide=(HERE/'README.md').read_text()
assert guide_name not in bpy.data.texts
bpy.data.texts.new(guide_name).write(guide)
scene['visualization_revision']=12
scene['opening_notes_text']=guide_name
scene['revision_12_baseline_scene_sha256']=baseline_sha
scene['revision_12_geometry_basis']='Preserved revision11 complete assembly; only three original MIDI FONTbody strings corrected to DIN1 MIDI OUT,DIN2 THRU,DIN3 MIDI IN from electrical topology. FONT styles/materials/poses and every native component,case/panel/hardware mesh are unchanged.'
scene['revision_12_corrected_midi_legend_count']=len(changes)
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False)
assert sha(BASELINE)==baseline_sha
record=dict(visualization_revision=12,kicad_revision=11,
    preserved_baseline_scene='blender-case-revision-11/'+BASELINE.name,
    preserved_baseline_sha256=baseline_sha,saved_scene=OUTPUT.name,
    saved_scene_sha256=sha(OUTPUT),saved_scene_bytes=OUTPUT.stat().st_size,
    corrected_midi_legend_count=len(changes),corrected_objects=list(LABELS),
    legend_changes=changes,
    unchanged_DIN4_display_text='SYNC',
    function_mapping={'DIN1':'MIDI OUT','DIN2':'MIDI THRU','DIN3':'MIDI IN','DIN4':'DIN SYNC'},
    mapping_basis='Independently verified original Eagle and current KiCad electrical topology; see validation/din-midi-review and independent verification.',
    current_opening_notes_text=guide_name,
    current_opening_notes_sha256=hashlib.sha256(guide.encode()).hexdigest(),
    native_geometry_changed=False,kicad_files_changed=False,
    hardware_changed=False,case_or_panel_geometry_changed=False,
    FONT_style_material_or_pose_changed=False,
    glyph_back_gap_nominal_mm=.01,physical_fit_qualified=False)
(HERE/'revision-12-change-record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({key:value for key,value in record.items()if key!='legend_changes'},indent=2))
