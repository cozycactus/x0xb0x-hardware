#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""The last checks: margin decomposition, pot taper, the kit's near-sine note, roll-off slopes,
Stinchcombe's open question about mixed diodes. Writes results/extras.json."""
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import calibrate
import vcfdeck as V

OUT = Path(__file__).parent / 'results'
TM3 = json.loads((Path(__file__).parent / 'calibration.json').read_text())['tm3']
LARGE = {'C25': 100e-6, 'C27': 100e-6, 'C23': 1e-3, 'C14': 1e-3, 'C15': 1e-3}
VARIANTS = {
    'stock': {},
    'feedback x2': dict(r={'R97': 12.2e3 / 2 - 2.2e3}),
    'couplers removed': dict(r=LARGE),
    'couplers removed, Q21 not loading': dict(bf1583=20000, r={**LARGE, 'R113': 10e6, 'R114': 10e6}),
    'Q21 hFE 250': dict(bf1583=250),
    'Q21 hFE 800': dict(bf1583=800),
}


def margin_case(args):
    name, cut = args
    o = {**dict(cut=cut, res=1.0, env=0.0, tm3=TM3), **VARIANTS[name]}
    f, T = V.loop_run(o, fstart=1)
    osc = V.oscillation_margin(f, T)
    r = V.ac_run(o, fstart=10, fstop=30e3, per_decade=30)
    return dict(name=name, cut=cut, ladder_ua=r['op']['ladder_ua'], fosc=float(osc[0]), margin_db=float(osc[1]))


def harmonics(t, x, f0, n=12):
    per = 1 / f0
    m = t > t[-1] - int(0.16 / per) * per
    tt, xx = t[m], x[m] - x[m].mean()
    return np.array([2 * abs(np.mean(xx * np.exp(-2j * np.pi * k * f0 * tt))) for k in range(1, n + 1)])


