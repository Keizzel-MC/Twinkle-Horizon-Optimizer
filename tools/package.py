#!/usr/bin/env python3
"""Package deterministic Horizon native SOURCE bundle; does not compile Rust."""
import argparse
import hashlib
import json
from pathlib import Path
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'native' / 'twinkle_opt'
BUNDLE = MOD / 'mixins' / 'twinkle_opt'


def checks():
    manifest = json.loads((MOD / 'horizon-native.json').read_text())
    compat = json.loads((MOD / 'compatibility.json').read_text())
    lock = json.loads((ROOT / 'source-lock.json').read_text())
    bundle = tomllib.loads((BUNDLE / 'horizon-mixin.toml').read_text())
    assert manifest['schema'] == 1 and manifest['id'] == bundle['mod']['id'] == 'twinkle_opt'
    assert manifest['version'] == bundle['mod']['version']
    assert manifest['game'] == compat['game']
    assert manifest['horizon'] == compat['horizon_revision'] == lock['horizon_revision']
    assert manifest['mixins'] == compat['horizon_mixins_revision'] == lock['horizon_mixins_revision']
    assert bundle['compatibility']['horizon_revision'] == manifest['horizon']
    assert len(manifest['horizon']) == len(manifest['mixins']) == 40
    # The mod hooks private renderer methods, NOT Horizon's stable hook API.
    assert 'hooks' not in manifest
    targets = {
        'page_runs_already_sorted': 'horizon_client_render::gfx::page_runs::PageRuns::regroup',
        'column_bounds_one_pass': 'horizon_client_render::gfx::resident::Column::bounds',
        'tiny_translucency_sort': 'horizon_client_render::gfx::translucency::Sorter::sort',
    }
    injections = bundle['injection']
    assert len(injections) == len(targets)
    for injection in injections:
        assert injection['target'] == targets.pop(injection['id'])
        assert injection['kind'] == ('HEAD' if injection['id'] == 'column_bounds_one_pass' else 'OVERWRITE')
        assert injection.get('cancellable', False) == (injection['kind'] == 'HEAD')
        assert (BUNDLE / injection['helper']).is_file()
        assert len(injection['bindings']) == {'page_runs_already_sorted': 4, 'column_bounds_one_pass': 1, 'tiny_translucency_sort': 3}[injection['id']]
    assert not targets
    return manifest


def package(output=None):
    manifest = checks()
    content = {'horizon-native.json': json.dumps(manifest, indent=2, sort_keys=True) + '\n'}
    for file in sorted(BUNDLE.iterdir()):
        if file.suffix in ('.toml', '.rs'):
            content[f'mixins/{manifest["id"]}/{file.name}'] = file.read_text()
    out = Path(output) if output else ROOT / f'{manifest["id"]}-{manifest["version"]}.hnmod'
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w') as z:
        for name, txt in sorted(content.items()):
            metadata = zipfile.ZipInfo(name, (2026, 10, 31, 0, 0, 0))
            metadata.compress_type = zipfile.ZIP_DEFLATED
            metadata.external_attr = 0o100644 << 16
            z.writestr(metadata, txt.encode('utf-8'))
    print(json.dumps({
        'status': 'UNCOMPILED_SOURCE_BUNDLE', 'file': str(out),
        'bytes': out.stat().st_size, 'sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
        'injections': len(tomllib.loads((BUNDLE / 'horizon-mixin.toml').read_text())['injection']),
    }, indent=2))
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    package(args.output)
