"""Independent read-only saved Blender7 LED/panel/cap attachment verification.

The original displayed cap transforms are captured from actual revision6
depsgraph collection instances, not source-object matrix_world values. Only
final-* reports in this review directory are written. No scene is saved.
"""
from pathlib import Path
import bpy,json,hashlib,struct,math
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent;W=H.parents[2]
old=W/'visualization/blender-case-revision-6/x0xb0x-populated-with-case.blend'
final=W/'visualization/blender-case-revision-7/x0xb0x-populated-with-case.blend'
measurement=H/'front-control-native-measurements.json'
planpath=W/'visualization/blender-case-revision-7/board-meshes/source-model-plan.json'
ledmanifest=W/'validation/models-review-10/led-assembly-quality/led-assembly-manifest.json'
ledaudit=W/'validation/models-review-10/led-assembly-quality/led-assembly-geometry-audit.json'
lens_dimensions=H/'final-source-lens-dimensions.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
input_hashes={str(p):sha(p)for p in [old,final,measurement,planpath,ledmanifest,ledaudit,lens_dimensions]}
baseline=json.loads(measurement.read_text())
base_rows={r['reference']:r for f in baseline['frames']if f['frame']==1 for r in f['rows']}
plan=json.loads(planpath.read_text());lm=json.loads(ledmanifest.read_text());la=json.loads(ledaudit.read_text())
part=lm['parts'][0];step=Path(part['step']);input_hashes[str(step)]=sha(step)
lens_source=json.loads(lens_dimensions.read_text())
cap_names=[f'S{i} / switch cap proxy'for i in range(5,28)]
led_refs=[f'LED{i}'for i in range(1,41)]
board_name='Mainboard — B.Cu outward in assembled view'
panel_name='Top panel — original DXF'
checks=[]
def check(name,passed,**evidence):
    checks.append(dict(check=name,passed=bool(passed),**evidence))
def matrix_error(a,b):return max(abs(v-w)for x,y in zip(a,b)for v,w in zip(x,y))
def serial(m):return [list(r)for r in m]
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def bounds(points):
    return dict(min_mm=[min(v[k]for v in points)for k in range(3)],
                max_mm=[max(v[k]for v in points)for k in range(3)])
def geometry(o):
    d=hashlib.sha256()
    for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
    for p in o.data.polygons:
        d.update(struct.pack('<I',len(p.vertices)))
        d.update(struct.pack('<'+str(len(p.vertices))+'I',*p.vertices))
        d.update(struct.pack('<I',p.material_index))
    return d.hexdigest()
def colors(o):
    rows=[]
    for m in o.data.materials:
        if m is None:rows.append(None);continue
        shader=m.node_tree.nodes.get('Principled BSDF')if m.use_nodes else None
        rows.append(dict(name=m.name,diffuse=list(m.diffuse_color),
                         base_color=list(shader.inputs['Base Color'].default_value)if shader else None))
    return rows
def displayed(names):
    found={n:[]for n in names}
    for ins in bpy.context.evaluated_depsgraph_get().object_instances:
        n=ins.object.original.name
        if n in found:found[n].append(ins.matrix_world.copy())
    return found
def reference(o):
    while o:
        if o.get('source_reference'):return o['source_reference']
        o=o.parent
    return None

# Fresh baseline read: actual old rendered instance transforms and colors.
bpy.ops.wm.open_mainfile(filepath=str(old));s=bpy.context.scene;s.frame_set(1)
bpy.context.view_layer.update();original_display=displayed(cap_names)
original_board=bpy.data.objects[board_name].matrix_world.copy()
original_caps={}
for n in cap_names:
    o=bpy.data.objects[n]
    check('Baseline has exactly one rendered cap: '+n,len(original_display[n])==1)
    original_caps[n]=dict(world=original_display[n][0],geometry=geometry(o),
                          colors=colors(o),vertices=len(o.data.vertices),
                          polygons=len(o.data.polygons))

bpy.ops.wm.open_mainfile(filepath=str(final));s=bpy.context.scene;s.frame_set(1)
bpy.context.view_layer.update();board=bpy.data.objects[board_name]
panel=bpy.data.objects[panel_name]
native={r:[o for o in board.instance_collection.all_objects
           if o.type=='MESH'and reference(o)==r]for r in led_refs}
