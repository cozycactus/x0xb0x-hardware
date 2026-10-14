#!/usr/bin/env python3
"""Export original-BOM control body illustrations in the original F.Cu frame.

SPDX-License-Identifier: CC0-1.0
Run with FreeCAD's bundled Python. Writes only this isolated asset directory.
All dimensions are millimetres. No electrical or mechanical seating qualification
is implied by a body envelope. Terminals are deliberately outside this scope.
"""
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
import Mesh

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
V = App.Vector
sys.path.insert(0, str(WORK.parent / 'kicad-import/validation'))
from verify_native_projects import children, one, parse_sexpr, property_value

BOM_URL = 'https://ladyada.net/make/x0xb0x/fab/parts.html'
MIRROR_URL = ('https://raw.githubusercontent.com/x0xb0x/x0xb0x.github.io/'
              '1910f746d2d8758f2651596b00c08f76c847c926/'
              'pages/ladyada.net/make/x0xb0x/fab/parts.html')
FRAME = {'x': 'original F.Cu footprint X',
         'y': 'negative original F.Cu footprint Y',
         'z': 'outward from component side',
         'origin': 'original library origin in XY; housing rear datum at Z=0',
         'placement': 'Apply actual KiCad side flip and footprint rotation once.',
         'baked_placement_side_flip': False}
