# Front LED and button construction review

The original x0xb0x has **40 PCB-mounted LEDs**, whose lenses appear through the front-panel holes, and **23 PCB-mounted tactile switches with separate snap-on caps**. Those visible controls belong on the front of the finished enclosure. There is no additional set of 40 electrical panel LEDs.

The original [sequencer assembly instructions](https://www.ladyada.net/make/x0xb0x/fab/seq/index.html) describe plastic LED spacers and alignment through the panel while soldering. Standard parts are rounded LEDs emitting red light; other LEDs are discussed separately. The retained original bare-PCB and finished-panel photos were visually inspected: they show clear lenses with red emitted light. The original [finishing instructions](https://www.ladyada.net/make/x0xb0x/fab/finish/index.html) tell the builder to snap caps onto the switches before attaching the mainboard/front panel.

## Current saved Blender revision 6

The read-only measurement script opened the stable scene at frames 1, 80 and 120 without saving it. SHA256 remained `c1e20cbd5971b7f8ddc372cb96c406328d7d49110bdb507f252b142cd18f2ac9`.

| Item | Fresh saved-scene result | Meaning |
|---|---|---|
| Native LEDs / added lens proxies | 40 native LED references plus 40 separate red lens proxy meshes | One electrical set is intended, but a duplicate, disconnected presentation surface was added to show light at the front. |
| Native LED lens-axis alignment | Maximum 0.000039 mm error against original DXF hole centers | Placement in X/Y is correct within export precision. The generic polarity flat offsets its bounding-box midpoint by 0.2 mm; that midpoint is not the lens axis. |
| Lens proxy X/Y alignment | Maximum 0.000024 mm error against all 40 original DXF holes | The proxy layout follows the original panel. |
| Native LED top | 0.2212 mm below the panel underside | Current native body does not reach through the panel. |
| Added lens proxy | Bottom 1.0968 mm above underside; top 1.7780 mm above panel top | The native tip and proxy bottom have a disconnected normal gap of approximately 1.3180 mm. |
| Caps / native tactile switches | 23 caps on 23 native references | Correct assembly population. |
| Cap dimensions and opening | Full cap 11 mm high; minimum 0.2250 mm nominal edge clearance in original DXF opening | The visible cap envelope fits the source opening under current illustrative placement. |
| Cap projection / actuator | Cap top 2.5000 mm above panel; native actuator tip extends 2.4040 mm into solid cap envelope | Visually plausible overlap, with actual hollow socket, snap engagement and switch travel unqualified. |

At **frame 80**, all 40 red proxy lenses and all 23 caps stay with the lifted front-panel proxy collection; the native LEDs and switch bodies follow the PCB. That presentation implies a misleading attachment for those parts. In the real source assembly, the LEDs remain soldered to the board and the caps are attached to their board-mounted switches. At **frame 120**, the panel and all front proxies are hidden, while the native PCB population remains visible.

The original source cutout orientation and photo color mapping are consistent with the current caps: **S17–S24 white**, other 15 caps black; S5, S6, S14, S15 and S16 are horizontal. Color mapping is supported by the prior source-photo evidence retained with the scene. This review freshly checked the geometric cutout clearances.

## LED mounting evidence and qualification

The original [parts list](https://www.ladyada.net/make/x0xb0x/fab/parts.html) specifies **VCC STD240B, 0.24 inch (6.096 mm)** spacers. The sequencer page instead lists **0.22 inch (5.588 mm)**. The discrepancy is retained explicitly; spacer height also depends on the fitted LED package.

Fresh inspection of the official generic KiCad LED STEP shows a lower lens/flange datum at **Z3.0 mm**, lens top **Z11.6 mm**, and two 0.4 × 0.4 mm leads reaching Z−2.5 mm. A source model already includes 3 mm of body stand-off; adding an entire 6.096 mm translation would double-count that part of the mount height.

With the current board/panel seat and this same generic 8.6 mm lens/body, a **body-only** lift to the 6.096 mm BOM spacer would be **3.096 mm**, placing its tip **1.300 mm above the panel**. The 5.588 mm alternative would lift the body 2.588 mm and leave 0.792 mm visible. Those are qualified geometric comparisons, not changes applied to the project. The existing proxy top would correspond to a 6.574 mm generic-body stand-off, matching neither source entry.

Raising the whole current LED model by 3.096 mm would also raise its cut lead ends to Z+0.596 mm above the PCB seat. A continuous installed model therefore requires preserving the full source-width leads while extending them back to the PCB and below-seat tails. Lead thinning or floating terminals would conceal the construction problem.

## Recommended correction

Replace the separate red lens shortcut with **one continuous, source-qualified LED assembly per PCB reference**, including the chosen spacer height and full-width leads; represent a clear lens with red light when illuminated. Preserve all 40 original PCB axes, polarity orientation and panel holes. Keep exact historical LED identity, the 0.22/0.24 inch source conflict and actual installed seating qualified.

In exploded views, PCB LEDs and snap-on switch caps should follow their PCB references. The panel may lift away independently. Keep existing assembled cap exposure and source cutout dimensions until a real cap socket/travel drawing supports a more precise model. This review authorizes no source/project edits and made none.

Evidence: `front-control-native-measurements.json`, `generic-LED-source-bounds.json`, `front-controls-review.json` and the pinned original author pages under `sources/`. The two original research photographs remain at their previously retained paths and are not embedded in this review or proposed as redistributable textures.
