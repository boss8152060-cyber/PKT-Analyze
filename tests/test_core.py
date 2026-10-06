"""Unit tests for the pure-logic CORE region of PKStudio.py.

Run from the Run folder:   python -m unittest discover -s tests -v
(or: python -m pytest tests)

PKStudio.py starts a GUI/CUDA bootstrap when imported, so the tests exec only
the region between the CORE-BEGIN / CORE-END markers.
"""
import math
import numpy as np
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


class SpeedTests(unittest.TestCase):
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


class LdpTests(unittest.TestCase):
    ldp = staticmethod(lambda pts, w, k=1: CORE["ldp_for_zone"](pts, w, k))

    def test_straight_line_has_zero_deviation(self):
        pts = [(x * 0.1, 0.0) for x in range(101)]
        r = self.ldp(pts, 3.5)
        self.assertAlmostEqual(r["Delta_Y_m"], 0.0, places=9)
        self.assertAlmostEqual(r["LDP_percent"], 0.0, places=9)

    def test_known_bump(self):
        # enters and leaves at y = 0, peak 0.35 m in the middle; W = 3.5 -> dY / (W/2) = 0.35 / 1.75 = 20 %
        pts = [(x * 0.1, 0.35 * math.sin(math.pi * x / 100)) for x in range(101)]
        r = self.ldp(pts, 3.5)
        self.assertAlmostEqual(r["Delta_Y_m"], 0.35, places=6)
        self.assertAlmostEqual(r["LDP_percent"], 20.0, places=4)
        self.assertEqual(r["P_in"], (0.0, 0.0))

    def test_offset_but_straight_is_zero(self):
        # drives straight but hugs the kerb (y = 1.2 m): LDP is about weaving, not offset
        pts = [(x * 0.1, 1.2) for x in range(101)]
        self.assertAlmostEqual(self.ldp(pts, 3.5)["LDP_percent"], 0.0, places=9)

    def test_diagonal_path_measured_perpendicular_to_chord(self):
        # straight diagonal path (45 deg) must give 0; a 0.2 m perpendicular bump gives 0.2
        pts = [(i * 0.1, i * 0.1) for i in range(101)]
        self.assertAlmostEqual(self.ldp(pts, 3.5)["Delta_Y_m"], 0.0, places=9)
        bump = [(x + 0.2 * math.sin(math.pi * i / 100) * -math.sqrt(0.5),
                 y + 0.2 * math.sin(math.pi * i / 100) * math.sqrt(0.5))
                for i, (x, y) in enumerate(pts)]
        self.assertAlmostEqual(self.ldp(bump, 3.5)["Delta_Y_m"], 0.2, places=6)

    def test_denominator_is_half_the_width(self):
        pts = [(x * 0.1, 0.35 * math.sin(math.pi * x / 100)) for x in range(101)]
        self.assertAlmostEqual(self.ldp(pts, 7.0)["LDP_percent"], 10.0, places=4)    # 0.35 / 3.5
        self.assertAlmostEqual(self.ldp(pts, 1.4)["LDP_percent"], 50.0, places=4)    # 0.35 / 0.7

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


class LateralClearanceTests(unittest.TestCase):
    lc = staticmethod(lambda a, h, b, la=2.0, lb=4.5, wa=0.8, wb=1.8:
                      CORE["lateral_clearance"](a, h, b, la, lb, wa, wb))

    def test_simple_side_by_side(self):
        r = self.lc((0, 0), (1, 0), (1, 2))
        self.assertAlmostEqual(r["Lateral_m"], 2.0)
        self.assertAlmostEqual(r["Along_m"], 1.0)
        self.assertAlmostEqual(r["Clearance_m"], 2.0 - 1.3)
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

    def test_fixed_along_limit_replaces_the_automatic_one(self):
        f = CORE["lateral_clearance"]
        near = f((0, 0), (1, 0), (5, 2), 2.0, 4.5, 0.8, 1.8)                     # 5 m ahead > (2 + 4.5) / 2
        wide = f((0, 0), (1, 0), (5, 2), 2.0, 4.5, 0.8, 1.8, along_limit=6.0)
        self.assertFalse(near["Overlap"])
        self.assertTrue(wide["Overlap"])

    def test_max_lateral_drops_unrelated_pairs(self):
        f = CORE["lateral_clearance"]
        far = f((0, 0), (1, 0), (0.5, 8.0), 2.0, 4.5, 0.8, 1.8, max_lateral=3.5)  # 8 m sideways
        near = f((0, 0), (1, 0), (0.5, 3.0), 2.0, 4.5, 0.8, 1.8, max_lateral=3.5)
        off = f((0, 0), (1, 0), (0.5, 8.0), 2.0, 4.5, 0.8, 1.8, max_lateral=0)    # 0 = no limit
        self.assertTrue(far["Too_Far"])
        self.assertFalse(near["Too_Far"])
        self.assertFalse(off["Too_Far"])

    def test_negative_when_boxes_overlap_sideways(self):
        r = self.lc((0, 0), (1, 0), (0, 0.9))          # 0.9 < (0.8 + 1.8) / 2
        self.assertLess(r["Clearance_m"], 0)

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


