"""BOM-grounded connector BODY illustrations, with no leads or locators.

Canonical coordinates are original F.Cu footprint(X,-Y,Z-outward), in mm.
These are dimension-preserving visualization reconstructions, not component
CAD qualified against historical pin holes or mechanical tolerances.
"""
from pathlib import Path
import json,math,re,hashlib,shutil
import FreeCAD as App
import Part,MeshPart
ROOT=Path('/Users/ruslanmigirov/Downloads/hardware')
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'source';SOURCE.mkdir(exist_ok=True)
V=App.Vector

def box(w,d,h,x=None,y=0,z=0):
 return Part.makeBox(w,d,h,V(-w/2 if x is None else x,y,z))
def y_cylinder(radius,length,y,z,direction=1,x=0):
 return Part.makeCylinder(radius,length,V(x,y,z),V(0,direction,0))
def xz_prism(points,y,length):
 pts=[V(x,y,z) for x,z in points]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,length,0))
def fuse(shapes):
 result=shapes[0]
 for s in shapes[1:]:result=result.fuse(s)
 return result.removeSplitter()
def cut(shape,tool):return shape.cut(tool).removeSplitter()

# Five-pin DIN. Printed envelope20W x15.8maxD x21.1H, flange1.8mm.
# Rear cylinder/low web and face recess are generalized inside that envelope.
din_flange=box(20,1.8,21.1)
din_rear=y_cylinder(9,14,1.8,9)
din=fuse([din_flange,din_rear,box(15,14,2,y=1.8)])
din=cut(din,y_cylinder(7.1,9,-.1,10))
# Keep a recessed socket face at6mm depth, with five holes on printed7mmPCD.
socket=y_cylinder(6.7,1.4,6,10)
for angle in [0,45,90,135,180]:
 a=math.radians(angle);socket=cut(socket,y_cylinder(.65,1.6,5.9,10-3.5*math.sin(a),x=3.5*math.cos(a)))
din=fuse([din,socket])
# Manufacturer specifies3x1.6mm holes on19mm circle; these are flange holes,
# not leads/locators, and retain that printed pattern.
for angle in [90,210,330]:
 a=math.radians(angle);din=cut(din,y_cylinder(.8,2,-.1,10+9.5*math.sin(a),x=9.5*math.cos(a)))

# MJ-3536N current-family housing envelope. Internal jack mechanism omitted.
mj=box(10,15.8,10)
mj=cut(mj,y_cylinder(1.8,4,-.1,5.5))
# A shallow top recess is an explicit unsized illustration detail.
mj=cut(mj,box(6.6,11.3,2.1,y=4.5,z=8.0))
mj_bushing=cut(y_cylinder(3,3,-3,5.5),y_cylinder(1.8,3.2,-3.1,5.5))

# PJ-202AH footprint's local+KiCadY points into the body, hence negativeCADY.
# Preserve9x14.4x11mm; rounded rear cover is a generalized exterior detail.
pj_front=box(9,3.5,11,y=-3.5)
pj_rear=fuse([box(9,10.9,6.5,y=-14.4),y_cylinder(4.5,10.9,-14.4,6.5)])
pj=fuse([pj_front,pj_rear])
pj=cut(pj,y_cylinder(3.25,9.1,.1,6.5,direction=-1))
pj_pin=y_cylinder(1,7.8,-1.1,6.5,direction=-1)

# REAN NYS216: current family housing rear24.5mm + front bushing8.5mm=33mm.
# Keep the maximum front-envelope16.5mm height. Exact historical lead positions
# are not represented. Top cross slots are generalized from family appearance.
nys=box(20,24.5,16.5)
for y in [5.0,11.4,17.8]:nys=cut(nys,box(16,2.3,6.7,y=y,z=10))
nys_bushing=y_cylinder(5.5,8.5,-8.5,8)
nys=fuse([nys,nys_bushing])
nys=cut(nys,y_cylinder(3.2,12,-8.6,8))

