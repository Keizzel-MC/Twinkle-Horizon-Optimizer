#!/usr/bin/env python3
import unittest
from pathlib import Path
import subprocess
import sys
import zipfile
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    subprocess.check_call([sys.executable, str(ROOT / 'tools' / 'package.py')])
    out = ROOT / 'twinkle_opt-0.2.1.hnmod'
    with zipfile.ZipFile(out) as z:
        entries = z.namelist()
        assert entries == sorted(entries)
        assert all(name == 'horizon-native.json' or name.startswith('mixins/twinkle_opt/') for name in entries)
        assert json.loads(z.read('horizon-native.json'))['schema'] == 1
    print('SHA256:', hashlib.sha256(out.read_bytes()).hexdigest())
    print('Comprobaciones estáticas y algorítmicas completadas. COMPILACIÓN RUST: NO PROBADA.')
