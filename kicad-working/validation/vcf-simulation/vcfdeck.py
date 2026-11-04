#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Generate and run ngspice decks of the x0xb0x VCF from the KiCad netlist.

Every part value and connection below comes from vcf-parts.json, which extract_vcf.py
exports from kicad-working/mainboard/mainboard.kicad_sch. Only the following are not from
the netlist: the transistor models (substitutes built from the datasheet hFE/fT/Cob), the
pot positions, and the saw source (kit-documented levels).
"""
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COMP = json.loads((HERE / 'vcf-parts.json').read_text())['components'] if (HERE / 'vcf-parts.json').exists() else {}
NGSPICE = os.environ.get('NGSPICE') or shutil.which('ngspice') or 'ngspice'

# Parts simulated, grouped by function. Any other part on the board is not in the deck.
FILTER = ('R47 R61 R64 R65 R94 R96 R97 R109 R112 R115 R116 R95 R67 R68 R69 R70 R71 R98 R108 '
          'R110 R111 R66 R72 R73 R99 R113 R114 R62 R63 R46 '
          'C19 C24 C26 C25 C27 C18 C13 C14 C15 C17 C22 C23 C29 C16 C30 C28 '
          'Q9 Q10 Q11 Q13 Q14 Q15 Q16 Q17 Q18 Q19 Q20 Q23 Q12 Q21 Q22 D24').split()
OUTPUT_TAP = 'C20 C21 R121 R122 R124 R125 R126 C37'.split()
ACCENT_LOAD = 'R119 C36'.split()
MEG = ('R138 R152 C62 Q40 Q41 R117 D26 D28 D29 D37 R151 Q38 R148 R149 R150 C54 C55 Q37 R143 '
       'R144 R146 R142 C72 Q35 R139 R140 R141').split()
SQUARE = 'R34 R35 C10 Q8 R36 C11 R45'.split()
CONTROLS = 'TM3 VR3 VR5 VR4 VR7 VR6 IC12 Q39'.split()
ALL_PARTS = FILTER + OUTPUT_TAP + ACCENT_LOAD + MEG + SQUARE + CONTROLS

# Substitute Gummel-Poon models. hFE and fT/Cob follow the datasheets in the hardware
# repository (2SC1583, 2SC2291: Mitsubishi; 2SC536: Sanyo). IS, VAF and the junction
# capacitance split are generic small-signal values, since no datasheet gives them.
MODELS = """
.model N536  NPN (IS=1.2e-14 BF={bf536}  NF=1 VAF=100 IKF=0.1 ISE=3e-15 NE=1.5 BR=5 RB=60 RC=1 RE=0.4 CJE=10p CJC=3p TF=0.7n TR=60n XTB=1.5)
.model N1583 NPN (IS=1.2e-14 BF={bf1583} NF=1 VAF=120 IKF=0.1 ISE=3e-15 NE=1.5 BR=5 RB=60 RC=1 RE=0.4 CJE=8p  CJC=2.5p TF=1n  TR=60n XTB=1.5)
.model N1583Q12 NPN (IS=1.2e-14 BF={bfq12} NF=1 VAF=120 IKF=0.1 ISE=3e-15 NE=1.5 BR=5 RB=60 RC=1 RE=0.4 CJE=8p  CJC=2.5p TF=1n  TR=60n XTB=1.5)
.model N2291 NPN (IS=1.2e-14 BF={bf2291} NF=1 VAF=150 IKF=0.1 ISE=3e-15 NE=1.5 BR=5 RB=60 RC=1 RE=0.4 CJE=8p  CJC=2.5p TF=1.5n TR=60n XTB=1.5)
.model P733  PNP (IS=1.2e-14 BF=300 NF=1 VAF=60 IKF=0.1 ISE=3e-15 NE=1.5 BR=5 RB=60 RC=1 RE=0.4 CJE=10p CJC=4.5p TF=1n TR=60n XTB=1.5)
.model D4148 D (IS=2.52n RS=0.568 N=1.752 CJO=4p M=0.4 TT=20n)
.model SW4066 SW (RON=250 ROFF=1e9 VT=6 VH=0.5)
.model J2SK30 NJF (VTO=-1.2 BETA=1.4m LAMBDA=0.01)
"""
MODEL_OF = {'2SA733P': 'P733', '2SC536F': 'N536', '2SC1583': 'N1583', '2SC2291': 'N2291'}  # by first 7 chars
DUAL = {'Q12', 'Q21', 'Q22'}

# meg: MEG capacitor C62 voltage for AC runs. A decayed MEG sits near 1.7 V (see report).
DEFAULTS = dict(cut=0.5, res=1.0, env=0.0, decay=0.0, acc=0.5, tm3=0.5, temp=25.0, meg=1.7,
                bf536=240, bf1583=400, bfq12=400, bf2291=400)  # bf1583 is Q21 only; Q12 has bfq12


def node(name):
    if name == 'GND':
        return '0'
    if name == '+5.333V':
        return 'vref'
    if name == '+12V':
        return 'vcc'
    if name in ('GATE', 'ACCENT'):
        return 'n' + name.lower()
    return 'n' + re.sub(r'[^0-9A-Za-z]', '', name.replace('N$', '')).lower()


def value_of(ref, override):
    if ref in override:
        return override[ref]
    v = COMP[ref]['value'].strip()
    if ref[0] == 'C':
        return float(v.split('/')[0]) * 1e-6
    m = re.fullmatch(r'([0-9.]+)([kKmM]?)', v)
    assert m, (ref, v)
    return float(m[1]) * {'': 1, 'k': 1e3, 'K': 1e3, 'M': 1e6, 'm': 1e6}[m[2]]


def pins(ref):
    return {p['func'].split('_')[0]: node(p['net']) for p in COMP[ref]['pins'].values()}


def taper_a(x):
    """Audio-taper track fraction from rotation: 20 % at half rotation (assumed)."""
    return 0.4 * x if x <= 0.5 else 0.2 + 1.6 * (x - 0.5)


def pot(name, a, s, e, total, frac):
    frac = min(max(frac, 0.0), 1.0)
    return [f'R{name}as {a} {s} {max(total * frac, 1.0):.6g}', f'R{name}se {s} {e} {max(total * (1 - frac), 1.0):.6g}']


def half_models(half_bf, models_text):
    """Extra .model lines that give one half of a pair its own hFE, for the pair-matching study."""
    out = []
    for half, bf in half_bf.items():
        base = 'N1583Q12' if half[:3] == 'Q12' else MODEL_OF[COMP[half[:3]]['value'][:7]]
        line = next(x for x in models_text.splitlines() if x.startswith(f'.model {base} '))
        out.append(re.sub(r'\bBF=\S+', f'BF={bf}', line.replace(f'.model {base} ', f'.model M{half} ', 1), count=1))
    return out


def part_lines(refs, override, is_scale, subst=(), half_bf=()):
    out = []
    for ref in refs:
        p = pins(ref)
        k = ref[0]
        if ref in subst:  # a real diode in place of the diode-connected or common-base transistor
            out.append(f'D{ref} {p["B"]} {p["E"]} D4148')
            if 'E1' in p:
                out.append(f'D{ref}b {p["B"]} {p["E1"]} D4148')
            continue
        if k in 'RC':
            names = list(p.values())
            assert len(names) == 2, ref
            out.append(f'{ref} {names[0]} {names[1]} {value_of(ref, override):.6g}')
        elif k == 'D':
            out.append(f'D{ref[1:]} {p["A"]} {p["C"]} D4148')
        elif ref in DUAL:
            m = 'N1583Q12' if ref == 'Q12' else MODEL_OF[COMP[ref]['value'][:7]]
            sa, sb = is_scale.get(ref + 'A', 1.0), is_scale.get(ref + 'B', 1.0)
            ma = f'M{ref}A' if ref + 'A' in half_bf else m
            mb = f'M{ref}B' if ref + 'B' in half_bf else m
            if ref == 'Q22':
                out.append(f'Q{ref}A {p["C1"]} {p["B"]} {p["E1"]} {ma} {sa:.5g}')
                out.append(f'Q{ref}B {p["C"]} {p["B"]} {p["E"]} {mb} {sb:.5g}')
            else:
                out.append(f'Q{ref}A {p["C"]} {p["B"]} {p["E"]} {ma} {sa:.5g}')
                out.append(f'Q{ref}B {p["C1"]} {p["B1"]} {p["E"]} {mb} {sb:.5g}')
        elif k == 'Q':
            m = MODEL_OF[COMP[ref]['value'][:7]]
            out.append(f'Q{ref} {p["C"]} {p["B"]} {p["E"]} {m} {is_scale.get(ref, 1.0):.5g}')
        else:
            raise ValueError(ref)
    return out


def circuit(opts):
    """The deck body shared by all analyses. opts: see DEFAULTS, plus r (value overrides,
    ohms or farads, by reference), is_scale (BJT area factors) and broken_loop."""
    o = {**DEFAULTS, **opts}
    r = o.get('r', {})
    scale = o.get('is_scale', {})
    models = MODELS.format(**o)
    L = ['* x0xb0x VCF from KiCad netlist', models, *half_models(o.get('half_bf', {}), models), 'Vcc vcc 0 12', 'Vref vref 0 5.333']
    L += part_lines(FILTER + OUTPUT_TAP + ACCENT_LOAD + MEG, r, scale, o.get('subst', ()), o.get('half_bf', ()))
    tm3, vr3, vr5, vr4, vr7, vr6 = (pins(x) for x in ('TM3', 'VR3', 'VR5', 'VR4', 'VR7', 'VR6'))
    L += pot('TM3', tm3['A'], tm3['S'], tm3['E'], 500e3, o['tm3'])
    L += pot('VR3', vr3['A'], vr3['S'], vr3['E'], 50e3, taper_a(o['cut']))
    L += pot('VR5', vr5['A'], vr5['S'], vr5['E'], 50e3, taper_a(o['env']))
    L += pot('VR4a', vr4['A'], vr4['S'], vr4['E'], 50e3, o['res'])
    L += pot('VR4b', vr4['A1'], vr4['S1'], vr4['E1'], 50e3, o['res'])
    L += pot('VR7', vr7['A'], vr7['S'], vr7['E'], 50e3, o['acc'])
    L += pot('VR6', vr6['A1'], vr6['S1'], vr6['E1'], 1e6, taper_a(o['decay']))
    ic12 = pins('IC12')
    n53, n150, n156, n52, n57 = node('N$53'), node('N$150'), node('N$156'), node('N$52'), node('N$57')
    assert ic12['A'] and n57
    L += [f'SWmeg {n53} {n150} {n57} 0 SW4066', f'SWdecay {n52} {n156} {n57} 0 SW4066']
    q39 = pins('Q39')
    L += [f'JQ39 {q39["D"]} {q39["G"]} {q39["S"]} J2SK30']
    L += o.get('extra', ['Vgate ngate 0 0', 'Vaccent naccent 0 5'])
    if o.get('meg') is not None:  # hold the MEG capacitor at a stated voltage (AC analyses)
        L += [f'Vmegforce {node("N$46")} 0 DC {o["meg"]}']
    return L, o


def run(deck_lines, data_files):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / 'deck.cir'
        text = '\n'.join(deck_lines) + '\n.end\n'
        text = text.replace('@DIR@', d)
        path.write_text(text)
        res = subprocess.run([NGSPICE, '-b', str(path)], capture_output=True, text=True, timeout=1800)
        log = res.stdout + res.stderr
        out = {}
        for name in data_files:
            f = Path(d) / name
            if not f.exists():
                raise RuntimeError('ngspice produced no ' + name + '\n' + log[-3000:])
            out[name] = np.loadtxt(f, skiprows=1, ndmin=2)
        return out, log


SIGNALS = dict(ladder_p='n143', ladder_m='n120', top='n144', vca='n623')


def ac_run(opts, fstart=5, fstop=100e3, per_decade=60):
    """Small-signal response from the waveform switch (N$126) with the MEG at rest."""
    L, o = circuit(opts)
    L += ['Vsrc n126 0 DC 8.5 AC 1']
    L += ['.options temp=%g tnom=25 reltol=1e-4' % o['temp'], '.control', 'set wr_singlescale', 'set wr_vecnames',
          'op', 'let ladder_ua = 1e6*(v(n127)-v(n146))/%g' % value_of('R69', o.get('r', {})), 'let r73_ua = 1e6*(v(n151)-v(n147))/%g' % value_of('R73', o.get('r', {})),
          'echo OP $&ladder_ua $&r73_ua', 'print v(n561) v(n134) v(n147) v(n146) v(n127) v(n143) v(n120) v(n140) v(n144) v(n53) v(n52) v(n46) v(n124) v(n60) v(n138) v(n141) v(n139) v(n131) v(n130)',
          f'ac dec {per_decade} {fstart} {fstop}',
          'let g1 = v(n623)', 'let g2 = v(n143)-v(n120)', 'let g3 = v(n144)', 'let g4 = v(n124)-v(n60)',
          'wrdata @DIR@/ac.txt real(g1) imag(g1) real(g2) imag(g2) real(g3) imag(g3) real(g4) imag(g4)',
          '.endc']
    data, log = run(L, ['ac.txt'])
    op = {}
    m = re.search(r'^OP\s+(\S+)\s+(\S+)', log, re.M)
    if m:
        op['ladder_ua'], op['r73_ua'] = float(m[1]), float(m[2])
    for name, val in re.findall(r'^v\((n\d+|nq\d+)\)\s*=\s*(\S+)', log, re.M):
        op[name] = float(val)
    op['log'] = log
    a = data['ac.txt']
    f = a[:, 0]
    res = dict(f=f, op=op, vca=a[:, 1] + 1j * a[:, 2], ladder=a[:, 3] + 1j * a[:, 4], top=a[:, 5] + 1j * a[:, 6], vd=a[:, 7] + 1j * a[:, 8])
    return res


def loop_run(opts, fstart=5, fstop=200e3, per_decade=80):
    """Loop gain with the loop opened between C23 and R97, the only single-ended point.
    The returned node keeps an equivalent load, and T = +1 is the oscillation condition."""
    o = {**opts}
    r = dict(o.get('r', {}))
    L, oo = circuit({**o, 'r': r})
    # Reconnect R97: its C23 side (N$128) now only sees a dummy load; R97 is driven by the test source.
    p97 = list(pins('R97').values())
    assert 'n128' in p97 and 'n60' in p97
    L = [x for x in L if not x.startswith('R97 ')]
    r97 = value_of('R97', r)
    L += [f'R97 nbreak n60 {r97:.6g}', 'Ctest nbreak nt 1', 'Vtest nt 0 DC 0 AC 1', f'Rload n128 nload {r97 + value_of("R98", r):.6g}', 'Vload nload 0 DC 5.3',
          'Vsrc n126 0 DC 8.5']
    L += ['.options temp=%g tnom=25 reltol=1e-4' % oo['temp'], '.control', 'set wr_singlescale', 'set wr_vecnames',
          f'ac dec {per_decade} {fstart} {fstop}', 'let t = v(n128)', 'wrdata @DIR@/loop.txt real(t) imag(t)', '.endc']
    data, log = run(L, ['loop.txt'])
    a = data['loop.txt']
    return a[:, 0], a[:, 1] + 1j * a[:, 2]


def oscillation_margin(f, T, fmin=40.0, fmax=1e9):
    """Find where T crosses the positive real axis (phase 0) between fmin and fmax. Returns the
    crossing with the largest magnitude: (frequency, |T| in dB). The audio crossing is the
    filter's resonance; call with fmax=40 to look at the sub-audio crossing of the AC couplers."""
    ph = np.unwrap(np.angle(T))
    best = None
    for i in range(len(f) - 1):
        if f[i] < fmin or f[i] > fmax:
            continue
        for k in range(-3, 4):
            target = 2 * math.pi * k
            if (ph[i] - target) * (ph[i + 1] - target) <= 0 and abs(ph[i + 1] - ph[i]) < 2:
                t = (target - ph[i]) / (ph[i + 1] - ph[i]) if ph[i + 1] != ph[i] else 0
                fc = f[i] * (f[i + 1] / f[i]) ** t
                db = 20 * np.log10(abs(T[i])) * (1 - t) + 20 * np.log10(abs(T[i + 1])) * t
                if best is None or db > best[1]:
                    best = (fc, db)
    return best


