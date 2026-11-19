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
m.filedialog.askopenfilename = lambda **k: ""                           # (the editor asks for the drone picture when it does not know it: nothing is chosen in a test)
app.run3_align_var.set("")
w0 = app.open_zone_editor(ask_drone=False)
root.update()
check("without an Align the editor opens in the Align mode (nothing aligned, no drone picture)", isinstance(w0, m.ZoneAlignEditor) and w0.mode == "align" and not w0.aligned and w0.drone_img is None)
check("clicking on the drone picture without one says so", w0._click_drone(10, 10) is False)
w0.close()
app.run3_align_var.set(align_json)
w1 = app.open_align_and_zones()
root.update()
check("one button: with an alignment it opens the same window in the edit mode", isinstance(w1, m.ZoneAlignEditor) and w1.mode == "edit" and w1.aligned)
w1.close()

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
# the length of every edge is written on the pictures (a switch turns it off)
import numpy as _np
_img_on = _np.zeros((700, 1000, 3), _np.uint8)
_img_off = _np.zeros((700, 1000, 3), _np.uint8)
ed.len_var.set(True)
ed._draw(_img_on, "plan", ed.ppane)
ed.len_var.set(False)
ed._draw(_img_off, "plan", ed.ppane)
check("edge lengths (m) are drawn on the picture and the switch removes them", int((_img_on.sum(axis=2) > 0).sum()) > int((_img_off.sum(axis=2) > 0).sum()) + 200,
      f"{int((_img_on.sum(axis=2) > 0).sum())} vs {int((_img_off.sum(axis=2) > 0).sum())}")
