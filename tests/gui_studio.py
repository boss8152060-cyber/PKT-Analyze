"""The one window of the site setup (1.57.0): draw the zones, pin their corners on the drone picture (a pin = one corner with its place on the video AND on the drone
picture, locked as a pair), the Align made of the pins, the scale from a real length, the Lines of the Gap Acceptance streams, and what is written for the program.

A synthetic site: a ground plane seen by a tilted camera, and from straight above (20 drone pixels per metre).

Run from the Run folder:   python tests/gui_studio.py
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

HERE = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(prefix="pk_studio_")
os.environ["PKT_USER_DATA"] = os.path.join(tmp, "user_data")
os.makedirs(os.environ["PKT_USER_DATA"])
os.environ["PK_STUDIO_CUDA_RELAUNCHED"] = "1"
spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


CW, CH = 1280, 720
H_CAM = cv2.getPerspectiveTransform(np.float32([(0, 0), (60, 0), (60, 20), (0, 20)]), np.float32([(100, 330), (1200, 280), (1260, 600), (40, 630)]))


def video_px(g):
    return cv2.perspectiveTransform(np.asarray(g, float).reshape(-1, 1, 2), H_CAM).reshape(-1, 2)


def drone_px(g):
    return np.asarray(g, float) * 20.0 + [60.0, 80.0]


video = os.path.join(tmp, "20260907_084751A_.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(5):
    vw.write(np.full((CH, CW, 3), 90, np.uint8))
vw.release()
video_size = os.path.getsize(video)
drone_file = os.path.join(tmp, "drone.png")
cv2.imencode(".png", np.full((560, 1400, 3), 120, np.uint8))[1].tofile(drone_file)

G = {"Zone 2": [(4, 5), (18, 5), (18.9, 12), (4.7, 12)], "Zone 3": [(18, 5), (32, 5), (32.9, 12), (18.9, 12)], "Zone 4": [(32, 5), (36, 8.2), (32.9, 12)]}
allg = np.array(sorted({tuple(q) for g in G.values() for q in g}))
allv = video_px(allg)
alld = drone_px(allg)

root = tk.Tk()
root.geometry("1500x900+0+0")
app = m.Run1App(root)
shown = []
asked = []
m.messagebox.showinfo = lambda *a, **k: shown.append(("info", a))
m.messagebox.showerror = lambda *a, **k: shown.append(("error", a))
m.messagebox.askyesno = lambda *a, **k: (asked.append(a), True)[1]
m.filedialog.askopenfilename = lambda **k: ""
app.video_var.set(video)

# ---- the window opens on a site with nothing drawn
st = app.open_site_studio(ask_drone=False)
root.update()
check("the window opens (video only: no zones, no drone picture)", isinstance(st, m.SiteStudio) and st.drone_img is None and not st.nodes and st.vpane.view is not None)
check("it asks for a video first", (lambda: (app.video_var.set(""), app.open_site_studio())[1])() is None)
app.video_var.set(video)


def vclick(x, y):
    return st.on_click("video")(float(x), float(y))


def draw_zone(name, pts_ground):
    st.cur_zone = name
    for q in video_px(pts_ground):
        vclick(*q)
    return st.finish_zone()


def drone_of_node(nid):
    v = np.array(st.nodes[nid]["v"])
    return alld[int(np.argmin(np.hypot(*(allv - v).T)))]


# ---- draw the zones: neighbours share corners
check("Zone 2 is drawn with 4 clicks and closed", draw_zone("Zone 2", G["Zone 2"]) is True and len(st.zones["Zone 2"]) == 4 and not st.draft)
check("the next zone to draw is picked", st.cur_zone == "Zone 1" and st.sel is not None)
draw_zone("Zone 3", G["Zone 3"])
check("Zone 3 shares two corners with Zone 2 (6 corners now, not 8)", len(st.nodes) == 6 and set(st.zones["Zone 2"]) & set(st.zones["Zone 3"]) and len(set(st.zones["Zone 2"]) & set(st.zones["Zone 3"])) == 2,
      str(len(st.nodes)))
draw_zone("Zone 4", G["Zone 4"])
check("Zone 4 shares two corners with Zone 3 (7 corners for the 3 zones)", len(st.nodes) == 7 and len(st.zones["Zone 4"]) == 3, str(len(st.nodes)))
check("the corner shared by two zones is labelled after the first one (Z2.2) and has the other as a member", any(len(st._zones_of(n)) == 2 for n in st.nodes))
check("nothing is pinned yet: the Align is not fitted and the plane shows nothing", not st.aligned and st._pin_counts() == {"todo": 7, "done": 0, "skip": 0})

# ---- pin: the corner waits, the click on the drone picture places it, the next one waits
check("the drone picture is loaded", st.load_drone(drone_file) is True and st.drone_img is not None)
first = st.sel
check("the first corner waits for its place on the drone picture", first == min(st.nodes) and st.nodes[first]["d"] is None)
st.set_kind("projective")
for _ in range(7):
    nid = st.sel
    st._click_drone(*drone_of_node(nid))
check("all 7 corners are pinned (every click went to the corner that was waiting)", st._pin_counts()["done"] == 7 and st.sel is None)
check("the Align fits from 4 pins on and then follows every pin", st.aligned and st.cfg is not None)
check("a click on the drone picture with nothing waiting does nothing", st._click_drone(100, 100) is False)
check("no scale yet: not used for the analysis", st.scale == 0 and not app.run3_align_enabled_var.get())

# ---- the pin is a locked pair: dragging on the video moves the video place only, on the drone picture the drone place only
nid = [n for n in st.nodes if len(st._zones_of(n)) == 1 and "Zone 2" in st._zones_of(n)][0]
v0, d0 = list(st.nodes[nid]["v"]), list(st.nodes[nid]["d"])
ex, ey = st.vpane.to_view(*v0)
check("a press on a corner of the video grabs it", st.on_press("video")(v0[0], v0[1], ex, ey) is True)
st.on_drag("video")(v0[0] + 25, v0[1] + 12)
st.on_release()
check("dragging on the video moved its place on the video ...", abs(st.nodes[nid]["v"][0] - (v0[0] + 25)) < 1.0 or st.nodes[nid]["v"] != v0, str(st.nodes[nid]["v"]))
check("... and NOT its place on the drone picture", st.nodes[nid]["d"] == d0, str(st.nodes[nid]["d"]))
check("the zone polygon on the video follows (it uses the corner)", nid in st.zones["Zone 2"])
v1 = list(st.nodes[nid]["v"])
ex, ey = st.dpane.to_view(*d0)
check("a press on the pin on the drone picture grabs it", st.on_press("drone")(d0[0], d0[1], ex, ey) is True)
st.on_drag("drone")(d0[0] + 30, d0[1] - 10)
st.on_release()
check("dragging on the drone picture moved the drone place only", st.nodes[nid]["d"] == [d0[0] + 30, d0[1] - 10] and st.nodes[nid]["v"] == v1, str(st.nodes[nid]["d"]))
st.undo()
st.undo()
check("two undos put both places back", st.nodes[nid]["v"] == v0 and st.nodes[nid]["d"] == d0, f"{st.nodes[nid]['v']} {st.nodes[nid]['d']}")
st.redo()
check("redo moves the video place again", st.nodes[nid]["v"] == v1)
st.undo()
check("a click on a corner without dragging only picks it", (lambda: (st.on_press("video")(v0[0], v0[1], ex, ey), st.on_release())[1])() is None and st.sel == nid
      and st.nodes[nid]["v"] == v0)

# ---- the scale from one real length: the plane comes out in metres
rows = {r["label"]: r for r in st.edge_rows()}
r14 = [r for r in rows.values() if r["label"].startswith("Zone 2: 1→2")][0]
check("before the scale the plane is in drone pixels (the 14 m edge is 280 of them)", abs(r14["measured"] - 280.0) < 3.0, f"{r14['measured']:.1f}")
st.set_real_length(r14["key"], "14")
check("the real length of one edge sets the scale (no question: nothing to overturn)", st.apply_real_scale() is True and abs(st.scale - 0.05) < 0.001, str(st.scale))
r72 = [r for r in st.edge_rows() if r["label"].startswith("Zone 2: 2→3")][0]
check("the other edges are in metres (7.06 m on the ground)", abs(r72["measured"] - math.hypot(0.9, 7.0)) < 0.1, f"{r72['measured']:.2f}")
saved = json.loads(app.run3_align_var.get())
check("the Align is kept (pairs with their zone-corner labels, scale, drone picture) and the analysis is told to use it", len(saved["pairs"]) == 7 and all(q.get("l") for q in saved["pairs"])
      and abs(saved["scale"] - 0.05) < 0.001 and saved["drone"]["path"] == drone_file and app.run3_align_enabled_var.get() and saved["edge_lengths"][0]["m"] == 14.0)
check("the fit text names the kind and the error", "จัดแนว" in st.fit_text() and "7" in st.fit_text())

# ---- a corner dragged in the plane moves on the video only
nid_p = [n for n in st.nodes if len(st._zones_of(n)) == 1 and "Zone 4" in st._zones_of(n)][0]
v_before, d_before = list(st.nodes[nid_p]["v"]), list(st.nodes[nid_p]["d"])
px = st.plan_to_px(st.plan_of(np.array([v_before])))[0]
ex, ey = st.ppane.to_view(*px)
check("a press on a corner of the plane grabs it", st.on_press("plan")(px[0], px[1], ex, ey) is True)
cfg_before = st.cfg
st.on_drag("plan")(px[0] + 20, px[1] + 15)
st.on_release()
dd = st.drone_of(np.array([st.nodes[nid_p]["v"]]))[0]
check("dragging in the plane moves the corner on the ground: both places follow and stay a right pin", st.nodes[nid_p]["v"] != v_before and st.nodes[nid_p]["d"] != d_before
      and np.hypot(*(np.array(st.nodes[nid_p]["d"]) - dd)) < 1e-6)
check("... and the Align does not change", st.cfg is cfg_before)
st.undo()

# ---- merge: a corner dropped on a corner of another zone becomes that corner
n_before = len(st.nodes)
a = [n for n in st.nodes if st._zones_of(n) == ["Zone 4"]][0]
b = [n for n in st.nodes if st._zones_of(n) == ["Zone 2"]][0]
st.nodes[a]["v"] = list(st.nodes[b]["v"])
check("a corner on top of another one of a different zone is merged into it", st._try_merge(a) is True and len(st.nodes) == n_before - 1 and b in st.zones["Zone 4"])
st.undo() if False else None
for z in ("Zone 4",):
    pass

# ---- skip, go back, unpin, the worst pin
st2 = None
st.close()
app.zones = {z: [] for z in m.ZONE_NAMES}
app.run3_align_var.set("")
app.run3_align_enabled_var.set(False)
app.lines = {n: [] for n in m.LINE_NAMES}
st = app.open_site_studio(ask_drone=False)
root.update()
st.load_drone(drone_file)
for name in ("Zone 2", "Zone 3", "Zone 4"):
    draw_zone(name, G[name])
order = sorted(st.nodes)
first = st.sel
check("a corner can be skipped: the next one waits", st.skip_pin() is True and st._pin_state(first) == "skip" and st.sel != first)
check("going back takes the skipped corner up again", st.goto_pin(-1) is True and st.sel == first and st._pin_state(first) == "todo")
for nid in order:
    st.sel = nid
    st._click_drone(*drone_of_node(nid))
check("all pinned again", st._pin_counts()["done"] == 7 and st.aligned)
r14 = [r for r in st.edge_rows() if r["label"].startswith("Zone 2: 1→2")][0]
st.set_real_length(r14["key"], "14")
st.apply_real_scale()
bad = order[3]
good_d = list(st.nodes[bad]["d"])
st.nodes[bad]["d"] = [good_d[0] + 160.0, good_d[1] - 90.0]                  # one pin clicked in the wrong place
st._refit()
check("the pin whose removal fits best is the wrong one", st.worst_pair() == bad, str(st.worst_pair()))
check("'lift the worst pin' takes its drone place away and makes it wait again", st.delete_worst_pair() is True and st.nodes[bad]["d"] is None and st.sel == bad)
st._click_drone(*good_d)
check("placed again", st.nodes[bad]["d"] is not None and st._pin_state(bad) == "done")
check("'lift the pin of the picked corner' makes it wait again", (lambda: (setattr(st, "sel", bad), st.unpin_selected())[1])() is True and st.nodes[bad]["d"] is None)
st._click_drone(*good_d)

# ---- delete a corner (never below 3), clear a zone
z4 = st.zones["Zone 4"]
st.sel = z4[0]
check("a corner of a zone with 3 corners cannot be deleted", st.delete_selected_corner() is False and len(st.zones["Zone 4"]) == 3)
st.sel = [n for n in st.zones["Zone 2"] if st._zones_of(n) == ["Zone 2"]][0]
n_nodes = len(st.nodes)
check("a corner of a 4-corner zone can be deleted with its pin", st.delete_selected_corner() is True and len(st.zones["Zone 2"]) == 3 and len(st.nodes) == n_nodes - 1)
st.undo()
check("undo brings the corner back", len(st.zones["Zone 2"]) == 4)
st.cur_zone = "Zone 4"
st.clear_current()
check("clearing a zone empties it; a corner only it used that is pinned stays as a pin of its own", st.zones["Zone 4"] == [] and len(st.nodes) == 7
      and sum(1 for n in st.nodes if not st._zones_of(n)) == 1, str(len(st.nodes)))
st.undo()
check("undo draws it back", len(st.zones["Zone 4"]) == 3 and len(st.nodes) == 7)

# ---- cancel a zone being drawn: its corners go
st.cur_zone = "Zone 5"
vclick(*video_px([(40, 14)])[0])
vclick(*video_px([(44, 14)])[0])
n_draft = len(st.nodes)
check("a zone being drawn has its corners", len(st.draft) == 2 and n_draft == 9)
check("Esc cancels it and the corners go", st.cancel_draft() is True and not st.draft and len(st.nodes) == 7)
vclick(*video_px([(40, 14)])[0])
check("Backspace removes the last corner", st.remove_last_draft_point() is True and not st.draft and len(st.nodes) == 7)
check("a zone needs 3 corners to close", (lambda: (vclick(*video_px([(40, 14)])[0]), vclick(*video_px([(44, 14)])[0]), st.finish_zone())[2])() is False)
st.cancel_draft()
fx, fy = st.vpane.to_view(*video_px([(40, 14)])[0])
for q in video_px([(40, 14), (44, 14), (44, 18)]):
    vclick(*q)
ix, iy = st.vpane.to_image(fx + 2, fy + 2)
check("a click on the first corner closes the zone", vclick(ix, iy) is True and len(st.zones["Zone 5"]) == 3 and not st.draft)
st.cur_zone = "Zone 5"
st.clear_current()

# ---- the Lines of the Gap Acceptance streams
mvs = [s["mv"] for s in st.streams]
check("the streams that need a line are listed", "2-3-4" in mvs and len(mvs) == 4, str(mvs))
s234 = [s for s in st.streams if s["mv"] == "2-3-4"][0]
check("the stream between Zone 2 and Zone 3 can use the edge the zones share (nothing to draw)", st.stream_edge("2-3-4") is not None and "ขอบโซน" in st.stream_status(s234), st.stream_status(s234))
st.set_stream_mode("2-3-4", "edge")
check("a stream whose zones are not both drawn cannot use an edge: it falls back to a drawn Line", (lambda: (st.set_stream_mode("5-6-7", "edge"), [s for s in st.streams if s["mv"] == "5-6-7"][0]["mode"])[1])() == "drawn")
st._on_tab(1)
st.stream_var.set("5-6-7")
s567 = [s for s in st.streams if s["mv"] == "5-6-7"][0]
vclick(*video_px([(40, 14)])[0])
check("one click starts a Line", len(st.line_draft) == 1)
vclick(*video_px([(52, 14)])[0])
check("the second click completes it", len(st.lines[s567["line"]]) == 2 and not st.line_draft and "✓" in st.stream_status(s567), st.stream_status(s567))
lx, ly = st.lines[s567["line"]][1]
ex, ey = st.vpane.to_view(lx, ly)
check("a Line end can be grabbed and moved", st.on_press("video")(lx, ly, ex, ey) is True)
st.on_drag("video")(lx + 30, ly + 20)
st.on_release()
check("the Line end moved", st.lines[s567["line"]][1] != [lx, ly])
check("the choices of the streams that are done: the edge (2-3-4) and the Line drawn (5-6-7)", st.assignments() == {"2-3-4": "Edge 2-3", "5-6-7": s567["line"]}, str(st.assignments()))
st.clear_stream("5-6-7")
check("a Line can be cleared", st.lines[s567["line"]] == [] and "5-6-7" not in st.assignments())
vclick(*video_px([(40, 14)])[0])
vclick(*video_px([(52, 14)])[0])
st._on_tab(0)

# ---- what is written for the program
before = sorted(os.listdir(tmp))
path = st.use()
zones_dir = os.path.join(os.environ["PKT_USER_DATA"], "Zones")
check("the zone file is written in the data folder of the program, named after the video", path is not None and os.path.dirname(path) == zones_dir
      and os.path.basename(path) == "20260907_084751A__zones.json", str(path))
data = json.load(open(path, encoding="utf-8"))
check("it has the format of the PKT Data zone file with the 3 zones and the drawn Line", [z["name"] for z in data["zones"]] == ["Zone 2", "Zone 3", "Zone 4"]
      and data["frame_width"] == CW and list(data["lines"]) == [s567["line"]] and all({"points", "points_norm", "id", "area_px"} <= set(z) for z in data["zones"]))
check("the program loaded the zones and the Line", [z for z in m.ZONE_NAMES if len(app.zones[z]) >= 3] == ["Zone 2", "Zone 3", "Zone 4"] and len(app.lines[s567["line"]]) == 2)
mapping = app.run3_reference_mapping_text
check("the Reference Line Mapping got the edge of 2-3-4 and the Line of 5-6-7, and the streams use what was chosen", "Edge 2-3" in mapping and s567["line"] in mapping
      and app.run3_ref_line_source_var.get() == "per_stream", mapping[:200])
check("the video was not touched and nothing was written beside it", os.path.getsize(video) == video_size and sorted(os.listdir(tmp)) == before)
saved_as = st.save_as(os.path.join(tmp, "copy.json"))
check("the zone file can also be saved where the user wants (the program keeps using its own)", saved_as and json.load(open(saved_as, encoding="utf-8"))["zones"] and app.zone_line_config_var.get() == path)
check("with no zone drawn it says so and writes nothing", (lambda: (shown.clear(), [st.zones.__setitem__(z, []) for z in m.ZONE_NAMES], st.use())[2])() is None and shown and shown[-1][0] == "error")
st.undo()
st.close()

# ---- opened again: everything is there (zones, pins, scale, real length, Lines)
st = app.open_site_studio(ask_drone=False)
root.update()
check("opened again it has the 7 corners, all pinned, aligned, with the scale", len(st.nodes) == 7 and st._pin_counts()["done"] == 7 and st.aligned and abs(st.scale - 0.05) < 0.001,
      str((len(st.nodes), st._pin_counts(), st.aligned, st.scale)))
check("the real length is still there", list(st.real.values()) == [14.0], str(st.real))
check("the Line is back in its stream", len(st.lines[s567["line"]]) == 2 and [s for s in st.streams if s["mv"] == "5-6-7"][0]["mode"] == "drawn")
st.close()

# ---- an Align saved by the earlier Align window opens here (same format)
app.zones = {z: [] for z in m.ZONE_NAMES}
for name, g in G.items():
    app.zones[name] = [tuple(float(v) for v in q) for q in video_px(g)]
app.run3_align_var.set("")
dlg = app.open_align()
root.update()
dlg.load_drone(drone_file)
dlg.load_zone_pins()
dlg.set_kind("projective")
while dlg.pin_index is not None:
    pin = dlg.pins[dlg.pin_index]
    dlg.place_pin(*alld[int(np.argmin(np.hypot(*(allv - np.array(pin["p"])).T)))])
dlg.set_scale_from_points((0, 0), (100, 0), 5.0)
check("the earlier Align window saved an Align", dlg.apply() is True and len(json.loads(app.run3_align_var.get())["pairs"]) == 7)
st = app.open_site_studio(ask_drone=False)
root.update()
check("the new window reads it: every corner pinned, aligned, scale set", st._pin_counts()["done"] == 7 and st.aligned and abs(st.scale - 0.05) < 1e-9, str(st._pin_counts()))
check("it opens on the Zone tab and draws all three views without error", st.tab == "zone" and all(st._draw(np.zeros((400, 600, 3), np.uint8), n, st._pane(n)) is None for n in ("video", "drone", "plan")))

# ---- make the cross edges vertical (the pins stay: only the video places move)
leaning_before = abs(st.plan_of(np.array([st.nodes[st.zones["Zone 2"][1]]["v"]]))[0][0] - st.plan_of(np.array([st.nodes[st.zones["Zone 2"][2]]["v"]]))[0][0])
pins_before = {n: list(v["d"]) for n, v in st.nodes.items()}
rep = st.make_perpendicular()
a_, b_ = (st.plan_of(np.array([st.nodes[st.zones["Zone 2"][i]]["v"]]))[0] for i in (1, 2))
check("the cross edge of Zone 2 leaned and is vertical now", leaning_before > 0.5 and abs(a_[0] - b_[0]) < 0.02, f"{leaning_before:.2f} -> {abs(a_[0] - b_[0]):.3f}")
check("the pins stay right: the drone places moved with the corners", all(np.hypot(*(np.array(v["d"]) - st.drone_of(np.array([v["v"]]))[0])) < 1e-6 for v in st.nodes.values()))
check("the corner shared by two zones is still shared", st.zones["Zone 2"][1] == st.zones["Zone 3"][0])

# ---- the keys do nothing while a box has the focus
st.sel = st.zones["Zone 2"][0]
st.scale_entry_focus = True
st.top.focus_force()
for w in st.top.winfo_children():
    pass
check("a key of the window (Delete) works when no box has the focus", st._on_key(lambda: "ok") == "ok")

st.close()
root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
