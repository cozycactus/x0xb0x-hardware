"""Detailed, qualified body-only candidates for the original x0xb0x pots.

SPDX-License-Identifier: CC0-1.0
Manufacturer source documents retain their own rights. No manufacturer CAD is
claimed, no original assets/design files are changed, and no fit is certified.
"""
from pathlib import Path
import sys, json, hashlib, math
sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part, Import, MeshPart
from step_face_colors import add_step_face_colors

H = Path(__file__).resolve().parent
W = H.parents[2]
V = App.Vector
BLACK = (.028, .030, .035)
METAL = (.61, .63, .65)
RIVET = (.69, .70, .72)
WAFER = (.23, .12, .055)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
INPUTS = [W/'mainboard/mainboard.kicad_pcb', W/'ioboard/ioboard.kicad_pcb']
INPUTS += [W/'mainboard/mainboard-import-fps.pretty'/f for f in ('EVU.kicad_mod', 'ALPHADUAL.kicad_mod')]
INPUTS += list((W/'mainboard/3dmodels/Revision7/control-colors').glob('*EVU*.step'))
INPUTS += list((W/'mainboard/3dmodels/Revision7/control-colors').glob('*Alpha*.step'))
BEFORE = {str(p): sha(p) for p in INPUTS}

def box(w, d, h, x=None, y=None, z=0):
    return Part.makeBox(w, d, h, V(-w/2 if x is None else x, -d/2 if y is None else y, z))

def cyl(d, h, z=0, x=0, y=0):
    return Part.makeCylinder(d/2, h, V(x, y, z))

