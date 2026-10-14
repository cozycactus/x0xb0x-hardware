# Independent saved-geometry audit

`audit_saved_nuts.py` measures the three audio connector nuts from the saved
Blender scene. Generation manifests are not used as measurements. It derives
the flange center from saved outer extents, intersects actual saved triangles
with the central wrench-body plane, reduces the resulting convex hull to its
six flats, and measures the separation of opposite support planes. Saved
outer-ring vertices establish the flange diameter and thickness; the complete
mesh establishes total depth and rear seating plane.

The bore datum comes independently from the evaluated native connector and
nut collection-instance matrices. Its saved inner-wall radius, axial span and
coaxiality with the new flange/hex profile are checked against that actual
native mating axis. The nut object origins and stored matrices remain unchanged;
only the permitted new mesh profile shifts locally to that common axis.

The printed nominal geometry is SW15 wrench flats, a 17.5 mm flange, a 1.5 mm
flange thickness and a 5 mm overall depth. The 9.6 mm plain bore illustrates
clearance around the retained 9.525 mm native threaded nose. Its thread form,
tolerance and physical interchangeability are not qualified.

The rounded front treatment, its 0.55 mm transition depth and its 15 mm front
circle are undimensioned appearance choices. Undimensioned rear features are
omitted to preserve the nominal rear seating plane and overall depth. These
choices are explicitly qualified in the source contract and scene guide.

`verification/audit_saved_scene.py` independently reopens both saved revisions
9 and 10 and compares their stored mesh fingerprints, materials, object poses,
hierarchy, collections, editable labels, wires, cameras, animation and evaluated
instance matrices in frames 1, 80, 120 and 160. Only the three nut mesh data
blocks, explicit revision metadata and one new opening guide may differ.
All three washer meshes and all 491 fitted native component assemblies must
remain unchanged.

The unchanged reusable `scripts/verify_rear_openings.py` checks the eleven rear
mating passages against all displayed mesh geometry, includes 600 isolated
hardware rays and preserves the intentional DIN inserts, USB tongue and power
pin. The checks concern the modeled openings and geometry; they do not certify
physical assembly fit or cable compatibility.

## Fresh saved-file results

The final saved revision 10 scene (`9c75786aa2ea7a551ef68ed0715c6ac8ef12455213dd24192e5a07f4d00f1d07`, 42,935,746 bytes) passes:

- **43 independent saved-mesh geometry checks** for the three nuts. Actual central sections have six 15 mm flats; flange diameter is 17.5000 mm, flange thickness is 1.5000 mm and total depth is 5.0000 mm. The native-axis inner wall measures 9.6000 mm nominal diameter. Each mesh is one closed manifold solid with positive signed volume of approximately 680.1319 mm³.
- **14,823 fresh saved-file preservation checks** against revision 9. Exactly the three named nut mesh data blocks differ. All three washer meshes, all 491 native component assemblies, the 40 LEDs, 23 PCB-attached caps, enclosure/panels, labels, wires, cameras, materials, animation and displayed poses in all four inspection frames remain unchanged. Only explicit revision metadata and one new guide are added.
- **44 rear-opening checks / 974 raycasts**, using the unchanged reusable verifier. All eleven mating passages remain open with intended recessed internals retained.

The nominal profile is coaxial with the actual native socket axis within less than 0.000001 mm numerical residual. Its local offset is about 0.082 mm while the original object origins/matrices stay unchanged. The saved rounded front transition retains all 65 declared arc stations, measured directly at their saved vertex planes. Partial Boolean clip levels are not complete radial stations and can lie inside the envelope. All 4,007 rounded-region vertices per nut were additionally checked against every hex support plane and the analytic quarter ellipse. The maximum outward normal-distance residual is less than 0.000001 mm, within saved-coordinate floating-point precision. Because the outer cap/hex intersection is convex, triangle interiors also remain inside this envelope. These are numerical geometry checks, not manufacturing tolerances.

The rounded treatment is an appearance reconstruction, not a printed manufacturer dimension. The older native 3/8-32 nose and newer M11 hardware drawing are not proof of interchangeable threads; the scene keeps a plain bore with physical fit unqualified.

Revision 9 remains byte-identical at SHA256 `96c57c42b2019abb3d4431b63b363587c509890185e0ed895436f103cd535158`. Inspection did not change either saved scene. Detailed measured values are in `saved-nut-geometry-audit.json`; combined input hashes and outcome are in `independent-validation-summary.json`.
