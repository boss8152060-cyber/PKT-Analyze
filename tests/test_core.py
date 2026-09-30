"""Unit tests for the pure-logic CORE region of PKStudio.py.

Run from the Run folder:   python -m unittest discover -s tests -v
(or: python -m pytest tests)

PKStudio.py starts a GUI/CUDA bootstrap when imported, so the tests exec only
the region between the CORE-BEGIN / CORE-END markers.
"""
import math
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "PKStudio.py")


def load_core():
    with open(SRC, encoding="utf-8") as f:
        text = f.read()
    begin = text.index("# ==== CORE-BEGIN")
    end = text.index("# ==== CORE-END ====")
    ns = {}
    exec(compile(text[begin:end], "PKStudio.py[CORE]", "exec"), ns)
    return ns


CORE = load_core()
import random
clean = CORE["clean_zone_visits"]
seq_from = CORE["zone_sequence_from_samples"]
classify = CORE["classify_movement"]
PATTERNS = CORE["MOVEMENT_PATTERNS"]


class CleanZoneVisits(unittest.TestCase):
    def test_aba_flicker_removed(self):
        self.assertEqual(clean([("A", 0, 1), ("B", 1.02, 1.05), ("A", 1.07, 2)]), [("A", 0, 2)])

    def test_brief_exit_merged(self):
        self.assertEqual(clean([("A", 0, 1), ("A", 1.05, 2)]), [("A", 0, 2)])

    def test_real_reentry_kept(self):
        v = [("A", 0, 1), ("A", 1.5, 2)]
        self.assertEqual(clean(v), v)

    def test_real_transit_kept(self):
        v = [("1", 0, 1), ("6", 1.02, 1.04), ("5", 1.06, 2)]
        self.assertEqual(clean(v), v)

    def test_long_middle_kept(self):
        v = [("A", 0, 1), ("B", 1.02, 3), ("A", 3.02, 4)]
        self.assertEqual(clean(v), v)


class Patterns(unittest.TestCase):
    def test_six_movements(self):
        self.assertEqual(
            set(PATTERNS),
            {"1-3-4", "2-3-1", "1-3-6-7", "5-6-3-1", "2-3-4", "5-6-7"},
        )

    def test_id_matches_sequence(self):
        for mid, info in PATTERNS.items():
            self.assertEqual(mid, "-".join(str(z) for z in info["sequence"]))

    def test_no_pattern_inside_another(self):
        # otherwise an Exact match could also be read as a Partial of another pattern
        for a, ia in PATTERNS.items():
            for b, ib in PATTERNS.items():
                if a == b:
                    continue
                n = len(ia["sequence"])
                frags = [ib["sequence"][i:i + n] for i in range(len(ib["sequence"]) - n + 1)]
                self.assertNotIn(ia["sequence"], frags, (a, b))

    def test_main_road_flags(self):
        self.assertEqual({m for m, i in PATTERNS.items() if i["main_road"]}, {"2-3-4", "5-6-7"})
        self.assertEqual(PATTERNS["2-3-4"]["side"], "entry")
        self.assertEqual(PATTERNS["5-6-7"]["side"], "opposite")


class Classify(unittest.TestCase):
    def test_exact(self):
        for mid, info in PATTERNS.items():
            self.assertEqual(classify(info["sequence"]), (mid, "Exact"))

    def test_consecutive_duplicates_ignored(self):
        self.assertEqual(classify([2, 2, 3, 3, 4]), ("2-3-4", "Exact"))

    def test_partial_unique(self):
        self.assertEqual(classify([1, 3, 6]), ("1-3-6-7", "Partial"))
        self.assertEqual(classify([6, 3, 1]), ("5-6-3-1", "Partial"))
        self.assertEqual(classify([3, 6, 7]), ("1-3-6-7", "Partial"))

    def test_partial_ambiguous_never_guessed(self):
        for frag in ([3, 4], [2, 3], [1, 3], [6, 7], [5, 6], [3, 1]):
            self.assertEqual(classify(frag), ("", "Ambiguous"), frag)

    def test_unclassified(self):
        self.assertEqual(classify([4, 3]), ("", "Unclassified"))
        self.assertEqual(classify([2, 3, 6, 7]), ("", "Unclassified"))

    def test_insufficient(self):
        self.assertEqual(classify([3]), ("", "Insufficient"))
        self.assertEqual(classify([]), ("", "Insufficient"))


