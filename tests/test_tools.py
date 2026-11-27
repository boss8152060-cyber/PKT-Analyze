"""Unit tests of the pure helpers of tools/batch_run.py (no YOLO, no GUI)."""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import batch_run  # noqa: E402


class PlanRuns(unittest.TestCase):
    def test_no_sweep_one_run_per_video(self):
        self.assertEqual(batch_run.plan_runs([("a.mp4", "S/d1"), ("b.mp4", "S/d2")], {}),
                         [("a.mp4", "S/d1", {}), ("b.mp4", "S/d2", {})])

    def test_plain_paths_accepted(self):
        self.assertEqual(batch_run.plan_runs(["a.mp4"], {}), [("a.mp4", "", {})])

    def test_every_combination_per_video(self):
        runs = batch_run.plan_runs([("a.mp4", "S")], {"track_buffer": ["15", "60"], "match_threshold": ["0.7", "0.9"]})
        self.assertEqual(len(runs), 4)
        self.assertIn(("a.mp4", "S", {"track_buffer": "60", "match_threshold": "0.7"}), runs)

    def test_run_names_are_file_safe_and_distinct(self):
        n1 = batch_run.run_name_for("C:/x/DJI 0426.MP4", {"track_buffer": "15"})
        n2 = batch_run.run_name_for("C:/x/DJI 0426.MP4", {"track_buffer": "60"})
        self.assertEqual(n1, "DJI_0426__track_buffer-15")
        self.assertNotEqual(n1, n2)
        self.assertEqual(batch_run.run_name_for("a.mp4", {}), "a")

    def test_parse_sweeps(self):
        self.assertEqual(batch_run.parse_sweeps(["track_buffer=15, 30,60"]), {"track_buffer": ["15", "30", "60"]})
        with self.assertRaises(SystemExit):
            batch_run.parse_sweeps(["track_buffer"])


class FolderMirror(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pk_tree_")
        for rel in ("Site8/2026-09-07/a.mp4", "Site8/2026-09-07/b.MP4", "Site8/2026-09-08/c.mp4", "Site8/2026-09-08/notes.txt"):
            full = os.path.join(self.root, *rel.split("/"))
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, "w").close()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_find_videos_keeps_place_and_day(self):
        found = batch_run.find_videos([os.path.join(self.root, "Site8")])
        self.assertEqual([(os.path.basename(v), rel) for v, rel in found],
                         [("a.mp4", "Site8/2026-09-07"), ("b.MP4", "Site8/2026-09-07"), ("c.mp4", "Site8/2026-09-08")])

    def test_single_file_has_no_folder(self):
        f = os.path.join(self.root, "Site8", "2026-09-07", "a.mp4")
        self.assertEqual(batch_run.find_videos([f]), [(f, "")])

    def test_run_dir_mirrors_input(self):
        self.assertEqual(batch_run.run_dir_for("out", "Site8/2026-09-07", "a"), os.path.join("out", "Site8", "2026-09-07", "a"))
        self.assertEqual(batch_run.run_dir_for("out", "", "a"), os.path.join("out", "a"))

    def test_picked_folder_name_is_the_first_level_at_any_depth(self):
        deep = os.path.join(self.root, "Site8", "x", "y", "z")
        os.makedirs(deep)
        open(os.path.join(deep, "deep.mp4"), "w").close()
        found = {os.path.basename(v): rel for v, rel in batch_run.find_videos([os.path.join(self.root, "Site8")])}
        self.assertEqual(found["deep.mp4"], "Site8/x/y/z")
        self.assertEqual(found["a.mp4"], "Site8/2026-09-07")

    def test_keep_levels_adds_folders_above_the_picked_one(self):
        day = os.path.join(self.root, "Site8", "2026-09-08")
        self.assertEqual([rel for _v, rel in batch_run.find_videos([day])], ["2026-09-08"])
        self.assertEqual([rel for _v, rel in batch_run.find_videos([day], keep_levels=1)], ["Site8/2026-09-08"])
        top = os.path.basename(self.root)
        self.assertEqual([rel for _v, rel in batch_run.find_videos([day], keep_levels=2)], [top + "/Site8/2026-09-08"])
        # picking the higher folder gives the same relative folder for the same clip
        via_top = [rel for v, rel in batch_run.find_videos([os.path.join(self.root, "Site8")]) if v.endswith("c.mp4")]
        self.assertEqual(via_top, ["Site8/2026-09-08"])

    def test_keep_levels_stops_at_the_drive_root(self):
        found = batch_run.find_videos([os.path.join(self.root, "Site8", "2026-09-08")], keep_levels=60)
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0][1].endswith("Site8/2026-09-08"))

    def test_single_file_levels(self):
        f = os.path.join(self.root, "Site8", "2026-09-07", "a.mp4")
        self.assertEqual(batch_run.find_videos([f], keep_levels=2)[0][1], "Site8/2026-09-07")

    def test_a_later_import_lands_in_the_existing_folders(self):
        first = batch_run.find_videos([os.path.join(self.root, "Site8", "2026-09-07")], keep_levels=1)
        second = batch_run.find_videos([os.path.join(self.root, "Site8", "2026-09-08")], keep_levels=1)
        top = lambda items: {os.path.dirname(batch_run.run_dir_for("out", rel, "x")).rsplit(os.sep, 1)[0] for _v, rel in items}
        self.assertEqual(top(first), top(second))          # the same parent folder is reused
        self.assertNotEqual({rel for _v, rel in first}, {rel for _v, rel in second})

    def test_same_clip_folder_for_two_files_is_reported(self):
        runs = [("C:/x/a.mp4", "S", {}), ("C:/x/a.mov", "S", {}), ("C:/x/b.mp4", "S", {})]
        self.assertEqual(batch_run.duplicate_run_dirs("out", runs), [os.path.join("out", "S", "a")])


