"""Read-only independent KK1 pose proposal, no source or project mutation."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part,Import,MeshPart
H=Path(__file__).resolve().parent;W=H.parents[2];V=App.Vector
heat_path=H/'Aavid_574502B00000G_DrawingDerived_FoldedSpring.step'
reg_path=W/'validation/models-review-6/misc-body-illustrations/MC78M05_TO220_BodyOnlyIllustration.step'
heat=Part.read(str(heat_path));reg=Part.read(str(reg_path));reg.translate(V(0,-1.27,0))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def bounds(s):
 b=s.BoundBox;return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
def box(w,d,h,x,y,z):return Part.makeBox(w,d,h,V(x,y,z))
# Reconstruct only the frozen generator's named finger mask as a review tool;
# the immutable candidate BRep is read unchanged and not regenerated/exported.
fingers=[]
for side in [-1,1]:
 sections=[]
 for z,tip in [(0,1.55),(4.9,.85),(9.8,1.55)]:
  pts=[(-3.65,2.28),(-tip,3.31),(-tip-.22,3.94),(-3.85,2.91)]
  if side>0:pts=[(-x,y) for x,y in reversed(pts)]
  vv=[V(x,y,z) for x,y in pts];wire=Part.makePolygon(vv+[vv[0]]);sections.append(Part.Wire(wire.Edges))
 fingers.append(Part.makeLoft(sections,True,False))
finger_mask=Part.makeCompound(fingers)
poses=[]
for label,offset in [('prior_zero',[0,0,0]),('Y_only',[0,-8.78,0]),('rejected_point72',[0,-8.78,.72]),('hole_and_back_plane_aligned',[0,-8.78,3.9])]:
 h=heat.copy();h.translate(V(*offset));mask=finger_mask.copy();mask.translate(V(*offset))
 common=h.common(reg);finger_common=common.common(mask);rigid_common=common.cut(mask)
 face_contacts=[]
 for hf in h.Faces:
  hb=hf.BoundBox
  if abs(hb.YMin+.65)>1e-7 or abs(hb.YMax+.65)>1e-7:continue
  for rf in reg.Faces:
   rb=rf.BoundBox
   if abs(rb.YMin+.65)>1e-7 or abs(rb.YMax+.65)>1e-7:continue
   touch=hf.common(rf)
   if touch.Area>1e-7:face_contacts.append({'area_mm2':touch.Area,'bounds_mm':bounds(touch)})
 poses.append({'label':label,'offset_mm':offset,'bounds_in_KK1_frame_mm':bounds(h),
               'intersection_volume_mm3':common.Volume,'intersection_bounds_mm':bounds(common) if common.Volume>1e-8 else None,
               'intersection_in_reconstructed_spring_fingers_mm3':finger_common.Volume,
               'intersection_outside_finger_mask_mm3':rigid_common.Volume,
               'rear_contact_plane_y_mm':8.13+offset[1],
               'heatsink_hole_axis_z_mm':11.81+offset[2], 'regulator_hole_axis_z_mm':15.71,
               'hole_axis_residual_mm':abs(11.81+offset[2]-15.71),
               'coplanar_back_contact_faces':face_contacts,
               'total_coplanar_back_contact_area_mm2':sum(t['area_mm2'] for t in face_contacts)})
out={'scope':'Independent exact-BRep comparison of immutable KK1 and unchanged IC20 with explicit proposed model-only translations. No PCB/model/scenes changed.',
     'source_sha256':{str(heat_path):sha(heat_path),str(reg_path):sha(reg_path)},
     'actual_native_origin_difference_IC20_minus_KK1_mm':[0,-1.27,0],
     'primary_drawing_interpretation':{'through_hole_axis_height_mm':11.81,'upper_lance_bottom_datum_mm':14.99,
                                       'note':'Fresh high-resolution drawing inspection confirms11.81 throughholecentre and14.99 upperlancebottom, neither is a holdingcatch datum.'},
     'poses':poses,'proposed_offset_mm':[0,-8.78,3.9],
     'nominal_channel_mm':4.19,'nominal_channel_tolerance_mm':.13,'regulator_plastic_depth_mm':4.455,
     'nominal_plastic_over_channel_mm':.265,
     'limitations':['IC20 is a nominal generic body-only model with assumed bodybottomZ3.0 and vendor/seating uncertainty. Hole alignment inherits that assumption.',
                    'Remaining intersection is evaluated geometrically, not presumed elastic. Finger geometry itself is unsized reconstruction; alloy/tempering, force/deformation and tolerances are unknown.',
                    'No manufacturer-mounted exact-part assemblyphoto was recovered in this bounded local review. Manufacturer drawing shows TO220 slide-on checking gap and device/tab concept, but does not qualify actual x0xb0x seating.',
                    'Full-case/neighbor mesh screen is recorded separately; this is not hardware assembly or thermal qualification.']}
(H/'independent-nominal-seating-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'poses':[{k:r[k] for k in ('label','offset_mm','intersection_volume_mm3','intersection_in_reconstructed_spring_fingers_mm3','intersection_outside_finger_mask_mm3','hole_axis_residual_mm','total_coplanar_back_contact_area_mm2')} for r in poses]},indent=2))
