#!/usr/bin/env python3
"""Correct negative Eagle pad flags in generated XML only; preserve sources."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[2]
VAL = Path(__file__).resolve().parent
OUT = VAL / "repaired-eagle-xml"
REFERENCE = "https://raw.githubusercontent.com/alexer/pyeagle/master/eagle.py"


def original_packages(source_name):
    root = ET.parse(VAL / "decoded-xml" / (source_name + ".restored-fields.xml")).getroot()
    result = {}
    for library in root.findall(".//libraries/library"):
        for package in library.findall(".//packages/package"):
            key = (library.get("name"), package.get("name"))
            assert key not in result, key
            result[key] = package
    return result


reports = {}
for target_name, source_name in (
    ("mainboard.brd", "mainboard.brd"),
    ("ioboard.brd", "ioboard.brd"),
    ("ioboard-schema-extra-footprints.brd", "ioboard.sch"),
):
    source_raw = (BASE / source_name).read_bytes()
    source_packages = original_packages(source_name)
    target = OUT / target_name
    old_bytes = target.read_bytes()
    root = ET.fromstring(old_bytes)
    changes, checked = [], Counter()
    for library in root.findall(".//libraries/library"):
        for package in library.findall(".//packages/package"):
            key = (library.get("name"), package.get("name"))
            source_package = source_packages[key]
            pads = [n for n in package if n.tag in ("pad", "smd")]
            source_pads = [n for n in source_package if n.tag in ("pad", "smd")]
            assert len(pads) == len(source_pads), key
            for pad, source_pad in zip(pads, source_pads):
                assert pad.tag == source_pad.tag and pad.get("name") == source_pad.get("name"), key
                offset = int(source_pad.get("_binary_offset"))
                record = source_raw[offset:offset + 24]
                assert record[0] == (0x2A if pad.tag == "pad" else 0x2B)
                fields = [("stop", 1), ("thermals", 4)]
                if pad.tag == "smd":
                    fields.append(("cream", 2))
                for field, mask in fields:
                    expected = "no" if record[18] & mask else "yes"
                    checked[field] += 1
                    if pad.get(field) != expected:
                        changes.append(dict(library=key[0], package=key[1],
                            pad=pad.get("name"), record_offset=offset,
                            raw_flag_byte=record[18], field=field,
                            before=pad.get(field), after=expected))
                        pad.set(field, expected)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(target, encoding="utf-8", xml_declaration=True)
    reports[target_name] = dict(source=source_name,
        source_sha256=hashlib.sha256(source_raw).hexdigest(),
        before_sha256=hashlib.sha256(old_bytes).hexdigest(),
        after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        checked_fields=dict(checked), changed_fields=len(changes), changes=changes,
        reference=REFERENCE,
        method="PAD/SMD byte 18 bits 0/2 (and SMD bit 1) are negative flags; XML boolean is the inverse. Via stop and polygon flags are unchanged.")
(OUT / "pad-flag-correction-report.json").write_text(json.dumps(reports, indent=2) + "\n")
for name, report in reports.items():
    print(name, report["checked_fields"], "changed", report["changed_fields"])
