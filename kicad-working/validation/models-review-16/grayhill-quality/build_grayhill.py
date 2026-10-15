"""Grayhill 25LB22-H body rebuilt from the Series 25L drawing and a product photograph.

Printed datasheet dimensions (and the frame of the revision-8 model) are kept exactly:
21.97 mm square body and output board, 25.91 mm board depth with the 14.97 mm tongue,
1.14 mm board, mounting face 8.71 mm above the seat, 3/8-32 bushing 6.35 mm long with
8.13 mm flats, 6.35 mm shaft to 27.76 mm with its 6.35 x 5.56 mm flat toward the pins,
and the non-turn tab 3.05 x 1.73 mm on the vertical centre line 10.16 mm from the axis,
opposite the pins (drawing front view). The photograph (Grayhill 25L, hex output,
label 8 4 2 1 C) supplies the unprinted appearance: square base with a round drum top,
two side lock lugs, a white label band, a green FR4 output board with gold lands and
solder joints. Those proportions are photo-derived, not dimensioned.

Run with FreeCAD's Python from the repository root:
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
      kicad-working/validation/models-review-16/grayhill-quality/build_grayhill.py
"""
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App  # noqa: E402
import Import  # noqa: E402
import Part  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
SOURCES = WORK / 'visualization/blender-case-revision-7/quality-model-sources/rotary-quality'
sys.path.insert(0, str(SOURCES))
from step_face_colors import add_step_face_colors  # noqa: E402

V = App.Vector
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
BLACK, WHITE, CREAM = (.035, .035, .04), (.93, .93, .91), (.88, .86, .78)
GREEN, GOLD, SOLDER, INK = (.42, .58, .16), (.86, .72, .36), (.80, .81, .82), (.03, .03, .03)
SQUARE, SEAT, FACE = 21.97, 1.14, 8.71
DRUM_D, DRUM_Z = 20.2, 4.3            # photo-derived: drum just inside the square, over a 3.2 mm base
PINS_Y, PITCH = -12.7, 2.54
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731


def box(w, d, h, x=None, y=None, z=0):
    return Part.makeBox(w, d, h, V(-w / 2 if x is None else x, -d / 2 if y is None else y, z))


def cyl(d, h, z=0, x=0, y=0):
    return Part.makeCylinder(d / 2, h, V(x, y, z))


def fuse(parts):
    s = parts[0]
    for p in parts[1:]:
        s = s.fuse(p)
    return s.removeSplitter()


def rounded_box(w, d, h, r, z=0, cy=0):
    core = [box(w - 2 * r, d, h, z=z, y=cy - d / 2), box(w, d - 2 * r, h, z=z, y=cy - d / 2 + r)]
    for x in (-w / 2 + r, w / 2 - r):
        for y in (cy - d / 2 + r, cy + d / 2 - r):
            core.append(cyl(r * 2, h, z, x, y))
    return fuse(core)


previous = Part.Shape()
previous.read(str(WORK / 'mainboard/3dmodels/Revision8/rotary-quality/Grayhill_25LB22H_DetailedCandidate.step'))
old = {n: s for n, s in zip(('FR4OutputBoard', 'BlackMoldedHousing', 'ThreadedDoubleDBushing',
                             'LightPolymerFlattedShaft', 'IntegralNonTurnTab'), previous.Solids[:5])}

# Output board: printed outline (kept from revision 8), now green FR4 with gold lands.
board = old['FR4OutputBoard'].copy()
lands = Part.makeCompound([cyl(1.5, .035, SEAT, x, PINS_Y).cut(cyl(.75, .06, SEAT - .01, x, PINS_Y))
                           for x in (-2 * PITCH, -PITCH, 0, PITCH, 2 * PITCH)])
# Solder fillets around each pin on the lands (the pins themselves are terminals).
joints = Part.makeCompound([Part.makeCone(.7, .38, .55, V(x, PINS_Y, SEAT + .035)) for x in
                            (-2 * PITCH, -PITCH, 0, PITCH, 2 * PITCH)])

