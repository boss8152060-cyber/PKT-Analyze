"""PET counts a pair only if its conflict type (the TTC angle rule) is switched on: pet_include_rear_end / _lane_change / _crossing (SPEC 8).
`_run3_pet` is a method of the GUI class: it is pulled out of PKStudio.py with `ast` (no tkinter / cv2 needed)."""
import ast
import math
import os
import re
import unittest
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(os.path.dirname(HERE), "PKStudio.py"), encoding="utf-8").read()
NS = {"np": np, "defaultdict": defaultdict, "math": math, "re": re}
exec(SRC[SRC.index("# ==== CORE-BEGIN"):SRC.index("# ==== CORE-END")], NS)
TREE = ast.parse(SRC)
CLS = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and any(isinstance(b, ast.FunctionDef) and b.name == "_run3_pet" for b in n.body))
KEEP = [b for b in CLS.body if isinstance(b, ast.FunctionDef) and b.name in ("_run3_pet", "_run3_mean_speed_kmh", "_fmt")]
MOD = ast.Module(body=[ast.ClassDef(name="T", bases=[], keywords=[], body=KEEP, decorator_list=[])], type_ignores=[])
ast.fix_missing_locations(MOD)
NS.update(PET_RING_POINTS=24, PET_SPEED_WINDOW_S=0.5, PET_SHOW_LEAD_S=1.0, PET_SHOW_TAIL_S=0.5, PET_GAP_FLAG_S=0.5,
          risk_level_low_is_risky=lambda v, lim: "x", risk_level_high_is_risky=lambda v, lim: "x", combine_risk=lambda a, b: "x")
exec(compile(MOD, "pet", "exec"), NS)


def make():
    t = NS["T"]()
    t._run3_canonical_class = lambda x: x
    t._fmt = staticmethod(lambda v, n: "" if v is None else f"{v:.{n}f}")
    return t


def track(points):
    return [{"_m": (x, y), "_timestamp": t, "_zone_num": 3, "class_name": "Car", "frame": str(int(round(t * 10))), "_point": (x * 10, y * 10)}
            for t, x, y in points]


def config(rear=False, lane=True, cross=True):
    return {"pet_max_s": 10.0, "pet_threshold": 1.0, "pet_min_speed_kmh": None, "pet_zones": [3], "site_id": 8, "widths": {"Car": 1.8},
            "pet_use_area": False, "pet_include_rear_end": rear, "pet_include_lane_change": lane, "pet_include_crossing": cross, "risk_limits": {"pet_s": (1.0, 2.0, 3.0), "speed_kmh": (60, 40, 20)}}


class PetRearEnd(unittest.TestCase):
    def scene(self):
        ta = np.arange(0, 4.0001, 0.1)
        p = track([(t, 10 * t, 0.0) for t in ta])                                          # P along +x, 10 m/s, passes x = 20 at t = 2
        q_same = track([(t, 10 * (t + 1.0) * math.cos(0.2), -2.0 + 10 * (t + 1.0) * math.sin(0.2)) for t in ta])   # ~11 deg to P: crosses P's path from below
        r_cross = track([(t, 25.0, 10 * (t - 3.0)) for t in ta])                           # perpendicular to P
        return {"1": p, "2": q_same, "3": r_cross}, {"1": "2-3-4", "2": "2-3-4", "3": "1-3-6-7"}

    def test_each_conflict_type_has_its_own_switch(self):
        tracks, mv = self.scene()
        every, d_all = make()._run3_pet(tracks, config(rear=True), mv, {}, {})          # all three types on
        types = [r["Conflict_Type"] for r in every]
        self.assertIn("Rear-end", types)
        self.assertIn("Crossing", types)
        self.assertEqual(d_all["excluded_by_type"], 0)
        default, d_def = make()._run3_pet(tracks, config(), mv, {}, {})                  # defaults: Rear-end off
        self.assertNotIn("Rear-end", [r["Conflict_Type"] for r in default])
        self.assertEqual(d_def["excluded_rear_end"], types.count("Rear-end"))
        self.assertEqual(len(default), len(every) - types.count("Rear-end"))             # nothing else is lost
        no_cross, d_nc = make()._run3_pet(tracks, config(rear=True, cross=False), mv, {}, {})
        self.assertNotIn("Crossing", [r["Conflict_Type"] for r in no_cross])
        self.assertEqual(d_nc["excluded_crossing"], types.count("Crossing"))
        self.assertIn("Rear-end", [r["Conflict_Type"] for r in no_cross])

    def test_excluded_pairs_get_no_crossing_mark_in_the_videos(self):
        tracks, mv = self.scene()
        t_all, t_def = make(), make()
        t_all._run3_pet(tracks, config(rear=True), mv, {}, {})
        t_def._run3_pet(tracks, config(), mv, {}, {})
        self.assertLess(sum(len(v) for v in t_def._run3_pet_shapes.values()), sum(len(v) for v in t_all._run3_pet_shapes.values()))

    def test_type_switch_helper(self):
        inc = NS["pet_type_included"]
        self.assertFalse(inc("Rear-end", {}))                      # default off
        self.assertTrue(inc("Lane change", {}))
        self.assertTrue(inc("Crossing", {}))
        self.assertTrue(inc("Unclassified", {"pet_include_crossing": False}))     # no angle: always counted
        self.assertTrue(inc("Rear-end", {"pet_include_rear_end": True}))
        self.assertFalse(inc("Lane change", {"pet_include_lane_change": False}))

    def test_ttc_type_switch_helper(self):
        inc = NS["ttc_type_included"]
        self.assertTrue(all(inc(t, {}) for t in ("Rear-end", "Lane change", "Crossing", "Unclassified")))     # TTC: every type on by default
        self.assertFalse(inc("Crossing", {"ttc_include_crossing": False}))
        self.assertFalse(inc("Rear-end", {"ttc_include_rear_end": False}))
        self.assertTrue(inc("Lane change", {"ttc_include_crossing": False, "ttc_include_rear_end": False}))
        self.assertTrue(inc("Unclassified", {"ttc_include_crossing": False}))


if __name__ == "__main__":
    unittest.main()
