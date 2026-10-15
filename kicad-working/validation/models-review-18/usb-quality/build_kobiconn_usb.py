"""Correct the USB illustration from the recovered BOM connector drawing.

Independent reconstruction: CC0-1.0. Source drawings retain their own rights.
The old outer envelope and mating cavity are retained, lifted onto the printed
0.38 mm body-to-PCB gap. Signal-pin exit insulation and gold mating strips are
explicit illustrations; neither their unprinted dimensions nor internal routing
is represented as manufacturer CAD or physical fit qualification.
"""
from pathlib import Path
import ast
import hashlib
import json
import math
import re
import sys

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Import
import Part
import Mesh

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK.parent
OLD = WORK / 'ioboard/3dmodels/Revision13/terminals/USB_TypeB-body-illustration_Terminals.step'
PDF = HERE / 'sources/kobiconn-154-2442-e-kc301021-2006.pdf'
OUTPUT = HERE / 'Kobiconn1542442E_DrawingDerived_Terminals.step'
V = App.Vector
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
guards = {str(p): sha(p) for p in [OLD, PDF, WORK / 'ioboard/ioboard.kicad_pcb', WORK / 'mainboard/mainboard.kicad_pcb']}
helpers = WORK / 'validation/models-review-13/terminal-quality/build_terminals.py'
tree = ast.parse(helpers.read_text())
names = {'box', 'extrude_poly', 'blade', 'brep_colors'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), str(helpers), 'exec'))
legacy = WORK / 'visualization/blender-case-revision-7/quality-model-sources/rear-quality/build_rear_quality.py'
tree = ast.parse(legacy.read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'face_colors'], type_ignores=[]), str(legacy), 'exec'))

old = Part.Shape(); old.read(str(OLD))
assert old.isValid() and len(old.Solids) == 8
old_palette = brep_colors(OLD)
assert len(old_palette) == 8
shell, insulator = [s.copy() for s in old.Solids[:2]]
for s in [shell, insulator]: s.translate(V(0, 0, .38))
signals = [('1', 1.25, 14.99), ('2', -1.25, 14.99), ('3', -1.25, 12.99), ('4', 1.25, 12.99)]
pins = []
for pin, x, y in signals:
    # Pin section is retained as the earlier 0.40 mm square illustration.
    # The source dimensions its projection, not the pin stock or exit skirt.
    pin_shape = blade(dict(x=x, y=y, w=.4, t=.4, z_top=1.2,
                           z_tip=-2.91, face='xz', tip='point', eyelet=None))
    pins.append(pin_shape)
    shell = shell.cut(box(x-.55, y-.55, .30, x+.55, y+.55, 1.15))
    insulator = insulator.fuse(box(x-.48, y-.48, .38, x+.48, y+.48, .95))
locks = [blade(dict(x=x, y=10.28, w=2.4, t=.30, z_top=1.0,
                    z_tip=-3.72, face='yz', tip='fork', eyelet=None)) for x in [-6.02, 6.02]]
pins += locks
# Front view labels two upper and two lower contact positions. The strip size
# and visible length are illustrative, with no assertion about hidden routing.
gold = []
for x in [-1.25, 1.25]:
    gold.append(box(x-.20, 1.5, 6.67, x+.20, 6.0, 6.77))
    gold.append(box(x-.20, 1.5, 4.49, x+.20, 6.0, 4.59))
for metal in pins[:4] + gold:
    insulator = insulator.cut(metal)
shell = shell.removeSplitter()
insulator = insulator.removeSplitter()
parts = [('Shell', shell), ('Insulator', insulator),
         ('DrawingDerivedTerminals', Part.makeCompound(pins)), ('MatingContacts', Part.makeCompound(gold))]
TIN = (0.74, .75, .76)
GOLD = (.82, .68, .20)
colours = [old_palette[0], old_palette[1]] + [TIN]*6 + [GOLD]*4
doc = App.newDocument('KobiconnUSB')
assembly = doc.addObject('App::Part', 'Assembly')
assembly.Label = 'Kobiconn1542442E_DrawingDerived_Terminals'
for i, (name, shape) in enumerate(parts):
    obj = doc.addObject('Part::Feature', f'P{i:02d}')
    obj.Label = name; obj.Shape = shape
    assembly.addObject(obj)
    Mesh.Mesh(shape.tessellate(.025)).write(str(HERE / (name + '.stl')))
