#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Finish the mainboard after the hand routing: run once, with KiCad closed.

Marks the four SIP pairs do-not-place, moves the chips' references clear of the original text where there is room, and adds the
four chips to the schematic scripts' parts data. Tracks, pads and pours are not touched.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent / 'mainboard'
DATA = HERE.parent / 'schematic-redraw' / 'data' / 'mainboard_parts.json'
TEXT = {'Q121': (56.0, -120.7), 'Q122': (57.6, -104.4)}
CHIPS = ('Q112', 'Q121', 'Q122', 'Q126')


def footprint_span(text, ref):
    i = text.index(f'(property "Reference" "{ref}"')
    return text.rindex('\n\t(footprint ', 0, i), text.index('\n\t)\n', i)


def main():
    path = PROJECT / 'mainboard.kicad_pcb'
    text = path.read_text()
    for ref in ('Q12', 'Q21', 'Q22', 'Q26'):
        a, b = footprint_span(text, ref)
        f = text[a:b]
        assert '(attr' not in f.split('(fp_', 1)[0], ref
        n, count = re.subn(r'(\n\t\t)\(duplicate_pad_numbers_are_jumpers', r'\1(attr dnp)\1(duplicate_pad_numbers_are_jumpers', f, count=1)
        assert count == 1, ref
        text = text[:a] + n + text[b:]
    for ref, (x, y) in TEXT.items():
        a, b = footprint_span(text, ref)
        f = text[a:b]
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', f)
        assert not at[3], ref
        n, count = re.subn(rf'(\(property "Reference" "{ref}"\s+\(at )[-\d.]+ [-\d.]+', rf'\g<1>{round(x - float(at[1]), 3)} {round(y - float(at[2]), 3)}', f, count=1)
        assert count == 1, ref
        text = text[:a] + n + text[b:]
    path.write_text(text)

    parts = json.loads(DATA.read_text())
    for ref in CHIPS:
        a, b = footprint_span(text, ref)
        f = text[a:b]
        value = re.search(r'\(property "Value" "([^"]*)"', f)[1]
        pads = [dict(num=n, net=net, fn='') for n, net in re.findall(r'\(pad "(\d)" smd roundrect.*?\(net "([^"]*)"\)', f, re.S)]
        assert len(pads) == 6, (ref, pads)
        parts[ref] = dict(val=value, value=value, fp='x0x-smd:SOT-363_Hand', path=None, board_only=False, pads=pads)
    DATA.write_text(json.dumps(parts, indent=0, sort_keys=True))
    print('finished', CHIPS)


if __name__ == '__main__':
    main()
