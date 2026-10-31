import unittest
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aggregate_benchmarks import aggregate
from baseline_report import summarize
import json


class ActualBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.r = json.loads((ROOT / 'benchmarks' / 'vanilla-aa27eca-standard.json').read_text())

    def test_baseline(self):
        s = summarize(self.r)
        self.assertEqual(len(s['scenes']), 4)
        self.assertEqual(s['conditions']['render_distance'], 16)
        self.assertAlmostEqual(s['mean_of_scene_avg_fps'], 1078.977, places=2)
        self.assertTrue(s['single_run_per_scene'])

    def test_aggregate_three_independent_runs(self):
        a = aggregate([self.r, self.r, self.r])
        self.assertEqual(a['conditions']['repeats'], 3)
        self.assertEqual(len(a['frames']), 12)
        self.assertEqual({x['repeat'] for x in a['frames']}, {0, 1, 2})
        self.assertEqual(a['metrics'], {})

    def test_aggregate_rejects_settings_change(self):
        copy = json.loads(json.dumps(self.r))
        copy['conditions']['render_distance'] = 12
        with self.assertRaises(ValueError):
            aggregate([self.r, copy, self.r])

    def test_aggregate_rejects_version_change(self):
        copy = json.loads(json.dumps(self.r))
        copy['app']['version'] = 'other'
        with self.assertRaises(ValueError):
            aggregate([self.r, copy, self.r])

    def test_aggregate_rejects_single_run(self):
        with self.assertRaises(ValueError):
            aggregate([self.r])


if __name__=='__main__':
    unittest.main()
