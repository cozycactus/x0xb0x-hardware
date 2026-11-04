#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Drawing tools for the hand-drawn x0xb0x sheets: symbols, parts, wires, labels and writing the files.

Nothing here decides which wires exist. Each sheet function types its own routes and label names, and check_nets.py then
compares the result with the board copper and the original Eagle schematic. The board data only gives values, footprints
and pin names, and the net of each pin for choosing which pins need a net-name label at the end.
"""
import collections
import json
import math
import re
import uuid
from pathlib import Path

import oldlib

HERE = Path(__file__).resolve().parent
LIB = 'x0x'
NS = uuid.UUID('6f1f1b0e-58f5-4f55-9a53-3a3b7f1f0c11')
SCH_FORMAT, LIB_FORMAT = 20260306, 20251024  # What KiCad 10.0.7 writes. An older number makes the editor warn on opening
# Each project file's top-level sheet. Instance paths start here: with any other id the editor rebuilds them and reports an error.
TOP_LEVEL_SHEET = {'mainboard': '7f5f96c8-b7f4-4dd0-b468-89b5c943dd10', 'ioboard': '525a5368-a8f5-40c5-afd5-32cbf9441891'}
DEVICE_NAMES = {'LED5MM', 'J12MM', 'J15MM'}  # Kept as the part's value, but they say nothing on the sheet
RAILS = {'GND': 'GND', '+5.333V': 'RING', '+5V': 'RING', '+12V': 'TRI', '+6V': 'TRI'}
FONT = '(effects (font (size 1.27 1.27)))'
HIDDEN = '(effects (font (size 1.27 1.27)) (hide yes))'
BODY = '(stroke (width 0.254) (type default)) (fill (type none))'
SOLID = '(stroke (width 0.254) (type default)) (fill (type outline))'


def uid(*key):
    return str(uuid.uuid5(NS, '/'.join(map(str, key))))


def fmt(v):
    return f'{round(v, 3):g}'


def line(*pts):
    return ('line', pts)


def solid(*pts):
    return ('solid', pts)


def arc(a, m, b):
    return ('arc', a, m, b)


def art(items, sx=1):
    """Symbol graphics from sheet coordinates (y down) to KiCad's library coordinates (y up), mirrored if asked."""
    p = lambda t: (t[0] * sx, -t[1])
    out = ''
    for kind, *rest in items:
        if kind in ('line', 'solid'):
            xy = ' '.join(f'(xy {fmt(x)} {fmt(y)})' for x, y in map(p, rest[0]))
            out += f'(polyline (pts {xy}) {SOLID if kind == "solid" else BODY})'
        elif kind == 'arc':
            a, m, b = map(p, rest)
            out += f'(arc (start {fmt(a[0])} {fmt(a[1])}) (mid {fmt(m[0])} {fmt(m[1])}) (end {fmt(b[0])} {fmt(b[1])}) {BODY})'
        elif kind == 'ring':
            c = p(rest[0])
            out += f'(circle (center {fmt(c[0])} {fmt(c[1])}) (radius {rest[1]}) {BODY})'
    return out


def pin(x, y, side, number, name='', sx=1, kind='passive', length=2.54):
    if sx < 0 and side in 'LR':
        side = {'L': 'R', 'R': 'L'}[side]
    ang = {'L': 0, 'R': 180, 'T': 270, 'B': 90}[side]
    return f'(pin {kind} line (at {fmt(x * sx)} {fmt(-y)} {ang}) (length {length}) (name "{name}" {FONT}) (number "{number}" {FONT}))'


def head(name, letter, power=False, in_bom=True):
    return (f'(symbol "{name}" {"(power global) " if power else ""}(pin_numbers (hide yes)) (pin_names (offset 0) (hide yes)) (exclude_from_sim no) (in_bom {"yes" if in_bom else "no"}) (on_board yes) '
            f'(property "Reference" "{letter}" (at 0 2.54 0) {FONT}) (property "Value" "{name}" (at 0 -2.54 0) {FONT}) '
            f'(property "Footprint" "" (at 0 0 0) {HIDDEN}) (property "Datasheet" "" (at 0 0 0) {HIDDEN}) (property "Description" "" (at 0 0 0) {HIDDEN}) ')


def symbol(name, letter, items, pins, sx=1):
    """pins: (x, y, side, number, pin name), in sheet coordinates. Several numbers on one point are stacked pads."""
    lines = ' '.join(pin(x, y, s, n, nm, sx) for x, y, s, n, nm in pins)
    return head(name, letter) + f'(symbol "{name}_0_1" {art(items, sx)}) (symbol "{name}_1_1" {lines}))'


ZIG = [(-2.54, 0), (-2.117, -0.889), (-1.27, 0.889), (-0.423, -0.889), (0.423, 0.889), (1.27, -0.889), (2.117, 0.889), (2.54, 0)]
RES = [line(*ZIG)]
CAP = [line((-2.54, 0), (-0.635, 0)), line((0.635, 0), (2.54, 0)), line((-0.635, -1.778), (-0.635, 1.778)), line((0.635, -1.778), (0.635, 1.778))]
ELECTRO = [line((-2.54, 0), (-0.635, 0)), line((0.254, 0), (2.54, 0)), line((-0.635, -1.778), (-0.635, 1.778)), arc((0.889, -1.778), (0.254, 0), (0.889, 1.778)),
           line((-2.032, -1.651), (-1.016, -1.651)), line((-1.524, -2.159), (-1.524, -1.143))]
