"""Derive DIN functions from electrical pad nets, independently of scene labels.

The optional legacy decoder arguments refresh a concise evidence extract from
the preserved binary Eagle schematic. The saved extract is also checked against
current PCB connectivity, so the ordinary verification needs no external tool.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / 'PROJECT.json').is_file())
PCB = REPO / 'kicad-working/ioboard/ioboard.kicad_pcb'
EAGLE = REPO / 'original-eagle/ioboard.sch'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def field(node, key):
    rows = children(node, key)
    return rows[0][1:] if rows else []


def board_parts():
    stack, root = [], None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+', PCB.read_text()):
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            stack.append(node)
        elif token == ')':
            node = stack.pop()
            if not stack:
                root = node
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    result = {}
    for footprint in children(root, 'footprint'):
        properties = {p[1]: p[2] for p in children(footprint, 'property')}
        result[properties['Reference']] = dict(
            value=properties.get('Value'), position=field(footprint, 'at'),
            pads={p[1]: (field(p, 'net') or [None])[0]
                  for p in children(footprint, 'pad')})
    return result


def derive():
    parts = board_parts()

    def resistor_paths(net, resistance=None):
        return [(ref, other) for ref, part in parts.items()
                if ref.startswith('R') and (resistance is None or part['value'] == resistance)
                and net is not None and net in part['pads'].values()
                for other in set(part['pads'].values()) - {net, None}]

    optos = {ref: p for ref, p in parts.items() if p['value'] == '4N37'}
    assert len(optos) == 1
    opto_ref, opto = next(iter(optos.items()))
    functions, used = {}, {opto_ref}
    for ref, part in sorted(parts.items()):
        if not ref.startswith('DIN'):
            continue
        p = part['pads']
        four, five = resistor_paths(p.get('4'), '220'), resistor_paths(p.get('5'), '220')
        input_anode = [(r, net) for r, net in four if net == opto['pads']['1']]
        supply = [(r, net) for r, net in four if net == '+5V']
        drivers = [(r, net) for r, net in five if net in {'MIDI_OUT', 'MIDI_IN'}]
        sync = {pin: [(r, net) for r, net in resistor_paths(p.get(pin))
                      if net and net.startswith('DINSYNC')]
                for pin in ('1', '3', '4', '5')}
        if p.get('5') == opto['pads']['2'] and input_anode:
            label, function = 'MIDI IN', 'optoisolated MIDI input'
            evidence = dict(pin4_series=input_anode, pin5_opto_cathode=opto_ref + '.2',
                            opto_anode=opto_ref + '.1')
            used.update(r for r, _ in input_anode)
        elif supply and len(drivers) == 1:
            driver_ref, net = drivers[0]
            label = 'MIDI OUT' if net == 'MIDI_OUT' else 'THRU'
            function = 'processor MIDI output' if net == 'MIDI_OUT' else 'buffered MIDI thru'
            evidence = dict(pin4_supply_series=supply, pin5_driver_series=drivers,
                            driver_net=net)
            used.update(r for r, _ in supply + drivers)
        elif all(len(rows) == 1 for rows in sync.values()) and {
                rows[0][1] for rows in sync.values()} == {
                'DINSYNC1', 'DINSYNC2', 'DINSYNC3', 'DINSYNC4'}:
            label, function = 'SYNC', 'four-line DIN synchronization'
            evidence = dict(pin_series_nets=sync)
            used.update(rows[0][0] for rows in sync.values())
        else:
            raise AssertionError('Unclassified electrical function: ' + ref)
        functions[ref] = dict(expected_legend=label, function=function,
                              connector_pad_nets=p, evidence=evidence)
        used.add(ref)
    assert len(functions) == 4
    # Establish that MIDI_IN is the buffered opto-receiver node and MIDI_OUT
    # reaches the processor header, rather than trusting a net name alone.
    transistor = [(ref, p) for ref, p in parts.items()
                  if p['value'] == '2SC536F' and p['pads'].get('2') == 'MIDI_IN'
                  and p['pads'].get('3') == 'GND'
                  and p['pads'].get('1') == opto['pads']['4']]
    header = [(ref, p) for ref, p in parts.items()
              if p['pads'].get('5') == 'MIDI_IN' and p['pads'].get('6') == 'MIDI_OUT']
    assert len(transistor) == len(header) == 1
    assert parts['D48']['pads'] == {'A': opto['pads']['2'], 'C': opto['pads']['1']}
    used.update([transistor[0][0], header[0][0], 'D48', 'R16', 'R17', 'R20'])
    return dict(pcb=str(PCB.relative_to(REPO)), pcb_sha256=sha(PCB),
                original_eagle=str(EAGLE.relative_to(REPO)), eagle_sha256=sha(EAGLE),
                functions=functions,
                buffered_receiver=dict(opto=opto_ref, transistor=transistor[0][0],
                                       processor_header=header[0][0]),
                selected_parts={ref: parts[ref] for ref in sorted(used)},
                method='Classify DIN pins using resistor, optocoupler, transistor and header connectivity; no scene or generator mapping is read.',
                physical_fit_qualified=False)


def refresh_eagle(helper, spec, result):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(helper.parent))
    from inspect_eagle_source import Eagle, load_spec
    source = Eagle(EAGLE, load_spec(spec)).schematic()
    refs = set(result['selected_parts'])
    memberships = [dict(row, raw_record_hex=EAGLE.read_bytes()[
                    row['record_index'] * 24:(row['record_index'] + 1) * 24].hex())
                   for row in source['source_schematic_pin_net_memberships']
                   if row['reference'] in refs]
    result['original_binary_evidence'] = dict(
        decoder_sha256=sha(helper), parser_spec_sha256=sha(spec),
        source_sha256=source['sha256'],
        all_records_match_fork_parser=source['all_records_match_fork_parser'],
        selected_parts=[p for p in source['parts'] if p['name'] in refs],
        selected_pin_net_memberships=memberships,
        qualification='Direct selected IO binary record memberships; the legacy decoder is not a physical or complete-design certification.')


def verify_original_evidence(result, stored):
    evidence = stored['original_binary_evidence']
    assert evidence['source_sha256'] == result['eagle_sha256']
    binary = EAGLE.read_bytes()
    assert all(binary[row['record_index'] * 24:(row['record_index'] + 1) * 24].hex()
               == row['raw_record_hex'] for row in evidence['selected_pin_net_memberships'])
    pairs = {(row['reference'], pad, row['net'])
             for row in evidence['selected_pin_net_memberships'] for pad in row['pads']}
    wanted = {(ref, pad, net) for ref, p in result['selected_parts'].items()
              for pad, net in p['pads'].items() if net is not None}
    assert wanted <= pairs, sorted(wanted - pairs)
    return dict(passed=True, connected_pad_memberships_checked=len(wanted),
                original_binary_record_count=len(evidence['selected_pin_net_memberships']),
                original_raw_records_replayed=len(evidence['selected_pin_net_memberships']),
                source_sha256=evidence['source_sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--legacy-decoder', type=Path)
    parser.add_argument('--parser-spec', type=Path)
    args = parser.parse_args()
    result = derive()
    target = HERE / 'midi-connectivity-evidence.json'
    if args.legacy_decoder and args.parser_spec:
        refresh_eagle(args.legacy_decoder, args.parser_spec, result)
    else:
        result['original_binary_evidence'] = json.loads(target.read_text())['original_binary_evidence']
    result['original_comparison'] = verify_original_evidence(result, result)
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in {'selected_parts', 'original_binary_evidence'}}, indent=2))
