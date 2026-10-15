"""Micro-Ohm LPTC12 drawing-derived nominal model for the two original PTCs.

Original geometry/code CC0-1.0; source documents retain their publisher rights.
Printed body/lead dimensions govern. Installation and coating details remain
explicit illustrations, and neither PCB layout nor old model is changed here.
"""
import ast,hashlib,json,math,re,sys
from pathlib import Path
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part,Import,Mesh
H=Path(__file__).resolve().parent;W=H.parents[2];R=W.parent;V=App.Vector
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=W/'mainboard/3dmodels/Revision13/terminals/Microohm_LPTC12T21001_ApproxBody_Terminals.step'
pdf=H/'sources/micro-ohm-precision-film-sensor-user.pdf'
inputs=[old,W/'mainboard/mainboard.kicad_pcb',W/'ioboard/ioboard.kicad_pcb',W/'visualization/blender-case-revision-22/x0xb0x-populated-with-case.blend'];guards={str(p):sha(p) for p in inputs}
helpers=W/'validation/models-review-16/terminal-quality/build_terminals.py';tree=ast.parse(helpers.read_text());names={'axial_lead','expected_volume','brep_colors'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(helpers),'exec'))
legacy=W/'visualization/blender-case-revision-7/quality-model-sources/rear-quality/build_rear_quality.py';node=next(n for n in ast.parse(legacy.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='face_colors');exec(compile(ast.Module(body=[node],type_ignores=[]),str(legacy),'exec'))
palette=brep_colors(old);assert len(palette)==8
length,diameter,lead_d=3.7,1.9,.45;seat=.4;axis=seat+diameter/2;taper=.42
body=Part.makeCylinder(diameter/2,length-2*taper,V(-length/2+taper,0,axis),V(1,0,0))
body=body.fuse(Part.makeCone(.26,diameter/2,taper,V(-length/2,0,axis),V(1,0,0)))
body=body.fuse(Part.makeCone(diameter/2,.26,taper,V(length/2-taper,0,axis),V(1,0,0))).removeSplitter()
coating=[]
for x in [-1.0,-.52,-.04,.44,1.0]:
 ring=Part.makeCylinder(.95,.18,V(x-.09,0,axis),V(1,0,0)).cut(Part.makeCylinder(.94,.20,V(x-.10,0,axis),V(1,0,0)))
 coating.append(ring);body=body.cut(ring)
body=body.removeSplitter();terminal_specs=[];leads=[]
for sign in [-1,1]:
 spec=dict(name=str(len(leads)+1),pad=str(len(leads)+1),kind='axial_lead',x_body=sign*1.70,x_hole=sign*5.08,z_axis=axis,d=lead_d,bend_r=.75,z_tip=-3.1)
 lead=axial_lead(spec);leads.append(lead);terminal_specs.append(spec)
checks=[]
def check(name,ok,**detail):
 checks.append(dict(check=name,passed=bool(ok),**detail))
 if not ok:print(json.dumps(checks[-1]),flush=True)
 assert ok,name
check('Valid single body and five coating-band solids',body.isValid() and len(body.Solids)==1 and all(b.isValid() and len(b.Solids)==1 for b in coating))
body_envelope=Part.makeCompound([body]+coating);b=body_envelope.BoundBox
check('Printed3.7mm body length and1.9mm diameter retained',max(abs(x-y) for x,y in zip([b.XLength,b.YLength,b.ZLength],[length,diameter,diameter]))<1e-7,bounds_mm=[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax])
check('Existing0.4mm illustrated body standoff retained',abs(b.ZMin-seat)<1e-7)
check('Coating does not enlarge the printed outside diameter',abs(b.YLength-diameter)<1e-7)
for i,(lead,spec) in enumerate(zip(leads,terminal_specs)):
 check('Lead'+str(i+1)+' is a valid single continuous solid',lead.isValid() and len(lead.Solids)==1)
 check('Lead'+str(i+1)+' retains full analytic sweep volume',abs(lead.Volume-expected_volume(spec))<1e-7,volume_mm3=lead.Volume)
 check('Lead'+str(i+1)+' joins its own body end',lead.common(body).Volume>0 and lead.distToShape(body)[0]<1e-7)
 for z in [-2.5,-1,0,.3]:
  sec=lead.section(Part.makePlane(30,30,V(-15,-15,z)));bb=sec.BoundBox
  check('Lead'+str(i+1)+' full diameter and original hole axis atZ'+str(z),max(abs(a-v) for a,v in zip([bb.XLength,bb.YLength,(bb.XMin+bb.XMax)/2,(bb.YMin+bb.YMax)/2],[lead_d,lead_d,spec['x_hole'],0]))<1e-6)
 check('Lead'+str(i+1)+' retained solder-tail projection',abs(lead.BoundBox.ZMin+3.1)<1e-7)
check('The two separate terminals do not intersect',leads[0].common(leads[1]).Volume<1e-9)
check('Coating does not overlap base body',all(body.common(c).Volume<1e-8 for c in coating))
features=[('Body',body,palette[0])]+[('Band'+str(i+1),b,palette[i+1]) for i,b in enumerate(coating)]+[('DrawingDerivedTerminals',Part.makeCompound(leads),palette[-1])]
doc=App.newDocument('Microohm_LPTC12_Primary');objects=[]
for name,shape,rgb in features:
 o=doc.addObject('PartDesign::Feature',name);o.Shape=shape;objects.append(o);Mesh.Mesh(shape.tessellate(.025)).write(str(H/(name+'.stl')))
doc.recompute();out=H/'Microohm_LPTC12_PrimaryDimensions_Terminals.step';Import.export(objects,str(out));face_colors(out,[tuple(rgb) for _,s,rgb in features for _ in s.Solids]);out.write_text('\n'.join(l.rstrip() for l in out.read_text().splitlines())+'\n')
saved=Part.Shape();saved.read(str(out));check('Saved STEP contains eight valid positive solids',saved.isValid() and len(saved.Solids)==8 and all(s.Volume>0 for s in saved.Solids))
check('Original color palette and band order retained',brep_colors(out)==palette)
# OCC may classify a coincident reimported pipe as fully different in a cut.
# Check bilateral sampled surfaces plus independent analytic signatures instead.
roundtrip=[]
for index,(a,b) in enumerate(zip([s for _,shape,_ in features for s in shape.Solids],saved.Solids)):
 differences=[abs(a.Volume-b.Volume),abs(a.Area-b.Area),(a.CenterOfMass-b.CenterOfMass).Length]
 bounds_error=max(abs(getattr(a.optimalBoundingBox(False,False),k)-getattr(b.optimalBoundingBox(False,False),k)) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax'])
 distances=[]
 for left,right in [(a,b),(b,a)]:
  vertices,_=left.tessellate(.035)
  distances.extend(Part.Vertex(p).distToShape(right)[0] for p in vertices)
 maximum=max(distances)
 check('Saved solid'+str(index+1)+' preserves surfaces, volume, area, centroid and bounds',max(differences)<1e-7 and bounds_error<2e-7 and maximum<1e-7,maximum_surface_distance_mm=maximum,surface_samples=len(distances),volume_area_centroid_errors=differences,bounds_error_mm=bounds_error)
 roundtrip.append(dict(solid=index+1,maximum_surface_distance_mm=maximum,surface_samples=len(distances)))
doc.saveAs(str(H/'Microohm_LPTC12_PrimaryDimensions_FormedLeads.FCStd'));App.closeDocument(doc.Name)
check('All original model, PCB and Blender files remain unchanged',guards=={str(p):sha(p) for p in inputs})
report=dict(passed=True,check_count=len(checks),checks=checks,model=out.name,model_sha256=sha(out),previous_model_sha256=sha(old),source=dict(file='sources/micro-ohm-precision-film-sensor-user.pdf',sha256=sha(pdf),title='Micro-Ohm Precision Film Temperature Sensor Type LPTC',page=1,original_url='http://www.micro-ohm.com/temperature/temprecflm.html',retrieval='User printed the archived manufacturer HTML page to PDF; original downloaded PDF preserved byte-for-byte',archive_capture_timestamp='Not established by the printed PDF; CDX records retained separately'),dimensions_mm=dict(body_length=length,body_diameter=diameter,lead_diameter=lead_d,original_board_pitch=10.16,illustrated_body_standoff=seat,illustrated_bend_radius=.75,retained_solder_tip_z=-3.1),terminal_specs=terminal_specs,body_palette=palette,limitations=['Independent nominal reconstruction from the original manufacturer family page; not manufacturer CAD or measurement of the fitted historical part','0.4mm body standoff,0.75mm lead bend radius, formed lead paths and trimmed tails are installation illustrations','End tapers,0.18mm band widths, band positions and recessed0.01mm coating thickness are illustrative','Original BOM color sequence retained; no new electrical TCR/band-code certification inferred from the drawing','Source table provides no dimensional tolerance; actual fitted package/assembly fit remains unqualified'],physical_fit_qualified=False)
(H/'ptc-model-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,check_count=len(checks),model_sha256=sha(out)),indent=2),flush=True)
