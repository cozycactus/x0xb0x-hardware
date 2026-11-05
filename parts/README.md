# Parts order list

[`x0xb0x-parts-order.md`](x0xb0x-parts-order.md) lists the parts for one x0xb0x, with the same rows in [`x0xb0x-parts-order.csv`](x0xb0x-parts-order.csv). Each row gives the original part, the part to buy now, its Mouser number, and the stock and price read on the date shown. Rows also carry the substitutes for rare parts and fit notes checked against the KiCad footprints.

Both lists are generated, so edit the scripts and not the lists:

| File | What it does |
|---|---|
| `scripts/bom_rows.py` | Holds every row. The block at its end overrides the rows above it with the Mouser re-read |
| `scripts/report_template.md` | Holds the text around the table: rare parts, fit checks, open questions, limits |
| `scripts/build_table.py` | Writes both lists and `work/table.md`, and checks every reference and quantity against the boards |
| `scripts/extract_footprints.py` | Reads both KiCad boards into `work/footprints.json` |

Rebuild from the repository root:

```bash
python3 -I parts/scripts/extract_footprints.py kicad-working/mainboard/mainboard.kicad_pcb kicad-working/ioboard/ioboard.kicad_pcb
```

```bash
python3 -I parts/scripts/build_table.py
```

Stock and prices change after the dates in each row. Datasheets are linked, not copied. The link to the signal-integrity study points to `../../x0xb0x-si-emc/`, a folder beside this repository that isn't part of it.

This folder moved here on 2026-11-06 from a separate folder with no version control. Only links changed: local copies of four datasheets became links to their makers' pages.
