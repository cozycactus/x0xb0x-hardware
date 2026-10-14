"""Create original CC0 canonical body/wire illustrations for KiCad and Blender.

All dimensions are millimetres. Unverified semiconductor/thermistor leads
are omitted. Actual source pads, copper and placements are read only.
"""
from pathlib import Path
import sys, math, json, hashlib, re
sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part, Import, MeshPart

HERE=Path(__file__).resolve().parent
POSITION=json.loads((HERE/'actual-source-positions.json').read_text())
BLACK=(.06,.06,.065);SILVER=(.70,.72,.74);BLUE=(.04,.28,.55);WHITE=(.84,.85,.82)
V=App.Vector
MODELS={}

def box(x,y,z,origin):return Part.makeBox(x,y,z,V(*origin))
def cylinder(r,h,origin,axis=(0,0,1)):return Part.makeCylinder(r,h,V(*origin),V(*axis))
def fused(shapes):
    shape=shapes[0]
    for other in shapes[1:]:shape=shape.fuse(other)
    return shape.removeSplitter()

def add_step_face_colors(path,features):
    """Bind standard AP214 surface styles to faces, without changing geometry.

    Uses the same styled-item/surface-style chain as installed KiCad STEP
    assets. FreeCAD headless exports no ViewObject colors, so apply explicit
    face styles to each exported feature's solids.
    """
    text=path.read_text();entities={int(n):v for n,v in re.findall(r'#(\d+)\s*=\s*(.*?);',text,re.S)}
    breps=[int(n) for n in re.findall(r'#(\d+)\s*=\s*MANIFOLD_SOLID_BREP',text)]
    color_groups=[]
    for _,shape,color in features:
        color_groups.extend([color]*len(shape.Solids))
    assert len(breps)==len(color_groups),(path,len(breps),len(color_groups))
    next_id=max(entities)+1;extra=[]
    def entity(value):
        nonlocal next_id
        n=next_id;next_id+=1;extra.append(f'#{n} = {value};');return n
    for brep,color in zip(breps,color_groups):
        shell=int(re.findall(r'#(\d+)',entities[brep])[0]);faces=[int(n) for n in re.findall(r'#(\d+)',entities[shell])]
        context=None
        for value in entities.values():
            if (value.startswith('ADVANCED_BREP_SHAPE_REPRESENTATION') or value.startswith('SHAPE_REPRESENTATION')) and brep in [int(n) for n in re.findall(r'#(\d+)',value)]:
                refs=re.findall(r'#(\d+)',value);context=int(refs[-1]);break
        assert context is not None
        rgb=entity("COLOUR_RGB('',"+','.join(str(v) for v in color)+')')
        fill_color=entity(f"FILL_AREA_STYLE_COLOUR('',#{rgb})")
        fill=entity(f"FILL_AREA_STYLE('',(#{fill_color}))")
        surface_fill=entity(f'SURFACE_STYLE_FILL_AREA(#{fill})')
        side=entity(f"SURFACE_SIDE_STYLE('',(#{surface_fill}))")
        usage=entity(f'SURFACE_STYLE_USAGE(.BOTH.,#{side})')
        assignment=entity(f'PRESENTATION_STYLE_ASSIGNMENT((#{usage}))')
        styled=[entity(f"STYLED_ITEM('body illustration color',(#{assignment}),#{face})") for face in faces]
        entity("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',("+
               ','.join('#'+str(n) for n in styled)+f'),#{context})')
    text=text.replace('ENDSEC;\nEND-ISO-10303-21;', '\n'.join(extra)+'\nENDSEC;\nEND-ISO-10303-21;')
    path.write_text(text)
    return len(color_groups)

def save_model(key,features,dimensions,classification,sources,limitations,material):
    doc=App.newDocument('Misc_'+key)
    objects=[]
    for label,shape,color in features:
        assert shape.isValid() and shape.Volume>0,(key,label)
        obj=doc.addObject('PartDesign::Feature',label);obj.Label=label;obj.Shape=shape
        objects.append(obj)
    doc.recompute()
    step=HERE/(key+'.step');stl=HERE/(key+'.stl')
    Import.export(objects,str(step));colors=add_step_face_colors(step,features)
    shape=Part.makeCompound([f[1] for f in features])
    MeshPart.meshFromShape(Shape=shape,LinearDeflection=.04,AngularDeflection=.15,Relative=False).write(str(stl))
    segments=[]
    for label,part,color in features:
        dest=HERE/(key+'--'+label+'.stl')
        MeshPart.meshFromShape(Shape=part,LinearDeflection=.04,AngularDeflection=.15,Relative=False).write(str(dest))
        segments.append({'name':label,'stl':dest.name,'color_rgb':list(color)})
    reloaded=Part.read(str(step));assert reloaded.isValid();b=reloaded.BoundBox
    assert abs(reloaded.Volume-shape.Volume)<max(1e-5,shape.Volume*1e-8)
    MODELS[key]={'stl':stl.name,'stl_path':str(stl),'step':step.name,'step_path':str(step),
       'step_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),'stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest(),
       'units':'mm','classification':classification,'sources':sources,'dimensions':dimensions,
       'material_color_suggestions':material,'limitations':limitations,'segments':segments,
       'geometry_audit':{'valid_STEP':True,'solids':len(reloaded.Solids),'colored_solids':colors,
                         'volume_mm3':reloaded.Volume,'bbox_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],
                         'AP214_face_styles':step.read_text().count('STYLED_ITEM')}}
    App.closeDocument(doc.Name)