doc.recompute()
Import.export([assembly], str(OUTPUT))
face_colors(OUTPUT, [list(c) for c in colours])
# OpenCascade's harmless continuation spaces are removed before hashing.
OUTPUT.write_text('\n'.join(line.rstrip() for line in OUTPUT.read_text().splitlines()) + '\n')
doc.saveAs(str(HERE / 'Kobiconn1542442E_DrawingDerived_Terminals.FCStd'))
App.closeDocument(doc.Name)
saved = Part.Shape(); saved.read(str(OUTPUT))
checks = []
def check(name, passed, **details): checks.append(dict(check=name, passed=bool(passed), **details))
def bounds(s):
    b=s.BoundBox
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
check('Saved STEP is valid with12 positive solids', saved.isValid() and len(saved.Solids)==12 and all(s.Volume>0 for s in saved.Solids))
check('Shell retains printed body envelope at0.38mm PCB gap',
      max(abs(a-b) for a,b in zip(bounds(shell),[-6.02,0,.38,6.02,16,11]))<1e-7, bounds_mm=bounds(shell))
check('Outer body XY width/depth and original mating cavity are retained',
      shell.common(box(-7,-.01,1.79,7,1.15,9.59)).Volume <= old.Solids[0].common(box(-7,-.01,1.41,7,1.15,9.21)).Volume+1e-5)
baseline_intersections=[]
for i,(pin,x,y) in enumerate(signals):
    p=saved.Solids[2+i]
    hit=p.common(saved.Solids[0]).Volume
    old_hit=old.Solids[2+i].common(old.Solids[0]).Volume
    baseline_intersections.append(old_hit)
    check('Signal'+pin+' printed2.91mm projection', abs(p.BoundBox.ZMin+2.91)<1e-7, tip_z_mm=p.BoundBox.ZMin)
    check('Signal'+pin+' XY axes retained', abs(p.BoundBox.Center.x-x)<1e-7 and abs(p.BoundBox.Center.y-y)<1e-7)
    check('Signal'+pin+' has no conductive shell intersection', hit<1e-9 and p.distToShape(saved.Solids[0])[0]>.20,
          shell_intersection_mm3=hit, shell_gap_mm=p.distToShape(saved.Solids[0])[0])
    check('Signal'+pin+' exits through insulator', p.distToShape(saved.Solids[1])[0]<1e-7 and p.common(saved.Solids[1]).Volume<1e-9)
check('Regression reproduces all four old signal/shell intersections', all(v>.01 for v in baseline_intersections), old_intersections_mm3=baseline_intersections)
for i,p in enumerate(saved.Solids[6:8]):
    check('Mounting tab'+str(i+1)+' printed3.72mm projection', abs(p.BoundBox.ZMin+3.72)<1e-7, tip_z_mm=p.BoundBox.ZMin)
    check('Mounting tab'+str(i+1)+' joins metal shell', p.common(saved.Solids[0]).Volume>.01)
for i,p in enumerate(saved.Solids[8:]):
    check('Gold mating strip'+str(i+1)+' contacts insulator and clears shield',
          p.distToShape(saved.Solids[1])[0]<1e-7 and p.distToShape(saved.Solids[0])[0]>.10)
check('Four named assembly parts retained in STEP', re.findall(r"PRODUCT\('([^']*)'", OUTPUT.read_text())[1:]==[n for n,s in parts])
check('STEP colours retain shell/white/tin plus gold mating surfaces', brep_colors(OUTPUT)==colours)
check('Source STEP, downloaded drawing and both PCBs remain byte-identical', all(sha(Path(p))==h for p,h in guards.items()))
limitations = ['Independent drawing-derived illustration, not manufacturer CAD or identification of the physically fitted connector.',
 'Body standoff and terminal projections follow the2006 BOM part drawing; original XY axes, body envelope and mating cavity are preserved.',
 'Signal stock0.40mm square, board-lock width2.4mm/thickness0.30mm/fork shape, shell gauge, insulating exit skirts and gold-strip dimensions remain illustrative.',
 'Hidden internal contact routing, stamped spring features and exact mould/retention geometry are not reconstructed.',
 'Nominal board-lock interference remains documented; no PCB hole, copper, placement or tolerance change.']
report=dict(passed=all(c['passed'] for c in checks),check_count=len(checks),checks=checks,
 source=str(OLD.relative_to(WORK)),source_sha256=guards[str(OLD)],
 drawing=dict(path=str(PDF.relative_to(REPO)),sha256=sha(PDF),url='https://www.mouser.com/catalog/specsheets/KC-301021.pdf',title='Kobiconn154-2442-E, KC-301021, revised2006-07-19',retrieved='User downloaded in browser; preserved byte-for-byte from Downloads/KC-301021.pdf'),
 model=OUTPUT.name,model_sha256=sha(OUTPUT),model_bytes=OUTPUT.stat().st_size,
 parts=[dict(name=n,solids=len(s.Solids),bounds_mm=bounds(s)) for n,s in parts],
 body_gap_mm=.38,signal_projection_mm=2.91,board_lock_projection_mm=3.72,
 old_signal_shell_intersections_mm3=baseline_intersections,
 source_and_PCB_read_only=True,limitations=limitations,physical_fit_qualified=False)
(HERE/'usb-model-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','parts']},indent=2),flush=True)
assert report['passed'],[c for c in checks if not c['passed']]
