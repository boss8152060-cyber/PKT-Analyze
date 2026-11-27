"""Combined CSV files over many clips.

Every clip has its own folder with its own CSV files (Gap_Acceptance.csv, Speed.csv, ...; results of older versions
were named <clip>_Speed.csv or Run_3_Speed.csv and are still found).
This module puts the same kind of file from all clips together into one CSV per kind, in the same layout as a clip
folder (1_ID_Zone.csv ... 8_PET.csv, 0_Raw/, 9_Summary/ - see LAYOUT), with the first column `Clip` saying which clip a
row comes from (vehicle IDs are only unique inside a clip, so always read an ID together with Clip), plus
9_Summary/Clip_List.csv (a table of the clips: frames, length, vehicles, rows of each indicator) and
9_Summary/Statistics.csv (Mean, SD, V50, V85 ... over all clips).  It is rebuilt from the clip folders that exist, so
adding clips later only means running it again.
This is done for every folder level that holds 2 or more clips: e.g. Site/All_Clips (every day) and
Site/<day>/All_Clips (the clips of that day); a level whose clips are exactly those of the level above is skipped
(it would be a copy).

The batch calls combine_top_folders() after every run; it can also be used on its own:
    python tools/combine_clips.py <output root> [<top folder name> ...]
Only the standard library is needed.
"""
import csv
import json
import math
import os
import re
import struct
import sys
import time

COMBINED_DIR = "All_Clips"

# Vehicle IDs (and event / pair numbers) restart from 1 in every clip, so in the combined files each of these columns
# gets a companion <column>_Unique = "<Clip>#<value>" that is unique over all clips.
ID_COLUMNS = ("track_id", "Vehicle_ID", "Vehicle_ID_A", "Vehicle_ID_B", "Vehicle_A_ID", "Vehicle_B_ID", "Subject_ID",
              "Conflicting_ID_A", "Conflicting_ID_B", "Lead_Vehicle_ID", "Lag_Vehicle_ID", "Duplicate_ID", "Kept_ID", "Pair_ID", "Interaction_ID",
              "Event_ID", "Decision_Event_ID")

# kinds of CSV that are put together (the file of a clip is <clip>_<kind>.csv; older runs: Run_3_<kind>.csv)
KINDS = ("ID_Zone_Summary", "Speed_Zone", "LDP", "Lateral_Clearance_Pairs", "Gap_Acceptance", "Critical_Gap", "Headway", "TTC", "PET",
         "Speed", "Speed_Detail", "Lateral_Clearance", "TTC_Detail", "Duplicate_Tracks",   # Speed = the speed of every frame; Speed_Detail only exists in older results (merged, no statistics)
         "Indicator_Summary", "Zone_Summary")                                  # the summary of each clip, one under the other

# kinds counted per clip in the clip table (column Rows_<kind>)
COUNTED_KINDS = ("Speed_Zone", "LDP", "Lateral_Clearance_Pairs", "Gap_Acceptance", "Headway", "TTC", "PET")

# Layout of a clip folder (since 1.50.0). The analysis writes plain names (LDP.csv ...) and arrange_clip_folder() then
# moves them here: the analysis results numbered in the order of the work, the raw / checking data in 0_Raw, the
# summaries and settings in 9_Summary; videos and pictures stay in the clip folder. All_Clips uses the same layout.
RAW_DIR = "0_Raw"
SUMMARY_DIR = "9_Summary"
LAYOUT = {
    "ID_Zone_Summary.csv": "1_ID_Zone.csv",
    "Speed_Zone.csv": "2_Speed.csv",                     # mean speed of every vehicle in every zone it passed
    "LDP.csv": "3_LDP.csv",
    "Lateral_Clearance_Pairs.csv": "4_Lateral_Clearance.csv",
    "Gap_Acceptance.csv": "5_Gap_Acceptance.csv",
    "Critical_Gap.csv": "5_Critical_Gap.csv",
    "Headway.csv": "6_Headway.csv",
    "TTC.csv": "7_TTC.csv",
    "PET.csv": "8_PET.csv",
    "Detection_Records.csv": RAW_DIR + "/Detection_Records.csv",
    "Detection_Records_Topview.csv": RAW_DIR + "/Detection_Records_Topview.csv",
    "Speed.csv": RAW_DIR + "/Speed_Frames.csv",          # the speed of every frame
    "Speed_Detail.csv": RAW_DIR + "/Speed_Detail.csv",
    "Lateral_Clearance.csv": RAW_DIR + "/Lateral_Clearance_Samples.csv",
    "TTC_Detail.csv": RAW_DIR + "/TTC_Detail.csv",
    "TTC_Frames.csv": RAW_DIR + "/TTC_Frames.csv",
    "Duplicate_Tracks.csv": RAW_DIR + "/Duplicate_Tracks.csv",
    "Indicator_Summary.csv": SUMMARY_DIR + "/Indicator_Summary.csv",
    "Zone_Summary.csv": SUMMARY_DIR + "/Zone_Summary.csv",
    "Summary.json": SUMMARY_DIR + "/Summary.json",
    "Run_Summary.json": SUMMARY_DIR + "/Run_Summary.json",
    "Settings.json": SUMMARY_DIR + "/Settings.json",
    "Measurement_Summary.json": SUMMARY_DIR + "/Measurement_Summary.json",
    "ByteTrack.yaml": SUMMARY_DIR + "/ByteTrack.yaml",
}
LAYOUT_DIRS = (RAW_DIR, SUMMARY_DIR)
# files of the combined folder (besides the LAYOUT names of the kinds)
CLIP_LIST = SUMMARY_DIR + "/Clip_List.csv"
STATISTICS_FILE = SUMMARY_DIR + "/Statistics.csv"
COMBINED_SUMMARY = SUMMARY_DIR + "/Combined_Summary.json"