bom='https://ladyada.net/make/x0xb0x/fab/parts.html'
ct='https://www.nidec-components.com/e/catalog/trimmer/ct-6.pdf'
body=box(7,7,5.3,(-3.5,-3.5,0))
rotor=cylinder(2.2,1.2,(0,0,4.6))
slot=box(2.6,.6,1.6,(-1.3,-.3,4.2)).fuse(box(.6,2.6,1.6,(-.3,-1.3,4.2)))
body=body.cut(slot);rotor=rotor.cut(slot)
save_model('CT6EP_TopAdjust_BodyIllustration', [('Housing',body,BLUE),('Rotor',rotor,WHITE)],
 {'published_body_width_mm':7,'published_body_depth_mm':7,'published_total_height_mm':5.8,
  'published_slot_length_width_depth_mm':[2.6,.6,1.6],'nominal_lead_grid_mm':[5.0,2.5],'actual_board_grid_mm':[5.08,2.54]},
 'Original CT6EP-family nominal body illustration; no electrical terminals', [bom,ct],
 ['Original BOM calls these VishayCT6EP202/502/503/504; current primary CT-6EP catalog is Nidec/Copal. This is not the earlier CTS306 substitution.',
  '7x7x5.8mm and slot dimensions follow the current manufacturer CT-6EP drawing. Historical vendor/revision is not confirmed.',
  'Rotor diameter, housing/rotor split and colors are presentation approximations. No unverified terminals, clips or printed markings are modeled.',
  'Body seated at canonicalZ0 is an installed-height assumption. Body-only assignment does not establish pin fit.'],
 {'Housing':'blue polymer','Rotor':'off-white plastic'})

# A generic TO220 body within primary MC78M00 case221AB dimensional limits.
# The lead region is omitted completely; bottom3mm is an explicit seat choice.
plastic=box(10.0,4.455,9.5,(-5.0,-3.835,3.0))
tab=box(10.0,1.27,6.0,(-5.0,-.65,12.5))
tab=tab.cut(cylinder(1.83,2.0,(0,-.9,15.71),(0,1,0)))
save_model('MC78M05_TO220_BodyOnlyIllustration',[('PlasticBody',plastic,BLACK),('MetalTab',tab,SILVER)],
 {'nominal_body_width_depth_total_height_mm':[10.0,4.455,15.5],'body_bottom_height_mm':3.0,'body_top_height_mm':18.5,
  'nominal_tab_thickness_mm':1.27,'nominal_mount_hole_diameter_mm':3.66},
 'Generic MC78M05/7805 TO220 nominal body and tab; all leads omitted',
 [bom,'https://www.onsemi.com/download/data-sheet/pdf/mc78m00-d.pdf'],
 ['Original BOM identifies7805 TO220 and links FairchildMC78M05CT; exact supplied regulator vendor/suffix is unconfirmed.',
  'Nominal exterior dimensions lie within current onsemi case221AB published limits; body/tab segmentation and mounting-hole pose are simplified.',
  'No terminals are modeled. The prior nominal pin-clearance concern is not hidden by thinning or moving leads.',
  'Body bottomZ3.0mm and canonicalY placement are illustration assumptions informed by the installed standard TO220 package and source footprint; real seat/heatsink contact is not certified.'],
 {'PlasticBody':'black epoxy','MetalTab':'silver metal'})

