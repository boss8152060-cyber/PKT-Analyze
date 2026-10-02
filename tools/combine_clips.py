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
import sys

COMBINED_DIR = "All_Clips"

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
            for r in rows:
                row = {"Clip": label}
                row.update(r)
                rows_all.append(row)
        if rows_all:
            merged[kind] = rows_all
            with open(os.path.join(target_dir, f"All_{kind}.csv"), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=["Clip"] + fields, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows_all)

    with open(os.path.join(target_dir, "All_Clips.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Clip", "Folder"])
        for folder, label in clips:
            w.writerow([label, folder])

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
