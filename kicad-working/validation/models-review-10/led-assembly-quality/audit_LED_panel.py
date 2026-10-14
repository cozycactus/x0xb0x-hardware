"""Original source holes/current measured seat, candidate LED BRep cross-section."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part
H=Path(__file__).resolve().parent;W=H.parents[2];V=A.Vector
m=json.loads((H/'led-assembly-manifest.json').read_text());part=m['parts'][0];shape=Part.read(part['step']);head=max(shape.Solids,key=lambda s:s.Volume)
measure=json.loads((W/'validation/models-review-10/front-controls-review/front-control-native-measurements.json').read_text());rows=[]
for row in measure['frames'][0]['rows']:
 if not row['reference'].startswith('LED'):continue
 seat=row['native_lens_axis_at_lower_flange_panel_mm'][2]-3
 lower=-seat;upper=lower+1.5748;slab=Part.makeBox(20,20,1.5748,V(-8,-10,lower));section=head.common(slab)
 hole=Part.makeCylinder(row['DXF_hole_radius_mm'],1.5748,V(1.27,0,lower))
 outside=section.cut(hole).Volume;axis_error=row['native_lens_axis_xy_alignment_error_mm'];margin=row['DXF_hole_radius_mm']-2.5-axis_error
 rows.append({'reference':row['reference'],'source_panel_underside_Z_mm':lower,'source_panel_top_Z_mm':upper,'new_lens_tip_above_panel_top_mm':14.696-upper,
 'nominal_coaxial_LED_volume_outside_panel_hole_mm3':outside,'native_lens_axis_error_mm':axis_error,'nominal_radial_margin_less_export_axis_residual_mm':margin,
 'passed':outside<1e-7 and margin>0})
r={'passed':len(rows)==40 and all(r['passed'] for r in rows),'rows':rows,'minimum_nominal_radial_margin_less_export_axis_residual_mm':min(r['nominal_radial_margin_less_export_axis_residual_mm'] for r in rows),
 'new_tip_projection_range_mm':[min(r['new_lens_tip_above_panel_top_mm'] for r in rows),max(r['new_lens_tip_above_panel_top_mm'] for r in rows)],
 'scope':'Original source DXF hole radius2.54mm/current measured stable6 board-panel seat vs candidate generic body. Each slab is exact-BRep checked coaxially; native residual is conservatively subtracted from nominal cylinder clearance.',
 'limits':['Nominal source-qualified geometry and export precision only. Actual LED diameter/height, physical spacer, drill and panel tolerances remain unknown.',
 'The 0.24in source-BOM seat is selected explicitly; original sequencer0.22in alternative is retained. No hardware fitted-fit claim.'],
 'measurement_scene_sha256':measure['scene_sha256'],'STEP_sha256':hashlib.sha256(Path(part['step']).read_bytes()).hexdigest()}
(H/'led-panel-hole-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2));assert r['passed']