class RiskLevels(unittest.TestCase):
    """Risk levels of the seminar slides (CROW 2009): index level, speed level, overall = the less severe of the two."""

    def test_ttc_levels(self):
        f, lim = CORE["risk_level_low_is_risky"], CORE["RISK_DEFAULT_LIMITS"]["ttc_s"]
        self.assertEqual([f(v, lim) for v in (0.5, 0.99, 1.0, 1.5, 1.51, 2.0, 2.01, 9.0)],
                         ["High", "High", "Moderate", "Moderate", "Low", "Low", "Interaction", "Interaction"])

    def test_pet_levels(self):
        f, lim = CORE["risk_level_low_is_risky"], CORE["RISK_DEFAULT_LIMITS"]["pet_s"]
        self.assertEqual([f(v, lim) for v in (0.9, 1.0, 2.0, 2.1, 3.0, 3.1)], ["High", "Moderate", "Moderate", "Low", "Low", "Interaction"])

    def test_speed_and_ldp_levels(self):
        f = CORE["risk_level_high_is_risky"]
        sp = CORE["RISK_DEFAULT_LIMITS"]["speed_kmh"]
        self.assertEqual([f(v, sp) for v in (60, 50, 49.9, 30, 29.9, 15, 14.9, 0)], ["High", "High", "Moderate", "Moderate", "Low", "Low", "Interaction", "Interaction"])
        ldp = CORE["RISK_DEFAULT_LIMITS"]["ldp_pct"]
        self.assertEqual([f(v, ldp) for v in (95, 80, 79, 50, 49, 30, 29)], ["High", "High", "Moderate", "Moderate", "Low", "Low", "Interaction"])

    def test_values_are_judged_at_the_exported_precision(self):
        self.assertEqual(CORE["risk_level_low_is_risky"](0.99999999999, (1.0, 1.5, 2.0)), "Moderate")     # = 1.000000 s in the file
        self.assertEqual(CORE["risk_level_high_is_risky"](49.9999999999, (50.0, 30.0, 15.0)), "High")

    def test_overall_is_the_less_severe_level(self):
        c = CORE["combine_risk"]
        self.assertEqual(c("High", "Moderate"), "Moderate")        # TTC 0.5 s with 40 km/h (the orange block of the slide)
        self.assertEqual(c("Moderate", "High"), "Moderate")        # TTC 1.2 s with 60 km/h
        self.assertEqual(c("Low", "High"), "Low")                  # TTC 1.8 s with 60 km/h
        self.assertEqual(c("High", "Low"), "Low")
        self.assertEqual(c("High", "Interaction"), "Interaction")  # TTC 0.5 s with 10 km/h (the green floor)
        self.assertEqual(c("High", "High"), "High")
        self.assertEqual(c("High", ""), "")                        # speed unknown
        self.assertEqual(c("High", None), "")

    def test_the_colour_map_of_the_ttc_chart(self):
        # every block of the chart: (TTC, speed) -> colour
        ttc, spd = CORE["RISK_DEFAULT_LIMITS"]["ttc_s"], CORE["RISK_DEFAULT_LIMITS"]["speed_kmh"]
        lv = lambda t, v: CORE["combine_risk"](CORE["risk_level_low_is_risky"](t, ttc), CORE["risk_level_high_is_risky"](v, spd))
        self.assertEqual(lv(0.5, 70), "High")
        self.assertEqual(lv(0.5, 40), "Moderate")
        self.assertEqual(lv(1.2, 80), "Moderate")
        self.assertEqual(lv(0.5, 20), "Low")
        self.assertEqual(lv(1.8, 80), "Low")
        self.assertEqual(lv(2.5, 80), "Interaction")
        self.assertEqual(lv(0.5, 10), "Interaction")

    def test_parse_limits(self):
        p = CORE["parse_risk_limits"]
        self.assertEqual(p("1.0, 1.5, 2.0", True), (1.0, 1.5, 2.0))
        self.assertEqual(p("50 30 15", False), (50.0, 30.0, 15.0))
        for bad, asc in (("1, 2", True), ("2, 1, 3", True), ("1, 2, 3", False), ("a, b, c", True), ("1, 1, 2", True)):
            with self.assertRaises(ValueError):
                p(bad, asc)


class MovingRectTtc(unittest.TestCase):
    """TTC of two vehicle rectangles that keep their velocity: the time until they first touch."""
    CAR = (4.5, 1.8)
    MC = (2.0, 0.8)

    def ttc(self, p_a, v_a, p_b, v_b, size_a=CAR, size_b=CAR, margin=0.0, rel=0.0):
        return CORE["moving_rect_ttc"](p_a, v_a, size_a, p_b, v_b, size_b, margin, rel)

    def test_following_in_one_lane(self):
        # A 15 m/s, B 20 m ahead at 10 m/s: the boxes are 20 - 4.5 = 15.5 m apart, closing at 5 m/s -> 3.1 s (the classic S / CS)
        r = self.ttc((0, 0), (15, 0), (20, 0), (10, 0))
        self.assertEqual(r["status"], "collision")
        self.assertAlmostEqual(r["TTC"], 3.1, places=9)
        self.assertAlmostEqual(r["DTC"], 15.5, places=9)

    def test_the_margin_enlarges_the_boxes(self):
        r = self.ttc((0, 0), (15, 0), (20, 0), (10, 0), margin=0.25)        # 0.25 m on every side of both boxes: 0.5 m less gap
        self.assertAlmostEqual(r["TTC"], 3.0, places=9)

    def test_head_on(self):
        r = self.ttc((0, 0), (10, 0), (30, 0), (-10, 0))                    # 30 - 4.5 = 25.5 m closing at 20 m/s
        self.assertAlmostEqual(r["TTC"], 25.5 / 20.0, places=9)

    def test_a_pair_that_passes_beside_each_other_never_touches(self):
        # the R37 case: A drives by a parked-ish B that is 4 m to the side (half widths 0.9 + 0.9 = 1.8 m)
        self.assertEqual(self.ttc((-30, 0), (11, 0), (0, -4), (0.5, 0))["status"], "none")
        # with a very large margin the boxes would touch
        self.assertEqual(self.ttc((-30, 0), (11, 0), (0, -4), (0.5, 0), margin=2.0)["status"], "collision")

    def test_a_lateral_offset_inside_the_widths_still_collides(self):
        self.assertEqual(self.ttc((0, 0), (15, 0), (20, 1.5), (10, 0))["status"], "collision")      # 1.5 < 1.8
        self.assertEqual(self.ttc((0, 0), (15, 0), (20, 2.0), (10, 0))["status"], "none")           # 2.0 > 1.8
        self.assertEqual(self.ttc((0, 0), (15, 0), (20, 2.0), (10, 0), margin=0.25)["status"], "collision")   # 1.8 + 0.5 > 2.0

    def test_separating_vehicles_have_no_ttc(self):
        self.assertEqual(self.ttc((0, 0), (10, 0), (20, 0), (15, 0))["status"], "none")             # the leader is faster

    def test_already_overlapping(self):
        self.assertEqual(self.ttc((0, 0), (10, 0), (3.0, 0), (5, 0))["status"], "overlap")          # 3 m apart, the boxes (4.5 m) overlap

    def test_crossing_at_right_angle(self):
        # A along +x, B along +y, both 10 m/s, both reach (15, 0) at about the same time: the boxes touch before the centres meet
        r = self.ttc((0, 0), (10, 0), (15, -12), (0, 10))
        self.assertEqual(r["status"], "collision")
        self.assertLess(r["TTC"], 1.2)                                       # the centres meet at 1.5 s (A) / 1.2 s (B)

    def test_small_relative_speed_is_skipped(self):
        self.assertEqual(self.ttc((0, 0), (10, 0), (20, 0), (9.8, 0), rel=0.5)["status"], "slow")
        self.assertEqual(self.ttc((0, 0), (10, 0), (20, 0), (9.8, 0), rel=0.1)["status"], "collision")

    def test_a_vehicle_without_heading_is_skipped(self):
        self.assertEqual(self.ttc((0, 0), (0, 0), (20, 0), (-5, 0))["status"], "slow")

    def test_symmetric_in_the_two_vehicles(self):
        a = self.ttc((0, 0), (10, 3), (25, 2), (-6, 1), size_a=self.CAR, size_b=self.MC)
        b = self.ttc((25, 2), (-6, 1), (0, 0), (10, 3), size_a=self.MC, size_b=self.CAR)
        self.assertEqual(a["status"], b["status"])
        if a["status"] == "collision":
            self.assertAlmostEqual(a["TTC"], b["TTC"], places=9)

    def test_matches_a_brute_force_scan(self):
        """For random pairs the first-contact time equals the first time a plain static overlap test (separating axes) says 'overlap'."""
        import random
        rnd = random.Random(7)

        def corners(p, v, size, margin):
            sp = math.hypot(*v)
            h = (v[0] / sp, v[1] / sp)
            n = (-h[1], h[0])
            hl, hw = size[0] / 2 + margin, size[1] / 2 + margin
            return [(p[0] + sx * hl * h[0] + sy * hw * n[0], p[1] + sx * hl * h[1] + sy * hw * n[1]) for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1))]

        def overlap(ca, cb):
            for poly in (ca, cb):
                for k in range(4):
                    e = (poly[(k + 1) % 4][0] - poly[k][0], poly[(k + 1) % 4][1] - poly[k][1])
                    ax = (-e[1], e[0])
                    pa = [q[0] * ax[0] + q[1] * ax[1] for q in ca]
                    pb = [q[0] * ax[0] + q[1] * ax[1] for q in cb]
                    if max(pa) < min(pb) or max(pb) < min(pa):
                        return False
            return True

        checked = 0
        for _ in range(400):
            size_a, size_b = rnd.choice((self.CAR, self.MC)), rnd.choice((self.CAR, self.MC))
            p_a = (rnd.uniform(-8, 8), rnd.uniform(-8, 8)); p_b = (rnd.uniform(-8, 8), rnd.uniform(-8, 8))
            v_a = (rnd.uniform(-12, 12), rnd.uniform(-12, 12)); v_b = (rnd.uniform(-12, 12), rnd.uniform(-12, 12))
            if math.hypot(*v_a) < 0.5 or math.hypot(*v_b) < 0.5:
                continue
            r = CORE["moving_rect_ttc"](p_a, v_a, size_a, p_b, v_b, size_b, 0.2, 0.0)
            hit = None
            for k in range(0, 4001):
                t = k * 0.0025
                ca = corners((p_a[0] + v_a[0] * t, p_a[1] + v_a[1] * t), v_a, size_a, 0.2)
                cb = corners((p_b[0] + v_b[0] * t, p_b[1] + v_b[1] * t), v_b, size_b, 0.2)
                if overlap(ca, cb):
                    hit = t
                    break
            if r["status"] == "overlap":
                self.assertEqual(hit, 0.0)
            elif r["status"] == "collision":
                if r["TTC"] <= 10.0:
                    self.assertIsNotNone(hit)
                    self.assertAlmostEqual(hit, r["TTC"], delta=0.0026)
            else:
                self.assertIsNone(hit)
            checked += 1
        self.assertGreater(checked, 300)


