"""Detailed review-only candidates for original CTS/NKK/Grayhill controls.

Original own parametric NKK/Grayhill interpretation: CC0-1.0. CTS candidate
incorporates manufacturer shared-family housing geometry; manufacturer rights
remain applicable. No candidate is claimed to be exact manufacturer BOM CAD.
"""
from pathlib import Path
import sys,json,hashlib,math
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part,Import,MeshPart
from step_face_colors import add_step_face_colors
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
V=App.Vector
BLACK=(.035,.035,.04);METAL=(.62,.64,.66);BRASS=(.62,.59,.48);WHITE=(.88,.86,.78);FR4=(.51,.48,.25)
INPUTS=[ROOT/'mainboard/mainboard.kicad_pcb',ROOT/'ioboard/ioboard.kicad_pcb',HERE/'sources/cts290-wrong-variant-reference.STEP',ROOT/'validation/models-review-6/control-body-illustrations/CTS_290VAA5F201B2_BodyIllustration.step',ROOT/'validation/models-review-6/control-body-illustrations/NKK_B12AB_BodyIllustration.step',ROOT/'validation/models-review-6/control-body-illustrations/Grayhill_25LB22H_BodyIllustration.step']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
BEFORE={str(p):sha(p) for p in INPUTS}
def box(w,d,h,x=None,y=None,z=0):return Part.makeBox(w,d,h,V(-w/2 if x is None else x,-d/2 if y is None else y,z))
def cyl(d,h,z=0,x=0,y=0):return Part.makeCylinder(d/2,h,V(x,y,z))
def fuse(parts):
 s=parts[0]
 for p in parts[1:]:s=s.fuse(p)
 return s.removeSplitter()
def rounded_box(w,d,h,r,z=0,cy=0):
 core=[box(w-2*r,d,h,z=z,y=cy-d/2),box(w,d-2*r,h,z=z,y=cy-d/2+r)]
 for x in [-w/2+r,w/2-r]:
  for y in [cy-d/2+r,cy+d/2-r]:core.append(cyl(r*2,h,z,x,y))
 return fuse(core)
def flat_shaft(d,z0,z1,flat_length,across,chamfer=.3):
 s=cyl(d,z1-z0-chamfer,z0).fuse(Part.makeCone(d/2,d/2-chamfer,chamfer,V(0,0,z1-chamfer)))
 # Preserve original canonical flat on negativeY. Across=flat plane to far tangent.
 s=s.cut(box(30,20,flat_length,x=-15,y=-20-(across-d/2),z=z1-flat_length))
 return s.removeSplitter()
def mesh_bounds(shape):
 verts,_=shape.tessellate(.015);return {'min_mm':[min(getattr(v,c) for v in verts) for c in ['x','y','z']],'max_mm':[max(getattr(v,c) for v in verts) for c in ['x','y','z']]}
def bb(shape):
 b=shape.BoundBox;return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
