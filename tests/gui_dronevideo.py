"""The third video: the X-Y plane drawn on the drone / top-view picture of the Align (Tracking_Topview_Drone.mp4) with its own display switches,
and the independent record choice (none / whole analysed part / a range) of each of the three videos.

Run from the Run folder:   python tests/gui_dronevideo.py
"""
import importlib.util
import json
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


tmp = tempfile.mkdtemp(prefix="pk_drone_")
video = os.path.join(tmp, "clip.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (1280, 720))
for _ in range(5):
    vw.write(np.full((720, 1280, 3), 60, np.uint8))
vw.release()
# the drone picture: a blue sheet (so that it is easy to tell from the dark X-Y plane)
drone_path = os.path.join(tmp, "drone.png")
cv2.imwrite(drone_path, np.full((800, 1200, 3), (200, 80, 20), np.uint8))

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
app.zones = {name: [] for name in m.ZONE_NAMES}
app.zones["Zone 1"] = [(100, 100), (900, 100), (900, 500), (100, 500)]
# Align: video pixel (x, y) -> drone pixel (x, y) * 0.9 (a pure scale), 0.1 m per drone pixel
src = [(100, 100), (900, 100), (900, 500), (100, 500), (500, 300)]
pairs = [{"s": list(q), "d": [q[0] * 0.9, q[1] * 0.9]} for q in src]
align = {"pairs": pairs, "kind": "helmert", "scale": 0.1, "rot_deg": 0.0, "origin": [0.0, 0.0], "video_size": [1280, 720],
         "drone": {"path": drone_path, "frame": ""}}
app.run3_align_var.set(json.dumps(align))
app.run3_align_enabled_var.set(True)
app.video_var.set(video)
cfg = app._run3_align_cfg(silent=True)
check("the Align builds", cfg is not None and "error" not in cfg, str(cfg)[:100] if cfg is None or "error" in cfg else "")

tracks = {1: [], 2: []}
for k in range(40):
    t = k / 10.0
    p1 = np.array([[200.0 + 10 * k, 300.0]])
    p2 = np.array([[800.0 - 8 * k, 250.0 + 2 * k]])
    tracks[1].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Car", "zone": "Zone 1", "confidence": "0.91",
                      "_m": tuple(m.align_apply(cfg, p1)[0]), "_mc": tuple(m.align_apply(cfg, p1)[0])})
    tracks[2].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Motorcycle", "zone": "", "confidence": "0.80",
                      "_m": tuple(m.align_apply(cfg, p2)[0]), "_mc": tuple(m.align_apply(cfg, p2)[0])})
c = {"perspective": None, "ppm": 40.0, "axis_deg": 0.0, "align": cfg, "align_drone": (drone_path, None)}


def frame_at(path, idx=15):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, f = cap.read()
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return (f.astype(np.int16) if ok else None), n


all_off = dict({f"show_label_{n}": False for n in ("id", "class", "conf", "zone", "speed")}, draw_trail=False)
out = tempfile.mkdtemp(dir=tmp)
v = app._run3_write_topview_video(tracks, c, out, video, display=dict(all_off, dr_show_label_id=True), drone=True)
check("the drone video is written with its own name", v is not None and os.path.basename(v) == "Tracking_Topview_Drone.mp4", str(v))
f, n = frame_at(v)
check("it has a frame per processed frame", f is not None and n >= 30, str(n))
check("the picture has the shape of the drone picture (3:2)", abs(f.shape[1] / f.shape[0] - 1.5) < 0.02, f"{f.shape[1]}x{f.shape[0]}")
blue = ((f[..., 0] > 150) & (f[..., 2] < 60)).mean()
check("the drone picture is the background", blue > 0.6, f"{blue:.2f}")
# the vehicle of track 1 at frame 15 (video px (350, 300)) is drawn at the same place of the drone picture (x 0.9 -> 315, 270 at the original scale; 1200 px wide -> scale 1)
pt = f[270 - 6:270 + 7, 315 - 6:315 + 7]
yellow = ((pt[..., 2] > 200) & (pt[..., 1] > 200) & (pt[..., 0] < 90)).sum()
check("the vehicle is drawn where the Align puts it on the drone picture", yellow > 8, str(int(yellow)))

# its switches are its own: the X-Y video's labels on / the drone video's labels off -> no green text on the drone video
out2 = tempfile.mkdtemp(dir=tmp)
v2 = app._run3_write_topview_video(tracks, c, out2, video, display=dict(all_off, xy_show_label_id=True, xy_show_label_class=True, dr_show_label_id=False,
                                                                       dr_show_label_class=False, dr_show_label_conf=False, dr_show_label_zone=False,
                                                                       dr_show_label_speed=False), drone=True)
