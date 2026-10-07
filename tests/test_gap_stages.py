"""Unit tests of the staged Gap Acceptance (SPEC 6.1) and of Headway (SPEC 9.1) on synthetic scenes with known answers.

`_run3_gap` is a method of the GUI class, so it is pulled out of PKStudio.py with `ast` and run on a
tiny stand-in object (no tkinter / cv2 needed)."""
import ast
import math
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(os.path.dirname(HERE), "PKStudio.py"), encoding="utf-8").read()
TREE = ast.parse(SRC)
import re
NS = {"math": math, "re": re}
exec(SRC[SRC.index("# ==== CORE-BEGIN"):SRC.index("# ==== CORE-END")], NS)
for node in TREE.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in (
            "GAP_STAGE_CONFLICTS", "RUN3_GAP_CONFLICT_MAP", "ZONE_EDGE_DEFAULT"):
        exec(compile(ast.Module([node], []), "x", "exec"), NS)
for node in ast.walk(TREE):
    if isinstance(node, ast.FunctionDef) and node.name in ("_run3_gap", "_run3_stream_events", "_run3_headway", "_run3_canonical_class", "_run3_reference_line", "_run3_named_line"):
        exec(compile(ast.Module([node], []), node.name, "exec"), NS)
for node in TREE.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "GAP_REFERENCE_ZONE":
        exec(compile(ast.Module([node], []), "x", "exec"), NS)


class Fake:
    lines = {}
    _run3_stream_events = NS["_run3_stream_events"]
    _run3_reference_line = NS["_run3_reference_line"]
    _run3_named_line = NS["_run3_named_line"]
    zones = {}
    _run3_canonical_class = staticmethod(NS["_run3_canonical_class"])
    _fmt = staticmethod(lambda v, d=3: "" if v is None else f"{v:.{d}f}")
    _run3_speed_at = staticmethod(lambda rows, t: 0.0)
    _run3_line_crossing_time = staticmethod(lambda *a: None)


def track(zones, stop=None, end=12.0, dt=0.05):
    """zones = [(from_time, zone)]; moves 0.5 m per sample except while stopped (stop = (t0, t1))."""
    rows, t, x = [], 0.0, 0.0
    while t <= end:
        z = None
        for tf, zz in zones:
            if t >= tf:
                z = zz
        if not (stop and stop[0] <= t < stop[1]):
            x += 0.5
        rows.append({"_timestamp": t, "_zone_num": z, "_m": (x, 0.0), "class_name": "Car"})
        t += dt
    return rows


def scene(extra):
    tracks, mv = {}, {}
    for i, t in enumerate((2, 3, 6, 8), 1):          # stream 2-3-4 (reference = first time in zone 2)
        tracks[str(i)], mv[str(i)] = track([(t, 2)]), "2-3-4"
    for i, t in enumerate((5, 9), 11):               # stream 5-6-7 (reference = first time in zone 5)
        tracks[str(i)], mv[str(i)] = track([(t, 5)]), "5-6-7"
    for tid, (movement, rows) in extra.items():
        tracks[tid], mv[tid] = rows, movement
    return tracks, mv


def headway(tracks, mv, lengths=None, speed=36.0):
    class F(Fake):
        _run3_speed_at = staticmethod(lambda rows, t: speed)
    c = {"site_id": 8, "lengths": lengths or {"Car": 4.5}, "ttc_min_speed_kmh": 5.0}
    return NS["_run3_headway"](F(), tracks, c, {}, mv)


def run(tracks, mv, selected):
    c = {"gap_movements": selected, "site_id": 8, "waiting_threshold": 5.0, "hold_min_duration_s": 0.3}
    return NS["_run3_gap"](Fake(), tracks, c, {}, mv)


