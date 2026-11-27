"""Write the clock time each clip's video started (video_start) into the Run_Summary.json of clips analysed before
PKT-Analyze 1.61.1, so the combined files (All_Clips) get Clip_Start for GoPro clips too (Clip_Start + the seconds in
the CSV files = clock time).

    python tools/set_clip_start.py <results folder> <video folder> [--force] [--dry-run]

The video of a clip is the file named in its Settings.json when it still exists; otherwise the file in <video folder>
whose name is the clip name (e.g. GX010111.MP4), preferring one whose parent folder has the same name as the clip
folder's parent (e.g. the day 2026_09_05). The start is the time in the file name, else Date modified minus the video
length (see combine_clips.video_start_time). Clips that already have video_start are left alone unless --force.
Nothing else in the clip folder is changed; run combine (or the program's "combine results") afterwards.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import combine_clips as cc  # noqa: E402

VIDEO_EXT = (".mp4", ".mov", ".avi", ".mkv")


def index_videos(video_root):
    found = {}
    for dirpath, _dirs, files in os.walk(video_root):
        for fn in files:
            if fn.lower().endswith(VIDEO_EXT):
                found.setdefault(os.path.splitext(fn)[0].lower(), []).append(os.path.join(dirpath, fn))
    return found


def video_for(folder, videos):
    name = os.path.basename(os.path.normpath(folder))
    try:
        with open(cc.result_file(folder, "Settings.json") or "", encoding="utf-8") as f:
            path = json.load(f).get("video") or ""
        if path and os.path.isfile(path):
            return path
    except (OSError, ValueError, AttributeError):
        pass
    options = videos.get(name.lower(), [])
    parents = [p for p in os.path.normpath(folder).split(os.sep)[:-1]]
    same_day = [v for v in options if os.path.basename(os.path.dirname(v)) in parents]
    if len(same_day) == 1:
        return same_day[0]
    return options[0] if len(options) == 1 else ""


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 1
    root, video_root = args
    force, dry = "--force" in argv, "--dry-run" in argv
    videos = index_videos(video_root)
    done = missing = kept = 0
    for folder, label in cc.find_clip_folders(root):
        summary = cc.result_file(folder, "Run_Summary.json")
        if not summary:
            continue
        with open(summary, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("video_start") and not force:
            kept += 1
            continue
        video = video_for(folder, videos)
        start, how = cc.video_start_time(video) if video else ("", "")
        if not start:
            missing += 1
            print(f"{label}: video not found or no start time")
            continue
        print(f"{label}: {start} ({how})")
        if not dry:
            data["video_start"], data["video_start_method"] = start, how
            with open(summary, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        done += 1
    print(f"written {done}, already set {kept}, not found {missing}{' (dry run)' if dry else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