DIODE = [line((-2.54, 0), (2.54, 0)), line((-1.27, -1.27), (-1.27, 1.27), (1.27, 0), (-1.27, -1.27)), line((1.27, -1.27), (1.27, 1.27))]
THERM = RES + [line((-2.032, 1.905), (2.032, -1.905)), line((2.032, -1.905), (2.794, -1.905))]
JUMP = [line((-2.54, 0), (-1.016, 0)), line((1.016, 0), (2.54, 0)), ('ring', (-1.016 + 0.381, 0), 0.381), ('ring', (1.016 - 0.381, 0), 0.381), arc((-1.016, -0.635), (0, -1.27), (1.016, -0.635))]
NPN = [line((-2.54, 0), (-0.635, 0)), line((-0.635, -1.905), (-0.635, 1.905)), line((-0.635, -0.635), (2.54, -2.54)), line((-0.635, 0.635), (2.54, 2.54)), solid((2.54, 2.54), (1.27, 2.413), (1.905, 1.397), (2.54, 2.54))]
PNP = [line((-2.54, 0), (-0.635, 0)), line((-0.635, -1.905), (-0.635, 1.905)), line((-0.635, -0.635), (2.54, -2.54)), line((-0.635, 0.635), (2.54, 2.54)), solid((-0.635, -0.635), (0.635, -0.635), (0, -1.651), (-0.635, -0.635))]
JFET = [line((-2.54, 0), (-0.635, 0)), line((-0.635, -2.032), (-0.635, 2.032)), line((-0.635, -1.27), (2.54, -1.27), (2.54, -2.54)), line((-0.635, 1.27), (2.54, 1.27), (2.54, 2.54)), solid((-0.635, 0), (-1.778, -0.508), (-1.778, 0.508), (-0.635, 0))]
TRANSISTOR = {'NPN': (NPN, [(-5.08, 0, 'L', '1', 'B'), (2.54, -5.08, 'T', '2', 'C'), (2.54, 5.08, 'B', '3', 'E')]),
              'PNP': (PNP, [(-5.08, 0, 'L', '1', 'B'), (2.54, 5.08, 'B', '2', 'C'), (2.54, -5.08, 'T', '3', 'E')]),
              'JFET': (JFET, [(-5.08, 0, 'L', '2', 'G'), (2.54, -5.08, 'T', '1', 'D'), (2.54, 5.08, 'B', '3', 'S')])}
CAPSULE = [line((-7.62, -5.08), (7.62, -5.08)), line((-7.62, 5.08), (7.62, 5.08)), arc((-7.62, -5.08), (-12.7, 0), (-7.62, 5.08)), arc((7.62, -5.08), (12.7, 0), (7.62, 5.08))]
PAIR_CE = CAPSULE + [
    line((-12.7, 0), (-10.16, 0)), line((-10.16, -1.905), (-10.16, 1.905)), line((-10.16, -0.635), (-7.62, -2.54), (-7.62, -5.08)), line((-10.16, 0.635), (-7.62, 2.54)),
    solid((-7.62, 2.54), (-8.89, 2.413), (-8.255, 1.397), (-7.62, 2.54)), line((-7.62, 2.54), (7.62, 2.54)),
    line((12.7, 0), (10.16, 0)), line((10.16, -1.905), (10.16, 1.905)), line((10.16, -0.635), (7.62, -2.54), (7.62, -5.08)), line((10.16, 0.635), (7.62, 2.54)),
    solid((7.62, 2.54), (8.89, 2.413), (8.255, 1.397), (7.62, 2.54)), line((0, 2.54), (0, 5.08))]
PAIR_CE_PINS = [(-15.24, 0, 'L', '1', 'B'), (-7.62, -7.62, 'T', '2', 'C'), (0, 7.62, 'B', '3', 'E'), (7.62, -7.62, 'T', '4', 'C1'), (15.24, 0, 'R', '5', 'B1')]
PAIR_CB = CAPSULE + [
    line((-5.08, -1.905), (-5.08, 1.905)), line((5.08, -1.905), (5.08, 1.905)), line((-5.08, 0), (5.08, 0)), line((0, 0), (0, 5.08)),
    line((-5.08, -0.635), (-7.62, -2.54), (-7.62, -5.08)), line((-5.08, 0.635), (-7.62, 2.54), (-7.62, 5.08)), solid((-7.62, 2.54), (-6.35, 2.413), (-6.985, 1.397), (-7.62, 2.54)),
    line((5.08, -0.635), (7.62, -2.54), (7.62, -5.08)), line((5.08, 0.635), (7.62, 2.54), (7.62, 5.08)), solid((7.62, 2.54), (6.35, 2.413), (6.985, 1.397), (7.62, 2.54))]
