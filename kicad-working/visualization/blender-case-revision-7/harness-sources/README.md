# Independently verified x0xb0x harness

**Five electrical groups, 24 conductors, 48 endpoint pads.** Current PCB pads agree with fresh native schematic netlists for every endpoint. The earlier map matches every actual endpoint net and local pad position.

The [original jumper table](https://wiki.ladyada.net/x0x/jumpers) gives signal functions. The [original finishing instructions](https://www.ladyada.net/make/x0xb0x/fab/finish/index.html) specify soldered ribbons, four 3-conductor pieces plus two 6-conductor pieces, and pin 1 stripe alignment at both ends. The [VCO manual](https://www.ladyada.net/make/x0xb0x/fab/vco.html) independently confirms corresponding J4 pins.

| Group/pin | Main net | I/O net | Function |
|---|---|---|---|
| J3.1→J3.1 | USBRX | USB_TX | USB TX |
| J3.2→J3.2 | USB_TX | USB_RX | USB RX |
| J3.3→J3.3 | +5V | +5V | +5 V |
| J3.4→J3.4 | +5V | +5V | +5 V |
| J3.5→J3.5 | MIDI_IN | MIDI_IN | Midi In |
| J3.6→J3.6 | MIDI_OUT | MIDI_OUT | Midi Out |
| J3.7→J3.7 | GND | GND | GND |
| J3.8→J3.8 | GND | GND | GND |
| J3.9→J3.9 | DINSYNC4 | DINSYNC4 | Din Sync 4 |
| J3.10→J3.10 | DINSYNC3 | DINSYNC3 | Din Sync 3 |
| J3.11→J3.11 | DINSYNC2 | DINSYNC2 | Din Sync 2 |
| J3.12→J3.12 | DINSYNC1 | DINSYNC1 | Din Sync 1 |
| J4.1→J4.1 | +5.333V | +5.333V | 5.333V |
| J4.2→J4.2 | GND | GND | GND |
| J4.3→J4.3 | +12V | +12V | 12V |
| J5.1→J5.1 | N$10 | HP_OUT | Headphone |
| J5.2→J5.2 | GND | GND | GND |
| J5.3→J5.3 | +6V | +6V | 6V |
| J6.1→J6.1 | N$625 | N$27 | CV |
| J6.2→J6.2 | GND | GND | GND |
| J6.3→J6.3 | N$622 | N$26 | Gate |
| J7.1→J7.1 | N$7 | N$1 | Mix Out |
| J7.2→J7.2 | GND | GND | GND |
| J7.3→J7.3 | N$20 | N$2 | Mix In |

**USB needs no physical pin swap.** J3.1 connects FT232 IC25.25 TXD output (`USB_TX`) to MCU IC3.3 RXD1 (`USBRX`). J3.2 connects MCU IC3.4 TXD1 (`USB_TX`) to FT232 IC25.24 RXD input (`USB_RX`). The same net string appears on different directions in the two independent projects; pin numbers and device pin functions resolve the ambiguity.

The two 6-conductor pieces are allocated to J3.1–6 and J3.7–12 by the documented counts and the actual 12-pad row. That allocation is a reconstruction inference. Bends, slack, wire sections, trimmed length and the 3D route remain scene construction choices. Use actual endpoint pad positions and each board world matrix; no historical installed cable path or physical fit is certified.

See [verified-harness-map.json](verified-harness-map.json) for all actual endpoint coordinates, orientations, silk pin markers, schematic endpoint evidence, source hashes and ambiguity notes. The primary wiki reference retains its CC BY-SA 4.0 attribution. No KiCad/project files were edited.
