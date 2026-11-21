"""End-to-end Run 3 of the site types (1.59.0) on SYNTHETIC scenes with known answers (no video, no YOLO): the 4-leg junction with Zone 8, and the same cars
analysed as a 4-leg junction with a median island (two 3-leg junctions) and as a 3-leg junction (where Zone 8 and the way across do not exist).

Run from the Run folder:   python tests/e2e_sites.py
Units: metres; pixel = metre x PPM (PPM = 100, no perspective); 60 FPS. A car drives along +x at 10 m/s; its zone is by x (30 m split evenly among the zones of its Movement).
"""
import csv
import importlib.util
import json
import os
import sys
import tempfile
import tkinter as tk

os.environ["PK_STUDIO_CUDA_RELAUNCHED"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

PPM, FPS = 100.0, 60.0
failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def car(tid, zones, y, t0=0.0, speed=10.0, n=720):
    """A car that enters at t0 and drives along +x: the rows of Detection_Records (30 m of road split evenly among `zones`)."""
    rows = []
    hl, hw = 4.5 / 2 * PPM, 1.8 / 2 * PPM
    for i in range(n):
        t = i / FPS - t0
        x = speed * t
        if x < 0 or x >= 30:
            continue
        zone = zones[min(len(zones) - 1, int(x / (30.0 / len(zones))))]
        cx, cy = x * PPM, y * PPM
        rows.append({"frame": i + 1, "timestamp": f"{(i + 1) / FPS:.6f}", "track_id": tid, "class_name": "Car", "confidence": "0.9",
                     "bbox_x1": int(cx - hl), "bbox_y1": int(cy - hw), "bbox_x2": int(cx + hl), "bbox_y2": int(cy + hw),
                     "trajectory_x": int(cx), "trajectory_y": int(cy), "zone": f"Zone {zone}"})
    return rows


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{k: (v.replace("→", "-") if isinstance(v, str) else v) for k, v in r.items()} for r in csv.DictReader(f)]


def run_scene(app, vehicles):
    out = tempfile.mkdtemp(prefix="pk_sites_")
    rows = sorted((r for _, rs in vehicles for r in rs), key=lambda r: (r["frame"], r["track_id"]))
    write_csv(os.path.join(out, "Detection_Records.csv"), list(rows[0].keys()), rows)
    write_csv(os.path.join(out, "ID_Zone_Summary.csv"), ["track_id", "class_name"], [{"track_id": tid, "class_name": "Car"} for tid, _ in vehicles])
    app._run3_cfg = app._run3_snapshot_config()
    app.run3_processing({}, out, "T")
    app.root.update_idletasks()
    with open(os.path.join(out, "Summary.json"), encoding="utf-8") as f:
        return out, json.load(f)


