#!/usr/bin/env python3
"""Compare imported KiCad PCBs with the independent Eagle source inventory.

Reads only source inventory and native PCB files. Writes a comparison report;
never modifies either design. Exact pad-number/net-name multisets are compared
per reference, including repeated pad numbers and unconnected pads.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def tokens(text):
    """Tokenize KiCad S-expressions, preserving quoted/escaped string values."""
    pos, length = 0, len(text)
    while pos < length:
        ch = text[pos]
        if ch.isspace():
            pos += 1
        elif ch == ";":
            end = text.find("\n", pos)
            pos = length if end < 0 else end + 1
        elif ch in "()":
            yield ch, False
            pos += 1
        elif ch == '"':
            pos += 1
            value = []
            while pos < length:
                ch = text[pos]
                pos += 1
                if ch == '"':
                    break
                if ch == "\\":
                    if pos >= length:
                        raise ValueError("Unterminated quoted escape")
                    escaped = text[pos]
                    pos += 1
                    value.append({"n": "\n", "r": "\r", "t": "\t"}.get(escaped, escaped))
                else:
                    value.append(ch)
            else:
                raise ValueError("Unterminated quoted string")
            yield "".join(value), True
        else:
            start = pos
            while pos < length and not text[pos].isspace() and text[pos] not in "()":
                pos += 1
            yield text[start:pos], False


def parse_sexpr(text):
    stack, roots = [], []
    for token, quoted in tokens(text):
        if not quoted and token == "(":
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif not quoted and token == ")":
            if not stack:
                raise ValueError("Unexpected closing parenthesis")
            stack.pop()
        else:
            if not stack:
                raise ValueError("Atom outside S-expression")
            stack[-1].append(token)
    if stack:
        raise ValueError("Unclosed S-expression")
    if len(roots) != 1 or not roots[0] or roots[0][0] != "kicad_pcb":
        raise ValueError("Expected one kicad_pcb root")
    return roots[0]


def children(node, name):
    return [item for item in node if isinstance(item, list) and item and item[0] == name]


def one(node, name):
    matches = children(node, name)
    return matches[0] if matches else None


def property_value(footprint, name, legacy):
    for prop in children(footprint, "property"):
        if len(prop) >= 3 and prop[1] == name:
            return prop[2]
    for text in children(footprint, "fp_text"):
        if len(text) >= 3 and text[1] == legacy:
            return text[2]
    return None


def native_reference(reference):
    """KiCad's Eagle importer appends 0 when a reference ends in a nondigit."""
    return reference if reference and reference[-1].isdigit() else reference + "0"


def inventory_pcb(path):
    data = path.read_bytes()
    root = parse_sexpr(data.decode("utf-8"))
    nets = {net[1]: net[2] for net in children(root, "net") if len(net) >= 3}
    elements, errors, mechanical_holes, net_names = [], [], 0, set(nets.values())
    for footprint in children(root, "footprint") + children(root, "module"):
        pads = []
        reference = property_value(footprint, "Reference", "reference")
        for pad in children(footprint, "pad"):
            if pad[2] == "np_thru_hole" and pad[1] == "":
                mechanical_holes += 1
                continue
            net = one(pad, "net")
            net_name = None
            if net and len(net) >= 2:
                if len(net) >= 3:
                    net_name = net[2]
                elif net[1] in nets:
                    net_name = nets[net[1]]
                elif not nets:
                    # KiCad 11 serializes a net by name: (net "NAME").
                    net_name = net[1]
                elif net[1] != "0":
                    errors.append(dict(reference=reference, pad=pad[1], unknown_net_code=net[1]))
            if net_name == "":
                net_name = None
            if net_name:
                net_names.add(net_name)
            pads.append(dict(name=pad[1], net=net_name,
                             type="through_hole" if pad[2] in ("thru_hole", "np_thru_hole")
                             else "smd" if pad[2] in ("smd", "connect") else pad[2]))
        elements.append(dict(reference=reference,
                             value=property_value(footprint, "Value", "value"), pads=pads))
    tracks = children(root, "segment") + children(root, "arc")
    for item in tracks + children(root, "via") + children(root, "zone"):
        net = one(item, "net")
        if net:
            name = net[2] if len(net) >= 3 else nets.get(net[1], net[1] if not nets else "")
            if name:
                net_names.add(name)
    track_layers = Counter(one(track, "layer")[1] for track in tracks if one(track, "layer"))
    zones = children(root, "zone")
    copper_zones = []
    for zone in zones:
        layer = one(zone, "layer")
        layers = one(zone, "layers")
        zone_layers = [layer[1]] if layer else layers[1:] if layers else []
        if one(zone, "keepout") is None:
            copper_zones.extend(value for value in zone_layers if value.endswith(".Cu"))
    return dict(file=str(path.resolve()), sha256=hashlib.sha256(data).hexdigest(),
                footprints=len(elements), pads=sum(len(el["pads"]) for el in elements),
                mechanical_holes=mechanical_holes,
                pads_including_mechanical_holes=sum(len(el["pads"]) for el in elements) + mechanical_holes,
                pad_types=dict(Counter(pad["type"] for el in elements for pad in el["pads"])),
                unconnected_pads=sum(pad["net"] is None for el in elements for pad in el["pads"]),
                named_nets=len({name for name in net_names if name}),
                vias=len(children(root, "via")), track_segments=len(children(root, "segment")),
                track_arcs=len(children(root, "arc")), tracks_total=len(tracks),
                tracks_by_copper_layer=dict(track_layers),
                copper_zones_by_layer=dict(Counter(copper_zones)),
                elements=elements, parse_errors=errors)