def export(key,refs,footprint,features,dimensions,improvements,limits,sources,license):
 doc=App.newDocument(key);objects=[];feature_records=[]
 for label,shape,color,basis in features:
  assert shape.isValid() and shape.Volume>0,(key,label)
  obj=doc.addObject('PartDesign::Feature',label);obj.Label=label;obj.Shape=shape;objects.append(obj)
  mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.12,Relative=False);dest=HERE/(key+'--'+label+'.stl');mesh.write(str(dest))
  feature_records.append({'name':label,'stl':str(dest),'sha256':sha(dest),'color_srgb':color,'evidence_basis':basis,'solid_count':len(shape.Solids),'faces':len(shape.Faces),'volume_mm3':shape.Volume,'tight_mesh_bounds':mesh_bounds(shape)})
 doc.recompute();dest=HERE/(key+'.step');Import.export(objects,str(dest));styles=add_step_face_colors(dest,[(label,s,c) for label,s,c,_ in features]);compound=Part.makeCompound([s for _,s,_,_ in features]);mesh=MeshPart.meshFromShape(Shape=compound,LinearDeflection=.025,AngularDeflection=.12,Relative=False);stl=HERE/(key+'.stl');mesh.write(str(stl));back=Part.read(str(dest));assert back.isValid();assert abs(back.Volume-compound.Volume)<max(1e-5,compound.Volume*1e-7);tight=mesh_bounds(back);assert tight['min_mm'][2]>-1e-6
 old=ROOT/'validation/models-review-6/control-body-illustrations'/(key.replace('_DetailedCandidate','_BodyIllustration')+'.step')
 rec={'id':key,'board':'mainboard','references':refs,'footprint':footprint,'step':str(dest),'stl':str(stl),'source_sha256':sha(dest),'stl_sha256':sha(stl),'units':'mm','canonical_frame':'Original F.Cu footprintX,-footprintY,+Z outward; no placement side flip baked in.','offset_mm':[0,0,0],'rotation_deg':[0,0,0],'scale':[1,1,1],'classification':'Detailed source-grounded body-only visualization candidate; physical fit unqualified','dimensions':dimensions,'improvements':improvements,'limitations':limits,'sources':sources,'license':license,'segments':feature_records,'geometry_audit':{'STEP_roundtrip_valid':True,'colored_solids':styles,'solid_count':len(back.Solids),'faces':len(back.Faces),'volume_mm3':back.Volume,'compound_bbox_mm':bb(back),'tight_mesh_bounds':tight,'triangles':mesh.CountFacets,'all_geometry_at_or_above_canonical_seat':True}}
 App.closeDocument(doc.Name);PARTS.append(rec)
 print(key,'ready',len(back.Faces),'faces',flush=True)

PARTS=[]
# CTS: retain authentic shared-series housing features only, not old terminals,
# old threaded B bushing, or old long C0 shaft. Rigid transform reproduces the
# earlier source-verified family frame. A-body rearZ0 and frontZ6.2 remain fixed.
source=Part.read(str(HERE/'sources/cts290-wrong-variant-reference.STEP'))
mat=App.Matrix();mat.A11=-1;mat.A12=0;mat.A13=0;mat.A21=0;mat.A22=0;mat.A23=1;mat.A31=0;mat.A32=1;mat.A33=0;mat.A34=2.93
source.transformShape(mat,False)
window=box(40,40,6.2,z=0)
features=[]
for i,label,color in [(1,'SharedFamilyStator',BLACK),(3,'SharedFamilyRearMolding',BLACK),(4,'SharedFamilyMetalCan',METAL),(5,'SharedFamilyFrontHousing',METAL)]:
 s=source.Solids[i].common(window)
 features.append((label,s,color,'Official wrong-variant CAD shared housing subset, rigidly transformed then intersected with0≤Z≤6.2mm. Shared-family applicability is qualified; original CAD immutable.'))
bush=cyl(7,4.7,6.2).fuse(Part.makeCone(3.5,3.2,.3,V(0,0,10.9)))
features += [('ExactA_UnthreadedBushing',bush,BRASS,'Exact BOM A code:7mm nonthreaded bushing,5mm projection from housing front; small top chamfer unsized.'),('ExactA5_FlattedShaft',flat_shaft(6,6.2,21.2,7,4.5,.3),BRASS,'Exact BOM A5/F:6mm shaft,15mm from housing front,7mm-long4.5mm-across flat. Tip chamfer unsized.')]
export('CTS_290VAA5F201B2_DetailedCandidate',['S2'],'PEC11-S',features,
 {'nominal_metal_housing_width_depth_height_mm':[9.8,10.6,6.2],'housing_rear_z_mm':0,'housing_front_z_mm':6.2,'bushing_diameter_length_mm':[7,5],'shaft_diameter_mm':6,'shaft_tip_z_mm':21.2,'shaft_length_from_housing_front_mm':15,'flat_length_across_mm':[7,4.5]},
 ['Manufacturer shared-family stamped can with locking folds and molded rear/contact carrier replaces rectangular envelope.','ThreadedB/30mm C0 geometry removed completely; exactA unthreaded5mm bushing and A5/F15mm shaft regenerated.','Separated polymer and metal colors; full neutral shaft datum21.2mm preserved.'],
 ['This is a derived original-BOM visualization, not exact manufacturer290VAA5F201B2 CAD. Housing subset comes from290VBC0F201B2; equivalence of every small historical molding detail remains unverified.','The source family CAD includes a molding/terminal-guard overhang outside the nominal9.8x10.6mm metal can; it is preserved as source geometry, not mistaken for a published metal-can size.','Original shaft, threaded bushing and all source electrical-terminal solids are discarded. All below-seat mounting legs are omitted; previous incompatible tab/hole fit is not transferred to this candidate.','Bushing/shaft chamfers are illustration details. No pin fit, installed seating or enclosure clearance certification.'],
 ['https://www.ctscorp.com/Files/CAD/Encoders/CTS-Encoders-290-CAD-Files.zip','https://www.ctscorp.com/Files/DataSheets/Encoders/encoders-290-datasheet.pdf'],
 'CTS manufacturer geometry rights retained for shared housing derivative; original new bushing/shaft parameterization CC0-1.0.')

