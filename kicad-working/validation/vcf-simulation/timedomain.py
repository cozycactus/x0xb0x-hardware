#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Time-domain studies with the real MEG and accent circuits. Writes results/*.json, and the
long waveform arrays that plots.py needs to native-probes/ (ignored by git)."""
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
PROBES = Path(__file__).parent / 'native-probes'
PROBES.mkdir(exist_ok=True)
TM3 = json.loads((Path(__file__).parent / 'calibration.json').read_text())['tm3']
R69 = 2200.0


def ladder_ua(d):
    return 1e6 * (d['n127'] - d['n146']) / R69


def band_env(t, x, f0, width=0.25):
    """Envelope of x in a band around f0, by FFT."""
    dt = t[1] - t[0]
    X = np.fft.rfft(x - x.mean())
    fr = np.fft.rfftfreq(len(x), dt)
    X[(fr < f0 * (1 - width)) | (fr > f0 * (1 + width))] = 0
    return 2 * np.abs(np.fft.ifft(np.concatenate([X, np.zeros(len(x) - len(X))])))


def kick_case(args):
    cut, mult, bf, fa = args
    o = dict(cut=cut, res=1.0, env=0.0, tm3=TM3, bf1583=bf)
    if mult != 1:
        o['r'] = {'R97': 12.2e3 / mult - 2.2e3}
    src = ['Vsrc n126 0 PWL(0 8.5 0.05 8.5 0.0501 9.5 0.0502 8.5)']
    d = V.tran_run(o, [], 2.0, source=src, tstep=20e-6, tmax=10e-6, save=('n144', 'n623', 'n127', 'n146', 'n60', 'n124'))
    t, x = d['t'], d['n144']
    env_a = band_env(t, x, fa, 0.3)
    env_s = band_env(t, x, 8.0, 0.7)
    ok = t > 0.06
    tail = t > 1.7
    # decay rate of the audio ring from its envelope, between 10 % and 90 % of the kept time
    mask = (t > 0.055) & (t < 0.055 + 0.05)
    slope = np.polyfit(t[mask], np.log(env_a[mask] + 1e-12), 1)[0]
    return dict(cut=cut, mult=mult, bf=bf, fa=fa, audio_peak=float(env_a[ok].max()), audio_tail=float(env_a[tail].max()), audio_rate=float(slope),
                sub_peak=float(env_s[ok].max()), sub_tail=float(env_s[tail].max()), pp_tail=float(np.ptp(x[tail])), ua=float(ladder_ua(d)[-1]))


def kicks():
    jobs = [(0.0, 1, 400, 265.0), (0.5, 1, 400, 560.0), (1.0, 1, 400, 1824.0), (0.0, 2, 400, 273.0), (0.5, 2, 400, 569.0), (1.0, 2, 400, 1834.0),
            (1.0, 1, 800, 1830.0), (0.5, 1, 800, 560.0), (0.0, 1, 800, 265.0)]
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(kick_case, jobs))
    (OUT / 'kicks.json').write_text(json.dumps(rows, indent=1))
    for r in rows:
        print(f"cut {r['cut']:.1f} fb x{r['mult']} hFE {r['bf']}: audio ring {r['audio_peak'] * 1e3:8.2f} mV -> tail {r['audio_tail'] * 1e3:8.2f} mV, rate {r['audio_rate']:8.1f} /s;"
              f" 8 Hz band {r['sub_peak'] * 1e3:8.2f} -> tail {r['sub_tail'] * 1e3:8.2f} mV; tail p-p {r['pp_tail'] * 1e3:8.1f} mV")


def waveforms_case(args):
    res, cut, wave, f0 = args
    o = dict(cut=cut, res=res, env=0.0, tm3=TM3)
    d = V.tran_run(o, [(0.02, 10.0, f0, False)], 0.5, wave=wave, tstep=10e-6, tmax=5e-6,
                   save=('n623', 'n144', 'n126', 'n124', 'n60', 'n127', 'n146', 'n53'))
    keep = d['t'] > 0.34
    t = d['t'][keep]
    return dict(res=res, cut=cut, wave=wave, f0=f0, t=t - t[0], vca=d['n623'][keep], src=d['n126'][keep], top=d['n144'][keep], ua=ladder_ua(d)[keep], vd=(d['n124'] - d['n60'])[keep])


def waveforms():
    jobs = [(res, cut, wave, 65.41) for wave in ('saw', 'square') for res in (0.0, 0.5, 1.0) for cut in (0.5,)] + [(1.0, 1.0, 'saw', 65.41), (1.0, 0.0, 'saw', 65.41), (1.0, 0.5, 'saw', 130.81), (1.0, 0.5, 'square', 130.81)]
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(waveforms_case, jobs))
    np.savez_compressed(PROBES / 'waveforms.npz', rows=np.array(rows, dtype=object), allow_pickle=True)
    (OUT / 'waveforms_summary.json').write_text(json.dumps([
        dict(wave=r['wave'], f0=r['f0'], cut=r['cut'], res=r['res'], vca_mvpp=float(np.ptp(r['vca']) * 1e3), q12_vd_mvpp=float(np.ptp(r['vd']) * 1e3), top_vpp=float(np.ptp(r['top'])),
             source_vpp=float(np.ptp(r['src'])), source_mean=float(r['src'].mean()), ladder_ua=float(r['ua'].mean())) for r in rows], indent=1))
    for r in rows:
        print(f"{r['wave']:6s} {r['f0']:6.1f} Hz cut {r['cut']:.1f} res {r['res']:.1f}: VCA-in {np.ptp(r['vca']) * 1e3:7.2f} mVpp, Q12 Vd {np.ptp(r['vd']) * 1e3:6.1f} mVpp, top {np.ptp(r['top']):6.2f} Vpp, source {np.ptp(r['src']):5.2f} Vpp mean {r['src'].mean():5.2f}, ladder {r['ua'].mean():6.2f} uA")


def env_case(args):
    label, cut, res, envm, decay, acc, pattern, wave = args
    o = dict(cut=cut, res=res, env=envm, decay=decay, acc=acc, tm3=TM3)
    step = 0.125
    notes = [(0.25 + i * step, 0.25 + i * step + step / 2, 65.41, bool(a)) for i, a in enumerate(pattern)]
    d = V.tran_run(o, notes, 0.25 + len(pattern) * step + 0.5, wave=wave, tstep=25e-6, tmax=10e-6, reltol=2e-3,
                   save=('n53', 'n46', 'n134', 'n561', 'n127', 'n146', 'n161', 'n152', 'n623'))
    ds = 8
    return dict(label=label, cut=cut, res=res, env=envm, decay=decay, acc=acc, pattern=list(pattern), t=d['t'][::ds], meg=d['n53'][::ds], c62=d['n46'][::ds], sum_mv=1e3 * (d['n134'] - d['n561'])[::ds], ua=ladder_ua(d)[::ds], c13=d['n161'][::ds], vca=d['n623'])


def envelopes():
    pattern_all = [1] * 8
    pattern_none = [0] * 8
    jobs = []
    for res in (0.0, 0.5, 1.0):
        jobs.append((f'accent all, Res {res:.1f}', 0.5, res, 0.5, 0.5, 1.0, pattern_all, 'saw'))
    jobs.append(('no accent, Res 1', 0.5, 1.0, 0.5, 0.5, 1.0, pattern_none, 'saw'))
    for envm in (0.0, 0.5, 1.0):
        jobs.append((f'Env {envm:.1f}', 0.5, 0.5, envm, 0.5, 0.0, [0, 0, 0, 0, 0, 0, 0, 0], 'saw'))
    for dec in (0.0, 1.0):
        jobs.append((f'Decay {dec:.1f}', 0.5, 0.5, 1.0, dec, 0.0, [0, 0, 0, 0], 'saw'))
    for acc in (0.25, 0.5, 1.0):
        jobs.append((f'accent pot {acc}', 0.5, 1.0, 0.5, 0.5, acc, pattern_all, 'saw'))
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(env_case, jobs))
    np.savez_compressed(PROBES / 'envelopes.npz', rows=np.array(rows, dtype=object), allow_pickle=True)
    summary = []
    for r in rows:
        t = r['t']
        step = 0.125
        peaks = []
        for i in range(len(r['pattern'])):
            m = (t >= 0.25 + i * step) & (t < 0.25 + (i + 1) * step)
            peaks.append(float(r['ua'][m].max()))
        rest = float(r['ua'][(t > 0.15) & (t < 0.24)].mean())
        delays = []
        for i in range(len(r['pattern'])):
            m = (t >= 0.25 + i * step) & (t < 0.25 + (i + 1) * step)
            delays.append(float(t[m][int(np.argmax(r['ua'][m]))] - (0.25 + i * step)) * 1e3)
        summary.append(dict(label=r['label'], cut=r['cut'], res=r['res'], env=r['env'], decay=r['decay'], acc=r['acc'], rest_ua=rest, note_peaks_ua=peaks, gate_to_peak_ms=delays,
                            meg_max=float(r['meg'].max()), sum_max_mv=float(r['sum_mv'].max()), sum_min_mv=float(r['sum_mv'].min())))
        print(f"{r['label']:24s} rest {rest:6.2f} uA  note peaks " + ' '.join(f'{p:6.1f}' for p in peaks) + f"   MEG max {r['meg'].max():5.2f} V min {r['meg'][t > 0.3].min():5.2f} V  sum max {r['sum_mv'].max():6.1f} mV min {r['sum_mv'].min():6.1f} mV")
    (OUT / 'envelopes_summary.json').write_text(json.dumps(summary, indent=1))


def slow_case(args):
    """A long run with no notes: does the loop's sub-audio crossing really grow?"""
    bf, cut, mult = args
    o = dict(cut=cut, res=1.0, env=0.0, tm3=TM3, bf1583=bf)
    if mult != 1:
        o['r'] = {'R97': 12.2e3 / mult - 2.2e3}
    src = ['Vsrc n126 0 PWL(0 8.5 0.05 8.5 0.0501 9.5 0.0502 8.5)']
    d = V.tran_run(o, [], 16.0, source=src, tstep=100e-6, tmax=50e-6, save=('n144', 'n623'))
    t, x = d['t'], d['n144']
    windows = [(1, 2), (4, 5), (8, 9), (12, 13), (15, 16)]
    pp = [float(np.ptp(x[(t >= a) & (t < b)])) * 1e3 for a, b in windows]
    m = t > 14
    xx = x[m] - x[m].mean()
    spec = np.abs(np.fft.rfft(xx * np.hanning(len(xx))))
    return dict(bf=bf, cut=cut, mult=mult, windows_s=windows, top_mvpp=pp, dominant_hz=float(np.fft.rfftfreq(len(xx), t[1] - t[0])[int(np.argmax(spec))]), vca_mvpp=float(np.ptp(d['n623'][m])) * 1e3)


