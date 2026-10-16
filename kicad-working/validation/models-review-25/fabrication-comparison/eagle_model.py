# SPDX-License-Identifier: CC0-1.0
"""Board-level geometry from the decoded Eagle 4.13 XML (repaired staging XML).

Coordinates are Eagle board coordinates in mm (y up), which equal KiCad's
Gerber coordinates (KiCad imported with y negated, Gerber negates it back).
Design-rule semantics follow Eagle 4.13: pad/via restring, stop frame.
"""
import math
import xml.etree.ElementTree as ET

# Eagle layer pairs swapped by mirroring an element
MIRROR = {1: 16, 16: 1, 21: 22, 22: 21, 25: 26, 26: 25, 27: 28, 28: 27, 29: 30, 30: 29,
          31: 32, 32: 31, 35: 36, 36: 35, 37: 38, 38: 37, 39: 40, 40: 39, 41: 42, 42: 41,
          43: 44, 44: 43, 51: 52, 52: 51}


def mm(v):
    if v is None:
        return None
    v = v.strip()
    if v.endswith('mil'):
        return float(v[:-3]) * 0.0254
    if v.endswith('mm'):
        return float(v[:-2])
    return float(v)


def rot_of(s):
    s = s or 'R0'
    mirror = 'M' in s
    spin = 'S' in s
    ang = float(s.replace('M', '').replace('S', '').replace('R', '') or 0)
    return mirror, ang, spin


class Xform:
    def __init__(self, x=0.0, y=0.0, rot='R0'):
        self.x, self.y = x, y
        self.mirror, self.ang, _ = rot_of(rot)

    def pt(self, px, py):
        # Eagle rotates the package first, then mirrors about the y axis
        a = math.radians(self.ang)
        c, s = math.cos(a), math.sin(a)
        rx, ry = px * c - py * s, px * s + py * c
        if self.mirror:
            rx = -rx
        return (self.x + rx, self.y + ry)

    def angle(self, local_rot):
        """Absolute (mirror, angle) of an object with local rotation string."""
        m, a, _ = rot_of(local_rot)
        a = a + self.ang
        if self.mirror:
            a = 180 - a
        return (m != self.mirror), a % 360

    def layer(self, l):
        return MIRROR.get(l, l) if self.mirror else l


def arc_center(x1, y1, x2, y2, curve):
    """Centre of an Eagle wire arc of signed sweep `curve` degrees (ccw positive)."""
    c = math.radians(curve)
    dx, dy = x2 - x1, y2 - y1
    d = math.hypot(dx, dy)
    r = d / 2 / math.sin(abs(c) / 2)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    h = math.sqrt(max(r * r - d * d / 4, 0.0))
    # centre lies to the left of the chord for ccw sweeps < 180
    nx, ny = -dy / d, dx / d
    sgn = 1 if (curve > 0) == (abs(curve) < 180) else -1
    return mx + sgn * h * nx, my + sgn * h * ny, r


