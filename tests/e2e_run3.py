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


def read_csv(path, raw=False):
    """Run 3 writes movements / zone sequences with arrows (2→3→4) so that Excel does not
    turn them into dates; the checks below compare with the hyphen form unless raw=True."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not raw:
        rows = [{k: (v.replace("→", "-") if isinstance(v, str) else v) for k, v in r.items()} for r in rows]
    return rows


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
    with open(os.path.join(out, "T_Summary.json"), encoding="utf-8") as f:
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
        # 6 = the SAME car as B tracked under a second ID for 1 s (frames 100-160): must be removed
        (6, "Car", [dict(r, track_id=6) for r in make_rows(2, "Car", along_x(1.5, 10.0), zones_by_x(2, 3, 4), n, (4.5, 1.8))
                    if 100 <= r["frame"] <= 160]),
    ]
    out, summary = run_scene(app, veh)
    print("scene 1 output:", out)
    dtracks = summary["diagnostics"]["duplicate_tracks"]
    check("duplicate track (same car, second ID) detected and its frames removed",
          dtracks["tracks_affected"] == 1 and dtracks["frames_removed"] == 61, str(dtracks))
    dup_rows = read_csv(os.path.join(out, "T_Duplicate_Tracks.csv"))
    check("duplicate report: ID 6 is a duplicate of ID 2", len(dup_rows) == 1 and dup_rows[0]["Duplicate_ID"] == "6"
          and dup_rows[0]["Kept_ID"] == "2", str(dup_rows))
    lc_rows = read_csv(os.path.join(out, "T_Lateral_Clearance.csv"))
    check("no Lateral Clearance pair involves the duplicate ID 6 (it would show a fake -1.8 m)",
          all("6" not in r["Pair_ID"].split("_") for r in lc_rows),
          str(sorted({r["Pair_ID"] for r in lc_rows if "6" in r["Pair_ID"].split("_")})))

    # ---- movement ----
    mc = summary["source_counts"]["movement_counts"]
    check("movement 2-3-4 = 2 vehicles (A, B)", mc.get("2-3-4") == 2, str(mc))
    check("movement 5-6-7 = 1 vehicle (C)", mc.get("5-6-7") == 1, str(mc))
    check("movement 1-3-4 = 1 vehicle (E)", mc.get("1-3-4") == 1, str(mc))

    # ---- Speed ----
    det = read_csv(os.path.join(out, "T_Speed_Detail.csv"))
    by = {(r["Vehicle_ID"], r["Scope"], r["Key"]): float(r["Speed_kmh"]) for r in det}
    for vid, kmh in (("1", 36.0), ("2", 36.0), ("3", 18.0)):
        zs = [k for (v, sc, k) in by if v == vid and sc == "Zone"]
        check(f"vehicle {vid} has 3 zone speeds", len(zs) == 3, str(zs))
        check(f"vehicle {vid} zone speeds ~{kmh} km/h",
              all(abs(by[(vid, 'Zone', k)] - kmh) < 0.6 for k in zs), str({k: round(by[(vid, 'Zone', k)], 2) for k in zs}))
    check("vehicle 1 Movement 2-3-4 speed ~36", abs(by.get(("1", "Movement", "2-3-4"), 0) - 36.0) < 0.6)
    check("vehicle 3 Movement 5-6-7 speed ~18", abs(by.get(("3", "Movement", "5-6-7"), 0) - 18.0) < 0.6)
    stats = read_csv(os.path.join(out, "T_Speed_Statistics.csv"))
    z2 = [r for r in stats if r["Scope"] == "Zone" and r["Key"] == "Zone 2" and r["Vehicle_Class"] == "All"][0]
    check("Speed stats Zone 2: N=2, V50 ~36", z2["N"] == "2" and abs(float(z2["V50_kmh"]) - 36.0) < 0.6, str(z2))
    check("untracked detections diagnostic present (0 here)", summary["diagnostics"]["untracked_detections"]["rows_with_track_id_minus_1"] == 0)
    # --- per-zone calibration: Zone 3 has its own reference quad measured at 50 px/m (base = 100 px/m) ---
    app.run3_zone_calibrations = {"3": {"points": [[1000, -200], [2000, -200], [2000, 800], [1000, 800]], "lengths": [20, 20, 20, 20]}}
    out_z, summary_z = run_scene(app, veh)
    app.run3_zone_calibrations = {}
    det_z = read_csv(os.path.join(out_z, "T_Speed_Detail.csv"))
    bz = {(r["Vehicle_ID"], r["Key"]): (float(r["Speed_kmh"]), r["Calibration_Mode"]) for r in det_z if r["Scope"] == "Zone"}
    check("zone calibration: Zone 3 speed of vehicle 1 doubles (36 -> 72 km/h, own scale 50 px/m)", abs(bz[("1", "Zone 3")][0] - 72.0) < 1.5 and bz[("1", "Zone 3")][1] == "Zone_Homography", str(bz[("1", "Zone 3")]))
    check("zone calibration: Zone 2 and Zone 4 keep the base scale (36 km/h)", abs(bz[("1", "Zone 2")][0] - 36.0) < 1.0 and abs(bz[("1", "Zone 4")][0] - 36.0) < 1.0 and bz[("1", "Zone 2")][1] != "Zone_Homography", str((bz[("1", "Zone 2")], bz[("1", "Zone 4")])))
    zinfo = summary_z["calibration"].get("zone_calibrations", {})
    check("zone calibration is reported in the summary with its alignment check", "Zone 3" in zinfo and zinfo["Zone 3"]["alignment_rms_m"] > 1.0, str(zinfo))
    # --- speed above the plausible maximum is flagged and left out of the statistics ---
    app.run3_speed_max_var.set("30")
    out_o, summary_o = run_scene(app, veh)
    app.run3_speed_max_var.set("80")
    det_o = read_csv(os.path.join(out_o, "T_Speed_Detail.csv"))
    flagged = {r["Vehicle_ID"] for r in det_o if "Speed_Above_Max" in r["QC_Flag"]}
    check("max speed 30: the 36 km/h vehicles 1, 2, 4, 5 are flagged, the 18 km/h vehicle 3 is not", flagged == {"1", "2", "4", "5"}, str(flagged))
    st_o = read_csv(os.path.join(out_o, "T_Speed_Statistics.csv"))
    z2o = [r for r in st_o if r["Scope"] == "Zone" and r["Key"] == "Zone 2" and r["Vehicle_Class"] == "All"]
    check("flagged speeds are left out of the statistics (Zone 2 has no 18 km/h vehicle -> no row)", not z2o, str(z2o))
    check("flagged rows stay in the detail file", len(det_o) == len(det))
    # --- tools/sensitivity.py: re-run Run 3 for several values of one setting ---
    sys.path.insert(0, os.path.join(HERE, "..", "tools"))
    import sensitivity
    sens = sensitivity.run_sensitivity(app, out, "T", {"speed_max_kmh": ["30", "80"]})
    zs = {(r["Value"]): r for r in sens if r["Group"] == "Zone 2" and r["Indicator"].startswith("Speed")}
    check("sensitivity: speed_max 80 -> Zone 2 N=2; 30 -> Zone 2 has no row (both 36 km/h vehicles excluded)",
          zs.get("80", {}).get("N") == "2" and "30" not in zs, str(zs))
    check("sensitivity leaves the source folder untouched", not os.path.exists(os.path.join(out, "Sensitivity_speed_max_kmh.csv")))
    raw_speed = read_csv(os.path.join(out, "T_Speed.csv"), raw=True)
    check("CSV movement / zone-sequence cells use arrows (Excel would turn 2-3-4 into a date)",
          any(r["Zone_Sequence"] == "2→3→4" for r in raw_speed) and not any("-" in r["Zone_Sequence"] for r in raw_speed),
          str([r["Zone_Sequence"] for r in raw_speed][:5]))
    wide = read_csv(os.path.join(out, "T_Speed.csv"))
    check("vehicle summary rows = 5 (the duplicate ID 6 has no rows left)", len(wide) == 5, str(len(wide)))
    check("vehicle summary has Zone_Sequence 2-3-4", any(r["Zone_Sequence"] == "2-3-4" for r in wide))

    # ---- LDP ----
    ldp = read_csv(os.path.join(out, "T_LDP.csv"))
    lz = {(r["Vehicle_ID"], r["Zone"]): r for r in ldp}
    check("LDP rows for every main-road vehicle A, B, C (any class); D, E are not main-road", {v for v, _ in lz} == {"1", "2", "3"}, str(sorted(lz)))
    check("LDP car B (straight) ~ 0 %", float(lz[("2", "Zone 3")]["LDP_percent"]) < 0.5)
    check("LDP risk level: A zone 3 (14.7 %) = None, C zone 6 (28.6 %) = None", lz[("1", "Zone 3")]["LDP_Level"] == "None" and lz[("3", "Zone 6")]["LDP_Level"] == "None")
    a3 = float(lz[("1", "Zone 3")]["LDP_percent"])
    check("LDP A zone 3 ~ 0.35/(4.75/2) = 14.74 %", abs(a3 - 14.74) < 0.7, f"{a3:.3f}")
    check("LDP A zone 2 ~ 0 %", float(lz[("1", "Zone 2")]["LDP_percent"]) < 0.5)
    c6 = float(lz[("3", "Zone 6")]["LDP_percent"])
    check("LDP C zone 6 ~ 0.60/(4.20/2) = 28.57 % (opposite-side W)", abs(c6 - 28.57) < 1.2, f"{c6:.3f}")
    check("LDP W_entry for A, W_opp for C",
          lz[("1", "Zone 3")]["Lane_Width_W_m"] == "4.750" and lz[("3", "Zone 6")]["Lane_Width_W_m"] == "4.200")
    check("LDP zone 1 never reported", all(r["Zone"] != "Zone 1" for r in ldp))

    # ---- Lateral Clearance ----
    lc = read_csv(os.path.join(out, "T_Lateral_Clearance.csv"))
    pairs_seen = {r["Pair_ID"] for r in lc}
    check("Lateral Clearance pairs (all classes): A-B, A-E, B-E, D-E; crossing A-D / B-D excluded",
          pairs_seen == {"1_2", "1_5", "2_5", "4_5"}, str(sorted(pairs_seen)))
    be = [float(r["Lateral_Clearance_m"]) for r in lc if r["Pair_ID"] == "2_5" and r["Zone"] == "Zone 4"]
    check("Lateral Clearance car-car B-E zone 4 = 3.1 - 1.8 = 1.30 m (A = earlier ID)", bool(be) and all(abs(v - 1.30) < 0.05 for v in be),
          f"n={len(be)}" + (f" mean={sum(be)/len(be):.3f}" if be else ""))
    de = [float(r["Lateral_Clearance_m"]) for r in lc if r["Pair_ID"] == "4_5" and r["Zone"] == "Zone 3"]
    check("Lateral Clearance car-car D-E zone 3 = 4.1 - 1.8 = 2.30 m", bool(de) and all(abs(v - 2.30) < 0.05 for v in de),
          f"n={len(de)}" + (f" mean={sum(de)/len(de):.3f}" if de else ""))
    ae_zones = {r["Zone"] for r in lc if r["Pair_ID"] == "1_5"}
    check("Lateral Clearance A-E measured in zones 3 and 4 only (shared transition 3-4; not in zone 1/2)",
          ae_zones == {"Zone 3", "Zone 4"}, str(ae_zones))
    ab = [float(r["Lateral_Clearance_m"]) for r in lc if r["Pair_ID"] == "1_2" and r["Zone"] == "Zone 2"]
    check("Lateral Clearance A-B zone 2 = 1.5 - (0.8+1.8)/2 = 0.20 m", bool(ab) and all(abs(v - 0.20) < 0.03 for v in ab),
          f"n={len(ab)} mean={sum(ab)/len(ab):.3f}" if ab else "no rows")
    ae = [float(r["Lateral_Clearance_m"]) for r in lc if r["Pair_ID"] == "1_5" and r["Zone"] == "Zone 4"]
    check("Lateral Clearance A-E zone 4 = 1.6 - 1.3 = 0.30 m", bool(ae) and all(abs(v - 0.30) < 0.03 for v in ae),
          f"n={len(ae)}" + (f" mean={sum(ae)/len(ae):.3f}" if ae else ""))
    pr = read_csv(os.path.join(out, "T_Lateral_Clearance_Pairs.csv"))
    check("Lateral Clearance pair summary rows (A-B x3, A-E x2, B-E x2, D-E x1)", len(pr) == 8, str([(r['Pair_ID'], r['Zone']) for r in pr]))
    # motorcycle-pairs-only switch: only the pairs that include a motorcycle remain
    app.run3_lc_motorcycle_pairs_only_var.set(True)
    out_m, _ = run_scene(app, veh)
    app.run3_lc_motorcycle_pairs_only_var.set(False)
    only_m = {r["Pair_ID"] for r in read_csv(os.path.join(out_m, "T_Lateral_Clearance.csv"))}
    check("Lateral Clearance motorcycle-pairs-only option keeps A-B and A-E only", only_m == {"1_2", "1_5"}, str(sorted(only_m)))
    ind = read_csv(os.path.join(out, "T_Indicator_Summary.csv"))
    check("indicator summary lists LDP, Lateral Clearance, Speed", any("LDP" in r["Indicator"] for r in ind) and any("Lateral Clearance" in r["Indicator"] for r in ind) and any("Speed" in r["Indicator"] for r in ind))


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
    # side collision off -> only the rear-end event remains
    app.run3_ttc_side_enabled_var.set(False)
    out_off, _ = run_scene(app, veh)
    app.run3_ttc_side_enabled_var.set(True)
    kinds_off = {r["TTC_Type"] for r in read_csv(os.path.join(out_off, "T_TTC.csv"))}
    check("TTC side collision can be switched off (only RearEnd remains)", kinds_off == {"RearEnd"}, str(kinds_off))
    # a tighter window rule (factor 0, margin 0.05 s): P-R arrive 0.1 s apart -> no longer a collision course
    app.run3_ttc_side_factor_var.set("0"); app.run3_ttc_side_margin_var.set("0.05")
    out_tight, _ = run_scene(app, veh)
    app.run3_ttc_side_factor_var.set("1.0"); app.run3_ttc_side_margin_var.set("0.0")
    kinds_tight = {r["TTC_Type"] for r in read_csv(os.path.join(out_tight, "T_TTC.csv"))}
    check("TTC side window is adjustable (factor 0, margin 0.05 s drops the 0.1 s apart pair)", kinds_tight == {"RearEnd"}, str(kinds_tight))

    reasons = summary["diagnostics"].get("empty_outputs", [])
    check("empty Gap Acceptance output is explained (no Line drawn yet)", any("Gap Acceptance" in r and "Line" in r for r in reasons), str(reasons))
    check("non-empty indicators are not listed as empty", not any(r.startswith(("LDP", "TTC", "PET", "Speed")) for r in reasons), str(reasons))
    mv = summary["source_counts"]["movement_counts"]
    check("scene 2 movements: P = 2-3-4, Q and R = 1-3-6-7 (partial)", mv.get("2-3-4") == 1 and mv.get("1-3-6-7") == 2, str(mv))

    # ---- PET ----
    pet = read_csv(os.path.join(out, "T_PET.csv"))
    pairs = {(r["Vehicle_ID_A"], r["Vehicle_ID_B"]): r for r in pet}
    check("PET exactly one PET event: P-Q (P-R overlaps in time, Q-R same movement, F/L no movement)",
          set(pairs) == {("1", "2")}, str(sorted(pairs)))
    if ("1", "2") in pairs:
        r = pairs[("1", "2")]
        check("PET PET(P,Q) = 1.0 s", abs(float(r["PET_s"]) - 1.0) < 0.06, r["PET_s"])
        check("PET conflict type Crossing in Zone 3", r["Conflict_Type"] == "Crossing" and r["Conflict_Zone"] == "Zone 3",
              f"{r['Conflict_Type']} {r['Conflict_Zone']}")

    # ---- TTC ----
    ttc = read_csv(os.path.join(out, "T_TTC.csv"))
    kinds = {(r["TTC_Type"], frozenset((r["Vehicle_A_ID"], r["Vehicle_B_ID"]))): r for r in ttc}
    check("TTC event set = RearEnd F->L and Side P-R",
          set(kinds) == {("RearEnd", frozenset(("4", "5"))), ("Side", frozenset(("1", "3")))},
          str(sorted((k, sorted(v)) for k, v in kinds)))
    re_ = kinds.get(("RearEnd", frozenset(("4", "5"))))
    if re_:
        check("TTC rear-end: follower is vehicle 4", re_["Vehicle_A_ID"] == "4")
        check("TTC rear-end TTCmin ~ 1.12 s", abs(float(re_["TTC_s"]) - 1.12) < 0.08, re_["TTC_s"])
        check("TTC rear-end CS = 5 m/s = 18 km/h", abs(float(re_["CS_Closing_Speed_kmh"]) - 18.0) < 0.5, re_["CS_Closing_Speed_kmh"])
    sd = kinds.get(("Side", frozenset(("1", "3"))))
    if sd:
        check("TTC side TTCmin < 0.1 s (P passes the crossing 0.1 s before R)", float(sd["TTC_s"]) < 0.1, sd["TTC_s"])
        check("TTC side: P arrives first, arrival diff 0.1 s",
              sd["Vehicle_A_ID"] == "1" and abs(float(sd["Arrival_Diff_s"]) - 0.1) < 0.03,
              f"A={sd['Vehicle_A_ID']} diff={sd['Arrival_Diff_s']}")
        check("TTC side path angle 90 deg", abs(float(sd["Path_Angle_deg"]) - 90.0) < 1.0, sd["Path_Angle_deg"])


def stream_rows(tid, t_cross, x_line, y, jitter=0.0, t_appear=None):
    """A car of a conflicting stream moving along +x at 10 m/s, crossing x = x_line at t_cross."""
    def f(t):
        if t_appear is not None and t < t_appear:
            return None
        return (x_line + 10.0 * (t - t_cross) + (jitter * math.sin(30.0 * t) if jitter else 0.0), y)
    return f


def gap_subject_path(t_stop_end=3.0, hold=None):
    """Subject: waits at (15, -6) until t_stop_end, then +y at 4 m/s. hold = (t_from, t_to): stands still
    at its position at t_from, then continues +x at 6 m/s (the 'stop in the middle of the junction' case)."""
    def f(t):
        if t < t_stop_end:
            return (15.0, -6.0)
        if hold is None:
            if t < t_stop_end + 1.5:
                return (15.0, -6.0 + 4.0 * (t - t_stop_end))
            return (15.0 + 6.0 * (t - t_stop_end - 1.5), 0.0)
        t0, t1 = hold
        if t < t0:
            return (15.0, -6.0 + 4.0 * (t - t_stop_end))
        y_stop = -6.0 + 4.0 * (t0 - t_stop_end)
        if t < t1:
            return (15.0, y_stop)
        return (15.0 + 6.0 * (t - t1), y_stop)
    return f


def scene3(app):
    """Gap Acceptance with a Line + mapping (first crossing only, jitter robust).
    Subject S (1-3-4) waits in zone 1 until t = 3.0 s, reaches the conflict zone 3 at t = 4.0 s and drives on
    without stopping. Stream 2-3-4 crosses Line 1 (x = 15 m) at 1, ~1.92 (jitters across the line 3 times) and 5 s.
    Access stage: gap 1.0->1.92 closed before entry = Rejected (0.92 s); gap 1.92->5.0 is open at entry = Accepted,
    available gap = time left = 5.0 - 4.0 = 1.0 s."""
    n = 480
    zone_x = lambda x, y: 2 if x < 10 else (3 if x < 20 else 4)
    zone_s = lambda x, y: 1 if y < -2 else (3 if x < 20 else 4)
    veh = [
        (1, "Car", make_rows(1, "Car", stream_rows(1, 1.0, 15.0, 5.0), zone_x, n, (4.5, 1.8))),
        (2, "Car", make_rows(2, "Car", stream_rows(2, 2.0, 15.0, 5.0, jitter=1.2), zone_x, n, (4.5, 1.8))),
        (3, "Car", make_rows(3, "Car", stream_rows(3, 5.0, 15.0, 5.0), zone_x, n, (4.5, 1.8))),
        (4, "Car", make_rows(4, "Car", gap_subject_path(), zone_s, n, (4.5, 1.8))),
    ]
    app.lines["Line 1"] = [(1500, -1000), (1500, 2000)]
    app.run3_reference_text.delete("1.0", "end")
    app.run3_reference_text.insert("1.0", "8|2-3-4|Line 1")
    app.run3_gap_subject_1367_var.set(False)
    app.run3_gap_subject_5631_var.set(False)
    out, summary = run_scene(app, veh)
    print("scene 3 output:", out)

    mv = summary["source_counts"]["movement_counts"]
    check("scene 3 movements: S = 1-3-4, stream = 2-3-4 x3", mv.get("1-3-4") == 1 and mv.get("2-3-4") == 3, str(mv))
    gap = read_csv(os.path.join(out, "T_Gap_Acceptance.csv"))
    roles = sorted(r["Gap_Role"] for r in gap)
    check("Gap Acceptance exactly one rejected + one accepted gap (jitter did not add gaps)",
          roles == ["Accepted", "Rejected"], str(roles) + " " + str([r["X31_Available_Gap"] for r in gap]))
    by = {r["Gap_Role"]: r for r in gap}
    rej, acc = by.get("Rejected"), by.get("Accepted")
    if rej and acc:
        check("Gap Acceptance rejected gap ~ 0.92 s (closed before the subject entered)", abs(float(rej["X31_Available_Gap"]) - 0.917) < 0.06,
              rej["X31_Available_Gap"])
        check("Gap Acceptance accepted gap = time left at zone-3 entry = 1.0 s", abs(float(acc["X31_Available_Gap"]) - 1.0) < 0.05,
              acc["X31_Available_Gap"])
        check("Gap Acceptance waiting time = entry 4.0 s - first seen 0.017 s ~ 3.98 s", abs(float(acc["X32_Waiting_Time"]) - 3.98) < 0.1,
              acc["X32_Waiting_Time"])
        check("Gap Acceptance Access stage, decided in zone 3", acc["Decision_Stage"] == "Access" and acc["Decision_Zone"] == "3",
              f"{acc['Decision_Stage']} zone {acc['Decision_Zone']}")
        check("Gap Acceptance subject 4 (1-3-4) vs stream 2-3-4 on Line 1",
              acc["Subject_ID"] == "4" and acc["Subject_Movement"] == "1-3-4" and acc["Conflicting_Movement"] == "2-3-4"
              and acc["Reference_Line"] == "Line 1")
        check("Gap Acceptance flags 1 / 0", acc["Gap_Acceptance"] == "1" and rej["Gap_Acceptance"] == "0")
        check("Gap Acceptance speeds of the subject and stream vehicles are reported",
              acc["Subject_Speed_kmh"] != "" and acc["Conflict_Speed_A_kmh"] != "")


def scene4(app):
    """Gap Acceptance: subject 1-3-6-7 meets TWO streams at once (2-3-4 on Line 1, 5-6-7 on Line 2).
    It enters the conflict zones at t = 4.0 s. 2-3-4 crosses at 1, 2, 5 s -> open gap 2->5 leaves 1.0 s;
    5-6-7 crosses at 1.5, 2.5, 4.5 s -> open gap 2.5->4.5 leaves 0.5 s => the smaller (5-6-7, 0.5 s) controls.
    Rejected: 2-3-4 gap 1->2 (1.0 s) and 5-6-7 gap 1.5->2.5 (1.0 s)."""
    n = 480
    zone_s = lambda x, y: 1 if y < -2 else (3 if y < 2 else (6 if y < 6 else 7))
    zone_a = lambda x, y: 2 if x < 10 else (3 if x < 20 else 4)
    zone_b = lambda x, y: 5 if x < 10 else (6 if x < 20 else 7)
    veh = [
        (1, "Car", make_rows(1, "Car", stream_rows(1, 1.0, 15.0, 5.0), zone_a, n, (4.5, 1.8))),
        (2, "Car", make_rows(2, "Car", stream_rows(2, 2.0, 15.0, 5.0), zone_a, n, (4.5, 1.8))),
        (3, "Car", make_rows(3, "Car", stream_rows(3, 5.0, 15.0, 5.0), zone_a, n, (4.5, 1.8))),
        (4, "Car", make_rows(4, "Car", stream_rows(4, 1.5, 16.0, -20.0), zone_b, n, (4.5, 1.8))),
        (5, "Car", make_rows(5, "Car", stream_rows(5, 2.5, 16.0, -20.0), zone_b, n, (4.5, 1.8))),
        (6, "Car", make_rows(6, "Car", stream_rows(6, 4.5, 16.0, -20.0), zone_b, n, (4.5, 1.8))),
        (7, "Car", make_rows(7, "Car", lambda t: (15.0, -6.0) if t < 3.0 else (15.0, -6.0 + 4.0 * (t - 3.0)), zone_s, n, (4.5, 1.8))),
    ]
    app.lines["Line 1"] = [(1500, -1000), (1500, 2000)]
    app.lines["Line 2"] = [(1600, -3000), (1600, 1000)]
    app.run3_reference_text.delete("1.0", "end")
    app.run3_reference_text.insert("1.0", "8|2-3-4|Line 1\n8|5-6-7|Line 2")
    app.run3_gap_subject_134_var.set(False)
    app.run3_gap_subject_1367_var.set(True)
    app.run3_gap_subject_5631_var.set(False)
    out, summary = run_scene(app, veh)
    print("scene 4 output:", out)
    mv = summary["source_counts"]["movement_counts"]
    check("scene 4 movements: subject 1-3-6-7, streams 2-3-4 x3 and 5-6-7 x3",
          mv.get("1-3-6-7") == 1 and mv.get("2-3-4") == 3 and mv.get("5-6-7") == 3, str(mv))
    gap = read_csv(os.path.join(out, "T_Gap_Acceptance.csv"))
    acc = [r for r in gap if r["Gap_Role"] == "Accepted"]
    rej = [r for r in gap if r["Gap_Role"] == "Rejected"]
    check("Gap Acceptance two simultaneous streams: 1 accepted + 2 rejected", len(acc) == 1 and len(rej) == 2,
          str([(r["Gap_Role"], r["Conflicting_Movement"], r["X31_Available_Gap"]) for r in gap]))
    if acc:
        check("Gap Acceptance smaller remaining gap controls (5-6-7, 0.5 s)",
              acc[0]["Conflicting_Movement"] == "5-6-7" and abs(float(acc[0]["X31_Available_Gap"]) - 0.5) < 0.05,
              f"{acc[0]['Conflicting_Movement']} {acc[0]['X31_Available_Gap']}")
    check("Gap Acceptance rejected gaps come from both streams",
          {r["Conflicting_Movement"] for r in rej} == {"2-3-4", "5-6-7"}, str([r["Conflicting_Movement"] for r in rej]))
    app.run3_gap_subject_134_var.set(True)
    app.run3_gap_subject_5631_var.set(True)


def scene6(app):
    """Gap Acceptance WITHOUT any Line: the reference time of a stream vehicle = the first time it is seen in the
    origin zone of its stream (zone 2 for 2-3-4). Stream cars first appear in zone 2 (x = 5 m) at 1, 2 and 5 s."""
    n = 480
    zone_x = lambda x, y: 2 if x < 10 else (3 if x < 20 else 4)
    zone_s = lambda x, y: 1 if y < -2 else (3 if x < 20 else 4)
    veh = [
        (1, "Car", make_rows(1, "Car", stream_rows(1, 2.0, 15.0, 5.0, t_appear=1.0), zone_x, n, (4.5, 1.8))),
        (2, "Car", make_rows(2, "Car", stream_rows(2, 3.0, 15.0, 5.0, t_appear=2.0), zone_x, n, (4.5, 1.8))),
        (3, "Car", make_rows(3, "Car", stream_rows(3, 6.0, 15.0, 5.0, t_appear=5.0), zone_x, n, (4.5, 1.8))),
        (4, "Car", make_rows(4, "Car", gap_subject_path(), zone_s, n, (4.5, 1.8))),
    ]
    saved = {k: list(v) for k, v in app.lines.items()}
    for k in app.lines:
        app.lines[k] = []
    app.run3_reference_text.delete("1.0", "end")
    app.run3_reference_text.insert("1.0", "8|2-3-4|Line 1")
    app.run3_gap_subject_1367_var.set(False)
    app.run3_gap_subject_5631_var.set(False)
    out, summary = run_scene(app, veh)
    print("scene 6 output:", out)
    gap = read_csv(os.path.join(out, "T_Gap_Acceptance.csv"))
    check("Gap Acceptance works without a Line (origin-zone fallback): 1 accepted + 1 rejected",
          sorted(r["Gap_Role"] for r in gap) == ["Accepted", "Rejected"], str([(r["Gap_Role"], r["X31_Available_Gap"]) for r in gap]))
    by = {r["Gap_Role"]: r for r in gap}
    if by.get("Accepted") and by.get("Rejected"):
        check("fallback: accepted gap 2->5 s leaves 1.0 s at t = 4.0 s", abs(float(by["Accepted"]["X31_Available_Gap"]) - 1.0) < 0.05,
              by["Accepted"]["X31_Available_Gap"])
        check("fallback: rejected gap 1->2 s = ~1.0 s", abs(float(by["Rejected"]["X31_Available_Gap"]) - 1.0) < 0.06, by["Rejected"]["X31_Available_Gap"])
        check("fallback is named in Reference_Line / QC_Flag", by["Accepted"]["Reference_Line"] == "Observed Zone 2"
              and "Origin_Zone" in by["Accepted"]["QC_Flag"], f"{by['Accepted']['Reference_Line']} | {by['Accepted']['QC_Flag']}")
    for k, v in saved.items():
        app.lines[k] = v
    app.run3_gap_subject_1367_var.set(True)
    app.run3_gap_subject_5631_var.set(True)


def scene7(app):
    """Gap Acceptance, STOP inside the conflict zone -> Access rejected, then Exit stage.
    Subject 1-3-4 enters zone 3 at t = 4.0 s (gap 3->6 s is open), stops at (15, -1) from 4.25 to 5.75 s, then drives
    on to zone 4 (target) at ~6.6 s. Stream 2-3-4 crosses Line 1 at 2, 3, 6, 8 s.
    Access: gap 2->3 closed before entry = Rejected (1.0 s); gap 3->6 open at entry but the driver stopped = Rejected (2.0 s).
    Exit: only NEW gaps after the resumption (5.77 s): gap 6->8 contains the target-zone entry = Accepted (~1.4 s left)."""
    n = 720
    zone_x = lambda x, y: 2 if x < 10 else (3 if x < 20 else 4)
    zone_s = lambda x, y: 1 if y < -2 else (3 if x < 20 else 4)
    veh = [
        (1, "Car", make_rows(1, "Car", stream_rows(1, 2.0, 15.0, 5.0), zone_x, n, (4.5, 1.8))),
        (2, "Car", make_rows(2, "Car", stream_rows(2, 3.0, 15.0, 5.0), zone_x, n, (4.5, 1.8))),
        (3, "Car", make_rows(3, "Car", stream_rows(3, 6.0, 15.0, 5.0), zone_x, n, (4.5, 1.8))),
        (4, "Car", make_rows(4, "Car", stream_rows(4, 8.0, 15.0, 5.0), zone_x, n, (4.5, 1.8))),
        (5, "Car", make_rows(5, "Car", gap_subject_path(hold=(4.25, 5.75)), zone_s, n, (4.5, 1.8))),
    ]
    app.lines["Line 1"] = [(1500, -1000), (1500, 2000)]
    app.run3_reference_text.delete("1.0", "end")
    app.run3_reference_text.insert("1.0", "8|2-3-4|Line 1")
    app.run3_gap_subject_1367_var.set(False)
    app.run3_gap_subject_5631_var.set(False)
    out, summary = run_scene(app, veh)
    print("scene 7 output:", out)
    gap = read_csv(os.path.join(out, "T_Gap_Acceptance.csv"))
    rows = [(r["Decision_Stage"], r["Gap_Role"], round(float(r["X31_Available_Gap"]), 2)) for r in gap]
    print("   rows:", rows)
    access = [r for r in gap if r["Decision_Stage"] == "Access"]
    exit_ = [r for r in gap if r["Decision_Stage"] == "Exit"]
    check("stop in the conflict zone: Access has 2 rejected gaps, no accepted one",
          len(access) == 2 and all(r["Gap_Role"] == "Rejected" for r in access), str(rows))
    check("Access rejected gaps are ~1.0 s (2->3) and ~2.0 s (3->6, open at entry)",
          sorted(round(float(r["X31_Available_Gap"]), 1) for r in access) == [1.0, 2.0], str(rows))
    check("Exit stage: exactly one accepted gap (6->8 contains the target-zone entry)",
          len(exit_) == 1 and exit_[0]["Gap_Role"] == "Accepted" and abs(float(exit_[0]["X31_Available_Gap"]) - 1.4) < 0.1, str(rows))
    check("Exit stage is decided in the target zone 4", bool(exit_) and exit_[0]["Decision_Zone"] == "4")
    check("the gap 3->6 of the Access stage is NOT reused in Exit",
          not any(abs(float(r["Gap_Start_Time"]) - 3.0) < 0.05 for r in exit_))
    check("QC tells about the stop", all("Stop_" in r["QC_Flag"] for r in gap), str([r["QC_Flag"] for r in gap][:2]))
    app.run3_gap_subject_1367_var.set(True)
    app.run3_gap_subject_5631_var.set(True)


def scene5(app):
    """A car that wobbles across a zone boundary (labels 2,3,2,3,4 with visits of 0.2 s each) is
    still recognised as 2-3-4 (status Exact_AfterDedupe) and gets LDP rows."""
    zone_w = lambda x, y: 2 if x < 10 else (3 if x < 12 else (2 if x < 14 else (3 if x < 20 else 4)))
    veh = [(1, "Car", make_rows(1, "Car", along_x(0.0, 10.0), zone_w, 360, (4.5, 1.8)))]
    out, summary = run_scene(app, veh)
    print("scene 5 output:", out)
    ms = summary["source_counts"]["movement_status"]
    check("wobbling car recognised as 2-3-4 after removing repeated zones", ms.get("Exact_AfterDedupe") == 1
          and summary["source_counts"]["movement_counts"].get("2-3-4") == 1, str(ms))
    ldp = read_csv(os.path.join(out, "T_LDP.csv"))
    check("LDP is computed for it (status Exact_AfterDedupe counts as Exact)", len(ldp) >= 2, str(len(ldp)))
    wide = read_csv(os.path.join(out, "T_Speed.csv"))
    check("vehicle speed table shows status and movement", wide[0]["Movement"] == "2-3-4" and wide[0]["Movement_Status"] == "Exact_AfterDedupe")


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
    print("=== scene 3: Gap Acceptance ===")
    scene3(app)
    print("=== scene 4: Gap Acceptance, two streams at once ===")
    scene4(app)
    print("=== scene 5: zone-boundary wobble ===")
    scene5(app)
    print("=== scene 6: Gap Acceptance without a Line ===")
    scene6(app)
    print("=== scene 7: Gap Acceptance, stop in the conflict zone ===")
    scene7(app)

    root.destroy()
    print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
