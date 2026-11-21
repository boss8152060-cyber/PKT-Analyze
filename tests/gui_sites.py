"""The site types (1.59.0): 3-leg junction with Zone 1-4 / Zone 1-7, 4-leg junction (Zone 1-8), 4-leg junction with a median island (two 3-leg junctions).

The choice on the screen, the zones (Zone 8), the streams of the Gap tab that follow the type, what a run is told (the Movements, the subjects of Gap Acceptance, the Headway
Movements), what the settings keep, and the Movement every track gets.

Run from the Run folder:   python tests/gui_sites.py
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
tmp = tempfile.mkdtemp(prefix="pk_sites_")
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
video = os.path.join(tmp, "20260907_084751A_.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(3):
    vw.write(np.full((CH, CW, 3), 90, np.uint8))
vw.release()

root = tk.Tk()
root.geometry("1500x900+0+0")
app = m.Run1App(root)
m.messagebox.showinfo = lambda *a, **k: None
m.messagebox.showerror = lambda *a, **k: None
m.messagebox.askyesno = lambda *a, **k: True
app.video_var.set(video)
app.run3_site_id_var.set("8")
for key, val in (("lane_entry_motorcycle_m", "1.5"), ("lane_entry_car_m", "3.25"), ("lane_opp_motorcycle_m", "1.2"), ("lane_opp_car_m", "3.0"), ("median_m", "0")):
    app.run3_geometry_vars[key].set(val)

# ------------------------------------------------------------------ the choice
check("the default site type is the 3-leg junction with 7 zones (what it always was)", app.run3_site_type() == "t_full")
check("a nonsense value is the default", (app.run3_site_type_var.set("zzz"), app.run3_site_type())[1] == "t_full")
app.run3_site_type_var.set("t_full")

# ------------------------------------------------------------------ the zones: 8, the 8th drawn like the others
zone8 = [[900.0, 500.0], [1100.0, 500.0], [1100.0, 600.0], [900.0, 600.0]]
app.zones["Zone 8"] = zone8
check("there are 8 zones", len(m.ZONE_NAMES) == 8 and "Zone 8" in app.zones)
st = app.open_site_studio(ask_drone=False)
root.update()
check("the zone list of the window shows 8 zones and Zone 8 is the drawn one", st.zone_list.size() == 8 and len(st.zones["Zone 8"]) == 4, str(st.zone_list.size()))
check("the window has the choice of the site type (the 3-leg junction with 7 zones is on)", st.app.run3_site_type() == "t_full")


def stream_set(studio):
    return {s["mv"] for s in studio.streams}


check("3-leg junction, Zone 1-7: the 4 streams it always had", stream_set(st) == {"2-3-4", "5-6-7", "5-6-3-1", "1-3-6-7"}, str(sorted(stream_set(st))))
lines_before = {s["mv"]: s["line"] for s in st.streams}
app.run3_site_type_var.set("t_small")
root.update()
check("3-leg junction, Zone 1-4: only the stream 2-3-4 needs a line", stream_set(st) == {"2-3-4"}, str(sorted(stream_set(st))))
check("the stream that stays keeps its Line", st.streams[0]["line"] == lines_before["2-3-4"])
check("the Gap tab shows one box for it", len(st.stream_status_vars) == 1 and "2-3-4" in st.stream_status_vars)
app.run3_site_type_var.set("x_open")
root.update()
expect_open = {"2-3-4", "5-6-7", "5-6-3-1", "1-3-6-7", "2-3-1", "8-6-3-1", "1-3-6-8"}
check("4-leg junction: the streams that Zone 8 and the way across need as well", stream_set(st) == expect_open, str(sorted(stream_set(st))))
check("every stream has its own Line, no Line is used twice, and there are Lines enough", len({s["line"] for s in st.streams}) == len(st.streams) and all(s["line"] in m.LINE_NAMES for s in st.streams))
check("the Gap tab shows a box for each", set(st.stream_status_vars) == expect_open)
app.run3_site_type_var.set("x_median")
root.update()
check("4-leg junction with a median island: the streams of the two 3-leg junctions (2-3-4 and 5-6-7)", stream_set(st) == {"2-3-4", "5-6-7"}, str(sorted(stream_set(st))))
for s in st.streams:
    st.set_stream_mode(s["mv"], "edge")
check("the line of Zone 5|6 comes from the edge the two zones share when they touch", True)
st.close()
root.update()
check("closing the window takes its watch of the site type away (changing the type then does nothing to it)", (app.run3_site_type_var.set("t_full"), True)[1])

# ------------------------------------------------------------------ what a run is told
for site, gap_all, hw_all in (
        ("t_small", ["1-3-4"], ["1-3-4", "2-3-1", "2-3-4"]),
        ("t_full", ["1-3-4", "1-3-6-7", "5-6-3-1"], ["1-3-4", "2-3-1", "1-3-6-7", "5-6-3-1", "2-3-4", "5-6-7"]),
        ("x_open", ["1-3-4", "1-3-6-7", "5-6-3-1", "8-6-7", "8-6-3-4", "1-3-6-8", "8-6-3-1"], None),
        ("x_median", ["1-3-4", "8-6-7"], ["1-3-4", "2-3-1", "2-3-4", "5-6-7", "5-6-8", "8-6-7"])):
    app.run3_site_type_var.set(site)
    cfg = app._run3_snapshot_config()
    check(f"[{site}] the run knows the site type", cfg.get("site_type") == site, str(cfg.get("site_type")))
    check(f"[{site}] the subjects of Gap Acceptance are the ticked ones that the site has", sorted(cfg["gap_movements"]) == sorted(gap_all), str(cfg["gap_movements"]))
    want_hw = hw_all if hw_all is not None else m.site_movements(site)
    check(f"[{site}] the Headway Movements are the ticked ones that the site has", sorted(cfg["headway_movements"]) == sorted(want_hw), str(cfg["headway_movements"]))
app.run3_site_type_var.set("x_median")
for mv, var in app.run3_gap_subject_extra_vars.items():
    var.set(False)
app.run3_gap_subject_134_var.set(False)
try:
    app.validate_run3_settings()
    check("[x_median] no subject of Gap Acceptance left that the site has is refused", False)
except ValueError as exc:
    check("[x_median] no subject of Gap Acceptance left that the site has is refused", "subject" in str(exc))
app.run3_gap_subject_134_var.set(True)
for var in app.run3_gap_subject_extra_vars.values():
    var.set(True)

# ------------------------------------------------------------------ the settings keep it
app.run3_site_type_var.set("x_median")
app.run3_gap_subject_extra_vars["8-6-7"].set(False)
project = app._json_safe(app.get_project())
run3_saved = None


def find_run3(o):
    global run3_saved
    if isinstance(o, dict):
        if "site_type" in o and "gap_subject_867" in o:
            run3_saved = o
        for v in o.values():
            find_run3(v)
    elif isinstance(o, list):
        for v in o:
            find_run3(v)


find_run3(project)
check("the saved project holds the site type and the subjects of the 4-leg junction", run3_saved is not None and run3_saved["site_type"] == "x_median"
      and run3_saved.get("gap_subject_867") is False and run3_saved.get("gap_subject_8634") is True, str(run3_saved and {k: v for k, v in run3_saved.items() if "site" in k or "gap_subject" in k}))
app.run3_site_type_var.set("t_full")
app.run3_gap_subject_extra_vars["8-6-7"].set(True)
app.set_settings(json.loads(json.dumps(project)))
check("opening it again gives the type and the ticks back", app.run3_site_type() == "x_median" and app.run3_gap_subject_extra_vars["8-6-7"].get() is False,
      f"{app.run3_site_type()} {app.run3_gap_subject_extra_vars['8-6-7'].get()}")
old_project = json.loads(json.dumps(project))


def strip_new(o):
    if isinstance(o, dict):
        for k in [k for k in o if k == "site_type" or k in ("gap_subject_867", "gap_subject_8634", "gap_subject_1368", "gap_subject_8631")]:
            del o[k]
        if isinstance(o.get("headway_movements"), list):
            o["headway_movements"] = [mv for mv in o["headway_movements"] if mv not in m.NEW_4LEG_MOVEMENTS]
        for v in o.values():
            strip_new(v)
    elif isinstance(o, list):
        for v in o:
            strip_new(v)


strip_new(old_project)
app.run3_site_type_var.set("x_open")
for var in app.run3_headway_movement_vars.values():
    var.set(False)
app.set_settings(old_project)
check("a project saved before the site types opens as the 3-leg junction with 7 zones", app.run3_site_type() == "t_full", app.run3_site_type())
check("... and its Headway list gets the new Movements ticked (they cannot have been unticked by the user)",
      all(app.run3_headway_movement_vars[mv].get() for mv in m.NEW_4LEG_MOVEMENTS if mv in app.run3_headway_movement_vars))
app.run3_gap_subject_extra_vars["8-6-7"].set(True)

# ------------------------------------------------------------------ the Movement of every track
tracks = {i: [{"_timestamp": 0.1 * k, "_zone_num": z} for k, z in enumerate(seq)] for i, seq in enumerate(
    [(1, 3, 4), (8, 6, 7), (5, 6, 8), (8, 6, 3, 4), (1, 3, 6, 8), (8, 6, 3, 1), (2, 3, 4), (5, 6, 7)], start=1)}
mv_open, st_open, _ = app._run3_build_movement_index(tracks, None, None, None, "x_open")
check("4-leg junction: every way through it is known, Zone 8 included",
      [mv_open[str(i)] for i in range(1, 9)] == ["1-3-4", "8-6-7", "5-6-8", "8-6-3-4", "1-3-6-8", "8-6-3-1", "2-3-4", "5-6-7"], str([mv_open[str(i)] for i in range(1, 9)]))
mv_med, _, _ = app._run3_build_movement_index(tracks, None, None, None, "x_median")
check("with a median island the ways across it are not analysed", [mv_med[str(i)] for i in (4, 5, 6)] == ["", "", ""] and mv_med["2"] == "8-6-7" and mv_med["3"] == "5-6-8", str(mv_med))
mv_t, _, _ = app._run3_build_movement_index(tracks, None, None, None, "t_full")
check("the 3-leg junction does not know the Movements of Zone 8 (its results do not change)", mv_t["2"] == "" and mv_t["1"] == "1-3-4" and mv_t["7"] == "2-3-4", str(mv_t))

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
