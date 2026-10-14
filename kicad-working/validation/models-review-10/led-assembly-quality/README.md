# Continuous PCB-mounted 5 mm LED installation model

This isolated candidate replaces the disconnected front-panel lens shortcut with a **single complete PCB-mounted LED assembly for each of LED1–LED40**. The exact official generic KiCad lens/flange body is retained above its lower Z3.0 mm plane, then translated upward by 3.096 mm. Both full **0.4 × 0.4 mm** leads extend continuously from the body underside at Z6.096 mm through the PCB seat to unchanged Z−2.5 mm cut tails. No terminal width or body dimension is reduced.

The selected 6.096 mm body seat follows the original [x0xb0x BOM](https://www.ladyada.net/make/x0xb0x/fab/parts.html), which identifies **VCC STD240B, 0.24 inch**. The [sequencer manual](https://www.ladyada.net/make/x0xb0x/fab/seq/index.html) explains the spacer and front-hole alignment construction, but its parts table instead gives 0.22 inch (5.588 mm). This source conflict remains explicit. The exact original supplied LED vendor, package tolerance and fitted stand-off are not established by the generic model.

Original author bare-control-PCB and finished-panel photographs were visually inspected; their lenses are clear when unlit and emit red light. The model therefore uses a light clear-body material role, with transmission/refraction supplied as a qualified Blender appearance choice. Internal die, bond wires, reflector cup and optical behavior are not reconstructed.

The original stock model already places its lens underside 3 mm above its seat. A body-only lift of **3.096 mm**, rather than adding the full 6.096 mm, avoids double-counting that original stand-off. Lifting the entire stock model would incorrectly raise its cut terminals above the board. This candidate instead keeps the cut tails and extends their full square cross-section.

The new model retains the **original source coordinate frame**: lead axes at X0 and X2.54 mm and lens axis X1.27 mm. All 40 existing native assignments preserve **offset [1.27, 0, 0] mm**, **rotation [0, 0, 180] degrees**, and unity scale. Under that mapping, sourceX0 is cathode K at footprintX+1.27 mm; sourceX2.54 is anode A at footprintX−1.27 mm. The source polarity flat is preserved.

| Dimension or property | Value |
|---|---:|
| Generic lens/flange body height, unchanged | 8.6 mm |
| Lower body/flange seat selected from BOM | 6.096 mm |
| Body-only lift from stock geometry | 3.096 mm |
| New source lens top | 14.696 mm |
| Full width and thickness of each lead | 0.4 × 0.4 mm |
| Lead-axis pitch | 2.54 mm |
| Trimmed tail bottom | −2.5 mm |
| Actual original drills, all 80 checked | 1.0 mm |
| Minimum nominal square-corner/drill radial margin | 0.217157 mm |

The model has three individually colored valid solids, joined at their interfaces into **one connected solid**. Its full STL and each color-role STL are closed. `led-assembly-geometry-audit.json` records **233 checks passed**, including fresh STEP reload, exact source-head preservation under inverse translation, full-width sections at seven lead depths, all 80 actual pad/drill axes, polarity and unchanged native transforms.

The current board/panel presentation seat would place the generic lens tip approximately **1.300 mm above the panel top** with the selected 0.24 inch seat, compared with **0.792 mm** for the unresolved 0.22 inch alternative. Those are model comparisons, not physical measured fit. The isolated native KiCad export and review keep the original B.Cu/model transform and confirm the final source bounds and materials.

**No black spacer body is invented.** A primary-authored 2007 VCC catalogue drawing was located at a distributor PDF URL, but retrieval returned HTTP403. Original source text establishes the height and role, while the exact outer body, separator and lead-entry geometry remain unverified. The selected spacer height is represented by body seating and recorded in the manifest. The source conflict and this deliberate omitted shape remain visible in the documentation.

The new LED model is intended for project assignment and independent integration checks. The root assembly update must remove the old 40 separate red lens proxies, retain 40 PCB references, and keep LEDs associated with their PCB in exploded views. The separate 23 switch caps also belong to their PCB-mounted tactile switches. This asset builder does not edit any working project, footprint, pad, panel or saved Blender scene.

`led-assembly-manifest.json` supplies one family with all 40 assignments; `frozen-candidate-hashes.json` pins the final STEP/STL assets. Native evidence is under `native-probes/`, and `LED-native-panel-mount-review.png` shows the complete LED, its full leads, original nominal drill holes and a small current-height panel patch. Those patches are review illustrations only.

Original installation/reconstruction code and new extensions are CC0-1.0. Reused official KiCad head geometry retains the KiCad package-library license and applicable exception. Original author photographs and reference text retain publisher rights and are not newly relicensed.
