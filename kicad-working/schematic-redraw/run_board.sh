#!/bin/zsh
# Build a board's sheets into a scratch folder, render them and compare the nets. Usage: run_board.sh <mainboard|ioboard> <out dir> [lines]
H=${0:A:h}; B=$1; O=$2; cd $H; PYTHONDONTWRITEBYTECODE=1 python3 build.py $B $O 2>&1 | tail -30
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
$CLI sch export pdf -o $O/all.pdf $O/$B.kicad_sch 2>&1 | grep -v -E 'Fontconfig|Done|Plotted'
$CLI sch export netlist --format kicadsexpr -o $O/m.net $O/$B.kicad_sch 2>&1 | grep -v -E 'Fontconfig|Done'
python3 -I check_nets.py $B $O/m.net 2>&1 | cut -c1-170 | head -${3:-60}
