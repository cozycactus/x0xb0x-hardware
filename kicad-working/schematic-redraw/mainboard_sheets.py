#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""The mainboard's sheets. Each function places its parts and types its own wires and label names, following the blocks of
the original Eagle sheet. check_nets.py compares the result with the board copper and with the Eagle nets."""

MCU, GATE, SHIFT_IN, SHIFT_OUT, TACT = "MEGA162P''", '7412N', '7416N', '7459N', "40-XX''"


def draw_cpu(d):
    d.block('Reset and clock', 63.5, 53.34, 142.24, 124.46, title_at=(66.04, 120.65))
    d.block('MCU', 143.51, 66.04, 261.62, 185.42)
    d.block('Unused gates of IC1', 96.52, 20.32, 182.88, 50.8)
    d.block('EEPROM', 261.62 + 1.27, 66.04, 345.44, 111.76)
    d.block('To the I/O board', 262.89, 129.54, 345.44, 185.42)

    # Power-on reset through IC1A, as drawn on the original sheet.
    d.rail('+5V', (86.36, 58.42))
    d.route((81.28, 58.42), (91.44, 58.42))
    d.down('D1', 81.28, 66.04, 'C', left_text=True)
    d.down('R200', 91.44, 66.04, '1')
    d.route('D1.C', (81.28, 58.42))
    d.route('R200.1', (91.44, 58.42))
    d.route('D1.A', (81.28, 78.74))
    d.route('R200.2', (91.44, 78.74))
    d.down('C105', 81.28, 86.36, '+', left_text=True)
    d.route((81.28, 78.74), 'C105.+')
    d.ground('C105.-')
    d.chip('IC1', GATE, 1, 119.38, 78.74, ref_at=(124.46, 71.12), val_at=(124.46, 73.66), just='left')
    d.route((81.28, 78.74), 'IC1.2')
    d.rail('+5V', 'IC1.1')
    d.across('D2', 119.38, 88.9, 'C')
    d.route((104.14, 78.74), (104.14, 88.9), 'D2.C')
    d.route('D2.A', (134.62, 88.9), (134.62, 78.74))
    d.chip('IC3', MCU, 1, 165.1, 119.38, ref_at=(149.86, 74.93), val_at=(165.1, 180.34))
    d.route('IC1.3', 'IC3.9')

    # The MCU's clock and supply.
    d.reso('XTL1', 106.68, 104.14)
    d.route('XTL1.3', (106.68, 93.98), (139.7, 93.98), (139.7, 86.36), 'IC3.18')
    d.route('XTL1.1', (106.68, 116.84), (142.24, 116.84), (142.24, 91.44), 'IC3.19')
    d.ground('XTL1.2', 'L')
    d.note('XTL1 is a ceramic resonator', 66.04, 116.84)
    d.route('IC3.40', (129.54, 96.52))
    d.rail('+5V', (129.54, 96.52), 'L')
    d.route('IC3.20', (139.7, 99.06), (139.7, 111.76))
    d.ground((139.7, 111.76))
    d.down('C106', 134.62, 104.14, '2', left_text=True)
    d.route((134.62, 96.52), 'C106.2')
    d.route('C106.1', (134.62, 111.76), (139.7, 111.76))
    d.down('C102', 83.82, 104.14, '+')
    d.rail('+5V', 'C102.+')
    d.ground('C102.-')
    d.route('C102.+', (76.2, 99.06))
    d.flag((76.2, 99.06))

    # The MCU's lines, named as on the original sheet.
    for pin_no, net in ((32, 'LED_LATCH'), (33, 'ROTARYCOM3'), (34, 'ROTARY1'), (35, 'ROTARY2'), (36, 'ROTARY4'), (37, 'ROTARY8'), (38, 'TEMPO_SW_A'), (39, 'TEMPO_SW_B'),
                        (8, 'SPI_CLK'), (7, 'SPI_OUT'), (6, 'SPI_IN'), (4, 'USB_TX'), (3, 'USBRX'), (1, 'SWITCH_LATCH'),
                        (28, 'ACCENT'), (27, 'SLIDE'), (26, 'NOTE5'), (25, 'NOTE4'), (24, 'NOTE3'), (23, 'NOTE2'), (22, 'NOTE1'), (21, 'NOTE0'),
                        (17, 'DINSYNC1'), (16, 'DINSYNC2'), (15, 'DINSYNC3'), (14, 'DINSYNC4'), (11, 'MIDI_OUT'), (10, 'MIDI_IN'),
                        (29, 'NOTE_LATCH'), (30, 'GATE')):
        d.out(f'IC3.{pin_no}', net, 'R', 5.08)
    for pin_no in (5, 2, 13, 12, 31):
        d.nc(f'IC3.{pin_no}')

    # The rest of IC1: its supply and the two gates the board doesn't use.
    d.chip('IC1', GATE, 5, 205.74, 40.64, ref_at=(198.12, 40.64), val_at=(198.12, 43.18), hide_value=True)
    d.rail('+5V', 'IC1.14')
    d.ground('IC1.7')
    d.down('C103', 215.9, 40.64, '1')
    d.route('C103.1', (215.9, 30.48), 'IC1.14')
    d.route('C103.2', (215.9, 50.8), 'IC1.7')
    d.chip('IC1', GATE, 2, 119.38, 40.64, ref_at=(124.46, 33.02), val_at=(124.46, 35.56), hide_value=True, just='left')
    d.route('IC1.4', (106.68, 30.48), (106.68, 40.64), 'IC1.5')
    d.route((106.68, 40.64), (106.68, 45.72))
    d.ground((106.68, 45.72))
    d.nc('IC1.6')
    d.chip('IC1', GATE, 4, 165.1, 40.64, ref_at=(170.18, 33.02), val_at=(170.18, 35.56), hide_value=True, just='left')
    d.route('IC1.13', (152.4, 30.48), (152.4, 40.64), 'IC1.12')
    d.route((152.4, 40.64), (152.4, 45.72))
    d.ground((152.4, 45.72))
    d.nc('IC1.11')

    # The EEPROM.
    d.chip('IC2', 'AT25P', 1, 287.02, 88.9, ref_at=(279.4, 77.47), val_at=(287.02, 100.33))
    d.route('IC2.8', (266.7, 81.28))
    d.rail('+5V', (266.7, 81.28))
    d.route('IC2.4', (266.7, 96.52))
    d.ground((266.7, 96.52))
    d.down('C107', 266.7, 88.9, '2')
    d.route((266.7, 81.28), 'C107.2')
    d.route('C107.1', (266.7, 96.52))
    d.rail('+5V', 'IC2.7', 'R')
    d.rail('+5V', 'IC2.3', 'R')
    d.out('IC2.1', 'SWITCH_LATCH', 'R', 5.08)
    d.out('IC2.6', 'SPI_CLK', 'R', 5.08)
    d.out('IC2.2', 'SPI_OUT', 'R', 5.08)
    d.out('IC2.5', 'SPI_IN', 'R', 5.08)

    # The connector to the I/O board.
    d.chip('J3', "MA12-''", 1, 287.02, 160.02, ref_at=(287.02, 141.0), hide_value=True)
    for pin_no, net in ((12, 'DINSYNC1'), (11, 'DINSYNC2'), (10, 'DINSYNC3'), (9, 'DINSYNC4'), (6, 'MIDI_OUT'), (5, 'MIDI_IN'), (2, 'USB_TX'), (1, 'USBRX')):
        d.out(f'J3.{pin_no}', net, 'R', 5.08)
    d.route('J3.8', (299.72, 154.94), (299.72, 157.48), 'J3.7')
    d.ground((299.72, 157.48), 'R')
    d.route('J3.4', (299.72, 165.1), (299.72, 167.64), 'J3.3')
    d.rail('+5V', (299.72, 167.64), 'R')

    # On the board but not on the original sheet. With no symbol, Update PCB would delete them.
    d.block('Mounting holes', 143.51, 190.5, 261.62, 220.98)
    for i, ref in enumerate(('U$2', 'U$23', 'U$24', 'U$25', 'U$27', 'U$28', 'U$29')):
        d.hole(ref, 152.4 + 15.24 * i, 205.74)
    d.note('3.3 mm holes: on the board only, not on the original sheet', 146.05, 215.9)


def draw_encoders(d):
    d.dx, d.dy = 25.4, 25.4
    d.block('Rotary Encoders', 2.54, 22.86, 243.84, 180.34)

    # The two function switches, read through a diode each. ROTARYCOM3 drives S3 directly and S4 through Q5.
    d.note('function select', 53.34, 35.56)
    d.chip('S4', "GH307''", 1, 76.2, 60.96, ref_at=(83.82, 43.18), val_at=(83.82, 71.12))
    d.note('bank select', 53.34, 101.6)
    d.chip('S3', "GH307''", 1, 76.2, 127, ref_at=(83.82, 109.22), val_at=(83.82, 137.16))
    for s, y in (('S4', 60.96), ('S3', 127)):
        d.route(f'{s}.MT1', (58.42, y + 5.08))
        d.route((58.42, y + 2.54), (58.42, y + 5.08))
        d.ground((58.42, y + 5.08))
        d.route(f'{s}.MT2', (58.42, y))
        d.route(f'{s}.MT3', (58.42, y + 2.54))
        d.route(f'{s}.MT4', (58.42, y + 2.54))
    rows = (('D6', 'S4.P$8', 50.8, 104.14), ('D5', 'S4.P$4', 55.88, 109.22), ('D4', 'S4.P$2', 60.96, 114.3), ('D3', 'S4.P$1', 66.04, 119.38),
            ('D10', 'S3.P$8', 116.84, 104.14), ('D9', 'S3.P$4', 121.92, 109.22), ('D8', 'S3.P$2', 127, 114.3), ('D7', 'S3.P$1', 132.08, 119.38))
    for ref, contact, y, bus in rows:
        d.across(ref, 91.44, y, 'C', compact=True)
        d.route(contact, f'{ref}.C')
        d.route(f'{ref}.A', (bus, y))
    for net, x, top in (('ROTARY8', 104.14, 50.8), ('ROTARY4', 109.22, 55.88), ('ROTARY2', 114.3, 60.96), ('ROTARY1', 119.38, 66.04)):
        d.route((x, top), (x, 147.32))
        d.label(net, (x, 147.32), 'B')

    d.transistor('Q5', 40.64, 86.36, 'NPN')
    d.route('Q5.2', (43.18, 73.66), (71.12, 73.66), 'S4.C')
    d.ground('Q5.3')
    d.down('R254', 27.94, 96.52, '1', left_text=True)
    d.route('Q5.1', (27.94, 86.36), 'R254.1')
    d.across('R255', 15.24, 86.36, '1')
    d.route('R255.2', (27.94, 86.36))
    d.ground('R255.1', 'L')
    d.route('R254.2', (27.94, 142.24), (71.12, 142.24), 'S3.C')
    d.route((27.94, 142.24), (27.94, 152.4))
    d.label('ROTARYCOM3', (27.94, 152.4), 'B')

    # The tempo encoder.
    d.note('tempo', 142.24, 35.56)
    d.chip('S2', "PEC11-S''", 1, 152.4, 60.96, ref_at=(152.4, 47.0), val_at=(152.4, 76.2))
    d.route('S2.P$2', 'S2.P$1')
    d.route('S2.P$1', (134.62, 71.12))
    d.ground((134.62, 71.12))
    d.ground('S2.C', 'L')
    d.down('R270', 165.1, 58.42, '2')
    d.down('R269', 177.8, 58.42, '1')
    d.route('S2.SW2', (185.42, 50.8))
    d.route('R270.2', (165.1, 50.8))
    d.route('R269.1', (177.8, 50.8))
    d.across('J2', 190.5, 50.8, '1')
    d.rail('+5V', 'J2.2', 'R')
    d.route('S2.A', (160.02, 58.42), (160.02, 63.5), 'R270.1')
    d.down('R235', 165.1, 76.2, '1')
    d.route('R270.1', 'R235.1')
    d.route('S2.B', (177.8, 68.58), 'R269.2')
    d.down('R236', 177.8, 76.2, '1')
    d.route((177.8, 68.58), 'R236.1')
    d.route('S2.SW1', (144.78, 43.18), (185.42, 43.18))
    d.across('J1', 190.5, 43.18, '1')
    d.route((185.42, 43.18), 'J1.1')
    d.route('J1.2', (218.44, 43.18))
    d.label('TEMPO_SW', (218.44, 43.18))
    d.down('R233', 208.28, 50.8, '1')
    d.route((208.28, 43.18), 'R233.1')
    d.ground('R233.2')
    d.route('R235.2', (165.1, 93.98))
    d.down('C100', 165.1, 99.06, '2', left_text=True)
    d.ground('C100.1')
    d.route('R236.2', (187.96, 81.28), (187.96, 93.98))
    d.down('C101', 187.96, 99.06, '2', left_text=True)
    d.ground('C101.1')
    d.route((165.1, 86.36), (205.74, 86.36))
    d.label('TEMPO_SW_A', (205.74, 86.36))
    d.route((187.96, 81.28), (205.74, 81.28))
    d.label('TEMPO_SW_B', (205.74, 81.28))


SWITCH_ROWS = (
    # shift register, its y offset, and its inputs from H to A: (input pin, switch, rot, pads on +5V, open pads, signal pad, resistor, its pad on the signal, resistor's pad at the switch)
    ('IC16', 0.0, (
        (6, 'S14', 0, '2', '1 4', '3', 'R202', '3', '1'),
        (5, 'S27', 0, '2', '1', '3', 'R201', '4', '1'),
        (4, 'S26', 180, '4', '3', '1', 'R206', '2', '1'),
        (3, 'S25', 180, '4', '3', '1', 'R209', '2', '1'),
        (14, 'S24', 0, '2', '1', '3', 'R210', '4', '1'),
        (13, 'S22', 0, '1 2', '3', '4', 'R214', '4', '1'),
        (12, 'S21', 0, '2', '1 3', '4', 'R216', '4', '1'),
        (11, 'S23', 0, '1 2', '', '3', 'R212', '4', '1'))),
    ('IC17', 71.12, (
        (6, 'S13', 180, '4', '3', '1', 'R263', '2', '1'),
        (5, 'S12', 180, '4', '3 2', '1', 'R207', '1', '2'),
        (4, 'S11', 0, '1', '2', '3', 'R259', '4', '1'),
        (3, 'S10', 0, '1', '2', '3', 'R257', '4', '1'),
        (14, 'S9', 0, '1', '2 4', '3', 'R218', '3', '1'),
        (13, 'S8', 0, '1', '2', '3', 'R247', '4', '1'),
        (12, 'S7', 0, '1', '2 4', '3', 'R225', '3', '1'),
        (11, 'S6', 180, '3', '4', '1', 'R240', '2', '1'))),
    ('IC18', 142.24, (
        (6, 'S20', 0, '2', '1 3', '4', 'R219', '4', '1'),
        (5, 'S19', 0, '1 2', '3', '4', 'R220', '4', '1'),
        (4, 'S18', 0, '2', '1 3', '4', 'R224', '4', '1'),
        (3, 'S17', 0, '2', '1 3', '4', 'R226', '4', '1'),
        (14, 'S5', 0, '2', '1 3', '4', 'R230', '4', '1'),
        None,
        (12, 'S15', 180, '4', '3 2', '1', 'R232', '1', '1'),
        (11, 'S16', 180, '4', '3', '1', 'R231', '2', '1'))),
)


def draw_switches(d):
    d.dx, d.dy = 12.7, 5.08
    d.block('Tact Switches', 7.62, 10.16, 281.94, 243.84)
    pitch, x0 = 17.78, 25.4
    ic_x = x0 + 7 * pitch + 45.72
    for ic, off, columns in SWITCH_ROWS:
        rail_y, sw_y = 25.4 + off, 35.56 + off
        d.chip(ic, SHIFT_IN, 1, ic_x, 73.66 + off, ref_at=(ic_x - 7.62, 73.66 + off - 23.5), val_at=(ic_x, 73.66 + off + 20.32))
        d.rail('+5V', (x0 - 2.54, rail_y))
        last = x0 - 2.54
        for i, col in enumerate(columns):
            x = x0 + i * pitch
            if col is None:
                d.out(f'{ic}.13', 'TEMPO_SW', 'L', 12.7)
                continue
            pin_no, sw, rot, on_rail, open_pads, sig, res, res_at, res_pad = col
            at = x + 2.54 if rot == 180 else x
            d.chip(sw, TACT, 1, at, sw_y, rot, ref_at=(x - 5.08, sw_y), hide_value=True, just='right')
            for pad in on_rail.split():
                pad_x = round(d.pins[f'{sw}.{pad}'][0] - d.dx, 2)
                d.route(f'{sw}.{pad}', (pad_x, rail_y))
                last = max(last, pad_x)
            for pad in open_pads.split():
                d.nc(f'{sw}.{pad}')
            row_y = d.pins[f'{ic}.{pin_no}'][1] - d.dy
            sx = round(d.pins[f'{sw}.{sig}'][0] - d.dx, 2)
            rx = round(d.pins[f'{sw}.{res_at}'][0] - d.dx, 2)
            is_left = abs(rx - x) < 0.01
            other = round(x + 2.54, 2) if is_left else round(x, 2)
            d.down(res, rx, sw_y + 15.24, res_pad, left_text=is_left)
            d.route(f'{sw}.{res_at}', f'{res}.{res_pad}')
            d.ground(f'{res}.{"2" if res_pad == "1" else "1"}')
            if sig == res_at:
                y = sw_y + 7.62
                d.route((rx, y), (other, y), (other, row_y), f'{ic}.{pin_no}')
            else:
                d.route(f'{sw}.{sig}', (sx, row_y), f'{ic}.{pin_no}')
        d.route((x0 - 2.54, rail_y), (last, rail_y))
        d.ground(f'{ic}.15', 'L')
        d.out(f'{ic}.1', 'SWITCH_LATCH', 'L', 5.08)
        d.out(f'{ic}.2', 'SPI_CLK', 'L', 5.08)
        d.nc(f'{ic}.7')
        d.chip(ic, SHIFT_IN, 2, ic_x + 35.56, 73.66 + off, ref_at=(ic_x + 27.94, 71.12 + off), hide_value=True)
        d.rail('+5V', f'{ic}.16')
        d.ground(f'{ic}.8')
    # Decoupling, on the two registers that have a capacitor on the original sheet.
    for ic, cap, off in (('IC17', 'C113', 71.12), ('IC18', 'C112', 142.24)):
        cx = ic_x + 45.72
        d.down(cap, cx, 73.66 + off, '2')
        d.route(f'{cap}.2', (cx, 66.04 + off), f'{ic}.16')
        d.route(f'{cap}.1', (cx, 81.28 + off), f'{ic}.8')
    # The registers in a chain, and out to the MCU through IC1C.
    d.ground('IC16.10', 'L')
    for a, off in (('IC16', 0.0), ('IC17', 71.12)):
        b = 'IC17' if a == 'IC16' else 'IC18'
        out_y = 73.66 + off - 12.7
        row = 73.66 + off + 71.12 - 15.24 - 5.08
        d.route(f'{a}.9', (ic_x + 20.32, out_y), (ic_x + 20.32, row), (ic_x - 17.78, row), (ic_x - 17.78, row + 5.08), f'{b}.10')
    d.chip('IC1', GATE, 3, 266.7, 198.12, ref_at=(271.78, 190.5), hide_value=True, just='left')
    d.route('IC18.9', (213.36, 203.2), (213.36, 198.12), 'IC1.9')
    d.out('IC1.8', 'SPI_OUT', 'R', 5.08)
    d.out('IC1.10', 'SWITCH_LATCH', 'T', 2.54)


LED_CHAIN = (
    # shift register, x, y, decoupling capacitor, and its outputs QA to QH: (pin, resistor, resistor's pad on the pin, LED)
    ('IC4', 58.42, 66.04, 'C110', ((15, 'R227', '1', 'LED30'), (1, 'R229', '1', 'LED28'), (2, 'R228', '2', 'LED29'), (3, 'R238', '2', 'LED18'),
                                   (4, 'R239', '2', 'LED19'), (5, 'R234', '1', 'LED1'), (6, 'R237', '1', 'LED2'), (7, 'R241', '1', 'LED3'))),
    ('IC5', 180.34, 66.04, 'C104', ((15, 'R221', '1', 'LED33'), (1, 'R223', '1', 'LED31'), (2, 'R222', '2', 'LED32'), (3, 'R245', '2', 'LED20'),
                                    (4, 'R246', '1', 'LED21'), (5, 'R242', '1', 'LED4'), (6, 'R243', '2', 'LED5'), (7, 'R244', '2', 'LED6'))),
    ('IC7', 302.26, 66.04, 'C111', ((15, 'R250', '2', 'LED7'), (1, 'R252', '2', 'LED9'), (2, 'R251', '1', 'LED8'), (3, 'R253', '1', 'LED10'),
                                    (4, 'R256', '1', 'LED11'), (5, 'R260', '1', 'LED12'), (6, 'R261', '1', 'LED13'), (7, 'R262', '2', 'LED14'))),
    ('IC6', 58.42, 162.56, 'C109', ((15, 'R208', '1', 'LED38'), (1, 'R211', '1', 'LED37'), (2, 'R213', '1', 'LED36'), (3, 'R215', '1', 'LED35'),
                                    (4, 'R217', '2', 'LED34'), (5, 'R258', '1', 'LED24'), (6, 'R249', '2', 'LED23'), (7, 'R248', '1', 'LED22'))),
    ('IC8', 180.34, 162.56, 'C108', ((15, 'R203', '1', 'LED27'), (1, 'R205', '1', 'LED39'), (2, 'R204', '2', 'LED40'), (3, 'R264', '1', 'LED26'),
                                     (4, 'R265', '1', 'LED25'), (5, 'R266', '2', 'LED15'), (6, 'R267', '1', 'LED16'), (7, 'R268', '1', 'LED17'))),
)
LED_FAN = (15.24, 17.78, 20.32, None, 22.86, 20.32, 17.78, 15.24)


def draw_leds(d):
    d.dx, d.dy = 15.24, 7.62
    d.block('LEDs', -5.08, 2.54, 376.92, 213.36)
    for ic, x, y, cap, outputs in LED_CHAIN:
        d.chip(ic, SHIFT_OUT, 1, x, y, ref_at=(x - 7.62, y - 15.24), val_at=(x, y + 16.51))
        # Each output through its resistor and LED to ground, fanned out from the 2.54 mm pins to 5.08 mm rows.
        bus = x + 58.42
        for i, (pin_no, res, on_pin, led) in enumerate(outputs):
            row = y - 17.78 + 5.08 * i
            other = '2' if on_pin == '1' else '1'
            d.across(res, x + 33.02, row, on_pin, compact=True)
            d.across(led, x + 45.72, row, 'A', ref_at=(9.0, -1.27))
            d.route(f'{res}.{other}', f'{led}.A')
            d.route(f'{led}.K', (bus, row))
            fan = LED_FAN[i]
            if fan is None:
                d.route(f'{ic}.{pin_no}', f'{res}.{on_pin}')
            else:
                pin_y = d.pins[f'{ic}.{pin_no}'][1] - d.dy
                d.route(f'{ic}.{pin_no}', (x + fan, pin_y), (x + fan, row), f'{res}.{on_pin}')
        d.route((bus, y - 17.78), (bus, y + 20.32))
        d.ground((bus, y + 20.32))
        d.rail('+5V', f'{ic}.10', 'L')
        d.ground(f'{ic}.13', 'L')
        # Its supply and decoupling, above the chip.
        d.chip(ic, SHIFT_OUT, 2, x, y - 33.02, ref_at=(x - 2.54, y - 33.02), hide_value=True, just='right')
        d.rail('+5V', f'{ic}.16')
        d.ground(f'{ic}.8')
        d.down(cap, x + 10.16, y - 33.02, '2')
        d.route(f'{cap}.2', (x + 10.16, y - 40.64), f'{ic}.16')
        d.route(f'{cap}.1', (x + 10.16, y - 25.4), f'{ic}.8')
        # The clock and latch from the bus lines below.
        d.route(f'{ic}.11', (x - 22.86, y - 5.08), (x - 22.86, y + 27.94))
        d.route(f'{ic}.12', (x - 25.4, y + 2.54), (x - 25.4, y + 30.48))
    for y in (66.04, 162.56):
        d.route((22.86, y + 27.94), (279.4 if y < 100 else 157.48, y + 27.94))
        d.route((20.32, y + 30.48), (276.86 if y < 100 else 154.94, y + 30.48))
    d.route((22.86, 93.98), (22.86, 190.5))
    d.route((20.32, 96.52), (20.32, 193.04))
    d.route((22.86, 190.5), (15.24, 190.5))
    d.label('SPI_CLK', (15.24, 190.5), 'L')
    d.route((20.32, 193.04), (15.24, 193.04))
    d.label('LED_LATCH', (15.24, 193.04), 'L')
    # The chain: SPI_IN into IC4, each QH* into the next SER.
    d.route('IC4.14', (30.48, 55.88), (30.48, 40.64))
    d.label('SPI_IN', (30.48, 40.64), 'L')
    for a, b, x in (('IC4', 'IC5', 58.42), ('IC5', 'IC7', 180.34)):
        nx = x + 121.92
        d.route(f'{a}.9', (x + 13.97, 78.74), (x + 13.97, 91.44), (nx - 27.94, 91.44), (nx - 27.94, 55.88), f'{b}.14')
    d.route('IC7.9', (316.23, 78.74), (316.23, 99.06), (15.24, 99.06), (15.24, 152.4), 'IC6.14')
    d.route('IC6.9', (72.39, 175.26), (72.39, 187.96), (152.4, 187.96), (152.4, 152.4), 'IC8.14')
    d.nc('IC8.9')


def draw_cv_vco(d):
    d.dx, d.dy = 2.54, 12.7
    # The note latch and its resistor ladder: six bits into a 200K R-2R network.
    d.chip('IC9', '4174P', 1, 45.72, 83.82, ref_at=(38.1, 68.58), val_at=(45.72, 99.06))
    for pin_no, net in ((3, 'NOTE0'), (4, 'NOTE2'), (6, 'NOTE4'), (11, 'NOTE5'), (13, 'NOTE3'), (14, 'NOTE1'), (9, 'NOTE_LATCH')):
        d.out(f'IC9.{pin_no}', net, 'L', 5.08)
    d.rail('+5.333V', 'IC9.1', 'L')
    d.chip('IC9', '4174P', 2, 25.4, 45.72, ref_at=(30.48, 45.72), hide_value=True, just='left')
    d.rail('+5.333V', 'IC9.16')
    d.ground('IC9.8')
    rungs = (('R82', 111.76, 'N$237'), ('R81', 96.52, 'N$243'), ('R80', 81.28, 'N$155'), ('R79', 66.04, 'N$89'), ('R87', 50.8, 'N$86'), ('R90', 35.56, 'N$112'))
    pads = {'R82': '1', 'R81': '2', 'R80': '1', 'R79': '2', 'R87': '1', 'R90': '1'}
    lanes = {'R82': (2, 83.82), 'R81': (15, 88.9), 'R80': (5, 78.74), 'R79': (12, 93.98), 'R87': (7, 73.66), 'R90': (10, 68.58)}
    for res, y, _net in rungs:
        d.across(res, 104.14, y, pads[res], compact=True)
        pin_no, lane = lanes[res]
        pin_y = d.pins[f'IC9.{pin_no}'][1] - d.dy
        d.route(f'IC9.{pin_no}', (lane, pin_y), (lane, y), f'{res}.{pads[res]}')
    # The ladder's rungs, two 200K in parallel each, bottom to top.
    x1, x2 = 121.92, 137.16
    rung = ((111.76, 96.52, 'R74', '1', 'R75', '1'), (96.52, 81.28, 'R76', '2', 'R77', '1'), (81.28, 66.04, 'R84', '2', 'R83', '1'), (66.04, 50.8, 'R85', '2', 'R86', '1'), (50.8, 35.56, 'R88', '1', 'R89', '2'))
    for low, high, a, a_top, b, b_top in rung:
        mid = (low + high) / 2
        d.down(a, x1, mid, a_top)
        d.down(b, x2, mid, b_top)
        ga = {'1': '2', '2': '1'}[a_top]
        gb = {'1': '2', '2': '1'}[b_top]
        d.route(f'{a}.{a_top}', (x1, high))
        d.route(f'{a}.{ga}', (x1, low))
        d.route(f'{b}.{b_top}', (x2, high))
        d.route(f'{b}.{gb}', (x2, low))
    for _res, y, _net in rungs:
        other = '2' if pads[_res] == '1' else '1'
        d.route(f'{_res}.{other}', (x1, y), (x2, y))
    d.down('R78', x1, 121.92, '2')
    d.route((x1, 111.76), 'R78.2')
    d.rail('+5.333V', 'R78.1', 'B')

    # The CV buffer and the slide switches.
    d.chip('IC11', 'AN656N', 2, 200.66, 38.1, ref_at=(203.2, 30.48), hide_value=True, just='left')
    d.route((x2, 35.56), 'IC11.5')
    d.route((170.18, 35.56), (170.18, 76.2))
    d.route('IC11.6', (190.5, 40.64), (190.5, 48.26))
    d.across('R107', 200.66, 48.26, '1')
    d.route((190.5, 48.26), 'R107.1')
    d.route('R107.2', (213.36, 48.26), (213.36, 38.1))
    d.route('IC11.7', (243.84, 38.1))
    d.down('D31', 220.98, 27.94, 'C')
    d.route('D31.A', (220.98, 38.1))
    d.rail('+12V', 'D31.C')
    d.down('D30', 220.98, 48.26, 'C')
    d.route((220.98, 38.1), 'D30.C')
    d.ground('D30.A')
    d.chip('IC11', 'AN656N', 3, 165.1, 15.24, ref_at=(168.91, 15.24), hide_value=True, just='left')
    d.rail('+12V', 'IC11.8')
    d.ground('IC11.4')
    d.chip('IC12', '4066N', 3, 185.42, 78.74, ref_at=(177.8, 71.12), val_at=(185.42, 87.63), hide_value=False)
    d.route((170.18, 76.2), 'IC12.8')
    d.chip('IC12', '4066N', 4, 220.98, 78.74, 180, ref_at=(228.6, 71.12), hide_value=True)
    d.route('IC12.9', (203.2, 76.2), (203.2, 81.28), 'IC12.10')
    d.down('C35', 203.2, 88.9, '1')
    d.route((203.2, 81.28), 'C35.1')
    d.ground('C35.2')
    d.route((243.84, 38.1), (243.84, 81.28), 'IC12.11')

    d.transistor('Q30', 170.18, 109.22, 'NPN', flip=True)
    d.route('IC12.6', (167.64, 81.28), 'Q30.2')
    d.ground('Q30.3')
    d.across('R93', 157.48, 88.9, '1')
    d.route('R93.2', (167.64, 88.9))
    d.rail('+12V', 'R93.1', 'T')
    d.across('R91', 187.96, 109.22, '2')
    d.route('Q30.1', 'R91.2')
    d.route('R91.1', (195.58, 109.22), (195.58, 99.06), (238.76, 99.06))
    d.route('IC12.12', (238.76, 76.2), (238.76, 104.14))
    d.transistor('Q29', 236.22, 109.22, 'NPN')
    d.route((238.76, 104.14), 'Q29.2')
    d.ground('Q29.3')
    d.across('R92', 251.46, 99.06, '1')
    d.route((238.76, 99.06), 'R92.1')
    d.rail('+12V', 'R92.2', 'R')
    d.across('R59', 215.9, 109.22, '1')
    d.route('R59.2', 'Q29.1')
    d.out('R59.1', 'SLIDE', 'L', 2.54)
    d.down('R60', 226.06, 116.84, '2')
    d.route((226.06, 109.22), 'R60.2')
    d.ground('R60.1')

    # The exponential converter.
    d.pair('Q26', 307.34, 73.66)
    d.rail('+5.333V', 'Q26.1', 'T')
    d.chip('IC11', 'AN656N', 1, 292.1, 104.14, ref_at=(295.91, 96.52), hide_value=True)
    d.rail('+5.333V', 'IC11.3', 'T')
    d.down('R104', 307.34, 88.9, '1')
    d.route('Q26.3', 'R104.1')
    d.route('R104.2', (307.34, 104.14), 'IC11.1')
    d.route('Q26.2', (299.72, 60.96), (279.4, 60.96), (279.4, 106.68), 'IC11.2')
    d.across('C34', 292.1, 114.3, '2')
    d.route((279.4, 106.68), (279.4, 114.3), 'C34.2')
    d.route('C34.1', (302.26, 114.3), (302.26, 104.14))
    d.down('R102', 279.4, 50.8, '2')
    d.route('R102.1', (279.4, 60.96))
    d.trim('TM4', 279.4, 38.1)
    d.route('TM4.2', 'R102.2')
    d.rail('+5.333V', 'TM4.3', 'T')
    d.rail('+12V', 'TM4.1', 'T')
    d.down('R103', 261.62, 50.8, '1')
    d.route('R103.2', (261.62, 60.96), (279.4, 60.96))
    d.rail('+12V', 'R103.1')
    d.trim('TM5', 322.58, 45.72, value_dx=-5.08)
    d.route((243.84, 38.1), (243.84, 20.32), (312.42, 20.32), (312.42, 53.34), 'TM5.2')
    d.route((312.42, 45.72), 'TM5.3')

    # Tuning: the note CV through TM5 and R106, and the tuning pot through R118, summed at Q26's other base.
    d.down('R106', 330.2, 55.88, '1')
    d.route('TM5.1', 'R106.1')
    d.route('R106.2', (330.2, 73.66))
    d.route('Q26.5', (340.36, 73.66))
    d.down('R118', 340.36, 55.88, '1')
    d.route('R118.2', (340.36, 73.66))
    d.pot('VR2', 355.6, 45.72, wiper_left=True)
    d.route('R118.1', (340.36, 45.72), 'VR2.2')
    d.rail('+5.333V', 'VR2.3')
    d.ground('VR2.1')
    d.route('VR2.M1', (363.22, 48.26))
    d.ground((363.22, 48.26))
    d.caption('TUNING', 366.0, 40.64)
    d.down('R100B0', 330.2, 81.28, '2', left_text=True, hide_value=True)
    d.down('R100A0', 340.36, 81.28, '1', hide_value=True)
    d.note('R100A0, R100B0: THERMISTOR-7,5', 312.42, 99.06)
    d.route((330.2, 73.66), 'R100B0.2')
    d.route((340.36, 73.66), 'R100A0.1')
    d.route('R100B0.1', (330.2, 88.9), (340.36, 88.9), 'R100A0.2')
    d.rail('+5.333V', (335.28, 88.9), 'B')

    # The saw core: Q26 pulls C33 down until the Q25 and Q27 latch fires and resets it.
    d.route('Q26.4', (314.96, 63.5), (350.52, 63.5), (350.52, 124.46))
    d.transistor('Q27', 378.46, 88.9, 'PNP')
    d.rail('+12V', 'Q27.3')
    d.down('D25', 381, 101.6, 'A')
    d.route('Q27.2', 'D25.A')
    d.transistor('Q24', 378.46, 116.84, 'NPN', text=(370.84, 'right'))
    d.route('D25.C', (381, 109.22), 'Q24.2')
    d.route('Q24.1', (373.38, 111.76), 'Q24.2')
    d.transistor('Q25', 363.22, 109.22, 'NPN', flip=True, text=(362.0, 'left', -8.89))
    d.route('Q25.1', (381, 109.22))
    d.route('Q25.2', (360.68, 88.9), 'Q27.1')
    d.route('Q25.3', (360.68, 124.46), (350.52, 124.46))
    d.down('C33', 355.6, 132.08, '1')
    d.route((355.6, 124.46), 'C33.1')
    d.ground('C33.2')
    d.down('R101', 381, 129.54, '1')
    d.route('Q24.3', 'R101.1')
    d.rail('+5.333V', 'R101.2', 'B')
    d.transistor('Q28', 345.44, 124.46, 'JFET', flip=True, text=(340.36, 'right'))
    d.route('Q28.2', (350.52, 124.46))
    d.rail('+12V', 'Q28.1')
    d.down('R105', 342.9, 139.7, '2')
    d.route('Q28.3', 'R105.2')
    d.ground('R105.1')

    # The saw to the waveform switch, directly and through the square shaper.
    d.route((342.9, 132.08), (330.2, 132.08), (330.2, 175.26), (271.78, 175.26), (271.78, 165.1))
    d.across('R35', 317.5, 147.32, '2')
    d.across('C10', 317.5, 157.48, '2')
    d.route((330.2, 147.32), 'R35.1')
    d.route((330.2, 157.48), 'C10.1')
    d.down('R34', 307.34, 152.4, '1', left_text=False)
    d.route('R35.2', 'R34.1')
    d.route('C10.2', 'R34.2')
    d.transistor('Q8', 297.18, 147.32, 'PNP', flip=True)
    d.route('Q8.1', 'R34.1')
    d.down('R45', 294.64, 132.08, '1')
    d.rail('+12V', 'R45.1')
    d.route('R45.2', 'Q8.3')
    d.down('C11', 276.86, 142.24, '+')
    d.route('C11.+', (294.64, 137.16))
    d.ground('C11.-')
    d.down('R36', 294.64, 162.56, '1')
    d.route('Q8.2', 'R36.1')
    d.rail('+5.333V', 'R36.2', 'B')
    d.chip('S1', "SWITCH_GND''", 1, 262.89, 160.02, 180, ref_at=(254.0, 158.75), hide_value=True)
    d.route((294.64, 154.94), 'S1.3')
    d.route((271.78, 165.1), 'S1.1')
    d.out('S1.2', 'N$126', 'R', 2.54)
    d.route('S1.M3', 'S1.M4', (257.81, 147.32), (257.81, 172.72), 'S1.M2', 'S1.M1')
    d.route((257.81, 172.72), (257.81, 175.26))
    d.ground((257.81, 175.26))
    d.caption('WAVEFORM', 251.46, 142.24)

    # The supply entry from the I/O board, and the CV and gate going back to it.
    d.chip('J4', "MA03-''", 1, 203.2, 160.02, ref_at=(200.66, 152.4), hide_value=True)
    d.rail('+12V', 'J4.3', 'R')
    d.ground('J4.2', 'R')
    d.rail('+5.333V', 'J4.1', 'R')
    d.down('C32', 175.26, 160.02, '+')
    d.rail('+12V', 'C32.+')
    d.ground('C32.-')
    d.route('C32.+', (172.72, 154.94))
    d.flag((172.72, 154.94))
    d.route('C32.-', (172.72, 165.1))
    d.flag((172.72, 165.1))
    d.down('C31', 187.96, 160.02, '+')
    d.rail('+5.333V', 'C31.+')
    d.ground('C31.-')
    d.route('C31.+', (185.42, 154.94))
    d.flag((185.42, 154.94))
    d.note('supply from the I/O board', 175.26, 142.24)
    d.chip('J6', "MA03-''", 1, 271.78, 25.4, 180, ref_at=(275.59, 19.05), hide_value=True)
    d.route('J6.1', (261.62, 22.86), (261.62, 20.32))
    d.ground('J6.2', 'L')
    d.out('J6.3', 'N$622', 'L', 2.54)
    d.note('CV and gate to the I/O board', 250.0, 12.7)

    # Q26 as a SOT-363 chip, in the free corner of the sheet. The original's holes stay on the board.
    d.block('SMD pair for Q26', 297.18, 182.88, 396.24, 233.68)
    d.sot('Q126', 347.98, 208.28)
    d.alt_out('Q126.5', 'N$99', 'L')
    d.alt_out('Q126.3', 'N$113', 'T')
    d.alt_out('Q126.1', 'N$101', 'B')
    d.alt_out('Q126.6', 'N$98', 'T')
    d.rail('+5.333V', 'Q126.2', 'R')
    d.note('Fit Q126 or Q26, never both', 299.72, 229.87)

    # Q28 as an SC-59 chip, beside that frame. The original's holes stay on the board.
    d.block('SMD JFET for Q28', 238.76, 182.88, 292.1, 233.68)
    d.sc59('Q128', 261.62, 208.28)
    d.alt_out('Q128.3', 'N$113', 'L')
    d.rail('+12V', 'Q128.2')
    d.alt_out('Q128.1', 'N$108', 'B')
    d.note('Fit Q128 or Q28, never both', 241.3, 229.87)


def draw_vcf(d):
    d.dx, d.dy = 38.1, 15.24
    d.block('Diode ladder', 17.78, 20.32, 124.46, 151.13)
    d.block('Output amplifier and resonance', 125.73, 20.32, 300.99, 142.24)
    d.block('Exponential converter', 40.64, 152.4, 224.79, 215.9)
    d.block('Accent sweep', 226.06, 160.02, 317.5, 203.2)

    # The filtered +12 V rail along the top, from R95 at the right to R115 at the left.
    d.route((68.58, 30.48), (226.06, 30.48))
    d.across('R95', 231.14, 30.48, '1')
    d.route('R95.1', (226.06, 30.48))
    d.rail('+12V', 'R95.2', 'R')
    d.down('C28', 213.36, 38.1, '+')
    d.route('C28.+', (213.36, 30.48))
    d.ground('C28.-')

    # Q22 on top of the ladder, with its bases held by R115 and C30.
    d.pair('Q22', 96.52, 40.64, shape='CB')
    d.route('Q22.2', (88.9, 30.48))
    d.route('Q22.4', (104.14, 30.48))
    d.down('R115', 68.58, 38.1, '1')
    d.route('R115.1', (68.58, 30.48))
    d.down('C30', 68.58, 58.42, '+')
    d.route('R115.2', (68.58, 50.8), 'C30.+')
    d.route('Q22.3', (96.52, 50.8), (68.58, 50.8))
    d.ground('C30.-')

    # The ladder: two columns of diode-connected transistors, with the capacitors between them.
    for left, right, y in (('Q16', 'Q23', 71.12), ('Q14', 'Q17', 86.36), ('Q13', 'Q15', 101.6)):
        d.transistor(left, 86.36, y, 'NPN', text=(78.74, 'right'))
        d.route(f'{left}.1', (81.28, y - 5.08), f'{left}.2')
        d.transistor(right, 106.68, y, 'NPN', flip=True, text=(114.3, 'left'))
        d.route(f'{right}.1', (111.76, y - 5.08), f'{right}.2')
    d.across('C26', 96.52, 63.5, '1')
    d.across('C24', 96.52, 78.74, '1')
    d.across('C19', 96.52, 93.98, '1')
    d.across('C18', 96.52, 109.22, '2')
    d.route('Q22.1', (88.9, 53.34), (88.9, 63.5), 'Q16.2')
    d.route('Q22.5', (104.14, 63.5), 'Q23.2')
    d.route('Q16.3', (88.9, 78.74), 'Q14.2')
    d.route('Q23.3', (104.14, 78.74), 'Q17.2')
    d.route('Q14.3', (88.9, 93.98), 'Q13.2')
    d.route('Q17.3', (104.14, 93.98), 'Q15.2')
    d.route((88.9, 63.5), 'C26.1')
    d.route('C26.2', (104.14, 63.5))
    d.route((88.9, 78.74), 'C24.1')
    d.route('C24.2', (104.14, 78.74))
    d.route((88.9, 93.98), 'C19.1')
    d.route('C19.2', (104.14, 93.98))
    d.pair('Q12', 96.52, 119.38)
    d.route('Q13.3', (88.9, 109.22), 'Q12.2')
    d.route('Q15.3', (104.14, 109.22), 'Q12.4')
    d.route((88.9, 109.22), 'C18.2')
    d.route('C18.1', (104.14, 109.22))

    # The input, and the bias of Q12's two bases.
    d.label('N$126', (25.4, 119.38), 'L')
    d.note('from the waveform switch S1', 20.32, 114.3)
    d.across('R62', 38.1, 119.38, '1')
    d.across('C17', 58.42, 119.38, '+')
    d.route((25.4, 119.38), 'R62.1')
    d.route('R62.2', 'C17.+')
    d.route('C17.-', (71.12, 119.38), 'Q12.1')
    d.down('R70', 71.12, 127, '1')
    d.route((71.12, 119.38), 'R70.1')
    d.down('R98', 111.76, 127, '1')
    d.route('Q12.5', 'R98.1')
    d.route((58.42, 134.62), (111.76, 134.62))
    d.route('R70.2', (71.12, 134.62))
    d.route('R98.2', (111.76, 134.62))
    d.down('C16', 58.42, 142.24, '+')
    d.route((58.42, 134.62), 'C16.+')
    d.ground('C16.-')
    d.across('R68', 45.72, 134.62, '1')
    d.route('R68.2', (58.42, 134.62))
    d.rail('+5.333V', 'R68.1', 'L')

    # The ladder's current comes in through Q12's emitter, from the exponential converter below.
    d.down('R69', 96.52, 142.24, '1')
    d.route('Q12.3', 'R69.1')

    # Q21, with its inputs AC-coupled from the top of the ladder.
    d.pair('Q21', 162.56, 63.5, flip=True)
    d.across('C27', 134.62, 63.5, '1')
    d.route((104.14, 63.5), 'C27.1')
    d.route('C27.2', 'Q21.5')
    d.down('C25', 177.8, 58.42, '1')
    d.route((88.9, 53.34), 'C25.1')
    d.route('C25.2', 'Q21.1')
    d.down('R111', 154.94, 40.64, '1')
    d.route('R111.1', (154.94, 30.48))
    d.route('R111.2', 'Q21.4')
    d.down('R110', 170.18, 40.64, '2')
    d.route('R110.2', (170.18, 30.48))
    d.route('R110.1', (170.18, 48.26), 'Q21.2')

    # Q21's input bias and its tail current, Q20.
    d.down('R113', 147.32, 71.12, '1', left_text=True)
    d.route('Q21.5', 'R113.1')
    d.down('R114', 177.8, 71.12, '2')
    d.route('Q21.1', 'R114.2')
    d.route('R113.2', (147.32, 78.74), (177.8, 78.74), 'R114.1')
    d.across('R116', 137.16, 78.74, '2')
    d.route('R116.1', (147.32, 78.74))
    d.rail('+5.333V', 'R116.2')
    d.down('C29', 177.8, 86.36, '+')
    d.route((177.8, 78.74), 'C29.+')
    d.ground('C29.-')
    d.down('R112', 147.32, 83.82, '1', left_text=True)
    d.down('R109', 147.32, 96.52, '1', left_text=True)
    d.route('R112.2', 'R109.1')
    d.ground('R109.2')
    d.transistor('Q20', 160.02, 88.9, 'NPN')
    d.route('R112.2', 'Q20.1')
    d.route('Q21.3', 'Q20.2')
    d.down('R108', 162.56, 101.6, '2')
    d.route('Q20.3', 'R108.2')
    d.ground('R108.1')

    # Q19 follows Q21's output and drives the resonance pot through C14.
    d.transistor('Q19', 198.12, 48.26, 'NPN')
    d.route((170.18, 48.26), 'Q19.1')
    d.route('Q19.2', (200.66, 30.48))
    d.down('R96', 200.66, 66.04, '2')
    d.route('Q19.3', (200.66, 58.42), 'R96.2')
    d.ground('R96.1')
    d.across('C14', 215.9, 58.42, '+')
    d.route((200.66, 58.42), 'C14.+')
    d.pot_dual('VR4', 1, 236.22, 66.04)
    d.route('C14.-', 'VR4.3A')
    d.route('VR4.3A', (254, 58.42))
    d.label('N$27', (254, 58.42))
    d.note('to C21 and the VCA', 267.97, 58.42)
    d.ground('VR4.1A')
    d.route('VR4.2A', (248.92, 66.04), (254, 66.04))
    d.label('N$26', (254, 66.04))
    d.note('to C20 and the VCA', 267.97, 66.04)
    d.caption('RESONANCE', 208.28, 78.74)

    # Resonance feedback: from the pot's wiper through Q18 and back to Q12's right base.
    d.across('C15', 233.68, 109.22, '+')
    d.route('C15.-', (248.92, 109.22), (248.92, 66.04))
    d.across('R67', 213.36, 109.22, '2')
    d.route('R67.1', 'C15.+')
    d.transistor('Q18', 190.5, 109.22, 'NPN', flip=True)
    d.route('Q18.2', (187.96, 30.48))
    d.route('Q18.1', (200.66, 109.22), 'R67.2')
    d.down('R99', 200.66, 116.84, '2')
    d.route((200.66, 109.22), 'R99.2')
    d.down('C22', 200.66, 132.08, '+')
    d.route('R99.1', (200.66, 124.46), 'C22.+')
    d.ground('C22.-')
    d.across('R66', 213.36, 124.46, '1')
    d.route((200.66, 124.46), 'R66.1')
    d.rail('+5.333V', 'R66.2', 'R')
    d.down('R94', 187.96, 127, '2')
    d.route('Q18.3', (187.96, 119.38), 'R94.2')
    d.ground('R94.1')
    d.across('C23', 165.1, 119.38, '+')
    d.route('C23.-', (187.96, 119.38))
    d.across('R97', 134.62, 119.38, '1')
    d.route('Q12.5', 'R97.1')
    d.route('R97.2', 'C23.+')

    # The exponential converter.
    d.transistor('Q11', 99.06, 157.48, 'NPN', flip=True)
    d.route('R69.2', 'Q11.2')
    d.transistor('Q10', 119.38, 170.18, 'PNP', flip=True)
    d.route('Q11.1', (116.84, 157.48))
    d.route('Q10.3', (116.84, 157.48))
    d.across('R73', 129.54, 157.48, '1')
    d.route((116.84, 157.48), 'R73.1')
    d.trim('TM3', 152.4, 157.48)
    d.route('R73.2', (139.7, 157.48), 'TM3.3')
    d.route((139.7, 157.48), (139.7, 165.1), 'TM3.2')
    d.pot('VR3', 208.28, 167.64, wiper_left=True)
    d.route('TM3.1', (200.66, 157.48), 'VR3.2')
    d.rail('+12V', 'VR3.3')
    d.route('VR3.M1', (215.9, 170.18))
    d.ground((215.9, 170.18))
    d.transistor('Q9', 68.58, 198.12, 'PNP')
    d.route('Q9.3', (71.12, 190.5))
    d.route((71.12, 190.5), (142.24, 190.5))
    d.route('Q11.3', (96.52, 190.5))
    d.route('Q10.2', (116.84, 190.5))
    d.ground('Q9.2')
    d.down('R65', 58.42, 190.5, '2')
    d.rail('+5.333V', 'R65.2')
    d.down('R64', 58.42, 205.74, '1')
    d.route('R65.1', (58.42, 198.12), 'Q9.1')
    d.route((58.42, 198.12), 'R64.1')
    d.ground('R64.2')
    d.down('R71', 129.54, 180.34, '2')
    d.route('Q10.1', (129.54, 170.18), 'R71.2')
    d.route('R71.1', (129.54, 190.5))

    # What moves the cutoff: Cutoff pot VR3 and Env Mod pot VR5 into the summing node, and the accent sweep.
    d.across('R63', 147.32, 170.18, '1')
    d.route((129.54, 170.18), (139.7, 170.18), 'R63.1')
    d.across('R72', 147.32, 182.88, '1')
    d.route((139.7, 170.18), (139.7, 182.88), 'R72.1')
    d.across('R61', 147.32, 190.5, '2')
    d.route((142.24, 190.5), 'R61.2')
    d.pot('VR5', 172.72, 170.18, wiper_left=True)
    d.route('R63.2', 'VR5.2')
    d.route('R61.1', (172.72, 190.5), 'VR5.1')
    d.route('VR5.M1', (180.34, 172.72))
    d.ground((180.34, 172.72))
    d.route('VR5.3', (177.8, 162.56))
    d.label('N$53', (177.8, 162.56))
    d.note('from MEG', 188.5, 162.56)
    d.caption('ENV. MOD', 153.67, 186.69)
    d.across('R47', 165.1, 198.12, '2')
    d.route((139.7, 190.5), (139.7, 198.12), 'R47.2')
    d.route('R47.1', (208.28, 198.12), 'VR3.1')
    d.caption('CUTOFF FREQ.', 186.69, 177.8)

    # The accent sweep.
    d.pot_dual('VR4', 2, 238.76, 182.88, wiper_left=True)
    d.route('R72.2', 'VR4.2B')
    d.down('C13', 254, 177.8, '+')
    d.route('VR4.3B', (238.76, 170.18), (254, 170.18), 'C13.+')
    d.ground('C13.-')
    d.across('R46', 254, 190.5, '2')
    d.route('VR4.1B', 'R46.2')
    d.across('D24', 271.78, 190.5, 'C')
    d.route('R46.1', 'D24.C')
    d.route('D24.A', (284.48, 190.5))
    d.label('N$35', (284.48, 190.5))
    d.note('accent line, from R119 and VR7', 263.08, 196.85)

    # Q22, Q12 and Q21 as SOT-363 chips. The originals' holes stay on the board.
    d.block('SMD pairs', 304.8, 5.08, 370.84, 147.32)
    d.sot('Q122', 337.82, 35.56, shape='CB')
    d.alt_out('Q122.3', 'N$122', 'T')
    d.alt_out('Q122.6', 'N$122', 'T')
    d.alt_out('Q122.4', 'N$143', 'B')
    d.alt_out('Q122.2', 'N$115', 'B')
    d.alt_out('Q122.1', 'N$120', 'B')
    d.sot('Q112', 337.82, 81.28)
    d.alt_out('Q112.5', 'N$124', 'L')
    d.alt_out('Q112.3', 'N$118', 'T')
    d.alt_out('Q112.1', 'N$127', 'B')
    d.alt_out('Q112.6', 'N$121', 'T')
    d.alt_out('Q112.2', 'N$60', 'R')
    d.sot('Q121', 337.82, 124.46)
    d.alt_out('Q121.5', 'N$138', 'L')
    d.alt_out('Q121.3', 'N$140', 'T')
    d.alt_out('Q121.1', 'N$139', 'B')
    d.alt_out('Q121.6', 'N$148', 'T')
    d.alt_out('Q121.2', 'N$141', 'R')
    d.note('Fit each chip or the SIP part it replaces, never both', 307.34, 143.51)


def draw_vca(d):
    d.dx, d.dy = 22.86, 7.62
    d.block('VCA', 30.48, 12.7, 300.0, 158.75)
    d.note('the envelope, turned into a current', 53.34, 20.32)

    # The current mirrors into the VCA's control pin, as on the original sheet.
    d.transistor('Q2', 121.92, 45.72, 'PNP', flip=True)
    d.transistor('Q1', 134.62, 45.72, 'PNP')
    d.route('Q2.1', 'Q1.1')
    d.rail('+12V', 'Q2.3')
    d.rail('+12V', 'Q1.3')
    d.route('Q2.2', (119.38, 53.34), (127, 53.34), 'Q2.1')
    d.transistor('Q4', 121.92, 68.58, 'NPN', flip=True)
    d.transistor('Q3', 134.62, 68.58, 'NPN')
    d.route('Q4.1', 'Q3.1')
    d.route((119.38, 53.34), 'Q4.2')
    d.ground('Q4.3')
    d.ground('Q3.3')
    d.route((128.27, 68.58), (128.27, 60.96), (137.16, 60.96), 'Q3.2')
    d.route('Q1.2', (149.86, 50.8), (149.86, 35.56), (198.12, 35.56))

    # The VCA itself: the BA6110, with the optional BA662 position below it, sharing its inputs and outputs.
    d.chip('IC15B0', "BA611''", 1, 200.66, 50.8, ref_at=(198.12, 66.04), val_at=(198.12, 68.58))
    d.route((198.12, 35.56), 'IC15B0.4')
    d.route('IC15B0.3', (203.2, 38.1), (208.28, 38.1), (208.28, 40.64))
    d.ground((208.28, 40.64))
    d.rail('+12V', 'IC15B0.9')
    d.ground('IC15B0.5')
    d.route('IC15B0.6', 'IC15B0.7')
    d.chip('IC15A0', "BA662''", 1, 200.66, 124.46, ref_at=(200.66, 139.7), hide_value=True)
    d.rail('+12V', 'IC15A0.4')
    d.rail('+12V', 'IC15A0.9')
    d.ground('IC15A0.5')
    d.route('IC15A0.6', 'IC15A0.7')
    d.note('optional, not fitted', 210.82, 139.7)
    d.route('IC15B0.1', (180.34, 48.26), (180.34, 144.78))
    d.route('IC15A0.3', (180.34, 127))
    d.route('IC15B0.2', (175.26, 53.34), (175.26, 121.92), 'IC15A0.2')
    d.route((214.63, 50.8), (214.63, 124.46))
    d.route('IC15B0.8', (261.62, 50.8))
    d.route((254, 50.8), (254, 124.46), 'IC15A0.8')
    d.across('C38', 266.7, 50.8, '+')
    d.out('C38.-', 'N$32', 'R', 2.54)
    d.note('to VOLUME', 285.0, 50.8)

    # The feedback that sets the output's DC level.
    d.across('R128', 228.6, 73.66, '2')
    d.route((214.63, 73.66), 'R128.2')
    d.across('R127', 228.6, 83.82, '1')
    d.route((214.63, 83.82), 'R127.1')
    d.down('R129', 238.76, 78.74, '2')
    d.route('R128.1', 'R129.2')
    d.route('R127.2', 'R129.1')
    d.across('R162', 228.6, 63.5, '1')
    d.rail('+5.333V', 'R162.1', 'T')
    d.route('R162.2', (238.76, 63.5), 'R129.2')
    d.down('C40', 248.92, 71.12, '+', left_text=True)
    d.route((238.76, 63.5), (248.92, 63.5), (248.92, 66.04))
    d.ground('C40.-')

    # N$69 also goes to the BA662's control pin.
    d.route((137.16, 60.96), (170.18, 60.96), (170.18, 111.76), (198.12, 111.76), 'IC15A0.1')

    # Accent adds to the VCA's current through D27.
    d.down('D27', 152.4, 68.58, 'C', left_text=False)
    d.route((152.4, 60.96), 'D27.C')
    d.down('R120', 152.4, 81.28, '1')
    d.route('D27.A', 'R120.1')
    d.route('R120.2', (152.4, 88.9))
    d.down('C36', 152.4, 96.52, '1')
    d.route((152.4, 88.9), 'C36.1')
    d.ground('C36.2')
    d.across('R119', 139.7, 88.9, '2')
    d.route('R119.1', (152.4, 88.9))
    d.out('R119.2', 'N$35', 'L', 2.54)

    # The input bias, and the filter's two outputs through C20, C21, R121 and R122.
    d.across('R125', 160.02, 109.22, '1')
    d.route('R125.2', (175.26, 109.22))
    d.across('R124', 160.02, 119.38, '2')
    d.route('R124.1', (180.34, 119.38))
    d.route('R125.1', (154.94, 114.3), 'R124.2')
    d.down('C37', 147.32, 121.92, '+')
    d.route((154.94, 114.3), (147.32, 114.3), 'C37.+')
    d.ground('C37.-')
    d.across('R126', 134.62, 114.3, '1')
    d.route('R126.2', (147.32, 114.3))
    d.rail('+5.333V', 'R126.1', 'L')
    d.across('R121', 167.64, 134.62, '1')
    d.route('R121.2', (180.34, 134.62))
    d.across('C21', 152.4, 134.62, '2')
    d.route('C21.1', 'R121.1')
    d.out('C21.2', 'N$27', 'L', 2.54)
    d.across('R122', 167.64, 144.78, '2')
    d.route('R122.1', (180.34, 144.78))
    d.across('C20', 152.4, 144.78, '2')
    d.route('C20.1', 'R122.2')
    d.out('C20.2', 'N$26', 'L', 2.54)
    d.note('from the VCF', 120.0, 139.7)

    # The envelope turned into the current for Q3: Q31 and Q32.
    d.transistor('Q31', 101.6, 55.88, 'PNP')
    d.route('Q31.2', (104.14, 60.96), (128.27, 60.96))
    d.down('R131', 104.14, 40.64, '2')
    d.route('R131.1', 'Q31.3')
    d.across('R133', 91.44, 27.94, '2')
    d.route('R131.2', (104.14, 27.94), 'R133.1')
    d.out('R133.2', 'N$63', 'L', 2.54)
    d.route('Q31.1', (81.28, 55.88))
    d.down('R123', 91.44, 45.72, '2')
    d.route('R123.1', (91.44, 55.88))
    d.rail('+12V', 'R123.2')
    d.down('C42', 81.28, 63.5, '+')
    d.route((81.28, 55.88), 'C42.+')
    d.ground('C42.-')
    d.down('R132', 91.44, 63.5, '1')
    d.route((91.44, 55.88), 'R132.1')
    d.transistor('Q32', 88.9, 73.66, 'NPN')
    d.route('R132.2', 'Q32.2')
    d.down('R130', 91.44, 86.36, '1')
    d.route('Q32.3', 'R130.1')
    d.ground('R130.2')
    d.across('R134', 66.04, 73.66, '1')
    d.route('R134.2', 'Q32.1')
    d.out('R134.1', 'N$64', 'L', 2.54)
    d.down('C41', 76.2, 81.28, '1')
    d.route((76.2, 73.66), 'C41.1')
    d.ground('C41.2')


def draw_env(d):
    d.dx, d.dy = 12.7, 15.24
    d.block('ENV', 12.7, 10.16, 310.0, 180.0)

    # The gate turns on Q37, Q36 and the VCA envelope.
    d.label('GATE', (33.02, 71.12), 'L')
    d.across('R146', 45.72, 71.12, '2')
    d.route((33.02, 71.12), 'R146.2')
    d.down('R144', 53.34, 78.74, '1')
    d.transistor('Q37', 63.5, 71.12, 'NPN')
    d.route('R146.1', 'Q37.1')
    d.route((53.34, 71.12), 'R144.1')
    d.ground('R144.2')
    d.ground('Q37.3')
    d.down('R143', 66.04, 55.88, '2')
    d.route('R143.1', 'Q37.2')
    d.down('R142', 66.04, 35.56, '2')
    d.route('R142.1', (66.04, 45.72), 'R143.2')
    d.down('C72', 53.34, 35.56, '+', left_text=True)
    d.route('C72.+', (53.34, 27.94), (66.04, 27.94), 'R142.2')
    d.rail('+12V', (66.04, 27.94))
    d.route('C72.-', (53.34, 45.72), (66.04, 45.72))
    d.transistor('Q36', 81.28, 45.72, 'PNP')
    d.route((66.04, 45.72), 'Q36.1')
    d.rail('+12V', 'Q36.3')
    d.down('R145', 83.82, 60.96, '2')
    d.route('Q36.2', 'R145.2')
    d.ground('R145.1')
    d.route((83.82, 53.34), (96.52, 53.34), (96.52, 43.18))
    d.across('D34', 101.6, 43.18, 'A')
    d.across('D35', 101.6, 53.34, 'A')
    d.across('R137', 119.38, 43.18, '1')
    d.route('D34.C', 'R137.1')
    d.out('R137.2', 'N$622', 'R', 2.54)
    d.note('gate out, to J6', 142.24, 43.18)
    d.out('D35.C', 'N$63', 'R', 2.54)
    d.note('to the VCA', 124.46, 53.34)

    # The gate's edge through C54 and Q38 starts the main envelope.
    d.route((66.04, 63.5), (78.74, 63.5), (78.74, 88.9))
    d.across('C54', 86.36, 88.9, '2')
    d.route((78.74, 88.9), 'C54.2')
    d.across('R148', 101.6, 88.9, '1')
    d.route('C54.1', 'R148.1')
    d.down('R149', 111.76, 78.74, '2')
    d.route('R148.2', (111.76, 88.9), 'R149.1')
    d.rail('+12V', 'R149.2')
    d.transistor('Q38', 119.38, 88.9, 'PNP')
    d.route((111.76, 88.9), 'Q38.1')
    d.down('R150', 121.92, 73.66, '1')
    d.rail('+12V', 'R150.1')
    d.route('R150.2', 'Q38.3')
    d.down('C55', 139.7, 86.36, '+')
    d.route((121.92, 81.28), 'C55.+')
    d.ground('C55.-')
    d.down('R151', 121.92, 109.22, '2', left_text=True)
    d.route('Q38.2', 'R151.2')
    d.ground('R151.1')
    d.route((121.92, 101.6), (137.16, 101.6), (137.16, 96.52))
    d.across('D36', 147.32, 96.52, 'A')
    d.route((137.16, 96.52), 'D36.A')
    d.out('D36.C', 'N$64', 'R', 2.54)
    d.across('D37', 147.32, 106.68, 'A')
    d.route((137.16, 101.6), (137.16, 106.68), 'D37.A')
    d.across('R152', 162.56, 106.68, '2')
    d.route('D37.C', 'R152.2')

    # C62 holds the main envelope: Q40 and Q41 follow it onto N$53, and R138 and the Decay pot discharge it.
    d.down('C62', 170.18, 114.3, '+')
    d.route('R152.1', (170.18, 106.68), 'C62.+')
    d.ground('C62.-')
    d.down('R138', 170.18, 96.52, '1', left_text=True)
    d.route('R138.2', (170.18, 106.68))
    d.transistor('Q40', 180.34, 106.68, 'NPN')
    d.route((170.18, 106.68), 'Q40.1')
    d.rail('+12V', 'Q40.2')
    d.transistor('Q41', 198.12, 116.84, 'NPN')
    d.route('Q40.3', (182.88, 116.84), 'Q41.1')
    d.rail('+12V', 'Q41.2')
    d.route('Q41.3', (200.66, 124.46))
    d.transistor('Q39', 198.12, 134.62, 'JFET')
    d.route((200.66, 124.46), 'Q39.1')
    d.route('Q39.2', (193.04, 139.7), 'Q39.3')
    d.ground('Q39.3')
    d.chip('IC12', '4066N', 2, 200.66, 88.9, 180, ref_at=(193.04, 81.28), hide_value=True)
    d.route('R138.1', 'IC12.3')
    d.pot_dual('VR6', 2, 180.34, 76.2, wiper_left=True)
    d.route('VR6.1B', (180.34, 91.44))
    d.route('VR6.2B', (172.72, 68.58), 'VR6.3B')
    d.route('VR6.3B', (180.34, 63.5), (233.68, 63.5))
    d.caption('ENV. DECAY', 148.0, 76.2)
    d.route((220.98, 63.5), (220.98, 91.44), 'IC12.4')
    d.down('D28', 233.68, 71.12, 'A')
    d.route((233.68, 63.5), 'D28.A')
    d.down('D29', 233.68, 83.82, 'A')
    d.route('D28.C', 'D29.A')
    d.down('D26', 233.68, 99.06, 'A')
    d.route('D29.C', (233.68, 91.44), 'D26.A')
    d.ground('D26.C')
    d.across('R117', 246.38, 91.44, '2')
    d.route((233.68, 91.44), 'R117.2')
    d.rail('+5.333V', 'R117.1', 'R')

    # The other section of the Decay pot isn't used: all its pins go to ground.
    d.pot_dual('VR6', 1, 266.7, 45.72)
    d.route('VR6.3A', (276.86, 38.1), (276.86, 53.34), 'VR6.1A')
    d.route('VR6.2A', (276.86, 45.72))
    d.ground('VR6.1A')
    d.note('unused section', 254.0, 33.02)

    # IC12A switches N$53 to the Accent pot during accented notes, and IC12B shortens the decay.
    d.chip('IC12', '4066N', 1, 233.68, 127, ref_at=(226.06, 119.38), hide_value=True)
    d.route((200.66, 124.46), 'IC12.1')
    d.route((213.36, 124.46), (213.36, 116.84))
    d.label('N$53', (213.36, 116.84), 'T')
    d.note('to the VCF', 218.44, 111.76)
    d.pot('VR7', 264.16, 132.08)
    d.route('IC12.2', 'VR7.3')
    d.ground('VR7.1')
    d.route('VR7.M1', (256.54, 134.62))
    d.ground((256.54, 134.62))
    d.out('VR7.2', 'N$35', 'R', 2.54)
    d.caption('ACCENT', 266.7, 142.24)
    d.route('IC12.5', (215.9, 86.36), (215.9, 147.32))
    d.route((215.9, 129.54), 'IC12.13')
    d.transistor('Q35', 213.36, 152.4, 'NPN')
    d.route((215.9, 147.32), 'Q35.2')
    d.ground('Q35.3')
    d.across('R139', 228.6, 139.7, '1')
    d.route((215.9, 139.7), 'R139.1')
    d.rail('+12V', 'R139.2', 'R')
    d.down('R140', 203.2, 160.02, '1', left_text=True)
    d.route('Q35.1', (203.2, 152.4), 'R140.1')
    d.ground('R140.2')
    d.across('R141', 190.5, 152.4, '2')
    d.route('R141.1', (203.2, 152.4))
    d.out('R141.2', 'ACCENT', 'L', 2.54)

    d.chip('IC12', '4066N', 5, 287.02, 88.9, ref_at=(290.83, 88.9), hide_value=True, just='left')
    d.rail('+12V', 'IC12.14')
    d.ground('IC12.7')

    # Q39 as an SC-59 chip, below the frame. The original's holes stay on the board.
    d.block('SMD JFET for Q39', 198.12, 187.96, 264.16, 233.68)
    d.sc59('Q139', 228.6, 208.28)
    d.alt_out('Q139.2', 'N$53', 'T')
    d.route('Q139.3', (223.52, 213.36), 'Q139.1')
    d.ground('Q139.1')
    d.note('Fit Q139 or Q39, never both', 200.66, 229.87)


def draw_mixer(d):
    d.dx, d.dy = 25.4, 20.32
    d.block('MIXER', 15.24, 2.54, 190.5, 108.0)
    d.block('HEADPHONE', 116.84, 109.22, 276.86, 170.0)

    # Volume into the mixer, and the MIX IN jack's return through C58.
    d.pot('VR8', 40.64, 86.36)
    d.route('VR8.3', (40.64, 73.66))
    d.label('N$32', (40.64, 73.66), 'T')
    d.note('from the VCA', 43.18, 68.58)
    d.ground('VR8.1')
    d.route('VR8.M1', (33.02, 88.9))
    d.ground((33.02, 88.9))
    d.caption('VOLUME', 22.86, 76.2)
    d.across('C59', 55.88, 86.36, '-')
    d.route('VR8.2', 'C59.-')
    d.across('R155', 71.12, 86.36, '1')
    d.route('C59.+', 'R155.1')
    d.route('R155.2', (81.28, 86.36))
    d.across('C58', 55.88, 96.52, '-')
    d.across('R156', 71.12, 96.52, '2')
    d.route('C58.+', 'R156.2')
    d.route('R156.1', (81.28, 96.52), (81.28, 86.36))

    # The mixer's amplifier: Q34 and Q33 with R153 around them.
    d.transistor('Q34', 78.74, 53.34, 'NPN')
    d.route('Q34.3', (81.28, 86.36))
    d.down('C52', 63.5, 60.96, '+', left_text=True)
    d.route('Q34.1', (63.5, 53.34), 'C52.+')
    d.ground('C52.-')
    d.across('R157', 50.8, 53.34, '2')
    d.route('R157.1', (63.5, 53.34))
    d.rail('+5.333V', 'R157.2', 'L')
    d.route('Q34.2', (81.28, 43.18), (96.52, 43.18))
    d.down('R158', 96.52, 48.26, '1')
    d.transistor('Q33', 106.68, 53.34, 'PNP')
    d.route('R158.2', 'Q33.1')
    d.across('R154', 104.14, 38.1, '1')
    d.route((96.52, 43.18), (96.52, 38.1), 'R154.1')
    d.route('R154.2', (109.22, 38.1))
    d.route((109.22, 30.48), 'Q33.3')
    d.across('R136', 119.38, 30.48, '2')
    d.route((109.22, 30.48), 'R136.2')
    d.rail('+12V', 'R136.1', 'R')
    d.down('C53', 119.38, 45.72, '+')
    d.route((109.22, 38.1), (119.38, 38.1), 'C53.+')
    d.ground('C53.-')
    d.route('Q33.2', (109.22, 66.04))
    d.across('R153', 96.52, 66.04, '1')
    d.route((81.28, 66.04), 'R153.1')
    d.route('R153.2', (109.22, 66.04))
    d.down('R160', 109.22, 73.66, '2', left_text=True)
    d.route((109.22, 66.04), 'R160.2')
    d.ground('R160.1')

    # Out to the MIX OUT jack, and on to the headphone amplifier.
    d.across('R161', 124.46, 66.04, '2')
    d.route((109.22, 66.04), 'R161.2')
    d.across('C56', 144.78, 66.04, '+')
    d.route('R161.1', 'C56.+')
    d.down('R165', 154.94, 73.66, '1', left_text=True)
    d.route('C56.-', (154.94, 66.04), 'R165.1')
    d.ground('R165.2')
    d.chip('J7', "MA03-''", 1, 172.72, 68.58, 180, ref_at=(172.72, 60.96), hide_value=True)
    d.route((154.94, 66.04), 'J7.1')
    d.ground('J7.2', 'L')
    d.route('J7.3', (160.02, 71.12), (160.02, 106.68), (50.8, 106.68), 'C58.-')
    d.note('MIX OUT and MIX IN,', 162.56, 78.74)
    d.note('to the I/O board', 162.56, 81.28)

    # The headphone amplifier.
    d.route((114.3, 66.04), (114.3, 129.54))
    d.across('R159', 124.46, 129.54, '2')
    d.route((114.3, 129.54), 'R159.2')
    d.across('C51', 144.78, 129.54, '+')
    d.route('R159.1', 'C51.+')
    d.chip('IC14', "LA44140''", 1, 165.1, 132.08, ref_at=(153.67, 125.73), val_at=(186.69, 147.32))
    d.route('C51.-', 'IC14.2')
    d.route('IC14.3', (154.94, 134.62))
    d.down('C50', 154.94, 142.24, '+', left_text=True)
    d.route((154.94, 134.62), 'C50.+')
    d.down('R135', 154.94, 154.94, '2', left_text=True)
    d.route('C50.-', 'R135.2')
    d.ground('R135.1')
    d.route('IC14.1', (167.64, 147.32))
    d.across('C47', 172.72, 147.32, '2', flip_text=True)
    d.route('C47.1', (177.8, 147.32), 'IC14.4')
    d.ground('IC14.5')
    d.route('IC14.9', (167.64, 119.38), (157.48, 119.38))
    d.across('C48', 152.4, 119.38, '-')
    d.ground('C48.-', 'L')
    d.route('IC14.8', (172.72, 111.76), (200.66, 111.76))
    d.route('IC14.7', (177.8, 121.92), (195.58, 121.92))
    d.rail('+6V', (177.8, 121.92), 'T')
    d.down('C46', 190.5, 116.84, '2')
    d.route((190.5, 111.76), 'C46.2')
    d.down('D33', 195.58, 127, 'C', left_text=True)
    d.down('C44', 200.66, 119.38, '+')
    d.route((200.66, 111.76), 'C44.+')
    d.route('C44.-', (200.66, 132.08))
    d.route('IC14.6', (213.36, 132.08))
    d.across('C43', 218.44, 132.08, '+')
    d.down('D32', 195.58, 139.7, 'C', left_text=True)
    d.route((195.58, 132.08), 'D32.C')
    d.ground('D32.A')
    d.down('C45', 205.74, 139.7, '1')
    d.route((205.74, 132.08), 'C45.1')
    d.ground('C45.2')
    d.chip('J5', "MA03-''", 1, 238.76, 134.62, 180, ref_at=(238.76, 127), hide_value=True)
    d.route('C43.-', 'J5.1')
    d.ground('J5.2', 'L')
    d.route('J5.3', (231.14, 142.24))
    d.rail('+6V', (231.14, 142.24), 'B')
    d.route((231.14, 139.7), (228.6, 139.7))
    d.flag((228.6, 139.7))
    d.note('to the headphone jack,', 241.3, 142.24)
    d.note('on the I/O board', 241.3, 144.78)
    d.down('C49', 256.54, 124.46, '+')
    d.rail('+6V', 'C49.+')
    d.ground('C49.-')