def slow():
    jobs = [(400, 1.0, 1), (600, 1.0, 1), (800, 1.0, 1), (800, 0.5, 1), (400, 0.5, 2), (400, 1.0, 2)]
    with ProcessPoolExecutor(6) as ex:
        rows = list(ex.map(slow_case, jobs))
    (OUT / 'slow_growth.json').write_text(json.dumps(rows, indent=1))
    for r in rows:
        print(f"hFE {r['bf']} cut {r['cut']} fb x{r['mult']}: Q19 emitter mVpp {[round(x, 2) for x in r['top_mvpp']]}, dominant {r['dominant_hz']:.1f} Hz, VCA input {r['vca_mvpp']:.3f} mVpp")


LEAK_CASES = {
    'matched': {},
    'Q12 off by 1 mV': {'Q12A': 1},
    'Q12 off by 3 mV': {'Q12A': 3},
    'Q12 off by 10 mV': {'Q12A': 10},
    'Q12 off by 30 mV': {'Q12A': 30},
    'Q22 off by 10 mV': {'Q22A': 10},
    'Q22 off by 30 mV': {'Q22A': 30},
    'Q21 off by 10 mV': {'Q21A': 10},
    'ladder left side +10 mV each': {'Q13': 10, 'Q14': 10, 'Q16': 10},
}
LEAK_PATTERN = [1, 0, 0, 1, 1, 0, 1, 0]


