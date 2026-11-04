#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Check the VCF simulation's stored results against the sources they are compared with, and write
docs/vcf-simulation.json. Runs no simulation; needs kicad-cli for the schematic comparison only.
These are checks of a model against published statements. Nothing here is a hardware measurement."""
import json
import math
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import extract_vcf
import vcfdeck as V

ROOT = HERE.parents[2]
RES = HERE / 'results'


def load(name):
    return json.loads((RES / name).read_text())


CHECKS = []


def check(text, passed, **values):
    CHECKS.append(dict(check=text, passed=bool(passed), **values))


# ---- Source of the circuit ----
check('vcf-parts.json matches the current KiCad schematic', extract_vcf.check())
missing = sorted(set(extract_vcf.VCF_BOM) - set(V.ALL_PARTS))
check("Every reference on the expanded BOM's VCF list is in the deck", not missing, references=len(extract_vcf.VCF_BOM), missing=missing)

# ---- Stinchcombe, Analysis of the Moog transistor ladder and derivative filters ----
check('Ladder denominator with equal caps is x^4+7x^3+15x^2+10x+1', V.poly_coeffs(1.0).tolist() == [1, 7, 15, 10, 1])
check('Ladder denominator with the bottom cap halved is 0.5x^4+4x^3+10x^2+8x+1', V.poly_coeffs(0.5).tolist() == [0.5, 4, 10, 8, 1])
k_equal, _ = V.critical_k(1.0)
check('Feedback gain needed to oscillate with equal caps is about 18.4', abs(k_equal - 18.4) < 0.05, k=k_equal)
ladder = load('ladder_check.json')
errors = [abs(20 * math.log10(V.np.interp(1000, r['f'], r['sim_unloaded']) / V.np.interp(1000, r['f'], r['calc']))) for r in ladder]
check('SPICE ladder is within 0.1 dB of the analytic response at 1 kHz', max(errors) < 0.1, max_error_db=max(errors), cases=len(ladder))
check('SPICE and analytic -3 dB corners coincide', all(r['f3_unloaded'] == r['f3_calc'] for r in ladder))
extras = load('extras.json')
slopes = [s[2] for s in extras['slopes']]
check('Roll-off steepens to 24 dB/oct, passing 18 dB/oct on the way', slopes == sorted(slopes, reverse=True) and abs(slopes[-1] + 24) < 0.2 and min(slopes[:-1]) < -18 < max(slopes), slopes_db_per_octave=slopes)
mixed = extras['mixed_diodes']
check('1N4148s at the ladder top add gain, and forcing N to 1 removes it', 4 < mixed['top 1N4148, N=1.752'] < 5.5 and abs(mixed['top diode, N forced to 1']) < 0.3, gains_db=mixed)

# ---- Kit pages ----
cal = json.loads((HERE / 'calibration.json').read_text())
check('TM3 can reach the kit tuning band, 400 to 600 Hz', all(0 < cal[k] < 1 for k in ('tm3', 'tm3_400', 'tm3_600')), tm3_fraction={k: cal[k] for k in ('tm3', 'tm3_400', 'tm3_600')})
mc = load('monte_carlo.json')
check('TM3 reaches 500 Hz in every tolerance sample', all(r['in_range'] for r in mc), samples=len(mc))
squares = [r for r in load('waveforms_summary.json') if r['wave'] == 'square']
check('Simulated square is near the kit figures of about 4 Vpp on 7 V', all(3 < r['source_vpp'] < 5 and 6 < r['source_mean'] < 8 for r in squares), vpp=squares[0]['source_vpp'], mean_v=squares[0]['source_mean'])
down = V.np.array(extras['kit_both down']['top'])
check('With both knobs down the note is almost sinusoidal', 20 * math.log10(down[1] / down[0]) < -12, second_harmonic_db=20 * math.log10(down[1] / down[0]))

# ---- Devil Fish manual and Whittle ----
kicks = load('kicks.json')
stock = [r for r in kicks if r['mult'] == 1 and r['bf'] == 400]
doubled = {r['cut']: r for r in kicks if r['mult'] == 2}
check('Stock filter does not sustain oscillation at any cutoff tested', all(r['pp_tail'] < 1e-3 for r in stock), cases=len(stock))
check('With feedback doubled it sustains at mid and high cutoff and not at the lowest', doubled[0.0]['pp_tail'] < 1e-3 and doubled[0.5]['pp_tail'] > 0.1 and doubled[1.0]['pp_tail'] > 0.1, tail_vpp={str(k): v['pp_tail'] for k, v in doubled.items()})
drive = {r['label']: r for r in load('drive.json')}
saw = [r for r in drive.values() if r['label'].startswith('drive')]
check('Heavy input quenches the resonance and leaves the fundamental', drive['drive x8']['compress_db'] < -10 and -2 < drive['drive x1']['compress_db'] < 0 and all(abs(r['fund_db']) < 1 for r in saw),
      stock_db=drive['drive x1']['compress_db'], x8_db=drive['drive x8']['compress_db'])
env = {r['label']: r for r in load('envelopes_summary.json')}
hi, lo = env['accent all, Res 1.0'], env['accent all, Res 0.0']
check('Accent is a direct pulse with Resonance low and a lag with it high', max(lo['gate_to_peak_ms']) < 2 and min(hi['gate_to_peak_ms']) > 15, low_ms=lo['gate_to_peak_ms'][0], high_ms=hi['gate_to_peak_ms'][-1])
check('Repeated accents stack at full Resonance', hi['note_peaks_ua'][-1] / hi['note_peaks_ua'][0] > 1.3, first_ua=hi['note_peaks_ua'][0], settled_ua=hi['note_peaks_ua'][-1])
check('Env Mod cannot reach zero: at 0 % the note still sweeps', env['Env 0.0']['note_peaks_ua'][-1] / env['Env 0.0']['rest_ua'] > 1.5, rest_ua=env['Env 0.0']['rest_ua'], peak_ua=env['Env 0.0']['note_peaks_ua'][-1])
check('More Env Mod lowers the resting cutoff', env['Env 0.0']['rest_ua'] > env['Env 0.5']['rest_ua'] > env['Env 1.0']['rest_ua'], rest_ua=[env[f'Env {x}']['rest_ua'] for x in ('0.0', '0.5', '1.0')])
tap = load('tap.json')


def bass(label, cut):
    r = next(x for x in tap if x['label'] == label and x['res'] == 0.0 and x['cut'] == cut)
    return V.np.interp(32, r['f'], r['vca']) - V.np.interp(65.4, r['f'], r['vca'])


check('Bass is down by the same order as the manual, and C20/C21 cause it', -8 < bass('stock', 1.0) < -3 and -8 < bass('stock', 0.5) < -3 and abs(bass('large tap caps', 0.5)) < 1,
      db_32hz_vs_65hz=dict(cut50=bass('stock', 0.5), cut100=bass('stock', 1.0), large_caps=bass('large tap caps', 0.5)))

# ---- Findings the report rests on ----
rows = load('one_at_a_time.json')
base = {r['cut']: r for r in rows if r['name'] == 'baseline'}
check('Resonance Q rises with cutoff', base['low']['q'] < base['mid']['q'] < base['high']['q'], q={k: v['q'] for k, v in base.items()})
margins = extras['margins']
as_built = [r['margin_db'] for r in margins if r['name'] == 'stock']
lossless = [r['margin_db'] for r in margins if r['name'] == 'couplers removed, Q21 not loading']
check('Margin is below 0 dB as built, and flat just above 0 dB with the two losses removed', max(as_built) < 0 and 0 < min(lossless) and max(lossless) < 0.5, as_built_db=[as_built[0], as_built[-1]], lossless_db=[lossless[0], lossless[-1]])
table = extras['hfe_table']
hfes = sorted(table, key=int)
check("Q rises with Q21's hFE at every cutoff", all(table[a][c]['q'] < table[b][c]['q'] for a, b in zip(hfes, hfes[1:]) for c in ('low', 'mid', 'high')), hfe=[int(x) for x in hfes])
named = {(r['name'], r['cut']): r for r in rows}
for part, label in (('Q12', 'Q12 hFE'), ('2SC2291', 'Q22 hFE')):
    tail = ('250 (datasheet min)', '800 (datasheet max)') if part == 'Q12' else ('250', '800')
    spread = max(abs(named[(f'{part} hFE {t}', c)]['margin_db'] - base[c]['margin_db']) for t in tail for c in base)
    check(f'{label} across the datasheet range barely changes the loop margin', spread < 0.1, largest_change_db=spread)
leak = {r['name']: r for r in load('envelope_leak.json') if not r['audio']}
notes = next(r for r in load('envelope_leak.json') if r['audio'] and r['name'] == 'matched')['vca_gated_mvpp']
q12 = [leak[f'Q12 off by {x} mV']['vca_gated_mvpp'] for x in (1, 3, 10, 30)]
check('Envelope leakage grows with Q12 offset, and stays well below the notes up to 3 mV', q12 == sorted(q12) and q12[1] < notes / 30, leak_mvpp=q12, notes_mvpp=notes)
check('Q22, Q21 and ladder offsets of 10 mV leave the envelope leakage unchanged', all(abs(leak[k]['vca_gated_mvpp'] - leak['matched']['vca_gated_mvpp']) < 0.01 for k in ('Q22 off by 10 mV', 'Q21 off by 10 mV', 'ladder left side +10 mV each')))
pairs = {r['name']: r for r in load('pair_matching.json')}
matched = pairs['matched']


def margin_change(name):
    return max(abs(pairs[name]['small_signal'][c]['margin_db'] - matched['small_signal'][c]['margin_db']) for c in ('low', 'mid', 'high'))


q22 = [n for n in pairs if n.startswith('Q22')]
check('Q22 needs no matching: no difference between its halves moves the margin', max(margin_change(n) for n in q22) < 0.02, cases=len(q22), largest_change_db=max(margin_change(n) for n in q22))
q12_hfe = [n for n in pairs if n.startswith('Q12 hFE')]
check("A difference in hFE between Q12's halves does not move the margin", max(margin_change(n) for n in q12_hfe) < 0.02, cases=len(q12_hfe))
check("Q12 tolerates a 10 mV Vbe offset, and 30 mV costs real Q", margin_change('Q12 Vbe off by 10 mV') < 0.3 and pairs['Q12 Vbe off by 30 mV']['small_signal']['mid']['q'] < 0.8 * matched['small_signal']['mid']['q'])
check("Q21's hFE match matters: hFE 800 and 250 cut its Q at the top of the range by more than half", pairs['Q21 hFE 800 and 250']['small_signal']['high']['q'] < 0.5 * matched['small_signal']['high']['q'], q=pairs['Q21 hFE 800 and 250']['small_signal']['high']['q'])
rate = {c: sum(r[c]['margin_db'] > 0 for r in mc) / len(mc) for c in ('low', 'mid', 'high')}
check('Across the tolerance run, self-oscillation appears only at the top of the range', rate['low'] == 0 and rate['mid'] == 0 and 0 < rate['high'] < 0.2, fraction=rate)

# ---- The folder itself ----
offenders = []
for path in HERE.rglob('*'):
    if path.is_file() and path.suffix in ('.py', '.md', '.json') and 'native-probes' not in path.parts and path.name != Path(__file__).name:
        text = path.read_text()
        if '/Users' + '/' in text or '/opt/' + 'homebrew' in text:
            offenders.append(path.name)
check('No machine-specific paths in the study', not offenders, offenders=offenders)
waves = sorted(RES.glob('*.wav'))
fine = []
for path in waves:
    with wave.open(str(path)) as w:
        fine.append(w.getnchannels() == 1 and w.getframerate() == 48000 and abs(w.getnframes() / 48000 - 4.35) < 0.01)
check('Four demonstration WAVs, mono 48 kHz, 4.35 s', len(waves) == 4 and all(fine), files=[p.name for p in waves])

record = dict(
    schema=1,
    generator='verify_report.py',
    passed=all(c['passed'] for c in CHECKS),
    check_count=len(CHECKS),
    scope='ngspice model of the VCF built from the KiCad netlist, compared with published analysis and published claims about the TB-303. Nothing is measured on hardware.',
    measured_on_hardware=False,
    report='kicad-working/validation/vcf-simulation/README.md',
    checks=CHECKS,
    findings=dict(
        q_at_full_resonance={k: v['q'] for k, v in base.items()},
        peak_hz_per_microamp={k: v['fpeak'] / v['ladder_ua'] for k, v in base.items()},
        analytic_critical_gain_actual_caps=V.critical_k(18 / 33)[0],
        margin_db_as_built={k: v['margin_db'] for k, v in base.items()},
        top_of_cutoff_range_depends_on_unknown_pot_taper={k: v['f_high'] for k, v in extras['taper'].items()},
        tolerance_self_oscillation_fraction=rate,
    ),
    open_items=[
        'The taper of VR3 is unknown; only the knob-to-Hz map depends on it.',
        'The sub-audio loop crossing near 6 to 8 Hz is a model-only prediction, unconfirmed by any report found.',
        'The transistor models are substitutes; IS, VAF and the capacitance split are generic values.',
        'The VCO is an ideal saw, and the VCA and output stage are not simulated.',
    ],
    sources=[
        'https://www.timstinchcombe.co.uk/synth/Moog_ladder_tf.pdf',
        'https://www.firstpr.com.au/rwi/dfish/303-unique.html',
        'https://www.firstpr.com.au/rwi/dfish/Devil-Fish-Manual.pdf',
        'https://raw.githubusercontent.com/x0xb0x/x0xb0x.github.io/HEAD/pages/ladyada.net/make/x0xb0x/fab/vcf/index.html',
        'https://raw.githubusercontent.com/x0xb0x/x0xb0x.github.io/HEAD/pages/ladyada.net/make/x0xb0x/fab/vco.html',
    ],
    models_changed=False,
)
(ROOT / 'docs' / 'vcf-simulation.json').write_text(json.dumps(record, indent=2) + '\n')
for c in CHECKS:
    print('PASS' if c['passed'] else 'FAIL', c['check'])
print(f"{sum(c['passed'] for c in CHECKS)} of {len(CHECKS)} passed; wrote docs/vcf-simulation.json")
raise SystemExit(0 if record['passed'] else 1)
