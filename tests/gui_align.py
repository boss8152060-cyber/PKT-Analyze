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
# a badly clicked pair: the table puts it first (red), the worst-pair button removes it
dlg.add_pair(video_px([[30.0, 10.0]])[0] + [70.0, -45.0], drone_px([[30.0, 10.0]])[0])
root.update()
first_row = dlg.tree.item(dlg.tree.get_children()[0], "values")
check("the table is sorted: the badly clicked pair is on top and marked red", int(first_row[0]) == 21 and "bad" in dlg.tree.item(dlg.tree.get_children()[0], "tags"), str(first_row))
check("the report names the doubtful pairs", "#21" in dlg.report_text.get("1.0", "end"))
dlg.tree.selection_set(dlg.tree.get_children()[0])
root.update()
check("choosing a row marks that pair in both pictures", dlg.selected == 20)
check("the worst-pair button finds and removes it", dlg.worst_index() == 20 and dlg.delete_worst() and len(dlg.pairs) == 20 and dlg.selected is None)
dlg.mode_var.set("measure")
dlg.click_drone(100.0, 100.0)
dlg.click_drone(300.0, 100.0)
check("the test measurement on the drone picture shows the metres (200 drone px at 0.05 m = 10 m)", "10.00" in dlg.msg_var.get(), dlg.msg_var.get())
dlg.mode_var.set("pairs")
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

# ---- zones: the corners drawn on the video appear as pins; the place they SHOULD have is clicked on the drone picture ----
import json
zone_src = os.path.join(tmp, "zones.json")
true_rects = {"Zone 2": [(6, 6), (18, 6), (18, 12), (6, 12)], "Zone 3": [(18, 6), (34, 6), (34, 12), (18, 12)]}
rng = np.random.default_rng(5)
zones_json = {"video_path": video, "frame_width": CW, "frame_height": CH, "lines": {}, "zones": []}
for name, g in true_rects.items():
    drawn = video_px(g) + rng.normal(0, 14, (4, 2))                                          # the corners were drawn a little off the lane edges
    zones_json["zones"].append({"name": name, "id": f"z_{name[-1]}", "points": [[int(round(a)), int(round(b))] for a, b in drawn], "color_bgr": [0, 200, 0], "show_label": True})
with open(zone_src, "w", encoding="utf-8") as f:
    json.dump(zones_json, f)
app.zone_line_config_var.set(zone_src)
app.load_pkstudio_zones()
zd = app.open_align()
root.update()
check("the corners of the drawn zones are the pins", [p_["label"] for p_ in zd.zone_pins] == ["Z2.1", "Z2.2", "Z2.3", "Z2.4", "Z3.1", "Z3.2", "Z3.3", "Z3.4"])
zd.mode_var.set("zones")
zd.select_pin(0)
root.update()
check("the zone mode draws the pins on both pictures", zd.vpane.last_render is not None and zd.dpane.last_render is not None and len(zd._pred) == 8)
check("no zone can be saved before every corner has a place", zd.save_zones() is None)
order = [(n, k) for n in true_rects for k in range(4)]
for n, k in order:
    zd.click_drone(*drone_px([true_rects[n][k]])[0])                                         # the pins are placed in order, each click moves on
check("the pins advance by themselves and all eight are placed", all(p_["target"] for p_ in zd.zone_pins) and zd._pin_text(0).startswith("✓"))
orig_text = open(zone_src, encoding="utf-8").read()
newp = zd.new_zone_polygons()
check("both zones get a new video polygon with extra points on the edges", set(newp) == {"Zone 2", "Zone 3"} and all(len(v) == 16 for v in newp.values()), str({k: len(v) for k, v in newp.items()}))
cfg_z = app._run3_snapshot_config()
for name, g in true_rects.items():
    mm = app._run3_to_metric(np.array(newp[name]), cfg_z)
    xs_ = mm[:, 0]
    ys_ = mm[:, 1]
    w_, h_ = float(np.ptp(xs_)), float(np.ptp(ys_))
    want_w, want_h = g[1][0] - g[0][0], g[2][1] - g[1][1]
    check(f"{name}: the new polygon is the rectangle on the road ({want_w:g} x {want_h:g} m)", abs(w_ - want_w) < 0.25 and abs(h_ - want_h) < 0.25, f"{w_:.2f} x {h_:.2f}")
old_poly = np.array(app.zones["Zone 2"], float)
mo = app._run3_to_metric(old_poly, cfg_z)
check("the zone as it was drawn is NOT a clean rectangle (that was the problem)", float(np.ptp(mo[:, 0])) > 12.3 or float(np.ptp(mo[:, 1])) > 6.3 or abs(mo[1, 1] - mo[0, 1]) > 0.3)
path = zd.save_zones()
check("a NEW zone file is written next to the old one and loaded", path is not None and path.endswith("_aligned.json") and os.path.isfile(path) and app.zone_line_config_var.get() == path)
check("the original zone file is untouched", open(zone_src, encoding="utf-8").read() == orig_text)
saved_z = json.load(open(path, encoding="utf-8"))
check("the new file keeps the format (names, points, points_norm, area, frame size)", [z["name"] for z in saved_z["zones"]] == ["Zone 2", "Zone 3"] and len(saved_z["zones"][0]["points"]) == 16
      and len(saved_z["zones"][0]["points_norm"]) == 16 and saved_z["zones"][0]["area_px"] > 0 and saved_z["frame_width"] == CW)
check("the program now uses the new zones", len(app.zones["Zone 2"]) == 16 and len(app.zones["Zone 3"]) == 16)
n_before = len(zd._all_pairs())
zd.zone_gcp_var.set(True)
root.update()
check("ticking 'use the placed pins as control points' adds them to the fit", len(zd._all_pairs()) == n_before + 8 and "error" not in zd.report)
zd.zone_gcp_var.set(False)
zd.clear_pins()
check("clearing the pins starts again", not any(p_["target"] for p_ in zd.zone_pins))
zd.close()

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
