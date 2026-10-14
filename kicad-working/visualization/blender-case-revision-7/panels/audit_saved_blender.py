"""Independent, read-only audit of the saved Blender visual assembly."""
import bpy
from pathlib import Path
import array
import collections
import hashlib
import json
import math
from mathutils import Vector

BASE = Path(__file__).resolve().parent.parent
scene = bpy.context.scene
loaded_initial_frame = scene.frame_current
loaded_initial_camera = scene.camera.name if scene.camera else None
scene.frame_set(1)
report = {'blender_version':bpy.app.version_string,
          'loaded_file':bpy.data.filepath,
          'file_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
          'saved_initial_frame':loaded_initial_frame,
          'saved_initial_camera':loaded_initial_camera,
          'units':{'system':scene.unit_settings.system,
                   'display_length_unit':scene.unit_settings.length_unit,
                   'scale_length':scene.unit_settings.scale_length},
          'errors':[]}
checks = []
def check(condition, description):
    checks.append({'check':description,'passed':bool(condition)})
    if not condition:report['errors'].append(description)

main = bpy.data.objects['Mainboard — B.Cu outward in assembled view']
io = bpy.data.objects['I/O board — rear mounting approximation']
mp = bpy.data.objects['Top panel — original DXF']
rp = bpy.data.objects['Rear panel — original DXF']
panels = json.loads((BASE/'panels/original-panels.json').read_text())
interfaces = json.loads((BASE/'panels/board-interface-positions.json').read_text())
check(loaded_initial_frame==1 and loaded_initial_camera=='Camera / assembled and exploded',
      'Saved file opens at assembled frame1 with intended camera')
check(scene.unit_settings.system=='METRIC' and scene.unit_settings.scale_length==1,
      'SI metre geometry with metric display')
