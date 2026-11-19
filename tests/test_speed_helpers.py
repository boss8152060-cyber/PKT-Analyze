"""Speed-up helpers (PKT 1.33.0): they must give the same answers as the plain code they replace."""
import math
import os
import random
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(os.path.dirname(HERE), "PKStudio.py"), encoding="utf-8").read()
NS = {"np": np, "math": math, "os": os}
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


class TensorRtPackages(unittest.TestCase):
    def test_pip_package_follows_the_cuda_of_pytorch(self):
        spec = NS["tensorrt_pip_spec"]
        self.assertEqual(spec("12.4"), "tensorrt-cu12<11")
        self.assertEqual(spec("13.0"), "tensorrt-cu13")
        self.assertEqual(spec(None), "tensorrt<11")

    def test_wrong_build_is_found(self):
        mism = NS["tensorrt_build_mismatch"]
        self.assertTrue(mism("12.4", {"tensorrt": "11.4.0.106", "tensorrt_cu13": "11.4.0.106"}))
        self.assertTrue(mism("12.4", {"tensorrt": "10.16.1.11", "tensorrt_cu13": "10.16.1.11"}))
        self.assertTrue(mism("12.4", {"tensorrt": "11.0.0"}))
        self.assertFalse(mism("12.4", {"tensorrt_cu12": "10.16.1.11", "tensorrt_cu12_libs": "10.16.1.11"}))
        self.assertFalse(mism("12.4", {}))
        self.assertFalse(mism("13.0", {"tensorrt_cu13": "11.4"}))
        self.assertFalse(mism(None, {"tensorrt_cu13": "11.4"}))

    def test_a_failing_build_raises_instead_of_crashing_the_program(self):
        with self.assertRaises(RuntimeError):
            NS["build_tensorrt_engine"]("no_such_model.pt", os.path.join(HERE, "no_such.engine"), 640, "cpu", timeout_s=120)


class GpuBackends(unittest.TestCase):
    def test_vendor_from_the_name(self):
        v = NS["gpu_vendor"]
        self.assertEqual(v("NVIDIA GeForce GTX 1650"), "nvidia")
        self.assertEqual(v("NVIDIA RTX A2000 Laptop GPU"), "nvidia")
        self.assertEqual(v("AMD Radeon(TM) Graphics"), "amd")
        self.assertEqual(v("Radeon RX 6600"), "amd")
        self.assertEqual(v("Intel(R) UHD Graphics 630"), "intel")
        self.assertEqual(v("Microsoft Basic Display Adapter"), "other")
        self.assertEqual(v(None), "other")

    def test_the_installed_tensorrt_version_is_found_under_any_package_name(self):
        class Fake:
            def __init__(self, have):
                self.have = have

            def version(self, name):
                if name in self.have:
                    return self.have[name]
                raise LookupError(name)
        f = NS["installed_tensorrt_version"]
        self.assertEqual(f(Fake({})), "")                                              # nothing installed: no version (engine name ..._trtx)
        self.assertEqual(f(Fake({"tensorrt_cu12": "10.16.1.11"})), "10.16.1.11")
        self.assertEqual(f(Fake({"tensorrt": "10.3.0", "tensorrt_cu12": "10.16.1.11"})), "10.3.0")
        name = NS["tensorrt_engine_name"]("m/best.pt", 640, True, (7, 5), f(Fake({"tensorrt_cu12": "10.16.1.11"})))
        self.assertTrue(name.endswith("_sm75_trt10.engine"))                           # the name after the install carries the version

    def test_engine_name_tells_the_gpu_generation_and_precision(self):
        n = NS["tensorrt_engine_name"]
        base = os.path.join("x", "best.pt")
        self.assertEqual(n(base, 640, True, (7, 5), "10.16.1.11"), os.path.join("x", "best") + "_640_fp16_sm75_trt10.engine")
        self.assertEqual(n(base, 960, False, (8, 6), "11.4"), os.path.join("x", "best") + "_960_fp32_sm86_trt11.engine")
        self.assertNotEqual(n(base, 640, True, (7, 5), "10.1"), n(base, 640, True, (8, 9), "10.1"))      # another GPU generation = another file
        self.assertTrue(n(base, 640, True, None, "").endswith("_smXX_trtx.engine"))

    def test_directml_onnx_name_has_the_size(self):
        self.assertEqual(NS["directml_onnx_name"](os.path.join("m", "best.pt"), 640), os.path.join("m", "best") + "_640_dml.onnx")