def leak_case(args):
    """How much of the envelope and accent reaches the VCA input with no audio going in, and how loud
    the same notes are with the saw. The MEG sweeps the ladder current, which a balanced ladder rejects."""
    name, audio = args
    scale = {k: math.exp(mv * 1e-3 / 0.02585) for k, mv in LEAK_CASES[name].items()}
    o = dict(cut=0.35, res=0.85, env=0.6, decay=0.35, acc=0.8, tm3=TM3, is_scale=scale)
    step = 0.125
    notes = [(0.25 + i * step, 0.25 + i * step + step / 2, 65.41, bool(a)) for i, a in enumerate(LEAK_PATTERN)]
    src = None if audio else ['Vsrc n126 0 DC 8.5']
    d = V.tran_run(o, notes, 1.4, source=src, tstep=25e-6, tmax=10e-6, save=('n623', 'n144'))
    t, x = d['t'], d['n623']
    # The VCA opens about 4 ms after the gate (Devil Fish manual), so also measure only what it would pass.
    gated = np.zeros_like(t, dtype=bool)
    for t_on, t_off, _, _ in notes:
        gated |= (t >= t_on + 0.004) & (t < t_off + 0.016)
    late = t > 0.3
    return dict(name=name, audio=audio, vca_mvpp=float(np.ptp(x[late])) * 1e3, vca_gated_mvpp=max(float(np.ptp(x[(t >= n[0] + 0.004) & (t < n[1] + 0.016)])) for n in notes[1:]) * 1e3,
                top_mvpp=float(np.ptp(d['n144'][late])) * 1e3)


def leak():
    jobs = [(n, False) for n in LEAK_CASES] + [(n, True) for n in ('matched', 'Q12 off by 10 mV', 'Q22 off by 10 mV')]
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(leak_case, jobs))
    (OUT / 'envelope_leak.json').write_text(json.dumps(rows, indent=1))
    ref = next(r for r in rows if r['audio'] and r['name'] == 'matched')['vca_gated_mvpp']
    for r in rows:
        print(f"{r['name']:30s} {'saw' if r['audio'] else 'no audio':8s} VCA input {r['vca_mvpp']:8.4f} mVpp, while the VCA is open {r['vca_gated_mvpp']:8.4f} mVpp ({20 * math.log10(r['vca_gated_mvpp'] / ref):6.1f} dB re the notes)")


if __name__ == '__main__':
    which = sys.argv[1:] or ['kicks', 'wave', 'env', 'slow', 'leak']
    if 'kicks' in which:
        kicks()
    if 'wave' in which:
        waveforms()
    if 'env' in which:
        envelopes()
    if 'slow' in which:
        slow()
    if 'leak' in which:
        leak()