reference_roots={r:[o for o in board.instance_collection.all_objects
                    if o.get('source_reference')==r]for r in led_refs}
check('Exactly40 PCB-mounted native LED assemblies',len(native)==40 and all(len(reference_roots[r])==1 and len(native[r])==3 for r in led_refs))
check('No standalone LED lens proxy survives',not any(o.name.startswith('LED')and o.name.endswith(' / visible lens proxy')for o in bpy.data.objects))
check('Exactly23 original named caps survive',sum(o.name in cap_names for o in bpy.data.objects)==23)
check('Every cap is parented to the mainboard instance',all(bpy.data.objects[n].parent==board for n in cap_names))
front=bpy.data.objects['Front controls — presentation proxies']
check('Caps removed from old front-panel instance source',all(n not in front.instance_collection.all_objects for n in cap_names))
collections={c.name for n in cap_names for c in bpy.data.objects[n].users_collection}
check('Caps share one ordinary scene display collection',len(collections)==1 and next(iter(collections))in s.collection.children)
check('Cap display collection is not itself instanced',not any(o.instance_collection and o.instance_collection.name in collections for o in bpy.data.objects))
check('Final LED STEP matches frozen source',sha(step)==part['source_sha256']=='2a61af0d1b2a4ef8f4e8ddda40651a13ee141cf824938d16ae99e5583483d987')
check('Linked233 full-width lead/source checks passed',la['passed']and la['checks_passed']==233 and la['geometry_step_sha256']==part['source_sha256'])
led_assignment={r:a for a in plan['assignments']for r in a['references']if a['board']=='mainboard'and r in led_refs}
check('All40 saved-plan LED assignments reference final raised model',set(led_assignment)==set(led_refs)and all(a['source_sha256']==part['source_sha256']for a in led_assignment.values()))

