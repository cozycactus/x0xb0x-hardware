#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""All report figures, from results/. Colours: the dataviz reference palette, validated for light mode."""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
RES = HERE / 'results'
PROBES = HERE / 'native-probes'
OUT = HERE / 'plots'
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
S = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#6250d6']
BLUE_RAMP = ['#b7d3f2', '#86b4e8', '#5595dd', '#2a78d6', '#154f99']
plt.rcParams.update({'font.family': ['Helvetica', 'Arial', 'DejaVu Sans'], 'font.size': 10, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.7, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': SURF,
                     'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'axes.titlesize': 11, 'axes.titlecolor': INK, 'axes.titleweight': 'normal', 'legend.frameon': False,
                     'lines.linewidth': 1.6, 'figure.dpi': 150, 'axes.axisbelow': True, 'axes.titlelocation': 'left'})


def fig(w, h, title, sub=None, **kw):
    f, ax = plt.subplots(figsize=(w, h), constrained_layout=True, **kw)
    f.suptitle(title, x=0.012, ha='left', fontsize=13, color=INK, fontweight='bold')
    return f, ax


def hz(ax):
    ax.set_xscale('log')
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:g}' if v < 1000 else f'{v / 1000:g}k'))


def f1():
    c = json.loads((RES / 'ladder_check.json').read_text())
    f, ax = fig(7.6, 4.0, 'The KiCad ladder in SPICE matches the published equation to within 0.1 dB')
    for i, cut in enumerate((0.0, 0.5, 1.0)):
        r = next(x for x in c if x['cut'] == cut and x['c18'] == 18e-9)
        fr = np.array(r['f'])
        ax.plot(fr, 20 * np.log10(r['calc']), color=GRID, lw=5, solid_capstyle='round', label='Analytic: Stinchcombe, extended to .018/.033' if i == 0 else None)
        ax.plot(fr, 20 * np.log10(r['sim_unloaded']), color=S[0], lw=1.5, label='SPICE, output amp off the ladder' if i == 0 else None)
        ax.plot(fr, 20 * np.log10(r['sim']), color=S[1], lw=1.2, ls='--', label='SPICE, as built (Q21 loads the top)' if i == 0 else None)
        y = np.interp(1500, fr, 20 * np.log10(r['calc']))
        ax.annotate(f"{r['ladder_ua']:.1f} µA", (1500, y), xytext=(4, 5), textcoords='offset points', color=INK2, fontsize=9)
    hz(ax)
    ax.set(xlim=(10, 30e3), ylim=(-80, 5), xlabel='Frequency (Hz)', ylabel='Ladder gain, Q12 input to top (dB)')
    ax.legend(loc='lower left')
    f.savefig(OUT / '01-validation.png')


def f2():
    R = json.loads((RES / 'responses.json').read_text())
    f, (a, b) = fig(10, 4.1, 'Resonance reshapes the response: it lifts a peak and sinks everything below it', sharey=True, ncols=2)
    for i, res in enumerate((0, 0.25, 0.5, 0.75, 1.0)):
        r = next(x for x in R if x['cut'] == 0.5 and x['res'] == res)
        a.plot(r['f'], r['vca_db'], color=BLUE_RAMP[i], label=f'{int(res * 100)} %')
    for i, cut in enumerate((0, 0.25, 0.5, 0.75, 1.0)):
        r = next(x for x in R if x['res'] == 1.0 and x['cut'] == cut)
        b.plot(r['f'], r['vca_db'], color=BLUE_RAMP[i], label=f'{int(cut * 100)} %')
    a.set_title('Cutoff at 50 %, Resonance varied')
    b.set_title('Resonance at 100 %, Cutoff varied')
    for x, t in ((a, 'Resonance'), (b, 'Cutoff')):
        hz(x)
        x.set(xlim=(10, 20e3), ylim=(-100, -20), xlabel='Frequency (Hz)')
        x.legend(title=t, loc='lower left')
    a.set_ylabel('Waveform switch to VCA input (dB)')
    f.savefig(OUT / '02-knob-responses.png')


