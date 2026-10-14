# Misc PCB body and wire illustrations

These nine original parametric models cover **21 fitted reference positions** through 12 assignment groups in [misc-body-manifest.json](misc-body-manifest.json). Each reference receives one complete colored STEP model. The corresponding STL and optional color-role STL segments are included for Blender import. All dimensions use millimetres; canonical X follows the source F.Cu footprint X, canonical Y is minus the footprint Y, and canonical Z points outward from the F.Cu seat. KiCad applies the actual footprint position and angle. Assignment offsets and rotations are zero.

| References | Identity and model evidence | Main limitation |
|---|---|---|
| Main TM3/TM4/TM5; I/O TM6 | Original BOM CT6EP504/503/502/202; current Nidec/Copal CT-6EP primary outline, 7 × 7 × 5.8 mm | Original BOM calls Vishay; historical vendor/revision unresolved. Rotor details and seating approximate; no terminals. |
| I/O IC20 | Generic MC78M05/7805 TO220 body and tab within current onsemi case 221AB outline | Exact original vendor/suffix, body seat and segmentation unconfirmed; no leads. |
| Main R100A0/R100B0 | Original Microohm LPTC12T21001 1 kΩ **PTC** identity and original band sequence | No primary mechanical drawing recovered; 7.62 × 2.54 mm nominal body follows source footprint artwork, height approximate; no leads. |
| Main Q22 | Original 2SC2291 SIP5 identity and source footprint outline | No primary package drawing recovered; 5 mm height approximate; no leads. |
| I/O KK1 | Original Aavid 574502B00000G, current Boyd specific drawing envelope 21.84 × 10.03 × 19.05 mm | Folds, wall thickness and contact geometry approximate. Family table gives a conflicting 9.02 mm depth; original D03S artwork is narrower. |
| Main J1/J2 | Bare wire jumpers at actual 12.70/15.24 mm pad spacing | Wire diameter, bridge height and forming lengths inferred. |
| Main and I/O J3–J7 | Soldered ribbon terminations: one 12-conductor and four 3-conductor positions per board, actual 2.54 mm pad pitch | Terminations only. 7.5 mm stub height and wire sections inferred; 152.4 mm is original stock length, not an installed cable length. |

**Main IC15A0 is intentionally unpopulated.** The original VCA assembly specifies BA662A at IC15A *or* BA6110 at IC15B plus Q1–Q4. The supplied circuit uses the latter. Adding a second OTA body would misrepresent this assembly.

The generator reads source board poses and pads and writes only this asset directory. It does not change pads, copper, footprints, board placement, library models or Blender scenes. The supplied manifest supports the separately authorized KiCad and Blender visual assignments. These models are visual body/wire representations; they do not certify package pin fit, mechanical clearance, regulator/heatsink contact or physical assembly.

## Validation

- Nine complete STEP files reloaded in OpenCASCADE as valid positive-volume geometry; reloaded volume matched exported geometry within the recorded tolerance.
- Every STEP contains AP214 surface styles; each manifest records bounds, solid count and file hashes.
- All 52 jumper/ribbon conductor axes matched the actual placed pad centres after the source F.Cu position and angle, with a maximum residual of 2.8422 × 10⁻¹⁴ mm.
- Both source PCB hashes matched the read-only starting snapshot after generation.
- The manifest lists every dimension assumption and source URL, and hashes every retained source document under `reference/`.

## Source and license

The original x0xb0x BOM and assembly pages are authored by Limor Fried / Adafruit and retained through the original project mirror, pinned at commit `1910f746d2d8758f2651596b00c08f76c847c926`. The original project license is preserved separately in the scene source directory. Manufacturer drawings and original photos retain their owners' copyrights and are reference evidence, not newly licensed artwork.

The original parametric illustrations, generator and asset manifest in this directory are dedicated under CC0-1.0; see [LICENSE-illustrations.txt](LICENSE-illustrations.txt). No manufacturer-authored CAD is claimed for these assets.
