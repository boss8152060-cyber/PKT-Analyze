"""Real test: "continues the previous clip" - the tracker (vehicle IDs) carries on from one clip to the next while the time
range, the recording and the result files stay separate for each clip. Also: IDs of a not-continued clip continue after the
IDs of the folder.

Run from the Run folder:   py -3.12 tests/e2e_chain.py     (needs YOLO + a sample video; skips otherwise)
List:  Site/a.mp4, Site/b.mp4 (continues a: b starts right where a ends), Site/c.mp4 (another moment, not continued)
  a: whole clip, no recording     b: analysed from 0.05 s, records 0.5-1.0 s only     c: whole clip
Expected: three result folders a, b, c; a vehicle that is in view at the cut keeps ONE ID in a and b; b has its own time range
and its own short video, a has none; c's IDs start after the highest ID used by a and b.
"""
import csv
import json
import os
import shutil
import sys
import tempfile
import time
import tkinter as tk
from tkinter import messagebox

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import batch_run  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def wait_in_mainloop(done, timeout):
    end = time.time() + timeout

    def poll():
        if done() or time.time() > end:
            root.quit()
        else:
            root.after(50, poll)
    root.after(50, poll)
    root.mainloop()


vid_dir = os.path.join(HERE, "..", "..", "Input", "Video")
src = next((os.path.join(vid_dir, f) for f in sorted(os.listdir(vid_dir)) if f.lower().endswith(".mp4")), None) if os.path.isdir(vid_dir) else None
zone = os.path.join(HERE, "..", "..", "Input", "Zone", "20260907_084751A_zones.json")
if not src or not os.path.isfile(zone):
    print("SKIP: no sample video / zone file in PK STUDIO/Input")
    sys.exit(0)

tmp = tempfile.mkdtemp(prefix="pk_chain_")
tree = os.path.join(tmp, "in", "Site")
os.makedirs(tree)
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
w, h = int(cap.get(3)), int(cap.get(4))
n = int(2 * fps)
for name, first in (("a.mp4", 600), ("b.mp4", 600 + n), ("c.mp4", 2400)):      # b starts right where a ends
    out = cv2.VideoWriter(os.path.join(tree, name), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    for _ in range(n):
        ok, f = cap.read()
        if not ok:
            break
        out.write(f)
    out.release()
cap.release()

mod = batch_run.load_pkstudio()
root = tk.Tk()
root.withdraw()
app = mod.Run1App(root)
messagebox.showinfo = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: print("ERROR BOX:", a)
messagebox.askokcancel = lambda *a, **k: True
for key, val in (("lane_entry_motorcycle_m", "1.5"), ("lane_entry_car_m", "3.25"), ("lane_opp_motorcycle_m", "1.2"),
                 ("lane_opp_car_m", "3.0"), ("median_m", "0")):
    app.run3_geometry_vars[key].set(val)
app.zone_line_config_var.set(zone)
app.load_pkstudio_zones()
o = os.path.join(tmp, "out")
app.output_var.set(o)
panel = app.clips_panel
panel.add_videos(batch_run.find_videos([tree]))
check("three clips listed in order a, b, c", [os.path.basename(c["video"]) for c in panel.clips] == ["a.mp4", "b.mp4", "c.mp4"])
panel.tree.selection_set(["1"])
panel.toggle_continue()
check("b is marked as the continuation of a", panel.clips[1]["continues_previous"] is True and panel.clips[0]["continues_previous"] is False)
panel.tree.selection_set(["0"])
panel.toggle_continue()
check("the first clip of the list cannot continue anything", panel.clips[0]["continues_previous"] is False)
panel.clips[0].update({"save_video": False})
panel.clips[1].update({"analysis_start_s": "0:00.05", "save_video": True, "record_start_s": "0:00.5", "record_end_s": "0:01.0"})
panel.refresh()
vals = [panel.tree.item(i, "values") for i in panel.tree.get_children()]
check("the list shows b's own time range and recording and the continue mark", vals[1][1].startswith("0:00.05") and vals[1][3].startswith("↳") and vals[0][3] == "" and vals[2][3] == "", str(vals))
panel.skip_done_var.set(False)
app.start_analysis()
wait_in_mainloop(lambda: not app.running, 900)
wait_in_mainloop(lambda: False, 1)
check("batch finished", not app.running)

site = os.path.join(o, "Site")
check("every clip has its own result folder: a, b, c (nothing is joined)", sorted(d for d in os.listdir(site) if d != "All_Clips") == ["a", "b", "c"], str(sorted(os.listdir(site))))
a_dir, b_dir, c_dir = (os.path.join(site, x) for x in ("a", "b", "c"))


def det(d):
    return list(csv.DictReader(open(os.path.join(d, "Detection_Records.csv"), encoding="utf-8-sig")))


da, db, dc = det(a_dir), det(b_dir), det(c_dir)
fb = sorted({int(r["frame"]) for r in db})
first_exp = int(__import__("math").ceil(0.05 * fps - 1e-6)) + 1
check("b keeps its own time range: it starts at 0.05 s, not at the first frame", fb[0] >= first_exp, f"first frame {fb[0]} (expected >= {first_exp})")
check("a has no result video, b has its own short one (0.5-1.0 s = about 30 frames)",
      not os.path.isfile(os.path.join(a_dir, "Tracking_Result.mp4")) and os.path.isfile(os.path.join(b_dir, "Tracking_Result.mp4")))
rv = cv2.VideoCapture(os.path.join(b_dir, "Tracking_Result.mp4"))
rec_frames = int(rv.get(cv2.CAP_PROP_FRAME_COUNT))
rv.release()
check("b's video holds only the 0.5 s that was asked for", 0.4 * fps <= rec_frames <= 0.6 * fps + 2, f"{rec_frames} frames")
ids = {k: {int(r["track_id"]) for r in rows if int(r["track_id"]) >= 0} for k, rows in (("a", da), ("b", db), ("c", dc))}
check("a vehicle in view at the cut keeps ONE ID in a and in b (the tracker continued)", len(ids["a"] & ids["b"]) >= 1, f"IDs in both: {sorted(ids['a'] & ids['b'])[:8]}")
sa, sb, sc = (json.load(open(os.path.join(d, "Run_Summary.json"), encoding="utf-8")) for d in (a_dir, b_dir, c_dir))
check("the run summaries say what happened: only b continued the tracker", (sa["tracker_continued_from_previous_clip"], sb["tracker_continued_from_previous_clip"], sc["tracker_continued_from_previous_clip"]) == (False, True, False))
check("b keeps a's numbering (same offset), c starts after the highest ID of the folder", sb["id_offset"] == sa["id_offset"] and sc["id_offset"] == max(sa["max_track_id"], sb["max_track_id"]),
      f"offsets a {sa['id_offset']} b {sb['id_offset']} c {sc['id_offset']}; max IDs a {sa['max_track_id']} b {sb['max_track_id']}")
check("c's IDs are all above the others (no ID used twice in the folder)", ids["c"] and min(ids["c"]) > max(ids["a"] | ids["b"]) and not (ids["c"] & (ids["a"] | ids["b"])), f"c min {min(ids['c'])} / a,b max {max(ids['a'] | ids['b'])}")
ac = [r["Clip"] for r in csv.DictReader(open(os.path.join(site, "All_Clips", "All_Clips.csv"), encoding="utf-8-sig"))]
check("the combined files list a, b and c", sorted(ac) == ["Site/a", "Site/b", "Site/c"], str(ac))

root.destroy()
shutil.rmtree(tmp, ignore_errors=True)
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
