#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Small-signal studies, each changing one thing from the trimmed baseline. Writes results/*.json."""
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import vcfdeck as V

OUT = Path(__file__).parent / 'results'
OUT.mkdir(exist_ok=True)
CAL = json.loads((Path(__file__).parent / 'calibration.json').read_text())
TM3 = CAL['tm3']
CUTS = dict(low=0.0, mid=0.5, high=1.0)
VT = 0.02585


def caps(scale):
    return {c: float(V.COMP[c]['value']) * 1e-6 * scale for c in ('C18', 'C19', 'C24', 'C26')}


def vbe_mismatch(mv):
    """Area factor for a Vbe difference of mv (split between the pair)."""
    return math.exp(mv * 1e-3 / VT)


CASES = {
    'baseline': {},
    # Ladder capacitors
    'C18 .033 (equal caps)': dict(r={'C18': 33e-9}),
    'C18 .0165 (exactly half)': dict(r={'C18': 16.5e-9}),
    'C18 .010': dict(r={'C18': 10e-9}),
    'all ladder caps x2': dict(r=caps(2)),
    'all ladder caps x0.5': dict(r=caps(0.5)),
    # AC coupling inside the feedback loop
    'C25,C27 .1 -> 1 uF (top couplers)': dict(r={'C25': 1e-6, 'C27': 1e-6}),
    'C25,C27 .1 -> .047 uF': dict(r={'C25': 47e-9, 'C27': 47e-9}),
    'C23 1 -> 10 uF (feedback coupler)': dict(r={'C23': 10e-6}),
    'C23 1 -> .22 uF': dict(r={'C23': 0.22e-6}),
    'C14,C15 1 -> 10 uF': dict(r={'C14': 10e-6, 'C15': 10e-6}),
    'all four couplers large (no HP)': dict(r={'C25': 100e-6, 'C27': 100e-6, 'C23': 1e-3, 'C14': 1e-3, 'C15': 1e-3}),
    # The feedback amplifier
    'Q12 hFE 250 (datasheet min)': dict(bfq12=250),
    'Q12 hFE 800 (datasheet max)': dict(bfq12=800),
    'Q21 hFE 250 (datasheet min)': dict(bf1583=250),
    'Q21 hFE 800 (datasheet max)': dict(bf1583=800),
    'R113,R114 100K -> 1M (bias only)': dict(r={'R113': 1e6, 'R114': 1e6}),
    'R108 2.2K -> 3.3K (less amp current)': dict(r={'R108': 3.3e3}),
    'R108 2.2K -> 1.5K (more amp current)': dict(r={'R108': 1.5e3}),
    'R110,R111 22K -> 18K': dict(r={'R110': 18e3, 'R111': 18e3}),
    'R97 10K -> 4.7K (about double feedback)': dict(r={'R97': 4.7e3}),
    'R97 10K -> 22K (about half feedback)': dict(r={'R97': 22e3}),
    # Ladder devices
    '2SC536 hFE 160': dict(bf536=160),
    '2SC536 hFE 320': dict(bf536=320),
    '2SC2291 hFE 250': dict(bf2291=250),
    '2SC2291 hFE 800': dict(bf2291=800),
    # Matching (datasheet: 1 mV typical, 10 mV max)
    'Q12 pair off by 1 mV': dict(is_scale={'Q12A': vbe_mismatch(1)}),
    'Q12 pair off by 10 mV': dict(is_scale={'Q12A': vbe_mismatch(10)}),
    'Q21 pair off by 10 mV': dict(is_scale={'Q21A': vbe_mismatch(10)}),
    'Q22 pair off by 10 mV': dict(is_scale={'Q22A': vbe_mismatch(10)}),
    'ladder left side +10 mV each': dict(is_scale={'Q13': vbe_mismatch(10), 'Q14': vbe_mismatch(10), 'Q16': vbe_mismatch(10)}),
    # Temperature and supplies
    'temperature 15 C': dict(temp=15),
    'temperature 35 C': dict(temp=35),
    'temperature 45 C': dict(temp=45),
    # Control scale
    'Q10/Q11 Is ratio x2 (unmatched NPN/PNP)': dict(is_scale={'Q11': 2.0}),
    'TM3 at 400 Hz tune': dict(tm3=CAL['tm3_400']),
    'TM3 at 600 Hz tune': dict(tm3=CAL['tm3_600']),
    'MEG cap floor 0.2 V (long idle)': dict(meg=0.2),
    'Q11 1 C hotter than Q10 (2 mV)': dict(is_scale={'Q11': vbe_mismatch(2)}),
    # Devices people substitute, and the loading of the output amp
    'ladder of 1N4148 instead of 2SC536': dict(subst=('Q13', 'Q14', 'Q15', 'Q16', 'Q17', 'Q23')),
    'top pair Q22 as 1N4148': dict(subst=('Q22',)),
    'couplers large AND Q21 not loading': dict(bf1583=20000, r={'R113': 10e6, 'R114': 10e6, 'C25': 100e-6, 'C27': 100e-6, 'C23': 1e-3, 'C14': 1e-3, 'C15': 1e-3}),
}


