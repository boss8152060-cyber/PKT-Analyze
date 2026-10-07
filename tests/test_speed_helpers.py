"""Speed-up helpers (PKT 1.33.0): they must give the same answers as the plain code they replace."""
import math
import os
import random
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(os.path.dirname(HERE), "PKStudio.py"), encoding="utf-8").read()
NS = {"np": np, "math": math}
exec(SRC[SRC.index("# ==== CORE-BEGIN"):SRC.index("# ==== CORE-END")], NS)


class PairsWithinRadius(unittest.TestCase):
    def test_same_pairs_and_order_as_the_double_loop(self):
        rnd = random.Random(7)
        for n in (0, 1, 2, 5, 30):
            pts = [(rnd.uniform(0, 60), rnd.uniform(0, 20)) for _ in range(n)]
            for radius in (5.0, 20.0, None):
                expect, far = [], 0
                for i in range(n):
                    for j in range(i + 1, n):
                        if radius is not None and math.hypot(pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]) > radius:
                            far += 1
                        else:
                            expect.append((i, j))
                got, got_far = NS["pairs_within_radius"](pts, radius)
                self.assertEqual(got, expect)
                self.assertEqual(got_far, far)

    def test_a_pair_exactly_at_the_radius_is_kept(self):
        got, far = NS["pairs_within_radius"]([(0, 0), (3, 4)], 5.0)
        self.assertEqual((got, far), ([(0, 1)], 0))


class BoxesOverlap(unittest.TestCase):
    def test_paths_that_cross_have_touching_boxes(self):
        rnd = random.Random(3)
        for _ in range(300):
            A = np.cumsum(np.array([[rnd.uniform(-1, 1), rnd.uniform(-1, 1)] for _ in range(8)]), axis=0)
            B = np.cumsum(np.array([[rnd.uniform(-1, 1), rnd.uniform(-1, 1)] for _ in range(8)]), axis=0) + rnd.uniform(-4, 4)
            if NS["path_crossing"](A, B) is not None:
                self.assertTrue(NS["boxes_overlap"](A, B))          # the filter never drops a real crossing

    def test_far_apart(self):
        self.assertFalse(NS["boxes_overlap"]([(0, 0), (1, 1)], [(5, 5), (6, 6)]))
        self.assertTrue(NS["boxes_overlap"]([(0, 0), (2, 2)], [(2, 2), (3, 3)]))   # touching at a corner counts
        self.assertFalse(NS["boxes_overlap"]([], [(0, 0)]))


class ScaledVideoSize(unittest.TestCase):
    def test_sizes(self):
        f = NS["scaled_video_size"]
        self.assertEqual(f(3840, 2160, "1920"), (1920, 1080))
        self.assertEqual(f(1920, 1080, "1920"), (1920, 1080))       # not wider: unchanged
        self.assertEqual(f(3840, 2160, "0"), (3840, 2160))          # 0 = original
        self.assertEqual(f(3840, 2160, ""), (3840, 2160))
        self.assertEqual(f(3840, 2160, "abc"), (3840, 2160))
        w, h = f(4000, 3000, "1921")
        self.assertEqual((w % 2, h % 2), (0, 0))                     # even numbers for the encoder
        self.assertEqual(w, 1920)



class EnsurePackage(unittest.TestCase):
    def test_installed_package_is_not_reinstalled(self):
        calls = []
        ok, msg = NS["ensure_python_package"]("x", runner=lambda *a, **k: calls.append(a), finder=lambda m: object())
        self.assertTrue(ok)
        self.assertEqual(calls, [])

    def test_missing_package_is_installed_with_this_python(self):
        state = {"installed": False}
        seen = []

        class R:
            returncode = 0
            stdout = stderr = ""

        def runner(cmd, **k):
            seen.append(cmd)
            state["installed"] = True
            return R()
        ok, msg = NS["ensure_python_package"]("tensorrt", "tensorrt", runner=runner, finder=lambda m: object() if state["installed"] else None)
        self.assertTrue(ok)
        self.assertEqual(seen[0][1:], ["-m", "pip", "install", "tensorrt"])

    def test_failed_install_is_reported(self):
        class R:
            returncode = 1
            stdout = ""
            stderr = "ERROR: no matching distribution"
        ok, msg = NS["ensure_python_package"]("tensorrt", runner=lambda *a, **k: R(), finder=lambda m: None)
        self.assertFalse(ok)
        self.assertIn("no matching distribution", msg)


if __name__ == "__main__":
    unittest.main()
