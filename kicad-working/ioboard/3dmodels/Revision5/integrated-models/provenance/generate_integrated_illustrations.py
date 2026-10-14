#!/usr/bin/env python3
"""Original CC0 package illustrations; dimensions and choices are explicit.

Run with the bundled FreeCAD Python. These are parametric illustrations using
primary package dimensions, not copied manufacturer CAD or fitted-part proof.
SPDX-License-Identifier: CC0-1.0
"""
import sys,json,hashlib,math
from pathlib import Path
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];V=App.Vector
helper=HERE/'step_colors.py'
from step_colors import set_step_colors
sys.path.insert(0,str(WORK.parent/'kicad-import/validation'))
from verify_native_projects import parse_sexpr,children,one,property_value

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def body_profile_xz(points,y0,depth):
    points=[V(x,y0,z) for x,z in points]
    return Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(0,depth,0))
def body_profile_yz(points,x0,width):
    points=[V(x0,y,z) for y,z in points]
    return Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(width,0,0))
def box_lead(x,width,thickness,bottom,top):
    return Part.makeBox(width,thickness,top-bottom,V(x-width/2,-thickness/2,bottom))
def fanned_round_lead(x0,x1,bottom_body,diameter):
    top=V(x0,0,bottom_body+.12);start=V(x0,0,2.35)
    end=V(x1,0,.45);tail=V(x1,0,-2.5)
    curve=Part.BezierCurve();curve.setPoles([start,V(x0,0,1.8),V(x1,0,1.1),end])
    wire=Part.Wire([Part.makeLine(top,start),curve.toShape(),Part.makeLine(end,tail)])
    section=Part.Wire(Part.makeCircle(diameter/2,top,V(0,0,1)))
    shape=wire.makePipeShell([section],True,False)
    assert shape.isValid() and len(shape.Solids)==1
    return shape,wire.Length

specs=[
 dict(name='SIP9_LA4140_3017C_MaxBody_P2.54_Illustration',board='mainboard',footprint='SIP9',refs=['IC14'],kind='LA4140',
      body_mm=[22.3,3.0,5.7],body_dimension_basis=['printed22.3','printed3.0','maximum5.7'],standoff=.7,pitch=2.54,
      lead_section_mm=[.5,.25],tail=-2.5,body_y_bounds=[-1.65,1.35],front_pin_order=[str(i) for i in range(1,10)],
      source='../mainboard-review-2/reference-documents/LA4140-SANYO-alternative.pdf',
      source_url='https://static.chipdip.ru/lib/301/DOC000301904.pdf',
      document='Sanyo ENN528D page1,3017C-SIP9; retained alternative has legible dimension font',
      assumptions=['Body uses printed22.3×3.0 and maximum5.7mm envelope.','0.7mm mounting standoff and2.5mm cut tail are illustration choices.','Lead section0.50×0.25mm has no printed tolerance/maxima.','Front face points toward negative modelY; pin1 is negativeX.','Drafts, exact shoulders and printed markings are simplified.']),
 dict(name='SIP9_BA6110_NominalBody_P2.54_Illustration',board='mainboard',footprint='SIP9',refs=['IC15B0'],kind='BA6110',
      body_mm=[21.8,2.8,5.8],body_dimension_basis=['nominal±0.2','nominal±0.2','nominal±0.2'],standoff=1.2,pitch=2.54,
      lead_section_mm=[.6,.4],tail=-3.5,body_y_bounds=[-1.4,1.4],front_pin_order=[str(i) for i in range(1,10)],
      source='../mainboard-review-2/reference-documents/BA6110-ROHM-DSA003839.pdf',
      source_url='https://datasheet.datasheetarchive.com/originals/library/Datasheet-0103/DSA003839.pdf',
      document='ROHM BA6110/BA6110FS page7,SIP9',
      assumptions=['Body uses nominal21.8×2.8×5.8mm; each drawing tolerance±0.2mm.','1.2mm shoulder-to-board mounting interpretation and3.5mm tail give nominal10.5mm total from tip to top.','Lead lower width0.6mm has no tolerance;0.4mm thickness is printed0.3±0.1 maximum.','Front face points toward negative modelY; pin1 is negativeX.','Body drafts, shoulder flare, top groove and printed markings are simplified.']),
 dict(name='SSIP5_2SC1583_MaxBody_FannedP2.286_Illustration',board='mainboard',footprint='SSIP5',refs=['Q12','Q21','Q26'],kind='2SC1583',
      body_mm=[8.1,3.6,5.6],body_dimension_basis=['maximum','maximum','maximum'],standoff=2.8,pitch=2.286,native_pitch=1.25,
      lead_diameter=.45,tail=-2.5,body_y_bounds=[-2.2,1.4],front_pin_order=['1/B1','2/C1','3/E','4/C2','5/B2'],
      source='reference/2SC1583-Mitsubishi.pdf',source_url='https://www.radioradar.net/en/files.html?fid=502807',
      document='Original Japanese Mitsubishi Semiconductor2SC1583 datasheet,page1',
      assumptions=['Body uses maximum8.1×3.6×5.6mm envelope,not exact selected part.','Native lead pitch is1.25mm. Five0.45mm round leads are explicitly fanned to existing2.286mm PCB pitch above the board.','2.8mm body standoff,Bezier lead bends and2.5mm cut tails are mounting illustrations.','Drawing supplies10.5mm minimum uncut lead length; illustration shows trimmed formed leads.','Front flat face is negativeY; sloped rear top is positiveY. Lead row is1.4mm from rear edge.','No dimensions or model are borrowed for2SC2291.']),
 dict(name='Resonator_AWCR6MD_MaxBody_P2.54_Illustration',board='ioboard',footprint='Resonator_6MHz_x0x',refs=['XTL2'],kind='AWCR6',
      body_mm=[9.5,4,6.5],body_dimension_basis=['maximum','maximum','maximum'],standoff=.35,pitch=2.54,
      lead_section_mm=[.6,.35],tail=-2.5,front_pin_order=['3','2/GND','1'],rotation_deg=[0,0,0],
      source='../reference-pdfs/awcr-md.pdf',source_url='https://media.digikey.com/pdf/Data%20Sheets/Abracon%20Corp%20PDFs/AWCR_MD.pdf',
      document='Abracon AWCR-MD,revised2013-05-07,page3,1.79–6MHz low-profile bulk',
      assumptions=['Body uses maximum9.5×4×6.5mm envelope.','Exact PCB pitch2.54mm lies within manufacturer2.5±0.3mm range.','Lead section uses printed maxima0.5±0.1 by0.25±0.1mm.','0.35mm body standoff,2.5mm cut tails,rounded corners and blue color are illustration choices.','Manufacturer front view has pin3 negativeX,pin2 center,pin1 positiveX; matchesXTL2P$3/P$2/P$1.']),
 dict(name='Resonator_AWCR16MD_MaxBody_P2.54_Illustration',board='mainboard',footprint='2SC2021',refs=['XTL1'],kind='AWCR16',
      body_mm=[10,5,10],body_dimension_basis=['maximum','maximum','maximum'],standoff=.35,pitch=2.54,
      lead_section_mm=[.6,.35],tail=-2.5,front_pin_order=['3','2/GND','1'],rotation_deg=[0,0,180],
      source='../reference-pdfs/awcr-md.pdf',source_url='https://media.digikey.com/pdf/Data%20Sheets/Abracon%20Corp%20PDFs/AWCR_MD.pdf',
      document='Abracon AWCR-MD,revised2013-05-07,page3,13.01–60MHz bulk; original BOM815-AWCR-16.00MD',
      assumptions=['Body uses maximum10×5×10mm envelope for16MHz.','Exact PCB pitch2.54mm lies within manufacturer2.5±0.3mm range.','Lead section uses printed maxima0.5±0.1 by0.25±0.1mm.','0.35mm body standoff,2.5mm cut tails,rounded corners and blue color are illustration choices.','Manufacturer front has pin1 positiveX; serializedZ180places it on sourceXTL1pad1 negativeX. Middle pin2 remainsGND.'])
]

