"""Batch run (plan 3.1) and tracker / confidence sweep (plan 2.3) for PK Studio, without the GUI.

Runs the real Run 1 + 2 + 3 pipeline (YOLO + tracker + zones + indicators) on several videos
and/or for several values of a Run 1 setting, one output folder per run, then writes a
comparison table.

    python tools/batch_run.py --settings <Research_Settings.json> --out <root_folder> \\
           --videos <video files and/or folders> [--sweep track_buffer=15,30,60] [--sweep match_threshold=0.7,0.8,0.9]

  Folders are searched recursively and the output MIRRORS the folder structure that was imported, at any
  depth and with any folder names (nothing is assumed to be a "place" or a "day"):
      <picked folder>/A/B/clip1.mp4   ->   <out>/<picked folder>/A/B/clip1/   (this clip's own CSV files)
  A folder that already exists in <out> is reused, a missing one is created, so a later batch is ADDED to the
  same tree and finished clips are skipped (--skip-done); old results are never touched.

  --settings   a <run>_Research_Settings.json saved by an earlier run in the program (it holds the model,
               zones, Lines, calibration, widths, ...). Without it the program defaults are used.
  --videos     video files and/or folders (default: the video in the settings); a folder is scanned for
               videos in all its sub-folders; its own name is the first output level
  --keep-levels N  also keep the names of the N folders ABOVE each picked folder in the output (default 0):
               picking <root>/A/B with N=1 gives <out>/A/B/..., so a sub-folder can be added to a tree that
               was imported from a higher folder before
  --plan       a batch plan .json saved by the program's Batch window: per clip the time range to analyse and
               whether / which part to record (replaces --videos; --save-video is then ignored)
  --skip-done  skip a clip whose result folder already has Run_3_Summary.json (resume an interrupted batch)
  --zone-file  Zone file to use instead of the one in the settings (e.g. for a different camera)
  --set        setting=value (repeatable) fixed for all runs, e.g. lane_entry_motorcycle_m=1.5
  --sweep      setting=v1,v2,...  (repeatable; every combination is run). Run 1 settings such as
               track_buffer, match_threshold, track_high, track_low, new_track, confidence, iou, img_size
  --save-video also write the annotated result video (off by default: much faster)
  --out        root folder; each run goes to <out>/<same folders as the input>/<video>[__setting-value...]/

Results: <out>/Batch_Comparison.csv (one row per run: IDs, ID-switch warnings, detection losses,
untracked detections, duplicate tracks, Movement Exact count, time); a new batch updates the rows of the clips it ran
and keeps the rows of the other clips.

How to read a sweep: fewer unique_track_ids / id_switch_warnings / detection_loss_events / duplicate
tracks at a similar number of Exact movements = steadier tracking. This tool only reports - it does
not pick or change a setting for you.  Needs torch/cv2/ultralytics (Python 3.12 with CUDA); a long
video takes as long as in the program.
"""
import argparse
import copy
import csv
import itertools
import json
import os
import queue
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load_pkstudio():
    import importlib.util
    os.environ["PK_STUDIO_CUDA_RELAUNCHED"] = "1"
    spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def slug(text):
    return re.sub(r"[^0-9A-Za-z._-]+", "_", str(text)).strip("_")


VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".mts", ".m4v")


def find_videos(inputs, keep_levels=0):
    """inputs = files and/or folders -> sorted list of (video_path, rel_dir). rel_dir is the folder structure
    to rebuild in the output: for a picked folder it starts with the folder's own name and continues with every
    sub-folder down to the video's folder, at any depth. keep_levels = N also keeps the names of the N folders
    above the picked folder. A single file gets the last N folder names above it ('' when N = 0)."""
    found = []
    for item in inputs:
        item = os.path.abspath(item)
        if os.path.isfile(item):
            parts = [x for x in os.path.dirname(item).replace("\\", "/").split("/") if x][-keep_levels:] if keep_levels > 0 else []
            found.append((item, "/".join(parts)))
            continue
        top = item
        for _ in range(int(keep_levels) + 1):
            parent = os.path.dirname(top)
            if parent == top:
                break
            top = parent
        for dirpath, dirnames, filenames in os.walk(item):
            dirnames.sort()
            for fn in sorted(filenames):
                if fn.lower().endswith(VIDEO_EXTS):
                    rel = os.path.relpath(dirpath, top).replace("\\", "/")
                    found.append((os.path.join(dirpath, fn), "" if rel == "." else rel))
    return found


