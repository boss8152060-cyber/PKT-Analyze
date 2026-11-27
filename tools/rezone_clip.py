"""Give a finished clip its zones (and its camera geometry) again WITHOUT detecting again (PKT-Analyze 1.61.8).

Use it when a clip was analysed with zones drawn for another camera view, e.g. a clip of the same camera recording
that got the zones of a later recording:

    python tools/rezone_clip.py <clip folder> --from <clip folder with the right zones> [--dry-run]

What it does to <clip folder>:
  1. keeps the old files once: 0_Raw/Detection_Records_before_rezone.csv, 0_Raw/ID_Zone_Summary_before_rezone.csv,
     9_Summary/Settings_before_rezone.json
  2. copies the camera-view settings of --from into its Settings.json: the zones (zone_snapshot, zone_file) and the
     Run 3 geometry (run3: calibration, alignment, lines ...). Clip settings (video, analysis window, run name ...) stay.
  3. gives every detection its zone again from its trajectory point (rezone_detection_records in PKStudio.py, the
     same rule as Run 1: checked to give the same zones and routes as Run 1 on real clips) and writes
     Detection_Records.csv, 1_ID_Zone.csv (ID_Zone_Summary) and 9_Summary/Zone_Summary.csv
  4. notes "rezoned_from_raw" in Run_Summary.json
Then compute the indicators again from the raw data (clip list option, or _rerun_indicators) so 2_Speed ... 8_PET use
the new zones. The detections themselves (boxes, track IDs, trajectory points) do not change.
"""
import csv
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import combine_clips as cc  # noqa: E402

VIEW_KEYS = ("zone_snapshot", "zone_file", "run3")      # what belongs to the camera view, not to the clip


def load_core():
    with open(os.path.join(os.path.dirname(HERE), "PKStudio.py"), encoding="utf-8") as f:
        text = f.read()
    ns = {"os": os}
    exec(compile(text[text.index("# ==== CORE-BEGIN"):text.index("# ==== CORE-END ====")], "PKStudio.py[CORE]", "exec"), ns)
    return ns


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def write_rows(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def keep_once(src, dst):
    if src and os.path.isfile(src) and not os.path.exists(dst):
        shutil.copy2(src, dst)


def rezone_clip(clip, source, dry_run=False, log=print):
    name = os.path.basename(os.path.normpath(clip))
    settings_path = cc.result_file(clip, "Settings.json", name)
    det_path = cc.result_file(clip, "Detection_Records.csv", name)
    ids_path = cc.result_file(clip, "ID_Zone_Summary.csv", name)
    zone_path = cc.result_file(clip, "Zone_Summary.csv", name) or os.path.join(clip, cc.SUMMARY_DIR, "Zone_Summary.csv")
    src_settings = cc.result_file(source, "Settings.json") if os.path.isdir(source) else source
    if not (settings_path and det_path and ids_path and src_settings):
        raise FileNotFoundError("the clip needs Settings.json, Detection_Records.csv and ID_Zone_Summary.csv; the source a Settings.json")
    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)
    with open(src_settings, encoding="utf-8") as f:
        src = json.load(f)
    zones = src["zone_snapshot"]["zones"]
    core = load_core()
    fields, rows = read_rows(det_path)
    old_ids = {r["track_id"]: r["zone_sequence"] for r in read_rows(ids_path)[1]}
    new_rows, id_rows, zone_rows = core["rezone_detection_records"](rows, zones, 1)
    changed = sum(1 for a, b in zip(rows, new_rows) if a.get("zone") != b.get("zone"))
    routes = sum(1 for r in id_rows if old_ids.get(r["track_id"]) != r["zone_sequence"])
    log(f"{name}: zones from {os.path.basename(os.path.dirname(os.path.dirname(src_settings)))}; "
        f"{changed} of {len(rows)} detections and {routes} of {len(id_rows)} routes change")
    if dry_run:
        return changed, routes
    raw_dir, sum_dir = os.path.dirname(det_path), os.path.dirname(settings_path)
    keep_once(det_path, os.path.join(raw_dir, "Detection_Records_before_rezone.csv"))
    keep_once(ids_path, os.path.join(raw_dir, "ID_Zone_Summary_before_rezone.csv"))
    keep_once(settings_path, os.path.join(sum_dir, "Settings_before_rezone.json"))
    for k in VIEW_KEYS:
        if k in src:
            settings[k] = src[k]
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)
    write_rows(det_path, fields, new_rows)
    write_rows(ids_path, ["track_id", "class_name", "first_seen_timestamp", "last_seen_timestamp", "track_duration_seconds",
                          "first_zone", "last_zone", "zone_sequence", "unique_zones_visited", "zone_transition_count",
                          "total_zone_time_seconds"], id_rows)
    write_rows(zone_path, ["zone", "unique_ids", "total_entries", "average_duration_seconds", "min_duration_seconds",
                           "max_duration_seconds", "first_entry_timestamp", "last_entry_timestamp"], zone_rows)
    rs = cc.result_file(clip, "Run_Summary.json", name)
    if rs:
        with open(rs, encoding="utf-8") as f:
            data = json.load(f)
        data["rezoned_from_raw"] = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "zones_from": src_settings,
                                    "detections_changed": changed, "routes_changed": routes}
        with open(rs, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    return changed, routes


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if "--from" not in argv or len(args) != 2:
        print(__doc__)
        return 1
    clip, source = args[0], argv[argv.index("--from") + 1]
    rezone_clip(clip, source, dry_run="--dry-run" in argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