class RectPolygonAndInvertMap(unittest.TestCase):
    def test_rectangle_corners(self):
        q = CORE["rect_polygon"]((10.0, 5.0), (3.0, 0.0), (4.5, 1.8), 0.25)        # long side along +x, 0.25 m more on every side
        self.assertAlmostEqual(q[:, 0].max() - q[:, 0].min(), 5.0, places=9)
        self.assertAlmostEqual(q[:, 1].max() - q[:, 1].min(), 2.3, places=9)
        self.assertAlmostEqual(q[:, 0].mean(), 10.0, places=9)
        self.assertAlmostEqual(q[:, 1].mean(), 5.0, places=9)
        d = CORE["rect_polygon"]((0.0, 0.0), (1.0, 1.0), (4.0, 2.0), 0.0)          # along the diagonal
        self.assertAlmostEqual(math.hypot(*(d[0] - d[1])), 2.0, places=9)
        self.assertAlmostEqual(math.hypot(*(d[1] - d[2])), 4.0, places=9)

    def test_invert_map_round_trip(self):
        h = CORE["homography_from_points"]([(0, 0), (60, 0), (60, 20), (0, 20)], [(150, 500), (1800, 420), (1900, 900), (60, 950)])
        to_plane = lambda px: CORE["apply_homography"](np.linalg.inv(h), np.asarray(px, float).reshape(-1, 2))
        px = np.array([[500.0, 700.0], [1200.0, 650.0]])
        back = CORE["invert_map"](to_plane, to_plane(px), px + 40)
        self.assertLess(np.abs(back - px).max(), 1e-2)


class ConflictAngle(unittest.TestCase):
    def test_angle_between_velocities(self):
        ang = CORE["conflict_angle_deg"]
        self.assertAlmostEqual(ang((10, 0), (10, 0)), 0.0, places=6)
        self.assertAlmostEqual(ang((10, 0), (0, 10)), 90.0, places=6)
        self.assertAlmostEqual(ang((10, 0), (-10, 0)), 180.0, places=6)
        self.assertAlmostEqual(ang((10, 0), (5, 5)), 45.0, places=6)

    def test_a_vehicle_without_heading_has_no_angle(self):
        ang = CORE["conflict_angle_deg"]
        self.assertIsNone(ang((10, 0), (0, 0)))
        self.assertIsNone(ang((10, 0), (0.1, 0), min_speed=0.5))

    def test_types_follow_the_30_and_85_degree_limits(self):
        t = CORE["ttc_conflict_type"]
        self.assertEqual(t(0.0), "Rear-end")
        self.assertEqual(t(29.9), "Rear-end")
        self.assertEqual(t(30.0), "Lane change")
        self.assertEqual(t(85.0), "Lane change")
        self.assertEqual(t(85.1), "Crossing")
        self.assertEqual(t(180.0), "Crossing")
        self.assertEqual(t(None), "Unclassified")
        self.assertEqual(t(40.0, 45.0, 90.0), "Rear-end")                   # the limits are adjustable