# another roadside video as the left picture
video2 = os.path.join(tmp, "clip2.mp4")
vw2 = cv2.VideoWriter(video2, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(5):
    vw2.write(np.full((CH, CW, 3), 200, np.uint8))
vw2.release()
mean_before = float(ed.video_img.mean())
zones_before = {z: [list(q) for q in pts] for z, pts in ed.zones.items()}
check("zone editor: the window can change to another video", ed.change_video(video2) is True and ed.video_path == video2 and float(ed.video_img.mean()) > mean_before + 50)
check("zone editor: the zones keep their pixel positions and the choice is remembered", ed.zones == zones_before and app.edit_video == video2 and ed.vpath_var.get() == video2)
check("zone editor: a missing file changes nothing", ed.change_video(os.path.join(tmp, "nothing.mp4")) is False and ed.video_path == video2)
app.edit_video = ""
ed.len_var.set(True)
ed.close()

# ---- real lengths of the zone edges (1.54.0): optional, kept in the Align, fit the scale
ed = app.open_zone_editor()
root.update()
rows = ed.edge_rows()
labels = [r["label"] for r in rows]
check("the table lists every distinct edge once (11 sides of 3 zones, 2 shared -> 9)", len(rows) == len({r["key"] for r in rows}) and len(rows) == 9, str(labels))
check("an edge shared by two zones is one row, named after both", any(" = " in lab for lab in labels), str(labels))
check("nothing is entered at first and the table says what to do", not ed.real and "ดับเบิลคลิก" in ed.edge_msg_var.get())
r0, r1 = rows[0], rows[1]
check("a number with a comma is read (12,5 = 12.5 m)", ed.set_real_length(r0["key"], "12,5") is True and ed.real[r0["key"]] == 12.5)
check("a text or a zero is refused and changes nothing", ed.set_real_length(r1["key"], "abc") is False and ed.set_real_length(r1["key"], "0") is False and r1["key"] not in ed.real)
saved = json.loads(app.run3_align_var.get())
check("the real length is kept in the saved Align", saved.get("edge_lengths") == [{"zone": r0["z"], "i": r0["i"], "m": 12.5}], str(saved.get("edge_lengths")))
check("the table shows the difference to what the Align measures", ed.edge_tree.item("0", "values")[2] == "12.5" and ed.edge_tree.item("0", "values")[3].endswith("%"))
ed.close()
ed = app.open_zone_editor()
root.update()
check("opened again the real length is still there", ed.real.get(r0["key"]) == 12.5)

# make the measured length 10 % short of the real one for two edges, then fit
meas = {r["key"]: r["measured"] for r in ed.edge_rows()}
ed.set_real_length(r0["key"], f"{meas[r0['key']] * 1.1:.4f}")
ed.set_real_length(r1["key"], f"{meas[r1['key']] * 1.1:.4f}")
scale0 = float(ed.cfg["scale"])
asked.clear()
check("the scale is adjusted by the fitted factor after asking", ed.apply_real_scale() is True and len(asked) == 1)
check("the new scale is 10 % larger", abs(float(ed.cfg["scale"]) / scale0 - 1.1) < 5e-4, f"{float(ed.cfg['scale']) / scale0:.5f}")
check("the measured lengths now fit the real ones", all(abs(r["measured"] - ed.real[r["key"]]) < 0.02 for r in ed.edge_rows() if r["key"] in ed.real))
check("the Align saved for the analysis has the new scale", abs(json.loads(app.run3_align_var.get())["scale"] / scale0 - 1.1) < 5e-4)
check("nothing more to adjust once it fits", ed.apply_real_scale() is False)
m.messagebox.askyesno = lambda *a, **k: (asked.append(a), False)[1]
ed.set_real_length(r1["key"], f"{ed.edge_rows()[1]['measured'] * 1.5:.4f}")
scale1 = float(ed.cfg["scale"])
check("answering No leaves the scale alone", ed.apply_real_scale() is False and float(ed.cfg["scale"]) == scale1)
m.messagebox.askyesno = lambda *a, **k: (asked.append(a), True)[1]
ed.set_real_length(r1["key"], "")
check("an empty entry clears the real length of that edge", r1["key"] not in ed.real and len(json.loads(app.run3_align_var.get())["edge_lengths"]) == 1)

# the Align window keeps the real lengths when it saves again
d3 = app.open_align()
root.update()
check("the Align window knows the real lengths", len(d3.edge_lengths) == 1)
check("and keeps them when it is saved", d3.apply() is True and len(json.loads(app.run3_align_var.get()).get("edge_lengths", [])) == 1)
ed.close()


# ---- the Align inside this window (1.56.0): the zone corners are the pins, the drone picture is clicked, the scale comes from a real length
for name, g in GROUND_ZONES.items():
    app.zones[name] = [tuple(float(v) for v in q) for q in video_px(g)]
corner_ground = np.array(sorted({tuple(q) for g in GROUND_ZONES.values() for q in g}))
corner_video = video_px(corner_ground)
corner_drone = drone_px(corner_ground)


def drone_of_group(ed_, gid):
    v = ed_.group_video(gid)
    return corner_drone[int(np.argmin(np.hypot(*(corner_video - v).T)))]


app.run3_align_var.set("")
app.run3_align_enabled_var.set(False)
ed = app.open_zone_editor(ask_drone=False)
root.update()
check("the 7 corners of the 3 zones are the pins and none is done", len(ed.members) == 7 and ed._pin_counts() == {"todo": 7, "done": 0, "skip": 0}, str(ed._pin_counts()))
check("the first corner waits for its place (label Z2.1)", ed.cur_pin is not None and ed._pin_label(ed.cur_pin).startswith("Z2.1"), str(ed._pin_label(ed.cur_pin)))
check("a shared corner has both zones in its label", any("=" in ed._pin_label(g) for g in ed.members), str([ed._pin_label(g) for g in ed.members]))
check("the drone picture is loaded from a file", ed.load_drone(drone_file) is True and ed.drone_img is not None and ed.dpath_var.get() == drone_file)
ed.set_kind("lens")
order = []
for _ in range(7):
    gid = ed.cur_pin
    order.append(gid)
    check_ok = ed._click_drone(*drone_of_group(ed, gid))
check("every corner got its place on the drone picture (7 pairs, labelled)", len(ed.pairs) == 7 and all(q.get("l") for q in ed.pairs) and ed._pin_counts()["done"] == 7 and ed.cur_pin is None)
check("the Align fits once there are enough pairs", ed.aligned is True and ed.cfg is not None)
check("nothing is in metres yet: the scale is not set and the analysis is not told to use the Align", ed.scale == 0 and not app.run3_align_enabled_var.get())
saved = json.loads(app.run3_align_var.get())
check("the Align is kept in the project (pairs, kind, labels, drone picture) with the scale 0", len(saved["pairs"]) == 7 and saved["kind"] == "lens" and saved["scale"] == 0.0
      and saved["drone"]["path"] == drone_file and all(q.get("l") for q in saved["pairs"]))
check("the table says that the scale is missing", "สเกล" in ed.edge_msg_var.get(), ed.edge_msg_var.get())
check("the report names the fit and the missing scale", "จัดแนว" in ed.report_text() and "ยังไม่ได้ตั้งสเกล" in ed.report_text())

# one real length sets the scale (14 m = the edge 1-2 of Zone 2 on the ground)
rows = ed.edge_rows()
row = [r for r in rows if r["label"].startswith("Zone 2: 1→2")][0]
check("without the scale the plane is in drone pixels (the edge is 280 of them)", abs(row["measured"] - 280.0) < 4.0, f"{row['measured']:.1f}")
ed.set_real_length(row["key"], "14")
check("the scale is set from the real length, no question asked (nothing to overturn)", ed.apply_real_scale() is True and abs(ed.scale - 0.05) < 0.001, f"{ed.scale}")
rows = {r["label"]: r for r in ed.edge_rows()}
check("the other edges now come out in metres (Zone 2: 2→3 = 7.06 m on the ground)", abs([r for r in rows.values() if r["label"].startswith("Zone 2: 2→3")][0]["measured"] - math.hypot(0.9, 7.0)) < 0.1,
      str([r["measured"] for r in rows.values() if r["label"].startswith("Zone 2: 2→3")]))
saved = json.loads(app.run3_align_var.get())
check("the Align now has the scale and the analysis is told to use it", abs(saved["scale"] - 0.05) < 0.001 and app.run3_align_enabled_var.get() is True and saved["info"]["unit"] == "m")
check("the real length is kept too", saved.get("edge_lengths") and abs(saved["edge_lengths"][0]["m"] - 14.0) < 1e-9)
check("the status of the project says what the Align is", "7 คู่" in app._align_status_text(), app._align_status_text())

# skipping, going back, an extra point, deleting
ed.close()
app.run3_align_var.set("")
app.run3_align_enabled_var.set(False)
ed = app.open_zone_editor(ask_drone=False)
root.update()
ed.load_drone(drone_file)
first = ed.cur_pin
check("a corner can be skipped: the next one waits", ed.skip_pin() is True and ed._pin_state(first) == "skip" and ed.cur_pin != first)
check("going back takes the skipped corner up again", ed.goto_pin(-1) is True and ed.cur_pin == first and ed._pin_state(first) == "todo")
vx, vy = ed.group_video(ed.cur_pin)
ed.vpane.set_image(ed.video_img)
root.update()
check("a click on the video away from every corner is an extra point waiting for its place", ed._click_video(vx + 300, vy - 120) is True and ed.pending_free is not None)
check("the drone click makes it an unlabelled pair", ed._click_drone(300, 200) is True and len(ed.pairs) == 1 and "l" not in ed.pairs[0] and ed.pending_free is None)
check("the last pair can be deleted", ed.delete_last_pair() is True and not ed.pairs)
for gid in sorted(ed.members):
    ed.cur_pin = gid
    ed._click_drone(*drone_of_group(ed, gid))
check("all 7 corners placed again", len(ed.pairs) == 7 and ed.aligned)
ed.set_scale_text if False else None
ed.scale_var.set("0.05")
check("the scale can be typed (metres per drone pixel)", ed.set_scale_text() is True and abs(ed.scale - 0.05) < 1e-12 and app.run3_align_enabled_var.get() is True)
# a wrong extra pair is the worst one and goes with 'delete the worst'
ed._click_video(corner_video[0][0] + 5.0, corner_video[0][1] + 150.0)
ed._click_drone(900.0, 40.0)
n8 = len(ed.pairs)
check("a wrong extra pair is added (8 pairs)", n8 == 8 and "l" not in ed.pairs[-1])
check("'delete the worst pair' removes it", ed.delete_worst_pair() is True and len(ed.pairs) == 7 and all(q.get("l") for q in ed.pairs), str(len(ed.pairs)))
# a corner that is done is placed again by clicking it on the video
gid0 = sorted(ed.members)[2]
vx, vy = ed.group_video(gid0)
check("clicking a corner that is done makes it wait again (its old place goes)", ed._click_video(vx, vy) is True and ed.cur_pin == gid0 and len(ed.pairs) == 6 and ed._pin_state(gid0) == "todo")
ed._click_drone(*drone_of_group(ed, gid0))
check("and the new place is taken", len(ed.pairs) == 7 and ed._pin_state(gid0) == "done")

# modes: in the Align mode corners are not dragged, in the edit mode they are
ed.mode_var.set("align")
ed._on_mode()
ex, ey = ed.vpane.to_view(vx, vy)
check("in the Align mode a press on a corner grabs nothing", ed._on_press("video")(vx, vy, ex, ey) is False)
ed.mode_var.set("edit")
ed._on_mode()
check("in the edit mode it grabs the corner", ed._on_press("video")(vx, vy, ex, ey) is True)
ed._on_release()
# the views draw in both modes
img = np.zeros((500, 700, 3), np.uint8)
ed.mode_var.set("align")
ed._on_mode()
for pn, pane in (("video", ed.vpane), ("drone", ed.dpane), ("plan", ed.ppane)):
    ed._draw(img, pn, pane)
check("the pins are drawn on the video and the pairs on the drone picture", True)
ed.close()

# opened again: aligned, in metres, in the edit mode, the pairs and the real length still there
ed = app.open_zone_editor(ask_drone=False)
root.update()
check("opened again it is aligned with the scale and the 7 pairs and starts in the edit mode", ed.aligned and abs(ed.scale - 0.05) < 1e-9 and len(ed.pairs) == 7 and ed.mode == "edit")
ed.close()

# the Align saved by the old Align window (the data format is the same) opens here
app.run3_align_var.set(align_json)
ed = app.open_zone_editor(ask_drone=False)
root.update()
check("an Align saved by the Align window opens here too", ed.aligned and ed.mode == "edit" and ed.drone_img is not None)
ed.close()

# a pure function: an Align that cannot be fitted yet leaves the views empty
app.run3_align_var.set("")
ed = app.open_zone_editor(ask_drone=False)
root.update()
check("an editor without an Align draws the views (empty) without error", all(ed._draw(np.zeros((400, 600, 3), np.uint8), pn, pane) is None for pn, pane in (("video", ed.vpane), ("drone", ed.dpane), ("plan", ed.ppane))))
ed.close()

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
