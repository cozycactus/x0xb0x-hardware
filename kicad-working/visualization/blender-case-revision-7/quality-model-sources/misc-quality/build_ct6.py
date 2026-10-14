from pathlib import Path
import sys,math,json,hashlib,copy
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part,Import,MeshPart
from step_colors import add_step_face_colors
H=Path(__file__).resolve().parent;V=App.Vector
BLUE=(.035,.22,.51);IVORY=(.84,.85,.80);METAL=(.62,.64,.67)
def box(a,b,c,x,y,z):return Part.makeBox(a,b,c,V(x,y,z))
def cyl(r,h,x,y,z):return Part.makeCylinder(r,h,V(x,y,z))
def fuse(xs):
 s=xs[0]
 for x in xs[1:]:s=s.fuse(x)
 return s.removeSplitter()
# Exact7mm body envelope; drawing-based0.45mm corner rounds.
r=.45
base=fuse([box(7-2*r,7,5.45,-3.5+r,-3.5,0),box(7,7-2*r,5.45,-3.5,-3.5+r,0)]+[cyl(r,5.45,x,y,0) for x in [-3.5+r,3.5-r] for y in [-3.5+r,3.5-r]])
base=base.cut(cyl(2.96,1.5,0,0,4.15))
# Corner snap-lug grooves visible in the outline; widths/heights unsized.
for x in [-3.5,2.35]:
 for y in [-3.5,2.35]:base=base.cut(box(1.15,1.15,.4,x,y,4.45))
lugs=fuse([box(.75,.95,.2,x,y,5.45) for x in [-3.25,2.5] for y in [-3.05,2.10]])
label=box(5.3,.85,.12,-2.65,-3.2,5.45)
# Twelve teeth follow the drawing; their unsized radii/angles are reconstruction.
rotor=cyl(2.14,1.65,0,0,4.15)
teeth=[]
for i in range(12):
 a=2*math.pi*i/12
 pts=[]
 for rad,delta in [(2.05,-.13),(2.8,-.105),(2.8,.105),(2.05,.13)]:pts.append(V(rad*math.cos(a+delta),rad*math.sin(a+delta),4.95))
 teeth.append(Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,.85)))
rotor=fuse([rotor]+teeth)
# The only published slot dimensions:0.6W x2.6L x1.6D.
slot=box(2.6,.6,1.6,-1.3,-.3,4.2).fuse(box(.6,2.6,1.6,-.3,-1.3,4.2))
rotor=rotor.cut(slot)
# Published0.45mm nominal leads,5x2.5mmgrid, untrimmed7mm nominal length.
leads=fuse([cyl(.225,7,x,y,-7) for x,y in [(-2.5,0),(0,-2.5),(2.5,0)]])
features=[('MoldedHousing',base,BLUE),('CornerLugs',lugs,BLUE),('ResistanceLabelPanel',label,BLUE),('SlottedAdjustmentRotor',rotor,IVORY),('NominalUntrimmedLeads',leads,METAL)]
doc=App.newDocument('CT6EP_Detailed');objs=[]
for name,s,c in features:
 assert s.isValid() and s.Volume>0,name
 ob=doc.addObject('PartDesign::Feature',name);ob.Shape=s;objs.append(ob)
doc.recompute();step=H/'CT6EP_DatasheetDetailed.step';Import.export(objs,str(step));add_step_face_colors(step,features)
allshape=Part.makeCompound([s for _,s,_ in features]);re=Part.read(str(step));assert re.isValid();assert abs(re.Volume-allshape.Volume)<1e-5
segments=[]
for name,s,c in features:
 p=H/('CT6EP_DatasheetDetailed_'+name+'.stl');MeshPart.meshFromShape(Shape=s,LinearDeflection=.025,AngularDeflection=.12,Relative=False).write(str(p));segments.append({'name':name,'stl':str(p),'color_rgb':c,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
MeshPart.meshFromShape(Shape=allshape,LinearDeflection=.025,AngularDeflection=.12,Relative=False).write(str(H/'CT6EP_DatasheetDetailed.stl'))
limits=['Manufacturer CT6EP drawing supplies7x7x5.8mm envelope,0.6x2.6x1.6mm crossslot,0.45mm leads,5x2.5mm lead grid and7+/-2mm untrimmed length. Current Nidec/Copal family is not proven identical to original Vishay-supplied historical stock.','Housing radii, seam/lug positions, label-panel relief and rotor/tooth dimensions are interpreted from the unsized outline; not factory CAD. Resistance and production date are not invented.','The canonical origin and native assignment transform are unchanged. Body seated atZ0 is an installed-height assumption. Leads are manufacturer nominal untrimmed length; actual soldered trim length is unknown.','Nominal lead grid differs from original board5.08x2.54 by0.04mm peraxis. Nominal drill1.0mm minus lead0.45mm permits this nominal centre mismatch; tolerance and real formed-lead seating are not qualified.','No part body was reduced or moved to fit the case. This visual model is not physical assembly or fabrication qualification.']
prior=json.loads((H.parent.parent/'models-review-7/combined-model-plan.json').read_text());rows=[]
for old in prior['assignments']:
 if 'CT6EP_' in old['source_model']:
  row={k:copy.deepcopy(old[k]) for k in ['board','references','footprint','offset_mm','scale','rotation_deg']};row.update(source_model=str(step),source_sha256=hashlib.sha256(step.read_bytes()).hexdigest(),source_kind='Original CC0 parametric reconstruction from manufacturer CT6EP drawing',classification='Detailed datasheet-derived CT6EP family model with nominal untrimmed leads',limitations=limits,source_urls=['https://www.nidec-components.com/e/catalog/trimmer/ct-6.pdf','https://ladyada.net/make/x0xb0x/fab/parts.html']);rows.append(row)
b=re.BoundBox
report={'assignments':rows,'parts':[{'id':'CT6EP_DatasheetDetailed','step':str(step),'segments':segments,'published_dimensions_mm':{'body':[7,7,5.8],'slot':[.6,2.6,1.6],'lead_diameter':.45,'lead_length_nominal':7,'lead_grid':[5,2.5]},'geometry_audit':{'valid':True,'solids':len(re.Solids),'faces':len(re.Faces),'volume_mm3':re.Volume,'bounds_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],'roundtrip_volume_difference_mm3':re.Volume-allshape.Volume},'limitations':limits}]}
(H/'misc-quality-manifest.json').write_text(json.dumps(report,indent=2)+'\n');doc.saveAs(str(H/'CT6EP_DatasheetDetailed.FCStd'));print(json.dumps(report['parts'][0]['geometry_audit']))
