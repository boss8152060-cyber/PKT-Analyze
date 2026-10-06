"""The vehicle rectangles that TTC uses, drawn on the X-Y video and on the real video (each with its own switch).

Two cars drive towards each other (10 m/s each, 4.5 m x 1.8 m). The boxes (+ 0.25 m on each side) touch when the centres are 5.0 m apart: at t = 1.75 s.
Before that the frames count (red, with the TTC written), after that they overlap.

Run from the Run folder:   python tests/gui_ttcboxes.py
"""
import importlib.util
import os
import sys
import tempfile
import tkinter as tk

import cv2
import numpy as np

os.environ["PK_STUDIO_CUDA_RELAUNCHED"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


tmp = tempfile.mkdtemp(prefix="pk_ttcbox_")
out_dir = os.path.join(tmp, "ผลลัพธ์")
os.makedirs(out_dir)
CW, CH = 1280, 720
PPM = 20.0
video = os.path.join(tmp, "clip.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(30):
    vw.write(np.full((CH, CW, 3), 80, np.uint8))
vw.release()

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
app.zones = {name: [] for name in m.ZONE_NAMES}
app.zones["Zone 3"] = [(20, 100), (1260, 100), (1260, 600), (20, 600)]
c = {"perspective": None, "perspective_enabled": False, "ppm": PPM, "axis_deg": 0.0, "align": None, "site_id": 8,
     "ttc_enabled": True, "ttc_zones": [3], "ttc_velocity_window_s": 0.5, "ttc_min_speed_kmh": 5.0, "ttc_min_rel_speed_ms": 0.5, "ttc_pair_radius_m": 50.0,
     "ttc_max_record_s": None, "ttc_box_margin_m": 0.25, "ttc_angle_rear_end_deg": 30.0, "ttc_angle_crossing_deg": 85.0,
     "widths": {"Car": 1.8}, "lengths": {"Car": 4.5}, "risk_limits": dict(m.RISK_DEFAULT_LIMITS), "ttc_show_boxes_xy": True, "ttc_show_boxes_video": True}

tracks = {1: [], 2: []}
for k in range(21):
    t = k / 10.0
    for tid, x in ((1, 5.0 + 10.0 * t), (2, 45.0 - 10.0 * t)):
        px = (x * PPM, 15.0 * PPM)
        tracks[tid].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Car", "zone": "Zone 3", "_zone_num": 3,
                            "_point": px, "_center": px, "_m": (x, 15.0), "_mc": (x, 15.0), "confidence": "0.9"})
rows, diag, frames, shapes = app._run3_ttc(tracks, c, {})
app._run3_ttc_shapes = shapes
check("one event: the two cars head-on (angle 180 deg = Crossing in the 30 / 85 deg scheme)", len(rows) == 1 and rows[0]["TTC_Type"] == "Crossing", str([r["TTC_Type"] for r in rows]))
check("the shapes have the rectangles of both cars in every frame with a heading", all(len(sh["rects"]) == 2 for fr, sh in shapes.items() if 2 <= fr <= 21), str({fr: len(sh["rects"]) for fr, sh in list(shapes.items())[:4]}))
sh = shapes[11]                                               # t = 1.0 s: the centres are 20 - 20 = 20 m apart (45-10 - (5+10)) = 20 m: boxes 15 m apart: counted
check("at t = 1.0 s both cars are 'hot' (in a counted TTC frame) and the pair TTC is written (15 m closing at 20 m/s = 0.75 s)",
      sh["hot"] == {1, 2} and sh["pairs"] and abs(sh["pairs"][0][2] - 0.75) < 0.03, str((sh["hot"], sh["pairs"])))
poly = sh["rects"][0]["poly"]
check("the rectangle of car 1 is 5.0 m x 2.3 m (4.5 x 1.8 + 0.25 m on each side), long side along +x",
      abs((poly[:, 0].max() - poly[:, 0].min()) - 5.0) < 1e-6 and abs((poly[:, 1].max() - poly[:, 1].min()) - 2.3) < 1e-6)
last = shapes[21]
check("at t = 2.0 s the boxes overlap: not hot", last["hot"] == set() and len(last["rects"]) == 2, str(last["hot"]))


def frame_at(path, idx):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, f = cap.read()
    cap.release()
    return f.astype(np.int16) if ok else None


def red(f):
    return (f[:, :, 2] > 190) & (f[:, :, 1] < 80) & (f[:, :, 0] < 80)


def green(f):
    return (f[:, :, 1] > 180) & (f[:, :, 2] < 80) & (f[:, :, 0] < 80)


# ---- X-Y video
v_on = app._run3_write_topview_video(tracks, c, out_dir, video, display={"draw_trail": False})
v_off = app._run3_write_topview_video(tracks, dict(c, ttc_show_boxes_xy=False), tempfile.mkdtemp(dir=tmp), video, display={"draw_trail": False})
a, b = frame_at(v_on, 10), frame_at(v_off, 10)
check("X-Y video: the rectangles are drawn when the switch is on (red = counted frame)", int(red(a).sum()) > 200 and int(red(b).sum()) < int(red(a).sum()) // 10,
      f"red on {int(red(a).sum())} / off {int(red(b).sum())}")
a2, b2 = frame_at(v_on, 19), frame_at(v_off, 19)
changed = int((np.abs(a2 - b2).sum(axis=2) > 60).sum())
check("X-Y video: after the boxes overlap they are drawn (green, not red): the picture differs from the switch-off one and has no red", changed > 800 and int(red(a2).sum()) < 100,
      f"changed {changed} red {int(red(a2).sum())}")
check("X-Y video with the switch off has no red rectangles", int(red(b).sum()) < 20 and int(red(b2).sum()) < 20, f"{int(red(b).sum())} {int(red(b2).sum())}")

# ---- the real video
bv = app._run3_write_ttc_boxes_video(tracks, c, out_dir, video)
check("Tracking_TTC_Boxes.mp4 is written (also in a folder with Thai letters)", bv is not None and os.path.isfile(bv))
cap = cv2.VideoCapture(bv)
nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
cap.release()
check("it has the size of the real video and one picture per frame with rectangles", size == (CW, CH) and nf >= 19, f"{size} {nf}")
f = frame_at(bv, 10)
ys, xs = np.where(red(f))
check("the red rectangles are where the cars are (y = 15 m x 20 px = 300 px, x between car 1 and car 2)", len(ys) > 200 and abs(float(np.median(ys)) - 300) < 40, f"{len(ys)} px, median y {np.median(ys) if len(ys) else None}")
# car 1 at t = 1.0 s is at x = 15 m = 300 px; its box is 5.0 m = 100 px long: the red pixels reach x = 250..350
check("the box of car 1 is 100 px long (5.0 m x 20 px/m)", len(xs) > 0 and (xs.min() <= 252) and np.any((xs >= 340) & (xs <= 352)), f"x {xs.min() if len(xs) else None}..{xs.max() if len(xs) else None}")
check("without the shapes nothing is written", (lambda: (setattr(app, "_run3_ttc_shapes", None), app._run3_write_ttc_boxes_video(tracks, c, out_dir, video))[1] is None)())

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
