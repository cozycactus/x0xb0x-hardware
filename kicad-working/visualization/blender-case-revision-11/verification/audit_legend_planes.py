"""Actual glyph-to-panel gaps in every saved inspection pose; no scene save."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
source=Path(bpy.data.filepath).resolve();digest=hashlib.sha256(source.read_bytes()).hexdigest()
repo=next(p for p in source.parents if(p/'PROJECT.json').is_file())
baseline=repo/'kicad-working/validation/rear-seating-review/scene-audit/rear-seating-audit.json'
old={p['object']:p for p in json.loads(baseline.read_text())['labels']}
LABELS={r+' label'for r in ['POWER0','HEADPHONE0','MIXIN0','MIXOUT0','CV0','GATE0','USB0','DIN1','DIN2','DIN3','DIN4']}
scene=bpy.context.scene;initial_frame=scene.frame_current;checks=[];frames=[]
def check(name,passed,**details):checks.append(dict(check=name,passed=bool(passed),**details))
for frame in [1,80,120,160]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    panel=bpy.data.objects['Rear panel — original DXF'];rear=bpy.data.objects['Rear faces — presentation proxies'];inv=panel.matrix_world.inverted()
    check('Rear legend instancer shares exact panel pose frame'+str(frame),all(a==b for ra,rb in zip(panel.matrix_world,rear.matrix_world)for a,b in zip(ra,rb)))
    panel_points=[];glyphs={name:[]for name in LABELS};panel_instances=0
    for instance in bpy.context.evaluated_depsgraph_get().object_instances:
        obj=instance.object;name=obj.original.name
        if obj.type=='MESH'and instance.parent and instance.parent.name=='Rear panel — original DXF':
            panel_instances+=1;panel_points.extend([inv@instance.matrix_world@v.co*1000 for v in obj.data.vertices])
        if name in LABELS and obj.type=='FONT':
            mesh=obj.to_mesh();glyphs[name].append([inv@instance.matrix_world@v.co*1000 for v in mesh.vertices]);obj.to_mesh_clear()
    check('Exactly one actual panel mesh displayed frame'+str(frame),panel_instances==1)
    exterior=max(p.z for p in panel_points);record=dict(frame=frame,panel_exterior_normal_mm=exterior,labels=[])
    for name in sorted(LABELS):
        check('One evaluated FONT assembly for '+name+' frame'+str(frame),len(glyphs[name])==1)
        points=glyphs[name][0];bounds=[min(p[i]for p in points)for i in range(3)]+[max(p[i]for p in points)for i in range(3)]
        low,high=bounds[2]-exterior,bounds[5]-exterior
        check('Actual glyph back sits .01mm outside panel: '+name+' frame'+str(frame),abs(low-.01)<.0001,
              minimum_gap_mm=low,maximum_gap_mm=high,numeric_tolerance_mm=.0001)
        baseline_bounds=old[name]['glyph_panel_local_bounds_mm'];xy_error=max(abs(bounds[i]-baseline_bounds[i])for i in [0,1,3,4])
        check('Actual in-plane glyph extents retained: '+name+' frame'+str(frame),xy_error<.0001,max_in_plane_error_mm=xy_error)
        check('Original .012mm full glyph extrusion retained: '+name+' frame'+str(frame),abs(high-low-.012)<.0001,full_thickness_mm=high-low)
        record['labels'].append(dict(object=name,glyph_bounds_panel_local_mm=bounds,minimum_gap_mm=low,maximum_gap_mm=high,max_in_plane_error_mm=xy_error))
    frames.append(record)
scene.frame_set(initial_frame);bpy.context.view_layer.update()
check('Read-only glyph inspection leaves saved scene bytes unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==digest)
failures=[c for c in checks if not c['passed']]
out=dict(passed=not failures,check_count=len(checks),scene_sha256=digest,unique_rear_legend_count=11,frame_count=4,
         evaluated_glyph_pose_count=44,frames=frames,failures=failures,checks=checks,read_only=True,
         physical_fit_qualified=False,method='Actual evaluated FONT glyph vertices and panel mesh vertices transformed into each frame\'s evaluated panel coordinates. FONT/MESH conversion representations are not counted as separate labels.')
(HERE/'rear-legend-plane-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items()if k not in {'frames','checks'}},indent=2));assert not failures,'Actual glyph/panel plane audit failed'
