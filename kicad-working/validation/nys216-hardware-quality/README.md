# NYS216 mounting nut refinement sources

This review supplies source evidence and explicit modeling parameters for the
three rear audio mounting nuts in Blender revision 10. It changes no connector
STEP files, PCB, scene or hardware mesh itself. Existing retained sources are
referenced and hashed instead of copied again.

The six-flat nut is real. The official older DXF shows six flats and SW15, and
the current manufacturer photograph confirms the rounded front treatment. The
2015 PDF's separate circular nut view depicts the larger rear flange and radial
rear-face features; it does not replace the external wrench flats with a round
or many-sided wrench profile.

| Parameter | Value | Basis |
| --- | --- | --- |
| Wrench size across flats | 15 mm | Printed SW15, official older DXF and newer PDF |
| Rear circular flange diameter | 17.5 mm | Printed newer PDF nut detail |
| Total nut depth | 5 mm | Printed newer PDF nut detail |
| Rear flange depth | 1.5 mm | Printed newer PDF nut detail |
| Front circular face diameter | 15 mm | Visual modeling choice; front circle and bevel are visible but undimensioned |
| Front corner-trimming depth | 0.55 mm | Visual modeling choice within the published 5 mm envelope |
| Plain clearance bore | 9.6 mm | Retained revision 9 illustration, around actual older 9.525 mm native nose |

The proposed local profile runs from Z = -2.5 mm at the mounting side to
Z = +2.5 mm at the outward face, preserving the previous nut origin and pose.
The circular flange occupies the rear 1.5 mm. The remaining 3.5 mm has six
15 mm flats; a sampled quarter-ellipse radial envelope rounds its front corners
into a circular face over the last 0.55 mm. In the local radius/Z section the
selected curve is Z = 1.95 + 0.55 sin(theta), R = 7.5 + (8.660254 - 7.5)
cos(theta), for theta from zero to pi/2. Its tangents join the outer envelope
and front face smoothly. Sixty-four quarter-arc segments are a rendering
resolution choice. This captures the source's rounded visual treatment without
claiming an exact molding radius. The quarter-ellipse shape, 0.55 mm span and
15 mm front circle remain explicitly illustrative in the delivered guide.

The new complete nut profile and plain bore share the actual native mating
axis, expressed in each retained nut object's local XY coordinates. The old
exterior illustration's axis was approximately 0.082 mm above that axis. This
small mesh-center refinement makes the new flange, six flats, rounded face and
bore coaxial; it preserves all nominal sizes about their common center. The
object origin, transform, parenting and actual PCB component pose stay
unchanged. The local profile center must be derived from the native axis rather
than assumed to be the existing object's local XY origin. Only the three nut
meshes are refined; native connector and washer geometry remain unchanged.

The enlarged newer drawing shows nine radial features at 40-degree intervals.
Their interpretation as rear mounting-face ribs is supported by its side
section, but function, stock sizes and angular datum are not specified. Omit
them in this pass to preserve the mounting plane and avoid an invented seating
projection.

The installed connector follows the older DXF's 3/8-32 UNEF nose, nominally
9.525 mm. The newer nut detail specifies M11 x 1.25. These source revisions are
not proof of thread interchangeability. The scene retains a plain 9.6 mm bore,
without a female thread. The existing washers retain the newer PDF's 11.3 mm
bore, 15.3 mm outside diameter and 1.2 mm thickness. Historical supplied
hardware identity and physical fit remain unqualified.

`hardware-parameters.json` contains the full coordinate/profile contract, each
dimension's classification, preservation requirements and limitations.
`source-evidence.json` pins the retained drawing/photo hashes and preserves the
relevant original DXF entities. `collect_source_evidence.py` reproduces those
two JSON files from read-only retained inputs and writes solely here.

Primary source links:

- [Official REAN NYS216 product](https://www.rean-connectors.com/en/product/nys216)
- [Official older DXF](https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1)
- [Official 2015 PDF](https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1)
- [Official product photograph](https://www.rean-connectors.com/uploads/media/400x/02/15142-NYS216.jpg?v=1-0)

Manufacturer sources retain their respective rights. The audit code and
original parameter notes are CC0-1.0. All geometry is a qualified illustration,
not a factory mechanical or assembly model.
