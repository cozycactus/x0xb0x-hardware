"""Audit lead presence and nominal hole fit on the native KiCad revision-21 exports.

Imports the GLB files written by export_native_boards.py and the pcbnew pad record,
then, in the board frame (no model-frame assumptions):

* every drilled pad of every fitted model must have model geometry inside its drill at
  mid-board depth, except the four Grayhill MT bracket holes whose legs the drawing does
  not define;
* for the 25 terminal-completed references and the 39 Xicon XRL electrolytics, each drilled pad's model section is measured at the top
  face, mid-depth and bottom face: the largest radial excess over the drill wall is the
  nominal interference (negative margin) and is reported, not corrected;
* geometry crossing the board away from every hole and the lead protrusion beyond the far
  face are reported.

Run read-only with Blender:
  Blender --background --factory-startup --python-exit-code 1 \
      --python kicad-working/validation/models-review-21/audit_native_terminals.py
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
PROBES = HERE / 'native-probes'
sys.path.insert(0, str(HERE.parent / 'models-review-16/terminal-quality'))
from terminal_spec import MODELS  # noqa: E402

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
record = json.loads((HERE / 'native-export-record.json').read_text())
pads = json.loads((PROBES / 'pads.json').read_text())
assert sha(PROBES / 'pads.json') == record['pads_sha256']
OUTPUTS = {spec['output']: key for key, spec in MODELS.items()}
OUTPUTS['Kobiconn1542442E_DrawingDerived_Terminals.step'] = 'USB'
OUTPUTS['Microohm_LPTC12_PrimaryDimensions_Terminals.step'] = 'LPTC'
OUTPUTS['CP_Xicon_XRL_D5.0x11_P2.54_KiCadFrame.step'] = 'XRL_D5'
OUTPUTS['CP_Xicon_XRL_D6.3x11_P2.54_KiCadFrame.step'] = 'XRL_D6.3'
OUTPUTS['CP_Xicon_XRL_D10x12.5_P5.08_KiCadFrame.step'] = 'XRL_D10'
OUTPUTS['CP_Xicon_XRL1u50_P3.556_PhotoColours.step'] = 'XRL_C17'
OUTPUTS['CP_Xicon_XRL2200u16_P5.08_PhotoColours.step'] = 'XRL_C3_C5'
BY_DESIGN_EMPTY = {('Grayhill25L', n): 'Holes for the optional 25J5155 mounting bracket; the BOM part 25LB22-H has no -Z bracket suffix'
                   for n in ('MT1', 'MT2', 'MT3', 'MT4')}
FACE_INSET = 0.02


def world_tris(root):
    out = []
    for o in [root, *root.children_recursive]:
        if o.type != 'MESH' or not o.data.polygons:
            continue
        m = np.array(o.matrix_world)
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get('co', co)
        w = (co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]) * 1000
        o.data.calc_loop_triangles()
        t = np.empty(len(o.data.loop_triangles) * 3, dtype=np.int64)
        o.data.loop_triangles.foreach_get('vertices', t)
        out.append(w[t.reshape(-1, 3)])
    return np.vstack(out) if out else np.zeros((0, 3, 3))


def section(tris, z):
    s = tris[:, :, 2] - z
    cross = (s.min(1) < 0) & (s.max(1) > 0)
    pts = []
    for tri, ss in zip(tris[cross], s[cross]):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if (ss[a] < 0) != (ss[b] < 0):
                pts.append((tri[a] + (tri[b] - tri[a]) * (ss[a] / (ss[a] - ss[b])))[:2])
    return np.array(pts) if pts else np.zeros((0, 2))


def drill_distance(points, pad):
    """Distance of each point from the drill axis (segment for slots) and the drill radius."""
    cx, cy = pad['x_mm'], -pad['y_mm']
    dx, dy = pad['drill_mm']
    r = min(dx, dy) / 2
    half = max(dx, dy) / 2 - r
    ang = math.radians(pad['orientation_deg'])
    u = np.array((math.cos(ang), math.sin(ang)) if dx >= dy else (-math.sin(ang), math.cos(ang)))
    rel = points - np.array([cx, cy])
    t = np.clip(rel @ u, -half, half)
    return np.linalg.norm(rel - np.outer(t, u), axis=1), r


def main():
    checks, boards, detail = [], {}, {}

    def check(name, ok, **extra):
        checks.append(dict(check=name, passed=bool(ok), **extra))

    for board in ('ioboard', 'mainboard'):
        glb = PROBES / f'{board}.glb'
        check(f'{board}: GLB matches export record', sha(glb) == record['boards'][board]['glb_sha256'])
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(glb))
        base = next(o for o in bpy.data.objects if o.parent is None)
        roots = {o.name: o for o in base.children}
        thickness = pads[board]['thickness_mm']
        fps = {f['reference']: f for f in pads[board]['footprints']}
        tops = {round(roots[r].matrix_world.translation.z * 1000, 4) for r, f in fps.items()
                if r in roots and not f['flipped']}
        bottoms = {round(roots[r].matrix_world.translation.z * 1000, 4) for r, f in fps.items()
                   if r in roots and f['flipped']}
        top = max(tops)
        bottom = top - thickness
        # KiCad seats bottom-side model roots a fixed 0.08 mm beyond the bare-board face; recorded, not corrected.
        check(f'{board}: top and bottom component roots each share one seating plane',
              len(tops) == 1 and len(bottoms) <= 1, top=top, bottom=bottom, bottom_roots=sorted(bottoms))
        status = {}
        for ref, fp in fps.items():
            if not fp['models'] or ref not in roots:
                continue
            key = next((OUTPUTS[m.split('/')[-1]] for m in fp['models'] if m.split('/')[-1] in OUTPUTS), None)
            tris = world_tris(roots[ref])
            drilled = [p for p in fp['pads'] if p['attribute'] in ('PTH', 'NPTH')]
            mid = section(tris, top - thickness / 2)
            empty = []
            for p in drilled:
                d, r = drill_distance(mid, p) if len(mid) else (np.zeros(0), 0)
                if not (d < r).any() and (key, p['number']) not in BY_DESIGN_EMPTY:
                    empty.append(p['number'])
            status[ref] = 'all pins' if not empty else 'missing: ' + ','.join(empty)
            if key is None:
                continue
            heights = dict(top_face=top - FACE_INSET, mid=top - thickness / 2, bottom_face=bottom + FACE_INSET)
            sections = {h: section(tris, z) for h, z in heights.items()}
            # Each section point belongs to the pad whose drill wall is nearest (neighbouring leads at
            # 2.0-2.5 mm pitch must not count against a pad); points over 1 mm outside every wall are stray.
            excess_by_height = {}
            for h, pts in sections.items():
                e = (np.array([drill_distance(pts, p)[0] - drill_distance(pts, p)[1] for p in drilled])
                     if len(pts) else np.zeros((len(drilled), 0)))
                owner = e.argmin(0) if len(pts) else np.zeros(0, int)
                assigned = (e.min(0) < 1.0) if len(pts) else np.zeros(0, bool)
                excess_by_height[h] = (e, owner, assigned)
            rows = []
            for i, p in enumerate(drilled):
                row = dict(pad=p['number'], drill_mm=p['drill_mm'], centre_mm=[p['x_mm'], -p['y_mm']])
                worst, centres = None, []
                for h, pts in sections.items():
                    e, owner, assigned = excess_by_height[h]
                    near = assigned & (owner == i)
                    if not near.any():
                        continue
                    excess = float(e[i][near].max())
                    worst = excess if worst is None else max(worst, excess)
                    q = pts[near]
                    centres.append(((q.min(0) + q.max(0)) / 2 - np.array(row['centre_mm'])).tolist())
                if (key, p['number']) in BY_DESIGN_EMPTY:
                    row.update(result='empty by design', reason=BY_DESIGN_EMPTY[(key, p['number'])])
                elif worst is None:
                    row.update(result='no terminal found')
                else:
                    in_hole = (drill_distance(mid, p)[0] < drill_distance(mid, p)[1]).any() if len(mid) else False
                    row.update(result=('fits' if worst <= 0 else 'interferes' if in_hole else 'misses hole'),
                               margin_mm=round(-worst, 4),
                               section_centre_offset_mm=[round(float(np.mean([c[i] for c in centres])), 4)
                                                         for i in (0, 1)])
                rows.append(row)
            stray = {h: int((~excess_by_height[h][2]).sum()) for h in sections}
            if fp['flipped']:
                protrusion = float(tris[:, :, 2].max() - top)
            else:
                protrusion = float(bottom - tris[:, :, 2].min())
            detail.setdefault(key, {})[ref] = dict(board=board, flipped=fp['flipped'], pads=rows,
                                                   section_points_away_from_holes=stray,
                                                   lead_protrusion_beyond_far_face_mm=round(protrusion, 4))
        counts = {}
        for s in status.values():
            counts['all pins' if s == 'all pins' else 'missing'] = counts.get(
                'all pins' if s == 'all pins' else 'missing', 0) + 1
        boards[board] = dict(board_top_mm=top, board_bottom_mm=bottom, fitted_models=len(status), counts=counts,
                             missing={r: s for r, s in status.items() if s != 'all pins'})
        check(f'{board}: every fitted model has a lead in every drilled hole', not boards[board]['missing'],
              missing=boards[board]['missing'])
    check('491 fitted models audited', sum(b['fitted_models'] for b in boards.values()) == 491)
    check('All 64 terminal-completed and electrolytic references audited', sum(len(v) for v in detail.values()) == 64)
    for key, refs in detail.items():
        first = next(iter(refs.values()))
        same = all(len(v['pads']) == len(first['pads']) and all(
            a['pad'] == b['pad'] and a['result'] == b['result'] and
            abs(a.get('margin_mm', 0) - b.get('margin_mm', 0)) < 1e-3 for a, b in zip(v['pads'], first['pads']))
            for v in refs.values())
        check(f'{key}: identical nominal fit at every placed reference', same)
        check(f'{key}: every specified terminal is found at its pad',
              all(r['result'] != 'no terminal found' for v in refs.values() for r in v['pads']))
    findings = []
    for key, refs in detail.items():
        ref, v = next(iter(refs.items()))
        for r in v['pads']:
            if r['result'] in ('interferes', 'misses hole'):
                findings.append(dict(model=key, references=sorted(refs), pad=r['pad'], result=r['result'],
                                     margin_mm=r['margin_mm'], drill_mm=r['drill_mm'],
                                     section_centre_offset_mm=r['section_centre_offset_mm']))
    report = dict(schema=1, revision=21, generator='audit_native_terminals.py', blender=bpy.app.version_string,
                  passed=all(c['passed'] for c in checks), check_count=len(checks), checks=checks,
                  boards=boards, nominal_fit_findings=findings, models=detail,
                  method='Triangle sections of the native KiCad GLB at the board faces (0.02 mm inside) and mid-depth; '
                         'margin = drill radius minus the largest distance of nearby section points from the drill axis.',
                  physical_fit_qualified=False)
    (HERE / 'native-terminal-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('passed', 'check_count', 'boards')}, indent=1))
    for f in findings:
        print('FINDING', f)
    for c in checks:
        if not c['passed']:
            print('FAIL', c)
    if not report['passed']:
        raise SystemExit(1)


main()