# Generic USB-B using original BOM154-2442-E envelope, rather than asserting
# PN61729 lead compatibility. Shape/opening/chamfers are illustrative.
w,d,h=12.04,16.0,10.62
outer=box(w,d,h)
# Chamfered Type-B opening: use the drawing's7.78W x8.45H face aperture.
aperture=[(-4.225,1.42),(4.225,1.42),(4.225,7.20),(2.225,9.20),(-2.225,9.20),(-4.225,7.20)]
usb_shell=cut(outer,xz_prism(aperture,-.05,10.6))
# Leave a nominal0.38mm stamped shell around a rear insert, with a visibly
# recessed white insulator. Its unprinted internal detail is illustrative.
usb_shell=cut(usb_shell,box(w-.76,d-.8,h-.76,y=.4,z=.38))
usb_insert=box(w-.9,d-1.6,h-.9,y=1.2,z=.45)
usb_insert=cut(usb_insert,xz_prism(aperture,1.19,8.6))
usb_tongue=box(4.0,9.2,2.1,y=1.3,z=4.2)
usb_insert=fuse([usb_insert,usb_tongue])

SOURCE_FILES={
 'mj3536n':ROOT/'kicad-working/validation/reference-pdfs/mj-3536n.pdf',
 'pj202ah':ROOT/'kicad-working/validation/reference-pdfs/pj-202ah.pdf',
 'sds50j':ROOT/'kicad-working/visualization/blender-case-revision-2/bom-parts/sds-j.pdf',
 'nys216':ROOT/'kicad-working/validation/models-review-5/connector-models/nys216.pdf',
}
source_records=[]
for key,p in SOURCE_FILES.items():
 target=SOURCE/(key+'.pdf');shutil.copy2(p,target)
 source_records.append({'id':key,'filename':str(target.relative_to(HERE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})

ep=SOURCE/'kc-301021-web-extract.json'
if ep.exists():source_records.append({'id':'usb-bom-web-text','filename':str(ep.relative_to(HERE)),'sha256':hashlib.sha256(ep.read_bytes()).hexdigest(),'bytes':ep.stat().st_size,'url':'https://www.mouser.com/catalog/specsheets/KC-301021.pdf','retrieval':'indexed primaryPDFtext; localPDFbinary not recovered'})

s=(ROOT/'kicad-working/ioboard/ioboard.kicad_pcb').read_text()
starts=[m.start() for m in re.finditer(r'\n\t\(footprint ',s)]+[len(s)]
poses={}
for a,b in zip(starts,starts[1:]):
 f=s[a:b];m=re.search(r'\(property "Reference" "([^"]+)"',f)
 if not m:continue
 at=re.search(r'\n\t\t\(at ([^\)]+)\)',f)
 if not at:continue
 values=list(map(float,at.group(1).split()));x,y=values[:2];angle=values[2] if len(values)>2 else 0
 poses[m.group(1)]={'reference':m.group(1),'footprint':re.search(r'footprint "([^"]+)',f).group(1),'pcb_xy_mm':[x,y],'angle_degrees':angle,'native_translation_mm':[x,-y,1.595],'native_rotation_about_z_degrees':angle}

COMMON=[
 'Body-only visual illustration; terminals and locators omitted, not fit qualified.',
 'Published nominal body envelope retained at scale1. No shrinking to satisfy pads or enclosure clearance.',
 'All solder terminals, board locators and mounting pegs omitted; no historical pin-fit or toleranced seating assertion.',
 'Internal details, small fillets and some recesses are generalized. Exact historical manufactured variant remains unverified.',
]
parts=[];shapes_by_id={};doc=App.newDocument('RearBodyIllustrations')
def add(key,shape,refs,identity,dims,material,color,urls,source_ids,limits,role='housing',status='current-family body illustration'):
 shape=shape.removeSplitter()
 shapes_by_id[key]=shape
 if not shape.isValid():raise RuntimeError(key+' invalid')
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.08,AngularDeflection=.12,Relative=False)
 filename=key+'.stl';mesh.write(str(HERE/filename))
 o=doc.addObject('PartDesign::Feature',key.replace('-','_'));o.Shape=shape;o.Label=key
 bb=shape.BoundBox
 parts.append({'id':key,'board':'ioboard','references':refs,'filename':filename,'path':str(HERE/filename),'format':'stl','units':'mm','classification':status,'identity':identity,'role':role,
 'canonical_frame':{'x':'original footprintX','y':'negative original footprintY','z':'outward from F.Cu body seating plane','origin':'original footprintXY origin at nominal body seating plane','unit':'mm'},
 'instance_poses':[poses[r] for r in refs],
 'body_orientation_offset_override':{'translation_mm':[0,0,0],'rotation_degrees':[0,0,0],'scale':[1,1,1]},
 'dimensions_mm':dims,'source_urls':urls,'source_ids':source_ids,
 'material_suggestion':material,'color_srgb':color,'limitations':COMMON+limits,
 'mesh_validation':{'shape_valid':shape.isValid(),'solid_count':len(shape.Solids),'triangles':mesh.CountFacets,'volume_mm3':shape.Volume,'bounds_mm':{'min':[bb.XMin,bb.YMin,bb.ZMin],'max':[bb.XMax,bb.YMax,bb.ZMax]}},
 'sha256':hashlib.sha256((HERE/filename).read_bytes()).hexdigest()})
BOM='https://ladyada.net/make/x0xb0x/fab/parts.html'
add('sds50j-body',din,['DIN1','DIN2','DIN3','DIN4'],'CUI/Same Sky SDS-50J; historical distributor CP-2350',{'width':20,'depth_max':15.8,'height':21.1,'flange_thickness':1.8,'body_rear_height':18,'socket_axis_height':10,'contact_pcd':7},'black PBT/PE',[.035,.035,.04,1],[BOM,'https://www.sameskydevices.com/product/resource/sds-j.pdf'],['sds50j'],['Rear cylinder and face recess diameter14.2mm are unsized exterior approximations; printed20x15.8x21.1mm envelope preserved.','Three1.6mm flange holes use printed19mm mounting circle; this diameter is not mistaken for the mating aperture.','Five front socket holes are illustrative1.3mm openings on printed7mmPCD; no contact/lead-fit claim.'])
add('mj3536n-housing',mj,['CV0','GATE0'],'Historical MJ-CP3536N; current MJ-3536N reference',{'body_width':10,'body_depth':15.8,'body_height':10,'socket_axis_height':5.5},'black PBT',[.025,.027,.03,1],[BOM,'https://www.sameskydevices.com/product/resource/mj-3536n.pdf'],['mj3536n'],['Housing front nominally at canonicalY0, matching historical outline; current family terminal/body offsets not qualified.','Shallow top recess is generalized; current-family full10x15.8x10mm housing envelope retained.'])
add('mj3536n-bushing',mj_bushing,['CV0','GATE0'],'MJ-3536N nickel plated brass bushing',{'outer_diameter':6,'bore_diameter':3.6,'projection':3,'socket_axis_height':5.5},'nickel plated brass',[.48,.5,.52,1],[BOM,'https://www.sameskydevices.com/product/resource/mj-3536n.pdf'],['mj3536n'],['No mounting nut implied. Full3mm bushing projection is retained even if scene seating requires review.'],role='bushing')
add('pj202ah-housing',pj,['POWER0'],'CUI/Same Sky PJ-202AH',{'width':9,'depth':14.4,'height':11,'socket_axis_height':6.5,'bore_diameter':6.5,'insertion_depth':9},'black PBT',[.025,.027,.03,1],[BOM,'https://www.sameskydevices.com/product/resource/pj-202ah.pdf'],['pj202ah'],['Canonical body extends toward negativeY because the original footprint body is drawn in positiveKiCadY; actualPOWER0 angle180 must be applied.','Rounded rear cover geometry generalized within full9x14.4x11mm envelope.'])
add('pj202ah-center-pin',pj_pin,['POWER0'],'PJ-202AH center pin',{'pin_diameter':2,'illustrative_visible_length':7.8,'socket_axis_height':6.5},'nickel plated copper',[.52,.54,.56,1],[BOM,'https://www.sameskydevices.com/product/resource/pj-202ah.pdf'],['pj202ah'],['2mm pin diameter is printed; axial start/end are an illustration of the9mm insertion cavity, not mechanical tolerances.'],role='center pin')
add('nys216-body',nys,['HEADPHONE0','MIXIN0','MIXOUT0'],'REAN/Neutrik NYS216 current family',{'body_width':20,'body_height_max':16.5,'body_depth_to_shoulder':24.5,'front_bushing_projection':8.5,'overall_depth':33,'bushing_major_diameter':11,'socket_axis_height':8},'black PA6 +30percentGF',[.035,.035,.037,1],[BOM,'https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1'],['nys216'],['Full33mm overall axial length retained:24.5mm rear housing plus8.5mm bushing.','Current drawing also shows15.5mm side height; this illustration conservatively preserves16.5mm maximum front housing envelope.','Top slots and6.4mm bore are generalized. Nut/washer are omitted because exterior hardware is a separate existing scene illustration.','Historical asymmetric pad rows and current lead offsets are intentionally not represented.'])
usb_urls=[BOM,'https://www.mouser.com/catalog/specsheets/KC-301021.pdf']
usb_limits=['Generic TypeB body using originalBOM Kobiconn154-2442-E dimensions, not an exactPN61729 asset.','BOM drawing envelope12.04x16.00x10.62mm and aperture7.78x8.45mm were recovered as primaryPDF text viaweb/Firecrawl; localdownload returnedHTML access page.','Nominal0.38mm shell gauge, chamfer outline, tongue and internal seating are illustrative; no lead compatibility asserted.']
add('usb-typeb-shell',usb_shell,['USB0'],'Generic USB-B / original BOM Kobiconn154-2442-E',{'width':12.04,'depth':16,'height':10.62,'aperture_width':8.45,'aperture_height':7.78},'tin plated copper alloy',[.55,.57,.6,1],usb_urls,['usb-bom-web-text'],usb_limits,role='metal shell',status='generic BOM-family body illustration; PN61729 fit unqualified')
add('usb-typeb-insulator',usb_insert,['USB0'],'Generic USB-B white insulator',{'body_envelope_width':12.04,'body_envelope_depth':16,'body_envelope_height':10.62,'internal_shape':'generalized'},'white glass-filled PBT',[.82,.82,.76,1],usb_urls,['usb-bom-web-text'],usb_limits,role='insulator',status='generic BOM-family body illustration; internal shape approximate')

doc.recompute();doc.saveAs(str(HERE/'rear-body-illustrations.FCStd'))
manifest={'schema_version':1,'units':'mm','scope':'Separate full body illustrations for all11 rear connector instances. No PCB/GLB/scene edits by generator; body-only STEP assignment recommendations included.',
 'board_mount_z_mm':1.595,'footprint_pose_rule':'Root applies T(pcbX,-pcbY,1.595)*Rz(actual angle). STL geometry already uses original footprint(X,-Y,Z-outward).',
 'parts':parts,'sources':source_records,'PCB_source_sha256':hashlib.sha256((ROOT/'kicad-working/ioboard/ioboard.kicad_pcb').read_bytes()).hexdigest(),
 'unique_reference_count':len({r for p in parts for r in p['references']}),'body_only':True,'physical_fit_qualified':False,
 'replace_or_dedupe_existing_face_proxies':'These assets include the housing front/bushing. Existing rearface presentation proxies can overlap; root should hide corresponding duplicate face disks/bushings while retaining separately illustratedNYS nuts/washers if desired.'}
# Add AP214 solid appearance to body-only STEP exports. This adds standard
# presentation entities only; all BRep geometry is exported by OpenCascade.
def colored_step(shape,path,palette):
 shape.exportStep(str(path))
 data=path.read_text()
 solids=re.findall(r'#(\d+)\s*=\s*MANIFOLD_SOLID_BREP',data)
 context=re.search(r'#(\d+)\s*=\s*\(\s*GEOMETRIC_REPRESENTATION_CONTEXT',data).group(1)
 if len(solids)!=len(palette):raise RuntimeError('STEP solid/color count mismatch')
 next_id=max(map(int,re.findall(r'#(\d+)',data)))+1
 entities=[];styled=[]
 for solid,color in zip(solids,palette):
  i=next_id;next_id+=8
  entities += [f"#{i}=COLOUR_RGB('',{color[0]},{color[1]},{color[2]});",
   f"#{i+1}=FILL_AREA_STYLE_COLOUR('',#{i});",
   f"#{i+2}=FILL_AREA_STYLE('',(#{i+1}));",
   f"#{i+3}=SURFACE_STYLE_FILL_AREA(#{i+2});",
   f"#{i+4}=SURFACE_SIDE_STYLE('',(#{i+3}));",
   f"#{i+5}=SURFACE_STYLE_USAGE(.BOTH.,#{i+4});",
   f"#{i+6}=PRESENTATION_STYLE_ASSIGNMENT((#{i+5}));",
   f"#{i+7}=STYLED_ITEM('',(#{i+6}),#{solid});"]
  styled.append('#'+str(i+7))
 entities.append(f"#{next_id}=MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({','.join(styled)}),#{context});")
 pos=data.rfind('ENDSEC;')
 path.write_text(data[:pos]+'\n'+'\n'.join(entities)+'\n'+data[pos:])
 # Re-import to confirm the styled STEP remains valid and preserves its solids.
 check=Part.Shape();check.read(str(path))
 if not check.isValid() or len(check.Solids)!=len(shape.Solids):raise RuntimeError('STEP round-trip invalid')
 return hashlib.sha256(path.read_bytes()).hexdigest()
for part in parts:
 step_path=HERE/(part['id']+'.step');shape=shapes_by_id[part['id']]
 part['step_filename']=step_path.name;part['step_path']=str(step_path)
 part['step_sha256']=colored_step(shape,step_path,[part['color_srgb'][:3]]*len(shape.Solids))
groups=[('SDS50J','CP-2350',['sds50j-body']),
        ('MJ3536N','MJ-3536N',['mj3536n-housing','mj3536n-bushing']),
        ('PJ202AH','PJ-202AH',['pj202ah-housing','pj202ah-center-pin']),
        ('NYS216','REAN_1_4STERO',['nys216-body']),
        ('USB_TypeB','PN61729',['usb-typeb-shell','usb-typeb-insulator'])]
assignments=[]
for key,footprint,ids in groups:
 pp=[p for p in parts if p['id'] in ids]
 combined=Part.makeCompound([shapes_by_id[i] for i in ids])
 palette=[p['color_srgb'][:3] for p in pp for solid in shapes_by_id[p['id']].Solids]
 step_path=HERE/(key+'-body-illustration.step')
 digest=colored_step(combined,step_path,palette)
 assignments.append({'board':'ioboard','references':pp[0]['references'],'footprint':footprint,
  'source_model':str(step_path),'source_sha256':digest,'offset_mm':[0,0,0],
  'scale':[1,1,1],'rotation_deg':[0,0,0],
  'source_kind':'Parametric nominal body illustration reconstructed from originalBOM/current manufacturer drawings; no terminals or locators',
  'classification':'body-only visual illustration; terminals and locators omitted, not fit qualified',
  'limitations':list(dict.fromkeys(v for p in pp for v in p['limitations'])),
  'source_urls':list(dict.fromkeys(v for p in pp for v in p['source_urls'])),
  'canonical_frame':pp[0]['canonical_frame'],'part_ids':ids,
  'color_entities':'AP214 styled solid colors; BRep geometry round-trip valid',
  'solid_count':len(combined.Solids)})
manifest['assignments']=assignments
(HERE/'rear-body-illustrations-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'part_files':len(parts),'references':manifest['unique_reference_count'],'all_valid':all(p['mesh_validation']['shape_valid'] for p in parts),'triangles':sum(p['mesh_validation']['triangles'] for p in parts),'manifest':str(HERE/'rear-body-illustrations-manifest.json')},indent=2))