# NKK: source sized bracket stock and exterior cage, with separately visible
# molded body. Unsized folding reliefs/windows are explicitly approximate.
body=rounded_box(6.0,8.0,9.8,.55,z=.2)
# Source broad case profile steps, bounded by exact8x8.8 cage envelope.
body=body.fuse(box(6,8.8,1.7,z=.2)).removeSplitter()
top=rounded_box(8,8.8,.4,.55,z=10.0).cut(cyl(5.7,.6,9.9))
walls=[]
for x in [-4,3.6]:
 wall=box(.4,8.8,10.0,x=x,y=-4.4,z=0)
 # Broad side window exposing case, inferred from the public exact B12AB view.
 wall=wall.cut(box(.7,5.8,5.2,x=x-.15,y=-2.9,z=2.6))
 walls.append(wall)
for y in [-4.4,4.0]:
 wall=box(8,.4,10.0,x=-4,y=y,z=0)
 # Source visible central folded strap and small rectangular inspection slot.
 wall=wall.cut(box(1.45,.7,2.25,x=-.725,y=y-.15,z=5.15))
 wall=wall.cut(box(1.5,.7,1.45,x=-4,y=y-.15,z=0)).cut(box(1.5,.7,1.45,x=2.5,y=y-.15,z=0))
 walls.append(wall)
bracket=fuse([top]+walls)
bushing=cyl(6,2.7,10.4).cut(cyl(3.1,.8,12.4))
lever=cyl(2.6,8.7,13.1).fuse(Part.makeSphere(1.3,V(0,0,21.8))).common(box(10,10,10,z=13.1)).removeSplitter()
export('NKK_B12AB_DetailedCandidate',['S1'],'NKKTOGGLE',[
 ('PolymerCase',body,BLACK,'Own rounded/stepped body reconstruction from primaryA17 drawing and exact publicB12AB CAD preview; corner radii and steps unsized.'),
 ('FoldedBracketCage',bracket,METAL,'Exact0.4mm bracket stock and8x8.8x10.4mm envelope. Cage/window/folding details visually reconstructed from exact publicB12AB preview andA17, with unsized dimensions qualified.'),
 ('UnthreadedBushing',bushing,BLACK,'Exact B12AB unthreaded6mm bushing,2.7mm projection; visible collar recess unsized.'),
 ('RoundedBatLeverNeutral',lever,METAL,'Source10mm×2.6mm bat lever. Rounded end reconstructed from exact publicCAD preview; neutral reference pose retained, not an ON position.')],
 {'overall_cage_width_depth_height_mm':[8,8.8,10.4],'bracket_stock_mm':.4,'body_bushing_total_z_mm':13.1,'bushing_diameter_projection_mm':[6,2.7],'lever_diameter_axial_length_mm':[2.6,10],'neutral_lever_tip_z_mm':23.1,'total_throw_degrees':26},
 ['Replaced solid metal box with folded0.4mm cage, visible windows, separate stepped polymer case and front plate.','Added rounded lever end and collar recess while retaining13.1mm bushing datum and10mm axial lever length.','No electrical terminals or bracket ground pins; no false pin-fit result.'],
 ['Exact officialB12AB CAD configuration and preview were inspected, but DownloadCAD requires login. This is own source-grounded parameterization, not a recovered manufacturerSTEP.','Bracket window sizes, molding radii, local steps and collar recess are unsized visual interpretations within the unchanged published envelope.','Lever remains upright in a neutral inspection pose. B12AB is ON-NONE-ON and an installed lever would occupy either±13degree endpoint; no switch state is claimed.','Body rear atZ0 is the existing mounting assumption. Historical seat, terminals and full mechanical fit remain unqualified.'],
 ['https://www.nkkswitches.eu/pdf/toggle_B.pdf','https://www.nkkswitches.com/wp-content/themes/impress-blank/search/inc/part.php?part_no=B12AB','https://nkkswitches-embedded.partcommunity.com/3d-cad-models/?info=nkkswitches%2Ftoggle%2Fb%2Fb_asmtab.prj'],
 'CC0-1.0 for own parametric candidate; manufacturer sources and preview retain their rights.')

