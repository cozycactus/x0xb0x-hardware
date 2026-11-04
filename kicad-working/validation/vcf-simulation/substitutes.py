#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Replacement duals for Q12, Q21, Q22 (VCF) and Q26 (VCO): model values only. Writes results/substitutes.json
and results/substitutes_vco.json. Usage: substitutes.py [vcf | vco]

The stand-ins are fitted to the numbers each datasheet prints, not to a measured part or a vendor SPICE file:
- BCM847: hFE 250 at 10 uA, 200/290/450 at 2 mA, Vbe 660 mV at 2 mA, Cc 1.5 pF, Ce 11 pF, fT 250 MHz.
  (Nexperia/NXP BCM847BV_BS_DS Rev. 06.) Matching is 0.9 in hFE and 2 mV in Vbe, stated at 2 mA only.
- BC847C (onsemi BC847CDW1, SOT-363, no matching spec): hFE 270 at 10 uA, 420/520/800 at 2 mA, Vbe 660 mV at 2 mA,
  Cob 4.5 pF max, of which 2 pF is assumed typical. (onsemi BC846BDW1/D Rev. 16.)
- SSM2212 SOIC: hFE 580 from 1 uA to 1 mA (Fig. 6), 300 min at 1 mA, 200 min at 10 uA, Vbe from Fig. 8,
  Ccb from Fig. 13, Ccc from Fig. 14, rbb' 28 ohm, fT 200 MHz, protection diodes across each base-emitter junction.
  (Analog Devices SSM2212 Rev. C.) CJE is not printed and is an assumption.
