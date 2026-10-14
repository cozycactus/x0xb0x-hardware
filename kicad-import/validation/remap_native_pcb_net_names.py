#!/usr/bin/env python3
"""Rename only native PCB net-name string tokens using verified SCH pad groups.

Dry-run by default. --apply is required to modify a PCB. The input structural
report must contain a passing, current schematic netlist and an unambiguous
name bijection covering every source schematic physical net group. Current
PCB names are first matched to original source PCB names by exact pad groups,
so an earlier importer's automatic names can be remapped safely. Original
PCB-only empty net names are protected. No track, pad, via, zone, or placement
geometry is edited.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def scan_tokens(text):
    pos, length = 0, len(text)
    while pos < length:
        ch = text[pos]
        if ch.isspace():
            pos += 1
            continue
        if ch == ";":
            end = text.find("\n", pos)
            pos = length if end < 0 else end + 1
            continue
        start = pos
        if ch in "()":
            pos += 1
            yield ch, False, start, pos
            continue
        if ch == '"':
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
                    ch = text[pos]
                    pos += 1
                    value.append({"n": "\n", "r": "\r", "t": "\t"}.get(ch, ch))
                else:
                    value.append(ch)
            else:
                raise ValueError("Unterminated quoted string")
            yield "".join(value), True, start, pos
            continue
        while pos < length and not text[pos].isspace() and text[pos] not in "()":
            pos += 1
        yield text[start:pos], False, start, pos


def net_name_tokens(text):
    stack, result = [], []
    for token in scan_tokens(text):
        value, quoted, _, _ = token
        if not quoted and value == "(":
            if stack:
                stack[-1].append(None)
            stack.append([])
        elif not quoted and value == ")":
            if not stack:
                raise ValueError("Unbalanced S-expression")
            members = stack.pop()
            if members and members[0] and members[0][0] == "net":
                if len(members) in (2, 3) and members[-1] and members[-1][1]:
                    result.append(members[-1])
        else:
            if not stack:
                raise ValueError("Atom outside S-expression")
            stack[-1].append(token)
    if stack:
        raise ValueError("Unclosed S-expression")
    return sorted(result, key=lambda token: token[2])


def rewrite_names(text, mapping):
    edits, occurrences = [], Counter()
    for value, _, start, end in net_name_tokens(text):
        occurrences[value] += 1
        target = mapping.get(value, value)
        if target != value:
            edits.append((start, end, json.dumps(target, ensure_ascii=False), value, target))
    pieces, cursor = [], 0
    for start, end, replacement, _, _ in edits:
        pieces.extend((text[cursor:start], replacement))
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces), edits, occurrences


def rename_parsed_tree(tree, mapping):
    if not isinstance(tree, list):
        return tree
    if tree and tree[0] == "net" and len(tree) in (2, 3):
        result = list(tree)
        result[-1] = mapping.get(result[-1], result[-1])
        return result
    return [rename_parsed_tree(item, mapping) for item in tree]


def current_to_source_board_names(source_board, native, normalize_reference):
    """Derive an exact bijection from current native PCB names to source names."""
    source_groups, native_groups = defaultdict(set), defaultdict(set)
    for element in source_board["elements"]:
        reference = normalize_reference(element["reference"])
        for pad in element["pads"]:
            if pad["net"] is not None:
                source_groups[pad["net"]].add((reference, pad["name"]))
    for element in native["elements"]:
        for pad in element["pads"]:
            if pad["net"] is not None:
                native_groups[pad["net"]].add((element["reference"], pad["name"]))
    source_by_group, native_by_group = defaultdict(list), defaultdict(list)
    for name, pins in source_groups.items():
        source_by_group[frozenset(pins)].append(name)
    for name, pins in native_groups.items():
        native_by_group[frozenset(pins)].append(name)
    if any(len(names) != 1 for names in source_by_group.values()):
        raise ValueError("Original source PCB has ambiguous identical pad groups")
    if any(len(names) != 1 for names in native_by_group.values()):
        raise ValueError("Current native PCB has ambiguous identical pad groups")
    if source_by_group.keys() != native_by_group.keys():
        missing = [dict(source_net=source_by_group[group][0],
                        pads=[dict(reference=ref, pad=pad) for ref, pad in sorted(group)])
                   for group in source_by_group.keys() - native_by_group.keys()]
        extra = [dict(current_net=native_by_group[group][0],
                      pads=[dict(reference=ref, pad=pad) for ref, pad in sorted(group)])
                 for group in native_by_group.keys() - source_by_group.keys()]
        raise ValueError("Current PCB pad groups differ from original source PCB: " +
                         json.dumps(dict(missing_source_groups=missing, extra_native_groups=extra)))
    mapping = {native_by_group[group][0]: names[0]
               for group, names in source_by_group.items()}
    if len(mapping) != len(source_groups) or len(set(mapping.values())) != len(mapping):
        raise ValueError("Current PCB to source PCB net names are not strictly bijective")
    return mapping


def main():
    validation_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write verified net-name-only edits to native PCB files")
    parser.add_argument("--project", choices=("mainboard", "ioboard"), action="append")
    parser.add_argument("--project-root", type=Path, default=validation_dir.parent)
    parser.add_argument("--source-report", type=Path, default=validation_dir / "eagle-source-structure.json")
    parser.add_argument("--comparison-report", type=Path, default=validation_dir / "native-project-structure-checks.json")
    parser.add_argument("--output-report", type=Path, default=validation_dir / "native-net-name-remapping.json")
    args = parser.parse_args()
    source = json.loads(args.source_report.read_text())
    comparison = json.loads(args.comparison_report.read_text())
    spec = importlib.util.spec_from_file_location("native_verifier", validation_dir / "verify_native_projects.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    plans, report = [], dict(mode="apply" if args.apply else "dry-run", projects={})
    for stem in args.project or ("mainboard", "ioboard"):
        project = comparison["projects"][stem]
        netlist = project["schematic_netlist"]
        if netlist["status"] != "pass":
            raise SystemExit(f"{stem}: schematic netlist must pass before net-name remapping (currently {netlist['status']})")
        netlist_path = Path(netlist["file"])
        if sha256(netlist_path.read_bytes()) != netlist["sha256"]:
            raise SystemExit(f"{stem}: netlist changed; rerun verify_native_projects.py before remapping")
        source_to_fresh = netlist["source_to_native_net_name_bijection"]
        if (len(source_to_fresh) != netlist["expected_physical_net_groups"] or
                len(set(source_to_fresh.values())) != len(source_to_fresh)):
            raise SystemExit(f"{stem}: incomplete or ambiguous source-to-native net-name bijection")
        protected = set(source["source_pair_consistency"][stem]["board_only_net_names"])
        if protected & source_to_fresh.keys():
            raise SystemExit(f"{stem}: mapping attempts to rename an original board-only empty net")
        path = args.project_root / stem / (stem + ".kicad_pcb")
        before = path.read_bytes()
        recorded_hash = project.get("native_inventory", {}).get("sha256")
        if recorded_hash and sha256(before) != recorded_hash:
            raise SystemExit(f"{stem}: PCB changed; rerun verify_native_projects.py before remapping")
        try:
            current_to_source = current_to_source_board_names(source["files"][stem + ".brd"],
                verifier.inventory_pcb(path), verifier.native_reference)
        except ValueError as error:
            raise SystemExit(f"{stem}: {error}")
        if any(name not in source_to_fresh for name in current_to_source.values()):
            raise SystemExit(f"{stem}: a nonempty source PCB net lacks a fresh schematic mapping")
        mapping = {current: source_to_fresh[source_name]
                   for current, source_name in current_to_source.items()}
        if len(set(mapping.values())) != len(mapping):
            raise SystemExit(f"{stem}: composed current-to-fresh name mapping is not bijective")
        if protected & mapping.keys():
            raise SystemExit(f"{stem}: current mapping would rename an original board-only empty net name")
        text = before.decode("utf-8")
        changed, edits, occurrences = rewrite_names(text, mapping)
        after = changed.encode("utf-8")
        before_tree = verifier.parse_sexpr(text)
        after_tree = verifier.parse_sexpr(changed)
        if rename_parsed_tree(before_tree, mapping) != after_tree:
            raise SystemExit(f"{stem}: non-net S-expression content changed unexpectedly")
        after_occurrences = Counter(token[0] for token in net_name_tokens(changed))
        if any(occurrences[name] != after_occurrences[name] for name in protected):
            raise SystemExit(f"{stem}: original board-only empty net occurrence changed")
        # A temporary candidate permits the normal structural verifier to check
        # every original PCB pad/net assignment after applying the bijection.
        candidate = validation_dir / f".{stem}-net-remapping-candidate.kicad_pcb"
        try:
            candidate.write_bytes(after)
            native = verifier.inventory_pcb(candidate)
            checked = verifier.compare(source["files"][stem + ".brd"], native, source_to_fresh)
            if checked["status"] != "pass":
                raise SystemExit(f"{stem}: candidate fails structural verification: {json.dumps(checked['differences'])}")
        finally:
            candidate.unlink(missing_ok=True)
        renamed = Counter((old, target) for _, _, _, old, target in edits)
        report["projects"][stem] = dict(file=str(path.resolve()), before_sha256=sha256(before),
            after_sha256=sha256(after), changed_net_name_tokens=len(edits),
            renamed_nets=[dict(before=name, source_board=current_to_source[name], native=target, occurrences=count)
                          for (name, target), count in sorted(renamed.items())],
            source_to_native_net_name_bijection=source_to_fresh,
            current_to_source_board_net_name_bijection=current_to_source,
            current_to_fresh_schematic_net_name_bijection=mapping,
            current_board_pad_groups_exactly_match_original_source=True,
            protected_original_board_only_empty_net_names=len(protected),
            protected_empty_net_string_occurrences_before=sum(occurrences[name] for name in protected),
            protected_empty_net_string_occurrences_after=sum(after_occurrences[name] for name in protected),
            all_non_net_s_expression_content_unchanged=True,
            route_geometry_placement_and_pad_topology_unchanged=True,
            candidate_structural_check="pass")
        plans.append((stem, path, before, after))
    if args.apply:
        backup_dir = validation_dir / "net-name-remapping-backups"
        backup_dir.mkdir(exist_ok=True)
        for stem, path, before, after in plans:
            if path.read_bytes() != before:
                raise SystemExit(f"{stem}: PCB changed during planning; no remap applied to this file")
            if before != after:
                backup = backup_dir / f"{stem}-{sha256(before)[:12]}.kicad_pcb"
                if backup.exists() and backup.read_bytes() != before:
                    raise SystemExit(f"{stem}: existing backup differs unexpectedly")
                if not backup.exists():
                    shutil.copy2(path, backup)
                temporary = path.with_suffix(path.suffix + ".net-remap.tmp")
                temporary.write_bytes(after)
                temporary.replace(path)
                report["projects"][stem]["backup"] = str(backup.resolve())
    temporary = args.output_report.with_suffix(args.output_report.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(args.output_report)
    print(json.dumps(dict(mode=report["mode"], projects={stem: dict(
        changed_net_name_tokens=project["changed_net_name_tokens"],
        renamed_net_names=len(project["renamed_nets"]),
        candidate_structural_check=project["candidate_structural_check"])
        for stem, project in report["projects"].items()}, report=str(args.output_report.resolve())), indent=2))


if __name__ == "__main__":
    main()