class SequenceFromSamples(unittest.TestCase):
    @staticmethod
    def run_samples(zones, dt=1 / 60):
        return [(i * dt, z) for i, z in enumerate(zones)]

    def test_simple_through(self):
        z = [2] * 30 + [3] * 30 + [4] * 30
        self.assertEqual(seq_from(self.run_samples(z)), [2, 3, 4])

    def test_boundary_flicker_removed(self):
        # 3 -> 2 -> 3 for one frame at the 2/3 border
        z = [2] * 30 + [3] * 5 + [2] + [3] * 30 + [4] * 30
        self.assertEqual(seq_from(self.run_samples(z)), [2, 3, 4])

    def test_brief_gap_outside_zones_merged(self):
        z = [1] * 20 + [None] * 2 + [1] * 20 + [3] * 20 + [4] * 20
        self.assertEqual(seq_from(self.run_samples(z)), [1, 3, 4])

    def test_long_gap_outside_zones_kept_as_reentry_then_deduped(self):
        z = [3] * 20 + [None] * 30 + [3] * 20
        self.assertEqual(seq_from(self.run_samples(z)), [3])

    def test_right_turn_through_conflict_zones(self):
        z = [1] * 40 + [3] * 20 + [6] * 20 + [7] * 40
        self.assertEqual(classify(seq_from(self.run_samples(z))), ("1-3-6-7", "Exact"))


def make_rows(zone_plan, speed_ms=10.0, dt=1 / 60, jitter=0.0, seed=1):
    """One vehicle moving along +x at speed_ms; zone_plan = [(zone, n_samples), ...]."""
    rnd = random.Random(seed)
    rows, i = [], 0
    for zone, n in zone_plan:
        for _ in range(n):
            t = i * dt
            x = speed_ms * t + rnd.uniform(-jitter, jitter)
            y = rnd.uniform(-jitter, jitter)
            rows.append({"_timestamp": t, "_m": (x, y), "_zone_num": zone, "frame": str(i + 1)})
            i += 1
    return rows


class SpeedY6(unittest.TestCase):
    def test_path_speed_known(self):
        rows = make_rows([(2, 61)])           # 1 s at 10 m/s -> 10 m -> 36 km/h
        d, t, v = CORE["path_speed"]([r["_timestamp"] for r in rows], [r["_m"] for r in rows])
        self.assertAlmostEqual(d, 10.0, places=6)
        self.assertAlmostEqual(v, 36.0, places=6)

    def test_path_speed_rejects_short_or_static(self):
        self.assertIsNone(CORE["path_speed"]([0.0], [(0, 0)]))
        self.assertIsNone(CORE["path_speed"]([0.0, 1.0], [(0, 0), (0, 0)]))

    def test_zone_and_movement_speed(self):
        rows = make_rows([(2, 61), (3, 61), (4, 61)])
        recs = CORE["track_speed_records"](rows, {2, 3, 4}, "2-3-4", "Exact", 1)
        by = {(r["Scope"], r["Key"]): r for r in recs}
        for z in (2, 3, 4):
            self.assertAlmostEqual(by[("Zone", f"Zone {z}")]["Speed_kmh"], 36.0, places=6)
        mv = by[("Movement", "2-3-4")]
        self.assertAlmostEqual(mv["Speed_kmh"], 36.0, places=6)
        self.assertAlmostEqual(mv["Distance_m"], 182 * 10.0 / 60, places=6)   # 183 samples = 182 steps of 1/60 s
        self.assertEqual(mv["Flag"], "")

    def test_unselected_zone_not_reported_but_movement_is(self):
        rows = make_rows([(2, 61), (3, 61), (4, 61)])
        recs = CORE["track_speed_records"](rows, {3}, "2-3-4", "Exact", 1)
        self.assertEqual({(r["Scope"], r["Key"]) for r in recs}, {("Zone", "Zone 3"), ("Movement", "2-3-4")})

    def test_no_movement_when_unclassified(self):
        rows = make_rows([(3, 61), (4, 61)])
        recs = CORE["track_speed_records"](rows, {3, 4}, "", "Ambiguous", 1)
        self.assertEqual({r["Scope"] for r in recs}, {"Zone"})

    def test_partial_flag(self):
        rows = make_rows([(1, 30), (3, 30), (6, 30)])
        recs = CORE["track_speed_records"](rows, {1, 3, 6}, "1-3-6-7", "Partial", 1)
        mv = [r for r in recs if r["Scope"] == "Movement"][0]
        self.assertEqual(mv["Flag"], "Partial_Movement")

    def test_smoothing_reduces_jitter_inflation(self):
        # slow vehicle (2 m/s = 7.2 km/h, 3.3 cm per frame) with +-3 cm bbox jitter
        rows = make_rows([(2, 121)], speed_ms=2.0, jitter=0.03, seed=7)
        raw = CORE["track_speed_records"](rows, {2}, "", "", 1)[0]["Speed_kmh"]
        smooth = CORE["track_speed_records"](rows, {2}, "", "", 5)[0]["Speed_kmh"]
        self.assertGreater(raw, 7.2 + 1.5)                        # jitter inflates path length a lot
        self.assertLess(abs(smooth - 7.2), abs(raw - 7.2))        # smoothing pulls it back
        self.assertLess(abs(smooth - 7.2), 0.5)

    def test_smoothing_does_not_bias_clean_motion(self):
        rows = make_rows([(2, 61)])                              # noise-free 36 km/h
        for k in (1, 3, 5, 9, 31):
            v = CORE["track_speed_records"](rows, {2}, "", "", k)[0]["Speed_kmh"]
            self.assertAlmostEqual(v, 36.0, places=6, msg=f"k={k}")

    def test_smoothing_window_shrinks_for_short_series(self):
        rows = make_rows([(2, 4)])                               # only 4 samples, k=9 requested
        v = CORE["track_speed_records"](rows, {2}, "", "", 9)[0]["Speed_kmh"]
        self.assertAlmostEqual(v, 36.0, places=6)

    def test_rolling_median(self):
        out = CORE["rolling_median"]([0, 0, 100, 0, 0], 3)
        self.assertEqual(list(out), [0, 0, 0, 0, 0])


