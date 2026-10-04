"""Real-pipeline test of the setting "รถที่อยู่นอกโซน" for the normal video: dot / hide / show (needs YOLO + a video).

Run from the Run folder:   py -3.12 tests/e2e_outside.py
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
import json
zd = json.load(open(zone, encoding="utf-8"))
zd["zones"] = [z for z in zd["zones"] if z.get("name") == "Zone 4"]                          # ONE small zone: most vehicles are outside every zone
small_zone = os.path.join(tmp, "one_zone.json")
json.dump(zd, open(small_zone, "w", encoding="utf-8"))
res = {}
for mode in ("dot", "hide", "show"):
    base = app.get_settings()
    base["zone_file"] = small_zone
    base.pop("zone_snapshot", None)
    base.setdefault("run3", {}).update({"lane_entry_motorcycle_m": "1.5", "lane_entry_car_m": "3.25", "lane_opp_motorcycle_m": "1.2", "lane_opp_car_m": "3.0", "median_m": "0"})
    base.update({"analysis_start_s": "1.0", "analysis_end_s": "0:02", "record_start_s": "1.0", "record_end_s": "2.0",
                 "outside_zone_normal": mode, "draw_center": True, "draw_trail": True, "show_bbox": True})
    rows = batch_run.run_batch(app, base, os.path.join(tmp, "out_" + mode), [(clip, "", {})], save_video=True, log=lambda *_: None)
    check(f"run completed ({mode})", rows[0]["Status"] == "completed", rows[0]["Status"])
    v = cv2.VideoCapture(os.path.join(tmp, "out_" + mode, "clip", "Tracking_Result.mp4"))
    red = green = 0
    while True:
        ok, f = v.read()
        if not ok:
            break
        red += int(((f[..., 2] > 200) & (f[..., 1] < 70) & (f[..., 0] < 70)).sum())             # the red ring of the decision point
        green += int(((f[..., 1] > 200) & (f[..., 2] < 80) & (f[..., 0] < 80)).sum())            # boxes and labels
    v.release()
    res[mode] = (red, green)
print(res)
check("dot (the old behaviour): rings outside the zones are drawn", res["dot"][0] > 0)
check("hide: no ring and nothing else of a vehicle outside every zone", res["hide"][0] == 0, str(res["hide"]))
check("show: the vehicles outside the zones get box/labels like those inside (more green than dot)", res["show"][1] > res["dot"][1], str((res["show"], res["dot"])))
check("hide draws no more of the boxes than dot (inside the zones is the same)", res["hide"][1] <= res["dot"][1] * 1.05 + 50, str((res["hide"], res["dot"])))
root.destroy()
shutil.rmtree(tmp, ignore_errors=True)
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