# Housing: square base, round drum top with a rounded upper edge, two side lock lugs.
base = rounded_box(SQUARE, SQUARE, DRUM_Z - SEAT, 1.9, z=SEAT)
drum = cyl(DRUM_D, FACE - DRUM_Z, DRUM_Z).common(box(SQUARE, SQUARE, FACE - DRUM_Z, z=DRUM_Z))
drum = drum.makeFillet(.7, [e for e in drum.Edges if abs(e.BoundBox.ZMin - FACE) < 1e-6
                             and e.Curve.__class__.__name__ == 'Circle'])
LUG_IN = DRUM_D / 2 - .5                # lugs run from inside the drum out to the printed square edge
lugs = [box(SQUARE / 2 - LUG_IN, 3.0, 2.6, x=(LUG_IN if s > 0 else -SQUARE / 2), y=-1.5, z=DRUM_Z + .2) for s in (-1, 1)]
housing = fuse([base, drum] + lugs)

# Label band on the drum front (toward the pins), photo layout "8 4 2 1 C".
R, H0, H1, SPAN = DRUM_D / 2, DRUM_Z + .45, DRUM_Z + 2.35, 84.0
# 0.17 mm thick: KiCad tessellates this radius in 12-degree facets whose chords dip 0.056 mm, so a thinner
# label lets the black drum show through at facet centres.
ring = cyl(2 * R + .30, H1 - H0, H0).cut(cyl(2 * R - .04, H1 - H0 + .2, H0 - .1))
sector = Part.makeCylinder(R + 1, H1 - H0 + .2, V(0, 0, H0 - .1), V(0, 0, 1), SPAN)
sector.rotate(V(0, 0, 0), V(0, 0, 1), -90 - SPAN / 2)
band = ring.common(sector).removeSplitter()
glyphs = []
for char, angle in zip('8421C', (-30, -15, 0, 15, 30)):
    wires = Part.makeWireString(char, str(Path(FONT).parent) + '/', Path(FONT).name, 1.25, 0)
    faces = [Part.Face(w) for w in wires[0]]
    face = faces[0]
    for extra in faces[1:]:
        face = face.cut(extra) if face.common(extra).Area > 1e-9 else face.fuse(extra)
    solid = face.extrude(V(0, 0, .06))
    bb = solid.BoundBox
    solid.translate(V(-(bb.XMin + bb.XMax) / 2, -(bb.YMin + bb.YMax) / 2, 0))
    solid.rotate(V(0, 0, 0), V(1, 0, 0), 90)                     # stand the glyph up, facing -Y
    solid.translate(V(0, -(R + .15), (H0 + H1) / 2))
    solid.rotate(V(0, 0, 0), V(0, 0, 1), angle)
    glyphs.append(solid)
text = Part.makeCompound(glyphs)

bushing = old['ThreadedDoubleDBushing'].copy()
shaft = old['LightPolymerFlattedShaft'].copy()
tab = box(3.05, 1.73, 1.73, y=10.16 - 1.73 / 2, z=FACE)        # drawing: 3.05 wide by 1.73 thick, opposite the pins

parts = [('FR4OutputBoard', board, GREEN), ('OutputBoardLands', lands, GOLD), ('SolderJoints', joints, SOLDER),
         ('BlackMoldedHousing', housing, BLACK), ('LabelBand', band, WHITE), ('LabelText', text, INK),
         ('ThreadedDoubleDBushing', bushing, BLACK), ('LightPolymerFlattedShaft', shaft, CREAM),
         ('IntegralNonTurnTab', tab, BLACK)]
checks = []


def check(name, ok, **detail):
    checks.append(dict(check=name, passed=bool(ok), **detail))


for name, shape, _ in parts:
    check(f'{name}: valid', shape.isValid() and len(shape.Solids) >= 1, solids=len(shape.Solids))
hb, bb0, db = housing.optimalBoundingBox(False, False), base.optimalBoundingBox(False, False), drum.optimalBoundingBox(False, False)
ob = old['BlackMoldedHousing'].optimalBoundingBox(False, False)
check('Housing keeps the printed 21.97 mm square, seat and 8.71 mm mounting face',
      abs(bb0.XMax - bb0.XMin - SQUARE) < 1e-6 and abs(bb0.YMax - bb0.YMin - SQUARE) < 1e-6
      and abs(hb.ZMin - SEAT) < 1e-6 and abs(hb.ZMax - FACE) < 1e-6 and db.XMax <= SQUARE / 2 + 1e-6,
      bounds=[round(v, 4) for v in (hb.XMin, hb.YMin, hb.ZMin, hb.XMax, hb.YMax, hb.ZMax)])
