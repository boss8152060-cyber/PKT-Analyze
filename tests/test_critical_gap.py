"""Critical Gap groups (SPEC 6.1): per waiting-driver class and per class of the vehicle behind the gap. `critical_gap_groups` is in the CORE part."""
import os
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(os.path.dirname(HERE), "PKStudio.py"), encoding="utf-8").read()
NS = {"np": np}
exec(SRC[SRC.index("# ==== CORE-BEGIN"):SRC.index("# ==== CORE-END")], NS)
groups = NS["critical_gap_groups"]


def row(sid, cls, accepted, gap, lag, movement="1-3-4", stage=1):
    return {"Subject_ID": sid, "Subject_Class": cls, "Subject_Movement": movement, "Stage_No": stage,
            "Gap_Acceptance": 1 if accepted else 0, "Available_Gap_s": f"{gap:.3f}", "Conflicting_Class_B": lag}


ROWS = [
    row("S1", "Car", False, 0.6, "Car"), row("S1", "Car", False, 1.0, "Car"), row("S1", "Car", True, 2.0, "Bus"),     # S1: max rejected 1.0, accepted 2.0 (behind: Bus)
    row("S2", "Motorcycle", False, 0.8, "Car"), row("S2", "Motorcycle", True, 1.5, "Car"),
    row("S3", "Car", True, 3.0, "Car"),                                                                              # accepted only
    row("S4", "Motorcycle", False, 0.5, "Car"),                                                                      # rejected only
]


class CriticalGapGroups(unittest.TestCase):
    def test_by_waiting_driver_class_is_the_default(self):
        g = groups(ROWS)
        self.assertEqual(sorted(g), [("Car", "All", "1-3-4", 1), ("Motorcycle", "All", "1-3-4", 1)])
        car, mc = g[("Car", "All", "1-3-4", 1)], g[("Motorcycle", "All", "1-3-4", 1)]
        self.assertEqual(car["intervals"], [(1.0, 2.0)])                       # the largest rejected gap and the accepted gap of S1
        self.assertEqual((car["accepted_only"], car["rejected_only"]), (1, 0))   # S3
        self.assertEqual(mc["intervals"], [(0.8, 1.5)])
        self.assertEqual((mc["accepted_only"], mc["rejected_only"]), (0, 1))     # S4

    def test_all_classes_together(self):
        g = groups(ROWS, by_subject=False)
        self.assertEqual(list(g), [("All", "All", "1-3-4", 1)])
        self.assertEqual(sorted(g[("All", "All", "1-3-4", 1)]["intervals"]), [(0.8, 1.5), (1.0, 2.0)])
        self.assertEqual(sorted(g[("All", "All", "1-3-4", 1)]["accepted"]), [1.5, 2.0])

    def test_by_the_class_of_the_vehicle_behind_the_gap(self):
        g = groups(ROWS, by_subject=False, by_lag=True)
        self.assertEqual(sorted(g), [("All", "Bus", "1-3-4", 1), ("All", "Car", "1-3-4", 1)])
        self.assertEqual(g[("All", "Bus", "1-3-4", 1)]["intervals"], [(1.0, 2.0)])          # S1 accepted a gap that a Bus closes
        car = g[("All", "Car", "1-3-4", 1)]
        self.assertEqual(car["intervals"], [(0.8, 1.5)])
        self.assertEqual((car["accepted_only"], car["rejected_only"]), (1, 1))

    def test_both_splits(self):
        self.assertEqual(sorted(groups(ROWS, True, True)),
                         [("Car", "Bus", "1-3-4", 1), ("Car", "Car", "1-3-4", 1), ("Motorcycle", "Car", "1-3-4", 1)])

    def test_movement_and_stage_stay_separate(self):
        rows = [row("A", "Car", False, 1.0, "Car", "1-3-6-7", 1), row("A", "Car", True, 2.0, "Car", "1-3-6-7", 1),
                row("A", "Car", False, 0.5, "Car", "1-3-6-7", 2), row("A", "Car", True, 1.2, "Car", "1-3-6-7", 2)]
        g = groups(rows)
        self.assertEqual(g[("Car", "All", "1-3-6-7", 1)]["intervals"], [(1.0, 2.0)])
        self.assertEqual(g[("Car", "All", "1-3-6-7", 2)]["intervals"], [(0.5, 1.2)])


if __name__ == "__main__":
    unittest.main()