PAIR_CB_PINS = [(-7.62, 7.62, 'B', '1', 'E1'), (-7.62, -7.62, 'T', '2', 'C1'), (0, 7.62, 'B', '3', 'B'), (7.62, -7.62, 'T', '4', 'C'), (7.62, 7.62, 'B', '5', 'E')]
# The same pairs as SOT-363 chips: 1 E1, 2 B1, 3 C2, 4 E2, 5 B2, 6 C1. Each transistor keeps its place in the SIP symbol, and pads on one net are stacked.
SOT_CE_PINS = [(-15.24, 0, 'L', '5', 'B'), (-7.62, -7.62, 'T', '3', 'C'), (0, 7.62, 'B', '1', 'E'), (0, 7.62, 'B', '4', 'E1'), (7.62, -7.62, 'T', '6', 'C1'), (15.24, 0, 'R', '2', 'B1')]
SOT_CB_PINS = [(-7.62, 7.62, 'B', '4', 'E1'), (-7.62, -7.62, 'T', '3', 'C1'), (0, 7.62, 'B', '2', 'B'), (0, 7.62, 'B', '5', 'B1'), (7.62, -7.62, 'T', '6', 'C'), (7.62, 7.62, 'B', '1', 'E')]
DNP = {'Q12', 'Q21', 'Q22', 'Q26'}  # The SIP pairs: the SMD chips beside them are the parts to fit, and the holes stay for the originals
# A pot standing upright: pin 3 at the top, pin 1 at the bottom, the wiper to the right, the metal case to the left.
ZIG_V = [(y, x) for x, y in ZIG]
POT = [line(*ZIG_V), line((5.08, 0), (2.032, 0)), solid((1.016, 0), (2.286, -0.635), (2.286, 0.635), (1.016, 0)), line((0, -5.08), (0, -2.54)), line((0, 2.54), (0, 5.08))]
CASE = [line((-5.08, 0), (-3.175, 0)), line((-3.175, -2.54), (-3.175, 2.54))]
TRIM = [line((-5.08, 0), (-2.54, 0)), line(*ZIG), line((2.54, 0), (5.08, 0)), line((0, 5.08), (0, 2.032)), solid((0, 1.016), (-0.635, 2.286), (0.635, 2.286), (0, 1.016))]
LED = DIODE + [line((-0.508, -1.778), (0.762, -3.048)), line((0.508, -1.778), (1.778, -3.048))]
# A tact switch standing upright: pins 1 and 2 are one strip at the top, pins 3 and 4 one strip at the bottom.
TACT = [line((-1.27, -2.54), (1.27, -2.54)), line((-1.27, 2.54), (1.27, 2.54)), line((0, 2.54), (2.032, -1.27))]
HOLE = [('ring', (0, 0), 1.651), line((-2.54, 0), (2.54, 0)), line((0, -2.54), (0, 2.54))]


def library():
    r_pins = [(-5.08, 0, 'L', '1', '1'), (5.08, 0, 'R', '2', '2')]
    lib = {
        'R': symbol('R', 'R', RES, r_pins),
        'C': symbol('C', 'C', CAP, r_pins),
        'CP': symbol('CP', 'C', ELECTRO, [(-5.08, 0, 'L', '+', '+'), (5.08, 0, 'R', '-', '-')]),
        'D': symbol('D', 'D', DIODE, [(-5.08, 0, 'L', 'A', 'A'), (5.08, 0, 'R', 'C', 'C')]),
        'LED': symbol('LED', 'LED', LED, [(-5.08, 0, 'L', 'A', 'A'), (5.08, 0, 'R', 'K', 'C')]),
        'THERM': symbol('THERM', 'R', THERM, r_pins),
        'JUMP': symbol('JUMP', 'J', JUMP, r_pins),
        'TACT': symbol('TACT', 'S', TACT, [(0, -5.08, 'T', '1', 'S'), (0, -5.08, 'T', '2', 'S1'), (0, 5.08, 'B', '3', 'P'), (0, 5.08, 'B', '4', 'P1')]),
        'PAIR_CE': symbol('PAIR_CE', 'Q', PAIR_CE, PAIR_CE_PINS),
        'PAIR_CE_F': symbol('PAIR_CE_F', 'Q', PAIR_CE, PAIR_CE_PINS, -1),
        'PAIR_CB': symbol('PAIR_CB', 'Q', PAIR_CB, PAIR_CB_PINS),
        'SOT_CE': symbol('SOT_CE', 'Q', PAIR_CE, SOT_CE_PINS),
        'SOT_CB': symbol('SOT_CB', 'Q', PAIR_CB, SOT_CB_PINS),
        'TRIM': symbol('TRIM', 'TM', TRIM, [(-7.62, 0, 'L', '3', 'E'), (7.62, 0, 'R', '1', 'A'), (0, 7.62, 'B', '2', 'S')]),
    }
    reso = [line((0, -5.08), (0, -1.905)), line((0, 1.905), (0, 5.08)), line((-1.778, -1.905), (1.778, -1.905)), line((-1.778, 1.905), (1.778, 1.905)), line((-1.27, -1.016), (1.27, -1.016), (1.27, 1.016), (-1.27, 1.016), (-1.27, -1.016)), line((-5.08, 0), (-1.27, 0))]
    lib['RESO'] = symbol('RESO', 'XTL', reso, [(0, -5.08, 'T', '3', 'B'), (0, 5.08, 'B', '1', 'E'), (-5.08, 0, 'L', '2', 'C')])
    for kind, (items, pins) in TRANSISTOR.items():
        lib[kind] = symbol(kind, 'Q', items, pins)
        lib[kind + '_F'] = symbol(kind + '_F', 'Q', items, pins, -1)
    pot_pins = [(0, -7.62, 'T', '3', 'E'), (7.62, 0, 'R', '2', 'S'), (0, 7.62, 'B', '1', 'A')]
    case_pins = [(-7.62, 0, 'L', 'M1', 'M1'), (-7.62, 0, 'L', 'M2', 'M2')]
    lib['POT'] = symbol('POT', 'VR', POT + CASE, pot_pins + case_pins)
    lib['POT_F'] = symbol('POT_F', 'VR', POT + CASE, pot_pins + case_pins, -1)
    # A dual pot. Pads M1 and M2 share GND with pin 1A, so they are stacked there.
    unit_a = ' '.join(pin(x, y, s, n, nm) for x, y, s, n, nm in [(0, -7.62, 'T', '3A', 'E'), (7.62, 0, 'R', '2A', 'S'), (0, 7.62, 'B', '1A', 'A'), (0, 7.62, 'B', 'M1', 'MT1'), (0, 7.62, 'B', 'M2', 'MT2')])
    unit_b = ' '.join(pin(x, y, s, n, nm, -1) for x, y, s, n, nm in [(0, -7.62, 'T', '3B', 'E1'), (7.62, 0, 'R', '2B', 'S1'), (0, 7.62, 'B', '1B', 'A1')])
    lib['POT_DUAL'] = (head('POT_DUAL', 'VR') + f'(symbol "POT_DUAL_1_0" {art(POT)}) (symbol "POT_DUAL_1_1" {unit_a}) '
                       f'(symbol "POT_DUAL_2_0" {art(POT, -1)}) (symbol "POT_DUAL_2_1" {unit_b}))')
    shapes = {'GND': (line((0, 0), (0, 1.27)), line((-1.27, 1.27), (1.27, 1.27), (0, 2.54), (-1.27, 1.27))),
              'RING': (line((0, 0), (0, -1.27)), ('ring', (0, -2.032), 0.762)),
              'TRI': (line((0, 0), (0, -1.016)), solid((-1.016, -1.016), (1.016, -1.016), (0, -2.54), (-1.016, -1.016)))}
    for net, shape in RAILS.items():
        name = 'PWR_' + net
        lib[name] = head(name, '#PWR', True) + (f'(symbol "{name}_0_1" {art(shapes[shape])}) (symbol "{name}_1_1" (pin power_in line (at 0 0 90) (length 0) (name "{net}" {FONT}) (number "1" {FONT}))))')
    lib['FLAG'] = head('FLAG', '#FLG', True) + (f'(symbol "FLAG_0_0" (pin power_out line (at 0 0 90) (length 0) (name "" {FONT}) (number "1" {FONT}))) (symbol "FLAG_0_1" ' +
                                                art([line((0, 0), (0, -1.27), (-1.016, -1.905), (0, -2.54), (1.016, -1.905), (0, -1.27))]) + '))')
    return lib