def duplicate_run_dirs(out_root, runs):
    """Run folders that two clips of the plan would share (e.g. a.mp4 and a.mov in one folder) -> list of paths."""
    seen, dup = {}, []
    for video, rel, ov in runs:
        d = run_dir_for(out_root, rel, run_name_for(video, ov))
        if d in seen and seen[d] != video:
            dup.append(d)
        seen[d] = video
    return dup


def plan_runs(videos, sweeps):
    """videos = [(video_path, rel_dir)] (plain paths are accepted too); sweeps = {setting: [values]}
    -> list of (video, rel_dir, {setting: value}) for every combination."""
    keys = list(sweeps)
    combos = list(itertools.product(*[sweeps[k] for k in keys])) if keys else [()]
    items = [(v, "") if isinstance(v, str) else v for v in videos]
    return [(v, rel, dict(zip(keys, combo))) for v, rel in items for combo in combos]


def run_name_for(video, overrides):
    base = slug(os.path.splitext(os.path.basename(video))[0])
    if overrides:
        base += "__" + "__".join(f"{slug(k)}-{slug(v)}" for k, v in overrides.items())
    return base


def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def count_rows(path):
    if not os.path.isfile(path):
        return None
    with open(path, newline="", encoding="utf-8-sig") as f:
        return max(0, sum(1 for _ in f) - 1)


def run_dir_for(out_root, rel_dir, name):
    return os.path.join(out_root, *[x for x in rel_dir.split("/") if x], name)


def collect_row(run_dir, run_name, video, rel_dir, overrides, error, seconds):
    run1 = read_json(os.path.join(run_dir, run_name + "_Research_Run_Summary.json"))
    run3 = read_json(os.path.join(run_dir, "Run_3_Summary.json"))
    dup = (run3.get("diagnostics", {}).get("duplicate_tracks") or {}).get("tracks_affected")
    mstat = (run3.get("source_counts", {}) or {}).get("movement_status", {}) or {}
    exact = None if not mstat else mstat.get("Exact", 0) + mstat.get("Exact_AfterDedupe", 0)
    row = {
        "Run": run_name, "Folder": rel_dir, "Video": os.path.basename(video),
        "Overrides": "; ".join(f"{k}={v}" for k, v in overrides.items()),
        "Status": "ERROR: " + error if error else run1.get("status", "no summary"),
        "Frames": run1.get("processed_frames"),
        "Unique_Track_IDs": run1.get("unique_track_ids"),
        "ID_Switch_Warnings": run1.get("id_switch_warnings"),
        "Detection_Loss_Events": run1.get("detection_loss_events"),
        "Untracked_Detections": run1.get("untracked_detections"),
        "Duplicate_Tracks": dup,
        "Movement_Exact": exact,
        "Tracks_In_Run3": (run3.get("source_counts", {}) or {}).get("track_ids"),
        "Seconds": round(seconds, 1),
    }
    for name, fname in (("Rows_LC", "Run_3_Lateral_Clearance_Pairs.csv"), ("Rows_Gap", "Run_3_Gap_Acceptance.csv"),
                        ("Rows_TTC", "Run_3_TTC.csv"), ("Rows_PET", "Run_3_PET.csv"),
                        ("Rows_Speed", "Run_3_Speed.csv"), ("Rows_LDP", "Run_3_LDP.csv")):
        row[name] = count_rows(os.path.join(run_dir, fname))
    return row


CLIP_KEYS = ("analysis_start_s", "analysis_end_s", "save_video", "record_start_s", "record_end_s")