class LdpY1(unittest.TestCase):
    ldp = staticmethod(lambda pts, w, k=1: CORE["ldp_for_zone"](pts, w, k))

    def test_straight_line_has_zero_deviation(self):
        pts = [(x * 0.1, 0.0) for x in range(101)]
        r = self.ldp(pts, 3.5)
        self.assertAlmostEqual(r["Delta_Y_m"], 0.0, places=9)
        self.assertAlmostEqual(r["Y1_LDP_percent"], 0.0, places=9)

    def test_known_bump(self):
        # enters and leaves at y = 0, peak 0.35 m in the middle; W = 3.5 -> 10 %
        pts = [(x * 0.1, 0.35 * math.sin(math.pi * x / 100)) for x in range(101)]
        r = self.ldp(pts, 3.5)
        self.assertAlmostEqual(r["Delta_Y_m"], 0.35, places=6)
        self.assertAlmostEqual(r["Y1_LDP_percent"], 10.0, places=4)
        self.assertEqual(r["P_in"], (0.0, 0.0))

    def test_offset_but_straight_is_zero(self):
        # drives straight but hugs the kerb (y = 1.2 m): LDP is about weaving, not offset
        pts = [(x * 0.1, 1.2) for x in range(101)]
        self.assertAlmostEqual(self.ldp(pts, 3.5)["Y1_LDP_percent"], 0.0, places=9)

    def test_diagonal_path_measured_perpendicular_to_chord(self):
        # straight diagonal path (45 deg) must give 0; a 0.2 m perpendicular bump gives 0.2
        pts = [(i * 0.1, i * 0.1) for i in range(101)]
        self.assertAlmostEqual(self.ldp(pts, 3.5)["Delta_Y_m"], 0.0, places=9)
        bump = [(x + 0.2 * math.sin(math.pi * i / 100) * -math.sqrt(0.5),
                 y + 0.2 * math.sin(math.pi * i / 100) * math.sqrt(0.5))
                for i, (x, y) in enumerate(pts)]
        self.assertAlmostEqual(self.ldp(bump, 3.5)["Delta_Y_m"], 0.2, places=6)

    def test_denominator_is_full_width_not_half(self):
        pts = [(x * 0.1, 0.35 * math.sin(math.pi * x / 100)) for x in range(101)]
        self.assertAlmostEqual(self.ldp(pts, 7.0)["Y1_LDP_percent"], 5.0, places=4)

    def test_too_few_samples_or_zero_chord(self):
        self.assertIsNone(self.ldp([(0, 0), (1, 0)], 3.5))
        self.assertIsNone(self.ldp([(0, 0), (1, 1), (0, 0)], 3.5))

    def test_short_chord_flag(self):
        pts = [(x * 0.01, 0.0) for x in range(51)]          # 0.5 m chord
        self.assertTrue(self.ldp(pts, 3.5)["Short_Chord"])

    def test_smoothing_ignores_single_spike(self):
        pts = [(x * 0.1, 0.0) for x in range(101)]
        pts[50] = (5.0, 0.8)                                  # one bbox glitch
        raw = self.ldp(pts, 3.5, 1)["Delta_Y_m"]
        smooth = self.ldp(pts, 3.5, 5)["Delta_Y_m"]
        self.assertAlmostEqual(raw, 0.8, places=6)
        self.assertLess(smooth, 0.05)


