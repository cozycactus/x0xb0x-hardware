#!/usr/bin/env python3
"""Read-only structure inventory of legacy Eagle sources using the fork's spec.

This helper does not convert a design or modify an Eagle source. It reads the
24-byte binary record table in eagle_bin_parser.cpp and independently inventories
placed objects. Long text is decoded in the serialized field order used by the
fork's postprocFreeText fallback; pointer bytes are retained separately so
that a later comparison can verify the importer resolved every long string.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


def split_cpp(text):
    result, start, depth, quote, escape = [], 0, 0, None, False
    for i, ch in enumerate(text):
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "{(":
            depth += 1
        elif ch in "})":
            depth -= 1
        elif ch == "," and depth == 0:
            result.append(text[start:i].strip())
            start = i + 1
    result.append(text[start:].strip())
    return [x for x in result if x]


def load_spec(path):
    source = path.read_text()
    ids = {key: int(value, 16) for key, value in re.findall(
        r"(EGKW_SECT_\w+)\s*=\s*(0x[0-9A-Fa-f]+)", source)}
    spec = source[source.index("const SCRIPT_ROW g_script[] = {"):]
    spec = spec[spec.index("{") + 1:spec.index("};")]
    spec = re.sub(r"//[^\n]*", "", spec)
    rows = []
    for row in split_cpp(spec):
        fields = split_cpp(row.strip()[1:-1])
        if len(fields) != 6 or fields[0] == "0":
            continue
        cmd = ids.get(fields[0])
        if cmd is None:
            cmd = int(fields[0], 0)
        subs = []
        for sub in split_cpp(fields[4][1:-1]):
            if sub == "TERM_S":
                continue
            off, length, kind, name = split_cpp(sub[1:-1])
            subs.append((int(off), int(length), kind,
                         None if name == "nullptr" else json.loads(name)))
        attrs = []
        for attr in split_cpp(fields[5][1:-1]):
            if attr == "TERM_A":
                continue
            name, kind, off, length = split_cpp(attr[1:-1])
            attrs.append((json.loads(name), kind, int(off), length))
        rows.append(dict(cmd=cmd, mask=int(fields[1], 0),
                         name=None if fields[2] == "nullptr" else json.loads(fields[2]),
                         subs=subs, attrs=attrs))
    return rows


class Eagle:
    def __init__(self, path, spec):
        self.path, self.data, self.records = path, path.read_bytes(), []
        self.block_count = int.from_bytes(self.data[4:8], "little")
        self.version = f"{self.data[8]}.{self.data[9]}"
        assert self.data[:2] in (b"\x10\x80", b"\x10\x00")
        assert len(self.data) >= self.block_count * 24
        self.long_refs = []
        for index in range(self.block_count):
            raw = self.data[index * 24:(index + 1) * 24]
            tag = int.from_bytes(raw[:2], "big")
            matched = []
            for row in spec:
                if tag & row["mask"] != row["cmd"]:
                    continue
                if self.data[8] > 3 and row["cmd"] in (0x2a00, 0x2b00):
                    if any(name == "name" and off == 16
                           for name, _, off, _ in row["attrs"]):
                        continue
                matched.append(row)
            assert matched, (path.name, index, hex(tag))
            row = matched[0]
            attrs, string_order = {}, []
            for name, kind, off, length in row["attrs"]:
                if kind == "T_STR":
                    length = int(length, 0)
                    value = raw[off:off + length]
                    attrs[name] = value.split(b"\0")[0].decode("utf-8", "replace")
                    string_order.append(name)
                    if value[:1] == b"\x7f":
                        self.long_refs.append(dict(index=index, field=name,
                            pointer=int.from_bytes(raw[off + 1:off + 5], "little"),
                            raw_field_hex=value.hex()))
                elif kind in ("T_INT", "T_UINT"):
                    attrs[name] = int.from_bytes(raw[off:off + int(length, 0)],
                                                "little", signed=kind == "T_INT")
            if row["cmd"] == 0x3a00:
                # The fork leaves this record undecoded. The source's bus has
                # its free-text marker at offset 4 and owns the next 3 records.
                # Retain it so its string does not shift every subsequent net.
                value = raw[4:24]
                attrs["name"] = value.split(b"\0")[0].decode("utf-8", "replace")
                string_order.append("name")
                if value[:1] == b"\x7f":
                    self.long_refs.append(dict(index=index, field="name",
                        pointer=int.from_bytes(raw[5:9], "little"),
                        raw_field_hex=value.hex(), independent_bus_decode=True))
            self.records.append(dict(index=index, id=row["cmd"], tag=tag,
                                     kind=row["name"], raw=raw, attrs=attrs,
                                     string_order=string_order, spec=row,
                                     children=[]))
        self.read_spans()
        self.decode_free_text()

    def read_spans(self):
        # For placement and signal membership, these records declare the number
        # of following physical 24-byte records in their little-endian word at
        # offset 2. Inventory that bounded span independently of the fork's
        # recursive DOM construction, whose SS_DIRECT modes can consume siblings.
        for node in self.records:
            if node["id"] not in (0x1c00, 0x1e00, 0x2e00, 0x3000, 0x3800, 0x3a00):
                continue
            count = int.from_bytes(node["raw"][2:4], "little")
            start = node["index"] + 1
            assert start + count <= self.block_count
            node["children"] = self.records[start:start + count]

    def decode_free_text(self):
        start = self.block_count * 24
        self.texts, self.text_offsets = [], []
        if self.data[start:start + 2] == b"\x13\x12":
            length = int.from_bytes(self.data[start + 4:start + 6], "little", signed=True)
            blob = self.data[start + 8:start + 8 + length + 4]
            pos = 0
            while pos < len(blob) and blob[pos]:
                end = blob.index(0, pos)
                self.text_offsets.append(pos)
                self.texts.append(blob[pos:end].decode("utf-8", "replace"))
                pos = end + 1
        order = {
            0x2f00: ["value", "name"], 0x3800: ["value", "name"],
            0x3600: ["name", "table"], 0x1e00: ["name", "desc"],
            0x1900: ["library", "desc"], 0x3700: ["name", "desc", "prefix"],
            0x4200: ["attribute", "symbol"],
        }
        lookup = {(r["index"], r["field"]): r for r in self.long_refs}
        cursor = 0
        for node in self.records:
            for key in order.get(node["id"], node["string_order"]):
                ref = lookup.get((node["index"], key))
                if ref:
                    assert cursor < len(self.texts), (self.path.name, cursor)
                    node["attrs"][key] = self.texts[cursor]
                    ref["sequential_text"] = self.texts[cursor]
                    ref["text_blob_offset"] = self.text_offsets[cursor]
                    cursor += 1
        self.free_text_consumed = cursor
        assert cursor == len(self.texts), (self.path.name, cursor, len(self.texts))

    def by_id(self, tag):
        return [r for r in self.records if r["id"] == tag]

    def common(self):
        pointers = defaultdict(list)
        for ref in self.long_refs:
            pointers[ref["pointer"]].append(ref)
        return dict(file=str(self.path.resolve()),
                    sha256=hashlib.sha256(self.data).hexdigest(),
                    eagle_version=self.version, file_bytes=len(self.data),
                    records_24_bytes=self.block_count,
                    trailing_bytes=len(self.data) - self.block_count * 24,
                    all_records_match_fork_parser=True,
                    declared_placement_and_signal_spans_within_file=True,
                    record_counts=dict(Counter(r["kind"] or f"unknown_{r['id']:04x}"
                                               for r in self.records)),
                    free_text_strings=len(self.texts),
                    sequential_long_text_refs=self.free_text_consumed,
                    long_text_resolution="Serialized field order; every free-text string consumed exactly once. Mainboard bus decoded independently at offset 4.",
                    long_text_references=self.long_refs,
                    repeated_pointers_with_distinct_strings={str(k): v for k, v in pointers.items()
                        if len({ref["sequential_text"] for ref in v}) > 1})

    def board(self):
        report = self.common()
        libraries, current = [], None
        for rec in self.records:
            if rec["id"] == 0x1900:
                current = dict(name=rec["attrs"].get("library"), packages=[])
                libraries.append(current)
            elif rec["id"] == 0x1e00:
                descendants = self.records[rec["index"] + 1:
                    rec["index"] + 1 + int.from_bytes(rec["raw"][2:4], "little")]
                current["packages"].append(dict(name=rec["attrs"].get("name"),
                    holes=sum(r["id"] == 0x2800 for r in descendants),
                    pads=[dict(name=r["attrs"].get("name"),
                               type="through_hole" if r["id"] == 0x2a00 else "smd")
                          for r in descendants if r["id"] in (0x2a00, 0x2b00)]))
        elements = []
        for rec in self.by_id(0x2e00):
            attrs = rec["attrs"]
            meta = next(r["attrs"] for r in rec["children"] if r["id"] == 0x2f00)
            library = libraries[attrs["library"] - 1]
            package = library["packages"][attrs["package"] - 1]
            elements.append(dict(reference=meta["name"], value=meta["value"],
                library=library["name"], package=package["name"],
                x_mm=attrs["x"] * 0.0001, y_mm=attrs["y"] * 0.0001,
                rotation_degrees=(int.from_bytes(rec["raw"][16:18], "little") & 4095) * 360 / 4096,
                mirrored=bool(rec["raw"][17] & 0x10),
                mechanical_holes=package["holes"],
                pads=[dict(pad, net=None) for pad in package["pads"]]))
        signals, errors, memberships = [], [], []
        for signal in self.by_id(0x1c00):
            contacts = []
            for rec in signal["children"]:
                if rec["id"] != 0x3e00:
                    continue
                ei, pi = rec["attrs"]["partnumber"], rec["attrs"]["pin"]
                assert 1 <= ei <= len(elements)
                element = elements[ei - 1]
                assert 1 <= pi <= len(element["pads"])
                pad = element["pads"][pi - 1]
                if pad["net"] is not None:
                    errors.append(dict(reference=element["reference"], pad=pad["name"],
                                       first=pad["net"], second=signal["attrs"]["name"]))
                pad["net"] = signal["attrs"]["name"]
                contact = dict(reference=element["reference"], pad=pad["name"])
                contacts.append(contact)
                memberships.append(dict(contact, net=pad["net"]))
            signals.append(dict(name=signal["attrs"]["name"], contacts=contacts,
                                record_index=signal["index"]))
        first_signal = min(r["index"] for r in self.by_id(0x1c00))
        signal_records = self.records[first_signal:]
        polygon_children = set()
        for polygon in signal_records:
            if polygon["id"] != 0x2100:
                continue
            count = int.from_bytes(polygon["raw"][2:4], "little")
            polygon_children.update(range(polygon["index"] + 1, polygon["index"] + 1 + count))
        all_wires = [r for r in signal_records if r["id"] in (0x2200, 0x2400)]
        wires = [r for r in all_wires if r["index"] not in polygon_children]
        polygon_wires = [r for r in all_wires if r["index"] in polygon_children]
        airwires = [dict(record_index=r["index"], layer=r["raw"][3] & 127,
                         x1_mm=r["attrs"].get("linetype_0_x1", 0) * 0.0001,
                         y1_mm=r["attrs"].get("linetype_0_y1", 0) * 0.0001,
                         x2_mm=r["attrs"].get("linetype_0_x2", 0) * 0.0001,
                         y2_mm=r["attrs"].get("linetype_0_y2", 0) * 0.0001)
                    for r in wires if r["raw"][3] & 127 == 19]
        placed = Counter(pad["type"] for element in elements for pad in element["pads"])
        report.update(library_definition_count=len(libraries),
                      library_package_definition_count=sum(len(lib["packages"]) for lib in libraries),
                      library_pad_definition_count=len(self.by_id(0x2a00)) + len(self.by_id(0x2b00)),
                      placed_footprints=len(elements), placed_pads=sum(placed.values()),
                      placed_mechanical_holes=sum(el["mechanical_holes"] for el in elements),
                      placed_pad_types=dict(placed),
                      unconnected_pads=sum(pad["net"] is None for el in elements for pad in el["pads"]),
                      signal_record_count=len(signals), unique_signal_names=len({s["name"] for s in signals}),
                      contactrefs=len(memberships), duplicate_pad_memberships=errors,
                      signal_wire_records_by_eagle_layer=dict(Counter(str(r["raw"][3] & 127) for r in wires)),
                      polygon_edge_wire_records_by_eagle_layer=dict(Counter(str(r["raw"][3] & 127) for r in polygon_wires)),
                      signal_wire_records_including_polygon_edges_by_eagle_layer=dict(Counter(str(r["raw"][3] & 127) for r in all_wires)),
                      signal_vias=sum(r["id"] == 0x2900 for r in signal_records),
                      signal_polygons_by_eagle_layer=dict(Counter(str(r["raw"][18] & 127)
                          for r in signal_records if r["id"] == 0x2100)),
                      original_airwires=airwires,
                      elements=elements, signals=signals,
                      pad_net_memberships=memberships,
                      notes=["Library pad definitions are counted separately from instantiated board pads.",
                             "Coordinates use the binary format's 0.1 micrometre units before KiCad axis/origin transforms.",
                             "Wire counts exclude footprint drawings and plain-board graphics."])
        return report

    def schematic(self):
        report = self.common()
        parts = []
        for rec in self.by_id(0x3800):
            parts.append(dict(record_index=rec["index"], **rec["attrs"],
                placed_gate_instances=sum(r["id"] == 0x3000 for r in rec["children"])))
        first_sheet = min(r["index"] for r in self.by_id(0x1a00))
        sheet_records = self.records[first_sheet:]
        report.update(library_definition_count=len(self.by_id(0x1500)),
                      library_symbol_definitions=len(self.by_id(0x1d00)),
                      library_package_definitions=len(self.by_id(0x1e00)),
                      sheet_count=len(self.by_id(0x1a00)),
                      part_records=len(parts), unique_part_references=len({p["name"] for p in parts}),
                      placed_gate_instances=len(self.by_id(0x3000)),
                      net_records=len(self.by_id(0x1f00)),
                      net_names=[r["attrs"]["name"] for r in self.by_id(0x1f00)],
                      net_segments=len(self.by_id(0x2000)),
                      pin_connection_records=len(self.by_id(0x3d00)),
                      junctions=sum(r["id"] == 0x2700 for r in sheet_records),
                      net_bus_labels=sum(r["id"] == 0x3300 for r in sheet_records),
                      bus_records=[dict(record_index=r["index"], name=r["attrs"].get("name"),
                                        raw_hex=r["raw"].hex())
                                   for r in sheet_records if r["id"] == 0x3a00],
                      sheet_wire_records_by_eagle_layer=dict(Counter(str(r["raw"][3] & 127)
                          for r in sheet_records if r["id"] in (0x2200, 0x2400))),
                      parts=parts,
                      limitations=["The fork maps 0x3a00 SCHEMABUS to an unnamed leaf with no fields. "
                                   "Its rename pass does not map that record to XML bus. The mainboard's "
                                   "single bus is therefore a potential fidelity gap requiring visual/electrical checking."])
        catalog = self.schematic_libraries()
        report["raw_library_ordinals"] = catalog
        memberships = []
        part_records = self.by_id(0x3800)
        for net in self.by_id(0x1f00):
            count = int.from_bytes(net["raw"][2:4], "little")
            descendants = self.records[net["index"] + 1:net["index"] + 1 + count]
            for conn in descendants:
                if conn["id"] != 0x3d00:
                    continue
                part_no, gate_no, pin_no = (int.from_bytes(conn["raw"][off:off + 2], "little")
                                            for off in (4, 6, 8))
                assert 1 <= part_no <= len(part_records)
                part = part_records[part_no - 1]["attrs"]
                lib = catalog[part["lib"] - 1]
                device = lib["devicesets"][part["device"] - 1]
                gate = device["gates"][gate_no - 1]
                symbol = lib["symbols"][gate["symbol_ordinal"] - 1]
                pin = symbol["pins"][pin_no - 1]
                variant = device["variants"][part["variant"] - 1]
                pads = [connection["pad"] for connection in variant["connects"]
                        if connection["gate_ordinal"] == gate_no and connection["pin_ordinal"] == pin_no]
                memberships.append(dict(record_index=conn["index"], reference=part["name"],
                    net=net["attrs"]["name"], gate=gate["name"], pin=pin["name"], pads=pads,
                    part_ordinal=part_no, gate_ordinal=gate_no, pin_ordinal=pin_no,
                    has_package=variant["package_ordinal"] > 0))
        report["source_schematic_pin_net_memberships"] = memberships
        return report

    def schematic_libraries(self):
        catalog = []

        def span(node):
            count = int.from_bytes(node["raw"][2:4], "little")
            return self.records[node["index"] + 1:node["index"] + 1 + count]

        for library in self.by_id(0x1500):
            start = library["index"] + 1
            dev_span = library["attrs"]["devsubsecs"]
            sym_span = library["attrs"]["symsubsecs"]
            pkg_span = library["attrs"]["pacsubsecs"]
            dev_records = self.records[start:start + dev_span]
            sym_records = self.records[start + dev_span:start + dev_span + sym_span]
            pkg_records = self.records[start + dev_span + sym_span:
                                       start + dev_span + sym_span + pkg_span]
            assert not dev_records or dev_records[0]["id"] == 0x1700
            assert not sym_records or sym_records[0]["id"] == 0x1800
            assert not pkg_records or pkg_records[0]["id"] == 0x1900
            packages = [dict(record_index=pkg["index"], name=pkg["attrs"]["name"],
                             pads=[dict(name=pad["attrs"]["name"], record_index=pad["index"])
                                   for pad in span(pkg) if pad["id"] in (0x2a00, 0x2b00)])
                        for pkg in pkg_records if pkg["id"] == 0x1e00]
            symbols = [dict(record_index=symbol["index"], name=symbol["attrs"]["name"],
                            pins=[dict(name=pin["attrs"]["name"], record_index=pin["index"])
                                  for pin in span(symbol) if pin["id"] == 0x2c00])
                       for symbol in sym_records if symbol["id"] == 0x1d00]
            devices = []
            for device in dev_records:
                if device["id"] != 0x3700:
                    continue
                attrs = device["attrs"]
                start = device["index"] + 1
                variant_records = self.records[start:start + attrs["variants"]]
                gate_records = self.records[start + attrs["variants"]:
                                            start + attrs["variants"] + attrs["gates"]]
                assert all(gate["id"] == 0x2d00 for gate in gate_records)
                gates = [dict(record_index=gate["index"], name=gate["attrs"]["name"],
                              symbol_ordinal=gate["attrs"]["symno"],
                              symbol=symbols[gate["attrs"]["symno"] - 1]["name"])
                         for gate in gate_records]
                pin_bits = device["raw"][7] & 15
                variants = []
                for variant in variant_records:
                    if variant["id"] != 0x3600:
                        continue
                    package_no = variant["attrs"]["package"]
                    package = packages[package_no - 1] if package_no else None
                    entries = [byte for conn in span(variant) if conn["id"] == 0x3c00
                               for byte in conn["raw"][2:24]]
                    connects = []
                    if package and entries:
                        assert pin_bits in (4, 6)
                        assert len(entries) >= len(package["pads"])
                        for pad, entry in zip(package["pads"], entries):
                            if not entry:
                                continue
                            gate_no, pin_no = entry >> pin_bits, entry & ((1 << pin_bits) - 1)
                            gate = gates[gate_no - 1]
                            symbol = symbols[gate["symbol_ordinal"] - 1]
                            pin = symbol["pins"][pin_no - 1]
                            connects.append(dict(pad=pad["name"], gate_ordinal=gate_no,
                                                 pin_ordinal=pin_no, gate=gate["name"],
                                                 pin=pin["name"]))
                    variants.append(dict(record_index=variant["index"],
                        name=variant["attrs"]["name"], package_ordinal=package_no,
                        package=package["name"] if package else None, connects=connects,
                        raw_connection_entries=entries))
                devices.append(dict(record_index=device["index"], name=attrs["name"],
                    prefix=attrs["prefix"], desc=attrs["desc"], pin_index_bits=pin_bits,
                    gates=gates, variants=variants))
            catalog.append(dict(record_index=library["index"], name=library["attrs"]["name"],
                                devicesets=devices, symbols=symbols, packages=packages))
        return catalog


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--parser-source", type=Path,
        default=Path("/Users/ruslanmigirov/cozycactus/kicad/common/io/eagle/eagle_bin_parser.cpp"))
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name("eagle-source-structure.json"))
    args = parser.parse_args()
    spec = load_spec(args.parser_source)
    result = dict(format="legacy-eagle-source-structure-v1",
        parser_spec=str(args.parser_source.resolve()),
        parser_spec_sha256=hashlib.sha256(args.parser_source.read_bytes()).hexdigest(),
        provenance="CVS/Repository=hardware; CVS/Root=:pserver:anonymous@a.cvs.sourceforge.net:/cvsroot/x0xb0x; all files CVS revision 1.1, March 2007.",
        method="Read-only independent Python inventory of fixed-length records using the checked-out fork's record table; no design conversion.",
        caution="Long text is decoded in serialized free-text order, not by absolute pointer consensus. Raw pointer bytes are preserved for comparison; these four files have no equal pointers resolving to different strings.",
        files={})
    for stem in ("mainboard", "ioboard"):
        for suffix in (".sch", ".brd"):
            eagle = Eagle(args.source_dir / (stem + suffix), spec)
            result["files"][stem + suffix] = eagle.board() if suffix == ".brd" else eagle.schematic()
    result["source_pair_consistency"] = {}
    for stem in ("mainboard", "ioboard"):
        board = result["files"][stem + ".brd"]
        sch = result["files"][stem + ".sch"]
        board_refs = {el["reference"]: el for el in board["elements"]}
        sch_refs = {part["name"]: part for part in sch["parts"]}
        board_net_names = {signal["name"] for signal in board["signals"]}
        sch_net_names = set(sch["net_names"])
        board_pad_nets = {(entry["reference"], entry["pad"]): entry["net"]
                          for entry in board["pad_net_memberships"]}
        sch_pad_nets = {(entry["reference"], pad): entry["net"]
                       for entry in sch["source_schematic_pin_net_memberships"]
                       for pad in entry["pads"]}
        result["source_pair_consistency"][stem] = dict(
            board_only_references=sorted(board_refs.keys() - sch_refs.keys()),
            schematic_only_references=sorted(sch_refs.keys() - board_refs.keys()),
            shared_reference_value_mismatches=[dict(reference=ref,
                board_value=board_refs[ref]["value"], schematic_value=sch_refs[ref]["value"])
                for ref in sorted(board_refs.keys() & sch_refs.keys())
                if board_refs[ref]["value"] != sch_refs[ref]["value"]],
            board_only_net_names=sorted(board_net_names - sch_net_names),
            schematic_only_net_names=sorted(sch_net_names - board_net_names),
            board_signals_without_contactrefs=[signal["name"] for signal in board["signals"]
                                              if not signal["contacts"]],
            shared_pad_net_mismatches=[dict(reference=ref, pad=pad,
                schematic_net=sch_pad_nets[(ref, pad)], board_net=board_pad_nets[(ref, pad)])
                for ref, pad in sorted(board_pad_nets.keys() & sch_pad_nets.keys())
                if board_pad_nets[(ref, pad)] != sch_pad_nets[(ref, pad)]],
            schematic_pad_connections_absent_from_board=[dict(reference=ref, pad=pad,
                net=sch_pad_nets[(ref, pad)]) for ref, pad in sorted(sch_pad_nets.keys() - board_pad_nets.keys())],
            board_pad_connections_absent_from_schematic=[dict(reference=ref, pad=pad,
                net=board_pad_nets[(ref, pad)]) for ref, pad in sorted(board_pad_nets.keys() - sch_pad_nets.keys())],
            original_pair_notes=[
                "Mainboard has 139 original PCB signal records without pad contactrefs; these account for all 139 board-only net names.",
                "Mainboard has seven original board-only U$ references. These are source differences, not conversion losses.",
            ] if stem == "mainboard" else [])
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(args.output)
    for name, info in result["files"].items():
        print(name, {key: info[key] for key in ("eagle_version", "records_24_bytes",
              "free_text_strings", "sequential_long_text_refs")})
        if name.endswith(".brd"):
            print({key: info[key] for key in ("placed_footprints", "placed_pads", "unconnected_pads",
                  "signal_record_count", "unique_signal_names", "contactrefs", "duplicate_pad_memberships")})
    print("Saved", args.output)


if __name__ == "__main__":
    main()
