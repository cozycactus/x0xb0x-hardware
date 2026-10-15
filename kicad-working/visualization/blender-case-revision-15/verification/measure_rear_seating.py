"""Read-only seating measurements from evaluated saved Blender geometry.

Panel cutout positions are fitted to actual mesh vertices; retained DXF data
only identifies which boundary belongs to each connector. Mesh Boolean
intersections screen nominal illustrated material, without qualifying fit.
"""
import bpy,bmesh,json,hashlib,math
from pathlib import Path
from mathutils import Vector
import numpy as np

# Copy of validation/rear-seating-review/scene-audit/audit_rear_seating.py
# with only its repository path and output file changed, so revisions 14 and
# 15 are measured by identical code without overwriting the revision-10 report.
# Run: Blender --background <scene> --python-exit-code 1 --python this.py -- <output.json>
import sys
HERE=Path(__file__).resolve().parent
source=Path(bpy.data.filepath).resolve()
repo=HERE.parents[3]
OUTPUT=HERE/sys.argv[sys.argv.index('--')+1]
panel_source=repo/'kicad-working/visualization/blender-case-revision-7/panels/original-panels.json'
dxf=json.loads(panel_source.read_text())['iopanel']
digest=hashlib.sha256(source.read_bytes()).hexdigest()
scene=bpy.context.scene;initial_frame=scene.frame_current
scene.frame_set(1);bpy.context.view_layer.update()
panel_matrix=bpy.data.objects['Rear panel — original DXF'].matrix_world.copy()
inv_panel=panel_matrix.inverted()
refs=['POWER0','HEADPHONE0','MIXIN0','MIXOUT0','CV0','GATE0','USB0','DIN1','DIN2','DIN3','DIN4']
spec={r:dict(axis_z=8.,face_y=-8.5,shoulder_y=0.,mating_radius=3.175,nose_radius=4.7625)for r in ['HEADPHONE0','MIXIN0','MIXOUT0']}
spec.update({r:dict(axis_z=5.5,face_y=-3.,shoulder_y=0.,mating_radius=1.8,nose_radius=3.)for r in ['CV0','GATE0']})
spec.update({r:dict(axis_z=10.,face_y=0.,shoulder_y=0.,mating_radius=7.1)for r in ['DIN1','DIN2','DIN3','DIN4']})
spec['POWER0']=dict(axis_z=6.5,face_y=0.,mating_radius=3.25)
spec['USB0']=dict(axis_z=5.31,face_y=0.,axis_is_illustrative_envelope_center=True)
items={};labels={}
for instance in bpy.context.evaluated_depsgraph_get().object_instances:
    obj=instance.object;name=obj.original.name
    parent=instance.parent.name if instance.parent else ''
    selected=(name in ['IOBOARD/'+r+'/mesh'for r in refs]
              or parent in ['Rear panel — original DXF','Case / bottom','Case / upper']
              or name.endswith((' / black ABS washer proxy',' / black PA6 nut proxy')))
    if obj.type=='FONT' and parent=='Rear faces — presentation proxies':
        mesh=obj.to_mesh();pts=[inv_panel@instance.matrix_world@v.co*1000 for v in mesh.vertices];obj.to_mesh_clear()
        labels[name]=dict(object=name,body=obj.original.data.body,
                          glyph_panel_local_bounds_mm=[min(p[i]for p in pts)for i in range(3)]+[max(p[i]for p in pts)for i in range(3)],
                          extrusion_mm=obj.original.data.extrude*1000)
    if not selected or obj.type!='MESH':continue
    items[name]=dict(name=name,parent=parent,matrix=instance.matrix_world.copy(),
                     vertices=[v.co.copy()for v in obj.data.vertices],
                     faces=[list(p.vertices)for p in obj.data.polygons])
panel_item=next(v for v in items.values()if v['parent']=='Rear panel — original DXF')
panel_vertices=[inv_panel@panel_item['matrix']@v*1000 for v in panel_item['vertices']]
inner=min(p.z for p in panel_vertices);outer=max(p.z for p in panel_vertices)
outer_vertices=[p for p in panel_vertices if abs(p.z-outer)<.001]

def fit_circle(points):
    a=np.array([[2*p.x,2*p.y,1]for p in points]);b=np.array([p.x*p.x+p.y*p.y for p in points])
    x,y,c=np.linalg.lstsq(a,b,rcond=None)[0];radius=math.sqrt(c+x*x+y*y)
    return [float(x),float(y)],float(radius),max(abs(math.hypot(p.x-x,p.y-y)-radius)for p in points)

def edge_distance(point,a,b):
    vx,vy=b[0]-a[0],b[1]-a[1];t=max(0.,min(1.,((point[0]-a[0])*vx+(point[1]-a[1])*vy)/(vx*vx+vy*vy)))
    return math.hypot(point[0]-a[0]-t*vx,point[1]-a[1]-t*vy)

def mesh_circle_center(item,axis_dimension=2):
    points=[inv_panel@item['matrix']@v*1000 for v in item['vertices']]
    lo=[min(p[i]for p in points)for i in range(3)];hi=[max(p[i]for p in points)for i in range(3)]
    return [(lo[0]+hi[0])/2,(lo[1]+hi[1])/2],lo+hi

