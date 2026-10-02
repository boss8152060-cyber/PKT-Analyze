"""Combined CSV files over many clips.

Every clip has its own folder with its own CSV files (<clip>_Gap_Acceptance.csv, <clip>_Speed.csv, ...).
This module puts the same kind of file from all clips together into one CSV per kind (All_<kind>.csv), with the
first column `Clip` saying which clip a row comes from (vehicle IDs are only unique inside a clip, so always read
an ID together with Clip), plus All_Clips.csv (the list of clips) and All_Statistics.csv (Mean, SD, V50, V85 ...
over all clips).  It is rebuilt from the clip folders that exist, so adding clips later only means running it again.

The batch calls combine_top_folders() after every run; it can also be used on its own:
    python tools/combine_clips.py <output root> [<top folder name> ...]
Only the standard library is needed.
"""
import csv
import json
import math
import os
import re
import sys

COMBINED_DIR = "All_Clips"

# Vehicle IDs (and event / pair numbers) restart from 1 in every clip, so in the combined files each of these columns
# gets a companion <column>_Unique = "<Clip>#<value>" that is unique over all clips.
ID_COLUMNS = ("track_id", "Vehicle_ID", "Vehicle_ID_A", "Vehicle_ID_B", "Vehicle_A_ID", "Vehicle_B_ID", "Subject_ID",
              "Conflicting_ID_A", "Conflicting_ID_B", "Duplicate_ID", "Kept_ID", "Pair_ID", "Interaction_ID",
              "Event_ID", "Decision_Event_ID")

# kinds of CSV that are put together (the file of a clip is <clip>_<kind>.csv; older runs: Run_3_<kind>.csv)
KINDS = ("Gap_Acceptance", "Critical_Gap", "LDP", "Lateral_Clearance", "Lateral_Clearance_Pairs", "TTC", "PET",
         "Speed", "Speed_Detail", "Duplicate_Tracks", "ID_Zone_Summary")

# kind -> (indicator name, value column, group columns) for All_Statistics.csv
STATISTICS = {
    "Speed_Detail": ("Speed", "Speed_kmh", ("Scope", "Key", "Vehicle_Class")),
    "LDP": ("LDP", "LDP_percent", ("Zone",)),
    "Lateral_Clearance_Pairs": ("Lateral Clearance (pair minimum)", "Lateral_Clearance_Min_m", ("Zone",)),
    "TTC": ("TTC", "TTC_s", ("TTC_Type",)),
    "PET": ("PET", "PET_s", ("Conflict_Type", "Conflict_Zone")),
    "Gap_Acceptance": ("Gap Acceptance (available gap)", "X31_Available_Gap", ("Decision_Stage", "Gap_Role")),
}


def summary_path(clip_dir, clip_name=None):
    """The Summary.json of a clip folder (new name <clip>_Summary.json, older Run_3_Summary.json) or None."""
    clip_name = clip_name or os.path.basename(os.path.normpath(clip_dir))
    for name in (f"{clip_name}_Summary.json", "Run_3_Summary.json"):
        p = os.path.join(clip_dir, name)
        if os.path.isfile(p):
            return p
    return None


def kind_file(clip_dir, kind, clip_name=None):
    clip_name = clip_name or os.path.basename(os.path.normpath(clip_dir))
    for name in (f"{clip_name}_{kind}.csv", f"Run_3_{kind}.csv"):
        p = os.path.join(clip_dir, name)
        if os.path.isfile(p):
            return p
    return None


def find_clip_folders(root):
    """[(folder, label)] of every clip folder (one that holds a Summary.json) under root; label = path from the
    parent of root, with '/' (e.g. 'Site/day1/clip1')."""
    found = []
    base_parent = os.path.dirname(os.path.normpath(root))
    for dirpath, dirnames, _files in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != COMBINED_DIR)
        if summary_path(dirpath):
            found.append((dirpath, os.path.relpath(dirpath, base_parent).replace("\\", "/")))
    return found


def clip_start_time(label):
    """Recording start time from a file name such as 20260907_084751A_ -> '2026-09-07 08:47:51' ('' when the name has none).
    Times inside the CSV files are seconds from the start of the video, so Clip_Start + seconds = clock time."""
    m = re.search(r"(20\d{2})(\d{2})(\d{2})[_-]?(\d{2})(\d{2})(\d{2})", os.path.basename(label))
    if not m:
        return ""
    y, mo, d, h, mi, s = m.groups()
    if not (1 <= int(mo) <= 12 and 1 <= int(d) <= 31 and int(h) < 24 and int(mi) < 60 and int(s) < 60):
        return ""
    return f"{y}-{mo}-{d} {h}:{mi}:{s}"


def clip_max_id(folder):
    """Highest vehicle ID used in a clip folder (0 when unknown): from its run summary, else from the detection records."""
    name = os.path.basename(os.path.normpath(folder))
    try:
        with open(os.path.join(folder, f"{name}_Research_Run_Summary.json"), encoding="utf-8") as f:
            value = json.load(f).get("max_track_id")
        if isinstance(value, int):
            return value
    except (OSError, ValueError):
        pass
    best = 0
    path = os.path.join(folder, f"{name}_Detection_Records.csv")
    if os.path.isfile(path):
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    best = max(best, int(row.get("track_id", 0)))
                except (TypeError, ValueError):
                    pass
    return best


