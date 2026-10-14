"""Generic source-body 5mm LEDs at source BOM spacer height, no project edits."""
from pathlib import Path
import ast,hashlib,json,re,shutil,sys
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part,Import,MeshPart,Mesh
H=Path(__file__).resolve().parent;W=H.parents[2];V=A.Vector
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=H/'sources/official-KiCad-LED_D5.0mm-original.step'
assert sha(source)=='7cc5086e6ee1fb4853d1fb74675a61a436c8811204094823b31f04ce788e5d40'
stock=Part.read(str(source))
old=W/'validation/models-review-6/misc-body-illustrations/generate_misc_bodies.py'
node=next(n for n in ast.parse(old.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='add_step_face_colors')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(old),'exec'))
body=stock.common(Part.makeBox(20,20,20,V(-8,-10,3)))
assert body.isValid() and len(body.Solids)==1
head=body.copy();head.translate(V(0,0,3.096))
legs=[Part.makeBox(.4,.4,8.596,V(x-.2,-.2,-2.5)) for x in [0,2.54]]
features=[('ClearLensBody',head,(.72,.82,.85)),('CathodeFullWidthLead',legs[0],(.824,.82,.781)),('AnodeFullWidthLead',legs[1],(.824,.82,.781))]
# Explicit roles convey clear/unlit photo appearance; optical glass is Blender material work.
doc=A.newDocument('Generic_LED5mm_STD240B_Installed');objs=[]
for name,s,c in features:
 o=doc.addObject('PartDesign::Feature',name);o.Shape=Part.makeCompound([s]);objs.append(o)
doc.recompute();key='Generic_LED5mm_STD240B_6p096_ClearBody_FullLeads';step=H/(key+'.step');stl=H/(key+'.stl')
Import.export(objs,str(step));add_step_face_colors(step,features)
united=head.multiFuse(legs).removeSplitter();assert len(united.Solids)==1 and united.isValid()
MeshPart.meshFromShape(Shape=united,LinearDeflection=.02,AngularDeflection=.1,Relative=False).write(str(stl))
segments=[]
for name,s,c in features:
 p=H/(key+'--'+name+'.stl');MeshPart.meshFromShape(Shape=s,LinearDeflection=.02,AngularDeflection=.1,Relative=False).write(str(p));assert Mesh.Mesh(str(p)).isSolid()
 segments.append({'name':name,'stl':p.name,'color_rgb':list(c)})
r=Part.read(str(step));assert r.isValid() and abs(r.Volume-united.Volume)<1e-6 and Mesh.Mesh(str(stl)).isSolid()
def bounds(s):
 b=s.BoundBox;return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
expected=bounds(stock);expected[5]+=3.096
assert max(abs(a-b) for a,b in zip(bounds(r),expected))<1e-6,(bounds(r),expected)
refs=['LED'+str(i) for i in range(1,41)]
limitations=[
 'The complete official generic KiCad LED body above its Z3mm lower-flange plane is preserved by a rigid +3.096mm translation. Exact original fitted LED manufacturer and package tolerances are unknown.',
 'The selected 6.096mm lower-body height follows the original BOM VCC STD240B 0.24in. The original sequencer table instead says0.22in/5.588mm; that conflict is preserved, not silently resolved as a measured installed height.',
 'Full stock 0.4x0.4mm lead cross-sections at sourceX0 andX2.54mm are retained and extended continuously from trimmedZ-2.5mm to the new body undersideZ6.096mm. Lead material, cut length and exact fitted original lead specification remain generic illustration data.',
 'Existing native model offset[1.27,0,0] and rotation[0,0,180] with unity scale are preserved for all40LED references; original footprint axes, polarity, pad and drill geometry are unchanged.',
 'Clear/unlit lens appearance follows original author PCB/panel photos. STEP light-gray color is an appearance role, not an optical simulation; Blender transmission/refraction settings are presentation choices.',
 'Spacer height is represented by body seating. No black spacer shape is added because an exact primary outline was not recovered in the bounded search. This avoids inventing unverified outer profile or lead holes.',
 'Current scene panel seat yields a nominal1.300mm lens-tip projection above the top panel; alternative0.22in spacing yields0.792mm. Native exported assembly measurements must independently confirm this after integration.',
 'No lead thinning, scaled body, moved PCB footprint, altered panel hole or fitted tolerance/physical assembly claim is made.'
]
urls=['https://www.ladyada.net/make/x0xb0x/fab/parts.html','https://www.ladyada.net/make/x0xb0x/fab/seq/index.html','https://www.flickr.com/photos/ladyada/388601923','https://www.flickr.com/photos/ladyada/388576688']
part={'id':key,'board':'mainboard','references':refs,'footprint':'LED5MM','step':str(step),'stl':str(stl),'units':'mm','source_sha256':sha(step),'stl_sha256':sha(stl),
 'canonical_frame':'Original official generic stock LED source frame retained: source lead axesX0 andX2.54mm, lens axisX1.27mm; existing native offset/rotation applies unchanged.',
 'classification':'Original-photo clear-body generic 5mm LED with source-BOM spacer seat and full-width extended leads','source_urls':urls,'limitations':limitations,'segments':segments,
 'geometry':{'valid':r.isValid(),'solids':len(r.Solids),'faces':len(r.Faces),'volume_mm3':r.Volume,'exact_bounds_mm':bounds(r),'union_solid_count':len(united.Solids),'STL_closed':Mesh.Mesh(str(stl)).isSolid(),'STL_facets':Mesh.Mesh(str(stl)).CountFacets,'AP214_styled_faces':step.read_text().count('STYLED_ITEM')},
 'dimensions':{'generic_source_lower_body_Z_mm':3,'selected_BOM_body_lower_Z_mm':6.096,'source_body_rigid_lift_mm':3.096,'lens_top_Z_mm':14.696,'stock_lens_body_height_mm':8.6,'full_lead_width_mm':.4,'full_lead_thickness_mm':.4,'lead_axis_source_X_mm':[0,2.54],'trimmed_tail_minimum_Z_mm':-2.5,'unresolved_seq_alternative_standoff_mm':5.588},
 'stock_source_step':str(source),'stock_source_sha256':sha(source),'source_body_before_lift_bounds_mm':bounds(body),'source_body_volume_mm3':body.Volume}
a={'board':'mainboard','references':refs,'footprint':'LED5MM','source_model':str(step),'source_sha256':sha(step),'offset_mm':[1.27,0,0],'rotation_deg':[0,0,180],'scale':[1,1,1],
 'source_kind':'Official generic source body with original author BOM spacer height and full-width continuous installed leads','classification':part['classification'],'limitations':limitations,'source_urls':urls,
 'replaces_source_model':str(source),'replaces_source_sha256':sha(source)}
report={'date':'2026-10-14','parts':[part],'assignments':[a],'generator':'build_LED_installed.py','license':'Reconstruction code CC0-1.0; modified official KiCad source-head geometry CC-BY-SA-4.0 with the official KiCad library exception; original source texts/photos retain publisher rights.', 'geometry_audit':'led-assembly-geometry-audit.json', 'native_export_audit':'native-probes/native-export-audit.json', 'panel_hole_audit':'led-panel-hole-audit.json', 'documentation':'README.md'}
(H/'led-assembly-manifest.json').write_text(json.dumps(report,indent=2)+'\n');A.closeDocument(doc.Name)
print(json.dumps({'source_sha256':part['source_sha256'],'geometry':part['geometry'],'dimensions':part['dimensions']},indent=2))