def make_copy(item):
    mesh=bpy.data.meshes.new('__seating_audit_mesh')
    mesh.from_pydata(item['vertices'],[],item['faces']);mesh.update()
    obj=bpy.data.objects.new('__seating_audit_object',mesh);scene.collection.objects.link(obj)
    obj.matrix_world=item['matrix'];return obj

def intersection(a_item,b_item):
    a=make_copy(a_item);b=make_copy(b_item)
    modifier=a.modifiers.new('__read_only_intersection','BOOLEAN');modifier.operation='INTERSECT';modifier.solver='EXACT';modifier.object=b
    bpy.context.view_layer.update();evaluated=a.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    bm=bmesh.new();bm.from_mesh(mesh);volume=abs(bm.calc_volume(signed=True)*a.matrix_world.to_3x3().determinant())*1e9
    bounds=None
    if mesh.vertices:
        points=[inv_panel@a.matrix_world@v.co*1000 for v in mesh.vertices]
        bounds=[min(p[i]for p in points)for i in range(3)]+[max(p[i]for p in points)for i in range(3)]
    result=dict(volume_mm3=volume,vertex_count=len(mesh.vertices),face_count=len(mesh.polygons),
                nonmanifold_edge_count=sum(not e.is_manifold for e in bm.edges),bounds_panel_local_mm=bounds,
                substantial_nominal_overlap=volume>.01,numeric_contact_threshold_mm3=.01)
    bm.free();evaluated.to_mesh_clear()
    for obj in [a,b]:
        data=obj.data;bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(data)
    return result

report=dict(scene=source.name,scene_sha256=digest,blender_version=bpy.app.version_string,
            panel=dict(mesh=panel_item['name'],inner_plane_mm=inner,outer_plane_mm=outer,
                       measured_thickness_mm=outer-inner,source_nominal_thickness_mm=dxf['thickness_mm'],
                       local_frame='X right in original rear drawing, Y up, normal Z outward; actual slab is negative normal Z to zero'),
            ports=[],audio_hardware=[],labels=[],intersections=[],physical_fit_qualified=False,
            read_only=True,
            method='Frame1 evaluated collection-instance matrices; saved mesh vertices, fitted cutout boundaries, actual surface planes and exact-solver triangle-mesh Boolean screening. No source scene is saved.')
for ref in refs:
    item=items['IOBOARD/'+ref+'/mesh'];sp=spec[ref];matrix=inv_panel@item['matrix']
    face=matrix@Vector((0,sp['face_y']/1000,sp['axis_z']/1000))*1000
    outward=(matrix.to_3x3()@Vector((0,1 if ref=='POWER0'else-1,0))).normalized()
    intersection_xy=[face.x+outward.x/outward.z*(outer-face.z),face.y+outward.y/outward.z*(outer-face.z)]
    row=dict(reference=ref,native_axis_at_panel_exterior_mm=intersection_xy,outward_axis_in_panel_frame=list(outward),
             native_mating_face_normal_mm=face.z,mating_face_projection_beyond_panel_exterior_mm=face.z-outer,
             axis_height_basis=('illustrative outer-envelope center, not a printed PCB-to-port datum'if sp.get('axis_is_illustrative_envelope_center')else'saved canonical model axis from existing drawing-derived illustration'))
    row['confidence']=dict(saved_scene_geometry='high: actual evaluated saved mesh and source boundary fits',
        historical_installed_fit='unqualified',
        key_uncertainty=('Generic USB envelope center, omitted locators and body seat, historical part identity'if ref=='USB0'else
                         'Historical body-seat/terminal identity and canonical-to-footprint registration; omitted terminals/locators'))
    cut=next(c for c in dxf['circles']+dxf['rectangular_cutouts']if c.get('board_reference')==ref)
    if 'radius_mm'in cut:
        guess=cut['center_mm'];radius=cut['radius_mm']
        boundary=[p for p in outer_vertices if abs(math.hypot(p.x-guess[0],p.y-guess[1])-radius)<.005]
        center,fitted_radius,residual=fit_circle(boundary)
        polygon=sorted(set((round(p.x,7),round(p.y,7))for p in boundary),key=lambda p:math.atan2(p[1]-center[1],p[0]-center[0]))
        wall_distance=min(edge_distance(intersection_xy,a,b)for a,b in zip(polygon,polygon[1:]+polygon[:1]))
        row['actual_cutout']=dict(shape='circular',fitted_center_mm=center,fitted_radius_mm=fitted_radius,
                                  radial_fit_max_error_mm=residual,boundary_sample_count=len(boundary),
                                  original_DXF_center_mm=guess,axis_minus_hole_center_mm=[intersection_xy[i]-center[i]for i in range(2)],
                                  axis_eccentricity_mm=math.dist(intersection_xy,center),minimum_axis_to_saved_polygon_wall_mm=wall_distance)
        row['mating_aperture_radial_margin_to_panel_mm']=wall_distance-sp['mating_radius']
        if 'nose_radius'in sp:row['native_bushing_outer_envelope_radial_margin_to_panel_mm']=wall_distance-sp['nose_radius']
    else:
        lo,hi=cut['bounds_mm'];boundary=[p for p in outer_vertices if lo[0]-.005<=p.x<=hi[0]+.005 and lo[1]-.005<=p.y<=hi[1]+.005 and min(abs(p.x-lo[0]),abs(p.x-hi[0]),abs(p.y-lo[1]),abs(p.y-hi[1]))<.005]
        actual_lo=[min(p[i]for p in boundary)for i in range(2)];actual_hi=[max(p[i]for p in boundary)for i in range(2)]
        center=[(a+b)/2 for a,b in zip(actual_lo,actual_hi)]
        body=[matrix@v*1000 for v in item['vertices']];bodylo=[min(p[i]for p in body)for i in range(2)];bodyhi=[max(p[i]for p in body)for i in range(2)]
        row['actual_cutout']=dict(shape='rectangular',bounds_mm=[actual_lo,actual_hi],boundary_sample_count=len(boundary),axis_minus_rectangle_center_mm=[intersection_xy[i]-center[i]for i in range(2)])
        row['body_envelope_clearance_to_rectangle_mm']=dict(left=bodylo[0]-actual_lo[0],right=actual_hi[0]-bodyhi[0],bottom=bodylo[1]-actual_lo[1],top=actual_hi[1]-bodyhi[1])
    if 'shoulder_y'in sp:
        shoulder=matrix@Vector((0,sp['shoulder_y']/1000,sp['axis_z']/1000))*1000
        row['housing_shoulder_or_flange_front_normal_mm']=shoulder.z
        row['shoulder_minus_panel_inner_plane_mm']=shoulder.z-inner
        row['shoulder_status']='penetrates panel from inside'if shoulder.z-inner>.001 else'coincident within saved-mesh numerical precision'if abs(shoulder.z-inner)<.001 else'gap behind inner plane'
    panel_overlap=intersection(item,panel_item);row['actual_panel_material_intersection']=panel_overlap
    for case in [v for v in items.values()if v['parent']in ['Case / bottom','Case / upper']]:
        overlap=intersection(item,case);report['intersections'].append(dict(first=ref,second=case['name'],**overlap))
    report['ports'].append(row)
    print(ref,'panel material overlap mm3',panel_overlap['volume_mm3'],flush=True)