main_normal = (main.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
panel_normal = (mp.matrix_world.to_3x3()@Vector((0,0,1))).normalized()
io_normal = (io.matrix_world.to_3x3()@Vector((0,0,1))).normalized()
report['assembled_normals']={'main_BCu_world':list(main_normal),
                            'main_panel_outward':list(panel_normal),
                            'main_BCu_dot_panel_outward':main_normal.dot(panel_normal),
                            'IO_FCu_world':list(io_normal)}
check(main_normal.dot(panel_normal)>.999999,'Mainboard B.Cu faces outward at frame1')
check(io_normal.z>.999999,'I/O F.Cu faces upward at frame1')

rows=[]
for f in interfaces['mainboard']:
    cuts = [c for c in panels['mainpanel']['circles']+panels['mainpanel']['rectangular_cutouts']
            if c.get('board_reference')==f['ref']]
    if not cuts:continue
    c=cuts[0]
    xy=c.get('center_mm') or [(a+b)/2 for a,b in zip(*c['bounds_mm'])]
    native=Vector((f['x']*.001,-f['y']*.001,0))
    world=main.matrix_world@native
    local=mp.matrix_world.inverted()@world
    resid=math.dist((local.x*1000,local.y*1000),xy)
    rows.append({'ref':f['ref'],'kind':c['function'],
                 'panel_xy_from_saved_world_matrices_mm':[local.x*1000,local.y*1000],
                 'source_DXF_xy_mm':xy,'residual_mm':resid,
                 'native_Z0_normal_distance_from_panel_underside_mm':local.z*1000})
report['mainboard_registration']={k:{'count':sum(r['kind']==k for r in rows),
    'maximum_residual_mm':max(r['residual_mm'] for r in rows if r['kind']==k)}
    for k in ['LED','control','button','mount']}
report['mainboard_registration']['rows']=rows
check(len(rows)==81,'Saved matrices register all81 mainboard cutout references')
for kind,tol in [('LED',.0001),('control',.0001),('button',.092),('mount',.246)]:
    check(report['mainboard_registration'][kind]['maximum_residual_mm']<tol,
          'Mainboard '+kind+' residual preserves original panel registration')

irows=[]
for f in interfaces['ioboard']:
    cuts=[c for c in panels['iopanel']['circles']+panels['iopanel']['rectangular_cutouts']
          if c.get('board_reference')==f['ref']]
    if not cuts:continue
    c=cuts[0];xy=c.get('center_mm') or [(a+b)/2 for a,b in zip(*c['bounds_mm'])]
    world=io.matrix_world@Vector((f['x']*.001,-f['y']*.001,0))
    local=rp.matrix_world.inverted()@world
    irows.append({'ref':f['ref'],'source_panel_x_mm':xy[0],
                  'panel_x_from_saved_world_matrices_mm':local.x*1000,
                  'horizontal_residual_mm':abs(local.x*1000-xy[0])})
report['IO_registration']={'count':len(irows),'maximum_horizontal_residual_mm':max(r['horizontal_residual_mm'] for r in irows),'rows':irows}
check(len(irows)==11 and report['IO_registration']['maximum_horizontal_residual_mm']<.0001,
      'Saved matrices preserve all11 rear horizontal positions')

# Compare saved native collection geometry to fresh source-GLB import by data
# fingerprints and complete native world matrices; this is independent of
# renamed objects and claims stored as custom properties.
def mesh_fingerprints(objects):
    result=collections.Counter()
    for o in objects:
        if o.type!='MESH':continue
        coords=array.array('f',[0])*(len(o.data.vertices)*3)
        o.data.vertices.foreach_get('co',coords)
        loops=array.array('i',[0])*len(o.data.loops)
        o.data.loops.foreach_get('vertex_index',loops)
        starts=array.array('i',[0])*len(o.data.polygons)
        counts=array.array('i',[0])*len(o.data.polygons)
        o.data.polygons.foreach_get('loop_start',starts)
        o.data.polygons.foreach_get('loop_total',counts)
        digest=hashlib.sha256(coords.tobytes()+loops.tobytes()+starts.tobytes()+counts.tobytes()).hexdigest()
        transform=tuple(round(x,9) for row in o.matrix_world for x in row)
        result[(digest,transform)]+=1
    return result
report['boards']={}
for name, inst in [('mainboard',main),('ioboard',io)]:
    source_collection=bpy.data.collections['SOURCE / '+name+' / immutable native KiCad GLB']
    saved=list(source_collection.objects)
    saved_fingerprints=mesh_fingerprints(saved)
    saved_refs={o.get('source_reference') for o in saved if o.get('source_reference')}
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(BASE/'board-meshes'/(name+'.glb')))
    imported=[o for o in bpy.data.objects if o not in before]
    source_fingerprints=mesh_fingerprints(imported)
    meshes=[o for o in saved if o.type=='MESH']
    board_record={'component_reference_count':len(saved_refs),'mesh_objects':len(meshes),
                  'vertices':sum(len(o.data.vertices) for o in meshes),
                  'geometry_and_native_transform_equal_fresh_GLB':saved_fingerprints==source_fingerprints,
                  'source_GLB_sha256':hashlib.sha256((BASE/'board-meshes'/(name+'.glb')).read_bytes()).hexdigest(),
                  'saved_collection':source_collection.name,
                  'saved_mesh_modifiers':sum(len(o.modifiers) for o in meshes),
                  'PCB_mesh_z_bounds_mm':[]}
    # Board meshes have no component-reference parent, unlike component meshes.
    pcbmesh=[o for o in meshes if not (o.parent and o.parent.get('source_reference'))]
    bounds=[]
    for o in pcbmesh:
        vs=[o.matrix_world@Vector(v) for v in o.bound_box]
        bounds.append({'name':o.name,'z_min_mm':min(v.z for v in vs)*1000,
                       'z_max_mm':max(v.z for v in vs)*1000,
                       'vertices':len(o.data.vertices)})
    board_record['PCB_mesh_z_bounds_mm']=bounds
    report['boards'][name]=board_record
    if name=='ioboard':
        laminate_bounds=[b for b in bounds if abs(b['z_min_mm'])<.0001 and abs(b['z_max_mm']-1.510)<.0001]
        check(bool(laminate_bounds),'I/O source laminate top identified at nativeZ1.510mm')
        laminate_top=max(b['z_max_mm'] for b in laminate_bounds)
        top_world=inst.matrix_world@Vector((0,0,laminate_top*.001))
        rear_bottom_world=rp.matrix_world@Vector((0,0,0))
        delta=(top_world.z-rear_bottom_world.z)*1000
        report['IO_laminate_top_datum']={'native_laminate_top_mm':laminate_top,
            'world_laminate_top_mm':top_world.z*1000,
            'rear_panel_bottom_world_mm':rear_bottom_world.z*1000,
            'laminate_top_above_rear_panel_bottom_mm':delta,
            'status':'Documented illustration seating datum; no physical-fit claim'}
        check(abs(delta-6.184)<.0001,'I/O actual laminate top sits6.184mm above rear panel bottom')
    check(saved_fingerprints==source_fingerprints,name+' geometry and native object matrices match fresh GLB import')
    check(len(saved_refs)==(362 if name=='mainboard' else 63),name+' native component count matches ECAD assembly')
    check(board_record['saved_mesh_modifiers']==0,name+' native meshes have no geometry modifiers')
    for o in imported:bpy.data.objects.remove(o,do_unlink=True)