class ConflictType(unittest.TestCase):
    def test_types(self):
        ct = CORE["conflict_type_from_sequences"]
        self.assertEqual(ct((1, 3, 4), (2, 3, 4), True), "Crossing")
        self.assertEqual(ct((1, 3, 4), (2, 3, 4)), "Merging")
        self.assertEqual(ct((1, 3, 4), (1, 3, 6, 7)), "Diverging")
        self.assertEqual(ct((2, 3, 4), (5, 6, 7)), "Merging/Diverging")
        self.assertEqual(ct([], [1, 2]), "Merging/Diverging")


class LineEditorHelpers(unittest.TestCase):
    def test_canvas_to_video(self):
        f = CORE["canvas_to_video"]
        self.assertEqual(f(100, 50, 0.5, 1920, 1080), (200, 100))
        self.assertEqual(f(-10, 99999, 0.5, 1920, 1080), (0, 1079))
        self.assertEqual(f(0, 0, 1.0, 640, 360), (0, 0))

    def test_scale_points(self):
        f = CORE["scale_points"]
        self.assertEqual(f([(100, 50), (200, 150)], 320, 180, 640, 360), [(200, 100), (400, 300)])
        self.assertEqual(f([(100, 50)], 640, 360, 640, 360), [(100, 50)])
        self.assertEqual(f([(100, 50)], None, None, 640, 360), [(100, 50)])      # unknown size: unchanged

    def test_mapping_text_fills_and_keeps_other_rows(self):
        f = CORE["update_reference_mapping_text"]
        old = ("# Site_ID|Movement|Line N\n# 8|2-3-4|Line N\n# 8|5-6-7|Line N\n9|2-3-4|Line 6\n8|2-3-1|Line 5")
        new = f(old, "8", {"2-3-4": "Line 1", "5-6-7": "Line 2"})
        rows = new.splitlines()
        self.assertIn("# Site_ID|Movement|Line N", rows)         # header comment kept
        self.assertNotIn("# 8|2-3-4|Line N", rows)              # template rows replaced
        self.assertIn("9|2-3-4|Line 6", rows)                   # other site kept
        self.assertIn("8|2-3-1|Line 5", rows)                   # other movement kept
        self.assertEqual(rows[-2:], ["8|2-3-4|Line 1", "8|5-6-7|Line 2"])

    def test_mapping_text_replaces_an_existing_active_row(self):
        f = CORE["update_reference_mapping_text"]
        new = f("8|2-3-4|Line 3", "8", {"2-3-4": "Line 1"})
        self.assertEqual(new, "8|2-3-4|Line 1")

    def test_mapping_text_from_empty(self):
        f = CORE["update_reference_mapping_text"]
        self.assertEqual(f("", "8", {"5-6-7": "Line 2"}), "8|5-6-7|Line 2")


class DuplicateTracks(unittest.TestCase):
    def boxes(self, spec):
        """spec = {track_id: {frame: (x1, y1, x2, y2)}} -> frame_boxes"""
        fb = {}
        for tid, frames in spec.items():
            for fr, box in frames.items():
                fb.setdefault(fr, []).append((tid, box))
        return fb

    def test_iou(self):
        f = CORE["bbox_iou"]
        self.assertAlmostEqual(f((0, 0, 10, 10), (0, 0, 10, 10)), 1.0)
        self.assertAlmostEqual(f((0, 0, 10, 10), (5, 0, 15, 10)), 1.0 / 3.0)
        self.assertEqual(f((0, 0, 10, 10), (20, 20, 30, 30)), 0.0)

    def test_same_car_under_two_ids_is_found(self):
        a = {fr: (100 + fr, 50, 130 + fr, 70) for fr in range(1, 101)}        # long track
        b = {fr: (101 + fr, 51, 131 + fr, 71) for fr in range(40, 70)}        # 30 frames, same car
        dup = CORE["find_duplicate_tracks"](self.boxes({"6": a, "22": b}), {"6": 100, "22": 30})
        self.assertEqual(set(dup), {"22"})
        self.assertEqual(dup["22"]["keep"], "6")
        self.assertEqual(dup["22"]["frames"], set(range(40, 70)))

    def test_two_cars_side_by_side_are_not_duplicates(self):
        a = {fr: (100 + fr, 50, 130 + fr, 70) for fr in range(1, 60)}
        b = {fr: (100 + fr, 75, 130 + fr, 95) for fr in range(1, 60)}
        self.assertEqual(CORE["find_duplicate_tracks"](self.boxes({"1": a, "2": b}), {"1": 59, "2": 59}), {})

    def test_short_overlap_is_not_enough(self):
        # a 40-frame track that lies on top of the other vehicle for only 5 of its frames is another vehicle that crossed
        a = {fr: (100, 50, 130, 70) for fr in range(1, 50)}
        b = {fr: (100, 50, 130, 70) for fr in range(1, 6)}
        b.update({fr: (400, 50, 430, 70) for fr in range(6, 41)})
        self.assertEqual(CORE["find_duplicate_tracks"](self.boxes({"1": a, "2": b}), {"1": 49, "2": 40}), {})

    def test_partial_overlap_removes_only_the_overlapping_frames(self):
        a = {fr: (100, 50, 130, 70) for fr in range(1, 101)}
        b = {fr: (100, 50, 130, 70) for fr in range(1, 21)}
        b.update({fr: (300, 200, 330, 220) for fr in range(21, 61)})           # later it is a different car
        dup = CORE["find_duplicate_tracks"](self.boxes({"1": a, "2": b}), {"1": 100, "2": 60})
        self.assertEqual(dup["2"]["frames"], set(range(1, 21)))

    def test_equal_length_keeps_the_earlier_id(self):
        a = {fr: (100, 50, 130, 70) for fr in range(1, 31)}
        dup = CORE["find_duplicate_tracks"](self.boxes({"3": a, "9": dict(a)}), {"3": 30, "9": 30})
        self.assertEqual(list(dup), ["9"])