for ref in ['HEADPHONE0','MIXIN0','MIXOUT0']:
    port=next(p for p in report['ports']if p['reference']==ref);axis=port['native_axis_at_panel_exterior_mm']
    stack={}
    for suffix in ['black ABS washer proxy','black PA6 nut proxy']:
        item=items[ref+' / '+suffix];center,bounds=mesh_circle_center(item)
        stack[suffix]=dict(outer_center_panel_xy_mm=center,bounds_panel_local_mm=bounds,
                           outside_center_minus_native_axis_mm=[center[i]-axis[i]for i in range(2)],
                           outer_center_eccentricity_mm=math.dist(center,axis),
                           actual_panel_intersection=intersection(item,panel_item))
    washer,nut=stack['black ABS washer proxy'],stack['black PA6 nut proxy']
    report['audio_hardware'].append(dict(reference=ref,parts=stack,
       washer_rear_minus_panel_exterior_mm=washer['bounds_panel_local_mm'][2]-outer,
       nut_rear_minus_washer_front_mm=nut['bounds_panel_local_mm'][2]-washer['bounds_panel_local_mm'][5],
       native_nose_tip_beyond_nut_front_mm=port['native_mating_face_normal_mm']-nut['bounds_panel_local_mm'][5],
       conditional_tip_projection_if_shoulder_seated_at_panel_inner_mm=8.5-(outer-inner)-1.2-5.,
       mixed_source_threads_unqualified=True))
for label in labels.values():
    bounds=label['glyph_panel_local_bounds_mm'];label['glyph_minimum_gap_above_panel_exterior_mm']=bounds[2]-outer;label['glyph_maximum_gap_above_panel_exterior_mm']=bounds[5]-outer;report['labels'].append(label)
scene.frame_set(initial_frame);bpy.context.view_layer.update()
report['saved_scene_bytes_unchanged']=hashlib.sha256(source.read_bytes()).hexdigest()==digest
report['source_panel_json_sha256']=hashlib.sha256(panel_source.read_bytes()).hexdigest()
report['summary']=dict(port_count=len(report['ports']),label_count=len(labels),
    native_ports_with_substantial_panel_material_overlap=[p['reference']for p in report['ports']if p['actual_panel_material_intersection']['substantial_nominal_overlap']],
    native_port_case_intersections=[x for x in report['intersections']if x['substantial_nominal_overlap']],
    floating_rear_legends=[p['object']for p in report['labels']if p['glyph_minimum_gap_above_panel_exterior_mm']>.1])
OUTPUT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['summary'],indent=2))
assert report['saved_scene_bytes_unchanged']
