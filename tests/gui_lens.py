"""Lens correction without any reference picture: the straight-line tool, the lens values in the settings, and the Topview video
(the road without vehicles, straightened and laid flat on the ground).

Run from the Run folder:   python tests/gui_lens.py
A synthetic wide-angle camera is made: a ground texture seen through a known perspective and a known barrel distortion.
"""
import importlib.util
import json
import math
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


tmp = tempfile.mkdtemp(prefix="pk_lens_")
CW, CH = 1280, 720
LENS = (0.50, 0.0, 0.0)                      # a plain equidistant fisheye, about 113 degrees across at 16:9 (GoPro Wide class)
rng = np.random.default_rng(8)

# ---- the world: a ground texture (20 px per metre), seen by an ideal camera, then bent by the lens
tex = np.full((800, 1200, 3), 110, np.uint8)
for _ in range(260):
    x0, y0 = int(rng.integers(0, 1150)), int(rng.integers(0, 760))
    if rng.random() < 0.5:
        cv2.rectangle(tex, (x0, y0), (x0 + int(rng.integers(8, 60)), y0 + int(rng.integers(3, 14))), tuple(int(v) for v in rng.integers(30, 230, 3)), -1)
    else:
        cv2.line(tex, (x0, y0), (x0 + int(rng.integers(-90, 90)), y0 + int(rng.integers(-90, 90))), tuple(int(v) for v in rng.integers(30, 230, 3)), int(rng.integers(2, 5)))
