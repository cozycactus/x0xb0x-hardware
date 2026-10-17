# SPDX-License-Identifier: CC0-1.0
"""Refill every zone of a board with KiCad's own zone filler and save it to another file.

Run with KiCad's bundled Python:  refill_zones.py <in.kicad_pcb> <out.kicad_pcb>
"""
import sys

import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
assert pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(sys.argv[2], board)