def max_track_id(out_root, top, exclude_dir=None):
    """Highest vehicle ID already used by the clips of a top folder ('' = clips straight in out_root), so that a new
    clip can continue the numbering after it. exclude_dir = the clip being (re)analysed."""
    src = os.path.join(out_root, top) if top else out_root
    if not os.path.isdir(src):
        return 0
    if top:
        clips = find_clip_folders(src)
    else:
        clips = [(os.path.join(src, d), d) for d in sorted(os.listdir(src))
                 if d != COMBINED_DIR and os.path.isdir(os.path.join(src, d)) and summary_path(os.path.join(src, d))]
    skip = os.path.normcase(os.path.abspath(exclude_dir)) if exclude_dir else None
    return max([clip_max_id(folder) for folder, _label in clips if os.path.normcase(os.path.abspath(folder)) != skip] or [0])


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def percentile(sorted_values, q):
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    pos = (n - 1) * q / 100.0
    lo = int(math.floor(pos))
    hi = min(lo + 1, n - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def stats(values):
    v = sorted(values)
    n = len(v)
    mean = sum(v) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in v) / (n - 1)) if n > 1 else None
    return {"N": n, "Mean": mean, "SD": sd, "V50_Median": percentile(v, 50), "P85": percentile(v, 85), "Min": v[0], "Max": v[-1]}


def to_float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def combine(clips, target_dir):
    """clips = [(clip folder, label)] -> writes the combined files into target_dir; returns a summary dict."""
    os.makedirs(target_dir, exist_ok=True)
    merged = {}
    for kind in KINDS:
        rows_all, fields = [], []
        for folder, label in clips:
            path = kind_file(folder, kind)
            if not path:
                continue
            rows = read_rows(path)
            if rows:
                for k in rows[0].keys():
                    if k not in fields:
                        fields.append(k)
            start = clip_start_time(label)
            for r in rows:
                row = {"Clip": label, "Clip_Start": start}
                for k, v in r.items():
                    row[k] = v
                    if k in ID_COLUMNS:
                        row[k + "_Unique"] = f"{label}#{v}" if str(v).strip() != "" else ""
                rows_all.append(row)
        if rows_all:
            merged[kind] = rows_all
            header = ["Clip", "Clip_Start"]
            for k in fields:
                header.append(k)
                if k in ID_COLUMNS:
                    header.append(k + "_Unique")
            with open(os.path.join(target_dir, f"All_{kind}.csv"), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows_all)

    with open(os.path.join(target_dir, "All_Clips.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Clip", "Clip_Start", "Folder"])
        for folder, label in clips:
            w.writerow([label, clip_start_time(label), folder])

    out_rows = []
    for kind, (indicator, column, group_cols) in STATISTICS.items():
        groups = {}
        for r in merged.get(kind, []):
            if "Speed_Above_Max" in str(r.get("QC_Flag", "")):
                continue
            v = to_float(r.get(column))
            if v is None:
                continue
            key = " | ".join(str(r.get(c, "")) for c in group_cols)
            groups.setdefault(key, []).append((r["Clip"], v))
            groups.setdefault("All", []).append((r["Clip"], v))
        for key, items in sorted(groups.items()):
            s = stats([v for _, v in items])
            out_rows.append({"Indicator": indicator, "Group": key, "Clips": len({c for c, _ in items}), **s})
    cols = ["Indicator", "Group", "Clips", "N", "Mean", "SD", "V50_Median", "P85", "Min", "Max"]
    with open(os.path.join(target_dir, "All_Statistics.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out_rows:
            w.writerow({k: ("" if r[k] is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k])) for k in cols})
    summary = {"clips": [label for _f, label in clips], "files": {k: len(v) for k, v in merged.items()}, "statistics_rows": len(out_rows)}
    with open(os.path.join(target_dir, "All_Summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary


def combine_top_folders(out_root, tops, min_clips=2, log=print):
    """For every top folder name in `tops` ('' = clips placed straight in out_root) combine all of its clips
    (every depth, old and new) into <top folder>/All_Clips/. Returns {top: summary}."""
    result = {}
    for top in sorted(set(tops)):
        src = os.path.join(out_root, top) if top else out_root
        if not os.path.isdir(src):
            continue
        if top:
            clips = find_clip_folders(src)
        else:      # clips placed directly in the output root: only its direct sub-folders
            clips = [(os.path.join(src, d), d) for d in sorted(os.listdir(src))
                     if d != COMBINED_DIR and os.path.isdir(os.path.join(src, d)) and summary_path(os.path.join(src, d))]
        if len(clips) < min_clips:
            continue
        target = os.path.join(src, COMBINED_DIR)
        result[top] = combine(clips, target)
        log("combined -> " + target)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    root = os.path.abspath(sys.argv[1])
    tops = sys.argv[2:] or sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d != COMBINED_DIR)
    print(json.dumps(combine_top_folders(root, tops), indent=2, ensure_ascii=False))
