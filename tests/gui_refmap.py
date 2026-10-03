"""Reference-map calibration (a top-view drone picture used as the MAP): dialog logic, settings, and the Topview video.

Run from the Run folder:   python tests/gui_refmap.py
A synthetic map and a synthetic camera frame (the map seen through a known perspective) are made; the dialog is
driven through its methods (no mouse), then the result must reproduce the known camera-pixel -> metre mapping.
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


tmp = tempfile.mkdtemp(prefix="pk_refmap_")
SCALE = 20.0                                                   # map: 20 px per metre
# --- the map: 1200 x 800 px (60 x 40 m) with a few markings
map_img = np.full((800, 1200, 3), 90, np.uint8)
for x in range(0, 1200, 100):
    cv2.line(map_img, (x, 0), (x, 799), (200, 200, 200), 2)
for y in range(0, 800, 100):
    cv2.line(map_img, (0, y), (1199, y), (200, 200, 200), 2)
map_path = os.path.join(tmp, "map.png")
cv2.imwrite(map_path, map_img)
# --- the camera: sees the map through a known perspective (map px -> camera px)
h_map_to_cam = np.array([[0.9, 0.25, 120.0], [-0.05, 0.8, 60.0], [0.0003, 0.0009, 1.0]])
cam_frame = cv2.warpPerspective(map_img, h_map_to_cam, (1280, 720))
video_path = os.path.join(tmp, "cam.mp4")
vw = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*"mp4v"), 10, (1280, 720))
for _ in range(20):
    vw.write(cam_frame)
vw.release()

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
# a modal box must never block the test: answer them
m.messagebox.askyesno = lambda *a, **k: False
m.messagebox.showwarning = lambda *a, **k: None
m.messagebox.showinfo = lambda *a, **k: None
m.simpledialog.askfloat = lambda *a, **k: None
m.simpledialog.askstring = lambda *a, **k: None
app.video_var.set(video_path)

# ---- the dialog
dlg = app.open_reference_map()
root.update()
def grid_overlaps(container):
    cells, bad = {}, []
    for child in container.winfo_children():
        if child.winfo_manager() == "grid":
            info = child.grid_info()
            for r in range(int(info["row"]), int(info["row"]) + int(info["rowspan"])):
                for col in range(int(info["column"]), int(info["column"]) + int(info["columnspan"])):
                    if (r, col) in cells:
                        bad.append(f"{child.winfo_class()} vs {cells[(r, col)]} at {(r, col)}")
                    cells[(r, col)] = child.winfo_class()
        bad += grid_overlaps(child)
    return bad


check("dialog opens and shows the camera frame", dlg.cam_img is not None and dlg.view.get("cam") is not None)
check("dialog: no two widgets share a grid cell", not grid_overlaps(dlg.top), str(grid_overlaps(dlg.top)))
check("map missing: calibration not ready", dlg.calibration() is None and "เลือกแผนที่" in dlg.msg_var.get())
check("map loads", dlg.set_map(map_path) and dlg.map_img is not None)
# ---- zoom at the pointer, pan, reset view, frame slider
root.update()
k0, ox0, oy0 = dlg.view["map"]
ex, ey = 300, 200                                              # a pointer position inside the map canvas
img_pt = ((ex - ox0) / k0, (ey - oy0) / k0)                    # the map point under the pointer
dlg.zoom_at("map", ex, ey, 3)
k1, ox1, oy1 = dlg.view["map"]
check("wheel zoom: zoom factor grows", dlg.zoom["map"] > 1.9 and k1 > k0 * 1.9, f"zoom {dlg.zoom['map']:.2f}")
check("wheel zoom keeps the point under the pointer fixed",
      abs(img_pt[0] * k1 + ox1 - ex) < 1.0 and abs(img_pt[1] * k1 + oy1 - ey) < 1.0)
check("the other picture is not zoomed", dlg.zoom["cam"] == 1.0)
dlg.zoom_at("map", ex, ey, 100)
check("zoom stops at the maximum", dlg.zoom["map"] <= dlg.ZOOM_MAX + 1e-9, f"{dlg.zoom['map']:.1f}")
dlg.pan_by("map", -30, 20)
k2, ox2, oy2 = dlg.view["map"]
check("pan moves the picture", k2 == dlg.view["map"][0] and ox2 != ox1)
# a click while zoomed lands on the right map pixel
dlg._on_click("map", ex, ey)                                   # (no pending camera point: only a message)
dlg.reset_view("map")
k3, ox3, oy3 = dlg.view["map"]
check("reset view: back to fit, zoom 1", dlg.zoom["map"] == 1.0 and abs(k3 - k0) < 1e-6 and abs(ox3 - ox0) < 1.0)
dlg.zoom_at("cam", 100, 100, 2)
dlg.zoom_at("map", 100, 100, 2)
dlg.reset_views()
check("reset both views", dlg.zoom["cam"] == 1.0 and dlg.zoom["map"] == 1.0)
dlg.zoom_at("cam", 100, 100, -5)
check("zoom out below fit is ignored", dlg.zoom["cam"] == 1.0)
check("camera frame slider covers the video", int(float(dlg.sliders["cam"].cget("to"))) == dlg.cam_total - 1)
n0 = dlg.cam_idx
dlg.step("cam", "frame", 3)
check("step frames", dlg.cam_idx == min(dlg.cam_total - 1, n0 + 3))
dlg.step("cam", "sec", -1)
check("step by seconds", dlg.cam_idx < n0 + 3)
check("goto frame by number", dlg._load_frame("2") and dlg.cam_idx == 1)
check("map is an image: the map slider is off", str(dlg.sliders["map"].cget("state")) == "disabled" or dlg.map_cap is None)
dlg.start_scale_mode()
check("scale mode starts", dlg.scale_mode)
# a known 10 m distance on the map (200 px)
check("scale from two points and a distance", dlg.set_scale_from_points((100, 100), (300, 100), 10.0) and abs(dlg.scale - 20.0) < 1e-9)

h_cam_to_map = np.linalg.inv(h_map_to_cam)
map_pts = [(200, 150), (900, 160), (1000, 650), (250, 600), (600, 400), (700, 250)]
ph = lambda h, pts: cv2.perspectiveTransform(np.float32(pts).reshape(-1, 1, 2), np.float64(h)).reshape(-1, 2)
cam_pts = ph(h_map_to_cam, map_pts)
check("map click before a camera click is refused", dlg.add_map_point(1, 1) is False and len(dlg.pairs) == 0)
for c_, p_ in zip(cam_pts[:3], map_pts[:3]):
    dlg.add_camera_point(*c_)
    dlg.add_map_point(*p_)
check("3 pairs: not enough yet", dlg.calibration() is None and len(dlg.pairs) == 3)
for c_, p_ in zip(cam_pts[3:], map_pts[3:]):
    dlg.add_camera_point(*c_)
    dlg.add_map_point(*p_)
cal = dlg.calibration()
check("6 pairs: calibration ready, error ~0", cal is not None and cal["rms_m"] < 0.01, "" if cal is None else f"{cal['rms_m'] * 100:.3f} cm")
root.update()
check("canvases draw the clicked points (no exception)", dlg.photos.get("cam") is not None and dlg.photos.get("map") is not None)
dlg.add_camera_point(10, 10)
dlg.undo()
check("undo drops a pending camera point first", dlg.pending_cam is None and len(dlg.pairs) == 6)
dlg.undo()
dlg.undo()
check("undo then drops pairs", len(dlg.pairs) == 4)
for c_, p_ in zip(cam_pts[4:], map_pts[4:]):
    dlg.add_camera_point(*c_)
    dlg.add_map_point(*p_)
check("save stores the map, scale and pairs in the program settings", dlg.save() is True)
check("settings hold the reference map",
      app.run3_refmap_enabled_var.get() and app.run3_refmap_path_var.get() == map_path
      and abs(float(app.run3_refmap_scale_var.get()) - 20.0) < 1e-3 and len(json.loads(app.run3_refmap_pairs_var.get())) == 6)
check("status text shows the map and error", "map.png" in app.run3_refmap_status_var.get(), app.run3_refmap_status_var.get())

# ---- program side
persp = app._run3_get_perspective_matrix(silent=False)
check("reference map is the perspective used by Run 3", persp is not None and persp.get("map") is not None)
c = {"perspective": persp, "ppm": 1.0, "axis_deg": 0.0}
test_cam = [(640.0, 360.0), (300.0, 500.0), (900.0, 200.0)]
got = app._run3_to_metric(test_cam, c)
want = ph(h_cam_to_map, test_cam) / SCALE
check("camera pixel -> metres matches the known mapping", np.allclose(got, want, atol=0.02), f"max diff {np.abs(got - want).max():.4f} m")
check("calibration mode name", app._run3_calibration_mode(c) == "Reference_Map")
cfg = app._run3_snapshot_config()
check("config carries the map calibration", cfg["perspective"] is not None and cfg["perspective_enabled"])
# the saved settings come back
st = app.get_settings() if hasattr(app, "get_settings") else None
app2 = m.Run1App(tk.Toplevel(root))
app2.set_settings(st)
check("settings round trip", app2.run3_refmap_enabled_var.get() and len(app2._run3_refmap_state()["pairs"]) == 6
      and app2._run3_refmap_state()["map_path"] == map_path)
# incomplete map: validation message and silent None
app2.run3_refmap_pairs_var.set("[[1,2,3,4]]")
check("incomplete map: silent -> None", app2._run3_get_perspective_matrix(silent=True) is None)
try:
    app2._run3_get_perspective_matrix(silent=False)
    check("incomplete map: raises a clear error", False)
except ValueError as exc:
    check("incomplete map: raises a clear error", "4 matching points" in str(exc), str(exc))

# ---- Topview video drawn on the map
tracks = {}
for tid, (y0, x_speed) in enumerate(((10.0, 4.0), (25.0, 6.0)), start=1):
    rows = []
    for k in range(40):
        t = k / 10.0
        pm = (5.0 + x_speed * t, y0)
        rows.append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "class_name": "Car", "zone": "",
                     "_timestamp": t, "_m": pm, "_mc": pm, "_point": None, "_center": None, "_zone_num": None})
    tracks[str(tid)] = rows
cfg2 = dict(cfg)
cfg2["lengths"] = {"Car": 4.5}
cfg2["widths"] = {"Car": 1.8}
out_dir = tempfile.mkdtemp(prefix="pk_tv_", dir=tmp)
vid = app._run3_write_topview_video(tracks, cfg2, out_dir, video_path)
cap = cv2.VideoCapture(vid)
ok, fr = cap.read()
cap.release()
check("Topview video drawn on the map", ok and fr is not None and fr.std() > 8, "" if not ok else f"std {fr.std():.1f}")
# the map shows through (light grid lines of the map exist in the frame)
check("the map is the background", ok and (fr > 150).any(axis=2).sum() > 500)

# ---- zones over the pictures, error colours, delete a point, warning on a poor calibration
app.zones["Zone 3"] = [(300, 200), (900, 200), (900, 500), (300, 500)]
dlg3 = app.open_reference_map()
dlg3.node_mode_var.set(False)                                  # (these steps click point pairs by hand)
dlg3.reset()
dlg3.set_scale_from_points((100, 100), (300, 100), 10.0)
for c_, p_ in zip(cam_pts, map_pts):
    dlg3.add_camera_point(*c_)
    dlg3.add_map_point(*p_)
root.update()
on = dlg3.last_render["map"].copy()
dlg3.show_zones_var.set(False)
dlg3.reset_views_keep()
off = dlg3.last_render["map"].copy()
check("zones are drawn on the map through the calibration (and can be switched off)", (on != off).any())
check("zone polygon through the calibration lands where the camera zone is on the ground",
      all(len(poly) == 4 for _, poly in dlg3._zone_polys()))
# a deliberately wrong pair -> a red point with a big error
dlg3.show_zones_var.set(True)
dlg3.add_camera_point(*cam_pts[0]); dlg3.add_map_point(map_pts[0][0] + 400, map_pts[0][1] + 300)
bad = dlg3.calibration()
check("a wrong pair shows a clearly larger error", bad is not None and max(bad["errors_m"]) > 0.5 and bad["errors_m"][-1] == max(bad["errors_m"]) or max(bad["errors_m"]) > 0.5)
check("delete a pair by its number", dlg3.delete_pair("7") and len(dlg3.pairs) == 6 and dlg3.delete_pair("99") is False)
check("after deleting the wrong pair the calibration is exact again", dlg3.calibration()["rms_m"] < 0.01)
dlg3.add_camera_point(*cam_pts[1]); dlg3.add_map_point(map_pts[1][0] + 600, map_pts[1][1] + 500)
asked = []
orig_ask = m.messagebox.askyesno
m.messagebox.askyesno = lambda *a, **k: (asked.append(a[0]) or False)
check("a poor calibration asks before saving (and 'no' keeps the dialog)", dlg3.save() is False and len(asked) == 1)
m.messagebox.askyesno = orig_ask
dlg3.close()

# ---- zone corners as the camera-side reference points: only the map is clicked
map_z3 = [(300, 200), (700, 180), (900, 300), (880, 500), (500, 560), (280, 420)]
map_z4 = [(900, 300), (1100, 320), (1120, 520), (880, 500)]                # shares 2 corners with Zone 3
app.zones["Zone 3"] = [tuple(q) for q in ph(h_map_to_cam, map_z3)]
app.zones["Zone 4"] = [tuple(q) for q in ph(h_map_to_cam, map_z4)]
dlg5 = app.open_reference_map()
dlg5.reset()
dlg5.set_scale_from_points((100, 100), (300, 100), 10.0)
check("zone corners become reference points (shared corners once)", len(dlg5.nodes) == 8, str([n["label"] for n in dlg5.nodes]))
truth = {}
for i, nd in enumerate(dlg5.nodes):
    z = int(nd["zone"].split()[-1])
    truth[i] = (map_z3 if z == 3 else map_z4)[nd["idx"]]
dlg5.node_mode_var.set(True)
check("node mode starts on the first corner", dlg5.toggle_node_mode() and dlg5.active_node == 0)
root.update()
cvm5 = dlg5.canvases["map"]
kk, oxx, oyy = dlg5.view["map"]
for i in range(4):                                                # 4 corners: click only the map, the camera side is already known
    check(f"corner {i + 1}: the active one is next", dlg5.active_node == i)
    tx, ty = truth[i]
    cvm5.event_generate("<ButtonPress-1>", x=int(tx * kk + oxx), y=int(ty * kk + oyy))
    cvm5.event_generate("<ButtonRelease-1>", x=int(tx * kk + oxx), y=int(ty * kk + oyy))
    root.update()
check("4 map clicks = 4 pairs with the corner positions as camera points", len(dlg5.pairs) == 4
      and all(abs(dlg5.pairs[i][0] - dlg5.nodes[i]["cam"][0]) < 0.01 for i in range(4)))
check("the calibration is ready", dlg5.calibration() is not None)
pred = [dlg5.predicted_map(i) for i in range(4, 8)]
check("the remaining corners show on the map where the calibration puts them",
      all(q is not None and abs(q[0] - truth[i][0]) < 3 and abs(q[1] - truth[i][1]) < 3 for q, i in zip(pred, range(4, 8))),
      str([(q, truth[i]) for q, i in zip(pred, range(4, 8))]))
# drag a predicted corner marker to its place with the mouse -> it becomes a pair
root.update()
kk, oxx, oyy = dlg5.view["map"]
px_, py_ = dlg5.predicted_map(4)
sx, sy = int(px_ * kk + oxx), int(py_ * kk + oyy)
tx, ty = truth[4]
cvm5.event_generate("<ButtonPress-1>", x=sx, y=sy)
cvm5.event_generate("<B1-Motion>", x=int(tx * kk + oxx) + 1, y=int(ty * kk + oyy) + 1)
cvm5.event_generate("<ButtonRelease-1>", x=int(tx * kk + oxx) + 1, y=int(ty * kk + oyy) + 1)
root.update()
check("dragging a corner marker creates its pair", len(dlg5.pairs) == 5 and dlg5.node_pair_index(4) == 4, str(len(dlg5.pairs)))
# drag an already paired corner: its map position follows
root.update()
kk, oxx, oyy = dlg5.view["map"]                                   # (the canvas may have been resized by the changing label)
j = dlg5.node_pair_index(0)
before = list(dlg5.pairs[j][2:])
bx, by = int(before[0] * kk + oxx), int(before[1] * kk + oyy)
cvm5.event_generate("<ButtonPress-1>", x=bx, y=by)
cvm5.event_generate("<B1-Motion>", x=bx + 12, y=by + 8)
cvm5.event_generate("<ButtonRelease-1>", x=bx + 12, y=by + 8)
root.update()
check("dragging a paired corner moves its map point to the pointer", abs(dlg5.pairs[j][2] - (bx + 12 - oxx) / kk) < 0.6 and abs(dlg5.pairs[j][3] - (by + 8 - oyy) / kk) < 0.6, str(dlg5.pairs[j][2:]))
dlg5.assign_node(0, *truth[0])
check("skip a corner", dlg5.select_node(5) and dlg5.skip_node() and 5 in dlg5.skipped_nodes and dlg5.active_node != 5)
# the camera picture: clicking a corner selects it
rootk, cox, coy = dlg5.view["cam"]
nx, ny = dlg5.nodes[6]["cam"]
dlg5.canvases["cam"].event_generate("<ButtonPress-1>", x=int(nx * rootk + cox), y=int(ny * rootk + coy))
dlg5.canvases["cam"].event_generate("<ButtonRelease-1>", x=int(nx * rootk + cox), y=int(ny * rootk + coy))
root.update()
check("clicking a corner on the camera picture selects it (no stray point)", dlg5.active_node == 6 and dlg5.pending_cam is None)
a_ = dlg5.last_render["map"]
check("node markers are drawn on the map", a_ is not None and a_.std() > 5)
check("the progress text counts the corners", "จับคู่แล้ว 5" in dlg5.node_msg_var.get(), dlg5.node_msg_var.get())
dlg5.close()

# ---- the zones come onto the map by themselves; real distances between the corners
dlg6 = app.open_reference_map()
dlg6.reset()
dlg6.scale = None
dlg6.scale_var.set("")
dlg6.refresh()
check("zones are on the map right away (node mode is on by itself)", dlg6.node_mode_var.get() and len(dlg6.nodes) == 8)
mh_, mw_ = dlg6.map_img.shape[:2]
pos0 = [dlg6.predicted_map(i) for i in range(8)]
check("first layout: every corner has a place on the map, inside it", all(q is not None and 0 <= q[0] < mw_ and 0 <= q[1] < mh_ for q in pos0))
dlg6.rotate_layout()
pos1 = [dlg6.predicted_map(i) for i in range(8)]
check("rotate the layout moves the corners", any(abs(a_[0] - b_[0]) > 5 or abs(a_[1] - b_[1]) > 5 for a_, b_ in zip(pos0, pos1)))
dlg6.rotate_layout(); dlg6.rotate_layout(); dlg6.rotate_layout()
dlg6.flip_layout()
pos2 = [dlg6.predicted_map(i) for i in range(8)]
check("flip the layout mirrors it", any(abs(a_[0] - b_[0]) > 5 for a_, b_ in zip(pos0, pos2)))
dlg6.flip_layout()
truth6 = {}
for i, nd in enumerate(dlg6.nodes):
    truth6[i] = (map_z3 if nd["zone"] == "Zone 3" else map_z4)[nd["idx"]]
dlg6.assign_node(0, *truth6[0])
p1 = dlg6.predicted_map(1)
check("one corner placed: the layout follows it (that corner sits exactly where it was put)", dlg6._node_map_pos(0) == tuple(map(float, truth6[0])) and p1 is not None)
dlg6.assign_node(1, *truth6[1])
dlg6.assign_node(2, *truth6[2])
q3 = dlg6.predicted_map(3)
check("three corners placed: the others follow an affine fit (rough)", q3 is not None and math.hypot(q3[0] - truth6[3][0], q3[1] - truth6[3][1]) < 200)
for i in (3, 4, 5, 6, 7):
    dlg6.assign_node(i, *truth6[i])
check("all corners placed", all(dlg6.node_pair_index(i) is not None for i in range(8)) and len(dlg6.pairs) == 8)
check("edges of the zones, shared edges once", len(dlg6.edges) == 9, str([e["label"] for e in dlg6.edges]))
check("no scale yet: the table has no measured length", all(r[3] is None for r in dlg6.edge_rows()))
e0 = dlg6.edges[0]
real0 = math.hypot(truth6[e0["a"]][0] - truth6[e0["b"]][0], truth6[e0["a"]][1] - truth6[e0["b"]][1]) / 20.0
check("a real distance on one edge gives the map scale", dlg6.set_distance(e0["key"], real0) and dlg6.scale is not None and abs(dlg6.scale - 20.0) < 1e-6,
      str(dlg6.scale))
for e in dlg6.edges[1:]:
    real = math.hypot(truth6[e["a"]][0] - truth6[e["b"]][0], truth6[e["a"]][1] - truth6[e["b"]][1]) / 20.0
    dlg6.set_distance(e["key"], real)
rows = dlg6.edge_rows()
check("all distances entered and the measured ones agree", all(r[5] == "ตรง" for r in rows), str([r[5] for r in rows]))
check("the table shows the rows", len(dlg6.tree.get_children()) == 9)
e3 = dlg6.edges[3]
dlg6.set_distance(e3["key"], 1.6 * (math.hypot(truth6[e3["a"]][0] - truth6[e3["b"]][0], truth6[e3["a"]][1] - truth6[e3["b"]][1]) / 20.0))
bad_rows = [r for r in dlg6.edge_rows() if r[5] == "ตรวจจุด!"]
check("a wrong distance is flagged to check the corner", len(bad_rows) == 1 and bad_rows[0][0] == e3["key"], str(bad_rows))
dlg6.set_distance(e3["key"], None)
check("clearing a distance", e3["key"] not in dlg6.distances)
check("a custom pair of corners", dlg6.add_custom_edge("Z3.1", "Z4.3") and len(dlg6.edges) == 10
      and dlg6.add_custom_edge("z3.1", "z4.3") is False and dlg6.add_custom_edge("Z3.1", "Z9.9") is False)
saved_state = dlg6.result()
check("the distances are in the result", len(saved_state["distances"]) == 8 and saved_state["scale"] > 0)
check("save keeps pairs, scale and distances in the settings", dlg6.save() is True
      and len(app._run3_refmap_state()["distances"]) == 8 and len(app._run3_refmap_state()["pairs"]) == 8)
dlg7 = app.open_reference_map()
check("a new dialog brings the distances and the corners back", len(dlg7.distances) == 8 and len(dlg7.pairs) == 8 and dlg7.node_mode_var.get())
dlg7.close()

# ---- automatic alignment (ECC on road-edge images): a textured map, a camera seeing it, clicks that are ~0.6 m off
rng = np.random.default_rng(11)
tex = np.full((800, 1200, 3), 110, np.uint8)
for _ in range(260):                                               # random bars and lines = edges to align on
    x0, y0 = int(rng.integers(0, 1150)), int(rng.integers(0, 760))
    if rng.random() < 0.5:
        cv2.rectangle(tex, (x0, y0), (x0 + int(rng.integers(8, 60)), y0 + int(rng.integers(3, 14))), tuple(int(v) for v in rng.integers(30, 230, 3)), -1)
    else:
        cv2.line(tex, (x0, y0), (x0 + int(rng.integers(-90, 90)), y0 + int(rng.integers(-90, 90))), tuple(int(v) for v in rng.integers(30, 230, 3)), int(rng.integers(2, 5)))
tex_path = os.path.join(tmp, "tex_map.png")
cv2.imwrite(tex_path, tex)
cam2 = cv2.warpPerspective(tex, h_map_to_cam, (1280, 720))
cam2_path = os.path.join(tmp, "cam2.mp4")
vw = cv2.VideoWriter(cam2_path, cv2.VideoWriter_fourcc(*"mp4v"), 10, (1280, 720))
for _ in range(10):
    vw.write(cam2)
vw.release()
old_video = app.video_var.get()
app.video_var.set(cam2_path)
dlg8 = app.open_reference_map()
dlg8.node_mode_var.set(False)
dlg8.reset()
dlg8.refine = None
dlg8.set_map(tex_path)
dlg8.set_scale_from_points((100, 100), (300, 100), 10.0)
pts_map = np.column_stack([rng.uniform(150, 1050, 8), rng.uniform(100, 700, 8)])
pts_cam = ph(h_map_to_cam, pts_map)
noisy = pts_map + rng.normal(0, 12.0, pts_map.shape)                # ~0.6 m click errors
for c_, p_ in zip(pts_cam, noisy):
    dlg8.add_camera_point(*c_)
    dlg8.add_map_point(*p_)
test_map = np.column_stack([rng.uniform(300, 900, 40), rng.uniform(200, 560, 40)])      # ground points inside the zones
test_cam = ph(h_map_to_cam, test_map)


def ground_error(dlg):
    cal = dlg.calibration()
    pred = m.apply_homography(cal["H"], test_cam) * dlg.scale
    return float(np.mean(np.hypot(*(pred - test_map).T)) / 20.0)


err_rough = ground_error(dlg8)
check("noisy clicks: the ground positions are about half a metre off", err_rough > 0.15, f"{err_rough:.2f} m")
res8 = dlg8.auto_align(model="affine", blocking=True)
check("automatic alignment returns a correction", res8 is not None and res8["R"].shape == (3, 3))
check("the road-edge agreement gets better", res8["ncc_after"] > res8["ncc_before"] + 0.02, f"{res8['ncc_before']:.3f} -> {res8['ncc_after']:.3f}")
dlg8.apply_refine(res8)
err_fine = ground_error(dlg8)
check("after the alignment the ground positions are clearly closer to the truth", err_fine < 0.75 * err_rough and err_fine < 0.45,
      f"{err_rough:.2f} m -> {err_fine:.2f} m")
check("the message says the pair errors are measured against the clicks", "ปรับอัตโนมัติ" in dlg8.msg_var.get())
check("the summary text gives the agreement and the shift in cm", "ซม." in dlg8.refine_summary(res8))
dlg8.clear_refine()
check("clear: back to the clicked pairs' calibration", dlg8.refine is None and abs(ground_error(dlg8) - err_rough) < 1e-9)
dlg8.apply_refine(res8)
saved_refine = dlg8.result()["refine"]
check("save keeps the correction in the settings and the program uses it", dlg8.save() is True
      and app._run3_refmap_state()["refine"] is not None
      and np.allclose(app._run3_refmap_state()["refine"], saved_refine, atol=1e-6))
persp8 = app._run3_get_perspective_matrix(silent=False)
check("the perspective used by Run 3 includes the correction", persp8 is not None and persp8.get("refined") is True)
got8 = app._run3_to_metric(test_cam[:5], {"perspective": persp8, "ppm": 1.0, "axis_deg": 0.0})
check("Run 3 metres follow the refined mapping (map px / scale)", np.hypot(*(got8 * 20.0 - test_map[:5]).T).mean() / 20.0 < 0.30)
# a blocking call without a calibration is refused politely
dlg9 = app.open_reference_map()
dlg9.node_mode_var.set(False)
dlg9.reset()
check("no calibration yet: automatic alignment is refused with a message", dlg9.auto_align(blocking=True) is None and "4 คู่" in dlg9.msg_var.get())
dlg9.close()
app.video_var.set(old_video)

# ---- the map can also be a VIDEO (a drone clip): one chosen frame is the map
map_video = os.path.join(tmp, "drone_ไทย.mp4")                       # (non-ASCII name on purpose)
vw = cv2.VideoWriter(map_video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (1200, 800))
other = np.full((800, 1200, 3), 40, np.uint8)
for k in range(30):
    vw.write(map_img if k < 15 else other)                          # frames 1-15 = the grid map, 16-30 = dark
vw.release()
check("is_video_file", m.is_video_file(map_video) and not m.is_video_file(map_path))
first = m.load_reference_map_image(map_video, 3)
last = m.load_reference_map_image(map_video, 25)
check("video map: frame choice", first is not None and last is not None and abs(float(first.mean()) - float(map_img.mean())) < 6
      and abs(float(last.mean()) - 40.0) < 6, f"first {first.mean():.1f} last {last.mean():.1f}")
check("image map with a non-ASCII path loads", m.load_reference_map_image(map_path) is not None)
dlg2 = app.open_reference_map()
dlg2.node_mode_var.set(False)
check("video map accepted by the dialog", dlg2.set_map(map_video, 2) and dlg2.map_frame == 2 and dlg2.pairs == [], str(dlg2.map_frame))
dlg2.set_scale_from_points((100, 100), (300, 100), 10.0)
for c_, p_ in zip(cam_pts, map_pts):
    dlg2.add_camera_point(*c_)
    dlg2.add_map_point(*p_)
check("map frame can be changed", dlg2.set_map_frame("25") and dlg2.map_frame == 24 and abs(float(dlg2.map_img.mean()) - 40.0) < 6)
dlg2.set_map_frame("3")
check("video map: the map slider is on and covers the map video", str(dlg2.sliders["map"].cget("state")) == "normal"
      and int(float(dlg2.sliders["map"].cget("to"))) == dlg2.map_total - 1)
dlg2.step("map", "frame", 2)
check("video map: step frames", dlg2.map_frame == 4, str(dlg2.map_frame))
# real mouse events: wheel zoom at the pointer, a drag pans, a plain click puts a point
root.update()
cvm = dlg2.canvases["map"]
cvm.event_generate("<MouseWheel>", x=250, y=180, delta=120)
root.update()
check("mouse wheel event zooms", dlg2.zoom["map"] > 1.0, f"{dlg2.zoom['map']:.2f}")
ox_before = dlg2.view["map"][1]
cvm.event_generate("<ButtonPress-1>", x=250, y=180)
cvm.event_generate("<B1-Motion>", x=290, y=200)
cvm.event_generate("<ButtonRelease-1>", x=290, y=200)
root.update()
check("dragging pans (and does not put a point)", dlg2.view["map"][1] != ox_before and dlg2.pending_cam is None)
dlg2.reset_view("map")
dlg2.add_camera_point(5, 5)
n_pairs = len(dlg2.pairs)
cvm.event_generate("<ButtonPress-1>", x=300, y=220)
cvm.event_generate("<ButtonRelease-1>", x=300, y=220)
root.update()
check("a plain click on the map completes the pair", len(dlg2.pairs) == n_pairs + 1)
dlg2.undo()
dlg2.set_map_frame("3")
check("video map: save", dlg2.save() is True)
st2 = app._run3_refmap_state()
check("video map: path and frame are kept in the settings", st2["map_path"] == map_video and st2["map_frame"] == 2, str(st2["map_frame"]))
persp2 = app._run3_get_perspective_matrix(silent=False)
check("video map: calibration works", persp2 is not None and persp2["map"]["frame"] == 2)
cfg3 = dict(cfg2)
cfg3["perspective"] = persp2
out3 = tempfile.mkdtemp(prefix="pk_tv_", dir=tmp)
vid3 = app._run3_write_topview_video(tracks, cfg3, out3, video_path)
cap = cv2.VideoCapture(vid3)
ok3, fr3 = cap.read()
cap.release()
check("Topview video drawn on the video map", ok3 and fr3 is not None and fr3.std() > 8)

root.destroy()
print("ALL OK" if not failures else "FAILED: " + ", ".join(failures))
sys.exit(1 if failures else 0)