def clip_settings(base_settings, video, rel_dir, overrides, out_root, clip_params=None, save_video=False):
    """Settings dict of one clip -> (settings, run_name, run_dir). clip_params = the per-clip choices
    (analysis_start_s / analysis_end_s / save_video / record_start_s / record_end_s) of the batch plan."""
    name = run_name_for(video, overrides)
    run_dir = run_dir_for(out_root, rel_dir, name)
    st = copy.deepcopy(base_settings)
    st.update({"video": video, "output": run_dir, "run_name": name,
               "show_preview": False, "save_video": bool(save_video)})
    for k, v in (clip_params or {}).items():
        if k in CLIP_KEYS:
            st[k] = v
    for k, v in overrides.items():
        st[k] = v
        if isinstance(st.get("run3"), dict) and k in st["run3"]:
            st["run3"][k] = v
    return st, name, run_dir


def save_plan(path, out_root, clips):
    """clips = [{video, rel_dir, analysis_start_s, analysis_end_s, save_video, record_start_s, record_end_s}]"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "output": out_root, "clips": clips}, f, indent=2, ensure_ascii=False)


def load_plan(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    clips = data.get("clips")
    if not isinstance(clips, list) or not all(isinstance(c, dict) and c.get("video") for c in clips):
        raise ValueError("not a PK Studio batch plan (needs a 'clips' list with a 'video' in each)")
    return data.get("output", ""), clips


def clip_label(clip):
    """Short text of a clip's choices for lists: 'analyse 0:30 - 2:15 | record 1:00 - 1:30'."""
    a0, a1 = str(clip.get("analysis_start_s", "") or ""), str(clip.get("analysis_end_s", "") or "")
    ana = "ทั้งคลิป" if not a0 and not a1 else f"{a0 or 'เริ่ม'} – {a1 or 'จบ'}"
    if not clip.get("save_video", False):
        rec = "ไม่บันทึก"
    else:
        r0, r1 = str(clip.get("record_start_s", "") or ""), str(clip.get("record_end_s", "") or "")
        rec = "ตลอดช่วงวิเคราะห์" if not r0 and not r1 else f"{r0 or 'เริ่ม'} – {r1 or 'จบ'}"
    return ana, rec


