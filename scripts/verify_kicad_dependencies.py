#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Read-only clone-local KiCad dependency checks; no KiCad install required."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys


EXPECTED = {
    "mainboard": {
        "models": 413,
        "mechanical": {"U$2", "U$23", "U$24", "U$25", "U$27", "U$28", "U$29"},
        "optional": {"IC15A0"},
    },
    "ioboard": {"models": 82, "mechanical": set(), "optional": set()},
}


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                      help="Repository root (defaults to this script's checkout)")
    root = args.parse_args().root.resolve()
    failures, boards = [], {}

    def fail(owner, reason, **details):
        failures.append({"owner": owner, "reason": reason, **details})

    def relative(path):
        return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)

    # Reuse only the existing pure tokenizer. Its command-line work is main-guarded.
    # Suppress Python's cache writes so verification leaves the checkout untouched.
    sys.dont_write_bytecode = True
    parser_path = root / "kicad-import/validation/verify_native_projects.py"
    try:
        spec = importlib.util.spec_from_file_location("native_kicad_parser", parser_path)
        parser = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(parser)
    except (OSError, ImportError, AttributeError) as error:
        print(json.dumps({"passed": False, "failures": [{
            "owner": relative(parser_path), "reason": str(error)}]}, indent=2))
        return 1

    children, one = parser.children, parser.one

    def read_tree(path, kind):
        stack, roots = [], []
        for token, quoted in parser.tokens(path.read_text(encoding="utf-8")):
            if token == "(" and not quoted:
                node = []
                (stack[-1] if stack else roots).append(node)
                stack.append(node)
            elif token == ")" and not quoted:
                if not stack:
                    raise ValueError(f"{relative(path)}: unexpected closing parenthesis")
                stack.pop()
            elif stack:
                stack[-1].append(token)
            else:
                raise ValueError(f"{relative(path)}: atom outside S-expression")
        if stack or len(roots) != 1 or not roots[0] or roots[0][0] != kind:
            raise ValueError(f"{relative(path)}: expected one complete {kind} expression")
        return roots[0]

    def field(node, key):
        value = one(node, key)
        return value[1] if value and len(value) > 1 else ""

    def prop(node, key):
        return next((p[2] for p in children(node, "property")
                     if len(p) > 2 and p[1] == key), "")

    def local_path(uri, project, owner, directory=False):
        prefix = "${KIPRJMOD}/"
        if not uri.startswith(prefix) or "$" in uri[len(prefix):] or "\\" in uri:
            fail(owner, "Dependency must use ${KIPRJMOD}/, without other variables",
                 dependency=uri)
            return None
        path = (project / uri[len(prefix):]).resolve()
        if not path.is_relative_to(project):
            fail(owner, "Dependency escapes its project folder", dependency=uri,
                 resolved_path=str(path))
            return None
        if not (path.is_dir() if directory else path.is_file()):
            fail(owner, "Missing dependency", dependency=uri,
                 expected_path=relative(path))
            return None
        if not directory and not path.stat().st_size:
            fail(owner, "Dependency file is empty", expected_path=relative(path))
        # macOS can resolve incorrectly cased paths that fail in a Linux clone.
        current = project
        for part in path.relative_to(project).parts:
            if part not in {p.name for p in current.iterdir()}:
                fail(owner, "Dependency path case differs from the checked-in name",
                     dependency=uri, expected_path=relative(path))
                return None
            current = current / part
        return path

    def tables(project, filename, root_kind, directory):
        table_path = project / filename
        result = {}
        for lib in children(read_tree(table_path, root_kind), "lib"):
            name = field(lib, "name")
            if not name or name in result:
                fail(relative(table_path), "Missing or duplicate library nickname", name=name)
            if field(lib, "type") != "KiCad":
                fail(relative(table_path), "Expected a project-local KiCad library", name=name)
            result[name] = local_path(field(lib, "uri"), project,
                                      f"{relative(table_path)}:{name}", directory)
        if not result:
            fail(relative(table_path), "No project-local libraries registered")
        return result

    def footprint_path(identifier, libraries, owner):
        nickname, colon, name = identifier.partition(":")
        if not colon or nickname not in libraries:
            fail(owner, "Footprint has no matching project library", footprint=identifier)
            return None
        library = libraries[nickname]
        if library is None:
            return None
        path = library / (name + ".kicad_mod")
        if (path.parent != library or not path.resolve().is_relative_to(library)
                or not path.is_file() or path.name not in {
                p.name for p in library.iterdir()}):
            fail(owner, "Missing local footprint", footprint=identifier,
                 expected_path=relative(path))
            return None
        return path

    for name, expected in EXPECTED.items():
        project = (root / "kicad-working" / name).resolve()
        start = len(failures)
        try:
            if not project.is_relative_to(root):
                raise ValueError("Project folder escapes the checkout")
            project_file = project / (name + ".kicad_pro")
            json.loads(project_file.read_text(encoding="utf-8"))
            fp_libs = tables(project, "fp-lib-table", "fp_lib_table", True)
            sym_libs = tables(project, "sym-lib-table", "sym_lib_table", False)
            symbol_names = {
                nickname: {s[1] for s in children(read_tree(path, "kicad_symbol_lib"),
                                                 "symbol")}
                for nickname, path in sym_libs.items() if path is not None
            }
            cached_models, library_footprints = 0, 0
            for library in fp_libs.values():
                if library is None:
                    continue
                for path in sorted(library.glob("*.kicad_mod")):
                    fp = read_tree(path, "footprint")
                    library_footprints += 1
                    for model in children(fp, "model"):
                        local_path(model[1], project, relative(path))
                        cached_models += 1

            root_path = project / (name + ".kicad_sch")
            root_sheet = read_tree(root_path, "kicad_sch")
            sheet_paths = [root_path]
            for sheet in children(root_sheet, "sheet"):
                sheet_path = project / prop(sheet, "Sheetfile")
                if sheet_path.is_file():
                    sheet_paths.append(sheet_path)
                else:
                    fail(relative(root_path), "Sheet file missing", sheet=prop(sheet, "Sheetfile"))
            symbols, schematic_footprints = [], set()
            for schematic_path in sheet_paths:
                schematic = read_tree(schematic_path, "kicad_sch")
                embedded = {s[1] for s in children(one(schematic, "lib_symbols") or [],
                                                  "symbol")}
                for symbol in children(schematic, "symbol"):
                    symbols.append(symbol)
                    owner = f"{relative(schematic_path)}:{prop(symbol, 'Reference')}"
                    identifier = field(symbol, "lib_id")
                    nickname, colon, symbol_name = identifier.partition(":")
                    if not colon or symbol_name not in symbol_names.get(nickname, set()):
                        fail(owner, "Symbol missing from project-local library", symbol=identifier)
                    if identifier not in embedded:
                        fail(owner, "Symbol missing from embedded schematic cache", symbol=identifier)
                    footprint = prop(symbol, "Footprint")
                    if footprint:
                        footprint_path(footprint, fp_libs, owner)
                        schematic_footprints.add(footprint)

            pcb_path = project / (name + ".kicad_pcb")
            pcb = read_tree(pcb_path, "kicad_pcb")
            footprints = children(pcb, "footprint")
            fitted, mechanical, optional, seen, assets = set(), set(), set(), set(), set()
            for fp in footprints:
                reference = parser.property_value(fp, "Reference", "reference")
                owner = f"{relative(pcb_path)}:{reference}"
                if not reference or reference in seen:
                    fail(owner, "Missing or duplicate board reference")
                seen.add(reference)
                footprint_path(fp[1], fp_libs, owner)
                models = children(fp, "model")
                pads = children(fp, "pad")
                is_mechanical = bool(pads) and all(p[2] == "np_thru_hole" for p in pads)
                if reference in expected["mechanical"]:
                    mechanical.add(reference)
                    if not is_mechanical or models:
                        fail(owner, "Expected an unmodeled mechanical-only hole footprint")
                elif reference in expected["optional"]:
                    optional.add(reference)
                    if is_mechanical or models or not fp[1].endswith(":SIP9"):
                        fail(owner, "Expected documented optional/unmodeled BA662A SIP9 footprint")
                else:
                    fitted.add(reference)
                    if len(models) != 1:
                        fail(owner, "Expected one model for this fitted reference",
                             model_count=len(models))
                for model in models:
                    path = local_path(model[1], project, owner)
                    if path is not None:
                        assets.add(relative(path))
            if len(fitted) != expected["models"]:
                fail(name, "Fitted reference count changed", expected=expected["models"],
                     actual=len(fitted))
            for category, actual in (("mechanical", mechanical), ("optional", optional)):
                if actual != expected[category]:
                    fail(name, f"Documented {category} reference set changed",
                         expected=sorted(expected[category]), actual=sorted(actual))
            boards[name] = {
                "passed": len(failures) == start,
                "footprints": len(footprints), "fitted_model_references": len(fitted),
                "unique_board_model_assets": len(assets),
                "mechanical_only_unmodeled": sorted(mechanical),
                "optional_component_unmodeled": sorted(optional),
                "schematic_symbol_instances": len(symbols),
                "schematic_footprint_ids": len(schematic_footprints),
                "local_symbol_libraries": len(sym_libs),
                "local_footprint_libraries": len(fp_libs),
                "library_footprints_checked": library_footprints,
                "cached_footprint_models_checked": cached_models,
            }
        except (OSError, ValueError, IndexError, TypeError) as error:
            fail(name, str(error))
            boards[name] = {"passed": False}

    print(json.dumps({
        "passed": not failures, "repository_root": str(root), "boards": boards,
        "fitted_model_references_expected": 495, "failures": failures,
        "scope": "Read-only library and model resolution within this checkout. "
                 "No global KiCad libraries or original workspace required. "
                 "Does not validate ERC, DRC, model geometry or physical fit. "
                 "IC15A0 remains documented optional/unmodeled; this does not set a DNP flag.",
    }, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
