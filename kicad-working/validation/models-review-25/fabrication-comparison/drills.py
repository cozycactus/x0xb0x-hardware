# SPDX-License-Identifier: CC0-1.0
"""Match Eagle drill sites (pads, vias, holes) with Excellon holes."""
import math


def match(E_, K_, tol=0.01):
    """E_: (kind, ident, (x, y), drill_mm); K_: Excellon holes. Sizes compared at Excellon's 3 decimals."""
    unE, used, sizes = [], set(), []
    for kind, n, (x, y), d in E_:
        best = None
        for i, h in enumerate(K_):
            if i in used:
                continue
            dd = math.hypot(h['pos'][0] - x, h['pos'][1] - y)
            if dd < tol and (best is None or dd < best[0]):
                best = (dd, i)
        if best is None:
            unE.append((kind, n, (x, y), d))
            continue
        used.add(best[1])
        h = K_[best[1]]
        if abs(h['drill'] - round(d, 3)) > 0.0006 or 'end' in h:
            sizes.append((kind, n, (x, y), d, h['drill'], h.get('end')))
    return unE, [h for i, h in enumerate(K_) if i not in used], sizes
