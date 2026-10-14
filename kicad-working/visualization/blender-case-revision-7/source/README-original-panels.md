# Original x0xb0x panel source

Copyright (c) Limor Fried & Adafruit industries. The original design MIT
license is preserved in `LICENSE-original-design.txt` and the full mirrored
original download page is retained as HTML. `x0xb0x` is Adafruit's trademark.

The two official linked DXF assets were recovered from the public x0xb0x.org
website mirror repository `x0xb0x/x0xb0x.github.io`, pinned to commit
`1910f746d2d8758f2651596b00c08f76c847c926`. The downloaded byte lengths and
Git blob hashes match the repository tree. `panel-downloads.json` records
original and mirror URLs, hashes, and recovery evidence. No login was used.
The original ladyada.net downloads returned HTTP403 in this session.

Each drawing explicitly identifies inches. Conversion is25.4mm/inch.
The original download page specifies0.062inch (1.5748mm) sheet material.
Model-space and paper-space geometry are duplicates; the parser keeps only
model-space manufacturing circles and continuous closed line loops.
Construction centerlines, dimensions and annotations stay in the raw DXFs.
One isolated continuous rear-panel line runs across the CV/GATE circle
centres; it is retained as an open source line and excluded from physical
cut geometry.

The main panel has58 round holes and23 rectangular cuts. The rear panel has
9 round holes and2 rectangular cuts. These sources contain manufacturing
annotations, but no actual control legends or silkscreen artwork. The
whole-sheet SVGs are diagnostic line plots and do not constitute panel art.

`../panels/original-panels.json` contains millimetre geometry, preserved
source handles and source coordinates. `../panels/board-panel-alignment.json`
contains actual board position correspondences and limitations. Both PCB
files are read only in this workflow. The four rear mainboard mounting
positions differ by0.24548344mm from the source panel positions; the
original geometries were preserved. Rear assembly height and setback are
explicit illustration assumptions pending historical fitted-part data.