class Comparison(unittest.TestCase):
    def test_comparison_table_grows_and_updates(self):
        d = tempfile.mkdtemp(prefix="pk_cmp_")
        try:
            row = lambda folder, run, status: {"Run": run, "Folder": folder, "Overrides": "", "Status": status}
            batch_run.finish_batch(d, [], [row("S/d1", "a", "completed"), row("S/d1", "b", "completed")], log=lambda *_: None)
            batch_run.finish_batch(d, [], [row("S/d2", "c", "completed"), row("S/d1", "b", "stopped")], log=lambda *_: None)
            with open(os.path.join(d, "Batch_Comparison.csv"), newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual([(r["Folder"], r["Run"], r["Status"]) for r in rows],
                             [("S/d1", "a", "completed"), ("S/d1", "b", "stopped"), ("S/d2", "c", "completed")])
        finally:
            shutil.rmtree(d, ignore_errors=True)


class ClipPlan(unittest.TestCase):
    def test_clip_settings_applies_the_clips_choices(self):
        base = {"video": "x", "save_video": True, "analysis_start_s": "", "run3": {}}
        clip = {"video": "a.mp4", "rel_dir": "S/d", "analysis_start_s": "0:30", "analysis_end_s": "2:15",
                "save_video": True, "record_start_s": "1:00", "record_end_s": "1:30"}
        st, name, run_dir = batch_run.clip_settings(base, "a.mp4", "S/d", {}, "out", clip, clip["save_video"])
        self.assertEqual((st["analysis_start_s"], st["analysis_end_s"], st["record_start_s"], st["record_end_s"]),
                         ("0:30", "2:15", "1:00", "1:30"))
        self.assertTrue(st["save_video"])
        self.assertFalse(st["show_preview"])
        self.assertEqual(run_dir, os.path.join("out", "S", "d", "a"))
        self.assertNotIn("rel_dir", st)              # only the known per-clip keys are copied
        self.assertEqual(base["analysis_start_s"], "")   # the base settings are not modified

    def test_preview_follows_the_users_choice(self):
        st, _, _ = batch_run.clip_settings({"show_preview": True}, "a.mp4", "", {}, "out", None, False)
        self.assertFalse(st["show_preview"])                                  # command line: off by default
        st, _, _ = batch_run.clip_settings({"show_preview": True}, "a.mp4", "", {}, "out", None, False, show_preview=True)
        self.assertTrue(st["show_preview"])                                   # the window passes the tick-box value

    def test_no_recording_overrides_the_default(self):
        st, _, _ = batch_run.clip_settings({"save_video": True}, "a.mp4", "", {}, "out", {"save_video": False}, False)
        self.assertFalse(st["save_video"])

    def test_labels(self):
        self.assertEqual(batch_run.clip_label({}), ("ทั้งคลิป", "ไม่บันทึก"))
        self.assertEqual(batch_run.clip_label({"analysis_start_s": "0:30", "save_video": True}), ("0:30 – จบ", "ตลอดช่วงวิเคราะห์"))
        self.assertEqual(batch_run.clip_label({"analysis_end_s": "2", "save_video": True, "record_start_s": "1", "record_end_s": "1.5"}),
                         ("เริ่ม – 2", "1 – 1.5"))

    def test_plan_file_round_trip_and_validation(self):
        d = tempfile.mkdtemp(prefix="pk_plan_")
        try:
            path = os.path.join(d, "p.json")
            clips = [{"video": "a.mp4", "rel_dir": "S", "analysis_start_s": "1", "save_video": False}]
            batch_run.save_plan(path, "out", clips)
            self.assertEqual(batch_run.load_plan(path), ("out", clips))
            with open(path, "w", encoding="utf-8") as f:
                f.write('{"clips": [{"no_video": 1}]}')
            with self.assertRaises(ValueError):
                batch_run.load_plan(path)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class CombineClips(unittest.TestCase):
    """Per-clip CSV files are put together into All_<kind>.csv with a Clip column."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pk_comb_")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _clip(self, rel, speeds, old_names=False, clip_prefixed=False):
        d = os.path.join(self.root, *rel.split("/"))
        os.makedirs(d)
        name = os.path.basename(d)
        prefix = "Run_3_" if old_names else (name + "_" if clip_prefixed else "")
        with open(os.path.join(d, prefix + "Summary.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(d, prefix + "LDP.csv"), "w", newline="", encoding="utf-8-sig") as f:      # the values the statistics are made of
            w = csv.writer(f)
            w.writerow(["Vehicle_ID", "Zone", "Vehicle_Class", "LDP_percent", "QC_Flag"])
            for i, v in enumerate(speeds, 1):
                w.writerow([i, "Zone 2", "Car", v, ""])
        with open(os.path.join(d, prefix + "Speed.csv"), "w", newline="", encoding="utf-8-sig") as f:    # the speed of every frame (no statistics are made of it)
            w = csv.writer(f)
            w.writerow(["Frame", "Time_s", "Vehicle_ID", "Vehicle_Class", "Zone", "Movement", "Speed_kmh", "QC_Flag"])
            for i, v in enumerate(speeds, 1):
                w.writerow([i, i / 30.0, i, "Car", "Zone 2", "2-3-4", v, ""])
        with open(os.path.join(d, prefix + "Gap_Acceptance.csv"), "w", newline="", encoding="utf-8-sig") as f:
            f.write("Subject_ID,Gap_Role" + chr(10))           # a file with only a header row (an empty indicator)
        return d

    def test_combined_files_have_a_clip_column_and_all_rows(self):
        import combine_clips
        self._clip("Site/d1/a", [30, 40])
        self._clip("Site/d2/b", [50])
        out = combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        self.assertEqual(sorted(out["Site"]["clips"]), ["Site/d1/a", "Site/d2/b"])
        target = os.path.join(self.root, "Site", "All_Clips")
        with open(os.path.join(target, "3_LDP.csv"), newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([(r["Clip"], r["Vehicle_ID"], r["LDP_percent"]) for r in rows],
                         [("Site/d1/a", "1", "30"), ("Site/d1/a", "2", "40"), ("Site/d2/b", "1", "50")])
        with open(os.path.join(target, "0_Raw", "Speed_Frames.csv"), newline="", encoding="utf-8-sig") as f:       # the per-frame speed is merged too ...
            self.assertEqual(len(list(csv.DictReader(f))), 3)
        self.assertFalse(os.path.exists(os.path.join(target, "5_Gap_Acceptance.csv")))    # nothing but headers -> no file
        with open(os.path.join(target, "9_Summary", "Statistics.csv"), newline="", encoding="utf-8-sig") as f:
            st = {r["Group"]: r for r in csv.DictReader(f)}
        self.assertEqual(st["All"]["N"], "3")
        self.assertAlmostEqual(float(st["All"]["Mean"]), 40.0)
        self.assertAlmostEqual(float(st["All"]["V50_Median"]), 40.0)
        self.assertEqual({r["Indicator"] for r in csv.DictReader(open(os.path.join(target, "9_Summary", "Statistics.csv"), newline="", encoding="utf-8-sig"))}, {"LDP"})   # ... but no Speed statistics

    def test_runs_folder_layout_has_clips_all_clips_and_reports(self):
        """Output folder named Runs: Runs/<day>/Clips/<clip>, Runs/<day>/All_Clips, and Batch_Comparison.csv in the Reports folder beside Runs."""
        import combine_clips
        runs = os.path.join(self.root, "Site", "Runs")
        a = batch_run.run_dir_for(runs, "2026_09_13", "a")
        b = batch_run.run_dir_for(runs, "2026_09_13", "b")
        self.assertEqual(a, os.path.join(runs, "2026_09_13", "Clips", "a"))
        self.assertEqual(batch_run.run_dir_for(runs, "Site8/2026_09_13", "a"), os.path.join(runs, "Site8", "Clips", "2026_09_13", "a"))
        self.assertEqual(batch_run.run_dir_for(os.path.join(self.root, "out"), "d", "a"), os.path.join(self.root, "out", "d", "a"))   # any other folder: as before
        for d, v in ((a, [30, 40]), (b, [50])):
            os.makedirs(d)
            with open(os.path.join(d, "Summary.json"), "w") as f:
                f.write("{}")
            with open(os.path.join(d, "LDP.csv"), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Vehicle_ID", "Zone", "Vehicle_Class", "LDP_percent", "QC_Flag"])
                for i, x in enumerate(v, 1):
                    w.writerow([i, "Zone 2", "Car", x, ""])
        row = lambda run: {"Run": run, "Folder": "2026_09_13", "Overrides": "", "Status": "completed"}
        batch_run.finish_batch(runs, [("v", "2026_09_13", {})], [row("a"), row("b")], log=lambda *_: None)
        self.assertTrue(os.path.isfile(os.path.join(self.root, "Site", "Reports", "Batch_Comparison.csv")))
        self.assertFalse(os.path.exists(os.path.join(runs, "Batch_Comparison.csv")))
        target = os.path.join(runs, "2026_09_13", "All_Clips")
        self.assertTrue(os.path.isdir(target))
        self.assertFalse(os.path.exists(os.path.join(runs, "2026_09_13", "Clips", "All_Clips")))
        with open(os.path.join(target, "3_LDP.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual([r["Clip"] for r in csv.DictReader(f)], ["2026_09_13/a", "2026_09_13/a", "2026_09_13/b"])

    def test_ids_that_restart_in_every_clip_get_a_unique_key(self):
        import combine_clips
        self._clip("Site/d1/20260907_084751A_", [30, 40])
        self._clip("Site/d1/b", [50])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        with open(os.path.join(self.root, "Site", "All_Clips", "3_LDP.csv"), newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            rows = list(reader)
        self.assertEqual(header[:5], ["Clip", "Clip_Start", "Vehicle_ID", "Vehicle_ID_Unique", "Zone"])
        ids = [r["Vehicle_ID"] for r in rows]
        self.assertEqual(ids, ["1", "2", "1"])                                   # the plain ID repeats ...
        uniq = [r["Vehicle_ID_Unique"] for r in rows]
        self.assertEqual(len(set(uniq)), 3)                                      # ... the unique key does not
        self.assertEqual(uniq[0], "Site/d1/20260907_084751A_#1")
        self.assertEqual(rows[0]["Clip_Start"], "2026-09-07 08:47:51")           # clock time of the clip start from its name
        self.assertEqual(rows[2]["Clip_Start"], "")                              # no time in the name -> blank

    def test_clip_start_time_parsing(self):
        import combine_clips
        f = combine_clips.clip_start_time
        self.assertEqual(f("S/20260907_084751A_"), "2026-09-07 08:47:51")
        self.assertEqual(f("S/x/20251231-235959"), "2025-12-31 23:59:59")
        self.assertEqual(f("S/DJI_0426"), "")
        self.assertEqual(f("S/20261399_999999"), "")                             # impossible date/time is not a time

    def _fake_mp4(self, path, seconds, scale=1000):
        """A file with only a moov/mvhd box (version 0) holding the given length."""
        import struct
        mvhd = struct.pack(">I4s", 8 + 4 + 16 + 80, b"mvhd") + bytes(4) + struct.pack(">IIII", 0, 0, scale, int(seconds * scale)) + bytes(80)
        moov = struct.pack(">I4s", 8 + len(mvhd), b"moov") + mvhd
        ftyp = struct.pack(">I4s", 16, b"ftyp") + b"isom" + bytes(4)
        with open(path, "wb") as f:
            f.write(ftyp + moov)

    def test_video_start_from_name_else_modified_minus_length(self):
        import combine_clips
        import time
        p = os.path.join(self.root, "20260907_084751A.mp4")
        self._fake_mp4(p, 25 * 60)
        self.assertEqual(combine_clips.video_start_time(p), ("2026-09-07 08:47:51", "file name"))
        g = os.path.join(self.root, "GX030111.MP4")
        self._fake_mp4(g, 4868.2)
        self.assertAlmostEqual(combine_clips.mp4_length_s(g), 4868.2, places=3)
        end = time.mktime((2026, 9, 5, 11, 23, 0, 0, 0, -1))
        os.utime(g, (end, end))
        self.assertEqual(combine_clips.video_start_time(g), ("2026-09-05 10:01:52", "modified - length"))
        self.assertEqual(combine_clips.video_start_time(os.path.join(self.root, "missing.mp4")), ("", ""))

    def test_clip_start_comes_from_run_summary_when_the_name_has_no_time(self):
        import combine_clips
        d = self._clip("Site/d1/GX010111", [30])
        with open(os.path.join(d, "Run_Summary.json"), "w", encoding="utf-8") as f:
            json.dump({"video_start": "2026-09-05 07:20:30"}, f)
        self._clip("Site/d1/GX020111", [40])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        with open(os.path.join(self.root, "Site", "All_Clips", "3_LDP.csv"), newline="", encoding="utf-8-sig") as f:
            starts = {r["Clip"]: r["Clip_Start"] for r in csv.DictReader(f)}
        self.assertEqual(starts, {"Site/d1/GX010111": "2026-09-05 07:20:30", "Site/d1/GX020111": ""})

    def test_set_clip_start_finds_the_video_by_name_and_day(self):
        import combine_clips
        import set_clip_start
        import time
        d = self._clip("Results/2026_09_05/GX010111", [30])
        with open(os.path.join(d, "Run_Summary.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "completed"}, f)
        vids = os.path.join(self.root, "Video")
        for day, stamp in (("2026_09_04", (2026, 9, 4, 9, 0, 0)), ("2026_09_05", (2026, 9, 5, 9, 0, 0))):
            os.makedirs(os.path.join(vids, day))
            v = os.path.join(vids, day, "GX010111.MP4")
            self._fake_mp4(v, 3600)
            t = time.mktime(stamp + (0, 0, -1))
            os.utime(v, (t, t))
        set_clip_start.main([os.path.join(self.root, "Results"), vids])
        with open(os.path.join(d, "Run_Summary.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual((data["video_start"], data["video_start_method"], data["status"]), ("2026-09-05 08:00:00", "modified - length", "completed"))
        self.assertEqual(combine_clips.clip_start(d, "Results/2026_09_05/GX010111"), "2026-09-05 08:00:00")

    def test_rezone_clip_takes_zones_and_geometry_from_another_clip(self):
        import rezone_clip
        def clip(rel, zones, run3):
            d = os.path.join(self.root, *rel.split("/"))
            os.makedirs(os.path.join(d, "0_Raw"))
            os.makedirs(os.path.join(d, "9_Summary"))
            with open(os.path.join(d, "9_Summary", "Settings.json"), "w", encoding="utf-8") as f:
                json.dump({"video": rel + ".MP4", "zone_snapshot": {"zones": zones}, "run3": run3, "zone_file": rel}, f)
            with open(os.path.join(d, "9_Summary", "Run_Summary.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "completed"}, f)
            with open(os.path.join(d, "0_Raw", "Detection_Records.csv"), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["frame", "timestamp", "track_id", "class_name", "trajectory_x", "trajectory_y", "zone"])
                for i, x in enumerate((5, 15, 25)):
                    w.writerow([i + 1, i * 0.5, 1, "Car", x, 5, "Zone 7"])
            with open(os.path.join(d, "1_ID_Zone.csv"), "w", newline="", encoding="utf-8-sig") as f:
                f.write("track_id,zone_sequence" + chr(10) + "1,Zone 7" + chr(10))
            return d
        sq = lambda x0: [[x0, 0], [x0 + 10, 0], [x0 + 10, 10], [x0, 10]]  # noqa: E731
        good = clip("S/d/A", {"Zone 1": sq(0), "Zone 3": sq(10), "Zone 4": sq(20)}, {"cal": "A"})
        bad = clip("S/d/B", {"Zone 7": sq(0)}, {"cal": "other camera"})
        rezone_clip.rezone_clip(bad, good, log=lambda *_: None)
        with open(os.path.join(bad, "1_ID_Zone.csv"), encoding="utf-8-sig") as f:
            self.assertEqual(next(csv.DictReader(f))["zone_sequence"], "Zone 1 > Zone 3 > Zone 4")
        with open(os.path.join(bad, "9_Summary", "Settings.json"), encoding="utf-8") as f:
            st = json.load(f)
        self.assertEqual((st["run3"], st["video"], st["zone_file"]), ({"cal": "A"}, "S/d/B.MP4", "S/d/A"))
        self.assertTrue(os.path.isfile(os.path.join(bad, "0_Raw", "Detection_Records_before_rezone.csv")))
        self.assertTrue(os.path.isfile(os.path.join(bad, "9_Summary", "Settings_before_rezone.json")))
        with open(os.path.join(bad, "9_Summary", "Run_Summary.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["rezoned_from_raw"]["routes_changed"], 1)

    def test_stabilize_maps_points_back_into_the_reference_view(self):
        import numpy as np
        import stabilize_clip
        shift = np.array([[1, 0, -40], [0, 1, -20], [0, 0, 1]], dtype=float)   # the view moved 40 px left, 20 px up
        samples = [[0.0, np.eye(3), 500], [10.0, shift, 500]]
        rows = [{"timestamp": "1.0", "trajectory_x": "100", "trajectory_y": "100", "bbox_x1": "90", "bbox_y1": "80", "bbox_x2": "110", "bbox_y2": "100"},
                {"timestamp": "11.0", "trajectory_x": "60", "trajectory_y": "80", "bbox_x1": "50", "bbox_y1": "60", "bbox_x2": "70", "bbox_y2": "80"}]
        out = stabilize_clip.stabilize_rows(rows, samples)
        self.assertEqual((out[0]["trajectory_x"], out[0]["trajectory_y"]), ("100", "100"))      # before the move: unchanged
        self.assertEqual((out[1]["trajectory_x"], out[1]["trajectory_y"]), ("100", "100"))      # after it: back where it was
        self.assertEqual((out[1]["bbox_x1"], out[1]["bbox_y2"]), ("90", "100"))
        self.assertEqual(stabilize_clip.shift_px(shift), (-40.0, -20.0))

    def test_old_run_3_names_are_still_read(self):
        import combine_clips
        self._clip("Site/d1/a", [30], old_names=True)
        self._clip("Site/d1/b", [60], clip_prefixed=True)
        self._clip("Site/d1/c", [90])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        with open(os.path.join(self.root, "Site", "All_Clips", "3_LDP.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual(sorted(r["Clip"] for r in csv.DictReader(f)), ["Site/d1/a", "Site/d1/b", "Site/d1/c"])

    def test_gap_statistics_read_the_new_and_the_old_column_name(self):
        import combine_clips
        for rel, col in (("Site/d1/new", "Available_Gap_s"), ("Site/d1/old", "X31_Available_Gap")):    # old results keep their old column name
            d = self._clip(rel, [30])
            with open(os.path.join(d, "Gap_Acceptance.csv"), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Subject_ID", "Decision_Stage", "Gap_Role", col, "QC_Flag"])
                w.writerow([1, "Access", "Accepted", 2.0, ""])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        with open(os.path.join(self.root, "Site", "All_Clips", "9_Summary", "Statistics.csv"), newline="", encoding="utf-8-sig") as f:
            rows = [r for r in csv.DictReader(f) if r["Indicator"].startswith("Gap Acceptance") and r["Group"] == "All"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["N"], "2")                                   # one value from each clip

    def test_a_later_clip_is_added_to_the_combined_files(self):
        import combine_clips
        self._clip("Site/d1/a", [30])
        self._clip("Site/d1/b", [40])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        self._clip("Site/d2/c", [50])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)      # rebuilt from every clip folder
        with open(os.path.join(self.root, "Site", "All_Clips", "9_Summary", "Clip_List.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual([r["Clip"] for r in csv.DictReader(f)], ["Site/d1/a", "Site/d1/b", "Site/d2/c"])

    def test_one_clip_is_not_combined_with_itself(self):
        import combine_clips
        self._clip("Site/d1/a", [30])
        self.assertEqual(combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None), {})
        self.assertFalse(os.path.exists(os.path.join(self.root, "Site", "All_Clips")))

    def test_every_day_folder_gets_its_own_combined_files(self):
        import combine_clips
        self._clip("Site/d1/a", [30, 40])
        self._clip("Site/d1/b", [50])
        self._clip("Site/d2/c", [60])
        self._clip("Site/d3/x/e", [70])                                     # d3/x holds the same clips as d3 -> only d3
        self._clip("Site/d3/x/f", [80])
        out = combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        self.assertEqual(sorted(out), ["Site", "Site/d1", "Site/d3"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "Site", "d2", "All_Clips")))       # one clip only
        self.assertFalse(os.path.exists(os.path.join(self.root, "Site", "d3", "x", "All_Clips")))
        day = os.path.join(self.root, "Site", "d1", "All_Clips")
        with open(os.path.join(day, "3_LDP.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual([r["Clip"] for r in csv.DictReader(f)], ["d1/a", "d1/a", "d1/b"])     # only the clips of that day
        with open(os.path.join(self.root, "Site", "All_Clips", "3_LDP.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 6)                 # the site: every day
        with open(os.path.join(day, "9_Summary", "Clip_List.csv"), newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([(r["Clip"], r["Rows_LDP"], r["Rows_TTC"]) for r in rows], [("d1/a", "2", "0"), ("d1/b", "1", "0")])

    def test_a_clip_folder_is_arranged_and_still_found(self):
        import combine_clips
        d = self._clip("Site/d1/a", [30, 40])
        for name in ("Detection_Records.csv", "ID_Zone_Summary.csv", "Speed_Zone.csv"):
            with open(os.path.join(d, name), "w", encoding="utf-8") as f:
                f.write("x" + chr(10))
        with open(os.path.join(d, "Tracking_Result.mp4"), "w") as f:
            f.write("v")
        with open(os.path.join(d, "Summary.json"), "w", encoding="utf-8") as f:       # a path inside a JSON file follows its file
            json.dump({"outputs": {"ldp": os.path.join(d, "LDP.csv"), "video": os.path.join(d, "Tracking_Result.mp4")}}, f)
        moved = combine_clips.arrange_clip_folder(d)
        self.assertEqual(len(moved), 7)
        self.assertEqual(sorted(f for f in os.listdir(d)),
                         ["0_Raw", "1_ID_Zone.csv", "2_Speed.csv", "3_LDP.csv", "5_Gap_Acceptance.csv", "9_Summary", "Tracking_Result.mp4"])
        self.assertEqual(sorted(os.listdir(os.path.join(d, "0_Raw"))), ["Detection_Records.csv", "Speed_Frames.csv"])
        with open(os.path.join(d, "9_Summary", "Summary.json"), encoding="utf-8") as f:
            out = json.load(f)["outputs"]
        self.assertEqual(out["ldp"], os.path.join(d, "3_LDP.csv"))
        self.assertEqual(out["video"], os.path.join(d, "Tracking_Result.mp4"))
        rf = combine_clips.result_file
        self.assertEqual(rf(d, "Speed.csv"), os.path.join(d, "0_Raw", "Speed_Frames.csv"))      # found under the old plain name
        self.assertEqual(rf(d, "Detection_Records.csv"), os.path.join(d, "0_Raw", "Detection_Records.csv"))
        self.assertIsNotNone(combine_clips.summary_path(d))
        self._clip("Site/d1/b", [50])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        self.assertEqual([lab for _f, lab in combine_clips.find_clip_folders(os.path.join(self.root, "Site"))], ["Site/d1/a", "Site/d1/b"])  # 9_Summary is no clip
        with open(os.path.join(self.root, "Site", "All_Clips", "3_LDP.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 3)
        combine_clips.arrange_clip_folder(d)                                    # nothing left to move: nothing happens
        self.assertTrue(os.path.isfile(os.path.join(d, "3_LDP.csv")))

    def test_results_with_the_old_names_are_arranged_too(self):
        import combine_clips
        a = self._clip("Site/d1/a", [30], old_names=True)                   # Run_3_LDP.csv ...
        b = self._clip("Site/d1/b", [40], clip_prefixed=True)               # b_LDP.csv ...
        combine_clips.arrange_clip_folder(a)
        combine_clips.arrange_clip_folder(b)
        for d in (a, b):
            self.assertTrue(os.path.isfile(os.path.join(d, "3_LDP.csv")))
            self.assertTrue(os.path.isfile(os.path.join(d, "0_Raw", "Speed_Frames.csv")))
            self.assertTrue(os.path.isfile(os.path.join(d, "9_Summary", "Summary.json")))
        self.assertEqual(sorted(os.listdir(b)), ["0_Raw", "3_LDP.csv", "5_Gap_Acceptance.csv", "9_Summary"])

    def test_the_combined_files_of_older_versions_are_replaced(self):
        import combine_clips
        self._clip("Site/d1/a", [30])
        self._clip("Site/d1/b", [40])
        target = os.path.join(self.root, "Site", "All_Clips")
        os.makedirs(target)
        for old in ("All_LDP.csv", "All_Clips.csv", "All_Summary.json", "my_notes.txt"):
            with open(os.path.join(target, old), "w") as f:
                f.write("x")
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        names = sorted(os.listdir(target))
        self.assertNotIn("All_LDP.csv", names)
        self.assertIn("my_notes.txt", names)                                   # a file of the user stays
        self.assertIn("3_LDP.csv", names)

    def test_the_summary_of_each_clip_is_put_together_too(self):
        import combine_clips
        for rel in ("Site/d1/a", "Site/d1/b"):
            d = self._clip(rel, [30])
            with open(os.path.join(d, "Indicator_Summary.csv"), "w", newline="", encoding="utf-8-sig") as f:
                f.write("Indicator,N,Mean" + chr(10) + "LDP,1,30" + chr(10))
            with open(os.path.join(d, "Run_Summary.json"), "w") as f:
                f.write('{"status": "completed", "processed_frames": 300, "unique_track_ids": 7}')
            with open(os.path.join(d, "Settings.json"), "w") as f:
                f.write('{"video_fps": "30"}')
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        target = os.path.join(self.root, "Site", "All_Clips")
        with open(os.path.join(target, "9_Summary", "Indicator_Summary.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual([(r["Clip"], r["Indicator"]) for r in csv.DictReader(f)], [("Site/d1/a", "LDP"), ("Site/d1/b", "LDP")])
        with open(os.path.join(target, "9_Summary", "Clip_List.csv"), newline="", encoding="utf-8-sig") as f:
            r = next(csv.DictReader(f))
        self.assertEqual((r["Status"], r["Frames"], r["Duration_s"], r["Unique_Track_IDs"]), ("completed", "300", "10.0", "7"))

    def test_the_combined_folder_is_never_read_as_a_clip(self):
        import combine_clips
        self._clip("Site/d1/a", [30])
        self._clip("Site/d1/b", [40])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        with open(os.path.join(self.root, "Site", "All_Clips", "3_LDP.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 2)


class RunComplete(unittest.TestCase):
    """batch_run.run_complete: a clip is done only when it was analysed to the end of its video (a stopped clip, or one whose disk was lost, is done again)."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pk_runc_")
        self.d = os.path.join(self.root, "clip1")
        os.makedirs(self.d)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, summary=True, run=None):
        if summary:
            with open(os.path.join(self.d, "Summary.json"), "w") as f:
                f.write("{}")
        if run is not None:
            with open(os.path.join(self.d, "Run_Summary.json"), "w") as f:
                json.dump(run, f)

    def test_no_summary_is_not_done(self):
        self._write(summary=False, run={"status": "completed", "input": {"read_to_the_end": True}})
        self.assertFalse(batch_run.run_complete(self.d, "clip1"))

    def test_read_to_the_end_is_done(self):
        self._write(run={"status": "completed", "input": {"read_to_the_end": True}})
        self.assertTrue(batch_run.run_complete(self.d, "clip1"))

    def test_stopped_or_interrupted_is_not_done(self):
        for status in ("stopped", "interrupted"):
            self._write(run={"status": status, "input": {"read_to_the_end": status == "stopped"}})
            self.assertFalse(batch_run.run_complete(self.d, "clip1"), status)

    def test_a_video_not_read_to_the_end_is_not_done(self):
        self._write(run={"status": "completed", "input": {"read_to_the_end": False}})
        self.assertFalse(batch_run.run_complete(self.d, "clip1"))

    def test_older_results_are_judged_by_the_frames(self):
        full = {"status": "completed", "total_frames": 3600, "processed_frames": 1800, "analysis_window": {"first_frame": 1, "last_frame": 3600}}
        with open(os.path.join(self.d, "Settings.json"), "w") as f:
            json.dump({"frame_skip": "1 - Process every 2nd frame"}, f)
        self._write(run=full)
        self.assertTrue(batch_run.run_complete(self.d, "clip1"))                              # 1800 detected x 2 = the whole video
        self._write(run=dict(full, processed_frames=700))
        self.assertFalse(batch_run.run_complete(self.d, "clip1"))                             # 1400 of 3600: the video was cut
        self.assertEqual([batch_run.frame_skip_from_text(t) for t in ("NO - Process every frame", "1 - Process every 2nd frame", "4 - Process every 5th frame", "")], [1, 2, 5, 1])

    def test_a_result_with_no_run_summary_is_taken_as_done(self):
        self._write(run=None)
        self.assertTrue(batch_run.run_complete(self.d, "clip1"))