def measure(args):
    name, case, cutname, res, tm3 = args
    o = {**dict(cut=CUTS[cutname], res=res, env=0.0, tm3=tm3), **case}
    if 'tm3' in case:
        o['tm3'] = case['tm3']
    r = V.ac_run(o, fstart=10, fstop=40e3, per_decade=120)
    f, vca = r['f'], r['vca']
    fp, pk = V.peak(f, vca, lo=40)
    g65 = float(np.interp(65.4, f, 20 * np.log10(np.abs(vca))))
    # width of the peak at -3 dB gives Q, on a fine grid around the peak
    rf = V.ac_run(o, fstart=fp / 1.9, fstop=fp * 1.9, per_decade=1500)
    fp, pk = V.peak(rf['f'], rf['vca'], lo=fp / 2)
    ff = rf['f']
    m = 20 * np.log10(np.abs(rf['vca']))
    ip = int(np.argmin(np.abs(ff - fp)))
    lo = ip
    while lo > 0 and m[lo] > pk - 3:
        lo -= 1
    hi = ip
    while hi < len(ff) - 1 and m[hi] > pk - 3:
        hi += 1
    q = fp / (ff[hi] - ff[lo]) if lo > 0 and hi < len(ff) - 1 else None
    fl, T = V.loop_run(o, fstart=1)
    osc = V.oscillation_margin(fl, T)
    sub = V.oscillation_margin(fl, T, fmin=1.0, fmax=40.0)
    return dict(name=name, cut=cutname, res=res, ladder_ua=r['op']['ladder_ua'], fpeak=float(fp), peak_db=float(pk), q=q, gain65_db=g65,
                fosc=float(osc[0]) if osc else None, margin_db=float(osc[1]) if osc else None,
                fsub=float(sub[0]) if sub else None, sub_db=float(sub[1]) if sub else None)


def one_at_a_time():
    jobs = [(n, c, cn, 1.0, TM3) for n, c in CASES.items() for cn in CUTS]
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(measure, jobs))
    (OUT / 'one_at_a_time.json').write_text(json.dumps(rows, indent=1))
    base = {r['cut']: r for r in rows if r['name'] == 'baseline'}
    print(f"{'change':44s} {'cut':4s} {'uA':>6s} {'fpk Hz':>8s} {'d oct':>6s} {'pk dB':>7s} {'d dB':>6s} {'Q':>5s} {'fosc':>7s} {'margin':>7s} {'d m':>6s} {'fsub':>5s} {'sub':>6s}")
    for r in rows:
        b = base[r['cut']]
        print(f"{r['name'][:44]:44s} {r['cut']:4s} {r['ladder_ua']:6.2f} {r['fpeak']:8.1f} {math.log2(r['fpeak'] / b['fpeak']):6.2f} {r['peak_db']:7.2f} {r['peak_db'] - b['peak_db']:6.2f} "
              f"{(r['q'] or 0):5.1f} {r['fosc']:7.1f} {r['margin_db']:7.2f} {r['margin_db'] - b['margin_db']:6.2f} {(r['fsub'] or 0):5.1f} {(r['sub_db'] or 0):6.2f}")


def knob_map(args):
    cut, res = args
    o = dict(cut=cut, res=res, env=0.0, tm3=TM3)
    r = V.ac_run(o, fstart=10, fstop=40e3, per_decade=120)
    fl, T = V.loop_run(o, fstart=1)
    osc = V.oscillation_margin(fl, T)
    return dict(cut=cut, res=res, T_f=fl.tolist(), T_db=(20 * np.log10(np.abs(T))).tolist(), T_deg=np.degrees(np.unwrap(np.angle(T))).tolist(), f=r['f'].tolist(), vca_db=(20 * np.log10(np.abs(r['vca']))).tolist(), top_db=(20 * np.log10(np.abs(r['top']))).tolist(),
                ladder_ua=r['op']['ladder_ua'], fosc=float(osc[0]) if osc else None, margin_db=float(osc[1]) if osc else None)