class RobustMovement(unittest.TestCase):
    f = staticmethod(lambda seq: CORE["classify_movement_robust"](seq))

    def test_wobble_across_a_boundary_is_recovered(self):
        self.assertEqual(self.f([2, 3, 2, 3, 4]), ("2-3-4", "Exact_AfterDedupe"))
        self.assertEqual(self.f([1, 3, 6, 3, 6, 7]), ("1-3-6-7", "Exact_AfterDedupe"))
        self.assertEqual(self.f([5, 6, 5, 6, 7]), ("5-6-7", "Exact_AfterDedupe"))

    def test_plain_answers_are_never_changed(self):
        self.assertEqual(self.f([2, 3, 4]), ("2-3-4", "Exact"))
        self.assertEqual(self.f([1, 3, 6]), ("1-3-6-7", "Partial"))
        self.assertEqual(self.f([3, 4]), ("", "Ambiguous"))
        self.assertEqual(self.f([3]), ("", "Insufficient"))

    def test_partial_after_dedupe(self):
        self.assertEqual(self.f([1, 3, 1, 3, 6]), ("1-3-6-7", "Partial_AfterDedupe"))

    def test_real_world_oscillation_that_still_fits_nothing(self):
        # from the old run: 4-3-4-3-4-3-6-1 -> first visits 4,3,6,1 is not a defined movement
        self.assertEqual(self.f([4, 3, 4, 3, 4, 3, 6, 1]), ("", "Unclassified"))

    def test_first_visit_order(self):
        self.assertEqual(CORE["first_visit_order"]([4, 7, 6, 7, 6, 7, 1]), [4, 7, 6, 1])


class GapHoldAndIntervals(unittest.TestCase):
    def samples(self, plan, dt=1 / 60):
        """plan = [(n_samples, speed_ms, inside_bool), ...] -> [(t, x, y, inside)]"""
        out, x, i = [], 0.0, 0
        for n, v, inside in plan:
            for _ in range(n):
                out.append((i * dt, x, 0.0, inside))
                x += v * dt
                i += 1
        return out

    def test_moving_through_is_not_a_stop(self):
        r = CORE["find_hold"](self.samples([(60, 4.0, True)]))
        self.assertEqual(r["state"], "Continued")

    def test_stop_then_resume(self):
        r = CORE["find_hold"](self.samples([(10, 4.0, True), (60, 0.0, True), (30, 4.0, True)]))
        self.assertEqual(r["state"], "Stopped_then_Resumed")
        self.assertAlmostEqual(r["stop_start"], 10 / 60, places=6)
        self.assertAlmostEqual(r["resume_time"], 71 / 60, places=6)        # first sample whose step is fast

    def test_stop_then_leaves_the_conflict_zones(self):
        r = CORE["find_hold"](self.samples([(10, 4.0, True), (40, 0.0, True), (5, 4.0, False)]))
        self.assertEqual(r["state"], "Stopped_then_Resumed")
        self.assertAlmostEqual(r["resume_time"], 50 / 60, places=6)

    def test_stopped_until_the_end_is_censored(self):
        r = CORE["find_hold"](self.samples([(10, 4.0, True), (60, 0.0, True)]))
        self.assertEqual(r["state"], "Stopped_Censored")
        self.assertIsNone(r["resume_time"])

    def test_short_pause_is_not_a_stop(self):
        # 0.2 s at rest < 0.30 s minimum
        r = CORE["find_hold"](self.samples([(10, 4.0, True), (12, 0.0, True), (30, 4.0, True)]))
        self.assertEqual(r["state"], "Continued")

    def test_thresholds_are_adjustable(self):
        plan = [(10, 4.0, True), (60, 0.5, True), (30, 4.0, True)]         # crawling at 1.8 km/h
        self.assertEqual(CORE["find_hold"](self.samples(plan), 5.0, 0.3)["state"], "Stopped_then_Resumed")
        self.assertEqual(CORE["find_hold"](self.samples(plan), 1.0, 0.3)["state"], "Continued")
        self.assertEqual(CORE["find_hold"](self.samples([(10, 4.0, True), (12, 0.0, True), (30, 4.0, True)]), 5.0, 0.1)["state"],
                         "Stopped_then_Resumed")

    def test_leaving_without_a_stop(self):
        r = CORE["find_hold"](self.samples([(10, 4.0, True), (5, 4.0, False)]))
        self.assertEqual(r["state"], "Continued")

    def test_gap_intervals(self):
        ev = [(5.0, "3", "Car", "Line 1", ""), (1.0, "1", "Car", "Line 1", ""), (2.0, "2", "Bus", "Line 1", "")]
        g = CORE["build_gap_intervals"](ev)
        self.assertEqual([(x["gap_start"], x["gap_end"], x["id_a"], x["id_b"]) for x in g], [(1.0, 2.0, "1", "2"), (2.0, 5.0, "2", "3")])

    def test_gap_intervals_one_event_per_vehicle_and_no_empty_gap(self):
        ev = [(1.0, "1", "Car", "L", ""), (1.5, "1", "Car", "L", ""), (1.0, "2", "Car", "L", ""), (4.0, "3", "Car", "L", "")]
        g = CORE["build_gap_intervals"](ev)
        self.assertEqual([(x["gap_start"], x["gap_end"]) for x in g], [(1.0, 4.0)])      # 1 and 2 at the same time: no zero gap
        self.assertEqual(CORE["build_gap_intervals"]([(1.0, "1", "Car", "L", "")]), [])

    def test_gap_paths_follow_the_movement_patterns(self):
        for mv, info in CORE["GAP_PATHS"].items():
            seq = CORE["MOVEMENT_PATTERNS"][mv]["sequence"]
            self.assertEqual(info["wait"], (seq[0],))
            self.assertEqual(info["target"], seq[-1])
            self.assertEqual(set(info["middle"]), set(seq[1:-1]))
        self.assertEqual(set(CORE["GAP_REFERENCE_ZONE"]), {"2-3-4", "5-6-7", "5-6-3-1", "1-3-6-7"})


class ExcelSafe(unittest.TestCase):
    f = staticmethod(lambda v: CORE["excel_safe_value"](v))

    def test_movements_and_sequences_get_arrows(self):
        self.assertEqual(self.f("2-3-4"), "2\u21923\u21924")
        self.assertEqual(self.f("1-3-6-7"), "1\u21923\u21926\u21927")
        self.assertEqual(self.f("5-6"), "5\u21926")

    def test_other_values_are_untouched(self):
        for v in ("Zone 3", "Movement 2-3-4", "-1.5", "0.016666", "", "8", "Line 1", "2024-01-05", 7, None, 3.5):
            self.assertEqual(self.f(v), v)


class SpeedOutlier(unittest.TestCase):
    f = staticmethod(lambda v, m: CORE["is_speed_outlier"](v, m))

    def test_flagging(self):
        self.assertTrue(self.f(99.2, 80))
        self.assertFalse(self.f(80, 80))
        self.assertFalse(self.f(22, 80))

    def test_zero_or_none_turns_check_off(self):
        self.assertFalse(self.f(300, 0))
        self.assertFalse(self.f(300, None))


