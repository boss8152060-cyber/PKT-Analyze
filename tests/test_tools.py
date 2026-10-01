"""Unit tests of the pure helpers of tools/batch_run.py (no YOLO, no GUI)."""
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

    def test_combined_groups_one_per_folder_level(self):
        runs = batch_run.plan_runs([("a.mp4", "Site8/d1"), ("b.mp4", "Site8/d1"), ("c.mp4", "Site8/d2")], {})
        g = batch_run.combined_groups(runs)
        self.assertEqual(g[("Site8/d1", ())], [0, 1])          # the day with 2 clips
        self.assertNotIn(("Site8/d2", ()), g)                  # a day with 1 clip needs no combined set
        self.assertEqual(g[("Site8", ())], [0, 1, 2])          # the place: all 3 clips
        self.assertNotIn(("", ()), g)                          # the root would only repeat the place's set

    def test_combined_groups_keep_sweep_values_apart(self):
        runs = batch_run.plan_runs([("a.mp4", "S"), ("b.mp4", "S")], {"track_buffer": ["15", "60"]})
        g = batch_run.combined_groups(runs)
        self.assertEqual(len(g[("S", (("track_buffer", "15"),))]), 2)
        self.assertEqual(len(g[("S", (("track_buffer", "60"),))]), 2)


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


if __name__ == "__main__":
    unittest.main()
