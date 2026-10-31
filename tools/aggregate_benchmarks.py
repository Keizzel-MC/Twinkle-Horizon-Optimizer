#!/usr/bin/env python3
"""Merge independent standard-run JSON reports for a fair, reproducible A/B comparison.

No invented frames: every entry is copied from a real Horizon report. Reject
mixed seeds/settings/hardware/releases and repeated input paths.
"""
import argparse
import json
from pathlib import Path

# Keep the same scene/settings consistency rules as compare_benchmarks.py.
from compare_benchmarks import FIELDS


def aggregate(reports):
    if len(reports) < 3:
        raise ValueError('Necesitas al menos 3 ejecuciones reales.')
    first = reports[0]
    if first.get('format') != 'horizon-benchmark-report' or first.get('version') != 1:
        raise ValueError('Formato de benchmark inválido')
    expected_phases = {frame['phase'] for frame in first.get('frames', [])}
    if not expected_phases:
        raise ValueError('Primer informe sin datos de fotogramas')
    for i, r in enumerate(reports):
        if r.get('format') != first['format'] or r.get('version') != first['version']:
            raise ValueError(f'Informe {i + 1}: formato distinto')
        for k in FIELDS:
            if r.get('conditions', {}).get(k) != first.get('conditions', {}).get(k):
                raise ValueError(f'Informe {i + 1}: {k} distinto')
        for k in ('cpu', 'gpu', 'ram_mb', 'display'):
            if r.get('hardware', {}).get(k) != first.get('hardware', {}).get(k):
                raise ValueError(f'Informe {i + 1}: equipo {k} distinto')
        for k in ('name', 'version'):
            if r.get('app', {}).get(k) != first.get('app', {}).get(k):
                raise ValueError(f'Informe {i + 1}: versión de aplicación distinta')
        frames = r.get('frames', [])
        if len(frames) != len(expected_phases) or {f['phase'] for f in frames} != expected_phases:
            raise ValueError(f'Informe {i + 1}: escenas distintas/duplicadas')
        if any(f.get('repeat') != 0 for f in frames):
            raise ValueError(f'Informe {i + 1}: debe ser una ejecución individual')
    result = {k: v for k, v in first.items() if k not in ('frames', 'metrics')}
    result['frames'] = []
    result['conditions'] = dict(first['conditions'], repeats=len(reports))
    # Do not copy one run's aggregate metrics and falsely advertise their values
    # as a measurement over all repeats. Comparison tool uses frames only.
    result['metrics'] = {}
    for run_index, report in enumerate(reports):
        for f in report['frames']:
            result['frames'].append(dict(f, repeat=run_index))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path)
    parser.add_argument('reports', nargs='+', type=Path)
    args = parser.parse_args()
    if len({p.resolve() for p in args.reports}) != len(args.reports):
        raise SystemExit('No puedes contar el mismo archivo dos veces.')
    merged = aggregate([json.loads(p.read_text(encoding='utf-8')) for p in args.reports])
    args.out.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Agregadas {len(args.reports)} ejecuciones reales -> {args.out}')


if __name__ == '__main__':
    main()
