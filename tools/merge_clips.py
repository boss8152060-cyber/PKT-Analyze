"""Cross-clip summary for Run 3 (plan 3.1).

Several clips = several Run 3 output folders (each holds Run_3_*.csv).  This tool puts the
per-event files of all clips together (adds a Clip column; vehicle IDs are only unique inside a
clip) and recomputes the statistics over ALL clips.

    python tools/merge_clips.py <out_dir> <clip_folder> [<clip_folder> ...]

Writes into <out_dir>:
    Merged_<name>.csv            one per Run 3 file found (Clip column first)
    Combined_Statistics.csv      Mean / SD / V50(median) / V85(P85) / Min / Max over all clips
    Combined_Summary.json        clips used + row counts

Speed values flagged Speed_Above_Max are left out of the statistics (same rule as Run 3).
Only the standard library is needed.
"""
import csv
import json
import math
import os
import sys

# file -> (indicator name, value column, group columns)
FILES = {
    "Run_3_Speed_Detail.csv": ("Speed", "Speed_kmh", ("Scope", "Key", "Vehicle_Class")),
    "Run_3_LDP.csv": ("LDP", "LDP_percent", ("Zone",)),
    "Run_3_Lateral_Clearance_Pairs.csv": ("Lateral Clearance (pair minimum)", "Lateral_Clearance_Min_m", ("Zone",)),
    "Run_3_TTC.csv": ("TTC", "TTC_s", ("TTC_Type",)),
    "Run_3_PET.csv": ("PET", "PET_s", ("Conflict_Type", "Conflict_Zone")),
    "Run_3_Gap_Acceptance.csv": ("Gap Acceptance (available gap)", "X31_Available_Gap", ("Decision_Stage", "Gap_Role")),
}
# files merged without statistics
EXTRA_FILES = ("Run_3_Lateral_Clearance.csv", "Run_3_Speed.csv", "Run_3_Critical_Gap.csv", "Run_3_Duplicate_Tracks.csv")


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def percentile(sorted_values, q):
    """Linear interpolation between closest ranks (same as numpy.percentile)."""
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
    return {"N": n, "Mean": mean, "SD": sd, "V50_Median": percentile(v, 50), "P85": percentile(v, 85),
            "Min": v[0], "Max": v[-1]}


def to_float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def merge(out_dir, clip_dirs, labels=None):
    """labels = optional clip names (e.g. 'day/video') for the Clip column; default = folder names."""
    os.makedirs(out_dir, exist_ok=True)
    clip_names = []
    for i, d in enumerate(clip_dirs):
        name = labels[i] if labels else (os.path.basename(os.path.normpath(d)) or d)
        while name in clip_names:
            name += "_"
        clip_names.append(name)

    merged = {}
    for fname in list(FILES) + list(EXTRA_FILES):
        rows_all, fields = [], []
        for d, clip in zip(clip_dirs, clip_names):
            path = os.path.join(d, fname)
            if not os.path.isfile(path):
                continue
            rows = read_rows(path)
            if rows:
                fields = fields or list(rows[0].keys())
            for r in rows:
                r2 = {"Clip": clip}
                r2.update(r)
                rows_all.append(r2)
        if not rows_all:
            continue
        merged[fname] = rows_all
        out_name = "Merged_" + fname.replace("Run_3_", "")
        with open(os.path.join(out_dir, out_name), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["Clip"] + fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows_all)

    out_rows = []
    for fname, (indicator, column, group_cols) in FILES.items():
        rows = merged.get(fname, [])
        groups = {}
        for r in rows:
            if "Speed_Above_Max" in str(r.get("QC_Flag", "")):
                continue
            v = to_float(r.get(column))
            if v is None:
                continue
            key = " | ".join(str(r.get(c, "")) for c in group_cols)
            groups.setdefault(("All", key), []).append((r["Clip"], v))
            groups.setdefault(("All", "All"), []).append((r["Clip"], v))
        for (_, key), items in sorted(groups.items()):
            s = stats([v for _, v in items])
            out_rows.append({
                "Indicator": indicator, "Group": key, "Clips": len({c for c, _ in items}),
                "N": s["N"], "Mean": s["Mean"], "SD": s["SD"], "V50_Median": s["V50_Median"],
                "P85": s["P85"], "Min": s["Min"], "Max": s["Max"],
            })
    cols = ["Indicator", "Group", "Clips", "N", "Mean", "SD", "V50_Median", "P85", "Min", "Max"]
    with open(os.path.join(out_dir, "Combined_Statistics.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out_rows:
            w.writerow({k: ("" if r[k] is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k])) for k in cols})
    summary = {"clips": dict(zip(clip_names, clip_dirs)),
               "merged_rows": {k: len(v) for k, v in merged.items()},
               "statistics_rows": len(out_rows)}
    with open(os.path.join(out_dir, "Combined_Summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary, out_rows


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    s, _ = merge(sys.argv[1], sys.argv[2:])
    print(json.dumps(s, indent=2, ensure_ascii=False))
