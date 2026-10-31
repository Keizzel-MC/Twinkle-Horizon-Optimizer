import importlib.util
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from package import checks, package
from compare_benchmarks import compare


class BundleTests(unittest.TestCase):
    def test_manifest_and_injections(self):
        manifest = checks()
        self.assertEqual(manifest['schema'], 1)
        self.assertNotIn('hooks', manifest)
        toml = tomllib.loads((ROOT / 'native/twinkle_opt/mixins/twinkle_opt/horizon-mixin.toml').read_text())
        self.assertEqual(len(toml['injection']), 3)
        self.assertEqual([i['kind'] for i in toml['injection']], ['OVERWRITE', 'HEAD', 'OVERWRITE'])

    def test_reproducible_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            one = package(Path(td) / '1.hnmod')
            two = package(Path(td) / '2.hnmod')
            self.assertEqual(one.read_bytes(), two.read_bytes())
            with ZipFile(one) as z:
                self.assertEqual(len(z.namelist()), 5)
                self.assertEqual(z.namelist(), sorted(z.namelist()))
                self.assertEqual(json.loads(z.read('horizon-native.json'))['version'], '0.2.1')
                self.assertNotIn('hooks', json.loads(z.read('horizon-native.json')))
                self.assertTrue(all(x.filename == 'horizon-native.json' or
                                    x.filename.startswith('mixins/twinkle_opt/') for x in z.infolist()))

    def test_source_pins_are_exact_sha1(self):
        pins = json.loads((ROOT / 'source-lock.json').read_text())
        self.assertEqual(len(pins['horizon_revision']), 40)
        for rev in [pins['horizon_revision'], pins['horizon_mixins_revision'],
                    *pins['original_git_blob_sha1'].values()]:
            self.assertTrue(len(rev) == 40 and all(x in '0123456789abcdef' for x in rev))

    def test_no_external_network_calls_or_unreviewed_imports(self):
        helpers = list((ROOT / 'native/twinkle_opt/mixins/twinkle_opt').glob('*.rs'))
        self.assertEqual(len(helpers), 3)
        for helper in helpers:
            text = helper.read_text()
            for forbidden in ('unsafe', 'std::net', 'reqwest', 'std::process', 'std::fs',
                              'include_bytes!', 'extern crate', 'Command::', 'std::env'):
                self.assertNotIn(forbidden, text)
            self.assertTrue('ControlFlow::' in text or 'sorter.order.sort_by' in text or 'runs.runs.sort_by_key' in text)


class CompareTests(unittest.TestCase):
    @staticmethod
    def sample(fps, seed='123'):
        return dict(format='horizon-benchmark-report', version=1,
                    conditions=dict(seed=seed, scenario='flight', render_distance=12,
                                    simulation_distance=12, window=[1280, 720], vsync=False),
                    frames=[dict(phase='forest', repeat=i, avg_fps=fps + i,
                                 low_1pct_fps=60 + i, p95_ms=14.5 + i, p99_ms=21 + i)
                            for i in range(3)])

    def test_comparison_uses_real_frames(self):
        rows = compare(self.sample(100), self.sample(110))
        self.assertEqual(rows['forest']['avg_fps']['base'], 101)
        self.assertEqual(rows['forest']['avg_fps']['mod'], 111)
        self.assertTrue(rows['forest']['avg_fps']['higher_is_better'])
        self.assertFalse(rows['forest']['p95_ms']['higher_is_better'])

    def test_incompatible_conditions_are_rejected(self):
        with self.assertRaises(ValueError):
            compare(self.sample(100), self.sample(110, seed='other'))

    def test_single_repeat_is_rejected(self):
        a = self.sample(100)
        a['frames'] = a['frames'][:1]
        with self.assertRaises(ValueError):
            compare(a, self.sample(120))


if __name__ == '__main__':
    unittest.main()
