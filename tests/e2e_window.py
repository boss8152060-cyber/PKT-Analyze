"""Real-pipeline test of the analysis window and the recording window (needs YOLO + a video).

Run from the Run folder:   py -3.12 tests/e2e_window.py
Cuts a 3 s clip (60 fps) out of the first video in ../Input/Video (skips if there is none), runs the
real Run 1+2+3 pipeline on it with  analyse 1.0 s - 2.0 s  and  record 1.2 s - 1.5 s  and checks the
frames/timestamps in Detection_Records.csv and the length of the recorded video.
"""
import csv
import os
import shutil
import sys
import tempfile
import tkinter as tk

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import batch_run  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


vid_dir = os.path.join(HERE, "..", "..", "Input", "Video")
src = next((os.path.join(vid_dir, f) for f in sorted(os.listdir(vid_dir)) if f.lower().endswith(".mp4")), None) if os.path.isdir(vid_dir) else None
zone = os.path.join(HERE, "..", "..", "Input", "Zone", "20260907_084751A_zones.json")
if not src or not os.path.isfile(zone):
    print("SKIP: no sample video / zone file in PK STUDIO/Input")
    sys.exit(0)

tmp = tempfile.mkdtemp(prefix="pk_win_")
clip = os.path.join(tmp, "clip.mp4")
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
w, h = int(cap.get(3)), int(cap.get(4))
out = cv2.VideoWriter(clip, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
cap.set(cv2.CAP_PROP_POS_FRAMES, 600)
for _ in range(int(3 * fps)):
    ok, f = cap.read()
    if not ok:
        break
    out.write(f)
out.release()
cap.release()

batch = batch_run.load_pkstudio()
root = tk.Tk()
root.withdraw()
app = batch.Run1App(root)
base = app.get_settings()
base["zone_file"] = zone
base.pop("zone_snapshot", None)
base.setdefault("run3", {}).update({"lane_entry_motorcycle_m": "1.5", "lane_entry_car_m": "3.25",
                                    "lane_opp_motorcycle_m": "1.2", "lane_opp_car_m": "3.0", "median_m": "0"})
base.update({"analysis_start_s": "1.0", "analysis_end_s": "0:02", "record_start_s": "1.2", "record_end_s": "1.5"})
rows = batch_run.run_batch(app, base, os.path.join(tmp, "out"), [(clip, "", {})], save_video=True, log=lambda *_: None)
check("run completed", rows[0]["Status"] == "completed", rows[0]["Status"])
run_dir = os.path.join(tmp, "out", "clip")
det = list(csv.DictReader(open(os.path.join(run_dir, "Detection_Records.csv"), encoding="utf-8-sig")))
frames = sorted({int(r["frame"]) for r in det})
stamps = [float(r["timestamp"]) for r in det]
import math
first_exp = int(math.ceil(1.0 * fps - 1e-6)) + 1      # fps of the real file is 60.003, not exactly 60
last_exp = int(math.floor(2.0 * fps + 1e-6)) + 1
check(f"detections only inside frames {first_exp}..{last_exp} (1.0 s - 2.0 s)", frames and frames[0] >= first_exp and frames[-1] <= last_exp, f"{frames[:1]}..{frames[-1:]}")
check("first timestamp is the video time 1.0 s (not restarted at 0)", abs(min(stamps) - 1.0) < 0.03, f"{min(stamps):.3f}")
check("last timestamp <= 2.0 s", max(stamps) <= 2.0 + 1e-6, f"{max(stamps):.3f}")
v = cv2.VideoCapture(os.path.join(run_dir, "Tracking_Result.mp4"))
n = int(v.get(cv2.CAP_PROP_FRAME_COUNT))
v.release()
check("recorded video = frames 73..91 only (1.2 s - 1.5 s) = 19 frames", abs(n - 19) <= 1, str(n))
import json
summ = json.load(open(os.path.join(run_dir, "Run_Summary.json"), encoding="utf-8"))
check("run summary states the analysis window", summ.get("analysis_window", {}).get("first_frame") == first_exp and summ["analysis_window"]["last_frame"] == last_exp, str(summ.get("analysis_window")))
root.destroy()
shutil.rmtree(tmp, ignore_errors=True)
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