proxycols=[c for c in bpy.data.collections if 'presentation' in c.name.lower()]
report['proxy_collections']=[{'name':c.name,'objects':len(c.objects)} for c in proxycols]
for c in proxycols:
    check(c not in [main.instance_collection,io.instance_collection],
          'Proxy assets separated from native board collection: '+c.name)
report['source_asset_collections_linked_directly_to_scene']=[c.name for c in scene.collection.children if c.name.startswith('SOURCE /')]
check(not report['source_asset_collections_linked_directly_to_scene'],
      'Source collections display only through intended assembly instances')
# Revision2 adds an exact display/reference partition without editing native
# collections. Verify that every derived polygon reconstructs its original
# vertex order and that retained/reference pieces partition complete meshes.
source_io=bpy.data.collections['SOURCE / ioboard / immutable native KiCad GLB']
display_io=io.instance_collection
check(source_io.use_fake_user,
      'Immutable I/O source collection has a persistent fake user after switching display instance')
reference_instance=bpy.data.objects['Historical detached Dimension outline — hidden reference']
reference_collection=reference_instance.instance_collection
partition={}
partition_errors=[]
for role,collection in [('display',display_io),('reference',reference_collection)]:
    for obj in collection.objects:
        original_name=obj.get('original_native_mesh')
        if not original_name:continue
        original=bpy.data.objects[original_name]
        vertex_attribute=obj.data.attributes.get('original_vertex_index')
        polygon_attribute=obj.data.attributes.get('original_polygon_index')
        if not vertex_attribute or not polygon_attribute:
            partition_errors.append(obj.name+' lacks original-index attributes')
            continue
        vertex_indices=[v.value for v in vertex_attribute.data]
        polygon_indices=[v.value for v in polygon_attribute.data]
        original_polygons=partition.setdefault(original_name,{'display':[],'reference':[]})
        original_polygons[role].extend(polygon_indices)
        for vertex,old_index in zip(obj.data.vertices,vertex_indices):
            if (vertex.co-original.data.vertices[old_index].co).length>1e-10:
                partition_errors.append(obj.name+' altered native vertex position')
                break
        for polygon,old_index in zip(obj.data.polygons,polygon_indices):
            reconstructed=[vertex_indices[i] for i in polygon.vertices]
            if reconstructed!=list(original.data.polygons[old_index].vertices):
                partition_errors.append(obj.name+' altered native polygon vertex order')
                break
        if any(abs(a-b)>1e-9 for a,b in zip(
                [v for row in obj.matrix_world for v in row],
                [v for row in original.matrix_world for v in row])):
            partition_errors.append(obj.name+' altered native transform')
