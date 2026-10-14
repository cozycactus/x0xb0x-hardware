#!/usr/bin/env python3
"""Restore source Eagle sizing rules omitted from generated conversion XML."""

import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[2]
VAL = Path(__file__).resolve().parent
OUT = VAL / "repaired-eagle-xml"
reports = {}

for stem in ("mainboard", "ioboard"):
    raw = (BASE / (stem + ".brd")).read_bytes()
    record_end = int.from_bytes(raw[4:8], "little") * 24
    start = raw.index(b"\x10\x04\x00\x20", record_end)
    length = struct.unpack_from("<I", raw, start + 4)[0] - 4
    payload = raw[start + 8:start + 8 + length]
    magic = payload.index(b"\x78\x56\x34\x12")
    body = payload[magic:]
    # The serialized rules use the 426-byte layout, independently of the
    # drawing header's 4.13 version. The payload length identifies this layout.
    assert len(body) == 426
    ratios = struct.unpack_from("<7d", body, 88)
    limits = struct.unpack_from("<14I", body, 144)
    shapes = struct.unpack_from("<3i", body, 200)
    mask_ratios = struct.unpack_from("<2d", body, 212)
    mask_limits = struct.unpack_from("<5I", body, 228)
    roundness = struct.unpack_from("<dII", body, 248)
    elongation = body[300:302]
    names = ("PadTop", "PadInner", "PadBottom", "ViaOuter", "ViaInner")
    params = {}
    for index, name in enumerate(names):
        params["rv" + name] = format(ratios[index], ".12g")
        params["rlMin" + name] = format(limits[index * 2] * 0.0001, ".12g") + "mm"
        params["rlMax" + name] = format(limits[index * 2 + 1] * 0.0001, ".12g") + "mm"
    for name, value in zip(("psTop", "psBottom", "psFirst"), shapes):
        params[name] = str(value)
    for name, value in zip(("mvStopFrame", "mvCreamFrame"), mask_ratios):
        params[name] = format(value, ".12g")
    for name, value in zip(("mlMinStopFrame", "mlMaxStopFrame", "mlMinCreamFrame", "mlMaxCreamFrame"), mask_limits):
        params[name] = format(value * 0.0001, ".12g") + "mm"
    params["srRoundness"] = format(roundness[0], ".12g")
    for name, value in zip(("srMinRoundness", "srMaxRoundness"), roundness[1:]):
        params[name] = format(value * 0.0001, ".12g") + "mm"
    for name, value in zip(("psElongationLong", "psElongationOffset"), elongation):
        params[name] = str(value)
    target = OUT / (stem + ".brd")
    root = ET.parse(target).getroot()
    rules = root.find(".//designrules")
    assert rules is not None
    byname = {node.get("name"): node for node in rules.findall("param")}
    changes = []
    for name, value in params.items():
        node = byname.get(name)
        if node is None:
            node = ET.SubElement(rules, "param", {"name": name})
        old = node.get("value")
        if old != value:
            changes.append(dict(name=name, before=old, after=value))
            node.set("value", value)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(target, encoding="utf-8", xml_declaration=True)
    vias = root.findall(".//via")
    via_diameters = []
    for via in vias:
        drill = float(via.get("drill"))
        explicit = float(via.get("diameter"))
        annulus = max(limits[6] * 0.0001, min(drill * ratios[3], limits[7] * 0.0001))
        via_diameters.append(explicit or round(drill + 2 * annulus, 7))
    reports[stem] = dict(source_sha256=hashlib.sha256(raw).hexdigest(),
        rules_magic_offset=start + 8 + magic, rules_layout_bytes=len(body),
        raw_ratios=ratios, raw_limits_units_0_1um=limits,
        changes=changes, corrected_xml_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        source_derived_via_diameters_mm=via_diameters,
        reference="https://raw.githubusercontent.com/alexer/pyeagle/master/eagle.py",
        finding="Automatic via diameter needed the source 8mil minimum annulus; importer fallback is 10mil. Pad and mask/paste defaults match source. Offset elongation differs but no offset pads exist in these boards.")
    assert all(abs(diameter - 1.0064) < 0.0000001 for diameter in via_diameters)
(OUT / "designrule-correction-report.json").write_text(json.dumps(reports, indent=2) + "\n")
for stem, report in reports.items():
    print(stem, "restored rules", len(report["changes"]),
          "source via diameters mm", report["source_derived_via_diameters_mm"])