class TimeWindow(unittest.TestCase):
    P = staticmethod(lambda s: CORE["parse_clock_time"](s))
    W = staticmethod(lambda a, b, fps, n: CORE["window_frames"](a, b, fps, n))
    F = staticmethod(lambda s: CORE["format_clock_time"](s))

    def test_parse_accepts_seconds_and_clock_forms(self):
        self.assertIsNone(self.P(""))
        self.assertIsNone(self.P("  "))
        self.assertEqual(self.P("75"), 75.0)
        self.assertEqual(self.P("75.5"), 75.5)
        self.assertEqual(self.P("1:15"), 75.0)
        self.assertEqual(self.P("01:15.5"), 75.5)
        self.assertEqual(self.P("1:02:03"), 3723.0)

    def test_parse_rejects_bad_input(self):
        for bad in ("abc", "-5", "1:75", "1:2:3:4", "nan", "inf", "1::2"):
            with self.assertRaises(ValueError, msg=bad):
                self.P(bad)

    def test_format_round_trips(self):
        for s in (0.0, 5.5, 75.0, 75.5, 3723.0):
            self.assertAlmostEqual(self.P(self.F(s)), s, places=1)
        self.assertEqual(self.F(75.5), "1:15.5")
        self.assertEqual(self.F(3723.0), "1:02:03.0")

    def test_window_frames_use_time_zero_for_frame_1(self):
        # 60 fps: frame N is at (N-1)/60 s. From 1.0 s = frame 61; to 2.0 s = frame 121 (inclusive)
        self.assertEqual(self.W(1.0, 2.0, 60.0, 3600), (61, 121))
        self.assertEqual(self.W(None, None, 60.0, 3600), (1, 3600))
        self.assertEqual(self.W(0.0, 0.0, 30.0, 100), (1, 1))

    def test_window_between_frames_rounds_inwards(self):
        # 30 fps frame times 0, 0.0333, 0.0667...; start 0.04 -> next frame (3), end 0.05 -> last frame at or before (2)
        self.assertEqual(self.W(0.04, 0.2, 30.0, 100), (3, 7))

    def test_window_end_clipped_to_video(self):
        self.assertEqual(self.W(1.0, 999.0, 60.0, 600), (61, 600))

    def test_window_errors(self):
        with self.assertRaises(ValueError):
            self.W(5.0, 3.0, 30.0, 1000)           # end before start
        with self.assertRaises(ValueError):
            self.W(100.0, None, 30.0, 300)         # starts after the video ends

    def test_unknown_length(self):
        self.assertEqual(self.W(1.0, None, 30.0, 0), (31, None))
        self.assertEqual(self.W(None, 2.0, 30.0, 0), (1, 61))


class ZoneCalibration(unittest.TestCase):
    H = staticmethod(lambda s, d: CORE["homography_from_points"](s, d))
    A = staticmethod(lambda h, p: CORE["apply_homography"](h, p))
    Z = staticmethod(lambda s, l, b: CORE["zone_metric_transform"](s, l, b))
    P = staticmethod(lambda t, p: CORE["zone_metric_points"](t, p))

    def test_homography_maps_the_four_points_exactly(self):
        src = [(10, 10), (410, 30), (380, 250), (0, 220)]
        dst = [(0, 0), (8, 0), (8, 4), (0, 4)]
        out = self.A(self.H(src, dst), src)
        for o, d in zip(out, dst):
            self.assertAlmostEqual(o[0], d[0], places=6)
            self.assertAlmostEqual(o[1], d[1], places=6)

    def test_zone_transform_gives_true_scale_and_keeps_the_common_frame(self):
        import math as _m
        quad = [(0, 0), (200, 0), (200, 100), (0, 100)]          # 200 x 100 px = 4 m x 2 m  ->  50 px/m
        ang = _m.radians(30)
        rot = lambda x, y: (x * _m.cos(ang) - y * _m.sin(ang) + 7.0, x * _m.sin(ang) + y * _m.cos(ang) - 3.0)
        base = [rot(0, 0), rot(4, 0), rot(4, 2), rot(0, 2)]       # where the base calibration puts the same corners
        t = self.Z(quad, [4, 2, 4, 2], base)
        self.assertLess(t["rms"], 1e-9)
        m = self.P(t, [(0, 0), (100, 50), (200, 100)])
        for got, want in zip(m, (rot(0, 0), rot(2, 1), rot(4, 2))):
            self.assertAlmostEqual(got[0], want[0], places=6)
            self.assertAlmostEqual(got[1], want[1], places=6)
        # 100 px along the long side = 2 m, in the common frame
        d = float(((m[1] - m[0]) ** 2).sum() ** 0.5)
        self.assertAlmostEqual(d, ((2 * 1) ** 2 + (1 * 1) ** 2) ** 0.5, places=6)

    def test_zone_scale_replaces_a_wrong_base_scale(self):
        quad = [(0, 0), (200, 0), (200, 100), (0, 100)]
        wrong_base = [(0, 0), (2, 0), (2, 1), (0, 1)]             # base thinks the quad is only 2 m x 1 m (100 px/m)
        t = self.Z(quad, [4, 2, 4, 2], wrong_base)               # but its sides were measured: 4 m x 2 m
        self.assertGreater(t["rms"], 0.3)                         # the disagreement is reported
        m = self.P(t, [(0, 50), (200, 50)])
        self.assertAlmostEqual(float(((m[1] - m[0]) ** 2).sum() ** 0.5), 4.0, places=6)    # speed uses the measured scale


class ShortDuplicateTracks(unittest.TestCase):
    F = staticmethod(lambda fb, ln: CORE["find_duplicate_tracks"](fb, ln))
    BOX = (100, 100, 200, 300)

    def test_a_short_blip_on_the_same_vehicle_is_a_duplicate(self):
        # real vehicle 1 for 60 frames; a 3-frame "Van" box (ID 9) sits on top of it in all 3 of its frames
        fb = {f: [(1, self.BOX)] for f in range(60)}
        for f in (20, 21, 22):
            fb[f].append((9, (101, 101, 201, 301)))
        out = self.F(fb, {1: 60, 9: 3})
        self.assertEqual(set(out), {9})
        self.assertEqual(out[9]["keep"], 1)
        self.assertEqual(out[9]["frames"], {20, 21, 22})

    def test_a_one_frame_blip_is_a_duplicate_too(self):
        fb = {f: [(1, self.BOX)] for f in range(30)}
        fb[5].append((7, self.BOX))
        self.assertEqual(set(self.F(fb, {1: 30, 7: 1})), {7})

    def test_a_short_track_that_only_partly_overlaps_is_kept(self):
        # 5 frames long, only 2 of them on top of vehicle 1 (40 %): another vehicle that happens to cross -> not a duplicate
        fb = {f: [(1, self.BOX)] for f in range(40)}
        for f in (10, 11):
            fb[f].append((8, self.BOX))
        for f in (12, 13, 14):
            fb[f].append((8, (300, 100, 400, 300)))
        self.assertEqual(self.F(fb, {1: 40, 8: 5}), {})

    def test_a_short_track_beside_another_vehicle_is_kept(self):
        fb = {f: [(1, self.BOX), (6, (210, 100, 310, 300))] for f in range(4)}      # side by side, no overlap
        self.assertEqual(self.F(fb, {1: 4, 6: 4}), {})

    def test_the_original_rule_for_long_tracks_is_unchanged(self):
        fb = {f: [(1, self.BOX), (2, self.BOX)] for f in range(12)}
        out = self.F(fb, {1: 50, 2: 12})
        self.assertEqual(set(out), {2})
        fb = {f: [(1, self.BOX), (2, self.BOX)] for f in range(9)}                   # 9 shared frames of a long track: kept
        self.assertEqual(self.F(fb, {1: 50, 2: 40}), {})


