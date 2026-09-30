"""End-to-end Run 3 test on SYNTHETIC scenes with known answers (no video, no YOLO).

Run from the Run folder:   python tests/e2e_run3.py
Needs torch/cv2/ultralytics (imports PKStudio.py), creates a hidden Tk window,
writes fake Run 2 CSV files into a temp folder and runs the real
run3_processing(), then checks the CSV/JSON outputs.

Units: metres; pixel = metre x PPM (PPM = 100, no perspective); 60 FPS.

Scene 1  (speed, LDP, lateral clearance).  Zones by x: 0-10 / 10-20 / 20-30 m
  A  Motorcycle 2-3-4   y = 0.0   10 m/s, weaves 0.35 m in zone 3
  B  Car        2-3-4   y = 1.5   10 m/s, beside A
  C  Motorcycle 5-6-7   y = 8.0    5 m/s, weaves 0.60 m in zone 6
  D  Car        1-3-6   y = 2.5   10 m/s  (crossing flow, must not pair with A)
  E  Car        1-3-4   y = -1.6  10 m/s  (merging flow, pairs with A in zones 3-4)

Scene 2  (PET, TTC).  Crossing and rear-end conflicts
  P  Car  2-3-4   along +x at y = 0, 10 m/s, passes (15, 0) at t = 1.5 s
  Q  Car  1-3-6   along +y at x = 15, passes (15, 0) at t = 3.1 s  -> PET(P,Q) = 1.0 s
  R  Car  1-3-6   along +y at x = 15, passes (15, 0) at t = 1.6 s  -> side TTC(P,R) ~ 0
  F  Car  (zone 3) along +x at y = -12, 10 m/s behind  L  Car at 5 m/s, 20 m ahead
        -> rear-end TTC(F,L) = (S = 15.5 - 5 t) / 5 m/s  (ends when L leaves at t = 2 s: ~1.12 s)
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


def zone_name(zone):
    return f"Zone {zone}" if zone else ""


def make_rows(tid, cls, path_fn, zone_fn, n_frames, size_m):
    """path_fn(t) -> (x_m, y_m) or None (vehicle not present); zone_fn(x, y) -> zone number or None."""
    rows = []
    hl, hw = size_m[0] / 2 * PPM, size_m[1] / 2 * PPM
    for i in range(n_frames):
        pos = path_fn(i / FPS)
        if pos is None:
            continue
        x, y = pos
        cx, cy = x * PPM, y * PPM
        rows.append({
            "frame": i + 1, "timestamp": f"{(i + 1) / FPS:.6f}", "track_id": tid, "class_id": 0,
            "class_name": cls, "confidence": "0.9",
            "bbox_x1": int(cx - hl), "bbox_y1": int(cy - hw), "bbox_x2": int(cx + hl), "bbox_y2": int(cy + hw),
            "bbox_width": int(2 * hl), "bbox_height": int(2 * hw), "bbox_area": 0,
            "trajectory_x": int(cx), "trajectory_y": int(cy),
            "trajectory_position": "Center", "trajectory_offset": "0.00",
            "zone": zone_name(zone_fn(x, y)),
        })
    return rows


def along_x(y_m, speed, x0=0.0, y_fn=None):
    def f(t):
        x = x0 + speed * t
        if x < 0 or x >= 30:
            return None
        return (x, y_m + (y_fn(x) if y_fn else 0.0))
    return f


def zones_by_x(z_a, z_b, z_c):
    return lambda x, y: (z_a, z_b, z_c)[int(x // 10)] if 0 <= x < 30 else None


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def run_scene(app, vehicles):
    """vehicles = [(tid, class_name, rows)]. Returns (out_dir, summary)."""
    out = tempfile.mkdtemp(prefix="pk_e2e_")
    rows = [r for _, _, rs in vehicles for r in rs]
    rows.sort(key=lambda r: (r["frame"], r["track_id"]))
    write_csv(os.path.join(out, "T_Detection_Records.csv"), list(rows[0].keys()), rows)
    write_csv(os.path.join(out, "T_ID_Zone_Summary.csv"), ["track_id", "class_name"],
              [{"track_id": tid, "class_name": cls} for tid, cls, _ in vehicles])
    app._run3_cfg = app._run3_snapshot_config()
    app.run3_processing({}, out, "T")
    app.root.update_idletasks()
    with open(os.path.join(out, "Run_3_Summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    return out, summary


def scene1(app):
    bump_a = lambda x: 0.35 * math.sin(math.pi * (x - 10) / 10) if 10 <= x < 20 else 0.0
    bump_c = lambda x: 0.60 * math.sin(math.pi * (x - 10) / 10) if 10 <= x < 20 else 0.0
    n = 360
    veh = [
        (1, "Motorcycle", make_rows(1, "Motorcycle", along_x(0.0, 10.0, y_fn=bump_a), zones_by_x(2, 3, 4), n, (2.0, 0.8))),
        (2, "Car", make_rows(2, "Car", along_x(1.5, 10.0), zones_by_x(2, 3, 4), n, (4.5, 1.8))),
        (3, "Motorcycle", make_rows(3, "Motorcycle", along_x(8.0, 5.0, y_fn=bump_c), zones_by_x(5, 6, 7), n, (2.0, 0.8))),
        (4, "Car", make_rows(4, "Car", along_x(2.5, 10.0), zones_by_x(1, 3, 6), n, (4.5, 1.8))),
        (5, "Car", make_rows(5, "Car", along_x(-1.6, 10.0), zones_by_x(1, 3, 4), n, (4.5, 1.8))),
    ]
    out, summary = run_scene(app, veh)
    print("scene 1 output:", out)

    # ---- movement ----
    mc = summary["source_counts"]["movement_counts"]
    check("movement 2-3-4 = 2 vehicles (A, B)", mc.get("2-3-4") == 2, str(mc))
    check("movement 5-6-7 = 1 vehicle (C)", mc.get("5-6-7") == 1, str(mc))
    check("movement 1-3-4 = 1 vehicle (E)", mc.get("1-3-4") == 1, str(mc))

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
    check("vehicle summary rows = 5", len(wide) == 5)
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

    # ---- Y2 Lateral Clearance ----
    lc = read_csv(os.path.join(out, "Run_3_Y2_Lateral_Clearance.csv"))
    pairs_seen = {r["Pair_ID"] for r in lc}
    check("Y2 pairs = A-B (2-3-4 & 2-3-4) and A-E (merging) only; A-D crossing excluded",
          pairs_seen == {"1_2", "1_5"}, str(sorted(pairs_seen)))
    ae_zones = {r["Zone"] for r in lc if r["Pair_ID"] == "1_5"}
    check("Y2 A-E measured in zones 3 and 4 only (shared transition 3-4; not in zone 1/2)",
          ae_zones == {"Zone 3", "Zone 4"}, str(ae_zones))
    ab = [float(r["Y2_Lateral_Clearance"]) for r in lc if r["Pair_ID"] == "1_2" and r["Zone"] == "Zone 2"]
    check("Y2 A-B zone 2 = 1.5 - (0.8+1.8)/2 = 0.20 m", bool(ab) and all(abs(v - 0.20) < 0.03 for v in ab),
          f"n={len(ab)} mean={sum(ab)/len(ab):.3f}" if ab else "no rows")
    ae = [float(r["Y2_Lateral_Clearance"]) for r in lc if r["Pair_ID"] == "1_5" and r["Zone"] == "Zone 4"]
    check("Y2 A-E zone 4 = 1.6 - 1.3 = 0.30 m", bool(ae) and all(abs(v - 0.30) < 0.03 for v in ae),
          f"n={len(ae)}" + (f" mean={sum(ae)/len(ae):.3f}" if ae else ""))
    pr = read_csv(os.path.join(out, "Run_3_Y2_Lateral_Clearance_Pairs.csv"))
    check("Y2 pair summary rows (A-B x 3 zones + A-E x 2)", len(pr) == 5, str([(r['Pair_ID'], r['Zone']) for r in pr]))
    ind = read_csv(os.path.join(out, "Run_3_Indicator_Summary.csv"))
    check("indicator summary has Y1, Y2, Y6", {"Y1", "Y2", "Y6"} <= {r["Code"] for r in ind})


def scene2(app):
    n = 360
    p_path = along_x(0.0, 10.0)
    cross = lambda t_pass: (lambda t: (15.0, 10.0 * (t - t_pass)) if -10 <= 10.0 * (t - t_pass) <= 10 else None)
    zone_y = lambda x, y: 1 if y < -5 else (3 if y < 5 else 6)
    veh = [
        (1, "Car", make_rows(1, "Car", p_path, zones_by_x(2, 3, 4), n, (4.5, 1.8))),
        (2, "Car", make_rows(2, "Car", cross(3.1), zone_y, n, (4.5, 1.8))),
        (3, "Car", make_rows(3, "Car", cross(1.6), zone_y, n, (4.5, 1.8))),
        (4, "Car", make_rows(4, "Car", along_x(-12.0, 10.0), lambda x, y: 3, n, (4.5, 1.8))),
        (5, "Car", make_rows(5, "Car", along_x(-12.0, 5.0, x0=20.0), lambda x, y: 3, n, (4.5, 1.8))),
    ]
    out, summary = run_scene(app, veh)
    print("scene 2 output:", out)

    mv = summary["source_counts"]["movement_counts"]
    check("scene 2 movements: P = 2-3-4, Q and R = 1-3-6-7 (partial)", mv.get("2-3-4") == 1 and mv.get("1-3-6-7") == 2, str(mv))

    # ---- Y5 PET ----
    pet = read_csv(os.path.join(out, "Run_3_Y5_PET.csv"))
    pairs = {(r["Vehicle_ID_A"], r["Vehicle_ID_B"]): r for r in pet}
    check("Y5 exactly one PET event: P-Q (P-R overlaps in time, Q-R same movement, F/L no movement)",
          set(pairs) == {("1", "2")}, str(sorted(pairs)))
    if ("1", "2") in pairs:
        r = pairs[("1", "2")]
        check("Y5 PET(P,Q) = 1.0 s", abs(float(r["Y5_PET"]) - 1.0) < 0.06, r["Y5_PET"])
        check("Y5 conflict type Crossing in Zone 3", r["Conflict_Type"] == "Crossing" and r["Conflict_Zone"] == "Zone 3",
              f"{r['Conflict_Type']} {r['Conflict_Zone']}")

    # ---- Y4 TTC ----
    ttc = read_csv(os.path.join(out, "Run_3_Y4_TTC.csv"))
    kinds = {(r["TTC_Type"], frozenset((r["Vehicle_A_ID"], r["Vehicle_B_ID"]))): r for r in ttc}
    check("Y4 event set = RearEnd F->L and Side P-R",
          set(kinds) == {("RearEnd", frozenset(("4", "5"))), ("Side", frozenset(("1", "3")))},
          str(sorted((k, sorted(v)) for k, v in kinds)))
    re_ = kinds.get(("RearEnd", frozenset(("4", "5"))))
    if re_:
        check("Y4 rear-end: follower is vehicle 4", re_["Vehicle_A_ID"] == "4")
        check("Y4 rear-end TTCmin ~ 1.12 s", abs(float(re_["Y4_TTC_s"]) - 1.12) < 0.08, re_["Y4_TTC_s"])
        check("Y4 rear-end CS = 5 m/s = 18 km/h", abs(float(re_["CS_Closing_Speed_kmh"]) - 18.0) < 0.5, re_["CS_Closing_Speed_kmh"])
    sd = kinds.get(("Side", frozenset(("1", "3"))))
    if sd:
        check("Y4 side TTCmin < 0.1 s (P passes the crossing 0.1 s before R)", float(sd["Y4_TTC_s"]) < 0.1, sd["Y4_TTC_s"])
        check("Y4 side: P arrives first, arrival diff 0.1 s",
              sd["Vehicle_A_ID"] == "1" and abs(float(sd["Arrival_Diff_s"]) - 0.1) < 0.03,
              f"A={sd['Vehicle_A_ID']} diff={sd['Arrival_Diff_s']}")
        check("Y4 side path angle 90 deg", abs(float(sd["Path_Angle_deg"]) - 90.0) < 1.0, sd["Path_Angle_deg"])


def main():
    root = tk.Tk()
    root.withdraw()
    app = m.Run1App(root)
    app.run3_site_id_var.set("8")
    app.run3_ppm_var.set(str(PPM))
    app.run3_perspective_enabled_var.set(False)
    g = app.run3_geometry_vars
    for key, val in (("lane_entry_motorcycle_m", "1.5"), ("lane_entry_car_m", "3.25"),
                     ("lane_opp_motorcycle_m", "1.2"), ("lane_opp_car_m", "3.0"), ("median_m", "0")):
        g[key].set(val)
    app.run3_ldp_smoothing_var.set("1")      # exact check of the LDP geometry (smoothing is unit-tested)

    print("=== scene 1: speed / LDP / lateral clearance ===")
    scene1(app)
    print("=== scene 2: PET / TTC ===")
    scene2(app)

    root.destroy()
    print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
