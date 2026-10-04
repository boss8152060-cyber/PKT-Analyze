"""Perspective calibration from the zones: the zone corners are the ground points, the user types the real length of the zone edges.

A synthetic road (ground plane seen by a tilted camera) with three zones whose real size is known; checks that the window picks the
corners up by itself, guesses the directions, fits the ground transform, reports the sizes in metres, saves everything to the
settings and that Run 3 then maps pixels to the true metres.

Run from the Run folder:   python tests/gui_zonecal.py
"""
import importlib.util
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

# ---- a bent picture: every zone gets its own transform (the page then shows ONE summary line)
CENTRE = np.array([CW / 2.0, CH / 2.0])
WIDE = cv2.getPerspectiveTransform(np.float32([(0, 0), (60, 0), (60, 20), (0, 20)]), np.float32([(100, 330), (1200, 280), (1260, 600), (40, 630)]))


def bent_px(g):
    q = cv2.perspectiveTransform(np.asarray(g, float).reshape(-1, 1, 2), WIDE).reshape(-1, 2)
    x = (q - CENTRE) / (CW / 2.0)
    return x * (1 - 0.18 * (x ** 2).sum(1, keepdims=True)) * (CW / 2.0) + CENTRE


BENT = {"Zone 2": [(6, 6), (18, 6), (18, 12), (6, 12)], "Zone 3": [(24, 8), (36, 8), (36, 14), (24, 14)], "Zone 4": [(42, 6), (54, 6), (54, 12), (42, 12)]}
app.zones = {name: [] for name in m.ZONE_NAMES}
for name, g in BENT.items():
    app.zones[name] = [tuple(float(v) for v in q) for q in bent_px(g)]
app.run3_zone_calibrations = {}
app.run3_cal_mode_var.set("rect")
app.run3_zone_ground_var.set("")
dz = app.open_zone_ground_calibration()
root.update()
for name in BENT:
    num = name.split()[-1]
    dz.set_edge(f"Z{num}.1", f"Z{num}.2", 12, "A")
    dz.set_edge(f"Z{num}.2", f"Z{num}.3", 6, "B")
    dz.set_edge(f"Z{num}.3", f"Z{num}.4", 12, "A")
    dz.set_edge(f"Z{num}.4", f"Z{num}.1", 6, "B")
resb = dz.check()
check("bent picture: the radial trend is found (k1 about 0.18) and the typed lengths then agree", "error" not in resb and 0.10 < dz.lens_k1 < 0.28 and resb["rms_dist_m"] < 0.15, f"k1 {dz.lens_k1:.3f}, rms {resb.get('rms_dist_m')}")
check("every zone has its own fit in the report", set(dz.zone_results) == {"Zone 2", "Zone 3", "Zone 4"} and all("error" not in v for v in dz.zone_results.values()) and "แยกรายโซน" in dz.report.get("1.0", "end"))
check("applying saves the zones' own calibrations", dz.apply() is True and set(app.run3_zone_calibrations) == {"2", "3", "4"} and all(v["kind"] == "poly" for v in app.run3_zone_calibrations.values()))
# outside every zone: the radial trend (centre exact, the edges drift) keeps the metres right where no zone was calibrated
outside = np.array([[58.0, 16.0], [2.0, 18.0], [30.0, 4.0], [50.0, 16.0]])               # near the picture's edges / above the zones
origin_b = np.array(BENT["Zone 2"][0], float)
cfg_lens = app._run3_snapshot_config()
err_lens = np.abs(app._run3_to_metric(bent_px(outside), cfg_lens) - (outside - origin_b)).max()
k1_saved = app.run3_lens_k1_var.get()
app.run3_lens_k1_var.set("")
cfg_nolens = app._run3_snapshot_config()
err_nolens = np.abs(app._run3_to_metric(bent_px(outside), cfg_nolens) - (outside - origin_b)).max()
app.run3_lens_k1_var.set(k1_saved)
check("the lens trend is saved with the calibration", k1_saved != "" and 0.10 < float(k1_saved) < 0.28, k1_saved)
check("outside the zones (near the edges) the trend keeps the metres right, without it they drift", err_lens < 0.8 and err_nolens > 2 * err_lens, f"with {err_lens:.2f} m, without {err_nolens:.2f} m")
page = app.cal_mode_text.get()
check("the page names the base and the zones with their own calibration in ONE line", "ฐาน" in page and "Zone 2" in page and "Zone 4" in page, page)
cfgb = app._run3_snapshot_config()
check("Run 3 gets the zones' own calibrations", set(cfgb["zone_calibrations"]) == {2, 3, 4} and cfgb["zone_calibrations"][3].get("kind") == "poly")
tracks = {1: [{"_point": tuple(bent_px([(26, 9)])[0]), "_center": tuple(bent_px([(26, 9)])[0]), "_zone_num": 3},
              {"_point": tuple(bent_px([(34, 13)])[0]), "_center": tuple(bent_px([(34, 13)])[0]), "_zone_num": 3}],
          2: [{"_point": tuple(bent_px([(44, 7)])[0]), "_center": tuple(bent_px([(44, 7)])[0]), "_zone_num": 4},
              {"_point": tuple(bent_px([(52, 11)])[0]), "_center": tuple(bent_px([(52, 11)])[0]), "_zone_num": 4}]}
app._run3_attach_metric(tracks, cfgb)
d_mid = float(np.hypot(*(np.array(tracks[1][0]["_m"]) - np.array(tracks[1][1]["_m"]))))
d_right = float(np.hypot(*(np.array(tracks[2][0]["_m"]) - np.array(tracks[2][1]["_m"]))))
true_mid, true_right = math.hypot(8, 4), math.hypot(8, 4)
check("inside a zone the distances are right (the middle zone and the zone at the picture's edge)", abs(d_mid - true_mid) < 0.25 and abs(d_right - true_right) < 0.25, f"{d_mid:.2f} / {d_right:.2f} (true {true_mid:.2f})")
dz2 = app.open_zone_ground_calibration()
root.update()
check("reopening keeps the typed lengths", dz2.len_vars[("Z3.1", "Z3.2")].get() == "12")
dz2.per_zone_var.set(False)
dz2.apply()
check("without the tick the zones' own calibrations are removed again", app.run3_zone_calibrations == {})
app.zones = {name: [] for name in m.ZONE_NAMES}
for name, g in ZONES.items():
    app.zones[name] = [tuple(int(round(v)) for v in q) for q in to_px(g)]

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