def fuse(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.removeSplitter()

def rounded(w, d, h, r, z=0, cy=0):
    return fuse([box(w-2*r, d, h, y=cy-d/2, z=z), box(w, d-2*r, h, y=cy-d/2+r, z=z)]
                + [cyl(2*r, h, z, x, y) for x in (-w/2+r, w/2-r) for y in (cy-d/2+r, cy+d/2-r)])

def profile(points, z, h):
    vv = [V(x, y, z) for x, y in points]
    return Part.Face(Part.makePolygon(vv+[vv[0]])).extrude(V(0, 0, h))

def shaft(z0, tip, flat_length, radial_tip_reduction, axial_tip_length):
    # Original inspection flat remains negativeY; absolute mechanical setting
    # is not inferred from this static depiction.
    s = cyl(6, tip-z0-axial_tip_length, z0)
    s = s.fuse(Part.makeCone(3, 3-radial_tip_reduction, axial_tip_length, V(0, 0, tip-axial_tip_length)))
    return s.cut(box(20, 10, flat_length, x=-10, y=-11.5, z=tip-flat_length)).removeSplitter()

def bbox(s):
    b = s.BoundBox
    return [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]

def tight(s):
    vv, _ = s.tessellate(.01)
    return {'min_mm': [min(getattr(v, c) for v in vv) for c in ('x','y','z')],
            'max_mm': [max(getattr(v, c) for v in vv) for c in ('x','y','z')]}

PARTS = []
def export(key, refs, fp, features, dimensions, sources, improvements, limits):
    doc = App.newDocument(key)
    objects, segments = [], []
    for name, shape, rgb, evidence in features:
        assert shape.isValid() and shape.Volume > 0, (key, name)
        o = doc.addObject('PartDesign::Feature', name)
        o.Label, o.Shape = name, shape
        objects.append(o)
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.02, AngularDeflection=.10, Relative=False)
        stl = H/(key+'--'+name+'.stl')
        mesh.write(str(stl))
        segments.append({'name': name, 'stl': str(stl), 'sha256': sha(stl), 'units': 'mm',
                         'color_srgb': rgb, 'evidence_basis': evidence, 'faces': len(shape.Faces),
                         'solid_count': len(shape.Solids), 'volume_mm3': shape.Volume,
                         'tight_mesh_bounds': tight(shape), 'triangles': mesh.CountFacets})
    doc.recompute()
    step = H/(key+'.step')
    Import.export(objects, str(step))
    styles = add_step_face_colors(step, [(n,s,c) for n,s,c,_ in features])
    original = Part.makeCompound([s for _,s,_,_ in features])
    reread = Part.read(str(step))
    assert reread.isValid() and all(s.isValid() and s.Volume > 0 for s in reread.Solids)
    assert abs(reread.Volume-original.Volume) < 1e-5
    stl = H/(key+'.stl')
    mesh = MeshPart.meshFromShape(Shape=original, LinearDeflection=.02, AngularDeflection=.10, Relative=False)
    mesh.write(str(stl))
    common = ['Detailed own reconstruction from primary manufacturer drawings; not recovered manufacturer CAD.',
              'Canonical original F.Cu footprint frame: X=footprint X,Y=-footprint Y,Z outward, with housing rear atZ0 as existing seating assumption. No footprint placement or side flip is baked into geometry.',
              'All nominal exterior dimensions and full shaft heights are retained. No resizing or relocation was performed to make the enclosure fit.',
              'Colors/material roles and unsized molding, wafer split, metal stock, crimp folds, rivet diameters and small radii are qualified visual interpretations.',
              'Electrical solder leads, below-seat mounting legs and internal wipers are omitted. Exact lead-form/trim, historical seating gap, tolerances, terminal insertion and complete assembly fit are unqualified.']
    PARTS.append({'id': key, 'board': 'mainboard', 'references': refs, 'footprint': fp,
                  'step': str(step), 'source_model': str(step), 'source_sha256': sha(step),
                  'stl': str(stl), 'stl_sha256': sha(stl), 'units': 'mm',
                  'canonical_frame': 'Original F.Cu footprintX,-footprintY,+Z outward; rearZ0, no placed transform baked in.',
                  'offset_mm': [0,0,0], 'rotation_deg': [0,0,0], 'scale': [1,1,1],
                  'classification': 'Detailed source-grounded original-BOM family body illustration; historical variant/physical fit unqualified',
                  'source_kind': 'Own primary-drawing reconstruction with published versus unsized features recorded',
                  'dimensions': dimensions, 'source_urls': [s['url'] for s in sources], 'sources': sources,
                  'segments': segments, 'improvements': improvements, 'limitations': common+limits,
                  'geometry_license': 'CC0-1.0 own reconstruction only; manufacturer document/photo rights retained.',
                  'geometry_audit': {'valid': reread.isValid(), 'all_solids_valid_positive_volume': True,
                                     'solid_count': len(reread.Solids), 'faces': len(reread.Faces),
                                     'volume_mm3': reread.Volume, 'roundtrip_volume_difference_mm3': reread.Volume-original.Volume,
                                     'bounds_mm': bbox(reread), 'tight_mesh_bounds': tight(reread),
                                     'triangles': mesh.CountFacets, 'colored_solids': styles}})
    App.closeDocument(doc.Name)
    print(key, 'ready', len(reread.Faces), 'faces', flush=True)

# Panasonic EVUF2L: No.8 body/sleeve with FL3 full shaft. The source photograph
# shows a black molded case/shaft and bright front sheet frame, not a metal box.
evu_case = rounded(8, 8, 7.25, .45, z=.85)
evu_case = evu_case.cut(box(1.0, .6, 5.0, x=-4.05, y=-1.7, z=2.0))
evu_case = evu_case.cut(box(1.0, .6, 5.0, x=3.05, y=1.1, z=2.0))
evu_wafer = rounded(8, 8, .85, .30)
evu_carrier = rounded(7.4, 2.2, 3.45, .25, z=0, cy=-5.1)
evu_wafer = fuse([evu_wafer, evu_carrier])
evu_outline = [(-4,-6.5),(4,-6.5),(4,-4.6),(4.85,-4.6),(4.85,5.6),(4.35,6),(-4.35,6),(-4.85,5.6),(-4.85,-4.6),(-4,-4.6)]
evu_front = profile(evu_outline, 8.1, .4).cut(cyl(6.1, .6, 8.0))
for x,y in [(-2.5,4.3),(2.5,-4.3)]:
    evu_front = evu_front.cut(cyl(1.05, .6, 8.0, x, y))