# kind -> (indicator name, value column, group columns) for the combined statistics
STATISTICS = {
    "Speed_Zone": ("Speed (mean per vehicle in zone)", "Mean_Speed_kmh", ("Zone",)),
    "LDP": ("LDP", "LDP_percent", ("Zone",)),
    "Lateral_Clearance_Pairs": ("Lateral Clearance (pair minimum)", "Lateral_Clearance_Min_m", ("Zone",)),
    "TTC": ("TTC", "TTC_s", ("TTC_Type",)),
    "PET": ("PET", "PET_s", ("Conflict_Type", "Conflict_Zone")),
    "Gap_Acceptance": ("Gap Acceptance (available gap)", "Available_Gap_s", ("Decision_Stage", "Gap_Role")),
    "Headway": ("Headway (time headway)", "Time_Headway_s", ("Movement",)),
}


# column renamed in v28(129) -> its name in older results (so All_Statistics still reads them)
OLD_COLUMN_NAMES = {"Available_Gap_s": "X31_Available_Gap"}


def result_file(folder, new_name, clip_name=None):
    """Path of a result file inside a clip folder, or None. New results have plain names (Speed.csv, Summary.json,
    Tracking_Result.mp4 ...); results of older versions are found too (<clip>_Speed.csv, <clip>_Research_Settings.json,
    Run_3_Speed.csv ...) and so are the arranged results (3_LDP.csv, 0_Raw/Speed_Frames.csv, 9_Summary/Summary.json)."""
    clip_name = clip_name or os.path.basename(os.path.normpath(folder))
    names = [new_name]
    if new_name in LAYOUT:
        names.append(LAYOUT[new_name])
    names += [f"{clip_name}_{new_name}", f"{clip_name}_Research_{new_name}", f"Run_3_{new_name}", f"Run_1_Research_{new_name}"]
    for name in names:
        p = os.path.join(folder, *name.split("/"))
        if os.path.isfile(p):
            return p
    return None


def _same_path(a, b):
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def _swap_paths(value, moved):
    """`value` (from a JSON file) with every path of a moved file replaced by its new path."""
    if isinstance(value, dict):
        return {k: _swap_paths(v, moved) for k, v in value.items()}
    if isinstance(value, list):
        return [_swap_paths(v, moved) for v in value]
    if isinstance(value, str) and len(value) > 3 and ("/" in value or "\\" in value):
        for old, new in moved:
            if _same_path(value, old):
                return new
    return value


def arrange_clip_folder(folder):
    """Moves the plain-named results of a clip folder into LAYOUT (an older arranged copy is replaced) and puts the new
    paths into its JSON files. Returns {old path: new path}. Files that are not in LAYOUT (videos, pictures) stay.
    Results of older versions named <clip>_LDP.csv / Run_3_LDP.csv ... are moved the same way (a plain name wins)."""
    moved = []
    clip = os.path.basename(os.path.normpath(folder))
    for plain, rel in LAYOUT.items():
        src = next((p for p in (os.path.join(folder, n) for n in (plain, f"{clip}_{plain}", f"{clip}_Research_{plain}",
                                                                   f"Run_3_{plain}", f"Run_1_Research_{plain}"))
                    if os.path.isfile(p)), None)
        if src is None:
            continue
        dst = os.path.join(folder, *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.replace(src, dst)
        moved.append((src, dst))
    if moved:
        for rel in (LAYOUT["Summary.json"], LAYOUT["Run_Summary.json"]):
            path = os.path.join(folder, *rel.split("/"))
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(_swap_paths(data, moved), f, indent=4, ensure_ascii=False)
            except (OSError, ValueError):
                pass
    return dict(moved)


def summary_path(clip_dir, clip_name=None):
    """The Summary.json of a clip folder (None when the clip has not been analysed)."""
    return result_file(clip_dir, "Summary.json", clip_name)


def kind_file(clip_dir, kind, clip_name=None):
    return result_file(clip_dir, f"{kind}.csv", clip_name)


def find_clip_folders(root):
    """[(folder, label)] of every clip folder (one that holds a Summary.json) under root; label = path from the
    parent of root, with '/' (e.g. 'Site/day1/clip1')."""
    found = []
    base_parent = os.path.dirname(os.path.normpath(root))
    for dirpath, dirnames, _files in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != COMBINED_DIR and d not in LAYOUT_DIRS)
        if summary_path(dirpath):
            label = os.path.relpath(dirpath, base_parent).replace("\\", "/").split("/")
            found.append((dirpath, "/".join(x for x in label[:-1] if x != "Clips") + ("/" if len(label) > 1 else "") + label[-1]))
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


