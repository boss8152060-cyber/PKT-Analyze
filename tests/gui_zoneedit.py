"""The zone editor on the video | drone | X-Y views: corners dragged in any of them, shared corners moving together, snap, Shift = perpendicular,
undo / redo, "make perpendicular", saving a NEW zone file in the same format.

A synthetic site (like tests/gui_align.py): a ground plane seen by a tilted camera with a barrel lens, and from straight above.

Run from the Run folder:   python tests/gui_zoneedit.py
"""
import hashlib
import importlib.util
import json
import math
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


tmp = tempfile.mkdtemp(prefix="pk_zed_")
CW, CH = 1280, 720
H_CAM = cv2.getPerspectiveTransform(np.float32([(0, 0), (60, 0), (60, 20), (0, 20)]), np.float32([(100, 330), (1200, 280), (1260, 600), (40, 630)]))
K1 = 0.22


def video_px(g):
    q = cv2.perspectiveTransform(np.asarray(g, float).reshape(-1, 1, 2), H_CAM).reshape(-1, 2)
    c = np.array([CW / 2.0, CH / 2.0])
    x = (q - c) / (CW / 2.0)
    ru = np.sqrt((x ** 2).sum(1))
    rd = ru.copy()
    for _ in range(60):
        rd = np.maximum(rd - (rd * (1 + K1 * rd ** 2) - ru) / (1 + 3 * K1 * rd ** 2), 0)
    sc = np.where(ru > 1e-12, rd / np.where(ru > 1e-12, ru, 1.0), 1.0)
    return x * sc[:, None] * (CW / 2.0) + c


def drone_px(g):
    return np.asarray(g, float) * 20.0 + [60.0, 80.0]