class IdContinuation(unittest.TestCase):
    def test_the_continue_mark_is_kept_in_a_plan_but_is_not_a_run_setting(self):
        self.assertIn("continues_previous", batch_run.PLAN_KEYS)
        self.assertNotIn("continues_previous", batch_run.CLIP_KEYS)
        st, _, _ = batch_run.clip_settings({}, "C:/x/a.mp4", "S", {}, "out", {"continues_previous": True, "analysis_end_s": "0:30"}, False)
        self.assertNotIn("continues_previous", st)
        self.assertEqual(st["analysis_end_s"], "0:30")                       # time range stays per clip

    def _fake_clip(self, root, rel, max_id, with_summary_json=True):
        d = os.path.join(root, *rel.split("/"))
        os.makedirs(d)
        name = os.path.basename(d)
        with open(os.path.join(d, "Summary.json"), "w") as f:
            f.write("{}")
        if with_summary_json:
            with open(os.path.join(d, "Run_Summary.json"), "w") as f:
                json.dump({"max_track_id": max_id}, f)
        else:       # an older result: only the detection records tell the highest ID
            with open(os.path.join(d, name + "_Detection_Records.csv"), "w", newline="") as f:
                f.write("frame,track_id" + chr(10) + "1,3" + chr(10) + "2,%d" % max_id + chr(10) + "3,-1" + chr(10))
        return d

    def test_result_file_finds_plain_and_older_names(self):
        import combine_clips
        d = os.path.join(tempfile.mkdtemp(prefix="pk_names_"), "clip1")
        os.makedirs(d)
        try:
            for fn in ("Speed.csv", "clip1_Research_Settings.json", "Run_3_TTC.csv", "clip1_Detection_Records.csv"):
                open(os.path.join(d, fn), "w").close()
            rf = combine_clips.result_file
            self.assertEqual(os.path.basename(rf(d, "Speed.csv")), "Speed.csv")
            self.assertEqual(os.path.basename(rf(d, "Settings.json")), "clip1_Research_Settings.json")
            self.assertEqual(os.path.basename(rf(d, "TTC.csv")), "Run_3_TTC.csv")
            self.assertEqual(os.path.basename(rf(d, "Detection_Records.csv")), "clip1_Detection_Records.csv")
            self.assertIsNone(rf(d, "PET.csv"))
        finally:
            shutil.rmtree(os.path.dirname(d), ignore_errors=True)

    def test_ids_continue_after_the_previous_clips_of_the_same_top_folder(self):
        root = tempfile.mkdtemp(prefix="pk_ids_")
        try:
            self._fake_clip(root, "Site/d1/a", 57)
            self._fake_clip(root, "Site/d1/b", 120, with_summary_json=False)
            self._fake_clip(root, "Other/x", 999)
            st, _, _ = batch_run.clip_settings({}, "C:/v/c.mp4", "Site/d2", {}, root)
            self.assertEqual(st["id_offset"], 120)                              # highest of Site only (not of Other)
            st, _, _ = batch_run.clip_settings({}, "C:/v/new.mp4", "Brand_new", {}, root)
            self.assertEqual(st["id_offset"], 0)                                # nothing there yet
            # a clip that is analysed again does not count itself
            st, _, _ = batch_run.clip_settings({}, "C:/v/b.mp4", "Site/d1", {}, root)
            self.assertEqual(st["id_offset"], 57)
            # tracker sweeps stay comparable: no offset
            st, _, _ = batch_run.clip_settings({}, "C:/v/c.mp4", "Site/d2", {"track_buffer": "15"}, root)
            self.assertEqual(st["id_offset"], 0)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
