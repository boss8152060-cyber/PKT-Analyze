"""Layout check for every window of the program: no two widgets may share a grid cell (the bug where the
'Known Length P4->P1' field sat under a label and could not be edited).

Run from the Run folder:   python tests/gui_layout.py
Checks the main window (all four steps) and the Perspective Calibration dialog (needs a video: a tiny
synthetic one is made), and that every entry of the calibration dialog is really visible on screen.
"""
import importlib.util
import os
import sys
import tempfile
import time
import tkinter as tk
from tkinter import messagebox

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


def overlaps(container):
    """Grid cells claimed by two children of the same container -> list of descriptions."""
    cells, bad = {}, []
    for child in container.winfo_children():
        try:
            if child.winfo_manager() != "grid":
                continue
            gi = child.grid_info()
        except tk.TclError:
            continue
        r, c = int(gi["row"]), int(gi["column"])
        rs, cs = int(gi.get("rowspan", 1)), int(gi.get("columnspan", 1))
        for rr in range(r, r + rs):
            for cc in range(c, c + cs):
                if (rr, cc) in cells:
                    bad.append(f"{cells[(rr, cc)]} / {child.winfo_class()}:{str(child.cget('text')) if 'text' in child.keys() else ''} at row {rr}, column {cc}")
                else:
                    cells[(rr, cc)] = f"{child.winfo_class()}:{str(child.cget('text')) if 'text' in child.keys() else ''}"
    return bad


def walk(widget, out):
    out.extend(overlaps(widget))
    for ch in widget.winfo_children():
        walk(ch, out)


root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
root.deiconify()
for i in range(4):
    app.notebook.select(i)
    root.update()
bad = []
walk(app.root, bad)
check("main window: no two widgets share a grid cell", not bad, "; ".join(bad[:5]))

tmp = tempfile.mkdtemp(prefix="pk_cal_")
vp = os.path.join(tmp, "v.mp4")
w = cv2.VideoWriter(vp, cv2.VideoWriter_fourcc(*"mp4v"), 30.0, (640, 360))
for i in range(20):
    w.write(np.full((360, 640, 3), 80, dtype=np.uint8))
w.release()
app.video_var.set(vp)
before = set(root.winfo_children())
messagebox.showerror = lambda *a, **k: None
app.open_perspective_calibration()
for _ in range(15):
    root.update()
    time.sleep(0.02)
dialogs = [c for c in root.winfo_children() if c not in before and isinstance(c, tk.Toplevel)]
check("calibration dialog opened", len(dialogs) == 1)
top = dialogs[0]
bad = []
walk(top, bad)
check("calibration dialog: no two widgets share a grid cell", not bad, "; ".join(bad[:5]))
entries = []


def find_entries(wd):
    for ch in wd.winfo_children():
        if ch.winfo_class() in ("TEntry", "Entry"):
            entries.append(ch)
        find_entries(ch)


find_entries(top)
check("calibration dialog: Frame + four Known Length entries are all shown and fit in the window",
      len(entries) >= 5 and all(e.winfo_ismapped() and e.winfo_width() > 20 and e.winfo_rootx() + e.winfo_width() <= top.winfo_rootx() + top.winfo_width() + 2 for e in entries),
      f"{len(entries)} entries")
apply_btn = [b for b in top.winfo_children()[0].winfo_children() if False]
texts = []


def collect_buttons(wd):
    for ch in wd.winfo_children():
        if ch.winfo_class() == "TButton":
            texts.append((str(ch.cget("text")), ch.winfo_ismapped(), ch.winfo_rooty() + ch.winfo_height() <= root.winfo_screenheight()))
        collect_buttons(ch)


collect_buttons(top)
check("calibration dialog: Apply Calibration and Cancel are visible on screen", all(v for t, mapped, v in texts if "Apply" in t or t == "Cancel") and any("Apply" in t for t, _, _ in texts), str(texts))
check("calibration dialog fits the screen", top.winfo_height() <= root.winfo_screenheight(), f"{top.winfo_height()} / {root.winfo_screenheight()}")
top.destroy()

# ---- points of an earlier calibration come back (no need to click them again) ----
for var, xy in zip((app.run3_perspective_p1_var, app.run3_perspective_p2_var, app.run3_perspective_p3_var, app.run3_perspective_p4_var),
                   ("100.5,50", "500,60", "520,300", "90,310")):
    var.set(xy)
before = set(root.winfo_children())
app.open_perspective_calibration()
for _ in range(10):
    root.update()
    time.sleep(0.02)
top2 = [c for c in root.winfo_children() if c not in before and isinstance(c, tk.Toplevel)][0]
check("calibration dialog shows the four saved points again", top2.calibration_state["points"] == [(100.5, 50.0), (500.0, 60.0), (520.0, 300.0), (90.0, 310.0)],
      str(top2.calibration_state["points"]))
top2.destroy()
for var in (app.run3_perspective_p1_var, app.run3_perspective_p2_var, app.run3_perspective_p3_var, app.run3_perspective_p4_var):
    var.set("")
before = set(root.winfo_children())
app.open_perspective_calibration()
for _ in range(10):
    root.update()
    time.sleep(0.02)
top3 = [c for c in root.winfo_children() if c not in before and isinstance(c, tk.Toplevel)][0]
check("with nothing saved the picture starts empty", top3.calibration_state["points"] == [])
top3.destroy()