def f3():
    E = json.loads((RES / 'extras.json').read_text())['margins']
    f, ax = fig(7.8, 4.3, 'Why the resonance weakens at low cutoff: the loop loses up to 6.6 dB there')
    styles = {'couplers removed, Q21 not loading': (S[2], 'Couplers removed, Q21 not loading', 7), 'couplers removed': (S[3], 'Couplers removed', -1), 'stock': (S[0], 'As built', -9)}
    for name, (col, lab, dy) in styles.items():
        r = [x for x in E if x['name'] == name]
        ax.plot([x['ladder_ua'] for x in r], [x['margin_db'] for x in r], color=col, marker='o', ms=4, lw=1.8)
        ax.annotate(lab, (r[-1]['ladder_ua'], r[-1]['margin_db']), xytext=(6, dy), textcoords='offset points', va='center', color=INK, fontsize=9)
    lo = [x for x in E if x['name'] == 'Q21 hFE 250']
    hi = [x for x in E if x['name'] == 'Q21 hFE 800']
    ax.fill_between([x['ladder_ua'] for x in lo], [x['margin_db'] for x in lo], [x['margin_db'] for x in hi], color=S[0], alpha=0.15, lw=0)
    ax.annotate('Q21 hFE 250 to 800', (lo[3]['ladder_ua'], lo[3]['margin_db']), xytext=(4, -12), textcoords='offset points', color=INK2, fontsize=9)
    x2 = [x for x in E if x['name'] == 'feedback x2']
    ax.plot([x['ladder_ua'] for x in x2], [x['margin_db'] for x in x2], color=S[1], marker='o', ms=4, lw=1.8)
    ax.annotate('Feedback doubled\n(Devil Fish "high resonance")', (x2[-1]['ladder_ua'], x2[-1]['margin_db']), xytext=(6, 0), textcoords='offset points', va='center', color=INK, fontsize=9)
    ax.axhline(0, color=INK2, lw=1)
    ax.annotate('Self-oscillates above this line', (9.5, 0), xytext=(0, 12), textcoords='offset points', color=INK2, fontsize=9)
    ax.set_xscale('log')
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:g}'))
    ax.set_xticks([3, 5, 7.5, 10, 15, 20, 27])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set(xlim=(2.8, 70), ylim=(-9, 6.5), xlabel='Ladder current (µA). Cutoff knob 0 to 100 % covers 3 to 27 µA', ylabel='Loop gain at the resonance crossing (dB)')
    f.savefig(OUT / '03-self-oscillation-margin.png')


def f4():
    rows = json.loads((RES / 'one_at_a_time.json').read_text())
    base = {r['cut']: r for r in rows if r['name'] == 'baseline'}
    names = [r['name'] for r in rows if r['cut'] == 'mid' and r['name'] != 'baseline']
    drop = {'Q12 hFE 250 (datasheet min)', 'Q12 hFE 800 (datasheet max)', 'TM3 at 400 Hz tune', 'TM3 at 600 Hz tune', 'couplers large AND Q21 not loading', 'all four couplers large (no HP)', 'MEG cap floor 0.2 V (long idle)', '2SC2291 hFE 250', '2SC2291 hFE 800', 'Q22 pair off by 10 mV', 'ladder left side +10 mV each', 'Q12 pair off by 1 mV', 'Q21 pair off by 10 mV', 'R110,R111 22K -> 18K', 'C18 .010', '2SC536 hFE 320', 'temperature 15 C', 'temperature 35 C', 'C25,C27 .1 -> .047 uF', 'C23 1 -> .22 uF'}
    names = [n for n in names if n not in drop]
    data = []
    for n in names:
        r = {x['cut']: x for x in rows if x['name'] == n}
        data.append((n, [math.log2(r[c]['fpeak'] / base[c]['fpeak']) for c in ('low', 'mid', 'high')], [r[c]['margin_db'] - base[c]['margin_db'] for c in ('low', 'mid', 'high')]))
    data.sort(key=lambda d: max(abs(x) for x in d[2]))
    f, (a, b) = fig(10.6, 6.6, 'What moves the filter, one change at a time, at full Resonance', ncols=2, sharey=True, width_ratios=[1, 1])
    y = np.arange(len(data))
    for k, (lab, col) in enumerate((('Cutoff 0 %', S[0]), ('Cutoff 50 %', S[1]), ('Cutoff 100 %', S[2]))):
        a.scatter([d[1][k] for d in data], y, s=26, color=col, label=lab, zorder=3, edgecolor=SURF, linewidth=0.8)
        b.scatter([d[2][k] for d in data], y, s=26, color=col, zorder=3, edgecolor=SURF, linewidth=0.8)
    a.set_yticks(y, [d[0].replace('->', 'to') for d in data], fontsize=8.5)
    for x in (a, b):
        x.axvline(0, color=INK2, lw=1)
        x.grid(axis='y', visible=False)
    a.set(xlabel='Shift of the resonant peak (octaves)')
    b.set(xlabel='Change of loop margin (dB). More means sharper resonance')
    a.legend(loc='lower left', fontsize=9)
    f.savefig(OUT / '04-influence-ranking.png')


def f5():
    rows = np.load(PROBES / 'waveforms.npz', allow_pickle=True)['rows']
    f, ax = fig(10, 4.5, 'C1 at Cutoff 50 %: the simulated waveform at the VCA input', nrows=2, ncols=3, sharex=True, sharey=True)
    for i, (w, c) in enumerate((('saw', S[0]), ('square', S[1]))):
        for j, res in enumerate((0.0, 0.5, 1.0)):
            r = next(x for x in rows if x['wave'] == w and x['res'] == res and x['cut'] == 0.5 and abs(x['f0'] - 65.41) < 1)
            t, v = r['t'] * 1e3, (r['vca'] - r['vca'].mean()) * 1e3
            ax[i, j].plot(t, v, color=c, lw=1.1)
            ax[i, j].set_xlim(0, 2.2 * 1000 / 65.41)
            ax[i, j].set_title(f"{w.capitalize()}, Resonance {int(res * 100)} %", fontsize=10)
    for x in ax[1]:
        x.set_xlabel('Time (ms)')
    for x in ax[:, 0]:
        x.set_ylabel('mV')
    f.savefig(OUT / '05-waveforms.png')


