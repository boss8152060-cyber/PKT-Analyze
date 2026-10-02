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

# --- Gap Acceptance conflict table given by the user ---
check("Gap conflict table", m.RUN3_GAP_CONFLICT_MAP == {
    "1-3-4": ["2-3-4"],
    "1-3-6-7": ["2-3-4", "5-6-7", "5-6-3-1"],
    "5-6-3-1": ["2-3-4", "1-3-6-7"],
}, str(m.RUN3_GAP_CONFLICT_MAP))

check("Gap paths and conflict table cover the same subject movements", set(m.GAP_PATHS) == set(m.RUN3_GAP_CONFLICT_MAP))

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

# --- worker threads reach the UI only through the queue (no Tk call from the thread) ---
import threading
import time
seen = []
th = threading.Thread(target=lambda: (app.update_ui(status="from worker"),
                                      app.post_ui(lambda: seen.append(threading.current_thread() is threading.main_thread()))))
th.start()
th.join()
end = time.time() + 1.0
while time.time() < end and not seen:
    root.update()
    time.sleep(0.01)
check("UI queue: callback posted by a worker thread runs on the main thread", seen == [True] and app.status_var.get() == "from worker", str(seen))
check("default paths are relative to the program folder", m.DEFAULT_MODEL.endswith(os.path.join("PK STUDIO", "Input", "Model", "best.pt")), m.DEFAULT_MODEL)

# --- window layout: four steps + a run bar with the ready-to-run list ---
check("four steps in order", [app.notebook.tab(i, "text") for i in range(4)] == ["① คลิปวิดีโอ", "② ทางแยก", "③ ตัวชี้วัด", "④ ตรวจจับและติดตาม"])
app.refresh_checklist()
check("run bar lists model / clips / zones / lines / widths / output", set(app.check_labels) == {"model", "clips", "zones", "lines", "widths", "output"})
check("no clips yet: the START text has no count", app.start_button.cget("text") == "▶ เริ่มวิเคราะห์", app.start_button.cget("text"))
app.clips_panel.add_videos([("C:/x/a.mp4", "S/d")])
app.refresh_checklist()
check("a newly added clip starts with no result video", app.clips_panel.clips[0]["save_video"] is False)
app.trajectory_position_var.set("Top")
app.run3_perspective_enabled_var.set(True)
check("warning: road-plane calibration with Trajectory Position = Top", any("Trajectory Position" in w for w in app.collect_run3_warnings()))
app.trajectory_position_var.set("Bottom")
check("no such warning with Bottom", not any("Trajectory Position" in w for w in app.collect_run3_warnings()))
app.run3_perspective_enabled_var.set(False)
app.draw_center_var.set(True)
check("runtime snapshot knows about the decision-point option", app._runtime_snapshot().get("show_decision_point") is True)
app.draw_center_var.set(False)
check("one clip is a list of one", "1 คลิป" in app.start_button.cget("text"), app.start_button.cget("text"))
app.clips_panel.clear()
from tkinter import messagebox as _mb
_shown = []
_mb.showinfo = lambda *a, **k: _shown.append(a)
app.notebook.select(2)
app.start_analysis()
check("START with an empty list explains what to do and goes to step 1", len(_shown) == 1 and app.notebook.index(app.notebook.select()) == 0 and not app.running, str(_shown))
check("every indicator has its own switch in its group", all(hasattr(app, n) for n in ("run3_ldp_enabled_var", "run3_lc_enabled_var", "run3_gap_enabled_var", "run3_ttc_enabled_var", "run3_pet_enabled_var", "run3_speed_enabled_var")))
check("reference mapping text widget exists (Gap Acceptance group)", hasattr(app, "run3_reference_text"))

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
