"""Sensitivity analysis of Run 3 settings (plan 3.2).

Re-runs Run 3 on an EXISTING Run 2 result (Detection_Records + ID_Zone_Summary) once for every
value of one setting and tabulates how each indicator changes (N, Mean, Median, P85).  YOLO is
not run again, the original output folder is not touched (everything happens in a temp copy).

    python tools/sensitivity.py <output_folder> <setting>=<v1>,<v2>,... [<setting>=...] [--out file.csv]

Examples (setting names = keys of the "run3" part of Settings.json, i.e. RUN3_DEFAULTS):
    python tools/sensitivity.py ../Output/Run3 pet_interaction_distance_m=2,3,4
    python tools/sensitivity.py ../Output/Run3 speed_max_kmh=40,60,80 ttc_max_record_s=2,3,5

The run name is the name of the folder (older results: taken from <run>_Detection_Records.csv); the saved
Settings.json (if present) supplies all other settings.  Needs torch/cv2/ultralytics
(it uses the real PKStudio code) and creates a hidden Tk window.
"""
import copy
import csv
import importlib.util
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def load_pkstudio():
    os.environ["PK_STUDIO_CUDA_RELAUNCHED"] = "1"
    spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_run_name(folder):
    for fn in sorted(os.listdir(folder)):
        if fn == "Detection_Records.csv":
            return os.path.basename(os.path.normpath(folder))
        if fn.endswith("_Detection_Records.csv"):
            return fn[: -len("_Detection_Records.csv")]
    raise SystemExit(f"no Detection_Records.csv in {folder}")


def read_indicator_summary(path):
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def run_sensitivity(app, folder, run_name, params, base_settings=None):
    """params = {setting: [values]}. Returns rows
    (Setting, Value, Indicator, Group, N, Mean, Median, P85) one per indicator group and value."""
    out_rows = []
    if base_settings is None:
        base_settings = app.get_settings()   # a partial dict would reset e.g. the Speed zone ticks
    for setting, values in params.items():
        for value in values:
            tmp = tempfile.mkdtemp(prefix="pk_sens_")
            try:
                import combine_clips
                for plain in ("Detection_Records.csv", "ID_Zone_Summary.csv"):
                    src = combine_clips.result_file(folder, plain, run_name)
                    if src:
                        shutil.copy(src, os.path.join(tmp, plain))
                st = copy.deepcopy(base_settings)
                st.setdefault("run3", {})[setting] = value
                app.set_settings(st)
                app._run3_cfg = app._run3_snapshot_config()
                app.run3_processing({}, tmp, run_name)
                for r in read_indicator_summary(os.path.join(tmp, "Indicator_Summary.csv")):
                    out_rows.append({
                        "Setting": setting, "Value": value, "Indicator": r.get("Indicator", ""),
                        "Group": r.get("Group", ""), "N": r.get("N", ""), "Mean": r.get("Mean", ""),
                        "Median": r.get("Median", ""), "P85": r.get("P85", ""),
                    })
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
    return out_rows


def write_rows(path, rows):
    cols = ["Setting", "Value", "Indicator", "Group", "N", "Mean", "Median", "P85"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main(argv):
    out_path = None
    if "--out" in argv:
        i = argv.index("--out")
        out_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) < 2:
        print(__doc__)
        return 1
    folder = os.path.abspath(argv[0])
    params = {}
    for a in argv[1:]:
        key, _, vals = a.partition("=")
        params[key.strip()] = [v.strip() for v in vals.split(",") if v.strip()]
    run_name = find_run_name(folder)
    mod = load_pkstudio()
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    app = mod.Run1App(root)
    base = None
    import combine_clips
    sp = combine_clips.result_file(folder, "Settings.json", run_name)
    if sp:
        with open(sp, encoding="utf-8") as f:
            base = json.load(f)
    rows = run_sensitivity(app, folder, run_name, params, base)
    out_path = out_path or os.path.join(folder, "Sensitivity_" + "_".join(params) + ".csv")
    write_rows(out_path, rows)
    print(f"{len(rows)} rows -> {out_path}")
    root.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
