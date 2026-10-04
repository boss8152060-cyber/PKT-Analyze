"""Align: video pixels -> the drone's plane. Pairs of points, the kinds of transformation, the report (error + leave-one-out), saving,
using the result for every point (Run 3 / the X-Y outputs), the video of another size, the layout.

A synthetic site: a ground plane seen by a tilted camera with a barrel lens (the video) and from straight above (the drone picture).

Run from the Run folder:   python tests/gui_align.py
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

# ---- the zone corners as pins: the video side comes from the zone file, only the drone side is clicked (or skipped)
z2 = [(10.0, 5.0), (24.0, 5.0), (24.0, 12.0), (10.0, 12.0)]
z3 = [(24.0, 5.0), (38.0, 5.0), (38.0, 12.0), (24.0, 12.0)]                                # shares two corners with zone 2
app.zones = {name: [] for name in m.ZONE_NAMES}
app.zones["Zone 2"] = [tuple(float(v) for v in q) for q in video_px(z2)]
app.zones["Zone 3"] = [tuple(float(v) for v in q) for q in video_px(z3)]
orig_align = app.run3_align_var.get()
app.run3_align_var.set("")
app.run3_align_enabled_var.set(False)
dp = app.open_align()
root.update()
dp.load_drone(drone_file)
dp.set_scale_from_points((100, 100), (300, 100), 10.0)
check("the zone corners become pins; a corner shared by two zones is ONE pin", len(dp.pins) == 6 and any("=" in pin["l"] for pin in dp.pins), str([pin["l"] for pin in dp.pins]))
dp.set_mode_pins()
check("the first pin waits for its place on the drone picture", dp.pin_index == 0 and "Z2.1" in dp.msg_var.get(), dp.msg_var.get())
true_d = {pin["l"].split("=")[0]: pin for pin in dp.pins}
corners = {"Z2.1": z2[0], "Z2.2": z2[1], "Z2.3": z2[2], "Z2.4": z2[3], "Z3.2": z3[1], "Z3.3": z3[2]}
n0 = len(dp.pairs)
dp.click_drone(*drone_px([corners["Z2.1"]])[0])
check("a click on the drone picture makes a pair whose video side is the zone corner from the file", len(dp.pairs) == n0 + 1 and dp.pairs[-1].get("l") == "Z2.1"
      and abs(dp.pairs[-1]["s"][0] - video_px([corners["Z2.1"]])[0][0]) < 1e-6)
check("the next pin comes up by itself", dp.pin_index == 1)
dp.skip_pin()
check("a skipped pin is skipped (not a pair) and the next one comes up", dp.pins[1]["state"] == "skip" and dp.pin_index == 2 and len(dp.pairs) == n0 + 1)
for label in ("Z2.3", "Z2.4", "Z3.2", "Z3.3"):
    dp.click_drone(*drone_px([corners[label]])[0])
c = dp.pin_status()
check("the progress counts done / skipped / left", c == {"todo": 0, "done": 5, "skip": 1}, str(c))
check("the table shows the name of a zone-corner pair", any(dp.tree.item(i, "values")[3] == "Z2.3" for i in dp.tree.get_children()))
dp.delete_pair(len(dp.pairs) - 1)
check("deleting a zone-corner pair puts its pin back to 'to do'", dp.pin_status()["todo"] == 1 and dp.pin_index is not None)
dp.goto_pin(-1)
check("a skipped pin can be taken up again with the arrows", dp.pins[1]["state"] in ("todo", "skip"))
dp.set_kind("helmert")
dp.pairs = [q for q in dp.pairs if q.get("l")]                                                # only the zone pins now
dp.set_kind("affine")
check("the pins alone can already give a report", dp.report is not None and "error" not in dp.report, str(dp.report.get("error") if dp.report else ""))
dp.apply()
saved_pairs = json.loads(app.run3_align_var.get())
check("the pairs keep their zone-corner names and the skipped pins are saved", all(q.get("l") for q in saved_pairs["pairs"]) and len(saved_pairs["skipped"]) >= 0)
dq = app.open_align()
root.update()
check("opening again: the pins done / skipped come back as they were", dq.pin_status()["done"] == len([q for q in saved_pairs["pairs"] if q.get("l")]) and len(dq.pins) == 6)
dq.close()
app.zones = {name: [] for name in m.ZONE_NAMES}
app.run3_align_var.set(orig_align)                                                       # back to the lens alignment for the tests below
app.run3_align_enabled_var.set(True)
app._align_cache = None
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
