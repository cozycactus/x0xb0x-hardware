# Abracon resonator visual refinement

Two original parameterized **family illustrations** replace the previous
rounded-box bodies with tapered profiles and three coated lead shoulders.
These are revision-11 candidates. The generator writes only this directory;
it does not install models or alter a PCB, footprint or Blender assembly.

The [Abracon AWCR-MD drawing, revised 05.07.13, page 3](https://media.digikey.com/pdf/Data%20Sheets/Abracon%20Corp%20PDFs/AWCR_MD.pdf)
was visually inspected in `rendered/Abracon_AWCR_MD_2013-page-3.png`. Its
source PDF is retained under `sources/`; SHA256 is
`ef48f7b242efe5cfc1f1514721edb274fb13dd2caea086bebe3f40e30fa01a7a`.
The bulk outline supports tapered thickness, softened front corners and
three coated shoulders. It does not fully dimension these profiles.

| Reference | Drawing family used | Maximum body envelope | Preserved model rotation |
| --- | --- | --- | --- |
| IO XTL2 | 1.79 to 6.00 MHz low-profile bulk | 9.5 x 4.0 x 6.5 mm | Z = 0 degrees |
| Main XTL1 | 13.01 to 60.00 MHz bulk | 10.0 x 5.0 x 10.0 mm | Z = 180 degrees |

These maximum envelopes are unchanged from revision 5. The exact historically
fitted manufacturer, part revision and individual body size are unverified.
The original project permits an alternative 6 MHz resonator and notes that
its coating may be orange. Both candidates retain the previous illustrative
blue color. No manufacturer branding or frequency marking is invented.

## Preserved lead geometry and placement

- Three full rectangular leads have the original **0.6 x 0.35 mm** maximum
  sections. These follow the drawing's 0.5 +/- 0.1 mm width and
  0.25 +/- 0.1 mm thickness. They have not been narrowed to fit.
- Their model centers remain X = -2.54, 0 and +2.54 mm, Y = 0. The exact
  2.54 mm board pitch falls within the published 2.5 +/- 0.3 mm range.
- Every lead still spans Z = -2.5 to +0.47 mm. Fresh STEP comparisons against
  the prior installed STEP give **zero symmetric-difference lead volume**.
- The inherited body datum is Z = +0.35 mm. This stand-off and the trimmed
  2.5 mm tails are mounting illustrations. They are not the manufacturer's
  specified uncut bulk lead length of 5.0 +/- 1.0 mm.
- Offsets remain zero and scales remain unity. XTL1 retains its original
  180-degree model rotation; XTL2 retains zero. The drawing's front pin order
  is 3/output, 2/ground, 1/input from negative to positive model X.
- All six lead centers map to the existing board pin numbers, without
  changing footprint pose, pad geometry, drill, net or placement.

## Deliberate visual assumptions

The model is an intersection of independently defined smooth front and side
profiles. Only the outer width, depth and height above are published sizes.
The exact Bezier control points are visible in `build_resonators.py` and remain
explicitly undimensioned visual choices. The front shoulder floor lies at
16 percent of body height, the side's maximum depth runs from 50 to 75
percent of height, and the softened top reaches the full published height.

The three shoulder bases are 0.96 mm wide; their upper width is 1.34 mm and
their top is at 24 percent of body height. The side profile's base is 0.55 mm
thick. These dimensions are appearance parameters, not Abracon callouts.
No exact molding radii, draft angle, surface texture, tolerance stack, body
seating, solder joint, cap or enclosure clearance is qualified by this pass.

The whole refined body remains within the earlier rounded-box body. Removing
box volume improves shape without increasing the previous maximum envelope.
The colored STEP contains four valid material-role solids; their boolean
union is one connected solid. Per-feature STLs retain material separation.
The single combined STL is the closed exterior union, without duplicate
internal sheets at metal/coating overlaps.

## Verification and reproduction

`resonator-quality-manifest.json` provides two assignments with STEP hashes,
source attribution, transforms, limits and per-feature mesh colors.
`resonator-quality-geometry-review.json` records **60 passing** generator
checks. `resonator-quality-saved-geometry-review.json` records **68 passing**
independent fresh-STEP reimport checks. The latter imports no generator code;
it compares old and new STEP geometry, measures Z=-1 mm lead sections and
checks source-board hashes. Physical fit remains unqualified.

The STEP conversion changes Bezier surfaces to B-splines. Full bounds agree
to better than 0.000001 mm; the largest reported volume-integration difference
is about 0.0000184 mm3, or 0.000000053 relative. Both numerical errors are
recorded explicitly, separately from lead geometry and placement checks.

Run the following from the repository root with the installed FreeCAD runtime:

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python kicad-working/validation/models-review-11/resonator-quality/build_resonators.py
/Applications/FreeCAD.app/Contents/Resources/bin/python kicad-working/validation/models-review-11/resonator-quality/audit_saved_resonators.py
```

The review PNG is generated from frozen per-feature STLs by
`render_resonators.py`. It changes no existing scene or geometry.
Regenerating STEP files can change export metadata and hashes even when
geometry is equal; root integration should use the frozen reviewed files.

## Rights

The independent model geometry, generator, audit and render scripts are
dedicated under CC0-1.0. The STEP face-color helper is retained from this
project's original revision-10 helper, with unchanged behavior. No downloaded
manufacturer CAD was read, converted or incorporated. Abracon's drawing and
source images retain their respective copyright; this dedication does not
apply to manufacturer documents, trademarks or branding.