h_ground_to_cam = np.array([[0.9, 0.25, 120.0], [-0.05, 0.8, 60.0], [0.0003, 0.0009, 1.0]])         # texture px -> ideal camera px
ideal = cv2.warpPerspective(tex, h_ground_to_cam, (CW, CH))
yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float64)
src = m.lens_undistort(np.stack([xx.ravel(), yy.ravel()], 1), (CW, CH), LENS).reshape(CH, CW, 2).astype(np.float32)
bent = cv2.remap(ideal, src[..., 0], src[..., 1], cv2.INTER_LINEAR)
video = os.path.join(tmp, "wide.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(30):
    vw.write(bent)
vw.release()

# ---- a second clip of straight lines (a grid) for the line tool
grid_ideal = np.full((CH, CW, 3), 90, np.uint8)
for x in range(160, CW, 160):
    cv2.line(grid_ideal, (x, 0), (x, CH - 1), (240, 240, 240), 3)
for y in range(120, CH, 120):
    cv2.line(grid_ideal, (0, y), (CW - 1, y), (240, 240, 240), 3)
grid_bent = cv2.remap(grid_ideal, src[..., 0], src[..., 1], cv2.INTER_LINEAR)
grid_video = os.path.join(tmp, "grid.mp4")
vw = cv2.VideoWriter(grid_video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(10):
    vw.write(grid_bent)
vw.release()

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
m.messagebox.showinfo = lambda *a, **k: None
m.messagebox.showerror = lambda *a, **k: None
app.video_var.set(grid_video)

# ---- the line tool
dlg = app.open_lens_line_tool()
root.update()
check("the line tool opens on a frame of the video", dlg is not None and dlg.cam_img is not None and dlg.size == (CW, CH))
check("no lines: estimating says what is missing", dlg.estimate() is None and "2 เส้น" in dlg.msg_var.get())


def clicked_line(x0, y0, x1, y1, n=8):
    ideal_pts = np.column_stack([np.linspace(x0, x1, n), np.linspace(y0, y1, n)])
    return m.lens_distort(ideal_pts, (CW, CH), LENS)                 # where the camera recorded them


lines = [clicked_line(160, 20, 160, 700), clicked_line(1120, 20, 1120, 700), clicked_line(20, 120, 1260, 120),
         clicked_line(20, 600, 1260, 600), clicked_line(640, 20, 640, 700)]
for i, pts in enumerate(lines):
    if i:
        dlg.new_line()
    for x, y in pts:
        dlg.add_point(x, y)
root.update()
check("five lines clicked", len(dlg.usable_lines()) == 5)
check("an empty line is not added twice", dlg.new_line() and dlg.new_line() is False)
dlg.delete_line()
est = dlg.estimate()
check("the lens is found from the lines", est is not None and abs(est["lens"][0] - LENS[0]) < 0.05, "" if est is None else f"f {est['lens'][0]:.3f}")
check("the lines get much straighter", est is not None and est["bend_after"] < 0.15 * est["bend_before"], "" if est is None else f"{est['bend_before'] * 100:.2f}% -> {est['bend_after'] * 100:.3f}%")
dlg.fixed_var.set(True)
dlg.refresh()
root.update()
fixed_view = dlg.last_render.copy()
dlg.fixed_var.set(False)
dlg.refresh()
check("the corrected picture can be shown", (fixed_view != dlg.last_render).any())
# clicking in the corrected picture is carried back to the recorded picture
dlg.fixed_var.set(True)
n_before = len(dlg.lines[-1])
dlg.add_point(300.0, 300.0)
back = dlg.lines[-1][-1]
want = m.lens_distort([(300.0, 300.0)], (CW, CH), dlg.lens)[0]
check("a point clicked in the corrected picture is stored as in the recorded one", abs(back[0] - want[0]) < 1e-6 and abs(back[1] - want[1]) < 1e-6)
dlg.undo_point()
dlg.fixed_var.set(False)
root.update()
# mouse: wheel zoom and a click
cv_ = dlg.canvas
cv_.event_generate("<MouseWheel>", x=300, y=200, delta=120)
root.update()
check("mouse wheel zooms the picture", dlg.zoom > 1.0)
dlg.reset_view()
n0 = len(dlg.lines[-1])
k_, ox_, oy_ = dlg.view
cv_.event_generate("<ButtonPress-1>", x=int(400 * k_ + ox_), y=int(300 * k_ + oy_))
cv_.event_generate("<ButtonRelease-1>", x=int(400 * k_ + ox_), y=int(300 * k_ + oy_))
root.update()
check("a plain click adds a point", len(dlg.lines[-1]) == n0 + 1)
dlg.undo_point()
applied = dlg.apply()
check("apply writes the lens into the settings and closes", applied and app.run3_lens_f_var.get() != "" and abs(float(app.run3_lens_f_var.get()) - LENS[0]) < 0.05)
lens_app, size_app = app._run3_lens_params()
check("the program reads the lens back with the picture size", lens_app is not None and size_app == (CW, CH) and abs(lens_app[0] - LENS[0]) < 0.05)

# ---- settings round trip, preview, clear
saved = app.get_settings()
app2 = m.Run1App(tk.Toplevel(root))
app2.set_settings(saved)
check("the lens values survive saving and loading the settings", app2.run3_lens_k1_var.get() == app.run3_lens_k1_var.get() and app2.run3_lens_f_var.get() == app.run3_lens_f_var.get())
pv = app.preview_lens_settings()
check("the before/after preview shows two pictures", pv is not None and len(pv.photos) == 2)
pv.destroy()
app.clear_lens_values()
check("clear removes the lens", app._run3_lens_params() == (None, None))
app.set_lens_values(LENS)
check("typed / applied values are used", app._run3_lens_params()[0] is not None)
app.run3_lens_k1_var.set("0")
app.run3_lens_f_var.set("0.2")
check("a lens whose corner ray would be beyond 87 degrees is ignored", app._run3_lens_params() == (None, None))
app.set_lens_values(LENS)

# ---- every pixel -> metre conversion straightens the points first
H_c2m = np.diag([1 / 20.0, 1 / 20.0, 1.0]) @ np.linalg.inv(h_ground_to_cam)                   # ideal camera px -> metres
c_lens = {"perspective": {"H": H_c2m}, "lens": LENS, "lens_size": (CW, CH), "ppm": 1.0, "axis_deg": 0.0}
c_none = {"perspective": {"H": H_c2m}, "lens": None, "lens_size": None, "ppm": 1.0, "axis_deg": 0.0}
ground = np.array([[12.0, 10.0], [30.0, 20.0], [45.0, 30.0], [8.0, 33.0]])                   # metres
cam_ideal = cv2.perspectiveTransform(ground.reshape(-1, 1, 2) * 20.0, h_ground_to_cam).reshape(-1, 2)
cam_rec = m.lens_distort(cam_ideal, (CW, CH), LENS)
err_lens = np.abs(app._run3_to_metric(cam_rec, c_lens) - ground).max()
err_none = np.abs(app._run3_to_metric(cam_rec, c_none) - ground).max()
check("with the lens the recorded points land on the right metres", err_lens < 0.01, f"{err_lens:.4f} m")
check("without the lens the same points are far off", err_none > 0.5, f"{err_none:.2f} m")
check("metres -> camera pixels undoes pixels -> metres (lens + homography)", np.allclose(app._run3_from_metric(app._run3_to_metric(cam_rec, c_lens), c_lens), cam_rec, atol=1e-5))
c_ppm = {"perspective": None, "lens": LENS, "lens_size": (CW, CH), "ppm": 40.0, "axis_deg": 12.0}
check("the inverse also works for PPM-only calibration", np.allclose(app._run3_from_metric(app._run3_to_metric(cam_rec, c_ppm), c_ppm), cam_rec, atol=1e-5))

# ---- the four clicked corners of the Perspective calibration are straightened too
app._lens_size_override = (CW, CH)
rect = np.array([[10.0, 8.0], [20.0, 8.0], [20.0, 14.0], [10.0, 14.0]])                       # a 10 m x 6 m rectangle on the ground
corners_rec = m.lens_distort(cv2.perspectiveTransform(rect.reshape(-1, 1, 2) * 20.0, h_ground_to_cam).reshape(-1, 2), (CW, CH), LENS)
app.run3_perspective_enabled_var.set(True)
for var, pt in zip((app.run3_perspective_p1_var, app.run3_perspective_p2_var, app.run3_perspective_p3_var, app.run3_perspective_p4_var), corners_rec):
    var.set(f"{pt[0]:.3f},{pt[1]:.3f}")
for var, v in zip((app.run3_perspective_l12_var, app.run3_perspective_l23_var, app.run3_perspective_l34_var, app.run3_perspective_l41_var), ("10", "6", "10", "6")):
    var.set(v)
cfg = app._run3_snapshot_config()
mapped = app._run3_to_metric(corners_rec, cfg)
want = np.array([[0, 0], [10, 0], [10, 6], [0, 6]], float)
check("the clicked calibration corners become the true rectangle (lens included)", np.abs(mapped - want).max() < 0.02, f"max {np.abs(mapped - want).max():.4f} m")
app.clear_lens_values()
cfg_no = app._run3_snapshot_config()
mapped_no = app._run3_to_metric(corners_rec, cfg_no)
check("without the lens the same corners still map to the rectangle (the 4 points absorb it)", np.abs(mapped_no - want).max() < 0.05)
outer_ground = np.array([[30.0, 24.0], [4.0, 28.0], [40.0, 10.0], [25.0, 32.0]])         # well outside the clicked rectangle
outer_rec = m.lens_distort(cv2.perspectiveTransform(outer_ground.reshape(-1, 1, 2) * 20.0, h_ground_to_cam).reshape(-1, 2), (CW, CH), LENS)
outer_want = outer_ground - np.array([10.0, 8.0])
e_lens = np.abs(app._run3_to_metric(outer_rec, cfg) - outer_want).max()
e_none = np.abs(app._run3_to_metric(outer_rec, cfg_no) - outer_want).max()
check("away from the clicked rectangle the positions are right only with the lens", e_lens < 0.05 and e_none > 0.3, f"with {e_lens:.3f} m, without {e_none:.2f} m")

# ---- the Topview video: the empty road, lens corrected, laid flat
app.zones = {name: [] for name in m.ZONE_NAMES}
tr = {"1": []}
for k in range(30):
    pm = (12.0 + k * 0.9, 12.0 + k * 0.45)
    tr["1"].append({"frame": str(k + 1), "timestamp": f"{k / 10.0:.6f}", "class_name": "Car", "zone": "", "_timestamp": k / 10.0,
                    "_m": pm, "_mc": pm, "_point": None, "_center": None, "_zone_num": None})
base_cfg = {"ppm": 1.0, "axis_deg": 0.0, "lengths": {"Car": 4.5}, "widths": {"Car": 1.8}, "perspective": {"H": H_c2m}}
out_a = tempfile.mkdtemp(prefix="pk_tv_", dir=tmp)
vid_a = app._run3_write_topview_video(tr, dict(base_cfg, lens=LENS, lens_size=(CW, CH)), out_a, video)
cvs = m.topview_canvas([r["_m"] for r in tr["1"]], 1280, aspect=CW / CH)
Wf, Hf = cvs["w"], cvs["h"]
xs_, ys_ = np.meshgrid(np.arange(Wf, dtype=np.float64), np.arange(Hf, dtype=np.float64))
met = np.stack([xs_ / cvs["scale"] + cvs["xmin"], ys_ / cvs["scale"] + cvs["ymin"]], axis=-1)
expected = cv2.remap(tex, (met[..., 0] * 20.0).astype(np.float32), (met[..., 1] * 20.0).astype(np.float32), cv2.INTER_LINEAR)
cam_px = m.lens_distort(cv2.perspectiveTransform(met.reshape(-1, 1, 2) * 20.0, h_ground_to_cam).reshape(-1, 2), (CW, CH), LENS)
ideal_px = cv2.perspectiveTransform(met.reshape(-1, 1, 2) * 20.0, h_ground_to_cam).reshape(-1, 2)
seen = ((cam_px[:, 0] > 5) & (cam_px[:, 0] < CW - 5) & (cam_px[:, 1] > 5) & (cam_px[:, 1] < CH - 5)
        & (ideal_px[:, 0] > 5) & (ideal_px[:, 0] < CW - 5) & (ideal_px[:, 1] > 5) & (ideal_px[:, 1] < CH - 5)).reshape(Hf, Wf)
inside = (met[..., 0] * 20 > 5) & (met[..., 0] * 20 < 1195) & (met[..., 1] * 20 > 5) & (met[..., 1] * 20 < 795)
path = m.topview_px(cvs, np.array([r["_m"] for r in tr["1"]]))
near = np.zeros((Hf, Wf), bool)
for q in path[::3]:
    near |= np.hypot(xs_ - q[0], ys_ - q[1]) < 1.5 * cvs["scale"]                              # the area around the vehicle path stays visible (the rest is blanked)
car = m.topview_px(cvs, [tr["1"][14]["_m"]])[0]
valid = seen & inside & near & (np.hypot(xs_ - car[0], ys_ - car[1]) > 90) & (ys_ > 30)


def ncc_of(video_path, frame_index=14):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, fr = cap.read()
    cap.release()
    g1 = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float64)[valid]
    g2 = cv2.cvtColor(expected, cv2.COLOR_BGR2GRAY).astype(np.float64)[valid]
    g1, g2 = g1 - g1.mean(), g2 - g2.mean()
    return float((g1 * g2).sum() / np.sqrt((g1 ** 2).sum() * (g2 ** 2).sum() + 1e-9))


ncc_a = ncc_of(vid_a)
if os.environ.get("PK_DEBUG_SAVE"):
    cap_ = cv2.VideoCapture(vid_a); cap_.set(cv2.CAP_PROP_POS_FRAMES, 14); ok_, fr_ = cap_.read(); cap_.release()
    vis = np.hstack([fr_, expected, np.repeat((valid * 255).astype(np.uint8)[..., None], 3, axis=2)])
    cv2.imwrite(os.environ["PK_DEBUG_SAVE"], vis)
check("the Topview road matches the real ground seen from above", ncc_a > 0.80, f"NCC {ncc_a:.3f}, valid pixels {int(valid.sum())}")

# ---- the vehicle's own picture is placed on its footprint (the Topview looks like the normal video, from above)
import copy
tr_bb = copy.deepcopy(tr)
for r in tr_bb["1"]:
    r.update({"bbox_x1": "300", "bbox_y1": "200", "bbox_x2": "420", "bbox_y2": "280"})
vid_bb = app._run3_write_topview_video(tr_bb, dict(base_cfg, lens=LENS, lens_size=(CW, CH)), tempfile.mkdtemp(prefix="pk_tv_", dir=tmp), video)


def frame_of(path, idx=14):
    cap_ = cv2.VideoCapture(path)
    cap_.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok_, f_ = cap_.read()
    cap_.release()
    return f_.astype(np.int16)


diff = np.abs(frame_of(vid_bb) - frame_of(vid_a)).sum(axis=2)
off = {f"show_label_{n}": False for n in ("id", "class", "conf", "zone", "speed")}
vid_off = app._run3_write_topview_video(tr_bb, dict(base_cfg, lens=LENS, lens_size=(CW, CH)), tempfile.mkdtemp(prefix="pk_tv_", dir=tmp), video, display=dict(off, draw_trail=False))
vid_id = app._run3_write_topview_video(tr_bb, dict(base_cfg, lens=LENS, lens_size=(CW, CH)), tempfile.mkdtemp(prefix="pk_tv_", dir=tmp), video, display=dict(off, show_label_id=True, show_prefix_id=True, draw_trail=True, trail_length=10))
d_lab = np.abs(frame_of(vid_id) - frame_of(vid_off)).sum(axis=2)
check("the labels and the trajectory of the Topview follow the display settings", int((d_lab > 60).sum()) > 100, f"{int((d_lab > 60).sum())} pixels differ")
check("with every label off nothing but the point is drawn on the vehicle (no box, no text)", int((np.abs(frame_of(vid_off) - frame_of(vid_bb)).sum(axis=2) > 60).sum()) > 0)
# ---- map-style Topview: empty grid + road lines clicked on the camera picture
def to_rec(gm):
    return m.lens_distort(cv2.perspectiveTransform(np.asarray(gm, float).reshape(-1, 1, 2) * 20.0, h_ground_to_cam).reshape(-1, 2), (CW, CH), LENS)


road_ground = [np.array([[14.0, 14.0], [36.0, 14.0]]), np.array([[14.0, 18.0], [36.0, 18.0]])]    # two straight road edges, 4 m apart
dlg = m.RoadLineDialog(app, video, app.set_road_lines)
for k_, g_ in enumerate(road_ground):
    for pt_ in to_rec(g_):                                   # only the two end points are clicked: the road is straight
        dlg.add_point(*pt_)
    if k_ == 0:
        dlg.new_line()
check("the road line tool keeps the clicked lines", len([l for l in dlg.lines if len(l) >= 2]) == 2)
check("the road lines are applied and read back", dlg.apply() and len(app.get_road_lines()) == 2)
cfg_map = dict(base_cfg, lens=LENS, lens_size=(CW, CH), topview_map=True, road_lines=app.get_road_lines())
vid_map = app._run3_write_topview_video(tr, cfg_map, tempfile.mkdtemp(prefix="pk_tv_", dir=tmp), video)
fm = frame_of(vid_map).astype(np.uint8)
hit = []
for g_ in road_ground:
    for fr_ in (0.2, 0.5, 0.8):                              # points along the real road edge, between the two clicks
        pxm = m.topview_px(cvs, [g_[0] + (g_[1] - g_[0]) * fr_])[0]
        x_, y_ = int(round(pxm[0])), int(round(pxm[1]))
        if np.hypot(x_ - car[0], y_ - car[1]) < 120:         # the vehicle and its label are drawn over the line there
            continue
        hit.append(fm[max(0, y_ - 2):y_ + 3, max(0, x_ - 2):x_ + 3].mean(axis=(0, 1)).min() > 150)
check("the road lines land on the right metres (even bent by the lens between the clicks)", all(hit), f"{sum(hit)}/{len(hit)}")
check("the map-style Topview has no camera photo (plain background away from the lines)", float(np.abs(fm[5:25, 5:60].astype(float) - 38).mean()) < 40)

check("the Topview has the video's shape", abs(Wf / Hf - CW / CH) < 0.02, f"{Wf}x{Hf}")
check("the vehicle picture is pasted at its footprint (and only there)", int((diff > 60).sum()) > 500 and int((np.hypot(xs_ - car[0], ys_ - car[1]) > 250)[diff > 60].sum()) == 0, f"{int((diff > 60).sum())} changed pixels")
vid_b = app._run3_write_topview_video(tr, dict(base_cfg, lens=None, lens_size=None), tempfile.mkdtemp(prefix="pk_tv_", dir=tmp), video)
ncc_b = ncc_of(vid_b)
check("without the lens correction the road stays curved (clearly worse)", ncc_b < ncc_a - 0.08, f"with {ncc_a:.3f}, without {ncc_b:.3f}")
cap = cv2.VideoCapture(vid_a)
check("the video plays as long as the analysed part", abs(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) - 3.0) < 0.3)
cap.release()

root.destroy()
print("ALL OK" if not failures else "FAILED: " + ", ".join(failures))
sys.exit(1 if failures else 0)
