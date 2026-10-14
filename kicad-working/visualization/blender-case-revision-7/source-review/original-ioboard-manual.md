![](https://ladyada.net/images/wavebubble/topheaderbadge.png)

x0xb0xfabrication manual: I/O board

- [About](https://ladyada.net/make/x0xb0x/index.html)

- [News](http://www.ladyada.net/rant/?cat=2)

- [F.A.Q.](https://ladyada.net/make/x0xb0x/FAQ.html)

- [Samples](https://ladyada.net/make/x0xb0x/samples.html)

- [Gallery](https://ladyada.net/make/x0xb0x/gallery.html)

- [Mods](https://ladyada.net/make/x0xb0x/mods.html)

- [Make](https://ladyada.net/make/x0xb0x/fab/index.html)

  - [Parts](https://ladyada.net/make/x0xb0x/fab/parts.html)

  - [Tools](https://ladyada.net/make/x0xb0x/fab/tools.html)

  - [Preparation](https://ladyada.net/make/x0xb0x/fab/prep/index.html)

  - [Power](https://ladyada.net/make/x0xb0x/fab/powersupply.html)

  - [VCO](https://ladyada.net/make/x0xb0x/fab/vco.html)

  - [VCF](https://ladyada.net/make/x0xb0x/fab/vcf/index.html)

  - [Envelope](https://ladyada.net/make/x0xb0x/fab/env/index.html)

  - [VCA](https://ladyada.net/make/x0xb0x/fab/vca/index.html)

  - [Headphone](https://ladyada.net/make/x0xb0x/fab/hp-mix/index.html)

  - [I/O Board](https://ladyada.net/make/x0xb0x/fab/ioboard/index.html)

  - [Sequencer](https://ladyada.net/make/x0xb0x/fab/seq/index.html)

  - [Finishing](https://ladyada.net/make/x0xb0x/fab/finish/index.html)
- [Use](https://ladyada.net/make/x0xb0x/manual/index.html)

- [Firmware](http://sourceforge.net/projects/x0xb0x/)

- [Software](https://ladyada.net/make/x0xb0x/software/index.html)

- [Download](https://ladyada.net/make/x0xb0x/download.html)

- [Resources](https://ladyada.net/make/x0xb0x/resc.html)

- [Forums](http://forums.ladyada.net/)

- [Wiki](http://www.ladyada.net/wiki/x0x:x0xd0x)


ladyada.net

Introduction

In this
section, the entire IO board is soldered together and the USB is tested.
Be sure to follow the instructions for how to solder in the surface
mount USB chip.

_Note_: in batch #6 we've started to notice that the optoisolators are possibly made to a different specification. If MIDI out and MIDI thru are working but MIDI in is not, try upping R16 to 120 or 150 ohms!

You
are here

[![](https://ladyada.net/make/x0xb0x/fab/images/ioboard_done_t.jpg)](https://ladyada.net/make/x0xb0x/fab/images/ioboard_done.jpg)

Testing
and soldering order

**If you are concerned that you will not be able to solder the USB chip, we are offering, as an extra service, to prebuild & test USB. Just make sure you request it when you order your kit.**

Since the USB chip is the most difficult part to
solder, this should be done first, so that there is plenty of space
to work in. There are a few techniques for soldering SMD parts.
The two techniques I am a fan of are:


1. Soldering with silver solder as carefully as possible, and then
    using solder wick to clean up
2. Soldering with solder paste, and then using solder wick to clean
    up.

There are a bunch of tutorial sites on this (just search on google!):

- The [SMD \\
tutorial from SILabs](http://www2.silabs.com/public/documents/tpub_doc/anote/Microcontrollers/en/an114.pdf) (just the part about adding parts)
- [Kevin \\
Ro's tutorial](http://www.kevinro.com/newdocs/learningcenter/surface.htm)

Here's a straightforward method for soldering this chip using
solder & wick. The magnifying glass comes in very very handy here! Its essential to check for bridged pins and unconnected pins.

01. If you have flux, spread some on the pads, this will help bridging.
     The solder mask should also help a lot.

    [![](https://ladyada.net/make/x0xb0x/fab/images/usb_before_t.jpg)](https://ladyada.net/make/x0xb0x/fab/images/usb_before.jpg)
02. Place a small amount of solder on a corner pad.
03. Using tweezers, position the chip correctly (the circle on the
     picture matches the circle indent on the chip) and heat the corner
     pad. When the soldered pad is heated up, align the chip in the
     right location, then pull the soldering iron away.

    [![](https://ladyada.net/make/x0xb0x/fab/images/usb_tack1_t.jpg)](https://ladyada.net/make/x0xb0x/fab/images/usb_tack1.jpg)
04. Place a small amount of solder on the iron tip. Tack the opposite
     corner, holding the chip steady with the tweezers.

    [![](https://ladyada.net/make/x0xb0x/fab/images/usb_tack2_t.jpg)](https://ladyada.net/make/x0xb0x/fab/images/usb_tack2.jpg)
05. Double check that you have the chip positioned right.

    ![](https://ladyada.net/make/x0xb0x/fab/images/usb_tacked.jpg)
06. As carefully as possible, solder the remaining pins. Heat where
     the pin and pad meet, then quickly touch some solder to the pin,
     the solder should flow down to the pad.

    ![](https://ladyada.net/make/x0xb0x/fab/images/usb_soldered.jpg)
07. Dont worry if you bridge some pins, just fix it with the wick.

    [![](https://ladyada.net/make/x0xb0x/fab/images/usb_wick_t.jpg)](https://ladyada.net/make/x0xb0x/fab/images/usb_wick.jpg)
08. When you're done, look at the board under a magnifier, or hold
     up to the light at an angle to see all the pins

    ![](https://ladyada.net/make/x0xb0x/fab/images/usb_done.jpg)
09. Ok now that you're done with the USB chip and you're pretty
     sure its soldered correctly, solder in all the rest of the components
     on the IO board. When soldering in the MIDI/DINSYNC connectors,
     make sure to 'pre-stress' them as they are a little flimsy: press
     them back so that the face is flush with the PCB while soldering
     them in. Be sure to use lots of solder on all the connector components
     to make a good mechanical bond.
10. Power the IO board, but don't connect it to the main board
11. Plug in the USB into a computer.
12. The computer should detect a "Serial <-> USB"
     chip and request a driver.
13. Download the [driver \\
     from FTDI](http://www.ftdichip.com/Drivers/FT232-FT245Drivers.htm#VCP). Make sure to grab the VCP driver. Install it.
     Verify that a new COM port is created (under Windows, look
     under hardware control panel)

Parts

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/quarter_stereo_t.jpg) | 1/4" stereo jack | 3 | MIXOUT, MIXIN, HEADPHONE |
| [![](https://ladyada.net/images/parts/eigthjack_t.jpg)](https://ladyada.net/images/parts/eigthjack.jpg) | 1/8" jack | 2 | CV, GATE |
| ![](https://ladyada.net/images/parts/USBjackB_t.jpg) | USB type-B jack | 1 | USB |
| [![](https://ladyada.net/images/parts/DINjack_t.jpg)](https://ladyada.net/images/parts/DINjack.jpg) | MIDI/DINSYNC jack | 4 | DIN1-4 |
| [![](https://ladyada.net/images/parts/1n4148_t.jpg)](https://ladyada.net/images/parts/1n4001_t.jpg) | 1N4148 | 1 | D48 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rBrown_t.gif) | ![](https://ladyada.net/images/parts/rBlack_t.gif) | ![](https://ladyada.net/images/parts/rBlack_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 10 ohm 5% resistor | 2 | R186, R164 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/rBlack_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 22 ohm 5% resistor | 1 | R20 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/rViolet_t.gif) | ![](https://ladyada.net/images/parts/rBlack_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 27 ohm 5% resistor | 2 | R6, R7 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rBrown_t.gif) | ![](https://ladyada.net/images/parts/rBlack_t.gif) | ![](https://ladyada.net/images/parts/rBrown_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 100 ohm 5% resistor | 1 | R16 (see MIDI in note above) |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/rBrown_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 220 ohm 5% resistor | 5 | R13-R15, R18, R19 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rYellow_t.gif) | ![](https://ladyada.net/images/parts/rViolet_t.gif) | ![](https://ladyada.net/images/parts/rBrown_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 470 ohm 5% resistor | 1 | R12 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rBrown_t.gif) | ![](https://ladyada.net/images/parts/rBlack_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 1K 5% resistor | 1 | R17 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rBrown_t.gif) | ![](https://ladyada.net/images/parts/rGreen_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 1.5K 5% resistor | 1 | R8 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 2.2K 5% resistor | 4 | R21-R24 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rYellow_t.gif) | ![](https://ladyada.net/images/parts/rViolet_t.gif) | ![](https://ladyada.net/images/parts/rRed_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 4.7K 5% resistor | 1 | R9 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rBrown_t.gif) | ![](https://ladyada.net/images/parts/rBlack_t.gif) | ![](https://ladyada.net/images/parts/rOrange_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 10K 5% resistor | 2 | R10, R11 |
| |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| ![](https://ladyada.net/images/parts/resleft_t.gif) | ![](https://ladyada.net/images/parts/rBrown_t.gif) | ![](https://ladyada.net/images/parts/rBlack_t.gif) | ![](https://ladyada.net/images/parts/rYellow_t.gif) | ![](https://ladyada.net/images/parts/spacer_t.gif) | ![](https://ladyada.net/images/parts/rGold_t.gif) | ![](https://ladyada.net/images/parts/resright_t.gif) | | 100K 5% resistor | 4 | R25-R28 |
| [![](https://ladyada.net/images/parts/033poly_t.jpg)](https://ladyada.net/images/parts/033poly.jpg) | .033uF (2A333K) polyester capacitor | 1 | C201 |
| [![](https://ladyada.net/images/parts/104cerm_t.jpg)](https://ladyada.net/images/parts/104cerm.jpg) | .1uF (104) ceramic | 2 | C202, C204 |
| [![](https://ladyada.net/images/parts/10uf_t.jpg)](https://ladyada.net/images/parts/10uf.jpg) | 10uF electrolytic capacitor | 2 | C203, C205 |
| [![](https://ladyada.net/images/parts/2sc536_t.jpg)](https://ladyada.net/images/parts/2sc536.jpg) | 2SC536F, TO-92 NPN transistor | 1 | Q50 |
| [![](https://ladyada.net/images/parts/4N37_t.jpg)](https://ladyada.net/images/parts/4N37.jpg) | 4N37 optoisolator | 1 | IC24 |
| [![](https://ladyada.net/images/parts/ft232_t.jpg)](https://ladyada.net/images/parts/ft232.jpg) | FT232 USB chip | 1 | IC25 |
| [![](https://ladyada.net/images/parts/xtal6m_t.jpg)](https://ladyada.net/images/parts/xtal6m.jpg) | 6MHz ceramic resonator | 1 | XTAL2 |

May 17, 2011 20:07
