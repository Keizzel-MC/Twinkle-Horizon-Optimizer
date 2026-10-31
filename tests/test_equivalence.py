"""Independent Python behavioral models of the exact pinned Rust routines.
These tests do NOT compile the native hook: they test its algorithmic contract.
"""
from copy import deepcopy
import random
import unittest


def regroup_original(runs, draws, pages, base):
    """Model of pinned PageRuns::regroup, including the original page-only shortcut."""
    def page(run):
        return run['key'] & 0xffffffff
    if all(page(runs[i - 1]) == page(runs[i]) for i in range(1, len(runs))):
        return runs
    runs.sort(key=lambda r: r['key'])  # stable Python sort mirrors stable Rust sort_by_key
    scratch = []
    for run in runs:
        start, end = run['start'], run['start'] + run['len']
        run['start'] = base + len(scratch)
        scratch.extend(zip(draws[start:end], pages[start:end]))
    for i, (draw, page_pair) in enumerate(scratch):
        draws[base + i] = draw
        pages[base + i] = page_pair
    return runs


def regroup_optimized(runs, draws, pages, base):
    """Model of our HEAD fastpath followed by untouched original if not taken."""
    if all(runs[i - 1]['key'] <= runs[i]['key'] for i in range(1, len(runs))):
        return runs
    return regroup_original(runs, draws, pages, base)


def original_bounds(sections):
    low = min((section for section, _ in sections), default=0)
    high = max((section for section, _ in sections), default=0)
    return low, high


def one_pass_bounds(sections):
    if not sections:
        return 0, 0
    low = high = sections[0][0]
    for y, _ in sections[1:]:
        low = min(low, y)
        high = max(high, y)
    return low, high


def compare_run_state(runs, draws, pages, base):
    a = deepcopy((runs, draws, pages))
    b = deepcopy((runs, draws, pages))
    result_a = regroup_original(*a, base)
    result_b = regroup_optimized(*b, base)
    assert a == b and result_a == result_b, ('Mismatch', runs, a, b)


class PageRunsTests(unittest.TestCase):
    def dataset(self, keys, lens, prefix=0, suffix=0):
        # each (key, len) is one section, runs are in original draw order
        draws = [(-1, -1)] * prefix
        pages = [(-99, None)] * prefix
        runs = []
        for i, (key, length) in enumerate(zip(keys, lens)):
            runs.append(dict(key=key, len=length, start=len(draws), tag=[i, key & 3, length]))
            for j in range(length):
                draws.append((i, j))
                pages.append((key & 0xffffffff, None))
        draws += [(-2, -2)] * suffix
        pages += [(-98, None)] * suffix
        return runs, draws, pages, prefix

    def test_empty(self):
        compare_run_state(*self.dataset([], []))
        compare_run_state(*self.dataset([], [], 3, 2))

    def test_single(self):
        compare_run_state(*self.dataset([12], [3], 2, 4))

    def test_same_page_different_bands(self):
        # This path is special in original Rust: no grouping even if bands fall out of order.
        compare_run_state(*self.dataset([(5 << 32) | 1, (3 << 32) | 1], [3, 1], 1, 1))

    def test_key_sorted_multi_page(self):
        for keys in ([0, 1, 2, 3], [0, 0, 1, 1, 2], [1, 3, 3, 3, 5], [0, 2**64 - 1]):
            compare_run_state(*self.dataset(keys, [2] * len(keys), 5, 7))

    def test_out_of_order_multi_page(self):
        for keys in ([2, 1, 2, 1], [100, 3, 100, 4], [2**64-1, 0, 2**64-1],
                     [(2 << 32) | 4, (1 << 32) | 7, (2 << 32) | 4]):
            compare_run_state(*self.dataset(keys, [3] * len(keys), 4, 2))

    def test_ties_stay_stable(self):
        compare_run_state(*self.dataset([2, 1, 2, 1, 2, 1, 2], [2, 4, 1, 5, 1, 2, 3]))

    def test_random_30000(self):
        rng = random.Random(20261031)
        for case in range(30_000):
            count = rng.randrange(0, 38)
            mode = case % 6
            if mode == 0:
                keys = sorted(rng.randrange(0, 22) for _ in range(count))
            elif mode == 1:
                keys = [((rng.randrange(0, 8) << 32) | 7) for _ in range(count)]
            elif mode == 2:
                keys = [rng.choice([0, 1, 2]) for _ in range(count)]
            elif mode == 3:
                keys = sorted((rng.randrange(0, 6) << 32 | rng.randrange(0, 9) for _ in range(count)), reverse=True)
            elif mode == 4:
                keys = [rng.getrandbits(64) for _ in range(count)]
            else:
                keys = [((rng.randrange(0, 5) << 32) | rng.randrange(0, 3)) for _ in range(count)]
            lens = [rng.randrange(1, 8) for _ in range(count)]
            prefix, suffix = rng.randrange(0, 6), rng.randrange(0, 6)
            try:
                compare_run_state(*self.dataset(keys, lens, prefix, suffix))
            except AssertionError as e:
                self.fail(f'Case {case}: {e}')


class ColumnBoundsTests(unittest.TestCase):
    def test_empty_single_and_extremes(self):
        for ys in ([], [0], [3], [-7], [2**31 - 1], [-2**31], [-2**31, 2**31 - 1],
                   [2**31 - 1, -2**31, -2**31], [4, 4, 4, 4]):
            values = [(y, i) for i, y in enumerate(ys)]
            self.assertEqual(original_bounds(values), one_pass_bounds(values))

    def test_random_30000(self):
        rng = random.Random(10262026)
        for _ in range(30_000):
            ys = [rng.randint(-2**31, 2**31 - 1) for _ in range(rng.randrange(0, 160))]
            values = [(y, i) for i, y in enumerate(ys)]
            self.assertEqual(original_bounds(values), one_pass_bounds(values))


if __name__ == '__main__':
    unittest.main()
