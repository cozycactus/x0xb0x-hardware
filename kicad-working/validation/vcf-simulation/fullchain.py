#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""The whole analog section in one ngspice deck: CV DAC, slide, VCO, square shaper, VCF, both
envelopes, accent, VCA and mixer, driven by the stock firmware's gate, slide, accent and note timing.
The line output (N$7, J7 pin 1, the MIX OUT jack) is what gets written to the WAV.

Parts and nets come from fullchain-parts.json, exported from the KiCad schematic. Behavioural, because
no SPICE model or usable datasheet was available: IC11 (AN6562 dual op-amp) and IC15 (BA6110, treated as
a plain bipolar OTA with a unity buffer). IC9 and IC3 are ideal logic sources. Rails are ideal.
Usage: fullchain.py parts | tune | check | render [name ...]"""
import json
import math
import sys
import wave
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vcfdeck as V

PARTS = HERE / 'fullchain-parts.json'
RES = HERE / 'results'
TUNING = HERE / 'fullchain-tuning.json'
TM3 = json.loads((HERE / 'calibration.json').read_text())['tm3']
if PARTS.exists():
    V.COMP.update(json.loads(PARTS.read_text())['components'])
V.DUAL.add('Q26')

CV_VCO = ('C10 C11 C33 C34 C35 D25 D30 D31 Q8 Q24 Q25 Q26 Q27 Q29 Q30 R34 R35 R36 R45 R59 R60 '
          'R74 R75 R76 R77 R78 R79 R80 R81 R82 R83 R84 R85 R86 R87 R88 R89 R90 R91 R92 R93 '
          'R100A0 R100B0 R101 R102 R103 R104 R105 R106 R107 R118').split()
VEG_VCA = 'Q36 R145 D34 R137 D35 D36 R133 R131 Q31 R123 C42 R132 Q32 R130 R134 C41 Q1 Q2 Q3 Q4 D27 R120 R127 R128 R129 C40 R162 C38'.split()
MIXER = 'C52 C53 C56 C58 C59 Q33 Q34 R136 R153 R154 R155 R156 R157 R158 R160 R161 R165'.split()
CONTROLS = 'TM4 TM5 VR2 VR8 Q28'.split()
ALL_NEW = CV_VCO + VEG_VCA + MIXER + CONTROLS
THERM = {'R100A0': 1000.0, 'R100B0': 1000.0}  # The kit's 1K PTCs, at 25 C

COMMON_MODELS = """
.model J2SK30O NJF (VTO=-1.0 BETA=1m LAMBDA=0.01)
.model DIC D (IS=1e-14 N=1)
* Q27 is one half of the core's latch, which only lets go when Q27 runs out of drive in saturation. No datasheet
* gives its gain there. These values are fitted so the core works up to the top note, as the real one does.
.model P733Q27 PNP (IS=1.2e-14 BF=150 NF=1 VAF=60 IKF=0.1 ISE=3e-15 NE=1.5 BR=1 RB=60 RC=1 RE=0.4 CJE=10p CJC=4.5p TF=1n TR=60n XTB=1.5)
.subckt OPA6562 p n o vcc
G1 0 a p n 1m
R1 a 0 100meg
C1 a 0 53p
B1 b 0 V = min(max(v(a), 0.7), v(vcc)-1.0)
R2 b o 50
.ends
"""

BIT_NETS = ['N$92', 'N$91', 'N$236', 'N$93', 'N$231', 'N$77']  # IC9 outputs for NOTE0..NOTE5 (D0, D5, D1, D4, D2, D3)
C2_CODE = 0x17                                                 # Firmware C2; the DAC gives 2.0 V, the kit's 65.4 Hz note


def vco_block(tm4, tm5, tune=0.5):
    """The CV buffer, exponential converter and core, with values from the netlist."""
    t4, t5, v2 = V.pins('TM4'), V.pins('TM5'), V.pins('VR2')
    q28 = V.pins('Q28')
    L = [COMMON_MODELS]
    L += [x.replace(' P733 ', ' P733Q27 ') if x.startswith('QQ27 ') else x for x in V.part_lines(CV_VCO, THERM, {})]
    L += V.pot('TM4', t4['A'], t4['S'], t4['E'], 50e3, tm4)
    L += V.pot('TM5', t5['A'], t5['S'], t5['E'], 5e3, tm5)
    L += V.pot('VR2', v2['A'], v2['S'], v2['E'], 50e3, tune)
    L += [f'JQ28 {q28["D"]} {q28["G"]} {q28["S"]} J2SK30O', 'XIC11A vref n98 n97 vcc OPA6562', 'XIC11B n112 n85 n625 vcc OPA6562',
          'SWslideon n112 n82 n83 0 SW4066', 'SWslideoff n625 n82 n88 0 SW4066',
          # SPICE starts the core exactly on its unstable DC point and has no noise to leave it. One kick does.
          'Ikick n113 0 PULSE(0 1m 2m 1u 1u 100u 100)']
    return L


def pwl(points):
    return 'PWL(' + ' '.join(f'{a:.8g} {b:.6g}' for a, b in points) + ')'


def schedule(steps, step_time, t0=0.05):
    """The firmware's note_on and note_off sequence (main.c, synth.c).
    note_on writes the note, the previous step's slide flag and this step's active-low accent; after the
    latch the gate rises unless this is a rest. Half a step later note_off raises SLIDE if this step slides,
    and otherwise drops the gate. Rests neither latch the DAC nor strike the gate."""
    edge = 1e-6
    bits = [[(0.0, 0.0)] for _ in range(6)]
    gate = [(0.0, 0.0)]
    slide = [(0.0, 0.0)]
    accent = [(0.0, 5.0)]
    state = dict(code=0, gate=0.0, slide=0.0, accent=5.0)

    def move(track, t, old, new):
        if old != new:
            track += [(t, old), (t + edge, new)]

    prev_slide = False
    for i, (code, acc, sl) in enumerate(steps):
        t = t0 + i * step_time
        new_slide = 5.0 if prev_slide else 0.0
        move(slide, t, state['slide'], new_slide)
        state['slide'] = new_slide
        new_acc = 0.0 if acc else 5.0
        move(accent, t, state['accent'], new_acc)
        state['accent'] = new_acc
        if code is not None:
            for b in range(6):
                old = 5.333 if state['code'] >> b & 1 else 0.0
                new = 5.333 if code >> b & 1 else 0.0
                move(bits[b], t + 2e-6, old, new)
            state['code'] = code
            move(gate, t + 12e-6, state['gate'], 5.0)
            state['gate'] = 5.0
        t_half = t + step_time / 2
        if code is not None and sl:
            move(slide, t_half, state['slide'], 5.0)
            state['slide'] = 5.0
        else:
            move(gate, t_half, state['gate'], 0.0)
            state['gate'] = 0.0
        prev_slide = bool(sl) and code is not None
    return bits, gate, slide, accent


def drive_lines(bits, gate, slide, accent):
    L = [f'VQ{b} {V.node(BIT_NETS[b])} 0 {pwl(bits[b])}' for b in range(6)]
    L += [f'Vgate ngate 0 {pwl(gate)}', f'Vaccent naccent 0 {pwl(accent)}', f'Vslide nslide 0 {pwl(slide)}']
    return L


def transient(lines, save, t_end, tstep, tmax, temp=25.0, reltol=1e-3):
    vecs = ' '.join(s if s.startswith('i(') else f'v({s})' for s in save)
    deck = lines + [f'.options temp={temp} tnom=25 reltol={reltol} abstol=1e-11 vntol=1e-6 method=gear itl4=60 itl1=500 gmin=1e-11', f'.tran {tstep} {t_end} 0 {tmax}',
                    '.control', 'set wr_singlescale', 'set wr_vecnames', 'run', 'linearize', f'wrdata @DIR@/tran.txt {vecs}', '.endc']
    data, log = V.run(deck, ['tran.txt'])
    a = data['tran.txt']
    out = dict(t=a[:, 0], log=log)
    for k, name in enumerate(save):
        out[name] = a[:, k + 1]
    return out


# ---- VCO on its own: tuning as the kit describes ----
def vco_frequency(tm4, tm5, code, tune=0.5, seconds=0.2):
    bits, gate, slide, accent = schedule([(code, 0, 0)], 10.0, t0=1e-4)
    L = ['* x0xb0x VCO alone', 'Vcc vcc 0 12', 'Vref vref 0 5.333', V.MODELS.format(**V.DEFAULTS)]
    L += vco_block(tm4, tm5, tune)
    L += [f'VQ{b} {V.node(BIT_NETS[b])} 0 DC {5.333 if code >> b & 1 else 0.0}' for b in range(6)]
    L += ['Vslide nslide 0 DC 0']
    d = transient(L, ('n113', 'n108', 'n303', 'n625', 'n97'), seconds, 5e-6, 3e-6)
    t, x = d['t'], d['n113']
    mid = 0.5 * (x[t > 0.02].max() + x[t > 0.02].min())
    up = np.where((x[:-1] < mid) & (x[1:] >= mid) & (t[:-1] > 0.02))[0]
    per = np.diff(t[up])
    return dict(hz=1.0 / float(np.mean(per)) if len(per) else 0.0, cycles=len(per), cv=float(d['n625'][-1]), v97=float(d['n97'][-1]), n113=(float(x[t > 0.02].min()), float(x[t > 0.02].max())),
                saw=(float(d['n108'][t > 0.02].min()), float(d['n108'][t > 0.02].max()), float(d['n108'][t > 0.02].mean())), square=(float(d['n303'][t > 0.02].min()), float(d['n303'][t > 0.02].max()), float(d['n303'][t > 0.02].mean())))


def tune_vco():
    """TM4 sets the pitch and TM5 the volts per octave. Both are trims on the real board."""
    tm4, tm5 = 0.5, 0.5
    for i in range(8):
        lo = vco_frequency(tm4, tm5, C2_CODE, seconds=0.3)
        hi = vco_frequency(tm4, tm5, C2_CODE + 24, seconds=0.12)
        oct_ = math.log2(hi['hz'] / lo['hz'])
        print(f'pass {i}: TM4 {tm4:.4f} TM5 {tm5:.4f}: {lo["hz"]:.3f} Hz at {lo["cv"]:.3f} V, {hi["hz"]:.3f} Hz at {hi["cv"]:.3f} V, {oct_:.4f} octaves')
        series = 27e3 + 5e3 * tm5
        tm5 = min(max((series * oct_ / 2.0 - 27e3) / 5e3, 0.0), 1.0)
        # f is proportional to the converter's reference current through R103 and R102
        iref = (12 - 5.333) / 220e3 + (12 - tm4 * (12 - 5.333) - 5.333) / 100e3
        want = iref * 65.41 / lo['hz']
        v114 = 5.333 + (want - (12 - 5.333) / 220e3) * 100e3
        tm4 = min(max((12 - v114) / (12 - 5.333), 0.0), 1.0)
    result = dict(tm4=tm4, tm5=tm5)
    TUNING.write_text(json.dumps(result, indent=1) + '\n')
    return result


# ---- The whole chain ----
def full_deck(tm4, tm5, knobs, steps, step_time, wave_name):
    o = {**dict(tm3=TM3, volume=0.75), **knobs}
    bits, gate, slide, accent = schedule(steps, step_time)
    extra = vco_block(tm4, tm5) + drive_lines(bits, gate, slide, accent)
    extra += V.part_lines(VEG_VCA + MIXER, {}, {})
    v8 = V.pins('VR8')
    extra += V.pot('VR8', v8['A'], v8['S'], v8['E'], 50e3, V.taper_a(o['volume']))
    extra += ['Rs1 n108 n126 1' if wave_name == 'saw' else 'Rs1 n303 n126 1']
    extra += ['Rjackmix n20 0 1']  # MIX IN: the jack's normal contact grounds the tip with no plug in
    # IC15 as a bipolar OTA: output current Iabc*tanh(Vd/(2*VT)), control pin two diodes above ground, unity buffer
    extra += ['Vabc n29 nabc1 0', 'Dabc1 nabc1 nabc2 DIC', 'Dabc2 nabc2 0 DIC', 'BOTA 0 n28 I = i(Vabc)*tanh(v(n623,n24)/0.0517)', 'Ebuf nbufo 0 n28 0 1', 'Rbuf nbufo n48 100']
    opts = {k: v for k, v in o.items() if k != 'volume'}
    L, _ = V.circuit({**opts, 'meg': None, 'extra': extra})
    return L


def default_steps(notes=None):
    return [(C2_CODE + st if st is not None else None, ac, sl) for st, ac, sl in notes]


# Same pattern as the earlier demonstration: (semitones above the kit's C1, accent, slide)
PATTERN = [(0, 1, 0), (0, 0, 0), (12, 0, 0), (0, 0, 1), (3, 1, 0), (0, 0, 0), (10, 0, 1), (12, 1, 0),
           (0, 0, 0), (0, 1, 0), (7, 0, 0), (0, 0, 0), (3, 0, 1), (5, 1, 1), (7, 1, 0), (0, 0, 0)]
STEP = 0.125
RENDERS = {
    'full-saw': ('saw', dict(cut=0.35, res=0.85, env=0.6, decay=0.35, acc=0.8)),
    'full-square': ('square', dict(cut=0.35, res=0.85, env=0.6, decay=0.35, acc=0.8)),
    'full-saw-open': ('saw', dict(cut=0.6, res=0.6, env=0.85, decay=0.5, acc=1.0)),
}


def lowpass_decimate(x, factor=2):
    n = 201
    h = np.sinc(np.arange(-(n // 2), n // 2 + 1) * (0.9 / factor)) * (0.9 / factor) * np.hanning(n)
    return np.convolve(x, h / h.sum(), mode='same')[::factor]


def render(name):
    tune = json.loads(TUNING.read_text())
    wave_name, knobs = RENDERS[name]
    steps = default_steps(PATTERN * 2)
    t_end = 0.05 + len(steps) * STEP + 0.35
    L = full_deck(tune['tm4'], tune['tm5'], knobs, steps, STEP, wave_name)
    d = transient(L, ('n7', 'n48', 'n623', 'n625', 'n53', 'n127', 'n146', 'i(vabc)'), t_end, 1 / 96000, 8e-6)
    t = d['t']
    out = d['n7'] - np.mean(d['n7'][t > 0.05])
    audio = lowpass_decimate(out)
    sr = 48000
    fade = int(0.003 * sr)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    peak = float(np.max(np.abs(audio)))
    path = RES / f'demo-{name}.wav'
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((0.89 * audio / peak * 32767).astype('<i2').tobytes())
    ua = 1e6 * (d['n127'] - d['n146']) / 2200
    return dict(name=name, file=path.name, seconds=len(audio) / sr, line_out_peak_v=peak, line_out_pp_v=float(np.ptp(out[t > 0.1])), ladder_ua=[float(ua.min()), float(ua.max())], cv_v=[float(d['n625'][t > 0.06].min()), float(d['n625'][t > 0.06].max())],
                iabc_ua_max=float(d['i(vabc)'].max() * 1e6), meg_max_v=float(d['n53'].max()), knobs=knobs, wave=wave_name)


def check():
    """Stage checks against what the kit pages and the Devil Fish manual state."""
    tune = json.loads(TUNING.read_text())
    out = {}
    for label, code in (('C1 at 2 V', C2_CODE), ('C2 at 3 V', C2_CODE + 12), ('C3 at 4 V', C2_CODE + 24), ('C1 at 2 V, 1 semitone', C2_CODE + 1)):
        r = vco_frequency(tune['tm4'], tune['tm5'], code, seconds=0.3 if code < C2_CODE + 12 else 0.15)
        out[label] = r
        print(f"{label:24s} CV {r['cv']:.3f} V  {r['hz']:8.3f} Hz, {r['cycles']} cycles; C33 {r['n113'][0]:.2f} to {r['n113'][1]:.2f} V; saw {r['saw'][0]:.2f} to {r['saw'][1]:.2f} V mean {r['saw'][2]:.2f}; square {r['square'][0]:.2f} to {r['square'][1]:.2f} V mean {r['square'][2]:.2f}")
    # One gated note, then two tied notes, with the whole chain: envelope timing and slide
    steps = [(C2_CODE, 0, 0), (C2_CODE, 0, 1), (C2_CODE + 12, 0, 0), (C2_CODE, 0, 0)]
    knobs = dict(cut=0.5, res=0.5, env=0.5, decay=0.5, acc=0.5)
    L = full_deck(tune['tm4'], tune['tm5'], knobs, steps, 0.25, 'saw')
    d = transient(L, ('n7', 'n39', 'n45', 'n68', 'n625', 'n82', 'n48', 'n28', 'n12', 'n5', 'n53', 'i(vabc)', 'ngate', 'nslide'), 1.25, 1 / 48000, 8e-6)
    t = d['t']
    print('Gate-on levels: N$39 max', round(float(d['n39'].max()), 2), 'V (kit: 12 V while gated); N$45 max', round(float(d['n45'].max()), 2), 'V (kit: brief pulse to 12 V)')
    t_on = 0.05 + 12e-6
    t_off = 0.05 + 0.125
    i = d['i(vabc)'] * 1e6
    start = next(float(t[k] - t_on) * 1e3 for k in range(len(t)) if t[k] > t_on and i[k] > 0.5 * i[(t > t_on) & (t < t_off)].max())
    stops = i[(t > t_off) & (t < t_off + 0.08)]
    tt = t[(t > t_off) & (t < t_off + 0.08)]
    level = float(np.interp(t_off, t, i))
    half = next((float(tt[k] - t_off) * 1e3 for k in range(len(tt)) if stops[k] < 0.5 * level), None)
    gone = next((float(tt[k] - t_off) * 1e3 for k in range(len(tt)) if stops[k] < 0.02 * level), None)
    print(f'VCA control current: peak {i.max():.1f} uA; half level {start:.2f} ms after gate on (manual: 1 to 5 ms, typically 4); after gate off, half at {half} ms and gone at {gone} ms (manual: about 16 ms)')
    a = (t > 0.06) & (t < t_off)
    fit = np.polyfit(t[a], np.log(np.maximum(i[a], 1e-3)), 1)[0]
    print(f'Decay of the VCA current during the first gate: time constant {-1 / fit:.2f} s')
    # Slide: step 3 glides from code+0 to code+12
    t_s = 0.05 + 2 * 0.25
    m = (t > t_s) & (t < t_s + 0.2)
    cv = d['n625']
    v0, v1 = float(np.interp(t_s - 1e-3, t, cv)), float(cv[m][-1])
    tau = next(float(t[m][k] - t_s) * 1e3 for k in range(int(m.sum())) if cv[m][k] > v0 + (v1 - v0) * (1 - 1 / math.e))
    print(f'Slide: CV {v0:.3f} V to {v1:.3f} V, time constant {tau:.1f} ms; R-2R and C35 predict 22 ms')
    print('Line output: N$48 p-p', round(float(np.ptp(d['n48'][t > 0.06])), 3), 'V; N$7 p-p', round(float(np.ptp(d['n7'][t > 0.06])), 3), 'V; mixer bias N$12', round(float(np.median(d['n12'])), 3), 'V, N$5', round(float(np.median(d['n5'])), 3), 'V; OTA output bias N$28', round(float(np.median(d['n28'])), 3), 'V')
    out['chain'] = dict(vca_half_on_ms=start, vca_half_off_ms=half, vca_gone_ms=gone, vca_peak_ua=float(i.max()), veg_time_constant_s=float(-1 / fit), slide_tau_ms=tau, n39_max=float(d['n39'].max()), n45_max=float(d['n45'].max()), line_pp=float(np.ptp(d['n7'][t > 0.06])))
    (RES / 'fullchain_check.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if what == 'parts':
        import extract_vcf
        comps = extract_vcf.read_parts(sorted(set(ALL_NEW + V.ALL_PARTS)))
        PARTS.write_text(json.dumps(dict(source='kicad-working/mainboard/mainboard.kicad_sch', components=comps), indent=1) + '\n')
        print(len(comps), 'parts')
    elif what == 'tune':
        print(tune_vco())
    elif what == 'check':
        check()
    else:
        names = sys.argv[2:] or list(RENDERS)
        with ProcessPoolExecutor(3) as ex:
            rows = list(ex.map(render, names))
        for r in rows:
            print(r)
        (RES / 'fullchain_render.json').write_text(json.dumps(rows, indent=1))
