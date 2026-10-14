# NYS216 exterior nut profile

The large six-flat black piece on the rear audio connectors is real mounting
hardware. It is the removable nut, not the 20 mm-wide ribbed jack body. Both the
official older DXF's assembled front view and the manufacturer's current photo
show six wrench flats, with a rounded or beveled circular front face. The
current Blender revision 9 plain hexagonal nut is a simplified illustration of
that real part; this review does not change its geometry.

Primary sources reviewed:

- [Official REAN NYS216 page](https://www.rean-connectors.com/en/product/nys216):
  describes a plastic housing supplied with a nut and washer.
- [Official NYS216 DXF](https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1):
  retained as `quality-model-sources/rear-quality/source/nys-216-manufacturer.dxf`
  in Blender revision 7. Drawing 3102 ST 22 01, revision C (2007), labels the
  assembled front hardware SW15 and shows a closed six-vertex outline. At the
  2:1 drawing scale, printed SW15 governs the 15 mm wrench-flat nominal rather
  than treating every raw DXF coordinate as an independent tolerance.
- [Official current product photograph](https://www.rean-connectors.com/uploads/media/400x/02/15142-NYS216.jpg?v=1-0):
  visibly shows a six-flat nut with a rounded front edge. It is retained locally
  as `nys216-official-current.jpg` for this source review. The photograph is
  manufacturer material; all rights remain with REAN.
- [Official 2015 PDF](https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1):
  the assembled front view again calls out SW15. Its separate nut detail gives
  a 17.5 mm circular flange envelope, 5 mm total depth and 1.5 mm flange depth.
  The washer has 11.3 mm bore, 15.3 mm outside diameter and 1.2 mm thickness.

The separate nut detail's circular view and nine small radial features do not
establish a many-sided external nut. The larger circular flange can hide the
smaller six-flat body when viewed from the mounting side. The corresponding
side section depicts small raised features on that flange's rear face.
Interpreting the circular view as the rear mounting face is an inference
supported by those views; calling the radial features a
specific anti-loosening mechanism would be an inference, not a stated source
function. The actual external six-flat profile is independently confirmed by
the assembled front view and product photograph.

The rounded or beveled front treatment can be justified visually. Its precise
radius, chamfer size and molding transitions are not dimensioned. Any future
refinement should preserve printed nominal dimensions and label those small
profile choices as illustrative.

The source revision discrepancy remains: the 2007 DXF specifies 3/8-32 UNEF,
while the 2015 PDF specifies M11 x 1.25. The installed source nose follows the
older 9.525 mm nominal. Revision 9 therefore uses a 9.6 mm plain nut clearance
bore, not a modeled female thread, and retains the newer drawing's 11.3 mm
washer bore. These illustrations do not certify thread compatibility or the
exact hardware supplied in historical x0xb0x kits.

No installed STEP, PCB, Blender scene or model-generation code was changed by
this profile review.