class StagedGap(unittest.TestCase):
    def test_one_middle_zone(self):
        tracks, mv = scene({"20": ("1-3-4", track([(0, 1), (4.0, 3), (7, 4)]))})
        rows = run(tracks, mv, ["1-3-4"])
        self.assertEqual([r["Gap_Role"] for r in rows], ["Rejected", "Accepted"])
        self.assertTrue(all(r["Decision_Stage"] == "Enter_Zone_3" and r["Stage_No"] == 1 for r in rows))
        self.assertAlmostEqual(float(rows[0]["Available_Gap_s"]), 1.05, places=2)   # gap 2->3 closed at the first wait sample
        self.assertAlmostEqual(float(rows[1]["Available_Gap_s"]), 2.0, places=2)    # gap 3->6 open at entry (4.0 s)

    def test_two_middle_zones_no_stop_gives_two_accepted_stages(self):
        tracks, mv = scene({"21": ("1-3-6-7", track([(0, 1), (4.0, 3), (6.5, 6), (9, 7)]))})
        rows = run(tracks, mv, ["1-3-6-7"])
        st2 = [r for r in rows if r["Stage_No"] == 2]
        self.assertEqual(len(st2), 1)
        self.assertEqual(st2[0]["Decision_Stage"], "Enter_Zone_6")
        self.assertEqual(st2[0]["Conflicting_Movement"], "5-6-7")                   # zone 6 meets 5-6-7 (not 2-3-4)
        self.assertEqual(st2[0]["Gap_Role"], "Accepted")
        self.assertAlmostEqual(float(st2[0]["Available_Gap_s"]), 2.5, places=2)     # gap 5->9 s, entry 6.5 s
        self.assertAlmostEqual(float(st2[0]["Waiting_Time_s"]), 2.5, places=2)      # stage 2 starts when zone 3 is entered
        self.assertTrue(all(r["Was_Stopped"] == 0 and r["Stopped_In_Conflict_Zone"] == 0 for r in rows))

    def test_stop_inside_first_middle_zone_is_waiting_of_stage_2(self):
        tracks, mv = scene({"22": ("1-3-6-7", track([(0, 1), (4.0, 3), (6.5, 6), (9, 7)], stop=(4.5, 6.0)))})
        rows = run(tracks, mv, ["1-3-6-7"])
        self.assertTrue(all(r["Was_Stopped"] == 0 for r in rows if r["Stage_No"] == 1))
        self.assertTrue(all(r["Was_Stopped"] == 1 for r in rows if r["Stage_No"] == 2))
        self.assertTrue(all(r["Stopped_In_Conflict_Zone"] == 0 for r in rows))

    def test_stop_in_last_zone_is_only_a_flag(self):
        tracks, mv = scene({"23": ("1-3-6-7", track([(0, 1), (4.0, 3), (6.5, 6), (9, 7)], stop=(7.0, 8.0)))})
        rows = run(tracks, mv, ["1-3-6-7"])
        last = [r for r in rows if r["Stage_No"] == 2]
        self.assertTrue(last and all(r["Stopped_In_Conflict_Zone"] == 1 for r in last))
        self.assertEqual([r["Gap_Role"] for r in last], ["Accepted"])               # the decision is not reversed

    def test_headway_of_a_stream(self):
        tracks, mv = scene({})                              # stream 2-3-4 enters zone 2 at 2, 3, 6, 8 s; 5-6-7 enters zone 5 at 5, 9 s
        rows = headway(tracks, mv)                          # every lead drives 36 km/h = 10 m/s, Car length 4.5 m
        by = {(r["Movement"], r["Lead_Vehicle_ID"]): r for r in rows}
        self.assertEqual([r["Time_Headway_s"] for r in rows if r["Movement"] == "2-3-4"], ["1.050", "3.000", "2.000"])       # vehicle 1 is first seen in zone 2 at its first sample after 2.0 s (2.05 s)
        self.assertEqual([r["Time_Headway_s"] for r in rows if r["Movement"] == "5-6-7"], ["4.000"])
        self.assertEqual(by[("2-3-4", "1")]["Time_Gap_s"], "0.600")                   # 1.05 - 4.5 / 10
        self.assertEqual(by[("2-3-4", "1")]["Reference_Line"], "Observed Zone 2")
        self.assertEqual(by[("2-3-4", "1")]["Lead_Length_m"], "4.50")
        self.assertNotIn("Negative_Time_Gap", by[("2-3-4", "1")]["QC_Flag"])

    def test_headway_negative_time_gap_and_slow_lead(self):
        tracks, mv = scene({})
        rows = headway(tracks, mv, {"Car": 14.0})            # a 14 m long lead: the 1.05 s headway is shorter than its length / speed
        first = [r for r in rows if r["Movement"] == "2-3-4"][0]
        self.assertEqual(first["Time_Gap_s"], "-0.350")
        self.assertIn("Negative_Time_Gap", first["QC_Flag"])
        slow = headway(tracks, mv, speed=2.0)
        self.assertEqual(slow[0]["Time_Gap_s"], "")
        self.assertIn("Lead_Too_Slow_For_Time_Gap", slow[0]["QC_Flag"])

    def test_stage_streams_match_union_map(self):
        for mv, per_zone in NS["GAP_STAGE_CONFLICTS"].items():
            union = sorted({s for streams in per_zone.values() for s in streams})
            self.assertEqual(union, sorted(NS["RUN3_GAP_CONFLICT_MAP"][mv]))


class ReferenceLine(unittest.TestCase):
    def fake(self, with_zones=True):
        f = Fake()
        f.lines = {"Line 4": [(1.0, 1.0), (2.0, 2.0)]}
        f.zones = {"Zone 1": [(0, 0), (10, 0), (10, 10), (0, 10)], "Zone 3": [(10, 0), (20, 0), (20, 10), (10, 10)]} if with_zones else {}
        return f

    def test_zone_edge_is_the_default_source(self):
        line, label = self.fake()._run3_reference_line("1-3-6-7", {(8, "1-3-6-7"): "Line 4"}, 8, {"reference_line_source": "zone_edge"})
        self.assertEqual(label, "Edge 1-3")
        self.assertEqual(sorted(line), [(10.0, 0.0), (10.0, 10.0)])

    def test_drawn_source_uses_the_mapped_line(self):
        line, label = self.fake()._run3_reference_line("1-3-6-7", {(8, "1-3-6-7"): "Line 4"}, 8, {"reference_line_source": "drawn"})
        self.assertEqual((label, line), ("Line 4", [(1.0, 1.0), (2.0, 2.0)]))

    def test_an_explicit_entry_wins_over_the_zone_edge(self):
        line, label = self.fake()._run3_reference_line("1-3-6-7", {}, 8, {"reference_line_source": "zone_edge"}, {(8, "1-3-6-7"): "Line 4"})
        self.assertEqual(label, "Line 4")

    def test_no_shared_edge_falls_back_to_the_mapped_line(self):
        line, label = self.fake(with_zones=False)._run3_reference_line("1-3-6-7", {(8, "1-3-6-7"): "Line 4"}, 8, {})
        self.assertEqual(label, "Line 4")
        none_line, none_label = self.fake(with_zones=False)._run3_reference_line("1-3-6-7", {}, 8, {})
        self.assertEqual(none_line, [])                                                           # nothing usable -> the caller uses the origin zone

    def test_edge_name_can_be_written_in_the_mapping(self):
        line, label = self.fake()._run3_reference_line("2-3-4", {(8, "2-3-4"): "Edge 1-3"}, 8, {"reference_line_source": "drawn"})
        self.assertEqual(label, "Edge 1-3")


if __name__ == "__main__":
    unittest.main()
