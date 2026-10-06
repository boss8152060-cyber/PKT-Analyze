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
  Q  Car  1-3-6   along +y at x = 15, passes (15, 0) at t = 3.1 s  -> PET(P,Q) = 1.24 s with the conflict area (point only: 1.6 s; P-R: area = undefined, point only 0.1 s)
  R  Car  1-3-6   along +y at x = 15, passes (15, 0) at t = 1.6 s  -> the 4.5 m x 1.8 m boxes touch at t = 1.235 s: TTC ~ 0 (Crossing, 90 deg)
  F  Car  (zone 3) along +x at y = -12, 10 m/s behind  L  Car at 5 m/s, 20 m ahead
        -> boxes (+ 0.25 m each side) 20 - 5 t - 5.0 m apart, closing at 5 m/s: TTC = 3 - t (ends when L leaves at t = 2 s: ~1.0 s, Rear-end, 0 deg)
"""
import csv
import importlib.util
import json
import cv2
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
            "frame": i + 1, "timestamp": f"{(i + 1) / FPS:.6f}", "track_id": tid,
            "class_name": cls, "confidence": "0.9",
            "bbox_x1": int(cx - hl), "bbox_y1": int(cy - hw), "bbox_x2": int(cx + hl), "bbox_y2": int(cy + hw),
            "trajectory_x": int(cx), "trajectory_y": int(cy),
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
    detail = os.path.join(os.path.dirname(path), "TTC_Detail.csv")
    if os.path.basename(path) == "TTC.csv" and os.path.isfile(detail):          # TTC.csv keeps the core columns; the relative vectors etc. are in TTC_Detail.csv
        with open(detail, newline="", encoding="utf-8-sig") as f:
            extra = {r["Event_ID"]: r for r in csv.DictReader(f)}
        rows = [dict(extra.get(r["Event_ID"], {}), **r) for r in rows]
    return rows


def run_scene(app, vehicles):
    """vehicles = [(tid, class_name, rows)]. Returns (out_dir, summary)."""
    out = tempfile.mkdtemp(prefix="pk_e2e_")
    rows = [r for _, _, rs in vehicles for r in rs]
    rows.sort(key=lambda r: (r["frame"], r["track_id"]))
    write_csv(os.path.join(out, "Detection_Records.csv"), list(rows[0].keys()), rows)
    write_csv(os.path.join(out, "ID_Zone_Summary.csv"), ["track_id", "class_name"],
              [{"track_id": tid, "class_name": cls} for tid, cls, _ in vehicles])
    app._run3_cfg = app._run3_snapshot_config()
    app.run3_processing({}, out, "T")
    app.root.update_idletasks()
    with open(os.path.join(out, "Summary.json"), encoding="utf-8") as f:
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
    dup_rows = read_csv(os.path.join(out, "Duplicate_Tracks.csv"))
    check("duplicate report: ID 6 is a duplicate of ID 2", len(dup_rows) == 1 and dup_rows[0]["Duplicate_ID"] == "6"
          and dup_rows[0]["Kept_ID"] == "2", str(dup_rows))
    lc_rows = read_csv(os.path.join(out, "Lateral_Clearance.csv"))
    check("no Lateral Clearance pair involves the duplicate ID 6 (it would show a fake -1.8 m)",
          all("6" not in r["Pair_ID"].split("_") for r in lc_rows),
          str(sorted({r["Pair_ID"] for r in lc_rows if "6" in r["Pair_ID"].split("_")})))

    # ---- movement ----
    mc = summary["source_counts"]["movement_counts"]
    check("movement 2-3-4 = 2 vehicles (A, B)", mc.get("2-3-4") == 2, str(mc))
    check("movement 5-6-7 = 1 vehicle (C)", mc.get("5-6-7") == 1, str(mc))
    check("movement 1-3-4 = 1 vehicle (E)", mc.get("1-3-4") == 1, str(mc))

    # ---- Speed (every frame, inside the selected zones; no statistics) ----
    sp = read_csv(os.path.join(out, "Speed.csv"))
    check("Speed.csv columns: one row per vehicle x frame", [*sp[0]] == ["Frame", "Time_s", "Vehicle_ID", "Vehicle_Class", "Zone", "Movement", "Speed_kmh", "QC_Flag"], str([*sp[0]]) if sp else "no rows")
    for vid, kmh in (("1", 36.0), ("2", 36.0), ("3", 18.0)):
        vr = [r for r in sp if r["Vehicle_ID"] == vid]
        zs = sorted({r["Zone"] for r in vr})
        check(f"vehicle {vid} has speeds in 3 zones", len(zs) == 3, str(zs))
        check(f"vehicle {vid} speed ~{kmh} km/h in every frame (a few hundred rows)", len(vr) > 100 and all(abs(float(r["Speed_kmh"]) - kmh) < 1.0 for r in vr),
              f"{len(vr)} rows, min {min(float(r['Speed_kmh']) for r in vr):.2f} max {max(float(r['Speed_kmh']) for r in vr):.2f}" if vr else "no rows")
    check("vehicle 1 rows carry its Movement 2-3-4; the duplicate ID 6 has no rows", all(r["Movement"] == "2-3-4" for r in sp if r["Vehicle_ID"] == "1")
          and not any(r["Vehicle_ID"] == "6" for r in sp))
    check("no old Speed files: Speed_Detail.csv / Speed_Statistics.csv are not written", not os.path.exists(os.path.join(out, "Speed_Detail.csv"))
          and not os.path.exists(os.path.join(out, "Speed_Statistics.csv")))
    check("untracked detections diagnostic present (0 here)", summary["diagnostics"]["untracked_detections"]["rows_with_track_id_minus_1"] == 0)
    raw_sp = read_csv(os.path.join(out, "Speed.csv"), raw=True)
    check("CSV movement cells use arrows (Excel would turn 2-3-4 into a date)",
          any(r["Movement"] == "2→3→4" for r in raw_sp) and not any("-" in r["Movement"] for r in raw_sp), str([r["Movement"] for r in raw_sp][:3]))
    # only the ticked zones: Zone 3 alone
    for zz, vv in app.run3_speed_zone_vars.items():
        vv.set(zz == 3)
    out_zs, _ = run_scene(app, veh)
    for vv in app.run3_speed_zone_vars.values():
        vv.set(True)
    sp_z3 = read_csv(os.path.join(out_zs, "Speed.csv"))
    check("speed zones: with only Zone 3 ticked every row is in Zone 3", len(sp_z3) > 0 and {r["Zone"] for r in sp_z3} == {"Zone 3"}, str({r["Zone"] for r in sp_z3}))
    # --- per-zone calibration: Zone 3 has its own reference quad measured at 50 px/m (base = 100 px/m) ---
    app.run3_zone_calibrations = {"3": {"points": [[1000, -200], [2000, -200], [2000, 800], [1000, 800]], "lengths": [20, 20, 20, 20]}}
    out_z, summary_z = run_scene(app, veh)
    app.run3_zone_calibrations = {}
    sp_z = read_csv(os.path.join(out_z, "Speed.csv"))
    bz = {z: [float(r["Speed_kmh"]) for r in sp_z if r["Vehicle_ID"] == "1" and r["Zone"] == z] for z in ("Zone 2", "Zone 3", "Zone 4")}
    check("zone calibration: Zone 3 speed of vehicle 1 doubles (36 -> 72 km/h, own scale 50 px/m)", bool(bz["Zone 3"]) and all(abs(v - 72.0) < 1.5 for v in bz["Zone 3"]),
          f"{min(bz['Zone 3']):.2f}..{max(bz['Zone 3']):.2f}" if bz["Zone 3"] else "no rows")
    check("zone calibration: Zone 2 and Zone 4 keep the base scale (36 km/h)", bool(bz["Zone 2"]) and bool(bz["Zone 4"]) and all(abs(v - 36.0) < 1.0 for v in bz["Zone 2"] + bz["Zone 4"]),
          str({k: (round(min(v), 2), round(max(v), 2)) for k, v in bz.items() if v}))
    zinfo = summary_z["calibration"].get("zone_calibrations", {})
    check("zone calibration is reported in the summary with its alignment check", "Zone 3" in zinfo and zinfo["Zone 3"]["alignment_rms_m"] > 1.0, str(zinfo))
    # --- speed above the plausible maximum is flagged (the rows stay) ---
    app.run3_speed_max_var.set("30")
    out_o, summary_o = run_scene(app, veh)
    app.run3_speed_max_var.set("80")
    sp_o = read_csv(os.path.join(out_o, "Speed.csv"))
    flagged = {r["Vehicle_ID"] for r in sp_o if "Speed_Above_Max" in r["QC_Flag"]}
    check("max speed 30: the 36 km/h vehicles 1, 2, 4, 5 are flagged, the 18 km/h vehicle 3 is not", flagged == {"1", "2", "4", "5"}, str(flagged))
    check("flagged rows stay in the file", len(sp_o) == len(sp))
    # --- tools/sensitivity.py: re-run Run 3 for several values of one setting (the Lateral Clearance side limit changes how many samples are measured) ---
    sys.path.insert(0, os.path.join(HERE, "..", "tools"))
    import sensitivity
    sens = sensitivity.run_sensitivity(app, out, "T", {"lc_max_lateral_m": ["0.5", "3.5"]})
    lcn = {r["Value"]: int(r["N"]) for r in sens if r["Indicator"].startswith("Lateral Clearance") and r["Group"] == "All samples"}
    check("sensitivity: a 3.5 m side limit measures more Lateral Clearance samples than 0.5 m", lcn.get("3.5", 0) > lcn.get("0.5", 0), str(lcn))
    check("sensitivity leaves the source folder untouched", not os.path.exists(os.path.join(out, "Sensitivity_lc_max_lateral_m.csv")))

    # ---- LDP ----
    ldp = read_csv(os.path.join(out, "LDP.csv"))
    lz = {(r["Vehicle_ID"], r["Zone"]): r for r in ldp}
    check("LDP rows for every main-road vehicle A, B, C (any class); D, E are not main-road", {v for v, _ in lz} == {"1", "2", "3"}, str(sorted(lz)))
    check("LDP car B (straight) ~ 0 %", float(lz[("2", "Zone 3")]["LDP_percent"]) < 0.5)
    check("LDP risk level: A zone 3 (14.7 %) = Interaction, C zone 6 (28.6 %) = Interaction", lz[("1", "Zone 3")]["LDP_Level"] == "Interaction" and lz[("3", "Zone 6")]["LDP_Level"] == "Interaction")
    check("LDP overall level = the less severe of the LDP level and the speed level (every row)",
          all(r["LDP_Risk_Level"] == m.combine_risk(r["LDP_Level"], r["Speed_Level"]) for r in ldp if r["Speed_Level"]), str([(r["LDP_Level"], r["Speed_Level"], r["LDP_Risk_Level"]) for r in ldp][:4]))
    a3 = float(lz[("1", "Zone 3")]["LDP_percent"])
    check("LDP A zone 3 ~ 0.35/(4.75/2) = 14.74 %", abs(a3 - 14.74) < 0.7, f"{a3:.3f}")
    check("LDP A zone 2 ~ 0 %", float(lz[("1", "Zone 2")]["LDP_percent"]) < 0.5)
    c6 = float(lz[("3", "Zone 6")]["LDP_percent"])
    check("LDP C zone 6 ~ 0.60/(4.20/2) = 28.57 % (opposite-side W)", abs(c6 - 28.57) < 1.2, f"{c6:.3f}")
    check("LDP W_entry for A, W_opp for C: LDP = Delta_Y / (W/2) x 100 with W 4.75 and 4.20",
          abs(float(lz[("1", "Zone 3")]["Delta_Y_m"]) / (4.75 / 2) * 100 - a3) < 0.05 and abs(float(lz[("3", "Zone 6")]["Delta_Y_m"]) / (4.20 / 2) * 100 - c6) < 0.05)
    check("LDP zone 1 never reported", all(r["Zone"] != "Zone 1" for r in ldp))

    # ---- Lateral Clearance ----
    lc = read_csv(os.path.join(out, "Lateral_Clearance.csv"))
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
    tvr = read_csv(os.path.join(out, "Detection_Records_Topview.csv"))
    check("Topview records: one row per observed point, in metres (the speed lives in Speed.csv since v28(131))", len(tvr) > 0 and {"x_m", "y_m", "cx_m", "cy_m"} <= set(tvr[0]) and "speed_kmh" not in tvr[0],
          str(len(tvr)))
    spd_rows = read_csv(os.path.join(out, "Speed.csv"))
    sp = [float(r["Speed_kmh"]) for r in spd_rows if r["Vehicle_ID"] == "1" and r["Speed_kmh"] != ""]
    check("Speed.csv: the speed of every frame (vehicle A of scene 1 drives 10 m/s = 36 km/h, weaving a little)", len(sp) > 10 and all(abs(v - 36.0) < 2.5 for v in sp),
          f"{len(sp)} values, min {min(sp) if sp else None}, max {max(sp) if sp else None}")
    tvv = os.path.join(out, "Tracking_Topview.mp4")
    cap_tv = cv2.VideoCapture(tvv)
    dur_tv = cap_tv.get(cv2.CAP_PROP_FRAME_COUNT) / (cap_tv.get(cv2.CAP_PROP_FPS) or 1.0)
    cap_tv.release()
    t_all_tv = [float(r["timestamp"]) for r in tvr]
    check("Topview video lasts as long as the analysed part of the video (not slowed down)",
          abs(dur_tv - (max(t_all_tv) - min(t_all_tv))) < 0.5, f"video {dur_tv:.2f} s, data {max(t_all_tv) - min(t_all_tv):.2f} s")
    check("Topview video written (plain grid when the video file is unknown)", os.path.isfile(tvv) and os.path.getsize(tvv) > 1000,
          str(os.path.getsize(tvv) if os.path.isfile(tvv) else "missing"))
    check("Trajectory_XY.png (the X-Y plane picture) is written", os.path.isfile(os.path.join(out, "Trajectory_XY.png")) and os.path.getsize(os.path.join(out, "Trajectory_XY.png")) > 2000)
    pr = read_csv(os.path.join(out, "Lateral_Clearance_Pairs.csv"))
    check("Lateral Clearance pair summary rows (A-B x3, A-E x2, B-E x2, D-E x1)", len(pr) == 8, str([(r['Pair_ID'], r['Zone']) for r in pr]))
    # motorcycle-pairs-only switch: only the pairs that include a motorcycle remain
    app.run3_lc_motorcycle_pairs_only_var.set(True)
    out_m, _ = run_scene(app, veh)
    app.run3_lc_motorcycle_pairs_only_var.set(False)
    only_m = {r["Pair_ID"] for r in read_csv(os.path.join(out_m, "Lateral_Clearance.csv"))}
    check("Lateral Clearance motorcycle-pairs-only option keeps A-B and A-E only", only_m == {"1_2", "1_5"}, str(sorted(only_m)))
    # sideways limit: D-E (4.1 m apart) is dropped at 3.5 m, the pairs closer than that stay
    app.run3_lc_max_lateral_var.set("3.5")
    out_l, _ = run_scene(app, veh)
    app.run3_lc_max_lateral_var.set("0")
    lim = {r["Pair_ID"] for r in read_csv(os.path.join(out_l, "Lateral_Clearance.csv"))}
    check("Lateral Clearance sideways limit 3.5 m drops D-E (4.1 m) and keeps the closer pairs", "4_5" not in lim and {"1_2", "1_5", "2_5"} <= lim, str(sorted(lim)))
    ind = read_csv(os.path.join(out, "Indicator_Summary.csv"))
    check("indicator summary lists LDP and Lateral Clearance (Speed is per frame in Speed.csv since v28(131), no statistics rows)", any("LDP" in r["Indicator"] for r in ind) and any("Lateral Clearance" in r["Indicator"] for r in ind) and not any(r["Indicator"].startswith("Speed") for r in ind))


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
    app.run3_ttc_method_var.set("box")                              # the rectangle method first (the checks below), the point method at the end of this scene
    out, summary = run_scene(app, veh)
    print("scene 2 output:", out)
    # the pair screening radius is adjustable: at 5 m only the P-R pair (about 1 m apart when they cross) is evaluated
    app.run3_ttc_pair_radius_var.set("5")
    out_r, _ = run_scene(app, veh)
    app.run3_ttc_pair_radius_var.set("20")
    pairs_r = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]) for r in read_csv(os.path.join(out_r, "TTC.csv"))}
    check("TTC pair screening radius is adjustable (5 m keeps only P-R)", pairs_r == {("1", "3")}, str(sorted(pairs_r)))
    # the conflict-angle limits are adjustable: with the crossing limit at 95 deg the 90 deg pair is a lane change
    app.run3_ttc_angle_cross_var.set("95")
    out_a, _ = run_scene(app, veh)
    app.run3_ttc_angle_cross_var.set("85")
    types_a = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]): r["TTC_Type"] for r in read_csv(os.path.join(out_a, "TTC.csv"))}
    check("TTC conflict-angle limit is adjustable (90 deg is Lane change below a 95 deg limit)", types_a.get(("1", "3")) == "Lane change", str(types_a))

    reasons = summary["diagnostics"].get("empty_outputs", [])
    check("empty Gap Acceptance output is explained (no Line drawn yet)", any("Gap Acceptance" in r and "Line" in r for r in reasons), str(reasons))
    check("non-empty indicators are not listed as empty", not any(r.startswith(("LDP", "TTC", "PET", "Speed")) for r in reasons), str(reasons))
    mv = summary["source_counts"]["movement_counts"]
    check("scene 2 movements: P = 2-3-4, Q and R = 1-3-6-7 (partial)", mv.get("2-3-4") == 1 and mv.get("1-3-6-7") == 2, str(mv))

    # ---- PET ----
    pet = read_csv(os.path.join(out, "PET.csv"))
    pairs = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]): r for r in pet}
    check("PET (conflict area, radius (W_A+W_B)/2 = 1.8 m): one event P-Q (P-R are in the area at the same time = undefined, Q-R never cross, F/L no movement)",
          set(pairs) == {("1", "2")}, str(sorted(pairs)))
    if ("1", "2") in pairs:
        r = pairs[("1", "2")]
        check("PET PET(P,Q) = 1.24 s (P leaves the 1.8 m circle at 1.68 s, Q enters it at 2.92 s)", abs(float(r["PET_s"]) - 1.24) < 0.06, r["PET_s"])
        check("PET area radius written: 1.8 m", abs(float(r["Area_Radius_m"]) - 1.8) < 0.01, r["Area_Radius_m"])
        check("PET crossing point written: (15, 0)", abs(float(r["Cross_X_m"]) - 15.0) < 0.05 and abs(float(r["Cross_Y_m"])) < 0.05,
              f"{r['Cross_X_m']} {r['Cross_Y_m']}")
        check("PET conflict zone 3, type by the TTC angle rule: P (+x) and Q (+y) meet at 90 deg = Crossing",
              r["Conflict_Zone"] == "Zone 3" and r["Conflict_Type"] == "Crossing" and abs(float(r["Theta_deg"]) - 90.0) < 3.0, f"{r['Conflict_Zone']} {r['Conflict_Type']} {r['Theta_deg']}")
        lim_pet = m.RISK_DEFAULT_LIMITS["pet_s"]
        check("PET levels follow the limits: PET level from PET_s, speed level from the 36 km/h of P and Q (Moderate), overall = the less severe",
              r["PET_Level"] == m.risk_level_low_is_risky(float(r["PET_s"]), lim_pet) and r["Speed_Level"] == "Moderate"
              and r["PET_Risk_Level"] == m.combine_risk(r["PET_Level"], "Moderate") and abs(float(r["Speed_A_At_Crossing_kmh"]) - 36.0) < 0.5,
              f"{r['PET_s']} {r['PET_Level']} {r['Speed_Level']} {r['PET_Risk_Level']} speeds {r['Speed_A_At_Crossing_kmh']} {r['Speed_B_At_Crossing_kmh']}")

    # PET with the area switched off = the crossing point only: PET = the difference of the times at the point
    app.run3_pet_use_area_var.set(False)
    out_pt, _ = run_scene(app, veh)
    app.run3_pet_use_area_var.set(True)
    pet_pt = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]): r for r in read_csv(os.path.join(out_pt, "PET.csv"))}
    check("PET point only: events P-Q and P-R", set(pet_pt) == {("1", "2"), ("1", "3")}, str(sorted(pet_pt)))
    if ("1", "2") in pet_pt and ("1", "3") in pet_pt:
        check("PET point only: PET(P,Q) = 1.6 s, PET(P,R) = 0.1 s, no radius",
              abs(float(pet_pt[("1", "2")]["PET_s"]) - 1.6) < 0.06 and abs(float(pet_pt[("1", "3")]["PET_s"]) - 0.1) < 0.06 and pet_pt[("1", "2")]["Area_Radius_m"] == "",
              f"{pet_pt[('1', '2')]['PET_s']} {pet_pt[('1', '3')]['PET_s']}")

    # ---- TTC (vehicle rectangles: the time until they first touch) ----
    ttc = read_csv(os.path.join(out, "TTC.csv"))
    ev = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]): r for r in ttc}
    check("TTC columns: conflict angle, relative vectors, DTC",
          {"Theta_deg", "Rel_X_m", "RelV_X_mps", "DTC_m", "TTC_Type", "Collide_X_m", "Collide_Y_m", "Miss_Distance_m"} <= set(ttc[0]) and "S_Conflict_Distance_m" not in ttc[0],
          str(sorted(ttc[0])) if ttc else "no rows")
    check("TTC events = F-L and P-R (P-L runs 12 m beside each other: the rectangles never touch)", set(ev) == {("4", "5"), ("1", "3")}, str(sorted(ev)))
    fl = ev.get(("4", "5"))
    if fl:
        check("TTC F-L: Rear-end, angle 0 deg", fl["TTC_Type"] == "Rear-end" and abs(float(fl["Theta_deg"])) < 1.0, f"{fl['TTC_Type']} {fl['Theta_deg']}")
        check("TTC F-L: boxes (4.5 m + 0.25 m on each side) closing at 5 m/s: (20 - 5 t - 5.0) / 5 = 3 - t -> ~ 1.0 s at t = 2 s", abs(float(fl["TTC_s"]) - 1.0) < 0.06, fl["TTC_s"])
        check("TTC F-L: DTC = TTC x 5 m/s", abs(float(fl["DTC_m"]) - 5.0 * float(fl["TTC_s"])) < 0.01, fl["DTC_m"])
        check("TTC F-L: relative speed 5 m/s = 18 km/h", abs(float(fl["Rel_Speed_kmh"]) - 18.0) < 0.5, fl["Rel_Speed_kmh"])
    pr_ = ev.get(("1", "3"))
    if pr_:
        check("TTC P-R: Crossing, angle 90 deg", pr_["TTC_Type"] == "Crossing" and abs(float(pr_["Theta_deg"]) - 90.0) < 1.0, f"{pr_['TTC_Type']} {pr_['Theta_deg']}")
        check("TTC P-R: the boxes touch at t = 1.235 s, so the last approaching frames have TTC ~ 0", float(pr_["TTC_s"]) < 0.05, pr_["TTC_s"])
        check("TTC P-R: relative speed sqrt(10^2 + 10^2) m/s = 50.9 km/h", abs(float(pr_["Rel_Speed_kmh"]) - 50.91) < 1.0, pr_["Rel_Speed_kmh"])
    check("TTC overall level = the less severe of the TTC level and the speed level (every row)",
          all(r["TTC_Risk_Level"] == m.combine_risk(r["TTC_Level"], r["Speed_Level"]) for r in ttc), str([(r["TTC_Level"], r["Speed_Level"], r["TTC_Risk_Level"]) for r in ttc]))
    check("TTC P-R (TTC ~ 0, speed 36 km/h = Moderate by the speed scale): TTC level High, overall Moderate",
          pr_ and pr_["TTC_Level"] == "High" and pr_["Speed_Level"] == "Moderate" and pr_["TTC_Risk_Level"] == "Moderate", f"{pr_['TTC_Level']} {pr_['Speed_Level']} {pr_['TTC_Risk_Level']}" if pr_ else "")
    check("TTC F-L: its level follows the limits (1.0 / 1.5 / 2.0 s)", fl and fl["TTC_Level"] == m.risk_level_low_is_risky(float(fl["TTC_s"]), m.RISK_DEFAULT_LIMITS["ttc_s"]),
          f"{fl['TTC_s']} {fl['TTC_Level']}" if fl else "")
    # the risk limits are editable: TTC limits 0.05 / 0.5 / 0.9 s -> F-L (~1.0 s) = Interaction, P-R (~0 s) = High
    app.run3_risk_vars["risk_ttc_limits_s"].set("0.05, 0.5, 0.9")
    out_rl, summ_rl = run_scene(app, veh)
    app.run3_risk_vars["risk_ttc_limits_s"].set(m.RUN3_DEFAULTS["risk_ttc_limits_s"])
    lv = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]): (r["TTC_Level"], r["TTC_Risk_Level"]) for r in read_csv(os.path.join(out_rl, "TTC.csv"))}
    check("TTC risk limits are editable (0.05 / 0.5 / 0.9 s: F-L = Interaction, P-R = High level)", lv.get(("4", "5"), ("", ""))[0] == "Interaction" and lv.get(("1", "3"), ("", ""))[0] == "High", str(lv))
    check("the limits used are written to the summary", summ_rl.get("risk_level_limits", {}).get("ttc_s") == [0.05, 0.5, 0.9], str(summ_rl.get("risk_level_limits")))
    # TTC_Frames.csv: every pair frame with a TTC or an overlap; the chosen minimum is marked
    fr_rows = read_csv(os.path.join(out, "TTC_Frames.csv"))
    check("TTC_Frames.csv has the frames of the pairs, with Status and DTC", len(fr_rows) > 20 and {"Status", "Is_Event_Min", "DTC_m", "TTC_s"} <= set(fr_rows[0]), str(len(fr_rows)))
    for pair in (("4", "5"), ("1", "3")):
        mins = [r for r in fr_rows if (r["Vehicle_A_ID"], r["Vehicle_B_ID"]) == pair and r["Is_Event_Min"] == "1"]
        check(f"TTC_Frames: exactly one marked minimum for {pair}, equal to the TTC.csv value", len(mins) == 1 and ev.get(pair) and abs(float(mins[0]["TTC_s"]) - float(ev[pair]["TTC_s"])) < 1e-6,
              str([(r["TTC_s"], ev.get(pair, {}).get("TTC_s")) for r in mins]))
        counted = [float(r["TTC_s"]) for r in fr_rows if (r["Vehicle_A_ID"], r["Vehicle_B_ID"]) == pair and r["Status"] == "Counted"]
        check(f"TTC_Frames: the marked minimum is the smallest counted TTC of {pair}", counted and abs(min(counted) - float(ev[pair]["TTC_s"])) < 1e-6)
    pr_rows = [r for r in fr_rows if (r["Vehicle_A_ID"], r["Vehicle_B_ID"]) == ("1", "3")]
    ov_rows = [r for r in pr_rows if r["Status"] == "Already_Overlapping"]
    check("TTC_Frames: P-R frames after the boxes touch (t > 1.235 s) are Already_Overlapping with no TTC",
          ov_rows and all(r["TTC_s"] == "" and float(r["Time_s"]) > 1.2 for r in ov_rows), f"{len(ov_rows)} overlap rows")
    cnt_pr = [r for r in pr_rows if r["Status"] == "Counted"]
    check("TTC_Frames: P-R counted frames have a TTC that falls as the boxes approach (more than 5 frames)", len(cnt_pr) > 5
          and float(cnt_pr[0]["TTC_s"]) > float(cnt_pr[-1]["TTC_s"]), f"{len(cnt_pr)} counted")
    check("TTC_Frames: P-L (12 m beside each other) has no frames: the rectangles never touch", not [r for r in fr_rows if (r["Vehicle_A_ID"], r["Vehicle_B_ID"]) == ("1", "5")])
    # a vehicle slower than the speed limit skips the frame: L drives 5 m/s = 18 km/h, so a 20 km/h limit drops F-L
    app.run3_ttc_min_speed_var.set("20")
    out_s, _ = run_scene(app, veh)
    app.run3_ttc_min_speed_var.set(m.RUN3_DEFAULTS["ttc_min_speed_kmh"])
    pairs_s = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]) for r in read_csv(os.path.join(out_s, "TTC.csv"))}
    check("TTC: a frame where a vehicle is slower than the speed limit is skipped (20 km/h drops F-L, L = 18 km/h)", pairs_s == {("1", "3")}, str(sorted(pairs_s)))
    # the box margin is adjustable: 0 -> F-L ~ 1.1 s (4.5 m boxes), 0.25 -> ~ 1.0 s, 1.5 -> ~ 0.5 s
    res_m = {}
    for mg in ("0", "1.5"):
        app.run3_ttc_box_margin_var.set(mg)
        o_, _ = run_scene(app, veh)
        res_m[mg] = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]): r for r in read_csv(os.path.join(o_, "TTC.csv"))}.get(("4", "5"))
    app.run3_ttc_box_margin_var.set(m.RUN3_DEFAULTS["ttc_box_margin_m"])
    check("TTC: box margin 0 -> F-L ~ 1.1 s (4.5 m boxes)", res_m["0"] and abs(float(res_m["0"]["TTC_s"]) - 1.1) < 0.06, res_m["0"]["TTC_s"] if res_m["0"] else "missing")
    check("TTC: box margin 1.5 m on each side -> F-L ~ 0.5 s", res_m["1.5"] and abs(float(res_m["1.5"]["TTC_s"]) - 0.5) < 0.06, res_m["1.5"]["TTC_s"] if res_m["1.5"] else "missing")
    # the record limit: 0.5 s keeps only P-R (~ 0 s) and drops F-L (~ 1.0 s); blank records everything
    app.run3_ttc_max_record_var.set("0.5")
    out_c, _ = run_scene(app, veh)
    pairs_c = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]) for r in read_csv(os.path.join(out_c, "TTC.csv"))}
    app.run3_ttc_max_record_var.set("")
    out_b, _ = run_scene(app, veh)
    app.run3_ttc_max_record_var.set(m.RUN3_DEFAULTS["ttc_max_record_s"])
    pairs_b = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]) for r in read_csv(os.path.join(out_b, "TTC.csv"))}
    check("TTC record limit: 0.5 s keeps only P-R; blank = everything is recorded", pairs_c == {("1", "3")} and pairs_b == {("4", "5"), ("1", "3")}, f"{sorted(pairs_c)} | {sorted(pairs_b)}")

    # ---- the POINT method (the default): one point per vehicle, vector TTC, the expected collision point is kept
    app.run3_ttc_method_var.set("point")
    out_p, _ = run_scene(app, veh)
    tp = read_csv(os.path.join(out_p, "TTC.csv"))
    evp = {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]): r for r in tp}
    check("point method: events = F-L and P-R (P-L passes 12 m beside: the points do not come within (1.8+1.8)/2 + 0.5 m)", set(evp) == {("4", "5"), ("1", "3")}, str(sorted(evp)))
    flp = evp.get(("4", "5"))
    if flp:
        check("point method F-L: TTC = (20 - 5 t) / 5 -> ~ 2.0 s (the classic centre-to-centre time); Rear-end", abs(float(flp["TTC_s"]) - 2.0) < 0.05 and flp["TTC_Type"] == "Rear-end", f"{flp['TTC_s']} {flp['TTC_Type']}")
        check("point method F-L: the two paths are parallel (same line) -> no crossing point (Collide blank, no arrivals) and the points meet (miss 0)",
              flp["Collide_X_m"] == "" and flp["Collide_Y_m"] == "" and flp["Arrival_A_s"] == "" and float(flp["Miss_Distance_m"]) < 0.01,
              f"({flp['Collide_X_m']}, {flp['Collide_Y_m']}) miss {flp['Miss_Distance_m']}")
    prp = evp.get(("1", "3"))
    if prp:
        check("point method P-R: Crossing; TTC ~ 0; the expected collision point is where the straight paths cross, (15, 0)", prp["TTC_Type"] == "Crossing" and float(prp["TTC_s"]) < 0.06
              and abs(float(prp["Collide_X_m"]) - 15.0) < 0.1 and abs(float(prp["Collide_Y_m"])) < 0.1, f"{prp['TTC_s']} ({prp['Collide_X_m']}, {prp['Collide_Y_m']})")
        check("point method P-R: the arrival times at the crossing differ by 0.1 s (P at 1.5 s, R at 1.6 s): Arrival_B - Arrival_A ~ 0.1 s",
              abs(abs(float(prp["Arrival_B_s"]) - float(prp["Arrival_A_s"])) - 0.1) < 0.05 and float(prp["Dist_A_to_Collide_m"]) > 0, f"{prp['Arrival_A_s']} {prp['Arrival_B_s']}")
    frp = read_csv(os.path.join(out_p, "TTC_Frames.csv"))
    plp = [r for r in frp if (r["Vehicle_A_ID"], r["Vehicle_B_ID"]) == ("1", "5")]
    check("point method: P-L frames are listed as Miss_Too_Far with a 12 m miss and no counted frame", plp and all(r["Status"] == "Miss_Too_Far" for r in plp) and all(abs(float(r["Miss_Distance_m"]) - 12.0) < 0.3 for r in plp), str({r["Status"] for r in plp}))
    app.run3_ttc_miss_margin_var.set("20")
    out_pg, _ = run_scene(app, veh)
    app.run3_ttc_miss_margin_var.set(m.RUN3_DEFAULTS["ttc_miss_margin_m"])
    check("point method: the miss margin is adjustable (20 m brings P-L back)", ("1", "5") in {(r["Vehicle_A_ID"], r["Vehicle_B_ID"]) for r in read_csv(os.path.join(out_pg, "TTC.csv"))})


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
    gap = read_csv(os.path.join(out, "Gap_Acceptance.csv"))
    roles = sorted(r["Gap_Role"] for r in gap)
    check("Gap Acceptance exactly one rejected + one accepted gap (jitter did not add gaps)",
          roles == ["Accepted", "Rejected"], str(roles) + " " + str([r["Available_Gap_s"] for r in gap]))
    by = {r["Gap_Role"]: r for r in gap}
    rej, acc = by.get("Rejected"), by.get("Accepted")
    if rej and acc:
        check("Gap Acceptance rejected gap ~ 0.92 s (closed before the subject entered)", abs(float(rej["Available_Gap_s"]) - 0.917) < 0.06,
              rej["Available_Gap_s"])
        check("Gap Acceptance accepted gap = time left at zone-3 entry = 1.0 s", abs(float(acc["Available_Gap_s"]) - 1.0) < 0.05,
              acc["Available_Gap_s"])
        check("Gap Acceptance waiting time = entry 4.0 s - first seen 0.017 s ~ 3.98 s", abs(float(acc["Waiting_Time_s"]) - 3.98) < 0.1,
              acc["Waiting_Time_s"])
        check("Gap Acceptance Access stage, decided in zone 3", acc["Decision_Stage"] == "Access" and acc["Decision_Zone"] == "3",
              f"{acc['Decision_Stage']} zone {acc['Decision_Zone']}")
        check("Gap Acceptance subject 4 (1-3-4) vs stream 2-3-4 on Line 1",
              acc["Subject_ID"] == "4" and acc["Subject_Movement"] == "1-3-4" and acc["Conflicting_Movement"] == "2-3-4"
              and acc["Reference_Line"] == "Line 1")
        check("Gap Acceptance Accepted / Rejected (no duplicate 1 / 0 column)", acc["Gap_Role"] == "Accepted" and rej["Gap_Role"] == "Rejected" and "Gap_Acceptance" not in acc)
        check("Gap Acceptance speeds of the subject and stream vehicles are reported",
              acc["Subject_Speed_At_Decision_kmh"] != "" and acc["Conflict_Speed_A_At_Decision_kmh"] != "")


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
    gap = read_csv(os.path.join(out, "Gap_Acceptance.csv"))
    acc = [r for r in gap if r["Gap_Role"] == "Accepted"]
    rej = [r for r in gap if r["Gap_Role"] == "Rejected"]
    check("Gap Acceptance two simultaneous streams: 1 accepted + 2 rejected", len(acc) == 1 and len(rej) == 2,
          str([(r["Gap_Role"], r["Conflicting_Movement"], r["Available_Gap_s"]) for r in gap]))
    if acc:
        check("Gap Acceptance smaller remaining gap controls (5-6-7, 0.5 s)",
              acc[0]["Conflicting_Movement"] == "5-6-7" and abs(float(acc[0]["Available_Gap_s"]) - 0.5) < 0.05,
              f"{acc[0]['Conflicting_Movement']} {acc[0]['Available_Gap_s']}")
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
    gap = read_csv(os.path.join(out, "Gap_Acceptance.csv"))
    check("Gap Acceptance works without a Line (origin-zone fallback): 1 accepted + 1 rejected",
          sorted(r["Gap_Role"] for r in gap) == ["Accepted", "Rejected"], str([(r["Gap_Role"], r["Available_Gap_s"]) for r in gap]))
    by = {r["Gap_Role"]: r for r in gap}
    if by.get("Accepted") and by.get("Rejected"):
        check("fallback: accepted gap 2->5 s leaves 1.0 s at t = 4.0 s", abs(float(by["Accepted"]["Available_Gap_s"]) - 1.0) < 0.05,
              by["Accepted"]["Available_Gap_s"])
        check("fallback: rejected gap 1->2 s = ~1.0 s", abs(float(by["Rejected"]["Available_Gap_s"]) - 1.0) < 0.06, by["Rejected"]["Available_Gap_s"])
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
    gap = read_csv(os.path.join(out, "Gap_Acceptance.csv"))
    rows = [(r["Decision_Stage"], r["Gap_Role"], round(float(r["Available_Gap_s"]), 2)) for r in gap]
    print("   rows:", rows)
    access = [r for r in gap if r["Decision_Stage"] == "Access"]
    exit_ = [r for r in gap if r["Decision_Stage"] == "Exit"]
    check("stop in the conflict zone: Access has 2 rejected gaps, no accepted one",
          len(access) == 2 and all(r["Gap_Role"] == "Rejected" for r in access), str(rows))
    check("Access rejected gaps are ~1.0 s (2->3) and ~2.0 s (3->6, open at entry)",
          sorted(round(float(r["Available_Gap_s"]), 1) for r in access) == [1.0, 2.0], str(rows))
    check("Exit stage: exactly one accepted gap (6->8 contains the target-zone entry)",
          len(exit_) == 1 and exit_[0]["Gap_Role"] == "Accepted" and abs(float(exit_[0]["Available_Gap_s"]) - 1.4) < 0.1, str(rows))
    check("Exit stage is decided in the target zone 4", bool(exit_) and exit_[0]["Decision_Zone"] == "4")
    check("the gap 3->6 of the Access stage is NOT reused in Exit",
          not any(abs(float(r["Gap_Start_Time_s"]) - 3.0) < 0.05 for r in exit_))
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
    ldp = read_csv(os.path.join(out, "LDP.csv"))
    check("LDP is computed for it (status Exact_AfterDedupe counts as Exact)", len(ldp) >= 2, str(len(ldp)))
    spd5 = read_csv(os.path.join(out, "Speed.csv"))
    check("the speed rows of the wobbling car carry its Movement 2-3-4", len(spd5) > 0 and all(r["Movement"] == "2-3-4" for r in spd5))


def main():
    root = tk.Tk()
    root.withdraw()
    app = m.Run1App(root)
    app.run3_write_detail_var.set(True)           # Lateral_Clearance.csv (every sample), TTC_Detail.csv, TTC_Frames.csv are checked below (off by default)
    app.run3_lc_max_lateral_var.set("0")          # the scene's D-E pair is 4.1 m apart sideways; the default limit (3.5 m) is tested below
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
