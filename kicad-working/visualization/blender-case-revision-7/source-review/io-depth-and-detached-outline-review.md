# I/O seating and detached outline: concrete finding

**Do not move the whole I/O PCB to eliminate the previous 14 sampled hits.**
All hits were on a detached historical outline imported as a second narrow
PCB strip, rather than on the populated rectangular PCB.

The original Eagle Dimension layer contains a 213.36 x 44.45 mm rectangular
PCB at X=0..213.36, Y=0..44.45. It also contains a detached 222.25 x 1.651 mm
rectangle outside that PCB, plus a further open line. The converted KiCad
coordinates invert Y: the detached rectangle is X=-4.064..218.186,
Y=+0.508..+2.159 mm. It has no pads or electrical connectivity.

The original I/O assembly photo, recovered from the pinned original-manual
mirror, shows one rectangular populated PCB and no detached parallel narrow
board. The original I/O manual also instructs seating the DIN connector faces
flush with the PCB edge. These support treating the detached contour as a
historical mechanical/construction reference. Its .065-inch thickness, location
outside the PCB, and alignment of its inner edge with all three REAN jack body
fronts suggest a rear-panel cross-section. That exact identity is not proven:
its width exceeds the original rear-panel DXF width by 4.318 mm and its thickness
exceeds the .062-inch panel by .0762 mm.

The next Blender presentation can therefore retain the detached geometry in a
separate **Historical detached Dimension outline - construction reference**
collection, hidden by default, while preserving its coordinates and keeping the
original PCB/GLB files untouched. No board translation is needed for this step.

The affected imported meshes are:

| Saved Blender mesh | Detached vertices | Detached polygons | Treatment |
| --- | ---: | ---: | --- |
| IOBOARD/PCB layers/mesh.003 | 98 | 76 | Split only the outside-strip silkscreen portion |
| IOBOARD/PCB layers/mesh.005 | 4 | 2 | Split only the top-mask rectangle |
| IOBOARD/PCB layers/mesh.006 | 4 | 2 | Split only the bottom-mask rectangle |
| IOBOARD/PCB layers/mesh.007 | 24 | 12 | Entire mesh is the detached FR4 strip |

There are zero polygons crossing between the selected strip and retained board.
The JSON mesh report records exact vertex and polygon indices from the pinned
GLB, native bounds, and source hash. Splitting and retaining all pieces preserves
130 vertices and 92 polygons without changing their locations.

For a later seating refinement, the historical body-front/strip-inner datum is
KiCad Y=+0.508 mm. Treating it as the intended rear-panel inner face would put
the PCB origin .508 mm forward of that face. Current NYS216 family lead spacing
suggests a different .158 mm offset; its historical variant is not established.
Neither supports an arbitrary 2.3 mm shift. Keep the current transform for the
immediate reference separation, and retain the submillimeter datum ambiguity.

Sources and hashes are in `io-depth-and-detached-outline-evidence.json`.
This review made no PCB, GLB, or delivered Blender scene changes.