evu_tabs = []
for x in (-4.35, 4.0):
    wall = box(.35, 6.8, 7.7, x=x, y=-3.4, z=.4)
    wall = wall.cut(box(.6, 3.7, 3.1, x=x-.1, y=-1.85, z=2.1))
    evu_tabs.append(wall)
for x in (-3.8, 2.6):
    evu_tabs.append(box(1.2, 1.0, .35, x=x, y=-3.9, z=.05))
evu_frame = fuse([evu_front]+evu_tabs)
evu_rivets = Part.makeCompound([cyl(.90,.08,8.42,x,y) for x,y in [(-2.5,4.3),(2.5,-4.3)]])
# Source sleeve has crossed knurl depiction; shallow straight groove locations
# and the small top lip are expressly unsized visual approximations.
evu_sleeve = cyl(9,5,8.5)
for i in range(16):
    tool = box(.23,.22,3.65,x=4.38,y=-.11,z=9.05)
    tool.rotate(V(0,0,0),V(0,0,1),i*22.5)
    evu_sleeve = evu_sleeve.cut(tool)
evu_sleeve = evu_sleeve.cut(cyl(6.15,.35,13.2)).removeSplitter()
evu_shaft = shaft(8.5,30,12,1,1)  # C1 is explicitly printed in the FL3 drawing.
export('Panasonic_EVUF2LFL3_DetailedCandidate',['VR2','VR3','VR5','VR7','VR8'],'EVU',[
    ('BlackMoldedCase',evu_case,BLACK,'Source No.8 case/photo; printed8mm nominal main body; small radii/side reliefs and axial split are unsized.'),
    ('RearWaferAndTerminalCarrier',evu_wafer,WAFER,'Rear wafer and terminal-side projection reconstructed from No.8 photo/outline. Material shade and local wafer thickness/carrier contours unsized; no solder leads.'),
    ('StampedFrontFrameAndCrimps',evu_frame,METAL,'Printed9.7mm width, +6.0/-6.5mm outline and8.5mm front datum. Sheet stock, edge folds, side windows and chamfered outline divisions are source-shaped unsized interpretation.'),
    ('FrontRivetHeads',evu_rivets,RIVET,'Two diagonal source-front rivet indications, contained withinZ8.5. Head dimensions/positions are traced visual detail, not fastener specification.'),
    ('UnthreadedSleeve',evu_sleeve,BLACK,'PrintedD9 sleeve with5mm projection. No screw thread. Surface groove count/depth and collar lip are unsized visual knurl indications.'),
    ('FL3_FlattedInsulatedShaft',evu_shaft,BLACK,'PrintedFL3 L21.5 from housingfrontZ8.5, D6 shaft,12mm flat,4.5mm across, C1 tip chamfer. Absolute rotary setting is not inferred.')],
    {'housing_width_depth_height_mm':[9.7,12.5,8.5], 'housing_y_min_max_mm':[-6.5,6],
     'main_molded_body_width_depth_mm':[8,8], 'sleeve_diameter_projection_mm':[9,5],
     'shaft_diameter_mm':6, 'shaft_length_from_front_mm':21.5, 'shaft_tip_z_mm':30,
     'flat_length_across_mm':[12,4.5], 'published_tip_chamfer_mm':1},
    [{'url':'https://hkjdwchip.com/image/files/panasonicelectroniccomponents-evue2af25d14-datasheets-6366.pdf',
      'local_file':str(H/'sources/panasonic-evu-primary-mirror.pdf'), 'sha256':sha(H/'sources/panasonic-evu-primary-mirror.pdf'),
      'pages':[4,5], 'publisher':'Panasonic','kind':'Primary 2005 manufacturer drawing preserved by public mirror'}],
    ['Replaced solid envelope with molded case, rear wafer/carrier, folded front sheet frame, diagonal rivet indications and grooved sleeve.',
     'Black insulated shaft and sleeve follow original manufacturer photograph; fullFL3 height and printedC1 tip retained.'],
    ['No exact EVUF2LFL3 manufacturer3DCAD was recovered from the bounded official CAD-index and product searches; no unrelated EVU variant CAD was substituted.',
     'Sleeve groove detail is a visual indication, not an exact crossed-knurl/tooling model. Body/wafer internal splits and colors are reconstructed.',
     'Manufacturer mounting-leg pattern differs from actual original footprint; all below-seat legs omitted and no mounting-hole fit is claimed.',
     'Shaft flat remains on canonical negativeY as prior inspection pose. The source drawing states fullCCW30degrees, but actual fitted rotary state is unmeasured.'])