class LateralClearanceY2(unittest.TestCase):
    lc = staticmethod(lambda a, h, b, la=2.0, lb=4.5, wa=0.8, wb=1.8:
                      CORE["lateral_clearance"](a, h, b, la, lb, wa, wb))

    def test_simple_side_by_side(self):
        r = self.lc((0, 0), (1, 0), (1, 2))
        self.assertAlmostEqual(r["Lateral_m"], 2.0)
        self.assertAlmostEqual(r["Along_m"], 1.0)
        self.assertAlmostEqual(r["Y2"], 2.0 - 1.3)
        self.assertTrue(r["Overlap"])

    def test_perpendicular_not_point_to_point(self):
        # B is 2 m to the side and 3 m ahead: point-to-point would give 3.6 m
        r = self.lc((0, 0), (1, 0), (3, 2), la=2.0, lb=4.5)
        self.assertAlmostEqual(r["Lateral_m"], 2.0)
        self.assertGreater(math.hypot(3, 2), 3.6)
        self.assertTrue(r["Overlap"])                 # |along| = 3 <= (2 + 4.5) / 2

    def test_axis_follows_vehicle_heading(self):
        u = (math.sqrt(0.5), math.sqrt(0.5))          # A drives diagonally
        perp = (-u[1], u[0])
        b = (2 * perp[0] + 1 * u[0], 2 * perp[1] + 1 * u[1])
        r = self.lc((0, 0), u, b)
        self.assertAlmostEqual(r["Lateral_m"], 2.0, places=9)
        self.assertAlmostEqual(r["Along_m"], 1.0, places=9)

    def test_no_overlap_when_far_apart_along_heading(self):
        r = self.lc((0, 0), (1, 0), (8, 2))            # 8 m ahead > (2 + 4.5) / 2
        self.assertFalse(r["Overlap"])

    def test_negative_when_boxes_overlap_sideways(self):
        r = self.lc((0, 0), (1, 0), (0, 0.9))          # 0.9 < (0.8 + 1.8) / 2
        self.assertLess(r["Y2"], 0)

    def test_same_direction_examples_from_the_user(self):
        sd = CORE["same_direction_in_zone"]
        a, b, c_ = (2, 3, 4), (2, 3, 1), (2, 3, 4)
        self.assertTrue(sd(a, b, 3))                   # A-B share 2-3
        self.assertTrue(sd(a, b, 2))
        self.assertFalse(sd(a, b, 4))                  # B never reaches zone 4 (seq stops before)
        self.assertTrue(sd(a, c_, 2) and sd(a, c_, 3) and sd(a, c_, 4))   # A-C share 2-3-4
        self.assertTrue(sd(b, c_, 3))                  # B-C share 2-3

    def test_crossing_or_opposite_flows_are_not_same_direction(self):
        sd = CORE["same_direction_in_zone"]
        self.assertFalse(sd((2, 3, 4), (1, 3, 6, 7), 3))   # crossing
        self.assertFalse(sd((2, 3, 4), (5, 6, 7), 3))
        self.assertFalse(sd((2, 3, 4), (5, 6, 3, 1), 3))   # 3 is shared but not a common transition
        self.assertFalse(sd((2, 3, 4), (1, 3, 4), 2))      # shared edge 3-4 does not touch zone 2
        self.assertTrue(sd((2, 3, 4), (1, 3, 4), 4))       # merging flows share 3-4

    def test_need_two_zones_observed(self):
        self.assertFalse(CORE["same_direction_in_zone"]((3,), (2, 3, 4), 3))

    def test_track_headings(self):
        ts = [i / 60 for i in range(60)]
        straight = CORE["track_headings"](ts, [(10 * t, 0.0) for t in ts], 0.5, 0.5)
        self.assertTrue(all(h is not None and abs(h[0] - 1) < 1e-9 for h in straight))
        still = CORE["track_headings"](ts, [(1.0, 1.0)] * 60, 0.5, 0.5)
        self.assertTrue(all(h is None for h in still))
        diag = CORE["track_headings"](ts, [(6 * t, -6 * t) for t in ts], 0.5, 0.5)
        self.assertAlmostEqual(diag[30][0], math.sqrt(0.5))
        self.assertAlmostEqual(diag[30][1], -math.sqrt(0.5))