def peak(f, h, lo=10.0):
    m = 20 * np.log10(np.abs(h))
    i = int(np.argmax(np.where(f >= lo, m, -999)))
    if 0 < i < len(f) - 1:  # parabolic refinement in log f
        y0, y1, y2 = m[i - 1], m[i], m[i + 1]
        d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) != 0 else 0
        return f[i] * (f[i + 1] / f[i]) ** d, y1 - 0.25 * (y0 - y2) * d
    return f[i], m[i]


def ladder_poly(s_over, r):
    """Exact small-signal denominator of the four-rung ladder with the bottom capacitor r*C:
    x = 2*a*C*s, a = 2*VT/If. r=1 gives x^4+7x^3+15x^2+10x+1, r=1/2 gives
    0.5x^4+4x^3+10x^2+8x+1: both are Stinchcombe's expressions before normalising."""
    x = s_over
    return (x ** 3 + 6 * x ** 2 + 10 * x + 4) * (1 + r * x) - (x ** 2 + 4 * x + 3)


def poly_coeffs(r):
    return np.array([r, 1 + 6 * r, 6 + 10 * r - 1, 10 + 4 * r - 4, 4 - 3], float)


def critical_k(r):
    """Smallest k for which D(x)+k has a root on the imaginary axis, with its x = j*w."""
    c = poly_coeffs(r)
    # D(jw) imaginary part: c1*(-w^3) + c3*w = 0 -> w^2 = c3/c1. Real part: c0 w^4 - c2 w^2 + c4.
    w2 = c[3] / c[1]
    return -(c[0] * w2 ** 2 - c[2] * w2 + c[4]), math.sqrt(w2)