video = os.path.join(tmp, "clip.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(5):
    vw.write(np.full((CH, CW, 3), 90, np.uint8))
vw.release()
drone_file = os.path.join(tmp, "drone.png")
ok, buf = cv2.imencode(".png", np.full((560, 1400, 3), 120, np.uint8))
buf.tofile(drone_file)

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
m.messagebox.showinfo = lambda *a, **k: None
m.messagebox.showerror = lambda *a, **k: None
asked = []
m.messagebox.askyesno = lambda *a, **k: (asked.append(a), True)[1]
app.video_var.set(video)

# the alignment (what the Align window saves)
gx, gy = np.linspace(4, 56, 5), np.linspace(3, 17, 4)
ground = np.array([(a, b) for a in gx for b in gy])
dlg = app.open_align()
root.update()
dlg.load_drone(drone_file)
for g, v, d in zip(ground, video_px(ground), drone_px(ground)):
    dlg.add_pair(v, d)
dlg.set_scale_from_points((100, 100), (300, 100), 10.0)
dlg.set_kind("lens")
dlg.apply()

# zones whose cross-road edges lean (as drawn on the video), neighbours share corners
Z2 = [(4, 5), (18, 5), (18.9, 12), (4.7, 12)]
Z3 = [(18, 5), (32, 5), (32.9, 12), (18.9, 12)]
Z4 = [(32, 5), (36, 8.2), (32.9, 12)]
GROUND_ZONES = {"Zone 2": Z2, "Zone 3": Z3, "Zone 4": Z4}
app.zones = {name: [] for name in m.ZONE_NAMES}
for name, g in GROUND_ZONES.items():
    app.zones[name] = [tuple(float(v) for v in q) for q in video_px(g)]
src_json = os.path.join(tmp, "clip_zones.json")
items = [{"id": f"zone_{i}", "name": name, "points": [[int(round(x)), int(round(y))] for x, y in app.zones[name]], "area_px": 1.0,
          "color_bgr": [0, 200 - 40 * i, 40 * i], "show_label": True, "reference_frame_index": 0} for i, name in enumerate(GROUND_ZONES)]
json.dump({"video_path": video, "frame_width": CW, "frame_height": CH, "zones": items}, open(src_json, "w", encoding="utf-8"))
app.zone_line_config_var.set(src_json)
before_hash = hashlib.md5(open(src_json, "rb").read()).hexdigest()

# ---- without what it needs
align_json = app.run3_align_var.get()
check("the alignment is saved", bool(json.loads(align_json or "{}").get("pairs")))
app.run3_align_var.set("")
check("without an alignment the editor says so (no window)", app.open_zone_editor() is None)
app.run3_align_var.set(align_json)

ed = app.open_zone_editor()
root.update()
check("the editor opens with the three views", ed is not None and ed.video_img is not None and ed.plan_img is not None and ed.vpane.view is not None)
check("corners of neighbouring zones at the same spot are ONE corner (7 corners for 3 zones)", len(ed.members) == 7, str(len(ed.members)))
txt = ed.report_text()
check("the report lists the lengths and the leaning cross edges", "Zone 2" in txt and "เอียง" in txt, txt[:160])
plan0 = {z: ed.plan_of(ed._vpts(z)) for z in ed.names}
check("the cross-road edges of the zones lean in the plane to start with", abs(plan0["Zone 2"][1][0] - plan0["Zone 2"][2][0]) > 0.5)

# ---- make perpendicular
rep = ed.make_perpendicular()
plan1 = {z: ed.plan_of(ed._vpts(z)) for z in ed.names}
check("after 'make perpendicular' the cross-road edges are vertical in the plane", abs(plan1["Zone 2"][1][0] - plan1["Zone 2"][2][0]) < 0.01
      and abs(plan1["Zone 2"][0][0] - plan1["Zone 2"][3][0]) < 0.01 and abs(plan1["Zone 3"][1][0] - plan1["Zone 3"][2][0]) < 0.01,
      f"{abs(plan1['Zone 2'][1][0] - plan1['Zone 2'][2][0]):.4f} m")
check("a corner shared by two zones is still shared (same video pixel in both)", ed.zones["Zone 2"][1] == ed.zones["Zone 3"][0] and ed.zones["Zone 2"][2] == ed.zones["Zone 3"][3])
check("the video corners were computed back from the plane (the plane position of the new video pixel is the vertical one)",
      np.abs(ed.plan_of(ed._vpts("Zone 3"))[1][0] - ed.plan_of(ed._vpts("Zone 3"))[2][0]) < 0.01)
check("the along-road edges did not move (still the same y)", abs(plan1["Zone 2"][0][1] - plan0["Zone 2"][0][1]) < 0.02)
ed.undo()
back = ed.plan_of(ed._vpts("Zone 2"))
check("undo brings the lean back", abs(back[1][0] - back[2][0]) > 0.5)
ed.redo()
check("redo makes it vertical again", abs(ed.plan_of(ed._vpts("Zone 2"))[1][0] - ed.plan_of(ed._vpts("Zone 2"))[2][0]) < 0.01)

# ---- drag in each of the three views (through the mouse handlers)
gid = ed.group_of[("Zone 3", 1)]
g_before = ed.group_plan(gid).copy()
for pane_name, pane in (("video", ed.vpane), ("drone", ed.dpane), ("plan", ed.ppane)):
    vpt = ed.pane_xy(pane_name, ed.group_video(gid).reshape(1, 2))[0]
    ex, ey = pane.to_view(*vpt)
    grabbed = ed._on_press(pane_name)(vpt[0], vpt[1], ex, ey)
    target_plan = g_before + np.array([0.6, -0.4])
    if pane_name == "video":
        tgt = ed.pane_xy("video", m.align_plane_to_video(ed.cfg, target_plan.reshape(1, 2), ed.group_video(gid).reshape(1, 2)))[0]
    elif pane_name == "drone":
        tgt = m.align_plane_to_drone(ed.cfg, target_plan.reshape(1, 2))[0]
    else:
        tgt = ed.plan_to_px(target_plan)[0]
    ed.snap_var.set(False)
    ed._on_drag(pane_name)(tgt[0], tgt[1])
    ed._on_release()
    moved = ed.group_plan(gid)
    check(f"dragging a corner in the {pane_name} view puts it where it was dragged", grabbed and np.abs(moved - target_plan).max() < 0.03, f"{moved} vs {target_plan}")
    check(f"  ... and the other zone that shares the corner moved with it ({pane_name})", all(np.abs(ed.plan_of(ed._vpts(z))[i] - moved).max() < 0.03 for z, i in ed.members[gid]))
    ed.undo()
    ed.snap_var.set(True)
check("an empty spot does not grab anything (the view can be panned)", ed._on_press("plan")(0, 0, 3, 3) is False)

# ---- snap
other = ed.group_of[("Zone 4", 1)]
op = ed.group_plan(other).copy()
ed.snap_cm_var.set("25")
ed.move_group_to(gid, op + np.array([0.12, 0.08]))
check("a corner dropped within 25 cm of another corner snaps onto it", np.abs(ed.group_plan(gid) - op).max() < 0.02)
ed.undo() if ed.undo_stack else None
ed.zones = {z: [list(q) for q in v] for z, v in ed.orig.items()}
# ---- Shift: perpendicular to the edge before
z, i = "Zone 2", 2                                                    # corner 3 of zone 2: previous = 2, before that = 1
gid2 = ed.group_of[(z, i)]
pl = ed.plan_of(ed._vpts(z))
ed.snap_var.set(False)
ed.move_group_to(gid2, pl[i] + np.array([1.3, 0.2]), shift=True)
pl2 = ed.plan_of(ed._vpts(z))
e1, e2 = pl2[1] - pl2[0], pl2[2] - pl2[1]
check("Shift: the edge from the previous corner is perpendicular to the one before", abs(float(e1 @ e2)) / (np.hypot(*e1) * np.hypot(*e2)) < 0.01, f"cos = {float(e1 @ e2) / (np.hypot(*e1) * np.hypot(*e2)):.4f}")
ed.zones = {z_: [list(q) for q in v] for z_, v in ed.orig.items()}

# ---- save as a NEW file
ed.make_perpendicular()
new_path = os.path.join(tmp, "clip_zones_aligned.json")
ed.save_new_file(new_path)
check("the original zone file is not touched", hashlib.md5(open(src_json, "rb").read()).hexdigest() == before_hash)
nd = json.load(open(new_path, encoding="utf-8"))
check("the new file has the same format (frame size, zones with points / points_norm / colour / id)", nd["frame_width"] == CW and nd["frame_height"] == CH and
      all({"id", "name", "points", "points_norm", "area_px", "color_bgr"} <= set(zz) for zz in nd["zones"]) and nd["zones"][0]["id"] == "zone_0")
check("the program takes the new file", (lambda: (app._load_pkstudio_json(new_path), True)[1])() and len(app.zones["Zone 2"]) == 4)
pn = app.zones["Zone 2"]
pp = ed.plan_of(np.asarray(pn, float))
check("with the new file loaded the cross-road edges are vertical in the plane (to a pixel's rounding)", abs(pp[1][0] - pp[2][0]) < 0.08 and abs(pp[0][0] - pp[3][0]) < 0.08,
      f"{abs(pp[1][0] - pp[2][0]):.3f} m")
check("a pixel's rounding is the only difference to what was edited", max(abs(pn[k][0] - ed.zones['Zone 2'][k][0]) for k in range(4)) <= 0.5 + 1e-9)
# ---- one click: use the edited zones for the analysis
ed.zones = {z_: [list(q) for q in v] for z_, v in ed.orig.items()}
ed.make_perpendicular()
app.zone_line_config_var.set(src_json)
used = ed.use_for_analysis()
check("'use for the analysis' writes <name>_aligned.json beside the original and the program takes it (no dialog)",
      used == os.path.join(tmp, "clip_zones_aligned.json") and app.zone_line_config_var.get() == used, str(used))
pu = ed.plan_of(np.asarray(app.zones["Zone 2"], float))
check("the program's zones are the edited ones (cross-road edges vertical in the plane)", abs(pu[1][0] - pu[2][0]) < 0.08)
check("the original zone file is still untouched", hashlib.md5(open(src_json, "rb").read()).hexdigest() == before_hash)
ed.close()

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
