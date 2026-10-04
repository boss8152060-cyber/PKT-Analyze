"""Align: video pixels -> the drone's plane. Pairs of points, the kinds of transformation, the report (error + leave-one-out), saving,
using the result for every point (Run 3 / the X-Y outputs), the video of another size, the layout.

A synthetic site: a ground plane seen by a tilted camera with a barrel lens (the video) and from straight above (the drone picture).

Run from the Run folder:   python tests/gui_align.py
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


tmp = tempfile.mkdtemp(prefix="pk_align_")
CW, CH = 1280, 720
H_CAM = cv2.getPerspectiveTransform(np.float32([(0, 0), (60, 0), (60, 20), (0, 20)]), np.float32([(100, 330), (1200, 280), (1260, 600), (40, 630)]))
K1 = 0.22                                                    # the radial trend of the lens


def video_px(g):
    """Ground metres -> video pixels: the tilted camera, then the barrel lens."""
    q = cv2.perspectiveTransform(np.asarray(g, float).reshape(-1, 1, 2), H_CAM).reshape(-1, 2)
    c = np.array([CW / 2.0, CH / 2.0])
    x = (q - c) / (CW / 2.0)
    ru = np.sqrt((x ** 2).sum(1))
    rd = ru.copy()
    for _ in range(60):
        rd = np.maximum(rd - (rd * (1 + K1 * rd ** 2) - ru) / (1 + 3 * K1 * rd ** 2), 0)
    sc = np.where(ru > 1e-12, rd / np.where(ru > 1e-12, ru, 1.0), 1.0)
    return x * sc[:, None] * (CW / 2.0) + c


DRONE_PPM = 20.0                                             # drone picture: 20 px per metre, origin (60, 80)


def drone_px(g):
    return np.asarray(g, float) * DRONE_PPM + [60.0, 80.0]


video = os.path.join(tmp, "clip.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(5):
    vw.write(np.full((CH, CW, 3), 90, np.uint8))
vw.release()
drone_file = os.path.join(tmp, "ภาพโดรน.png")                 # Thai letters in the name
ok, buf = cv2.imencode(".png", np.full((560, 1400, 3), 120, np.uint8))
buf.tofile(drone_file)

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
m.messagebox.showinfo = lambda *a, **k: None
m.messagebox.showerror = lambda *a, **k: None
m.simpledialog.askfloat = lambda *a, **k: 10.0
app.video_var.set("")
check("without a video the window refuses to open", app.open_align() is None)
app.video_var.set(video)
dlg = app.open_align()
root.update()
check("the window opens on a frame of the video", dlg is not None and dlg.video_img is not None and dlg.video_img.shape[:2] == (CH, CW))
check("a picture file with Thai letters in its name opens", dlg.load_drone(drone_file) and dlg.drone_img is not None)

# 20 pairs on the ground (road markings): 5 x 4 grid
gx, gy = np.linspace(4, 56, 5), np.linspace(3, 17, 4)
ground = np.array([(a, b) for a in gx for b in gy])
for g, v, d in zip(ground, video_px(ground), drone_px(ground)):
    dlg.add_pair(v, d)
check("20 pairs are collected", len(dlg.pairs) == 20)
check("with too few pairs a kind says so", "error" in m.transform_report("poly3", np.zeros((3, 2)), np.zeros((3, 2)), (CW, CH)))
dlg.set_scale_from_points((100, 100), (300, 100), 10.0)                                   # 200 drone px = 10 m
check("the scale is 0.05 m per drone pixel", abs(dlg.scale - 0.05) < 1e-9, f"{dlg.scale}")
reports = {}
for kind in ("helmert", "affine", "projective", "lens", "poly2", "poly3", "tps"):
    dlg.set_kind(kind)
    reports[kind] = dlg.report
check("every kind can be fitted with 20 pairs", all("error" not in r for r in reports.values()))
check("a flat transformation (projective) cannot follow the bent video, the lens kind can",
      reports["projective"]["rms_u"] > 0.10 and reports["lens"]["rms_u"] < 0.05, f"projective {reports['projective']['rms_u']:.3f} m, lens {reports['lens']['rms_u']:.3f} m")
check("the rubber sheet is exact at the pairs but its leave-one-out error shows the honest accuracy",
      reports["tps"]["rms_u"] < 0.02 and reports["tps"]["loo_rms_u"] > 3 * reports["tps"]["rms_u"], f"{reports['tps']['rms_u']:.4f} / {reports['tps']['loo_rms_u']:.3f}")
check("the report compares every kind", len(dlg.report["compare"]) == 7)
dlg.set_kind("lens")
root.update()
check("the table lists a row per pair", len(dlg.tree.get_children()) == 20)
check("the picture panes draw the pairs", dlg.vpane.last_render is not None and (dlg.vpane.last_render != dlg.vpane.last_render[0, 0]).any())
dlg.pending = (500.0, 400.0)
dlg.click_drone(100.0, 100.0)
check("a pending video click is completed by a drone click", len(dlg.pairs) == 21 and dlg.pending is None)
dlg.delete_pair(20)
check("a pair can be deleted", len(dlg.pairs) == 20)
bad_s = (700.0, 450.0)
dlg.add_pair(bad_s, tuple(np.array(drone_px(np.array([[20.0, 8.0]]))[0]) + [90.0, 60.0]))                       # a pair clicked 90/60 px away from where it should be
w = dlg.worst_pairs(3)
check("the worst pair is the badly clicked one", w and w[0][0] == "#21", str(w))
first_row = dlg.tree.item(dlg.tree.get_children()[0], "values")
check("the table lists the worst pair first and marks it red", first_row[0] == "#21" and "bad" in dlg.tree.item(dlg.tree.get_children()[0], "tags"), str(first_row))
check("the report names the worst pairs", "คู่ที่คลาดสูงสุด: #21" in dlg.report_text.get("1.0", "end"))
check("delete worst removes it", dlg.delete_worst() and len(dlg.pairs) == 20)
check("applying saves and switches Align on", dlg.apply() is True and app.run3_align_enabled_var.get() and "lens" in app.run3_align_var.get())
cfg = app._run3_snapshot_config()
check("Run 3 gets the Align config", cfg["align"] is not None and cfg["align"]["kind"] == "lens" and app._run3_calibration_mode(cfg) == "Align_lens")
test_g = np.array([[10.0, 8.0], [30.0, 12.0], [55.0, 15.0], [3.0, 18.0], [58.0, 4.0]])
origin = ground[0]
got = app._run3_to_metric(video_px(test_g), cfg)
err = np.abs(got - (test_g - origin)).max()
check("every point of the video lands on its true metre (x right, y down, origin = the first pair)", err < 0.15, f"{err:.3f} m")
check("the status line says what is used", "pair" in app._align_status_text() or "คู่" in app._align_status_text(), app._align_status_text())

# the plane can be turned: the main road along the drone picture's +y
dlg2 = app.open_align()
root.update()
check("the saved pairs and kind come back when the window opens again", len(dlg2.pairs) == 20 and dlg2.kind == "lens" and abs(dlg2.scale - 0.05) < 1e-9)
dlg2.set_road_direction((0, 0), (0, 100))                                                  # the road runs DOWN the drone picture
check("choosing the road direction turns the plane by 90 degrees", abs(dlg2.rot_deg - 90.0) < 1e-6)
dlg2.close()

saved = app.get_settings()
app2 = m.Run1App(tk.Toplevel(root))
app2.video_var.set(video)
app2.set_settings(saved)
check("the alignment survives saving and loading the settings", app2.run3_align_enabled_var.get() and app2.run3_align_var.get() == app.run3_align_var.get())
cfg2 = app2._run3_snapshot_config()
check("and gives the same metres", np.abs(app2._run3_to_metric(video_px(test_g), cfg2) - got).max() < 1e-9)

# a video of another size: the video points are scaled
app._actual_video_size = lambda: (CW * 2, CH * 2)
app._align_cache = None
cfg3 = app._run3_snapshot_config()
check("a video of twice the size gives the same metres for the doubled pixels", np.abs(app._run3_to_metric(video_px(test_g) * 2, cfg3) - got).max() < 0.05)
del app._actual_video_size
app._align_cache = None

# the X-Y outputs use the same metres
app.zones = {name: [] for name in m.ZONE_NAMES}
app.zones["Zone 1"] = [tuple(float(v) for v in q) for q in video_px([(10, 5), (30, 5), (30, 12), (10, 12)])]
tracks = {1: [{"frame": str(k + 1), "timestamp": f"{k / 10:.6f}", "_timestamp": k / 10.0, "class_name": "Car", "zone": "Zone 1", "confidence": "0.9",
               "_m": tuple(app._run3_to_metric(video_px([(12 + k, 8)]), cfg)[0])} for k in range(20)]}
png = app._run3_write_xy_plot(tracks, cfg, tempfile.mkdtemp(dir=tmp), video, display={})
check("the X-Y picture is written with the Align result", png is not None and os.path.isfile(png))

# an Align that is ticked but empty is an error at validation
app3 = m.Run1App(tk.Toplevel(root))
app3.video_var.set(video)
app3.run3_align_enabled_var.set(True)
try:
    app3._run3_align_cfg(silent=False)
    raised = False
except ValueError:
    raised = True
check("ticked without pairs: an error that says so", raised and app3._run3_align_cfg(silent=True) is None)


# ---- reference lines (N points in the video, head + tail in the drone picture) and the X-Y axes ----
dlg5 = app.open_align()
root.update()
dlg5.pairs, dlg5.lines, dlg5.axes = [], [], None
dlg5.set_kind("lens")
dlg5.scale_var.set("0.05")
dlg5.set_axes(video_px([(5, 3), (55, 3), (5, 17)]), drone_px([(5, 3), (55, 3), (5, 17)]))
check("the X-Y axes are set", dlg5.axes is not None and len(dlg5.axes["vid"]) == 3)
dlg5.mode_var.set("line")
dlg5.line_n_var.set("4")
g0, g1 = np.array([8.0, 6.0]), np.array([52.0, 6.0])
for t_ in np.linspace(0, 1, 4):
    gg = g0 * (1 - t_) + g1 * t_
    dlg5.click_video(*video_px([gg])[0])
check("N video points are collected for a reference line", len(dlg5.line_vid) == 4)
dlg5.click_video(1.0, 1.0)
check("more video points than asked are refused (and the message says so)", len(dlg5.line_vid) == 4 and "ครบ 4" in dlg5.msg_var.get())
dlg5.click_drone(*drone_px([g0])[0])
dlg5.click_drone(*drone_px([g1])[0])
check("head and tail in the drone picture complete the reference line", len(dlg5.lines) == 1 and dlg5.line_vid == [] and len(dlg5.lines[0]["pts"]) == 4)
for (a0, a1) in (((8, 12), (52, 12)), ((8, 16), (52, 16)), ((12, 3), (12, 17)), ((30, 3), (30, 17)), ((50, 3), (50, 17))):
    pts_v = [video_px([np.array(a0) * (1 - t_) + np.array(a1) * t_])[0] for t_ in np.linspace(0, 1, 6)]
    dlg5.add_line(pts_v, drone_px([a0])[0], drone_px([a1])[0])
check("six reference lines", len(dlg5.lines) == 6)
rep5 = dlg5.compute()
check("lines + axes alone (no clicked pairs) fit the bent video with the lens kind", "error" not in rep5 and rep5["rms_u"] < 0.05, f"{rep5.get('rms_u')}")
lr = rep5["lines"][0]
check("a reference line along the X axis makes ~0 degrees with it and crosses the Y axis at y = 3 m",
      abs(lr["angle_video_deg"]) < 0.5 and abs(lr["angle_drone_deg"]) < 1e-6 and abs(lr["y_cross_drone_m"] - 3.0) < 1e-6 and abs(lr["y_cross_video_m"] - 3.0) < 0.1, str(lr))
check("the report text names the crossings", "ตัดแกน X ที่" in dlg5.report_text.get("1.0", "end") or "ตัดแกน Y ที่" in dlg5.report_text.get("1.0", "end"))
check("the table has the axes and the line ends", any(v.startswith("แกน") for v in [dlg5.tree.item(i, "values")[0] for i in dlg5.tree.get_children()]) and any(v.startswith("L1") for v in [dlg5.tree.item(i, "values")[0] for i in dlg5.tree.get_children()]))
check("applying works and the output frame is the axes' frame", dlg5.apply() is True)
cfg5 = app._run3_snapshot_config()
test5 = np.array([[10.0, 8.0], [33.0, 12.0], [50.0, 15.0], [6.0, 5.0]])
got5 = app._run3_to_metric(video_px(test5), cfg5)
err5 = np.abs(got5 - (test5 - np.array([5.0, 3.0]))).max()
check("positions are measured from the axes' origin along the X axis", err5 < 0.15, f"{err5:.3f} m")
saved5 = app.get_settings()
app5 = m.Run1App(tk.Toplevel(root))
app5.video_var.set(video)
app5.set_settings(saved5)
cfg5b = app5._run3_snapshot_config()
check("lines and axes survive saving and loading", np.abs(app5._run3_to_metric(video_px(test5), cfg5b) - got5).max() < 1e-9 and "แกน" in app5._align_status_text())
app._actual_video_size = lambda: (CW * 2, CH * 2)
app._align_cache = None
cfg5c = app._run3_snapshot_config()
check("a video of twice the size: lines and axes are scaled too", np.abs(app._run3_to_metric(video_px(test5) * 2, cfg5c) - got5).max() < 0.08)
del app._actual_video_size
app._align_cache = None
dlg5.close() if dlg5.top.winfo_exists() else None

def overlaps(container):
    cells, bad = {}, []
    for child in container.winfo_children():
        try:
            if child.winfo_manager() != "grid":
                continue
            gi = child.grid_info()
        except tk.TclError:
            continue
        r, c = int(gi["row"]), int(gi["column"])
        for rr in range(r, r + int(gi.get("rowspan", 1))):
            for cc in range(c, c + int(gi.get("columnspan", 1))):
                if (rr, cc) in cells:
                    bad.append(f"{child.winfo_class()} at {rr},{cc}")
                cells[(rr, cc)] = child
    for ch in container.winfo_children():
        bad.extend(overlaps(ch))
    return bad


dlg4 = app.open_align()
root.update()
check("the Align window: no two widgets share a grid cell", not overlaps(dlg4.top), "; ".join(overlaps(dlg4.top)[:3]))
dlg4.close()
root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
