"""End-to-end Run 3 test on a SYNTHETIC scene with known answers (no video, no YOLO).

Run from the Run folder:   python tests/e2e_run3.py
Needs torch/cv2/ultralytics (imports PKStudio.py), creates a hidden Tk window,
writes fake Run 2 CSV files into a temp folder and runs the real
run3_processing(), then checks the CSV/JSON outputs.

Scene (metres; pixel = metre x PPM, PPM = 100, no perspective):
  Zones by x:  zone 2 / 5 : 0-10 m,  zone 3 / 6 : 10-20 m,  zone 4 / 7 : 20-30 m
  A  Motorcycle  2-3-4  y = 0.0   10 m/s (36 km/h)
  B  Car         2-3-4  y = 1.5   10 m/s, same x as A          (side by side)
  C  Motorcycle  5-6-7  y = 8.0    5 m/s (18 km/h)
"""
import csv
import importlib.util
import json
import math
import os
import sys
import tempfile
import tkinter as tk

os.environ["PK_STUDIO_CUDA_RELAUNCHED"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

PPM = 100.0
FPS = 60.0
failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def zone_of(x_m, zones):
    # zones = (zone for 0-10 m, zone for 10-20 m, zone for 20-30 m)
    if x_m < 0 or x_m >= 30:
        return ""
    return f"Zone {zones[int(x_m // 10)]}"


def vehicle_rows(tid, cls, zones, y_m, speed_ms, x0=0.0, frames=None, size_m=(4.0, 1.8), y_fn=None):
    n = frames or int(30.0 / speed_ms * FPS)
    rows = []
    for i in range(n):
        x = x0 + speed_ms * i / FPS
        if x >= 30:
            break
        cx, cy = x * PPM, (y_m + (y_fn(x) if y_fn else 0.0)) * PPM
        hl, hw = size_m[0] / 2 * PPM, size_m[1] / 2 * PPM
        rows.append({
            "frame": i + 1, "timestamp": f"{(i + 1) / FPS:.6f}", "track_id": tid, "class_id": 0,
            "class_name": cls, "confidence": "0.9",
            "bbox_x1": int(cx - hl), "bbox_y1": int(cy - hw), "bbox_x2": int(cx + hl), "bbox_y2": int(cy + hw),
            "bbox_width": int(2 * hl), "bbox_height": int(2 * hw), "bbox_area": 0,
            "trajectory_x": int(cx), "trajectory_y": int(cy),
            "trajectory_position": "Center", "trajectory_offset": "0.00",
            "zone": zone_of(x, zones),
        })
    return rows


def build_scene():
    rows = []
    # A weaves 0.35 m inside zone 3 (sin bump); C weaves 0.6 m inside zone 6
    bump_a = lambda x: 0.35 * math.sin(math.pi * (x - 10) / 10) if 10 <= x < 20 else 0.0
    bump_c = lambda x: 0.60 * math.sin(math.pi * (x - 10) / 10) if 10 <= x < 20 else 0.0
    rows += vehicle_rows(1, "Motorcycle", (2, 3, 4), 0.0, 10.0, size_m=(2.0, 0.8), y_fn=bump_a)
    rows += vehicle_rows(2, "Car", (2, 3, 4), 1.5, 10.0, size_m=(4.5, 1.8))
    rows += vehicle_rows(3, "Motorcycle", (5, 6, 7), 8.0, 5.0, size_m=(2.0, 0.8), y_fn=bump_c)
    rows.sort(key=lambda r: (r["frame"], r["track_id"]))
    return rows


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    root = tk.Tk()
    root.withdraw()
    app = m.Run1App(root)

    out = tempfile.mkdtemp(prefix="pk_e2e_")
    rows = build_scene()
    fields = list(rows[0].keys())
    write_csv(os.path.join(out, "T_Detection_Records.csv"), fields, rows)
    write_csv(os.path.join(out, "T_ID_Zone_Summary.csv"), ["track_id", "class_name"],
              [{"track_id": 1, "class_name": "Motorcycle"}, {"track_id": 2, "class_name": "Car"},
               {"track_id": 3, "class_name": "Motorcycle"}])

    app.run3_site_id_var.set("8")
    app.run3_ppm_var.set(str(PPM))
    app.run3_perspective_enabled_var.set(False)
    g = app.run3_geometry_vars
    for key, val in (("lane_entry_motorcycle_m", "1.5"), ("lane_entry_car_m", "3.25"),
                     ("lane_opp_motorcycle_m", "1.2"), ("lane_opp_car_m", "3.0"), ("median_m", "0")):
        g[key].set(val)
    app.run3_ldp_smoothing_var.set("1")      # exact check of the LDP geometry (smoothing is unit-tested)
    app._run3_cfg = app._run3_snapshot_config()
    outputs = app.run3_processing({}, out, "T")
    app.root.update_idletasks()

    summary = json.load(open(os.path.join(out, "Run_3_Summary.json"), encoding="utf-8"))
    print("output folder:", out)
    print("diagnostics  :", json.dumps(summary["diagnostics"], ensure_ascii=False)[:400])

    # ---- movement ----
    mc = summary["source_counts"]["movement_counts"]
    check("movement 2-3-4 = 2 vehicles (A, B)", mc.get("2-3-4") == 2, str(mc))
    check("movement 5-6-7 = 1 vehicle (C)", mc.get("5-6-7") == 1, str(mc))

    # ---- Y6 speed ----
    det = read_csv(os.path.join(out, "Run_3_Speed_Detail.csv"))
    by = {(r["Vehicle_ID"], r["Scope"], r["Key"]): float(r["Speed_kmh"]) for r in det}
    for vid, kmh in (("1", 36.0), ("2", 36.0), ("3", 18.0)):
        zs = [k for (v, sc, k) in by if v == vid and sc == "Zone"]
        check(f"vehicle {vid} has 3 zone speeds", len(zs) == 3, str(zs))
        check(f"vehicle {vid} zone speeds ~{kmh} km/h",
              all(abs(by[(vid, 'Zone', k)] - kmh) < 0.6 for k in zs), str({k: round(by[(vid, 'Zone', k)], 2) for k in zs}))
    check("vehicle 1 Movement 2-3-4 speed ~36", abs(by.get(("1", "Movement", "2-3-4"), 0) - 36.0) < 0.6)
    check("vehicle 3 Movement 5-6-7 speed ~18", abs(by.get(("3", "Movement", "5-6-7"), 0) - 18.0) < 0.6)
    stats = read_csv(os.path.join(out, "Run_3_Y6_Speed_Statistics.csv"))
    z2 = [r for r in stats if r["Scope"] == "Zone" and r["Key"] == "Zone 2" and r["Vehicle_Class"] == "All"][0]
    check("Y6 stats Zone 2: N=2, V50 ~36", z2["N"] == "2" and abs(float(z2["Y6_V50_kmh"]) - 36.0) < 0.6, str(z2))
    wide = read_csv(os.path.join(out, "Run_3_Speed.csv"))
    check("vehicle summary rows = 3", len(wide) == 3)
    check("vehicle summary has Zone_Sequence 2-3-4", any(r["Zone_Sequence"] == "2-3-4" for r in wide))

    # ---- Y1 LDP ----
    ldp = read_csv(os.path.join(out, "Run_3_Y1_LDP.csv"))
    lz = {(r["Vehicle_ID"], r["Zone"]): r for r in ldp}
    check("Y1 rows only for main-road motorcycles A and C (car B excluded)", {v for v, _ in lz} == {"1", "3"}, str(sorted(lz)))
    a3 = float(lz[("1", "Zone 3")]["Y1_LDP_percent"])
    check("Y1 A zone 3 ~ 0.35/4.75 = 7.37 %", abs(a3 - 7.37) < 0.35, f"{a3:.3f}")
    check("Y1 A zone 2 ~ 0 %", float(lz[("1", "Zone 2")]["Y1_LDP_percent"]) < 0.5)
    c6 = float(lz[("3", "Zone 6")]["Y1_LDP_percent"])
    check("Y1 C zone 6 ~ 0.60/4.20 = 14.29 % (opposite-side W)", abs(c6 - 14.29) < 0.6, f"{c6:.3f}")
    check("Y1 W_entry for A, W_opp for C",
          lz[("1", "Zone 3")]["Lane_Width_W_m"] == "4.750" and lz[("3", "Zone 6")]["Lane_Width_W_m"] == "4.200")
    check("Y1 zone 1 never reported", all(r["Zone"] != "Zone 1" for r in ldp))

    for extra in EXTRA_CHECKS:
        extra(out, summary, check, read_csv)

    root.destroy()
    print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
    return 1 if failures else 0


EXTRA_CHECKS = []   # later indicator checks are appended below

if __name__ == "__main__":
    sys.exit(main())
