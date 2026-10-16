# SPDX-License-Identifier: CC0-1.0
"""Minimal Excellon reader for KiCad decimal-metric drill files."""
import re


def read(path):
    tools, holes, cur, slot = {}, [], None, None
    for line in open(path):
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        m = re.match(r'^T(\d+)C([\d.]+)', line)
        if m:
            tools[int(m.group(1))] = float(m.group(2))
            continue
        m = re.match(r'^T(\d+)$', line)
        if m:
            cur = int(m.group(1))
            continue
        m = re.match(r'^X(-?[\d.]+)Y(-?[\d.]+)(G85X(-?[\d.]+)Y(-?[\d.]+))?$', line)
        if m and cur is not None:
            x, y = float(m.group(1)), float(m.group(2))
            if m.group(3):
                holes.append(dict(pos=(x, y), end=(float(m.group(4)), float(m.group(5))), drill=tools[cur]))
            else:
                holes.append(dict(pos=(x, y), drill=tools[cur]))
    return holes
