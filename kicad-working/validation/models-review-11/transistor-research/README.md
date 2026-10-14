# Historical Sanyo 2SC536 package source recovered

The actual **Sanyo No.333H** drawing is now recovered and visually inspected.
It appears on printed pages 243-244, PDF pages 247-248, in the
[1985 Sanyo transistor handbook](https://www.bitsavers.org/components/sanyo/_dataBooks/1985_Sanyo_Semiconductor_Handbook_-_Transistors.pdf).
The delivered two-page excerpt retains the original publisher markings. The
67,201,880-byte full handbook remains outside the tracked repository; its
SHA-256 is `e96643675ad4e019f6ea1cce5913a3ccaedd9c3374a8892479f8f0d2b6e40c4d`.

| Drawing family | Body width x depth x height | Factory pitch | Lead section |
| --- | --- | --- | --- |
| SP 2000B | 4.0 x 2.2 x 3.0 mm | 1.3 mm | 0.35 x 0.30 mm |
| NP 2003A, JEDEC TO-92 | 5.0 x 4.0 x 5.0 mm | 1.3 mm | 0.45 x 0.44 mm |

These dimensions are **typical**, not maximum clearance envelopes. The general
case-outline page, printed page 40/PDF page 44, explicitly states that dimensions
without min/max labels are typical. That page is included as a separate excerpt.
Both packages show a 14.0 mm factory lead length and a shoulder at 2.0 mm from
the body. The shoulder width callout is 0.45 mm. No.333H's bottom/end view labels
the leads **B-C-E** along their row. F is the **160-320 gain rank**, not a package
identifier.

The [original project parts list](https://www.ladyada.net/make/x0xb0x/fab/parts.html)
calls these 24 parts TO-92 and identifies their 536F marking. The frozen
[author photograph](https://raw.githubusercontent.com/x0xb0x/x0xb0x.github.io/1910f746d2d8758f2651596b00c08f76c847c926/assets/images/parts/2sc536.jpg)
has a nearly square frontal body, consistent with NP2003A. It is unscaled and
does not directly show depth or rear curvature. An initial impression that its
edge lips identified SP was rejected after checking the two drawing aspect
ratios. The BOM's explicit TO-92 description and photo support a **qualified NP
family illustration**, not authentication of the actual fitted vendor or mould.

This is a useful dimensional improvement over the former generic modern JSCJ
outline. The separate transistor candidate models use the recovered historical
typical dimensions while preserving existing PCB axes, transforms and electrical
mapping. Original board pitch is 2.54 mm, with three asymmetric 2.54/3.302 mm
forms; that installed lead forming remains qualified and is not replaced by
the factory pitch. Installed stand-off, trim lengths, curve radii, cosmetic
recess and colors remain illustration choices.

Modern 2SC536N/NPA-WA, JSCJ and Semtech drawings are not substituted for this
historical source. The recovered 1968 round-case Sanyo scan is historical
context only. The public Scribd No.333H preview corroborated the same printed
page, but the higher-resolution manufacturer handbook is the dimensional source.

`transistor-source-review.json` records source URLs, all delivered hashes,
dimensional readings, the corrected photo interpretation and limitations.
Original manufacturer documents and project photos retain their copyrights;
no new open license is asserted for those source files.
