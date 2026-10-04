"""The X-Y plane (Topview) outputs: Trajectory_XY.png and Tracking_Topview.mp4 drawn from the metric points.

Checks: same shape as the video, reference point + labels follow the display settings, the trajectory switch, the PNG (also in a folder
with Thai letters), no photo / no boxes.

Run from the Run folder:   python tests/gui_topview.py
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


tmp = tempfile.mkdtemp(prefix="pk_xy_")
out_dir = os.path.join(tmp, "ผลลัพธ์ทดสอบ")                       # a folder with Thai letters
os.makedirs(out_dir)
video = os.path.join(tmp, "clip.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (1280, 720))
for _ in range(5):
    vw.write(np.full((720, 1280, 3), 60, np.uint8))
vw.release()

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
app.zones = {name: [] for name in m.ZONE_NAMES}
app.zones["Zone 1"] = [(100, 100), (500, 100), (500, 300), (100, 300)]
tracks = {1: [], 2: []}
for k in range(40):
    t = k / 10.0
    tracks[1].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Car", "zone": "Zone 1" if k < 20 else "",
                      "confidence": "0.91", "_m": (2.0 + 0.9 * k, 5.0), "_mc": (2.0 + 0.9 * k, 5.0)})
    tracks[2].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Motorcycle", "zone": "",
                      "confidence": "0.80", "_m": (30.0 - 0.7 * k, 12.0 + 0.1 * k), "_mc": (30.0 - 0.7 * k, 12.0 + 0.1 * k)})
c = {"perspective": None, "ppm": 40.0, "axis_deg": 0.0}


def frame_at(path, idx=15):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, f = cap.read()
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return (f.astype(np.int16) if ok else None), n


all_off = {f"show_label_{n}": False for n in ("id", "class", "conf", "zone", "speed")}
v_on = app._run3_write_topview_video(tracks, c, out_dir, video, display={"draw_trail": False})
f_on, n_frames = frame_at(v_on)
check("the video is written (also in a folder with Thai letters)", f_on is not None and n_frames >= 30)
check("the picture has the shape of the video (16:9)", abs(f_on.shape[1] / f_on.shape[0] - 16 / 9) < 0.02, f"{f_on.shape[1]}x{f_on.shape[0]}")
v_off = app._run3_write_topview_video(tracks, c, tempfile.mkdtemp(dir=tmp), video, display=dict(all_off, draw_trail=False))
f_off, _ = frame_at(v_off)
check("labels on vs all off: the picture differs where the text is", int((np.abs(f_on - f_off).sum(axis=2) > 60).sum()) > 100)
v_tr = app._run3_write_topview_video(tracks, c, tempfile.mkdtemp(dir=tmp), video, display=dict(all_off, draw_trail=True, trail_length=10))
f_tr, _ = frame_at(v_tr)
check("the trajectory switch draws the trail", int((np.abs(f_tr - f_off).sum(axis=2) > 60).sum()) > 50)
v_id = app._run3_write_topview_video(tracks, c, tempfile.mkdtemp(dir=tmp), video, display=dict(all_off, show_label_id=True, show_prefix_id=True, draw_trail=False))
f_id, _ = frame_at(v_id)
check("one label on (ID with its prefix) differs from all off and from all on", int((np.abs(f_id - f_off).sum(axis=2) > 60).sum()) > 20
      and int((np.abs(f_id - f_on).sum(axis=2) > 60).sum()) > 20)
# a vehicle inside a zone is a yellow point, outside a red ring (frame 5: tracks[1] in Zone 1, tracks[2] in none)
cap = cv2.VideoCapture(v_off)
cap.set(cv2.CAP_PROP_POS_FRAMES, 5)
ok, f5 = cap.read()
cap.release()
yellow = ((f5[..., 2] > 200) & (f5[..., 1] > 200) & (f5[..., 0] < 90)).sum()
red = ((f5[..., 2] > 200) & (f5[..., 1] < 60) & (f5[..., 0] < 60)).sum()
check("the reference point is yellow inside a zone and a red ring outside", yellow > 15 and red > 8, f"yellow {yellow}, red {red}")
check("no boxes and no photo: the only large bright shapes are the points (the picture is mostly dark grid)", float((f5.mean(axis=2) > 120).mean()) < 0.01)

png = app._run3_write_xy_plot(tracks, c, out_dir, video, display={})
data = np.fromfile(png, dtype=np.uint8) if png else None
img = cv2.imdecode(data, cv2.IMREAD_COLOR) if data is not None else None
check("Trajectory_XY.png is written in the Thai-letter folder", img is not None and img.shape[1] / img.shape[0] > 1.7, "" if img is None else str(img.shape))
coloured = [(img[..., 0] > 200) & (img[..., 1] > 120) & (img[..., 2] < 90)]
check("the plot draws every track as a line (colour per ID)", int(coloured[0].sum()) > 100)
check("without tracks nothing is written", app._run3_write_xy_plot({}, c, out_dir, video) is None and app._run3_write_topview_video({}, c, out_dir, video) is None)
root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
