"""The vehicle rectangles that TTC uses, drawn on the X-Y video and on the normal roadside video (Tracking_Result.mp4; each with its own switch, no extra video).

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
     "widths": {"Car": 1.8}, "lengths": {"Car": 4.5}, "risk_limits": dict(m.RISK_DEFAULT_LIMITS), "ttc_show_boxes_xy": True, "ttc_show_boxes_video": True, "ttc_method": "box"}

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

# ---- the normal roadside video (Tracking_Result.mp4): the rectangles are drawn on it after Run 3 and it keeps its name
def make_result(name, n):
    path = os.path.join(out_dir, name)
    w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
    for _ in range(n):
        w.write(np.full((CH, CW, 3), 80, np.uint8))
    w.release()
    return path


res = make_result("Tracking_Result.mp4", 21)
before = os.path.getsize(res)
bv = app._run3_overlay_ttc_boxes(tracks, c, res, first_frame=1)
check("the rectangles are drawn on Tracking_Result.mp4 itself (same file name, no third video)", bv == res and os.path.isfile(res) and not os.path.exists(os.path.splitext(res)[0] + "._ttc_tmp.mp4"), str(bv))
check("no other video file is left in the folder", sorted(f for f in os.listdir(out_dir) if f.endswith(".mp4")) == ["Tracking_Result.mp4", "Tracking_Topview.mp4"], str(sorted(os.listdir(out_dir))))
cap = cv2.VideoCapture(res)
nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
cap.release()
check("it keeps the size and the number of pictures of the normal video", size == (CW, CH) and nf == 21, f"{size} {nf}")
f = frame_at(res, 10)
ys, xs = np.where(red(f))
check("the red rectangles are where the cars are (y = 15 m x 20 px = 300 px)", len(ys) > 200 and abs(float(np.median(ys)) - 300) < 40, f"{len(ys)} px, median y {np.median(ys) if len(ys) else None}")
# car 1 at t = 1.0 s is at x = 15 m = 300 px; its box is 5.0 m = 100 px long: the red pixels reach x = 250..350
check("the box of car 1 is 100 px long (5.0 m x 20 px/m)", len(xs) > 0 and (xs.min() <= 252) and np.any((xs >= 340) & (xs <= 352)), f"x {xs.min() if len(xs) else None}..{xs.max() if len(xs) else None}")
# a recording that starts later: picture i is frame first_frame + i
res2 = make_result("Tracking_Result.mp4", 11)
app._run3_overlay_ttc_boxes(tracks, c, res2, first_frame=11)                    # picture 0 is frame 11 (t = 1.0 s)
g0, g_last = frame_at(res2, 0), frame_at(res2, 10)
check("with a later first frame the pictures line up (picture 0 = frame 11 is red, picture 10 = frame 21 is not)", int(red(g0).sum()) > 200 and int(red(g_last).sum()) < 20,
      f"{int(red(g0).sum())} {int(red(g_last).sum())}")
check("first recorded frame: no window = 1; a recording start of 1 s at 10 fps = frame 11",
      app._run3_record_first_frame({}, video) == 1 and app._run3_record_first_frame({"record_start_s": "1"}, video) == 11,
      f"{app._run3_record_first_frame({}, video)} {app._run3_record_first_frame({'record_start_s': '1'}, video)}")
check("without a video or without shapes nothing is drawn", app._run3_overlay_ttc_boxes(tracks, c, os.path.join(out_dir, "nope.mp4"), 1) is None
      and (lambda: (setattr(app, "_run3_ttc_shapes", None), app._run3_overlay_ttc_boxes(tracks, c, res, 1))[1] is None)())


# ---- the POINT method: the expected collision point (where the two straight paths cross) is drawn as a red cross + the TTC
# car 1 along +x at y = 15 m (10 m/s), car 2 along -y at x = 25 m (10 m/s): both reach (25, 15) at t = 2.0 s
tr2 = {1: [], 2: []}
for k in range(21):
    t = k / 10.0
    for tid, (x, y) in ((1, (5.0 + 10.0 * t, 15.0)), (2, (25.0, 35.0 - 10.0 * t))):
        px = (x * PPM, y * PPM)
        tr2[tid].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Car", "zone": "Zone 3", "_zone_num": 3,
                         "_point": px, "_center": px, "_m": (x, y), "_mc": (x, y), "confidence": "0.9"})
cp_ = dict(c, ttc_method="point", ttc_miss_margin_m=0.5)
rows_p, diag_p, frames_p, shapes_p = app._run3_ttc(tr2, cp_, {})
app._run3_ttc_shapes = shapes_p
mk = shapes_p[11]["marks"]
check("point method: one mark at t = 1.0 s, TTC 1.0 s, the paths cross at (25, 15) m",
      len(mk) == 1 and abs(mk[0]["ttc"] - 1.0) < 0.03 and mk[0]["cross"] is not None and abs(mk[0]["cross"][0] - 25.0) < 0.05 and abs(mk[0]["cross"][1] - 15.0) < 0.05, str(mk[:1]))
check("point method: the event row has the crossing point, the distances and the arrival times (both 1.0 s from the minimum frame)",
      rows_p and rows_p[0]["Collide_X_m"] != "" and abs(float(rows_p[0]["Collide_X_m"]) - 25.0) < 0.1, str(rows_p[0] if rows_p else None))
check("point method: no rectangles are built", all(not sh["rects"] for sh in shapes_p.values()))
xp = frame_at(app._run3_write_topview_video(tr2, cp_, tempfile.mkdtemp(dir=tmp), video, display={"draw_trail": False}), 10)
check("X-Y video (point method): the red cross is drawn", int(red(xp).sum()) > 30, str(int(red(xp).sum())))
res_p = make_result("Tracking_Result.mp4", 21)
app._run3_overlay_ttc_boxes(tr2, cp_, res_p, first_frame=1)
fp_ = frame_at(res_p, 10)
ys2, xs2 = np.where(red(fp_))
check("normal video (point method): the cross is at (25 m x 20 px/m, 15 m x 20 px/m) = (500, 300) px", len(xs2) > 30 and abs(float(np.median(xs2)) - 500) < 25 and abs(float(np.median(ys2)) - 300) < 25,
      f"{len(xs2)} px, median ({np.median(xs2) if len(xs2) else None}, {np.median(ys2) if len(ys2) else None})")
# parallel paths (the two cars head-on on one line): no crossing point -> no cross, only a thin line and the TTC
rows_h, _d, _f, shapes_h = app._run3_ttc(tracks, cp_, {})
check("head-on cars on one line: no crossing point (parallel) - the mark has no cross", shapes_h[11]["marks"] and shapes_h[11]["marks"][0]["cross"] is None and rows_h[0]["Collide_X_m"] == "")

# ---- the meeting point has to be inside a selected zone (with room at the edge for the vehicle size)
app.zones["Zone 3"] = [(20, 100), (300, 100), (300, 600), (20, 600)]                  # x 1..15 m, y 5..30 m: the cars meet at (25, 15): 10 m outside
zc = dict(cp_, ttc_meet_in_zone=True, ttc_zone_margin_m=1.0)
rows_z, diag_z, frames_z, _sh = app._run3_ttc(tr2, zc, {})
check("the cars meet 10 m outside the zone: no event with a 1 m edge margin", rows_z == [] and diag_z["frames_meeting_outside_zone"] > 0, str((len(rows_z), diag_z["frames_meeting_outside_zone"])))
check("... the frames are listed as Outside_Zone in the frame file", any(r["Status"] == "Outside_Zone" for r in frames_z))
rows_z2, _d2, _f2, _s2 = app._run3_ttc(tr2, dict(zc, ttc_zone_margin_m=11.0), {})
check("with an 11 m edge margin (room for the vehicle size) the event counts", len(rows_z2) == 1 and abs(float(rows_z2[0]["Meet_X_m"]) - 25.0) < 0.5, str(rows_z2[:1]))
rows_z3, _d3, _f3, _s3 = app._run3_ttc(tr2, dict(zc, ttc_meet_in_zone=False), {})
check("the zone rule can be switched off", len(rows_z3) == 1)
app.zones["Zone 3"] = [(20, 100), (1260, 100), (1260, 600), (20, 600)]
rows_z4, _d4, _f4, _s4 = app._run3_ttc(tr2, zc, {})
check("a zone that holds the meeting point (x 1..63 m, y 5..30 m): counted", len(rows_z4) == 1)

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
