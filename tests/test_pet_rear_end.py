"""PET skips pairs of conflict type Rear-end (same direction at the crossing) when `pet_exclude_rear_end` is on (SPEC 8).
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


def config(exclude):
    return {"pet_max_s": 10.0, "pet_threshold": 1.0, "pet_min_speed_kmh": None, "pet_zones": [3], "site_id": 8, "widths": {"Car": 1.8},
            "pet_use_area": False, "pet_exclude_rear_end": exclude, "risk_limits": {"pet_s": (1.0, 2.0, 3.0), "speed_kmh": (60, 40, 20)}}


class PetRearEnd(unittest.TestCase):
    def scene(self):
        ta = np.arange(0, 4.0001, 0.1)
        p = track([(t, 10 * t, 0.0) for t in ta])                                          # P along +x, 10 m/s, passes x = 20 at t = 2
        q_same = track([(t, 10 * (t + 1.0) * math.cos(0.2), -2.0 + 10 * (t + 1.0) * math.sin(0.2)) for t in ta])   # ~11 deg to P: crosses P's path from below
        r_cross = track([(t, 25.0, 10 * (t - 3.0)) for t in ta])                           # perpendicular to P
        return {"1": p, "2": q_same, "3": r_cross}, {"1": "2-3-4", "2": "2-3-4", "3": "1-3-6-7"}

    def test_same_direction_pair_is_skipped_only_when_the_switch_is_on(self):
        tracks, mv = self.scene()
        out_on, diag_on = make()._run3_pet(tracks, config(True), mv, {}, {})
        out_off, diag_off = make()._run3_pet(tracks, config(False), mv, {}, {})
        types_off = sorted(r["Conflict_Type"] for r in out_off)
        self.assertIn("Rear-end", types_off)
        self.assertNotIn("Rear-end", [r["Conflict_Type"] for r in out_on])
        self.assertEqual(diag_on["excluded_rear_end"], types_off.count("Rear-end"))
        self.assertEqual(diag_off["excluded_rear_end"], 0)
        self.assertEqual(len(out_on), len(out_off) - types_off.count("Rear-end"))     # nothing else is lost
        self.assertTrue(any(r["Conflict_Type"] == "Crossing" for r in out_on))        # the perpendicular pair stays


if __name__ == "__main__":
    unittest.main()
