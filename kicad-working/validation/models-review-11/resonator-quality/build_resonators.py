#!/usr/bin/env python3
"""Independent drawing-derived AWCR family illustrations; writes this directory.

SPDX-License-Identifier: CC0-1.0
The manufacturer drawing remains copyrighted by Abracon. Profile coordinates,
colours, mounting height and trimmed tails are explicit visual assumptions.
No manufacturer CAD is read or incorporated. Existing PCB data is read only.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
import MeshPart
from step_appearance import face_colors

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
ROOT = WORK.parent
V = App.Vector
SOURCE = HERE / 'sources/Abracon_AWCR_MD_2013.pdf'
SOURCE_URL = 'https://media.digikey.com/pdf/Data%20Sheets/Abracon%20Corp%20PDFs/AWCR_MD.pdf'
BODY_COLOR = [.10, .25, .65]
LEAD_COLOR = [.72, .73, .75]
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
guards = {str(WORK / b / (b + '.kicad_pcb')): sha(WORK / b / (b + '.kicad_pcb'))
          for b in ['mainboard', 'ioboard']}
sys.path.insert(0, str(ROOT / 'kicad-import/validation'))
from verify_native_projects import tokens, children, one, property_value


def tree(text):
    roots, stack = [], []
    for token, quoted in tokens(text):
        if token == '(' and not quoted:
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ')' and not quoted:
            stack.pop()
        else:
            stack[-1].append(token)
    assert len(roots) == 1 and not stack
    return roots[0]


def bounds(shape):
    box = shape.optimalBoundingBox(False, False)
    return [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax]


def line(p, q, plane):
    point = (lambda v: V(v[0], 0, v[1])) if plane == 'xz' else (lambda v: V(0, v[0], v[1]))
    return Part.makeLine(point(p), point(q))


def bezier(points, plane):
    curve = Part.BezierCurve()
    point = (lambda v: V(v[0], 0, v[1])) if plane == 'xz' else (lambda v: V(0, v[0], v[1]))
    curve.setPoles([point(p) for p in points])
    return curve.toShape()


def profile_prism(points, plane, low, extent):
    edges = []
    for segment in points:
        edges.append(line(*segment, plane) if len(segment) == 2 else bezier(segment, plane))
    face = Part.Face(Part.Wire(edges))
    if plane == 'xz':
        face.translate(V(0, low, 0))
        return face.extrude(V(0, extent, 0))
    face.translate(V(low, 0, 0))
    return face.extrude(V(extent, 0, 0))


def tapered_body(w, d, h, s):
    # Only w/d/h are published dimensions. The normalized profile coordinates,
    # smooth Bezier control points, 0.96 mm neck widths and shoulder slopes are
    # intentionally declared visual interpretations of the two bulk views.
    p = lambda x, z: (w*x, s+h*z)
    front = [
        [p(-.32, .16), p(-.45, .22), p(-.50, .26), p(-.50, .40)],
        [p(-.50, .40), p(-.50, .68)],
        [p(-.50, .68), p(-.50, .91), p(-.44, 1), p(-.30, 1)],
        [p(-.30, 1), p(.30, 1)],
        [p(.30, 1), p(.44, 1), p(.50, .91), p(.50, .68)],
        [p(.50, .68), p(.50, .40)],
        [p(.50, .40), p(.50, .26), p(.45, .22), p(.32, .16)],
        [p(.32, .16), p(-.32, .16)],
    ]
    front_shape = profile_prism(front, 'xz', -d/2-.1, d+.2)
    for x in [-2.54, 0, 2.54]:
        polygon = [V(x-.48, -d/2-.1, s), V(x+.48, -d/2-.1, s),
                   V(x+.67, -d/2-.1, s+.24*h), V(x-.67, -d/2-.1, s+.24*h)]
        shoulder = Part.Face(Part.makePolygon(polygon+[polygon[0]])).extrude(V(0, d+.2, 0))
        front_shape = front_shape.fuse(shoulder)
    p = lambda y, z: (y, s+h*z)
    side = [
        [p(-.275, 0), p(.275, 0)],
        [p(.275, 0), p(.275, .16), p(d/2, .30), p(d/2, .50)],
        [p(d/2, .50), p(d/2, .75)],
        [p(d/2, .75), p(d/2, .93), p(d*.22, 1), p(0, 1)],
        [p(0, 1), p(-d*.22, 1), p(-d/2, .93), p(-d/2, .75)],
        [p(-d/2, .75), p(-d/2, .50)],
        [p(-d/2, .50), p(-d/2, .30), p(-.275, .16), p(-.275, 0)],
    ]
    side_shape = profile_prism(side, 'yz', -w/2-.1, w+.2)
    result = front_shape.common(side_shape).removeSplitter()
    if not result.isValid() or len(result.Solids) != 1:
        print('profile diagnostic', front_shape.isValid(), side_shape.isValid(),
              len(front_shape.Solids), len(side_shape.Solids),
              result.isValid(), len(result.Solids), front_shape.BoundBox,
              side_shape.BoundBox, front_shape.Volume, side_shape.Volume, flush=True)
    return result


checks = []


def check(name, condition, **evidence):
    row = dict(name=name, passed=bool(condition), **evidence)
    checks.append(row)
    if not condition:
        print(json.dumps(row, indent=2), flush=True)
        raise AssertionError(name)


check('retained-primary-drawing-hash', sha(SOURCE) ==
      'ef48f7b242efe5cfc1f1514721edb274fb13dd2caea086bebe3f40e30fa01a7a')
specs = [dict(mhz=6, board='ioboard', footprint='Resonator_6MHz_x0x',
              references=['XTL2'], body_mm=[9.5, 4, 6.5], rotation_deg=[0, 0, 0]),
         dict(mhz=16, board='mainboard', footprint='2SC2021',
              references=['XTL1'], body_mm=[10, 5, 10], rotation_deg=[0, 0, 180])]
parts, assignments = [], []
for spec in specs:
    name = f"Resonator_AWCR{spec['mhz']}MD_TaperShoulders_P2.54_Illustration"
    w, d, h = spec['body_mm']
    body = tapered_body(w, d, h, .35)
    baseline_path = WORK / spec['board'] / '3dmodels/Revision5/integrated-models' / (
        f"Resonator_AWCR{spec['mhz']}MD_MaxBody_P2.54_Illustration.step")
    baseline = Part.read(str(baseline_path))
    baseline_body = max(baseline.Solids, key=lambda s: s.Volume)
    old_leads = sorted([s for s in baseline.Solids if s.Volume < 1],
                       key=lambda s: s.CenterOfMass.x)
    leads = [Part.makeBox(.6, .35, 2.97, V(x-.3, -.175, -2.5))
             for x in [-2.54, 0, 2.54]]
    check(name+':one-valid-body', body.isValid() and len(body.Solids) == 1)
    check(name+':body-max-envelope-preserved',
          max(abs(a-b) for a, b in zip(bounds(body), bounds(baseline_body))) < 1e-6,
          previous_mm=bounds(baseline_body), refined_mm=bounds(body))
    for i, (old, new) in enumerate(zip(old_leads, leads)):
        difference = old.cut(new).Volume + new.cut(old).Volume
        check(name+f':lead-{i+1}-identical-geometry', difference < 1e-8,
              symmetric_difference_volume_mm3=difference,
              preserved_section_mm=[.6, .35], preserved_z_mm=[-2.5, .47])
        check(name+f':lead-{i+1}-body-contact', body.common(new).Volume > 0,
              contact_overlap_mm3=body.common(new).Volume)
    doc = App.newDocument(name)
    objects, features, colors = [], [], []
    for objname, role, shape, color in [('Body', 'coated_ceramic', body, BODY_COLOR)] + [
            (f'Lead{i+1}', 'lead', lead, LEAD_COLOR) for i, lead in enumerate(leads)]:
        check(name+':'+objname+':valid-solid', shape.isValid() and len(shape.Solids) == 1)
        obj = doc.addObject('Part::Feature', objname)
        obj.Shape = shape
        objects.append(obj)
        colors.append(color)
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.012,
                                     AngularDeflection=.08, Relative=False)
        path = HERE / (name+'--'+objname+'.stl')
        mesh.write(str(path))
        check(name+':'+objname+':closed-mesh', mesh.isSolid())
        features.append(dict(name=objname, role=role, stl=str(path),
                             sha256=sha(path), units='mm', color_rgb=color,
                             rgba=color+[1], exact_bounds_mm=bounds(shape),
                             volume_mm3=shape.Volume, triangles=mesh.CountFacets))
    compound = Part.makeCompound([o.Shape for o in objects])
    expected = [-w/2, -d/2, -2.5, w/2, d/2, .35+h]
    check(name+':full-envelope-preserved',
          max(abs(a-b) for a, b in zip(bounds(compound), expected)) < 1e-6,
          expected_mm=expected, actual_mm=bounds(compound))
    union = body
    for lead in leads:
        union = union.fuse(lead)
    union = union.removeSplitter()
    check(name+':one-connected-union', union.isValid() and len(union.Solids) == 1)
    path = HERE / (name+'.step')
    doc.recompute()
    Part.export(objects, str(path))
    plain = Part.read(str(path))
    appearance = face_colors(path, colors)
    restored = Part.read(str(path))
    # Boolean-intersected Bezier surfaces are converted to STEP B-splines.
    # Check full bounds independently to 1e-6 mm and volume to 1e-7 relative;
    # do not confuse numerical surface-integration noise with moved geometry.
    check(name+':STEP-roundtrip', restored.isValid() and len(restored.Solids) == 4 and
          abs(restored.Volume-compound.Volume)/compound.Volume < 1e-7 and
          max(abs(a-b) for a,b in zip(bounds(restored), bounds(compound))) < 1e-6,
          restored_valid=restored.isValid(), restored_solids=len(restored.Solids),
          compound_volume_mm3=compound.Volume, restored_volume_mm3=restored.Volume,
          absolute_volume_error_mm3=abs(restored.Volume-compound.Volume),
          relative_volume_error=abs(restored.Volume-compound.Volume)/compound.Volume,
          max_bounds_error_mm=max(abs(a-b) for a,b in zip(bounds(restored), bounds(compound))))
    check(name+':appearance-geometry-unchanged',
          plain.exportBrepToString() == restored.exportBrepToString())
    mesh = MeshPart.meshFromShape(Shape=union, LinearDeflection=.012,
                                 AngularDeflection=.08, Relative=False)
    stl = HERE / (name+'.stl')
    mesh.write(str(stl))
    check(name+':exterior-closed-mesh', mesh.isSolid())
    doc.saveAs(str(HERE / (name+'.FCStd')))
    App.closeDocument(doc.Name)
    # PCB coordinates use Y down, while STEP uses Y up. These parts are on
    # F.Cu and the only model rotation is the preserved XTL1 Z=180 degrees.
    pcb = tree((WORK / spec['board'] / (spec['board']+'.kicad_pcb')).read_text())
    footprint = next(f for f in children(pcb, 'footprint')
                     if property_value(f, 'Reference', 'reference') == spec['references'][0])
    check(name+':source-footprint', footprint[1].split(':')[-1] == spec['footprint'])
    model = children(footprint, 'model')[0]
    transforms = {key: [float(v) for v in one(one(model, field), 'xyz')[1:]]
                  for key, field in [('offset_mm', 'offset'), ('rotation_deg', 'rotate'), ('scale', 'scale')]}
    check(name+':original-transforms-preserved', transforms == dict(
        offset_mm=[0, 0, 0], rotation_deg=spec['rotation_deg'], scale=[1, 1, 1]))
    pads = children(footprint, 'pad')
    pad_records = []
    angle = math.radians(-spec['rotation_deg'][2])
    for x, pin in zip([-2.54, 0, 2.54], ['3', '2', '1']):
        pad = next(p for p in pads if p[1].replace('P$', '') == pin)
        pos = [float(v) for v in one(pad, 'at')[1:3]]
        actual = [math.cos(angle)*x, math.sin(angle)*x]
        error = math.dist(actual, [pos[0], -pos[1]])
        drill = float(one(pad, 'drill')[1])
        margin = drill/2-math.hypot(.6/2, .35/2)
        check(name+':pin-'+pin+':unchanged-center', error < 1e-7,
              lead_center_error_mm=error, board_pin=pad[1])
        check(name+':pin-'+pin+':nominal-drill-margin', margin > 0,
              drill_mm=drill, radial_margin_mm=margin)
        pad_records.append(dict(source_pin=pin, board_pin=pad[1],
                                center_error_mm=error, drill_mm=drill,
                                nominal_corner_margin_mm=margin))
    limitations = [
        'Independent original family illustration from the Abracon drawing; exact historically fitted manufacturer/part/revision is not established.',
        f'Body retains the same maximum {w} x {d} x {h} mm envelope. A maximum envelope is not an exact selected-part body size.',
        'The printed nominal lead pitch is 2.5 +/- 0.3 mm; the existing exact 2.54 mm PCB pitch is preserved, without moving footprint or pads.',
        'Full 0.6 x 0.35 mm maximum lead sections, original centers, 0.35 mm body datum and -2.5..0.47 mm lead extents are preserved exactly.',
        '0.35 mm body stand-off and 2.5 mm cut tails are inherited mounting illustrations, not the drawing factory lead length of 5 +/- 1 mm.',
        'The drawing supports a tapered side profile, softened front corners and three coated lead shoulders; the exact normalized profiles, Bezier control points, 0.96 mm shoulder base width, 1.34 mm upper width and 0.55 mm base thickness are undimensioned visual choices.',
        'Blue coating and silver lead colors are illustrative. The original project permits an alternative 6 MHz part and notes that its color can be orange.',
        'Frequency markings and manufacturer branding are intentionally omitted because fitted identity, typography and marking positions are unverified.',
        'No physical seating, tolerance stack, enclosure fit, solder joint or mechanical assembly approval is implied.'
    ]
    row = dict(id=name, board=spec['board'], footprint=spec['footprint'],
               references=spec['references'], source_model=str(path), step=str(path),
               source_sha256=sha(path), stl=str(stl), stl_sha256=sha(stl),
               source_urls=[SOURCE_URL], sources=[dict(url=SOURCE_URL,
                   document='Abracon AWCR-MD revised 05.07.13, page 3, bulk outline',
                   local_pdf=str(SOURCE), sha256=sha(SOURCE))],
               offset_mm=[0, 0, 0], rotation_deg=spec['rotation_deg'], scale=[1, 1, 1],
               classification='original_parametric_package_illustration_primary_max_dimensions_exact_board_pitch_undimensioned_profile_detail',
               source_kind='Independent original drawing-derived family illustration; no manufacturer CAD',
               license='CC0-1.0', limitations=limitations,
               source_face_and_pin_order=['3', '2/GND', '1'],
               per_instance_override=spec['mhz'] == 16,
               canonical_frame='millimeters; model X, -PCB-local-Y, outward Z; source front pin 3 at negative X',
               units='mm', body_mm=spec['body_mm'], body_bounds_mm=bounds(body),
               exact_bounds_mm=bounds(restored), features=features, mesh_parts=features,
               valid=True, solid_count=4, faces=len(restored.Faces),
               volume_mm3=restored.Volume, triangles=mesh.CountFacets,
               color_roles=appearance, baseline_model=str(baseline_path),
               baseline_sha256=sha(baseline_path), pad_checks=pad_records,
               placement_diff_zero=True, lead_geometry_diff_zero=True,
               physical_fit_qualified=False)
    parts.append(row)
    assignments.append({k: row[k] for k in ['board', 'footprint', 'references',
        'source_model', 'source_sha256', 'source_urls', 'sources', 'offset_mm',
        'rotation_deg', 'scale', 'classification', 'source_kind', 'license',
        'limitations', 'source_face_and_pin_order', 'per_instance_override', 'canonical_frame', 'units']})
check('source-PCBs-byte-unchanged', guards == {p: sha(p) for p in guards})
manifest = dict(date='2026-10-14', scope='Two resonator families, two references; candidate only',
                parts=parts, assignments=assignments, instance_count=2,
                assigned_instance_count=2, placement_diff_zero=True,
                source_projects_unchanged=True, source_project_hashes=guards,
                physical_fit_qualified=False, manufacturer_CAD_incorporated=False,
                geometry_license='CC0-1.0 original reconstruction geometry and scripts only; Abracon drawing retains its copyright',
                source_files=[dict(path=str(SOURCE.relative_to(HERE)), sha256=sha(SOURCE), bytes=SOURCE.stat().st_size)],
                generator=Path(__file__).name, generator_sha256=sha(__file__),
                freecad_version=App.Version())
(HERE/'resonator-quality-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
report = dict(passed=all(c['passed'] for c in checks), check_count=len(checks),
              failure_count=0, source_projects_unchanged=True,
              placement_diff_zero=True, lead_geometry_diff_zero=True,
              physical_fit_qualified=False, checks=checks)
(HERE/'resonator-quality-geometry-review.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(passed=True, checks=len(checks), model_hashes={p['id']:p['source_sha256'] for p in parts}), indent=2), flush=True)
