"""IC3 and IC2 in their original-BOM TE DIP sockets, in the unchanged KiCad DIP model frames.

Each output STEP holds two solids: the TE manufacturer socket model (geometry untouched,
rotated and translated so its tails sit on the chip's pin axes, notch at the pin-1 end
and seating plane on the board) and the installed KiCad DIP chip raised 5.10 mm so its
lead shoulders rest on the socket top. Faces are coloured individually: the chip keeps
the KiCad face colours; socket faces reaching below the board (the contacts) are tin,
all others black. The PCB model transforms stay unchanged.

Run with FreeCAD's Python from the repository root:
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
      kicad-working/validation/models-review-23/socket-quality/build_sockets.py
"""
import hashlib
import io
import json
import math
import re
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
V = App.Vector
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
EVIDENCE = json.loads((HERE / 'sources/socket-evidence.json').read_text())
SEAT = 5.10                         # socket height above the board (TE model and distributor data)
BLACK, TIN = (0.07, 0.07, 0.08), (0.80, 0.80, 0.78)
KICAD = WORK / 'mainboard/3dmodels/KiCad/Package_DIP.3dshapes'
SPECS = [dict(ref='IC3', footprint='DIL40', dip='DIP-40_W15.24mm', socket='TE_CVM_1-390262-5_3d_stp.zip', part='TE 1-390262-5 (BOM AMP 390262-5)', pins=40),
         dict(ref='IC2', footprint='DIL08_AT25', dip='DIP-8_W7.62mm', socket='TE_CVM_1-390261-2_3d_stp.zip', part='TE 1-390261-2 (BOM AMP 390261-2)', pins=8)]
checks = []


def check(name, ok, **detail):
    checks.append(dict(check=name, passed=bool(ok), **detail))
    if not ok:
        print('FAIL', json.dumps(checks[-1]), flush=True)


def entities(text):
    return {int(n): b for n, b in re.findall(r'#(\d+)\s*=\s*(.*?);', text, re.S)}


def face_colours(path):
    """Colour of every face of a single-solid STEP, in FreeCAD face order (shell order)."""
    text = Path(path).read_text()
    ent = entities(text)
    shell = next(b for b in ent.values() if b.startswith('CLOSED_SHELL'))
    faces = [int(x) for x in re.findall(r'#(\d+)', shell)]
    styled = {}
    for b in ent.values():
        m = re.match(r"STYLED_ITEM\('[^']*',\(#(\d+)\),#(\d+)\)", b.replace(' ', ''))
        if m:
            styled[int(m.group(2))] = int(m.group(1))
    out = []
    for f in faces:
        c = int(re.findall(r'#(\d+)', ent[styled[f]])[0])           # SURFACE_STYLE_USAGE
        while not ent[c].startswith('COLOUR_RGB'):
            c = int(re.findall(r'#(\d+)', ent[c])[-1])
        out.append(tuple(round(float(v), 6) for v in ent[c].rstrip(')').split(',')[1:]))
    return out


def add_face_styles(path, colours_per_solid, names):
    """Name each MANIFOLD_SOLID_BREP and give every face its own colour style (FreeCAD shell order)."""
    text = Path(path).read_text()
    ent = entities(text)
    breps = [n for n, b in ent.items() if b.startswith('MANIFOLD_SOLID_BREP')]
    assert len(breps) == len(colours_per_solid) == len(names)
    next_id = max(ent) + 1
    added, palette, styled = [], {}, []

    def add(expr):
        nonlocal next_id
        added.append(f'#{next_id} = {expr};')
        next_id += 1
        return next_id - 1

    for brep, colours, name in zip(breps, colours_per_solid, names):
        text = re.sub(rf"(#{brep}\s*=\s*MANIFOLD_SOLID_BREP\()'[^']*'", lambda m: m[1] + f"'{name}'", text)
        shell = int(re.findall(r'#(\d+)', ent[brep])[0])
        faces = [int(x) for x in re.findall(r'#(\d+)', ent[shell])]
        assert len(faces) == len(colours)
        for face, rgb in zip(faces, colours):
            if rgb not in palette:
                col = add("COLOUR_RGB('',{},{},{})".format(*rgb))
                area = add(f"FILL_AREA_STYLE('',(#{add(f'FILL_AREA_STYLE_COLOUR({chr(39)}{chr(39)},#{col})')}))")
                side = add(f"SURFACE_SIDE_STYLE('',(#{add(f'SURFACE_STYLE_FILL_AREA(#{area})')}))")
                palette[rgb] = add(f"PRESENTATION_STYLE_ASSIGNMENT((#{add(f'SURFACE_STYLE_USAGE(.BOTH.,#{side})')}))")
            styled.append(add(f"STYLED_ITEM('',(#{palette[rgb]}),#{face})"))
    context = next(n for n, b in ent.items() if 'GEOMETRIC_REPRESENTATION_CONTEXT(3)' in b)
    add("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({}),#{})".format(','.join(f'#{s}' for s in styled), context))
    marker = 'ENDSEC;\nEND-ISO-10303-21;'
    assert marker in text
    Path(path).write_text(text.replace(marker, '\n'.join(added) + '\n' + marker))