inv=panel.matrix_world.inverted();led_rows=[]
for r in led_refs:
    objs=native[r];root=objs[0]
    while not root.get('source_reference'):root=root.parent
    matrix=inv@board.matrix_world@root.matrix_world
    axis=matrix@Vector((.00127,0,.006096))*1000
    desired=base_rows[r]['DXF_hole_center_mm']
    error=math.dist(axis[:2],desired)
    points=[inv@board.matrix_world@o.matrix_world@v.co*1000 for o in objs for v in o.data.vertices]
    b=bounds(points);projection=b['max_mm'][2]-1.5748
    old_projection=base_rows[r]['proxy_tip_above_panel_top_mm']
    check('Native lens axis matches original DXF hole: '+r,error<.00015,maximum_error_mm=error)
    check('Raised native lens projects1.300mm above panel: '+r,abs(projection-1.3)<.001,projection_mm=projection)
    check('Nominal5mm lens and5.08mm DXF hole retained: '+r,abs(base_rows[r]['DXF_hole_radius_mm']*2-5.08)<1e-8)
    check('One complete native LED assembly with3material features under its PCB reference: '+r,len(objs)==3 and len(reference_roots[r])==1 and root.get('source_board')=='mainboard')
    head_points=[];lead_points=[];optics=[];pin_metallic=[]
    for o in objs:
        source_matrix=root.matrix_world.inverted()@o.matrix_world
        for mi,material in enumerate(o.data.materials):
            shader=material.node_tree.nodes.get('Principled BSDF')if material.use_nodes else None
            if shader is None:continue
            rgb=shader.inputs['Base Color'].default_value[:3]
            is_head=max(abs(a-linear(b))for a,b in zip(rgb,[.72,.82,.85]))<1e-6
            used={v for p in o.data.polygons if p.material_index==mi for v in p.vertices}
            pp=[source_matrix@o.data.vertices[i].co*1000 for i in used]
            if is_head:
                head_points.extend(pp)
                optics.append({key:shader.inputs[key].default_value for key in ['Metallic','Transmission Weight','IOR','Roughness','Emission Strength']})
            else:
                lead_points.extend(pp);pin_metallic.append(shader.inputs['Metallic'].default_value)
    # The source flange occupies Z6.096..7.096 after the rigid lift. Its5.8mm
    # diameter is below the panel; measure the actual4.9mm cylindrical lens of
    # the nominal5mm family above that flange, rather than its complete flange.
    cylinder_points=[p for p in head_points if p.z>7.2]
    body_diameter=2*max(math.hypot(p.x-1.27,p.y)for p in cylinder_points)
    check('Saved lens preserves source CAD4.9mm diameter of nominal5mm family: '+r,abs(body_diameter-lens_source['actual_CAD_lens_cylinder_and_dome_diameter_mm'])<.001,body_diameter_mm=body_diameter)
    lead_sections=[]
    for lead_axis in [0,2.54]:
        pp=[p for p in lead_points if abs(p.x-lead_axis)<.3]
        lb=bounds(pp);width=lb['max_mm'][0]-lb['min_mm'][0];thick=lb['max_mm'][1]-lb['min_mm'][1]
        check('Saved full-width continuous lead envelope: '+r+':'+str(lead_axis),abs(width-.4)<.001 and abs(thick-.4)<.001 and abs(lb['min_mm'][2]+2.5)<.001 and abs(lb['max_mm'][2]-6.096)<.001,source_axis_x_mm=lead_axis,lead_bounds_mm=lb)
        lead_sections.append(dict(source_axis_x_mm=lead_axis,bounds_source_mm=lb,width_mm=width,thickness_mm=thick))
    check('Lens has qualified unlit clear optical appearance: '+r,bool(optics)and all(abs(o['Metallic'])<1e-6 and abs(o['Transmission Weight']-.85)<1e-6 and abs(o['IOR']-1.5)<1e-6 and abs(o['Roughness']-.18)<1e-6 and abs(o['Emission Strength'])<1e-6 for o in optics))
    check('Lead material remains metal: '+r,bool(pin_metallic)and all(v>.9 for v in pin_metallic))
    led_rows.append(dict(reference=r,native_objects=[o.name for o in objs],
                         lens_axis_at_lower_flange_panel_mm=list(axis),
                         DXF_hole_center_mm=desired,axis_alignment_error_mm=error,
                         native_bounds_panel_mm=b,tip_above_panel_top_mm=projection,
                         old_separate_proxy_projection_mm=old_projection,
                         nominal_lens_diameter_mm=5,original_DXF_hole_diameter_mm=5.08,
                         measured_native_lens_body_diameter_mm=body_diameter,
                         native_lead_sections=lead_sections,optical_presentation=optics,
                         lead_metallic=pin_metallic,
                         nominal_family_radial_difference_mm=.04,
                         actual_CAD_lens_radial_difference_mm=(5.08-body_diameter)/2))

frames=[];orientation={'horizontal':[],'vertical':[]}
for f in [1,80,120,160]:
    s.frame_set(f);bpy.context.view_layer.update();shown=displayed(cap_names)
    rows=[]
    for n in cap_names:
        o=bpy.data.objects[n];oldcap=original_caps[n]
        expected=board.matrix_world@original_board.inverted()@oldcap['world']
        local_expected=original_board.inverted()@oldcap['world']
        stored_local=o.matrix_parent_inverse@o.matrix_basis
        if not o.hide_viewport:
            err=matrix_error(o.matrix_world,expected)
            check(f'Cap follows PCB from actual original seat at frame{f}: '+n,err<1e-7,maximum_matrix_error=err)
        else:
            err=matrix_error(stored_local,local_expected)
            check(f'Hidden cap retains constant PCB-relative attachment at frame{f}: '+n,err<1e-7,maximum_local_matrix_error=err)
        check(f'Cap mesh and material colors preserved at frame{f}: '+n,geometry(o)==oldcap['geometry']and colors(o)==oldcap['colors'])
        if f in [120,160]:
            check(f'Cap explicitly hidden in original inspection view{f}: '+n,o.hide_render and o.hide_viewport and not shown[n])
        elif not o.hide_viewport:
            check(f'Cap has one actual displayed transform at frame{f}: '+n,len(shown[n])==1 and matrix_error(shown[n][0],expected)<1e-7)
        else:
            check(f'Hidden cap has no visible instance at frame{f}: '+n,not shown[n])
        row=dict(object=n,world_matrix=serial(o.matrix_world),
                 expected_world_matrix=serial(expected),
                 maximum_matrix_error=err,rendered_instance_count=len(shown[n]),
                 pose_verification_basis='Actual evaluated displayed world matrix'if not o.hide_viewport else'Constant stored PCB-relative matrix; hidden matrix_world cache is not a displayed pose',
                 stored_local_to_PCB_matrix=serial(stored_local),
                 hide_render=o.hide_render,hide_viewport=o.hide_viewport,
                 parent=o.parent.name,mesh_sha256=geometry(o),material_colors=colors(o))
        if f==1:
            pts=[panel.matrix_world.inverted()@o.matrix_world@v.co*1000 for v in o.data.vertices]
            b=bounds(pts);prior=base_rows[n.split(' / ')[0]]['proxy_bounds_panel_mm']
            residual=max(abs(va-vb)for k in ['min_mm','max_mm']for va,vb in zip(b[k],prior[k]))
            check('Original assembled cap bounds and center preserved: '+n,residual<.00015,maximum_bounds_residual_mm=residual)
            width=b['max_mm'][0]-b['min_mm'][0];depth=b['max_mm'][1]-b['min_mm'][1]
            axis='horizontal'if width>depth else'vertical';orientation[axis].append(n)
            row.update(bounds_panel_mm=b,original_bounds_residual_mm=residual,
                       orientation_in_panel=axis,
                       panel_center_mm=[(b['min_mm'][i]+b['max_mm'][i])/2 for i in range(3)])
        rows.append(row)
    frames.append(dict(frame=f,board_world_matrix=serial(board.matrix_world),caps=rows))
