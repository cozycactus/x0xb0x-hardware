# SPDX-License-Identifier: CC0-1.0
"""Small RS274X reader sufficient for KiCad 10 output (mm, FSLAX46Y46)."""
import math
import re


class Gerber:
    def __init__(self, path):
        self.apertures, self.flashes, self.draws, self.regions = {}, [], [], []
        self.unknown = []
        text = open(path).read()
        self._parse(text)

    def _parse(self, text):
        fmt_dec = 6
        tokens = re.findall(r'%[^%]*%|[^*%\n]+\*', text)
        x = y = 0.0
        interp, ap, region, polarity = 'G01', None, None, 'D'
        obj_attrs, ap_attrs = {}, {}
        for tok in tokens:
            if tok.startswith('%'):
                body = tok.strip('%')
                for cmd in [c for c in body.split('*') if c]:
                    if cmd.startswith('FS'):
                        fmt_dec = int(re.search(r'X(\d)(\d)', cmd).group(2))
                    elif cmd.startswith('MO'):
                        assert cmd == 'MOMM', cmd
                    elif cmd.startswith('AD'):
                        m = re.match(r'ADD(\d+)([^,]+),?(.*)', cmd)
                        params = [float(v) for v in m.group(3).split('X')] if m.group(3) else []
                        self.apertures[int(m.group(1))] = dict(shape=m.group(2), params=params,
                                                               function=ap_attrs.get('.AperFunction'))
                    elif cmd.startswith('TA'):
                        k, _, v = cmd[2:].partition(',')
                        ap_attrs[k] = v
                    elif cmd.startswith('TO'):
                        k, _, v = cmd[2:].partition(',')
                        obj_attrs[k] = v
                    elif cmd.startswith('TD'):
                        k = cmd[2:]
                        if not k:
                            obj_attrs, ap_attrs = {}, {}
                        else:
                            obj_attrs.pop(k, None)
                            ap_attrs.pop(k, None)
                    elif cmd.startswith('LP'):
                        polarity = cmd[2]
                    elif cmd.startswith(('TF', 'AM', 'IP', 'SR', 'LM', 'LR', 'LS')) or cmd[0].isdigit() or cmd[0] in '$-':
                        if cmd.startswith(('SR', 'LM', 'LR', 'LS')):
                            self.unknown.append(cmd)
                    else:
                        self.unknown.append(cmd)
                continue
            w = tok[:-1].strip()
            if not w or w.startswith('G04'):
                continue
            if w in ('G01', 'G02', 'G03'):
                interp = w
                continue
            if w == 'G75':
                continue
            if w == 'G36':
                region = []
                cur = []
                continue
            if w == 'G37':
                if cur:
                    region.append(cur)
                self.regions.append(dict(contours=region, polarity=polarity, attrs=dict(obj_attrs)))
                region = None
                continue
            if w == 'M02':
                break
            m = re.match(r'^(G0[123])?(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?(D0?[123]|D\d+)?$', w)
            if not m:
                self.unknown.append(w)
                continue
            if m.group(1):
                interp = m.group(1)
            d = m.group(6)
            if d and d not in ('D01', 'D02', 'D03', 'D1', 'D2', 'D3') and not (m.group(2) or m.group(3)):
                ap = int(d[1:])
                continue
            nx = int(m.group(2)) / 10 ** fmt_dec if m.group(2) is not None else x
            ny = int(m.group(3)) / 10 ** fmt_dec if m.group(3) is not None else y
            i = int(m.group(4)) / 10 ** fmt_dec if m.group(4) is not None else 0.0
            j = int(m.group(5)) / 10 ** fmt_dec if m.group(5) is not None else 0.0
            d = (d or 'D01').replace('D0', 'D')
            if d == 'D2':
                if region is not None and cur:
                    region.append(cur)
                    cur = []
                x, y = nx, ny
                if region is not None:
                    cur = [('M', x, y)]
                continue
            if d == 'D3':
                self.flashes.append(dict(ap=ap, pos=(nx, ny), polarity=polarity, attrs=dict(obj_attrs)))
                x, y = nx, ny
                continue
            # D1
            seg = dict(p1=(x, y), p2=(nx, ny), interp=interp,
                       center=(x + i, y + j) if interp != 'G01' else None)
            if region is not None:
                if not cur:
                    cur = [('M', x, y)]
                cur.append(('L' if interp == 'G01' else interp, nx, ny, seg['center']))
            else:
                seg.update(ap=ap, polarity=polarity, attrs=dict(obj_attrs))
                self.draws.append(seg)
            x, y = nx, ny


def contour_points(contour, step_deg=5.0):
    """Polyline approximation of a region contour."""
    pts = []
    for c in contour:
        if c[0] == 'M':
            pts.append((c[1], c[2]))
        elif c[0] == 'L':
            pts.append((c[1], c[2]))
        else:
            x0, y0 = pts[-1]
            cx, cy = c[3]
            r = math.hypot(x0 - cx, y0 - cy)
            a0 = math.atan2(y0 - cy, x0 - cx)
            a1 = math.atan2(c[2] - cy, c[1] - cx)
            if c[0] == 'G03':
                while a1 <= a0:
                    a1 += 2 * math.pi
            else:
                while a1 >= a0:
                    a1 -= 2 * math.pi
            n = max(2, int(abs(a1 - a0) / math.radians(step_deg)))
            for k in range(1, n + 1):
                a = a0 + (a1 - a0) * k / n
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts
