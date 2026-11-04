#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Generate a board's sheets. Usage: build.py <mainboard|ioboard> <output dir>"""
import sys

import x0x_draw as X


def project_mainboard():
    import mainboard_sheets as M
    p = X.Project('mainboard', 'mainboard')
    pages = [('p02_cpu', 'CPU', M.draw_cpu, 'A3'), ('p03_encoders', 'Rotary encoders', M.draw_encoders, 'A3'), ('p04_switches', 'Tact switches', M.draw_switches, 'A3'), ('p05_leds', 'LEDs', M.draw_leds, 'A3'), ('p06_cv_vco', 'CV and VCO', M.draw_cv_vco, 'A3'), ('p07_vcf', 'VCF', M.draw_vcf, 'A3'), ('p08_vca', 'VCA', M.draw_vca, 'A3'), ('p09_env', 'Envelope', M.draw_env, 'A3'), ('p10_mixer', 'Mixer and headphone', M.draw_mixer, 'A3')]
    return p, pages, 'x0xb0x mainboard', ['x0xb0x Mainboard Beta Release (3/8/2005)', 'Copyright (c) 2005, Limor Fried.', 'See licensing information at http://www.ladyada.net/make/x0xb0x/']


def project_ioboard():
    import ioboard_sheets as I
    p = X.Project('ioboard', 'I/O board')
    pages = [('p02_power', 'Power', I.draw_power, 'A3'), ('p03_usb', 'USB', I.draw_usb, 'A3'), ('p04_midi_jacks', 'MIDI, DIN sync and jacks', I.draw_midi, 'A3')]
    return p, pages, 'x0xb0x I/O board', ['x0xb0x IOBoard v1.0 Release (5/2005)', 'Copyright (c) 2005, Limor Fried.', 'See licensing information at http://www.ladyada.net/make/x0xb0x/']


def build(board, out):
    p, pages, root_title, root_lines = (project_mainboard if board == 'mainboard' else project_ioboard)()
    for file, title, draw, paper in pages:
        draw(p.sheet(file, title, paper))
    problems = X.name_nets(p)
    for s in p.sheets:
        s.finish()
    X.write_project(p, out, root_title, root_lines, 'K29')
    print(f'{board}: {len(p.sheets)} sheets; nets with no label where one is needed: {len(problems)}')
    for t in problems[:40]:
        print('  ', t)
    return not problems


def main():
    board, out = sys.argv[1:3]
    raise SystemExit(0 if build(board, out) else 1)


if __name__ == '__main__':
    main()
