# Blender revision 27 — printed IC markings

Open `x0xb0x-populated-with-case.blend` with Blender 5.2.2 LTS. The 17 ICs show the native KiCad 24 markings transcribed from the original kit photographs, raised 0.03 mm in light-grey ink; the FT232BM (IC25) sits on the underside of the I/O board and reads correctly from below. Only the 17 existing part meshes change and one ink material is added. All 1721 objects, 491 native references, sockets, resistor bands, Xicon XRL electrolytics, 40 LEDs and spacers, 23 caps, case geometry, camera poses and animation are preserved.

Logos are omitted, the font approximates the vendors' and the codes come from one photographed kit. See `../../../docs/ic-markings.json` and the KiCad 24 review for sources and limits.

All 491 models match fresh native KiCad exports. The saved scene passes 12 preservation checks, 106 portability checks, 44 rear-opening checks/974 rays, the 25-reference/133-piece terminal-join check and the drill-fit check on all 489 drilled models; the contact screen finds no new contact.

Frames 1 assembled, 80 exploded, 120 control-side, 160 wiring study. `markings-*-before.png` and `-after.png` use identical cameras over the 74HC595s, IC24 and the underside IC25; their lighting is temporary. These checks do not qualify physical fit or circuit operation.