class RearEndTtc(unittest.TestCase):
    VMIN = 2.0 / 3.6
    COS = math.cos(math.radians(45))

    def re(self, p_f, v_f, p_l, v_l, lf=4.5, ll=4.5, wf=1.8, wl=1.8):
        return CORE["rear_end_ttc"](p_f, v_f, p_l, v_l, lf, ll, wf, wl, self.VMIN, self.COS)

    def test_known_value(self):
        r = self.re((0, 0), (10, 0), (20, 0), (5, 0))     # S = 20 - 4.5 = 15.5 ; CS = 5
        self.assertAlmostEqual(r["S"], 15.5)
        self.assertAlmostEqual(r["CS"], 5.0)
        self.assertAlmostEqual(r["TTC"], 3.1)

    def test_stationary_leader(self):
        r = self.re((0, 0), (10, 0), (30, 0), (0, 0))
        self.assertAlmostEqual(r["TTC"], 25.5 / 10.0)

    def test_leader_behind_or_not_closing_or_beside(self):
        self.assertIsNone(self.re((20, 0), (10, 0), (0, 0), (5, 0)))        # leader behind
        self.assertIsNone(self.re((0, 0), (5, 0), (20, 0), (10, 0)))        # leader faster
        self.assertIsNone(self.re((0, 0), (10, 0), (20, 3.0), (5, 0)))      # 3 m to the side > (1.8+1.8)/2

    def test_opposite_direction_is_not_rear_end(self):
        self.assertIsNone(self.re((0, 0), (10, 0), (20, 0), (-5, 0)))

    def test_boxes_already_overlap(self):
        r = self.re((0, 0), (10, 0), (3.0, 0), (5, 0))
        self.assertIsNotNone(r)
        self.assertIsNone(r["TTC"])

    def test_slow_follower_ignored(self):
        self.assertIsNone(self.re((0, 0), (0.1, 0), (20, 0), (0, 0)))


class SideTtc(unittest.TestCase):
    VMIN = 2.0 / 3.6

    def sd(self, p_i, v_i, p_j, v_j, li=4.5, lj=4.5):
        return CORE["side_ttc"](p_i, v_i, p_j, v_j, li, lj, self.VMIN)

    def test_perpendicular_same_arrival(self):
        r = self.sd((0, -10), (0, 10), (-10, 0), (10, 0))     # both reach (0,0) after 1 s
        self.assertAlmostEqual(r["TTC"], 1.0)
        self.assertAlmostEqual(r["d_i"], 10.0)
        self.assertAlmostEqual(r["angle_deg"], 90.0)

    def test_arrivals_too_far_apart_is_no_collision(self):
        self.assertIsNone(self.sd((0, -10), (0, 10), (-20, 0), (10, 0)))    # 1 s vs 2 s, window 0.45 s

    def test_arrival_difference_inside_window(self):
        r = self.sd((0, -10), (0, 10), (-14, 0), (10, 0))                   # 1.0 s vs 1.4 s
        self.assertAlmostEqual(r["TTC"], 1.0)
        self.assertAlmostEqual(r["t_j"], 1.4)

    def test_crossing_point_behind_one_vehicle(self):
        self.assertIsNone(self.sd((0, 5), (0, 10), (-10, 0), (10, 0)))      # i already past X

    def test_parallel_or_same_direction_excluded(self):
        self.assertIsNone(self.sd((0, 0), (10, 0), (5, 2), (10, 0)))
        self.assertIsNone(self.sd((0, 0), (10, 0), (5, 2), (10, 0.5)))      # 2.9 deg < 10 deg

    def test_merging_angle_counts(self):
        # 30 deg merge: j comes from the side and joins i's path 10 m ahead of i
        x = (10.0, 0.0)
        hj = (math.cos(math.radians(150)), math.sin(math.radians(150)))     # heading up-left
        pj = (x[0] - hj[0] * 10.0, x[1] - hj[1] * 10.0)
        r = self.sd((0, 0), (10, 0), pj, (hj[0] * 10.0, hj[1] * 10.0))
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r["TTC"], 1.0, places=6)
        self.assertAlmostEqual(r["angle_deg"], 30.0, places=6)

    def test_stationary_vehicle_excluded(self):
        self.assertIsNone(self.sd((0, -10), (0, 10), (0, 0), (0, 0)))


class ConflictType(unittest.TestCase):
    def test_types(self):
        ct = CORE["conflict_type_from_sequences"]
        self.assertEqual(ct((1, 3, 4), (2, 3, 4), True), "Crossing")
        self.assertEqual(ct((1, 3, 4), (2, 3, 4)), "Merging")
        self.assertEqual(ct((1, 3, 4), (1, 3, 6, 7)), "Diverging")
        self.assertEqual(ct((2, 3, 4), (5, 6, 7)), "Merging/Diverging")
        self.assertEqual(ct([], [1, 2]), "Merging/Diverging")


if __name__ == "__main__":
    unittest.main()
