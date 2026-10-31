#!/usr/bin/env python3
"""Print an existing Horizon standard benchmark's FPS/frame times with no estimates."""
import argparse
import json
from pathlib import Path
from statistics import mean


def summarize(report):
    if report.get('format') != 'horizon-benchmark-report' or report.get('version') != 1:
        raise ValueError('No es un informe Horizon válido')
    frames = report.get('frames', [])
    if not frames:
        raise ValueError('Sin muestras de fotogramas')
    return {
        'revision': report['app']['version'],
        'conditions': report['conditions'],
        'single_run_per_scene': len({f['phase'] for f in frames}) == len(frames),
        'mean_of_scene_avg_fps': round(mean(f['avg_fps'] for f in frames), 3),
        'scenes': [{k: f.get(k) for k in ('phase', 'avg_fps', 'low_1pct_fps', 'low_01pct_fps',
                                          'p95_ms', 'p99_ms', 'cpu_p50_ms', 'gpu_p50_ms')} for f in frames],
        'gpu_allocated_mb': report.get('metrics', {}).get('memory.gpu_mb', {}).get('mean'),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('report', type=Path)
    args = ap.parse_args()
    print(json.dumps(summarize(json.loads(args.report.read_text(encoding='utf-8'))), indent=2,
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