def mp4_length_s(path):
    """Length in seconds from the movie header (moov/mvhd) of an MP4/MOV file; None when it cannot be read."""
    try:
        with open(path, "rb") as f:
            end = os.fstat(f.fileno()).st_size

            def atoms(start, stop):
                pos = start
                while pos + 8 <= stop:
                    f.seek(pos)
                    head = f.read(16)
                    if len(head) < 8:
                        return
                    size, kind = struct.unpack(">I4s", head[:8])
                    hdr = 8
                    if size == 1 and len(head) == 16:
                        size, hdr = struct.unpack(">Q", head[8:16])[0], 16
                    elif size == 0:
                        size = stop - pos
                    if size < hdr:
                        return
                    yield kind, pos + hdr, pos + size
                    pos += size

            for kind, body, stop in atoms(0, end):
                if kind != b"moov":
                    continue
                for k2, b2, _s2 in atoms(body, stop):
                    if k2 == b"mvhd":
                        f.seek(b2)
                        if f.read(4)[0] == 1:
                            _c, _m, scale, dur = struct.unpack(">QQIQ", f.read(28))
                        else:
                            _c, _m, scale, dur = struct.unpack(">IIII", f.read(16))
                        return dur / scale if scale else None
    except (OSError, struct.error, IndexError):
        pass
    return None


def video_start_time(video_path):
    """(clock time the recording of a video started, how it was found): from the file name when it holds a time
    (CCTV style 20260907_084751A), else the file's "Date modified" minus the video length - the camera closes the file
    when that part of the recording ends (GoPro chapters GX01.., GX02.. each get their own). ('', '') when unknown.
    Checked on 737 videos of the PSU 2026 survey: both ways agree within 3 s."""
    start = clip_start_time(video_path or "")
    if start:
        return start, "file name"
    if not video_path or not os.path.isfile(video_path):
        return "", ""
    length = mp4_length_s(video_path)
    if not length:
        return "", ""
    t = os.path.getmtime(video_path) - length
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(round(t))), "modified - length"


def clip_start(folder, label):
    """Clock time a clip starts: from its name, else the video_start written in its Run_Summary.json ('' = unknown)."""
    start = clip_start_time(label)
    if start:
        return start
    try:
        with open(result_file(folder, "Run_Summary.json") or "", encoding="utf-8") as f:
            value = json.load(f).get("video_start")
        return value if isinstance(value, str) else ""
    except (OSError, ValueError, AttributeError):
        return ""


