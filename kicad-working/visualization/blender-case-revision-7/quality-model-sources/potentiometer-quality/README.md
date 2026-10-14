# Detailed original-family potentiometer candidates

**Frozen: two colored STEP families, seven references.** These review assets improve the original-BOM Panasonic EVUF2LFL3 and Alpha RV112BCF40-25 body illustrations without changing any actual KiCad project, original model or Blender scene.

The integration contract is in `potentiometer-quality-manifest.json`: one combined STEP per family, one model node per reference, millimetres, original F.Cu footprint X, negative footprint Y and Z outward. Housing rear Z0 remains the earlier seating assumption. All assignments use zero offset and rotation, and unity scale. The full nominal shaft tips remain **Panasonic Z30 mm** and **Alpha Z25 mm**.

| Family | References | Complete nominal bounds, mm | Features |
| --- | --- | --- | --- |
| Panasonic EVUF2LFL3 | VR2, VR3, VR5, VR7, VR8 | X−4.85…4.85, Y−6.5…6, Z0…30 | Black molded case, rear wafer/carrier, stamped front frame/crimps, rivet indications, unthreaded grooved sleeve, full FL3 flatted shaft with printed C1 tip |
| Alpha RV112BCF40-25 | VR4, VR6 | X−6.8…6.8, Y−8.7…6.7, Z0…25 | Shaped flange, folded metal can/crimps, rear and second wafer, molded core, unthreaded sleeve and opaque flatted shaft |

The bounded manufacturer CAD search recovered no openly downloadable exact-family 3D model. Source evidence is retained under `sources/`; the models are original drawing-derived reconstructions. Panasonic uses the retained 2005 primary No.8 and FL3 drawings. Alpha uses the correct official **insulated-shaft ID77** primary document, rather than the transparent-shaft ID78 sibling retained in review8.

Alpha historical BOM suffix **25F** is not silently treated as an exact current **25A** match. The current25A table lists both 7 and12 mm flats; the earlier 7 mm nominal choice remains explicitly qualified. Its tip callout `2-0.5` means two0.5 mm radial reductions, not a2 mm axial bevel. The selected1 mm axial taper is unsized. Both models retain the canonical negative-Y inspection flat rather than claiming an installed rotary setting.

Published versus unsized evidence is recorded per feature. Material shades, wafer axial divisions, sheet stock, crimp folds, rivet details, sleeve grooves, local contours and radii are visual reconstructions. Electrical leads, below-seat mounting legs and internal wipers are omitted. No soldered lead trim, historical seating gap, knob socket, tolerance or mechanical fit qualification is claimed. No body was resized or moved to satisfy enclosure clearance.

Fresh native FreeCAD validation passed **23 checks**, including valid positive-volume solids, full bounds, sleeve/shaft dimensions, selected flat lengths, zero/unity assignments and unchanged original inputs. There are **21 valid solids and324 faces**. STEP roundtrip volume differences are below7e−9 mm³.

Two isolated native KiCad probes preserve the original source-reference position, side and rotation while substituting only the candidate model in a temporary copy. All **14 named features** import with materials and their expected sRGB-to-linear palettes. The maximum canonical bounds residual is **0.000339 mm**, and the maximum linear color error is below1.5e−8. Evidence is in `native-quality-audit.json` and `geometry-quality-audit.json`.

The four standalone closeups and `potentiometer-quality-contact-sheet.png` were visually inspected. Full-shaft views preserve the full exterior height; housing closeups intentionally crop the shaft and are labeled. Rendering did not open or save any delivered scene. `potentiometer-quality-review.json` is the compact passed review record, and `frozen-candidate-hashes.json` pins the assets for integration.

Own reconstructed CAD and generator: CC0-1.0. Manufacturer drawings and their embedded photographs retain the manufacturers' rights. These CAD assets are not manufacturer-approved or factory CAD.