class TopviewTests(unittest.TestCase):
    def test_canvas_covers_the_points_and_is_even(self):
        cv = CORE["topview_canvas"]([(0, 0), (40, 0), (40, 20), (0, 20)] * 30, max_px=1000, margin_m=2.0)
        self.assertEqual(cv["w"] % 2, 0)
        self.assertEqual(cv["h"] % 2, 0)
        px = CORE["topview_px"](cv, [(0, 0), (40, 20)])
        self.assertTrue((px >= 0).all())
        self.assertLessEqual(px[:, 0].max(), cv["w"])
        self.assertLessEqual(px[:, 1].max(), cv["h"])
        self.assertAlmostEqual(cv["scale"] * (40 + 4), 1000, delta=2)       # the long side fills max_px

    def test_canvas_takes_the_shape_of_the_video(self):
        pts = [(0, 0), (20, 0), (20, 40), (0, 40)] * 30                    # a tall area
        cv = CORE["topview_canvas"](pts, max_px=1280, margin_m=2.0, aspect=16 / 9)
        self.assertAlmostEqual(cv["w"] / cv["h"], 16 / 9, delta=0.02)      # but a landscape picture, like the video
        px = CORE["topview_px"](cv, [(0, 0), (20, 40)])
        self.assertTrue((px >= 0).all() and px[:, 0].max() <= cv["w"] and px[:, 1].max() <= cv["h"])

    def test_canvas_ignores_a_far_outlier(self):
        pts = [(x * 0.1, 0.0) for x in range(400)] + [(5000.0, 0.0)]
        cv = CORE["topview_canvas"](pts, max_px=1000)
        self.assertGreater(cv["scale"], 10)                                 # not squeezed to fit the outlier

    def test_rect_follows_the_heading(self):
        r = CORE["oriented_rect"]((10, 5), (1.0, 0.0), 4.0, 2.0)
        self.assertAlmostEqual(r[:, 0].max() - r[:, 0].min(), 4.0)
        self.assertAlmostEqual(r[:, 1].max() - r[:, 1].min(), 2.0)
        u = (math.sqrt(0.5), math.sqrt(0.5))
        d = CORE["oriented_rect"]((0, 0), u, 4.0, 2.0)
        side = np_dist = ((d[0] - d[1]) ** 2).sum() ** 0.5
        self.assertAlmostEqual(side, 2.0)                                   # first edge = the width
        self.assertAlmostEqual(((d[1] - d[2]) ** 2).sum() ** 0.5, 4.0)      # second edge = the length
        self.assertTrue(CORE["oriented_rect"]((0, 0), None, 3.0, 1.0).shape == (4, 2))


class OutsideZonePlanTests(unittest.TestCase):
    P = staticmethod(lambda mode, inside, avail=True: CORE["outside_zone_plan"](mode, inside, avail))

    def test_inside_a_zone_is_always_drawn_in_full(self):
        for mode in ("dot", "hide", "show", "anything"):
            self.assertEqual(self.P(mode, True), {"point": True, "object": True})

    def test_no_zone_drawn_means_everything_is_drawn(self):
        for mode in ("dot", "hide", "show"):
            self.assertEqual(self.P(mode, False, False), {"point": True, "object": True})

    def test_outside_every_zone(self):
        self.assertEqual(self.P("dot", False), {"point": True, "object": False})           # the old behaviour: only the point
        self.assertEqual(self.P("hide", False), {"point": False, "object": False})
        self.assertEqual(self.P("show", False), {"point": True, "object": True})
        self.assertEqual(self.P("unknown", False), {"point": True, "object": False})        # an unreadable setting = the old behaviour


