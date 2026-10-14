"""Original drawing-derived 574502B00000G candidate; no project edits.

The primary 2017 drawing governs dimensions. Unsized fold and lance details
are explicit reconstruction parameters, not manufacturer CAD or fit proof.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import sys

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
import Import
import MeshPart

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
V = App.Vector
P = {
    'published_width_mm': 21.84,
    'specific_drawing_depth_mm': 10.03,
    'published_height_mm': 19.05,
    'catalogue_aluminium_thickness_mm': .63,
    'checking_gauge_gap_mm': 4.19,
    'checking_gauge_tolerance_mm': .13,
    'through_hole_diameter_mm': 3.81,
    'hole_axis_height_from_bottom_mm': 11.81,
    'upper_lance_datum_height_mm': 14.99,
    'family_table_depth_mm': 9.02,
    'retained_prior_canonical_front_y_mm': -1.27,
    'assumed_small_bend_center_radius_mm': .55,
    'traced_return_bend_center_radius_mm': 1.8,
    'traced_inner_channel_outer_width_mm': 12,
    'traced_outer_fin_tip_y_mm': 7.78,
    'traced_spring_finger_height_mm': 9.8,
    'assumed_inner_lance_width_mm': .45,
    'traced_inner_lance_height_mm': 8.2,
}
H = P['published_height_mm']
T = P['catalogue_aluminium_thickness_mm']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box(dx, dy, dz, point):
    return Part.makeBox(dx, dy, dz, V(*point))


def strip(a, b, height=H, z=0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy * T / (2 * length), dx * T / (2 * length)
    points = [(a[0]+nx, a[1]+ny), (b[0]+nx, b[1]+ny),
              (b[0]-nx, b[1]-ny), (a[0]-nx, a[1]-ny)]
    wire = Part.makePolygon([V(x, y, z) for x, y in points]
                            + [V(*points[0], z)])
    return Part.Face(wire).extrude(V(0, 0, height))


def bend(center, radius, start_deg, end_deg):
    def point(r, degrees):
        a = math.radians(degrees)
        return V(center[0]+r*math.cos(a), center[1]+r*math.sin(a), 0)
    middle = (start_deg + end_deg) / 2
    ro, ri = radius+T/2, radius-T/2
    edges = [Part.Arc(point(ro, start_deg), point(ro, middle),
                      point(ro, end_deg)).toShape(),
             Part.makeLine(point(ro, end_deg), point(ri, end_deg)),
             Part.Arc(point(ri, end_deg), point(ri, middle),
                      point(ri, start_deg)).toShape(),
             Part.makeLine(point(ri, start_deg), point(ro, start_deg))]
    return Part.Face(Part.Wire(edges)).extrude(V(0, 0, H))


def fuse(shapes):
    return shapes[0].multiFuse(shapes[1:]).removeSplitter()


def bounds(shape):
    b = shape.BoundBox
    return [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]


def style_step(path, color):
    text = path.read_text()
    entities = {int(n): v for n, v in re.findall(
        r'#(\d+)\s*=\s*(.*?);', text, re.S)}
    breps = [int(n) for n in re.findall(
        r'#(\d+)\s*=\s*MANIFOLD_SOLID_BREP', text)]
    assert len(breps) == 1
    brep = breps[0]
    shell = int(re.findall(r'#(\d+)', entities[brep])[0])
    faces = [int(n) for n in re.findall(r'#(\d+)', entities[shell])]
    context = None
    for value in entities.values():
        if (value.startswith('ADVANCED_BREP_SHAPE_REPRESENTATION')
                or value.startswith('SHAPE_REPRESENTATION')):
            refs = [int(n) for n in re.findall(r'#(\d+)', value)]
            if brep in refs:
                context = refs[-1]
                break
    assert context is not None
    number = max(entities) + 1
    extra = []
    def entity(value):
        nonlocal number
        current = number
        extra.append(f'#{current} = {value};')
        number += 1
        return current
    rgb = entity("COLOUR_RGB('Black anodized aluminium',"
                 + ','.join(map(str, color)) + ')')
    fill_color = entity(f"FILL_AREA_STYLE_COLOUR('',#{rgb})")
    fill = entity(f"FILL_AREA_STYLE('',(#{fill_color}))")
    surface = entity(f'SURFACE_STYLE_FILL_AREA(#{fill})')
    side = entity(f"SURFACE_SIDE_STYLE('',(#{surface}))")
    usage = entity(f'SURFACE_STYLE_USAGE(.BOTH.,#{side})')
    assignment = entity(f'PRESENTATION_STYLE_ASSIGNMENT((#{usage}))')
    styled = [entity(f"STYLED_ITEM('Anodized sheet',(#{assignment}),#{face})")
              for face in faces]
    entity("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',("
           + ','.join('#'+str(n) for n in styled) + f'),#{context})')
    text = text.replace('ENDSEC;\nEND-ISO-10303-21;',
                        '\n'.join(extra)+'\nENDSEC;\nEND-ISO-10303-21;')
    path.write_text(text)
    return len(faces)


previous = json.loads((WORK / 'validation/models-review-8/combined-model-plan.json').read_text())
old = next(r for r in previous['assignments'] if r['references'] == ['KK1'])
regulator = next(r for r in previous['assignments'] if r['references'] == ['IC20'])
source_files = [WORK/'ioboard/ioboard.kicad_pcb',
                WORK/'ioboard/ioboard-import-fps.pretty/D03S.kicad_mod',
                Path(old['source_model']), Path(regulator['source_model'])]
original_hashes = {str(path): digest(path) for path in source_files}

# One continuous folded sheet: outer return fins, paired rounded spring
# returns, central U channel, and its rear contact spine. These centerlines
# trace the exact part illustration but their unsized radii are assumptions.
left = [
    strip((-10.605, 7.78), (-10.605, -.355)),
    bend((-10.005, -.355), .6, 180, 270),
    strip((-10.005, -.955), (-3.5, -.955)),
    bend((-3.5, .845), 1.8, -90, 90),
    strip((-3.5, 2.645), (-5.135, 3.05)),
    bend((-5.135, 3.6), .55, 180, 270),
    strip((-5.685, 3.6), (-5.685, 7.895)),
    bend((-5.135, 7.895), .55, 90, 180),
]
right = []
for shape in left:
    mirrored = shape.mirror(V(0, 0, 0), V(1, 0, 0))
    right.append(mirrored)
sheet = fuse(left + right + [strip((-5.135, 8.445), (5.135, 8.445))])
assert sheet.isValid() and len(sheet.Solids) == 1, ('base', len(sheet.Solids))

# Free-state spring fingers are connected to the returns. Their changing
# width follows the lower front silhouette. The unsized loft is explicit;
# no claim is made for spring force, deformation, or exact stamped tooling.
fingers = []
for side in [-1, 1]:
    sections = []
    for z, tip in [(0, 1.55), (4.9, .85), (9.8, 1.55)]:
        points = [(-3.65, 2.28), (-tip, 3.31),
                  (-tip-.22, 3.94), (-3.85, 2.91)]
        if side > 0:
            points = [(-x, y) for x, y in reversed(points)]
        wire = Part.makePolygon([V(x, y, z) for x, y in points]
                                + [V(*points[0], z)])
        sections.append(Part.Wire(wire.Edges))
    fingers.append(Part.makeLoft(sections, True, False))
sheet = fuse([sheet] + fingers)

# Relief lances distinguish the free spring regions from a plain extrusion.
# Their widths and exact terminal heights are traced/assumed, not dimensioned.
for x in [-5.685, 5.685]:
    sheet = sheet.cut(box(.45, 5.2, 8.2, (x-.225, 3.2, -.001)))
hole = Part.makeCylinder(3.81/2, 1.5, V(0, 7.7, 11.81), V(0, 1, 0))
sheet = sheet.cut(hole)
for x in [-1.05, .8]:
    sheet = sheet.cut(box(.25, 1.5, 2.8, (x, 7.7, 14.99)))
# Unsized inward holding catch, bounded entirely by the published envelope.
catch = box(1.1, .55, .7, (-.55, 7.88, 17.2))
sheet = sheet.fuse(catch).removeSplitter()
assert sheet.isValid() and len(sheet.Solids) == 1, ('final', len(sheet.Solids))
expected = [-10.92, -1.27, 0, 10.92, 8.76, 19.05]
assert max(abs(a-b) for a, b in zip(bounds(sheet), expected)) < 1e-6

key = 'Aavid_574502B00000G_DrawingDerived_FoldedSpring'
doc = App.newDocument('KK1DetailedCandidate')
feature = doc.addObject('PartDesign::Feature', 'ContinuousFoldedSpringSheet')
feature.Label = '574502B00000G - continuous folded spring sheet'
feature.Shape = sheet
doc.recompute()
step_path = HERE / (key + '.step')
stl_path = HERE / (key + '.stl')
Import.export([feature], str(step_path))
unstyled = Part.read(str(step_path))
face_styles = style_step(step_path, (.055, .06, .065))
roundtrip = Part.read(str(step_path))
assert roundtrip.isValid() and len(roundtrip.Solids) == 1
assert abs(roundtrip.Volume - sheet.Volume) < 1e-6
assert unstyled.exportBrepToString() == roundtrip.exportBrepToString()
MeshPart.meshFromShape(Shape=sheet, LinearDeflection=.015,
                       AngularDeflection=.08, Relative=False).write(str(stl_path))
App.closeDocument(doc.Name)

# Compare both candidates with the unchanged nominal regulator, transformed
# solely by the original source footprint origin difference (IC20 Y=-1.27
# in KK1 coordinates). This is a geometric witness, not a seat adjustment.
reg = Part.read(regulator['source_model'])
reg.translate(V(0, -1.27, 0))
coarse = Part.read(old['source_model'])
common = roundtrip.common(reg)
old_common = coarse.common(reg)
distance, witnesses, details = roundtrip.distToShape(reg)
if common.Volume > 1e-9:
    MeshPart.meshFromShape(Shape=common, LinearDeflection=.01,
                           AngularDeflection=.1, Relative=False).write(
                               str(HERE/'nominal-regulator-intersection.stl'))
MeshPart.meshFromShape(Shape=reg, LinearDeflection=.02,
                       AngularDeflection=.1, Relative=False).write(
                           str(HERE/'unchanged-IC20-in-KK1-frame.stl'))
contact = {
    'scope': 'Exact BRep intersections with unchanged review8 nominal IC20 '
             'body-only illustration. Native source placement is retained.',
    'IC20_source_step': regulator['source_model'],
    'IC20_source_sha256': digest(Path(regulator['source_model'])),
    'IC20_to_KK1_canonical_translation_mm': [0, -1.27, 0],
    'coarse_KK1_source_step': old['source_model'],
    'coarse_KK1_solid_count': len(coarse.Solids),
    'coarse_intersection_volume_mm3': old_common.Volume,
    'new_KK1_solid_count': len(roundtrip.Solids),
    'new_intersection_volume_mm3': common.Volume,
    'new_intersection_bounds_mm': bounds(common) if common.Volume > 1e-9 else None,
    'minimum_shape_distance_mm': distance,
    'closest_witness_pairs_mm': [[list(a), list(b)] for a, b in witnesses[:8]],
    'interpretation': 'Published full-size geometry and original native pose '
                      'are preserved. A nonzero overlap identifies nominal '
                      'interference; it is not certified elastic spring '
                      'contact or a fitted regulator seat. No solid was '
                      'trimmed or shifted around IC20.',
}
(HERE/'nominal-regulator-contact-audit.json').write_text(
    json.dumps(contact, indent=2)+'\n')

limits = [
    'Drawing-derived reconstruction, not downloaded manufacturer CAD. Exact '
    '574502B00000G identity is retained; no solderable tabs from 03200/03300 '
    'variants were added.',
    'Specific 2017 part drawing gives 21.84 x 10.03 x 19.05 mm. Family table '
    'reports 9.02 mm depth. Specific drawing controls the envelope.',
    'Primary manufacturer catalogue printed page45 specifies 0.63 mm '
    'aluminium and black anodize. Thickness tolerance and spring alloy '
    'condition are unconfirmed.',
    'The 4.19 +/-0.13 mm checking-gauge gap, 3.81 mm hole, 11.81 mm hole '
    'height and 14.99 mm upper-lance datum follow the exact part drawing. '
    'Its parenthetical 11.81 (.485) callout conflicts internally; metric '
    '11.81 is retained, also consistent with catalogue .465 inch.',
    'Bend radii, inner channel width, outer-fin tip height, lances, contact '
    'finger loft, holding catch and stamped relief widths are unsized '
    'drawing-traced presentation geometry, documented in generator parameters.',
    'Canonical envelope Y=-1.27..8.76 and Z=0..19.05 retain the prior '
    'illustration datum. Actual installed slide height, insertion depth and '
    'free-state spring deformation are unconfirmed; native assignment stays '
    'zero offset/rotation with unity scale.',
    'D03S footprint artwork is 13.716 mm wide versus the BOM part width '
    '21.84 mm. Source footprint and all PCB geometry remain unchanged.',
    'Nominal regulator contact/intersection is measured separately; no '
    'clamping, thermal performance, elastic installation, physical clearance '
    'or manufacturing tolerance qualification is claimed.',
]
assignment = dict(old)
assignment.update({
    'source_model': str(step_path), 'source_sha256': digest(step_path),
    'source_kind': 'Primary manufacturer drawing-derived parametric reconstruction',
    'classification': 'Detailed exact-part continuous folded/slotted free-state '
                      'spring illustration; installed fit unqualified',
    'limitations': limits,
    'source_urls': [
        'https://ladyada.net/make/x0xb0x/fab/parts.html',
        'https://info.boydcorp.com/hubfs/Thermal/Air-Cooling/Boyd-Board-Level-Cooling-Slide-On-5744.pdf',
        'https://www.mouser.com/datasheet/2/2/Aavid_Boyd_Board_Level_Heatsinks_Catalog-3043646.pdf',
    ],
    'replaces_source_model': old['source_model'],
    'replaces_source_sha256': old['source_sha256'],
})
for field in ['local_model', 'review_manifest']:
    assignment.pop(field, None)
part = {
    'id': key, 'board': 'ioboard', 'references': ['KK1'], 'footprint': 'D03S',
    'step': str(step_path), 'stl': str(stl_path), 'units': 'mm',
    'source_sha256': digest(step_path), 'stl_sha256': digest(stl_path),
    'canonical_frame': 'Original F.Cu footprint X, -footprint Y, outward Z; '
                       'native PCB pose is not baked into geometry.',
    'classification': assignment['classification'], 'dimensions': P,
    'source_urls': assignment['source_urls'], 'limitations': limits,
    'color_rgb': [.055, .06, .065],
    'material': 'Black anodized aluminium sheet; exact sRGB shade is a '
                'presentation assumption.',
    'geometry': {'valid': roundtrip.isValid(), 'solids': len(roundtrip.Solids),
                 'faces': len(roundtrip.Faces), 'volume_mm3': roundtrip.Volume,
                 'exact_bounds_mm': bounds(roundtrip),
                 'AP214_styled_faces': face_styles,
                 'STEP_roundtrip_geometry_unchanged_by_color': True},
}
assert all(digest(Path(path)) == value
           for path, value in original_hashes.items())
manifest = {
    'date': '2026-10-14', 'parts': [part], 'assignments': [assignment],
    'generator': Path(__file__).name, 'source_file_hashes': original_hashes,
    'source_files_unchanged': True,
    'primary_pdf_sha256': digest(HERE/'sources/boyd-5740-manufacturer.pdf'),
    'source_exact_drawing': 'sources/boyd-574502B00000G-exact-drawing.png',
    'nominal_contact_report': 'nominal-regulator-contact-audit.json',
    'license': 'Original generator and reconstruction CC0-1.0. Manufacturer '
               'drawings retain publisher rights.',
}
(HERE/'heatsink-quality-manifest.json').write_text(
    json.dumps(manifest, indent=2)+'\n')
(HERE/'frozen-candidate-hashes.json').write_text(json.dumps(
    {step_path.name: digest(step_path), stl_path.name: digest(stl_path)},
    indent=2)+'\n')
print(json.dumps({'part': part['geometry'], 'contact': contact,
                  'source_sha256': part['source_sha256']}, indent=2))