def f6():
    rows = np.load(PROBES / 'envelopes.npz', allow_pickle=True)['rows']
    f, ax = fig(9.2, 4.6, 'Accent sweep: Resonance turns a sharp pulse into a slow rise that stacks')
    items = [('accent all, Res 0.0', S[0], 'Accent, Resonance 0 %', (1140, 205)), ('accent all, Res 0.5', S[1], 'Accent, Resonance 50 %', (1140, 88)), ('accent all, Res 1.0', S[2], 'Accent, Resonance 100 %', (1170, 40)), ('no accent, Res 1', INK2, 'No accent', (1270, 13))]
    for lab, col, txt, at in items:
        r = next(x for x in rows if x['label'] == lab)
        ax.plot(r['t'] * 1e3, r['ua'], color=col, lw=1.3)
        ax.annotate(txt, at, xytext=(6, 2), textcoords='offset points', color=INK, fontsize=9)
    for i in range(8):
        ax.axvspan(250 + i * 125, 250 + i * 125 + 62.5, color=GRID, alpha=0.45, lw=0)
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:g}'))
    ax.set_yticks([3, 5, 10, 20, 50, 100, 200])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set(xlim=(180, 1420), ylim=(3, 300), xlabel='Time (ms). Shading marks the gate, eight notes at 120 BPM', ylabel='Ladder current (µA)')
    f.savefig(OUT / '06-accent-sweep.png')


def f7():
    rows = json.loads((RES / 'drive.json').read_text())
    saw = [r for r in rows if r['label'].startswith('drive')]
    sq = [r for r in rows if r['label'].startswith('square')]
    f, ax = fig(7.4, 3.8, 'Harder drive quenches the resonance and leaves the fundamental alone')
    ax.plot([r['scale'] for r in saw], [r['compress_db'] for r in saw], color=S[0], marker='o', ms=5, lw=1.8)
    ax.plot([r['scale'] for r in saw], [r['fund_db'] for r in saw], color=INK2, marker='o', ms=4, lw=1.4)
    ax.plot([r['scale'] for r in sq], [r['compress_db'] for r in sq], color=S[1], marker='s', ms=5, lw=1.8)
    ax.annotate('Saw, harmonic at the peak', (8, saw[-1]['compress_db']), xytext=(-6, 8), textcoords='offset points', color=INK, ha='right', fontsize=9)
    ax.annotate('Square, harmonic at the peak', (4, sq[-1]['compress_db']), xytext=(4, 6), textcoords='offset points', color=INK, ha='left', fontsize=9)
    ax.annotate('Fundamental', (8, saw[-1]['fund_db']), xytext=(0, 6), textcoords='offset points', color=INK2, ha='right', fontsize=9)
    ax.axvline(1, color=GRID, lw=2)
    ax.annotate('Stock level', (1, -14), xytext=(4, 0), textcoords='offset points', color=INK2, fontsize=9)
    ax.set_xscale('log', base=2)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'×{v:g}'))
    ax.set(xlim=(0.09, 9), ylim=(-15, 2), xlabel='Input level, set by R62 (C1, Cutoff 50 %, Resonance 100 %)', ylabel='Output against the linear prediction (dB)')
    f.savefig(OUT / '07-drive.png')


def f8():
    rows = json.loads((RES / 'monte_carlo.json').read_text())
    f, ax = fig(10, 3.3, 'Across 200 simulated units, trimmed alike: most never self-oscillate', ncols=3, sharey=True)
    bins = np.arange(-10, 2.01, 0.4)
    for x, (k, lab) in zip(ax, (('low', 'Cutoff 0 %'), ('mid', 'Cutoff 50 %'), ('high', 'Cutoff 100 %'))):
        m = np.array([r[k]['margin_db'] for r in rows])
        x.hist(m, bins=bins, color=S[0], edgecolor=SURF, linewidth=1)
        x.axvline(0, color=INK2, lw=1)
        x.set_title(f"{lab}: median {np.median(m):.1f} dB, {100 * np.mean(m > 0):.0f} % above 0", fontsize=10)
        x.set_xlabel('Loop margin at the resonance (dB)')
        x.grid(axis='x', visible=False)
    ax[0].set_ylabel('Units')
    f.savefig(OUT / '08-tolerance.png')


for fn in (f1, f2, f3, f4, f5, f6, f7, f8):
    fn()
print(sorted(p.name for p in OUT.glob('*.png')))