class AlignTests(unittest.TestCase):
    """Align: pairs of points (video pixels -> drone pixels), kinds as in a GIS georeferencer."""
    SIZE = (1920, 1080)

    @staticmethod
    def grid(n_x=4, n_y=3):
        xs, ys = np.linspace(200, 1700, n_x), np.linspace(250, 900, n_y)
        return np.array([(a, b) for a in xs for b in ys], dtype=float)

    def project(self, pts):
        h = CORE["homography_from_points"]([(0, 0), (1920, 0), (1920, 1080), (0, 1080)], [(300, 200), (1500, 260), (1700, 900), (150, 800)])
        return CORE["apply_homography"](h, pts)

    def distort(self, pts, k1):
        """Straightened -> as a lens with the radial trend k1 records them (Newton on the radius)."""
        c = np.array([960.0, 540.0])
        x = (np.asarray(pts, float) - c) / 960.0
        ru = np.sqrt((x ** 2).sum(1))
        rd = ru.copy()
        for _ in range(60):
            rd = np.maximum(rd - (rd * (1 + k1 * rd ** 2) - ru) / (1 + 3 * k1 * rd ** 2), 0)
        sc = np.where(ru > 1e-12, rd / np.where(ru > 1e-12, ru, 1.0), 1.0)
        return x * sc[:, None] * 960.0 + c

    def test_helmert_affine_projective_are_exact_on_their_own_kind(self):
        src = self.grid()
        th = 0.3
        sim = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]]) * 0.8
        for kind, dst in (("helmert", src @ sim.T + [40, -25]),
                          ("affine", src @ np.array([[0.9, 0.2], [-0.1, 1.1]]).T + [5, 9]),
                          ("projective", self.project(src))):
            rep = CORE["transform_report"](kind, src, dst, self.SIZE)
            self.assertNotIn("error", rep, kind)
            self.assertLess(rep["rms"], 1e-3, kind)
            self.assertLess(rep["loo_rms"], 1e-2, kind)

    def test_a_projective_cannot_follow_a_bent_picture_but_poly_tps_and_lens_can(self):
        src = self.grid(5, 4)
        dst = self.project(self.distort(src, 0.25))                       # camera tilt AND a barrel lens
        rms = {k: CORE["transform_report"](k, src, dst, self.SIZE) for k in ("projective", "lens", "poly3", "tps")}
        self.assertGreater(rms["projective"]["rms"], 2.0)
        self.assertLess(rms["lens"]["rms"], 0.5 * rms["projective"]["rms"])
        self.assertLess(rms["tps"]["rms"], 0.5)                           # exact at the pairs (rubber sheet)
        self.assertGreater(rms["tps"]["loo_rms"], rms["tps"]["rms"])      # but the honest accuracy (leave one out) is worse
        self.assertLess(rms["lens"]["loo_rms"], rms["projective"]["loo_rms"])

    def test_too_few_pairs_say_so(self):
        src = self.grid(2, 2)
        self.assertIn("error", CORE["fit_transform"]("poly2", src, src, self.SIZE))
        self.assertIn("error", CORE["fit_transform"]("projective", src[:3], src[:3], self.SIZE))
        rep = CORE["transform_report"]("projective", src, self.project(src), self.SIZE)
        self.assertIsNone(rep["loo_rms"])                                  # 4 pairs for 4 needed: no leave-one-out

    def test_align_to_metres_scale_rotation_origin(self):
        src = self.grid()
        dst = src * 0.5 + [100, 50]                                       # a scaled copy
        data = {"pairs": [{"s": list(s_), "d": list(d_)} for s_, d_ in zip(src, dst)], "kind": "affine", "scale": 0.1, "rot_deg": 0.0,
                "origin": list(dst[0]), "video_size": list(self.SIZE)}
        cfg = CORE["align_build"](data)
        self.assertNotIn("error", cfg)
        m = CORE["align_apply"](cfg, src)
        self.assertAlmostEqual(m[0, 0], 0.0, delta=1e-6)                                   # the origin is the first pair
        self.assertAlmostEqual(float(np.hypot(*(m[1] - m[0]))), float(np.hypot(*((src[1] - src[0]) * 0.5))) * 0.1, delta=1e-6)
        data["rot_deg"] = 90.0                                                              # the road runs down the drone picture: turn it horizontal
        m90 = CORE["align_apply"](CORE["align_build"](data), src)
        self.assertAlmostEqual(float(np.hypot(*(m90[1] - m90[0]))), float(np.hypot(*(m[1] - m[0]))), delta=1e-6)
        self.assertAlmostEqual(m90[1, 0], m[1, 1], delta=1e-6)
        self.assertIn("error", CORE["align_build"](dict(data, scale=0)))


class ZoneEditCoreTests(unittest.TestCase):
    SIZE = (1920, 1080)

    def cfg(self, kind="lens"):
        rng = np.random.default_rng(2)
        gx, gy = np.linspace(2, 50, 5), np.linspace(2, 16, 4)
        ground = np.array([(a, b) for a in gx for b in gy])
        h = CORE["homography_from_points"]([(0, 0), (60, 0), (60, 20), (0, 20)], [(150, 500), (1800, 420), (1900, 900), (60, 950)])
        video = CORE["apply_homography"](h, ground)
        data = {"pairs": [{"s": list(v), "d": list(g * 20.0 + [100, 60])} for v, g in zip(video, ground)], "kind": kind, "scale": 0.05, "rot_deg": 0.0,
                "video_size": list(self.SIZE), "origin": [100.0, 60.0]}
        return CORE["align_build"](data), h

    def test_a_transformation_can_be_inverted(self):
        cfg, h = self.cfg("lens")
        video = CORE["apply_homography"](h, np.array([[12.0, 5.0], [33.0, 9.0], [47.0, 15.0]]))
        plane = CORE["align_apply"](cfg, video)
        back = CORE["align_plane_to_video"](cfg, plane, video + [25.0, -18.0])               # start the iteration away from the answer
        self.assertLess(np.abs(back - video).max(), 0.02)
        cfg90, _ = self.cfg("projective")
        cfg90["rot_deg"] = 90.0
        pl = CORE["align_apply"](cfg90, video)
        self.assertLess(np.abs(CORE["align_plane_to_video"](cfg90, pl, video) - video).max(), 0.02)

    def test_cross_road_edges_become_vertical_and_shared_corners_stay_shared(self):
        # two neighbouring zones, their cross edges lean; the corner chamfer (45 degrees) is left alone
        z2 = np.array([[0.0, 0.0], [5.0, 0.0], [5.6, 4.0], [0.4, 4.0]])
        z3 = np.array([[5.0, 0.0], [10.0, 0.0], [10.5, 4.0], [5.6, 4.0]])               # shares the edge (5,0)-(5.6,4) with zone 2
        chamfer = np.array([[10.0, 0.0], [12.0, 2.0], [10.5, 4.0]])
        out, rep = CORE["perpendicularize_zones"]({"Zone 2": z2, "Zone 3": z3, "Zone 4": chamfer})
        a = out["Zone 2"]
        self.assertAlmostEqual(a[1][0], a[2][0], places=9)                                    # the shared cross edge is vertical
        self.assertAlmostEqual(a[0][0], a[3][0], places=9)
        b = out["Zone 3"]
        self.assertTrue(np.allclose(a[1], b[0]) and np.allclose(a[2], b[3]))                  # still the same corners
        self.assertAlmostEqual(b[1][0], b[2][0], places=9)
        self.assertTrue(np.allclose(out["Zone 4"][1], [12.0, 2.0]))                           # the 45-degree chamfer end is not forced
        self.assertGreater(rep["moved_max_m"], 0.0)
        out2, _ = CORE["perpendicularize_zones"](out)
        self.assertTrue(all(np.allclose(out[k], out2[k]) for k in out))                       # doing it twice changes nothing

    def test_along_road_edges_can_be_levelled_too(self):
        z = np.array([[0.0, 0.0], [10.0, 0.3], [10.0, 4.0], [0.0, 4.2]])
        out, _ = CORE["perpendicularize_zones"]({"Zone 1": z}, horizontal_too=True)
        a = out["Zone 1"]
        self.assertAlmostEqual(a[0][1], a[1][1], places=9)
        self.assertAlmostEqual(a[2][1], a[3][1], places=9)


if __name__ == "__main__":
    unittest.main()
