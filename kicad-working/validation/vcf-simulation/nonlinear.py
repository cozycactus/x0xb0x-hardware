#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Large-signal behaviour and the output tap. Writes results/drive.json, results/tap.json, demo WAVs."""
import json
import math
import sys
import wave as wavelib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import vcfdeck as V

OUT = Path(__file__).parent / 'results'
OUT.mkdir(exist_ok=True)
TM3 = json.loads((Path(__file__).parent / 'calibration.json').read_text())['tm3']
F0 = 65.41


def harmonics(t, x, f0, n=60):
    """Amplitudes of harmonics 1..n over a whole number of periods at the end of the record."""
    dt = t[1] - t[0]
    per = 1.0 / f0
    cycles = int(0.16 / per)
    m = t > t[-1] - cycles * per
    tt, xx = t[m], x[m] - x[m].mean()
    return np.array([2 * abs(np.mean(xx * np.exp(-2j * np.pi * k * f0 * tt))) for k in range(1, n + 1)])


def drive_case(args):
    label, scale, wave, opts = args
    o = {**dict(cut=0.5, res=1.0, env=0.0, tm3=TM3), **opts}
    r = dict(o.get('r', {}))
    r['R62'] = 220e3 / scale
    o['r'] = r
    d = V.tran_run(o, [(0.02, 10.0, F0, False)], 0.5, wave=wave, tstep=10e-6, tmax=4e-6, reltol=5e-4, save=('n623', 'n126', 'n124', 'n60', 'n144'))
    t = d['t']
    h = harmonics(t, d['n623'], F0)
    hin = harmonics(t, d['n126'], F0)
    # Same MEG state as the transient (None: its resting point), or the peak moves and the comparison lies
    ac = V.ac_run({**o, 'meg': None}, fstart=20, fstop=20e3, per_decade=200)
    gain = np.array([np.interp((k + 1) * F0, ac['f'], np.abs(ac['vca'])) for k in range(len(h))])
    linear = hin * gain
    near = int(np.argmax(linear[:40]))
    return dict(label=label, scale=scale, wave=wave, h=h.tolist(), hin=hin.tolist(), linear=linear.tolist(), near=near, f_near=(near + 1) * F0,
                compress_db=float(20 * math.log10(h[near] / linear[near])), fund_db=float(20 * math.log10(h[0] / linear[0])),
                ratio_db=float(20 * math.log10(h[near] / h[0])), ratio_linear_db=float(20 * math.log10(linear[near] / linear[0])),
                even_odd_db=float(20 * math.log10(np.sum(h[1::2] ** 2) ** 0.5 / np.sum(h[0::2] ** 2) ** 0.5)),
                vd_pp=float(np.ptp(d['n124'][t > 0.3] - d['n60'][t > 0.3])), top_pp=float(np.ptp(d['n144'][t > 0.3])), vca_pp=float(np.ptp(d['n623'][t > 0.3])))


def drive():
    jobs = [(f'drive x{s}', s, 'saw', {}) for s in (0.1, 0.25, 0.5, 1, 2, 4, 8)]
    jobs += [(f'square x{s}', s, 'square', {}) for s in (0.25, 1, 4)]
    v = math.exp(10e-3 / 0.02585)
    jobs += [('Q12 off by 10 mV', 1, 'saw', dict(is_scale={'Q12A': v})), ('Q12 off by 1 mV', 1, 'saw', dict(is_scale={'Q12A': math.exp(1e-3 / 0.02585)})), ('ladder left +10 mV', 1, 'saw', dict(is_scale={'Q13': v, 'Q14': v, 'Q16': v}))]
    jobs += [(f'Res {x}', 1, 'saw', dict(res=x)) for x in (0.0, 0.5)]
    with ProcessPoolExecutor(6) as ex:
        rows = list(ex.map(drive_case, jobs))
    (OUT / 'drive.json').write_text(json.dumps(rows, indent=1))
    for r in rows:
        print(f"{r['label']:20s} Vd {r['vd_pp'] * 1e3:7.1f} mVpp  top {r['top_pp']:5.2f} Vpp  VCA {r['vca_pp'] * 1e3:7.2f} mVpp  near-peak harmonic {r['f_near']:6.0f} Hz:"
              f" actual vs linear {r['compress_db']:6.2f} dB, fundamental vs linear {r['fund_db']:6.2f} dB, peak/fund {r['ratio_db']:6.2f} dB (linear {r['ratio_linear_db']:6.2f}) even/odd {r['even_odd_db']:6.1f} dB")