f2, _ = frame_at(v2)
green = lambda a: int(((a[..., 1] > 200) & (a[..., 2] < 90) & (a[..., 0] < 90)).sum())
check("drone-video labels off although the X-Y video's labels are on", green(f2) == 0 and green(f) > 20, f"{green(f2)} vs {green(f)}")
# the zone is drawn on the picture
zone_px = int(((np.abs(f - np.array([200, 80, 20])).sum(axis=2) > 120)).sum())
check("the zone is drawn on the drone picture", zone_px > 300, str(zone_px))

# a range to record
out3 = tempfile.mkdtemp(dir=tmp)
v3 = app._run3_write_topview_video(tracks, c, out3, video, display=dict(all_off, drone_start_s="1", drone_end_s="2"), drone=True)
_, n3 = frame_at(v3)
check("only the chosen range is recorded (1-2 s = about 10 frames of 40)", 8 <= n3 <= 12, str(n3))
v4 = app._run3_write_topview_video(tracks, c, tempfile.mkdtemp(dir=tmp), video, display=dict(all_off, xy_start_s="2", xy_end_s="3"))
_, n4 = frame_at(v4)
check("the X-Y video has its own range", 8 <= n4 <= 12, str(n4))

# without the Align picture / the Align: no drone video (nothing is written)
check("no picture -> no drone video", app._run3_write_topview_video(tracks, dict(c, align_drone=None), tempfile.mkdtemp(dir=tmp), video, drone=True) is None)
check("no Align -> no drone video", app._run3_write_topview_video(tracks, dict(c, align=None), tempfile.mkdtemp(dir=tmp), video, drone=True) is None)

# ---- the settings: a third column of switches that is saved and loaded; an older file copies the X-Y choices ----
st = app.get_settings()
check("settings carry the drone switches", all(k in st for k in m.DR_DISPLAY_KEYS) and "outside_zone_dr" in st)
app.xy_vars["xy_show_label_id"].set(False)
app.dr_vars["dr_show_label_id"].set(True)
st = app.get_settings()
check("the three columns are independent", st["xy_show_label_id"] is False and st["dr_show_label_id"] is True)
old = {k: v_ for k, v_ in st.items() if not k.startswith("dr_") and k != "outside_zone_dr"}
old["xy_show_label_id"] = False
old["outside_zone_xy"] = "hide"
app.dr_vars["dr_show_label_id"].set(True)
app.set_settings(old)
check("an older settings file: the drone video starts with the X-Y choices", app.dr_vars["dr_show_label_id"].get() is False and app.outside_zone_dr_var.get() == "hide")

# ---- the clip list: the three videos each have their own choice ----
app.clips_panel.clear()
app.clips_panel.add_videos([("C:/x/a.mp4", "S")])
clip = app.clips_panel.clips[0]
check("a new clip: X-Y on, drone off, roadside off", clip["xy_video"] is True and clip["drone_video"] is False and clip["save_video"] is False)
clip.update({"drone_video": True, "drone_start_s": "0:10", "drone_end_s": "0:20", "xy_video": False})
app.clips_panel.refresh()
vals = tuple(app.clips_panel.tree.item(app.clips_panel.tree.get_children()[0], "values"))[1:]          # (without the number of the clip)
check("the list shows the three choices", vals[2] == "ไม่บันทึก" and vals[3] == "ไม่บันทึก" and vals[4] == "0:10 – 0:20", str(vals))
app.clips_panel.set_all_record(True, ("save_video", "xy_video", "drone_video"))
check("'all clips: record' turns the three on", clip["save_video"] and clip["xy_video"] and clip["drone_video"])
app.clips_panel.set_all_record(False, ("save_video", "xy_video", "drone_video"))
check("'all clips: do not record' turns the three off and clears the ranges", not clip["save_video"] and not clip["xy_video"] and not clip["drone_video"]
      and clip["drone_start_s"] == "" and clip["drone_end_s"] == "")
bt = m._tools_module("batch_run")
st2, _name, _dir = bt.clip_settings({"run3": {}}, "C:/x/a.mp4", "S", {}, tmp, {"xy_video": False, "drone_video": True, "drone_start_s": "5"}, False, False)
check("the choices reach the settings of the clip", st2["xy_video"] is False and st2["drone_video"] is True and st2["drone_start_s"] == "5", str({k: st2.get(k) for k in ("xy_video", "drone_video", "drone_start_s")}))

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
