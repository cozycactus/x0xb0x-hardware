"""Refill the mainboard pours and take the I/O rear-plate datum off Edge.Cuts (KiCad revision 27).

1. Mainboard zone fill. Revision 26 lengthened the 27 SIP9 pads of IC14, IC15A and IC15B but
   kept the saved F.Cu GND fill, which still cleared the shorter pads: as saved and plotted it
   touches 23 of them (KiCad DRC without refill: 23 clearance violations at 0.000 mm and 23
   solder-mask bridges). Revision 26's DRC refilled the zones before checking. A temporary copy
   is refilled with KiCad's zone filler (refill_zones.py); only the filled_polygon nodes of the
   two zones are copied from it into the working file. Zone outlines, priorities, clearances,
   thermal settings and every other node stay byte for byte.
2. I/O Edge.Cuts. Four 0.0254 mm lines on the original Eagle Dimension layer draw the rear-plate
   section, 222.25 x 1.651 mm, 0.508 mm behind the rear edge (the Blender rear-plate datum). On
   Edge.Cuts they form a second closed board outline that a fab would cut. They move to
   Dwgs.User, beside the detached datum line the importer already put there; only their layer
   node changes.

Run from the repository root:
  python3 -I kicad-working/validation/models-review-27/install_zone_fill_and_datum_layer.py
Needs KiCad 10.0.7 (kicad-cli and its Python).
"""
import collections
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parents[1]
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
PY = os.environ.get('KICAD_PYTHON',
                    '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
digest = lambda s: hashlib.sha256(s.encode()).hexdigest()  # noqa: E731
DATUM = {  # uuid: (start, end) in KiCad coordinates, width 0.0254 mm
    '17bb7a95-868c-435d-a637-3f311729a2a1': ((-4.064, 0.508), (218.186, 0.508)),
    'a9f41b20-420d-4a7b-87e5-d6962381e8ef': ((-4.064, 2.159), (-4.064, 0.508)),
    'ba5bb9d7-e510-4da8-a52d-f49f18435b21': ((218.186, 0.508), (218.186, 2.159)),
    'cecb0a24-35d8-45d2-8a23-0ab4fd509f3c': ((218.186, 2.159), (-4.064, 2.159)),
}
tmp = Path(tempfile.mkdtemp(prefix='x0xb0x-rev27-'))
env = dict(os.environ, KICAD_CONFIG_HOME=str(tmp / 'config'), XDG_CACHE_HOME=str(tmp / 'cache'))


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=env)
    assert r.returncode in (0, 5), (cmd, r.stderr[-800:])
    return r


def node_end(text, start):
    """Index just past the s-expression that opens at text[start] == '('."""
    depth, i, quoted = 0, start, False
    while True:
        c = text[i]
        if quoted:
            if c == '\\':
                i += 1
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1


def zones(text):
    """uuid -> (zone start, zone end, fill start, fill end, count): the filled_polygon children are one run at
    the end, separated only by whitespace (the digital pour keeps two blank lines after it, which stay)."""
    out = {}
    for m in re.finditer(r'\n\t\(zone\n', text):
        s = m.start() + 1
        e = node_end(text, s)
        fills = [s + f.start() + 1 for f in re.finditer(r'\n\t\t\(filled_polygon\n', text[s:e])]
        assert fills
        fe = node_end(text, fills[-1])
        assert not text[fe:e - 1].strip(), 'filled polygons are not the last children'
        for a, b in zip(fills, fills[1:]):
            assert not text[node_end(text, a):b].strip(), 'filled polygons are not contiguous'
        u = re.search(r'\n\t\t\(uuid "([^"]+)"\)', text[s:e]).group(1)
        out[u] = (s, e, fills[0], fe, len(fills))
    return out


def refilled(path):
    out = tmp / ('refilled-' + Path(path).name)
    r = subprocess.run([PY, '-I', str(H / 'refill_zones.py'), str(path), str(out)], capture_output=True, text=True,
                       env=env)
    assert r.returncode == 0, r.stderr[-800:]
    return out.read_text()