def drive_case_safe(args):
    label, scale, wave, opts = args
    if 'res' in opts:
        o = dict(opts)
        res = o.pop('res')
        return drive_case_res(label, scale, wave, o, res)
    return drive_case(args)


def drive_case_res(label, scale, wave, opts, res):
    o = dict(cut=0.5, res=res, env=0.0, tm3=TM3, **opts)
    r = dict(o.get('r', {}))
    r['R62'] = 220e3 / scale
    o['r'] = r
    d = V.tran_run(o, [(0.02, 10.0, F0, False)], 0.5, wave=wave, tstep=10e-6, tmax=4e-6, reltol=5e-4, save=('n623', 'n126', 'n124', 'n60', 'n144'))
    t = d['t']
    h = harmonics(t, d['n623'], F0)
    hin = harmonics(t, d['n126'], F0)
    # Same MEG state as the transient (None: its resting point), or the peak moves and the comparison lies
    ac = V.ac_run({**o, 'meg': None}, fstart=20, fstop=20e3, per_decade=200)
    gain = np.array([np.interp((k + 1) * F0, ac['f'], np.abs(ac['vca'])) for k in range(len(h))])
    linear = hin * gain
    near = int(np.argmax(linear[:40]))
    return dict(label=label, scale=scale, wave=wave, h=h.tolist(), hin=hin.tolist(), linear=linear.tolist(), near=near, f_near=(near + 1) * F0,
                compress_db=float(20 * math.log10(h[near] / linear[near])), fund_db=float(20 * math.log10(h[0] / linear[0])),
                ratio_db=float(20 * math.log10(h[near] / h[0])), ratio_linear_db=float(20 * math.log10(linear[near] / linear[0])),
                even_odd_db=float(20 * math.log10(np.sum(h[1::2] ** 2) ** 0.5 / np.sum(h[0::2] ** 2) ** 0.5)),
                vd_pp=float(np.ptp(d['n124'][t > 0.3] - d['n60'][t > 0.3])), top_pp=float(np.ptp(d['n144'][t > 0.3])), vca_pp=float(np.ptp(d['n623'][t > 0.3])))


def tap_case(args):
    label, res, cut, r = args
    o = dict(cut=cut, res=res, env=0.0, tm3=TM3, r=r)
    a = V.ac_run(o, fstart=5, fstop=20e3, per_decade=80)
    m = 20 * np.log10(np.abs(a['vca']))
    top = 20 * np.log10(np.abs(a['top']))
    return dict(label=label, res=res, cut=cut, f=a['f'].tolist(), vca=m.tolist(), top=top.tolist())


def tap():
    jobs = []
    for res in (0.0, 0.25, 0.5, 0.75, 1.0):
        jobs.append(('stock', res, 0.5, {}))
        jobs.append(('stock', res, 1.0, {}))
        jobs.append(('no wiper tap', res, 0.5, {'R122': 1e9}))
        jobs.append(('large tap caps', res, 0.5, {'C20': 10e-6, 'C21': 10e-6}))
    with ProcessPoolExecutor(6) as ex:
        rows = list(ex.map(tap_case, jobs))
    (OUT / 'tap.json').write_text(json.dumps(rows))
    print('VCA-input gain (dB) at 32, 65, 130, 260 Hz; and top-node gain at 65 Hz')
    for r in rows:
        f = np.array(r['f'])
        g = [np.interp(x, f, r['vca']) for x in (32, 65.4, 130.8, 261.6)]
        print(f"{r['label']:16s} cut {r['cut']:.1f} res {r['res']:.2f}: " + ' '.join(f'{x:7.2f}' for x in g) + f"   top@65 {np.interp(65.4, f, r['top']):7.2f}   32-vs-65 {g[0] - g[1]:6.2f}")


# ---- A short demonstration pattern. The notes are mine; nothing is copied from a recording. ----
STEP = 0.125   # 120 BPM sixteenths
# (semitones above C1, accent, slide into the next step)
PATTERN = [(0, 1, 0), (0, 0, 0), (12, 0, 0), (0, 0, 1), (3, 1, 0), (0, 0, 0), (10, 0, 1), (12, 1, 0),
           (0, 0, 0), (0, 1, 0), (7, 0, 0), (0, 0, 0), (3, 0, 1), (5, 1, 1), (7, 1, 0), (0, 0, 0)]


