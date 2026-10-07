"""Headway (SPEC 9.1): who follows whom. `headway_pairs` and `point_polyline_distance` are in the CORE part of PKStudio.py (known answers)."""
import os
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(os.path.dirname(HERE), "PKStudio.py"), encoding="utf-8").read()
NS = {"np": np}
exec(SRC[SRC.index("# ==== CORE-BEGIN"):SRC.index("# ==== CORE-END")], NS)
pairs, dist, edge = NS["headway_pairs"], NS["point_polyline_distance"], NS["shared_edge"]

# every vehicle drives along +x (y = its lane offset); positions at the reference time = (x at that time, y)
LANE_Y = {"A": 0.0, "B": 1.8, "C": 0.0, "D": 0.1}                    # B drives beside A / C (1.8 m to the side), D almost in A's path
SPEED = 10.0


def path_of(vid):
    return np.array([[x, LANE_Y[vid]] for x in np.arange(-50.0, 200.0, 1.0)])


def ref_position(vid, t):
    return (SPEED * t, LANE_Y[vid])


def half_sum(ca, cb):
    return (1.8 + 0.7) / 2.0 if "Motorcycle" in (ca, cb) else 1.8                # car + car 1.8 m; car + motorcycle 1.25 m


def ev(t, vid, cls="Car"):
    return (t, vid, cls, "Line 1", "")


class Headway(unittest.TestCase):
    def test_point_to_polyline_distance(self):
        line = [(0, 0), (10, 0), (10, 10)]
        self.assertAlmostEqual(dist((5, 3), line), 3.0)
        self.assertAlmostEqual(dist((12, 5), line), 2.0)                   # next to the second segment
        self.assertAlmostEqual(dist((-3, 4), line), 5.0)                   # beyond the start: distance to the end point
        self.assertIsNone(dist((0, 0), []))

    def test_followers_in_the_same_path_are_paired_in_order(self):
        out = pairs([ev(1.0, "A"), ev(3.0, "C"), ev(5.5, "D")], ref_position, path_of, half_sum)
        self.assertEqual([(g["id_a"], g["id_b"]) for g in out], [("A", "C"), ("C", "D")])      # A->C, C->D (not A->D)
        self.assertAlmostEqual(out[0]["gap_end"] - out[0]["gap_start"], 2.0)
        self.assertAlmostEqual(out[0]["lateral_m"], 0.0)

    def test_a_vehicle_beside_is_skipped_over(self):
        # A passes at 1 s, B (1.8 m beside, same class pair limit 1.8 m -> 1.8 > 1.8 is False, so use a 2.5 m offset) at 2 s, C (in A's path) at 3 s
        LANE_Y["B"] = 2.5
        out = pairs([ev(1.0, "A"), ev(2.0, "B"), ev(3.0, "C")], ref_position, path_of, half_sum)
        LANE_Y["B"] = 1.8
        self.assertEqual([(g["id_a"], g["id_b"]) for g in out], [("A", "C")])                  # B is beside: no pair with A, and C skips B
        # B itself has nobody in its own path: no pair for it either

    def test_the_limit_is_half_the_width_sum(self):
        LANE_Y["B"] = 1.79                                                                    # a hair inside 1.8 m -> still in the path
        inside = pairs([ev(1.0, "A"), ev(2.0, "B")], ref_position, path_of, half_sum)
        LANE_Y["B"] = 1.81                                                                    # a hair outside -> not following
        outside = pairs([ev(1.0, "A"), ev(2.0, "B")], ref_position, path_of, half_sum)
        LANE_Y["B"] = 1.8
        self.assertEqual(len(inside), 1)
        self.assertEqual(outside, [])

    def test_max_headway_stops_the_search(self):
        self.assertEqual(len(pairs([ev(1.0, "A"), ev(9.0, "C")], ref_position, path_of, half_sum, None)), 1)
        self.assertEqual(pairs([ev(1.0, "A"), ev(9.0, "C")], ref_position, path_of, half_sum, 5.0), [])

    def test_missing_path_is_kept_and_flagged(self):
        out = pairs([ev(1.0, "A"), ev(3.0, "C")], lambda v, t: None, lambda v: None, half_sum)
        self.assertEqual(len(out), 1)
        self.assertIn("No_Path_Check", out[0]["qc"])
        self.assertIsNone(out[0]["lateral_m"])

    def test_one_event_per_vehicle(self):
        out = pairs([ev(3.0, "C"), ev(1.0, "A"), ev(1.2, "A")], ref_position, path_of, half_sum)    # A's earliest event (1.0 s) counts
        self.assertEqual([(g["id_a"], g["id_b"], g["gap_start"]) for g in out], [("A", "C", 1.0)])


class SharedEdge(unittest.TestCase):
    A = [(0, 0), (10, 0), (10, 10), (0, 10)]

    def test_two_squares_sharing_a_side(self):
        e = edge(self.A, [(10, 0), (20, 0), (20, 10), (10, 10)])
        self.assertEqual(sorted(e), [(10.0, 0.0), (10.0, 10.0)])

    def test_corners_touching_the_side_of_the_other_zone(self):
        e = edge(self.A, [(10, -20), (20, -20), (20, 30), (10, 30)])            # the other zone is much longer: A's corners lie on its side
        self.assertEqual(sorted(e), [(10.0, 0.0), (10.0, 10.0)])

    def test_nodes_within_the_tolerance_are_one_node(self):
        e = edge(self.A, [(12, 1), (20, 0), (20, 10), (12, 9)], tol=3.0)         # almost touching (2 px apart)
        self.assertIsNotNone(e)
        self.assertEqual(edge(self.A, [(12, 1), (20, 0), (20, 10), (12, 9)], tol=1.0), None)

    def test_zones_that_do_not_touch(self):
        self.assertIsNone(edge(self.A, [(30, 0), (40, 0), (40, 10), (30, 10)]))

    def test_the_user_s_edge_table(self):
        self.assertEqual(NS["ZONE_EDGE_DEFAULT"], {"1-3-4": (1, 3), "1-3-6-7": (1, 3), "2-3-1": (2, 3), "2-3-4": (2, 3), "5-6-7": (5, 6), "5-6-3-1": (3, 6)})


if __name__ == "__main__":
    unittest.main()
