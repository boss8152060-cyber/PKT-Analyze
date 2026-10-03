"""Reference-map calibration (a top-view drone picture used as the MAP): dialog logic, settings, and the Topview video.

Run from the Run folder:   python tests/gui_refmap.py
A synthetic map and a synthetic camera frame (the map seen through a known perspective) are made; the dialog is
driven through its methods (no mouse), then the result must reproduce the known camera-pixel -> metre mapping.
"""
import importlib.util
import json
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

# ---- adjust the zones on the map (drag corners), then they come back as camera-picture zones and a new zone file
zone_src = os.path.join(tmp, "zones_src.json")
cam_zone = [(300, 200), (900, 200), (900, 500), (300, 500)]
with open(zone_src, "w", encoding="utf-8") as f:
    json.dump({"video_path": video_path, "frame_width": 1280, "frame_height": 720,
               "zones": [{"id": "z3", "name": "Zone 3", "points": cam_zone, "points_norm": [], "color_bgr": [0, 200, 0]}],
               "lines": {}}, f)
app.zone_line_config_var.set(zone_src)
app._load_pkstudio_json(zone_src)
dlg4 = app.open_reference_map()
dlg4.reset()
dlg4.set_scale_from_points((100, 100), (300, 100), 10.0)
for c_, p_ in zip(cam_pts, map_pts):
    dlg4.add_camera_point(*c_)
    dlg4.add_map_point(*p_)
dlg4.zone_edit_var.set(True)
check("zone edit starts when the calibration is ready", dlg4.toggle_zone_edit() and dlg4.zone_map is not None and len(dlg4.zone_map["Zone 3"]) == 4)
check("not adjusted yet: nothing to save", dlg4.zones_in_camera() is None)
orig_map = [list(q) for q in dlg4.zone_map["Zone 3"]]
want_cam0 = None
new_map0 = [orig_map[0][0] + 40.0, orig_map[0][1] + 25.0]
check("move a corner", dlg4.move_zone_vertex("Zone 3", 0, *new_map0))
zc = dlg4.zones_in_camera()
want = ph(h_map_to_cam, [new_map0])[0]
check("the moved corner comes back in camera pixels (exact calibration)", zc is not None and abs(zc["Zone 3"][0][0] - want[0]) < 1.5 and abs(zc["Zone 3"][0][1] - want[1]) < 1.5,
      "" if zc is None else f"{zc['Zone 3'][0]} vs {want.round(1)}")
check("the other corners stay where they were", zc is not None and all(abs(a_ - b_) <= 1.5 for a_, b_ in zip(zc["Zone 3"][1], cam_zone[1])))
check("delete a corner (4 -> 3) and not below 3", dlg4.delete_zone_vertex("Zone 3", 3) and len(dlg4.zone_map["Zone 3"]) == 3
      and dlg4.delete_zone_vertex("Zone 3", 0) is False)
check("insert a corner after corner 0", dlg4.insert_zone_vertex("Zone 3", 0, 700.0, 300.0) and len(dlg4.zone_map["Zone 3"]) == 4)
# the mouse: drag a corner square on the map canvas
root.update()
kk, oxx, oyy = dlg4.view["map"]
vx, vy = dlg4.zone_map["Zone 3"][1]
cvm4 = dlg4.canvases["map"]
sx, sy = int(vx * kk + oxx), int(vy * kk + oyy)
before = list(dlg4.zone_map["Zone 3"][1])
cvm4.event_generate("<ButtonPress-1>", x=sx, y=sy)
cvm4.event_generate("<B1-Motion>", x=sx + 30, y=sy + 18)
cvm4.event_generate("<ButtonRelease-1>", x=sx + 30, y=sy + 18)
root.update()
after = dlg4.zone_map["Zone 3"][1]
check("dragging a corner square moves that corner (and puts no point pair)", abs(after[0] - before[0] - 30 / kk) < 2 and abs(after[1] - before[1] - 18 / kk) < 2
      and dlg4.pending_cam is None, f"{before} -> {after}")
dlg4.revert_zones()
check("revert gives the original zones back", dlg4.zone_map is None and dlg4.zones_in_camera() is None)
dlg4.zone_edit_var.set(True)
dlg4.toggle_zone_edit()
dlg4.move_zone_vertex("Zone 3", 2, dlg4.zone_map["Zone 3"][2][0] + 30, dlg4.zone_map["Zone 3"][2][1] - 20)
shown = []
m.messagebox.showinfo = lambda *a, **k: shown.append(a)
check("save with adjusted zones", dlg4.save() is True)
new_zone_file = os.path.splitext(zone_src)[0] + "_mapfit.json"
check("a new zone file is written, the original is not touched",
      os.path.isfile(new_zone_file) and json.load(open(zone_src))["zones"][0]["points"] == [list(p) for p in cam_zone])
saved_pts = json.load(open(new_zone_file))["zones"][0]["points"]
check("the new file holds the adjusted zone and is the zone file now", app.zone_line_config_var.get() == new_zone_file and saved_pts[2] != list(cam_zone[2]),
      str(saved_pts))
check("the program uses the adjusted zone", len(app.zones["Zone 3"]) == 4 and [int(round(v)) for v in app.zones["Zone 3"][2]] == saved_pts[2])
check("the user is told a re-run is needed", len(shown) == 1)

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