def demo_case(args):
    name, wave, o = args
    loops = 2
    steps = PATTERN * loops
    tstart = 0.05
    notes = []
    i = 0
    fnote = lambda st: 65.41 * 2 ** (st / 12)
    for i, (st, ac, sl) in enumerate(steps):
        ton = tstart + i * STEP
        toff = ton + (STEP if sl else STEP / 2)
        notes.append((ton, toff, fnote(st), bool(ac)))
    t_end = tstart + len(steps) * STEP + 0.3

    def freq(t):
        k = min(max(int((t - tstart) // STEP), 0), len(steps) - 1)
        f_target = fnote(steps[k][0])
        if k and steps[k - 1][2]:  # slide: first-order glide from the previous note
            f_prev = fnote(steps[k - 1][0])
            return f_prev * (f_target / f_prev) ** (1 - math.exp(-(t - tstart - k * STEP) / 0.03))
        return f_target

    pts = []
    t = 0.0
    while t < t_end:
        per = 1.0 / freq(t)
        pts += [(t, 11.25), (t + per - 10e-6, 5.75)]
        t += per
    pts.append((t, 11.25))
    src = ['Vsaw n108 0 PWL(' + ' '.join(f'{a:.8g} {b:.6g}' for a, b in pts) + ')']
    if wave == 'saw':
        src.append('Rs1 n108 n126 1')
    else:
        src.append('Rs1 n303 n126 1')
        src += V.part_lines(V.SQUARE, o.get('r', {}), o.get('is_scale', {}))
    merged = notes  # tran_run merges tied gates
    d = V.tran_run(dict(o, tm3=TM3), merged, t_end, source=src, tstep=20.833e-6, tmax=8e-6, reltol=2e-3, save=('n623', 'n127', 'n146', 'n53', 'n161'))
    t = d['t']
    x = d['n623'] - np.mean(d['n623'])
    # A simple VCA stand-in, so that the file is listenable; the real IC15 VCA is not simulated.
    # From the Devil Fish manual: note starts ~4 ms after gate, ends ~16 ms after gate off. A slow decay
    # while the gate is high and a level boost on accent are approximations.
    spans = []
    for ton, toff, f, ac in merged:
        if spans and ton <= spans[-1][1] + 1e-6:
            spans[-1][1] = toff
        else:
            spans.append([ton, toff, ac])
    env = np.zeros_like(t)
    for ton, toff, ac in spans:
        m = (t >= ton + 0.004) & (t < toff + 0.016)
        tail = np.where(t[m] > toff + 0.008, 1 - (t[m] - toff - 0.008) / 0.008, 1.0)
        level = (1.8 if ac else 1.0) * np.exp(-(t[m] - ton) / 3.0)
        env[m] = np.maximum(env[m], level * tail)
    y = x * env
    sr = 48000
    tt = np.arange(t[0], t[-1], 1 / sr)
    yy = np.interp(tt, t, y)
    yy = yy - np.mean(yy)
    yy = 0.89 * yy / np.max(np.abs(yy))
    # fade the edges
    fade = int(0.005 * sr)
    yy[:fade] *= np.linspace(0, 1, fade)
    yy[-fade:] *= np.linspace(1, 0, fade)
    path = OUT / f'demo-{name}.wav'
    with wavelib.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((yy * 32767).astype('<i2').tobytes())
    ua = 1e6 * (d['n127'] - d['n146']) / 2200
    return dict(name=name, seconds=float(len(yy) / sr), ladder_peak_ua=float(ua.max()), ladder_min_ua=float(ua.min()), file=path.name)


def demo():
    jobs = [('saw', 'saw', dict(cut=0.35, res=0.85, env=0.6, decay=0.35, acc=0.8)),
            ('square', 'square', dict(cut=0.35, res=0.85, env=0.6, decay=0.35, acc=0.8)),
            ('saw-res-low', 'saw', dict(cut=0.35, res=0.15, env=0.6, decay=0.35, acc=0.8)),
            ('saw-no-accent-sweep', 'saw', dict(cut=0.35, res=0.85, env=0.6, decay=0.35, acc=0.8, r={'R72': 1e9}))]
    with ProcessPoolExecutor(4) as ex:
        for r in ex.map(demo_case, jobs):
            print(r)


if __name__ == '__main__':
    which = sys.argv[1:] or ['drive', 'tap', 'demo']
    if 'drive' in which:
        drive()
    if 'tap' in which:
        tap()
    if 'demo' in which:
        demo()
