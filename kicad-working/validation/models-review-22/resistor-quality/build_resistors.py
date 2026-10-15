"""Original-kit colour bands on the unchanged KiCad DIN0207 resistor bodies.

For each footprint/band variant used by the 212 fixed resistors, the installed KiCad
STEP (one solid) is split, without moving or reshaping anything, into its body (the
part inside a radius-1.45 mm envelope over the body's axial extent), two leads and
flush band rings: each band is the body's own material between two planes across the
axis, outside radius 0.7 mm, so the outer surface is the KiCad surface. Bands sit on
the end caps (first and tolerance band) and the waist, 0.5 mm wide (0.4 mm for the
three inner bands of a 1% part); mounted on end, the first band is at the top; lying
down, it is at the pad-1 end. Positions and colours are illustrations; band order and
values come from resistor-band-assignments.json.

Run with FreeCAD's Python from the repository root:
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
      kicad-working/validation/models-review-22/resistor-quality/build_resistors.py
"""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
V = App.Vector
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
GENERATOR = WORK / 'mainboard/3dmodels/Revision5/passive-models/provenance/generate_passive_illustrations.py'
node = next(n for n in ast.parse(GENERATOR.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'color_step')
exec(compile(ast.Module(body=[node], type_ignores=[]), str(GENERATOR), 'exec'))

BANDS = json.loads((HERE / 'sources/resistor-band-assignments.json').read_text())
assert BANDS['passed']
KICAD = WORK / 'mainboard/3dmodels/KiCad/Resistor_THT.3dshapes'
MODELS = {'0207_5V': ('R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical', 'P5.08mm_Vertical'),
          '0207_2V': ('R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical', 'P2.54mm_Vertical'),
          '0207_10': ('R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal', 'P10.16mm_Horizontal'),
          '0207_15': ('R_Axial_DIN0207_L6.3mm_D2.5mm_P15.24mm_Horizontal', 'P15.24mm_Horizontal')}
COLOUR = dict(Black=(0.05, 0.05, 0.05), Brown=(0.42, 0.22, 0.10), Red=(0.80, 0.07, 0.07), Orange=(0.95, 0.45, 0.05),
              Yellow=(0.95, 0.83, 0.10), Green=(0.10, 0.55, 0.20), Blue=(0.10, 0.25, 0.80), Violet=(0.52, 0.20, 0.70),
              Grey=(0.50, 0.50, 0.50), White=(0.95, 0.95, 0.95), Gold=(0.83, 0.66, 0.22))
BODY = {k: tuple(v) for k, v in BANDS['body_colours_srgb'].items()}
LEAD = (0.824, 0.82, 0.781)          # KiCad DIN0207 lead colour, unchanged
# Band spans along the body from end A (mm); end caps are u 0.62-1.58 and 4.72-5.68, the waist 1.58-4.72.
SPANS = {4: [(0.85, 1.35), (1.95, 2.45), (2.85, 3.35), (4.95, 5.45)],
         5: [(0.85, 1.35), (1.85, 2.25), (2.55, 2.95), (3.25, 3.65), (4.95, 5.45)]}
checks = []


def check(name, ok, **detail):
    checks.append(dict(check=name, passed=bool(ok), **detail))
    if not ok:
        print('FAIL', json.dumps(checks[-1]), flush=True)


def body_axis(shape):
    """Axis point, canonical direction (+Z upright, +X lying) and axial range of the body."""
    cyl = [f for f in shape.Faces if 'Cylinder' in type(f.Surface).__name__ and f.Surface.Radius > 1.1]
    axis = V(*(abs(round(c)) for c in cyl[0].Surface.Axis))
    centre = cyl[0].Surface.Center
    perp = [k for k in 'XYZ' if abs(getattr(axis, k.lower())) < .5]
    ends = [f for f in shape.Faces if 'Toroid' in type(f.Surface).__name__ and
            min(getattr(f.BoundBox, k + 'Length') for k in perp) > 2.6]
    ts = []
    for f in cyl + ends:
        b = f.BoundBox
        ts += [(V(*c) - centre).dot(axis) for c in ((b.XMin, b.YMin, b.ZMin), (b.XMax, b.YMax, b.ZMax))]
    return centre, axis, min(ts), max(ts)


def slab(centre, axis, t0, t1, r_out, r_in=0.0):
    ring = Part.makeCylinder(r_out, t1 - t0, centre + axis * t0, axis)
    if r_in:
        ring = ring.cut(Part.makeCylinder(r_in, t1 - t0, centre + axis * t0, axis))
    return ring


variants = {}
for ref, a in BANDS['assignments'].items():
    variants.setdefault((a['footprint'], tuple(a['bands']), a['tolerance']), []).append(f"{a['board']}:{ref}")
models = {}
for (footprint, bands, tol), refs in sorted(variants.items()):
    source_name, kind = MODELS[footprint]
    source = KICAD / f'{source_name}.step'
    original = Part.Shape()
    original.read(str(source))
    assert len(original.Solids) == 1
    solid = original.Solids[0]
    centre, axis, lo, hi = body_axis(solid)
    check(f'{source_name}: body is 6.3 mm long', abs(hi - lo - 6.3) < 1e-3, axial_range=[lo, hi])
    vertical = abs(axis.z) > .5
    # End A carries the first band: the top of an upright body, the pad-1 (low model x) end of a lying body.
    a_end = hi if vertical else lo
    direction = -1 if vertical else 1     # from end A towards end B along +axis
    envelope = slab(centre, axis, lo, hi, 1.45)
    body = solid.common(envelope)
    leads = solid.cut(envelope)
    check(f'{source_name}: body plus leads keep the KiCad volume', abs(body.Volume + leads.Volume - solid.Volume) < 1e-6
          and len(body.Solids) == 1 and len(leads.Solids) == 2)
    rings, band_parts = [], []
    for i, (u0, u1) in enumerate(SPANS[len(bands)]):
        t0, t1 = sorted((a_end + direction * u0, a_end + direction * u1))
        ring = slab(centre, axis, t0, t1, 1.6, 0.7)
        rings.append(ring)
        band = body.common(ring)
        band_parts.append((f'Band{i + 1}_{bands[i]}', band.Solids[0], COLOUR[bands[i]]))
        check(f'{source_name} {"-".join(bands)}: band {i + 1} is one ring', len(band.Solids) == 1)
    rest = body
    for ring in rings:
        rest = rest.cut(ring)
    parts = [('Body', rest.Solids[0], BODY[tol])] + band_parts + [(f'Lead_{i + 1}', s, LEAD) for i, s in enumerate(leads.Solids)]
    name = f'R_DIN0207_{kind}_{"-".join(bands)}_KiCadBody'
    tag = f'{source_name} {"-".join(bands)}'
    check(f'{tag}: body remainder is one solid', len(rest.Solids) == 1)
    check(f'{tag}: parts partition the KiCad solid exactly (volume)',
          abs(sum(s.Volume for _, s, _ in parts) - solid.Volume) < 1e-6)
    compound = Part.makeCompound([s for _, s, _ in parts])
    ob, cb = solid.optimalBoundingBox(), compound.optimalBoundingBox()
    check(f'{tag}: outer envelope identical to the KiCad model',
          max(abs(getattr(ob, k) - getattr(cb, k)) for k in ('XMin', 'YMin', 'ZMin', 'XMax', 'YMax', 'ZMax')) < 1e-6)
    # Every outer face of the band rings lies on a KiCad body surface (radius 1.25 caps or 1.125 waist).
    outer = [f for _, s, _ in band_parts for f in s.Faces if 'Cylinder' in type(f.Surface).__name__ and f.Surface.Radius > 1.0]
    check(f'{tag}: band outer faces lie on the KiCad body radii',
          len(outer) == len(band_parts) and all(min(abs(f.Surface.Radius - r) for r in (1.25, 1.125)) < 1e-6 for f in outer))
    # Reading order: band centres ordered from end A must give the assigned colours.
    order = sorted(band_parts, key=lambda p: (p[1].CenterOfMass - centre).dot(axis) * (direction))
    check(f'{tag}: bands read from end A in the assigned order', [n.split('_')[1] for n, _, _ in order] == list(bands))
    out = HERE / f'{name}.step'
    doc = App.newDocument('R' + hashlib.md5(name.encode()).hexdigest()[:8])
    objs = []
    for n, s, _ in parts:
        o = doc.addObject('Part::Feature', n)
        o.Shape = s
        objs.append(o)
    doc.recompute()
    Part.export(objs, str(out))
    App.closeDocument(doc.Name)
    color_step(out, parts)
    out.write_text('\n'.join(line.rstrip() for line in out.read_text().splitlines()) + '\n')
    back = Part.read(str(out))
    check(f'{tag}: saved STEP keeps every part, volume and centroid', back.isValid() and len(back.Solids) == len(parts) and
          all(abs(x.Volume - s.Volume) < 1e-6 and (x.CenterOfMass - s.CenterOfMass).Length < 1e-6 for x, (_, s, _) in zip(back.Solids, parts)))
    models[name] = dict(output=out.name, output_sha256=sha(out), footprint=footprint, source_model=f'KiCad/Resistor_THT.3dshapes/{source_name}.step',
                        source_sha256=sha(source), bands=list(bands), tolerance=tol, body_colour=BODY[tol],
                        band_colours={b: COLOUR[b] for b in bands}, references=sorted(refs), part_count=len(parts),
                        first_band_end='top (upright body)' if vertical else 'pad-1 end (lying body)')
report = dict(schema=1, revision=22, generator='build_resistors.py', passed=all(c['passed'] for c in checks), check_count=len(checks),
              checks=checks, models=models, band_spans_mm_from_end_A=SPANS, colours=COLOUR, body_colours=BODY, lead_colour=LEAD,
              assignments=dict(file='sources/resistor-band-assignments.json', sha256=sha(HERE / 'sources/resistor-band-assignments.json')),
              limitations=['Body and lead geometry are the installed KiCad DIN0207 models, unchanged; not a measurement of the kit parts.',
                           'Band widths, positions, the first-band end and the band colour values are illustrations; band order and values come from the original parts page.',
                           'The 1% body colour is sampled from four uncalibrated parts-page photographs; the 5% tan comes from the page band graphic, not a photograph.',
                           'R16 and R106 are banded per the parts page (150 ohm 5%, 24.0K 1%); their PCB values (100, 27K) are left unchanged.',
                           'The 40 LED resistors carry their PCB value (10K); the parts page says the value may vary.'],
              physical_fit_qualified=False)
(HERE / 'resistor-model-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(passed=report['passed'], check_count=len(checks), models=len(models)), indent=2))
assert report['passed']