# Alpha RV112BCF-40, correct insulated-shaft family source. The transparent
# shaft sibling from review8 is deliberately not used as original-BOM geometry.
alpha_wafer_outline = [(-5.5,5.0),(5.5,5.0),(5.5,-5.2),(6.5,-5.2),(6.5,-8.45),(-6.5,-8.45),(-6.5,-5.2),(-5.5,-5.2)]
alpha_back = profile(alpha_wafer_outline,0,.85)
alpha_second = rounded(10.4,9.6,.65,.4,z=3.05,cy=-.05)
alpha_core = rounded(10.3,9.6,5.7,.45,z=.85,cy=-.05)
alpha_core = alpha_core.cut(box(12,10.5,.65,y=-5.2,z=3.05))
alpha_outline = [(-5.2,6.7),(5.2,6.7),(6,5.9),(6,4.8),(5.5,4.8),(5.5,-5.1),(6.8,-5.1),(6.8,-7.8),(6,-8.7),(-6,-8.7),(-6.8,-7.8),(-6.8,-5.1),(-5.5,-5.1),(-5.5,4.8),(-6,4.8),(-6,5.9)]
alpha_front = profile(alpha_outline,6.55,.35).cut(cyl(6.15,.6,6.45))
alpha_front = alpha_front.cut(box(3.1,1.55,.6,y=-7.05,z=6.45))
alpha_rivet_pos = [(-4.05,4.95),(4.05,4.95),(-4.05,-4.95),(4.05,-4.95)]
for x,y in alpha_rivet_pos:
    alpha_front = alpha_front.cut(cyl(.95,.6,6.45,x,y))
alpha_shell = []
for x in (-5.5,5.2):
    wall = box(.3,10.0,5.7,x=x,y=-5,z=.85)
    for y in (-3.1,2.0):
        wall = wall.cut(box(.5,1.15,1.05,x=x-.1,y=y,z=2.45))
    alpha_shell.append(wall)
alpha_shell.append(box(11,.3,5.7,y=4.7,z=.85))
for x in (-5.35,4.15):
    for y in (-4.9,3.8):
        alpha_shell.append(box(1.2,1.1,.28,x=x,y=y,z=.57))
