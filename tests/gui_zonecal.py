"""Perspective calibration from the zones: the zone corners are the ground points, the user types the real length of the zone edges.

A synthetic road (ground plane seen by a tilted camera) with three zones whose real size is known; checks that the window picks the
corners up by itself, guesses the directions, fits the ground transform, reports the sizes in metres, saves everything to the
settings and that Run 3 then maps pixels to the true metres.

Run from the Run folder:   python tests/gui_zonecal.py
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


tmp = tempfile.mkdtemp(prefix="pk_zonecal_")
CW, CH = 1280, 720
H_GROUND = np.array([[18.0, 5.0, 120.0], [-1.0, 16.0, 60.0], [0.0003 * 20, 0.0009 * 20, 1.0]])             # ground metres -> picture pixels


def to_px(g):
    return cv2.perspectiveTransform(np.asarray(g, float).reshape(-1, 1, 2), H_GROUND).reshape(-1, 2)


video = os.path.join(tmp, "road.mp4")
frame = np.full((CH, CW, 3), 90, np.uint8)
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(6):
    vw.write(frame)
vw.release()

# three zones: 1 = the side street (long edge across the main road), 2 and 3 = the main road
ZONES = {"Zone 1": [(22, 22), (28, 22), (28, 34), (22, 34)],
         "Zone 2": [(12, 14), (24, 14), (24, 22), (12, 22)],
         "Zone 3": [(24, 14), (36, 14), (36, 22), (24, 22)]}

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
m.messagebox.showinfo = lambda *a, **k: None
m.messagebox.showerror = lambda *a, **k: None
app.video_var.set(video)
app.zones = {name: [] for name in m.ZONE_NAMES}
for name, g in ZONES.items():
    app.zones[name] = [tuple(int(round(v)) for v in q) for q in to_px(g)]

check("without zones the window refuses to open", (lambda a: (setattr(a, "zones", {n: [] for n in m.ZONE_NAMES}), a.open_zone_ground_calibration())[1])(app) is None)
for name, g in ZONES.items():
    app.zones[name] = [tuple(int(round(v)) for v in q) for q in to_px(g)]

dlg = app.open_zone_ground_calibration()
root.update()
check("the window opens on the zones", dlg is not None and len(dlg.edges) == 12 and dlg.edges[0]["a"] == "Z1.1")
guess = {(e["a"], e["b"]): e["dir"] for e in dlg.edges}
check("the directions are guessed from the picture (main road edges A, across B)",
      guess[("Z2.1", "Z2.2")] == "A" and guess[("Z2.2", "Z2.3")] == "B" and guess[("Z3.1", "Z3.2")] == "A" and guess[("Z1.2", "Z1.3")] == "B" and guess[("Z1.1", "Z1.2")] == "A", str(guess))

res, text = dlg.compute()
check("nothing typed: it says what is missing and writes nothing", "error" in res and app.run3_cal_mode_var.get() == "rect")
dlg.set_edge("Z2.1", "Z2.2", 12)
res, text = dlg.compute()
check("one length is not enough", "error" in res)
dlg.set_edge("Z2.2", "Z2.3", 8)
dlg.set_edge("Z3.1", "Z3.2", 12)
dlg.set_edge("Z1.2", "Z1.3", 12)
res = dlg.check()
check("lengths along and across the road: the transform is found", "error" not in res and res["method"] == "directions+distances", str(res.get("error")))
check("the report lists the size of every zone edge", all(z in dlg.report.get("1.0", "end") for z in ("Zone 1", "Zone 2", "Zone 3")) and "ขอบที่เบี่ยง" in dlg.report.get("1.0", "end"))
dlg.refresh()
root.update()
check("the picture shows the typed length", dlg.last_render is not None and (dlg.last_render != dlg.last_render[0, 0]).any())

pts, labels = dlg._points()
mapped = m.apply_homography(res["H"], np.array(pts))
truth = {}
for name, g in ZONES.items():
    for k, q in enumerate(g, start=1):
        truth[f"Z{name.split()[-1]}.{k}"] = np.array(q, float)
origin = truth["Z1.1"]
err = max(float(np.abs(mapped[i] - (truth[l] - origin)).max()) for i, l in enumerate(labels))
check("every zone corner comes out at its true place (x along the road, origin = first corner)", err < 0.2, f"{err:.4f} m")

check("applying saves the calibration and switches the mode", dlg.apply() is True and app.run3_cal_mode_var.get() == "zones" and app.run3_perspective_enabled_var.get())
cfg = app._run3_snapshot_config()
test_ground = np.array([[16.0, 18.0], [30.0, 20.0], [25.0, 28.0], [34.0, 15.0]])
got = app._run3_to_metric(to_px(test_ground), cfg)
err2 = np.abs(got - (test_ground - origin)).max()
check("Run 3 maps pixels to the true metres", err2 < 0.2, f"{err2:.4f} m")
check("the summary of the run names the method", cfg["perspective"]["method"] == "directions+distances" and app._run3_calibration_mode(cfg) == "Perspective_Homography")

saved = app.get_settings()
app2 = m.Run1App(tk.Toplevel(root))
app2.video_var.set(video)
app2.set_settings(saved)
check("the calibration survives saving and loading the settings", app2.run3_cal_mode_var.get() == "zones" and app2.run3_zone_ground_var.get() == app.run3_zone_ground_var.get())
dlg2 = app.open_zone_ground_calibration()
root.update()
check("reopening shows the typed lengths again", dlg2.len_vars[("Z2.1", "Z2.2")].get() == "12" and dlg2.len_vars[("Z1.2", "Z1.3")].get() == "12")
dlg2.close()

# a wrong length shows up in the check
dlg3 = app.open_zone_ground_calibration()
root.update()
dlg3.set_edge("Z3.2", "Z3.3", 20)                                        # really 8 m
res3 = dlg3.check()
lab3 = dlg3._points()[1]
dev = {frozenset((lab3[r["i"]], lab3[r["j"]])): abs(r["got_m"] - r["given_m"]) for r in res3["dist_report"]}
check("a wrong length shows as a clear error in the check (the conflicting pair deviates, the warning appears)",
      dev[frozenset(("Z3.2", "Z3.3"))] > 3.0 and res3["rms_dist_m"] > 1.0 and "คลาดความยาวเกิน" in dlg3.report.get("1.0", "end"),
      f"{dev[frozenset(('Z3.2', 'Z3.3'))]:.1f} m, rms {res3['rms_dist_m']:.2f}")
dlg3.close()

# the old four-corner window switches the mode back (set by hand here: its window code is covered by smoke_gui / gui_layout)
app.run3_cal_mode_var.set("rect")
check("with the mode 'rect' the zone calibration is not used", app._run3_snapshot_config()["perspective"] is None or "fit" not in app._run3_snapshot_config()["perspective"])

# the page shows only the block of the chosen method (no 4-corner fields next to the zone calibration)
app.run3_cal_mode_var.set("zones")
root.update()
check("zones mode: the zone block is shown, the 4-corner fields are hidden", app.cal_zone_frame.winfo_manager() == "grid" and app.cal_rect_frame.winfo_manager() == "")
app.run3_cal_mode_var.set("rect")
root.update()
check("rect mode: the 4-corner fields are shown, the zone block is hidden", app.cal_rect_frame.winfo_manager() == "grid" and app.cal_zone_frame.winfo_manager() == "")

# the window layout: no two widgets in one grid cell
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


dlg4 = app.open_zone_ground_calibration()
root.update()
check("the zone window: no two widgets share a grid cell", not overlaps(dlg4.top), "; ".join(overlaps(dlg4.top)[:3]))
dlg4.close()
root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
