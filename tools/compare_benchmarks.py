#!/usr/bin/env python3
"""Compare official Horizon benchmark JSON without fabricating gains or frames."""
from pathlib import Path
import argparse
import json
from statistics import median

FIELDS = ('scenario', 'seed', 'render_distance', 'simulation_distance', 'window', 'vsync',
          'fps_cap', 'offscreen')
MEASURES = ('avg_fps', 'low_1pct_fps', 'p95_ms', 'p99_ms', 'cpu_p50_ms', 'gpu_p50_ms')


def compare(a, b):
    for key in FIELDS:
        if a.get('conditions', {}).get(key) != b.get('conditions', {}).get(key):
            raise ValueError(f'Condiciones distintas para {key}: no se puede comparar.')
    if a.get('format') != 'horizon-benchmark-report' or b.get('format') != 'horizon-benchmark-report':
        raise ValueError('Se requieren informes oficiales horizon-benchmark-report.')
    if a.get('version') != 1 or b.get('version') != 1:
        raise ValueError('Versión de informe no reconocida.')
    before = {}
    after = {}
    for src, dest in ((a, before), (b, after)):
        for frame in src.get('frames', []):
            dest.setdefault(frame['phase'], []).append(frame)
    if not before or before.keys() != after.keys():
        raise ValueError('Escenarios ausentes o distintos.')
    result = {}
    for phase in sorted(before):
        if len(before[phase]) < 3 or len(after[phase]) < 3:
            raise ValueError(f'Se requieren al menos 3 repeticiones de {phase} en cada informe.')
        row = {}
        for name in MEASURES:
            x = [f[name] for f in before[phase] if isinstance(f.get(name), (float, int))]
            y = [f[name] for f in after[phase] if isinstance(f.get(name), (float, int))]
            if len(x) != len(before[phase]) or len(y) != len(after[phase]):
                continue
            old, new = median(x), median(y)
            row[name] = {'base': round(old, 3), 'mod': round(new, 3),
                         'change_pct': round((new / old - 1) * 100, 2) if old else None,
                         'higher_is_better': name.endswith('fps')}
        result[phase] = row
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('base', type=Path)
    p.add_argument('mod', type=Path)
    args = p.parse_args()
    print(json.dumps(compare(json.loads(args.base.read_text()), json.loads(args.mod.read_text())), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