check('Original5horizontal18vertical cap orientations preserved',len(orientation['horizontal'])==5 and len(orientation['vertical'])==18)
check('Every inspected scene/source input remains byte unchanged',all(sha(p)==h for p,h in input_hashes.items()))
failures=[c for c in checks if not c['passed']]
report=dict(passed=not failures,read_only=True,checks_count=len(checks),failures=failures,
            scene=str(final),scene_sha256=input_hashes[str(final)],
            scene_bytes=final.stat().st_size,source_hashes=input_hashes,
            native_LED_count=40,standalone_LED_proxy_count=0,cap_count=23,
            LED_measurements=led_rows,frames=frames,cap_orientations=orientation,
            maximum_LED_axis_alignment_error_mm=max(r['axis_alignment_error_mm']for r in led_rows),
            LED_tip_projection_range_mm=[min(r['tip_above_panel_top_mm']for r in led_rows),max(r['tip_above_panel_top_mm']for r in led_rows)],
            old_proxy_projection_range_mm=[min(r['old_separate_proxy_projection_mm']for r in led_rows),max(r['old_separate_proxy_projection_mm']for r in led_rows)],
            checks=checks,physical_fit_qualified=False,
            limitations=[
                'The source filename names a nominal5mm family, but analytical cylinder/dome surfaces are4.9mm diameter; this geometry is retained exactly. Nominal5.0 versus DXF5.08 gives0.04mm radial difference, while the actual4.9mm CAD cylinder gives0.09mm. Neither is a physical tolerance/clearance qualification.',
                'The original BOM specifies STD240B0.24inch/6.096mm. The older sequencer table says0.22inch/5.588mm; the alternative would yield0.792mm nominal lens projection. Actual fitted spacer height is unmeasured.',
                'The reconstructed LED preserves the generic stock head and continuous full0.4x0.4mm lead sections, as linked233source checks confirm. Exact original supplied LED identity and its lead specifications remain unverified.',
                'Spacer height is represented by body seating; the actual spacer outer mold/lead-hole shape is omitted because its exact outline was not recovered.',
                'Button caps preserve original solid presentation geometry, colors and centers; cap socket, retention, actuator travel and physical tolerance are not modeled or certified.',
                'Actual evaluated world transforms were checked at visibleframes1/80 to avoid double application of collection-instance transforms. Original inspectionframes120/160 hidecaps in viewport/render; constant stored PCB-relative attachment and visibility are verified without treating stale hidden matrix_world caches as displayed geometry.',
                'This is geometric/source/animation evidence, not optical or physical hardware certification.'
            ])
(H/'final-front-control-assembly-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k]for k in ['passed','checks_count','failures','scene_sha256','maximum_LED_axis_alignment_error_mm','LED_tip_projection_range_mm','old_proxy_projection_range_mm']},indent=2))
if failures:raise RuntimeError('Saved front assembly audit failed')
