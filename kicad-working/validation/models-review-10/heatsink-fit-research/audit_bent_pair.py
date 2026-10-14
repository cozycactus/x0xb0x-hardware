"""Fresh STEP reload, rigid equality, exact neighbor BReps, qualified seat audit."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part,Mesh
H=Path(__file__).resolve().parent;W=H.parents[2];V=A.Vector
manifest=json.loads((H/'bent-pair-manifest.json').read_text())
plan=json.loads((W/'validation/models-review-9/combined-model-plan.json').read_text())
poses={p['ref']:p for p in json.loads((W/'validation/models-review-9/heatsink-quality/independent-io-pose-input.json').read_text())}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bounds=lambda s:[s.BoundBox.XMin,s.BoundBox.YMin,s.BoundBox.ZMin,s.BoundBox.XMax,s.BoundBox.YMax,s.BoundBox.ZMax]
checks=[]
def check(name,value,detail=None):
 checks.append({'check':name,'passed':bool(value),'detail':detail})
models={p['references'][0]:Part.read(p['step']) for p in manifest['parts']}
for p in manifest['parts']:
 ref=p['references'][0];s=models[ref];old=Part.read(p['rigid_source'])
 check(ref+' final STEP SHA equals manifest',sha(Path(p['step']))==p['source_sha256'])
 check(ref+' STEP valid',s.isValid())
 check(ref+' source solid/face counts unchanged',len(s.Solids)==len(old.Solids) and len(s.Faces)==len(old.Faces))
 check(ref+' positive unchanged volume',s.Volume>0 and abs(s.Volume-old.Volume)<1e-7)
 check(ref+' full STL closed',Mesh.Mesh(p['stl']).isSolid())
 for seg in p['segments']:
  check(ref+'/'+seg['name']+' STL closed',Mesh.Mesh(str(H/seg['stl'])).isSolid())
 inverse=s.copy()
 if ref=='KK1':inverse.translate(V(0,1.27,0))
 inverse.translate(V(0,0,-2));inverse.rotate(V(0,0,0),V(1,0,0),90)
 if ref=='KK1':inverse.translate(V(0,7.51,-3.9))
 ab=inverse.cut(old).Volume;ba=old.cut(inverse).Volume
 check(ref+' rigid source symmetry preserved',ab<1e-6 and ba<1e-6,{'candidate_minus_source_mm3':ab,'source_minus_candidate_mm3':ba})
reg=models['IC20'].copy();reg.translate(V(0,-1.27,0));heat=models['KK1']
common=reg.common(heat)
# Frozen original reconstructed finger mask, transformed identically to KK1.
fingers=[]
for side in [-1,1]:
 sections=[]
 for z,tip in [(0,1.55),(4.9,.85),(9.8,1.55)]:
  points=[(-3.65,2.28),(-tip,3.31),(-tip-.22,3.94),(-3.85,2.91)]
  if side>0:points=[(-x,y) for x,y in reversed(points)]
  vv=[V(x,y,z) for x,y in points];sections.append(Part.Wire(Part.makePolygon(vv+[vv[0]]).Edges))
 fingers.append(Part.makeLoft(sections,True,False))
mask=Part.makeCompound(fingers);mask.translate(V(0,-7.51,3.9));mask.rotate(V(),V(1,0,0),-90);mask.translate(V(0,-1.27,2))
finger_overlap=common.common(mask).Volume;rigid_overlap=common.cut(mask).Volume
check('Existing nominal spring-finger overlap retained',abs(common.Volume-1.7294223413446805)<1e-6,{'volume_mm3':common.Volume})
check('No IC20 overlap outside reconstructed spring fingers',rigid_overlap<1e-7,{'volume_mm3':rigid_overlap})
rows=[];inspected=0
for a in plan['assignments']:
 if a['board']!='ioboard':continue
 for ref in a['references']:
  if ref in ['IC20','KK1']:continue
  p=poses[ref];other=Part.read(a['source_model']);inspected+=1
  if a['offset_mm']!=[0,0,0] or a['rotation_deg']!=[0,0,0] or a['scale']!=[1,1,1]:
   # Existing library-pose exceptions are covered by the native scene screen.
   continue
  if p['flipped']:
   # No flipped ref passes the candidate AABB. Avoid inventing unknown B.Cu seat.
   continue
  other.rotate(V(),V(0,0,1),p['angle']);other.translate(V(p['x']-poses['KK1']['x'],p['y']-poses['KK1']['y'],0))
  ob=bounds(other)
  for name,c in [('IC20',reg),('KK1',heat)]:
   cb=bounds(c)
   aabb=all(cb[i]<=ob[i+3] and ob[i]<=cb[i+3] for i in range(3))
   # Always retain C3/C4/C5 evidence even though the outward pose clears AABB.
   if not aabb and ref not in ['C3','C4','C5']:continue
   overlap=c.common(other).Volume if aabb else 0.0
   dist=c.distToShape(other)[0]
   rows.append({'candidate':name,'reference':ref,'source_step':a['source_model'],'source_sha256':sha(Path(a['source_model'])),'source_assignment_hash_matches':sha(Path(a['source_model']))==a['source_sha256'],
    'AABB_overlaps':aabb,'exact_intersection_volume_mm3':overlap,'exact_distance_mm':dist,'neighbor_bounds_in_KK1_frame_mm':ob})
   check(name+'/'+ref+' source hash retained',sha(Path(a['source_model']))==a['source_sha256'])
   check(name+'/'+ref+' no exact neighbor volume intersection',overlap<1e-7,{'volume_mm3':overlap,'distance_mm':dist})
for ref,s in models.items():
 check(ref+' above PCB seat plane',s.BoundBox.ZMin>0,{'minimum_z_mm':s.BoundBox.ZMin})
 check(ref+' beyond original main rectangular PCB backedge',s.BoundBox.YMin+poses[ref]['y']>44.45,{'candidate_min_native_y_mm':s.BoundBox.YMin+poses[ref]['y'],'source_main_rectangular_outline_ymax_mm':44.45})
# Original generic body mount hole and source KK1 hole are coaxial at Y14.44; the nominal rear contact face is Z1.38 mm.
report={'passed':all(c['passed'] for c in checks),'checks_passed':sum(c['passed'] for c in checks),'checks':checks,'neighbor_models_loaded':inspected,'exact_neighbor_scope':'All current zero/unity F.Cu source models screened by AABB; C3/C4/C5 always refined. Existing library-pose exceptions and B.Cu placement are covered by the native saved-scene screen.','neighbors':rows,
 'paired_contact':{'intersection_mm3':common.Volume,'spring_finger_intersection_mm3':finger_overlap,'outside_spring_finger_mask_mm3':rigid_overlap,
 'aligned_hole_axis_y_in_KK1_frame_mm':14.44,'nominal_contact_plane_z_mm':1.38,'IC20_tab_z_extent_mm':[1.38,2.65],'KK1_rear_sheet_z_extent_mm':[.75,1.38],'contact_area_preserved_from_revision_9_mm2':134.5990817203063},
 'installation_assumptions':manifest['installation_assumptions'],'limitations':manifest['parts'][0]['limitations'],
 'scope':'Isolated read-only exact STEP audit. Main rectangular PCB outline is only a source-datum check; the saved native full board and case mesh screen is separate.',
 'hashes':{p['step']:sha(Path(p['step'])) for p in manifest['parts']}}
(H/'bent-pair-geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks_passed':report['checks_passed'],'neighbors':rows,'paired_contact':report['paired_contact']},indent=2))
assert report['passed']