VAF, TR, IKF and the BR of both are generic, like the other stand-ins in vcfdeck.py."""
import json
import math
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import vcfdeck as V

OUT = Path(__file__).parent / 'results'
TM3 = json.loads((Path(__file__).parent / 'calibration.json').read_text())['tm3']
ORIGINAL_MODELS = V.MODELS


def bcm(bf=300):
    return f'NPN (IS=1.6e-14 BF={bf} NF=1 VAF=100 IKF=0.1 ISE=9.1e-15 NE=1.5 BR=5 RB=60 RC=1 RE=0.4 CJE=11p CJC=1.5p TF=0.6n TR=60n XTB=1.5)'


def ssm(bf=590, ise=1.7e-15, cjc=30):
    return f'NPN (IS=4.5e-13 BF={bf} NF=1 VAF=100 IKF=0.1 ISE={ise} NE=1.5 BR=5 RB=28 RC=1 RE=0.3 CJE=100p CJC={cjc}p VJC=0.4 MJC=0.25 TF=0.5n TR=60n XTB=1.5)'


def bc847c(bf=643):
    return f'NPN (IS=1.6e-14 BF={bf} NF=1 VAF=100 IKF=0.1 ISE=2.94e-14 NE=1.5 BR=5 RB=60 RC=1 RE=0.4 CJE=11p CJC=2p TF=0.6n TR=60n XTB=1.5)'


# hFE at 2 mA of 200 and 450 with the same low-current term: BF 205 and 474. BC847C at 420 and 800: BF 497 and 1133.
# SSM2212 minimum: 300 at 1 mA, 200 at 10 uA.
PARTS = {'bcm': bcm(), 'bcm_low': bcm(205), 'bcm_high': bcm(474), 'bc847c': bc847c(), 'bc847c_low': bc847c(497), 'bc847c_high': bc847c(1133),
         'ssm': ssm(), 'ssm_min': ssm(338, 2.6e-13), 'ssm_2xc': ssm(cjc=60)}
MODEL_NAME = {'Q12': 'N1583Q12', 'Q21': 'N1583', 'Q22': 'N2291', 'Q26': 'N1583'}


def ssm_extras(ref):
    """SSM2212 only: protection diode across each base-emitter junction, and collector-to-collector capacitance."""
    p = V.pins(ref)
    if ref == 'Q22':
        return [f'D{ref}pa {p["E1"]} {p["B"]} DPROT', f'D{ref}pb {p["E"]} {p["B"]} DPROT']
    return [f'D{ref}pa {p["E"]} {p["B"]} DPROT', f'D{ref}pb {p["E"]} {p["B1"]} DPROT', f'C{ref}cc {p["C"]} {p["C1"]} 20p']


def apply(sub):
    """sub: {ref: key in PARTS}. Rewrites the model text used by vcfdeck, which is copied verbatim into the deck."""
    text = ORIGINAL_MODELS
    extras = []
    for ref, key in sub.items():
        name = MODEL_NAME[ref]
        text = re.sub(rf'^\.model {name} .*$', f'.model {name} {PARTS[key]}', text, flags=re.M)
        if key.startswith('ssm'):
            extras += ssm_extras(ref)
    if extras:
        text += '.model DPROT D (IS=1e-14 N=1)\n' + '\n'.join(extras) + '\n'
    V.MODELS = text


def area(mv):
    return math.exp(mv * 1e-3 / 0.02585)


ALL3 = ('Q12', 'Q21', 'Q22')
def every(key):
    return {q: key for q in ALL3}


CASES = {
    'original as modelled (hFE 400)': (dict(), dict()),
    'original, hFE 250 (datasheet minimum)': (dict(), dict(bf1583=250, bfq12=250, bf2291=250)),
    'original, hFE 500 (top of F)': (dict(), dict(bf1583=500, bfq12=500, bf2291=500)),
    'original, hFE 800 (top of G)': (dict(), dict(bf1583=800, bfq12=800, bf2291=800)),
    'BCM847 in Q12 only': (dict(Q12='bcm'), dict()),
    'BCM847 in Q21 only': (dict(Q21='bcm'), dict()),
    'BCM847 in Q22 only': (dict(Q22='bcm'), dict()),
    'BCM847 in all three, typical': (every('bcm'), dict()),
    'BCM847 in all three, hFE 200 at 2 mA': (every('bcm_low'), dict()),
    'BCM847 in all three, hFE 450 at 2 mA': (every('bcm_high'), dict()),
    'BCM847, Q12 off by 2 mV': (every('bcm'), dict(is_scale={'Q12A': area(2)})),
    'BCM847, Q12 off by 10 mV': (every('bcm'), dict(is_scale={'Q12A': area(10)})),
    'BCM847, Q21 off by 2 mV': (every('bcm'), dict(is_scale={'Q21A': area(2)})),
    'BCM847, Q21 off by 10 mV': (every('bcm'), dict(is_scale={'Q21A': area(10)})),
    'BCM847, Q21 hFE ratio 0.9': (every('bcm'), dict(half_bf={'Q21B': 270})),
    'BCM847, Q21 hFE ratio 0.8': (every('bcm'), dict(half_bf={'Q21B': 240})),
    'BCM847, Q12 hFE ratio 0.9': (every('bcm'), dict(half_bf={'Q12B': 270})),
    'BC847C in Q21, BCM847 in Q12 and Q22': (dict(Q12='bcm', Q21='bc847c', Q22='bcm'), dict()),
    'BC847C in Q21, hFE 420 at 2 mA': (dict(Q12='bcm', Q21='bc847c_low', Q22='bcm'), dict()),
    'BC847C in Q21, hFE 800 at 2 mA': (dict(Q12='bcm', Q21='bc847c_high', Q22='bcm'), dict()),
    'BC847C in Q21, hFE ratio 0.9': (dict(Q12='bcm', Q21='bc847c', Q22='bcm'), dict(half_bf={'Q21B': 579})),
    'BC847C in Q21, hFE ratio 0.8': (dict(Q12='bcm', Q21='bc847c', Q22='bcm'), dict(half_bf={'Q21B': 514})),
    'BC847C in Q21, hFE ratio 0.7': (dict(Q12='bcm', Q21='bc847c', Q22='bcm'), dict(half_bf={'Q21B': 450})),
    'BC847C in Q21, off by 10 mV': (dict(Q12='bcm', Q21='bc847c', Q22='bcm'), dict(is_scale={'Q21A': area(10)})),
    'BC847C in Q21, off by 30 mV': (dict(Q12='bcm', Q21='bc847c', Q22='bcm'), dict(is_scale={'Q21A': area(30)})),
    'SSM2212 in Q12 only': (dict(Q12='ssm'), dict()),
    'SSM2212 in Q21 only': (dict(Q21='ssm'), dict()),
    'SSM2212 in Q22 only': (dict(Q22='ssm'), dict()),
    'SSM2212 in all three, typical': (every('ssm'), dict()),
    'SSM2212 in all three, datasheet minimum hFE': (every('ssm_min'), dict()),
    'SSM2212 in all three, Ccb doubled': (every('ssm_2xc'), dict()),
    'SSM2212 in Q21, BCM847 in Q12 and Q22': (dict(Q12='bcm', Q21='ssm', Q22='bcm'), dict()),
}
CUTS = dict(low=0.0, mid=0.5, high=1.0)
STEP = 0.125
PATTERN = [1, 0, 0, 1, 1, 0, 1, 0]
NOTES = [(0.25 + i * STEP, 0.25 + i * STEP + STEP / 2, 65.41, bool(a)) for i, a in enumerate(PATTERN)]
# Every junction the replacement pair has, for the worst reverse base-emitter voltage in a pattern
PAIR_NODES = dict(Q12=[('n127', 'n124'), ('n127', 'n60')], Q21=[('n139', 'n138'), ('n139', 'n141')], Q22=[('n143', 'n115'), ('n120', 'n115')])


def small_signal(name):
    sub, extra = CASES[name]
    apply(sub)
    out = {}
    for label, cut in CUTS.items():
        o = {**dict(cut=cut, res=1.0, env=0.0, tm3=TM3), **extra}
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
        out[label] = dict(fpeak=float(fp), q=float(fp / (b['f'][hi] - b['f'][lo])), margin_db=float(V.oscillation_margin(f, T)[1]), ladder_ua=op['ladder_ua'],
                          q21_collector_v=op.get('n140'), q21_emitter_v=op.get('n139'), q21_base_v=op.get('n138'), q12_base_v=op.get('n124'))
    return out


def noise(name):
    """White noise only: junction shot noise and resistor thermal noise. 1/f is not modelled, since neither
    the original's datasheet nor BCM847's gives it. Output at the VCF tap (N$623), 20 Hz to 20 kHz, in uV rms."""
    sub, extra = CASES[name]
    apply(sub)
    out = {}
    for label, cut in CUTS.items():
        for res in (0.0, 0.85):
            L, oo = V.circuit({**dict(cut=cut, res=res, env=0.0, tm3=TM3), **extra})
            L += ['Vsrc n126 0 DC 8.5 AC 1', f'.options temp={oo["temp"]} tnom=25', '.control', 'noise v(n623) Vsrc dec 40 20 20000', 'setplot noise2', 'print onoise_total', '.endc']
            _, log = V.run(L, [])
            m = re.search(r'onoise_total\s*=\s*(\S+)', log)
            out[f'{label}_res{int(res * 100)}'] = float(m[1]) * 1e6 if m else None
    return out


def time_domain(name):
    sub, extra = CASES[name]
    apply(sub)
    saves = ('n623', 'n124', 'n60', 'n127', 'n138', 'n141', 'n139', 'n143', 'n120', 'n115')
    o = {**dict(cut=0.35, res=0.85, env=0.6, decay=0.35, acc=0.8, tm3=TM3), **extra}
    leak = V.tran_run(o, NOTES, 1.4, source=['Vsrc n126 0 DC 8.5'], tstep=25e-6, tmax=10e-6, save=('n623',))
    t, x = leak['t'], leak['n623']
    notes = V.tran_run(o, NOTES, 1.4, tstep=25e-6, tmax=10e-6, save=saves)
    open_vca = lambda y: max(float(np.ptp(y[(t >= n[0] + 0.004) & (t < n[1] + 0.016)])) for n in NOTES[1:]) * 1e3
    tn = notes['t']
    settled = tn > 0.05
    reverse = {}
    for ref, pairs in PAIR_NODES.items():
        reverse[ref] = max(float((notes[e][settled] - notes[b][settled]).max()) for e, b in pairs)
    return dict(leak_mvpp=float(np.ptp(x[t > 0.3])) * 1e3, leak_open_mvpp=open_vca(x), notes_open_mvpp=open_vca(notes['n623']), worst_reverse_vbe=reverse)


def case(name):
    return dict(name=name, small_signal=small_signal(name), noise=noise(name), time_domain=time_domain(name))


def run_vcf():
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(case, CASES))
    (OUT / 'substitutes.json').write_text(json.dumps(rows, indent=1) + '\n')
    base = rows[0]
    print(f"{'case':46s} {'d oct at 0/50/100 %':>20s} {'Q at 0/50/100 %':>18s} {'margin dB':>20s} {'leak dB':>8s} {'noise uV (0 %, 50 %, res .85)':>30s}  rev Vbe Q12 Q21 Q22")
    ref = base['time_domain']['notes_open_mvpp']
    for r in rows:
        s, b, n, td = r['small_signal'], base['small_signal'], r['noise'], r['time_domain']
        print(f"{r['name']:46s} " + ' '.join(f"{math.log2(s[c]['fpeak'] / b[c]['fpeak']):6.2f}" for c in CUTS) + ' ' + ' '.join(f"{s[c]['q']:5.1f}" for c in CUTS) + ' ' + ' '.join(f"{s[c]['margin_db']:6.2f}" for c in CUTS)
              + f" {20 * math.log10(td['leak_open_mvpp'] / ref):8.1f}   {n['low_res85']:7.1f} {n['mid_res85']:7.1f} {n['high_res85']:7.1f}     "
              + ' '.join(f"{td['worst_reverse_vbe'][q]:5.2f}" for q in ALL3))


# ---- Q26, the VCO's exponential converter ----
VCO_CASES = {
    'original as modelled (hFE 400)': (None, 0.0),
    'BCM847 typical': ('bcm', 0.0),
    'BCM847 hFE 200 at 2 mA': ('bcm_low', 0.0),
    'BCM847 hFE 450 at 2 mA': ('bcm_high', 0.0),
    'BCM847 off by +2 mV': ('bcm', 2.0),
    'BCM847 off by -2 mV': ('bcm', -2.0),
    'BCM847 off by +10 mV': ('bcm', 10.0),
    'BCM847 off by -10 mV': ('bcm', -10.0),
    'BC847C typical': ('bc847c', 0.0),
    'SSM2212 typical': ('ssm', 0.0),
}
NOTE_CODES = (11, 23, 35, 47, 59)  # 32.7 to 523 Hz: firmware C2 = code 23


def vco_case(name):
    import fullchain as F
    key, mv = VCO_CASES[name]
    apply({'Q26': key} if key else {})
    base_block = F.vco_block

    def block(*a, **k):
        L = base_block(*a, **k)
        return [x.rsplit(' ', 1)[0] + f' {area(mv):.5g}' if x.startswith('QQ26A ') else x for x in L]
    F.vco_block = block
    tm = json.loads(F.TUNING.read_text())
    before = F.vco_frequency(tm['tm4'], tm['tm5'], F.C2_CODE, seconds=0.3)['hz']
    tm4, tm5 = tm['tm4'], tm['tm5']
    for _ in range(4):  # the same trim procedure as fullchain.tune_vco, without writing its tuning file
        lo = F.vco_frequency(tm4, tm5, F.C2_CODE, seconds=0.3)
        hi = F.vco_frequency(tm4, tm5, F.C2_CODE + 24, seconds=0.12)
        oct_ = math.log2(hi['hz'] / lo['hz'])
        series = 27e3 + 5e3 * tm5
        tm5 = min(max((series * oct_ / 2.0 - 27e3) / 5e3, 0.0), 1.0)
        iref = (12 - 5.333) / 220e3 + (12 - tm4 * (12 - 5.333) - 5.333) / 100e3
        v114 = 5.333 + (iref * 65.41 / lo['hz'] - (12 - 5.333) / 220e3) * 100e3
        tm4 = min(max((12 - v114) / (12 - 5.333), 0.0), 1.0)
    cents = {}
    for code in NOTE_CODES:
        seconds = 0.6 if code < F.C2_CODE else 0.3 if code == F.C2_CODE else 0.15
        r = F.vco_frequency(tm4, tm5, code, seconds=seconds)
        want = 65.41 * 2 ** ((code - F.C2_CODE) / 12)
        cents[code] = 1200 * math.log2(r['hz'] / want) if r['hz'] else None
    # Worst reverse base-emitter voltage at the top note, across the whole saw cycle
    bits, _, _, _ = F.schedule([(59, 0, 0)], 10.0, t0=1e-4)
    L = ['* VCO alone', 'Vcc vcc 0 12', 'Vref vref 0 5.333', V.MODELS.format(**V.DEFAULTS)] + F.vco_block(tm4, tm5, 0.5)
    L += [f'VQ{b} {V.node(F.BIT_NETS[b])} 0 DC {5.333 if 59 >> b & 1 else 0.0}' for b in range(6)] + ['Vslide nslide 0 DC 0']
    d = F.transient(L, ('n101', 'n99', 'vref', 'n113'), 0.08, 5e-6, 3e-6)
    settled = d['t'] > 0.02
    reverse = max(float((d['n101'][settled] - d['n99'][settled]).max()), float((d['n101'][settled] - d['vref'][settled]).max()))
    return dict(name=name, untrimmed_hz=before, tm4=tm4, tm5=tm5, cents=cents, worst_reverse_vbe=reverse, top_note_c33_v=[float(d['n113'][settled].min()), float(d['n113'][settled].max())])


def run_vco():
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(vco_case, VCO_CASES))
    (OUT / 'substitutes_vco.json').write_text(json.dumps(rows, indent=1) + '\n')
    print(f"{'case':34s} {'C2 untrimmed':>12s} {'TM4':>6s} {'TM5':>6s}  cents at 32.7, 65.4, 131, 262, 523 Hz after the trim    rev Vbe")
    for r in rows:
        print(f"{r['name']:34s} {r['untrimmed_hz']:9.2f} Hz {r['tm4']:6.3f} {r['tm5']:6.3f}  " + ' '.join(f"{c:7.1f}" if c is not None else '   stuck' for c in r['cents'].values()) + f"   {r['worst_reverse_vbe']:6.2f}")


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'vcf'
    run_vcf() if what == 'vcf' else run_vco()
