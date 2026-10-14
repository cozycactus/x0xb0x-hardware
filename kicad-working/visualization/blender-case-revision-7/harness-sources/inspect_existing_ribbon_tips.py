"""Read-only ribbon termination endpoint export from stable revision4."""
from pathlib import Path
import collections,hashlib,json,sys
import bpy
from mathutils import Vector
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
sys.path.insert(0,str(WORK.parent/'kicad-import/validation'))
from verify_native_projects import children,one,parse_sexpr,property_value
path=Path(bpy.data.filepath);digest=hashlib.sha256(path.read_bytes()).hexdigest()
assert digest=='2a124a12efc0e32250c9363ecbbd35c18d8f4ff1c5d9f7e46eafb3632b097a67'
manifest_path=WORK/'validation/models-review-6/misc-body-illustrations/misc-body-manifest.json'
manifest=json.loads(manifest_path.read_text())
groups={}
for part in manifest['parts']:
    for ref in part['references']:
        if ref in ['J3','J4','J5','J6','J7']:groups[(part['board'],ref)]=part
rows=[];geometry=[]
def ref_of(obj):
    while obj:
        if obj.get('source_reference'):return obj['source_reference']
        obj=obj.parent
    return None
for board,inst_name in [('mainboard','Mainboard — B.Cu outward in assembled view'),('ioboard','I/O board — rear mounting approximation')]:
    tree=parse_sexpr((WORK/board/(board+'.kicad_pcb')).read_text())
    fps={property_value(f,'Reference','reference'):f for f in children(tree,'footprint')}
    inst=bpy.data.objects[inst_name];objects=list(inst.instance_collection.objects)
    roots={o.get('source_reference'):o for o in objects if o.get('source_reference')}
    for ref in ['J3','J4','J5','J6','J7']:
        part=groups[board,ref];root=roots[ref];fp=fps[ref]
        assert one(fp,'layer')[1]=='F.Cu'
        pads=sorted(children(fp,'pad'),key=lambda p:int(p[1]))
        count=part['dimensions']['actual_conductor_count'];assert len(pads)==count
        meshes=[o for o in objects if o.type=='MESH' and ref_of(o)==ref]
        segments=[]
        for obj in meshes:
            points=[root.matrix_world.inverted()@obj.matrix_world@v.co for v in obj.data.vertices]
            bounds=[min(p[k] for p in points)*1000 for k in range(3)]+[max(p[k] for p in points)*1000 for k in range(3)]
            segments.append({'name':obj.name,'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons),'canonical_bounds_mm':bounds})
        geometry.append({'board':board,'reference':ref,'footprint':fp[1],
            'canonical_model_STEP':part['step_path'],'canonical_model_sha256':part['source_sha256'],
            'canonical_wire_axes_x_mm':[float(one(p,'at')[1]) for p in pads],
            'source_dimensions':part['dimensions'],'native_meshes':segments,
            'native_component_matrix':[list(r) for r in root.matrix_world]})
        for frame in [1,80,120]:
            bpy.context.scene.frame_set(frame)
            pose=inst.matrix_world@root.matrix_world
            normal=(pose.to_3x3()@Vector((0,0,1))).normalized()
            pitch=(pose.to_3x3()@Vector((1,0,0))).normalized()
            tips=[]
            for pad in pads:
                xy=[float(one(pad,'at')[1]),-float(one(pad,'at')[2])]
                tip=pose@Vector((xy[0]*.001,xy[1]*.001,.0075))
                start=pose@Vector((xy[0]*.001,xy[1]*.001,.00745))
                tips.append({'pin':pad[1],'canonical_axis_xy_mm':xy,
                    'canonical_insulation_tip_mm':xy+[7.5],'world_tip_mm':list(tip*1000),
                    'suggested_0p05mm_overlap_start_world_mm':list(start*1000)})
            rows.append({'board':board,'reference':ref,'frame':frame,
                'world_outward_tangent':list(normal),'world_row_axis_increasing_canonical_x':list(pitch),
                'tip_count':count,'tips':tips,'component_to_assembled_world_matrix':[list(r) for r in pose]})
assert sum(r['tip_count'] for r in rows if r['frame']==1)==48
distances=[]
for ref in ['J3','J4','J5','J6','J7']:
    a=next(r for r in rows if r['frame']==1 and r['board']=='mainboard' and r['reference']==ref)
    b=next(r for r in rows if r['frame']==1 and r['board']=='ioboard' and r['reference']==ref)
    for ta,tb in zip(a['tips'],b['tips']):
        distance=(Vector(ta['world_tip_mm'])-Vector(tb['world_tip_mm'])).length
        distances.append({'reference':ref,'pin':ta['pin'],'same_pin_tip_chord_mm':distance,
            'chord_plus_two_7p5mm_above_seat_stub_lengths_mm':distance+15,
            'original_stock_length_mm':152.4,
            'status':'Geometric lower bound using current inferred stub/seating poses; net map and actual stock trimming are separate evidence.'})
assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
report={'saved_scene':str(path),'saved_scene_sha256':digest,'saved_scene_unchanged':True,
    'source_misc_manifest':str(manifest_path),'source_misc_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    'native_reference_count':491,'inspected_native_ribbon_references':10,'span_conductors':24,'board_end_tips':48,
    'canonical_geometry':{'pitch_mm':2.54,'insulation_diameter_mm':1,'insulation_z_mm':[1.2,7.5],
        'web_thickness_mm':.35,'bare_conductor_diameter_mm':.4,'bare_conductor_z_mm':[-1.8,1.2],
        'total_3way_width_mm':6.08,'total_12way_width_mm':28.94,'stock_length_mm':152.4,
        'top_tip':'Flat insulation face atZ7.5; conductor model ends atZ1.2 and is not exposed at the upper tip.'},
    'geometry_records':geometry,'endpoints':rows,'assembled_same_pin_chords':distances,
    'limitations':['Dimensions other than conductor count/pad pitch are original presentation assumptions. No manufacturer bend-radius or fitted cable length qualification.',
        'Pin numbers here identify geometric tips. Electrical mapping is independently verified by the net/source review.']}
(HERE/'existing-ribbon-termination-endpoints.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'saved_scene_unchanged':True,'native_refs':10,'conductors':24,'tips':48,
    'J3_chord_mm':distances[0]['same_pin_tip_chord_mm'],'J3_chord_plus_existing_above_seat_stubs_mm':distances[0]['chord_plus_two_7p5mm_above_seat_stub_lengths_mm']}))