def sections(shape, z):
    out = []
    for w in shape.slice(V(0, 0, 1), z):
        b = w.BoundBox
        out.append(dict(centre=((b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2), size=(b.XLength, b.YLength)))
    return out


models = {}
for spec in SPECS:
    name = f'{spec["dip"]}_in_{spec["part"].split()[1]}_Socket_KiCadFrame'
    tag = spec['ref']
    dip_path = KICAD / f'{spec["dip"]}.step'
    chip = Part.Shape()
    chip.read(str(dip_path))
    chip_colours = face_colours(dip_path)
    check(f'{tag}: KiCad DIP is one solid with a colour per face', len(chip.Solids) == 1 and len(chip_colours) == len(chip.Faces))
    pins = sorted(s['centre'] for s in sections(chip, -1.0))
    check(f'{tag}: {spec["pins"]} chip pins found below the seat', len(pins) == spec['pins'], pins=len(pins))
    cx = (min(p[0] for p in pins) + max(p[0] for p in pins)) / 2
    cy = (min(p[1] for p in pins) + max(p[1] for p in pins)) / 2
    pin1 = min(pins, key=lambda p: math.hypot(*p))
    check(f'{tag}: chip pin 1 at the model origin', math.hypot(*pin1) < 1e-3)
    with zipfile.ZipFile(HERE / 'sources' / spec['socket']) as z:
        (inner,) = z.namelist()
        data = z.read(inner)
    info = EVIDENCE['manufacturer_models'][spec['socket']]
    check(f'{tag}: TE model matches the recorded hash', hashlib.sha256(data).hexdigest() == info['inner_sha256'])
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / inner
        p.write_bytes(data)
        socket = Part.Shape()
        socket.read(str(p))
    check(f'{tag}: TE socket is one valid solid with its top at z=0', socket.isValid() and len(socket.Solids) == 1 and
          abs(socket.BoundBox.ZMax) < 1e-6 and abs(socket.BoundBox.ZMin + 8.1) < 1e-6)
    sb = socket.BoundBox
    # Notch end: the end wall with less material carries the pin-1 notch.
    ends = {s: socket.common(Part.makeBox(1.5, sb.YLength + 2, 10.1, V(x, sb.YMin - 1, sb.ZMin - 1))).Volume
            for s, x in ((-1, sb.XMin), (1, sb.XMax - 1.5))}
    notch = min(ends, key=ends.get)
    check(f'{tag}: socket notch end identified', abs(ends[1] - ends[-1]) > 0.5, end_volumes=ends, notch_end='+X' if notch > 0 else '-X')
    original_volume = socket.Volume
    # Rotate the socket's long axis onto the chip's pin columns with the notch toward pin 1, seat on the board.
    # The row-spacing axis has exactly two distinct pin coordinates; the pin columns run along the other axis.
    long_axis_chip = V(0, 1, 0) if len({round(p[0], 3) for p in pins}) == 2 else V(1, 0, 0)
    towards_pin1 = V(pin1[0] - cx, pin1[1] - cy, 0)
    towards_pin1 = V(long_axis_chip.x * math.copysign(1, towards_pin1.x) if long_axis_chip.x else 0,
                     long_axis_chip.y * math.copysign(1, towards_pin1.y) if long_axis_chip.y else 0, 0)
    angle = math.degrees(math.atan2(towards_pin1.y, towards_pin1.x)) - (0 if notch > 0 else 180)
    socket.rotate(V(0, 0, 0), V(0, 0, 1), angle)
    socket.translate(V(cx, cy, SEAT))
    check(f'{tag}: socket geometry unchanged by placement (volume)', abs(socket.Volume - original_volume) < 1e-6)
    tails = sorted(s['centre'] for s in sections(socket, -1.5))
    worst = max(min(math.hypot(t[0] - p[0], t[1] - p[1]) for p in pins) for t in tails) if tails else 9
    check(f'{tag}: every socket tail lies on a chip pin axis (and so on its pad)', len(tails) == spec['pins'] and worst < 1e-3, worst_mm=worst)
    tail_sizes = {tuple(round(v, 3) for v in sorted(s['size'])) for s in sections(socket, -0.8)}
    check(f'{tag}: tails are 0.17 x 0.60 mm flats, diagonal inside the 0.8128 mm drill',
          tail_sizes == {(0.17, 0.6)} and math.hypot(0.17, 0.6) < 0.8128, tail_sizes=sorted(tail_sizes),
          nominal_corner_margin_mm=round(0.8128 / 2 - math.hypot(0.17, 0.6) / 2, 4))
    check(f'{tag}: socket seating plane on the board and top {SEAT} mm above it',
          abs(socket.BoundBox.ZMax - SEAT) < 1e-6 and abs(socket.BoundBox.ZMin - (SEAT - 8.1)) < 1e-6)
    pb = socket.BoundBox
    end_slab = lambda lo: socket.common(Part.makeBox(*((1.5, pb.YLength + 2) if long_axis_chip.x else (pb.XLength + 2, 1.5)), 10.1,  # noqa: E731
                                                      V(lo, pb.YMin - 1, -4) if long_axis_chip.x else V(pb.XMin - 1, lo, -4))).Volume
    lo_end, hi_end = (end_slab(pb.XMin), end_slab(pb.XMax - 1.5)) if long_axis_chip.x else (end_slab(pb.YMin), end_slab(pb.YMax - 1.5))
    pin1_high = (pin1[0] - cx if long_axis_chip.x else pin1[1] - cy) > 0
    check(f'{tag}: placed socket notch (lighter end wall) is at the chip pin-1 end', (hi_end < lo_end) == pin1_high,
          end_volumes=[round(lo_end, 3), round(hi_end, 3)])
    chip.translate(V(0, 0, SEAT))
    cb = chip.BoundBox
    body = [f for f, c in zip(chip.Faces, chip_colours) if c[0] < 0.5]
    body_bottom = min(f.BoundBox.ZMin for f in body)
    check(f'{tag}: raised chip body clears the socket top and its pin tips stay above the board',
          body_bottom >= SEAT - 1e-6 and cb.ZMin > 0, body_bottom_mm=round(body_bottom, 3), pin_tip_mm=round(cb.ZMin, 3))
    # Contact faces run from inside the housing through the board; any face reaching below the board is contact metal.
    socket_colours = [TIN if f.BoundBox.ZMin < -1e-6 else BLACK for f in socket.Faces]
    check(f'{tag}: contact faces reaching below the board are tin; every black face lies on or above the board',
          sum(c == TIN for c in socket_colours) > 0 and all(f.BoundBox.ZMin >= -1e-6 for f, c in zip(socket.Faces, socket_colours) if c == BLACK))
    out = HERE / f'{name}.step'
    doc = App.newDocument(tag)
    objs = []
    for n, s in (('TE_Socket', socket), ('KiCad_DIP_Chip_Raised', chip)):
        o = doc.addObject('Part::Feature', n)
        o.Shape = s
        objs.append(o)
    doc.recompute()
    Part.export(objs, str(out))
    App.closeDocument(doc.Name)
    back = Part.read(str(out))
    order_ok = len(back.Solids) == 2 and all(len(a.Faces) == len(b.Faces) and abs(a.Volume - b.Volume) < 1e-6
                                             for a, b in zip(back.Solids, (socket, chip)))
    check(f'{tag}: saved STEP keeps socket and chip solids, faces and volumes in order', order_ok)
    add_face_styles(out, [socket_colours, [tuple(c) for c in chip_colours]], ['TE_Socket', 'KiCad_DIP_Chip_Raised'])
    out.write_text('\n'.join(line.rstrip() for line in out.read_text().splitlines()) + '\n')
    styled = len(re.findall(r"STYLED_ITEM\(''", out.read_text()))
    check(f'{tag}: every face carries a colour style', styled == len(socket.Faces) + len(chip.Faces), styled=styled)
    overlap = socket.common(chip).Volume
    models[spec['ref']] = dict(output=out.name, output_sha256=sha(out), footprint=spec['footprint'], part=spec['part'],
                               socket_source=spec['socket'], socket_inner_sha256=info['inner_sha256'],
                               chip_source=f'KiCad/Package_DIP.3dshapes/{spec["dip"]}.step', chip_source_sha256=sha(dip_path),
                               seat_mm=SEAT, rotation_deg=angle, socket_centre_model_mm=[cx, cy],
                               chip_top_above_board_mm=round(cb.ZMax, 3), socket_outline_mm=[round(socket.BoundBox.XLength, 3), round(socket.BoundBox.YLength, 3)],
                               chip_pins_inside_socket_contacts_overlap_mm3=round(overlap, 3), colours=dict(housing=BLACK, tails=TIN))
report = dict(schema=1, revision=23, generator='build_sockets.py', passed=all(c['passed'] for c in checks), check_count=len(checks), checks=checks,
              models=models, evidence=dict(file='sources/socket-evidence.json', sha256=sha(HERE / 'sources/socket-evidence.json')),
              limitations=['TE models are for the 1- prefixed lead-free successors of the BOM part numbers; identical geometry is assumed.',
                           'The chip seating height (lead shoulders on the socket top, 5.10 mm) is assumed; TE customer drawings could not be retrieved.',
                           'TE models are single fused solids; contact faces that reach below the board are tin, while contact openings on top stay black.',
                           'Chip pins overlap the fused socket contacts inside the housing; this is hidden and not a fit claim.',
                           'Physical fit is unqualified.'],
              physical_fit_qualified=False)
(HERE / 'socket-model-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(passed=report['passed'], check_count=len(checks), models={k: (v['output'], v['rotation_deg'], v['chip_top_above_board_mm']) for k, v in models.items()}), indent=2))
assert report['passed']