# Grayhill exact no-Z body:21.97square polymer, with14.97wide FR4 tongue.
#23.50mm source outline is the optional bracket, which is deliberately absent.
board=fuse([rounded_box(21.97,21.97,1.14,1.7),rounded_box(14.97,6.0,1.14,.7,cy=-11.925)])
housing=rounded_box(21.97,21.97,6.16,1.9,z=1.14)
# Raised front cover with clipped/rounded corners, as source front view/photo.
front=rounded_box(20.4,20.4,1.41,2.1,z=7.3)
# The two mounting-bracket lock ears are integral plastic features, not the
# optional metal bracket; their unsized local dimensions follow the drawing.
ears=[]
for y in [-4.1,4.1]:ears.append(box(1.7,2.8,6.0,x=-10.985,y=y-1.4,z=1.3))
housing=fuse([housing,front]+ears)
# Published3/8-32 major diameter and double-D flats. Thread root depth/profile
# is an explicitly visual assumption, not a toleranced thread model.
major=9.525;pitch=25.4/32
bushing=cyl(major,6.35,8.71)
# Visual circumferential thread indication at the published pitch. The
# first true helix attempt did not produce a valid BRep after double-D cuts;
# this revolved profile is explicit visual representation, not a thread tool.
z0=8.71;ztop=15.06;outer=[V(major/2,0,z0)]
for i in range(8):
 a=z0+.15+i*pitch
 if a+.46>=ztop:break
 outer.extend([V(major/2,0,a),V(major/2-.32,0,a+.23),V(major/2,0,a+.46)])
outer.append(V(major/2,0,ztop))
points=[V(0,0,z0)]+outer+[V(0,0,ztop),V(0,0,z0)]
bushing=Part.Face(Part.makePolygon(points)).revolve(V(0,0,0),V(0,0,1),360).common(box(8.13,20,6.35,z=8.71)).removeSplitter()
# Leave a narrow uncut start collar so major diameter remains exact at the
# source bushing base while the profile preserves its full6.35mm projection.
shaft=flat_shaft(6.35,15.06,27.76,6.35,5.56,.25)
tab=cyl(3.05,1.73,8.71,x=10.16)
contacts=[]
for x in [-5.08,-2.54,0,2.54,5.08]:
 contacts.append(cyl(1.15,.035,1.14,x,-12.7).cut(cyl(.7,.06,1.13,x,-12.7)))
