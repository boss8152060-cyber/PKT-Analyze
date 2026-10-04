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
app.zones["Zone 1"] = [(100, 100), (1500, 100), (1500, 600), (100, 600)]
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

# ---- vehicles outside every zone: show / dot / hide (X-Y outputs) ----
def mark_px(f):
    return int(((f[..., 2] > 200) & (f[..., 1] < 60) & (f[..., 0] < 60)).sum())           # red ring pixels (outside every zone)


def label_px(f):
    return int(((f[..., 1] > 200) & (f[..., 2] < 90) & (f[..., 0] < 90)).sum())           # green label text


modes = {}
for mode in ("show", "dot", "hide"):
    pth = app._run3_write_topview_video(tracks, c, tempfile.mkdtemp(dir=tmp), video, display={"outside_zone_xy": mode, "draw_trail": True, "trail_length": 10})
    fr_, _ = frame_at(pth, 30)                                                              # frame 31: tracks[1] and tracks[2] are both outside Zone 1
    modes[mode] = (mark_px(fr_), label_px(fr_))
check("X-Y video, outside a zone: show = point + labels, dot = point only, hide = nothing",
      modes["show"][0] > 8 and modes["show"][1] > 50 and modes["dot"][0] > 8 and modes["dot"][1] == 0 and modes["hide"][0] == 0 and modes["hide"][1] == 0, str(modes))
px_modes = {}
for mode in ("show", "dot", "hide"):
    pth = app._run3_write_xy_plot(tracks, c, tempfile.mkdtemp(dir=tmp), video, display={"outside_zone_xy": mode})
    im_ = cv2.imdecode(np.fromfile(pth, dtype=np.uint8), cv2.IMREAD_COLOR)
    px_modes[mode] = int((np.abs(im_.astype(int) - 38).sum(axis=2) > 120).sum())
check("X-Y picture: hide draws less than dot, dot less than show (the tracks outside the zone)", px_modes["hide"] < px_modes["dot"] < px_modes["show"], str(px_modes))
saved = app.get_settings()
saved["outside_zone_normal"], saved["outside_zone_xy"] = "hide", "dot"
app2 = m.Run1App(tk.Toplevel(root))
app2.set_settings(saved)
check("both choices are saved and loaded with the settings", app2.outside_zone_normal_var.get() == "hide" and app2.outside_zone_xy_var.get() == "dot" and
      app2.get_settings()["outside_zone_normal"] == "hide" and app._runtime_snapshot(saved)["outside_zone_normal"] in ("dot", "hide", "show"))
check("the defaults keep what was: normal video = point only, X-Y = in full", app.get_settings()["outside_zone_normal"] == "dot" and app.get_settings()["outside_zone_xy"] == "show")

# ---- the picture is centred on the zones (a far vehicle does not push them to a corner)
far = {1: tracks[1] + [{"frame": "99", "timestamp": "9.9", "_timestamp": 9.9, "class_name": "Car", "zone": "", "confidence": "0.9", "_m": (-60.0, -80.0)}], 2: tracks[2]}
scene_far = app._run3_topview_scene(far, c, video, {})
zp = [q for _z, pts_ in [(zn, app._run3_to_metric(np.asarray(poly, float), c)) for zn, poly in app._zone_polygons()] for q in pts_]
zpx = m.topview_px(scene_far["cv"], np.asarray(zp, float))
cx_, cy_ = (zpx[:, 0].min() + zpx[:, 0].max()) / 2.0, (zpx[:, 1].min() + zpx[:, 1].max()) / 2.0
check("the zones are in the middle of the picture, also with a far vehicle in the data", abs(cx_ - scene_far["W"] / 2.0) < 0.06 * scene_far["W"] and abs(cy_ - scene_far["H"] / 2.0) < 0.06 * scene_far["H"], f"centre ({cx_:.0f}, {cy_:.0f}) in {scene_far['W']}x{scene_far['H']}")
check("the zones fill a good part of the picture", (zpx[:, 0].max() - zpx[:, 0].min()) > 0.25 * scene_far["W"])
# ---- a look before a run: the zones in metres with the calibration that is set now
m.messagebox.showerror = lambda *a, **k: None
app.run3_ppm_var.set("40")
app.video_var.set(video)
pw = app.preview_xy_plane()
root.update()
check("the preview opens before any run: a picture of the zones with a grid", pw is not None and pw.scene["base"].shape[1] / pw.scene["base"].shape[0] > 1.7)
check("it lists the real length of every zone edge (Zone 1 = 1400 px x 500 px at 40 px/m = 35.0 m x 12.5 m)", "35.0" in "\n".join(pw.lines) and "12.5" in "\n".join(pw.lines) and "Zone 1" in "\n".join(pw.lines), "\n".join(pw.lines[:3]))
check("it says which calibration is used", "PPM" in pw.lines[0] or "Perspective" in pw.lines[0] or "Align" in pw.lines[0], pw.lines[0])
pw.destroy()
saved_zones = app.zones
app.zones = {name: [] for name in m.ZONE_NAMES}
check("without zones the preview says so (no window)", app.preview_xy_plane() is None)
app.zones = saved_zones
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