def describe_counts(counter):
    return [dict(pad=key[0], net=key[1], count=value)
            for key, value in sorted(counter.items(), key=lambda item: (item[0][0], item[0][1] or ""))]


def compare(source, native, net_name_map=None):
    net_name_map = net_name_map or {}
    differences = []

    def equal(label, expected, actual):
        if expected != actual:
            differences.append(dict(check=label, expected=expected, actual=actual))

    equal("footprints", source["placed_footprints"], native["footprints"])
    equal("pads", source["placed_pads"], native["pads"])
    equal("mechanical_holes", source.get("placed_mechanical_holes", 0), native["mechanical_holes"])
    equal("pad_types", source["placed_pad_types"], native["pad_types"])
    equal("unconnected_pads", source["unconnected_pads"], native["unconnected_pads"])
    equal("vias", source["signal_vias"], native["vias"])
    expected_track_layers = {}
    for eagle_layer, count in source["signal_wire_records_by_eagle_layer"].items():
        if int(eagle_layer) == 19:
            continue
        layer = "F.Cu" if int(eagle_layer) == 1 else "B.Cu" if int(eagle_layer) == 16 else f"In{int(eagle_layer)-1}.Cu"
        expected_track_layers[layer] = count
    equal("tracks_by_copper_layer", expected_track_layers, native["tracks_by_copper_layer"])
    equal("tracks_total", sum(expected_track_layers.values()), native["tracks_total"])
    expected_zone_layers = {}
    for eagle_layer, count in source["signal_polygons_by_eagle_layer"].items():
        layer = "F.Cu" if int(eagle_layer) == 1 else "B.Cu" if int(eagle_layer) == 16 else f"In{int(eagle_layer)-1}.Cu"
        expected_zone_layers[layer] = count
    equal("copper_zones_by_layer", expected_zone_layers, native["copper_zones_by_layer"])
    aliases = {el["reference"]: native_reference(el["reference"]) for el in source["elements"]
               if native_reference(el["reference"]) != el["reference"]}
    source_refs = {native_reference(el["reference"]): el for el in source["elements"]}
    native_refs = defaultdict(list)
    for element in native["elements"]:
        native_refs[element["reference"]].append(element)
    missing = sorted(source_refs.keys() - native_refs.keys())
    extra = sorted(native_refs.keys() - source_refs.keys(), key=lambda value: value or "")
    duplicate_refs = {ref: len(els) for ref, els in native_refs.items() if len(els) != 1}
    equal("missing_references", [], missing)
    equal("extra_references", [], extra)
    equal("duplicate_native_references", {}, duplicate_refs)
    checked_refs, checked_pads = 0, 0
    for ref in sorted(source_refs.keys() & native_refs.keys()):
        if len(native_refs[ref]) != 1:
            continue
        expected, actual = source_refs[ref], native_refs[ref][0]
        checked_refs += 1
        checked_pads += len(expected["pads"])
        equal(f"reference[{ref}].value", expected["value"], actual["value"])
        expected_pads = Counter((pad["name"], net_name_map.get(pad["net"], pad["net"]))
                                for pad in expected["pads"])
        actual_pads = Counter((pad["name"], pad["net"]) for pad in actual["pads"])
        if expected_pads != actual_pads:
            differences.append(dict(check=f"reference[{ref}].pad_net_memberships",
                missing=describe_counts(expected_pads - actual_pads),
                extra=describe_counts(actual_pads - expected_pads)))
    equal("native_parse_errors", [], native["parse_errors"])
    return dict(status="pass" if not differences else "fail", differences=differences,
                checked_reference_values=checked_refs, checked_source_pads=checked_pads,
                source_to_native_net_name_map_used=net_name_map,
                renamed_source_nets=sum(name != target for name, target in net_name_map.items()),
                source_reference_aliases=aliases,
                scope="References, values, exact pad-number/net-name multisets, pad types/counts, vias, routed copper record counts by layer, copper polygon counts.",
                limitations=["This structural comparison does not prove trace geometry or manufacturing readiness.",
                             "Source airwires are recorded as original incompleteness and excluded from physical copper-track counts.",
                             "Extra source mainboard net records without pad contactrefs are retained in the source report; unused native net definitions may be omitted by KiCad."])