def main():
    out = {}
    with ProcessPoolExecutor(8) as ex:
        out['margins'] = list(ex.map(margin_case, [(n, float(c)) for n in VARIANTS for c in np.linspace(0, 1, 11)]))
    for n in VARIANTS:
        print(f'{n:36s}', ' '.join(f"{r['margin_db']:6.2f}" for r in out['margins'] if r['name'] == n))

    # Pot taper: only the knob-to-Hz map depends on it, so bracket the unknown.
    taper = {}
    original = V.taper_a
    for half in (0.10, 0.15, 0.20, 0.25):
        V.taper_a = lambda x, h=half: 2 * h * x if x <= 0.5 else h + 2 * (1 - h) * (x - 0.5)
        tm3 = calibrate.tune()
        lo = V.ac_run(dict(cut=0.0, res=1.0, env=0.0, tm3=tm3), fstart=40, fstop=30e3, per_decade=120)
        hi = V.ac_run(dict(cut=1.0, res=1.0, env=0.0, tm3=tm3), fstart=40, fstop=30e3, per_decade=120)
        taper[half] = dict(tm3=tm3, f_low=float(V.peak(lo['f'], lo['vca'], lo=40)[0]), f_high=float(V.peak(hi['f'], hi['vca'], lo=40)[0]))
        print('taper half-rotation', half, {k: round(v, 3) for k, v in taper[half].items()})
    V.taper_a = original
    out['taper'] = taper

    # The kit: "twist cutoff and resonance all the way down and examine the almost sinusoidal notes", at 3 V (130.8 Hz)
    for label, cut, res in (('both down', 0.0, 0.0), ('both up', 1.0, 1.0)):
        d = V.tran_run(dict(cut=cut, res=res, env=0.0, tm3=TM3), [(0.02, 10.0, 130.81, False)], 0.5, tstep=10e-6, tmax=5e-6, save=('n623', 'n144'))
        h = harmonics(d['t'], d['n144'], 130.81)
        hv = harmonics(d['t'], d['n623'], 130.81)
        out['kit_' + label] = dict(top=h.tolist(), vca=hv.tolist())
        print(f'{label}: harmonics re fundamental at Q19 emitter (dB)', np.round(20 * np.log10(h[:6] / h[0]), 1), ' THD %', round(100 * float(np.sqrt(np.sum(h[1:] ** 2)) / h[0]), 1),
              '; VCA input THD %', round(100 * float(np.sqrt(np.sum(hv[1:] ** 2)) / hv[0]), 1))

    # Roll-off slope of the ladder alone
    c = json.loads((OUT / 'ladder_check.json').read_text())
    row = next(r for r in c if r['cut'] == 0.5 and r['c18'] == 18e-9)
    f = np.array(row['f'])
    sim, calc = np.array(row['sim_unloaded']), np.array(row['calc'])
    slopes = []
    for a in (100, 200, 400, 800, 1600, 3200, 6400, 12800):
        s = 20 * math.log10(np.interp(2 * a, f, sim) / np.interp(a, f, sim))
        slopes.append((a, 2 * a, round(s, 1), round(20 * math.log10(np.interp(2 * a, f, calc) / np.interp(a, f, calc)), 1)))
    out['slopes'] = slopes
    print('slope dB/oct (SPICE, analytic) for If =', round(row['ladder_ua'], 2), 'uA:', slopes)

    # Stinchcombe's anomaly: 1N4148s at the top of the ladder give more gain than the model predicts, and he
    # suspected the emission coefficient. Measure the passband gain, with the output amp off the ladder.
    res = {}
    base = dict(cut=0.5, res=0.0, env=0.0, tm3=TM3, r={'C25': 1e-13, 'C27': 1e-13})
    def gain(**kw):
        r = V.ac_run({**base, **kw}, fstart=5, fstop=1e3, per_decade=30)
        return 20 * math.log10(np.interp(8.0, r['f'], np.abs(r['ladder'] / r['vd'])))
    res['stock'] = gain()
    res['top 1N4148, N=1.752'] = gain(subst=('Q22',))
    models = V.MODELS
    V.MODELS = models.replace('N=1.752', 'N=1.0')
    res['top diode, N forced to 1'] = gain(subst=('Q22',))
    V.MODELS = models
    res['ladder 1N4148, top transistor'] = gain(subst=('Q13', 'Q14', 'Q15', 'Q16', 'Q17', 'Q23'))
    out['mixed_diodes'] = res
    print('passband gain of the ladder alone (dB):', {k: round(v, 2) for k, v in res.items()})

    # What a lower or higher gain part does at Q21, for the choice of substitute
    table = {}
    for bf in (100, 150, 200, 300, 400, 600, 800):
        row = {}
        for name, cut in (('low', 0.0), ('mid', 0.5), ('high', 1.0)):
            o = dict(cut=cut, res=1.0, env=0.0, tm3=TM3, bf1583=bf)
            a = V.ac_run(o, fstart=30, fstop=20e3, per_decade=100)
            fp, _ = V.peak(a['f'], a['vca'], lo=40)
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
            row[name] = dict(q=fp / (b['f'][hi] - b['f'][lo]), margin=V.oscillation_margin(f, T)[1], sub=V.oscillation_margin(f, T, fmin=1, fmax=40)[1])
        table[bf] = row
        print('Q21 hFE', bf, ' '.join(f"{k}: Q {v['q']:5.1f} margin {v['margin']:6.2f}" for k, v in row.items()))
    out['hfe_table'] = table

    # Critical gain and frequency law
    laws = {}
    for name, r in (('equal', 1.0), ('half', 0.5), ('actual .018/.033', 18 / 33)):
        k, w = V.critical_k(r)
        c = V.poly_coeffs(r)
        roots = np.roots(c)
        laws[name] = dict(k=k, w=w, hz_per_ua=w * 1e-6 / (2 * math.pi * 4 * 0.02585 * 33e-9), poles=sorted(roots.real.tolist()))
        print(name, 'k_crit', round(k, 2), 'x', round(w, 4), 'Hz/uA', round(laws[name]['hz_per_ua'], 1), 'poles (x plane)', np.round(sorted(roots.real), 3))
    out['laws'] = laws

    # Operating point against hand values, for checking a built board
    op = V.ac_run(dict(cut=0.5, res=1.0, env=0.0, tm3=TM3), fstart=100, fstop=1000, per_decade=5)['op']
    out['op'] = {k: v for k, v in op.items() if k != 'log'}
    print({k: round(v, 3) for k, v in out['op'].items()})
    (OUT / 'extras.json').write_text(json.dumps(out, indent=1, default=float))


if __name__ == '__main__':
    main()