def imported(board, name, clean):
    """A symbol from the project's Eagle-import library, under a clean name, with the sheets' line and text sizes."""
    text = oldlib.load(board)[name]
    text = text.replace(f'"{name}"', f'"{clean}"', 1).replace(f'"{name}_', f'"{clean}_')
    text = re.sub(r'\(width 0\.4064\)', '(width 0.254)', text)
    text = re.sub(r'\(size (?:1\.\d+|2\.\d+) (?:1\.\d+|2\.\d+)\)', '(size 1.27 1.27)', text)
    return text


class Project:
    """One KiCad project: its board data, its symbols and its sheets, in page order."""

    def __init__(self, board, title_note):
        self.board = board
        self.parts = json.load(open(HERE / 'data' / f'{board}_parts.json'))
        self.lib = library()
        self.chips = {}  # clean symbol name to its pins per unit
        self.sheets = []
        self.title_note = title_note

    def chip_symbol(self, name):
        clean = re.sub(r"[^A-Za-z0-9_+.\-]", '', name).replace(',', '_') or 'X'
        clean = 'E_' + clean
        if clean not in self.chips:
            self.lib[clean] = imported(self.board, name, clean)
            self.chips[clean] = oldlib.units(oldlib.load(self.board)[name])
        return clean

    def sheet(self, file, title, paper='A3', dx=0.0, dy=0.0):
        s = Sheet(self, file, title, paper, dx, dy)
        self.sheets.append(s)
        return s


