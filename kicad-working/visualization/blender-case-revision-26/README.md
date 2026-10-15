# Blender revision 26 — original-BOM IC sockets

Open `x0xb0x-populated-with-case.blend` with Blender 5.2.2 LTS. IC3 and IC2 show the native KiCad 23 models: TE manufacturer models of their original-BOM DIP sockets (black ladder housings 5.10 mm tall, tin contacts) with the KiCad DIP chips resting on top, 8.78 mm above the board. Only the two existing part meshes change and two socket materials are added. All 1721 objects, 491 native references, resistor bands, Xicon XRL electrolytics, 40 LEDs and spacers, 23 caps, case geometry, camera poses and animation are preserved.

The chip seating height is an assumption and the TE models are for the lead-free successors of the BOM part numbers. See `../../../docs/ic-socket-completion.json` and the KiCad 23 review for sources and limits.

All 491 models match fresh native KiCad exports. The saved scene passes 12 preservation checks, 106 portability checks, 44 rear-opening checks/974 rays, the 25-reference/133-piece terminal-join check and the drill-fit check on all 489 drilled models. The neighbour screen finds no new contact; the free height above the chips falls from 12.9 to 7.8 mm (to the case floor, assembled).

Frames 1 assembled, 80 exploded, 120 control-side, 160 wiring study. `socket-ic3-*` and `socket-ic2-*` before/after images use identical cameras; their lighting is temporary. These checks do not qualify physical fit, tolerances or circuit operation.
