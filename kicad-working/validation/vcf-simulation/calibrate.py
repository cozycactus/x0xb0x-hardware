#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Trim TM3 to the kit's tuning point, then map the Cutoff knob. Writes calibration.json."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import vcfdeck as V


def tune(target=500.0, **kw):
    """Bisect TM3 on a log scale of the series resistance, for peak = target at Cut 50 %, Res 100 %."""
    lo, hi = 0.0, 1.0
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        r = V.ac_run(dict(cut=0.5, res=1.0, env=0.0, tm3=mid, **kw), fstart=50, fstop=20e3, per_decade=100)
        fp, _ = V.peak(r['f'], r['vca'], lo=60)
        if fp > target:   # too high: more series resistance
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


if __name__ == '__main__':
    tm3 = tune()
    print('TM3 fraction for 500 Hz:', round(tm3, 4), '=', round(tm3 * 500), 'kohm')
    limits = {}
    for t in (400, 600):
        limits[f'tm3_{t}'] = round(tune(t), 3)
        print('TM3 for', t, 'Hz:', limits[f'tm3_{t}'])
    rows = []
    for cut in np.linspace(0, 1, 11):
        for res in (1.0,):
            r = V.ac_run(dict(cut=float(cut), res=res, env=0.0, tm3=tm3), fstart=20, fstop=30e3, per_decade=100)
            fp, pk = V.peak(r['f'], r['vca'], lo=40)
            f, T = V.loop_run(dict(cut=float(cut), res=res, env=0.0, tm3=tm3))
            fo, m = V.oscillation_margin(f, T)
            rows.append(dict(cut=round(float(cut), 2), ladder_ua=r['op']['ladder_ua'], r73_ua=r['op']['r73_ua'], fpeak=fp, peak_db=pk, fosc=fo, margin_db=m))
            print(f"cut {cut:.1f}  ladder {r['op']['ladder_ua']:7.2f} uA  r73 {r['op']['r73_ua']:6.2f} uA  peak {fp:7.1f} Hz {pk:6.1f} dB   T=+real at {fo:7.1f} Hz, margin {m:6.2f} dB")
    Path(__file__).with_name('calibration.json').write_text(json.dumps(dict(tm3=tm3, **limits, rows=rows), indent=1))