def drc(path, label):
    out = tmp / f'{label}-drc.json'
    run([CLI, 'pcb', 'drc', '--format', 'json', '--units', 'mm', '--severity-all', '-o', out, path])
    return json.loads(out.read_text())


IGNORED = ('silk_over_copper', 'silk_overlap', 'silk_edge_clearance', 'track_dangling', 'lib_footprint_issues')

# 1. Mainboard filled polygons
mpath = W / 'mainboard/mainboard.kicad_pcb'
mold = mpath.read_text()
for ext in ('kicad_pcb', 'kicad_pro'):
    (tmp / 'before').mkdir(exist_ok=True)
    (tmp / 'before' / f'mainboard.{ext}').write_text((W / f'mainboard/mainboard.{ext}').read_text())
drc_before = drc(tmp / 'before/mainboard.kicad_pcb', 'mainboard-before')
saved = refilled(mpath)
zo, zs = zones(mold), zones(saved)
assert set(zo) == set(zs) and len(zo) == 2
edits, zone_rows = [], []
for u, (s, e, fs, fe, n) in sorted(zo.items(), key=lambda kv: kv[1][0]):
    s2, e2, fs2, fe2, n2 = zs[u]
    assert mold[s:fs] == saved[s2:fs2], f'zone {u}: a node other than filled_polygon differs'
    edits.append((fs, fe, saved[fs2:fe2]))
    zone_rows.append(dict(uuid=u, priority=int(re.search(r'\(priority (\d+)\)', mold[s:e]).group(1)),
                          filled_polygons_before=n, filled_polygons_after=n2,
                          fill_bytes_before=fe - fs, fill_bytes_after=fe2 - fs2,
                          fill_sha256_before=digest(mold[fs:fe]), fill_sha256_after=digest(saved[fs2:fe2])))
mnew, last, parts = None, 0, []
for a, b, text in sorted(edits):
    parts += [mold[last:a], text]
    last = b
mnew = ''.join(parts + [mold[last:]])
undo = mnew
for (a, b, text), (u, (s, e, fs, fe, n)) in zip(sorted(edits, reverse=True),
                                               sorted(zones(mnew).items(), key=lambda kv: -kv[1][0])):
    undo = undo[:fs] + mold[a:b] + undo[fe:]
assert undo == mold, 'mainboard: bytes outside the filled polygons changed'

# 2. I/O datum lines
ipath = W / 'ioboard/ioboard.kicad_pcb'
iold = ipath.read_text()
inew, line_rows = iold, []
for u, (p1, p2) in DATUM.items():
    at = inew.index(f'(uuid "{u}")')
    s = inew.rfind('\n\t(gr_line\n', 0, at) + 1
    e = node_end(inew, s)
    node = inew[s:e]
    nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', re.search(r'\(start ([^)]*)\)', node).group(1) + ' ' +
                                                     re.search(r'\(end ([^)]*)\)', node).group(1))]
    assert nums == [*p1, *p2], (u, nums)
    assert '(width 0.0254)' in node and node.count('(layer "Edge.Cuts")') == 1, u
    inew = inew[:s] + node.replace('(layer "Edge.Cuts")', '(layer "Dwgs.User")') + inew[e:]
    line_rows.append(dict(uuid=u, start=list(p1), end=list(p2), width_mm=0.0254, before='Edge.Cuts', after='Dwgs.User'))
assert inew.count('(layer "Dwgs.User")') == iold.count('(layer "Dwgs.User")') + 4
diff_lines = [i for i, (a, b) in enumerate(zip(iold.splitlines(), inew.splitlines())) if a != b]
assert len(iold.splitlines()) == len(inew.splitlines()) and len(diff_lines) == 4
assert all(inew.splitlines()[i].strip() == '(layer "Dwgs.User")' for i in diff_lines)