def responses():
    jobs = [(float(c), float(res)) for c in (0, 0.25, 0.5, 0.75, 1.0) for res in (0, 0.25, 0.5, 0.75, 1.0)]
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(knob_map, jobs))
    (OUT / 'responses.json').write_text(json.dumps(rows))
    for r in rows:
        if r['res'] == 1:
            print('cut', r['cut'], 'ladder uA', round(r['ladder_ua'], 2), 'osc', round(r['fosc'], 1), 'margin', round(r['margin_db'], 2))


def fine_margin(args):
    cut, res, mult = args
    o = dict(cut=cut, res=res, env=0.0, tm3=TM3)
    if mult != 1.0:
        o['r'] = {'R97': (10e3 + 2.2e3) / mult - 2.2e3}
    fl, T = V.loop_run(o, fstart=1)
    osc = V.oscillation_margin(fl, T)
    sub = V.oscillation_margin(fl, T, fmin=1.0, fmax=40.0)
    r = V.ac_run(o, fstart=10, fstop=40e3, per_decade=40)
    return dict(cut=cut, res=res, mult=mult, ladder_ua=r['op']['ladder_ua'], fosc=float(osc[0]), margin_db=float(osc[1]),
                fsub=float(sub[0]) if sub else None, sub_db=float(sub[1]) if sub else None)


def margins():
    jobs = [(float(c), float(res), m) for c in np.linspace(0, 1, 11) for res in (0.5, 0.75, 1.0) for m in (1.0, 2.0)]
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(fine_margin, jobs))
    (OUT / 'margins.json').write_text(json.dumps(rows, indent=1))
    for m in (1.0, 2.0):
        print('feedback x', m, ' Res 100 %:')
        for r in rows:
            if r['mult'] == m and r['res'] == 1.0:
                print(f"  cut {r['cut']:.1f}  {r['ladder_ua']:6.2f} uA  {r['fosc']:7.1f} Hz  margin {r['margin_db']:6.2f} dB {'SELF-OSC' if r['margin_db'] > 0 else '        '}  sub-audio {(r['fsub'] or 0):5.1f} Hz {(r['sub_db'] or 0):6.2f} dB")


def ladder_check():
    """Compare the circuit's own ladder with the analytic polynomial, using the current SPICE reports.
    Res 0 opens the loop, so ladder/vd is the ladder alone."""
    rows = []
    for cut in (0.0, 0.5, 1.0):
        for r18 in (18e-9, 33e-9):
            o = dict(cut=cut, res=0.0, env=0.0, tm3=TM3, r={'C18': r18})
            res = V.ac_run(o, fstart=10, fstop=40e3, per_decade=60)
            f = res['f']
            sim = np.abs(res['ladder'] / res['vd'])
            # also an unloaded version: Q21 removed from the ladder by C25,C27 -> ~0
            o2 = dict(o, r={'C18': r18, 'C25': 1e-13, 'C27': 1e-13})
            res2 = V.ac_run(o2, fstart=10, fstop=40e3, per_decade=60)
            sim2 = np.abs(res2['ladder'] / res2['vd'])
            If = res['op']['ladder_ua'] * 1e-6
            a = 2 * VT / If
            C = 33e-9
            x = 2 * a * C * 2j * np.pi * f
            calc = np.abs(1 / V.ladder_poly(x, r18 / C))
            f3 = lambda h: float(f[np.argmax(h / h[3] < 1 / math.sqrt(2))])
            rows.append(dict(cut=cut, c18=r18, ladder_ua=res['op']['ladder_ua'], f=f.tolist(), sim=sim.tolist(), sim_unloaded=sim2.tolist(), calc=calc.tolist(),
                             f3_sim=f3(sim), f3_unloaded=f3(sim2), f3_calc=f3(calc)))
            print(f"cut {cut:.1f} C18 {r18 * 1e9:4.0f} nF  If {If * 1e6:6.2f} uA  f-3dB calc {f3(calc):7.1f}  unloaded {f3(sim2):7.1f}  with Q21 {f3(sim):7.1f}   "
                  f"dB error at 1 kHz: unloaded {20 * math.log10(np.interp(1000, f, sim2) / np.interp(1000, f, calc)):5.2f}, with Q21 {20 * math.log10(np.interp(1000, f, sim) / np.interp(1000, f, calc)):5.2f}")
    (OUT / 'ladder_check.json').write_text(json.dumps(rows))


