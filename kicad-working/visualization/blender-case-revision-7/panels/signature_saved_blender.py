"""Cache signatures from the fully audited file or verify the final shell update.

This reads the saved Blender file and writes audit evidence only. It never
saves Blender state. --baseline requires the SHA from the full independent
geometry audit. --verify permits case shell and viewport-only changes.
"""
import bpy
from pathlib import Path
import array
import collections
import hashlib
import json
import sys

BASE=Path(__file__).resolve().parent.parent
SCENE=bpy.context.scene
FULL=BASE/'panels/independent-saved-blender-audit.json'
CACHE=BASE/'panels/fully-audited-scene-signatures.json'
FINAL=BASE/'panels/final-saved-blender-signature-check.json'

def rounded_matrix(m):
    return [[round(v,8) for v in row] for row in m]

def native_mesh_signature(collection):
    signatures=collections.Counter()
    meshes=[o for o in collection.objects if o.type=='MESH']
    for o in meshes:
        co=array.array('f',[0])*(len(o.data.vertices)*3)
        o.data.vertices.foreach_get('co',co)
        loops=array.array('i',[0])*len(o.data.loops)
        o.data.loops.foreach_get('vertex_index',loops)
        starts=array.array('i',[0])*len(o.data.polygons)
        counts=array.array('i',[0])*len(o.data.polygons)
        o.data.polygons.foreach_get('loop_start',starts)
        o.data.polygons.foreach_get('loop_total',counts)
        geometry=hashlib.sha256(co.tobytes()+loops.tobytes()+starts.tobytes()+counts.tobytes()).hexdigest()
        pose=tuple(round(v,9) for row in o.matrix_world for v in row)
        signatures[(geometry,pose)]+=1
    serialized=sorted([[geometry,list(pose),count] for (geometry,pose),count in signatures.items()])
    return {'geometry_and_native_transform_sha256':hashlib.sha256(json.dumps(serialized,separators=(',',':')).encode()).hexdigest(),
            'mesh_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),
            'component_reference_count':len({o.get('source_reference') for o in collection.objects if o.get('source_reference')}),
            'geometry_modifiers':sum(len(o.modifiers) for o in meshes)}

report={'file_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
        'file_path':bpy.data.filepath,'blender_version':bpy.app.version_string,
        'signature':{'saved_frame':SCENE.frame_current,'saved_camera':SCENE.camera.name,
                     'units':{'system':SCENE.unit_settings.system,'scale_length':SCENE.unit_settings.scale_length,
                              'length_unit':SCENE.unit_settings.length_unit},'assets':{},'frames':{}}}
assets={'mainboard':'Mainboard — B.Cu outward in assembled view',
        'ioboard':'I/O board — rear mounting approximation',
        'mainpanel':'Top panel — original DXF','iopanel':'Rear panel — original DXF'}
for key,object_name in assets.items():
    collection=(bpy.data.collections['SOURCE / '+key+' / immutable native KiCad GLB']
                if key in {'mainboard','ioboard'} else bpy.data.objects[object_name].instance_collection)
    report['signature']['assets'][key]=native_mesh_signature(collection)
report['signature']['assets']['IO_display']=native_mesh_signature(bpy.data.objects[assets['ioboard']].instance_collection)
report['signature']['assets']['historical_reference']=native_mesh_signature(bpy.data.objects['Historical detached Dimension outline — hidden reference'].instance_collection)
controls=bpy.data.collections['SOURCE / Front controls — presentation proxies, not ECAD models']
label_data=sorted([[o.name,o.data.body,rounded_matrix(o.matrix_world),round(o.data.size,9)] for o in controls.objects if o.type=='FONT'])
report['signature']['label_layout_sha256']=hashlib.sha256(json.dumps(label_data,separators=(',',':')).encode()).hexdigest()
cap_data=sorted([[o.name,rounded_matrix(o.matrix_world),o.active_material.name if o.active_material else None] for o in controls.objects if '/ switch cap proxy' in o.name])
report['signature']['cap_pose_color_sha256']=hashlib.sha256(json.dumps(cap_data,separators=(',',':')).encode()).hexdigest()
for frame in [1,80,120]:
    SCENE.frame_set(frame)
    f={key:rounded_matrix(bpy.data.objects[name].matrix_world) for key,name in assets.items()}
    f['camera_matrix']=rounded_matrix(SCENE.camera.matrix_world)
    f['camera_name']=SCENE.camera.name
    f['camera_lens_mm']=SCENE.camera.data.lens
    f['camera_type']=SCENE.camera.data.type
    f['camera_ortho_scale']=SCENE.camera.data.ortho_scale
    f['exposure']=SCENE.view_settings.exposure
    f['review_envelopes']={ref:{'local_matrix':rounded_matrix(bpy.data.objects[ref+' / separate Grayhill review envelope'].matrix_basis),
                             'hide_render':bpy.data.objects[ref+' / separate Grayhill review envelope'].hide_render,
                             'hide_viewport':bpy.data.objects[ref+' / separate Grayhill review envelope'].hide_viewport} for ref in ['S3','S4']}
    f['panel_hidden']=bpy.data.objects['Top panel — original DXF'].hide_render
    f['front_proxies_hidden']=bpy.data.objects['Front controls — presentation proxies'].hide_render
    report['signature']['frames'][str(frame)]=f
SCENE.frame_set(1)
if '--baseline' in sys.argv:
    full=json.loads(FULL.read_text())
    assert full['passed'] and full['file_sha256']==report['file_sha256'], 'Baseline file must be the exact fully audited file'
    report['full_audit_check_count']=len(full['checks'])
    report['full_audit_sha256']=hashlib.sha256(FULL.read_bytes()).hexdigest()
    CACHE.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'baseline_cached':True,'fully_audited_file_sha256':report['file_sha256']},indent=2))
elif '--verify' in sys.argv:
    baseline=json.loads(CACHE.read_text())
    report['baseline_fully_audited_file_sha256']=baseline['file_sha256']
    report['baseline_full_audit_check_count']=baseline['full_audit_check_count']
    report['passed']=report['signature']==baseline['signature']
    report['scope']='Final saved file preserves the fully independently audited native-board and panel geometry, object transforms, unit settings, component counts and frame1/frame80 camera/assembly poses. Case-shell replacements and viewport overlays are intentionally outside this signature. No Blender changes saved.'
    FINAL.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'final_file_sha256':report['file_sha256'],'baseline_file_sha256':baseline['file_sha256']},indent=2))
else:
    raise ValueError('Specify --baseline or --verify')