def compare_netlist(source, path):
    """Compare physical-pad connectivity independent of auto-generated names."""
    if not path.exists():
        return dict(status="pending", missing_native_netlist=str(path.resolve()))
    if not path.stat().st_size:
        return dict(status="pending", incomplete_native_netlist=str(path.resolve()))
    root = ET.parse(path).getroot()
    if root.tag != "export":
        raise ValueError("Expected KiCad XML netlist with export root; export using kicadxml format")
    physical_pads, source_connections = set(), defaultdict(set)
    physical_refs = set()
    libraries = source["raw_library_ordinals"]
    for part in source["parts"]:
        library = libraries[part["lib"] - 1]
        device = library["devicesets"][part["device"] - 1]
        variant = device["variants"][part["variant"] - 1]
        if not variant["package_ordinal"]:
            continue
        package = library["packages"][variant["package_ordinal"] - 1]
        reference = native_reference(part["name"])
        physical_refs.add(reference)
        physical_pads.update((reference, pad["name"]) for pad in package["pads"])
    for entry in source["source_schematic_pin_net_memberships"]:
        for pad in entry["pads"]:
            source_connections[(native_reference(entry["reference"]), pad)].add(entry["net"])
    expected_net_groups = defaultdict(set)
    for key, names in source_connections.items():
        for name in names:
            expected_net_groups[name].add(key)
    native_connections, native_net_groups = defaultdict(list), defaultdict(set)
    names_by_code, skipped_nodes = {}, 0
    for net in root.findall("./nets/net"):
        code = net.get("code", net.get("name"))
        names_by_code[code] = net.get("name", "")
        for node in net.findall("node"):
            ref, pin = node.get("ref"), node.get("pin")
            if ref not in physical_refs:
                skipped_nodes += 1
                continue
            key = (ref, pin)
            native_connections[key].append(code)
            native_net_groups[code].add(key)
    differences, renames, ignored_singletons, candidates = [], [], [], {}
    missing = sorted(source_connections.keys() - native_connections.keys())
    if missing:
        differences.append(dict(check="missing_physical_pin_memberships", pins=[
            dict(reference=ref, pad=pad, source_nets=sorted(source_connections[(ref, pad)]))
            for ref, pad in missing]))
    duplicates = []
    for (ref, pad), codes in native_connections.items():
        if len(codes) > 1:
            duplicates.append(dict(reference=ref, pad=pad, occurrences=len(codes),
                                   native_nets=[names_by_code[code] for code in codes]))
    if duplicates:
        differences.append(dict(check="duplicate_native_physical_pin_nodes", pins=duplicates))
    source_duplicates = [dict(reference=ref, pad=pad, nets=sorted(nets))
                         for (ref, pad), nets in source_connections.items() if len(nets) > 1]
    if source_duplicates:
        differences.append(dict(check="source_pin_in_multiple_nets", pins=source_duplicates))
    for key in sorted(native_connections.keys() - source_connections.keys()):
        codes = native_connections[key]
        if (key in physical_pads and len(codes) == 1 and
                len(native_net_groups[codes[0]]) == 1):
            ignored_singletons.append(dict(reference=key[0], pad=key[1],
                                           native_net=names_by_code[codes[0]]))
        else:
            differences.append(dict(check="unexpected_connected_physical_pin",
                reference=key[0], pad=key[1],
                native_nets=[names_by_code[code] for code in codes]))
    for name, expected_pins in sorted(expected_net_groups.items()):
        codes = {code for key in expected_pins for code in native_connections.get(key, [])}
        if len(codes) > 1:
            differences.append(dict(check="source_net_split", source_net=name,
                native_nets=[names_by_code[code] for code in sorted(codes)],
                pins=[dict(reference=key[0], pad=key[1]) for key in sorted(expected_pins)]))
        elif len(codes) == 1:
            code = next(iter(codes))
            if native_net_groups[code] == expected_pins:
                candidates[name] = names_by_code[code]
            if names_by_code[code].lstrip("/") != name:
                renames.append(dict(source_net=name, native_net=names_by_code[code],
                                    automatic_source_name=name.startswith("N$")))
    for code, actual_pins in native_net_groups.items():
        source_names = {name for key in actual_pins for name in source_connections.get(key, [])}
        if len(source_names) > 1:
            differences.append(dict(check="native_net_merges_source_nets",
                native_net=names_by_code[code], source_nets=sorted(source_names),
                pins=[dict(reference=key[0], pad=key[1]) for key in sorted(actual_pins)]))
    expected_groups = {frozenset(pins) for pins in expected_net_groups.values()}
    native_connected_groups = {frozenset(key for key in pins if key in source_connections)
                               for pins in native_net_groups.values()}
    native_connected_groups.discard(frozenset())
    target_sources = defaultdict(list)
    for source_name, native_name in candidates.items():
        target_sources[native_name].append(source_name)
    for native_name, source_names in target_sources.items():
        if len(source_names) > 1:
            differences.append(dict(check="ambiguous_native_net_name_mapping",
                                    native_net=native_name, source_nets=source_names))
            for source_name in source_names:
                del candidates[source_name]
    return dict(status="pass" if not differences else "fail", file=str(path.resolve()),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                expected_physical_memberships=len(source_connections),
                expected_physical_net_groups=len(expected_groups),
                native_physical_memberships=len(native_connections),
                native_physical_net_groups=len(native_connected_groups),
                source_physical_references=len(physical_refs),
                source_reference_aliases={part["name"]: native_reference(part["name"])
                    for part in source["parts"] if native_reference(part["name"]) != part["name"]},
                ignored_nonphysical_nodes=skipped_nodes,
                ignored_unconnected_singleton_pins=ignored_singletons,
                net_name_changes=renames,
                explicit_source_net_name_changes=[entry for entry in renames if not entry["automatic_source_name"]],
                source_to_native_net_name_bijection=candidates,
                mapped_source_net_groups=len(candidates),
                differences=differences,
                scope="Exact physical reference/pad net-group membership, missing/extra connected pins, duplicate pin nodes, net splits/merges. Auto-generated net names may differ.")