# outline after the move: the Edge.Cuts gr_lines form one closed rectangle
edge = []
for m in re.finditer(r'\n\t\(gr_line\n', inew):
    node = inew[m.start() + 1:node_end(inew, m.start() + 1)]
    if '(layer "Edge.Cuts")' in node:
        a = tuple(float(v) for v in re.search(r'\(start ([^)]*)\)', node).group(1).split())
        b = tuple(float(v) for v in re.search(r'\(end ([^)]*)\)', node).group(1).split())
        edge.append((a, b))
ends = collections.Counter(p for seg in edge for p in seg)
assert len(edge) == 4 and all(n == 2 for n in ends.values()) and len(ends) == 4, edge
xs, ys = [p[0] for p in ends], [p[1] for p in ends]
outline = [round(max(xs) - min(xs), 4), round(max(ys) - min(ys), 4)]

# write, then check the written boards with KiCad (DRC of the saved copper, no refill; refill is idempotent)
mpath.write_text(mnew)
ipath.write_text(inew)
for b in ('mainboard', 'ioboard'):
    (tmp / 'after').mkdir(exist_ok=True)
    for ext in ('kicad_pcb', 'kicad_pro'):
        (tmp / 'after' / f'{b}.{ext}').write_text((W / f'{b}/{b}.{ext}').read_text())
drc_after = {b: drc(tmp / f'after/{b}.kicad_pcb', f'{b}-after') for b in ('mainboard', 'ioboard')}
again = refilled(mpath)
za, zg = zones(mnew), zones(again)
idempotent = all(mnew[za[u][2]:za[u][3]] == again[zg[u][2]:zg[u][3]] for u in za)
copper = lambda d: collections.Counter(v['type'] for v in d['violations'] if v['type'] not in IGNORED)  # noqa: E731
checks = dict(
    mainboard_saved_copper_violations_before=dict(copper(drc_before)),
    mainboard_saved_copper_violations_after=dict(copper(drc_after['mainboard'])),
    ioboard_saved_copper_violations_after=dict(copper(drc_after['ioboard'])),
    ioboard_silk_edge_clearance_after=sum(1 for v in drc_after['ioboard']['violations']
                                          if v['type'] == 'silk_edge_clearance'),
    mainboard_refill_of_installed_fill_identical=idempotent,
    ioboard_edge_cuts_contours=1, ioboard_board_outline_mm=outline)
passed = (not checks['mainboard_saved_copper_violations_after'] and not checks['ioboard_saved_copper_violations_after']
          and idempotent and outline == [213.36, 44.45])
assert passed, checks

summary = json.loads((W / 'validation/working-validation-summary-revision-26.json').read_text())
files = [dict(file='mainboard/mainboard.kicad_pcb', before_sha256=digest(mold), after_sha256=sha(mpath),
              zones=zone_rows),
         dict(file='ioboard/ioboard.kicad_pcb', before_sha256=digest(iold), after_sha256=sha(ipath),
              lines_moved=line_rows)]
changed = sorted(f['file'] for f in files)
assert all(f in summary['outputs'] for f in changed)
audit = dict(
    passed=True, files=files, checks=checks,
    mainboard_saved_copper_violations_before=[
        dict(type=v['type'], description=v['description'],
             items=[[i['description'], [i['pos']['x'], -i['pos']['y']]] for i in v['items']])
        for v in drc_before['violations'] if v['type'] not in IGNORED],
    previous_core_file_count=len(summary['outputs']), changed_previous_core_files=changed, new_core_files=[],
    scope=('Mainboard: the filled_polygon nodes of the two F.Cu GND zones, replaced by KiCad 10.0.7\'s refill. '
           'I/O board: the layer node of four rear-plate datum lines, Edge.Cuts to Dwgs.User. Zone outlines and '
           'settings, nets, tracks, vias, pads, drills, footprint poses, models and the schematics are unchanged.'))
(H / 'installation-audit.json').write_text(json.dumps(audit, indent=1) + '\n')
print(json.dumps(dict(passed=True, changed_previous_core_files=changed, checks=checks,
                      zones=[{k: z[k] for k in ('priority', 'filled_polygons_before', 'filled_polygons_after',
                                                'fill_bytes_before', 'fill_bytes_after')} for z in zone_rows]), indent=1))
