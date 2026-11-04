#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Matching between the two halves of Q12, Q21 and Q22, one pair at a time. Writes results/pair_matching.json.

The datasheets allow |Vbe1-Vbe2| of 1 mV typical, 10 mV maximum, and hFE1/hFE2 down to 0.8. "Unselected" means
two separate parts from the hFE range with a 30 mV Vbe difference, which no factory pair would ship with."""
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import vcfdeck as V

OUT = Path(__file__).parent / 'results'
TM3 = json.loads((Path(__file__).parent / 'calibration.json').read_text())['tm3']


def area(mv):
    return math.exp(mv * 1e-3 / 0.02585)


CASES = {'matched': {}}
for q in ('Q12', 'Q21', 'Q22'):
    CASES[f'{q} Vbe off by 1 mV'] = dict(is_scale={q + 'A': area(1)})
    CASES[f'{q} Vbe off by 10 mV'] = dict(is_scale={q + 'A': area(10)})
    CASES[f'{q} Vbe off by 30 mV'] = dict(is_scale={q + 'A': area(30)})
    CASES[f'{q} hFE 400 and 320 (datasheet limit)'] = dict(half_bf={q + 'B': 320})
    CASES[f'{q} hFE 800 and 250'] = dict(half_bf={q + 'A': 800, q + 'B': 250})
    CASES[f'{q} hFE 250 and 800'] = dict(half_bf={q + 'A': 250, q + 'B': 800})
    CASES[f'{q} unselected, 30 mV, hFE 800 and 250'] = dict(is_scale={q + 'A': area(30)}, half_bf={q + 'A': 800, q + 'B': 250})
    CASES[f'{q} unselected, 30 mV, hFE 250 and 800'] = dict(is_scale={q + 'A': area(30)}, half_bf={q + 'A': 250, q + 'B': 800})
CUTS = dict(low=0.0, mid=0.5, high=1.0)
STEP = 0.125
PATTERN = [1, 0, 0, 1, 1, 0, 1, 0]
NOTES = [(0.25 + i * STEP, 0.25 + i * STEP + STEP / 2, 65.41, bool(a)) for i, a in enumerate(PATTERN)]


def small_signal(name):
    out = {}
    for label, cut in CUTS.items():
        o = {**dict(cut=cut, res=1.0, env=0.0, tm3=TM3), **CASES[name]}
        r = V.ac_run(o, fstart=30, fstop=20e3, per_decade=100)
        fp, _ = V.peak(r['f'], r['vca'], lo=40)
        b = V.ac_run(o, fstart=fp / 1.9, fstop=fp * 1.9, per_decade=1500)
        fp, pk = V.peak(b['f'], b['vca'], lo=fp / 2)
        m = 20 * np.log10(np.abs(b['vca']))
        i = int(np.argmin(np.abs(b['f'] - fp)))
        lo, hi = i, i
        while lo > 0 and m[lo] > pk - 3:
            lo -= 1
        while hi < len(m) - 1 and m[hi] > pk - 3:
            hi += 1
        f, T = V.loop_run(o, fstart=1)
        op = r['op']
        out[label] = dict(fpeak=float(fp), q=float(fp / (b['f'][hi] - b['f'][lo])), margin_db=float(V.oscillation_margin(f, T)[1]), ladder_ua=op['ladder_ua'], q21_collector_v=op.get('n140'), q21_emitter_v=op.get('n139'))
    return out


def time_domain(name):
    o = {**dict(cut=0.35, res=0.85, env=0.6, decay=0.35, acc=0.8, tm3=TM3), **CASES[name]}
    leak = V.tran_run(o, NOTES, 1.4, source=['Vsrc n126 0 DC 8.5'], tstep=25e-6, tmax=10e-6, save=('n623',))
    t, x = leak['t'], leak['n623']
    notes = V.tran_run(o, NOTES, 1.4, tstep=25e-6, tmax=10e-6, save=('n623',))
    open_vca = lambda y: max(float(np.ptp(y[(t >= n[0] + 0.004) & (t < n[1] + 0.016)])) for n in NOTES[1:]) * 1e3
    # Even harmonics, from a held note on the square wave, whose own even content is low
    q = {**dict(cut=0.5, res=0.85, env=0.0, tm3=TM3), **CASES[name]}
    d = V.tran_run(q, [(0.02, 10.0, 65.41, False)], 0.5, wave='square', tstep=10e-6, tmax=4e-6, reltol=5e-4, save=('n623',))
    tt, y = d['t'], d['n623']
    per = 1 / 65.41
    m = tt > tt[-1] - int(0.16 / per) * per
    tw, yw = tt[m], y[m] - y[m].mean()
    h = np.array([2 * abs(np.mean(yw * np.exp(-2j * np.pi * k * 65.41 * tw))) for k in range(1, 41)])
    return dict(leak_mvpp=float(np.ptp(x[t > 0.3])) * 1e3, leak_open_mvpp=open_vca(x), notes_open_mvpp=open_vca(notes['n623']), square_even_odd_db=float(20 * math.log10(np.sqrt((h[1::2] ** 2).sum()) / np.sqrt((h[0::2] ** 2).sum()))))


def case(name):
    return dict(name=name, small_signal=small_signal(name), time_domain=time_domain(name))


if __name__ == '__main__':
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(case, CASES))
    (OUT / 'pair_matching.json').write_text(json.dumps(rows, indent=1))
    base = rows[0]
    ref = base['time_domain']['notes_open_mvpp']
    print(f"{'case':42s} {'d oct at 0/50/100 %':>20s} {'Q at 0/50/100 %':>18s} {'d margin dB':>20s} {'leak dB':>8s} {'notes dB':>8s} {'even/odd':>8s}  Q21 coll V")
    for r in rows:
        s, b = r['small_signal'], base['small_signal']
        td = r['time_domain']
        print(f"{r['name']:42s} " + ' '.join(f"{math.log2(s[c]['fpeak'] / b[c]['fpeak']):6.2f}" for c in CUTS) + ' ' + ' '.join(f"{s[c]['q']:5.1f}" for c in CUTS) + ' ' + ' '.join(f"{s[c]['margin_db'] - b[c]['margin_db']:6.2f}" for c in CUTS)
              + f" {20 * math.log10(td['leak_open_mvpp'] / ref):8.1f} {20 * math.log10(td['notes_open_mvpp'] / ref):8.2f} {td['square_even_odd_db']:8.2f}  {s['mid']['q21_collector_v']}")
