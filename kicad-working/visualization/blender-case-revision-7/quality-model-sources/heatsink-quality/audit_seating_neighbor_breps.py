"""Refine three native-scene possible contacts using exact source STEP."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
H=Path(__file__).resolve().parent;W=H.parents[2];V=App.Vector
plan=json.loads((W/'validation/models-review-8/combined-model-plan.json').read_text())
poses={r['ref']:r for r in json.loads((H/'independent-io-pose-input.json').read_text())}
heat_path=H/'Aavid_574502B00000G_DrawingDerived_FoldedSpring.step'
heat=Part.read(str(heat_path));heat.translate(V(0,-8.78,3.9))
fingers=[]
for side in [-1,1]:
 sections=[]
 for z,tip in [(0,1.55),(4.9,.85),(9.8,1.55)]:
  pts=[(-3.65,2.28),(-tip,3.31),(-tip-.22,3.94),(-3.85,2.91)]
  if side>0:pts=[(-x,y) for x,y in reversed(pts)]
  vv=[V(x,y,z) for x,y in pts]
  wire=Part.makePolygon(vv+[vv[0]]);sections.append(Part.Wire(wire.Edges))
 fingers.append(Part.makeLoft(sections,True,False))
finger_mask=Part.makeCompound(fingers);finger_mask.translate(V(0,-8.78,3.9))
def bounds(s):
 b=s.BoundBox;return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
rows=[]
for ref in ['C3','C4','C5']:
 a=next(a for a in plan['assignments'] if a['board']=='ioboard' and ref in a['references'])
 assert a['offset_mm']==[0,0,0] and a['rotation_deg']==[0,0,0] and a['scale']==[1,1,1]
 p=poses[ref];assert not p['flipped'];model=Part.read(a['source_model'])
 model.rotate(V(0,0,0),V(0,0,1),p['angle'])
 model.translate(V(p['x']-poses['KK1']['x'],p['y']-poses['KK1']['y'],0))
 common=heat.common(model)
 rows.append({'reference':ref,'source_step':a['source_model'],'source_sha256':hashlib.sha256(Path(a['source_model']).read_bytes()).hexdigest(),
              'source_assignment_sha_matches':hashlib.sha256(Path(a['source_model']).read_bytes()).hexdigest()==a['source_sha256'],
              'native_FCu_position_xy_mm':[p['x'],p['y']],'native_angle_deg':p['angle'],
              'neighbor_bounds_in_KK1_frame_mm':bounds(model),'exact_intersection_volume_mm3':common.Volume,
              'intersection_with_spring_finger_mask_mm3':common.common(finger_mask).Volume,
              'rigid_intersection_outside_finger_mask_mm3':common.cut(finger_mask).Volume,
              'exact_intersection_bounds_mm':bounds(common) if common.Volume>1e-7 else None})
out={'scope':'Independent fresh exact-BRep refinements of three nearby native I/O component surfaces. Actual source native footprint poses/modelzero transforms retained; common board seat cancels in KK1frame.',
     'proposed_KK1_model_offset_mm':[0,-8.78,3.9], 'neighbor_records':rows,
     'passed_clear_of_neighbors':all(r['exact_intersection_volume_mm3']<1e-7 for r in rows),
     'finding':'Reject proposed pose as an installed model placement if any exact nearby component overlap is present. No shrink/trim/footprint move is proposed.',
     'limitations':['Neighbor models are source-qualified package/body illustrations, not measured actual fitted vendor/tolerance geometry. Nevertheless their unchanged modeled bodies materially overlap this pose.',
                    'Only the three possible native mesh contacts were refined; saved-scene full-case and other AABB/surface screen is a separate bounded report.']}
(H/'independent-seating-neighbor-breps.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