# Own plated surface land illustrations only, no terminals below the board.
export('Grayhill_25LB22H_DetailedCandidate',['S3','S4'],'GH3074',[
 ('FR4OutputBoard',board,FR4,'Primary materialFR4;21.97mm main body projection,14.97mm tongue width,25.91mm total depth and1.14mm source thickness. Corner radii unsized.'),
 ('BlackMoldedHousing',housing,BLACK,'ExactB black housing,21.97mm square main outline with source-visible rounded corners/front steps. Local radii and step heights unsized.'),
 ('ThreadedDoubleDBushing',bushing,BLACK,'Published3/8-32 major9.525mm,pitch0.79375mm,8.13mm across flats,6.35mm projection. Circumferential pitch rings indicate the thread, rather than a true helix; root depth and triangular profile are visual assumptions.'),
 ('LightPolymerFlattedShaft',shaft,WHITE,'Published reinforced-thermoplastic shaft,6.35mm diameter,12.7mm exposed length,6.35mm-long5.56mm-across flat. Light finish follows current manufacturer familyphoto; historical exact color unconfirmed.'),
 ('IntegralNonTurnTab',tab,BLACK,'Published3.05mm width,1.73mm height,10.16mm offset. Circular envelope retained from prior interpretation; small molded profile unmeasured.'),
 ('IllustratedTonguePlating',Part.makeCompound(contacts),(.72,.65,.36),'Five visible output-board land indications at source rowY-12.7,pitch2.54. Annulus size, plating appearance and drill openings are presentation details; no below-seat leads.')],
 {'main_polymer_body_square_mm':21.97,'body_front_z_mm':8.71,'overall_output_board_depth_mm':25.91,'output_tongue_width_mm':14.97,'output_tongue_y_min_mm':-14.925,'output_board_thickness_mm':1.14,'bushing_major_diameter_pitch_across_flats_length_mm':[9.525,pitch,8.13,6.35],'shaft_diameter_exposed_length_mm':[6.35,12.7],'shaft_tip_z_mm':27.76,'shaft_flat_length_across_mm':[6.35,5.56],'integral_tab_center_x_width_height_mm':[10.16,3.05,1.73],'optional_bracket_width_mm':23.50,'optional_bracket_present':False},
 ['Replaced full23.5x25.91 box with21.97mm rounded polymer body and separate FR4 output tongue, retaining full25.91mm overall depth.','Added front-case step, integral lock ears, fine3/8-32 bushing thread indication and source flatted shaft with tip chamfer.','Separated black housing/FR4/plating/light shaft appearance using primary material list and current familyphoto.','Exact no-Z variant contains no optional25J5155 metal bracket.'],
 ['Official exact-part page says3D Model Available No; this is own source-grounded reconstruction, not manufacturerCAD.','Published21.97mm body and25.91mm output-board depth retained;23.50mm is associated with optional bracket outline and is not used as an oversized solid for no-Z part.','Corner radii, front-case step divisions, lock-ear details and thread root/flank profile and nonhelical ring representation are unprinted visual approximations. The full nominal exterior datums are unchanged.','Current photo shows a light reinforced-thermoplastic shaft; exact historical shaft finish is unverified.','Tongue lands are visual indications only. All terminals and optional mounting legs omitted; no physical fit or contact clearance certification.'],
 ['https://grayhill.com/wp-content/uploads/media/25l-datasheet.pdf','https://grayhill.com/products/rotational-controls/mechanical-encoders/mechanical-encoder/25l/25lb22-h/','https://grayhill.com/wp-content/uploads/media/25l-mechanical-encoder-01.jpg'],
 'CC0-1.0 for own parametric candidate; manufacturer sources/photo retain their rights.')

assignments=[]
for p in PARTS:
 assignments.append({'board':p['board'],'references':p['references'],'footprint':p['footprint'],'source_model':p['step'],'source_sha256':p['source_sha256'],'offset_mm':[0,0,0],'scale':[1,1,1],'rotation_deg':[0,0,0],'source_kind':'Detailed source-grounded body-only candidate; per-feature evidence qualified','classification':p['classification'],'limitations':p['limitations'],'source_urls':p['sources'],'license':p['license']})
AFTER={str(p):sha(p) for p in INPUTS};assert BEFORE==AFTER
out={'scope':'Review-only detailed control candidates. No actual PCB/library/scene or original model modified.','units':'mm','canonical_frame':'X=original F.Cu footprintX,Y=-footprintY,Z=outward; native footprint/board transforms applied later, exactly once.','parts':PARTS,'assignments':assignments,'reference_count':sum(len(p['references']) for p in PARTS),'input_hashes':BEFORE,'inputs_unchanged':BEFORE==AFTER,'source_availability':'sources/source-availability.json','physical_fit_qualified':False}
(HERE/'rotary-quality-manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'families':len(PARTS),'references':out['reference_count'],'inputs_unchanged':out['inputs_unchanged'],'manifest':str(HERE/'rotary-quality-manifest.json')},indent=2))