SQUARE_LOAD = None


def tran_run(opts, notes, t_end, wave='saw', save=('n623', 'n144', 'n53', 'n46', 'n134', 'n561', 'n127', 'n146', 'n126', 'n161', 'n152'),
             tstep=10e-6, tmax=5e-6, saw_hi=11.25, saw_lo=5.75, reset=10e-6, reltol=1e-3, source=None):
    """Time-domain run with the real MEG and accent circuits.
    notes: list of (t_on, t_off, freq_hz, accent). Between notes the VCO holds its last pitch.
    The saw falls linearly and resets fast (Q26 sinks C33, Q25 recharges it), kit-level 5.5 Vpp on 8.5 V."""
    o = {**opts, 'meg': None}
    extra = []
    # Tied (slid) notes keep the gate high, so the MEG is not struck again.
    spans = []
    for t_on, t_off, _, _ in notes:
        if spans and t_on <= spans[-1][1] + 1e-6:
            spans[-1][1] = max(spans[-1][1], t_off)
        else:
            spans.append([t_on, t_off])
    gate = [(0.0, 0.0)]
    for a, b in spans:
        gate += [(a, 0.0), (a + 1e-6, 5.0), (b, 5.0), (b + 1e-6, 0.0)]
    # The accent line is active low. Stock firmware (synth.c) writes it in note_on, and note_off does not
    # touch it, so it holds until the next note even after the gate has fallen.
    acc = [(0.0, 5.0)]
    level = 5.0
    for t_on, _, _, ac in notes:
        want = 0.0 if ac else 5.0
        if want != level:
            acc += [(t_on - 2e-6, level), (t_on - 1e-6, want)]
            level = want
    extra.append('Vgate ngate 0 PWL(' + ' '.join(f'{a:.7g} {b:.6g}' for a, b in gate) + ')')
    extra.append('Vaccent naccent 0 PWL(' + ' '.join(f'{a:.7g} {b:.6g}' for a, b in acc) + ')')
    if source is not None:
        extra += source
    else:
        pts = []
        t = 0.0
        i = 0
        while t < t_end:
            while i + 1 < len(notes) and t >= notes[i + 1][0]:
                i += 1
            fr = notes[i][2] if notes else 100.0
            per = 1.0 / fr
            pts += [(t, saw_hi), (t + per - reset, saw_lo)]
            t += per
        pts.append((t, saw_hi))
        extra.append('Vsaw n108 0 PWL(' + ' '.join(f'{a:.8g} {b:.6g}' for a, b in pts) + ')')
        extra.append('Rs1 n108 n126 1' if wave == 'saw' else 'Rs1 n303 n126 1')
        extra += part_lines(SQUARE, o.get('r', {}), o.get('is_scale', {}))
    o['extra'] = extra
    L, oo = circuit(o)
    vecs = ' '.join(f'v({n})' for n in save)
    L += [f'.options temp={oo["temp"]} tnom=25 reltol={reltol} abstol=1e-11 vntol=1e-6 method=gear itl4=50', f'.tran {tstep} {t_end} 0 {tmax}',
          '.control', 'set wr_singlescale', 'set wr_vecnames', 'run', 'linearize', f'wrdata @DIR@/tran.txt {vecs}', '.endc']
    data, log = run(L, ['tran.txt'])
    a = data['tran.txt']
    out = dict(t=a[:, 0])
    for k, n in enumerate(save):
        out[n] = a[:, k + 1]
    out['log'] = log
    return out
