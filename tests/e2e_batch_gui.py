"""Real test of the GUI batch (Batch dialog logic + start_batch worker) on two short clips.

Run from the Run folder:   py -3.12 tests/e2e_batch_gui.py     (needs YOLO + a sample video; skips otherwise)
Tree:  Site/day1/a.mp4 (analyse 1.0-2.0 s, record 1.2-1.5 s)   Site/day1/b.mp4 (whole clip, no recording)
Checks the mirrored output folders, each clip's own CSVs, the _Combined sets, the time windows and that
the plan file can be saved, loaded and run again by tools/batch_run.py's helpers.
"""
import csv
import json
import os
import shutil
import sys
import tempfile
import time
import tkinter as tk
from tkinter import filedialog, messagebox

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
    """Run Tk's real mainloop (worker threads may only use Tk while it runs) until done() or timeout."""
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

tmp = tempfile.mkdtemp(prefix="pk_bgui_")
tree = os.path.join(tmp, "in", "Site", "day1")
os.makedirs(tree)
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
w, h = int(cap.get(3)), int(cap.get(4))
for name in ("a.mp4", "b.mp4"):
    out = cv2.VideoWriter(os.path.join(tree, name), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 600)
    for _ in range(int(3 * fps)):
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
shown = []
messagebox.showinfo = lambda *a, **k: shown.append(("info", a))
messagebox.showerror = lambda *a, **k: shown.append(("error", a))
messagebox.askokcancel = lambda *a, **k: True

# main-window settings the batch uses for every clip
for key, val in (("lane_entry_motorcycle_m", "1.5"), ("lane_entry_car_m", "3.25"), ("lane_opp_motorcycle_m", "1.2"),
                 ("lane_opp_car_m", "3.0"), ("median_m", "0")):
    app.run3_geometry_vars[key].set(val)
app.zone_line_config_var.set(zone)
app.load_pkstudio_zones()

# ---- dialog logic (no clicks needed) ----
dlg = mod.BatchDialog(app)
dlg.add_videos(batch_run.find_videos([os.path.join(tmp, "in", "Site")]))
check("dialog lists both clips with place/day", [c["rel_dir"] for c in dlg.clips] == ["Site/day1", "Site/day1"] and len(dlg.tree.get_children()) == 2)
dlg.clips[0].update({"analysis_start_s": "1.0", "analysis_end_s": "0:02", "save_video": True, "record_start_s": "1.2", "record_end_s": "1.5"})
dlg.clips[1].update({"save_video": False})
dlg.refresh()
vals = [dlg.tree.item(i, "values") for i in dlg.tree.get_children()]
check("list shows each clip's analysis and recording choice", vals[0][1] == "1.0 – 0:02" and vals[0][2] == "1.2 – 1.5" and vals[1][1] == "ทั้งคลิป" and vals[1][2] == "ไม่บันทึก", str(vals))
dlg.set_all_record(False)
check("'no recording for all' clears every clip", all(not c["save_video"] and not c["record_start_s"] for c in dlg.clips))
dlg.clips[0].update({"save_video": True, "record_start_s": "1.2", "record_end_s": "1.5"})
plan_path = os.path.join(tmp, "plan.json")
filedialog.asksaveasfilename = lambda *a, **k: plan_path
filedialog.askopenfilename = lambda *a, **k: plan_path
dlg.out_var.set(os.path.join(tmp, "out"))
dlg.save_plan()
dlg.clear()
dlg.load_plan()
check("plan file round trip keeps clips, times and output folder", len(dlg.clips) == 2 and dlg.clips[0]["record_end_s"] == "1.5" and dlg.out_var.get() == os.path.join(tmp, "out"))
out_root, plan_clips = batch_run.load_plan(plan_path)
check("tools/batch_run.py reads the same plan", len(plan_clips) == 2 and plan_clips[0]["analysis_end_s"] == "0:02")

# ---- run it ----
started = app.start_batch(dlg.clips, os.path.join(tmp, "out"), False)
check("batch started", started is True, str(shown))
wait_in_mainloop(lambda: not app.running, 600)
wait_in_mainloop(lambda: False, 1)
check("batch finished and the window is usable again", not app.running and str(app.start_button.cget("state")) == "normal")
check("final report shown once, no error box", [k for k, _ in shown] == ["info"], str([k for k, _ in shown]))

o = os.path.join(tmp, "out")
a_dir, b_dir = os.path.join(o, "Site", "day1", "a"), os.path.join(o, "Site", "day1", "b")
check("each clip has its own folder mirroring Site/day1/", os.path.isdir(a_dir) and os.path.isdir(b_dir))
check("each clip has its own CSV files", all(os.path.isfile(os.path.join(d, f)) for d in (a_dir, b_dir) for f in (os.path.basename(d) + "_Detection_Records.csv", "Run_3_Speed.csv", "Run_3_Summary.json")))
for d, lo, hi in ((a_dir, 1.0, 2.0), (b_dir, 0.0, 3.0)):
    det = list(csv.DictReader(open(os.path.join(d, os.path.basename(d) + "_Detection_Records.csv"), encoding="utf-8-sig")))
    ts = [float(r["timestamp"]) for r in det]
    check(f"{os.path.basename(d)}: timestamps inside {lo}-{hi} s", ts and min(ts) >= lo - 1e-6 and max(ts) <= hi + 1e-6, f"{min(ts):.2f}..{max(ts):.2f}")
check("clip a recorded only 1.2-1.5 s, clip b recorded nothing",
      os.path.isfile(os.path.join(a_dir, "a_Research_Tracking_Result.mp4")) and not os.path.isfile(os.path.join(b_dir, "b_Research_Tracking_Result.mp4")))
check("combined set exists for the day (the place above has the same two clips, so no duplicate set)",
      os.path.isfile(os.path.join(o, "Site", "day1", "_Combined", "Combined_Statistics.csv")) and not os.path.exists(os.path.join(o, "Site", "_Combined")))
clips_in = set(json.load(open(os.path.join(o, "Site", "day1", "_Combined", "Combined_Summary.json"), encoding="utf-8"))["clips"])
check("combined set names its clips by place/day/clip", clips_in == {"Site/day1/a", "Site/day1/b"}, str(clips_in))
cmp_rows = list(csv.DictReader(open(os.path.join(o, "Batch_Comparison.csv"), encoding="utf-8-sig")))
check("comparison table has both clips, completed", [r["Status"] for r in cmp_rows] == ["completed", "completed"], str([r["Status"] for r in cmp_rows]))

# ---- skip-done: running again does no work ----
shown.clear()
t0 = time.time()
app.start_batch(dlg.clips, o, True)
wait_in_mainloop(lambda: not app.running, 120)
wait_in_mainloop(lambda: False, 1)
check("second run with 'skip done' is instant (< 25 s)", time.time() - t0 < 25, f"{time.time() - t0:.1f}s")

root.destroy()
shutil.rmtree(tmp, ignore_errors=True)
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