class SpeedPerZone(unittest.TestCase):
    """2_Speed.csv: one row per vehicle per stay in a zone, made from the per-frame speeds."""

    @staticmethod
    def _rows(vid, zone, t0, speeds, flag_at=(), mv="2-3-4"):
        return [{"Vehicle_ID": vid, "Vehicle_Class": "Car", "Zone": zone, "Movement": mv, "Time_s": f"{t0 + i / 30.0:.6f}",
                 "Speed_kmh": f"{v:.2f}", "QC_Flag": "Speed_Above_Max" if i in flag_at else ""} for i, v in enumerate(speeds)]

    def test_one_row_per_vehicle_and_zone_in_the_order_it_passed(self):
        rows = self._rows(1, "Zone 2", 0.0, [20, 30, 40]) + self._rows(1, "Zone 3", 0.1, [10, 20]) + self._rows(1, "Zone 4", 0.2, [50, 60])
        rows += self._rows(2, "Zone 2", 5.0, [25, 35])
        out = NS["speed_zone_summary"](rows)
        self.assertEqual([(r["Vehicle_ID"], r["Zone"], r["Zone_Order"], r["Zone_Path"]) for r in out],
                         [(1, "Zone 2", 1, "2-3-4"), (1, "Zone 3", 2, "2-3-4"), (1, "Zone 4", 3, "2-3-4"), (2, "Zone 2", 1, "2")])
        z2 = out[0]
        self.assertEqual((z2["Mean_Speed_kmh"], z2["Median_Speed_kmh"], z2["Min_Speed_kmh"], z2["Max_Speed_kmh"]), ("30.00", "30.00", "20.00", "40.00"))
        self.assertEqual((z2["Entry_Speed_kmh"], z2["Exit_Speed_kmh"], z2["Frames"]), ("20.00", "40.00", 3))
        self.assertEqual((z2["Entry_Time_s"], z2["Exit_Time_s"], z2["Time_In_Zone_s"]), ("0.000", "0.067", "0.067"))
        self.assertEqual(set(out[0]), set(NS["SPEED_ZONE_FIELDS"]))

    def test_frames_above_the_limit_are_left_out_of_the_values(self):
        out = NS["speed_zone_summary"](self._rows(1, "Zone 3", 0.0, [20, 300, 40], flag_at=(1,)))
        self.assertEqual((out[0]["Mean_Speed_kmh"], out[0]["Frames_Above_Max"], out[0]["QC_Flag"]), ("30.00", 1, ""))
        out = NS["speed_zone_summary"](self._rows(1, "Zone 3", 0.0, [300], flag_at=(0,)))
        self.assertEqual((out[0]["Mean_Speed_kmh"], out[0]["QC_Flag"]), ("", "All_Frames_Above_Max"))

    def test_coming_back_to_a_zone_is_a_new_stay(self):
        rows = self._rows(1, "Zone 3", 0.0, [10, 10]) + self._rows(1, "Zone 6", 1.0, [20]) + self._rows(1, "Zone 3", 2.0, [30])
        rows += self._rows(1, "Zone 3", 9.0, [40])                     # a long break in the same zone: also a new stay
        out = NS["speed_zone_summary"](rows)
        self.assertEqual([r["Zone"] for r in out], ["Zone 3", "Zone 6", "Zone 3", "Zone 3"])
        self.assertEqual(out[0]["Zone_Path"], "3-6-3-3")

    def test_standing_frames_are_left_out_like_gap_and_ttc(self):
        speeds = [0.0, 3.0, 0.5, 4.9, 20.0, 30.0]                       # waits 4 frames (< 5 km/h, the box flickers), then drives off
        out = NS["speed_zone_summary"](self._rows(1, "Zone 1", 0.0, speeds))
        r = out[0]
        self.assertEqual((r["Mean_Speed_kmh"], r["Min_Speed_kmh"], r["Entry_Speed_kmh"]), ("25.00", "20.00", "20.00"))
        self.assertEqual((r["Moving_Frames"], r["Stopped_Frames"], r["Stopped_Time_s"], r["Frames"]), (2, 4, "0.133", 6))
        self.assertEqual(r["QC_Flag"], "")
        only = NS["speed_zone_summary"](self._rows(1, "Zone 1", 0.0, [0.2, 1.0, 0.0]))[0]       # never moved: no speed
        self.assertEqual((only["Mean_Speed_kmh"], only["QC_Flag"]), ("", "Stopped"))
        keep = NS["speed_zone_summary"](self._rows(1, "Zone 1", 0.0, speeds), stop_kmh=0)[0]    # 0 = keep every frame
        self.assertEqual(keep["Moving_Frames"], 6)

    def test_eta_counts_only_the_frames_that_are_detected(self):
        eta = NS["eta_seconds"]
        self.assertAlmostEqual(eta(90007, 21020, 29.28, 1), (90007 - 21020) / 29.28)           # every frame: frames left / frames per second
        self.assertAlmostEqual(eta(90007, 21020, 29.28, 2), (90007 - 21020) / 2 / 29.28)       # every 2nd frame: half of it (was shown twice as long)
        self.assertAlmostEqual(eta(100, 0, 10, 5), 2.0)
        self.assertEqual(eta(100, 100, 10, 2), 0.0)
        self.assertEqual(eta(100, 120, 10, 2), 0.0)                                            # past the end: never negative
        self.assertEqual(eta(100, 10, 0, 2), 0.0)                                              # no speed yet
        self.assertAlmostEqual(eta(100, 0, 10, 0), 10.0)                                       # a skip below 1 counts as 1

    def test_edge_length_scale_factor(self):
        f = NS["edge_scale_factor"]
        self.assertIsNone(f([]))
        self.assertIsNone(f([(10.0, None), (0.0, 5.0), (4.0, 0.0)]))                  # nothing usable
        self.assertAlmostEqual(f([(10.0, 11.0)]), 1.1)                                  # one known edge: the ratio
        self.assertAlmostEqual(f([(10.0, 11.0), (20.0, 22.0), (5.0, 5.5)]), 1.1)        # all edges 10 % short: the same factor
        self.assertAlmostEqual(f([(10.0, 11.0), (20.0, 20.0)]), (110 + 400) / (100 + 400))   # least squares through the origin: long edges count more
        err = NS["edge_length_errors"]
        self.assertAlmostEqual(err([(10.0, 11.0)])[0], -100.0 / 11.0)                   # measured 10 against real 11: -9.09 %
        self.assertEqual(err([(10.0, None), (10.0, 0)]), [None, None])
        self.assertAlmostEqual(err([(10.0, 11.0)], 1.1)[0], 0.0)                        # after the factor it fits

    def test_nothing_in_nothing_out(self):
        self.assertEqual(NS["speed_zone_summary"]([]), [])


if __name__ == "__main__":
    unittest.main()