class Board:
    def __init__(self, path):
        self.root = ET.parse(path).getroot()
        self.rules = {p.get('name'): p.get('value') for p in self.root.iter('param')}
        self.packages = {}
        for lib in self.root.iter('library'):
            for p in lib.iter('package'):
                self.packages[(lib.get('name'), p.get('name'))] = p
        self.wires, self.pads, self.smds, self.vias, self.holes = [], [], [], [], []
        self.circles, self.rects, self.polygons, self.texts = [], [], [], []
        self.signal_of = {}
        for sig in self.root.iter('signal'):
            for c in sig:
                if c.tag == 'contactref':
                    self.signal_of[(c.get('element'), c.get('pad'))] = sig.get('name')
        plain = self.root.find('.//plain')
        self._add_items(list(plain), Xform(), owner=None, signal=None)
        for sig in self.root.iter('signal'):
            self._add_items([c for c in sig if c.tag != 'contactref'], Xform(), owner=None,
                            signal=sig.get('name'))
        self.elements = list(self.root.iter('element'))
        for e in self.elements:
            pkg = self.packages[(e.get('library'), e.get('package'))]
            xf = Xform(mm(e.get('x')), mm(e.get('y')), e.get('rot'))
            self._add_items(list(pkg), xf, owner=e, signal=None)
            for tag, field in (('name', e.get('name')), ('value', e.get('value'))):
                c = e.find(tag)
                if c is None or c.get('layer') is None:
                    continue
                m, a, _ = rot_of(c.get('rot'))
                self.texts.append(dict(layer=int(c.get('layer')), pos=(mm(c.get('x')), mm(c.get('y'))),
                                       size=mm(c.get('size')), ratio=float(c.get('ratio') or 8), angle=a,
                                       mirror=m or c.get('mirrored') not in (None, '0', 'no'), text=field,
                                       element=e.get('name'), smashed=True))

    # -- design rules (Eagle 4.13)
    def _r(self, name, default):
        v = self.rules.get(name)
        return mm(v) if v is not None else default

    def pad_diameter(self, drill, lib_diam, layer='Top'):
        ring = min(max(self._r('rvPad' + layer, 0.25) * drill, self._r('rlMinPad' + layer, 0.254)),
                   self._r('rlMaxPad' + layer, 0.508))
        return max(lib_diam or 0.0, drill + 2 * ring)

    def via_diameter(self, drill, lib_diam):
        ring = min(max(self._r('rvViaOuter', 0.25) * drill, self._r('rlMinViaOuter', 0.2032)),
                   self._r('rlMaxViaOuter', 0.508))
        return max(lib_diam or 0.0, drill + 2 * ring)

    def stop_frame(self, size):
        return min(max(self._r('mvStopFrame', 1.0) * size, self._r('mlMinStopFrame', 0.1016)),
                   self._r('mlMaxStopFrame', 0.1016))

    def _add_items(self, items, xf, owner, signal):
        ename = owner.get('name') if owner is not None else None
        for c in items:
            t = c.tag
            if t == 'wire':
                l = xf.layer(int(c.get('layer')))
                p1 = xf.pt(mm(c.get('x1')), mm(c.get('y1')))
                p2 = xf.pt(mm(c.get('x2')), mm(c.get('y2')))
                curve = float(c.get('curve')) if c.get('curve') else 0.0
                if xf.mirror:
                    curve = -curve
                self.wires.append(dict(layer=l, p1=p1, p2=p2, width=mm(c.get('width')), curve=curve,
                                       signal=signal, element=ename))
            elif t == 'pad':
                p = xf.pt(mm(c.get('x')), mm(c.get('y')))
                drill = mm(c.get('drill'))
                m, a = xf.angle(c.get('rot'))
                self.pads.append(dict(pos=p, drill=drill, lib_diameter=mm(c.get('diameter')),
                                      shape=c.get('shape'), angle=a, name=c.get('name'), element=ename,
                                      stop=c.get('stop') != 'no', first=c.get('first') == 'yes',
                                      signal=self.signal_of.get((ename, c.get('name')))))
            elif t == 'smd':
                p = xf.pt(mm(c.get('x')), mm(c.get('y')))
                m, a = xf.angle(c.get('rot'))
                self.smds.append(dict(pos=p, dx=mm(c.get('dx')), dy=mm(c.get('dy')), angle=a,
                                      layer=xf.layer(int(c.get('layer'))), name=c.get('name'), element=ename,
                                      stop=c.get('stop') != 'no', cream=c.get('cream') != 'no',
                                      roundness=float(c.get('roundness') or 0),
                                      signal=self.signal_of.get((ename, c.get('name')))))
            elif t == 'via':
                p = xf.pt(mm(c.get('x')), mm(c.get('y')))
                self.vias.append(dict(pos=p, drill=mm(c.get('drill')), lib_diameter=mm(c.get('diameter')),
                                      shape=c.get('shape'), stop=c.get('stop'), signal=signal,
                                      extent=c.get('extent')))
            elif t == 'hole':
                p = xf.pt(mm(c.get('x')), mm(c.get('y')))
                self.holes.append(dict(pos=p, drill=mm(c.get('drill')), element=ename))
            elif t == 'circle':
                p = xf.pt(mm(c.get('x')), mm(c.get('y')))
                self.circles.append(dict(layer=xf.layer(int(c.get('layer'))), pos=p, radius=mm(c.get('radius')),
                                         width=mm(c.get('width')), element=ename))
            elif t == 'rectangle':
                x1, y1, x2, y2 = (mm(c.get(k)) for k in ('x1', 'y1', 'x2', 'y2'))
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                m, a, _ = rot_of(c.get('rot'))
                ra = math.radians(a)
                corners = []
                for qx, qy in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
                    dx, dy = qx - cx, qy - cy
                    corners.append(xf.pt(cx + dx * math.cos(ra) - dy * math.sin(ra),
                                         cy + dx * math.sin(ra) + dy * math.cos(ra)))
                self.rects.append(dict(layer=xf.layer(int(c.get('layer'))), corners=corners, element=ename))
            elif t == 'polygon':
                verts = []
                for v in c.iter('vertex'):
                    verts.append((xf.pt(mm(v.get('x')), mm(v.get('y'))),
                                  (-1 if xf.mirror else 1) * float(v.get('curve') or 0)))
                self.polygons.append(dict(layer=xf.layer(int(c.get('layer'))), verts=verts,
                                          width=mm(c.get('width')), isolate=mm(c.get('isolate')),
                                          spacing=mm(c.get('spacing')), rank=c.get('rank'),
                                          orphans=c.get('orphans'), thermals=c.get('thermals'),
                                          pour=c.get('pour'), signal=signal, element=ename))
            elif t == 'text':
                p = xf.pt(mm(c.get('x')), mm(c.get('y')))
                m, a = xf.angle(c.get('rot'))
                txt = c.get('textfield') or ''
                if owner is not None and txt.upper() in ('>NAME', '>VALUE'):
                    child = owner.find('name' if txt.upper() == '>NAME' else 'value')
                    if child is not None and child.get('layer') is not None:
                        continue
                    txt = owner.get('name') if txt.upper() == '>NAME' else owner.get('value')
                self.texts.append(dict(layer=xf.layer(int(c.get('layer'))), pos=p, size=mm(c.get('size')),
                                       ratio=float(c.get('ratio') or 8), angle=a, mirror=m, text=txt,
                                       element=ename))

    def pad_geometry(self, p):
        """Copper outline description of a THT pad: (kind, w, h, angle) in mm."""
        d = self.pad_diameter(p['drill'], p['lib_diameter'])
        s = p['shape']
        if s == 'long':
            return ('oval', 2 * d, d, p['angle'])
        if s == 'square':
            return ('rect', d, d, p['angle'])
        if s == 'octagon':
            return ('octagon', d, d, p['angle'])
        if s == 'offset':
            return ('offset', 2 * d, d, p['angle'])
        return ('circle', d, d, 0.0)