class Sheet:
    def __init__(self, project, file, title, paper, dx, dy):
        self.project, self.file, self.title, self.paper = project, file, title, paper
        self.dx, self.dy = dx, dy
        self.real = project.parts
        self.items, self.pins, self.ends, self.segments = [], {}, [], []
        self.used, self.touched, self.labelled = set(), set(), set()
        self.n = 0
        self.order = []  # pins in the order placed
        self.alternates = set()  # pins of parts drawn apart from the circuit, joined to it by visible labels

    # ---- Basics
    def _xy(self, x, y):
        return round(x + self.dx, 3), round(y + self.dy, 3)

    def _at(self, pt):
        return self.pins[pt] if isinstance(pt, str) else self._xy(*pt)

    def _symbol(self, ref, sym, x, y, rot, fields, angle=0, unit=1, just=None, pins=None, value=None, hide_value=False, in_bom=True):
        x, y = self._xy(x, y)
        p = self.real[ref]
        self.used.add(sym)
        (rx, ry), (vx, vy) = [self._xy(*f) for f in fields]
        effects = f'(effects (font (size 1.27 1.27)) (justify {just}))' if just else FONT
        numbers = pins if pins is not None else [q['num'] for q in p['pads']]
        val = p['value']
        shown = HIDDEN if (hide_value or not val or val in DEVICE_NAMES or "''" in val) else effects
        self.items.append(
            f'(symbol (lib_id "{LIB}:{sym}") (at {x} {y} {rot}) (unit {unit}) (exclude_from_sim no) (in_bom {"yes" if in_bom else "no"}) (on_board yes) (dnp {"yes" if ref in DNP else "no"}) (uuid "{uid(self.file, "sym", ref, unit)}") '
            f'(property "Reference" "{ref}" (at {rx} {ry} {angle}) {effects}) (property "Value" "{val}" (at {vx} {vy} {angle}) {shown}) '
            f'(property "Footprint" "{p["fp"]}" (at {x} {y} 0) {HIDDEN}) (property "Datasheet" "" (at {x} {y} 0) {HIDDEN}) (property "Description" "" (at {x} {y} 0) {HIDDEN}) '
            + ' '.join(f'(pin "{n}" (uuid "{uid(self.file, "pin", ref, n)}"))' for n in numbers) + f' @INST:{ref}|{unit}@)')

    def _pin(self, ref, num, x, y):
        pt = self._xy(x, y)
        key = f'{ref}.{num}'
        assert key not in self.pins, key
        self.pins[key] = pt
        self.ends.append(pt)
        self.order.append(key)

    def _stack(self, ref, num, onto):
        key = f'{ref}.{num}'
        self.pins[key] = self.pins[f'{ref}.{onto}']
        self.order.append(key)

    def net(self, ref, num):
        return next(q['net'] for q in self.real[ref]['pads'] if q['num'] == num)

    @staticmethod
    def _kind(ref, pads):
        nums = {q['num'] for q in pads}
        if '+' in nums:
            return 'CP', '+', '-'
        if 'K' in nums:
            return 'LED', 'A', 'K'
        if 'A' in nums:
            return 'D', 'A', 'C'
        if ref.startswith('R100'):
            return 'THERM', '1', '2'
        if ref[0] == 'J':
            return 'JUMP', '1', '2'
        return ('C' if ref[0] == 'C' else 'R'), '1', '2'

    # ---- Parts
    def across(self, ref, x, y, left, flip_text=False, compact=False, ref_at=None):
        """A two-pin part lying down, with the pad numbered `left` on the left. compact puts its reference and value on one
        line above it, for rows at 5.08 mm. ref_at moves the reference, relative to the part."""
        sym, first, second = self._kind(ref, self.real[ref]['pads'])
        rot = 0 if left == first else 180
        lift = {'CP': 3.175, 'LED': 5.08}.get(sym, 2.54)
        f = ((x, y - lift), (x, y + 2.54))
        if flip_text:
            f = ((x, y + 2.54), (x, y + 5.08))
        if compact:
            f = ((x - 3.0, y - 2.032), (x + 3.2, y - 2.032))
        if ref_at:
            f = ((x + ref_at[0], y + ref_at[1]), f[1])
        self._symbol(ref, sym, x, y, rot, f)
        self._pin(ref, left, x - 5.08, y)
        self._pin(ref, second if left == first else first, x + 5.08, y)

    def down(self, ref, x, y, top, left_text=False, hide_value=False):
        """A two-pin part standing up, with the pad numbered `top` at the top. Its text goes to the right unless left_text."""
        sym, first, second = self._kind(ref, self.real[ref]['pads'])
        rot = 270 if top == first else 90
        value = self.real[ref]['value']
        place = (lambda s: round(x - 2.54 - len(s) * 0.6, 2)) if left_text else (lambda s: round(x + 2.54 + len(s) * 0.6, 2))
        ry = y if hide_value else round(y - 1.27, 2)
        self._symbol(ref, sym, x, y, rot, ((place(ref), ry), (place(value), round(y + 1.27, 2))), angle=90, hide_value=hide_value)
        self._pin(ref, top, x, y - 5.08)
        self._pin(ref, second if top == first else first, x, y + 5.08)

    def transistor(self, ref, x, y, kind, flip=False, text=None):
        """text is (x, justify) when the reference and value shouldn't sit on the emitter's side."""
        items, pins = TRANSISTOR[kind]
        sx = -1 if flip else 1
        tx, just, *lift = text or ((x - 5.08, 'right') if flip else (x + 5.08, 'left'))
        ty = y + (lift[0] if lift else 0)
        self._symbol(ref, kind + ('_F' if flip else ''), x, y, 0, ((tx, ty - 1.27), (tx, ty + 1.27)), just=just)
        for px, py, _, num, _name in pins:
            self._pin(ref, num, x + px * sx, y + py)

    def pair(self, ref, x, y, flip=False, shape='CE'):
        sx = -1 if flip else 1
        pins = PAIR_CE_PINS if shape == 'CE' else PAIR_CB_PINS
        if shape == 'CE':
            fields, just = ((x, y - 3.302), (x, y - 0.889)), None  # inside the capsule, above the emitter line
        else:
            fields, just = ((x + 13.97, y - 1.27), (x + 13.97, y + 1.27)), 'left'
        self._symbol(ref, f'PAIR_{shape}' + ('_F' if flip else ''), x, y, 0, fields, just=just)
        for px, py, _, num, _name in pins:
            self._pin(ref, num, x + px * sx, y + py)

    def sot(self, ref, x, y, shape='CE'):
        """A SOT-363 pair standing in for a SIP pair, drawn apart from the circuit. Give each of its pins alt_out or rail."""
        pins = SOT_CE_PINS if shape == 'CE' else SOT_CB_PINS
        fields, just = (((x, y - 3.302), (x, y - 0.889)), None) if shape == 'CE' else (((x + 13.97, y - 1.27), (x + 13.97, y + 1.27)), 'left')
        self._symbol(ref, f'SOT_{shape}', x, y, 0, fields, just=just, pins=[q[3] for q in pins])
        seen = {}
        for px, py, _, num, _name in pins:
            if (px, py) in seen:
                self._stack(ref, num, seen[(px, py)])
            else:
                seen[(px, py)] = num
                self._pin(ref, num, x + px, y + py)
            self.alternates.add(f'{ref}.{num}')

    def alt_out(self, pin_name, net, side, length=2.54):
        """A stub and a visible label from an alternate's pin. The net keeps its own name on the circuit it belongs to."""
        had = net in self.labelled
        self.out(pin_name, net, side, length)
        if not had:
            self.labelled.discard(net)

    def pot(self, ref, x, y, wiper_left=False):
        sx = -1 if wiper_left else 1
        self._symbol(ref, 'POT_F' if wiper_left else 'POT', x, y, 0, ((x + 2.54 * sx, y - 5.08), (x + 2.54 * sx, y + 5.08)), just='right' if wiper_left else 'left', pins=['1', '2', '3', 'M1', 'M2'])
        self._pin(ref, '3', x, y - 7.62)
        self._pin(ref, '2', x + 7.62 * sx, y)
        self._pin(ref, '1', x, y + 7.62)
        self._pin(ref, 'M1', x - 7.62 * sx, y)
        self._stack(ref, 'M2', 'M1')

    def pot_dual(self, ref, unit, x, y, wiper_left=False):
        sx = -1 if wiper_left else 1
        s = 'AB'[unit - 1]
        pins = [f'3{s}', f'2{s}', f'1{s}'] + (['M1', 'M2'] if unit == 1 else [])
        self._symbol(ref, 'POT_DUAL', x, y, 0, ((x + 2.54 * sx, y - 5.08), (x + 2.54 * sx, y + 5.08)), unit=unit, just='right' if wiper_left else 'left', pins=pins)
        self._pin(ref, f'3{s}', x, y - 7.62)
        self._pin(ref, f'2{s}', x + 7.62 * sx, y)
        self._pin(ref, f'1{s}', x, y + 7.62)
        if unit == 1:
            self._stack(ref, 'M1', '1A')
            self._stack(ref, 'M2', '1A')

    def reso(self, ref, x, y):
        """The ceramic resonator: its output at the top, its input at the bottom, its centre pin to the left."""
        self._symbol(ref, 'RESO', x, y, 0, ((x + 2.54, y - 1.27), (x + 2.54, y + 1.27)), just='left', pins=['1', '2', '3'])
        self._pin(ref, '3', x, y - 5.08)
        self._pin(ref, '1', x, y + 5.08)
        self._pin(ref, '2', x - 5.08, y)

    def trim(self, ref, x, y, value_dx=5.08):
        self._symbol(ref, 'TRIM', x, y, 0, ((x, y - 2.54), (x + value_dx, y + 3.81)), pins=['1', '2', '3'])
        self._pin(ref, '3', x - 7.62, y)
        self._pin(ref, '1', x + 7.62, y)
        self._pin(ref, '2', x, y + 7.62)

    def tact(self, ref, x, y):
        """A tact switch with its pads stacked, one strip at the top and one at the bottom."""
        self._symbol(ref, 'TACT', x, y, 0, ((x + 3.81, y - 1.27), (x + 3.81, y + 1.27)), just='left', pins=['1', '2', '3', '4'], hide_value=True)
        self._pin(ref, '1', x, y - 5.08)
        self._stack(ref, '2', '1')
        self._pin(ref, '3', x, y + 5.08)
        self._stack(ref, '4', '3')

    def chip(self, ref, name, unit, x, y, rot=0, ref_at=None, val_at=None, hide_value=False, just=None):
        """A part with its original symbol. Pins come from the symbol, turned by rot."""
        clean = self.project.chip_symbol(name)
        pins = self.project.chips[clean].get(unit, [])
        t = math.radians(rot)
        c, s = round(math.cos(t), 6), round(math.sin(t), 6)
        ref_at = ref_at or (x, y - 2.54)
        val_at = val_at or (x, y + 2.54)
        self._symbol(ref, clean, x, y, rot, (ref_at, val_at), unit=unit, pins=[p[0] for p in pins], hide_value=hide_value, just=just)
        for num, _name, px, py, *_ in pins:
            qx, qy = px * c - py * s, px * s + py * c
            self._pin(ref, num, x + qx, y - qy)

    def hole(self, ref, x, y):
        """A mounting hole: a footprint with no pins and no net. It has a symbol so that Update PCB doesn't delete it, and stays out of the BOM."""
        self.project.lib.setdefault('HOLE', head('HOLE', 'H', in_bom=False) + f'(symbol "HOLE_0_1" {art(HOLE)}))')
        self._symbol(ref, 'HOLE', x, y, 0, ((x, y - 3.81), (x, y + 3.81)), pins=[], in_bom=False)

    # ---- Wires and marks
    def route(self, *points):
        path = []
        for pt in points:
            pt = self._at(pt)
            if path and path[-1][0] != pt[0] and path[-1][1] != pt[1]:
                raise ValueError(f'{self.file}: route not straight: {path[-1]} to {pt} in {points}')
            path.append(pt)
        self.segments += [s for s in zip(path, path[1:]) if s[0] != s[1]]
        self.touched |= set(path)

    def _power(self, net, pt, rot, text=None):
        x, y = self._at(pt)
        self.n += 1
        ref = f'#PWR{self.sheet_id()}{self.n:03d}'
        self.used.add('PWR_' + net)
        self.ends.append((x, y))
        self.touched.add((x, y))
        shown = text is not None
        tx, ty = (round(x + text[0], 2), round(y + text[1], 2)) if shown else (x, y)
        angle = 90 if rot in (90, 270) else 0
        self.items.append(
            f'(symbol (lib_id "{LIB}:PWR_{net}") (at {x} {y} {rot}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid(self.file, "pw", self.n)}") '
            f'(property "Reference" "{ref}" (at {x} {y} 0) {HIDDEN}) (property "Value" "{net}" (at {tx} {ty} {angle}) {FONT if shown else HIDDEN}) '
            f'(property "Footprint" "" (at {x} {y} 0) {HIDDEN}) (property "Datasheet" "" (at {x} {y} 0) {HIDDEN}) (property "Description" "" (at {x} {y} 0) {HIDDEN}) '
            f'(pin "1" (uuid "{uid(self.file, "pwpin", self.n)}")) @INST:{ref}|1@)')

    def sheet_id(self):
        return self.project.sheets.index(self) + 1

    def ground(self, pt, side='B'):
        """A ground symbol hanging below a pin, or pointing right (R) or left (L) from a side pin, or up (T)."""
        self._power('GND', pt, {'B': 0, 'R': 90, 'L': 270, 'T': 180}[side])

    def rail(self, net, pt, side='T'):
        """A supply symbol pointing up, left, right or down from a pin. The symbols point up at angle 0."""
        w = len(net) * 0.62 + 4.2
        self._power(net, pt, {'T': 0, 'L': 90, 'R': 270, 'B': 180}[side], {'T': (0, -5.08), 'L': (-w, 0), 'R': (w, 0), 'B': (0, 5.08)}[side])

    def flag(self, pt):
        """A PWR_FLAG: this rail is driven from another board, through a connector."""
        x, y = self._at(pt)
        self.n += 1
        ref = f'#FLG{self.sheet_id()}{self.n:03d}'
        self.used.add('FLAG')
        self.ends.append((x, y))
        self.touched.add((x, y))
        self.items.append(f'(symbol (lib_id "{LIB}:FLAG") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid(self.file, "fl", self.n)}") '
                          f'(property "Reference" "{ref}" (at {x} {y} 0) {HIDDEN}) (property "Value" "FLAG" (at {x} {y} 0) {HIDDEN}) (property "Footprint" "" (at {x} {y} 0) {HIDDEN}) '
                          f'(property "Datasheet" "" (at {x} {y} 0) {HIDDEN}) (property "Description" "" (at {x} {y} 0) {HIDDEN}) (pin "1" (uuid "{uid(self.file, "flp", self.n)}")) @INST:{ref}|1@)')

    def label(self, net, pt, side='R'):
        """A global label with its name typed by hand, pointing away from the wire: R, L, T or B."""
        x, y = self._at(pt)
        self.ends.append((x, y))
        self.touched.add((x, y))
        self.labelled.add(net)
        self.n += 1
        ang, just = {'R': (0, 'left'), 'L': (180, 'right'), 'T': (90, 'left'), 'B': (270, 'right')}[side]
        self.items.append(f'(global_label "{net}" (shape passive) (at {x} {y} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{uid(self.file, "lab", self.n)}") '
                          f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} 0) {HIDDEN}))')

    def out(self, pin_name, net, side='R', length=2.54):
        """A short stub from a pin to a global label."""
        x, y = self.pins[pin_name]
        dx, dy = {'R': (length, 0), 'L': (-length, 0), 'T': (0, -length), 'B': (0, length)}[side]
        end = (round(x + dx, 3), round(y + dy, 3))
        self.segments.append(((x, y), end))
        self.touched |= {(x, y), end}
        self.ends.append(end)
        self.label_abs(net, end, side)

    def label_abs(self, net, end, side):
        keep = self.dx, self.dy
        self.dx, self.dy = 0, 0
        self.label(net, end, side)
        self.dx, self.dy = keep

    def nc(self, pin_name):
        """A no-connect mark on a pin that the board leaves open."""
        x, y = self.pins[pin_name]
        self.n += 1
        self.touched.add((x, y))
        self.items.append(f'(no_connect (at {x} {y}) (uuid "{uid(self.file, "nc", self.n)}"))')

    def net_name(self, net, pt):
        """A net's Eagle name, too small to see, on one pin. One label per net, so it can't join anything by itself."""
        x, y = pt
        self.n += 1
        self.items.append(f'(global_label "{net}" (shape passive) (at {x} {y} 0) (effects (font (size 0.05 0.05)) (justify left)) (uuid "{uid(self.file, "nm", self.n)}") '
                          f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} 0) (effects (font (size 0.05 0.05)) (hide yes))))')

    def note(self, s, x, y, just='left'):
        x, y = self._xy(x, y)
        self.n += 1
        self.items.append(f'(text "{s}" (exclude_from_sim no) (at {x} {y} 0) (effects (font (size 1.27 1.27) (italic yes)) (justify {just})) (uuid "{uid(self.file, "note", self.n)}"))')

    def caption(self, s, x, y, just='left'):
        """A pot's or jack's function, as printed on the original sheet."""
        x, y = self._xy(x, y)
        self.n += 1
        self.items.append(f'(text "{s}" (exclude_from_sim no) (at {x} {y} 0) (effects (font (size 1.524 1.524) (bold yes)) (justify {just})) (uuid "{uid(self.file, "cap", self.n)}"))')

    def block(self, title, x0, y0, x1, y1, title_at=None):
        (ax, ay), (bx, by) = self._xy(x0, y0), self._xy(x1, y1)
        self.n += 1
        self.items.append(f'(rectangle (start {ax} {ay}) (end {bx} {by}) (stroke (width 0) (type dash)) (fill (type none)) (uuid "{uid(self.file, "frm", self.n)}"))')
        tx, ty = self._xy(*title_at) if title_at else (round(ax + 2.54, 2), round(ay + 3.81, 2))
        self.items.append(f'(text "{title}" (exclude_from_sim no) (at {tx} {ty} 0) (effects (font (size 2 2) (bold yes)) (justify left)) (uuid "{uid(self.file, "ttl", self.n)}"))')

    def finish(self):
        """Write the wires: split each one wherever something ends on it, and put a dot where three or more things meet."""
        nodes = set(self.ends) | {pt for seg in self.segments for pt in seg}
        pieces = []
        for a, b in self.segments:
            cuts = sorted({a, b} | {n for n in nodes if min(a[0], b[0]) <= n[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= n[1] <= max(a[1], b[1])})
            pieces += [p for p in zip(cuts, cuts[1:]) if p[0] != p[1]]
        pieces = sorted(set(pieces))
        count = collections.Counter(pt for piece in pieces for pt in piece)
        for pt in set(self.ends):
            count[pt] += 1
        for a, b in pieces:
            self.items.append(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid "{uid(self.file, "w", a, b)}"))')
        for pt, c in sorted(count.items()):
            if c >= 3:
                self.items.append(f'(junction (at {pt[0]} {pt[1]}) (diameter 0) (color 0 0 0 0) (uuid "{uid(self.file, "j", pt)}"))')