# Original footprint gives a7.62x2.54mm axial body envelope; no primary
#Microohm mechanical drawing was recovered. Dimensions/stand-off stay marked.
therm=box(.1,.1,.1,(0,0,0))
therm=cylinder(1.27,5.588,(-2.794,0,1.67),(1,0,0))
therm=therm.fuse(Part.makeCone(.90,1.27,1.016,V(-3.81,0,1.67),V(1,0,0)))
therm=therm.fuse(Part.makeCone(1.27,.90,1.016,V(2.794,0,1.67),V(1,0,0)))
features=[('Body',therm,(.25,.57,.68))]
for i,(x,color) in enumerate([(-2.2,(.25,.12,.04)),(-1.2,BLACK),(-.2,(.7,.015,.01)),(.8,(.25,.12,.04)),(2.2,(.05,.35,.08))]):
    ring=cylinder(1.28,.32,(x-.16,0,1.67),(1,0,0)).cut(cylinder(1.27,.34,(x-.17,0,1.67),(1,0,0)))
    features.append(('Band'+str(i+1),ring,color))
save_model('Microohm_LPTC12T21001_ApproxBody',features,
 {'footprint_outline_nominal_length_mm':7.62,'footprint_outline_nominal_diameter_mm':2.54,'assumed_body_standoff_mm':.4,
  'actual_pad_pitch_mm':10.16,'paint_band_radial_thickness_mm':.01},
 'Approximate Microohm LPTC12T21001 axial PTC body; no leads',
 [bom,'http://www.micro-ohm.com/temperature/temprecflm.html',
  'https://github.com/x0xb0x/x0xb0x.github.io/blob/1910f746d2d8758f2651596b00c08f76c847c926/assets/images/parts/posistor.jpg'],
 ['Original BOM identifies1kOhm PTC LPTC12T21001, not a generic NTC. Both R100A/R100B are fitted.',
  'Primary Microohm mechanical data was not recovered.7.62x2.54mm envelope follows the sourceR-7,5 outline; actual body dimensions remain approximate.',
  'Body standoff0.4mm, tapered ends, band locations and colors are illustration choices. Band sequence follows the original BOM.',
  'Unknown leads omitted; no pin fit or thermal coupling claim follows.'],
 {'Body':'blue/teal coating','Bands':'brown black red brown green'})

# Preserve the original SSIP5 footprint outline without calling it a
#manufacturer-authenticated2SC2291 package.
outline=[(-3.81,-1.27),(3.81,-1.27),(3.81,0),(3.175,2.032),(-3.175,2.032),(-3.81,0)]
wire=Part.makePolygon([V(x,y,0) for x,y in outline]+[V(*outline[0],0)])
qbody=Part.Face(wire).extrude(V(0,0,5.0))
save_model('2SC2291_SSIP5_ApproxBody',[('Body',qbody,BLACK)],
 {'footprint_outline_width_mm':7.62,'footprint_outline_depth_mm':3.302,'assumed_body_height_mm':5.0,'actual_board_pin_pitch_mm':2.286},
 'Approximate original-footprint2SC2291 SIP5 body; no leads',
 [bom,'https://github.com/x0xb0x/x0xb0x.github.io/blob/1910f746d2d8758f2651596b00c08f76c847c926/assets/images/parts/2SC2291.jpg'],
 ['Original BOM and primary project photo establish2SC2291 SIP5 matched pair with common base.',
  'No manufacturer package drawing was recovered. SourceSSIP5 outline supplies XY;5mm height and flat seating are explicit approximations.',
  'No2SC1583 package identity is assumed from the shared SSIP5 footprint. Unknown leads omitted.'],
 {'Body':'black epoxy'})

# Simplified folded spring outline, within the specific574502B00000G sheet
#envelope. Spring leaves and fine folds remain approximate.
H=19.05
plates=[box(.6,10.03,H,(-10.92,-1.27,0)),box(.6,10.03,H,(10.32,-1.27,0)),
        box(8.1,.6,H,(-10.92,-1.27,0)),box(8.1,.6,H,(2.82,-1.27,0)),
        box(12,.6,H,(-6,8.16,0)),box(.6,4.79,H,(-6,3.97,0)),box(.6,4.79,H,(5.4,3.97,0))]
# Small connector folds make the interpretation visible as one fitted
#spring-shell object; their sections are not manufacturer CAD.
plates.extend([box(3.78,.6,H,(-6,3.97,0)),box(3.78,.6,H,(2.22,3.97,0)),
               box(.6,4.64,H,(-2.82,-.67,0)),box(.6,4.64,H,(2.22,-.67,0))])
