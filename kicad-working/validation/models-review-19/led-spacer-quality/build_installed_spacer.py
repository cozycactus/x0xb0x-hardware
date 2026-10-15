"""Add drawing-derived STD240B spacers to the unchanged installed LED geometry.

Original spacer geometry/code CC0-1.0. Retained KiCad LED geometry uses its
original CC-BY-SA-4.0/library exception. Source documents retain their rights.
"""
import ast,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part,Import,Mesh
H=Path(__file__).resolve().parent;R=H.parents[3];W=R/'kicad-working';V=App.Vector
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=W/'mainboard/3dmodels/Revision10/led-assembly-quality/Generic_LED5mm_STD240B_6p096_ClearBody_FullLeads.step'
assert sha(old)=='2a61af0d1b2a4ef8f4e8ddda40651a13ee141cf824938d16ae99e5583483d987'
stock=Part.Shape();stock.read(str(old));assert len(stock.Solids)==3
pdf=H/'sources/vcc-std-series-datasheet.pdf';catalog=H/'sources/vcc-mouser-catalog-646-page178.pdf'
guards={str(p):sha(p) for p in [old,W/'mainboard/mainboard.kicad_pcb',W/'ioboard/ioboard.kicad_pcb',W/'visualization/blender-case-revision-21/x0xb0x-populated-with-case.blend']}
height=6.096;end=.254;depth=1.397
spacer=Part.makeCylinder(2.54,height-end,V(1.27,0,end))
# Section A-A specifies lengthXXX to the bottom of the0.010-inch end lands.
# Two annular end lands are illustrated at the solder-lead axes. Their outer
# radius is unsized; chosen0.65mm within the dimensioned outside envelope.
for x in [0,2.54]:spacer=spacer.fuse(Part.makeCylinder(.65,end,V(x,0,0)))
# Dimensioned0.160-to0.127-inch tapered LED seating recess,0.055-inch deep.
spacer=spacer.cut(Part.makeCone(1.613,2.032,depth,V(1.27,0,height-depth)))
# Four0.047-inch longitudinal holes at the dimensioned4PLS +/-0.050 axes.
for x in [0,2.54]:
 for y in [-1.27,1.27]:spacer=spacer.cut(Part.makeCylinder(.597,height+.2,V(x,y,-.1)))
# Two0.036-inch lead bores are explicit; the third central bore follows the
# tri-lead assembly/end view, with its unsized diameter illustrated the same.
for x in [2.54,1.27,0]:
 tool=Part.makeCylinder(.457,height+.2,V(x,0,-.1));tool.rotate(V(x,0,0),V(0,0,1),37)
 spacer=spacer.cut(tool).removeSplitter()
spacer=spacer.removeSplitter()
assert spacer.isValid() and len(spacer.Solids)==1
checks=[]
def check(name,ok,**data):
 checks.append(dict(check=name,passed=bool(ok),**data));assert ok,name
b=spacer.BoundBox
check('Drawing total length includes end projections',abs(b.ZMin)<1e-7 and abs(b.ZMax-height)<1e-7,total_mm=b.ZLength)
check('Drawing outside diameter retained',abs(b.XLength-5.08)<1e-7 and abs(b.YLength-5.08)<1e-7)
for i,s in enumerate(stock.Solids):
 check('Spacer has no volume overlap with unchanged LED part'+str(i+1),spacer.common(s).Volume<1e-9,intersection_mm3=spacer.common(s).Volume)
features=[('ClearLensBody',stock.Solids[0],(.72,.82,.85)),('CathodeFullWidthLead',stock.Solids[1],(.824,.82,.781)),('AnodeFullWidthLead',stock.Solids[2],(.824,.82,.781)),('BlackSTD240BSpacer',spacer,(.025,.027,.03))]
doc=App.newDocument('LED5mm_STD240B_WithSpacer');objs=[]
for name,shape,color in features:
 o=doc.addObject('PartDesign::Feature',name);o.Shape=shape;objs.append(o)
 Mesh.Mesh(shape.tessellate(.025)).write(str(H/(name+'.stl')))
doc.recompute();out=H/'LED5mm_STD240B_WithSpacer.step';Import.export(objs,str(out))
legacy=W/'visualization/blender-case-revision-7/quality-model-sources/rear-quality/build_rear_quality.py'
node=next(n for n in ast.parse(legacy.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='face_colors')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(legacy),'exec'));face_colors(out,[list(c) for _,s,c in features for _ in s.Solids])
out.write_text('\n'.join(l.rstrip() for l in out.read_text().splitlines())+'\n');saved=Part.Shape();saved.read(str(out))
check('Saved STEP has four valid positive solids',saved.isValid() and len(saved.Solids)==4 and all(s.Volume>0 for s in saved.Solids))
for i in range(3):
 delta=stock.Solids[i].cut(saved.Solids[i]).Volume+saved.Solids[i].cut(stock.Solids[i]).Volume
 check('Saved original LED part'+str(i+1)+' retained exactly',delta<1e-8,changed_volume_mm3=delta)
check('Spacer touches LED underside without overlap',spacer.distToShape(stock.Solids[0])[0]<1e-7)
check('Original LED vertical assembly bounds retained',max(abs(getattr(stock.BoundBox,k)-getattr(saved.BoundBox,k)) for k in ['ZMin','ZMax'])<1e-7)
doc.saveAs(str(H/'LED5mm_STD240B_WithSpacer.FCStd'));App.closeDocument(doc.Name)
check('Active board and saved scene inputs unchanged',guards=={p:sha(Path(p)) for p in guards})
report={'passed':True,'check_count':len(checks),'checks':checks,'model':out.name,'model_sha256':sha(out),'previous_model_sha256':sha(old),'source':{'file':'sources/vcc-std-series-datasheet.pdf','sha256':sha(pdf),'drawing':'STDxxxBLK_A rev001,2010-02-25','url':'https://www.alldatasheet.com/datasheet-pdf/pdf/606962/VCC/STD240BLK.html','retrieval':'User saved STD.PDF; preserved byte-for-byte'},'catalog':{'file':'sources/vcc-mouser-catalog-646-page178.pdf','sha256':sha(catalog),'url':'https://www.mouser.com/catalog/catalogusd/646/178.pdf'},'datum_resolution':'VCC section A-A specifies XXX as total length to bottom of end lands. STD240=6.096mm total; no LED lift required. The older catalog arrow visually excludes feet and is superseded by the detailed drawing.','dimensions_mm':{'total_length':height,'outside_diameter':5.08,'lead_pitch':2.54,'two_lead_hole_diameter':.914,'four_longitudinal_hole_diameter':1.194,'four_hole_xy_offsets':[1.27,1.27],'recess_top_diameter':4.064,'recess_bottom_diameter':3.226,'recess_depth':depth,'end_land_height':end},'limitations':['Independent drawing-derived illustration, not manufacturer CAD or exact historical fitted part','Central third-lead bore diameter, end-land outer radii and detailed retention tabs are unsized; central bore/end lands illustrated and compliant tabs omitted','Original BOM0.24-inch versus sequencer0.22-inch conflict persists; existing selected0.24-inch datum retained','Generic LED package and fitted material/tolerances remain unqualified'],'physical_fit_qualified':False}
(H/'installed-spacer-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'check_count':len(checks),'sha256':sha(out)},indent=2))
