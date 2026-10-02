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

    def _clip(self, rel, speeds, old_names=False):
        d = os.path.join(self.root, *rel.split("/"))
        os.makedirs(d)
        name = os.path.basename(d)
        prefix = "Run_3_" if old_names else name + "_"
        with open(os.path.join(d, prefix + "Summary.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(d, prefix + "Speed_Detail.csv"), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["Vehicle_ID", "Scope", "Key", "Vehicle_Class", "Speed_kmh", "QC_Flag"])
            for i, v in enumerate(speeds, 1):
                w.writerow([i, "Zone", "Zone 2", "Car", v, ""])
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
        with open(os.path.join(target, "All_Speed_Detail.csv"), newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([(r["Clip"], r["Vehicle_ID"], r["Speed_kmh"]) for r in rows],
                         [("Site/d1/a", "1", "30"), ("Site/d1/a", "2", "40"), ("Site/d2/b", "1", "50")])
        self.assertFalse(os.path.exists(os.path.join(target, "All_Gap_Acceptance.csv")))    # nothing but headers -> no file
        with open(os.path.join(target, "All_Statistics.csv"), newline="", encoding="utf-8-sig") as f:
            st = {r["Group"]: r for r in csv.DictReader(f)}
        self.assertEqual(st["All"]["N"], "3")
        self.assertAlmostEqual(float(st["All"]["Mean"]), 40.0)
        self.assertAlmostEqual(float(st["All"]["V50_Median"]), 40.0)

    def test_ids_that_restart_in_every_clip_get_a_unique_key(self):
        import combine_clips
        self._clip("Site/d1/20260907_084751A_", [30, 40])
        self._clip("Site/d1/b", [50])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        with open(os.path.join(self.root, "Site", "All_Clips", "All_Speed_Detail.csv"), newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            rows = list(reader)
        self.assertEqual(header[:5], ["Clip", "Clip_Start", "Vehicle_ID", "Vehicle_ID_Unique", "Scope"])
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

    def test_old_run_3_names_are_still_read(self):
        import combine_clips
        self._clip("Site/d1/a", [30], old_names=True)
        self._clip("Site/d1/b", [60])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        with open(os.path.join(self.root, "Site", "All_Clips", "All_Speed_Detail.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual(sorted(r["Clip"] for r in csv.DictReader(f)), ["Site/d1/a", "Site/d1/b"])

    def test_a_later_clip_is_added_to_the_combined_files(self):
        import combine_clips
        self._clip("Site/d1/a", [30])
        self._clip("Site/d1/b", [40])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        self._clip("Site/d2/c", [50])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)      # rebuilt from every clip folder
        with open(os.path.join(self.root, "Site", "All_Clips", "All_Clips.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual([r["Clip"] for r in csv.DictReader(f)], ["Site/d1/a", "Site/d1/b", "Site/d2/c"])

    def test_one_clip_is_not_combined_with_itself(self):
        import combine_clips
        self._clip("Site/d1/a", [30])
        self.assertEqual(combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None), {})
        self.assertFalse(os.path.exists(os.path.join(self.root, "Site", "All_Clips")))

    def test_the_combined_folder_is_never_read_as_a_clip(self):
        import combine_clips
        self._clip("Site/d1/a", [30])
        self._clip("Site/d1/b", [40])
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        combine_clips.combine_top_folders(self.root, ["Site"], log=lambda *_: None)
        with open(os.path.join(self.root, "Site", "All_Clips", "All_Speed_Detail.csv"), newline="", encoding="utf-8-sig") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 2)


class ChainsAndIdContinuation(unittest.TestCase):
    def test_group_units(self):
        clips = [{"video": "a"}, {"video": "b", "continues_previous": True}, {"video": "c", "continues_previous": True}, {"video": "d"}]
        units = batch_run.group_units(clips)
        self.assertEqual([[c["video"] for c in u] for u in units], [["a", "b", "c"], ["d"]])
        # a "continues" mark on the very first clip has nothing to continue
        self.assertEqual([[c["video"] for c in u] for u in batch_run.group_units([{"video": "a", "continues_previous": True}])], [["a"]])

    def test_chain_name(self):
        self.assertEqual(batch_run.chain_name(["C:/x/DJI_0426.MP4", "C:/x/DJI_0427.MP4", "C:/x/DJI_0428.MP4"]), "DJI_0426_to_DJI_0428")

    def test_a_chain_ignores_the_time_range_typed_for_its_clips(self):
        clip = {"analysis_start_s": "0:10", "analysis_end_s": "0:30", "record_start_s": "0:12", "record_end_s": "0:20", "save_video": True}
        st, _, _ = batch_run.clip_settings({}, "C:/x/a.mp4", "S", {}, "out", clip, True, chain=["C:/x/a.mp4", "C:/x/b.mp4"])
        self.assertEqual((st["analysis_start_s"], st["analysis_end_s"], st["record_start_s"], st["record_end_s"]), ("", "", "", ""))
        self.assertTrue(st["save_video"])                                       # recorded whole, as the first clip chose
        st, _, _ = batch_run.clip_settings({}, "C:/x/a.mp4", "S", {}, "out", clip, True)       # a single clip keeps its range
        self.assertEqual((st["analysis_start_s"], st["analysis_end_s"]), ("0:10", "0:30"))

    def test_clip_settings_for_a_chain(self):
        st, name, run_dir = batch_run.clip_settings({"run3": {}}, "C:/x/a.mp4", "S/d", {}, "out", None, False,
                                                    chain=["C:/x/a.mp4", "C:/x/b.mp4"])
        self.assertEqual(name, "a_to_b")
        self.assertEqual(st["video_chain"], ["C:/x/a.mp4", "C:/x/b.mp4"])
        self.assertEqual(run_dir, os.path.join("out", "S", "d", "a_to_b"))
        st1, name1, _ = batch_run.clip_settings({"run3": {}}, "C:/x/a.mp4", "S/d", {}, "out")
        self.assertNotIn("video_chain", st1)
        self.assertEqual(name1, "a")

    def _fake_clip(self, root, rel, max_id, with_summary_json=True):
        d = os.path.join(root, *rel.split("/"))
        os.makedirs(d)
        name = os.path.basename(d)
        with open(os.path.join(d, name + "_Summary.json"), "w") as f:
            f.write("{}")
        if with_summary_json:
            with open(os.path.join(d, name + "_Research_Run_Summary.json"), "w") as f:
                json.dump({"max_track_id": max_id}, f)
        else:       # an older result: only the detection records tell the highest ID
            with open(os.path.join(d, name + "_Detection_Records.csv"), "w", newline="") as f:
                f.write("frame,track_id" + chr(10) + "1,3" + chr(10) + "2,%d" % max_id + chr(10) + "3,-1" + chr(10))
        return d

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