for original_name,roles in partition.items():
    original=bpy.data.objects[original_name]
    combined=roles['display']+roles['reference']
    if sorted(combined)!=list(range(len(original.data.polygons))):
        partition_errors.append(original_name+' has overlapping or missing partition faces')
replaced_originals={bpy.data.objects[name] for name in partition}
unchanged_objects=set(source_io.objects)-replaced_originals
actual_unchanged={o for o in display_io.objects if not o.get('original_native_mesh')}
check(not partition_errors and len(partition)==4 and actual_unchanged==unchanged_objects,
      'Revision2 derived I/O display/reference exactly partitions4source meshes; all other native objects shared unchanged')
reference_meshes=[o for o in reference_collection.objects if o.type=='MESH']
reference_vertices=sum(len(o.data.vertices) for o in reference_meshes)
reference_polygons=sum(len(o.data.polygons) for o in reference_meshes)
check(reference_vertices==130 and reference_polygons==92 and reference_instance.hide_render and reference_instance.hide_viewport,
      'Revision2 hidden historical reference preserves130vertices and92polygons')
check(reference_instance.parent==io and all(abs(a-b)<1e-9 for a,b in zip(
      [v for row in reference_instance.matrix_basis for v in row],
      [v for row in __import__('mathutils').Matrix.Identity(4) for v in row])),
      'Historical reference follows I/O instance with identity local pose')
report['revision2_IO_partition']={'display_collection':display_io.name,
    'reference_collection':reference_collection.name,'original_meshes_partitioned':len(partition),
    'partition_errors':partition_errors,'reference_vertices':reference_vertices,
    'reference_polygons':reference_polygons,'reference_hidden_render':reference_instance.hide_render,
    'reference_hidden_viewport':reference_instance.hide_viewport,
    'display_vertices':sum(len(o.data.vertices) for o in display_io.objects if o.type=='MESH'),
    'display_component_references':len({o.get('source_reference') for o in display_io.objects if o.get('source_reference')})}

layout=json.loads((BASE/'source-review/original-photo-label-map.json').read_text())
controls=bpy.data.collections['SOURCE / Front controls — presentation proxies, not ECAD models']
text_objects=[o for o in controls.objects if o.type=='FONT']
text_by_name={o.name:o for o in text_objects}
label_errors=[]
for label in layout['labels']:
    obj=text_by_name.get('Photo-grounded / '+label['id'])
    if not obj or obj.data.body!=label['text']:
        label_errors.append(label['id']+' missing or changed text')
        continue
    x,y=label['anchor_mm']
    if math.dist((obj.location.x*1000,obj.location.y*1000),(x,y))>.0001:
        label_errors.append(label['id']+' changed label anchor')
check(len(text_objects)==100 and not label_errors,
      'Revision2 contains100editable photo-grounded labels with exact mapped content and anchors')
invented={'x0xb0x','SYNTHESIZER / SEQUENCER','WAVEFORM','BANK','MODE'}
check(not any(o.data.body in invented for o in text_objects),
      'Invented title/subtitle and generic WAVEFORM/BANK/MODE labels removed')
check(not any('388576688' in image.filepath or 'ladyada-panel' in image.filepath for image in bpy.data.images),
      'Source photograph is not embedded or used as an image texture')
cap_errors=[]
actual_white=[]
actual_horizontal=[]
for cut in panels['mainpanel']['rectangular_cutouts']:
    ref=cut['board_reference'];cap=bpy.data.objects[ref+' / switch cap proxy'];lo,hi=cut['bounds_mm']
    horizontal=hi[0]-lo[0]>hi[1]-lo[1]
    if horizontal:actual_horizontal.append(ref)
    expected_angle=math.pi/2 if horizontal else 0
    if abs(cap.rotation_euler.z-expected_angle)>1e-6:
        cap_errors.append(ref+' rotation does not match source cutout orientation')
    expected_white=ref in layout['cap_color_map']['white']
    material=cap.active_material.name if cap.active_material else ''
    if material=='Controls / warm white proxy':actual_white.append(ref)
    expected_material='Controls / warm white proxy' if expected_white else 'Controls / dark soft-touch proxy'
    if material!=expected_material:cap_errors.append(ref+' wrong original-photo cap color')