alpha_can = fuse(alpha_shell)
alpha_rivets = Part.makeCompound([cyl(.8,.08,6.82,x,y) for x,y in alpha_rivet_pos])
alpha_sleeve = cyl(7.2,5,6.9).cut(cyl(6.1,.28,11.65)).removeSplitter()
alpha_shaft = shaft(6.9,25,7,.5,1.0)
export('Alpha_RV112BCF40_25_DetailedCandidate',['VR4','VR6'],'ALPHADUAL',[
    ('RearWaferAndLowerCarrier',alpha_back,WAFER,'Source rear wafer/lower terminal carrier;13mm lower width within13.6mm outer frame. Exact wafer thickness/material and contour divisions are unsized.'),
    ('SecondGangWafer',alpha_second,WAFER,'Dual-gang source family supports separate wafer illustration. Individual internal wafer axial station/thickness is unsized; no internal circuit or contact geometry claim.'),
    ('MoldedDualGangCore',alpha_core,BLACK,'Source11mm mainbody within folded frame; local corner radii and internal seam are unsized visual reconstruction.'),
    ('FoldedMetalCanAndCrimps',alpha_can,METAL,'Source metal shield/photo with folded side tabs, within11mm mainbody and6.9mm axial datum. Stock, window and crimp locations are unsized.'),
    ('FrontPlate',alpha_front,METAL,'Printed12mm upper flange,11mm mainwidth,13.6mm outerlower flange, shaftaxis+6.7/-8.7mm andfrontZ6.9 retained. Frontwindow and corner shape/rivet details traced but unsized.'),
    ('FrontRivetHeads',alpha_rivets,RIVET,'Four source front rivet indications, contained withinfrontZ6.9. Rivet diameters/positions are visual estimates.'),
    ('UnthreadedSleeve',alpha_sleeve,METAL,'PrintedD7.2 unthreaded5mm sleeve. Collar lip unsized; metallic finish follows correct-family source photo, historical finish unconfirmed.'),
    ('OpaqueFlattedShaft',alpha_shaft,BLACK,'PrintedD6/4.5-across opaque shaft, fullL25 fromhousingrear. Flat7 selected fromcurrent25A options; exacthistorical25F option unconfirmed. Two0.5mm radial tipreductions printed;1mm axial taper length unsized.')],
    {'housing_overall_width_depth_height_mm':[13.6,15.4,6.9], 'main_body_width_mm':11, 'upper_flange_width_mm':12,
     'lower_carrier_width_mm':13, 'housing_y_min_max_mm':[-8.7,6.7], 'sleeve_diameter_projection_mm':[7.2,5],
     'shaft_diameter_mm':6, 'shaft_tip_z_mm':25, 'selected_current_family_flat_length_mm':7,
     'current25A_available_flat_lengths_mm':[7,12], 'shaft_across_flat_mm':4.5,
     'published_tip_radial_reduction_mm':.5, 'unsized_selected_tip_axial_taper_mm':1.0},
    [{'url':'https://www.taiwanalpha.com/downloads?target=products&id=77',
      'local_file':str(H/'sources/alpha-insulated-rv112b-primary.pdf'), 'sha256':sha(H/'sources/alpha-insulated-rv112b-primary.pdf'),
      'pages':[4,5], 'publisher':'Taiwan Alpha','kind':'Official primary insulated-shaft RV112B family drawing, exactBCF-40 housing row'}],
    ['Replaced13.6x15.4 solid envelope with shaped flange, folded metalcan/crimps, separate rearandsecond wafer, molded core, unthreaded sleeve and opaque flatted shaft.',
     'Correct official insulated-shaft family source replaces reliance ontransparent25AL sibling; full25mm shaft datum retained.'],
    ['No exact historicalRV112BCF40-25F manufacturer3DCAD was recovered. Currentinsulated25A family supports this nominalillustration; no transparent25AL orwrongbushingvariant CAD substituted.',
     'Historical originalBOM25F versuscurrent25A remains unresolved; current25A lists both7and12mm flats.7mm retained as priornominalinspection choice, not proof of historical25F geometry.',
     'Tipcallout2-0.5 specifies two0.5mm radial reductions; it does not specify2mm axial bevel. Axial taper length is a1mm visual assumption.',
     'Dualwafer axialstation, internalcore and metalfold details are unsized reconstructions. No below-seat solderleads ormountlegs modeled; no actualpad/leadfit claim.',
     'Shaft flat remains canonicalnegativeY inspection pose. FullCCWsourceangle and actualinstalledcontrolsetting are not inferred.'])

assert BEFORE == {str(p):sha(p) for p in INPUTS}, 'Original input changed during candidate generation'
assignments = [{k:p[k] for k in ['board','references','footprint','source_model','source_sha256','offset_mm','scale','rotation_deg','source_kind','classification','limitations','source_urls','units']} for p in PARTS]
out = {'scope':'Review-only detailed original-BOM family potentiometer candidates; no actual projects/scenes/original models modified.',
       'units':'mm', 'canonical_frame':'Original F.Cu footprintX,-footprintY,+Zoutward; rearZ0, zeroassignmentoffset/rotation, unityscale.',
       'parts':PARTS, 'assignments':assignments, 'reference_count':7, 'family_count':2,
       'input_hashes':BEFORE, 'inputs_unchanged':True, 'physical_fit_qualified':False,
       'source_availability':'sources/source-availability.json'}
(H/'potentiometer-quality-manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'passed':True,'families':2,'references':7,'manifest':str(H/'potentiometer-quality-manifest.json')},indent=2))
