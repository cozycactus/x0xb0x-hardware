"""Rebuild the six revision-15 terminal models with formed legs (terminal_spec.CHANGED).

Every terminal must join its body. The other six terminal models keep their
revision-13/14 STEP files unchanged.

Every original solid is re-exported unchanged and in order with its original
STEP colour; the terminal solids from terminal_spec.py are appended in a tin
colour. Each output is reloaded and checked: original solid geometry and
colours retained, terminal bounds equal to the specification, valid shapes.
Source STEP files and both PCBs are hash-guarded and never written.

Run with FreeCAD's Python from the repository root:
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
      kicad-working/validation/models-review-15/terminal-quality/build_terminals.py
"""
import ast
import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App  # noqa: E402
import Import  # noqa: E402
import Part  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK.parent
sys.path.insert(0, str(HERE))
from terminal_spec import CHANGED, FORMED_LEGS, MODELS, TIN, NYS216_FRONT_PROFILE  # noqa: E402

V = App.Vector
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
LEGACY = WORK / 'visualization/blender-case-revision-7/quality-model-sources/rear-quality/build_rear_quality.py'
module = ast.parse(LEGACY.read_text())
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'face_colors'],
                        type_ignores=[]), str(LEGACY), 'exec'))


def brep_colors(path):
    """Per-MANIFOLD_SOLID_BREP colour, in file order."""
    text = Path(path).read_text(errors='ignore')
    ent = {int(n): b for n, b in re.findall(r'#(\d+)\s*=\s*(.*?);', text, re.S)}
    target_rgb = {}
    for b in ent.values():
        if not b.startswith('STYLED_ITEM'):
            continue
        refs = list(map(int, re.findall(r'#(\d+)', b)))
        stack, seen, rgb = refs[:-1], set(), None
        while stack and rgb is None:
            r = stack.pop()
            if r in seen or r not in ent:
                continue
            seen.add(r)
            if ent[r].startswith('COLOUR_RGB'):
                rgb = tuple(float(v) for v in re.findall(r'[-\d.]+(?:E[-+]?\d+)?', ent[r].split(',', 1)[1]))
            else:
                stack.extend(map(int, re.findall(r'#(\d+)', ent[r])))
        target_rgb[refs[-1]] = rgb
    out = []
    for i, b in ent.items():
        if b.startswith('MANIFOLD_SOLID_BREP'):
            faces = list(map(int, re.findall(r'#(\d+)', ent[int(re.findall(r'#(\d+)', b)[0])])))
            out.append(target_rgb.get(i) or next((target_rgb[f] for f in faces if f in target_rgb), None))
    return out


