"""Verify the retained Mitsubishi package illustration and archive its source.

Read-only exact BRep checks; original installed forming remains illustrative.
"""
import hashlib,itertools,json,sys
from pathlib import Path
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
H=Path(__file__).resolve().parent;W=H.parents[1];R=W.parent;V=App.Vector
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=H/'sources/mitsubishi-2sc1583.pdf';assert sha(source)=='78dc3990fa5b2210453a0972f5a351e9fcef93f4bff40b6d42852999f63faefd'
model=W/'mainboard/3dmodels/Revision5/integrated-models/SSIP5_2SC1583_MaxBody_FannedP2.286_Illustration.step';assert sha(model)=='9a485b529d902a5b33a3beafe7bdca2cf4983aebc15ef889787b22e8e0af3c9d'
inputs=[model,W/'mainboard/mainboard.kicad_pcb',W/'ioboard/ioboard.kicad_pcb',W/'visualization/blender-case-revision-22/x0xb0x-populated-with-case.blend'];guards={str(p.relative_to(R)):sha(p) for p in inputs}
s=Part.Shape();s.read(str(model));checks=[]
def check(name,ok,**details):
 checks.append(dict(check=name,passed=bool(ok),**details));assert ok,name
check('Valid source model contains body and five independent leads',s.isValid() and len(s.Solids)==6)
body=s.Solids[0];leads=s.Solids[1:];b=body.BoundBox
check('Printed maximum body dimensions8.1x3.6x5.6mm retained',max(abs(a-v) for a,v in zip([b.XLength,b.YLength,b.ZLength],[8.1,3.6,5.6]))<1e-7)
check('Existing2.8mm installed standoff retained',abs(b.ZMin-2.8)<1e-7)
check('Printed rear-edge-to-lead-row1.4mm retained',abs(b.YMax-1.4)<1e-7)
points=[V(-4.05,y,z) for y,z in [(-2.2,2.8),(1.4,2.8),(1.4,6.4),(-.6,8.4),(-2.2,8.4)]]
expected=Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(8.1,0,0))
check('Body profile follows the source2x2mm rear-top bevel',body.cut(expected).Volume+expected.cut(body).Volume<1e-7)
sections=[]
for i,lead in enumerate(leads):
 check('Pin'+str(i+1)+' joins its body',lead.common(body).Volume>0)
 for z,pitch,label in [(2.7,1.25,'native'),(-1.0,2.286,'installed')]:
  sec=lead.section(Part.makePlane(30,30,V(-15,-15,z)));bb=sec.BoundBox;axis=(bb.XMin+bb.XMax)/2
  check('Pin'+str(i+1)+' '+label+' pitch axis',abs(axis-(i-2)*pitch)<1e-6)
  check('Pin'+str(i+1)+' '+label+' full0.45mm round section',abs(bb.XLength-.45)<1e-6 and abs(bb.YLength-.45)<1e-6 and abs(sec.Length-3.141592653589793*.45)<1e-5)
  sections.append(dict(pin=i+1,plane_z_mm=z,axis_x_mm=axis,diameter_x_mm=bb.XLength,diameter_y_mm=bb.YLength))
 check('Pin'+str(i+1)+' retained cut-tail extent',abs(lead.BoundBox.ZMin+2.5)<1e-7)
for (i,a),(j,b) in itertools.combinations(enumerate(leads),2):check('Pins'+str(i+1)+'/'+str(j+1)+' do not intersect',a.common(b).Volume<1e-9)
# Parse actual native PCB pads, not only the shared footprint cache.
sys.path.insert(0,str(R/'kicad-import/validation'))
from verify_native_projects import parse_sexpr,children,one,property_value
pcb=parse_sexpr((W/'mainboard/mainboard.kicad_pcb').read_text());pad_records=[]
for footprint in children(pcb,'footprint'):
 ref=property_value(footprint,'Reference','reference')
 if ref not in ['Q12','Q21','Q26']:continue
 model_node=one(footprint,'model');check(ref+' original zero/unity model transform',all([float(v) for v in one(one(model_node,key),'xyz')[1:]]==expected for key,expected in [('offset',[0,0,0]),('rotate',[0,0,0]),('scale',[1,1,1])]))
 check(ref+' uses the verified exact model',model_node[1]=='${KIPRJMOD}/3dmodels/Revision5/integrated-models/'+model.name)
 for pad in children(footprint,'pad'):
  if pad[1] not in ['1','2','3','4','5']:continue
  number=int(pad[1]);at=one(pad,'at');drill=float(one(pad,'drill')[1]);net=one(pad,'net');x,y=float(at[1]),float(at[2])
  check(ref+'/'+str(number)+' actual PCB axis matches installed lead',abs(x-(number-3)*2.286)<1e-7 and abs(y)<1e-7)
  check(ref+'/'+str(number)+' nominal drill clears full-diameter lead',drill>.45,drill_mm=drill,radial_margin_mm=(drill-.45)/2)
  pad_records.append(dict(reference=ref,pin=number,xy_mm=[x,y],drill_mm=drill,net=net[-1] if net and len(net)>1 else None))
check('All15 fitted pads checked',len(pad_records)==15)
check('All model, PCB and saved-scene bytes unchanged',guards=={str(p.relative_to(R)):sha(p) for p in inputs})
out=dict(passed=True,check_count=len(checks),checks=checks,source=dict(file='sources/mitsubishi-2sc1583.pdf',sha256=sha(source),publisher='Mitsubishi Semiconductor',url='https://www.radioradar.net/en/files.html?fid=502807',recovery='Archived from the older local conversion workspace; hash exactly matches the existing assignment provenance',page=1),model=str(model.relative_to(R)),model_sha256=sha(model),references=['Q12','Q21','Q26'],pin_roles=['1/B1','2/C1','3/E common','4/C2','5/B2'],sections=sections,pads=pad_records,active_inputs_unchanged=guards,limitations=['Body uses printed maximum dimensions, not a measured historical fitted part','2.8mm standoff,Bezier fanout,0.12mm body embedding and2.5mm trimmed tails remain installation illustrations','Native1.25mm lead pitch is fanned to original2.286mm PCB pitch; forming is not a manufacturer specification','Source10.5mm minimum lead length is uncut stock length, not installed tail length','No physical assembly, tolerance, or circuit-operation qualification'],read_only=True,physical_fit_qualified=False)
(H/'existing-model-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(passed=True,check_count=len(checks),fitted_pads=len(pad_records)),indent=2))
