"""Read-only rear presentation inventory from evaluated saved-scene geometry."""
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
SOURCE = Path(bpy.data.filepath)
original_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
refs = ['POWER0','HEADPHONE0','GATE0','CV0','USB0','MIXOUT0','DIN1','DIN2','DIN3','MIXIN0','DIN4']
relevant = {f'IOBOARD/{ref}/mesh' for ref in refs}
relevant |= {ref+' label' for ref in refs}
relevant |= {ref+suffix for ref in ('HEADPHONE0','MIXIN0','MIXOUT0')
             for suffix in (' / black PA6 nut proxy',' / black ABS washer proxy')}
relevant.add('iopanel — exact DXF profile')


def bounds(points):
    return [min(v[i] for v in points)*1000 for i in range(3)] + [
        max(v[i] for v in points)*1000 for i in range(3)]


instances = []
geometry_points = {}
for inst in dg.object_instances:
    obj = inst.object
    if obj.original.name not in relevant:
        continue
    record = dict(name=obj.name, original_name=obj.original.name,
        evaluated_type=obj.type, original_type=obj.original.type,
        is_instance=inst.is_instance,
        parent=inst.parent.name if inst.parent else None,
        instance_object=inst.instance_object.name if inst.instance_object else None,
        persistent_id=list(inst.persistent_id),
        show_self=inst.show_self, show_particles=inst.show_particles,
        matrix_world=[list(row) for row in inst.matrix_world])
    if obj.type in {'MESH','FONT'}:
        mesh=obj.to_mesh()
        points=[inst.matrix_world @ vertex.co for vertex in mesh.vertices]
        geometry_points.setdefault(obj.original.name, points)
        record.update(vertex_count=len(mesh.vertices),polygon_count=len(mesh.polygons),
            geometry_world_bounds_mm=bounds(points),
            material_names=[m.name if m else None for m in mesh.materials])
        obj.to_mesh_clear()
    if obj.original.type=='FONT':
        data=obj.original.data
        record['font']=dict(body=data.body,size_mm=data.size*1000,
                            extrude_mm=data.extrude*1000,offset_mm=data.offset*1000)
    instances.append(record)

collection=bpy.data.collections['SOURCE / Rear connector faces — presentation proxies, not ECAD models']
source_objects=[dict(name=obj.name,type=obj.type,collections=[c.name for c in obj.users_collection])
                for obj in collection.objects]
panel=[row for row in instances if row['original_name']=='iopanel — exact DXF profile'][0]
panel_inner=panel['geometry_world_bounds_mm'][1]
panel_outer=panel['geometry_world_bounds_mm'][4]
panel_matrix=next(inst.matrix_world.copy() for inst in dg.object_instances
                  if inst.object.original.name=='iopanel — exact DXF profile')
panel_normal=(panel_matrix.to_3x3() @ Vector((0,0,1))).normalized()
panel_front_projection=max(point.dot(panel_normal) for point in geometry_points['iopanel — exact DXF profile'])
panel_back_projection=min(point.dot(panel_normal) for point in geometry_points['iopanel — exact DXF profile'])
labels=[]
for ref in refs:
    rows=[row for row in instances if row['original_name']==ref+' label']
    labels.append(dict(reference=ref,dependency_graph_record_count=len(rows),
        records_differ=any(row['matrix_world']!=rows[0]['matrix_world'] for row in rows[1:]),
        font=rows[0]['font'],world_bounds_mm=rows[0]['geometry_world_bounds_mm'],
        normal_gap_above_panel_outer_mm=rows[0]['geometry_world_bounds_mm'][1]-panel_outer,
        actual_panel_normal_glyph_back_gap_mm=(min(point.dot(panel_normal) for point in geometry_points[ref+' label'])-panel_front_projection)*1000,
        actual_panel_normal_glyph_front_gap_mm=(max(point.dot(panel_normal) for point in geometry_points[ref+' label'])-panel_front_projection)*1000,
        original_scene_object_count=sum(obj.name==ref+' label' for obj in bpy.data.objects),
        paired_evaluated_types=sorted(row['evaluated_type'] for row in rows)))

hardware=[]
for ref in ('HEADPHONE0','MIXIN0','MIXOUT0'):
    nut=next(row for row in instances if row['original_name']==ref+' / black PA6 nut proxy')
    washer=next(row for row in instances if row['original_name']==ref+' / black ABS washer proxy')
    hardware.append(dict(reference=ref,nut_bounds_mm=nut['geometry_world_bounds_mm'],
        washer_bounds_mm=washer['geometry_world_bounds_mm'],
        washer_rear_above_panel_outer_mm=washer['geometry_world_bounds_mm'][1]-panel_outer,
        nut_rear_above_washer_front_mm=nut['geometry_world_bounds_mm'][1]-washer['geometry_world_bounds_mm'][4]))

ink=bpy.data.materials['Presentation label ink']
ink_record=dict(name=ink.name,diffuse_color=list(ink.diffuse_color),metallic=ink.metallic,
                roughness=ink.roughness,use_nodes=ink.use_nodes)
if ink.node_tree:
    bsdf=next((node for node in ink.node_tree.nodes if node.type=='BSDF_PRINCIPLED'),None)
    if bsdf:
        ink_record['principled_inputs']={name:list(bsdf.inputs[name].default_value) if name=='Base Color' else bsdf.inputs[name].default_value
                                        for name in ('Base Color','Metallic','Roughness','Alpha','Emission Strength')}

result=dict(inspection_complete=True,scene=str(SOURCE),scene_sha256=original_hash,
    method='Fresh saved Blender10, frame1 evaluated dependency-graph instances and all evaluated mesh/font vertices, no scene mutation/save.',
    native_port_reference_count=len(refs),rear_source_mesh_count=sum(row['type']=='MESH' for row in source_objects),
    rear_source_font_count=sum(row['type']=='FONT' for row in source_objects),
    rear_source_objects=source_objects,panel_inner_y_mm=panel_inner,panel_outer_y_mm=panel_outer,
    panel_outward_normal=list(panel_normal),
    panel_normal_thickness_mm=(panel_front_projection-panel_back_projection)*1000,
    label_material=ink_record,
    labels=labels,hardware=hardware,instances=instances,
    visual_label_seating_defect_found=all(row['actual_panel_normal_glyph_back_gap_mm']>1 for row in labels),
    correction_applied=False,
    scene_metadata={key:scene.get(key) for key in ('IO_axis_datum_assumption_mm','rear_panel_datum_uncertainty','BOM_seating_status')},
    source_bytes_unchanged=hashlib.sha256(SOURCE.read_bytes()).hexdigest()==original_hash)
assert result['source_bytes_unchanged']
(HERE/'rear-presentation-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:value for key,value in result.items() if key not in {'instances','rear_source_objects'}},indent=2))