def mc_sample(seed):
    rng = np.random.default_rng(seed)
    r = {}
    for ref in V.FILTER + V.OUTPUT_TAP:
        if ref[0] == 'R':
            r[ref] = V.value_of(ref, {}) * rng.uniform(0.95, 1.05)
        elif ref in ('C18', 'C19', 'C24', 'C26', 'C25', 'C27', 'C20', 'C21'):
            r[ref] = V.value_of(ref, {}) * rng.uniform(0.9, 1.1)
        elif ref[0] == 'C':
            r[ref] = V.value_of(ref, {}) * rng.uniform(0.8, 1.2)
    bf = float(rng.uniform(250, 800))
    bfq12 = float(rng.uniform(250, 800))
    bf536 = float(rng.uniform(160, 320))
    bf2291 = float(rng.uniform(250, 800))
    scale = {'Q11': float(np.exp(rng.uniform(-math.log(2), math.log(2))))}
    for q in ('Q12A', 'Q21A', 'Q22A'):
        scale[q] = vbe_mismatch(rng.uniform(-3, 3))
    for q in ('Q13', 'Q14', 'Q15', 'Q16', 'Q17', 'Q23'):
        scale[q] = vbe_mismatch(rng.uniform(-3, 3))
    base = dict(r=r, is_scale=scale, bf1583=bf, bfq12=bfq12, bf536=bf536, bf2291=bf2291)
    # Trim TM3 for the kit's 500 Hz: the peak follows the current, and the current 1/(R73 + TM3)
    rt = lambda x: 1e5 * (r['R73'] / 1e5) + x * 500e3
    tm3 = TM3
    in_range = True
    for _ in range(4):
        res = V.ac_run(dict(base, cut=0.5, res=1.0, env=0.0, tm3=tm3), fstart=60, fstop=20e3, per_decade=150)
        fp, _ = V.peak(res['f'], res['vca'], lo=60)
        tm3_new = (rt(tm3) * fp / 500.0 - r['R73']) / 500e3
        if tm3_new < 0 or tm3_new > 1:
            in_range = False
        tm3 = min(max(tm3_new, 0.0), 1.0)
    row = dict(seed=seed, bf1583=bf, tm3=tm3, in_range=in_range)
    for name, cut in CUTS.items():
        o = dict(base, cut=cut, res=1.0, env=0.0, tm3=tm3)
        fl, T = V.loop_run(o, fstart=1)
        osc = V.oscillation_margin(fl, T)
        sub = V.oscillation_margin(fl, T, fmin=1.0, fmax=40.0)
        ac = V.ac_run(o, fstart=20, fstop=30e3, per_decade=100)
        fp, _ = V.peak(ac['f'], ac['vca'], lo=40)
        row[name] = dict(fpeak=float(fp), margin_db=float(osc[1]), fosc=float(osc[0]), sub_db=float(sub[1]) if sub else None, fsub=float(sub[0]) if sub else None, ladder_ua=ac['op']['ladder_ua'])
    return row


def monte_carlo(n=200):
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(mc_sample, range(n)))
    (OUT / 'monte_carlo.json').write_text(json.dumps(rows, indent=1))
    for name in CUTS:
        m = np.array([r[name]['margin_db'] for r in rows])
        s = np.array([r[name]['sub_db'] for r in rows])
        fp = np.array([r[name]['fpeak'] for r in rows])
        print(f"{name:5s} audio margin {np.percentile(m, 5):6.2f} / {np.median(m):6.2f} / {np.percentile(m, 95):6.2f} dB, {100 * np.mean(m > 0):5.1f} % self-oscillate;"
              f" sub {np.percentile(s, 5):6.2f} / {np.median(s):6.2f} / {np.percentile(s, 95):6.2f} dB, {100 * np.mean(s > 0):5.1f} % unstable; peak {np.percentile(fp, 5):7.1f} / {np.median(fp):7.1f} / {np.percentile(fp, 95):7.1f} Hz")
    bf = np.array([r['bf1583'] for r in rows])
    m = np.array([r['high']['margin_db'] for r in rows])
    s = np.array([r['high']['sub_db'] for r in rows])
    print('correlation of hFE with audio margin at high cut', round(float(np.corrcoef(bf, m)[0, 1]), 2), 'and sub margin', round(float(np.corrcoef(bf, s)[0, 1]), 2))
    print('TM3 trim reached 500 Hz in', sum(r['in_range'] for r in rows), 'of', n, '; median', round(float(np.median([r['tm3'] for r in rows])), 3))


if __name__ == '__main__':
    which = sys.argv[1:] or ['ladder', 'one', 'resp', 'margins', 'mc']
    if 'ladder' in which:
        ladder_check()
    if 'one' in which:
        one_at_a_time()
    if 'resp' in which:
        responses()
    if 'margins' in which:
        margins()
    if 'mc' in which:
        monte_carlo()