def name_nets(project):
    """Give each net that stays on one sheet its Eagle name. A net on several sheets must have typed labels on each."""
    where = collections.defaultdict(set)
    parts = project.parts
    pad_net = {f'{r}.{q["num"]}': q['net'] for r, p in parts.items() for q in p['pads']}
    for s in project.sheets:
        for pin_name in s.order:
            where[pad_net[pin_name]].add(s.file)
    problems = []
    for s in project.sheets:
        first = {}
        for pin_name in s.order:
            if pin_name not in s.alternates:
                first.setdefault(pad_net[pin_name], s.pins[pin_name])
        for net, pt in first.items():
            if net is None or net in RAILS or net in s.labelled:
                continue
            if len(where[net]) > 1:
                problems.append(f'{net} is on {sorted(where[net])} but has no label on {s.file}')
                continue
            s.net_name(net, pt)
    return problems


def write_project(project, out, root_title, root_lines, rev):
    """Write the sheets, the root sheet that holds them, and the project's symbol library."""
    name = project.board
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    root = uid(name, 'root')
    top = TOP_LEVEL_SHEET[name]
    boxes = []
    sheet_ids = {}
    for i, s in enumerate(project.sheets):
        su = uid(name, 'sheet', s.file)
        sheet_ids[s.file] = su
        path = f'/{top}/{su}'
        body = '\n'.join(s.items)
        body = re.sub(r'@INST:([^|@]+)\|(\d+)@', lambda m: f'(instances (project "{name}" (path "{path}" (reference "{m[1]}") (unit {m[2]}))))', body)
        blocks = '\n'.join(project.lib[k].replace(f'(symbol "{k}"', f'(symbol "{LIB}:{k}"', 1) for k in sorted(s.used))
        (out / f'{s.file}.kicad_sch').write_text(
            f'(kicad_sch (version {SCH_FORMAT}) (generator "x0x_redraw") (generator_version "10.0") (uuid "{su}") (paper "{s.paper}")\n'
            f'(title_block (title "{s.title}") (rev "{rev}") (company "x0xb0x {project.title_note}") (comment 1 "Drawn from the original Eagle schematic; nets checked against the board copper.") '
            f'(comment 2 "Copyright (c) 2005, Limor Fried. See http://www.ladyada.net/make/x0xb0x/"))\n'
            f'(lib_symbols {blocks})\n{body}\n(embedded_fonts no))\n')
        x, y = 25 + 40 * i, 75 + 45 * (i % 3)  # KiCad plots sheets in order of x, then y, so x must rise with the page number
        boxes.append(f'(sheet (at {x} {y}) (size 55 30) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes) (stroke (width 0.1524) (type default)) (fill (color 0 0 0 0)) (uuid "{su}") '
                     f'(property "Sheetname" "{s.title}" (at {x} {y - 1} 0) (effects (font (size 1.27 1.27)) (justify left bottom))) (property "Sheetfile" "{s.file}.kicad_sch" (at {x} {y + 31} 0) (effects (font (size 1.27 1.27)) (justify left top))) '
                     f'(instances (project "{name}" (path "/{top}" (page "{i + 2}")))))')
    lines = '\n'.join(f'(text "{t}" (exclude_from_sim no) (at 25 {35 + j * 8} 0) (effects (font (size 3 3)) (justify left)) (uuid "{uid(name, "rt", j)}"))' for j, t in enumerate(root_lines))
    (out / f'{name}.kicad_sch').write_text(
        f'(kicad_sch (version {SCH_FORMAT}) (generator "x0x_redraw") (generator_version "10.0") (uuid "{root}") (paper "A3")\n'
        f'(title_block (title "{root_title}") (rev "{rev}") (company "x0xb0x {project.title_note}"))\n(lib_symbols)\n{lines}\n' + '\n'.join(boxes) + '\n(sheet_instances (path "/" (page "1")))\n(embedded_fonts no))\n')
    (out / f'{LIB}.kicad_sym').write_text(f'(kicad_symbol_lib (version {LIB_FORMAT}) (generator "x0x_redraw") (generator_version "10.0")\n' + '\n'.join(project.lib[k] for k in sorted(project.lib)) + '\n)\n')
    return sheet_ids