def combined_status(statuses):
    return "error" if "error" in statuses else "fail" if "fail" in statuses else "pending" if "pending" in statuses else "pass"


def main():
    parser = argparse.ArgumentParser()
    validation_dir = Path(__file__).resolve().parent
    parser.add_argument("--source-report", type=Path,
                        default=validation_dir / "eagle-source-structure.json")
    parser.add_argument("--project-root", type=Path, default=validation_dir.parent)
    parser.add_argument("--netlist-root", type=Path, default=validation_dir)
    parser.add_argument("--output", type=Path,
                        default=validation_dir / "native-project-structure-checks.json")
    args = parser.parse_args()
    source = json.loads(args.source_report.read_text())
    result = dict(format="eagle-native-structure-comparison-v1",
                  source_report=str(args.source_report.resolve()), projects={})
    for stem in ("mainboard", "ioboard"):
        native = None
        path = args.project_root / stem / (stem + ".kicad_pcb")
        if not path.exists():
            result["projects"][stem] = dict(status="pending", missing_native_file=str(path.resolve()))
        else:
            try:
                native = inventory_pcb(path)
                comparison = compare(source["files"][stem + ".brd"], native)
                comparison["native_inventory"] = {key: value for key, value in native.items() if key != "elements"}
                result["projects"][stem] = comparison
            except (ValueError, KeyError, IndexError, UnicodeError) as error:
                result["projects"][stem] = dict(status="error", file=str(path.resolve()), error=str(error))
        project = result["projects"][stem]
        project["pcb_status"] = project["status"]
        netlist_path = args.netlist_root / stem / (stem + ".net")
        try:
            project["schematic_netlist"] = compare_netlist(source["files"][stem + ".sch"], netlist_path)
        except (ValueError, KeyError, IndexError, ET.ParseError, UnicodeError) as error:
            project["schematic_netlist"] = dict(status="error", file=str(netlist_path.resolve()), error=str(error))
        mapping = project["schematic_netlist"].get("source_to_native_net_name_bijection", {})
        if native is not None:
            mapped_comparison = compare(source["files"][stem + ".brd"], native, mapping)
            for key, value in mapped_comparison.items():
                project[key] = value
            project["pcb_status"] = mapped_comparison["status"]
        project["source_original_schematic_board_differences"] = source["source_pair_consistency"][stem]
        project["status"] = combined_status({project["pcb_status"], project["schematic_netlist"]["status"]})
    statuses = {project["status"] for project in result["projects"].values()}
    result["status"] = combined_status(statuses)
    result["pcb_status"] = combined_status({project["pcb_status"] for project in result["projects"].values()})
    result["schematic_netlist_status"] = combined_status({project["schematic_netlist"]["status"]
                                                        for project in result["projects"].values()})
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(args.output)
    print(json.dumps({"status": result["status"], "projects": {
        name: {key: value for key, value in project.items() if key in (
            "status", "pcb_status", "missing_native_file", "error", "checked_reference_values", "checked_source_pads")}
        for name, project in result["projects"].items()}, "report": str(args.output.resolve())}, indent=2))
    raise SystemExit(1 if result["status"] in ("fail", "error") else 0)


if __name__ == "__main__":
    main()