def box(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def extrude_poly(points, axis, lo, hi):
    """Polygon in the plane normal to `axis` ('x' or 'y'); points are (u, z) pairs; extrude lo..hi."""
    if axis == 'y':
        pts = [V(u, lo, z) for u, z in points]
        vec = V(0, hi - lo, 0)
    else:
        pts = [V(lo, u, z) for u, z in points]
        vec = V(hi - lo, 0, 0)
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    return face.extrude(vec)


def blade(t):
    x, y, w, th, ztop, ztip = t['x'], t['y'], t['w'], t['t'], t['z_top'], t['z_tip']
    along_x = t['face'] == 'xz'
    hw, ht = w / 2, th / 2
    def rect(z0, z1):
        return box(x - hw, y - ht, z0, x + hw, y + ht, z1) if along_x else box(x - ht, y - hw, z0, x + ht, y + hw, z1)
    def thickness_cylinder(radius, zc):
        if along_x:
            return Part.makeCylinder(radius, th, V(x, y - ht, zc), V(0, 1, 0))
        return Part.makeCylinder(radius, th, V(x - ht, y, zc), V(1, 0, 0))
    tip = t['tip']
    if tip == 'round':
        solid = rect(ztip + hw, ztop).fuse(thickness_cylinder(hw, ztip + hw))
    elif tip == 'point':
        taper = 0.6
        u0 = x if along_x else y
        tri = [(u0 - hw, ztip + taper), (u0 + hw, ztip + taper), (u0, ztip)]
        wedge = extrude_poly(tri, 'y' if along_x else 'x', (y if along_x else x) - ht, (y if along_x else x) + ht)
        solid = rect(ztip + taper, ztop).fuse(wedge)
    else:
        solid = rect(ztip, ztop)
    if tip == 'fork':
        slot = 0.6
        if along_x:
            solid = solid.cut(box(x - slot / 2, y - th, ztip - 0.01, x + slot / 2, y + th, ztip + 1.8))
        else:
            solid = solid.cut(box(x - th, y - slot / 2, ztip - 0.01, x + th, y + slot / 2, ztip + 1.8))
    if t.get('eyelet'):
        r = t['eyelet'] / 2
        hole = (Part.makeCylinder(r, th + 0.2, V(x, y - ht - 0.1, ztip + hw), V(0, 1, 0)) if along_x
                else Part.makeCylinder(r, th + 0.2, V(x - ht - 0.1, y, ztip + hw), V(1, 0, 0)))
        solid = solid.cut(hole)
    return solid.removeSplitter()


def round_pin(t):
    return Part.makeCylinder(t['d'] / 2, t['z_top'] - t['z_tip'], V(t['x'], t['y'], t['z_tip']), V(0, 0, 1))


def nys_leg(t):
    x, y, w, ztop, ztip = t['x'], t['y'], t['w'], t['z_top'], t['z_tip']
    shift = abs(x) - 8.2
    profile = [((px + shift) if x > 0 else -(px + shift), pz) for px, pz in NYS216_FRONT_PROFILE]
    front = extrude_poly(profile, 'y', y - w / 2, y + w / 2)
    r = w / 2
    side = box(x - 1, y - r, ztip + r, x + 1, y + r, ztop).fuse(
        Part.makeCylinder(r, 2, V(x - 1, y, ztip + r), V(1, 0, 0)))
    return front.common(side).removeSplitter()


def bent_lead(t):
    x, yb_body, yh, zp = t['x'], t['y_body'], t['y_hole'], t['z_plane']
    w, th, R = t['w'], t['t'], t['bend_r']
    y_bend = yh + R
    shoulder = box(x - t['shoulder_w'] / 2, yb_body - t['shoulder_len'], zp - th / 2,
                   x + t['shoulder_w'] / 2, yb_body + 0.6, zp + th / 2)
    straight = box(x - w / 2, y_bend, zp - th / 2, x + w / 2, yb_body - t['shoulder_len'] + 0.001, zp + th / 2)
    section = Part.Face(Part.makePolygon([V(x - w / 2, y_bend, zp - th / 2), V(x + w / 2, y_bend, zp - th / 2),
                                          V(x + w / 2, y_bend, zp + th / 2), V(x - w / 2, y_bend, zp + th / 2),
                                          V(x - w / 2, y_bend, zp - th / 2)]))
    bend = section.revolve(V(0, y_bend, zp - R), V(1, 0, 0), 90)
    horizontal = yb_body - y_bend
    vertical = t['length'] - horizontal - math.pi * R / 2
    z_tip = zp - R - vertical
    down = box(x - w / 2, yh - th / 2, z_tip, x + w / 2, yh + th / 2, zp - R + 0.001)
    solid = shoulder.fuse([straight, bend, down]).removeSplitter()
    return solid, z_tip


def axial_lead(t):
    """One circular sweep along line-arc-line (a boolean fuse of tangent parts drops segments in OCC)."""
    sx = 1 if t['x_hole'] > 0 else -1
    r, R, za, xb, xh = t['d'] / 2, t['bend_r'], t['z_axis'], t['x_body'], t['x_hole']
    xc, zc, a = xh - sx * R, za - R, math.radians(45)
    path = Part.Wire([Part.LineSegment(V(xb, 0, za), V(xc, 0, za)).toShape(),
                      Part.Arc(V(xc, 0, za), V(xc + sx * R * math.sin(a), 0, zc + R * math.cos(a)),
                               V(xh, 0, zc)).toShape(),
                      Part.LineSegment(V(xh, 0, zc), V(xh, 0, t['z_tip'])).toShape()])
    return path.makePipeShell([Part.Wire(Part.makeCircle(r, V(xb, 0, za), V(sx, 0, 0)))], True, True)


def expected_volume(t):
    """Analytic volume of formed leads, so a boolean that silently drops a segment cannot pass."""
    if t['kind'] == 'axial_lead':
        r, R = t['d'] / 2, t['bend_r']
        horizontal = abs(t['x_hole'] - math.copysign(R, t['x_hole']) - t['x_body'])
        return math.pi * r * r * (horizontal + math.pi * R / 2 + t['z_axis'] - R - t['z_tip'])
    if t['kind'] == 'bent_lead':
        R, area = t['bend_r'], t['w'] * t['t']
        y_bend = t['y_hole'] + R
        horizontal = t['y_body'] - t['shoulder_len'] - y_bend
        vertical = t['length'] - (t['y_body'] - y_bend) - math.pi * R / 2
        shoulder = t['shoulder_w'] * (t['shoulder_len'] + 0.6) * t['t']
        return shoulder + area * (horizontal + math.pi * R / 2 + vertical)
    return None


def build(t):
    kind = t['kind']
    if kind == 'blade':
        return blade(t), t['z_tip']
    if kind == 'round':
        return round_pin(t), t['z_tip']
    if kind == 'nys_leg':
        return nys_leg(t), t['z_tip']
    if kind == 'bent_lead':
        return bent_lead(t)
    if kind == 'axial_lead':
        return axial_lead(t), t['z_tip']
    raise ValueError(kind)


def formed_leg(solid, t, body):
    """Riser and horizontal leg from the terminal into the nearest body edge, with the terminal's section."""
    d, pairs, _ = solid.distToShape(body)
    p_t, p_b = pairs[0]
    gap = p_b - p_t
    axis = 'x' if abs(gap.x) >= abs(gap.y) else 'y'
    sign = 1 if (gap.x if axis == 'x' else gap.y) > 0 else -1
    along_x = t['face'] == 'xz'
    assert (axis == 'y') == along_x, (t['name'], axis, t['face'])  # leg runs across the terminal's thickness
    w, th, x, y = t['w'], t['t'], t['x'], t['y']
    solids = list(body.Solids)
    end = (p_b.x if axis == 'x' else p_b.y) + sign * 0.3
    zc = max(t['z_top'], p_b.z) + th / 2
    while not any(s.isInside(V(end, p_b.y, zc) if axis == 'x' else V(p_b.x, end, zc), 1e-6, True) for s in solids):
        zc += 0.1
        assert zc < 4.0, (t['name'], 'no body material above the leg')
    lo, hi = zc - th / 2, zc + th / 2
    if axis == 'y':
        riser = box(x - w / 2, y - th / 2, t['z_top'] - 0.01, x + w / 2, y + th / 2, hi)
        a, b = sorted((y, end))
        leg = box(x - w / 2, a, lo, x + w / 2, b, hi)
    else:
        riser = box(x - th / 2, y - w / 2, t['z_top'] - 0.01, x + th / 2, y + w / 2, hi)
        a, b = sorted((x, end))
        leg = box(a, y - w / 2, lo, b, y + w / 2, hi)
    joined = solid.fuse([riser, leg]).removeSplitter()
    return joined, dict(axis=axis, direction=sign, gap_before_mm=round(d, 4), leg_height_mm=[round(lo, 4), round(hi, 4)],
                        leg_end_mm=round(end, 4), leg_length_mm=round(abs(end - (x if axis == 'x' else y)), 4))


def source_parts(source):
    """Root label and named part shapes of an assembly source, in solid order; None for a single product."""
    products = re.findall(r"PRODUCT\('([^']*)'", Path(source).read_text(errors='ignore'))
    if len(products) < 2:
        return None
    doc = App.newDocument('source')
    Import.insert(str(source), doc.Name)
    roots = [o for o in doc.Objects if o.TypeId == 'App::Part' and not o.InList]
    assert len(roots) == 1 and roots[0].Label == products[0], (source, [r.Label for r in roots])
    parts = []
    # Multi-solid products import as nested App::Part containers with suffixed labels; the file's own product
    # names (same order) are authoritative, and each such product is kept as one compound.
    for name, obj in zip(products[1:], roots[0].Group, strict=True):
        if obj.TypeId == 'Part::Feature':
            parts.append((name, obj.Shape.copy()))
        else:
            assert obj.TypeId == 'App::Part', obj.TypeId
            parts.append((name, Part.makeCompound([f.Shape.copy() for f in obj.Group if f.TypeId == 'Part::Feature'])))
    App.closeDocument(doc.Name)
    return products[0], parts


def vertex_key(solid):
    return sorted((round(v.X, 7), round(v.Y, 7), round(v.Z, 7)) for v in solid.Vertexes)


def main():
    guards = {p: sha(p) for p in [WORK / 'ioboard/ioboard.kicad_pcb', WORK / 'mainboard/mainboard.kicad_pcb']}
    report = dict(schema=1, revision=15, generator='build_terminals.py', freecad=App.Version()[:3], models={})
    checks = []

    def check(name, ok, **detail):
        checks.append(dict(check=name, passed=bool(ok), **detail))

    for key, spec in ((k, MODELS[k]) for k in CHANGED):
        source = WORK / spec['source_step']
        guards[source] = sha(source)
        old = Part.Shape()
        old.read(str(source))
        old_solids = list(old.Solids)
        palette = brep_colors(source)
        check(f'{key}: source solids and colours read in order', len(palette) == len(old_solids) and all(palette),
              solids=len(old_solids))
        terminals, rows = [], []
        for t in spec['terminals']:
            solid, z_tip = build(t)
            leg = None
            if t['name'] in FORMED_LEGS.get(key, {}).get('terminals', ()):
                solid, leg = formed_leg(solid, t, Part.makeCompound(old_solids))
            check(f"{key}/{t['name']}: terminal joins its body",
                  solid.distToShape(Part.makeCompound(old_solids))[0] < 1e-6, formed_leg=leg)
            check(f"{key}/{t['name']}: valid single terminal solid", solid.isValid() and len(solid.Solids) == 1,
                  volume=solid.Volume)
            bb = solid.optimalBoundingBox(False, False)
            check(f"{key}/{t['name']}: tip at specified depth", abs(bb.ZMin - z_tip) < 1e-6, z_min=bb.ZMin, z_tip=z_tip)
            volume = expected_volume(t)
            if volume is not None:
                check(f"{key}/{t['name']}: formed lead volume equals analytic path volume",
                      abs(solid.Volume - volume) < 2e-3, volume=solid.Volume, expected=volume)
            terminals.append(solid.Solids[0])
            rows.append(dict(name=t['name'], pad=t['pad'], kind=t['kind'], z_tip_mm=round(z_tip, 6),
                             bounds_mm=[round(v, 5) for v in (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)],
                             volume_mm3=round(solid.Volume, 6), formed_leg=leg))
        out_dir = WORK / spec['board'] / '3dmodels/Revision15/terminals'
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / spec['output']
        doc = App.newDocument(key)
        named = source_parts(source)
        if named:
            # Assembly sources keep their root and named part products (Blender shows them as named parts);
            # the terminals are one added part product.
            root_label, parts = named
            order = [round(s.Volume, 6) for _, shape in parts for s in shape.Solids]
            check(f'{key}: named source parts cover the solids in order', order == [round(s.Volume, 6) for s in old_solids],
                  parts=[label for label, _ in parts])
            assembly = doc.addObject('App::Part', 'Assembly')
            assembly.Label = root_label
            for i, (label, shape) in enumerate(parts + [('DrawingDerivedTerminals', Part.makeCompound(terminals))]):
                obj = doc.addObject('Part::Feature', f'P{i:02d}')
                obj.Label = label
                obj.Shape = shape
                assembly.addObject(obj)
            doc.recompute()
            Import.export([assembly], str(out))
        else:
            objects = []
            for i, s in enumerate(old_solids + terminals):
                obj = doc.addObject('Part::Feature', f'S{i:02d}')
                obj.Shape = s
                objects.append(obj)
            Part.export(objects, str(out))
        new_palette = [tuple(c) for c in palette] + [TIN] * len(terminals)
        face_colors(out, [list(c) for c in new_palette])
        App.closeDocument(doc.Name)
        saved = Part.Shape()
        saved.read(str(out))
        check(f'{key}: output valid with original plus terminal solids',
              saved.isValid() and len(saved.Solids) == len(old_solids) + len(terminals),
              solids=len(saved.Solids))
        # Vertices and topology must be identical; volume is re-integrated by OCC on reload, so curved faces
        # differ at the 1e-8 relative level and only a relative tolerance is meaningful there.
        pairs = list(zip(old_solids, saved.Solids[:len(old_solids)]))
        same = all(vertex_key(a) == vertex_key(b) and len(a.Faces) == len(b.Faces) and len(a.Edges) == len(b.Edges)
                   for a, b in pairs)
        volume_rel = max(abs(a.Volume - b.Volume) / a.Volume for a, b in pairs)
        check(f'{key}: original solids retained exactly and in order', same and volume_rel < 1e-6,
              max_relative_volume_difference=volume_rel)
        colours = brep_colors(out)
        check(f'{key}: original colours retained and terminals tinned',
              len(colours) == len(new_palette) and all(
                  all(abs(a - b) < 1e-6 for a, b in zip(c, p)) for c, p in zip(colours, new_palette)))
        products = re.findall(r"PRODUCT\('([^']*)'", out.read_text(errors='ignore'))
        if named:
            source_products = re.findall(r"PRODUCT\('([^']*)'", source.read_text(errors='ignore'))
            check(f'{key}: assembly root and named part products retained, terminal part added',
                  products == source_products + ['DrawingDerivedTerminals'], products=products)
        else:
            check(f'{key}: single-product source written as a single product', len(products) == 1)
        report['models'][key] = dict(
            board=spec['board'], source_step=spec['source_step'], source_sha256=guards[source],
            output=str(out.relative_to(WORK)), output_sha256=sha(out), output_bytes=out.stat().st_size,
            original_solids=len(old_solids), terminal_solids=len(terminals), drawing=spec['drawing'],
            provenance=spec['provenance'], terminals=rows)
        print(f"{key}: {len(old_solids)} + {len(terminals)} solids -> {out.relative_to(WORK)}", flush=True)
    check('Source STEP files and both PCBs unchanged', all(sha(p) == h for p, h in guards.items()))
    report.update(passed=all(c['passed'] for c in checks), check_count=len(checks), checks=checks,
                  physical_fit_qualified=False,
                  scope='Terminals added to body illustrations; positions per drawing dimensions, not moved to pads.')
    (HERE / 'terminal-model-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('passed', 'check_count')}))
    for c in checks:
        if not c['passed']:
            print('FAIL', c)
    assert report['passed']


main()
