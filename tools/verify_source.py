#!/usr/bin/env python3
"""Fail closed if upstream source differs from the internally hooked revision."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / 'source-lock.json').read_text())


def git(*args, cwd):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def verify(horizon):
    errors = []
    try:
        head = git('rev-parse', 'HEAD', cwd=horizon)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError('La carpeta indicada no es una copia Git válida de Horizon.')
    if head != LOCK['horizon_revision']:
        errors.append(f'HEAD esperado: {LOCK["horizon_revision"]}; actual: {head}')
    for path, expected in LOCK['original_git_blob_sha1'].items():
        source = horizon / path
        if not source.is_file():
            errors.append(f'Falta archivo: {path}')
            continue
        actual = git('hash-object', str(source), cwd=horizon)
        if actual != expected:
            errors.append(f'{path}: blob esperado {expected}, actual {actual}')
    if errors:
        for line in errors:
            print('ERROR:', line)
        return False
    print('OK: revisión y archivos internos coinciden exactamente con source-lock.json')
    return True


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('horizon', type=Path, help='checkout de git de horizon-rust/horizon')
    args = ap.parse_args()
    raise SystemExit(0 if verify(args.horizon.resolve()) else 1)