def finish_batch(out_root, runs, rows, log=print):
    """Batch_Comparison.csv in the output root: the rows of the clips just run replace their old rows, the rows
    of clips from earlier batches stay (so one table grows with the place)."""
    path = os.path.join(out_root, "Batch_Comparison.csv")
    old = {}
    if os.path.isfile(path):
        with open(path, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                old[(r.get("Folder", ""), r.get("Run", ""), r.get("Overrides", ""))] = r
    for r in rows:
        old[(r.get("Folder", ""), r.get("Run", ""), r.get("Overrides", ""))] = r
    write_comparison(path, [old[k] for k in sorted(old)])
    log("comparison -> " + path)


def run_batch(app, base_settings, out_root, runs, save_video=False, skip_done=False, clip_params=None, log=print):
    """Runs every (video, overrides) in `runs`; returns the comparison rows."""
    errors = []
    app.show_error = lambda msg: errors.append(str(msg))
    app.finish_integrated_ui = lambda *a, **k: None
    rows = []
    for i, (video, rel_dir, overrides) in enumerate(runs, 1):
        st, name, run_dir = clip_settings(base_settings, video, rel_dir, overrides, out_root,
                                          (clip_params or {}).get(video), save_video)
        os.makedirs(run_dir, exist_ok=True)
        if skip_done and os.path.isfile(os.path.join(run_dir, "Run_3_Summary.json")):
            log(f"[{i}/{len(runs)}] {name}: already done, skipped")
            rows.append(collect_row(run_dir, name, video, rel_dir, overrides, "", 0.0))
            continue
        log(f"[{i}/{len(runs)}] {name}")
        app.set_settings(st)
        app.validate_measurements()
        app.validate_run3_settings()
        settings = app.get_settings()
        app._rt = app._runtime_snapshot(settings)
        app._run3_cfg = app._run3_snapshot_config()
        app._run3_warnings = app.collect_run3_warnings()
        for w in app._run3_warnings:
            log("   warning: " + w.replace("\n", " "))
        app._zone_poly_cache = None
        app._overlay_cache = None
        app.running = True
        app.stop_event.clear()
        app.pause_event.set()
        del errors[:]
        t0 = time.time()
        app.run_processing(settings)
        seconds = time.time() - t0
        app.running = False
        while True:                      # drop the queued UI updates (no window is shown)
            try:
                app._ui_queue.get_nowait()
            except queue.Empty:
                break
        err = errors[0] if errors else ""
        rows.append(collect_row(run_dir, name, video, rel_dir, overrides, err, seconds))
        log(f"    -> {rows[-1]['Status']}  IDs={rows[-1]['Unique_Track_IDs']}  {seconds:.0f} s")
    return rows


COLUMNS = ["Run", "Folder", "Video", "Overrides", "Status", "Frames", "Unique_Track_IDs", "ID_Switch_Warnings",
           "Detection_Loss_Events", "Untracked_Detections", "Duplicate_Tracks", "Movement_Exact",
           "Tracks_In_Run3", "Rows_LC", "Rows_LDP", "Rows_Gap", "Rows_TTC", "Rows_PET", "Rows_Speed", "Seconds"]


def write_comparison(path, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def parse_sweeps(items):
    sweeps = {}
    for a in items or []:
        key, _, vals = a.partition("=")
        values = [v.strip() for v in vals.split(",") if v.strip()]
        if not key.strip() or not values:
            raise SystemExit(f"bad --sweep '{a}' (use setting=v1,v2,...)")
        sweeps[key.strip()] = values
    return sweeps


def main(argv=None):
    ap = argparse.ArgumentParser(description="PK Studio batch run / tracker sweep", add_help=True)
    ap.add_argument("--settings", help="<run>_Research_Settings.json from an earlier run")
    ap.add_argument("--out")
    ap.add_argument("--plan", help="batch plan .json saved by the program (per-clip time range and recording)")
    ap.add_argument("--videos", nargs="*")
    ap.add_argument("--zone-file")
    ap.add_argument("--sweep", action="append")
    ap.add_argument("--set", action="append", dest="fixed")
    ap.add_argument("--save-video", action="store_true")
    ap.add_argument("--skip-done", action="store_true")
    ap.add_argument("--keep-levels", type=int, default=0)
    args = ap.parse_args(argv)

    mod = load_pkstudio()
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    app = mod.Run1App(root)
    if args.settings:
        base = read_json(args.settings)
        if not base:
            raise SystemExit(f"cannot read settings: {args.settings}")
    else:
        base = app.get_settings()
    if args.zone_file:
        base["zone_file"] = args.zone_file
        base.pop("zone_snapshot", None)      # load the given Zone file instead of the embedded copy
    clip_params = {}
    plan_out = ""
    if args.plan:
        plan_out, plan_clips = load_plan(args.plan)
        videos = []
        for c in plan_clips:
            v = os.path.abspath(c["video"])
            if not os.path.isfile(v):
                raise SystemExit(f"video not found: {v}")
            videos.append((v, str(c.get("rel_dir", "") or "")))
            clip_params[v] = {k: c[k] for k in CLIP_KEYS if k in c}
    else:
        inputs = args.videos or ([base["video"]] if base.get("video") else [])
        if not inputs:
            raise SystemExit("no video given and none in the settings")
        for v in inputs:
            if not os.path.exists(v):
                raise SystemExit(f"video or folder not found: {v}")
        videos = find_videos(inputs, keep_levels=args.keep_levels)
        if not videos:
            raise SystemExit("no video files found in: " + ", ".join(inputs))
    run3 = base.setdefault("run3", {})
    for a in args.fixed or []:
        key, _, val = a.partition("=")
        if key.strip() in base and key.strip() != "run3":
            base[key.strip()] = val.strip()
        else:
            run3[key.strip()] = val.strip()
    sweeps = parse_sweeps(args.sweep)
    runs = plan_runs(videos, sweeps)
    if not (args.out or plan_out):
        raise SystemExit("give --out <folder> (or a plan that has an output folder)")
    out_root = os.path.abspath(args.out or plan_out)
    os.makedirs(out_root, exist_ok=True)
    try:
        rows = run_batch(app, base, out_root, runs, save_video=args.save_video, skip_done=args.skip_done,
                         clip_params=clip_params)
    except ValueError as exc:
        raise SystemExit("settings problem: %s (give the missing value with --set name=value, or use --settings from a saved run)" % exc)
    finish_batch(out_root, runs, rows)
    root.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main())