heatsink=fused(plates)
save_model('Aavid_574502B00000G_EnvelopeIllustration',[('BlackAnodizedShell',heatsink,(.035,.038,.042))],
 {'published_width_mm':21.84,'specific_part_drawing_depth_mm':10.03,'published_height_mm':19.05,
  'family_table_depth_mm':9.02,'assumed_fold_wall_thickness_mm':.6},
 'Published-envelope Aavid/Boyd574502B00000G heatsink illustration; folds approximate',
 [bom,'https://info.boydcorp.com/hubfs/Thermal/Air-Cooling/Boyd-Board-Level-Cooling-Slide-On-5744.pdf'],
 ['KK1 is a fitted padless heatsink, included separately from the electrical-pad inventory.',
  'Specific574502B00000G drawing gives21.84mm width,10.03mm side depth and19.05mm height; family summary table reports9.02mm depth. This model uses the specific part drawing.',
  'SourceD03S footprint artwork is13.716mm wide and conflicts with the BOM part; the board artwork is not altered.',
  'Fold wall0.6mm, simplified spring outline and installed seat are approximations; no real regulator contact/clamping or mechanical clearance is certified.'],
 {'BlackAnodizedShell':'black anodized aluminium'})

for pitch in [12.7,15.24]:
    r=.20;top=.80;bottom=-1.8
    shapes=[cylinder(r,pitch,(-pitch/2,0,top),(1,0,0)),
            cylinder(r,top-bottom,(-pitch/2,0,bottom)),cylinder(r,top-bottom,(pitch/2,0,bottom)),
            Part.makeSphere(r,V(-pitch/2,0,top)),Part.makeSphere(r,V(pitch/2,0,top))]
    key='WireJumper_P'+str(pitch).replace('.','p')
    save_model(key,[('Wire',fused(shapes),SILVER)],
      {'actual_pad_pitch_mm':pitch,'assumed_wire_diameter_mm':.4,'assumed_bridge_center_height_mm':.8,'assumed_below_seat_projection_mm':1.8},
      'Bare wire jumper illustration at actual source pad spacing', [bom],
      ['J1/J2 are soldered wire jumpers, not plastic connector bodies.',
       'Actual pad pitch and conductor axes are preserved. Wire diameter, bridge height, forming radius and trimmed projection are illustrative.'],
      {'Wire':'tinned silver wire'})

for count in [3,12]:
    pitch=2.54;xs=[(i-(count-1)/2)*pitch for i in range(count)]
    metal=[cylinder(.20,3.0,(x,0,-1.8)) for x in xs]
    insulated=[cylinder(.50,6.3,(x,0,1.2)) for x in xs]
    web=box((count-1)*pitch+1,.35,6.3,(xs[0]-.5,-.175,1.2))
    insulation=fused(insulated+[web])
    save_model('SolderedRibbon_'+str(count)+'Way_Termination',
      [('InsulatedRibbonStub',insulation,WHITE),('BareConductorEnds',Part.makeCompound(metal),SILVER)],
      {'actual_conductor_count':count,'actual_pitch_mm':pitch,'assumed_wire_diameter_mm':.4,
       'assumed_insulation_diameter_mm':1.0,'assumed_installed_stub_height_mm':7.5,'assumed_bare_end_projection_below_seat_mm':1.8,
       'original_stock_length_mm':152.4},
      'Soldered ribbon termination illustration; no invented header housing',
      [bom,'https://wiki.ladyada.net/x0x/jumpers','https://stuff.mit.edu/afs/sipb/contrib/doc/DigiKey/SECTA.pdf'],
      ['MA03-1/MA12-1 are footprint names; original assembly uses soldered ribbon jumpers, not fitted plastic headers.',
       'Conductor counts and2.54mm pad axes are exact. Wire sections,7.5mm stub height and forming/trim lengths are inferred presentation choices.',
       '152.4mm is original stock length, not validated installed board separation. Only terminations are modeled; board-to-board ribbon paths are assembly dependent.'],
      {'InsulatedRibbonStub':'off-white insulation','BareConductorEnds':'tinned silver wire'})

parts=[];assignments=[]
frame='X=original F.Cu footprintX,Y=-footprintY,Z=outward from F.Cu seat'
def group(board,refs,footprint,key,identity):
    m=MODELS[key]
    poses=[r for r in POSITION['instances'] if r['board']==board and r['reference'] in refs]
    assert len(poses)==len(refs)
    parts.append({'board':board,'references':refs,'footprint':footprint,'identity':identity,
       'stl':m['stl'],'stl_path':m['stl_path'],'step':m['step'],'step_path':m['step_path'],
       'units':'mm','canonical_frame':frame,'classification':m['classification'],'sources':m['sources'],
       'dimensions':m['dimensions'],'material_color_suggestions':m['material_color_suggestions'],
       'limitations':m['limitations'],'segments':m['segments'],'offset_mm':[0,0,0],'rotation_deg':[0,0,0],'scale':[1,1,1],
       'instances':poses,'source_sha256':m['step_sha256'],'stl_sha256':m['stl_sha256']})
    assignments.append({'board':board,'references':refs,'footprint':footprint,
       'source_model':m['step_path'],'source_sha256':m['step_sha256'],
       'offset_mm':[0,0,0],'scale':[1,1,1],'rotation_deg':[0,0,0],
       'source_kind':'original CC0 parametric body/wire illustration','classification':m['classification'],
       'limitations':m['limitations'],'source_urls':m['sources']})