# ---- test measurement: a perfect 400x200 px rectangle that is 4 m x 2 m  ->  100 px/m ----
for var, xy in zip((app.run3_perspective_p1_var, app.run3_perspective_p2_var, app.run3_perspective_p3_var, app.run3_perspective_p4_var),
                   ("100,100", "500,100", "500,300", "100,300")):
    var.set(xy)
for var, v in zip((app.run3_perspective_l12_var, app.run3_perspective_l23_var, app.run3_perspective_l34_var, app.run3_perspective_l41_var), ("4", "2", "4", "2")):
    var.set(v)
before = set(root.winfo_children())
app.open_perspective_calibration()
for _ in range(10):
    root.update()
    time.sleep(0.02)
top4 = [c for c in root.winfo_children() if c not in before and isinstance(c, tk.Toplevel)][0]
d1 = top4.measure_distance((100, 100), (300, 100))
d2 = top4.measure_distance((120, 140), (120, 260))
check("test measurement: 200 px along the 4 m side = 2.00 m, 120 px along the 2 m side = 1.20 m",
      d1 is not None and abs(d1 - 2.0) < 0.01 and abs(d2 - 1.2) < 0.01, f"{d1}, {d2}")
top4.destroy()

# ---- per-zone calibration: each zone gets its own reference quad ----
app.run3_zone_calibrations = {}
before = set(root.winfo_children())
app.open_perspective_calibration()
for _ in range(10):
    root.update()
    time.sleep(0.02)
top5 = [c for c in root.winfo_children() if c not in before and isinstance(c, tk.Toplevel)][0]
api, st5 = top5.calibration_api, top5.calibration_state
base_points = list(st5["points"])
api["set_mode"](api["mode_labels"][3])                       # "Zone 3"
check("choosing Zone 3 starts an empty reference quad (the base points are kept aside)", st5["points"] == [] and api["ctx"]["mode"] == "3")
st5["points"] = [(200.0, 100.0), (400.0, 100.0), (400.0, 200.0), (200.0, 200.0)]
for var, v in zip(api["length_vars"], ("8", "4", "8", "4")):
    var.set(v)
api["apply"]()
check("Apply in zone mode stores the quad for that zone only", set(app.run3_zone_calibrations) == {"3"} and app.run3_zone_calibrations["3"]["lengths"] == [8.0, 4.0, 8.0, 4.0])
check("the dialog stays open after a zone is saved", top5.winfo_exists())
api["set_mode"](api["mode_labels"][0])                       # back to the base calibration
check("back on the base calibration its own points and lengths come back", st5["points"] == base_points and [v.get() for v in api["length_vars"]] == ["4", "2", "4", "2"], str(st5["points"]))
api["set_mode"](api["mode_labels"][3])
check("Zone 3 shows its saved quad again", len(st5["points"]) == 4 and st5["points"][0] == (200.0, 100.0))
st = app.get_settings()
check("settings carry the zone calibration", st["run3"]["zone_calibrations"]["3"]["points"][0] == [200.0, 100.0])
app.run3_zone_calibrations = {}
app.set_settings(st)
check("settings restore the zone calibration", set(app.run3_zone_calibrations) == {"3"})
check("clean copy used by Run 3 has numbers and a zone number", app._run3_snapshot_config()["zone_calibrations"][3]["lengths"] == [8.0, 4.0, 8.0, 4.0])
api["delete_zone"]()
check("delete removes the zone calibration", app.run3_zone_calibrations == {})
# ---- a zone with its corners drawn: the corners appear as P1-P4 by themselves, only the four lengths are left to type ----
app.zones["Zone 4"] = [(300, 500), (700, 500), (720, 620), (280, 620)]
app.zones["Zone 5"] = [(900, 300), (1100, 300), (1130, 330), (1130, 450), (900, 450), (880, 420)]            # six corners
app.zones["Zone 3"] = []
api["set_mode"](api["mode_labels"][4])                       # "Zone 4"
check("a zone with 4 corners: P1-P4 are its corners, nothing to click", st5["points"] == [(300.0, 500.0), (700.0, 500.0), (720.0, 620.0), (280.0, 620.0)], str(st5["points"]))
for var, v in zip(api["length_vars"], ("12", "4.2", "12", "4.2")):
    var.set(v)
api["apply"]()
check("only typing the lengths and saving stores the zone calibration", app.run3_zone_calibrations.get("4", {}).get("lengths") == [12.0, 4.2, 12.0, 4.2])
api["set_mode"](api["mode_labels"][5])                       # "Zone 5": six corners
check("a zone with more corners is reduced to its 4 main corners", len(st5["points"]) == 4 and all(p in [(900.0, 300.0), (1100.0, 300.0), (1130.0, 330.0), (1130.0, 450.0), (900.0, 450.0), (880.0, 420.0)] for p in st5["points"]), str(st5["points"]))
api["set_mode"](api["mode_labels"][6])                       # "Zone 6": not drawn
check("a zone that is not drawn starts empty", st5["points"] == [])
api["set_mode"](api["mode_labels"][0])
bad = []
walk(top5, bad)
check("calibration dialog with the new controls: still no overlapping widgets", not bad, "; ".join(bad[:4]))
top5.destroy()
root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
