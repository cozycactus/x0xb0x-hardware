# Revision 2: independent reference split and clearance review

The saved revision-2 Blender file was reopened independently. All four split
PCB-layer meshes pass exact vertex and polygon union checks against their
preserved originals. Coordinate values, face winding, materials, smoothing,
and native transforms are unchanged. The hidden reference contains exactly
**130 vertices and 92 polygons**, with no lost, duplicated, or crossing faces.
Its selected indices match the independently extracted source contour.

The reference instance is hidden in both render and viewport, is parented to
the I/O instance, and has an identity local transform. The populated I/O
instance uses the derived DISPLAY collection. Its assembled world matrix is
exactly unchanged from the first delivered Blender file; that original file
also retains its recorded hash. No I/O seating shift was applied.

A fresh bounded case probe used **69,793 actual native-model vertices** sampled
from the two visible board instances, comprising 441 mesh objects. The hidden
historical reference, preserved verification originals, and independent
presentation proxies were excluded. It found **zero sampled intersections**
with either reconstructed case solid. The previous 14 hits belonged to the
detached historical outline now retained as a hidden reference, rather than
the populated I/O PCB rectangle.

The evidence is recorded in `revision-2-independent-split-audit.json` and
`case-clearance-review.json`, with Blender and case-mesh hashes. This remains a
sampled visualization check: it does not check every triangle, establish a
positive clearance margin, prove current manufacturer part identity, or certify
physical enclosure fit. Case seat datums, molded details, connector depth, and
the original rear mount-hole discrepancy retain their documented uncertainty.

No PCB, source GLB, delivered version-1 Blender file, or revision-2 scene was
edited by this audit.