group('mainboard',['TM3','TM4','TM5'],'306','CT6EP_TopAdjust_BodyIllustration','CT6EP504/503/502, original BOM calls Vishay')
group('ioboard',['TM6'],'306','CT6EP_TopAdjust_BodyIllustration','CT6EP202, original BOM calls Vishay')
group('mainboard',['R100A0','R100B0'],'R-7,5','Microohm_LPTC12T21001_ApproxBody','Microohm LPTC12T21001 PTC1kOhm')
group('mainboard',['Q22'],'SSIP5','2SC2291_SSIP5_ApproxBody','2SC2291 matched NPN pair with common base')
group('ioboard',['IC20'],'78XXS','MC78M05_TO220_BodyOnlyIllustration','7805/MC78M05 TO220 regulator')
group('ioboard',['KK1'],'D03S','Aavid_574502B00000G_EnvelopeIllustration','Aavid574502B00000G spring heatsink')
group('mainboard',['J1'],'12','WireJumper_P12p7','Bare wire jumper12.70mm pitch')
group('mainboard',['J2'],'15','WireJumper_P15p24','Bare wire jumper15.24mm pitch')
for board in ['mainboard','ioboard']:
    group(board,['J4','J5','J6','J7'],'MA03-1','SolderedRibbon_3Way_Termination','Soldered3conductor ribbon ends')
    group(board,['J3'],'MA12-1','SolderedRibbon_12Way_Termination','Soldered12conductor ribbon ends')

# Verify wire axes against actual placed pad positions after native XY pose.
wire_checks=[]
for part in parts:
    if part['footprint'] not in ['12','15','MA03-1','MA12-1']:continue
    pitch=part['dimensions'].get('actual_pad_pitch_mm',2.54)
    n=part['dimensions'].get('actual_conductor_count',2)
    for pose in part['instances']:
        angle=math.radians(pose['rotation_deg']);cx,cy=pose['native_position_xy_mm']
        for i,pad in enumerate(sorted(pose['actual_pads'],key=lambda p:int(p['number']))):
            x=(i-(n-1)/2)*pitch;expected=[cx+x*math.cos(angle),cy+x*math.sin(angle)]
            error=math.dist(expected,pad['native_xy_mm']);assert error<1e-7
            wire_checks.append({'board':part['board'],'reference':pose['reference'],'pad':pad['number'],'world_axis_residual_mm':error})

sources=[]
for f in sorted((HERE/'reference').iterdir()):
    if f.is_file():sources.append({'file':str(f.relative_to(HERE)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size})
board_preservation={name:hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'] for name,r in POSITION['boards'].items()}
assert all(board_preservation.values())
out={'scope':'Canonical complete body/wire models for the authorized KiCad and Blender visual assignments. No source board, library or scene edited by this generator.',
 'license':'CC0-1.0 for original parametric illustrations; source documents retain their respective copyrights.',
 'canonical_frame':frame,'models':MODELS,'parts':parts,'assignments':assignments,
 'fitted_reference_count':sum(len(p['references']) for p in parts),
 'intentionally_unpopulated':[{'board':'mainboard','reference':'IC15A0','identity':'BA662A optional alternate OTA','reason':'Original VCA manual specifies BA662 OR BA6110. Kit uses BA6110 atIC15B withQ1-Q4; BA662 usesIC15A and omitsQ1-Q4. Never populate both simultaneously.',
   'sources':['https://ladyada.net/make/x0xb0x/fab/vca/index.html',bom],'model_created':False}],
 'wire_axis_checks':{'count':len(wire_checks),'maximum_residual_mm':max(c['world_axis_residual_mm'] for c in wire_checks),'checks':wire_checks},
 'source_board_hashes':POSITION['boards'],'source_board_files_unchanged_by_generation':board_preservation,'source_documents':sources}
assert out['fitted_reference_count']==21
(HERE/'misc-body-manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'models':len(MODELS),'assignments':len(assignments),'fitted_references':out['fitted_reference_count'],'wire_axis_checks':len(wire_checks),'manifest':str(HERE/'misc-body-manifest.json')},indent=2))