records=[];assignments=[]
for spec in specs:
    w,d,h=spec['body_mm'];standoff=spec['standoff'];top=standoff+h
    if spec['kind']=='LA4140':
        body=body_profile_xz([(-w/2,standoff),(w/2,standoff),(w/2,top),(-w/2+1.5,top),(-w/2,top-1)],spec['body_y_bounds'][0],d)
    elif spec['kind']=='2SC1583':
        ymin,ymax=spec['body_y_bounds']
        body=body_profile_yz([(ymin,standoff),(ymax,standoff),(ymax,top-2),(ymax-2,top),(ymin,top)],-w/2,w)
    else:
        body=Part.makeBox(w,d,h,V(-w/2,-d/2,standoff))
        if spec['kind'].startswith('AWCR'):
            edges=[e for e in body.Edges if len(e.Vertexes)==2 and abs(e.Vertexes[0].Point.x-e.Vertexes[1].Point.x)<1e-8 and abs(e.Vertexes[0].Point.z-e.Vertexes[1].Point.z)<1e-8]
            body=body.makeFillet(1.15 if spec['kind']=='AWCR6' else 1.5,edges)
    n=9 if spec['kind'] in ['LA4140','BA6110'] else 5 if spec['kind']=='2SC1583' else 3
    positions=[(i-(n-1)/2)*spec['pitch'] for i in range(n)]
    doc=App.newDocument(spec['name']);objects=[];colors={}
    def add(name,shape,color):
        assert shape.isValid()
        assert len(shape.Solids)==1
        shape=shape.Solids[0]
        obj=doc.addObject('Part::Feature',name);obj.Shape=shape;objects.append(obj);colors[name]=color
    add('Body',body,[.07,.075,.08] if not spec['kind'].startswith('AWCR') else[.10,.25,.65])
    lengths=[]
    for i,x in enumerate(positions):
        if spec['kind']=='2SC1583':
            shape,length=fanned_round_lead((i-2)*spec['native_pitch'],x,standoff,spec['lead_diameter']);lengths.append(length)
        else:shape=box_lead(x,*spec['lead_section_mm'],spec['tail'],standoff+.12)
        add('Lead'+str(i+1),shape,[.72,.73,.75])
    joined=objects[0].Shape
    for obj in objects[1:]:joined=joined.fuse(obj.Shape)
    assert joined.isValid() and len(joined.Solids)==1
    path=HERE/(spec['name']+'.step');Part.export(objects,str(path));presentation=set_step_colors(path,colors,objects)
    imported=Part.read(str(path));assert imported.isValid()
    section=imported.section(Part.makePlane(100,100,V(-50,-50,-1)))
    wire_records=[]
    for edges in Part.sortEdges(section.Edges):
        wire=Part.Wire(edges);b=wire.BoundBox
        points=[p for p in wire.discretize(Number=256)]+[v.Point for v in wire.Vertexes]
        center=[(b.XMin+b.XMax)/2,(b.YMin+b.YMax)/2]
        radius=max(math.hypot(p.x-center[0],p.y-center[1]) for p in points)
        wire_records.append(dict(center_mm=center,max_radius_mm=radius))
    wire_records.sort(key=lambda r:r['center_mm'][0]);assert len(wire_records)==n
    for rec,x in zip(wire_records,positions):assert math.dist(rec['center_mm'],[x,0])<1e-7
    rotation=spec.get('rotation_deg',[0,0,0]);angle=math.radians(-rotation[2])
    boardpath=WORK/spec['board']/(spec['board']+'.kicad_pcb');br=parse_sexpr(boardpath.read_text());actual=[]
    for ref in spec['refs']:
        fp=next(f for f in children(br,'footprint') if property_value(f,'Reference','reference')==ref)
        assert fp[1].split(':')[-1]==spec['footprint'] and one(fp,'layer')[1]=='F.Cu'
        pads=children(fp,'pad');assert len(pads)==n
        for p in pads:
            xy=[float(one(p,'at')[1]),-float(one(p,'at')[2])]
            transformed=[[math.cos(angle)*r['center_mm'][0]-math.sin(angle)*r['center_mm'][1],math.sin(angle)*r['center_mm'][0]+math.cos(angle)*r['center_mm'][1]] for r in wire_records]
            j=min(range(n),key=lambda j:math.dist(xy,transformed[j]));error=math.dist(xy,transformed[j]);drill=float(one(p,'drill')[1]);margin=drill/2-wire_records[j]['max_radius_mm']
            assert error<1e-7 and margin>0
            actual.append(dict(reference=ref,pin=p[1],board_drill_mm=drill,lead_center_error_mm=error,lead_radius_mm=wire_records[j]['max_radius_mm'],radial_margin_mm=margin))
    source=(HERE/spec['source']).resolve() if spec['source'].startswith('reference/') else(HERE.parents[1]/spec['source'][3:]).resolve()
    assert source.exists(),source
    rec=dict(specification=spec,source_pdf=str(source),source_pdf_sha256=sha(source),source_model=str(path),sha256=sha(path),
             original_parametric_geometry=True,license='CC0-1.0',shape_valid=True,fully_joined=True,lead_sections_z_minus_1_mm=wire_records,
             actual_board_pad_checks=actual,presentation=presentation,formed_lead_path_lengths_mm=lengths)
    records.append(rec)
    assignments.append(dict(board=spec['board'],footprint=spec['footprint'],refs=spec['refs'],source_model=str(path),sha256=sha(path),
                            offset_mm=[0,0,0],rotation_deg=rotation,scale=[1,1,1],classification='original_parametric_package_illustration_primary_dimensions_exact_board_pitch',
                            source_kind='original project-generated CC0 illustration',license='CC0-1.0',sources=[dict(url=spec['source_url'],document=spec['document'],local_pdf=str(source),sha256=sha(source))],
                            limits=spec['assumptions']+['Not manufacturer CAD,exact fitted-part geometry,tolerance analysis or fabrication/assembly approval.'],
                            source_face_and_pin_order=spec['front_pin_order'],per_instance_override=spec['footprint'] in ['SIP9','SSIP5']))
    App.closeDocument(doc.Name)

unsupported=[dict(board='mainboard',footprint='SIP9',refs=['IC15A0'],part='BA662A optional VCA',reason='No authoritative part-specific package drawing recovered; population choice remains unchanged.'),
             dict(board='mainboard',footprint='SSIP5',refs=['Q22'],part='2SC2291',reason='No primary-authored package dimensions recovered; do not borrow2SC1583body dimensions merely because both useSSIP5.')]
(HERE/'integrated-model-records.json').write_text(json.dumps(dict(generator=Path(__file__).name,generator_sha256=sha(__file__),color_helper=str(helper),color_helper_sha256=sha(helper),freecad_version=App.Version(),models=records),indent=2)+'\n')
(HERE/'integrated-model-manifest.json').write_text(json.dumps(dict(assignments=assignments,assigned_instance_count=sum(len(r['refs']) for r in assignments),unsupported=unsupported),indent=2)+'\n')
print(json.dumps(dict(models=len(records),assigned_instances=sum(len(r['refs']) for r in assignments),all_step_reimports_and_actual_drill_sections_passed=True)))
