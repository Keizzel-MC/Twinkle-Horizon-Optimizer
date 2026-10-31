"""Behavioral comparison for the 0..2-quad stable-sort fast path.
Distance scoring uses float32 rounding and f32 total ordering bit transforms.
"""
import math
import random
import struct
import unittest


def f32(x):
    try:
        return struct.unpack('>f', struct.pack('>f', x))[0]
    except OverflowError:
        return math.copysign(float('inf'), x)


def bits(x):
    return struct.unpack('>I', struct.pack('>f', x))[0]


def total_key(v):
    b = bits(v)
    return ((~b) & 0xffffffff) if b & 0x80000000 else b ^ 0x80000000


def distance(center, camera):
    x, y, z = (f32(f32(camera[i]) - f32(center[i])) for i in range(3))
    return f32(f32(f32(x*x) + f32(y*y)) + f32(z*z))


def original(centers, camera):
    order = [(i, distance(center, camera)) for i, center in enumerate(centers)]
    order.sort(key=lambda e: total_key(e[1]), reverse=True)
    indices = []
    for quad, _ in order:
        v = quad * 4
        indices.extend((v, v+1, v+2, v+2, v+3, v))
    return [(i, bits(d)) for i, d in order], indices


def optimized(centers, camera):
    if len(centers) > 2:
        return original(centers, camera)
    order = [(i, distance(center, camera)) for i, center in enumerate(centers)]
    if len(order) == 2 and total_key(order[1][1]) > total_key(order[0][1]):
        order.reverse()
    indices = []
    for quad, _ in order:
        v = quad * 4
        indices.extend((v, v+1, v+2, v+2, v+3, v))
    return [(i, bits(d)) for i, d in order], indices


class SmallSortTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(original([], [0]*3), optimized([], [0]*3))

    def test_single(self):
        self.assertEqual(original([[1,2,3]], [0,0,0]), optimized([[1,2,3]], [0,0,0]))

    def test_distance_ascending_descending_and_ties(self):
        for centers in ([[[0,0,0], [10,0,0]], [[10,0,0], [0,0,0]],
                         [[10,0,0], [-10,0,0]], [[-0.0,0,0], [0.0,0,0]]]):
            self.assertEqual(original(centers, [0,0,0]), optimized(centers, [0,0,0]))

    def test_special_floats(self):
        for a in (0.0, -0.0, float('inf'), -float('inf'), float('nan')):
            for b in (0.0, -0.0, float('inf'), -float('inf'), float('nan')):
                centers = [[a,0,0], [b,0,0]]
                self.assertEqual(original(centers, [0,0,0]), optimized(centers, [0,0,0]))

    def test_larger_quads_preserve_original(self):
        rng = random.Random(220627)
        for _ in range(10000):
            centers = [[rng.uniform(-2000, 2000) for _ in range(3)]
                       for _ in range(rng.randrange(3, 30))]
            camera = [rng.uniform(-500,500) for _ in range(3)]
            self.assertEqual(original(centers, camera), optimized(centers, camera))

    def test_random_30000(self):
        rng = random.Random(20262026)
        for _ in range(30_000):
            centers = [[rng.uniform(-10000,10000) for _ in range(3)]
                       for _ in range(rng.randrange(0, 3))]
            camera = [rng.uniform(-10000,10000) for _ in range(3)]
            self.assertEqual(original(centers,camera), optimized(centers,camera))


if __name__ == '__main__':
    unittest.main()
