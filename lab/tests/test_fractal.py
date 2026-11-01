import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fractal

W, D = 128, 64
LAGS = [1, 2, 4, 8, 16]


def integrated_noise(rng):
    e = [[rng.gauss(0, 1) for _ in range(D)] for _ in range(W)]
    for x in range(W):
        for z in range(1, D):
            e[x][z] += e[x][z - 1]
    for x in range(1, W):
        for z in range(D):
            e[x][z] += e[x - 1][z]
    return {(x, z): e[x][z] for x in range(W) for z in range(D)}


def white_noise(rng):
    return {(x, z): rng.gauss(0, 1) for x in range(W) for z in range(D)}


class Lab(unittest.TestCase):
    def variogram_slope_recovers_h_half(self):
        rng = random.Random(7)
        rough = fractal.hurst(integrated_noise(rng), LAGS)
        white = fractal.hurst(white_noise(rng), LAGS)
        self.assertLess(abs(rough - 0.5), 0.08, f"rough H={rough}")
        self.assertLess(white, 0.25, f"white H={white}")


if __name__ == "__main__":
    unittest.main()