def main():
    root = tk.Tk()
    root.withdraw()
    app = m.Run1App(root)
    app.run3_lc_max_lateral_var.set("0")
    app.run3_site_id_var.set("8")
    app.run3_traj_smooth_method_var.set("none")
    app.run3_ref_line_source_var.set("drawn")
    app.run3_ppm_var.set(str(PPM))
    app.run3_perspective_enabled_var.set(False)
    for key, val in (("lane_entry_motorcycle_m", "1.5"), ("lane_entry_car_m", "3.25"), ("lane_opp_motorcycle_m", "1.2"), ("lane_opp_car_m", "3.0"), ("median_m", "0")):
        app.run3_geometry_vars[key].set(val)
    app.run3_ldp_smoothing_var.set("1")

    # every way through the 4-leg junction once, the left turn from Zone 8 twice (a Headway pair; a Gap subject behind the through cars of 5-6-7)
    ways = [
        (1, (8, 6, 7), 0.0, 0.0), (2, (8, 6, 7), 0.0, 8.0), (3, (5, 6, 8), 6.0, 0.5), (4, (8, 6, 3, 4), 9.0, 1.0), (5, (1, 3, 6, 8), 12.0, 1.5),
        (6, (8, 6, 3, 1), 15.0, 2.0), (7, (2, 3, 4), -6.0, 2.5), (8, (5, 6, 7), -9.0, 1.0), (9, (5, 6, 7), -9.0, 5.5), (10, (1, 3, 4), -3.0, 3.0),
        (11, (2, 3, 1), -15.0, 3.5), (12, (1, 3, 6, 7), -18.0, 4.0), (13, (5, 6, 3, 1), -21.0, 4.5),
    ]
    veh = [(tid, car(tid, z, y, t0)) for tid, z, y, t0 in ways]
    expect = {1: "8-6-7", 2: "8-6-7", 3: "5-6-8", 4: "8-6-3-4", 5: "1-3-6-8", 6: "8-6-3-1", 7: "2-3-4", 8: "5-6-7", 9: "5-6-7", 10: "1-3-4", 11: "2-3-1",
              12: "1-3-6-7", 13: "5-6-3-1"}

    # ---------------------------------------------------------------- 4-leg junction
    app.run3_site_type_var.set("x_open")
    out, summary = run_scene(app, veh)
    print("4-leg output:", out)
    mc = summary["source_counts"]["movement_counts"]
    check("[x_open] every Movement of the 4-leg junction is counted (11 of them)", set(mc) == set(m.site_movements("x_open")), str(sorted(mc)))
    want = {}
    for mv in expect.values():
        want[mv] = want.get(mv, 0) + 1
    check("[x_open] each car got the Movement it drives (Zone 8 included)", all(mc.get(mv, 0) == n for mv, n in want.items()), str(mc))
    speed = read_csv(os.path.join(out, "Speed.csv")) if os.path.isfile(os.path.join(out, "Speed.csv")) else []
    got = {}
    for r in speed:
        got.setdefault(r["Vehicle_ID"], set()).add(r["Movement"])
    check("[x_open] the Speed rows of every car carry its Movement", all(got.get(str(tid)) == {mv} for tid, mv in expect.items()), str({k: got.get(str(k)) for k in expect if got.get(str(k)) != {expect[k]}}))
    check("[x_open] Zone 8 has speed rows", any(r["Zone"] == "Zone 8" for r in speed), str(sorted({r["Zone"] for r in speed})))
    check("the summary tells the site type", summary["source_counts"].get("site_type") == "x_open", str(summary["source_counts"].get("site_type")))
    hw_path = os.path.join(out, "Headway.csv")
    hw = read_csv(hw_path) if os.path.isfile(hw_path) else []
    check("[x_open] Headway pairs the two cars of 8-6-7 (the left turn from Zone 8)", any(r["Movement"] == "8-6-7" for r in hw), str(sorted({r["Movement"] for r in hw})))
    check("[x_open] Headway has no row of a Movement with a single car", {r["Movement"] for r in hw} <= {"8-6-7", "5-6-7"}, str(sorted({r["Movement"] for r in hw})))
    gap_path = os.path.join(out, "Gap_Acceptance.csv")
    gap = read_csv(gap_path) if os.path.isfile(gap_path) else []
    subjects = {r["Subject_Movement"] for r in gap}
    print("   gap subjects:", sorted(subjects), "| streams:", sorted({r["Conflicting_Movement"] for r in gap}))
    check("[x_open] Gap Acceptance has the waiting drivers of Zone 8 (8-6-7 / 8-6-3-4 / 8-6-3-1) among its subjects", bool(subjects & {"8-6-7", "8-6-3-4", "8-6-3-1"}), str(sorted(subjects)))
    check("[x_open] a subject of Zone 8 waits only for the streams it should",
          all(r["Conflicting_Movement"] in m.site_gap_conflicts("x_open")[r["Subject_Movement"]] for r in gap), str(sorted({(r["Subject_Movement"], r["Conflicting_Movement"]) for r in gap})))

    # ---------------------------------------------------------------- the same cars, with a median island: two 3-leg junctions
    app.run3_site_type_var.set("x_median")
    out2, summary2 = run_scene(app, veh)
    mc2 = summary2["source_counts"]["movement_counts"]
    check("[x_median] only the Movements of the two 3-leg junctions are counted", set(mc2) == set(m.site_movements("x_median")), str(sorted(mc2)))
    check("[x_median] 8-6-7, 5-6-8, 2-3-4, 5-6-7, 1-3-4, 2-3-1 are counted", mc2.get("8-6-7") == 2 and mc2.get("5-6-8") == 1 and mc2.get("2-3-4") == 1 and mc2.get("5-6-7") == 2
          and mc2.get("1-3-4") == 1 and mc2.get("2-3-1") == 1, str(mc2))
    speed2 = read_csv(os.path.join(out2, "Speed.csv"))
    crossing = {"4", "5", "6", "12", "13"}                                                 # 8-6-3-4, 1-3-6-8, 8-6-3-1, 1-3-6-7, 5-6-3-1: they cross the median island
    check("[x_median] the cars that cross the median island have no Movement (they are not analysed as one)", all(r["Movement"] == "" for r in speed2 if r["Vehicle_ID"] in crossing),
          str({r["Vehicle_ID"]: r["Movement"] for r in speed2 if r["Vehicle_ID"] in crossing and r["Movement"]}))
    gap2 = read_csv(os.path.join(out2, "Gap_Acceptance.csv")) if os.path.isfile(os.path.join(out2, "Gap_Acceptance.csv")) else []
    check("[x_median] the waiting drivers are the ones of 1-3-4 and 8-6-7 only", {r["Subject_Movement"] for r in gap2} <= {"1-3-4", "8-6-7"}, str(sorted({r["Subject_Movement"] for r in gap2})))

    # ---------------------------------------------------------------- the 3-leg junction does not know Zone 8
    app.run3_site_type_var.set("t_full")
    out3, summary3 = run_scene(app, veh)
    mc3 = summary3["source_counts"]["movement_counts"]
    check("[t_full] the 3-leg junction counts its 6 Movements only, as before", set(mc3) == set(m.site_movements("t_full")), str(sorted(mc3)))
    check("[t_full] the cars of Zone 8 are not given a Movement", mc3.get("2-3-4") == 1 and mc3.get("5-6-7") == 2 and mc3.get("1-3-6-7") == 1 and mc3.get("5-6-3-1") == 1, str(mc3))
    app.run3_site_type_var.set("t_small")
    out4, summary4 = run_scene(app, veh)
    mc4 = summary4["source_counts"]["movement_counts"]
    check("[t_small] the 3-leg junction with 3 zones counts 1-3-4, 2-3-1, 2-3-4 only", set(mc4) == {"1-3-4", "2-3-1", "2-3-4"} and mc4.get("2-3-4") == 1, str(mc4))

    root.destroy()
    print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