check('Side lugs stay within the printed square, like the revision-8 lock ears',
      hb.XMax <= SQUARE / 2 + 1e-6 and -hb.XMin <= SQUARE / 2 + 1e-6, lug_x_mm=round(hb.XMax, 4), old_ear_x_mm=round(-ob.XMin, 4))
for name in ('FR4OutputBoard', 'ThreadedDoubleDBushing', 'LightPolymerFlattedShaft'):
    a = dict((n, s) for n, s, _ in parts)[name]
    check(f'{name}: identical to the revision-8 solid', a.isSame(old[name]) or
          (abs(a.Volume - old[name].Volume) < 1e-9 and a.BoundBox.isInside(old[name].BoundBox.getPoint(0))
           and [round(v, 6) for v in a.BoundBox.getPoint(6)] == [round(v, 6) for v in old[name].BoundBox.getPoint(6)]))
tb = tab.BoundBox
check('Non-turn tab 3.05 x 1.73 mm on the centre line 10.16 mm opposite the pins',
      abs((tb.YMin + tb.YMax) / 2 - 10.16) < 1e-9 and abs(tb.XMax - tb.XMin - 3.05) < 1e-9
      and abs(tb.YMax - tb.YMin - 1.73) < 1e-9 and abs(tb.XMin + tb.XMax) < 1e-9)
check('Label text is five glyphs on the band', len(text.Solids) >= 5 and all(
    band.BoundBox.ZMin <= g.BoundBox.ZMin and g.BoundBox.ZMax <= band.BoundBox.ZMax for g in glyphs))
fl = shaft.BoundBox
check('Shaft tip at 27.76 mm', abs(fl.ZMax - 27.76) < 1e-6)

doc = App.newDocument('grayhill')
assembly = doc.addObject('App::Part', 'Assembly')
assembly.Label = 'Grayhill_25LB22H_PhotoDrawing'
for i, (name, shape, _) in enumerate(parts):
    obj = doc.addObject('Part::Feature', f'P{i:02d}')
    obj.Label = name
    obj.Shape = shape
    assembly.addObject(obj)
doc.recompute()
out = HERE / 'Grayhill_25LB22H_PhotoDrawing.step'
Import.export([assembly], str(out))
add_step_face_colors(out, [(n, s, c) for n, s, c in parts])
back = Part.Shape()
back.read(str(out))
total = sum(len(s.Solids) for _, s, _ in parts)
check('Exported STEP reloads valid with every part solid', back.isValid() and len(back.Solids) == total,
      solids=len(back.Solids))
report = dict(schema=1, revision=16, generator='build_grayhill.py', passed=all(c['passed'] for c in checks),
              check_count=len(checks), checks=checks, step=str(out.relative_to(WORK)), step_sha256=sha(out),
              printed_dimensions_kept=dict(square_mm=SQUARE, seat_mm=SEAT, mounting_face_mm=FACE, board_depth_mm=25.91,
                                           tongue_width_mm=14.97, bushing='3/8-32, 6.35 long, 8.13 flats',
                                           shaft='6.35 dia to 27.76, flat 6.35 x 5.56 toward the pins',
                                           non_turn_tab_mm=dict(width=3.05, thickness=1.73, offset=10.16,
                                                                side='opposite the pins (drawing front view)')),
              photo_derived=dict(drum_diameter_mm=DRUM_D, drum_starts_mm=DRUM_Z, lock_lugs='two, one per side',
                                 label='8 4 2 1 C on a white band spanning 84 degrees',
                                 output_board='green FR4 with gold lands and solder fillets',
                                 tab_height_mm='1.73, assumed equal to the printed thickness'),
              sources=dict(drawing='kicad-working/visualization/blender-case-revision-7/quality-model-sources/rotary-quality/'
                                   'sources/grayhill25l.pdf',
                           photo='Grayhill 25L hex-output encoder photograph supplied by the user (label 8 4 2 1 C)'),
              physical_fit_qualified=False)
(HERE / 'grayhill-model-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'check_count')}))
for c in checks:
    if not c['passed']:
        print('FAIL', c)
assert report['passed']