def clip_max_id(folder):
    """Highest vehicle ID used in a clip folder (0 when unknown): from its run summary, else from the detection records."""
    try:
        with open(result_file(folder, "Run_Summary.json") or "", encoding="utf-8") as f:
            value = json.load(f).get("max_track_id")
        if isinstance(value, int):
            return value
    except (OSError, ValueError):
        pass
    best = 0
    path = result_file(folder, "Detection_Records.csv")
    if path:
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
    for name in os.listdir(target_dir):                   # files of the layout before 1.50.0 (All_LDP.csv ...)
        if (name.startswith("All_") and name.endswith(".csv")) or name == "All_Summary.json":
            try:
                os.remove(os.path.join(target_dir, name))
            except OSError:
                pass
    for d in LAYOUT_DIRS:
        os.makedirs(os.path.join(target_dir, d), exist_ok=True)

    def out_path(rel):
        return os.path.join(target_dir, *rel.split("/"))

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
            start = clip_start(folder, label)
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
            with open(out_path(LAYOUT.get(kind + ".csv", RAW_DIR + "/" + kind + ".csv")), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows_all)

    counts = {}                                          # (label, kind) -> rows of that clip
    for kind in COUNTED_KINDS:
        for r in merged.get(kind, []):
            counts[(r["Clip"], kind)] = counts.get((r["Clip"], kind), 0) + 1
    with open(out_path(CLIP_LIST), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Clip", "Clip_Start", "Status", "Frames", "Duration_s", "Unique_Track_IDs"]
                   + [f"Rows_{k}" for k in COUNTED_KINDS] + ["Folder"])
        for folder, label in clips:
            info = clip_info(folder)
            w.writerow([label, clip_start(folder, label), info["status"], info["frames"], info["duration"], info["vehicles"]]
                       + [counts.get((label, k), 0) for k in COUNTED_KINDS] + [folder])

    out_rows = []
    for kind, (indicator, column, group_cols) in STATISTICS.items():
        groups = {}
        for r in merged.get(kind, []):
            if "Speed_Above_Max" in str(r.get("QC_Flag", "")):
                continue
            v = to_float(r.get(column, r.get(OLD_COLUMN_NAMES.get(column, ""))))     # results of older versions use the old column name
            if v is None:
                continue
            key = " | ".join(str(r.get(c, "")) for c in group_cols)
            groups.setdefault(key, []).append((r["Clip"], v))
            groups.setdefault("All", []).append((r["Clip"], v))
        for key, items in sorted(groups.items()):
            s = stats([v for _, v in items])
            out_rows.append({"Indicator": indicator, "Group": key, "Clips": len({c for c, _ in items}), **s})
    cols = ["Indicator", "Group", "Clips", "N", "Mean", "SD", "V50_Median", "P85", "Min", "Max"]
    with open(out_path(STATISTICS_FILE), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out_rows:
            w.writerow({k: ("" if r[k] is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k])) for k in cols})
    summary = {"clips": [label for _f, label in clips], "files": {k: len(v) for k, v in merged.items()}, "statistics_rows": len(out_rows)}
    with open(out_path(COMBINED_SUMMARY), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary


def clip_info(folder):
    """{status, frames, duration (s), vehicles} of a clip folder from its Run_Summary.json / Settings.json ('' = unknown)."""
    info = {"status": "", "frames": "", "duration": "", "vehicles": ""}
    try:
        with open(result_file(folder, "Run_Summary.json") or "", encoding="utf-8") as f:
            rs = json.load(f)
    except (OSError, ValueError):
        return info
    info["status"] = rs.get("status", "")
    frames = rs.get("processed_frames", rs.get("total_frames"))
    info["frames"] = frames if isinstance(frames, int) else ""
    info["vehicles"] = rs.get("unique_track_ids", "")
    try:
        with open(result_file(folder, "Settings.json") or "", encoding="utf-8") as f:
            fps = to_float(json.load(f).get("video_fps"))
        if fps and isinstance(frames, int):
            info["duration"] = f"{frames / fps:.1f}"
    except (OSError, ValueError, AttributeError):
        pass
    return info


def _sub_levels(src, clips, min_clips):
    """[(folder, clips relabelled from the parent of that folder)] for every folder below src that holds min_clips or
    more clips, unless they are exactly the clips of the folder above it (that one already has them all)."""
    src = os.path.normpath(src)
    under = {}                                            # folder -> [clip folder] (every depth, walk order)
    for folder, _label in clips:
        d = os.path.dirname(os.path.normpath(folder))
        while len(d) > len(src) and d.startswith(src):
            under.setdefault(d, []).append(folder)
            d = os.path.dirname(d)
    clip_dirs = {os.path.normpath(f) for f, _ in clips}
    out = []
    for d in sorted(under):
        members = under[d]
        if d in clip_dirs or len(members) < min_clips:
            continue
        parent = os.path.dirname(d)
        if len(under.get(parent, [f for f, _ in clips] if parent == src else [])) == len(members):
            continue                                      # same clips as the folder above -> its All_Clips is the same
        base = os.path.dirname(d)
        out.append((d, [(f, os.path.relpath(f, base).replace("\\", "/")) for f in members]))
    return out


def combine_top_folders(out_root, tops, min_clips=2, log=print):
    """For every top folder name in `tops` ('' = clips placed straight in out_root) combine all of its clips
    (every depth, old and new) into <top folder>/All_Clips/, and the clips of every folder below it that holds 2 or
    more of them (e.g. one day) into <that folder>/All_Clips/. Returns {top or 'top/sub/folder': summary}."""
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
        if top:
            for folder, sub_clips in _sub_levels(src, clips, min_clips):
                target = os.path.join(folder, COMBINED_DIR)
                key = os.path.relpath(folder, out_root).replace("\\", "/")
                result[key] = combine(sub_clips, target)
                log("combined -> " + target)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    root = os.path.abspath(sys.argv[1])
    tops = sys.argv[2:] or sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d != COMBINED_DIR)
    print(json.dumps(combine_top_folders(root, tops), indent=2, ensure_ascii=False))