CLASS = 'original-BOM nominal body illustration'
COMMON_LIMITS = [
    'Body illustration derived from published dimensions; not manufacturer CAD.',
    'Housing rear datum is placed at model Z=0. Actual historical seating gap is unmeasured.',
    'Molding details, tolerances, chamfers and terminal geometry are outside this illustration.',
    'Full nominal body and shaft dimensions are retained; geometry is not reduced to clear an enclosure.',
    'This visual population asset does not qualify terminal fit, enclosure fit or physical assembly.'
]
MATERIALS = {
    'black_polymer': {'rgba': [0.035, 0.035, 0.04, 1], 'metallic': 0, 'roughness': 0.36},
    'brown_phenolic': {'rgba': [0.23, 0.11, 0.035, 1], 'metallic': 0, 'roughness': 0.58},
    'metal_case': {'rgba': [0.57, 0.59, 0.61, 1], 'metallic': 0.8, 'roughness': 0.34},
    'nickel_brass': {'rgba': [0.69, 0.70, 0.72, 1], 'metallic': 0.9, 'roughness': 0.23}
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def box(x, y, z, xmin=None, ymin=None, zmin=0):
    return Part.makeBox(x, y, z, V(-x / 2 if xmin is None else xmin,
                                  -y / 2 if ymin is None else ymin, zmin))


def cyl(d, h, z):
    return Part.makeCylinder(d / 2, h, V(0, 0, z))


def shaft(d, z0, z1, flat_length, across, flat_axis='y'):
    shape = cyl(d, z1 - z0, z0)
    cut_level = across - d / 2
    if flat_axis == 'y':
        cutter = box(30, 15 - cut_level, flat_length, -15, -15, z1 - flat_length)
    else:
        cutter = box(15 - cut_level, 30, flat_length, -15, -15, z1 - flat_length)
    return shape.cut(cutter)


def bbox(shape):
    b = shape.BoundBox
    return {'min_mm': [b.XMin, b.YMin, b.ZMin],
            'max_mm': [b.XMax, b.YMax, b.ZMax],
            'size_mm': [b.XLength, b.YLength, b.ZLength]}


def source(url, path, pages, kind='manufacturer dimension drawing'):
    return {'url': url, 'local_file': str(path), 'sha256': sha(path),
            'pages': pages, 'kind': kind}


PARTS = []
ASSIGNMENTS = []
AUDITS = []
INPUTS = [WORK / 'mainboard/mainboard.kicad_pcb'] + [
    WORK / ('mainboard/mainboard-import-fps.pretty/' + n + '.kicad_mod')
    for n in ['B3F-40XX', 'EVU', 'ALPHADUAL', 'PEC11-S', 'NKKTOGGLE', 'GH3074']]
BEFORE = {str(p): sha(p) for p in INPUTS}
BOARD_TREE = parse_sexpr(INPUTS[0].read_text())
FPS = {property_value(f, 'Reference', 'reference'): f
       for f in children(BOARD_TREE, 'footprint')}


def export_group(key, refs, footprint, identities, dimensions, segments,
                 sources, limits=None):
    """A segment is (name, role, material, shape); no below-board solids."""
    library = WORK / ('mainboard/mainboard-import-fps.pretty/' + footprint + '.kicad_mod')
    lt = one(parse_sexpr('(kicad_pcb ' + library.read_text() + ')'), 'footprint')
    assert one(lt, 'layer')[1] == 'F.Cu'
    for ref in refs:
        assert FPS[ref][1].split(':')[-1] == footprint, (ref, FPS[ref][1])
    doc = App.newDocument(key)
    objects = []
    mesh_parts = []
    for name, role, material, shape in segments:
        assert shape.isValid() and shape.Volume > 0, name
        assert shape.BoundBox.ZMin >= -1e-6, name
        obj = doc.addObject('PartDesign::Feature', name)
        obj.Label = name
        obj.Shape = shape
        if obj.ViewObject is not None:
            obj.ViewObject.ShapeColor = tuple(MATERIALS[material]['rgba'][:3])
        objects.append(obj)
        mesh = Mesh.Mesh(shape.tessellate(0.06))
        segment_stl = HERE / (key + '_' + name + '.stl')
        mesh.write(str(segment_stl))
        mesh_parts.append({'name': name, 'role': role, 'material': material,
                           'stl': str(segment_stl), 'units': 'mm',
                           'sha256': sha(segment_stl), 'bounds': bbox(shape),
                           'facets': mesh.CountFacets})
    doc.recompute()
    compound = Part.makeCompound([o.Shape for o in objects])
    step = HERE / (key + '.step')
    stl = HERE / (key + '.stl')
    Part.export(objects, str(step))
    mesh = Mesh.Mesh(compound.tessellate(0.06))
    mesh.write(str(stl))
    App.closeDocument(doc.Name)
    readback = Part.read(str(step))
    assert readback.isValid()
    b1, b2 = bbox(compound), bbox(readback)
    assert all(abs(a-b) < 1e-6 for a,b in zip(b1['size_mm'],b2['size_mm']))
    assert all(abs(a-b) < 1e-6 for a,b in zip(b1['min_mm'],b2['min_mm']))
    reread_mesh = Mesh.Mesh(str(stl))
    assert reread_mesh.CountFacets == mesh.CountFacets
    urls = [BOM_URL, MIRROR_URL] + [s['url'] for s in sources]
    all_limits = COMMON_LIMITS + (limits or [])
    part = {'id': key, 'board': 'mainboard', 'references': refs,
            'footprint': footprint, 'manufacturer_parts': identities,
            'classification': CLASS, 'body_only': True,
            'stl': str(stl), 'step': str(step), 'units': 'mm',
            'source_kind': 'original parameterized published-envelope illustration',
            'canonical_coordinate_convention': FRAME,
            'offset_mm': [0,0,0], 'rotation_deg': [0,0,0], 'scale': [1,1,1],
            'source_urls': urls, 'sources': sources,
            'dimensions': dimensions, 'bounds': b1,
            'source_sha256': sha(step), 'stl_sha256': sha(stl),
            'material_color_suggestions': MATERIALS,
            'mesh_parts': mesh_parts, 'limitations': all_limits,
            'source_library': str(library), 'source_library_sha256': sha(library),
            'combined_step_contains': [s[0] for s in segments],
            'step_colors': 'Material intent is recorded here; headless STEP may use viewer default colors.'}
    PARTS.append(part)
    ASSIGNMENTS.append({k:part[k] for k in [
        'board','references','footprint','source_sha256','offset_mm','scale',
        'rotation_deg','source_kind','classification','limitations','source_urls']})
    ASSIGNMENTS[-1]['source_model'] = str(step)
    AUDITS.append({'id':key,'instances':len(refs),'shape_valid':True,
                   'step_roundtrip_bounds_passed':True,
                   'canonical_library_is_front':True,'all_geometry_z_nonnegative':True,
                   'stl_roundtrip_facets':reread_mesh.CountFacets,
                   'bounds':b1,'solids':len(readback.Solids)})


# TL1100F160Q drawing P001099 rev E, total actuator height 7.30.
export_group('ESwitch_TL1100F160Q_BodyIllustration',
    ['S'+str(i) for i in range(5,28)], 'B3F-40XX', ['E-Switch TL1100F160Q'],
    {'housing_width_mm':12,'housing_length_mm':12,'base_height_mm':3.9,
     'lid_thickness_max_mm':0.5,'actuator_total_height_mm':7.3,
     'actuator_head_width_mm':3.3,'actuator_head_length_mm':2.5,
     'actuator_head_height_mm':1.8,'actuator_base_diameter_mm':6.7},
    [('Housing','housing','black_polymer',box(12,12,3.9)),
     ('Cover','housing','metal_case',box(12,12,0.5,zmin=3.9)),
     ('ActuatorBase','actuator','black_polymer',cyl(6.7,1.1,4.4)),
     ('ActuatorHead','actuator','black_polymer',box(3.3,2.5,1.8,zmin=5.5))],
    [source('https://configured-product-images.s3.amazonaws.com/2D/specs/TL1100F160Q.pdf',
            HERE.parent/'tact-switches/TL1100F160Q.pdf',[1])],
    ['Cover uses the printed 0.50 mm maximum thickness. The 1.10 mm actuator-base height is an illustrative link between the printed lid and actuator-head levels.',
     'The drawing preserves 7.30 mm total actuator height; cap color and installed cap seating remain separate assembly choices.'])

# EVUF2L No.8 housing and FL3 sleeve shaft. Shaft L is measured from Side A,
# i.e. the front of the H=8.5 housing, not from the housing rear/PCB datum.
export_group('Panasonic_EVUF2LFL3_BodyIllustration',
    ['VR2','VR3','VR5','VR7','VR8'],'EVU',
    ['Panasonic EVU-F2LFL3B54','Panasonic EVU-F2LFL3D54'],
    {'housing_width_mm':9.7,'housing_length_mm':12.5,'housing_height_mm':8.5,
     'housing_y_min_mm':-6.5,'housing_y_max_mm':6.0,
     'sleeve_diameter_mm':9,'sleeve_length_mm':5,'shaft_diameter_mm':6,
     'shaft_length_from_housing_front_mm':21.5,'shaft_flat_length_mm':12,
     'shaft_flat_across_mm':4.5,'shaft_tip_from_housing_rear_mm':30},
    [('Housing','housing','black_polymer',box(9.7,12.5,8.5,ymin=-6.5)),
     ('Sleeve','bushing','black_polymer',cyl(9,5,8.5)),
     ('Shaft','shaft','black_polymer',shaft(6,8.5,30,12,4.5))],
    [source('https://hkjdwchip.com/image/files/panasonicelectroniccomponents-evue2af25d14-datasheets-6366.pdf',
            HERE/'sources/panasonic-evu.pdf',[4,5],
            'Panasonic manufacturer dimension drawing preserved by public mirror')],
    ['The canonical terminal side is negative Y, matching the original F.Cu library after Cartesian Y inversion.',
     'Shaft flat is a nominal illustration; current rotation and historical assembly trim are unspecified. Shaft tip Z=30.0 mm follows the full FL3 drawing and is not shortened to fit the panel.'])

# RV112BCF-40 housing plus source25 mm shaft; L starts at REAR housing.
export_group('Alpha_RV112BCF40_25_BodyIllustration',
    ['VR4','VR6'],'ALPHADUAL',
    ['Alpha RV112BCF-40-25F-B54','Alpha RV112BCF-40-25F-A16'],
    {'housing_overall_width_mm':13.6,'housing_main_width_mm':11,
     'housing_flange_width_mm':12,'housing_length_mm':15.4,
     'housing_y_min_mm':-8.7,'housing_y_max_mm':6.7,'housing_height_mm':6.9,
     'sleeve_diameter_mm':7.2,'sleeve_length_mm':5,'shaft_diameter_mm':6,
     'shaft_length_from_housing_rear_mm':25,'nominal_current25A_flat_length_mm':7,
     'shaft_flat_across_mm':4.5},
    [('HousingEnvelope','housing','black_polymer',box(13.6,15.4,6.9,ymin=-8.7)),
     ('Sleeve','bushing','black_polymer',cyl(7.2,5,6.9)),
     ('Shaft','shaft','black_polymer',shaft(6,6.9,25,7,4.5))],
    [source('https://static.chipdip.ru/lib/521/DOC013521571.pdf',
            HERE/'sources/alpha-rv112b.pdf',[4,5,8],
            'Taiwan Alpha manufacturer dimension drawing preserved by public distributor')],
    ['Housing is the complete rectangular 13.6 by 15.4 mm published envelope, including the output-board/flange extent; detailed molding steps are not reconstructed.',
     'Original BOM uses historical 25F shaft suffix. Current drawing calls the 25 mm flatted option 25A; the 7 mm flat detail is explicitly a current-family nominal illustration, not verified historical 25F CAD.',
     'Unlike Panasonic, Alpha L=25 mm is measured from housing rear. Model shaft tip is Z=25 mm.'])

# Exact CTS original-BOM A (unthreaded) bushing and A5 (15mm) shaft, rather
# than the preserved manufacturer CAD B/C0 threaded/30mm variant.
export_group('CTS_290VAA5F201B2_BodyIllustration',
    ['S2'],'PEC11-S',['CTS 290VAA5F201B2'],
    {'housing_width_mm':9.8,'housing_length_mm':10.6,'housing_height_mm':6.2,
     'housing_y_min_mm':-5.1,'housing_y_max_mm':5.5,
     'bushing_diameter_mm':7,'bushing_length_mm':5,'shaft_diameter_mm':6,
     'shaft_length_from_housing_front_mm':15,'shaft_flat_length_mm':7,
     'shaft_flat_across_mm':4.5,'shaft_tip_from_housing_rear_mm':21.2},
    [('Housing','housing','metal_case',box(9.8,10.6,6.2,ymin=-5.1)),
     ('BushingA_Unthreaded','bushing','nickel_brass',cyl(7,5,6.2)),
     ('ShaftA5_Flatted','shaft','nickel_brass',shaft(6,6.2,21.2,7,4.5))],
    [source('https://www.ctscorp.com/Files/DataSheets/Encoders/encoders-290-datasheet.pdf',
            HERE.parent/'rotary-models/cts290.pdf',[2,3])],
    ['The original footprint is named PEC11-S, but the original BOM identifies CTS290VAA5F201B2. This illustration follows CTS dimensions, without substituting Bourns PEC11.',
     'Preserved manufacturer STEP290VBC0F201B2 has different bushing and shaft options and is not used to create this model.',
     'The housing-only illustration does not transfer the previous wrong-variant mounting-tab fit result to the illustrated original variant.'])

# NKK B12AB A17: 13.1 from rear housing plane to bushing front; bushing2.7.
# Lever10 is measured from bushing front. Bracket nominal thickness0.4.
export_group('NKK_B12AB_BodyIllustration',
    ['S1'],'NKKTOGGLE',['NKK B12AB-RO'],
    {'housing_with_bracket_width_mm':8,'housing_length_mm':8.8,
     'housing_with_bracket_depth_mm':10.4,'body_plus_bushing_depth_mm':13.1,
     'bushing_diameter_mm':6,'bushing_projection_mm':2.7,
     'lever_diameter_mm':2.6,'lever_length_mm':10,'total_throw_degrees':26,
     'lever_neutral_tip_z_mm':23.1,'bracket_stock_thickness_mm':0.4},
    [('HousingWithBracketEnvelope','housing','metal_case',box(8,8.8,10.4)),
     ('Bushing','bushing','black_polymer',cyl(6,2.7,10.4)),
     ('BatLeverNeutralEnvelope','actuator','nickel_brass',cyl(2.6,10,13.1))],
    [source('https://www.nkkswitches.eu/pdf/toggle_B.pdf',
            HERE/'sources/nkk-btoggles-eu.pdf',[3,4,6])],
    ['The bracketed housing uses its complete rectangular envelope; bracket windows, folds and separate polymer-case molding are not reconstructed.',
     'Lever is shown in a neutral reference pose to preserve its full 10 mm length. B12AB is ON-NONE-ON, so an installed lever should be posed to either end of the printed total26 degree throw. No switch-state claim is made.',
     'Source terminal-row offset is nominal1.0 mm; original library is1.016 mm. The body axis uses the original library origin, without inventing an offset to force terminal fit.'])

# Exact Grayhill no-Z original BOM part: no optional mounting bracket. This
# recreates the corrected F.Cu housing/tongue orientation and excludes leads.
gh_bushing = cyl(9.525,6.35,8.71).common(box(8.13,20,6.35,zmin=8.71))
export_group('Grayhill_25LB22H_BodyIllustration',
    ['S3','S4'],'GH3074',['Grayhill 25LB22-H'],
    {'housing_overall_width_mm':23.5,'housing_overall_length_mm':25.91,
     'housing_depth_mm':8.71,'housing_y_min_mm':-14.925,'housing_y_max_mm':10.985,
     'bushing_major_diameter_mm':9.525,'bushing_double_d_across_mm':8.13,
     'bushing_length_mm':6.35,'shaft_diameter_mm':6.35,
     'shaft_length_beyond_bushing_mm':12.7,'shaft_flat_length_mm':6.35,
     'shaft_flat_across_mm':5.56,'shaft_tip_z_mm':27.76,
     'anti_turn_tab_diameter_envelope_mm':3.05,'anti_turn_tab_height_mm':1.73,
     'anti_turn_tab_center_mm':[10.16,0]},
    [('HousingEnvelope','housing','black_polymer',box(23.5,25.91,8.71,ymin=-14.925)),
     ('DoubleDBushingEnvelope','bushing','black_polymer',gh_bushing),
     ('Shaft','shaft','black_polymer',shaft(6.35,15.06,27.76,6.35,5.56)),
     ('AntiTurnTabEnvelope','housing','black_polymer',
      Part.makeCylinder(3.05/2,1.73,V(10.16,0,8.71)))],
    [source('https://grayhill.com/wp-content/uploads/media/25l-datasheet.pdf',
            HERE.parent/'rotary-models/grayhill25l.pdf',[1,2])],
    ['Full housing rectangular envelope retains the output-board tongue on canonical negative Y. Native B.Cu side flip remains a placement operation.',
     'Bushing represents the source3/8-32 major-diameter double-D envelope; helical thread and mounting nut are omitted.',
     'No optional bracket is added to original25LB22-H. This is the same corrected original-F.Cu orientation independently audited in grayhill-world-orientation-audit.json.'])

AFTER = {str(p):sha(p) for p in INPUTS}
assert BEFORE == AFTER, 'Input board/library changed during asset generation'
assert sum(len(p['references']) for p in PARTS) == 34
assert len({r for p in PARTS for r in p['references']}) == 34
MANIFEST = {'date':'2026-10-14','units':'mm',
            'scope':'Six original-BOM control body illustrations for34 mainboard references.',
            'canonical_coordinate_convention':FRAME,
            'geometry_license':'CC0-1.0 (original generated illustrations only)',
            'source_document_rights':'Manufacturer documents retain their original rights.',
            'parts':PARTS,'assignments':ASSIGNMENTS,
            'instance_count':34,'family_count':6,
            'input_board_and_libraries_sha256':BEFORE,
            'generator_modified_input_board_or_libraries':False}
(HERE/'control-body-manifest.json').write_text(json.dumps(MANIFEST,indent=2)+'\n')
(HERE/'control-body-audit.json').write_text(json.dumps({
    'passed':True,'instance_count':34,'family_count':6,'audits':AUDITS,
    'input_board_and_libraries_unchanged_during_generation':BEFORE==AFTER,
    'limitations':['Checks establish artifact integrity, canonical frame and nominal envelopes; they do not qualify seating or terminal fit.']},indent=2)+'\n')
print(json.dumps({'manifest':str(HERE/'control-body-manifest.json'),
                  'families':len(PARTS),'instances':34,'passed':True}))