check(not cap_errors and set(actual_horizontal)=={'S5','S6','S14','S15','S16'},
      'Revision2 all23switchcaps use original cutout orientations;5horizontal side buttons')
check(set(actual_white)==set(layout['cap_color_map']['white']) and len(actual_white)==8,
      'Revision2 S17-S24white and all15other switchcaps black')
report['revision2_labels_caps']={'label_count':len(text_objects),'label_errors':label_errors,
    'cap_errors':cap_errors,'white_caps':sorted(actual_white),
    'horizontal_caps':sorted(actual_horizontal),'label_position_uncertainty_mm':1.5}

report['cameras']={}
for frame_number,expected_location,target in [(1,(.36,-.43,.37),(0,.095,.045)),
                                               (80,(.59,-.77,.66),(-.055,.105,.17))]:
    scene.frame_set(frame_number)
    camera=scene.camera
    actual_location=camera.matrix_world.translation
    actual_direction=(camera.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
    expected_direction=(Vector(target)-actual_location).normalized()
    position_error=(actual_location-Vector(expected_location)).length
    direction_dot=actual_direction.dot(expected_direction)
    report['cameras'][str(frame_number)]={'name':camera.name,
        'expected_location_m':expected_location,'actual_location_m':list(actual_location),
        'target_m':target,'position_error_m':position_error,
        'forward_direction':list(actual_direction),'forward_dot_target_direction':direction_dot,
        'lens_mm':camera.data.lens,'clip_start_m':camera.data.clip_start,'clip_end_m':camera.data.clip_end}
    check(camera.name=='Camera / assembled and exploded' and position_error<.000001,
          'Frame'+str(frame_number)+' camera matches intended position')
    check(direction_dot>.999999 and abs(camera.data.lens-57)<.0001,
          'Frame'+str(frame_number)+' camera points at intended target with57mm lens')
scene.frame_set(80)
exploded_main_normal=(main.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
report['frame80']={'main_BCu_world_normal':list(exploded_main_normal),
                   'dot_assembled_BCu_normal':exploded_main_normal.dot(main_normal),
                   'mainboard_translation_m':list(main.matrix_world.translation),
                   'top_panel_translation_m':list(mp.matrix_world.translation),
                   'camera':scene.camera.name if scene.camera else None}
check(exploded_main_normal.dot(main_normal)<-.99999,
      'Frame80 flips mainboard to show component side')
# Separate Grayhill envelopes are a frame120 review aid and must never be
# mistaken for native component assignments or appear in assembled/exploded
# presentation frames.
world_audit=json.loads((BASE/'review-models/grayhill-world-orientation-audit.json').read_text())
model_step=BASE/'review-models/Grayhill_25LB22H_PublishedEnvelope_Illustration.step'
check(world_audit['passed'] and hashlib.sha256(model_step.read_bytes()).hexdigest()==world_audit['canonical_model_sha256'],
      'Grayhill review STEP matches corrected canonical world-orientation audit')
envelopes={ref:bpy.data.objects[ref+' / separate Grayhill review envelope'] for ref in ['S3','S4']}
review_errors=[]
review_matrix_checks=[]
for item in world_audit['transforms']:
    ref=item['reference'];obj=envelopes[ref]
    expected=[list(row) for row in item['component_to_native_world_matrix']]
    for i in range(3):expected[i][3]*=.001
    actual=[list(row) for row in obj.matrix_basis]
    rotation_error=max(abs(actual[i][j]-expected[i][j]) for i in range(3) for j in range(3))
    translation_error=max(abs(actual[i][3]-expected[i][3]) for i in range(3))
    review_matrix_checks.append({'reference':ref,'actual_native_matrix_m':actual,
        'expected_native_matrix_m':expected,'rotation_component_error':rotation_error,
        'translation_error_mm':translation_error*1000,
        'rotation_tolerance':1e-6,'translation_tolerance_mm':.0001,
        'precision_note':'Blender stores float Euler angles;180degrees leaves about1.51e-7 dimensionless sine residue.'})
    if obj.parent!=main or rotation_error>1e-6 or translation_error>1e-7:
        review_errors.append(ref+' review envelope differs from independently audited native placement')
    if obj.instance_collection in [main.instance_collection,source_io] or obj.get('source_reference'):
        review_errors.append(ref+' review envelope overlaps native assignment collection')
check(not review_errors and len(envelopes)==2,
      'Two separate Grayhill review envelopes match native audited matrices and remain outside425native assignments')
review_frames={}
for frame_number in [1,80,120]:
    scene.frame_set(frame_number)
    visibility={ref:{'hide_render':obj.hide_render,'hide_viewport':obj.hide_viewport} for ref,obj in envelopes.items()}
    review_frames[str(frame_number)]={'envelopes':visibility,'exposure':scene.view_settings.exposure}
    expected_hidden=frame_number in [1,80]
    check(all(obj.hide_render==expected_hidden and obj.hide_viewport==expected_hidden for obj in envelopes.values()),
          'Grayhill review envelopes '+('hidden' if expected_hidden else 'visible')+' at frame'+str(frame_number))
scene.frame_set(120)
inspection_camera=scene.camera
normal120=(main.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
forward120=(inspection_camera.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
check(inspection_camera.name=='Camera / control side inspection' and inspection_camera.data.type=='ORTHO'
      and forward120.dot(-normal120)>.999999 and abs(inspection_camera.data.ortho_scale-.29)<1e-6,
      'Frame120 uses orthographic camera directed along mainboard control-side normal')
check(normal120.dot(main_normal)>.999999 and mp.hide_render and mp.hide_viewport
      and bpy.data.objects['Front controls — presentation proxies'].hide_render
      and bpy.data.objects['Front controls — presentation proxies'].hide_viewport,
      'Frame120 mainboard B.Cu remains outward with top panel and front proxies hidden')
check(abs(scene.view_settings.exposure+3.2)<1e-5,
      'Frame120 control-side exposure is-3.2')
report['revision2_control_side_review']={'canonical_STEP_sha256':world_audit['canonical_model_sha256'],
    'world_orientation_audit_sha256':hashlib.sha256((BASE/'review-models/grayhill-world-orientation-audit.json').read_bytes()).hexdigest(),
    'native_matrix_errors':review_errors,'native_matrix_checks':review_matrix_checks,'frames':review_frames,
    'camera_name':inspection_camera.name,'camera_type':inspection_camera.data.type,
    'camera_forward_dot_negative_control_normal':forward120.dot(-normal120),
    'mainboard_BCu_normal':list(normal120),'classification':'Separate conservative published-envelope review aid; no native ECAD assignment or physical-fit certification'}

scene.frame_set(1)
report['checks']=checks
report['passed']=not report['errors']
report['scope']='Saved .blend reopened independently. Read only; no saved changes. Geometry equality covers vertex positions, polygon topology and native mesh object transforms; materials may differ intentionally. Checks do not certify physical enclosure or component fit.'
(BASE/'panels/independent-saved-blender-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'errors':report['errors'],'boards':{n:{k:v for k,v in r.items() if k!='PCB_mesh_z_bounds_mm'} for n,r in report['boards'].items()},'main_registration':{k:v for k,v in report['mainboard_registration'].items() if k!='rows'},'IO_max_residual_mm':report['IO_registration']['maximum_horizontal_residual_mm']},indent=2))

# Cache final native/panel/pose signatures only when the disk file still
# matches the fully audited SHA. Later shell-only saves can be checked
# against this provenance-linked cache without importing source GLBs again.
if report['passed']:
    import sys
    sys.argv.append('--baseline')
    signature_script = BASE / 'panels/signature_saved_blender.py'
    exec(compile(signature_script.read_text(), str(signature_script), 'exec'))
