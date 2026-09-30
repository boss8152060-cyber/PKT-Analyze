"""Headless smoke test of the real PKStudio GUI object (needs torch/cv2/ultralytics).

Run from the Run folder:   python tests/smoke_gui.py
Builds the Tk window without showing it, round-trips the settings, runs the
Run 3 validation / snapshot / warning code and (optionally) the Movement
resolver on a Detection_Records.csv.  It does NOT run YOLO or need a video.

   python tests/smoke_gui.py "<path to ..._Detection_Records.csv>"
"""
import csv
import importlib.util
import os
import sys
import tkinter as tk

os.environ["PK_STUDIO_CUDA_RELAUNCHED"] = "1"   # skip the CUDA relaunch bootstrap
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


# --- road geometry ---
g = app.run3_geometry_vars
for key, val in (("lane_entry_motorcycle_m", "1.5"), ("lane_entry_car_m", "3.25"),
                 ("lane_opp_motorcycle_m", "1.2"), ("lane_opp_car_m", "3.0"), ("median_m", "0")):
    g[key].set(val)
check("W_entry total", app.run3_w_entry_text.get() == "W_entry = 4.750 m", app.run3_w_entry_text.get())
check("W_opp total", app.run3_w_opp_text.get() == "W_opp = 4.200 m", app.run3_w_opp_text.get())

# --- settings round trip ---
st = app.get_settings()
for key in m.RUN3_GEOMETRY_KEYS:
    g[key].set("")
app.set_settings(st)
check("settings round-trip", [g[k].get() for k in m.RUN3_GEOMETRY_KEYS] == ["1.5", "3.25", "1.2", "3.0", "0"])

# --- validation / snapshot ---
check("validate_run3_settings", app.validate_run3_settings() is True)
cfg = app._run3_snapshot_config()
check("snapshot geometry", cfg["geometry"]["lane_entry_car_m"] == 3.25)
g["lane_entry_car_m"].set("abc")
try:
    app.validate_run3_settings()
    check("non-numeric width rejected", False)
except ValueError:
    check("non-numeric width rejected", True)
g["lane_entry_car_m"].set("3.25")
check("warnings is a list", isinstance(app.collect_run3_warnings(), list))

# --- optional: Movement resolver on a real Detection_Records.csv ---
if len(sys.argv) > 1:
    with open(sys.argv[1], encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    tracks, summaries = app._run3_build_tracks(rows, [])
    mv, status, seqs = app._run3_build_movement_index(tracks, summaries)
    from collections import Counter
    print("movement counts:", Counter(mv.values()))
    print("status counts  :", Counter(status.values()))
    check("every track classified", set(mv) == {str(t) for t in tracks})

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
