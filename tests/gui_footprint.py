"""The vehicle footprint (length x width rectangle on the road plane): attached to the tracked points, drawn in the X-Y video and in the
real (roadside) video, and written to Detection_Records_Topview.csv.

Run from the Run folder:   python tests/gui_footprint.py
"""
import importlib.util
import os
import sys
import tempfile
import tkinter as tk

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


tmp = tempfile.mkdtemp(prefix="pk_fp_")
out_dir = os.path.join(tmp, "ผลลัพธ์ทดสอบ")
os.makedirs(out_dir)
CW, CH = 1280, 720
video = os.path.join(tmp, "clip.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(40):
    vw.write(np.full((CH, CW, 3), 70, np.uint8))
vw.release()

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
app.zones = {name: [] for name in m.ZONE_NAMES}
app.zones["Zone 1"] = [(100, 100), (1200, 100), (1200, 650), (100, 650)]
PPM = 40.0
c = {"perspective": None, "ppm": PPM, "axis_deg": 0.0, "align": None, "lc_heading_window_s": 0.5,
     "lengths": {"Car": 4.5, "Motorcycle": 2.0}, "widths": {"Car": 1.8, "Motorcycle": 0.8}, "footprint_xy": True, "footprint_video": True}
tracks = {1: [], 2: []}
for k in range(30):
    t = k / 10.0
    x = 150 + 25 * k                                           # a car going right: 25 px per frame = 6.25 m/s
    tracks[1].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Car", "zone": "Zone 1", "confidence": "0.9",
                      "bbox_x1": x - 90, "bbox_y1": 300, "bbox_x2": x + 90, "bbox_y2": 420, "_point": (x, 420.0), "_center": (x, 360.0)})
    y = 560 - 15 * k                                           # a motorcycle going up the picture
    tracks[2].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Motorcycle", "zone": "Zone 1", "confidence": "0.8",
                      "bbox_x1": 900, "bbox_y1": y - 60, "bbox_x2": 960, "bbox_y2": y, "_point": (930.0, float(y)), "_center": (930.0, y - 30.0)})
app._run3_attach_metric(tracks, c)
n = app._run3_attach_footprints(tracks, c)
check("every observed vehicle gets a footprint", n == 60, str(n))
r = tracks[1][10]
fp = np.asarray(r["_fp"])
side, long_ = np.hypot(*(fp[0] - fp[1])), np.hypot(*(fp[1] - fp[2]))
check("a car's footprint is 4.5 m x 1.8 m", abs(side - 1.8) < 1e-6 and abs(long_ - 4.5) < 1e-6, f"{side:.3f} x {long_:.3f}")
check("its long side is along the way it drives (to the right: heading ~ 0 deg)", abs(fp[1][1] - fp[2][1]) < 0.05, f"{fp}")
rm = tracks[2][10]
fpm = np.asarray(rm["_fp"])
check("the motorcycle (going 'up' the picture) is 2.0 m long along y and 0.8 m wide", abs(np.hypot(*(fpm[1] - fpm[2])) - 2.0) < 1e-6 and abs(fpm[1][0] - fpm[2][0]) < 0.05
      and abs(np.hypot(*(fpm[0] - fpm[1])) - 0.8) < 1e-6)
px = np.asarray(r["_fp_px"])
check("seen in the video the lowest corner of the footprint touches the bottom of the detector box", abs(px[:, 1].max() - r["bbox_y2"]) < 1.0, f"{px[:, 1].max()} vs {r['bbox_y2']}")
check("... and its middle is the middle of the box", abs((px[:, 0].min() + px[:, 0].max()) / 2 - (r["bbox_x1"] + r["bbox_x2"]) / 2) < 1.0)

# ---- the rows of Detection_Records_Topview.csv
rows = app._run3_topview_rows(tracks, c)
check("the Topview rows carry the heading and the 4 corners of the footprint", all(k in rows[0] for k in ("heading_deg", "fp_cx_m", "fp1_x_m", "fp4_y_m")) and rows[0]["fp1_x_m"] != "")

# ---- the X-Y video draws the footprint
v_on = app._run3_write_topview_video(tracks, c, out_dir, video, display={"draw_trail": False})
v_off = app._run3_write_topview_video(tracks, dict(c, footprint_xy=False), tempfile.mkdtemp(dir=tmp), video, display={"draw_trail": False})


def frame_at(path, idx=15):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, f = cap.read()
    cap.release()
    return f.astype(np.int16) if ok else None


a, b = frame_at(v_on), frame_at(v_off)
check("the X-Y video with the footprint switch on differs from the one with it off (green rectangles)", int((np.abs(a - b).sum(axis=2) > 60).sum()) > 300)

# ---- the real video with the footprints
fv = app._run3_write_footprint_video(tracks, c, out_dir, video, display={})
check("Tracking_Footprint.mp4 is written (also in a folder with Thai letters)", fv is not None and os.path.isfile(fv))
cap = cv2.VideoCapture(fv)
nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
cap.release()
check("it has the size of the real video and one picture per processed frame", size == (CW, CH) and nf == 30, f"{size} {nf}")
f = frame_at(fv, 10)
green = (f[:, :, 1] > 200) & (f[:, :, 0] < 80) & (f[:, :, 2] < 80)
check("the picture has the green footprint outline", int(green.sum()) > 200, str(int(green.sum())))
pt = np.round(px).astype(int)
ys, xs = np.where(green)
check("the green is where the footprint is (the car's rows in the picture)", ys.min() >= pt[:, 1].min() - 80 and ys.max() <= 700, f"{ys.min()}..{ys.max()}")
check("without a video file nothing is written", app._run3_write_footprint_video(tracks, c, out_dir, None) is None)
check("tracks without a box get no footprint (no crash)", app._run3_attach_footprints({1: [{"_timestamp": 0.0, "_m": (1.0, 1.0), "class_name": "Car"}]}, c) == 0)

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
