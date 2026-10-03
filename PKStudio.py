# ============================================================
# PK Studio V17 - Run 1 + 2 + 3 V28
# V28: 6 safety indicators in 3 domains (definitions: SPEC_v28_NewIndicators.md)
#   Distance: LDP, Lateral Clearance
#   Time    : Gap Acceptance, TTC (rear-end + side), PET
#   Speed   : Speed (per zone and per Movement; V50, V85, Mean, SD)
#   Zones 1-7; conflict zones 3 and 6. Movement = full zone sequence (6 patterns).
#   No Tk access from worker thread.
# ============================================================
#
# Vehicle Detection + Tracking + Trajectory + Zone/Line Measurement Research
# Movement (Run 3) comes from the flicker-cleaned zone sequence of each track
# (classify_movement); it is never guessed when the sequence is ambiguous.
# GUI Version 3 - CUDA Auto Environment
#
# IMPORTANT:
# This version checks the Python environment BEFORE importing
# PyTorch / Ultralytics.
#
# If the current Python has torch +cpu, the program searches
# other installed Python environments and automatically relaunches
# this same file with the first environment where:
#
#   torch.cuda.is_available() == True
#
# This prevents the common situation where:
#   Terminal  -> PyTorch CUDA = True
#   GUI       -> PyTorch +cpu
#
# ============================================================

import os
import sys
import csv
import json
import importlib.util
import time
import threading
import queue
import logging
import subprocess
import shutil
import math
import re
import base64
import numpy as np
from collections import deque, defaultdict


# ============================================================
# CUDA PYTHON BOOTSTRAP
# ============================================================

BOOTSTRAP_MARKER = "PK_STUDIO_CUDA_RELAUNCHED"


def _python_has_cuda(python_exe):
    """Check whether a Python executable has a CUDA-enabled PyTorch."""
    try:
        result = subprocess.run(
            [
                python_exe,
                "-c",
                (
                    "import torch; "
                    "print('1' if torch.cuda.is_available() else '0')"
                )
            ],
            capture_output=True,
            text=True,
            timeout=90
        )

        return result.returncode == 0 and result.stdout.strip() == "1"

    except Exception:
        return False


def _get_python_candidates():
    """Build a list of possible Python executables on Windows."""

    candidates = []

    def add(path):
        if not path:
            return

        path = os.path.abspath(path)

        if not os.path.isfile(path):
            return

        normalized = os.path.normcase(path)

        for existing in candidates:
            if os.path.normcase(existing) == normalized:
                return

        candidates.append(path)

    # Current Python first.
    add(sys.executable)

    # Python Launcher for Windows.
    py_launcher = shutil.which("py")

    if py_launcher:
        try:
            result = subprocess.run(
                [py_launcher, "-0p"],
                capture_output=True,
                text=True,
                timeout=10
            )

            for line in result.stdout.splitlines():
                line = line.strip()

                if not line:
                    continue

                # Typical output:
                # -V:3.14 * C:\...\python.exe
                # -V:3.13 C:\...\python.exe
                # -V:3.12 C:\...\python.exe
                if " " in line:
                    possible = line.split()[-1]

                    if os.path.isfile(possible):
                        add(possible)

        except Exception:
            pass

    # PATH Python.
    add(shutil.which("python"))
    add(shutil.which("python3"))

    # Common Windows installation locations.
    local_app = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "")

    roots = [
        os.path.join(local_app, "Programs", "Python"),
        os.path.join(program_files, "Python"),
        os.path.join(program_files_x86, "Python"),
        r"C:\Python",
    ]

    for root in roots:

        if not os.path.isdir(root):
            continue

        try:
            for name in os.listdir(root):

                folder = os.path.join(root, name)

                if not os.path.isdir(folder):
                    continue

                python_exe = os.path.join(
                    folder,
                    "python.exe"
                )

                add(python_exe)

        except Exception:
            pass

    # Explicit common Python versions.
    for version in [
        "Python314",
        "Python313",
        "Python312",
        "Python311",
        "Python310",
        "Python39",
    ]:

        add(
            os.path.join(
                local_app,
                "Programs",
                "Python",
                version,
                "python.exe"
            )
        )

    return candidates


def find_cuda_python(exclude=None):
    """Path of another installed Python whose PyTorch can use CUDA, or None."""
    skip = os.path.normcase(os.path.abspath(exclude or sys.executable))
    for python_exe in _get_python_candidates():
        if os.path.normcase(os.path.abspath(python_exe)) == skip:
            continue
        if _python_has_cuda(python_exe):
            return python_exe
    return None


def _bootstrap_cuda_environment():
    """
    If this Python has CPU-only PyTorch, automatically find another
    installed Python with CUDA PyTorch and relaunch this script.
    """

    if os.environ.get(BOOTSTRAP_MARKER) == "1":
        return

    # Do not import torch here until after we know which Python
    # environment is being used.
    try:
        check = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import torch; "
                    "print(torch.__version__); "
                    "print('CUDA=' + str(torch.cuda.is_available()))"
                )
            ],
            capture_output=True,
            text=True,
            timeout=90
        )

        output = (
            (check.stdout or "")
            + "\n"
            + (check.stderr or "")
        )

    except Exception:
        output = ""

    # If current Python already has CUDA, stay here.
    if "CUDA=True" in output:
        return

    # Current environment does not have usable CUDA.
    candidates = _get_python_candidates()

    # Remove current Python from the search list after checking it.
    current = os.path.normcase(
        os.path.abspath(sys.executable)
    )

    for python_exe in candidates:

        if os.path.normcase(
            os.path.abspath(python_exe)
        ) == current:
            continue

        if not _python_has_cuda(python_exe):
            continue

        # Found CUDA-enabled Python.
        script_path = os.path.abspath(
            sys.argv[0]
        )

        env = os.environ.copy()
        env[BOOTSTRAP_MARKER] = "1"

        print()
        print("=" * 75)
        print("PK Studio - CUDA Environment Auto Switch")
        print("=" * 75)
        print("Current Python:")
        print(sys.executable)
        print()
        print("Current environment does not provide CUDA.")
        print()
        print("CUDA Python found:")
        print(python_exe)
        print()
        print("Relaunching Run 1 with CUDA Python...")
        print("=" * 75)
        print()

        completed = subprocess.run(
            [
                python_exe,
                script_path,
                *sys.argv[1:]
            ],
            env=env
        )

        raise SystemExit(
            completed.returncode
        )


# Run BEFORE importing torch / ultralytics.
_bootstrap_cuda_environment()


# ============================================================
# NORMAL IMPORTS
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import cv2
import torch
from ultralytics import YOLO


# ============================================================
# DEFAULT PATHS
# ============================================================

class _NullCSVWriter:
    """No-op writer used for legacy research outputs that are no longer exported."""
    def writerow(self, *args, **kwargs):
        pass

    def flush(self):
        pass

    def close(self):
        pass


# Default paths are relative to this file: <PK STUDIO>\Run\PKStudio.py -> <PK STUDIO>\Input, \Output
_PK_STUDIO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _first_video(folder):
    try:
        for name in sorted(os.listdir(folder)):
            if name.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                return os.path.join(folder, name)
    except OSError:
        pass
    return os.path.join(folder, "video.mp4")


DEFAULT_MODEL = os.path.join(_PK_STUDIO_DIR, "Input", "Model", "best.pt")
DEFAULT_VIDEO = _first_video(os.path.join(_PK_STUDIO_DIR, "Input", "Video"))
DEFAULT_OUTPUT = os.path.join(_PK_STUDIO_DIR, "Output")

log = logging.getLogger("pkstudio")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_SETTINGS = {
    "run_name": "Run_1",
    "model": DEFAULT_MODEL,
    "video": DEFAULT_VIDEO,
    "output": DEFAULT_OUTPUT,

    "confidence": "0.25",
    "iou": "0.50",
    "img_size": "640",
    "analysis_start_s": "",             # analyse only from this time (blank = from the start); m:ss or seconds
    "analysis_end_s": "",               # ... to this time (blank = to the end)
    "record_start_s": "",               # Save Video: record only from this time (blank = start of the analysis window)
    "record_end_s": "",

    "tracker": "ByteTrack",

    "device": "Auto",
    "precision": "Auto",

    "frame_skip": "NO - Process every frame",

    "track_high": "0.25",
    "track_low": "0.10",
    "new_track": "0.25",
    "track_buffer": "30",
    "match_threshold": "0.80",

    "show_preview": True,
    "draw_center": False,  # draw the point that decides the zone (Trajectory Position) on the preview / result video
    "draw_trail": False,
    "trail_length": "30",

    "save_video": True,
    "save_csv": True,
    "csv_flush": "100",

    "research_mode": True,

    # Trajectory Position: choose where the tracked trajectory is anchored
    # inside each bounding box. Offset moves the anchor inward from the selected edge(s).
    "trajectory_position": "Center",
    "trajectory_offset": "0",

    # Zone overlay display controls.
    "show_zone_boundary": True,
    "show_zone_label": True,
    "show_zone_label_prefix": True,
    "zone_overlay_opacity": "45",

    # Individual vehicle label controls.
    "show_label_id": True,
    "show_label_class": True,
    "show_label_conf": True,
    "show_label_zone": True,
    "show_label_speed": True,
    "show_bbox": True,
    "show_prefix_id": False,
    "show_prefix_class": False,
    "show_prefix_conf": False,
    "show_prefix_zone": False,
    "show_prefix_speed": False,
}


# ============================================================
# RUN 3 DEFAULTS
# ============================================================

RUN3_VEHICLE_CLASSES = [
    "Bus", "Car", "Motorcycle", "Pickup", "Sidecar", "Truck", "Van"
]

RUN3_GEOMETRY_KEYS = ("lane_entry_motorcycle_m", "lane_entry_car_m",
                      "lane_opp_motorcycle_m", "lane_opp_car_m", "median_m")

RUN3_DEFAULTS = {
    # Starter preset based on the values currently entered in the researcher UI.
    # NOTE: values marked as implementation defaults are editable and are NOT
    # source-derived research constants.
    "site_id": "8",
    "speed_enabled": True,
    "gap_enabled": True,
    "lc_enabled": True,
    "pet_enabled": True,
    "ttc_enabled": True,
    "ldp_enabled": True,
    "ppm": "57.822",
    # Optional road-plane perspective calibration. Disabled by default because
    # image points and real dimensions are site/video-specific and were not
    # supplied in the research documents.
    "perspective_enabled": False,
    "perspective_p1": "",
    "perspective_p2": "",
    "perspective_p3": "",
    "perspective_p4": "",
    "perspective_length_m": "",
    "perspective_width_m": "",
    "perspective_l12_m": "",
    "perspective_l23_m": "",
    "perspective_l34_m": "",
    "perspective_l41_m": "",
    "waiting_speed_threshold": "5.00",      # Gap Acceptance: "stopped" inside the conflict zones = speed <= this (km/h)
    "gap_hold_min_duration_s": "0.30",      # ... for at least this long (s)
    "lateral_axis_angle_deg": "0.00",       # implementation starter value; verify per video
    "lc_heading_window_s": "0.50",          # centred window (s) used to get the heading of vehicle A
    "lens_f": "",                           # lens (radial) distortion correction: f (x picture width, blank = 1), k1, k2; blank = none
    "lens_k1": "",
    "lens_k2": "",
    "topview_map": False,                   # Topview as a map: empty grid + the road lines clicked on the camera picture (no camera photo)
    "road_lines": "",                       # JSON: road lines clicked on the camera picture (pixels as recorded)
    "topview_video": True,                  # also write Tracking_Topview.mp4 (road-plane picture drawn from the metric points)
    "lc_along_limit_m": "0",                # side-by-side window along the heading (m); 0 = auto (L_A + L_B) / 2
    "lc_max_lateral_m": "3.50",             # pairs further apart sideways than this (m) are unrelated; 0 = no limit
    "pet_interaction_distance_m": "3.00",   # implementation starter value
    "pet_threshold_s": "1.00",
    # V27 implementation starter values (editable; verify per site):
    "pet_max_s": "10.0",                    # pairs/events above this are not PET conflicts; blank = no limit
    "ttc_max_record_s": "3.0",              # record TTC events with TTCmin <= this value
    "ttc_heading_max_deg": "45",            # same-direction test for rear-end / deviation
    "ttc_velocity_window_s": "0.50",        # centred window of observed samples for velocity
    "ttc_min_speed_kmh": "2.0",             # follower must be moving
    # Side (crossing / merging) collision - adjustable because the rule is not settled yet:
    "ttc_side_enabled": True,
    "ttc_side_window_factor": "1.0",        # x (L_i/v_i + L_j/v_j)/2  (0 = ignore vehicle length)
    "ttc_side_margin_s": "0.0",             # seconds added to the arrival-time window
    "ttc_side_min_angle_deg": "10",         # paths closer to parallel than this are not a side conflict
    "ttc_side_mode": "Earlier arrival",     # Earlier arrival | Later arrival | Average of arrivals
    # V28: road geometry (m). Blank = not entered (never guessed).
    # W_entry = entry motorcycle lane + entry car lane (side with the side street: Zones 2-3-4)
    # W_opp   = opposite motorcycle lane + opposite car lane (Zones 5-6-7)
    "lane_entry_motorcycle_m": "",
    "lane_entry_car_m": "",
    "lane_opp_motorcycle_m": "",
    "lane_opp_car_m": "",
    "median_m": "",                         # recorded only; not used in any indicator
    "ldp_smoothing_samples": "5",           # rolling median to suppress bbox jitter (1 = off)
    # Speed: user can select any of Zones 1–6. CSV assigns each selected zone
    # to the research role: Zone 1 = access mouth, 2/4 = approach, 3/5 = exit, 6 = middle/access.
    "speed_zones": [1, 2, 3, 4, 5, 6, 7],
    "speed_smoothing_samples": "5",         # rolling-median window on positions before Speed (1 = off)
    "speed_max_kmh": "80",                  # Speed above this is flagged Speed_Above_Max and left out of the statistics (0 = off)
    "lc_zones": [2, 3, 4, 5, 6, 7],
    "lc_motorcycle_pairs_only": False,      # False = every pair of vehicles; True = only pairs that include a motorcycle
    "pet_zone6": True,
    "pet_zones": [3, 6],
    "ttc_zones": [3, 6],
    "ldp_zones": [2, 3, 4, 5, 6, 7],
    "gap_subject_134": True,
    "gap_subject_1367": True,
    "gap_subject_5631": True,
    "use_raff": True,
    "use_mle": True,
    # Reference Line Mapping (Site_ID|Movement|Line N): ready-made for Site 8 - the four conflicting
    # streams of Gap Acceptance use Line 1-4. The Lines themselves still have to be drawn
    # (button "วาด Line…" next to the Zone File); the editor keeps this mapping in sync.
    # Lines beginning with # are ignored by the program.
    "reference_line_mapping": "# Site_ID|Movement|Line N\n8|2-3-4|Line 1\n8|5-6-7|Line 2\n8|5-6-3-1|Line 3\n8|1-3-6-7|Line 4",
    # Starter width values entered in the current researcher UI.
    "vehicle_widths": {
        "Bus": "2.50",
        "Car": "1.80",
        "Motorcycle": "0.80",
        "Pickup": "1.85",
        "Sidecar": "1.30",
        "Truck": "2.50",
        "Van": "1.90",
    },
    # V27: vehicle lengths for the TTC clear gap S. Implementation starter
    # values — replace with the values adopted in Chapter 3.
    "vehicle_lengths": {
        "Bus": "12.00",
        "Car": "4.50",
        "Motorcycle": "2.00",
        "Pickup": "5.30",
        "Sidecar": "2.20",
        "Truck": "8.00",
        "Van": "5.00",
    },
}


# ============================================================
# APPLICATION
# ============================================================

ZONE_IDS = list(range(1, 8))
CONFLICT_ZONE_IDS = (3, 6)              # V28: conflict zones (PET / TTC); ordinary path zones for Movement
ZONE_NAMES = [f"Zone {i}" for i in ZONE_IDS]

# ==== CORE-BEGIN (pure logic, no GUI: unit-tested by tests/test_core.py) ====
import math
import re
import numpy as np

# V27(2): zone visits shorter/closer than this are treated as boundary flicker
# when the Run 2 summaries are built (raw Detection_Records zones are untouched).
ZONE_FLICKER_MERGE_S = 0.10


def collect_zone_visits(zone_states, fallback_end):
    """All (zone, start, end) visits of one track, including a visit that is
    still open when processing ends. Sorted by start time."""
    out = []
    for zname, zs in zone_states.items():
        for start, end in zs.get("visits", []):
            out.append((zname, float(start), float(end)))
        if zs.get("inside") and zs.get("entry_time") is not None:
            end = zs.get("last_inside_time")
            out.append((zname, float(zs["entry_time"]),
                        float(end) if end is not None else float(fallback_end)))
    out.sort(key=lambda v: (v[1], v[2]))
    return out


def clean_zone_visits(visits, merge_gap_s=ZONE_FLICKER_MERGE_S):
    """Remove zone-boundary flicker from a track's visit list.

    1. A short visit to another zone sandwiched between two visits of the same
       zone (A -> B -> A, B lasting <= merge_gap_s) is dropped.
    2. Consecutive visits of the same zone separated by <= merge_gap_s
       (the point briefly left the polygon) are merged into one visit.
    Real movements such as 1 -> 6 -> 5 are never changed.
    """
    vs = [list(v) for v in visits]
    changed = True
    while changed:
        changed = False
        i = 1
        while i < len(vs) - 1:
            a, b, c = vs[i - 1], vs[i], vs[i + 1]
            if (a[0] == c[0] and a[0] != b[0]
                    and b[2] - b[1] <= merge_gap_s
                    and c[1] - a[2] <= 2 * merge_gap_s):
                del vs[i]
                changed = True
            else:
                i += 1
        merged = []
        for v in vs:
            if merged and merged[-1][0] == v[0] and v[1] - merged[-1][2] <= merge_gap_s:
                merged[-1][2] = max(merged[-1][2], v[2])
                changed = True
            else:
                merged.append(v)
        vs = merged
    return [tuple(v) for v in vs]


# V28: Movement = the full (flicker-cleaned) zone sequence of a track.
# "side" selects the lane-width divisor of LDP for main-road through movements.
MOVEMENT_PATTERNS = {
    "1-3-4":   {"sequence": (1, 3, 4),    "type": "Left",    "main_road": False, "side": None,
                "name": "Left turn: side street -> main road"},
    "2-3-1":   {"sequence": (2, 3, 1),    "type": "Left",    "main_road": False, "side": None,
                "name": "Left turn: main road -> side street"},
    "1-3-6-7": {"sequence": (1, 3, 6, 7), "type": "Right",   "main_road": False, "side": None,
                "name": "Right turn: side street -> opposite side"},
    "5-6-3-1": {"sequence": (5, 6, 3, 1), "type": "Right",   "main_road": False, "side": None,
                "name": "Right turn: opposite side -> side street"},
    "2-3-4":   {"sequence": (2, 3, 4),    "type": "Through", "main_road": True,  "side": "entry",
                "name": "Through: entry side (Zones 2-3-4)"},
    "5-6-7":   {"sequence": (5, 6, 7),    "type": "Through", "main_road": True,  "side": "opposite",
                "name": "Through: opposite side (Zones 5-6-7)"},
}
MOVEMENT_IDS = list(MOVEMENT_PATTERNS)


def zone_sequence_from_samples(samples, merge_gap_s=ZONE_FLICKER_MERGE_S):
    """samples = [(timestamp, zone_number_or_None), ...] of ONE track (time order).
    Returns the flicker-cleaned zone sequence as a list of ints with no
    consecutive duplicates. A sample outside every zone (None) ends a visit."""
    visits = []
    cur = None
    for t, z in samples:
        if z is None:
            cur = None
            continue
        if cur is not None and visits[-1][0] == z:
            visits[-1][2] = t
        else:
            visits.append([z, t, t])
            cur = z
    seq = []
    for z, _s, _e in clean_zone_visits(visits, merge_gap_s):
        if not seq or seq[-1] != z:
            seq.append(z)
    return seq


def classify_movement(sequence):
    """Map a zone sequence to (movement_id, status). Never guesses.

    Exact        - equals one of MOVEMENT_PATTERNS
    Partial      - a fragment (>= 2 zones) that fits exactly ONE pattern
    Ambiguous    - a fragment that fits several patterns (e.g. 3-4 = 1-3-4 or 2-3-4)
    Unclassified - fits no pattern
    Insufficient - fewer than 2 zones observed
    """
    seq = []
    for z in sequence:
        z = int(z)
        if not seq or seq[-1] != z:
            seq.append(z)
    if len(seq) < 2:
        return "", "Insufficient"
    tup = tuple(seq)
    for mid, info in MOVEMENT_PATTERNS.items():
        if info["sequence"] == tup:
            return mid, "Exact"
    n = len(tup)
    cands = [mid for mid, info in MOVEMENT_PATTERNS.items()
             if any(info["sequence"][i:i + n] == tup for i in range(len(info["sequence"]) - n + 1))]
    if len(cands) == 1:
        return cands[0], "Partial"
    if len(cands) > 1:
        return "", "Ambiguous"
    return "", "Unclassified"


def rolling_median(values, k):
    """Rolling median with a window that shrinks at the ends (k odd; k<=1 = off)."""
    a = np.asarray(values, dtype=float)
    k = int(k)
    if k <= 1 or len(a) < 3:
        return a.copy()
    if k % 2 == 0:
        k += 1
    h = k // 2
    return np.array([np.median(a[max(0, i - h): i + h + 1]) for i in range(len(a))])


def path_speed(times, points, smoothing=1):
    """(distance_m, duration_s, speed_kmh) of one sample series, or None.
    points are metric (x, y). smoothing = rolling-median window (samples):
    only FULL symmetric windows are used, so the series is shortened by half a
    window at each end (a shrinking window at the ends would bias the path
    length of a moving vehicle low)."""
    n = len(times)
    if n < 2:
        return None
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    ts = list(times)
    k = int(smoothing) if smoothing else 1
    if k > 1:
        h = min(k // 2, (n - 2) // 2)
        if h >= 1:
            sx = [float(np.median(pts[i - h: i + h + 1, 0])) for i in range(h, n - h)]
            sy = [float(np.median(pts[i - h: i + h + 1, 1])) for i in range(h, n - h)]
            pts = np.stack([sx, sy], axis=1)
            ts = ts[h: n - h]
    dist = float(np.sum(np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))))
    dur = float(ts[-1] - ts[0])
    if dur <= 0 or dist <= 0:
        return None
    return dist, dur, dist / dur * 3.6


def track_speed_records(rows, speed_zones, movement_id="", movement_status="", smoothing=1):
    """Speed records of ONE track (rows in time order; dict rows with
    _timestamp, _m, _zone_num, frame): one record per selected zone plus one
    for the whole Movement (all samples inside the movement's zones)."""
    valid = [r for r in rows if r.get("_m") is not None and r.get("_zone_num") is not None]
    out = []

    def add(scope, key, sel, flag=""):
        if len(sel) < 2:
            return
        res = path_speed([r["_timestamp"] for r in sel], [r["_m"] for r in sel], smoothing)
        if res is None:
            return
        dist, dur, speed = res
        out.append({
            "Scope": scope, "Key": key, "Samples": len(sel),
            "Start_Time": sel[0]["_timestamp"], "End_Time": sel[-1]["_timestamp"],
            "Start_Frame": sel[0].get("frame", ""), "End_Frame": sel[-1].get("frame", ""),
            "Distance_m": dist, "Duration_s": dur, "Speed_kmh": speed, "Flag": flag,
        })

    for zone in sorted(speed_zones):
        add("Zone", f"Zone {zone}", [r for r in valid if r["_zone_num"] == zone])
    if movement_id:
        zones = set(MOVEMENT_PATTERNS[movement_id]["sequence"])
        add("Movement", movement_id, [r for r in valid if r["_zone_num"] in zones],
            "Partial_Movement" if str(movement_status).startswith("Partial") else "")
    return out


LDP_MIN_CHORD_M = 1.0   # the entry->exit reference line must be at least this long


def ldp_for_zone(points, lane_width_m, smoothing=1):
    """LDP of ONE vehicle in ONE zone (SPEC v28 section 4).

    Reference line = straight line from the point where the vehicle entered the
    zone (first sample) to the point where it left (last sample). Lateral
    deviation of every sample = its perpendicular distance to that line;
    dY = the maximum. LDP = dY / (W/2) x 100 with W = full width of that side's
    carriageway (motorcycle lane + car lane), so the divisor is W / 2.
    points are metric (x, y) in time order. Returns a dict or None (fewer than
    3 samples / zero-length chord)."""
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(pts) < 3:
        return None
    if smoothing and int(smoothing) > 1:
        # shrinking window at the ends on purpose: P_in / P_out must stay at the
        # zone entry / exit (unlike Speed, LDP is not a path-length measure)
        pts = np.stack([rolling_median(pts[:, 0], smoothing), rolling_median(pts[:, 1], smoothing)], axis=1)
    p_in, p_out = pts[0], pts[-1]
    chord = p_out - p_in
    length = float(np.hypot(chord[0], chord[1]))
    if length < 1e-9:
        return None
    u = chord / length
    rel = pts - p_in
    dev = np.abs(rel[:, 0] * u[1] - rel[:, 1] * u[0])       # |cross(u, p - p_in)|
    dy = float(np.max(dev))
    return {
        "P_in": (float(p_in[0]), float(p_in[1])), "P_out": (float(p_out[0]), float(p_out[1])),
        "Chord_Length_m": length, "Delta_Y_m": dy, "Mean_Dev_m": float(np.mean(dev)),
        "Samples": len(pts), "LDP_percent": dy / (float(lane_width_m) / 2.0) * 100.0,
        "Short_Chord": length < LDP_MIN_CHORD_M,
    }


def zone_edges(sequence):
    """Set of directed zone transitions of a sequence: (1,3,4) -> {(1,3), (3,4)}."""
    seq = list(sequence)
    return {(seq[i], seq[i + 1]) for i in range(len(seq) - 1)}


def same_direction_in_zone(seq_a, seq_b, zone):
    """Two vehicles move in the same direction in `zone` when their zone sequences
    share a directed transition that touches that zone (e.g. A = 2-3-4 and
    B = 2-3-1 share 2->3; A = 2-3-4 and B = 1-3-4 share 3->4). Needs >= 2 zones
    observed for both vehicles."""
    common = zone_edges(seq_a) & zone_edges(seq_b)
    return any(zone in edge for edge in common)


def track_headings(times, points, window_s, min_speed_ms):
    """Unit heading vector per sample from a centred window of observed samples
    (no interpolation). None where the vehicle is (nearly) stationary."""
    t = np.asarray(times, dtype=float)
    m = np.asarray(points, dtype=float).reshape(-1, 2)
    half = max(1e-6, float(window_s)) / 2.0
    lo = np.searchsorted(t, t - half, side="left")
    hi = np.searchsorted(t, t + half, side="right") - 1
    out = []
    for k in range(len(t)):
        a, b = lo[k], hi[k]
        if b <= a or t[b] <= t[a]:
            out.append(None)
            continue
        v = (m[b] - m[a]) / (t[b] - t[a])
        sp = float(np.hypot(v[0], v[1]))
        out.append((float(v[0] / sp), float(v[1] / sp)) if sp >= min_speed_ms else None)
    return out


def lateral_clearance(center_a, heading_a, center_b, len_a, len_b, w_a, w_b, along_limit=None, max_lateral=None):
    """Lateral clearance for one time sample (SPEC v28 section 5). Axes come from vehicle A's
    heading: `along` = separation along the heading, `lateral` = perpendicular
    separation. The vehicles are side by side when |along| <= along_limit, which is
    (L_A + L_B) / 2 unless a fixed limit (m) is given - only then the clearance is measurable.
    `max_lateral` (m, None/0 = off): a pair further apart sideways than this is not related
    (`Too_Far`), e.g. two vehicles far apart inside one large zone.
    clearance = lateral - (W_A + W_B) / 2 (edge to edge; negative = boxes overlap)."""
    dx, dy = center_b[0] - center_a[0], center_b[1] - center_a[1]
    hx, hy = heading_a
    along = dx * hx + dy * hy
    signed = hx * dy - hy * dx
    lateral = abs(signed)
    limit = along_limit if along_limit else (len_a + len_b) / 2.0
    return {
        "Along_m": along, "Lateral_m": lateral, "Signed_Lateral_m": signed,
        "Overlap": abs(along) <= limit,
        "Too_Far": bool(max_lateral) and lateral > max_lateral,
        "Clearance_m": lateral - (w_a + w_b) / 2.0,
    }


def conflict_type_from_sequences(seq_a, seq_b, trajectories_intersect=False):
    """PET conflict type. Crossing when the two trajectories intersect; otherwise
    Merging when both leave to the same zone, Diverging when both come from the
    same zone, else the undecided 'Merging/Diverging'."""
    if trajectories_intersect:
        return "Crossing"
    seq_a, seq_b = list(seq_a), list(seq_b)
    if seq_a and seq_b:
        if seq_a[-1] == seq_b[-1]:
            return "Merging"
        if seq_a[0] == seq_b[0]:
            return "Diverging"
    return "Merging/Diverging"


def rear_end_ttc(p_f, v_f, p_l, v_l, len_f, len_l, w_f, w_l, vmin, cos_max):
    """Rear-end TTC = S / CS (SPEC v28 section 7). Follower f, leader l;
    positions in m, velocities in m/s.
      S  = separation along the follower's heading - (L_f + L_l) / 2
      CS = closing speed along that heading = v_f - v_l(along)
    Conditions: follower moving (>= vmin), leader ahead, lateral offset within
    (W_f + W_l) / 2, same direction (or leader (nearly) stationary), CS > 0.
    Returns None when not a rear-end course, else a dict; TTC is None when the
    boxes already overlap (S <= 0)."""
    spd_f = math.hypot(v_f[0], v_f[1])
    if spd_f < vmin:
        return None
    hx, hy = v_f[0] / spd_f, v_f[1] / spd_f
    dx, dy = p_l[0] - p_f[0], p_l[1] - p_f[1]
    d_long = dx * hx + dy * hy
    if d_long <= 0:
        return None
    if abs(hx * dy - hy * dx) > (w_f + w_l) / 2.0:
        return None
    spd_l = math.hypot(v_l[0], v_l[1])
    if spd_l >= vmin and (hx * v_l[0] + hy * v_l[1]) / spd_l < cos_max:
        return None
    closing = spd_f - (v_l[0] * hx + v_l[1] * hy)
    if closing <= 0:
        return None
    gap = d_long - (len_f + len_l) / 2.0
    return {"S": gap, "CS": closing, "TTC": (gap / closing) if gap > 0 else None,
            "Speed_F": spd_f, "Speed_L": spd_l}


SIDE_TTC_MIN_ANGLE_DEG = 10.0   # paths closer to parallel than this are not a side (crossing) conflict


def side_ttc(p_i, v_i, p_j, v_j, len_i, len_j, vmin, min_angle_deg=SIDE_TTC_MIN_ANGLE_DEG,
             window_factor=1.0, margin_s=0.0, mode="earlier"):
    """Side (crossing / merging) TTC by distance to the path intersection
    (SPEC v28 section 7; constant velocity, straight paths along the velocity).
      X = intersection of the two straight paths (must be ahead of both)
      t_i = d_i / v_i,  t_j = d_j / v_j
    User-adjustable (the exact rule is not settled yet):
      window = window_factor x (L_i/v_i + L_j/v_j) / 2 + margin_s   (time the vehicles need to clear X)
      a collision course exists when |t_i - t_j| <= window
      TTC = "earlier" -> min(t_i, t_j) | "later" -> max(t_i, t_j) | "average" -> (t_i + t_j) / 2"""
    spd_i, spd_j = math.hypot(v_i[0], v_i[1]), math.hypot(v_j[0], v_j[1])
    if spd_i < vmin or spd_j < vmin:
        return None
    hix, hiy = v_i[0] / spd_i, v_i[1] / spd_i
    hjx, hjy = v_j[0] / spd_j, v_j[1] / spd_j
    den = hix * hjy - hiy * hjx
    if abs(den) < math.sin(math.radians(min_angle_deg)):
        return None
    dx, dy = p_j[0] - p_i[0], p_j[1] - p_i[1]
    s_i = (dx * hjy - dy * hjx) / den
    s_j = (dx * hiy - dy * hix) / den
    if s_i <= 0 or s_j <= 0:
        return None
    t_i, t_j = s_i / spd_i, s_j / spd_j
    window = float(window_factor) * (len_i / spd_i + len_j / spd_j) / 2.0 + float(margin_s)
    if abs(t_i - t_j) > window:
        return None
    ttc = {"later": max(t_i, t_j), "average": (t_i + t_j) / 2.0}.get(mode, min(t_i, t_j))
    return {"TTC": ttc, "t_i": t_i, "t_j": t_j, "d_i": s_i, "d_j": s_j,
            "window": window, "angle_deg": math.degrees(math.asin(min(1.0, abs(den))))}


def canvas_to_video(cx, cy, scale, width, height):
    """Canvas (screen) coordinates -> video pixel coordinates, clamped to the frame."""
    x = int(round(cx / scale))
    y = int(round(cy / scale))
    return max(0, min(width - 1, x)), max(0, min(height - 1, y))


def scale_points(points, src_w, src_h, dst_w, dst_h):
    """Scale (x, y) points from a src_w x src_h frame to a dst_w x dst_h frame.
    Returns the points unchanged when a size is unknown or the sizes match."""
    pts = [(int(round(x)), int(round(y))) for x, y in points]
    if not (src_w and src_h and dst_w and dst_h) or (src_w == dst_w and src_h == dst_h):
        return pts
    sx, sy = dst_w / float(src_w), dst_h / float(src_h)
    return [(int(round(x * sx)), int(round(y * sy))) for x, y in pts]


def update_reference_mapping_text(text, site_id, assignments):
    """Reference Line Mapping text with `Site_ID|Movement|Line N` rows for the
    given {movement: line_name}. Rows (active or commented-out template rows)
    of the same site and movement are replaced; everything else is kept."""
    site = str(site_id).strip()
    out = []
    for raw in str(text or "").splitlines():
        body = raw.strip().lstrip("#").strip()
        parts = [q.strip() for q in body.split("|")]
        if len(parts) == 3 and parts[0] == site and parts[1] in assignments:
            continue
        out.append(raw)
    while out and not out[-1].strip():
        out.pop()
    for movement, line_name in assignments.items():
        out.append(f"{site}|{movement}|{line_name}")
    return "\n".join(out)


DUPLICATE_TRACK_IOU = 0.70          # two track IDs whose boxes overlap this much are one vehicle
DUPLICATE_TRACK_MIN_FRAMES = 10     # ... for at least this many frames
DUPLICATE_SHORT_SHARE = 0.80        # a SHORT track (< min frames) is also a duplicate when this share of its frames overlaps a longer track


def bbox_iou(a, b):
    """Intersection over union of two (x1, y1, x2, y2) boxes."""
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def find_duplicate_tracks(frame_boxes, track_length, iou_min=DUPLICATE_TRACK_IOU,
                          min_frames=DUPLICATE_TRACK_MIN_FRAMES, short_share=DUPLICATE_SHORT_SHARE):
    """Detect one vehicle tracked under two IDs at the same time (an ID switch where the
    old ID does not die). frame_boxes = {frame: [(track_id, (x1, y1, x2, y2)), ...]},
    track_length = {track_id: number of rows}.

    Two IDs are duplicates when their boxes overlap with IoU >= iou_min in at least
    min_frames frames. A track that is shorter than min_frames (a 1-9 frame blip, often a second box
    with another class such as Van / Car on the same vehicle) is a duplicate when at least short_share
    of ITS frames overlap the other track that strongly. The track with fewer rows (ties: the later ID)
    is the duplicate.
    Returns {duplicate_id: {"keep": kept_id, "frames": set_of_frames_to_remove}}."""
    shared = {}
    for frame, items in frame_boxes.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                (ta, ba), (tb, bb) = items[i], items[j]
                if ta != tb and bbox_iou(ba, bb) >= iou_min:
                    shared.setdefault((ta, tb) if str(ta) < str(tb) else (tb, ta), set()).add(frame)
    out = {}
    for (ta, tb), frames in shared.items():
        la, lb = track_length.get(ta, 0), track_length.get(tb, 0)
        keep, drop = (ta, tb) if (la, str(tb)) > (lb, str(ta)) else (tb, ta)
        drop_len = max(1, track_length.get(drop, 0))
        if len(frames) < min_frames and not (drop_len < min_frames and len(frames) >= short_share * drop_len):
            continue
        entry = out.setdefault(drop, {"keep": keep, "frames": set()})
        entry["frames"] |= frames
    return out


def first_visit_order(sequence):
    """Zones in the order of their FIRST visit, repeats dropped (the idea of the Run 2
    column `unique_zones_visited`): 2,3,2,3,4 -> 2,3,4."""
    out = []
    for z in sequence:
        z = int(z)
        if z not in out:
            out.append(z)
    return out


def classify_movement_robust(sequence):
    """classify_movement on the cleaned zone sequence; when that gives no Exact/Partial
    answer, retry on the first-visit order so a vehicle that wobbles across a zone
    boundary (2-3-2-3-4) is still recognised. Returns (movement_id, status) with status
    Exact | Partial | Exact_AfterDedupe | Partial_AfterDedupe | Ambiguous |
    Unclassified | Insufficient. An Exact/Partial answer of the plain sequence is never
    changed."""
    movement, status = classify_movement(sequence)
    if status in ("Exact", "Partial"):
        return movement, status
    plain = []
    for z in sequence:
        if not plain or plain[-1] != int(z):
            plain.append(int(z))
    uniq = first_visit_order(sequence)
    if uniq != plain:
        movement2, status2 = classify_movement(uniq)
        if status2 == "Exact":
            return movement2, "Exact_AfterDedupe"
        if status2 == "Partial":
            return movement2, "Partial_AfterDedupe"
    return movement, status


# ---- Gap Acceptance (design of v26(5.14.11) "PASS", SPEC v28 section 6.1) ----
# Subject movement -> zones where the driver waits, conflict ("middle") zones and the target zone.
GAP_PATHS = {
    "1-3-4":   {"wait": (1,), "middle": (3,),   "target": 4},
    "1-3-6-7": {"wait": (1,), "middle": (3, 6), "target": 7},
    "5-6-3-1": {"wait": (5,), "middle": (6, 3), "target": 1},
}
# Fallback reference time of a conflicting stream when no Line is usable: the first time
# a vehicle of that stream is seen in the stream's origin zone.
GAP_REFERENCE_ZONE = {"2-3-4": 2, "5-6-7": 5, "5-6-3-1": 5, "1-3-6-7": 1}
GAP_HOLD_SPEED_KMH = 5.0      # default: "stopped" = speed <= this ...
GAP_HOLD_MIN_S = 0.30         # ... for at least this long (inside the conflict zones)


def find_hold(samples, speed_kmh=GAP_HOLD_SPEED_KMH, min_duration_s=GAP_HOLD_MIN_S):
    """Did the subject stop inside the conflict zones after entering them?

    samples = [(t, x_m, y_m, in_middle), ...] in time order, starting at the first
    sample inside the conflict zones. A stop = consecutive samples inside the
    conflict zones with speed <= speed_kmh lasting >= min_duration_s. No interpolation.
    Returns {"state": ..., "stop_start": t or None, "resume_time": t or None} with state
      "Continued"           - never stopped there
      "Stopped_then_Resumed"- resume_time = first observed sample after the stop that is
                              faster than the threshold or outside the conflict zones
      "Stopped_Censored"    - still stopped at the last observed sample"""
    prev = None
    run_start = None
    stop_start = None
    for t, x, y, inside in samples:
        if not inside:
            if stop_start is not None:
                return {"state": "Stopped_then_Resumed", "stop_start": stop_start, "resume_time": t}
            return {"state": "Continued", "stop_start": None, "resume_time": None}
        if prev is None:
            prev = (t, x, y)
            continue
        dt = t - prev[0]
        if dt <= 0:
            prev = (t, x, y)
            continue
        speed = math.hypot(x - prev[1], y - prev[2]) / dt * 3.6
        if speed <= speed_kmh:
            if run_start is None:
                run_start = prev[0]
            if stop_start is None and t - run_start >= min_duration_s:
                stop_start = run_start
        else:
            if stop_start is not None:
                return {"state": "Stopped_then_Resumed", "stop_start": stop_start, "resume_time": t}
            run_start = None
        prev = (t, x, y)
    if stop_start is not None:
        return {"state": "Stopped_Censored", "stop_start": stop_start, "resume_time": None}
    return {"state": "Continued", "stop_start": None, "resume_time": None}


def build_gap_intervals(events):
    """events = [(time, vehicle_id, class_name, reference_label, qc_flag), ...] of ONE
    conflicting stream. One event per vehicle (its earliest); gaps are the time between
    consecutive vehicles of the stream (different vehicles, positive length)."""
    first = {}
    for ev in events:
        vid = str(ev[1])
        if vid not in first or ev[0] < first[vid][0]:
            first[vid] = ev
    ordered = sorted(first.values(), key=lambda e: e[0])
    out = []
    for a, b in zip(ordered, ordered[1:]):
        if b[0] > a[0]:
            out.append({"gap_start": float(a[0]), "gap_end": float(b[0]),
                        "id_a": str(a[1]), "class_a": a[2], "id_b": str(b[1]), "class_b": b[2],
                        "reference": a[3], "qc": ";".join(dict.fromkeys(x for x in (a[4], b[4]) if x))})
    return out


def excel_safe_value(value):
    """Excel turns text such as 2-3-4 into a date (2 Mar 2004) and 5-6-7 into a number. A
    movement / zone sequence (zone numbers 1-7 joined by hyphens) is therefore written with
    arrows (2→3→4) in the Run 3 CSV files."""
    if isinstance(value, str) and re.fullmatch(r"[1-7](?:-[1-7])+", value):
        return value.replace("-", "→")
    return value

def is_speed_outlier(speed_kmh, max_kmh):
    """True when a Speed value is above the plausible maximum (max_kmh <= 0 = check off)."""
    return bool(max_kmh) and max_kmh > 0 and speed_kmh > max_kmh


def parse_clock_time(text):
    """Time typed by the user -> seconds. '' -> None; '75', '75.5' (seconds), '1:15', '01:15.5',
    '1:02:03' (h:m:s). Raises ValueError for anything else or a negative time."""
    s = str(text if text is not None else "").strip()
    if not s:
        return None
    parts = s.split(":")
    if len(parts) > 3:
        raise ValueError(f"time '{s}' is not valid (use seconds, m:ss or h:mm:ss)")
    try:
        nums = [float(x) for x in parts]
    except ValueError:
        raise ValueError(f"time '{s}' is not valid (use seconds, m:ss or h:mm:ss)")
    if any((x != x) or x < 0 or x in (float("inf"),) for x in nums):
        raise ValueError(f"time '{s}' is not valid")
    if len(nums) > 1 and any(x >= 60 for x in nums[1:]):
        raise ValueError(f"time '{s}': minutes and seconds must be below 60")
    secs = 0.0
    for x in nums:
        secs = secs * 60.0 + x
    return secs


def format_clock_time(seconds):
    """Seconds -> 'm:ss.s' or 'h:mm:ss.s' (what the player shows and what parse_clock_time reads back)."""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h * 3600 - m * 60
    return f"{h}:{m:02d}:{s:04.1f}" if h else f"{m}:{s:04.1f}"


def window_frames(start_s, end_s, fps, total_frames):
    """Time window -> (first_frame, last_frame), 1-based and inclusive; frame N is at time (N-1)/fps
    (SPEC: timestamps start at 0). start_s / end_s None = from the beginning / to the end.
    last_frame is None when the end is unknown (total_frames <= 0 and no end given).
    Raises ValueError when the window is empty or starts after the video ends."""
    first = 1
    if start_s is not None:
        first = int(math.ceil(start_s * fps - 1e-6)) + 1
    last = total_frames if total_frames and total_frames > 0 else None
    if end_s is not None:
        last_by_time = int(math.floor(end_s * fps + 1e-6)) + 1
        last = last_by_time if last is None else min(last, last_by_time)
    if total_frames and total_frames > 0 and first > total_frames:
        raise ValueError("the start time is after the end of the video")
    if last is not None and last < first:
        raise ValueError("the end time is before the start time")
    return first, last


def homography_from_points(src, dst):
    """3x3 homography mapping src -> dst (4 or more point pairs, direct linear transform)."""
    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.array(rows, dtype=float))
    h = vt[-1].reshape(3, 3)
    return h / h[2, 2]


def apply_homography(h, pts):
    p = np.asarray(pts, dtype=float).reshape(-1, 2)
    q = np.c_[p, np.ones(len(p))] @ np.asarray(h, dtype=float).T
    return q[:, :2] / q[:, 2:3]


def zone_metric_transform(src_pts, lengths, base_pts):
    """Per-zone calibration. src_pts = the 4 corners P1..P4 of the zone's own reference quadrilateral (image
    pixels); lengths = the real sides P1-P2, P2-P3, P3-P4, P4-P1 (m); base_pts = the same 4 corners in the common
    metric frame of the base calibration. The quadrilateral is mapped to its true rectangle with its own
    homography (so this zone gets its own scale and perspective), and that rectangle is then moved (rotation /
    mirror + shift, NO scaling) to the place where the base calibration puts the corners, so that positions of
    different zones stay in one common frame. 'rms' = how far the rigidly placed rectangle is from the base
    corners (m): a check that the zone reference and the base calibration describe the same patch of road."""
    l12, l23, l34, l41 = [float(v) for v in lengths]
    length, width = (l12 + l34) / 2.0, (l23 + l41) / 2.0
    rect = np.array([[0, 0], [length, 0], [length, width], [0, width]], dtype=float)
    h = homography_from_points(src_pts, rect)
    g = np.asarray(base_pts, dtype=float).reshape(4, 2)
    u, _, vt = np.linalg.svd((rect - rect.mean(0)).T @ (g - g.mean(0)))
    q = u @ vt
    t = g.mean(0) - rect.mean(0) @ q
    rms = float(np.sqrt(np.mean(np.sum((rect @ q + t - g) ** 2, axis=1))))
    return {"H": h, "Q": q, "t": t, "rms": rms, "length_m": length, "width_m": width}


def zone_metric_points(transform, pts):
    return apply_homography(transform["H"], pts) @ transform["Q"] + transform["t"]

# ---------------- Topview (road-plane) drawing helpers ----------------
TOPVIEW_CLASS_COLORS = {            # BGR
    "Motorcycle": (0, 165, 255), "Car": (255, 160, 40), "Pickup": (200, 120, 255), "Bus": (60, 60, 255),
    "Truck": (60, 200, 60), "Van": (200, 200, 60), "Sidecar": (0, 220, 220),
}
TOPVIEW_DEFAULT_COLOR = (230, 230, 230)


def topview_canvas(points_m, max_px=1280, margin_m=3.0, min_span_m=10.0, aspect=None):
    """Canvas for a Topview picture of metric points (N x 2): px/m, the metric origin of the top-left pixel and the
    picture size. Outliers are ignored (0.5 / 99.5 percentiles); the picture size is made even."""
    p = np.asarray(points_m, dtype=float).reshape(-1, 2)
    p = p[np.all(np.isfinite(p), axis=1)]
    if len(p) == 0:
        p = np.zeros((1, 2))
    lo = np.percentile(p, 0.5, axis=0) - margin_m
    hi = np.percentile(p, 99.5, axis=0) + margin_m
    span = np.maximum(hi - lo, min_span_m)
    if aspect:                                  # same width : height as the video (e.g. 16:9), the area is centred in it
        want = np.array([max(span[0], span[1] * aspect), max(span[1], span[0] / aspect)])
        lo = lo - (want - span) / 2.0
        span = want
    scale = float(max_px) / float(span.max())
    w, h = int(math.ceil(span[0] * scale)), int(math.ceil(span[1] * scale))
    return {"scale": scale, "xmin": float(lo[0]), "ymin": float(lo[1]), "w": w + (w % 2), "h": h + (h % 2)}


def topview_px(canvas, pts_m):
    """Metric points (N x 2) -> canvas pixels (N x 2, float)."""
    p = np.asarray(pts_m, dtype=float).reshape(-1, 2)
    return (p - np.array([canvas["xmin"], canvas["ymin"]])) * canvas["scale"]


def oriented_rect(center, heading, length, width):
    """Corners (4 x 2) of a length x width rectangle centred on `center`, its long side along `heading`
    (unit vector; None = along +x)."""
    hx, hy = heading if heading else (1.0, 0.0)
    ux, uy = np.array([hx, hy]), np.array([-hy, hx])
    c = np.asarray(center, dtype=float)
    hl, hw = length / 2.0, width / 2.0
    return np.array([c + hl * ux + hw * uy, c + hl * ux - hw * uy, c - hl * ux - hw * uy, c - hl * ux + hw * uy])

# ---------------- Lens (fisheye) distortion ----------------
# Action cameras (GoPro Wide, SJCAM 170 deg ...) look much wider than a rectilinear lens can: a polynomial in the
# image radius breaks down. The model used is the equidistant-with-corrections fisheye model (as cv2.fisheye):
#   a ray at angle theta from the optical axis lands at the normalised radius  theta_d = theta (1 + k1 theta^2 + k2 theta^4)
# (k1 = k2 = 0: the plain equidistant fisheye). In the straightened (rectilinear) picture the radius is tan(theta).
# lens = (f_ratio, k1[, k2]) with f = f_ratio x picture width (pixels), centre = picture centre.
THETA_MAX = 1.52                       # 87 degrees: a rectilinear picture cannot show rays beyond this


def _lens_terms(lens):
    return float(lens[0]), float(lens[1]), (float(lens[2]) if len(lens) > 2 else 0.0)


def lens_distort(pts, size, lens):
    """Straightened (rectilinear) pixels -> pixels as the fisheye lens recorded them."""
    f_ratio, k1, k2 = _lens_terms(lens)
    p = np.asarray(pts, dtype=float).reshape(-1, 2)
    c = np.array([size[0] / 2.0, size[1] / 2.0])
    f = f_ratio * size[0]
    x = (p - c) / f
    ru = np.sqrt((x ** 2).sum(axis=1))
    th = np.arctan(ru)
    thd = th * (1.0 + k1 * th ** 2 + k2 * th ** 4)
    scale = np.where(ru > 1e-12, thd / np.where(ru > 1e-12, ru, 1.0), 1.0)
    return x * scale[:, None] * f + c


def lens_undistort(pts, size, lens):
    """Pixels as recorded -> straightened (rectilinear) pixels (the inverse of lens_distort; Newton on the angle)."""
    f_ratio, k1, k2 = _lens_terms(lens)
    p = np.asarray(pts, dtype=float).reshape(-1, 2)
    c = np.array([size[0] / 2.0, size[1] / 2.0])
    f = f_ratio * size[0]
    x = (p - c) / f
    rd = np.sqrt((x ** 2).sum(axis=1))
    th = np.minimum(rd, THETA_MAX)
    for _ in range(50):
        g = th * (1.0 + k1 * th ** 2 + k2 * th ** 4) - rd
        d = 1.0 + 3.0 * k1 * th ** 2 + 5.0 * k2 * th ** 4
        th = np.clip(th - g / np.where(np.abs(d) < 1e-6, 1e-6, d), 0.0, THETA_MAX)
    ru = np.tan(th)
    scale = np.where(rd > 1e-12, ru / np.where(rd > 1e-12, rd, 1.0), 1.0)
    return x * scale[:, None] * f + c


def lens_is_valid(size, lens):
    """The model must grow steadily from the centre to the corner of the picture, with the corner ray inside 87 degrees."""
    f_ratio, k1, k2 = _lens_terms(lens)
    if f_ratio <= 0:
        return False
    rmax = math.hypot(size[0] / 2.0, size[1] / 2.0) / (f_ratio * size[0])        # corner radius (in f), as recorded
    th = np.linspace(0.0, THETA_MAX, 400)
    thd = th * (1.0 + k1 * th ** 2 + k2 * th ** 4)
    d = 1.0 + 3.0 * k1 * th ** 2 + 5.0 * k2 * th ** 4
    hit = np.nonzero(thd >= rmax)[0]
    if len(hit) == 0:
        return False
    return bool(np.all(d[:hit[0] + 1] > 0.1))


def line_bend(lines, size=None, lens=None):
    """How curved the clicked lines are: the RMS distance of their points from the straight line that fits them best, as a
    fraction of the line length (after the lens correction when `lens` is given). 0 = perfectly straight.
    lines = list of N x 2 arrays (N >= 3)."""
    acc, n = 0.0, 0
    for pts in lines:
        q = np.asarray(pts, dtype=float).reshape(-1, 2)
        if lens is not None:
            q = lens_undistort(q, size, lens)
        d = q - q.mean(axis=0)
        sv = np.linalg.svd(d, compute_uv=False)
        length = max(1e-9, float(np.ptp(d @ np.linalg.svd(d, full_matrices=False)[2][0])))
        acc += (float(sv[-1]) / math.sqrt(len(q)) / length) ** 2
        n += 1
    return math.sqrt(acc / n) if n else 0.0


def estimate_lens_from_lines(lines, size, use_k2=False, min_gain=0.3):
    """Find the fisheye lens that makes the clicked lines straight again. `lines` are points (pixels as recorded) clicked along
    things that are straight in reality (kerb edges, lane lines, crosswalk edges, building edges): >= 2 lines with >= 3 points
    each, best spread over the picture and its edges (a line through the centre says nothing about the lens).
    Searches f (the focal length, which for a fisheye sets how strongly the picture is bent) and k1 (and k2 when use_k2),
    with a small pull towards k = 0 (the plain equidistant fisheye). Returns {"lens", "bend_before", "bend_after" (fractions
    of the line length), "lines", "points"} or None when the lines are too few or the lens does not make them clearly
    straighter (< `min_gain`: the lens is not the problem, or the clicks are off)."""
    lines = [np.asarray(l, dtype=float).reshape(-1, 2) for l in lines if len(l) >= 3]
    if len(lines) < 2 or sum(len(l) for l in lines) < 6:
        return None
    before = line_bend(lines)

    def cost(f, k1, k2):
        lens = (f, k1, k2)
        if f <= 0.2 or not lens_is_valid(size, lens):
            return None
        return line_bend(lines, size, lens) ** 2 + 0.002 * (k1 ** 2 + k2 ** 2)

    best = (before ** 2, None)
    for f in np.arange(0.35, 1.61, 0.05):                            # coarse search without k2 (fast); k2 only refines
        for k1 in np.arange(-0.3, 0.301, 0.05):
            c_ = cost(float(f), float(k1), 0.0)
            if c_ is not None and c_ < best[0]:
                best = (c_, (float(f), float(k1), 0.0))
    if best[1] is None:
        return None
    step = [0.02, 0.02, 0.02]
    cur = list(best[1])
    for _ in range(18):                                              # local refinement, shrinking steps
        improved = False
        for idx in range(3 if use_k2 else 2):
            for sign in (1, -1):
                cand = list(cur)
                cand[idx] += sign * step[idx]
                c_ = cost(*cand)
                if c_ is not None and c_ < best[0]:
                    best, cur, improved = (c_, tuple(cand)), cand, True
        if not improved:
            step = [v / 2.0 for v in step]
    lens = tuple(float(v) for v in cur)
    after = line_bend(lines, size, lens)
    if after > (1.0 - min_gain) * before:
        return None
    return {"lens": lens, "bend_before": before, "bend_after": after, "lines": len(lines), "points": int(sum(len(l) for l in lines))}


# ==== CORE-END ====

RUN3_ALL_MOVEMENTS = MOVEMENT_IDS
# Gap Acceptance: subject movement -> conflicting movements whose line-crossing times
# form the available gaps (each needs a Reference Line Mapping entry).
# Confirmed by the user (2026-10-01): a subject may meet any of these streams, also several at once.
RUN3_GAP_CONFLICT_MAP = {
    "1-3-4": ["2-3-4"],
    "1-3-6-7": ["2-3-4", "5-6-7", "5-6-3-1"],
    "5-6-3-1": ["2-3-4", "1-3-6-7"],
}
LINE_NAMES = [f"Line {i}" for i in range(1, 7)]


class LineEditorDialog:
    """Click two points on a video frame to place the Reference Lines that Gap
    Acceptance needs (one per conflicting stream). Saves the Lines into the Zone
    JSON file and fills the Reference Line Mapping text."""

    def __init__(self, app, frame_bgr, frame_index, movements, assignments, lines):
        self.app = app
        self.frame_index = frame_index
        self.h, self.w = frame_bgr.shape[:2]
        self.movements = list(movements)
        self.assign = dict(assignments)
        self.points = {mv: [tuple(pt) for pt in lines.get(self.assign[mv], [])][:2] for mv in self.movements}
        self.pending = None
        self.current = next((mv for mv in self.movements if len(self.points[mv]) != 2), self.movements[0])

        self.top = tk.Toplevel(app.root)
        self.top.title("วาด Line สำหรับ Gap Acceptance")
        max_w = max(640, min(1300, self.top.winfo_screenwidth() - 340))
        max_h = max(360, min(820, self.top.winfo_screenheight() - 240))
        self.scale = min(1.0, max_w / float(self.w), max_h / float(self.h))
        shown = cv2.resize(frame_bgr, (int(self.w * self.scale), int(self.h * self.scale)))
        self._draw_zones(shown)
        ok, buf = cv2.imencode(".png", shown)
        self.photo = tk.PhotoImage(data=base64.b64encode(buf.tobytes()))

        side = ttk.Frame(self.top, padding=8)
        side.grid(row=0, column=0, sticky="ns")
        ttk.Label(side, text="1) เลือกกระแสรถ\n2) คลิก 2 จุดบนภาพ วางเส้นขวางทาง\n    ที่รถกระแสนั้นวิ่งผ่าน (ให้ยาวพอ\n    ที่รถทุกคันข้ามเส้นชัดเจน)\n3) กด \"บันทึก\"", justify="left").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.choice = tk.StringVar(value=self.current)
        self.status_labels = {}
        for i, mv in enumerate(self.movements, start=1):
            ttk.Radiobutton(side, text=f"กระแส {mv}  →  {self.assign[mv]}", value=mv, variable=self.choice,
                            command=lambda m=mv: self.select(m)).grid(row=i * 2 - 1, column=0, sticky="w")
            ttk.Button(side, text="ล้าง", width=5, command=lambda m=mv: self.clear(m)).grid(row=i * 2 - 1, column=1, padx=(6, 0))
            lab = ttk.Label(side, text="", foreground="#555555")
            lab.grid(row=i * 2, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=(0, 4))
            self.status_labels[mv] = lab
        nrow = len(self.movements) * 2 + 1
        ttk.Separator(side, orient="horizontal").grid(row=nrow, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(side, text=f"เฟรมที่ {frame_index} ของวิดีโอ ({self.w}×{self.h})", foreground="#555555").grid(row=nrow + 1, column=0, columnspan=2, sticky="w")
        ttk.Button(side, text="บันทึก", command=self.save).grid(row=nrow + 2, column=0, columnspan=2, sticky="ew", pady=(10, 2))
        ttk.Button(side, text="ปิด", command=self.top.destroy).grid(row=nrow + 3, column=0, columnspan=2, sticky="ew")

        self.canvas = tk.Canvas(self.top, width=shown.shape[1], height=shown.shape[0], highlightthickness=0, cursor="crosshair")
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.canvas.bind("<Button-1>", lambda e: self.add_point(e.x, e.y))
        self.canvas.bind("<Button-3>", lambda e: self.clear(self.current))
        self.redraw()

    # ---- drawing ----
    def _draw_zones(self, img):
        overlay = img.copy()
        for name, pts in self.app.zones.items():
            if len(pts) < 3:
                continue
            arr = (np.array(pts, dtype=float) * self.scale).astype(np.int32)
            cv2.fillPoly(overlay, [arr], (0, 200, 255))
            cv2.polylines(img, [arr], True, (0, 120, 255), 2)
            cx, cy = arr.mean(axis=0).astype(int)
            cv2.putText(img, name.replace("Zone ", ""), (int(cx) - 6, int(cy) + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.25, img, 0.75, 0, img)

    def redraw(self):
        self.canvas.delete("ov")
        colors = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#008080"]
        for i, mv in enumerate(self.movements):
            col = colors[i % len(colors)]
            pts = self.points[mv]
            if len(pts) == 2:
                (x1, y1), (x2, y2) = pts
                self.canvas.create_line(x1 * self.scale, y1 * self.scale, x2 * self.scale, y2 * self.scale, fill=col, width=4, tags="ov")
                for x, y in pts:
                    self.canvas.create_oval(x * self.scale - 5, y * self.scale - 5, x * self.scale + 5, y * self.scale + 5, fill=col, outline="white", tags="ov")
                self.canvas.create_text((x1 + x2) / 2 * self.scale + 6, (y1 + y2) / 2 * self.scale - 10, text=f"{mv} ({self.assign[mv]})", fill=col, anchor="w", font=("Segoe UI", 10, "bold"), tags="ov")
                self.status_labels[mv].config(text="วาดแล้ว ✓", foreground="#0a7a0a")
            else:
                self.status_labels[mv].config(text="ยังไม่ได้วาด", foreground="#b00020")
        if self.pending is not None:
            x, y = self.pending
            self.canvas.create_oval(x * self.scale - 6, y * self.scale - 6, x * self.scale + 6, y * self.scale + 6, outline="yellow", width=3, tags="ov")

    # ---- interaction (also called directly by the tests) ----
    def select(self, mv):
        self.current = mv
        self.choice.set(mv)
        self.pending = None
        self.redraw()

    def clear(self, mv):
        self.points[mv] = []
        if mv == self.current:
            self.pending = None
        self.redraw()

    def add_point(self, cx, cy):
        x, y = canvas_to_video(cx, cy, self.scale, self.w, self.h)
        if self.pending is None:
            self.pending = (x, y)
            self.points[self.current] = []
        else:
            if (x, y) == self.pending:
                return
            self.points[self.current] = [self.pending, (x, y)]
            self.pending = None
            nxt = next((m for m in self.movements if len(self.points[m]) != 2), None)
            if nxt:
                self.select(nxt)
                return
        self.redraw()

    def save(self):
        drawn = [mv for mv in self.movements if len(self.points[mv]) == 2]
        if not drawn:
            messagebox.showwarning("Line", "ยังไม่ได้วาดเส้นใดเลย", parent=self.top)
            return False
        missing = [mv for mv in self.movements if mv not in drawn]
        if missing and not messagebox.askyesno(
                "Line", "ยังไม่ได้วาดเส้นของกระแส: " + ", ".join(missing) + "\n\nบันทึกเฉพาะที่วาดแล้วหรือไม่?", parent=self.top):
            return False
        ok = self.app.apply_editor_lines(
            {self.assign[mv]: self.points[mv] for mv in drawn},
            {mv: self.assign[mv] for mv in drawn}, self.w, self.h)
        if ok:
            self.top.destroy()
        return ok


class ClipPlayerDialog:
    """Play a video inside the program and choose, for this clip, the time range to analyse and what to
    record. Result (self.result, None when cancelled):
      analysis_start_s / analysis_end_s   text, '' = from the beginning / to the end
      save_video                          False = record nothing
      record_start_s / record_end_s       text, '' = same as the analysis window
    Times are video times (m:ss.s); frame N is at (N-1)/fps like in every CSV file."""

    SHOW_W, SHOW_H = 900, 500

    def __init__(self, app, video_path, plan=None, title=None, modal=True):
        plan = plan or {}
        self.app = app
        self.video_path = video_path
        self.result = None
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise RuntimeError("Unable to open video")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        if self.fps <= 0:
            self.fps = 30.0
        self.total = max(1, int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.duration = self.total / self.fps
        self.pos = -1
        self.playing = False
        self._after = None
        self._busy = False

        self.top = tk.Toplevel(app.root)
        self.top.title(title or ("ดูวิดีโอและกำหนดช่วงเวลา — " + os.path.basename(video_path)))
        self.top.protocol("WM_DELETE_WINDOW", self.cancel)
        # The picture shrinks to fit the screen so that the OK / Cancel buttons at the bottom are always visible.
        sw, sh = self.top.winfo_screenwidth(), self.top.winfo_screenheight()
        self.SHOW_H = max(220, min(500, sh - 540))
        self.SHOW_W = max(480, min(900, sw - 80, int(self.SHOW_H * 1.8)))
        self.top.geometry("+10+10")

        self.a_start = tk.StringVar(value=str(plan.get("analysis_start_s", "") or ""))
        self.a_end = tk.StringVar(value=str(plan.get("analysis_end_s", "") or ""))
        self.r_start = tk.StringVar(value=str(plan.get("record_start_s", "") or ""))
        self.r_end = tk.StringVar(value=str(plan.get("record_end_s", "") or ""))
        if not plan.get("save_video", True):
            mode = "none"
        elif self.r_start.get().strip() or self.r_end.get().strip():
            mode = "range"
        else:
            mode = "window"
        self.rec_mode = tk.StringVar(value=mode)
        self.time_text = tk.StringVar(value="")

        self.canvas = tk.Canvas(self.top, width=self.SHOW_W, height=self.SHOW_H, bg="#111111", highlightthickness=0)
        self.canvas.grid(row=0, column=0, columnspan=2, padx=8, pady=(8, 4))
        self.slider = tk.Scale(self.top, from_=0, to=self.total - 1, orient="horizontal", showvalue=False,
                               length=self.SHOW_W, command=self._on_slider)
        self.slider.grid(row=1, column=0, columnspan=2, padx=8, sticky="ew")
        ttk.Label(self.top, textvariable=self.time_text, font=("Consolas", 11)).grid(row=2, column=0, columnspan=2, pady=(0, 2))

        bar = ttk.Frame(self.top)
        bar.grid(row=3, column=0, columnspan=2, pady=2)
        for text, delta in (("◀◀ -5 วิ", -5 * self.fps), ("◀ -1 เฟรม", -1), ("+1 เฟรม ▶", 1), ("+5 วิ ▶▶", 5 * self.fps)):
            ttk.Button(bar, text=text, command=lambda d=delta: self.step(int(round(d)))).pack(side="left", padx=2)
        self.play_button = ttk.Button(bar, text="▶ เล่น", width=9, command=self.toggle_play)
        self.play_button.pack(side="left", padx=(12, 2))

        a_box = ttk.LabelFrame(self.top, text="ช่วงที่ให้โปรแกรมวิเคราะห์ (ว่าง = ทั้งคลิป)", padding=6)
        a_box.grid(row=4, column=0, sticky="nsew", padx=(8, 4), pady=6)
        self._time_row(a_box, 0, "เริ่ม", self.a_start)
        self._time_row(a_box, 1, "สิ้นสุด", self.a_end)
        ttk.Label(a_box, text="เลื่อนวิดีโอไปจุดที่ต้องการ แล้วกด \"ใช้เวลานี้\"", foreground="#666666").grid(row=2, column=0, columnspan=4, sticky="w")

        r_box = ttk.LabelFrame(self.top, text="บันทึกวิดีโอผลลัพธ์ของคลิปนี้", padding=6)
        r_box.grid(row=4, column=1, sticky="nsew", padx=(4, 8), pady=6)
        ttk.Radiobutton(r_box, text="ไม่บันทึก", value="none", variable=self.rec_mode, command=self._redraw_timeline).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Radiobutton(r_box, text="บันทึกตลอดช่วงที่วิเคราะห์", value="window", variable=self.rec_mode, command=self._redraw_timeline).grid(row=1, column=0, columnspan=4, sticky="w")
        ttk.Radiobutton(r_box, text="บันทึกเฉพาะช่วง:", value="range", variable=self.rec_mode, command=self._redraw_timeline).grid(row=2, column=0, columnspan=4, sticky="w")
        self._time_row(r_box, 3, "เริ่ม", self.r_start)
        self._time_row(r_box, 4, "สิ้นสุด", self.r_end)

        self.timeline = tk.Canvas(self.top, width=self.SHOW_W, height=26, bg="#dddddd", highlightthickness=0)
        self.timeline.grid(row=5, column=0, columnspan=2, padx=8, pady=(0, 2))
        ttk.Label(self.top, text="แถบเวลา: สีเทา = ทั้งคลิป · ฟ้า = ช่วงวิเคราะห์ · แดง = ช่วงบันทึก · ขีดดำ = ตำแหน่งปัจจุบัน",
                  foreground="#666666").grid(row=6, column=0, columnspan=2)
        btns = ttk.Frame(self.top)
        btns.grid(row=7, column=0, columnspan=2, pady=8)
        self.ok_button = ttk.Button(btns, text="✔ บันทึกช่วงเวลานี้", width=20, command=self.apply)
        self.ok_button.pack(side="left", padx=6)
        ttk.Button(btns, text="ยกเลิก (ไม่บันทึก)", width=18, command=self.cancel).pack(side="left", padx=6)

        for var in (self.a_start, self.a_end, self.r_start, self.r_end):
            var.trace_add("write", lambda *_: self._redraw_timeline())
        self.top.bind("<Left>", lambda e: self.step(-1))
        self.top.bind("<Right>", lambda e: self.step(1))
        self.top.bind("<space>", lambda e: self.toggle_play())
        self.top.bind("<Return>", lambda e: self.apply())
        self.top.bind("<Escape>", lambda e: self.cancel())

        first = self._seconds(self.a_start.get())
        self.show_frame(int(round(first * self.fps)) if first is not None else 0)
        if modal:
            self.top.transient(app.root)
            self.top.grab_set()
            self.top.wait_window()

    # ---- building blocks ----
    def _time_row(self, parent, row, label, var):
        ttk.Label(parent, text=label, width=8).grid(row=row, column=0, sticky="w", pady=2)
        ttk.Entry(parent, textvariable=var, width=10).grid(row=row, column=1, sticky="w", pady=2)
        ttk.Button(parent, text="ใช้เวลานี้", command=lambda v=var: v.set(format_clock_time(self.current_time()))).grid(
            row=row, column=2, padx=4)
        ttk.Button(parent, text="ล้าง", width=5, command=lambda v=var: v.set("")).grid(row=row, column=3)

    @staticmethod
    def _seconds(text):
        try:
            return parse_clock_time(text)
        except ValueError:
            return None

    def current_time(self):
        return max(0, self.pos) / self.fps

    # ---- playback ----
    def show_frame(self, idx):
        idx = max(0, min(self.total - 1, int(idx)))
        if idx != self.pos + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = self.cap.read()
        if not ok or frame is None:
            self.playing = False
            self.play_button.config(text="▶ เล่น")
            return False
        self.pos = idx
        h, w = frame.shape[:2]
        scale = min(self.SHOW_W / float(w), self.SHOW_H / float(h))
        shown = cv2.resize(frame, (max(1, int(w * scale)), max(1, int(h * scale))))
        okp, buf = cv2.imencode(".png", shown)
        self.photo = tk.PhotoImage(data=base64.b64encode(buf.tobytes()))
        self.canvas.delete("all")
        self.canvas.create_image(self.SHOW_W // 2, self.SHOW_H // 2, image=self.photo)
        self._busy = True
        self.slider.set(idx)
        self._busy = False
        self.time_text.set(f"{format_clock_time(self.current_time())} / {format_clock_time(self.duration)}    เฟรม {idx + 1}/{self.total}")
        self._redraw_timeline()
        return True

    def _on_slider(self, value):
        if self._busy:
            return
        idx = int(float(value))
        if idx != self.pos:
            self.show_frame(idx)

    def step(self, delta):
        self.playing = False
        self.play_button.config(text="▶ เล่น")
        self.show_frame(self.pos + delta)

    def toggle_play(self):
        self.playing = not self.playing
        self.play_button.config(text="⏸ หยุด" if self.playing else "▶ เล่น")
        if self.playing:
            self._tick()

    def _tick(self):
        if not self.playing:
            return
        skip = max(1, int(round(self.fps / 25.0)))
        for _ in range(skip - 1):
            self.cap.grab()
            self.pos += 1
        if not self.show_frame(self.pos + 1):
            return
        self._after = self.top.after(40, self._tick)

    # ---- timeline ----
    def _redraw_timeline(self):
        c = self.timeline
        c.delete("all")
        w = self.SHOW_W
        x = lambda t: max(0, min(w, int(w * t / self.duration)))
        a0 = self._seconds(self.a_start.get())
        a1 = self._seconds(self.a_end.get())
        a0 = 0.0 if a0 is None else a0
        a1 = self.duration if a1 is None else a1
        c.create_rectangle(x(a0), 3, x(a1), 13, fill="#4a90e2", outline="")
        mode = self.rec_mode.get()
        if mode != "none":
            r0, r1 = a0, a1
            if mode == "range":
                v0, v1 = self._seconds(self.r_start.get()), self._seconds(self.r_end.get())
                r0 = a0 if v0 is None else max(a0, v0)
                r1 = a1 if v1 is None else min(a1, v1)
            c.create_rectangle(x(r0), 14, x(r1), 23, fill="#d9534f", outline="")
        c.create_line(x(self.current_time()), 0, x(self.current_time()), 26, fill="black", width=2)

    # ---- result ----
    def _validated(self):
        def get(var, label):
            try:
                return parse_clock_time(var.get())
            except ValueError as exc:
                raise ValueError(f"{label}: {exc}")
        a0, a1 = get(self.a_start, "เริ่มวิเคราะห์"), get(self.a_end, "สิ้นสุดวิเคราะห์")
        r0, r1 = get(self.r_start, "เริ่มบันทึก"), get(self.r_end, "สิ้นสุดบันทึก")
        if a0 is not None and a0 >= self.duration:
            raise ValueError("เวลาเริ่มวิเคราะห์อยู่หลังจบวิดีโอ")
        if a0 is not None and a1 is not None and a1 <= a0:
            raise ValueError("เวลาสิ้นสุดวิเคราะห์ต้องมากกว่าเวลาเริ่ม")
        if self.rec_mode.get() == "range" and r0 is not None and r1 is not None and r1 <= r0:
            raise ValueError("เวลาสิ้นสุดบันทึกต้องมากกว่าเวลาเริ่ม")
        return a0, a1, r0, r1

    def apply(self):
        try:
            self._validated()
        except ValueError as exc:
            messagebox.showerror("ช่วงเวลาไม่ถูกต้อง", str(exc), parent=self.top)
            return False
        mode = self.rec_mode.get()
        self.result = {
            "analysis_start_s": self.a_start.get().strip(),
            "analysis_end_s": self.a_end.get().strip(),
            "save_video": mode != "none",
            "record_start_s": self.r_start.get().strip() if mode == "range" else "",
            "record_end_s": self.r_end.get().strip() if mode == "range" else "",
        }
        self.close()
        return True

    def cancel(self):
        self.result = None
        self.close()

    def close(self):
        self.playing = False
        if self._after is not None:
            try:
                self.top.after_cancel(self._after)
            except Exception:
                pass
        try:
            self.cap.release()
        except Exception:
            pass
        try:
            self.top.grab_release()
        except Exception:
            pass
        self.top.destroy()


def lens_undistort_image(img, lens):
    """The camera picture with the fisheye distortion removed: the central part seen as a rectilinear picture of the same size and
    focal length f (so a pixel here is exactly the 'straightened' pixel lens_undistort returns for the recorded one)."""
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float64)
    src = lens_distort(np.stack([xs.ravel(), ys.ravel()], axis=1), (w, h), lens).reshape(h, w, 2).astype(np.float32)
    return cv2.remap(img, src[..., 0], src[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(32, 32, 32))


def show_lens_preview(parent, img, lens):
    """A window with the camera picture before (left) and after (right) the lens correction, with a grid:
    what is straight in the real world (kerbs, lane lines, building edges) must be straight on the right."""
    shown = []
    for im in (img.copy(), lens_undistort_image(img, lens)):
        h, w = im.shape[:2]
        for i in range(1, 10):
            cv2.line(im, (int(w * i / 10), 0), (int(w * i / 10), h - 1), (255, 255, 255), 1)
            cv2.line(im, (0, int(h * i / 10)), (w - 1, int(h * i / 10)), (255, 255, 255), 1)
        k = min(620.0 / w, 400.0 / h)
        ok, buf = cv2.imencode(".png", cv2.resize(im, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA))
        shown.append(tk.PhotoImage(data=base64.b64encode(buf.tobytes())))
    pv = tk.Toplevel(parent)
    pv.title("ภาพกล้องก่อน/หลังแก้เลนส์")
    pv.photos = shown
    k2 = f", k2={lens[2]:.2f}" if len(lens) > 2 and abs(lens[2]) > 1e-9 else ""
    for col, (text, ph_) in enumerate((("ก่อน (ภาพเดิมจากกล้อง)", shown[0]), (f"หลังแก้เลนส์ (f={lens[0]:.2f}, k1={lens[1]:.2f}{k2})", shown[1]))):
        ttk.Label(pv, text=text).grid(row=0, column=col, pady=(6, 0))
        tk.Label(pv, image=ph_).grid(row=1, column=col, padx=6, pady=4)
    ttk.Label(pv, text="ขอบถนน เส้นแบ่งเลน ขอบอาคารที่ตรงในโลกจริงควรเป็นเส้นตรงหลังแก้เลนส์ (เทียบกับเส้นตารางสีขาว) · ภาพหลังแก้เลนส์แสดงเฉพาะส่วนกลางของภาพ (ส่วนขอบถูกตัดออก) ซึ่งเป็นเรื่องปกติ",
              foreground="#555555").grid(row=2, column=0, columnspan=2, pady=(0, 8))
    return pv


class LensLineDialog:
    """Lens correction WITHOUT any reference picture: click points along things that are straight in the real world (kerb
    edges, lane lines, crosswalk edges, building edges) in a frame of the camera video; the lens (k1, optionally k2) that
    makes those lines straight again is found. Spread the lines over the picture and its edges. The logic is in plain
    methods (new_line, add_point, estimate, ...) so it can be tested without clicking."""

    VIEW_W, VIEW_H = 1000, 600
    LINE_COLORS = [(0, 255, 255), (0, 200, 0), (255, 160, 0), (255, 0, 255), (0, 128, 255), (255, 255, 0), (160, 160, 255), (80, 255, 160)]

    def __init__(self, app, video_path, on_apply, initial=None):
        self.app, self.on_apply = app, on_apply
        self.lines = [[]]
        self.lens = None
        self.result_info = None
        self.zoom = 1.0
        self.view = None
        self._pan = None
        self.photo = None
        self.last_render = None
        self.cap = cv2.VideoCapture(video_path)
        self.total = max(1, int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1))
        self.cam_img = None
        self.top = tk.Toplevel(app.root)
        self.top.title("แก้เลนส์จากเส้นตรง")
        self.top.geometry("+10+10")
        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self.top.dialog = self
        self.msg_var = tk.StringVar(value="")
        self.frame_var = tk.StringVar(value="")
        self.fixed_var = tk.BooleanVar(value=False)
        self.k2_var = tk.BooleanVar(value=False)
        self._build()
        self.set_frame(None)
        self.refresh()

    def _build(self):
        top = self.top
        bar = ttk.Frame(top, padding=6)
        bar.pack(fill="x")
        ttk.Label(bar, text=("คลิกจุดตามแนวที่ตรงในโลกจริง (ขอบฟุตปาธ เส้นแบ่งเลน ขอบทางม้าลาย ขอบอาคาร) เส้นละ 4–8 จุด ยิ่งไกลจากกลางภาพและยาวยิ่งดี "
                             "อย่างน้อย 3 เส้นกระจายทั่วภาพ แล้วกด ประมาณเลนส์ · ล้อเมาส์ = ซูมที่ลูกศรเมาส์ · ลาก = เลื่อนภาพ"),
                  wraplength=980, justify="left").grid(row=0, column=0, columnspan=9, sticky="w")
        ttk.Button(bar, text="เส้นใหม่", command=self.new_line).grid(row=1, column=0, pady=4, padx=(0, 4))
        ttk.Button(bar, text="ย้อนจุด", command=self.undo_point).grid(row=1, column=1, padx=4)
        ttk.Button(bar, text="ลบเส้นนี้", command=self.delete_line).grid(row=1, column=2, padx=4)
        ttk.Button(bar, text="ประมาณเลนส์", command=self.estimate).grid(row=1, column=3, padx=(14, 4))
        ttk.Checkbutton(bar, text="ใช้ k2 (ปรับละเอียด)", variable=self.k2_var).grid(row=1, column=4, padx=4)
        ttk.Checkbutton(bar, text="ดูภาพที่แก้เลนส์แล้ว", variable=self.fixed_var, command=self.refresh).grid(row=1, column=5, padx=4)
        ttk.Button(bar, text="รีเซ็ต View", command=self.reset_view).grid(row=1, column=6, padx=4)
        ttk.Button(bar, text="ใช้ค่านี้", command=self.apply).grid(row=1, column=7, padx=(14, 4))
        ttk.Button(bar, text="ปิด", command=self.close).grid(row=1, column=8, padx=4)
        ttk.Label(bar, text="เฟรม").grid(row=2, column=0, sticky="e")
        ttk.Entry(bar, textvariable=self.frame_var, width=8).grid(row=2, column=1, sticky="w")
        ttk.Button(bar, text="โหลดเฟรม", command=lambda: self.set_frame(self.frame_var.get())).grid(row=2, column=2, sticky="w")
        self.canvas = tk.Canvas(top, width=self.VIEW_W, height=self.VIEW_H, bg="#202020", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=6)
        self.canvas.bind("<Configure>", lambda e: self._on_configure())
        self.canvas.bind("<ButtonPress-1>", lambda e: self._press(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self._drag(e.x, e.y))
        self.canvas.bind("<ButtonRelease-1>", lambda e: self._release(e.x, e.y))
        for b in (2, 3):
            self.canvas.bind(f"<ButtonPress-{b}>", lambda e: self._press(e.x, e.y, True))
            self.canvas.bind(f"<B{b}-Motion>", lambda e: self._drag(e.x, e.y))
        self.canvas.bind("<MouseWheel>", lambda e: self.zoom_at(e.x, e.y, 1 if e.delta > 0 else -1))
        self.canvas.bind("<Button-4>", lambda e: self.zoom_at(e.x, e.y, 1))
        self.canvas.bind("<Button-5>", lambda e: self.zoom_at(e.x, e.y, -1))
        tk.Label(top, textvariable=self.msg_var, height=3, anchor="nw", wraplength=980, justify="left", padx=6, pady=4).pack(fill="x")

    # ----- the picture -----
    def set_frame(self, index):
        if not self.cap.isOpened():
            return False
        try:
            idx = int(float(index)) - 1 if index not in (None, "") else self.total // 2
        except ValueError:
            idx = self.total // 2
        idx = max(0, min(self.total - 1, idx))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = self.cap.read()
        if not ok:
            return False
        self.cam_img = fr
        self.size = (fr.shape[1], fr.shape[0])
        self.frame_var.set(str(idx + 1))
        self.view = None
        self.zoom = 1.0
        if getattr(self, "canvas", None):
            self.refresh()
        return True

    def _canvas_size(self):
        return max(50, self.canvas.winfo_width()), max(50, self.canvas.winfo_height())

    def reset_view(self):
        self.zoom = 1.0
        if self.cam_img is not None:
            cw, ch = self._canvas_size()
            w, h = self.size
            k = min(cw / float(w), ch / float(h))
            self.fit_k = k
            self.view = (k, (cw - w * k) / 2.0, (ch - h * k) / 2.0)
        self.refresh()

    def _on_configure(self):
        if self.zoom <= 1.0:
            self.view = None
        self.refresh()

    def zoom_at(self, ex, ey, steps):
        if self.view is None:
            return False
        k, ox, oy = self.view
        z_new = min(40.0, max(1.0, self.zoom * (1.25 ** steps)))
        if z_new == self.zoom:
            return False
        px, py = (ex - ox) / k, (ey - oy) / k
        self.zoom = z_new
        if z_new == 1.0:
            self.view = None
        else:
            k2 = self.fit_k * z_new
            self.view = (k2, ex - px * k2, ey - py * k2)
        self.refresh()
        return True

    def pan_by(self, dx, dy):
        if self.view is None:
            return False
        k, ox, oy = self.view
        self.view = (k, ox + dx, oy + dy)
        self.refresh()
        return True

    def _press(self, ex, ey, always_pan=False):
        self._pan = {"x": ex, "y": ey, "x0": ex, "y0": ey, "moved": bool(always_pan)}

    def _drag(self, ex, ey):
        p = self._pan
        if p is None:
            return
        if not p["moved"] and (abs(ex - p["x0"]) > 4 or abs(ey - p["y0"]) > 4) and self.zoom > 1.0:
            p["moved"] = True
        if p["moved"]:
            self.pan_by(ex - p["x"], ey - p["y"])
            p["x"], p["y"] = ex, ey

    def _release(self, ex, ey):
        p, self._pan = self._pan, None
        if p is not None and p["moved"]:
            return
        if self.view is None:
            return
        k, ox, oy = self.view
        x, y = (ex - ox) / k, (ey - oy) / k
        if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
            self.add_point(x, y)

    # ----- lines (logic) -----
    def new_line(self):
        if self.lines and not self.lines[-1]:
            return False                                           # the current line is still empty
        self.lines.append([])
        self.refresh()
        return True

    def add_point(self, x, y):
        """A point (in the picture as the camera recorded it) on the line being drawn. When the corrected picture is shown, the point
        is given in that picture and carried back to the recorded one."""
        pt = (float(x), float(y))
        if self.fixed_var.get() and self.lens is not None:
            pt = tuple(lens_distort([pt], self.size, self.lens)[0])
        self.lines[-1].append(pt)
        self.result_info = None
        self.refresh()
        return True

    def undo_point(self):
        if self.lines[-1]:
            self.lines[-1].pop()
        elif len(self.lines) > 1:
            self.lines.pop()
            if self.lines[-1]:
                self.lines[-1].pop()
        self.result_info = None
        self.refresh()

    def delete_line(self):
        if len(self.lines) > 1:
            self.lines.pop()
        else:
            self.lines = [[]]
        self.result_info = None
        self.refresh()

    def usable_lines(self):
        return [l for l in self.lines if len(l) >= 3]

    def estimate(self):
        use = self.usable_lines()
        if len(use) < 2:
            self.msg_var.set("ต้องมีอย่างน้อย 2 เส้น (แนะนำ 3 เส้นขึ้นไป) เส้นละ 3 จุดขึ้นไป")
            messagebox.showinfo("แก้เลนส์", self.msg_var.get(), parent=self.top)
            return None
        res = estimate_lens_from_lines(use, self.size, bool(self.k2_var.get()))
        if res is None:
            self.msg_var.set("ไม่พบเลนส์ที่ทำให้เส้นตรงขึ้นชัดเจน — เส้นอาจตรงอยู่แล้ว ผ่านกลางภาพมากเกินไป หรือคลิกไม่ตรงแนว ลองเพิ่มเส้นใกล้ขอบภาพ")
            messagebox.showinfo("แก้เลนส์", self.msg_var.get(), parent=self.top)
            return None
        self.lens, self.result_info = res["lens"], res
        self.msg_var.set(f"ประมาณเลนส์ได้: f = {res['lens'][0]:.3f}×ความกว้างภาพ, k1 = {res['lens'][1]:.3f}" + (f", k2 = {res['lens'][2]:.3f}" if self.k2_var.get() else "")
                         + f" · เส้นโค้ง {res['bend_before'] * 100:.2f}% → {res['bend_after'] * 100:.2f}% ของความยาวเส้น จาก {res['lines']} เส้น {res['points']} จุด"
                         + " · ติ๊ก 'ดูภาพที่แก้เลนส์แล้ว' เพื่อตรวจ แล้วกด ใช้ค่านี้")
        self.refresh()
        return res

    def apply(self):
        if self.lens is None:
            self.msg_var.set("ยังไม่ได้ประมาณเลนส์")
            return False
        self.on_apply(self.lens)
        self.close()
        return True

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        try:
            self.top.destroy()
        except tk.TclError:
            pass

    # ----- drawing -----
    def refresh(self):
        if self.cam_img is None or not getattr(self, "canvas", None):
            return
        if self.view is None:
            self.reset_view_silent()
        k, ox, oy = self.view
        cw, ch = self._canvas_size()
        show_fixed = self.fixed_var.get() and self.lens is not None
        img = lens_undistort_image(self.cam_img, self.lens) if show_fixed else self.cam_img
        h, w = img.shape[:2]
        out = np.full((ch, cw, 3), 32, np.uint8)
        ix0, iy0 = max(0, int(math.floor(-ox / k))), max(0, int(math.floor(-oy / k)))
        ix1, iy1 = min(w, int(math.ceil((cw - ox) / k))), min(h, int(math.ceil((ch - oy) / k)))
        if ix1 > ix0 and iy1 > iy0:
            res = cv2.resize(img[iy0:iy1, ix0:ix1], (max(1, int(round((ix1 - ix0) * k))), max(1, int(round((iy1 - iy0) * k)))),
                             interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_LINEAR)
            dx, dy = int(round(ix0 * k + ox)), int(round(iy0 * k + oy))
            sx0, sy0 = max(0, -dx), max(0, -dy)
            ex_, ey_ = min(res.shape[1], cw - dx), min(res.shape[0], ch - dy)
            if ex_ > sx0 and ey_ > sy0:
                out[dy + sy0:dy + ey_, dx + sx0:dx + ex_] = res[sy0:ey_, sx0:ex_]
        for n, pts in enumerate(self.lines):
            if not pts:
                continue
            col = self.LINE_COLORS[n % len(self.LINE_COLORS)]
            shown = lens_undistort(pts, self.size, self.lens) if show_fixed else np.asarray(pts, dtype=float)
            c = np.round(shown * k + np.array([ox, oy])).astype(np.int32)
            if len(c) > 1:
                cv2.polylines(out, [c.reshape(-1, 1, 2)], False, col, 1, cv2.LINE_AA)
            for q in c:
                cv2.circle(out, (int(q[0]), int(q[1])), 4, col, -1, cv2.LINE_AA)
            if show_fixed and len(shown) >= 3:                      # the straight line that fits the corrected points
                d = shown - shown.mean(axis=0)
                u = np.linalg.svd(d, full_matrices=False)[2][0]
                t = d @ u
                a, b = shown.mean(axis=0) + u * t.min(), shown.mean(axis=0) + u * t.max()
                cv2.line(out, tuple(np.round(a * k + [ox, oy]).astype(int)), tuple(np.round(b * k + [ox, oy]).astype(int)), (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(out, f"zoom x{self.zoom:.1f}" + ("   corrected picture" if show_fixed else ""), (6, ch - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        self.last_render = out
        ok, buf = cv2.imencode(".png", out)
        self.photo = tk.PhotoImage(data=base64.b64encode(buf.tobytes()))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        if not self.msg_var.get():
            self.msg_var.set("คลิกจุดตามแนวเส้นที่ตรงในโลกจริง")

    def reset_view_silent(self):
        cw, ch = self._canvas_size()
        w, h = self.size
        k = min(cw / float(w), ch / float(h))
        self.fit_k = k
        self.view = (k, (cw - w * k) / 2.0, (ch - h * k) / 2.0)


# ---------------- Road line types (Topview map) ----------------
_RL_WHITE, _RL_YELLOW, _RL_RED, _RL_BLACK, _RL_BLUE = (235, 235, 235), (0, 215, 255), (60, 60, 230), (12, 12, 12), (255, 130, 30)   # BGR
# key -> (Thai label, pattern [(length m, colour or None = gap)] or None = solid, colour of a solid line, width (m, min px), offsets (m))
ROAD_LINE_TYPES = {
    "white_solid": ("เส้นขาวทึบ (ขอบทาง / ห้ามเปลี่ยนเลน)", None, _RL_WHITE, (0.15, 2), (0.0,)),
    "white_dashed": ("เส้นขาวประ (แบ่งเลนทางเดียวกัน เปลี่ยนเลน/แซงได้)", [(3.0, _RL_WHITE), (6.0, None)], None, (0.15, 2), (0.0,)),
    "yellow_solid": ("เส้นเหลืองทึบ (แบ่งทิศทางสวน ห้ามแซง)", None, _RL_YELLOW, (0.15, 2), (0.0,)),
    "yellow_double": ("เส้นเหลืองคู่ (แบ่งทิศทางสวน ห้ามแซงทั้งสองฝั่ง)", None, _RL_YELLOW, (0.12, 2), (-0.15, 0.15)),
    "yellow_dashed": ("เส้นเหลืองประ (แบ่งทิศทางสวน แซงได้)", [(3.0, _RL_YELLOW), (6.0, None)], None, (0.15, 2), (0.0,)),
    "kerb_red_white": ("ขอบทางขาว-แดง", [(0.5, _RL_RED), (0.5, _RL_WHITE)], None, (0.35, 4), (0.0,)),
    "kerb_black_white": ("ขอบทางขาว-ดำ", [(0.5, _RL_BLACK), (0.5, _RL_WHITE)], None, (0.35, 4), (0.0,)),
    "kerb_yellow_white": ("ขอบทางขาว-เหลือง", [(0.5, _RL_YELLOW), (0.5, _RL_WHITE)], None, (0.35, 4), (0.0,)),
    "blue_motorcycle": ("ช่องจักรยานยนต์ (สีฟ้า)", None, _RL_BLUE, (0.5, 5), (0.0,)),
}
ROAD_LINE_DEFAULT = "white_solid"


def road_line_preview_color(kind):
    spec = ROAD_LINE_TYPES.get(kind, ROAD_LINE_TYPES[ROAD_LINE_DEFAULT])
    if spec[2] is not None:
        return spec[2]
    return next(c_ for _, c_ in spec[1] if c_ is not None and c_ != _RL_BLACK) if any(c_ not in (None, _RL_BLACK) for _, c_ in spec[1]) else _RL_BLACK


def normalize_road_line(item):
    """A saved road line (old format: a list of points; new: {"type"/"t", "points"/"p"}) -> (type key, list of (x, y))."""
    if isinstance(item, dict):
        kind = item.get("type", item.get("t", ROAD_LINE_DEFAULT))
        pts = item.get("points", item.get("p", []))
    else:
        kind, pts = ROAD_LINE_DEFAULT, item
    if kind == "kerb_yellow_black":                      # an earlier name of the white-yellow kerb
        kind = "kerb_yellow_white"
    if kind not in ROAD_LINE_TYPES:
        kind = ROAD_LINE_DEFAULT
    return kind, [(float(x), float(y)) for x, y in pts]


def road_line_straight(item):
    """Is this saved road line marked 'really straight' (it is then also used to estimate the lens)? Old formats: yes."""
    return bool(item.get("straight", item.get("s", True))) if isinstance(item, dict) else True


def _offset_polyline(q, d):
    """The polyline moved sideways by d pixels (normal of each vertex = mean of its two segments' normals)."""
    if abs(d) < 1e-9 or len(q) < 2:
        return q
    seg = np.diff(q, axis=0)
    ln = np.maximum(np.hypot(seg[:, 0], seg[:, 1]), 1e-9)
    nrm = np.stack([-seg[:, 1] / ln, seg[:, 0] / ln], axis=1)
    vn = np.zeros_like(q)
    vn[:-1] += nrm
    vn[1:] += nrm
    vl = np.maximum(np.hypot(vn[:, 0], vn[:, 1]), 1e-9)
    return q + vn / vl[:, None] * d


def draw_road_line(img, q, kind, scale):
    """Draw one road line (canvas pixels q, N x 2) in the style of its type; scale = px per metre."""
    label, pattern, color, (width_m, width_min), offsets = ROAD_LINE_TYPES.get(kind, ROAD_LINE_TYPES[ROAD_LINE_DEFAULT])
    q = np.asarray(q, dtype=float).reshape(-1, 2)
    if len(q) < 2:
        return
    width = max(int(width_min), int(round(width_m * scale)))
    for off in offsets:
        pts = _offset_polyline(q, off * scale)
        if pattern is None:
            cv2.polylines(img, [np.round(pts).astype(np.int32).reshape(-1, 1, 2)], False, color, width, cv2.LINE_AA)
            continue
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        total = float(cum[-1])
        period = sum(l_ for l_, _ in pattern) * scale
        if total <= 0 or period <= 1e-6 or total / period > 20000:
            continue
        pos, k = 0.0, 0
        while pos < total:
            length_m, col = pattern[k % len(pattern)]
            end = min(total, pos + length_m * scale)
            if col is not None and end > pos:
                tt = np.unique(np.concatenate([[pos], cum[(cum > pos) & (cum < end)], [end]]))
                xs, ys = np.interp(tt, cum, pts[:, 0]), np.interp(tt, cum, pts[:, 1])
                cv2.polylines(img, [np.round(np.stack([xs, ys], axis=1)).astype(np.int32).reshape(-1, 1, 2)], False, col, width, cv2.LINE_AA)
            pos, k = end, k + 1


class RoadLineDialog(LensLineDialog):
    """Road lines for the map-style Topview: click along kerbs, lane lines, crosswalk edges ... on a frame of the camera video
    (a line = as many points as it needs, 2 or more). The lines are carried to the road plane by the same lens + calibration
    as the vehicles, so they always match the vehicle positions. Same view controls as the lens tool."""

    def __init__(self, app, video_path, on_apply, initial=None):
        norm = [(normalize_road_line(it), road_line_straight(it)) for it in (initial or [])]
        super().__init__(app, video_path, on_apply)
        self.top.title("เลนส์ + เส้นถนน")
        self.types = [ROAD_LINE_DEFAULT]
        self.straight = [True]
        if norm:
            self.lines = [pts for (_, pts), _s in norm] + [[]]
            self.types = [k for (k, _), _s in norm] + [self.type_key()]
            self.straight = [st for _p, st in norm] + [bool(self.straight_var.get())]
        try:
            lens_now, size_now = app._run3_lens_params()
        except Exception:
            lens_now = None
        if lens_now is not None and tuple(size_now) == tuple(self.size):
            self.lens = tuple(lens_now)                      # the lens already set: the corrected picture can be shown at once
        self.refresh()

    def type_key(self):
        label = self.type_var.get()
        return next((k for k, v in ROAD_LINE_TYPES.items() if v[0] == label), ROAD_LINE_DEFAULT)

    def _sync_types(self):
        types = getattr(self, "types", [])
        while len(types) < len(self.lines):
            types.append(self.type_key())
        del types[len(self.lines):]
        self.types = types
        st = getattr(self, "straight", [])
        while len(st) < len(self.lines):
            st.append(bool(self.straight_var.get()))
        del st[len(self.lines):]
        self.straight = st

    def set_type(self, kind):
        """The type of the line being drawn."""
        self.type_var.set(ROAD_LINE_TYPES[kind][0])
        self._sync_types()
        self.types[-1] = kind
        self.refresh()

    def _on_straight_changed(self):
        self._sync_types()
        self.straight[-1] = bool(self.straight_var.get())
        self.result_info = None

    def usable_lines(self):
        """Only lines marked 'really straight' are used to estimate the lens (a curved road edge would bend the estimate)."""
        self._sync_types()
        return [l for l, st in zip(self.lines, self.straight) if st and len(l) >= 3]

    def _on_type_changed(self):
        self._sync_types()
        self.types[-1] = self.type_key()
        self.refresh()

    def new_line(self):
        ok = super().new_line()
        self._sync_types()
        return ok

    def undo_point(self):
        super().undo_point()
        self._sync_types()

    def delete_line(self):
        super().delete_line()
        self._sync_types()

    def refresh(self):
        self._sync_types()
        self.LINE_COLORS = [road_line_preview_color(k) for k in self.types] or [(0, 255, 255)]
        super().refresh()

    def _build(self):
        top = self.top
        bar = ttk.Frame(top, padding=6)
        bar.pack(fill="x")
        ttk.Label(bar, text=("คลิกจุดตามแนวเส้นถนน (ขอบถนน เส้นแบ่งเลน ขอบทางม้าลาย) เส้นละกี่จุดก็ได้ — เส้นตรงใช้ 2 จุด เส้นโค้งใช้หลายจุด "
                             "· เลือก ชนิดเส้น ก่อนวาดแต่ละเส้น · เส้นที่ตรงจริงในโลก (ติ๊กไว้) ใช้ประมาณเลนส์ได้ด้วย: เส้นตรงอย่างน้อย 3 เส้น 3 จุดขึ้นไป "
                             "ใกล้ขอบภาพ แล้วกด ประมาณเลนส์ — คลิกครั้งเดียวได้ทั้งเลนส์และเส้นถนน · กด เส้นใหม่ เมื่อจะเริ่มเส้นถัดไป · ล้อเมาส์ = ซูม · ลาก = เลื่อนภาพ"),
                  wraplength=980, justify="left").grid(row=0, column=0, columnspan=9, sticky="w")
        ttk.Button(bar, text="เส้นใหม่", command=self.new_line).grid(row=1, column=0, pady=4, padx=(0, 4))
        ttk.Button(bar, text="ย้อนจุด", command=self.undo_point).grid(row=1, column=1, padx=4)
        ttk.Button(bar, text="ลบเส้นนี้", command=self.delete_line).grid(row=1, column=2, padx=4)
        ttk.Button(bar, text="รีเซ็ต View", command=self.reset_view).grid(row=1, column=3, padx=4)
        ttk.Button(bar, text="ประมาณเลนส์", command=self.estimate).grid(row=1, column=4, padx=(14, 4))
        ttk.Checkbutton(bar, text="ดูภาพที่แก้เลนส์แล้ว", variable=self.fixed_var, command=self.refresh).grid(row=1, column=5, padx=4)
        ttk.Button(bar, text="ใช้ค่านี้ (เลนส์ + เส้น)", command=self.apply).grid(row=1, column=6, padx=(14, 4))
        ttk.Button(bar, text="ปิด", command=self.close).grid(row=1, column=7, padx=4)
        self.straight_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text="เส้นนี้ตรงจริง (ใช้ประมาณเลนส์)", variable=self.straight_var, command=self._on_straight_changed).grid(row=3, column=3, columnspan=3, sticky="w", padx=(10, 2))
        ttk.Label(bar, text="ชนิดเส้นที่กำลังวาด").grid(row=2, column=3, sticky="e", padx=(10, 2))
        self.type_var = tk.StringVar(value=ROAD_LINE_TYPES[ROAD_LINE_DEFAULT][0])
        cb = ttk.Combobox(bar, textvariable=self.type_var, values=[v[0] for v in ROAD_LINE_TYPES.values()], state="readonly", width=48)
        cb.grid(row=2, column=4, columnspan=3, sticky="w")
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_type_changed())
        ttk.Label(bar, text="เฟรม").grid(row=2, column=0, sticky="e")
        ttk.Entry(bar, textvariable=self.frame_var, width=8).grid(row=2, column=1, sticky="w")
        ttk.Button(bar, text="โหลดเฟรม", command=lambda: self.set_frame(self.frame_var.get())).grid(row=2, column=2, sticky="w")
        self.canvas = tk.Canvas(top, width=self.VIEW_W, height=self.VIEW_H, bg="#202020", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=6)
        self.canvas.bind("<Configure>", lambda e: self._on_configure())
        self.canvas.bind("<ButtonPress-1>", lambda e: self._press(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self._drag(e.x, e.y))
        self.canvas.bind("<ButtonRelease-1>", lambda e: self._release(e.x, e.y))
        for b in (2, 3):
            self.canvas.bind(f"<ButtonPress-{b}>", lambda e: self._press(e.x, e.y, True))
            self.canvas.bind(f"<B{b}-Motion>", lambda e: self._drag(e.x, e.y))
        self.canvas.bind("<MouseWheel>", lambda e: self.zoom_at(e.x, e.y, 1 if e.delta > 0 else -1))
        self.canvas.bind("<Button-4>", lambda e: self.zoom_at(e.x, e.y, 1))
        self.canvas.bind("<Button-5>", lambda e: self.zoom_at(e.x, e.y, -1))
        tk.Label(top, textvariable=self.msg_var, height=2, anchor="nw", wraplength=980, justify="left", padx=6, pady=4).pack(fill="x")

    def apply(self):
        self._sync_types()
        use = [{"type": k, "points": l, "straight": st} for l, k, st in zip(self.lines, self.types, self.straight) if len(l) >= 2]
        if not use and self.lens is None:
            self.msg_var.set("ยังไม่มีเส้น (แต่ละเส้นต้องมีอย่างน้อย 2 จุด)")
            messagebox.showinfo("เส้นถนน", self.msg_var.get(), parent=self.top)
            return False
        if use:
            self.on_apply(use)
        if self.lens is not None:
            self.app.set_lens_values(self.lens)
        self.close()
        return True


class BackgroundFrameReader:
    """Reads the next frames of a cv2.VideoCapture in a background thread while the main loop runs detection on the GPU
    (decoding a 1080p frame takes ~9 ms of CPU). The frames come out in exactly the same order and are exactly the same
    as reading them directly. decode(n) says whether the frame after n frames already read must be decoded (read) or
    only skipped (grab), the same rule the main loop uses."""

    _END = object()

    def __init__(self, cap, decode, frames_read, last_frame=None, maxsize=6):
        self.cap = cap
        self.decode = decode
        self.n = frames_read
        self.last_frame = last_frame
        self.error = None
        self.q = queue.Queue(maxsize=maxsize)
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _put(self, item):
        while not self._stop.is_set():
            try:
                self.q.put(item, timeout=0.2)
                return True
            except queue.Full:
                continue
        return False

    def _run(self):
        try:
            while not self._stop.is_set():
                if self.last_frame is not None and self.n >= self.last_frame:
                    break
                if self.decode(self.n):
                    ok, frame = self.cap.read()
                else:
                    ok, frame = self.cap.grab(), None
                self.n += 1
                if not ok:
                    break
                if not self._put(frame):
                    return
        except Exception as exc:          # reported to the main loop
            self.error = exc
        self._put(self._END)

    def next(self):
        """-> (ok, frame); frame is None for a frame that was only skipped."""
        item = self.q.get()
        if item is self._END:
            if self.error is not None:
                raise self.error
            self.q.put(self._END)         # keep answering 'end'
            return False, None
        return True, item

    def close(self):
        self._stop.set()
        try:
            while True:
                self.q.get_nowait()
        except queue.Empty:
            pass
        self.thread.join(timeout=5)


class BackgroundVideoWriter:
    """cv2.VideoWriter whose write() hands the frame to a background thread (encoding a 1080p frame takes ~25 ms of CPU),
    so the main loop does not wait for it. Frames are written in the same order; release() waits until all are written."""

    _END = object()

    def __init__(self, writer, maxsize=8):
        self.writer = writer
        self.error = None
        self.q = queue.Queue(maxsize=maxsize)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self._released = False

    def _run(self):
        while True:
            frame = self.q.get()
            if frame is self._END:
                break
            try:
                self.writer.write(frame)
            except Exception as exc:
                self.error = exc

    def isOpened(self):
        return self.writer.isOpened()

    def write(self, frame):
        if self.error is not None:
            raise self.error
        self.q.put(frame)

    def release(self):
        if self._released:
            return
        self._released = True
        self.q.put(self._END)
        self.thread.join()
        self.writer.release()


def fp16_is_faster(device_index=0):
    """FP16 is only faster on GPUs with tensor cores. On the GTX 16 series (and older cards) it is SLOWER: measured on the
    GTX 1650 with this model, 170 ms instead of 62 ms per frame. Auto precision uses FP16 only where it helps."""
    try:
        props = torch.cuda.get_device_properties(device_index)
    except Exception:
        return False
    name = str(props.name).upper()
    if "GTX 16" in name or "MX" in name:
        return False
    return props.major >= 7


def _tools_module(name):
    """Import a helper from the tools folder next to this file (batch_run)."""
    tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    return importlib.import_module(name)


class ClipListPanel(ttk.Frame):
    """Step 1 of the window: the clips to analyse. One clip or many, the same list: choose folders (any structure,
    any depth) or files, then set for every clip the time range to analyse and whether / which part of the result
    video to record. The output rebuilds the imported folder structure and gives every clip its own folder with its
    own CSV files; an existing folder is reused, a missing one is created, finished clips are skipped."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.bt = _tools_module("batch_run")
        self.clips = []
        self.keep_levels_var = tk.IntVar(value=0)
        self.skip_done_var = tk.BooleanVar(value=True)
        self.columnconfigure(0, weight=1)

        bar = ttk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Button(bar, text="เลือกโฟลเดอร์…", command=self.add_folder).pack(side="left", padx=2)
        ttk.Button(bar, text="เพิ่มไฟล์วิดีโอ…", command=self.add_files).pack(side="left", padx=2)
        ttk.Label(bar, text="รวมชื่อโฟลเดอร์ที่อยู่เหนือขึ้นไป").pack(side="left", padx=(12, 2))
        ttk.Spinbox(bar, from_=0, to=6, width=3, textvariable=self.keep_levels_var).pack(side="left")
        ttk.Button(bar, text="บันทึกรายการ…", command=self.save_plan).pack(side="right", padx=2)
        ttk.Button(bar, text="โหลดรายการ…", command=self.load_plan).pack(side="right", padx=2)

        self.tree = ttk.Treeview(self, columns=("clip", "analysis", "record", "chain"), show="headings", height=9, selectmode="extended")
        for col, text, width in (("clip", "คลิป (โฟลเดอร์ในผลลัพธ์ / ไฟล์)", 420), ("analysis", "ช่วงที่วิเคราะห์", 140), ("record", "บันทึกวิดีโอ", 170), ("chain", "ต่อเนื่อง", 130)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.app.refresh_checklist())
        self.rowconfigure(1, weight=1)

        act = ttk.Frame(self)
        act.grid(row=2, column=0, sticky="ew", pady=(4, 2))
        ttk.Button(act, text="ดูวิดีโอ / กำหนดช่วงเวลา…", command=self.edit_selected).pack(side="left", padx=2)
        ttk.Button(act, text="ต่อจากคลิปก่อน (ติ๊ก/เอาออก)", command=self.toggle_continue).pack(side="left", padx=2)
        ttk.Button(act, text="ลบที่เลือก", command=self.remove_selected).pack(side="left", padx=2)
        ttk.Button(act, text="ล้างรายการ", command=self.clear).pack(side="left", padx=2)
        ttk.Button(act, text="ทุกคลิป: ไม่บันทึกวิดีโอ", command=lambda: self.set_all_record(False)).pack(side="right", padx=2)
        ttk.Button(act, text="ทุกคลิป: บันทึกตลอดช่วงที่วิเคราะห์", command=lambda: self.set_all_record(True)).pack(side="right", padx=2)

        out = ttk.Frame(self)
        out.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        out.columnconfigure(1, weight=1)
        ttk.Label(out, text="โฟลเดอร์ผลลัพธ์").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(out, textvariable=app.output_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(out, text="Browse", command=app.browse_output).grid(row=0, column=2, padx=(6, 0))
        opts = ttk.Frame(self)
        opts.grid(row=4, column=0, sticky="w", pady=(4, 0))
        ttk.Checkbutton(opts, text="ข้ามคลิปที่วิเคราะห์เสร็จแล้ว (ดูจากโฟลเดอร์ผลลัพธ์ของคลิปนั้น)", variable=self.skip_done_var).pack(side="left")
        ttk.Label(self, foreground="#555555", justify="left",
                  text="• ดับเบิลคลิกที่คลิปเพื่อเปิดดูวิดีโอและตั้งช่วงเวลา/การบันทึกวิดีโอ (เลือกหลายคลิปแล้วตั้งครั้งเดียวได้) — คลิปเดียวก็ใช้รายการนี้\n"
                       "• คลิปที่เป็นส่วนต่อเนื่องของคลิปก่อนหน้า (เช่น โดรนแบ่งไฟล์) → เลือกคลิปแล้วกด \"ต่อจากคลิปก่อน\": การติดตามต่อเนื่อง รถคันเดิมได้ ID เดิมข้ามรอยตัด เลขใหม่นับต่อกัน — แต่ช่วงวิเคราะห์ การบันทึกวิดีโอ และ CSV ยังแยกต่อคลิป\n"
                       "• เลข ID ต่อจากคลิปก่อนหน้าในโฟลเดอร์เดียวกันเสมอ (ไม่ซ้ำกันทั้งชุด)\n"
                       "• คลิปที่เพิ่มเข้ามาตั้งเป็น \"ไม่บันทึกวิดีโอ\" ไว้ก่อน — ต้องการบันทึกให้กดปุ่ม \"ทุกคลิป: บันทึกตลอดช่วงที่วิเคราะห์\" หรือตั้งเป็นรายคลิป\n"
                       "• ผลลัพธ์สร้างโครงสร้างโฟลเดอร์ตามที่นำเข้า: โฟลเดอร์ผลลัพธ์ / ...โฟลเดอร์ต้นฉบับ... / ชื่อคลิป / (โฟลเดอร์ที่มีแล้วใช้อันเดิม)\n"
                       "• เวลาใน CSV เป็นเวลาของวิดีโอต้นฉบับ (เริ่มวิเคราะห์ที่นาที 2 → เวลาแรกใน CSV ≈ 120 วินาที)").grid(row=5, column=0, sticky="w", pady=(6, 0))

    # ---- list ----
    def _levels(self):
        try:
            return max(0, int(self.keep_levels_var.get()))
        except (tk.TclError, ValueError):
            return 0

    def _new_clip(self, video, rel_dir):
        return {"video": video, "rel_dir": rel_dir, "analysis_start_s": "", "analysis_end_s": "",
                "save_video": False, "record_start_s": "", "record_end_s": "", "continues_previous": False}     # new clips: no result video (faster, smaller)

    def add_videos(self, found):
        have = {c["video"] for c in self.clips}
        for video, rel in found:
            if video not in have:
                self.clips.append(self._new_clip(video, rel))
                have.add(video)
        self.refresh()

    def add_folder(self):
        """Import a folder with any structure. The output rebuilds it from the picked folder's name
        (plus the names of the 'levels above' folders when that number is above 0)."""
        path = filedialog.askdirectory(title="เลือกโฟลเดอร์ที่มีวิดีโอ (โครงสร้างโฟลเดอร์ข้างในจะถูกสร้างตามในผลลัพธ์)")
        if path:
            found = self.bt.find_videos([path], keep_levels=self._levels())
            if not found:
                messagebox.showinfo("คลิปวิดีโอ", "ไม่พบไฟล์วิดีโอในโฟลเดอร์นี้")
            self.add_videos(found)

    def add_files(self):
        paths = filedialog.askopenfilenames(title="เลือกวิดีโอ", filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")])
        self.add_videos(self.bt.find_videos([os.path.abspath(p) for p in paths], keep_levels=self._levels()))

    def selected_indexes(self):
        return sorted(int(i) for i in self.tree.selection())

    def remove_selected(self):
        for i in reversed(self.selected_indexes()):
            del self.clips[i]
        self.refresh()

    def clear(self):
        self.clips = []
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, c in enumerate(self.clips):
            ana, rec = self.bt.clip_label(c)
            cont = bool(c.get("continues_previous")) and i > 0
            name = "/".join(x for x in (c.get("rel_dir", ""), os.path.basename(c["video"])) if x)
            self.tree.insert("", "end", iid=str(i), values=(name, ana, rec, "↳ ต่อจากคลิปก่อน" if cont else ""))
        if self.clips:
            self.app.video_var.set(self.clips[0]["video"])
        self.app.refresh_checklist()

    def edit_selected(self):
        sel = self.selected_indexes()
        if not sel:
            messagebox.showinfo("คลิปวิดีโอ", "เลือกคลิปในรายการก่อน")
            return
        clip = self.clips[sel[0]]
        try:
            dlg = ClipPlayerDialog(self.app, clip["video"], clip)
        except Exception as exc:
            messagebox.showerror("ดูวิดีโอ", str(exc))
            return
        if dlg.result:
            for i in sel:                      # one choice applies to every selected clip
                self.clips[i].update(dlg.result)
            self.refresh()
            self.tree.selection_set([str(i) for i in sel])

    def toggle_continue(self):
        """Mark the selected clips as the continuation of the clip above them in the list (the tracking and vehicle IDs
        carry on from that clip; time range, recording and results stay separate). Clears the mark when it is already set."""
        sel = [i for i in self.selected_indexes() if i > 0]
        if not sel:
            messagebox.showinfo("คลิปวิดีโอ", "เลือกคลิปที่ต่อจากคลิปก่อนหน้า (ไม่ใช่คลิปแรกของรายการ)")
            return
        turn_on = not all(self.clips[i].get("continues_previous") for i in sel)
        for i in sel:
            self.clips[i]["continues_previous"] = turn_on
        self.refresh()
        self.tree.selection_set([str(i) for i in sel])

    def set_all_record(self, on):
        for c in self.clips:
            c["save_video"] = bool(on)
            if not on:
                c["record_start_s"] = c["record_end_s"] = ""
        self.refresh()

    # ---- list file ----
    def save_plan(self):
        if not self.clips:
            return
        path = filedialog.asksaveasfilename(title="บันทึกรายการคลิป", defaultextension=".json", filetypes=[("Clip list", "*.json")])
        if path:
            self.bt.save_plan(path, self.app.output_var.get().strip(), self.clips)

    def load_plan(self):
        path = filedialog.askopenfilename(title="โหลดรายการคลิป", filetypes=[("Clip list", "*.json")])
        if not path:
            return
        try:
            out, clips = self.bt.load_plan(path)
        except Exception as exc:
            messagebox.showerror("คลิปวิดีโอ", f"อ่านรายการไม่ได้: {exc}")
            return
        self.clips = []
        for c in clips:
            item = self._new_clip(c["video"], str(c.get("rel_dir", "") or ""))
            item.update({k: c[k] for k in self.bt.PLAN_KEYS if k in c})
            self.clips.append(item)
        if out:
            self.app.output_var.set(out)
        self.refresh()


class Run1App:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "PK Studio V28"
        )

        self.root.geometry(
            "1250x850"
        )

        self.root.minsize(
            950,
            700
        )

        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.running = False
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.worker_thread = None

        # Worker threads never touch Tk: they post callables here and the main thread runs them.
        self._ui_queue = queue.Queue()

        self.create_variables()
        self.build_gui()
        self.update_hardware_info()
        self._poll_ui_queue()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    # ========================================================
    # VARIABLES
    # ========================================================

    def create_variables(self):

        self.run_name_var = tk.StringVar(
            value=DEFAULT_SETTINGS["run_name"]
        )

        self.model_var = tk.StringVar(
            value=DEFAULT_SETTINGS["model"]
        )

        self.video_var = tk.StringVar(
            value=DEFAULT_SETTINGS["video"]
        )

        self.output_var = tk.StringVar(
            value=DEFAULT_SETTINGS["output"]
        )

        self.conf_var = tk.StringVar(
            value=DEFAULT_SETTINGS["confidence"]
        )

        self.iou_var = tk.StringVar(
            value=DEFAULT_SETTINGS["iou"]
        )

        self.img_size_var = tk.StringVar(
            value=DEFAULT_SETTINGS["img_size"]
        )

        self.tracker_var = tk.StringVar(
            value=DEFAULT_SETTINGS["tracker"]
        )

        self.device_var = tk.StringVar(
            value=DEFAULT_SETTINGS["device"]
        )

        self.precision_var = tk.StringVar(
            value=DEFAULT_SETTINGS["precision"]
        )

        self.frame_skip_var = tk.StringVar(
            value=DEFAULT_SETTINGS["frame_skip"]
        )

        self.track_high_var = tk.StringVar(
            value=DEFAULT_SETTINGS["track_high"]
        )

        self.track_low_var = tk.StringVar(
            value=DEFAULT_SETTINGS["track_low"]
        )

        self.new_track_var = tk.StringVar(
            value=DEFAULT_SETTINGS["new_track"]
        )

        self.track_buffer_var = tk.StringVar(
            value=DEFAULT_SETTINGS["track_buffer"]
        )

        self.match_threshold_var = tk.StringVar(
            value=DEFAULT_SETTINGS["match_threshold"]
        )

        self.show_preview_var = tk.BooleanVar(
            value=DEFAULT_SETTINGS["show_preview"]
        )

        self.draw_center_var = tk.BooleanVar(
            value=DEFAULT_SETTINGS["draw_center"]
        )

        self.draw_trail_var = tk.BooleanVar(
            value=DEFAULT_SETTINGS["draw_trail"]
        )

        self.trail_length_var = tk.StringVar(
            value=DEFAULT_SETTINGS["trail_length"]
        )

        self.save_video_var = tk.BooleanVar(
            value=DEFAULT_SETTINGS["save_video"]
        )

        self.save_csv_var = tk.BooleanVar(
            value=DEFAULT_SETTINGS["save_csv"]
        )

        self.csv_flush_var = tk.StringVar(
            value=DEFAULT_SETTINGS["csv_flush"]
        )

        self.research_mode_var = tk.BooleanVar(
            value=DEFAULT_SETTINGS["research_mode"]
        )

        # Trajectory Position controls.
        self.trajectory_position_var = tk.StringVar(value=DEFAULT_SETTINGS["trajectory_position"])
        self.trajectory_offset_var = tk.StringVar(value=DEFAULT_SETTINGS["trajectory_offset"])

        # Zone overlay display controls.
        self.show_zone_boundary_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_zone_boundary"])
        self.show_zone_label_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_zone_label"])
        self.show_zone_label_prefix_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_zone_label_prefix"])
        self.zone_overlay_opacity_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_overlay_opacity"])

        # Individual vehicle label controls.
        self.show_label_id_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_label_id"])
        self.show_label_class_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_label_class"])
        self.show_label_conf_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_label_conf"])
        self.show_label_zone_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_label_zone"])
        self.show_label_speed_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_label_speed"])
        self.show_bbox_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_bbox"])
        self.show_prefix_id_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_prefix_id"])
        self.show_prefix_class_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_prefix_class"])
        self.show_prefix_conf_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_prefix_conf"])
        self.show_prefix_zone_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_prefix_zone"])
        self.show_prefix_speed_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_prefix_speed"])


        # ========================================================
        # RUN 3 SAFETY ANALYSIS VARIABLES
        # ========================================================
        self.run3_site_id_var = tk.StringVar(value=RUN3_DEFAULTS["site_id"])
        self.run3_speed_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["speed_enabled"])
        self.run3_gap_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["gap_enabled"])
        self.run3_lc_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["lc_enabled"])
        self.run3_pet_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["pet_enabled"])
        self.run3_ttc_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["ttc_enabled"])
        self.run3_ldp_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["ldp_enabled"])
        self.run3_ppm_var = tk.StringVar(value=RUN3_DEFAULTS["ppm"])
        self.run3_perspective_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["perspective_enabled"])
        self.run3_perspective_p1_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_p1"])
        self.run3_perspective_p2_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_p2"])
        self.run3_perspective_p3_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_p3"])
        self.run3_perspective_p4_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_p4"])
        self.run3_perspective_length_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_length_m"])
        self.run3_perspective_width_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_width_m"])
        self.run3_perspective_l12_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_l12_m"])
        self.run3_perspective_l23_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_l23_m"])
        self.run3_perspective_l34_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_l34_m"])
        self.run3_perspective_l41_var = tk.StringVar(value=RUN3_DEFAULTS["perspective_l41_m"])
        self.run3_waiting_speed_threshold_var = tk.StringVar(value=RUN3_DEFAULTS["waiting_speed_threshold"])
        self.run3_hold_min_duration_var = tk.StringVar(value=RUN3_DEFAULTS["gap_hold_min_duration_s"])
        self.run3_lateral_axis_angle_var = tk.StringVar(value=RUN3_DEFAULTS["lateral_axis_angle_deg"])
        self.run3_lc_heading_window_var = tk.StringVar(value=RUN3_DEFAULTS["lc_heading_window_s"])
        self.run3_topview_video_var = tk.BooleanVar(value=RUN3_DEFAULTS["topview_video"])
        self.run3_topview_map_var = tk.BooleanVar(value=RUN3_DEFAULTS["topview_map"])
        self.run3_road_lines_var = tk.StringVar(value=RUN3_DEFAULTS["road_lines"])
        self.run3_lens_f_var = tk.StringVar(value=RUN3_DEFAULTS["lens_f"])
        self.run3_lens_k1_var = tk.StringVar(value=RUN3_DEFAULTS["lens_k1"])
        self.run3_lens_k2_var = tk.StringVar(value=RUN3_DEFAULTS["lens_k2"])
        self.run3_lc_along_limit_var = tk.StringVar(value=RUN3_DEFAULTS["lc_along_limit_m"])
        self.run3_lc_max_lateral_var = tk.StringVar(value=RUN3_DEFAULTS["lc_max_lateral_m"])
        self.run3_lc_motorcycle_pairs_only_var = tk.BooleanVar(value=RUN3_DEFAULTS["lc_motorcycle_pairs_only"])
        self.run3_pet_interaction_distance_var = tk.StringVar(value=RUN3_DEFAULTS["pet_interaction_distance_m"])
        self.run3_pet_threshold_var = tk.StringVar(value=RUN3_DEFAULTS["pet_threshold_s"])
        self.run3_speed_zone_vars = {z: tk.BooleanVar(value=(z in RUN3_DEFAULTS["speed_zones"])) for z in ZONE_IDS}
        self.run3_speed_smoothing_var = tk.StringVar(value=RUN3_DEFAULTS["speed_smoothing_samples"])
        self.run3_speed_max_var = tk.StringVar(value=RUN3_DEFAULTS["speed_max_kmh"])
        self.run3_zone_calibrations = {}          # {"4": {"points": [[x, y] x 4], "lengths": [l12, l23, l34, l41]}}: own reference quad per zone
        self.run3_zone_cal_text = tk.StringVar(value="")
        self.analysis_start_var = tk.StringVar(value=DEFAULT_SETTINGS["analysis_start_s"])
        self.analysis_end_var = tk.StringVar(value=DEFAULT_SETTINGS["analysis_end_s"])
        self.record_start_var = tk.StringVar(value=DEFAULT_SETTINGS["record_start_s"])
        self.record_end_var = tk.StringVar(value=DEFAULT_SETTINGS["record_end_s"])
        self.run3_lc_zone_vars = {z: tk.BooleanVar(value=(z in RUN3_DEFAULTS["lc_zones"])) for z in ZONE_IDS}
        self.run3_pet_zone_vars = {z: tk.BooleanVar(value=(z in RUN3_DEFAULTS["pet_zones"])) for z in CONFLICT_ZONE_IDS}
        self.run3_pet_zone6_var = self.run3_pet_zone_vars[6]   # backward-compatible alias
        self.run3_ttc_zone_vars = {z: tk.BooleanVar(value=(z in RUN3_DEFAULTS["ttc_zones"])) for z in ZONE_IDS}
        self.run3_ldp_zone_vars = {z: tk.BooleanVar(value=(z in RUN3_DEFAULTS["ldp_zones"])) for z in ZONE_IDS}
        self.run3_pet_max_var = tk.StringVar(value=RUN3_DEFAULTS["pet_max_s"])
        self.run3_ttc_max_record_var = tk.StringVar(value=RUN3_DEFAULTS["ttc_max_record_s"])
        self.run3_ttc_heading_max_var = tk.StringVar(value=RUN3_DEFAULTS["ttc_heading_max_deg"])
        self.run3_ttc_velocity_window_var = tk.StringVar(value=RUN3_DEFAULTS["ttc_velocity_window_s"])
        self.run3_ttc_min_speed_var = tk.StringVar(value=RUN3_DEFAULTS["ttc_min_speed_kmh"])
        self.run3_ttc_side_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["ttc_side_enabled"])
        self.run3_ttc_side_factor_var = tk.StringVar(value=RUN3_DEFAULTS["ttc_side_window_factor"])
        self.run3_ttc_side_margin_var = tk.StringVar(value=RUN3_DEFAULTS["ttc_side_margin_s"])
        self.run3_ttc_side_angle_var = tk.StringVar(value=RUN3_DEFAULTS["ttc_side_min_angle_deg"])
        self.run3_ttc_side_mode_var = tk.StringVar(value=RUN3_DEFAULTS["ttc_side_mode"])
        # V28: road geometry (lane widths per side + median)
        self.run3_geometry_vars = {
            key: tk.StringVar(value=RUN3_DEFAULTS[key]) for key in RUN3_GEOMETRY_KEYS
        }
        self.run3_w_entry_text = tk.StringVar(value="W_entry = -")
        self.run3_w_opp_text = tk.StringVar(value="W_opp = -")
        for _var in self.run3_geometry_vars.values():
            _var.trace_add("write", lambda *_: self._update_lane_totals())
        self.run3_ldp_smoothing_var = tk.StringVar(value=RUN3_DEFAULTS["ldp_smoothing_samples"])
        self.run3_gap_subject_134_var = tk.BooleanVar(value=RUN3_DEFAULTS["gap_subject_134"])
        self.run3_gap_subject_1367_var = tk.BooleanVar(value=RUN3_DEFAULTS["gap_subject_1367"])
        self.run3_gap_subject_5631_var = tk.BooleanVar(value=RUN3_DEFAULTS["gap_subject_5631"])
        self.run3_use_raff_var = tk.BooleanVar(value=RUN3_DEFAULTS["use_raff"])
        self.run3_use_mle_var = tk.BooleanVar(value=RUN3_DEFAULTS["use_mle"])
        self.run3_reference_mapping_text = RUN3_DEFAULTS["reference_line_mapping"]
        self.run3_width_vars = {
            name: tk.StringVar(value=RUN3_DEFAULTS["vehicle_widths"].get(name, ""))
            for name in RUN3_VEHICLE_CLASSES
        }
        self.run3_length_vars = {
            name: tk.StringVar(value=RUN3_DEFAULTS["vehicle_lengths"].get(name, ""))
            for name in RUN3_VEHICLE_CLASSES
        }
        self.run3_result_text = tk.StringVar(value="Run 3: not executed")
        # V27: plain-Python snapshots used by the worker thread.
        self._rt = None
        self._run3_cfg = None
        self.run3_last_outputs = {}
        self.run3_last_summary = {}
        self.run3_was_requested = False
        self._batch_mode = False
        self._last_run_error = ""
        self._carry = None

        self.status_var = tk.StringVar(
            value="Ready"
        )

        self.progress_var = tk.StringVar(
            value=""
        )

        self.hardware_var = tk.StringVar(
            value="Checking hardware..."
        )

        self.time_var = tk.StringVar(
            value=""
        )

        # Integrated Run 1 + Zone/Line measurement configuration.
        self.zone_line_config_var = tk.StringVar(value="")
        self.measurement_status_var = tk.StringVar(value="No PK Studio Zone file loaded")
        self.zone_source_video = ""
        self.zone_source_width = None
        self.zone_source_height = None
        self.zones = {name: [] for name in ZONE_NAMES}
        self.lines = {name: [] for name in LINE_NAMES}
        self.zone_meta = {}
        self.zone_file_format = None
        self.zone_scaled = []

    # ========================================================
    # GUI
    # ========================================================

    def build_gui(self):
        """Four steps in the order the work is done, a fixed run bar at the bottom.
          1 คลิปวิดีโอ   the clips (one or many), time range / recording per clip, output, what is drawn on the video
          2 ทางแยก       Zone file + Lines, which point decides the zone, road widths, metres calibration, vehicle sizes
          3 ตัวชี้วัด      the six indicators, each with its own switch and settings
          4 ตรวจจับและติดตาม  model, YOLO, device, tracker
        Every setting stays visible (grouped, not hidden); the variables and all run logic are unchanged."""
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        header = ttk.Frame(main)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="PK Studio", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="ตรวจจับและติดตามรถ แล้ววิเคราะห์ตัวชี้วัดความปลอดภัยจราจร (LDP · Lateral Clearance · Gap Acceptance · TTC · PET · Speed)",
                  foreground="#555555").grid(row=1, column=0, sticky="w")
        ttk.Button(header, text="โหลดการตั้งค่า", command=self.load_settings).grid(row=0, column=1, rowspan=2, padx=4)
        ttk.Button(header, text="บันทึกการตั้งค่า", command=self.save_settings).grid(row=0, column=2, rowspan=2, padx=4)

        self._page_canvases = []
        self.notebook = ttk.Notebook(main)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        for title, builder in (("① คลิปวิดีโอ", self.build_clips_tab), ("② ทางแยก", self.build_site_tab),
                               ("③ ตัวชี้วัด", self.build_indicator_tab), ("④ ตรวจจับและติดตาม", self.build_detect_tab)):
            outer, page = self._scroll_page()
            self.notebook.add(outer, text=title)
            self._page = page
            self._flow_row = 0
            builder()
        self.root.bind_all("<MouseWheel>", self.on_mousewheel)

        # ---------------- run bar (always visible) ----------------
        bottom = ttk.Frame(main)
        bottom.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        bottom.columnconfigure(0, weight=1)
        self.check_frame = ttk.Frame(bottom)
        self.check_frame.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))
        self.check_labels = {}
        for key in ("model", "clips", "zones", "lines", "widths", "output"):
            lab = ttk.Label(self.check_frame, text="")
            lab.pack(side="left", padx=(0, 14))
            self.check_labels[key] = lab
        ttk.Label(bottom, textvariable=self.status_var, anchor="w").grid(row=1, column=0, sticky="w")
        info = ttk.Frame(bottom)
        info.grid(row=2, column=0, sticky="w")
        ttk.Label(info, textvariable=self.progress_var).pack(side="left", padx=(0, 12))
        ttk.Label(info, textvariable=self.time_var).pack(side="left", padx=(0, 12))
        ttk.Label(info, textvariable=self.hardware_var, foreground="#666666").pack(side="left")
        self.pause_button = ttk.Button(bottom, text="Ⅱ PAUSE", command=self.toggle_pause, state="disabled")
        self.pause_button.grid(row=1, column=1, rowspan=2, padx=5, ipadx=10, ipady=6)
        self.start_button = ttk.Button(bottom, text="▶ เริ่มวิเคราะห์", command=self.start_analysis)
        self.start_button.grid(row=1, column=2, rowspan=2, padx=5, ipadx=15, ipady=6)
        self.stop_button = ttk.Button(bottom, text="■ STOP", command=self.request_stop, state="disabled")
        self.stop_button.grid(row=1, column=3, rowspan=2, padx=(5, 0), ipadx=12, ipady=6)
        self.refresh_checklist()

    # ---------------- helpers ----------------
    def _scroll_page(self):
        """A scrollable page for one tab -> (outer frame to add to the notebook, inner frame to fill)."""
        outer = ttk.Frame(self.notebook)
        canvas = tk.Canvas(outer, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, padding=(6, 6, 10, 16))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
        canvas.bind("<Configure>", lambda e, c=canvas, w=win: c.itemconfig(w, width=e.width))
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        inner.columnconfigure(0, weight=1)
        self._page_canvases.append(canvas)
        return outer, inner

    def on_mousewheel(self, event):
        try:
            canvas = self._page_canvases[self.notebook.index(self.notebook.select())]
        except (tk.TclError, IndexError, AttributeError):
            return
        if event.delta:
            canvas.yview_scroll(int(-event.delta / 120), "units")

    def section(self, title, column=0, row=0):
        """A titled group on the current page; groups are stacked top to bottom in the order they are built."""
        frame = ttk.LabelFrame(self._page, text=title, padding=10)
        frame.grid(row=self._flow_row, column=0, sticky="ew", padx=5, pady=5)
        self._flow_row += 1
        if getattr(self, "_stretch_entries", False):
            frame.columnconfigure(1, weight=1)       # long entries (paths, model) take the free width
        return frame

    def refresh_checklist(self):
        """The ready-to-run list above the START button (re-checked every second)."""
        try:
            green, orange, gray = "#0a7a3d", "#b45309", "#666666"
            zc = sorted(int(k) for k in self.run3_zone_calibrations if str(k).isdigit())
            self.run3_zone_cal_text.set(
                ("ปรับเทียบรายโซนแล้ว: " + ", ".join(f"Zone {z}" for z in zc) + " (ใช้แทนค่าฐานในโซนนั้น)") if zc else
                "ยังไม่มีการปรับเทียบรายโซน (ใช้ค่าฐานทั้งภาพ) — เปิดหน้าต่างปรับเทียบ แล้วเลือก \"ปรับเทียบสำหรับ\" ที่โซนที่ต้องการ")
            n_clips = len(self.clips_panel.clips) if getattr(self, "clips_panel", None) else 0
            zones = sum(1 for v in self.zones.values() if len(v) >= 3)
            lines = sum(1 for v in self.lines.values() if len(v) >= 2)

            def num(var):
                try:
                    return float(str(var.get()).strip()) > 0
                except Exception:
                    return False
            widths_needed = bool(self.run3_ldp_enabled_var.get())
            widths_ok = all(num(self.run3_geometry_vars[k]) for k in ("lane_entry_motorcycle_m", "lane_entry_car_m", "lane_opp_motorcycle_m", "lane_opp_car_m"))
            items = {
                "model": (os.path.isfile(self.model_var.get().strip()), "โมเดล"),
                "clips": (n_clips > 0, f"คลิป {n_clips}"),
                "zones": (zones >= 1, f"โซน {zones}/7"),
                "lines": (None if lines < 4 else True, f"Line {lines}/4 (ไม่บังคับ)"),
                "widths": ((widths_ok if widths_needed else None), "ความกว้างเลน" if widths_needed else "ความกว้างเลน (LDP ปิดอยู่)"),
                "output": (bool(self.output_var.get().strip()), "โฟลเดอร์ผลลัพธ์"),
            }
            for key, (ok, text) in items.items():
                mark, color = ("✔", green) if ok else (("–", gray) if ok is None else ("⚠", orange))
                self.check_labels[key].config(text=f"{mark} {text}", foreground=color)
            if not self.running:
                self.start_button.config(text=f"▶ เริ่มวิเคราะห์ ({n_clips} คลิป)" if n_clips else "▶ เริ่มวิเคราะห์")
            self.root.after(1000, self.refresh_checklist)
        except tk.TclError:
            pass          # window closed

    def start_analysis(self):
        """START: analyse every clip of the list (one clip = a list of one)."""
        clips = self.clips_panel.clips
        if not clips:
            self.notebook.select(0)
            messagebox.showinfo("เริ่มวิเคราะห์", "เพิ่มคลิปวิดีโอก่อน (ขั้น ① คลิปวิดีโอ → เลือกโฟลเดอร์ หรือ เพิ่มไฟล์วิดีโอ)")
            return
        out_root = self.output_var.get().strip()
        if not out_root:
            self.notebook.select(0)
            messagebox.showerror("เริ่มวิเคราะห์", "ระบุโฟลเดอร์ผลลัพธ์")
            return
        self.start_batch(clips, out_root, bool(self.clips_panel.skip_done_var.get()))

    # ---------------- tab 1: clips ----------------
    def build_clips_tab(self):
        box = self.section("คลิปที่จะวิเคราะห์")
        box.columnconfigure(0, weight=1)
        self.clips_panel = ClipListPanel(box, self)
        self.clips_panel.grid(row=0, column=0, sticky="nsew")

        box = self.section("การแสดงผลและไฟล์ที่บันทึก")
        box.columnconfigure(1, weight=0)
        gray = "#666666"

        def line(label, items, row):
            """label + a row of tick boxes (items = [(text, variable)])"""
            ttk.Label(box, text=label, width=22).grid(row=row, column=0, sticky="w", pady=3)
            fr = ttk.Frame(box)
            fr.grid(row=row, column=1, sticky="w")
            for text, var in items:
                ttk.Checkbutton(fr, text=text, variable=var).pack(side="left", padx=(0, 14))
            return fr

        line("ระหว่างรัน", [("Show Preview (เปิดหน้าต่างดูภาพ)", self.show_preview_var), ("Save CSV (Detection Records)", self.save_csv_var)], 0)
        fr = line("เส้นทางรถ", [("แสดงเส้นทาง (Trajectory)", self.draw_trail_var)], 1)
        ttk.Label(fr, text="ความยาว").pack(side="left", padx=(8, 4))
        ttk.Spinbox(fr, from_=1, to=300, textvariable=self.trail_length_var, width=6).pack(side="left")
        ttk.Separator(box, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 4))
        fr = line("Zone ที่วาดบนวิดีโอ", [("กรอบ Zone", self.show_zone_boundary_var), ("ชื่อ Zone", self.show_zone_label_var),
                                         ("แสดงคำว่า Zone", self.show_zone_label_prefix_var)], 3)
        ttk.Label(fr, text="ความจาง %").pack(side="left", padx=(8, 4))
        ttk.Spinbox(fr, from_=0, to=100, increment=5, textvariable=self.zone_overlay_opacity_var, width=6).pack(side="left")
        ttk.Label(fr, text="(0 = ไม่เห็น, 100 = ชัดสุด)", foreground=gray).pack(side="left", padx=(6, 0))
        line("จุดตัดสินโซน", [("แสดงจุดที่ใช้ตัดสินว่ารถอยู่โซนไหน (เหลือง = อยู่ในโซน, วงแดง = ไม่อยู่ในโซนใด)", self.draw_center_var)], 6)
        line("ป้ายบนตัวรถ", [("ID", self.show_label_id_var), ("Class", self.show_label_class_var), ("Conf", self.show_label_conf_var),
                             ("Zone", self.show_label_zone_var), ("Speed", self.show_label_speed_var), ("กรอบวัตถุ", self.show_bbox_var)], 4)
        line("ใส่ชื่อกำกับหน้าค่า", [("ID", self.show_prefix_id_var), ("Class", self.show_prefix_class_var), ("Conf", self.show_prefix_conf_var),
                                   ("Zone", self.show_prefix_zone_var), ("Speed", self.show_prefix_speed_var)], 5)

    # ---------------- tab 2: site ----------------
    def build_site_tab(self):
        gray = "#666666"
        box = self.section("ไฟล์โซนและเส้น (Zone 1–7, Line)")
        box.columnconfigure(1, weight=1)       # the path entry takes the free width
        ttk.Label(box, text="ไฟล์โซน").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(box, textvariable=self.zone_line_config_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(box, text="วาด Line…", command=self.open_line_editor).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(box, text="Browse", command=self.load_measurement_config).grid(row=0, column=3, padx=(5, 0))
        ttk.Label(box, textvariable=self.measurement_status_var, foreground=gray, anchor="w").grid(row=1, column=0, columnspan=4, sticky="w")

        box = self.section("จุดที่ใช้ตัดสินว่ารถอยู่โซนไหน")
        ttk.Label(box, text="ตำแหน่งบนกรอบรถ").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.trajectory_position_combo = ttk.Combobox(
            box, textvariable=self.trajectory_position_var, state="readonly", width=16,
            values=["Top", "Center", "Bottom", "Left", "Right", "Top Left", "Top Right", "Bottom Left", "Bottom Right"])
        self.trajectory_position_combo.grid(row=0, column=1, sticky="w", pady=4)
        ttk.Label(box, text="เลื่อนเข้าด้านใน %").grid(row=0, column=2, sticky="e", padx=(12, 4), pady=4)
        self.trajectory_offset_spin = ttk.Spinbox(box, from_=0, to=50, increment=1, textvariable=self.trajectory_offset_var, width=7)
        self.trajectory_offset_spin.grid(row=0, column=3, sticky="w", pady=4)
        ttk.Label(box, text="ใช้จุดเดียวบนกรอบรถตัดสินโซน (point-in-polygon); Center ไม่ใช้ค่าเลื่อน", foreground=gray).grid(row=1, column=0, columnspan=4, sticky="w")
        self.update_trajectory_position_controls()

        geo = self.section("ความกว้างถนน (m) — ใช้เป็นตัวหารของ LDP")
        ttk.Label(geo, text="ฝั่งทางเข้า–ออก (Zone 2-3-4)", foreground="#555555").grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(geo, text="เลนจักรยานยนต์").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(geo, textvariable=self.run3_geometry_vars["lane_entry_motorcycle_m"], width=8).grid(row=1, column=1, sticky="w", padx=(4, 16))
        ttk.Label(geo, text="เลนรถยนต์").grid(row=1, column=2, sticky="w")
        ttk.Entry(geo, textvariable=self.run3_geometry_vars["lane_entry_car_m"], width=8).grid(row=1, column=3, sticky="w", padx=(4, 16))
        ttk.Label(geo, textvariable=self.run3_w_entry_text, foreground="#0a5").grid(row=1, column=4, sticky="w")
        ttk.Label(geo, text="ฝั่งตรงข้ามทางเชื่อม (Zone 5-6-7)", foreground="#555555").grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))
        ttk.Label(geo, text="เลนจักรยานยนต์").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(geo, textvariable=self.run3_geometry_vars["lane_opp_motorcycle_m"], width=8).grid(row=3, column=1, sticky="w", padx=(4, 16))
        ttk.Label(geo, text="เลนรถยนต์").grid(row=3, column=2, sticky="w")
        ttk.Entry(geo, textvariable=self.run3_geometry_vars["lane_opp_car_m"], width=8).grid(row=3, column=3, sticky="w", padx=(4, 16))
        ttk.Label(geo, textvariable=self.run3_w_opp_text, foreground="#0a5").grid(row=3, column=4, sticky="w")
        ttk.Label(geo, text="ความกว้างเกาะกลาง (บันทึกไว้ ไม่ใช้คำนวณ)").grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 2))
        ttk.Entry(geo, textvariable=self.run3_geometry_vars["median_m"], width=8).grid(row=4, column=2, sticky="w", padx=(4, 16))
        self._update_lane_totals()

        cal = self.section("แปลงพิกัดภาพเป็นเมตร (PPM / Perspective)")
        for col in (1, 3):
            cal.columnconfigure(col, weight=1)
        r = 0
        ttk.Label(cal, text="Site_ID").grid(row=r, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(cal, textvariable=self.run3_site_id_var, width=18).grid(row=r, column=1, sticky="w", pady=4)
        ttk.Label(cal, text="PPM (พิกเซลต่อเมตร)").grid(row=r, column=2, sticky="e", padx=(12, 8), pady=4)
        ttk.Entry(cal, textvariable=self.run3_ppm_var, width=18).grid(row=r, column=3, sticky="w", pady=4)
        r += 1
        ttk.Label(cal, text="Road direction angle (deg) — ใช้เมื่อไม่มี Perspective").grid(row=r, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Entry(cal, textvariable=self.run3_lateral_axis_angle_var, width=18).grid(row=r, column=2, sticky="w", pady=4)
        r += 1
        lensf = ttk.LabelFrame(cal, text="เลนส์ fisheye (แก้ความโก่งของภาพกล้องมุมกว้างก่อนแปลงเป็นพื้นถนน — f = ความยาวโฟกัสเป็นเท่าของความกว้างภาพ เช่น 0.5 · เว้น f ว่าง = ไม่แก้)", padding=4)
        lensf.grid(row=r, column=0, columnspan=4, sticky="ew", pady=(6, 2))
        ttk.Label(lensf, text="f").pack(side="left")
        ttk.Entry(lensf, textvariable=self.run3_lens_f_var, width=6).pack(side="left", padx=(2, 8))
        ttk.Label(lensf, text="k1").pack(side="left")
        ttk.Entry(lensf, textvariable=self.run3_lens_k1_var, width=8).pack(side="left", padx=(2, 8))
        ttk.Label(lensf, text="k2").pack(side="left")
        ttk.Entry(lensf, textvariable=self.run3_lens_k2_var, width=8).pack(side="left", padx=(2, 8))
        ttk.Button(lensf, text="เลนส์ + เส้นถนน…", command=self.open_road_line_tool).pack(side="left", padx=4)
        ttk.Button(lensf, text="ดูภาพก่อน/หลัง", command=self.preview_lens_settings).pack(side="left", padx=4)
        ttk.Button(lensf, text="ล้าง", width=5, command=self.clear_lens_values).pack(side="left", padx=4)
        r += 1
        ttk.Checkbutton(cal, text="สร้างวิดีโอ Topview (Tracking_Topview.mp4)", variable=self.run3_topview_video_var).grid(row=r, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(cal, text="วาดจากพิกัดเมตรเดียวกับที่ตัวชี้วัดใช้ (ไฟล์ Detection_Records_Topview.csv เขียนทุกครั้ง)", foreground=gray).grid(row=r, column=2, columnspan=2, sticky="w", pady=2)
        r += 1
        roadf = ttk.Frame(cal)
        roadf.grid(row=r, column=0, columnspan=4, sticky="w", pady=2)
        ttk.Checkbutton(roadf, text="Topview แบบแผนที่ (กริดเปล่า + เส้นถนน ไม่ใช้ภาพกล้อง)", variable=self.run3_topview_map_var).pack(side="left")
        ttk.Button(roadf, text="เลนส์ + เส้นถนน…", command=self.open_road_line_tool).pack(side="left", padx=6)
        ttk.Button(roadf, text="ล้างเส้นถนน", command=self.clear_road_lines).pack(side="left", padx=2)
        self.road_lines_info_var = tk.StringVar(value="")
        ttk.Label(roadf, textvariable=self.road_lines_info_var, foreground=gray).pack(side="left", padx=6)
        self.run3_road_lines_var.trace_add("write", lambda *_: self._refresh_road_lines_info())
        self._refresh_road_lines_info()
        r += 1
        ttk.Checkbutton(cal, text="Perspective correction", variable=self.run3_perspective_enabled_var).grid(row=r, column=0, sticky="w", pady=(6, 4))
        ttk.Label(cal, text="ใช้เมื่อมีจุดอ้างอิงบนระนาบถนนที่ทราบระยะจริง (P1→P2 ต้องขนานแนวถนน)", foreground=gray).grid(row=r, column=1, columnspan=2, sticky="w", pady=(6, 4))
        ttk.Button(cal, text="🎯 Perspective / PPM Calibration", command=self.open_perspective_calibration).grid(row=r, column=3, sticky="e", pady=(6, 4))
        r += 1
        for (la, va, lb, vb) in (("P1", self.run3_perspective_p1_var, "P2", self.run3_perspective_p2_var),
                                 ("P3", self.run3_perspective_p3_var, "P4", self.run3_perspective_p4_var)):
            ttk.Label(cal, text=la).grid(row=r, column=0, sticky="e", padx=4, pady=2)
            ttk.Entry(cal, textvariable=va, width=18, state="readonly").grid(row=r, column=1, sticky="w", pady=2)
            ttk.Label(cal, text=lb).grid(row=r, column=2, sticky="e", padx=4, pady=2)
            ttk.Entry(cal, textvariable=vb, width=18, state="readonly").grid(row=r, column=3, sticky="w", pady=2)
            r += 1
        for (la, va, lb, vb) in (("ระยะจริง P1→P2 (m)", self.run3_perspective_l12_var, "ระยะจริง P2→P3 (m)", self.run3_perspective_l23_var),
                                 ("ระยะจริง P3→P4 (m)", self.run3_perspective_l34_var, "ระยะจริง P4→P1 (m)", self.run3_perspective_l41_var)):
            ttk.Label(cal, text=la).grid(row=r, column=0, sticky="w", padx=4, pady=2)
            ttk.Entry(cal, textvariable=va, width=18).grid(row=r, column=1, sticky="w", pady=2)
            ttk.Label(cal, text=lb).grid(row=r, column=2, sticky="e", padx=4, pady=2)
            ttk.Entry(cal, textvariable=vb, width=18).grid(row=r, column=3, sticky="w", pady=2)
            r += 1

        ttk.Label(cal, textvariable=self.run3_zone_cal_text, foreground="#0a7a3d").grid(row=r, column=0, columnspan=4, sticky="w", pady=(8, 0))

        dims = self.section("ขนาดรถ (m) — กว้าง W / ยาว L (ใช้กับ Lateral Clearance และ TTC)")
        ttk.Label(dims, text="ชนิด").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Label(dims, text="W").grid(row=1, column=0, sticky="w", padx=(0, 8))
        ttk.Label(dims, text="L").grid(row=2, column=0, sticky="w", padx=(0, 8))
        for i, name in enumerate(RUN3_VEHICLE_CLASSES, start=1):
            ttk.Label(dims, text=name).grid(row=0, column=i, sticky="w", padx=4)
            ttk.Entry(dims, textvariable=self.run3_width_vars[name], width=7).grid(row=1, column=i, sticky="w", padx=4, pady=1)
            ttk.Entry(dims, textvariable=self.run3_length_vars[name], width=7).grid(row=2, column=i, sticky="w", padx=4, pady=1)
        ttk.Label(dims, text="ค่าเริ่มต้นของโปรแกรม ควรตรวจกับแต่ละพื้นที่ (ไม่ใช่ค่าจากเอกสารอ้างอิง)", foreground=gray).grid(row=3, column=0, columnspan=9, sticky="w", pady=(6, 0))

    # ---------------- tab 3: indicators ----------------
    def _indicator_box(self, title, enabled_var, note=None):
        """A group per indicator; the tick in its title switches the indicator on or off."""
        label = ttk.Checkbutton(self._page, text=title, variable=enabled_var)
        box = ttk.LabelFrame(self._page, labelwidget=label, padding=10)
        box.grid(row=self._flow_row, column=0, sticky="ew", padx=5, pady=5)
        self._flow_row += 1
        for col in (1, 3, 5, 7):
            box.columnconfigure(col, weight=0)
        if note:
            ttk.Label(box, text=note, foreground="#555555", wraplength=900, justify="left").grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 4))
        return box

    @staticmethod
    def _zone_checks(box, var_map, row, label="โซนที่คำนวณ"):
        ttk.Label(box, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        for i, z in enumerate(sorted(var_map)):
            ttk.Checkbutton(box, text=f"Zone {z}", variable=var_map[z]).grid(row=row, column=1 + i, sticky="w", padx=(2, 10), pady=2)

    @staticmethod
    def _entry_row(box, row, label, var, width=8, col=0, span=5):
        ttk.Label(box, text=label).grid(row=row, column=col, columnspan=span, sticky="w", pady=2)
        ttk.Entry(box, textvariable=var, width=width).grid(row=row, column=col + span, sticky="w", pady=2, padx=(4, 0))

    def build_indicator_tab(self):
        gray = "#666666"
        ttk.Label(self._page, text="ติ๊กหน้าชื่อตัวชี้วัดเพื่อเปิด/ปิด — ค่าอื่นเป็นค่าเริ่มต้นที่ใช้ได้เลย ปรับเมื่อจำเป็น", foreground=gray).grid(row=self._flow_row, column=0, sticky="w", padx=6)
        self._flow_row += 1

        box = self._indicator_box("LDP", self.run3_ldp_enabled_var,
                                  "ΔY ÷ (W/2) × 100 — ΔY = ระยะตั้งฉากของเส้นทางรถจากเส้นอ้างอิง (จุดเข้า→จุดออกโซน) เฉพาะรถทางหลัก 2-3-4 (W_entry) และ 5-6-7 (W_opp) ทุกประเภทรถ")
        self._zone_checks(box, self.run3_ldp_zone_vars, 1)
        self._entry_row(box, 2, "Median smoothing (จำนวนตัวอย่าง, 1 = ปิด)", self.run3_ldp_smoothing_var)

        box = self._indicator_box("Lateral Clearance", self.run3_lc_enabled_var,
                                  "คู่รถทิศทางเดียวกันในโซนเดียวกัน วัดตั้งฉากกับทิศที่รถ A เคลื่อนที่เมื่อกรอบรถซ้อนกันตามแนวยาว (ถ้ามีจักรยานยนต์ในคู่ จักรยานยนต์คือ A)")
        self._zone_checks(box, self.run3_lc_zone_vars, 1)
        ttk.Checkbutton(box, text="เฉพาะคู่ที่มีรถจักรยานยนต์ (ไม่ติ๊ก = ทุกคู่ของยานพาหนะทุกประเภท)", variable=self.run3_lc_motorcycle_pairs_only_var).grid(row=2, column=0, columnspan=8, sticky="w", pady=2)
        self._entry_row(box, 3, "หน้าต่างหาทิศ heading ของรถ A (s)", self.run3_lc_heading_window_var)
        self._entry_row(box, 4, "ช่วงเคียงข้างตามแนวยาว ±(m) — 0 = อัตโนมัติ (L_A+L_B)/2", self.run3_lc_along_limit_var)
        self._entry_row(box, 5, "ระยะด้านข้างไกลสุดที่ถือว่าเกี่ยวข้องกัน (m) — 0 = ไม่จำกัด", self.run3_lc_max_lateral_var)

        box = self._indicator_box("Gap Acceptance", self.run3_gap_enabled_var,
                                  "รถที่รอ (ดูกระแสที่ต้องให้ทางตามตาราง) ยอมรับ/ปฏิเสธช่องว่างสองขั้น Access/Exit; Line เป็นตัวเลือก (ไม่มี Line ใช้เวลาเข้าโซนต้นทางของกระแสนั้น)")
        ttk.Label(box, text="รถที่รอ (Movement)").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Checkbutton(box, text="1-3-4", variable=self.run3_gap_subject_134_var).grid(row=1, column=1, sticky="w")
        ttk.Checkbutton(box, text="1-3-6-7", variable=self.run3_gap_subject_1367_var).grid(row=1, column=2, sticky="w")
        ttk.Checkbutton(box, text="5-6-3-1", variable=self.run3_gap_subject_5631_var).grid(row=1, column=3, sticky="w")
        self._entry_row(box, 2, "ถือว่ารถ \"หยุด\" กลางแยกเมื่อความเร็ว ≤ (km/h)", self.run3_waiting_speed_threshold_var)
        self._entry_row(box, 3, "... นานอย่างน้อย (s)", self.run3_hold_min_duration_var)
        ttk.Label(box, text="Critical Gap").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Checkbutton(box, text="Raff", variable=self.run3_use_raff_var).grid(row=4, column=1, sticky="w")
        ttk.Checkbutton(box, text="MLE", variable=self.run3_use_mle_var).grid(row=4, column=2, sticky="w")
        ttk.Label(box, text="Reference Line Mapping (Site_ID|Movement|Line N) — เติมให้เองเมื่อกด \"วาด Line…\"").grid(row=5, column=0, columnspan=6, sticky="w", pady=(6, 2))
        ttk.Button(box, text="Copy Template", command=self.copy_run3_mapping_template).grid(row=5, column=6, columnspan=2, sticky="e", pady=(6, 2))
        self.run3_reference_text = tk.Text(box, height=5, width=80, wrap="none")
        self.run3_reference_text.grid(row=6, column=0, columnspan=8, sticky="ew", pady=(0, 2))
        self.run3_reference_text.insert("1.0", self.run3_reference_mapping_text)

        box = self._indicator_box("TTC", self.run3_ttc_enabled_var,
                                  "ชนท้าย: TTC = S / CS   |   ชนด้านข้าง: เวลาถึงจุดตัดของเส้นทางสองคัน (ระยะทางถึงจุดตัด ÷ ความเร็ว) ชนเมื่อเวลาถึงต่างกันไม่เกินเวลาที่ตัวรถใช้พ้นจุดตัด")
        self._zone_checks(box, self.run3_ttc_zone_vars, 1)
        for i, (label, var) in enumerate((("บันทึกเมื่อ TTCmin ≤ (s)", self.run3_ttc_max_record_var),
                                          ("ชนท้าย: มุมทิศทางต่างกันไม่เกิน (deg)", self.run3_ttc_heading_max_var),
                                          ("หน้าต่างคำนวณความเร็ว (s)", self.run3_ttc_velocity_window_var),
                                          ("ความเร็วรถตามขั้นต่ำ (km/h)", self.run3_ttc_min_speed_var))):
            self._entry_row(box, 2 + i, label, var)
        ttk.Checkbutton(box, text="คำนวณ TTC ชนด้านข้าง", variable=self.run3_ttc_side_enabled_var).grid(row=6, column=0, columnspan=4, sticky="w", pady=(6, 2))
        for i, (label, var) in enumerate((("ตัวคูณหน้าต่างเวลาถึงจุดตัด (× เวลาที่ตัวรถพ้นจุดตัด, 0 = ไม่คิดความยาวรถ)", self.run3_ttc_side_factor_var),
                                          ("เวลาเผื่อเพิ่ม (s)", self.run3_ttc_side_margin_var),
                                          ("มุมระหว่างเส้นทางอย่างน้อย (deg)", self.run3_ttc_side_angle_var))):
            self._entry_row(box, 7 + i, label, var, span=7)
        ttk.Label(box, text="TTC ด้านข้าง =").grid(row=10, column=0, sticky="w", pady=2)
        ttk.Combobox(box, textvariable=self.run3_ttc_side_mode_var, state="readonly", width=20,
                     values=["Earlier arrival", "Later arrival", "Average of arrivals"]).grid(row=10, column=1, columnspan=3, sticky="w", pady=2)

        box = self._indicator_box("PET", self.run3_pet_enabled_var, "PET คำนวณแยกในแต่ละ Conflict Zone (Zone 3 / Zone 6)")
        self._zone_checks(box, self.run3_pet_zone_vars, 1, "Conflict Zone")
        for i, (label, var) in enumerate((("Interaction distance (m)", self.run3_pet_interaction_distance_var),
                                          ("PET threshold (s)", self.run3_pet_threshold_var),
                                          ("PET max (s) — ว่าง = ไม่จำกัด", self.run3_pet_max_var))):
            self._entry_row(box, 2 + i, label, var)

        box = self._indicator_box("Speed (V50, V85, Mean, SD)", self.run3_speed_enabled_var,
                                  "ความเร็วต่อโซน + ความเร็วภาพรวมตาม Movement (เช่น 2-3-4) — ความยาวเส้นทางเมตร ÷ เวลา")
        self._zone_checks(box, self.run3_speed_zone_vars, 1)
        self._entry_row(box, 2, "Median smoothing (จำนวนตัวอย่าง, 1 = ปิด)", self.run3_speed_smoothing_var)
        self._entry_row(box, 3, "ความเร็วสูงสุดที่สมเหตุสมผล (km/h, 0 = ปิด) — เกินนี้ติดธง ไม่นับในสถิติ", self.run3_speed_max_var, span=6)

        ttk.Label(self._page, textvariable=self.run3_result_text, foreground="#444444").grid(row=self._flow_row, column=0, sticky="w", padx=6, pady=(4, 0))
        self._flow_row += 1

    # ---------------- tab 4: detection and tracking ----------------
    def build_detect_tab(self):
        self._stretch_entries = True
        box = self.section("โมเดล")
        self.add_entry(box, 0, "ไฟล์โมเดล (.pt)", self.model_var, self.browse_model)
        self.build_detection_section()
        self.build_processing_section()
        self.build_bytetrack_section()

    # ========================================================
    # INTEGRATED ZONE / LINE MEASUREMENT
    # ========================================================

    def _update_lane_totals(self):
        """Show W_entry / W_opp (= motorcycle lane + car lane of each side)."""
        def total(a, b):
            try:
                x = float(self.run3_geometry_vars[a].get().strip())
                y = float(self.run3_geometry_vars[b].get().strip())
                return f"{x + y:.3f} m"
            except Exception:
                return "-"
        self.run3_w_entry_text.set("W_entry = " + total("lane_entry_motorcycle_m", "lane_entry_car_m"))
        self.run3_w_opp_text.set("W_opp = " + total("lane_opp_motorcycle_m", "lane_opp_car_m"))

    def update_trajectory_position_controls(self, event=None):
        """Update the trajectory-position controls.

        All nine anchor positions use the same inward Offset (%).
        Center ignores Offset because it is already centered.
        """
        return

    def refresh_measurement_status(self):
        z = sum(1 for v in self.zones.values() if len(v) >= 3)
        l = sum(1 for v in self.lines.values() if len(v) >= 2)
        source = os.path.basename(self.zone_line_config_var.get().strip()) if self.zone_line_config_var.get().strip() else "None"
        self.measurement_status_var.set(
            f"PK Studio: {source} | Zones loaded: {z} | Lines loaded: {l} | "
            f"Zone metrics: entry/exit/duration/distance/speed"
        )

    @staticmethod
    def _normalize_zone_item(item, fallback_name=None):
        """Convert one PK Studio zone record to a common internal format."""
        if not isinstance(item, dict):
            return None

        name = str(item.get("name", fallback_name or "")).strip()
        if not name:
            zone_id = item.get("id")
            name = f"Zone {zone_id}" if zone_id is not None else ""

        points = item.get("points") or []
        points_norm = item.get("points_norm") or []

        def clean_points(raw):
            result = []
            for point in raw:
                try:
                    if len(point) >= 2:
                        result.append((float(point[0]), float(point[1])))
                except Exception:
                    continue
            return result

        return {
            "id": item.get("id"),
            "name": name,
            "points": clean_points(points),
            "points_norm": clean_points(points_norm),
            "color_bgr": item.get("color_bgr", [0, 255, 0]),
            "show_label": bool(item.get("show_label", True)),
            "area_px": item.get("area_px"),
            "reference_frame_index": item.get("reference_frame_index"),
        }

    def _actual_video_size(self):
        video = self.video_var.get().strip()
        if not video or not os.path.isfile(video):
            return None, None
        cap = cv2.VideoCapture(video)
        try:
            if not cap.isOpened():
                return None, None
            return int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        finally:
            cap.release()

    def _prepare_zone_points(self, zone, source_width, source_height):
        """Use pixel points when resolutions match; otherwise use points_norm."""
        actual_w, actual_h = self._actual_video_size()
        if not actual_w or not actual_h:
            actual_w = source_width
            actual_h = source_height

        points = zone.get("points", [])
        points_norm = zone.get("points_norm", [])

        if source_width and source_height and (actual_w != source_width or actual_h != source_height):
            if points_norm and actual_w and actual_h:
                # PK Studio normalized coordinates are expected in [0, 1].
                prepared = [(x * actual_w, y * actual_h) for x, y in points_norm]
                return [(int(round(x)), int(round(y))) for x, y in prepared], True
            if points and source_width and source_height:
                # Fallback for older exports without points_norm.
                sx = actual_w / float(source_width)
                sy = actual_h / float(source_height)
                prepared = [(x * sx, y * sy) for x, y in points]
                return [(int(round(x)), int(round(y))) for x, y in prepared], True

        return [(int(round(x)), int(round(y))) for x, y in points], False

    def _load_pkstudio_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("The selected JSON file must contain an object at the top level.")

        raw_zones = data.get("zones")
        if not isinstance(raw_zones, list):
            # Compatibility with the older integrated JSON structure.
            legacy = data.get("zones", {})
            if isinstance(legacy, dict):
                raw_zones = []
                for name, points in legacy.items():
                    raw_zones.append({"name": name, "points": points})
            else:
                raise ValueError("The JSON file does not contain a valid 'zones' list.")

        source_width = data.get("frame_width")
        source_height = data.get("frame_height")
        try:
            source_width = int(source_width) if source_width is not None else None
            source_height = int(source_height) if source_height is not None else None
        except Exception:
            source_width = source_height = None

        zones = {name: [] for name in ZONE_NAMES}
        zone_meta = {}
        loaded = []
        scaled = []

        for raw in raw_zones:
            zone = self._normalize_zone_item(raw)
            if not zone:
                continue
            name = zone["name"]
            if name not in zones:
                # Accept numeric IDs even if the name was omitted/different.
                zid = zone.get("id")
                if zid is not None and f"Zone {zid}" in zones:
                    name = f"Zone {zid}"
                    zone["name"] = name
            if name not in zones:
                continue

            pts, was_scaled = self._prepare_zone_points(zone, source_width, source_height)
            if len(pts) >= 3:
                zones[name] = pts
                zone_meta[name] = zone
                loaded.append(name)
                if was_scaled:
                    scaled.append(name)

        if not loaded:
            raise ValueError("No valid Zone 1-7 definitions were found in the selected PK Studio file.")

        # Lines (optional): {"Line 1": [[x, y], [x, y]], ...}. They are in the frame size
        # given by lines_frame_width/height (written by the Line editor); otherwise in the
        # Zone file frame size. They are scaled to the real video size like the Zones.
        lines = {name: [] for name in LINE_NAMES}
        raw_lines = data.get("lines", {})
        if isinstance(raw_lines, dict):
            try:
                lines_w = int(data.get("lines_frame_width") or source_width or 0) or None
                lines_h = int(data.get("lines_frame_height") or source_height or 0) or None
            except Exception:
                lines_w = lines_h = None
            actual_w, actual_h = self._actual_video_size()
            for name, pts in raw_lines.items():
                if name in lines and isinstance(pts, list):
                    cleaned = []
                    for p in pts:
                        try:
                            cleaned.append((int(p[0]), int(p[1])))
                        except Exception:
                            pass
                    if len(cleaned) == 2:
                        lines[name] = scale_points(cleaned, lines_w, lines_h, actual_w, actual_h)

        self.zones = zones
        self.lines = lines
        self.zone_line_config_var.set(path)
        self.zone_source_video = str(data.get("video_path", ""))
        self.zone_source_width = source_width
        self.zone_source_height = source_height
        self.zone_meta = zone_meta
        self.zone_file_format = "JSON"
        self.zone_scaled = scaled

        self.refresh_measurement_status()

        status = f"Loaded {len(loaded)} zones from PK Studio JSON"
        if scaled:
            status += f" | Rescaled: {', '.join(scaled)}"
        self.status_var.set(status)

        # The JSON can contain a source video path. It is informational only;
        # the video selected in Run 1 remains the actual processing input.
        selected_video = self.video_var.get().strip()
        source_video = self.zone_source_video.strip()
        if source_video and selected_video:
            if os.path.basename(source_video).lower() != os.path.basename(selected_video).lower():
                self.measurement_status_var.set(
                    self.measurement_status_var.get()
                    + " | Warning: JSON video name differs from selected video"
                )

        return True

    def _load_pkstudio_python(self, path):
        spec = importlib.util.spec_from_file_location("pkstudio_zone_export", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load the PK Studio Zone Python file.")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        raw_zones = getattr(module, "ZONES", None)
        if not isinstance(raw_zones, list):
            raise ValueError("The selected Python file does not contain a valid ZONES list exported by PK Studio.")

        zones = {name: [] for name in ZONE_NAMES}
        meta = {}
        loaded = []

        for raw in raw_zones:
            zone = self._normalize_zone_item(raw)
            if not zone:
                continue
            name = zone["name"]
            zid = zone.get("id")
            if name not in zones and zid is not None and f"Zone {zid}" in zones:
                name = f"Zone {zid}"
                zone["name"] = name
            if name not in zones:
                continue
            if len(zone["points"]) >= 3:
                zones[name] = [(int(round(x)), int(round(y))) for x, y in zone["points"]]
                meta[name] = zone
                loaded.append(name)

        if not loaded:
            raise ValueError("No Zone 1-7 definitions were found in the PK Studio Python export.")

        lines = {name: [] for name in LINE_NAMES}
        raw_lines = getattr(module, "LINES", {})
        if isinstance(raw_lines, dict):
            for name, pts in raw_lines.items():
                if name in lines and isinstance(pts, list) and len(pts) == 2:
                    try:
                        lines[name] = [tuple(map(int, p[:2])) for p in pts]
                    except Exception:
                        pass

        self.zones = zones
        self.lines = lines
        self.zone_line_config_var.set(path)
        self.zone_source_video = str(getattr(module, "VIDEO", ""))
        self.zone_source_width = getattr(module, "FRAME_WIDTH", None)
        self.zone_source_height = getattr(module, "FRAME_HEIGHT", None)
        self.zone_meta = meta
        self.zone_file_format = "PY"
        self.zone_scaled = []
        self.refresh_measurement_status()
        self.status_var.set(f"Loaded {len(loaded)} zones from PK Studio Python")
        return True

    def load_pkstudio_zones(self):
        """Load either the current PK Studio JSON export or the older Python export."""
        path = self.zone_line_config_var.get().strip()
        if not path or not os.path.isfile(path):
            path = filedialog.askopenfilename(
                title="Load PK Studio Zone File",
                filetypes=[
                    ("PK Studio Zone files", "*.json *.py"),
                    ("JSON files", "*.json"),
                    ("Python files", "*.py"),
                    ("All files", "*.*")
                ]
            )
        if not path:
            return False

        try:
            if path.lower().endswith(".json"):
                ok = self._load_pkstudio_json(path)
            elif path.lower().endswith(".py"):
                ok = self._load_pkstudio_python(path)
            else:
                raise ValueError("Zone file must be .json or .py")

            if ok:
                self.validate_measurements()
            return bool(ok)

        except Exception as exc:
            messagebox.showerror("PK Studio Zone Load Error", str(exc))
            return False

    def load_measurement_config(self):
        return self.load_pkstudio_zones()

    # ========================================================
    # LINE EDITOR (Reference Lines for Gap Acceptance)
    # ========================================================

    # ========================================================
    # BATCH (many clips: time range + recording per clip, mirrored output folders)
    # ========================================================

    def start_batch(self, clips, out_root, skip_done):
        """Validate like START RUN, then run all clips one after another in a worker thread.
        Returns True when the batch was started."""
        if self.running:
            return False
        if not clips:
            messagebox.showerror("Batch", "ยังไม่ได้เลือกคลิป")
            return False
        for c in clips:
            if not os.path.isfile(c["video"]):
                messagebox.showerror("Batch", "ไม่พบไฟล์วิดีโอ\n\n" + c["video"])
                return False
            try:
                for key in ("analysis_start_s", "analysis_end_s", "record_start_s", "record_end_s"):
                    parse_clock_time(c.get(key, ""))
            except ValueError as exc:
                messagebox.showerror("Batch", f"{os.path.basename(c['video'])}: {exc}")
                return False
        clash = _tools_module("batch_run").duplicate_run_dirs(
            out_root, [(c["video"], str(c.get("rel_dir", "") or ""), {}) for c in clips])
        if clash:
            messagebox.showerror("Batch", "มีคลิปสองไฟล์ที่ได้โฟลเดอร์ผลลัพธ์ชื่อเดียวกัน (ชื่อไฟล์เหมือนกันต่างนามสกุล?)\n\n" + "\n".join(clash[:5]))
            return False
        self.video_var.set(clips[0]["video"])      # validate_settings wants an existing video
        try:
            self.validate_measurements()
            self.validate_run3_settings()
        except Exception as exc:
            messagebox.showerror("Run 3 / Measurement Configuration", str(exc))
            return False
        if not self.validate_settings():
            return False
        try:
            selected_device = self.resolve_device()
        except Exception as e:
            if self.offer_restart_with_cuda_python(str(e)):
                return False
            messagebox.showerror("CUDA / Device Error", str(e))
            return False
        self._run3_warnings = self.collect_run3_warnings()
        if self._run3_warnings:
            text = "\n\n".join(f"• {w}" for w in self._run3_warnings)
            if not messagebox.askokcancel("Run 3 pre-flight warnings", text + "\n\nContinue anyway?", icon="warning"):
                return False
        settings = self.get_settings()
        self._rt = self._runtime_snapshot(settings)
        self._run3_cfg = self._run3_snapshot_config()
        self._zone_poly_cache = None
        self._overlay_cache = None
        self.running = True
        self._batch_mode = True
        self._last_run_error = ""
        self.stop_event.clear()
        self.pause_event.set()
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal", text="Ⅱ PAUSE")
        self.stop_button.config(state="normal")
        self.status_var.set(f"Starting Batch ({len(clips)} clips) | Device = {selected_device}")
        self.progress_var.set("")
        self.time_var.set("")
        self.worker_thread = threading.Thread(
            target=self._batch_worker, args=(settings, [dict(c) for c in clips], out_root, skip_done), daemon=True)
        self.worker_thread.start()
        return True

    def _batch_worker(self, base_settings, clips, out_root, skip_done):
        bt = _tools_module("batch_run")
        rows, runs, empties = [], [], []
        stopped = False
        fatal = ""
        n = len(clips)
        self._carry = None
        try:
            os.makedirs(out_root, exist_ok=True)
            for i, c in enumerate(clips, 1):
                rel = str(c.get("rel_dir", "") or "")
                runs.append((c["video"], rel, {}))
                if self.stop_event.is_set():
                    stopped = True
                    break
                st, name, run_dir = bt.clip_settings(base_settings, c["video"], rel, {}, out_root, c, c.get("save_video", False),
                                                     show_preview=bool(base_settings.get("show_preview")))
                st["continue_tracker"] = bool(c.get("continues_previous")) and i > 1
                os.makedirs(run_dir, exist_ok=True)
                if skip_done and bt.summary_path(run_dir, name) is not None:
                    self._carry = None          # nothing was run, so there is no tracker to continue
                    rows.append(bt.collect_row(run_dir, name, c["video"], rel, {}, "", 0.0))
                    self.update_ui(status=f"Batch {i}/{n}: {name} — already done, skipped")
                    continue
                self.update_ui(status=f"Batch {i}/{n}: {name}")
                self._last_run_error = ""
                self.run3_last_summary = None
                t0 = time.time()
                self.run_processing(st)
                reasons = ((self.run3_last_summary or {}).get("diagnostics", {}) or {}).get("empty_outputs", []) or []
                if reasons:
                    empties.append((name, list(reasons)))
                rows.append(bt.collect_row(run_dir, name, c["video"], rel, {}, self._last_run_error, time.time() - t0))
                if self.stop_event.is_set():
                    stopped = True
                    break
            bt.finish_batch(out_root, runs, rows, log=lambda m: print(m))
        except Exception as exc:
            log.exception("Batch failed")
            fatal = str(exc)
        self.post_ui(lambda: self.finish_batch_ui(rows, n, out_root, stopped, fatal, empties))

    def finish_batch_ui(self, rows, total, out_root, stopped, fatal, empties=()):
        self.running = False
        self._batch_mode = False
        self._rt = None
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Ⅱ PAUSE")
        self.stop_button.config(state="disabled")
        ok = [r for r in rows if str(r["Status"]).startswith(("completed", "stopped"))]
        bad = [r for r in rows if str(r["Status"]).startswith("ERROR") or r["Status"] == "no summary"]
        self.status_var.set(f"Batch finished: {len(ok)}/{total} clips" + (" (stopped)" if stopped else ""))
        self.progress_var.set("100%" if not stopped else "")
        msg = f"Batch {'หยุดกลางทาง' if stopped else 'เสร็จ'}: {len(ok)} จาก {total} คลิป\n\nผลลัพธ์:\n{out_root}\n\n"
        msg += "• โฟลเดอร์ของแต่ละคลิป (ตามโครงสร้างต้นฉบับ) = CSV ของคลิปนั้น (ชื่อไฟล์ขึ้นต้นด้วยชื่อคลิป)\n• All_Clips (ในโฟลเดอร์ชั้นบนสุดที่นำเข้า) = CSV รวมทุกคลิป มีคอลัมน์ Clip บอกว่าแถวมาจากคลิปไหน (รวมคลิปรอบก่อน ๆ ที่อยู่ในโฟลเดอร์เดียวกัน)\n• Batch_Comparison.csv = ตารางเปรียบเทียบทุกคลิปในโฟลเดอร์ผลลัพธ์"
        if bad:
            msg += "\n\nคลิปที่มีปัญหา:\n" + "\n".join(f"- {r['Run']}: {r['Status']}" for r in bad)
        if empties:
            msg += "\n\nตัวชี้วัดที่ไม่มีข้อมูล (ไฟล์ CSV มีแต่หัวแถว) และสาเหตุ:"
            for clip_name, reasons in empties[:3]:
                msg += f"\n\n[{clip_name}]\n" + "\n".join("• " + r for r in reasons)
            if len(empties) > 3:
                msg += f"\n\n… และอีก {len(empties) - 3} คลิป (ดูใน <ชื่อคลิป>_Summary.json → diagnostics.empty_outputs ของแต่ละคลิป)"
        if fatal:
            msg += "\n\nข้อผิดพลาด: " + fatal
        messagebox.showinfo("PK Studio Batch", msg)

    def open_line_editor(self):
        """Open the dialog that draws the Reference Lines on a frame of the video."""
        video = self.video_var.get().strip()
        if not video or not os.path.isfile(video):
            messagebox.showerror("วาด Line", "เลือกไฟล์วิดีโอ (Video) ก่อน — Line วาดบนเฟรมของวิดีโอ")
            return None
        if not any(len(v) >= 3 for v in self.zones.values()):
            if not messagebox.askyesno("วาด Line", "ยังไม่ได้โหลดไฟล์ Zone (Line จะถูกบันทึกลงไฟล์ Zone)\n\nโหลดไฟล์ Zone ตอนนี้หรือไม่?"):
                return None
            if not self.load_pkstudio_zones():
                return None
        cap = cv2.VideoCapture(video)
        try:
            ok, frame = cap.read()
        finally:
            cap.release()
        if not ok or frame is None:
            messagebox.showerror("วาด Line", "อ่านเฟรมจากวิดีโอไม่ได้")
            return None
        movements = []
        for streams in RUN3_GAP_CONFLICT_MAP.values():
            for mv in streams:
                if mv not in movements:
                    movements.append(mv)
        site = self.run3_site_id_var.get().strip()
        text = self.run3_reference_text.get("1.0", "end-1c") if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text
        try:
            existing = {mv: ln for (st, mv), ln in self._run3_parse_reference_mapping(text).items() if st == site}
        except Exception:
            existing = {}
        assignments = {}
        used = set()
        for mv in movements:
            if existing.get(mv) in LINE_NAMES:
                assignments[mv] = existing[mv]
                used.add(existing[mv])
        free = [ln for ln in LINE_NAMES if ln not in used]
        for mv in movements:
            if mv not in assignments:
                assignments[mv] = free.pop(0)
        self.line_editor = LineEditorDialog(self, frame, 0, movements, assignments, self.lines)
        return self.line_editor

    def apply_editor_lines(self, lines_by_name, assignments, frame_w, frame_h):
        """Store the drawn Lines, write them into the Zone JSON and fill the mapping text."""
        try:
            path = self.zone_line_config_var.get().strip()
            if path.lower().endswith(".json") and os.path.isfile(path):
                if not messagebox.askyesno(
                        "บันทึก Line",
                        f"เพิ่ม Line ลงในไฟล์ Zone:\n{path}\n\n(ไฟล์เดิมจะสำรองไว้เป็น .bak ครั้งแรก) ตกลงหรือไม่?"):
                    return False
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not os.path.isfile(path + ".bak"):
                    shutil.copyfile(path, path + ".bak")
            else:
                new_path = filedialog.asksaveasfilename(
                    title="บันทึกโซน + Line เป็นไฟล์ JSON ใหม่", defaultextension=".json",
                    filetypes=[("JSON files", "*.json")],
                    initialfile=(os.path.splitext(os.path.basename(path))[0] if path else "zones") + "_with_lines.json")
                if not new_path:
                    return False
                path = new_path
                zones = []
                for index, name in enumerate(ZONE_NAMES, start=1):
                    pts = self.zones.get(name, [])
                    if len(pts) >= 3:
                        zones.append({"id": index, "name": name, "points": [list(q) for q in pts]})
                data = {"video_path": self.video_var.get().strip(),
                        "frame_width": self.zone_source_width or frame_w,
                        "frame_height": self.zone_source_height or frame_h,
                        "zones": zones}
            saved = data.get("lines") if isinstance(data.get("lines"), dict) else {}
            for name, pts in lines_by_name.items():
                saved[name] = [list(q) for q in pts]
            data["lines"] = saved
            data["lines_frame_width"] = frame_w
            data["lines_frame_height"] = frame_h
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as exc:
            messagebox.showerror("บันทึก Line", f"บันทึกไม่สำเร็จ:\n{exc}")
            return False

        for name, pts in lines_by_name.items():
            self.lines[name] = [tuple(q) for q in pts]
        self.zone_line_config_var.set(path)
        site = self.run3_site_id_var.get().strip()
        old = self.run3_reference_text.get("1.0", "end-1c") if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text
        new_text = update_reference_mapping_text(old, site, assignments)
        self.run3_reference_mapping_text = new_text
        if hasattr(self, "run3_reference_text"):
            self.run3_reference_text.delete("1.0", "end")
            self.run3_reference_text.insert("1.0", new_text)
        self.refresh_measurement_status()
        self.status_var.set(f"บันทึก {len(lines_by_name)} Line ลง {os.path.basename(path)} และเติม Reference Line Mapping แล้ว")
        return True

    def save_measurement_config(self):
        # Save the currently loaded geometry as a normalized JSON snapshot.
        path = filedialog.asksaveasfilename(
            title="Save Zone Configuration Snapshot",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="Run_1_Zone_Config_Used.json"
        )
        if not path:
            return

        zones = []
        for index, name in enumerate(ZONE_NAMES, start=1):
            points = self.zones.get(name, [])
            if len(points) < 3:
                continue
            meta = getattr(self, "zone_meta", {}).get(name, {})
            zones.append({
                "id": meta.get("id", index),
                "name": name,
                "points": [list(p) for p in points],
                "color_bgr": meta.get("color_bgr", [0, 255, 0]),
                "show_label": meta.get("show_label", True),
                "area_px": meta.get("area_px"),
                "reference_frame_index": meta.get("reference_frame_index"),
            })

        data = {
            "video_path": self.zone_source_video,
            "frame_width": self.zone_source_width,
            "frame_height": self.zone_source_height,
            "zones": zones,
            "source_format": getattr(self, "zone_file_format", None),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        self.status_var.set("Zone configuration snapshot saved")

    def draw_measurement_overlay(self, frame, frame_index, fps, zone_track_state, line_track_state, zone_entry_count, line_cross_count):
        """Draw optional, faint Zone boundaries and labels.

        Zone fill/background is never drawn. The user can independently toggle
        the Zone boundary and Zone label. Label text can be shown as either
        ``Zone 6`` or simply ``6``. Both are blended onto the original frame
        so they remain visually faint without a solid background rectangle.
        """
        rt = self._rt if (self.running and self._rt) else None
        if rt is not None:
            opacity = rt["zone_opacity"]
            show_boundary = rt["show_zone_boundary"]
            show_label = rt["show_zone_label"]
            label_prefix = rt["show_zone_label_prefix"]
        else:
            try:
                opacity = max(0.0, min(1.0, float(self.zone_overlay_opacity_var.get()) / 100.0))
            except Exception:
                opacity = 0.45
            show_boundary = bool(self.show_zone_boundary_var.get())
            show_label = bool(self.show_zone_label_var.get())
            label_prefix = bool(self.show_zone_label_prefix_var.get())

        # V27: the faint Zone layer is static, so it is rendered once and
        # only its non-empty pixels are blended on each frame (V26 copied and
        # blended the full frame every frame).
        if (show_boundary or show_label) and opacity <= 0.0:
            show_boundary = show_label = False   # nothing visible to draw
        if show_boundary or show_label:
            key = (frame.shape, opacity, show_boundary, show_label, label_prefix,
                   tuple((z, tuple(map(tuple, self.zones.get(z, [])))) for z in ZONE_NAMES))
            cache = getattr(self, "_overlay_cache", None)
            if cache is None or cache[0] != key:
                layer = np.zeros_like(frame)
                self._draw_zone_layer(layer, show_boundary, show_label, label_prefix)
                cover = np.zeros(frame.shape[:2], dtype=np.uint8)
                self._draw_zone_layer(cover, show_boundary, show_label, label_prefix, mono=True)
                idx = np.nonzero(cover)
                alpha = (cover[idx].astype(np.float32) / 255.0 * opacity)[:, None]
                cache = (key, idx, alpha, layer[idx].astype(np.float32) * opacity)
                self._overlay_cache = cache
            _, idx, alpha, colored = cache
            if len(idx[0]):
                px = frame[idx].astype(np.float32)
                frame[idx] = np.clip(px * (1.0 - alpha) + colored, 0, 255).astype(np.uint8)
            show_boundary = show_label = False   # skip the legacy full-frame path

        # Draw only the enabled Zone elements onto a temporary layer, then
        # blend that layer with the original frame. This creates a faint
        # appearance and, importantly, no black/solid label background.
        if show_boundary or show_label:
            overlay = frame.copy()

            for zname in ZONE_NAMES:
                polygon = self.zones.get(zname, [])
                if len(polygon) < 3:
                    continue

                pts = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
                meta = getattr(self, "zone_meta", {}).get(zname, {})
                color_raw = meta.get("color_bgr", [0, 200, 0])
                try:
                    color = tuple(int(max(0, min(255, v))) for v in color_raw[:3])
                    if len(color) != 3:
                        color = (0, 200, 0)
                except Exception:
                    color = (0, 200, 0)

                if show_boundary:
                    # 1 px is deliberately light; opacity controls overall strength.
                    cv2.polylines(overlay, [pts], True, color, 1, cv2.LINE_AA)

                if show_label and meta.get("show_label", True):
                    moments = cv2.moments(pts)
                    if abs(moments.get("m00", 0.0)) > 1e-6:
                        cx = int(moments["m10"] / moments["m00"])
                        cy = int(moments["m01"] / moments["m00"])
                    else:
                        cx = int(np.mean([p[0] for p in polygon]))
                        cy = int(np.mean([p[1] for p in polygon]))

                    # Toggle whether the word "Zone" is included.
                    label = zname if label_prefix else zname.replace("Zone ", "", 1)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.55
                    thickness = 1
                    (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)
                    tx = max(5, cx - tw // 2)
                    ty = max(th + 5, cy + th // 2)

                    # No rectangle/background: text is drawn directly on the
                    # transparent overlay and then blended with the frame.
                    cv2.putText(
                        overlay, label, (tx, ty), font, font_scale,
                        color, thickness, cv2.LINE_AA
                    )

            if opacity > 0.0:
                cv2.addWeighted(overlay, opacity, frame, 1.0 - opacity, 0, frame)

        # Keep line geometry behavior unchanged.
        for lname in LINE_NAMES:
            line = self.lines.get(lname, [])
            if len(line) != 2:
                continue
            p1 = tuple(map(int, line[0])); p2 = tuple(map(int, line[1]))
            cv2.line(frame, p1, p2, (255, 255, 255), 4, cv2.LINE_AA)
            cv2.circle(frame, p1, 6, (255, 255, 255), -1)
            cv2.circle(frame, p2, 6, (255, 255, 255), -1)
            mx, my = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
            cv2.putText(frame, lname, (mx, max(20, my - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

    # ========================================================
    # V27 RUNTIME SNAPSHOT (read once on the main thread)
    # ========================================================

    _ANCHORS = {
        "Top": (50.0, 0.0), "Center": (50.0, 50.0), "Bottom": (50.0, 100.0),
        "Left": (0.0, 50.0), "Right": (100.0, 50.0),
        "Top Left": (0.0, 0.0), "Top Right": (100.0, 0.0),
        "Bottom Left": (0.0, 100.0), "Bottom Right": (100.0, 100.0),
    }

    def _anchor_fraction(self, position, offset_text):
        try:
            offset = max(0.0, min(50.0, float(offset_text)))
        except Exception:
            offset = 0.0
        px, py = self._ANCHORS.get(str(position).strip(), self._ANCHORS["Center"])
        # Move only the coordinates that touch an edge.
        if px == 0.0:
            px = offset
        elif px == 100.0:
            px = 100.0 - offset
        if py == 0.0:
            py = offset
        elif py == 100.0:
            py = 100.0 - offset
        return px / 100.0, py / 100.0

    def _runtime_snapshot(self, settings=None):
        """Values used for every detection/frame, copied from Tk once."""
        def b(var):
            try:
                return bool(var.get())
            except Exception:
                return False
        try:
            opacity = max(0.0, min(1.0, float(self.zone_overlay_opacity_var.get()) / 100.0))
        except Exception:
            opacity = 0.45
        try:
            live_ppm = float(self.run3_ppm_var.get())
        except Exception:
            live_ppm = 0.0
        rt = {
            "anchor": self._anchor_fraction(self.trajectory_position_var.get(), self.trajectory_offset_var.get()),
            "zone_opacity": opacity,
            "show_zone_boundary": b(self.show_zone_boundary_var),
            "show_zone_label": b(self.show_zone_label_var),
            "show_zone_label_prefix": b(self.show_zone_label_prefix_var),
            "show_bbox": b(self.show_bbox_var),
            "show_decision_point": b(self.draw_center_var),
            "live_ppm": live_ppm,
        }
        for name in ("id", "class", "conf", "zone", "speed"):
            rt[f"show_label_{name}"] = b(getattr(self, f"show_label_{name}_var"))
            rt[f"show_prefix_{name}"] = b(getattr(self, f"show_prefix_{name}_var"))
        return rt

    def get_zone_reference_point(self, x1, y1, x2, y2):
        """Return the selected Trajectory Position inside the bounding box.

        Nine anchors are supported: Top, Center, Bottom, Left, Right,
        Top Left, Top Right, Bottom Left, Bottom Right.
        Offset (%) moves the anchor inward from the selected edge(s).
        V27: during a run the anchor comes from the start-of-run snapshot.
        """
        rt = self._rt if (self.running and self._rt) else None
        if rt is not None:
            fx, fy = rt["anchor"]
        else:
            fx, fy = self._anchor_fraction(self.trajectory_position_var.get(), self.trajectory_offset_var.get())
        return (
            int(round(x1 + (x2 - x1) * fx)),
            int(round(y1 + (y2 - y1) * fy)),
        )

    def _zone_polygons(self):
        """Cached int32 polygons for Zone assignment (built once per geometry)."""
        key = (id(self.zones),) + tuple((z, id(self.zones.get(z)), len(self.zones.get(z, []))) for z in ZONE_NAMES)
        cache = getattr(self, "_zone_poly_cache", None)
        if cache is None or cache[0] != key:
            polys = [
                (z, np.array(self.zones[z], dtype=np.int32))
                for z in ZONE_NAMES if len(self.zones.get(z, [])) >= 3
            ]
            cache = (key, polys)
            self._zone_poly_cache = cache
        return cache[1]

    def _draw_zone_layer(self, layer, show_boundary, show_label, label_prefix, mono=False):
        """Draw Zone boundaries/labels once onto a static layer."""
        for zname in ZONE_NAMES:
            polygon = self.zones.get(zname, [])
            if len(polygon) < 3:
                continue
            pts = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
            meta = getattr(self, "zone_meta", {}).get(zname, {})
            if mono:
                color = 255
            else:
                try:
                    color = tuple(int(max(0, min(255, v))) for v in meta.get("color_bgr", [0, 200, 0])[:3])
                    if len(color) != 3:
                        color = (0, 200, 0)
                except Exception:
                    color = (0, 200, 0)
            if show_boundary:
                cv2.polylines(layer, [pts], True, color, 1, cv2.LINE_AA)
            if show_label and meta.get("show_label", True):
                moments = cv2.moments(pts)
                if abs(moments.get("m00", 0.0)) > 1e-6:
                    cx = int(moments["m10"] / moments["m00"]); cy = int(moments["m01"] / moments["m00"])
                else:
                    cx = int(np.mean([p[0] for p in polygon])); cy = int(np.mean([p[1] for p in polygon]))
                label = zname if label_prefix else zname.replace("Zone ", "", 1)
                font = cv2.FONT_HERSHEY_SIMPLEX
                (tw, th), _ = cv2.getTextSize(label, font, 0.55, 1)
                cv2.putText(layer, label, (max(5, cx - tw // 2), max(th + 5, cy + th // 2)),
                            font, 0.55, color, 1, cv2.LINE_AA)


    def get_zone_from_trajectory_point(self, point):
        """Return the first Zone containing the selected Trajectory Position point.

        Zone membership is based ONLY on the selected Trajectory Position.
        The bounding-box area, overlap ratio, confidence score, and weighting
        are not calculated.
        """
        if point is None:
            return None
        pt = (float(point[0]), float(point[1]))
        for zname, poly in self._zone_polygons():
            if cv2.pointPolygonTest(poly, pt, False) >= 0:
                return zname
        return None

    def assign_zone_candidate(self, x1, y1, x2, y2):
        """Assign Zone using only the selected Trajectory Position."""
        point = self.get_zone_reference_point(x1, y1, x2, y2)
        zone = self.get_zone_from_trajectory_point(point)
        confidence = 1.0 if zone else 0.0
        scores = {zone: 1.0} if zone else {}
        return zone, confidence, {}, point, scores


    def confirm_zone(self, track_state, candidate, candidate_confidence, frame_index, confirmation_frames):
        """Confirm a Zone and clear it when the selected point leaves all Zones."""
        confirmation_frames = max(1, int(confirmation_frames))

        if candidate is None:
            track_state["candidate_zone"] = None
            track_state["candidate_count"] = 0
            track_state["candidate_confidence"] = 0.0
            track_state["no_zone_count"] = track_state.get("no_zone_count", 0) + 1

            # Important: a tracked object must stop being displayed as a Zone
            # object after its selected reference point leaves the Zone.
            if track_state["no_zone_count"] >= confirmation_frames:
                changed = track_state.get("confirmed_zone") is not None
                track_state["confirmed_zone"] = None
                track_state["confirmed_confidence"] = 0.0
                return None, changed

            return track_state.get("confirmed_zone"), False

        track_state["no_zone_count"] = 0

        if candidate == track_state.get("candidate_zone"):
            track_state["candidate_count"] = track_state.get("candidate_count", 0) + 1
        else:
            track_state["candidate_zone"] = candidate
            track_state["candidate_count"] = 1

        track_state["candidate_confidence"] = candidate_confidence

        if track_state["candidate_count"] >= confirmation_frames:
            changed = track_state.get("confirmed_zone") != candidate
            track_state["confirmed_zone"] = candidate
            track_state["confirmed_confidence"] = candidate_confidence
            return candidate, changed

        return track_state.get("confirmed_zone"), False

    @staticmethod
    def point_in_zone(x, y, points):
        if len(points) < 3:
            return False
        polygon = np.array(points, dtype=np.int32)
        return cv2.pointPolygonTest(polygon, (float(x), float(y)), False) >= 0

    @staticmethod
    def line_side(point, line):
        if len(line) < 2:
            return 0.0
        (x1, y1), (x2, y2) = line
        x, y = point
        return (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)

    @classmethod
    def line_crossing(cls, prev_point, curr_point, line):
        if len(line) < 2 or prev_point is None or curr_point is None:
            return None
        a = cls.line_side(prev_point, line)
        b = cls.line_side(curr_point, line)
        if a == 0 or b == 0 or (a < 0 < b) or (a > 0 > b):
            direction = "A_to_B" if a < b else "B_to_A"
            return direction
        return None

    def validate_measurements(self):
        has_any = any(len(v) >= 3 for v in self.zones.values()) or any(len(v) >= 2 for v in self.lines.values())
        if not has_any:
            return True
        bad_z = [k for k,v in self.zones.items() if v and len(v) < 3]
        bad_l = [k for k,v in self.lines.items() if v and len(v) != 2]
        if bad_z or bad_l:
            raise ValueError(f"Invalid measurement geometry. Zones need 3+ points; Lines need exactly 2 points.\nZones: {bad_z}\nLines: {bad_l}")
        return True

    # ========================================================
    # SCROLL
    # ========================================================

    # ========================================================
    # DETECTION
    # ========================================================

    def build_detection_section(self):

        frame = self.section(
            "การตรวจจับ (YOLO)",
            1,
            1
        )

        self.add_entry(
            frame, 0, "Confidence",
            self.conf_var
        )

        self.add_entry(
            frame, 1, "IoU",
            self.iou_var
        )

        ttk.Label(
            frame,
            text="Image Size"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=4
        )

        ttk.Combobox(
            frame,
            textvariable=self.img_size_var,
            values=[
                "320", "416", "512", "640",
                "768", "960", "1280"
            ],
            state="readonly",
            width=15
        ).grid(
            row=2,
            column=1,
            sticky="w"
        )

        ttk.Label(
            frame,
            text="Tracker"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=4
        )

        ttk.Combobox(
            frame,
            textvariable=self.tracker_var,
            values=[
                "ByteTrack",
                "BoT-SORT"
            ],
            state="readonly",
            width=15
        ).grid(
            row=3,
            column=1,
            sticky="w"
        )

    # ========================================================
    # PROCESSING
    # ========================================================

    def build_processing_section(self):

        frame = self.section(
            "การประมวลผล",
            0,
            2
        )

        ttk.Label(
            frame,
            text="Device"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=4
        )

        ttk.Combobox(
            frame,
            textvariable=self.device_var,
            values=[
                "Auto",
                "CPU",
                "GPU 0"
            ],
            state="readonly",
            width=18
        ).grid(
            row=0,
            column=1,
            sticky="w"
        )

        ttk.Label(
            frame,
            text="Precision"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=4
        )

        ttk.Combobox(
            frame,
            textvariable=self.precision_var,
            values=[
                "Auto",
                "FP16",
                "FP32"
            ],
            state="readonly",
            width=18
        ).grid(
            row=1,
            column=1,
            sticky="w"
        )

        ttk.Label(
            frame,
            text="Frame Skip"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=4
        )

        ttk.Combobox(
            frame,
            textvariable=self.frame_skip_var,
            values=[
                "NO - Process every frame",
                "1 - Process every 2nd frame",
                "2 - Process every 3rd frame",
                "3 - Process every 4th frame",
                "4 - Process every 5th frame"
            ],
            state="readonly",
            width=28
        ).grid(
            row=2,
            column=1,
            sticky="w"
        )

        ttk.Label(
            frame,
            text="GPU 0 = NVIDIA GeForce GTX 1650 — บนการ์ดรุ่นนี้ FP16 ช้ากว่า FP32 (~2.7 เท่า) ใช้ Auto หรือ FP32"
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0)
        )

    # ========================================================
    # BYTETRACK
    # ========================================================

    def build_bytetrack_section(self):

        frame = self.section(
            "การติดตามรถ (Tracker)",
            1,
            2
        )

        self.add_entry(
            frame, 0, "Track High Threshold",
            self.track_high_var
        )

        self.add_entry(
            frame, 1, "Track Low Threshold",
            self.track_low_var
        )

        self.add_entry(
            frame, 2, "New Track Threshold",
            self.new_track_var
        )

        self.add_entry(
            frame, 3, "Track Buffer",
            self.track_buffer_var
        )

        self.add_entry(
            frame, 4, "Match Threshold",
            self.match_threshold_var
        )

        ttk.Label(
            frame,
            text="These values apply when ByteTrack is selected"
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(5, 0)
        )

    # ========================================================
    # ADD ENTRY
    # ========================================================

    def add_entry(
        self,
        parent,
        row,
        label,
        variable,
        browse_command=None
    ):

        ttk.Label(
            parent,
            text=label
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=4
        )

        entry = ttk.Entry(
            parent,
            textvariable=variable,
            width=(None if browse_command else 12)
        )

        entry.grid(
            row=row,
            column=1,
            sticky=("ew" if browse_command else "w"),    # a path takes the width, a number does not
            pady=4
        )

        if browse_command:

            ttk.Button(
                parent,
                text="Browse",
                command=browse_command
            ).grid(
                row=row,
                column=2,
                padx=(5, 0)
            )

        return entry

    # ========================================================
    # BROWSE
    # ========================================================

    def browse_model(self):

        path = filedialog.askopenfilename(
            title="Select Model",
            filetypes=[
                ("PyTorch Model", "*.pt"),
                ("All Files", "*.*")
            ]
        )

        if path:
            self.model_var.set(path)

    def browse_video(self):

        path = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[
                ("Video", "*.mp4 *.avi *.mov *.mkv"),
                ("MP4", "*.mp4"),
                ("All Files", "*.*")
            ]
        )

        if path:
            self.video_var.set(path)

    def browse_output(self):

        path = filedialog.askdirectory(
            title="Select Output Folder"
        )

        if path:
            self.output_var.set(path)

    # ========================================================
    # HARDWARE
    # ========================================================

    def update_hardware_info(self):

        if torch.cuda.is_available():

            gpu_name = torch.cuda.get_device_name(0)

            try:
                total_memory = (
                    torch.cuda.get_device_properties(0)
                    .total_memory
                    / (1024 ** 3)
                )

                memory_text = (
                    f"{total_memory:.1f} GB"
                )

            except Exception:
                memory_text = "Unknown"

            self.hardware_var.set(
                f"GPU ✓ {gpu_name} | "
                f"CUDA ✓ | "
                f"PyTorch {torch.__version__} | "
                f"VRAM {memory_text}"
            )

        else:

            self.hardware_var.set(
                f"GPU ✗ | CUDA unavailable | "
                f"PyTorch {torch.__version__} | CPU mode"
            )

    # ========================================================
    # SAVE SETTINGS
    # ========================================================

    def _json_safe(self, value):
        """Convert settings/Zone data to plain JSON-safe Python values."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {str(k): self._json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._json_safe(v) for v in value]
        # Handle numpy scalar types without importing numpy here.
        try:
            return value.item()
        except Exception:
            return str(value)

    def _build_zone_snapshot(self):
        """Build a simple, self-contained Zone/Line snapshot for Settings."""
        zones = {}
        for name in ZONE_NAMES:
            zones[name] = [
                [float(p[0]), float(p[1])]
                for p in self.zones.get(name, [])
                if isinstance(p, (list, tuple)) and len(p) >= 2
            ]

        lines = {}
        for name in LINE_NAMES:
            lines[name] = [
                [float(p[0]), float(p[1])]
                for p in self.lines.get(name, [])
                if isinstance(p, (list, tuple)) and len(p) >= 2
            ]

        return {
            "version": 2,
            "zones": zones,
            "lines": lines,
            "zone_meta": self._json_safe(getattr(self, "zone_meta", {})),
            "zone_source_video": str(getattr(self, "zone_source_video", "") or ""),
            "zone_source_width": self._json_safe(getattr(self, "zone_source_width", None)),
            "zone_source_height": self._json_safe(getattr(self, "zone_source_height", None)),
            "zone_file_format": getattr(self, "zone_file_format", None),
            "zone_scaled": self._json_safe(getattr(self, "zone_scaled", [])),
        }

    def get_settings(self):
        """Return every user-editable setting plus an embedded Zone snapshot."""
        return {
            "settings_version": 2,
            "run_name": self.run_name_var.get(),
            "model": self.model_var.get(),
            "video": self.video_var.get(),
            "output": self.output_var.get(),
            "zone_file": self.zone_line_config_var.get(),
            "zone_snapshot": self._build_zone_snapshot(),
            "confidence": self.conf_var.get(),
            "iou": self.iou_var.get(),
            "img_size": self.img_size_var.get(),
            "tracker": self.tracker_var.get(),
            "device": self.device_var.get(),
            "precision": self.precision_var.get(),
            "frame_skip": self.frame_skip_var.get(),
            "track_high": self.track_high_var.get(),
            "track_low": self.track_low_var.get(),
            "new_track": self.new_track_var.get(),
            "track_buffer": self.track_buffer_var.get(),
            "match_threshold": self.match_threshold_var.get(),
            "show_preview": self.show_preview_var.get(),
            "draw_center": self.draw_center_var.get(),
            "draw_trail": self.draw_trail_var.get(),
            "trail_length": self.trail_length_var.get(),
            "save_video": self.save_video_var.get(),
            "analysis_start_s": self.analysis_start_var.get(),
            "analysis_end_s": self.analysis_end_var.get(),
            "record_start_s": self.record_start_var.get(),
            "record_end_s": self.record_end_var.get(),
            "save_csv": self.save_csv_var.get(),
            "csv_flush": self.csv_flush_var.get(),
            "research_mode": self.research_mode_var.get(),
            "trajectory_position": self.trajectory_position_var.get(),
            "trajectory_offset": self.trajectory_offset_var.get(),
            "show_zone_boundary": self.show_zone_boundary_var.get(),
            "show_zone_label": self.show_zone_label_var.get(),
            "show_zone_label_prefix": self.show_zone_label_prefix_var.get(),
            "zone_overlay_opacity": self.zone_overlay_opacity_var.get(),
            "show_label_id": self.show_label_id_var.get(),
            "show_label_class": self.show_label_class_var.get(),
            "show_label_conf": self.show_label_conf_var.get(),
            "show_label_zone": self.show_label_zone_var.get(),
            "show_label_speed": self.show_label_speed_var.get(),
            "show_bbox": self.show_bbox_var.get(),
            "show_prefix_id": self.show_prefix_id_var.get(),
            "show_prefix_class": self.show_prefix_class_var.get(),
            "show_prefix_conf": self.show_prefix_conf_var.get(),
            "show_prefix_zone": self.show_prefix_zone_var.get(),
            "show_prefix_speed": self.show_prefix_speed_var.get(),
            "run3": {
                "site_id": self.run3_site_id_var.get(),
                "speed_enabled": self.run3_speed_enabled_var.get(),
                "gap_enabled": self.run3_gap_enabled_var.get(),
                "lc_enabled": self.run3_lc_enabled_var.get(),
                "pet_enabled": self.run3_pet_enabled_var.get(),
                "ttc_enabled": self.run3_ttc_enabled_var.get(),
                "ldp_enabled": self.run3_ldp_enabled_var.get(),
                "ppm": self.run3_ppm_var.get(),
                "perspective_enabled": self.run3_perspective_enabled_var.get(),
                "perspective_p1": self.run3_perspective_p1_var.get(),
                "perspective_p2": self.run3_perspective_p2_var.get(),
                "perspective_p3": self.run3_perspective_p3_var.get(),
                "perspective_p4": self.run3_perspective_p4_var.get(),
                "perspective_length_m": self.run3_perspective_length_var.get(),
                "perspective_width_m": self.run3_perspective_width_var.get(),
                "perspective_l12_m": self.run3_perspective_l12_var.get(),
                "perspective_l23_m": self.run3_perspective_l23_var.get(),
                "perspective_l34_m": self.run3_perspective_l34_var.get(),
                "perspective_l41_m": self.run3_perspective_l41_var.get(),
                "waiting_speed_threshold": self.run3_waiting_speed_threshold_var.get(),
                "gap_hold_min_duration_s": self.run3_hold_min_duration_var.get(),
                "lateral_axis_angle_deg": self.run3_lateral_axis_angle_var.get(),
                "lc_heading_window_s": self.run3_lc_heading_window_var.get(),
                "topview_video": self.run3_topview_video_var.get(),
                "topview_map": self.run3_topview_map_var.get(),
                "road_lines": self.run3_road_lines_var.get(),
                "lens_f": self.run3_lens_f_var.get(),
                "lens_k1": self.run3_lens_k1_var.get(),
                "lens_k2": self.run3_lens_k2_var.get(),
                "lc_along_limit_m": self.run3_lc_along_limit_var.get(),
                "lc_max_lateral_m": self.run3_lc_max_lateral_var.get(),
                "lc_motorcycle_pairs_only": self.run3_lc_motorcycle_pairs_only_var.get(),
                "pet_interaction_distance_m": self.run3_pet_interaction_distance_var.get(),
                "pet_threshold_s": self.run3_pet_threshold_var.get(),
                "speed_zones": [z for z,v in self.run3_speed_zone_vars.items() if v.get()],
                "speed_smoothing_samples": self.run3_speed_smoothing_var.get(),
                "speed_max_kmh": self.run3_speed_max_var.get(),
                "zone_calibrations": json.loads(json.dumps(self.run3_zone_calibrations)),
                "lc_zones": [z for z,v in self.run3_lc_zone_vars.items() if v.get()],
                "pet_zone6": self.run3_pet_zone6_var.get(),
                "pet_zones": [z for z, v in self.run3_pet_zone_vars.items() if v.get()],
                "ttc_zones": [z for z, v in self.run3_ttc_zone_vars.items() if v.get()],
                "ldp_zones": [z for z, v in self.run3_ldp_zone_vars.items() if v.get()],
                "pet_max_s": self.run3_pet_max_var.get(),
                "ttc_max_record_s": self.run3_ttc_max_record_var.get(),
                "ttc_heading_max_deg": self.run3_ttc_heading_max_var.get(),
                "ttc_velocity_window_s": self.run3_ttc_velocity_window_var.get(),
                "ttc_min_speed_kmh": self.run3_ttc_min_speed_var.get(),
                "ttc_side_enabled": self.run3_ttc_side_enabled_var.get(),
                "ttc_side_window_factor": self.run3_ttc_side_factor_var.get(),
                "ttc_side_margin_s": self.run3_ttc_side_margin_var.get(),
                "ttc_side_min_angle_deg": self.run3_ttc_side_angle_var.get(),
                "ttc_side_mode": self.run3_ttc_side_mode_var.get(),
                **{key: self.run3_geometry_vars[key].get() for key in RUN3_GEOMETRY_KEYS},
                "ldp_smoothing_samples": self.run3_ldp_smoothing_var.get(),
                "vehicle_lengths": {name: var.get() for name, var in self.run3_length_vars.items()},
                "gap_subject_134": self.run3_gap_subject_134_var.get(),
                "gap_subject_1367": self.run3_gap_subject_1367_var.get(),
                "gap_subject_5631": self.run3_gap_subject_5631_var.get(),
                "use_raff": self.run3_use_raff_var.get(),
                "use_mle": self.run3_use_mle_var.get(),
                "reference_line_mapping": self.run3_reference_text.get("1.0", "end-1c") if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text,
                "vehicle_widths": {name: var.get() for name, var in self.run3_width_vars.items()},
            },
        }

    def save_settings(self):
        path = filedialog.asksaveasfilename(
            title="Save Run 1 Settings",
            defaultextension=".json",
            filetypes=[("PK Studio Settings", "*.json"), ("All Files", "*.*")],
            initialfile=self.run_name_var.get() + "_settings.json"
        )
        if not path:
            return

        try:
            settings = self._json_safe(self.get_settings())
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False, allow_nan=False)
            self.status_var.set(f"Settings saved: {os.path.basename(path)}")
            messagebox.showinfo("Settings Saved", f"Settings and Zone geometry saved successfully.\n\n{path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save settings:\n\n{e}")

    def load_settings(self):
        path = filedialog.askopenfilename(
            title="Load Run 1 Settings",
            filetypes=[("PK Studio Settings", "*.json"), ("JSON files", "*.json"), ("All Files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            if not isinstance(settings, dict):
                raise ValueError("Settings file must contain a JSON object.")

            self.set_settings(settings)
            self.status_var.set(f"Settings loaded: {os.path.basename(path)}")
            messagebox.showinfo("Settings Loaded", "All settings, including Zone geometry, were loaded successfully.")
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load settings:\n\n{e}")

    def set_settings(self, settings):
        """Apply settings and restore embedded Zone geometry first, without requiring the original Zone file."""
        pairs = [
            ("run_name", self.run_name_var),
            ("model", self.model_var),
            ("video", self.video_var),
            ("output", self.output_var),
            ("zone_file", self.zone_line_config_var),
            ("confidence", self.conf_var),
            ("iou", self.iou_var),
            ("img_size", self.img_size_var),
            ("tracker", self.tracker_var),
            ("device", self.device_var),
            ("precision", self.precision_var),
            ("frame_skip", self.frame_skip_var),
            ("track_high", self.track_high_var),
            ("track_low", self.track_low_var),
            ("new_track", self.new_track_var),
            ("track_buffer", self.track_buffer_var),
            ("match_threshold", self.match_threshold_var),
            ("show_preview", self.show_preview_var),
            ("draw_center", self.draw_center_var),
            ("draw_trail", self.draw_trail_var),
            ("trail_length", self.trail_length_var),
            ("save_video", self.save_video_var),
            ("analysis_start_s", self.analysis_start_var),
            ("analysis_end_s", self.analysis_end_var),
            ("record_start_s", self.record_start_var),
            ("record_end_s", self.record_end_var),
            ("save_csv", self.save_csv_var),
            ("csv_flush", self.csv_flush_var),
            ("research_mode", self.research_mode_var),
            ("trajectory_position", self.trajectory_position_var),
            ("trajectory_offset", self.trajectory_offset_var),
            ("show_zone_boundary", self.show_zone_boundary_var),
            ("show_zone_label", self.show_zone_label_var),
            ("show_zone_label_prefix", self.show_zone_label_prefix_var),
            ("zone_overlay_opacity", self.zone_overlay_opacity_var),
            ("show_label_id", self.show_label_id_var),
            ("show_label_class", self.show_label_class_var),
            ("show_label_conf", self.show_label_conf_var),
            ("show_label_zone", self.show_label_zone_var),
            ("show_label_speed", self.show_label_speed_var),
            ("show_bbox", self.show_bbox_var),
            ("show_prefix_id", self.show_prefix_id_var),
            ("show_prefix_class", self.show_prefix_class_var),
            ("show_prefix_conf", self.show_prefix_conf_var),
            ("show_prefix_zone", self.show_prefix_zone_var),
            ("show_prefix_speed", self.show_prefix_speed_var),
        ]

        for key, variable in pairs:
            if key in settings:
                variable.set(settings[key])

        run3 = settings.get("run3", {})
        if isinstance(run3, dict):
            zc = run3.get("zone_calibrations", {})
            self.run3_zone_calibrations = {
                str(k): v for k, v in zc.items()
                if isinstance(v, dict) and len(v.get("points", [])) == 4 and len(v.get("lengths", [])) == 4
            } if isinstance(zc, dict) else {}
            mapping_pairs = [
                ("site_id", self.run3_site_id_var),
                ("speed_enabled", self.run3_speed_enabled_var),
                ("gap_enabled", self.run3_gap_enabled_var),
                ("lc_enabled", self.run3_lc_enabled_var),
                ("pet_enabled", self.run3_pet_enabled_var),
                ("ttc_enabled", self.run3_ttc_enabled_var),
                ("ldp_enabled", self.run3_ldp_enabled_var),
                ("ppm", self.run3_ppm_var),
                ("perspective_enabled", self.run3_perspective_enabled_var),
                ("perspective_p1", self.run3_perspective_p1_var),
                ("perspective_p2", self.run3_perspective_p2_var),
                ("perspective_p3", self.run3_perspective_p3_var),
                ("perspective_p4", self.run3_perspective_p4_var),
                ("perspective_length_m", self.run3_perspective_length_var),
                ("perspective_width_m", self.run3_perspective_width_var),
                ("perspective_l12_m", self.run3_perspective_l12_var),
                ("perspective_l23_m", self.run3_perspective_l23_var),
                ("perspective_l34_m", self.run3_perspective_l34_var),
                ("perspective_l41_m", self.run3_perspective_l41_var),
                ("pet_max_s", self.run3_pet_max_var),
                ("ttc_max_record_s", self.run3_ttc_max_record_var),
                ("ttc_heading_max_deg", self.run3_ttc_heading_max_var),
                ("ttc_velocity_window_s", self.run3_ttc_velocity_window_var),
                ("ttc_min_speed_kmh", self.run3_ttc_min_speed_var),
                ("ttc_side_enabled", self.run3_ttc_side_enabled_var),
                ("ttc_side_window_factor", self.run3_ttc_side_factor_var),
                ("ttc_side_margin_s", self.run3_ttc_side_margin_var),
                ("ttc_side_min_angle_deg", self.run3_ttc_side_angle_var),
                ("ttc_side_mode", self.run3_ttc_side_mode_var),
                ("speed_smoothing_samples", self.run3_speed_smoothing_var),
                ("speed_max_kmh", self.run3_speed_max_var),
                ("ldp_smoothing_samples", self.run3_ldp_smoothing_var),
                ("waiting_speed_threshold", self.run3_waiting_speed_threshold_var),
                ("gap_hold_min_duration_s", self.run3_hold_min_duration_var),
                ("lateral_axis_angle_deg", self.run3_lateral_axis_angle_var),
                ("lc_heading_window_s", self.run3_lc_heading_window_var),
                ("topview_video", self.run3_topview_video_var),
                ("topview_map", self.run3_topview_map_var),
                ("road_lines", self.run3_road_lines_var),
                ("lens_f", self.run3_lens_f_var),
                ("lens_k1", self.run3_lens_k1_var),
                ("lens_k2", self.run3_lens_k2_var),
                ("lc_along_limit_m", self.run3_lc_along_limit_var),
                ("lc_max_lateral_m", self.run3_lc_max_lateral_var),
                ("lc_motorcycle_pairs_only", self.run3_lc_motorcycle_pairs_only_var),
                ("pet_interaction_distance_m", self.run3_pet_interaction_distance_var),
                ("pet_threshold_s", self.run3_pet_threshold_var),
                ("gap_subject_134", self.run3_gap_subject_134_var),
                ("gap_subject_1367", self.run3_gap_subject_1367_var),
                ("gap_subject_5631", self.run3_gap_subject_5631_var),
                ("use_raff", self.run3_use_raff_var),
                ("use_mle", self.run3_use_mle_var),
            ]
            mapping_pairs += [(key, self.run3_geometry_vars[key]) for key in RUN3_GEOMETRY_KEYS]
            for key, variable in mapping_pairs:
                if key in run3:
                    variable.set(run3[key])
            if "pet_zones" in run3:
                for z, var in self.run3_pet_zone_vars.items():
                    var.set(z in set(run3.get("pet_zones") or []))
            elif "pet_zone6" in run3:
                self.run3_pet_zone6_var.set(bool(run3.get("pet_zone6")))
            for key, var_map in (("ttc_zones", self.run3_ttc_zone_vars), ("ldp_zones", self.run3_ldp_zone_vars)):
                if key in run3:
                    for z, var in var_map.items():
                        var.set(z in set(run3.get(key) or []))
            lengths = run3.get("vehicle_lengths", {})
            if isinstance(lengths, dict):
                for name, var in self.run3_length_vars.items():
                    if name in lengths:
                        var.set(lengths[name])
            # Speed zone settings: new v14 key, with backward compatibility to v13.
            speed_zone_values = run3.get("speed_zones")
            if speed_zone_values is None:
                legacy = set(run3.get("speed_approach_zones", [])) | set(run3.get("speed_exit_zones", []))
                speed_zone_values = sorted(legacy)
            for z in ZONE_IDS:
                self.run3_speed_zone_vars[z].set(z in set(speed_zone_values or []))
                if "lc_zones" in run3:
                    self.run3_lc_zone_vars[z].set(z in set(run3.get("lc_zones", [])))
            self.run3_reference_mapping_text = str(run3.get("reference_line_mapping", "") or "")
            if hasattr(self, "run3_reference_text"):
                self.run3_reference_text.delete("1.0", "end")
                self.run3_reference_text.insert("1.0", self.run3_reference_mapping_text)
            widths = run3.get("vehicle_widths", {})
            if isinstance(widths, dict):
                for name, var in self.run3_width_vars.items():
                    if name in widths:
                        var.set(widths[name])

        snapshot = settings.get("zone_snapshot")
        restored = False
        if isinstance(snapshot, dict):
            raw_zones = snapshot.get("zones", {})
            raw_lines = snapshot.get("lines", {})
            if isinstance(raw_zones, dict):
                restored_zones = {name: [] for name in ZONE_NAMES}
                for name in ZONE_NAMES:
                    pts = raw_zones.get(name, [])
                    if isinstance(pts, list):
                        restored_zones[name] = [
                            (float(p[0]), float(p[1]))
                            for p in pts
                            if isinstance(p, (list, tuple)) and len(p) >= 2
                        ]
                self.zones = restored_zones
                restored = any(len(v) >= 3 for v in restored_zones.values())

            if isinstance(raw_lines, dict):
                restored_lines = {name: [] for name in LINE_NAMES}
                for name in LINE_NAMES:
                    pts = raw_lines.get(name, [])
                    if isinstance(pts, list):
                        restored_lines[name] = [
                            (float(p[0]), float(p[1]))
                            for p in pts
                            if isinstance(p, (list, tuple)) and len(p) >= 2
                        ]
                self.lines = restored_lines

            self.zone_meta = snapshot.get("zone_meta", {}) or {}
            self.zone_source_video = str(snapshot.get("zone_source_video", "") or "")
            self.zone_source_width = snapshot.get("zone_source_width")
            self.zone_source_height = snapshot.get("zone_source_height")
            self.zone_file_format = snapshot.get("zone_file_format")
            self.zone_scaled = snapshot.get("zone_scaled", []) or []

        # Backward compatibility: if there is no embedded snapshot, try the saved Zone file.
        if not restored:
            zone_path = self.zone_line_config_var.get().strip()
            if zone_path and os.path.isfile(zone_path):
                self.load_pkstudio_zones()

        self.refresh_measurement_status()
        self.update_trajectory_position_controls()

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_settings(self):

        if not os.path.isfile(
            self.model_var.get().strip()
        ):

            messagebox.showerror(
                "Model Error",
                "Model file not found\n\n"
                + self.model_var.get()
            )

            return False

        if not os.path.isfile(
            self.video_var.get().strip()
        ):

            messagebox.showerror(
                "Video Error",
                "Video file not found\n\n"
                + self.video_var.get()
            )

            return False

        if not self.run_name_var.get().strip():

            messagebox.showerror(
                "Run Name",
                "Please specify Run Name"
            )

            return False

        try:

            for label, var in (("Analyse from", self.analysis_start_var), ("Analyse to", self.analysis_end_var),
                               ("Record from", self.record_start_var), ("Record to", self.record_end_var)):
                try:
                    parse_clock_time(var.get())
                except ValueError as exc:
                    raise ValueError(f"{label}: {exc}")
            conf = float(self.conf_var.get())
            iou = float(self.iou_var.get())
            high = float(self.track_high_var.get())
            low = float(self.track_low_var.get())
            new_track = float(self.new_track_var.get())
            match = float(self.match_threshold_var.get())

            buffer = int(self.track_buffer_var.get())
            trail = int(self.trail_length_var.get())
            flush = int(self.csv_flush_var.get())

            for value in [
                conf,
                iou,
                high,
                low,
                new_track,
                match
            ]:

                if not 0 <= value <= 1:

                    raise ValueError(
                        "Threshold values must be between 0 and 1"
                    )

            if buffer < 1:
                raise ValueError(
                    "Track Buffer must be greater than 0"
                )

            if trail < 1:
                raise ValueError(
                    "Trail Length must be greater than 0"
                )

            if flush < 1:
                raise ValueError(
                    "CSV Flush must be greater than 0"
                )

        except Exception as e:

            messagebox.showerror(
                "Settings Error",
                str(e)
            )

            return False

        try:
            offset = float(self.trajectory_offset_var.get())
            if not 0 <= offset <= 50:
                raise ValueError("Trajectory Offset must be between 0 and 50%")
        except Exception as e:
            messagebox.showerror("Trajectory Position", str(e))
            return False

        if self.research_mode_var.get():

            self.frame_skip_var.set(
                "NO - Process every frame"
            )

            self.save_csv_var.set(True)

        return True

    # ========================================================
    # PERSPECTIVE CALIBRATION UI
    # ========================================================

    def open_perspective_calibration(self):
        """Open an in-app Tkinter calibration window.

        The user clicks P1 -> P2 -> P3 -> P4 on one road-plane quadrilateral.
        Coordinates are converted from the displayed image back to original-video
        pixel coordinates automatically, so the user never needs to type x,y.
        """
        video_path = str(self.video_var.get() or "").strip()
        if not video_path:
            messagebox.showerror("Perspective Calibration", "Please select a video first.")
            return
        if not os.path.isfile(video_path):
            messagebox.showerror("Perspective Calibration", f"Video not found:\n\n{video_path}")
            return

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            messagebox.showerror("Perspective Calibration", "Could not open the selected video.")
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        default_frame = max(0, min(total_frames - 1, total_frames // 2 if total_frames else 0))

        cap.set(cv2.CAP_PROP_POS_FRAMES, default_frame)
        ok, frame = cap.read()
        if not ok or frame is None:
            cap.release()
            messagebox.showerror("Perspective Calibration", "Could not read a calibration frame from the video.")
            return

        top = tk.Toplevel(self.root)
        top.title("PK Studio — Perspective Calibration")
        top.geometry("%dx%d+10+10" % (min(1280, top.winfo_screenwidth() - 40), min(900, top.winfo_screenheight() - 110)))
        top.minsize(900, 600)
        top.transient(self.root)
        top.grab_set()

        state = {
            "cap": cap,
            "frame": frame.copy(),
            "frame_index": default_frame,
            "points": [],
            "photo": None,
            "scale": 1.0,
            "offset_x": 0,
            "offset_y": 0,
            "image_w": width,
            "image_h": height,
            "drag_index": None,
        }

        # Points set by an earlier calibration come back on the picture (drag to adjust, Reset Points to start over).
        try:
            saved = [[float(v) for v in str(var.get()).replace(";", ",").split(",")]
                     for var in (self.run3_perspective_p1_var, self.run3_perspective_p2_var,
                                 self.run3_perspective_p3_var, self.run3_perspective_p4_var)]
            if len(saved) == 4 and all(len(pt) == 2 and 0 <= pt[0] <= width and 0 <= pt[1] <= height for pt in saved):
                state["points"] = [(pt[0], pt[1]) for pt in saved]
        except (ValueError, TypeError):
            pass
        top.calibration_state = state      # (also lets the tests look at the points)

        controls = ttk.Frame(top, padding=8)
        controls.pack(fill="x")
        canvas_frame = ttk.Frame(top, padding=(8, 0, 8, 8))
        canvas_frame.pack(fill="both", expand=True)

        controls.columnconfigure(10, weight=1)
        ttk.Label(controls, text=("ลำดับจุด: P1 → P2 → P3 → P4 | คลิกบนพื้นถนนที่เป็นพื้นที่เดียวกัน แล้วลากจุดปรับได้"
                                  + (" | จุดที่ตั้งไว้ก่อนหน้าแสดงอยู่แล้ว — ลากแก้ได้ หรือกด Reset Points เพื่อเริ่มใหม่" if len(state["points"]) == 4 else ""))).grid(
            row=0, column=0, columnspan=11, sticky="w", pady=(0, 6))

        # row 1: choose the frame, and the two buttons that finish the dialog (always visible at the top right)
        ttk.Label(controls, text="Frame").grid(row=1, column=0, sticky="e", padx=(0, 5))
        frame_var = tk.StringVar(value=str(default_frame + 1))
        frame_entry = ttk.Entry(controls, textvariable=frame_var, width=10)
        frame_entry.grid(row=1, column=1, sticky="w")
        ttk.Button(controls, text="Load Frame", command=lambda: load_frame()).grid(row=1, column=2, padx=5)
        ttk.Button(controls, text="Reset Points", command=lambda: reset_points()).grid(row=1, column=3, padx=5)
        measure_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls, text="วัดระยะทดสอบ (คลิก 2 จุด)", variable=measure_var,
                        command=lambda: render()).grid(row=1, column=4, padx=(14, 0))
        finish_bar = ttk.Frame(controls)
        finish_bar.grid(row=1, column=10, sticky="e")
        apply_button = ttk.Button(finish_bar, text="✅ Apply Calibration", command=lambda: apply_calibration())
        apply_button.pack(side="left", padx=5)
        ttk.Button(finish_bar, text="Cancel", command=lambda: (cap.release(), top.grab_release(), top.destroy())).pack(side="left", padx=5)

        # row 2: the four known real lengths in one row (the sides of the quadrilateral P1-P2-P3-P4)
        length_vars = [
            tk.StringVar(value=str(self.run3_perspective_l12_var.get() or "")),
            tk.StringVar(value=str(self.run3_perspective_l23_var.get() or "")),
            tk.StringVar(value=str(self.run3_perspective_l34_var.get() or "")),
            tk.StringVar(value=str(self.run3_perspective_l41_var.get() or "")),
        ]
        lengths_box = ttk.LabelFrame(controls, text="ระยะจริงของแต่ละด้าน (เมตร)", padding=(8, 4))
        lengths_box.grid(row=2, column=0, columnspan=11, sticky="w", pady=(8, 0))
        for i, (lab, var) in enumerate(zip(("P1→P2", "P2→P3", "P3→P4", "P4→P1"), length_vars)):
            ttk.Label(lengths_box, text=lab).grid(row=0, column=i * 2, sticky="e", padx=(0 if i == 0 else 16, 5))
            ttk.Entry(lengths_box, textvariable=var, width=10).grid(row=0, column=i * 2 + 1, sticky="w")

        # per-zone calibration: each zone can get its OWN reference quadrilateral (own scale and perspective)
        def current_data():
            return {"points": list(state["points"]), "lengths": [v.get() for v in length_vars]}

        def load_data(data):
            state["points"] = [tuple(p) for p in data.get("points", [])]
            for var, text in zip(length_vars, list(data.get("lengths", [])) + ["", "", "", ""]):
                var.set(str(text))
            state["measure"] = []

        ctx = {"mode": "base", "drafts": {}}
        base_initial = current_data()
        mode_labels = ["ทั้งภาพ (ฐาน)"] + [f"Zone {z}" for z in ZONE_IDS]
        mode_var = tk.StringVar(value=mode_labels[0])
        ttk.Label(controls, text="ปรับเทียบสำหรับ").grid(row=1, column=5, sticky="e", padx=(14, 4))
        mode_box = ttk.Combobox(controls, textvariable=mode_var, values=mode_labels, state="readonly", width=14)
        mode_box.grid(row=1, column=6, sticky="w")
        delete_zone_button = ttk.Button(controls, text="ลบของโซนนี้", command=lambda: delete_zone_calibration())
        delete_zone_button.grid(row=1, column=7, padx=6)
        delete_zone_button.state(["disabled"])
        mode_status_var = tk.StringVar(value="")
        ttk.Label(controls, textvariable=mode_status_var, foreground="#0a7a3d", wraplength=1200, justify="left").grid(row=8, column=0, columnspan=11, sticky="w")

        def zone_summary_text():
            zs = sorted(int(k) for k in self.run3_zone_calibrations)
            return ("ปรับเทียบรายโซนแล้ว: " + ", ".join(f"Zone {z}" for z in zs)) if zs else "ยังไม่มีการปรับเทียบรายโซน"

        def on_mode_change(event=None):
            ctx["drafts"][ctx["mode"]] = current_data()
            label = mode_var.get()
            key = "base" if label == mode_labels[0] else label.split()[-1]
            ctx["mode"] = key
            if key in ctx["drafts"]:
                load_data(ctx["drafts"][key])
            elif key == "base":
                load_data(base_initial)
            else:
                saved = self.run3_zone_calibrations.get(key)
                load_data({"points": saved["points"], "lengths": saved["lengths"]} if saved else {})
            apply_button.config(text="✅ Apply Calibration" if key == "base" else "✅ บันทึกโซนนี้")
            delete_zone_button.state(["disabled"] if key == "base" else ["!disabled"])
            mode_status_var.set("" if key == "base" else f"โหมด Zone {key}: คลิก P1–P4 ให้คลุมพื้นที่ถนนของโซนนี้ แล้วกรอกระยะจริง 4 ด้าน — {zone_summary_text()}")
            render()

        mode_box.bind("<<ComboboxSelected>>", on_mode_change)

        def apply_zone_calibration():
            z = ctx["mode"]
            if len(state["points"]) != 4:
                messagebox.showerror("Perspective Calibration", "Please click exactly 4 points in order: P1 → P2 → P3 → P4.", parent=top)
                return
            try:
                lengths = [float(v.get().strip()) for v in length_vars]
                if min(lengths) <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Perspective Calibration", "All four Known Length values must be positive numbers in meters.", parent=top)
                return
            area = abs(cv2.contourArea(np.float32(state["points"]).reshape((-1, 1, 2))))
            if area < 100.0:
                messagebox.showerror("Perspective Calibration", "The 4 selected points are too close together.", parent=top)
                return
            self.run3_zone_calibrations[z] = {"points": [[float(x), float(y)] for x, y in state["points"]], "lengths": lengths}
            ctx["drafts"].pop(z, None)
            mode_status_var.set(f"บันทึกการปรับเทียบ Zone {z} แล้ว — {zone_summary_text()} (เลือกโซนอื่นเพื่อทำต่อ หรือกด Cancel/ปิดหน้าต่างเมื่อเสร็จ)")
            render()

        def delete_zone_calibration():
            z = ctx["mode"]
            self.run3_zone_calibrations.pop(z, None)
            ctx["drafts"].pop(z, None)
            load_data({})
            mode_status_var.set(f"ลบการปรับเทียบ Zone {z} แล้ว — {zone_summary_text()}")
            render()

        # row 3: the picked points and the calculated PPM
        point_text_var = tk.StringVar(value="ยังไม่ได้เลือกจุด")
        ttk.Label(controls, textvariable=point_text_var, foreground="#555555").grid(row=3, column=0, columnspan=11, sticky="w", pady=(6, 0))
        ppm_calc_var = tk.StringVar(value="Calculated PPM: -")
        ttk.Label(controls, textvariable=ppm_calc_var, foreground="#155a8a").grid(row=4, column=0, columnspan=11, sticky="w", pady=(2, 0))
        ttk.Label(controls, text="ระบบคำนวณ PPM จากระยะทั้ง 4 ด้าน", foreground="#555555").grid(row=5, column=0, columnspan=11, sticky="w")

        measure_text_var = tk.StringVar(value="")
        ttk.Label(controls, textvariable=measure_text_var, foreground="#8a2be2").grid(row=6, column=0, columnspan=11, sticky="w", pady=(2, 0))
        ttk.Label(controls, foreground="#555555", wraplength=1200, justify="left", text="ตรวจความแม่น: ติ๊ก \"วัดระยะทดสอบ\" แล้ววัดของที่รู้ขนาด (ความกว้างเลน, เส้นประ, ทางม้าลาย) ทั้งใกล้และไกลกล้อง — "
                  "ถ้าไกลกล้องคลาดมาก ให้ขยายกรอบ P1–P4 ให้คลุมพื้นที่ที่รถวิ่งให้มากที่สุด (ด้านสั้นอย่างน้อยเท่าความกว้างถนน)").grid(
            row=7, column=0, columnspan=11, sticky="w")
        state["measure"] = []

        def current_homography():
            """Homography of the four points with the four typed lengths (same rule as Apply), or None."""
            if len(state["points"]) != 4:
                return None
            try:
                l12, l23, l34, l41 = [float(v.get().strip()) for v in length_vars]
                if min(l12, l23, l34, l41) <= 0:
                    return None
            except ValueError:
                return None
            length, width_m = (l12 + l34) / 2.0, (l23 + l41) / 2.0
            try:
                return cv2.getPerspectiveTransform(np.float32(state["points"]), np.float32([[0, 0], [length, 0], [length, width_m], [0, width_m]]))
            except cv2.error:
                return None

        def measure_distance(p, q):
            """Distance in metres between two image points (original-video pixels) on the road plane, or None."""
            Hm = current_homography()
            if Hm is None:
                return None
            a, b = cv2.perspectiveTransform(np.float32([[p, q]]), Hm)[0]
            return float(math.hypot(b[0] - a[0], b[1] - a[1]))

        top.measure_distance = measure_distance

        canvas = tk.Canvas(canvas_frame, background="#202020", highlightthickness=1)
        canvas.pack(fill="both", expand=True)

        def render():
            img = state["frame"]
            h, w = img.shape[:2]
            cw = max(100, int(canvas.winfo_width()))
            ch = max(100, int(canvas.winfo_height()))
            scale = min(cw / w, ch / h)
            if scale <= 0:
                scale = 1.0
            state["scale"] = scale
            new_w = max(1, int(round(w * scale)))
            new_h = max(1, int(round(h * scale)))
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
            view = resized.copy()
            # context: zone outlines (grey) and the quadrilaterals already calibrated per zone (green)
            for zname, zpts in self.zones.items():
                if len(zpts) >= 3:
                    zarr = np.array([[int(x * scale), int(y * scale)] for x, y in zpts], np.int32)
                    cv2.polylines(view, [zarr], True, (150, 150, 150), 1, cv2.LINE_AA)
                    cv2.putText(view, str(zname).replace("Zone ", "Z"), (int(zarr[0][0]) + 4, int(zarr[0][1]) + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (190, 190, 190), 1, cv2.LINE_AA)
            for zkey, zdat in self.run3_zone_calibrations.items():
                if zkey == ctx["mode"]:
                    continue
                zarr = np.array([[int(x * scale), int(y * scale)] for x, y in zdat["points"]], np.int32)
                cv2.polylines(view, [zarr], True, (0, 200, 0), 2, cv2.LINE_AA)
                cv2.putText(view, f"cal Z{zkey}", (int(zarr[0][0]) + 6, int(zarr[0][1]) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2, cv2.LINE_AA)
            labels = ["P1", "P2", "P3", "P4"]
            for idx, (px, py) in enumerate(state["points"]):
                vx = int(round(px * scale))
                vy = int(round(py * scale))
                cv2.circle(view, (vx, vy), 7, (0, 255, 255), -1)
                cv2.putText(view, labels[idx], (vx + 10, vy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2, cv2.LINE_AA)
            if len(state["points"]) >= 2:
                for i in range(1, len(state["points"])):
                    a = state["points"][i-1]; b = state["points"][i]
                    cv2.line(view, (int(a[0]*scale), int(a[1]*scale)), (int(b[0]*scale), int(b[1]*scale)), (0,255,255), 2, cv2.LINE_AA)
            if len(state["points"]) == 4:
                a = state["points"][3]; b = state["points"][0]
                cv2.line(view, (int(a[0]*scale), int(a[1]*scale)), (int(b[0]*scale), int(b[1]*scale)), (0,255,255), 2, cv2.LINE_AA)

            if state["measure"]:
                mp = state["measure"]
                for q in mp:
                    cv2.circle(view, (int(q[0] * scale), int(q[1] * scale)), 6, (255, 0, 255), -1)
                if len(mp) == 2:
                    cv2.line(view, (int(mp[0][0] * scale), int(mp[0][1] * scale)), (int(mp[1][0] * scale), int(mp[1][1] * scale)), (255, 0, 255), 2, cv2.LINE_AA)
                    dist = measure_distance(mp[0], mp[1])
                    if dist is None:
                        measure_text_var.set("วัดไม่ได้: ต้องมีจุด P1–P4 ครบ 4 จุด และกรอกระยะจริงทั้ง 4 ด้านก่อน")
                    else:
                        mid = (int((mp[0][0] + mp[1][0]) / 2 * scale) + 8, int((mp[0][1] + mp[1][1]) / 2 * scale) - 8)
                        cv2.putText(view, f"{dist:.2f} m", mid, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2, cv2.LINE_AA)
                        px = math.hypot(mp[1][0] - mp[0][0], mp[1][1] - mp[0][1])
                        measure_text_var.set(f"ระยะที่วัดได้ = {dist:.2f} เมตร ({px:.0f} พิกเซล, สเกลตรงนี้ ≈ {px / dist:.0f} px/m) — เทียบกับขนาดจริงของสิ่งที่วัด")
                else:
                    measure_text_var.set("คลิกจุดที่สองเพื่อวัด")
            else:
                measure_text_var.set("")

            ok, buf = cv2.imencode('.png', view)
            if not ok:
                return
            photo = tk.PhotoImage(data=buf.tobytes())
            state["photo"] = photo
            canvas.delete("all")
            state["offset_x"] = max(0, (cw - new_w) // 2)
            state["offset_y"] = max(0, (ch - new_h) // 2)
            canvas.create_image(state["offset_x"], state["offset_y"], anchor="nw", image=photo)
            canvas.create_text(10, 10, anchor="nw", text=f"Frame {state['frame_index']+1} | Image {w}×{h}", fill="white", font=("Segoe UI", 10, "bold"))
            point_text_var.set("  ".join(f"P{i+1}=({x:.1f},{y:.1f})" for i,(x,y) in enumerate(state["points"])) if state["points"] else "ยังไม่ได้เลือกจุด")
            try:
                vals = []
                edge_defs = [
                    (0,1,length_vars[0]),
                    (1,2,length_vars[1]),
                    (2,3,length_vars[2]),
                    (3,0,length_vars[3]),
                ]
                for i,j,var in edge_defs:
                    if len(state["points"]) <= j:
                        continue
                    real_m = float(var.get().strip())
                    if real_m <= 0:
                        continue
                    px = math.hypot(state["points"][j][0]-state["points"][i][0], state["points"][j][1]-state["points"][i][1])
                    if px > 0:
                        vals.append(px / real_m)
                if vals:
                    ppm_calc_var.set(f"Calculated PPM: {sum(vals)/len(vals):.6f} pixel/m | edges={len(vals)}")
                else:
                    ppm_calc_var.set("Calculated PPM: -")
            except Exception:
                ppm_calc_var.set("Calculated PPM: -")

        def load_frame():
            try:
                requested = int(float(frame_var.get())) - 1
            except Exception:
                messagebox.showerror("Perspective Calibration", "Frame must be an integer.", parent=top)
                return
            if total_frames > 0:
                requested = max(0, min(total_frames - 1, requested))
            cap.set(cv2.CAP_PROP_POS_FRAMES, requested)
            ok, new_frame = cap.read()
            if not ok or new_frame is None:
                messagebox.showerror("Perspective Calibration", "Could not read that frame.", parent=top)
                return
            state["frame"] = new_frame.copy()
            state["frame_index"] = requested
            state["points"] = []
            render()

        def reset_points():
            state["points"] = []
            state["measure"] = []
            render()

        def event_to_image(event):
            sx = state["scale"]
            ox = state["offset_x"]
            oy = state["offset_y"]
            x = (event.x - ox) / sx
            y = (event.y - oy) / sx
            return float(x), float(y)

        def on_click(event):
            x, y = event_to_image(event)
            if x < 0 or y < 0 or x > state["image_w"] or y > state["image_h"]:
                return
            if measure_var.get():
                if len(state["measure"]) >= 2:
                    state["measure"] = []
                state["measure"].append((x, y))
                render()
                return
            if len(state["points"]) >= 4:
                candidates = [(i, math.hypot(px-x, py-y)) for i,(px,py) in enumerate(state["points"])]
                i, d = min(candidates, key=lambda q: q[1])
                if d <= max(12.0 / max(state["scale"], 1e-6), 20.0):
                    state["drag_index"] = i
                    return
            if len(state["points"]) < 4:
                state["points"].append((x, y))
                render()

        def on_drag(event):
            idx = state.get("drag_index")
            if idx is None or idx >= len(state["points"]):
                return
            x, y = event_to_image(event)
            x = max(0.0, min(float(state["image_w"]), x))
            y = max(0.0, min(float(state["image_h"]), y))
            state["points"][idx] = (x, y)
            render()

        def on_release(event):
            state["drag_index"] = None

        def apply_calibration():
            if ctx["mode"] != "base":
                apply_zone_calibration()
                return
            if len(state["points"]) != 4:
                messagebox.showerror("Perspective Calibration", "Please click exactly 4 points in order: P1 → P2 → P3 → P4.", parent=top)
                return
            try:
                real_lengths = [float(v.get().strip()) for v in length_vars]
                if any(v <= 0 for v in real_lengths):
                    raise ValueError
                l12, l23, l34, l41 = real_lengths
            except Exception:
                messagebox.showerror("Perspective Calibration", "All four Known Length values must be positive numbers in meters.", parent=top)
                return

            pts = np.array(state["points"], dtype=np.float32)
            area = abs(cv2.contourArea(pts.reshape((-1,1,2))))
            if area < 100.0:
                messagebox.showerror("Perspective Calibration", "The 4 selected points are too close together. Select a larger road-plane area.", parent=top)
                return

            # A four-corner homography needs a fully specified target quadrilateral.
            # Four side lengths alone do not uniquely determine that quadrilateral,
            # so for the rectangular road patch used here we use the mean of opposite
            # measured sides as the target length/width, while retaining all four
            # measured sides as calibration/QC inputs.
            length = (l12 + l34) / 2.0
            width_m = (l23 + l41) / 2.0
            src = np.float32(state["points"])
            dst = np.float32([[0.0,0.0],[length,0.0],[length,width_m],[0.0,width_m]])
            try:
                H = cv2.getPerspectiveTransform(src, dst)
            except Exception as exc:
                messagebox.showerror("Perspective Calibration", f"Could not create perspective transform:\n\n{exc}", parent=top)
                return
            if not np.isfinite(H).all():
                messagebox.showerror("Perspective Calibration", "The selected points produced an invalid transformation.", parent=top)
                return

            self.run3_perspective_p1_var.set(f"{state['points'][0][0]:.3f},{state['points'][0][1]:.3f}")
            self.run3_perspective_p2_var.set(f"{state['points'][1][0]:.3f},{state['points'][1][1]:.3f}")
            self.run3_perspective_p3_var.set(f"{state['points'][2][0]:.3f},{state['points'][2][1]:.3f}")
            self.run3_perspective_p4_var.set(f"{state['points'][3][0]:.3f},{state['points'][3][1]:.3f}")
            self.run3_perspective_length_var.set(f"{length:g}")
            self.run3_perspective_width_var.set(f"{width_m:g}")
            self.run3_perspective_l12_var.set(f"{l12:g}")
            self.run3_perspective_l23_var.set(f"{l23:g}")
            self.run3_perspective_l34_var.set(f"{l34:g}")
            self.run3_perspective_l41_var.set(f"{l41:g}")
            self.run3_perspective_enabled_var.set(True)

            edge_specs = [(0,1,l12),(1,2,l23),(2,3,l34),(3,0,l41)]
            edge_ppm = []
            for i,j,real_m in edge_specs:
                px = math.hypot(state["points"][j][0]-state["points"][i][0], state["points"][j][1]-state["points"][i][1])
                if real_m > 0 and px > 0:
                    edge_ppm.append(px / real_m)
            reference_ppm = (sum(edge_ppm) / len(edge_ppm)) if edge_ppm else 0.0
            if reference_ppm > 0:
                self.run3_ppm_var.set(f"{reference_ppm:.6f}")
            ppm_calc_var.set(f"PPM = {reference_ppm:.6f} pixel/m | 4-edge mean")
            self.run3_result_text.set(f"Perspective calibrated: Frame {state['frame_index']+1}, {state['image_w']}×{state['image_h']} | PPM auto-calculated")

            # Save a site-specific calibration JSON beside the selected output when possible.
            try:
                out_dir = str(self.output_var.get() or "").strip()
                if out_dir:
                    os.makedirs(out_dir, exist_ok=True)
                    site = re.sub(r"[^A-Za-z0-9_-]+", "_", self.run3_site_id_var.get().strip() or "Unknown")
                    cal_path = os.path.join(out_dir, f"Site_{site}_Perspective_Calibration.json")
                    payload = {
                        "Site_ID": self.run3_site_id_var.get().strip(),
                        "video_path": video_path,
                        "frame_index_zero_based": state["frame_index"],
                        "frame_number_one_based": state["frame_index"] + 1,
                        "image_width": state["image_w"],
                        "image_height": state["image_h"],
                        "P1": list(state["points"][0]), "P2": list(state["points"][1]),
                        "P3": list(state["points"][2]), "P4": list(state["points"][3]),
                        "Known_Length_P1_P2_m": l12,
                        "Known_Length_P2_P3_m": l23,
                        "Known_Length_P3_P4_m": l34,
                        "Known_Length_P4_P1_m": l41,
                        "Homography_Target_Length_m": length,
                        "Homography_Target_Width_m": width_m,
                        "Reference_PPM_pixel_per_meter": reference_ppm,
                        "Edge_PPM": {"P1-P2": edge_ppm[0] if len(edge_ppm)>0 else None, "P2-P3": edge_ppm[1] if len(edge_ppm)>1 else None, "P3-P4": edge_ppm[2] if len(edge_ppm)>2 else None, "P4-P1": edge_ppm[3] if len(edge_ppm)>3 else None},
                        "point_order": "P1->P2->P3->P4",
                        "calibration_method": "Four-point planar homography with four-side metric inputs",
                    }
                    with open(cal_path, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=2, ensure_ascii=False)
                    self.status_var.set(f"Perspective calibration saved: {os.path.basename(cal_path)}")
            except Exception as exc:
                self.status_var.set(f"Perspective applied; JSON save skipped: {exc}")

            top.grab_release()
            top.destroy()

        def on_resize(event=None):
            render()

        canvas.bind("<Button-1>", on_click)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        canvas.bind("<Configure>", on_resize)

        def on_close():
            try:
                cap.release()
            finally:
                try:
                    top.grab_release()
                except Exception:
                    pass
                top.destroy()
        top.protocol("WM_DELETE_WINDOW", on_close)
        top.calibration_api = {          # (lets the tests drive the dialog without clicking)
            "set_mode": lambda label: (mode_var.set(label), on_mode_change()),
            "apply": apply_calibration, "delete_zone": delete_zone_calibration,
            "length_vars": length_vars, "ctx": ctx, "mode_labels": mode_labels,
        }

        # Initial render after the canvas gets its first size.
        top.after(100, render)

    # ========================================================
    # RUN 3 VALIDATION
    # ========================================================

    def _run3_float(self, value, name, positive=True):
        text = str(value).strip()
        if not text:
            raise ValueError(f"Run 3 requires {name}.")
        try:
            number = float(text)
        except Exception as exc:
            raise ValueError(f"Run 3 {name} must be numeric.") from exc
        if positive and number <= 0:
            raise ValueError(f"Run 3 {name} must be greater than 0.")
        return number

    def _run3_parse_xy(self, text, label):
        raw = str(text or "").strip()
        if not raw:
            raise ValueError(f"Perspective correction: {label} is required")
        parts = [p.strip() for p in raw.replace(";", ",").split(",")]
        if len(parts) != 2:
            raise ValueError(f"Perspective correction: {label} must be x,y in pixels")
        return float(parts[0]), float(parts[1])

    def _video_frame_for_tools(self):
        video = str(self.video_var.get() or "").strip()
        if not video or not os.path.isfile(video):
            messagebox.showerror("เลนส์", "เลือกวิดีโอก่อน (ใช้เฟรมจากวิดีโอนี้)")
            return None
        return video

    def open_lens_line_tool(self):
        video = self._video_frame_for_tools()
        if video is None:
            return None
        return LensLineDialog(self, video, self.set_lens_values)

    def get_road_lines(self):
        """The road lines clicked on the camera picture: list of {"type": key, "points": [(x, y) pixels as recorded, ...]}."""
        try:
            data = json.loads(self.run3_road_lines_var.get() or "[]")
            out = []
            for item in data:
                kind, pts = normalize_road_line(item)
                if len(pts) >= 2:
                    out.append({"type": kind, "points": pts, "straight": road_line_straight(item)})
            return out
        except (ValueError, TypeError):
            return []

    def set_road_lines(self, lines):
        norm = [(normalize_road_line(it), road_line_straight(it)) for it in (lines or [])]
        norm = [(k, pts, st) for (k, pts), st in norm if len(pts) >= 2]
        self.run3_road_lines_var.set(json.dumps([{"t": k, "p": [[round(x, 1), round(y, 1)] for x, y in pts], "s": bool(st)} for k, pts, st in norm]) if norm else "")

    def clear_road_lines(self):
        self.run3_road_lines_var.set("")

    def _refresh_road_lines_info(self):
        n = len(self.get_road_lines())
        try:
            self.road_lines_info_var.set(f"วาดแล้ว {n} เส้น" if n else "ยังไม่ได้วาดเส้นถนน")
        except (AttributeError, tk.TclError):
            pass

    def open_road_line_tool(self):
        video = self._video_frame_for_tools()
        if video is None:
            return None
        return RoadLineDialog(self, video, self.set_road_lines, initial=self.get_road_lines())

    def set_lens_values(self, lens):
        self.run3_lens_f_var.set(f"{float(lens[0]):.4f}")
        self.run3_lens_k1_var.set(f"{float(lens[1]):.4f}")
        self.run3_lens_k2_var.set(f"{float(lens[2]) if len(lens) > 2 else 0.0:.4f}")

    def clear_lens_values(self):
        for var in (self.run3_lens_f_var, self.run3_lens_k1_var, self.run3_lens_k2_var):
            var.set("")

    def preview_lens_settings(self):
        video = self._video_frame_for_tools()
        if video is None:
            return None
        lens, size = self._run3_lens_params()
        if lens is None:
            messagebox.showinfo("เลนส์", "ยังไม่ได้ตั้งค่าเลนส์ (ใส่ f หรือกด แก้เลนส์จากเส้นตรง)")
            return None
        cap = cv2.VideoCapture(video)
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 2) // 2)
            ok, fr = cap.read()
        finally:
            cap.release()
        return show_lens_preview(self.root, fr, lens) if ok else None

    def _run3_lens_params(self):
        """(lens, size) from the lens values of step 2 (or the lens tool); (None, None) when no correction is set."""
        def num(var):
            try:
                return float(str(var.get()).strip())
            except ValueError:
                return None
        f = num(self.run3_lens_f_var)
        if f is None or f <= 0:                                   # no focal length typed = no correction
            return None, None
        k1, k2 = num(self.run3_lens_k1_var) or 0.0, num(self.run3_lens_k2_var) or 0.0
        size = getattr(self, "_lens_size_override", None)
        if size is None:
            w, h = self._actual_video_size()
            size = (w, h) if w and h else None
        if size is None:
            return None, None
        lens = (f, k1, k2)
        return (lens, (int(size[0]), int(size[1]))) if lens_is_valid(size, lens) else (None, None)

    @staticmethod
    def _run3_undistort(pts, c):
        """Camera pixels as clicked / detected -> pixels of the straightened picture (no change without a lens)."""
        p = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
        return lens_undistort(p, c["lens_size"], c["lens"]) if c.get("lens") is not None else p

    def _run3_get_perspective_matrix(self, silent=False):
        if not bool(self.run3_perspective_enabled_var.get()):
            return None
        try:
            p1 = self._run3_parse_xy(self.run3_perspective_p1_var.get(), "P1")
            p2 = self._run3_parse_xy(self.run3_perspective_p2_var.get(), "P2")
            p3 = self._run3_parse_xy(self.run3_perspective_p3_var.get(), "P3")
            p4 = self._run3_parse_xy(self.run3_perspective_p4_var.get(), "P4")
            lens_, lsize_ = self._run3_lens_params()
            q1, q2, q3, q4 = ([tuple(q) for q in lens_undistort([p1, p2, p3, p4], lsize_, lens_)] if lens_ is not None else [p1, p2, p3, p4])
            # Prefer the four measured side lengths; target is the mean-opposite-side rectangle.
            raw4 = [
                self.run3_perspective_l12_var.get(), self.run3_perspective_l23_var.get(),
                self.run3_perspective_l34_var.get(), self.run3_perspective_l41_var.get(),
            ]
            if all(str(v).strip() for v in raw4):
                l12, l23, l34, l41 = [float(v) for v in raw4]
                if any(v <= 0 for v in (l12,l23,l34,l41)):
                    raise ValueError("Perspective correction: all four side lengths must be > 0")
                length_m = (l12 + l34) / 2.0
                width_m = (l23 + l41) / 2.0
            else:
                length_m = float(self.run3_perspective_length_var.get())
                width_m = float(self.run3_perspective_width_var.get())
            if length_m <= 0 or width_m <= 0:
                raise ValueError("Perspective correction: calibration lengths must be > 0")
            src = np.float32([q1, q2, q3, q4])
            dst = np.float32([[0,0],[length_m,0],[length_m,width_m],[0,width_m]])
            H = cv2.getPerspectiveTransform(src, dst)
            return {"H": H, "length_m": length_m, "width_m": width_m, "points": [p1,p2,p3,p4], "four_side_lengths_m": raw4}
        except Exception:
            if silent:
                return None
            raise

    @staticmethod
    def _run3_transform_point(point, perspective):
        if perspective is None or point is None:
            return point
        arr = np.array([[list(point)]], dtype=np.float32)
        mapped = cv2.perspectiveTransform(arr, perspective["H"])[0,0]
        return float(mapped[0]), float(mapped[1])

    @staticmethod
    def _run3_metric_segment_distance_sum(points):
        if len(points) < 2:
            return 0.0
        return sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a,b in zip(points, points[1:]))

    @staticmethod
    def _run3_unique_output_path(path):
        base, ext = os.path.splitext(path)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        candidate = f"{base}_{stamp}{ext}"
        if not os.path.exists(candidate):
            return candidate
        for i in range(1,1000):
            candidate = f"{base}_{stamp}_{i}{ext}"
            if not os.path.exists(candidate):
                return candidate
        raise IOError(f"Could not create unique output path for {path}")

    def _run3_open_csv_safe(self, desired_path):
        try:
            return open(desired_path, "w", newline="", encoding="utf-8-sig"), desired_path
        except PermissionError:
            fallback = self._run3_unique_output_path(desired_path)
            return open(fallback, "w", newline="", encoding="utf-8-sig"), fallback

    def validate_run3_settings(self):
        keys = ("speed", "gap", "lc", "pet", "ttc", "ldp")
        enabled = {k: bool(getattr(self, f"run3_{k}_enabled_var").get()) for k in keys}
        if not any(enabled.values()):
            return True

        if not self.run3_site_id_var.get().strip():
            raise ValueError("Run 3 Site_ID is required when Run 3 is enabled.")

        if self.run3_perspective_enabled_var.get():
            self._run3_get_perspective_matrix(silent=False)

        # Every Run 3 indicator now uses metric coordinates.
        self._run3_float(self.run3_ppm_var.get(), "PPM")
        self._run3_float(self.run3_lateral_axis_angle_var.get(), "road direction angle (deg)", positive=False)

        def need_zone(var_map, label):
            if not any(v.get() for v in var_map.values()):
                raise ValueError(f"Select at least one Zone for {label}.")

        if enabled["speed"]:
            need_zone(self.run3_speed_zone_vars, "Speed")
            self._run3_float(self.run3_speed_smoothing_var.get(), "speed smoothing samples")
            self._run3_float(self.run3_speed_max_var.get(), "max plausible speed (km/h)")
        if enabled["lc"]:
            need_zone(self.run3_lc_zone_vars, "Lateral Clearance")
            self._run3_float(self.run3_lc_heading_window_var.get(), "LC heading window (s)")
        if enabled["lc"] or enabled["ttc"]:
            for name in RUN3_VEHICLE_CLASSES:
                self._run3_float(self.run3_width_vars[name].get(), f"vehicle width for {name}")
        if enabled["lc"]:
            for name in RUN3_VEHICLE_CLASSES:
                self._run3_float(self.run3_length_vars[name].get(), f"vehicle length for {name} (Lateral Clearance needs the length)")
        if enabled["ttc"]:
            need_zone(self.run3_ttc_zone_vars, "TTC")
            for name in RUN3_VEHICLE_CLASSES:
                self._run3_float(self.run3_length_vars[name].get(), f"vehicle length for {name}")
            self._run3_float(self.run3_ttc_max_record_var.get(), "TTC record limit (s)")
            self._run3_float(self.run3_ttc_heading_max_var.get(), "TTC heading limit (deg)")
            self._run3_float(self.run3_ttc_velocity_window_var.get(), "TTC velocity window (s)")
            self._run3_float(self.run3_ttc_min_speed_var.get(), "TTC minimum follower speed (km/h)", positive=False)
            if self.run3_ttc_side_enabled_var.get():
                self._run3_float(self.run3_ttc_side_factor_var.get(), "TTC side window factor", positive=False)
                self._run3_float(self.run3_ttc_side_margin_var.get(), "TTC side extra time (s)", positive=False)
                angle = self._run3_float(self.run3_ttc_side_angle_var.get(), "TTC side minimum path angle (deg)")
                if not 0 < angle < 90:
                    raise ValueError("Run 3 TTC side minimum path angle must be between 0 and 90 degrees.")
                if float(self.run3_ttc_side_factor_var.get()) < 0 or float(self.run3_ttc_side_margin_var.get()) < 0:
                    raise ValueError("Run 3 TTC side window factor and extra time must not be negative.")
        for key in RUN3_GEOMETRY_KEYS:
            text = str(self.run3_geometry_vars[key].get()).strip()
            if text:   # must be numeric when entered (lane widths are required when LDP is enabled)
                self._run3_float(text, f"road geometry {key}", positive=(key != "median_m"))
        if enabled["ldp"]:
            need_zone(self.run3_ldp_zone_vars, "LDP")
            self._run3_float(self.run3_ldp_smoothing_var.get(), "LDP smoothing samples")
            for key in ("lane_entry_motorcycle_m", "lane_entry_car_m", "lane_opp_motorcycle_m", "lane_opp_car_m"):
                self._run3_float(self.run3_geometry_vars[key].get(), f"road geometry {key} (required by LDP)")
        if enabled["pet"]:
            need_zone(self.run3_pet_zone_vars, "PET (Zone 3 / Zone 6)")
            self._run3_float(self.run3_pet_interaction_distance_var.get(), "PET interaction distance (m)")
            self._run3_float(self.run3_pet_threshold_var.get(), "PET threshold (s)")
            if str(self.run3_pet_max_var.get()).strip():
                self._run3_float(self.run3_pet_max_var.get(), "PET max (s)")
        if enabled["gap"]:
            if not any([
                self.run3_gap_subject_134_var.get(),
                self.run3_gap_subject_1367_var.get(),
                self.run3_gap_subject_5631_var.get(),
            ]):
                raise ValueError("Select at least one Gap Acceptance subject movement.")
            self._run3_float(self.run3_waiting_speed_threshold_var.get(), "Gap Acceptance stop speed threshold (km/h)")
            self._run3_float(self.run3_hold_min_duration_var.get(), "Gap Acceptance stop minimum duration (s)")
            if not (self.run3_use_raff_var.get() or self.run3_use_mle_var.get()):
                raise ValueError("Select at least one Critical Gap method.")
            self.run3_reference_mapping_text = (
                self.run3_reference_text.get("1.0", "end-1c").strip()
                if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text.strip()
            )
        return True

    def collect_run3_warnings(self):
        """Non-blocking pre-flight checks. Returns a list of warning strings.

        These are situations that would otherwise produce empty or partial
        Run 3 output without any message (the run still completes).
        """
        warnings = []
        keys = {
            "speed": ("Speed", self.run3_speed_zone_vars),
            "lc": ("Lateral Clearance", self.run3_lc_zone_vars),
            "ttc": ("TTC", self.run3_ttc_zone_vars),
            "pet": ("PET", self.run3_pet_zone_vars),
            "ldp": ("LDP", self.run3_ldp_zone_vars),
        }
        # A Zone file (and its Lines) belongs to ONE camera view. Warn when the Video is a different one.
        zone_video = str(getattr(self, "zone_source_video", "") or "").strip()
        video_now = self.video_var.get().strip()
        if self.zone_line_config_var.get().strip() and zone_video and video_now:
            if os.path.basename(zone_video).lower() != os.path.basename(video_now).lower():
                warnings.append(
                    f"The Zone file was drawn on the video '{os.path.basename(zone_video)}' but the Video to process is "
                    f"'{os.path.basename(video_now)}'. Zones, Lines and the scale (PPM / Perspective) belong to one camera "
                    "view; with another video the results (Movement, LDP, Gap Acceptance ...) will be empty or wrong.")
            else:
                aw, ah = self._actual_video_size()
                zw, zh = getattr(self, "zone_source_width", None), getattr(self, "zone_source_height", None)
                if aw and ah and zw and zh and abs(aw / float(ah) - zw / float(zh)) > 0.02:
                    warnings.append(
                        f"The Zone file was drawn on {zw}x{zh} frames but the video is {aw}x{ah} (different shape): "
                        "the Zones cannot be scaled correctly.")
        position = str(self.trajectory_position_var.get()).strip()
        if (bool(self.run3_perspective_enabled_var.get()) or self.run3_ppm_var.get().strip()) and not position.startswith("Bottom"):
            warnings.append(
                f"Trajectory Position = '{position}' (ขั้น ② ทางแยก): PPM / Perspective Calibration วัดบนพื้นถนน แต่จุดนี้ไม่ใช่จุดที่ล้อแตะพื้น "
                "(เช่น Top = หัวคนขี่) ความเร็วและระยะจะเพี้ยน (โดยทั่วไปสูงเกินจริง) — แนะนำ Bottom")
        defined = {z for z in ZONE_IDS if len(self.zones.get(f"Zone {z}", [])) >= 3}
        any_enabled = any(bool(getattr(self, f"run3_{k}_enabled_var").get())
                          for k in ("speed", "gap", "lc", "pet", "ttc", "ldp"))
        if any_enabled and not defined:
            warnings.append(
                "Run 3 is enabled but no Zone is loaded. Zones are required for every "
                "Run 3 indicator, so all Run 3 outputs will be empty."
            )
            return warnings
        for key, (label, var_map) in keys.items():
            if not bool(getattr(self, f"run3_{key}_enabled_var").get()):
                continue
            missing = sorted(z for z, v in var_map.items() if v.get() and z not in defined)
            if missing:
                warnings.append(
                    f"{label}: Zone {', '.join(str(z) for z in missing)} selected but not defined in the "
                    f"loaded Zone file (defined: {', '.join(str(z) for z in sorted(defined))}). "
                    "Those zones will produce no data."
                )

        # Gap Acceptance: a Line per conflicting stream gives the best reference time; without a
        # usable Line the program uses the time a vehicle first enters the stream's origin zone.
        if bool(self.run3_gap_enabled_var.get()):
            subjects = [m for m, var in (("1-3-4", self.run3_gap_subject_134_var),
                                         ("1-3-6-7", self.run3_gap_subject_1367_var),
                                         ("5-6-3-1", self.run3_gap_subject_5631_var)) if var.get()]
            text = (self.run3_reference_text.get("1.0", "end-1c")
                    if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text)
            fallback = (" For such streams the program uses the time each vehicle first enters the origin zone "
                        "of the stream instead (more approximate; button 'วาด Line…' gives better results).")
            try:
                mapping = self._run3_parse_reference_mapping(text)
            except Exception as exc:
                mapping = None
                warnings.append(f"Gap Acceptance: Reference Line Mapping is invalid ({exc})." + fallback)
            if mapping is not None:
                site = self.run3_site_id_var.get().strip()
                site_map = {mv: ln for (st, mv), ln in mapping.items() if str(st).strip() == site}
                needed = sorted({c for m in subjects for c in RUN3_GAP_CONFLICT_MAP[m]})
                missing = [c for c in needed if c not in site_map]
                undrawn = sorted({f"{ln} ({c})" for c, ln in site_map.items()
                                  if c in needed and len(self.lines.get(ln, [])) != 2})
                parts = []
                if missing:
                    parts.append("no Line mapped for stream(s) " + ", ".join(missing) + f" (Site_ID '{site}')")
                if undrawn:
                    parts.append("mapped Line is not drawn/loaded in the Zone/Line file: " + ", ".join(undrawn))
                if parts:
                    warnings.append("Gap Acceptance: " + "; ".join(parts) + "." + fallback)
        return warnings

    # ========================================================
    # DEVICE
    # ========================================================

    def offer_restart_with_cuda_python(self, error_text):
        """GPU selected but this Python has a CPU-only PyTorch: look for another installed
        Python with CUDA and offer to reopen PK Studio with it. True = restarting."""
        try:
            self.status_var.set("กำลังหา Python ที่ใช้ GPU ได้...")
            self.root.update_idletasks()
            cuda_python = find_cuda_python()
        except Exception:
            cuda_python = None
        if not cuda_python:
            return False
        if not messagebox.askyesno(
                "CUDA / Device Error",
                error_text + "\n\n"
                "พบ Python ที่ใช้ GPU ได้:\n" + cuda_python + "\n\n"
                "ปิดหน้าต่างนี้แล้วเปิด PK Studio ใหม่ด้วย Python ตัวนั้นเลยหรือไม่?\n"
                "(ค่าที่ยังไม่ได้บันทึกจะหาย — กด No เพื่อใช้ CPU ต่อ)"):
            return False
        env = os.environ.copy()
        env[BOOTSTRAP_MARKER] = "1"
        try:
            subprocess.Popen([cuda_python, os.path.abspath(sys.argv[0]), *sys.argv[1:]], env=env)
        except Exception as exc:
            messagebox.showerror("Restart", f"เปิดใหม่ไม่สำเร็จ: {exc}")
            return False
        self.root.after(200, self.root.destroy)
        return True

    def resolve_device(self):

        selected = self.device_var.get()

        if selected == "CPU":
            return "cpu"

        if selected == "GPU 0":

            if not torch.cuda.is_available():

                raise RuntimeError(
                    "GPU 0 was selected, but this PyTorch environment "
                    "cannot use CUDA\n\n"
                    f"Python:\n{sys.executable}\n\n"
                    f"PyTorch:\n{torch.__version__}\n\n"
                    "CUDA available: False"
                )

            return "cuda:0"

        if torch.cuda.is_available():
            return "cuda:0"

        return "cpu"

    # ========================================================
    # FRAME SKIP
    # ========================================================

    def get_frame_skip(self):

        text = self.frame_skip_var.get()

        if text.startswith("NO"):
            return 1

        if "1 - " in text:
            return 2

        if "2 - " in text:
            return 3

        if "3 - " in text:
            return 4

        if "4 - " in text:
            return 5

        return 1

    def get_frame_skip_from_text(self, text):

        if text.startswith("NO"):
            return 1

        if "1 - " in text:
            return 2

        if "2 - " in text:
            return 3

        if "3 - " in text:
            return 4

        if "4 - " in text:
            return 5

        return 1

    # ========================================================
    # SAFE RUN NAME
    # ========================================================

    def safe_filename(self, name):

        invalid = '<>:"/\\|?*'

        for char in invalid:
            name = name.replace(char, "_")

        return name.strip()

    # ========================================================
    # BYTE TRACK YAML
    # ========================================================

    @staticmethod
    def _tracker_signature(settings):
        """Settings that must be the same for a tracker to be carried over to the next clip."""
        keys = ("model", "tracker", "confidence", "iou", "img_size", "track_high", "track_low", "new_track",
                "track_buffer", "match_threshold", "precision", "device", "frame_skip")
        return tuple(str(settings.get(k)) for k in keys)

    def create_bytetrack_yaml(self, output_dir, run_name="Run"):

        yaml_path = os.path.join(
            output_dir,
            "ByteTrack.yaml"
        )

        text = (
            "tracker_type: bytetrack\n"
            f"track_high_thresh: "
            f"{float(self.track_high_var.get())}\n"
            f"track_low_thresh: "
            f"{float(self.track_low_var.get())}\n"
            f"new_track_thresh: "
            f"{float(self.new_track_var.get())}\n"
            f"track_buffer: "
            f"{int(self.track_buffer_var.get())}\n"
            f"match_thresh: "
            f"{float(self.match_threshold_var.get())}\n"
            "fuse_score: True\n"
        )

        with open(
            yaml_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(text)

        return yaml_path

    # ========================================================
    # START
    # ========================================================

    # ========================================================
    # PAUSE
    # ========================================================

    def toggle_pause(self):

        if not self.running:
            return

        if self.pause_event.is_set():

            self.pause_event.clear()

            self.pause_button.config(
                text="▶ RESUME"
            )

            self.status_var.set("Paused")

        else:

            self.pause_event.set()

            self.pause_button.config(
                text="Ⅱ PAUSE"
            )

            self.status_var.set(
                "Processing..."
            )

    # ========================================================
    # STOP
    # ========================================================

    def request_stop(self):

        if not self.running:
            return

        self.stop_event.set()
        self.pause_event.set()

        self.status_var.set(
            "Stopping..."
        )

    # ========================================================
    # UI UPDATE
    # ========================================================

    def post_ui(self, fn):
        """Thread-safe: ask the main (Tk) thread to run fn() soon."""
        self._ui_queue.put(fn)

    def _poll_ui_queue(self):
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                try:
                    fn()
                except Exception:
                    log.exception("UI callback failed")
        except queue.Empty:
            pass
        try:
            self.root.after(50, self._poll_ui_queue)
        except tk.TclError:
            pass   # window already closed

    def update_ui(
        self,
        status=None,
        progress=None,
        timing=None
    ):

        def update():

            if status is not None:
                self.status_var.set(status)

            if progress is not None:
                self.progress_var.set(progress)

            if timing is not None:
                self.time_var.set(timing)

        self.post_ui(update)

    # ========================================================
    # PROCESSING
    # ========================================================

    def run_processing(self, settings):

        cap = None
        writer = None
        reader = None
        csv_file = None

        try:

            model_path = settings["model"]
            video_path = settings["video"]
            output_dir = settings["output"]

            # "Continues the previous clip": the tracker of the clip analysed right before this one is carried on, so a
            # vehicle that was being tracked keeps its ID, and new vehicles get the next numbers. The time range, the
            # recording and every result file stay separate for each clip.
            carry = self._carry if settings.get("continue_tracker") else None
            self._carry = None                  # only the clip run right before can be continued
            tracker_sig = self._tracker_signature(settings)
            if carry is not None and carry.get("sig") != tracker_sig:
                carry = None                    # the tracker / detection settings changed: start a new tracker
            # vehicle IDs continue after the previous clips of the folder (a continued clip keeps its predecessor's numbering)
            id_offset = carry["id_offset"] if carry else int(settings.get("id_offset", 0) or 0)

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            run_name = self.safe_filename(
                settings["run_name"]
            )

            rt = self._rt or {}
            self._run3_live_perspective = (self._run3_cfg or {}).get("perspective")

            # =========================================================
            # CSV OUTPUTS — ONLY 3 MAIN CSV FILES
            # =========================================================
            # 1) Detection_Records.csv   = raw per-frame detections
            # 2) ID_Zone_Summary.csv     = one summary per tracked ID
            # 3) Zone_Summary.csv        = one aggregate summary per Zone
            #
            # Legacy Research_*.csv files are intentionally NOT exported.
            # This keeps the output folder limited to the agreed 3 CSV files.

            output_video = os.path.join(
                output_dir,
                "Tracking_Result.mp4"
            )

            output_csv = os.path.join(
                output_dir,
                "Detection_Records.csv"
            )

            output_id_zone_summary = os.path.join(
                output_dir,
                "ID_Zone_Summary.csv"
            )

            output_zone_summary = os.path.join(
                output_dir,
                "Zone_Summary.csv"
            )

            # Non-CSV metadata files are still allowed.
            output_summary = os.path.join(
                output_dir,
                "Run_Summary.json"
            )

            output_settings = os.path.join(
                output_dir,
                "Settings.json"
            )

            output_tracker_yaml = os.path.join(
                output_dir,
                "ByteTrack.yaml"
            )

            output_measurement_summary = os.path.join(
                output_dir,
                "Measurement_Summary.json"
            )

            with open(
                output_settings,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    settings,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            device = self.resolve_device()

            precision = settings["precision"]

            use_fp16 = False

            if precision == "FP16":

                if device.startswith("cuda"):
                    use_fp16 = True

            elif precision == "Auto":

                if device.startswith("cuda"):
                    try:
                        dev_index = int(device.split(":")[1]) if ":" in device else 0
                    except ValueError:
                        dev_index = 0
                    use_fp16 = fp16_is_faster(dev_index)       # FP32 on the GTX 16 series, where FP16 is much slower

            if precision == "FP16" and not device.startswith("cuda"):

                raise RuntimeError(
                    "FP16 requires a CUDA/GPU device"
                )

            self.update_ui(
                status=(
                    "กำลังโหลดโมเดล... "
                    f"({device})"
                )
            )

            print()
            print("=" * 75)
            print("PK Studio - Vehicle Traffic Analysis")
            print("RUN 1 + 2 : Detection + Tracking + Trajectory + Zone/Line Measurement")
            print("=" * 75)
            print()
            print("Python      :", sys.executable)
            print("PyTorch     :", torch.__version__)
            print("CUDA        :", torch.cuda.is_available())

            if torch.cuda.is_available():
                print(
                    "GPU         :",
                    torch.cuda.get_device_name(0)
                )

            print()
            print("Run Name    :", run_name)
            print("Model       :", model_path)
            print("Video       :", video_path)
            print("Output      :", output_dir)
            print()
            print("Device      :", device)
            print(
                "Precision   :",
                "FP16" if use_fp16 else "FP32"
            )
            print()

            model = carry["model"] if carry else YOLO(
                model_path
            )

            cap = cv2.VideoCapture(
                video_path
            )

            if not cap.isOpened():

                raise RuntimeError(
                    "Unable to open video"
                )

            width = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_WIDTH
                )
            )

            height = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_HEIGHT
                )
            )

            fps = cap.get(
                cv2.CAP_PROP_FPS
            )

            if fps <= 0:
                fps = 30.0

            total_frames = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            # Analysis window and recording window (times are video times; frame N is at (N-1)/fps)
            video_total_frames = total_frames
            a_start = parse_clock_time(settings.get("analysis_start_s", ""))
            a_end = parse_clock_time(settings.get("analysis_end_s", ""))
            first_frame, last_frame = window_frames(a_start, a_end, fps, total_frames)
            r_start = parse_clock_time(settings.get("record_start_s", ""))
            r_end = parse_clock_time(settings.get("record_end_s", ""))
            rec_first, rec_last = first_frame, last_frame
            if r_start is not None:
                rec_first = max(first_frame, window_frames(r_start, None, fps, 0)[0])
            if r_end is not None:
                rec_end_frame = window_frames(None, r_end, fps, 0)[1]
                rec_last = rec_end_frame if rec_last is None else min(rec_last, rec_end_frame)
            rec_last_eff = rec_last if rec_last is not None else 10 ** 12
            window_start0 = first_frame - 1
            if last_frame is not None:
                total_frames = last_frame      # progress / ETA / "Frame: i/total" run to the end of the window

            if settings["save_video"]:

                fourcc = cv2.VideoWriter_fourcc(
                    *"mp4v"
                )

                writer = cv2.VideoWriter(
                    output_video,
                    fourcc,
                    fps,
                    (width, height)
                )

                if not writer.isOpened():

                    raise RuntimeError(
                        "Unable to create output video"
                    )

                writer = BackgroundVideoWriter(writer)      # encoding runs beside the detection

            tracker_name = settings["tracker"]

            if tracker_name == "ByteTrack":

                tracker_path = (
                    self.create_bytetrack_yaml(
                        output_dir,
                        run_name
                    )
                )

                # Keep the exact research filename in the run summary.
                output_tracker_yaml = tracker_path

            else:

                tracker_path = "botsort.yaml"
                output_tracker_yaml = None

            if settings["save_csv"]:

                csv_file = open(
                    output_csv,
                    "w",
                    newline="",
                    encoding="utf-8-sig"
                )

                csv_writer = csv.writer(
                    csv_file
                )

                csv_writer.writerow([
                    "frame", "timestamp", "track_id", "class_id", "class_name",
                    "confidence", "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2",
                    "bbox_width", "bbox_height", "bbox_area",
                    "trajectory_x", "trajectory_y",
                    "trajectory_position", "trajectory_offset",
                    "zone"
                ])

            else:

                csv_writer = None

            # =================================================
            # INTERNAL / LEGACY RESEARCH WRITERS
            # =================================================
            # Keep these as no-op writers so the existing tracking logic can
            # continue calculating internal statistics without creating extra
            # CSV files on disk.
            null_writer = _NullCSVWriter()
            track_stats_file = null_writer
            id_switch_file = null_writer
            detection_loss_file = null_writer
            processing_log_file = null_writer
            measurement_events_file = null_writer
            line_summary_file = null_writer

            track_stats_writer = null_writer
            id_switch_writer = null_writer
            detection_loss_writer = null_writer
            processing_log_writer = null_writer
            measurement_events_writer = null_writer
            line_summary_writer = null_writer

            # The two summary CSVs are real output files.
            zone_summary_file = open(
                output_zone_summary,
                "w",
                newline="",
                encoding="utf-8-sig"
            )
            zone_summary_writer = csv.writer(zone_summary_file)
            zone_summary_writer.writerow([
                "zone", "unique_ids", "total_entries", "average_duration_seconds",
                "min_duration_seconds", "max_duration_seconds",
                "first_entry_timestamp", "last_entry_timestamp"
            ])

            id_zone_summary_file = open(
                output_id_zone_summary,
                "w",
                newline="",
                encoding="utf-8-sig"
            )
            id_zone_summary_writer = csv.writer(id_zone_summary_file)
            id_zone_summary_writer.writerow([
                "track_id", "class_name", "first_seen_timestamp", "last_seen_timestamp",
                "track_duration_seconds", "first_zone", "last_zone", "zone_sequence",
                "unique_zones_visited", "zone_transition_count", "total_zone_time_seconds"
            ])

            # Integrated measurement state. This is updated directly from Run 1 tracking.
            zone_track_state = {}
            line_track_state = {}
            zone_assignment_summary = defaultdict(lambda: defaultdict(int))
            trajectory_position = settings.get("trajectory_position", self.trajectory_position_var.get())
            trajectory_offset = float(settings.get("trajectory_offset", self.trajectory_offset_var.get() or 0))
            zone_confirmation_frames = 1
            zone_entry_count = defaultdict(int)
            zone_exit_count = defaultdict(int)
            line_cross_count = defaultdict(int)

            # Per-track research state.
            track_stats = {}
            active_tracks = {}
            recent_lost_tracks = deque(maxlen=100)
            id_switch_warning_count = 0
            detection_loss_count = 0
            max_active_tracks = 0
            total_frames_with_detection = 0
            input_finished = False

            conf = float(
                settings["confidence"]
            )

            iou = float(
                settings["iou"]
            )

            img_size = int(
                settings["img_size"]
            )

            frame_skip = self.get_frame_skip_from_text(
                settings["frame_skip"]
            )

            csv_flush_every = int(
                settings["csv_flush"]
            )

            trail_length = int(
                settings["trail_length"]
            )

            show_preview = settings[
                "show_preview"
            ]

            self.validate_measurements()
            measurement_enabled = (
                any(len(v) >= 3 for v in self.zones.values())
                or any(len(v) >= 2 for v in self.lines.values())
            )
            if not hasattr(self, "zone_meta"):
                self.zone_meta = {}
            print("Measurement :", "Enabled (Zones/Lines integrated)" if measurement_enabled else "Disabled")
            if measurement_enabled:
                print("Zones       :", [k for k, v in self.zones.items() if len(v) >= 3])
                print("Lines       :", [k for k, v in self.lines.items() if len(v) == 2])
                print("Trajectory Position:", self.trajectory_position_var.get())
                print("Trajectory Offset  :", self.trajectory_offset_var.get(), "%")

            window_name = "PK Studio - Run 1"
            # V27: drawing is only needed when frames are shown or saved.
            render_needed = bool(show_preview) or writer is not None

            if show_preview:

                cv2.namedWindow(
                    window_name,
                    cv2.WINDOW_NORMAL
                )

                cv2.resizeWindow(
                    window_name,
                    width,
                    height
                )

            trails = {}
            zones_available_run = any(len(self.zones.get(z, [])) >= 3 for z in ZONE_NAMES)

            frame_index = 0
            if first_frame > 1:
                # jump to the start of the analysis window (frame_index keeps the original video frame number)
                cap.set(cv2.CAP_PROP_POS_FRAMES, first_frame - 1)
                if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) != first_frame - 1:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)      # seeking not exact in this file: read forward instead
                    for _skip in range(first_frame - 1):
                        if not cap.grab():
                            break
                frame_index = first_frame - 1
            processed_frames = 0
            total_detections = 0
            untracked_detections = 0

            # decoding runs beside the detection; a frame is only skipped (not decoded) when nothing uses it
            reader = BackgroundFrameReader(
                cap,
                lambda n: not (frame_skip > 1 and not render_needed and (n % frame_skip) != 0),
                frame_index,
                last_frame,
            )

            start_time = time.time()

            print()
            print("Image Size  :", img_size)
            print("Confidence  :", conf)
            print("IoU         :", iou)
            print("Tracker     :", tracker_name)
            print("Frame Skip  :", frame_skip)
            print()
            print("Video       :", width, "x", height)
            print("FPS         :", fps)
            print("Total Frame :", total_frames)
            print()
            print("=" * 75)
            print()

            self.update_ui(
                status=(
                    "Processing... "
                    f"Device={device} | "
                    f"{'FP16' if use_fp16 else 'FP32'}"
                )
            )

            # =================================================
            # MAIN LOOP
            # =================================================

            while True:

                if self.stop_event.is_set():
                    break

                self.pause_event.wait()

                if self.stop_event.is_set():
                    break

                if last_frame is not None and frame_index >= last_frame:
                    input_finished = True      # end of the analysis window
                    break

                # V27: skipped frames are only grabbed (not decoded) when
                # nothing has to be drawn/saved for them.
                if frame_skip > 1 and not render_needed and (frame_index % frame_skip) != 0:
                    if not reader.next()[0]:
                        input_finished = True
                        break
                    frame_index += 1
                    if frame_index % 50 == 0:
                        self.update_ui(progress=f"{frame_index}/{total_frames}")
                    continue

                success, frame = reader.next()

                if not success:
                    input_finished = True
                    break

                frame_index += 1

                # Draw Zone overlay BEFORE detections/tracks so bounding boxes and
                # trajectory lines are rendered on top of the translucent Zone.
                if measurement_enabled and render_needed:
                    self.draw_measurement_overlay(
                        frame, frame_index, fps, zone_track_state, line_track_state,
                        zone_entry_count, line_cross_count
                    )

                should_process = (
                    (frame_index - 1)
                    % frame_skip
                    == 0
                )

                if should_process:

                    processed_frames += 1

                    track_kwargs = {
                        "persist": True,
                        "tracker": tracker_path,
                        "conf": conf,
                        "iou": iou,
                        "imgsz": img_size,
                        "device": device,
                        "verbose": False,
                    }

                    if use_fp16:

                        # Ultralytics >= 8.4 renamed half -> quantize (half is deprecated);
                        # older versions only know half.
                        try:
                            from ultralytics.cfg import DEFAULT_CFG_DICT as _ucfg
                            _fp16_key = "quantize" if "quantize" in _ucfg else "half"
                        except Exception:
                            _fp16_key = "half"
                        track_kwargs[_fp16_key] = 16 if _fp16_key == "quantize" else True

                    results = model.track(
                        frame,
                        **track_kwargs
                    )

                    result = results[0]
                    boxes = result.boxes

                    if (
                        boxes is not None
                        and boxes.xyxy is not None
                    ):

                        xyxy = (
                            boxes.xyxy
                            .cpu()
                            .numpy()
                        )

                        if boxes.conf is not None:

                            confs = (
                                boxes.conf
                                .cpu()
                                .numpy()
                            )

                        else:

                            confs = []

                        if boxes.cls is not None:

                            classes = (
                                boxes.cls
                                .cpu()
                                .numpy()
                            )

                        else:

                            classes = []

                        if boxes.id is not None:

                            track_ids = (
                                boxes.id
                                .cpu()
                                .numpy()
                                .astype(int)
                            )

                        else:

                            track_ids = (
                                [-1] * len(xyxy)
                            )

                        for i in range(
                            len(xyxy)
                        ):

                            x1, y1, x2, y2 = map(
                                int,
                                xyxy[i]
                            )

                            confidence = (
                                float(confs[i])
                                if i < len(confs)
                                else 0.0
                            )

                            class_id = (
                                int(classes[i])
                                if i < len(classes)
                                else -1
                            )

                            track_id = (
                                int(track_ids[i])
                                if i < len(track_ids)
                                else -1
                            )
                            if track_id >= 0:
                                track_id += id_offset

                            try:

                                if isinstance(
                                    result.names,
                                    dict
                                ):

                                    class_name = (
                                        result.names.get(
                                            class_id,
                                            str(class_id)
                                        )
                                    )

                                else:

                                    class_name = (
                                        result.names[
                                            class_id
                                        ]
                                    )

                            except Exception:

                                class_name = str(
                                    class_id
                                )

                            center_x = int(
                                (x1 + x2) / 2
                            )

                            center_y = int(
                                (y1 + y2) / 2
                            )

                            total_detections += 1
                            if track_id < 0:
                                untracked_detections += 1

                            if track_id >= 0:
                                # Create/update research statistics for this track.
                                timestamp = (frame_index - 1) / fps
                                state = track_stats.setdefault(
                                    track_id,
                                    {
                                        "class_id": class_id,
                                        "class_name": class_name,
                                        "first_frame": frame_index,
                                        "last_frame": frame_index,
                                        "observed_frames": 0,
                                        "detection_count": 0,
                                        "loss_events": 0,
                                        "max_gap_frames": 0,
                                        "confidence_sum": 0.0,
                                        "center_x_sum": 0.0,
                                        "center_y_sum": 0.0,
                                        "total_distance_px": 0.0,
                                        "previous_center": None,
                                    }
                                )

                                # A gap before this observation is a detection-loss event.
                                if state["last_frame"] < frame_index - 1:
                                    gap = frame_index - state["last_frame"] - 1
                                    state["loss_events"] += 1
                                    state["max_gap_frames"] = max(
                                        state["max_gap_frames"], gap
                                    )
                                    detection_loss_count += 1
                                    detection_loss_writer.writerow([
                                        track_id,
                                        state["class_name"],
                                        state["last_frame"] + 1,
                                        frame_index - 1,
                                        gap,
                                        f"{state['last_frame'] / fps:.6f}",
                                        f"{(frame_index - 1) / fps:.6f}",
                                        True,
                                        frame_index,
                                    ])

                                state["last_frame"] = frame_index
                                state["observed_frames"] += 1
                                state["detection_count"] += 1
                                state["confidence_sum"] += confidence
                                state["center_x_sum"] += center_x
                                state["center_y_sum"] += center_y

                                if state["previous_center"] is not None:
                                    px, py = state["previous_center"]
                                    state["total_distance_px"] += (
                                        ((center_x - px) ** 2 + (center_y - py) ** 2) ** 0.5
                                    )

                                state["previous_center"] = (center_x, center_y)

                                # Re-association heuristic:
                                # if a recently lost track and a new track appear very
                                # close together, record a warning rather than claiming
                                # a definite ID switch.
                                for lost in list(recent_lost_tracks):
                                    if (
                                        lost["track_id"] != track_id
                                        and lost["class_id"] == class_id
                                        and frame_index - lost["last_frame"] <= 10
                                    ):
                                        dx = center_x - lost["center_x"]
                                        dy = center_y - lost["center_y"]
                                        distance = (dx * dx + dy * dy) ** 0.5
                                        bbox_diag = (
                                            ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                                        )
                                        threshold = max(50.0, bbox_diag * 0.75)

                                        if distance <= threshold:
                                            id_switch_warning_count += 1
                                            id_switch_writer.writerow([
                                                frame_index,
                                                f"{timestamp:.6f}",
                                                lost["track_id"],
                                                track_id,
                                                class_name,
                                                f"{distance:.2f}",
                                                "New ID appeared near recently lost ID",
                                                "WARNING",
                                            ])
                                            break

                                active_tracks[track_id] = {
                                    "track_id": track_id,
                                    "last_frame": frame_index,
                                    "center_x": center_x,
                                    "center_y": center_y,
                                    "class_id": class_id,
                                    "class_name": class_name,
                                }

                                # ==============================
                                # INTEGRATED ZONE MEASUREMENT
                                # ==============================
                                if measurement_enabled:
                                    # Zone membership uses the selected Trajectory Position only.
                                    # The bounding box itself is not used for Zone assignment.
                                    point = self.get_zone_reference_point(x1, y1, x2, y2)
                                    candidate, raw_confidence, overlap_map, custom_point, decision_scores = self.assign_zone_candidate(
                                        x1, y1, x2, y2
                                    )

                                    # Zone membership is determined only by the selected
                                    # Trajectory Position. The bounding-box area is not used
                                    # for Zone assignment.
                                    method_now = "Trajectory Position"
                                    no_zone = candidate is None
                                    zstate = zone_track_state.setdefault(track_id, {
                                        "candidate_zone": None,
                                        "candidate_count": 0,
                                        "candidate_confidence": 0.0,
                                        "confirmed_zone": None,
                                        "confirmed_confidence": 0.0,
                                        "previous_confirmed_zone": None,
                                        "previous_confirmed_point": None,
                                        "no_zone_count": 0,
                                        "zone_states": {},
                                        # Short trajectory history used only for the
                                        # on-screen live-speed display. This does not
                                        # replace the research calculation.
                                        "live_speed_history": [],
                                        "live_speed_kmh": None,
                                    })

                                    zstate["no_zone_count"] = 0 if not no_zone else zstate.get("no_zone_count", 0) + 1

                                    confirmed_zone, zone_changed = self.confirm_zone(
                                        zstate, candidate, raw_confidence,
                                        frame_index, 1
                                    )
                                    zstate["last_point"] = point
                                    zstate["last_bbox"] = (x1, y1, x2, y2)
                                    zstate["last_candidate"] = candidate
                                    zstate["last_candidate_confidence"] = raw_confidence
                                    zstate["last_overlap"] = overlap_map
                                    zstate["last_method"] = method_now

                                    # --------------------------------------------------
                                    # LIVE SPEED FOR ON-SCREEN OBJECT LABEL
                                    # --------------------------------------------------
                                    # Uses the same Trajectory Position point and the
                                    # configured PPM. A short rolling window is used
                                    # only to make the displayed speed less noisy.
                                    # research values are still calculated later
                                    # by Run 3 and are not changed by this display value.
                                    live_ppm = rt.get("live_ppm", 0.0)
                                    hist = zstate.get("live_speed_history", [])
                                    hist.append(((frame_index - 1) / fps, point[0], point[1]))
                                    if len(hist) > 6:
                                        hist = hist[-6:]
                                    zstate["live_speed_history"] = hist
                                    zstate["live_speed_kmh"] = None
                                    if len(hist) >= 2:
                                        t0 = hist[0][0]
                                        t1 = hist[-1][0]
                                        dt_live = float(t1) - float(t0)
                                        if dt_live > 0:
                                            live_persp = getattr(self, "_run3_live_perspective", None)
                                            if live_persp is not None:
                                                metric_points = [self._run3_transform_point((hh[1],hh[2]), live_persp) for hh in hist]
                                                dist_m_live = self._run3_metric_segment_distance_sum(metric_points)
                                                zstate["live_speed_kmh"] = (dist_m_live / dt_live) * 3.6
                                            elif live_ppm > 0:
                                                dist_px_live = self._run3_segment_distance_sum([(hh[1],hh[2]) for hh in hist])
                                                zstate["live_speed_kmh"] = (dist_px_live / live_ppm) / dt_live * 3.6

                                    if candidate:
                                        zone_assignment_summary[candidate]["observations"] += 1
                                    if confirmed_zone:
                                        zone_assignment_summary[confirmed_zone]["confirmed_frames"] += 1

                                    timestamp_now = (frame_index - 1) / fps
                                    previous_zone_point = zstate.get("previous_confirmed_point")
                                    previous_confirmed_zone = zstate.get("previous_confirmed_zone")

                                    # Close the previous confirmed Zone when a new Zone is confirmed.
                                    if previous_confirmed_zone and previous_confirmed_zone != confirmed_zone:
                                        oldzs = zstate.get("zone_states", {}).get(previous_confirmed_zone)
                                        if oldzs and oldzs.get("inside"):
                                            # V27(1): the visit ends at the last observed
                                            # sample inside the Zone and is stored so the
                                            # summaries can use it after the state is reset.
                                            exit_time = float(oldzs.get("last_inside_time") or oldzs["entry_time"])
                                            duration = max(0.0, exit_time - float(oldzs["entry_time"]))
                                            oldzs.setdefault("visits", []).append((float(oldzs["entry_time"]), exit_time))
                                            avg_speed = oldzs["distance_px"] / duration if duration > 0 else 0.0
                                            zone_exit_count[previous_confirmed_zone] += 1
                                            measurement_events_writer.writerow([
                                                frame_index, f"{timestamp_now:.6f}", track_id, class_name,
                                                "ZONE", previous_confirmed_zone, "EXIT",
                                                f"{duration:.6f}", f"{oldzs['distance_px']:.3f}",
                                                f"{avg_speed:.6f}", "ZONE_CHANGE"
                                            ])
                                            oldzs["inside"] = False
                                            oldzs["entry_frame"] = None
                                            oldzs["entry_time"] = None
                                            oldzs["distance_px"] = 0.0
                                            oldzs["last_point"] = None

                                    zone_states = zstate["zone_states"]
                                    for zname in ZONE_NAMES:
                                        if len(self.zones.get(zname, [])) < 3:
                                            continue
                                        zs = zone_states.setdefault(zname, {
                                            "inside": False,
                                            "entry_frame": None,
                                            "entry_time": None,
                                            "last_inside_time": None,
                                            "visits": [],
                                            "distance_px": 0.0,
                                            "last_point": None,
                                        })

                                        if confirmed_zone == zname:
                                            if not zs["inside"]:
                                                zs["inside"] = True
                                                zs["entry_frame"] = frame_index
                                                zs["entry_time"] = timestamp_now
                                                zs["last_inside_time"] = timestamp_now
                                                zs["distance_px"] = 0.0
                                                zs["last_point"] = point
                                                zone_entry_count[zname] += 1
                                                measurement_events_writer.writerow([
                                                    frame_index, f"{timestamp_now:.6f}", track_id, class_name,
                                                    "ZONE", zname, "ENTRY", "0.000000", "0.000", "", "CONFIRMED"
                                                ])
                                            elif previous_confirmed_zone == zname and previous_zone_point is not None:
                                                zs["last_inside_time"] = timestamp_now
                                                px, py = previous_zone_point
                                                zs["distance_px"] += (
                                                    (point[0] - px) ** 2 + (point[1] - py) ** 2
                                                ) ** 0.5
                                                zs["last_point"] = point

                                    zstate["previous_confirmed_zone"] = confirmed_zone
                                    zstate["previous_confirmed_point"] = point if confirmed_zone else None

                                # ==============================
                                    # INTEGRATED LINE MEASUREMENT
                                    # ==============================
                                    lstate = line_track_state.setdefault(track_id, {})
                                    previous_point = lstate.get("previous_point")
                                    timestamp_now = (frame_index - 1) / fps
                                    for lname in LINE_NAMES:
                                        line = self.lines.get(lname, [])
                                        if len(line) != 2:
                                            continue
                                        direction = self.line_crossing(previous_point, point, line)
                                        if direction:
                                            line_cross_count[lname] += 1
                                            measurement_events_writer.writerow([frame_index, f"{timestamp_now:.6f}", track_id, class_name, "LINE", lname, "CROSS", "", "", "", direction])
                                            line_summary_writer.writerow([lname, track_id, class_name, frame_index, f"{timestamp_now:.6f}", direction])
                                    lstate["previous_point"] = point

                                # Remove stale active tracks from the current active set.
                                for old_id in list(active_tracks):
                                    if frame_index - active_tracks[old_id]["last_frame"] > 1:
                                        old = active_tracks.pop(old_id)
                                        recent_lost_tracks.append(old)

                            if track_id >= 0:

                                if track_id not in trails:
                                    trails[track_id] = deque(maxlen=trail_length)

                                # IMPORTANT: the trajectory trail follows the same
                                # Trajectory Position used for Zone assignment.
                                # It no longer uses the geometric bbox center.
                                trajectory_point = self.get_zone_reference_point(
                                    x1, y1, x2, y2
                                )
                                trails[track_id].append(trajectory_point)

                            # A Zone-enabled run displays the object ONLY while the
                            # selected Reference Point is inside a Zone.
                            confirmed_label = None
                            if measurement_enabled and track_id >= 0:
                                confirmed_label = zone_track_state.get(track_id, {}).get("confirmed_zone")

                            zones_available = zones_available_run
                            show_object = (
                                not zones_available
                                or confirmed_label is not None
                            )

                            if render_needed and rt.get("show_decision_point"):
                                # The point that decides the zone: filled yellow = inside a zone, red ring = in no zone
                                # (such a vehicle is not drawn at all, so this is the only way to see why).
                                dpx, dpy = self.get_zone_reference_point(x1, y1, x2, y2)
                                dpx, dpy = int(round(dpx)), int(round(dpy))
                                dr = max(5, int(round(0.004 * max(frame.shape[0], frame.shape[1]))))
                                cv2.circle(frame, (dpx, dpy), dr + 2, (255, 255, 255), -1)
                                if confirmed_label is not None:
                                    cv2.circle(frame, (dpx, dpy), dr, (0, 255, 255), -1)
                                else:
                                    cv2.circle(frame, (dpx, dpy), dr, (0, 0, 255), 2)

                            if show_object and render_needed:
                                if rt.get("show_bbox", True):
                                    cv2.rectangle(
                                        frame,
                                        (x1, y1),
                                        (x2, y2),
                                        (0, 255, 0),
                                        2
                                    )

                                if (
                                    settings["draw_trail"]
                                    and confirmed_label
                                    and track_id >= 0
                                    and track_id in trails
                                ):
                                    points = list(trails[track_id])
                                    for p in range(1, len(points)):
                                        cv2.line(
                                            frame,
                                            points[p - 1],
                                            points[p],
                                            (255, 0, 255),
                                            2
                                        )

                                if confirmed_label:
                                    # Individual vehicle label controls.
                                    # Live speed is display-only; research values remain
                                    # calculated by Run 3 from the stored trajectory.
                                    live_speed = zone_track_state.get(track_id, {}).get("live_speed_kmh")
                                    parts = []
                                    if rt.get("show_label_id", True):
                                        value = str(track_id)
                                        parts.append(f"ID {value}" if rt.get("show_prefix_id", False) else value)
                                    if rt.get("show_label_class", True):
                                        # Display the human-readable class name, not the numeric class_id.
                                        # The numeric class_id remains available in Run 2 raw records for audit.
                                        value = str(class_name).strip() or str(class_id)
                                        parts.append(f"Class {value}" if rt.get("show_prefix_class", False) else value)
                                    if rt.get("show_label_conf", True):
                                        value = f"{confidence:.2f}"
                                        parts.append(f"Conf {value}" if rt.get("show_prefix_conf", False) else value)
                                    if rt.get("show_label_zone", True):
                                        zn = re.search(r"(\d+)", str(confirmed_label or ""))
                                        value = zn.group(1) if zn else "-"
                                        parts.append(f"Zone {value}" if rt.get("show_prefix_zone", False) else value)
                                    if rt.get("show_label_speed", True):
                                        value = f"{live_speed:.1f}" if live_speed is not None else "-"
                                        parts.append(f"Speed {value}" if rt.get("show_prefix_speed", False) else value)
                                    label = " | ".join(parts)
                                    if label:
                                        label_y = max(y1 - 10, 20)
                                        cv2.putText(
                                            frame, label, (x1, label_y),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                                            (0, 255, 0), 2, cv2.LINE_AA
                                        )

                            if csv_writer is not None:

                                timestamp = (
                                    (frame_index - 1) / fps
                                )

                                trajectory_point_csv = self.get_zone_reference_point(x1, y1, x2, y2)
                                bbox_width_csv = max(0, x2 - x1)
                                bbox_height_csv = max(0, y2 - y1)
                                bbox_area_csv = bbox_width_csv * bbox_height_csv
                                csv_writer.writerow([
                                    frame_index, f"{timestamp:.6f}", track_id, class_id, class_name,
                                    f"{confidence:.6f}", x1, y1, x2, y2,
                                    bbox_width_csv, bbox_height_csv, bbox_area_csv,
                                    trajectory_point_csv[0], trajectory_point_csv[1],
                                    trajectory_position, f"{trajectory_offset:.2f}",
                                    (zone_track_state.get(track_id, {}).get("confirmed_zone", "") if measurement_enabled else "")
                                ])

                    if active_tracks:
                        max_active_tracks = max(
                            max_active_tracks,
                            len(active_tracks)
                        )

                    if boxes is not None and len(boxes) > 0:
                        total_frames_with_detection += 1

                    if (
                        csv_file is not None
                        and processed_frames
                        % csv_flush_every == 0
                    ):

                        csv_file.flush()

                elapsed = (
                    time.time()
                    - start_time
                )

                processing_fps = (
                    processed_frames / elapsed
                    if elapsed > 0
                    else 0
                )

                percent = (
                    (frame_index - window_start0)
                    / max(1, total_frames - window_start0)
                    * 100
                    if total_frames > 0
                    else 0
                )

                if processing_fps > 0:

                    remaining_frames = (
                        total_frames
                        - frame_index
                    )

                    eta_seconds = (
                        remaining_frames
                        / processing_fps
                    )

                else:

                    eta_seconds = 0

                elapsed_text = self.format_time(
                    elapsed
                )

                eta_text = self.format_time(
                    eta_seconds
                )

                info_lines = [
                    f"Frame: {frame_index}/{total_frames}",
                    f"Processed: {processed_frames}",
                    f"FPS: {processing_fps:.2f}",
                    f"Device: {device}",
                    f"Precision: {'FP16' if use_fp16 else 'FP32'}",
                    f"Elapsed: {elapsed_text}",
                    f"ETA: {eta_text}",
                ]

                y_pos = 30

                for line in (info_lines if render_needed else ()):

                    text_size, _ = cv2.getTextSize(
                        line,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        2
                    )

                    text_width = text_size[0]

                    text_x = (
                        width
                        - text_width
                        - 20
                    )

                    cv2.putText(
                        frame,
                        line,
                        (
                            text_x,
                            y_pos
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA
                    )

                    y_pos += 27

                if writer is not None and rec_first <= frame_index <= rec_last_eff:

                    writer.write(
                        frame
                    )

                if show_preview:

                    cv2.imshow(
                        window_name,
                        frame
                    )

                    key = (
                        cv2.waitKey(1)
                        & 0xFF
                    )

                    if key == ord("q"):

                        self.stop_event.set()
                        break

                if (
                    frame_index % 20 == 0
                    or frame_index == 1
                ):

                    self.update_ui(
                        progress=(
                            f"{frame_index}/"
                            f"{total_frames} "
                            f"({percent:.1f}%)"
                        ),
                        timing=(
                            f"FPS {processing_fps:.2f} | "
                            f"Elapsed {elapsed_text} | "
                            f"ETA {eta_text}"
                        )
                    )

                if frame_index % 20 == 0 or frame_index == 1:
                    processing_log_writer.writerow([
                        frame_index,
                        f"{frame_index / fps:.6f}",
                        processed_frames,
                        f"{processing_fps:.6f}",
                        total_detections,
                        len(active_tracks),
                        device,
                        "FP16" if use_fp16 else "FP32",
                        "processing"
                    ])

                if frame_index % 100 == 0:

                    print(
                        f"Frame {frame_index}/"
                        f"{total_frames} | "
                        f"Processed {processed_frames} | "
                        f"FPS {processing_fps:.2f}"
                    )

            # =================================================
            # FINALIZE OUTPUTS
            # =================================================
            # IMPORTANT: Do not close research CSV files before the
            # final statistics / processing-log rows are written.
            # Pressing Q sets stop_event and reaches this block, so
            # closing them here first would cause:
            #     I/O operation on closed file.

            if reader is not None:
                reader.close()

            if cap is not None:
                cap.release()

            if writer is not None:
                writer.release()

            # Finalize track statistics and research summary.
            for track_id, state in sorted(track_stats.items()):
                duration_frames = (
                    state["last_frame"] - state["first_frame"] + 1
                )
                duration_seconds = duration_frames / fps if fps > 0 else 0
                continuity_ratio = (
                    state["observed_frames"] / duration_frames
                    if duration_frames > 0 else 0
                )
                avg_conf = (
                    state["confidence_sum"] / state["detection_count"]
                    if state["detection_count"] > 0 else 0
                )
                avg_x = (
                    state["center_x_sum"] / state["detection_count"]
                    if state["detection_count"] > 0 else 0
                )
                avg_y = (
                    state["center_y_sum"] / state["detection_count"]
                    if state["detection_count"] > 0 else 0
                )
                avg_step = (
                    state["total_distance_px"] / max(1, state["observed_frames"] - 1)
                )
                status = (
                    "Continuous"
                    if continuity_ratio >= 0.95
                    else "Has Detection Loss"
                )

                track_stats_writer.writerow([
                    track_id,
                    state["class_id"],
                    state["class_name"],
                    state["first_frame"],
                    state["last_frame"],
                    state["observed_frames"],
                    f"{duration_seconds:.6f}",
                    state["detection_count"],
                    f"{continuity_ratio:.6f}",
                    state["loss_events"],
                    state["max_gap_frames"],
                    f"{avg_conf:.6f}",
                    f"{avg_x:.3f}",
                    f"{avg_y:.3f}",
                    f"{state['total_distance_px']:.3f}",
                    f"{avg_step:.3f}",
                    status,
                ])

            self._carry = {"model": model, "id_offset": id_offset, "sig": tracker_sig}     # the next clip may continue this tracker

            # Finalize a compact per-ID route summary before closing any files.
            if measurement_enabled:
                for track_id in sorted(zone_track_state):
                    state_info = track_stats.get(track_id, {})
                    last_time_final = (state_info.get("last_frame", frame_index) - 1) / fps if fps > 0 else 0.0
                    visits = clean_zone_visits(collect_zone_visits(
                        zone_track_state[track_id].get("zone_states", {}), last_time_final
                    ))
                    if not visits:
                        continue
                    class_name_final = state_info.get("class_name", "")
                    zones_sequence = []
                    for zname, _s, _e in visits:
                        if not zones_sequence or zones_sequence[-1] != zname:
                            zones_sequence.append(zname)
                    total_zone_time = sum(max(0.0, e - s0) for _z, s0, e in visits)
                    first_seen_final = float(state_info.get("first_frame", 1) - 1) / fps if fps > 0 else 0.0
                    last_seen_final = float(state_info.get("last_frame", frame_index) - 1) / fps if fps > 0 else 0.0
                    unique_zones = []
                    for z in zones_sequence:
                        if z not in unique_zones:
                            unique_zones.append(z)
                    transitions = len(zones_sequence) - 1
                    id_zone_summary_writer.writerow([
                        track_id, class_name_final,
                        f"{first_seen_final:.6f}", f"{last_seen_final:.6f}",
                        f"{max(0.0, last_seen_final-first_seen_final):.6f}",
                        zones_sequence[0], zones_sequence[-1],
                        " > ".join(zones_sequence),
                        " | ".join(unique_zones), transitions,
                        f"{total_zone_time:.6f}"
                    ])

            # Finalize Zone_Summary as one aggregate row per Zone.
            if measurement_enabled:
                zone_aggregate = defaultdict(lambda: {
                    "ids": set(), "durations": [], "entries": 0,
                    "first_entry": None, "last_entry": None
                })
                for track_id, zmap in zone_track_state.items():
                    state_info = track_stats.get(track_id, {})
                    last_frame_final = state_info.get("last_frame", frame_index)
                    last_time_final = (last_frame_final - 1) / fps if fps > 0 else 0.0
                    for zname, start_t, end_t in clean_zone_visits(
                        collect_zone_visits(zmap.get("zone_states", {}), last_time_final)
                    ):
                        duration = max(0.0, float(end_t) - float(start_t))
                        agg = zone_aggregate[zname]
                        agg["ids"].add(track_id)
                        agg["durations"].append(duration)
                        agg["entries"] += 1
                        agg["first_entry"] = start_t if agg["first_entry"] is None else min(agg["first_entry"], start_t)
                        agg["last_entry"] = start_t if agg["last_entry"] is None else max(agg["last_entry"], start_t)

                for zname in ZONE_NAMES:
                    agg = zone_aggregate.get(zname)
                    if not agg or not agg["durations"]:
                        continue
                    durations = agg["durations"]
                    zone_summary_writer.writerow([
                        zname, len(agg["ids"]), agg["entries"],
                        f"{sum(durations)/len(durations):.6f}",
                        f"{min(durations):.6f}", f"{max(durations):.6f}",
                        f"{agg['first_entry']:.6f}", f"{agg['last_entry']:.6f}"
                    ])

                zone_summary_file.flush()
                id_zone_summary_file.flush()
                with open(output_measurement_summary, "w", encoding="utf-8") as mf:
                    json.dump({
                        "measurement_enabled": measurement_enabled,
                        "zones_defined": [k for k,v in self.zones.items() if len(v) >= 3],
                        "lines_defined": [k for k,v in self.lines.items() if len(v) == 2],
                        "zone_source_file": self.zone_line_config_var.get().strip(),
                        "zone_source_video": self.zone_source_video,
                        "zone_source_resolution": {"width": self.zone_source_width, "height": self.zone_source_height},
                        "zone_entries": dict(zone_entry_count),
                        "zone_exits": dict(zone_exit_count),
                        "line_crossings": dict(line_cross_count),
                        "zone_assignment": {
                            "method": "Trajectory Position",
                            "trajectory_position": self.trajectory_position_var.get(),
                            "trajectory_offset_percent": float(self.trajectory_offset_var.get()),
                            "temporal_confirmation_frames": 0,
                             "zone_assignment_rule": "Trajectory Position point-in-polygon only",
                            "summary_flicker_merge_s": ZONE_FLICKER_MERGE_S,
                            "assignment_observations": {
                                z: dict(v) for z, v in zone_assignment_summary.items()
                            },
                        },
                        "outputs": {
                            "detection_records": output_csv,
                            "id_zone_summary": output_id_zone_summary,
                            "zone_summary": output_zone_summary,
                        }
                    }, mf, indent=4, ensure_ascii=False)

            # Flush final processing event.
            elapsed_before_summary = time.time() - start_time
            final_fps = (
                processed_frames / elapsed_before_summary
                if elapsed_before_summary > 0 else 0
            )
            processing_log_writer.writerow([
                frame_index,
                f"{frame_index / fps:.6f}",
                processed_frames,
                f"{final_fps:.6f}",
                total_detections,
                len(active_tracks),
                device,
                "FP16" if use_fp16 else "FP32",
                "stopped_by_user" if self.stop_event.is_set()
                else ("completed_end_of_video" if input_finished else "stopped")
            ])

            # Close files only AFTER every final row has been written.
            if csv_file is not None:
                try:
                    csv_file.flush()
                    csv_file.close()
                except Exception:
                    pass

            for summary_file in (zone_summary_file, id_zone_summary_file):
                try:
                    summary_file.close()
                except Exception:
                    pass

            if show_preview:
                cv2.destroyAllWindows()

            total_time = (
                time.time()
                - start_time
            )

            average_fps = (
                processed_frames / total_time
                if total_time > 0
                else 0
            )

            stopped = (
                self.stop_event.is_set()
            )

            print()
            print("=" * 75)

            if stopped:
                print("RUN 1 STOPPED")
            else:
                print("RUN 1 FINISHED")

            print("=" * 75)

            print("Python          :", sys.executable)
            print("PyTorch         :", torch.__version__)
            print(
                "CUDA Available  :",
                torch.cuda.is_available()
            )

            if torch.cuda.is_available():

                print(
                    "GPU             :",
                    torch.cuda.get_device_name(0)
                )

            print("Device          :", device)
            print(
                "Precision       :",
                "FP16" if use_fp16 else "FP32"
            )

            print("Run Name        :", run_name)
            print("Total Frames    :", total_frames)
            print("Processed Frames:", processed_frames)
            print("Detections      :", total_detections)
            print("Untracked (ID -1):", untracked_detections)
            print(
                "Processing Time :",
                f"{total_time:.2f} sec"
            )
            print(
                "Average FPS     :",
                f"{average_fps:.2f}"
            )

            if settings["save_video"]:

                print()
                print("Video:")
                print(output_video)

            if settings["save_csv"]:

                print()
                print("CSV OUTPUTS (3 files):")
                print("1.", output_csv)
                print("2.", output_id_zone_summary)
                print("3.", output_zone_summary)

            # Research summary.
            stop_reason = (
                "Stopped by user"
                if stopped
                else (
                    "Completed: end of input video"
                    if input_finished
                    else "Stopped: processing loop ended"
                )
            )

            run_summary = {
                "run_name": run_name,
                "run_type": "Run 1 + 2 Integrated Research",
                "status": "stopped" if stopped else "completed",
                "stop_reason": stop_reason,
                "model": model_path,
                "video": video_path,
                "output_directory": output_dir,
                "device": device,
                "precision": "FP16" if use_fp16 else "FP32",
                "tracker": tracker_name,
                "total_frames": video_total_frames,
                "analysis_window": {
                    "start_s": a_start, "end_s": a_end,
                    "first_frame": first_frame, "last_frame": last_frame,
                    "note": "timestamps in the CSV files are the original video times",
                },
                "recorded_video_window": ({"first_frame": rec_first, "last_frame": rec_last} if writer is not None else None),
                "processed_frames": processed_frames,
                "frames_with_detection": total_frames_with_detection,
                "total_detections": total_detections,
                "untracked_detections": untracked_detections,
                "unique_track_ids": len(track_stats),
                "max_track_id": (max(track_stats) if track_stats else id_offset),
                "id_offset": id_offset,
                "tracker_continued_from_previous_clip": carry is not None,
                "max_active_tracks": max_active_tracks,
                "id_switch_warnings": id_switch_warning_count,
                "detection_loss_events": detection_loss_count,
                "zone_assignment": {
                    "method": "Trajectory Position",
                    "trajectory_position": self.trajectory_position_var.get(),
                    "trajectory_offset_percent": float(self.trajectory_offset_var.get()),
                    "temporal_confirmation_frames": 0,
                             "zone_assignment_rule": "Trajectory Position point-in-polygon only",
                            "summary_flicker_merge_s": ZONE_FLICKER_MERGE_S,
                },
                "processing_time_seconds": round(total_time, 6),
                "average_fps": round(average_fps, 6),
                "outputs": {
                    "detection_records": output_csv,
                    "id_zone_summary": output_id_zone_summary,
                    "zone_summary": output_zone_summary,
                    "tracking_result": output_video if settings["save_video"] else None,
                    "run_summary": output_summary,
                    "settings": output_settings,
                    "bytetrack_yaml": output_tracker_yaml if tracker_name == "ByteTrack" else None,
                    "measurement_summary": output_measurement_summary if measurement_enabled else None,
                },
            }

            with open(output_summary, "w", encoding="utf-8") as f:
                json.dump(
                    run_summary,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            print()
            print("Research Outputs:")
            for key, value in run_summary["outputs"].items():
                if value:
                    print(f"{key:22}: {value}")
            print()
            print("Summary:")
            print("Stop Reason         :", stop_reason)
            print("Unique Track IDs    :", len(track_stats))
            print("ID Switch Warnings  :", id_switch_warning_count)
            print("Detection Losses    :", detection_loss_count)
            print("Detection Records   :", output_csv)
            print("ID Zone Summary     :", output_id_zone_summary)
            print("Zone Summary        :", output_zone_summary)
            print("Run Summary         :", output_summary)
            print("=" * 75)

            # ------------------------------------------------------------
            # RUN 3 — execute only after Run 1 + Run 2 files are closed.
            # ------------------------------------------------------------
            self.run3_last_outputs = {}
            self.run3_last_summary = {}
            cfg = self._run3_cfg or {}
            self.run3_was_requested = any(
                cfg.get(k + "_enabled") for k in ("speed", "gap", "lc", "pet", "ttc", "ldp")
            )
            # Run 3 is a post-processing step that uses the completed/partial
            # Run 2 CSVs. It must still execute when the user presses STOP,
            # because Run 1 + Run 2 finalize and close their files first.
            # STOP means: stop video processing, then analyze the data already
            # produced by Run 2.
            if self.run3_was_requested:
                self.post_ui(lambda: self.status_var.set(
                    "Run 3 — analyzing Run 2 data" + (" (partial run after STOP)" if stopped else "")
                ))
                self.run3_last_outputs = self.run3_processing(settings, output_dir, run_name)
                # Add Run 3 information to the existing Run 1 + 2 summary JSON.
                try:
                    with open(output_summary, "r", encoding="utf-8") as sf:
                        integrated_summary = json.load(sf)
                    integrated_summary["run_type"] = "Run 1 + 2 + 3 Integrated Research"
                    integrated_summary["run3"] = self.run3_last_summary
                    with open(output_summary, "w", encoding="utf-8") as sf:
                        json.dump(integrated_summary, sf, indent=4, ensure_ascii=False)
                except Exception:
                    log.exception("Could not add the Run 3 result to %s", output_summary)
                    print("WARNING: could not add the Run 3 result to the summary JSON:", output_summary)

            self.post_ui(
                lambda: self.finish_integrated_ui(
                    stopped,
                    output_video,
                    output_csv,
                    output_settings,
                    output_summary,
                    output_id_zone_summary,
                    output_zone_summary
                )
            )

        except Exception as e:

            try:
                if cap is not None:
                    if reader is not None:
                        reader.close()
                    cap.release()
            except Exception:
                pass

            try:
                if writer is not None:
                    writer.release()
            except Exception:
                pass

            try:
                if csv_file is not None:
                    csv_file.close()
            except Exception:
                pass

            for summary_file in (
                locals().get("zone_summary_file"),
                locals().get("id_zone_summary_file"),
            ):
                try:
                    if summary_file is not None:
                        summary_file.close()
                except Exception:
                    pass

            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

            print()
            print("=" * 75)
            print("RUN 1 ERROR")
            print("=" * 75)
            print(str(e))
            print("=" * 75)

            # Tkinter callbacks run after this except block exits; capture the
            # exception text now instead of closing over Python's exception variable.
            error_message = str(e)
            self._last_run_error = error_message
            self.post_ui(
                lambda message=error_message: self.show_error(
                    message
                )
            )

    # ========================================================
    # RUN 3 PROCESSING
    # ========================================================

    @staticmethod
    def _run3_read_csv(path):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def _run3_build_movement_index(self, tracks, summaries=None, mapping=None, site_id=None):
        """One canonical Movement per Vehicle_ID (SPEC v28 section 3).

        The Movement comes from the flicker-cleaned zone sequence built from the
        Run 2 Detection_Records (same cleaning as the Run 2 summaries). Returns
        (movement_by_id, status_by_id, sequence_by_id); status is one of
        Exact / Partial / Ambiguous / Unclassified / Insufficient.
        """
        movement_by_id, status_by_id, sequence_by_id = {}, {}, {}
        for tid, rows in tracks.items():
            seq = zone_sequence_from_samples([(r["_timestamp"], r.get("_zone_num")) for r in rows])
            movement, status = classify_movement_robust(seq)
            key = str(tid)
            movement_by_id[key] = movement
            status_by_id[key] = status
            sequence_by_id[key] = seq
        return movement_by_id, status_by_id, sequence_by_id

    @staticmethod
    def _run3_float_safe(value):
        try:
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _run3_point_from_row(row):
        x = Run1App._run3_float_safe(row.get("trajectory_x"))
        y = Run1App._run3_float_safe(row.get("trajectory_y"))
        if x is None or y is None:
            return None
        return (x, y)

    @staticmethod
    def _run3_bbox_center(row):
        try:
            x1 = float(row["bbox_x1"]); y1 = float(row["bbox_y1"])
            x2 = float(row["bbox_x2"]); y2 = float(row["bbox_y2"])
            return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
        except Exception:
            return None

    @staticmethod
    def _run3_segment_distance_sum(points):
        total = 0.0
        for a, b in zip(points, points[1:]):
            total += math.hypot(b[0] - a[0], b[1] - a[1])
        return total

    @staticmethod
    def _run3_interp_point_time(p0, t0, p1, t1, target):
        vx = p1[0] - p0[0]
        vy = p1[1] - p0[1]
        den = vx * vx + vy * vy
        if den <= 0:
            return None
        u = ((target[0] - p0[0]) * vx + (target[1] - p0[1]) * vy) / den
        if u < 0 or u > 1:
            return None
        return (t0 + u * (t1 - t0), (p0[0] + u * vx, p0[1] + u * vy))

    @staticmethod
    def _run3_line_crossing_time(prev_point, prev_t, curr_point, curr_t, line):
        """Return the timestamp of an observed sample that first crosses the line.
        No temporal interpolation is used. The event time is therefore quantized
        to an actually observed frame, consistent with the requested no-interpolation rule.
        """
        if not prev_point or not curr_point or len(line) < 2:
            return None
        a, b = line[0], line[1]
        def side(p):
            return (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0])
        s0 = side(prev_point); s1 = side(curr_point)
        if s0 == 0 and s1 == 0:
            return None
        if s0 == 0:
            return prev_t
        if s1 == 0:
            return curr_t
        if (s0 < 0 < s1) or (s0 > 0 > s1):
            return curr_t
        return None

    def _run3_load_inputs(self, output_dir, run_name):
        """Load only the Run 2 sources needed for Run 3 calculations.

        Detection Records are the frame/trajectory source. ID Zone Summary is
        the track-level route/movement source. Zone Summary remains a Run 2 audit
        output, but is not re-read or used as a duplicate Run 3 calculation source.
        """
        cc = _tools_module("combine_clips")
        det = cc.result_file(output_dir, "Detection_Records.csv", run_name) or os.path.join(output_dir, "Detection_Records.csv")
        ids = cc.result_file(output_dir, "ID_Zone_Summary.csv", run_name) or os.path.join(output_dir, "ID_Zone_Summary.csv")
        zone = cc.result_file(output_dir, "Zone_Summary.csv", run_name) or os.path.join(output_dir, "Zone_Summary.csv")
        return (
            self._run3_read_csv(det),
            self._run3_read_csv(ids),
            [],
            det, ids, zone,
        )

    @staticmethod
    def _run3_canonical_class(value):
        """Normalize vehicle class labels coming from Run 2 without changing class meaning."""
        raw = str(value or "").strip().lower()
        aliases = {
            "bus": "Bus", "car": "Car", "motorcycle": "Motorcycle",
            "motorbike": "Motorcycle", "motor cycle": "Motorcycle",
            "pickup": "Pickup", "pickup truck": "Pickup",
            "sidecar": "Sidecar", "side car": "Sidecar", "motorcycle sidecar": "Sidecar",
            "truck": "Truck", "van": "Van", "person": "person",
        }
        return aliases.get(raw, str(value or "").strip())

    @staticmethod
    def _run3_time_tolerance(tracks):
        """Use an observed-frame tolerance rather than exact timestamp equality.
        This does not interpolate positions; it only matches observed samples
        that are close in time, which is useful when one tracker misses a frame.
        """
        intervals = []
        for rows in tracks.values():
            ts = [r.get("_timestamp") for r in rows if r.get("_timestamp") is not None]
            for a,b in zip(ts, ts[1:]):
                d=b-a
                if d > 0:
                    intervals.append(d)
        if not intervals:
            return 0.05
        med=float(np.median(intervals))
        return max(0.02, min(0.10, med*2.5))

    def _run3_build_tracks(self, detection_rows, id_rows):
        self._run3_untracked_rows = 0
        tracks = defaultdict(list)
        for row in detection_rows:
            tid = str(row.get("track_id", "")).strip()
            if not tid or tid == "-1":
                if tid == "-1":
                    self._run3_untracked_rows += 1
                continue
            ts = self._run3_float_safe(row.get("timestamp"))
            if ts is None:
                continue
            row2 = dict(row)
            row2["class_name"] = self._run3_canonical_class(row2.get("class_name", ""))
            row2["_timestamp"] = ts
            row2["_point"] = self._run3_point_from_row(row2)
            row2["_center"] = self._run3_bbox_center(row2)
            row2["_zone_num"] = None
            z = str(row.get("zone", ""))
            m = re.search(r"(\d+)", z)
            if m:
                row2["_zone_num"] = int(m.group(1))
            tracks[tid].append(row2)
        for rows in tracks.values():
            rows.sort(key=lambda r: r["_timestamp"])
        summaries = {str(r.get("track_id", "")): r for r in id_rows}
        return tracks, summaries

    # ========================================================
    # RUN 3 — CONFIGURATION SNAPSHOT (MAIN THREAD ONLY)
    # ========================================================
    # V27: Every Run 3 Tk variable is read ONCE on the main thread when START
    # is pressed. The worker thread then uses this plain dict only. Calling
    # tk.Variable.get() from the worker thread is not thread-safe and each
    # call is marshalled to the Tk main loop; in V26 several .get() calls sat
    # inside nested per-row / per-pair loops (PET, Gap, LC), which was the
    # main reason Run 3 became very slow on long videos.

    def _run3_snapshot_config(self):
        def num(var, default=None):
            try:
                text = str(var.get()).strip()
                return float(text) if text else default
            except Exception:
                return default

        def zones_of(var_map):
            return {z for z, v in var_map.items() if bool(v.get())}

        ppm = num(self.run3_ppm_var, 0.0) or 0.0
        gap_movements = []
        if self.run3_gap_subject_134_var.get(): gap_movements.append("1-3-4")
        if self.run3_gap_subject_1367_var.get(): gap_movements.append("1-3-6-7")
        if self.run3_gap_subject_5631_var.get(): gap_movements.append("5-6-3-1")
        mapping_text = (
            self.run3_reference_text.get("1.0", "end-1c")
            if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text
        )
        pet_max = num(self.run3_pet_max_var, None)
        geometry = {key: num(self.run3_geometry_vars[key], None) for key in RUN3_GEOMETRY_KEYS}
        def lane_total(a, b):
            return geometry[a] + geometry[b] if geometry[a] is not None and geometry[b] is not None else None
        w_entry = lane_total("lane_entry_motorcycle_m", "lane_entry_car_m")
        w_opp = lane_total("lane_opp_motorcycle_m", "lane_opp_car_m")
        return {
            "site_id": self.run3_site_id_var.get().strip(),
            "speed_enabled": bool(self.run3_speed_enabled_var.get()),
            "gap_enabled": bool(self.run3_gap_enabled_var.get()),
            "lc_enabled": bool(self.run3_lc_enabled_var.get()),
            "pet_enabled": bool(self.run3_pet_enabled_var.get()),
            "ttc_enabled": bool(self.run3_ttc_enabled_var.get()),
            "ldp_enabled": bool(self.run3_ldp_enabled_var.get()),
            "ppm": ppm,
            "perspective_enabled": bool(self.run3_perspective_enabled_var.get()),
            "perspective": self._run3_get_perspective_matrix(silent=True),
            "lens": self._run3_lens_params()[0],
            "lens_size": self._run3_lens_params()[1],
            "axis_deg": num(self.run3_lateral_axis_angle_var, 0.0) or 0.0,
            "speed_zones": zones_of(self.run3_speed_zone_vars),
            "speed_smoothing_samples": max(1, int(num(self.run3_speed_smoothing_var, 5) or 1)),
            "speed_max_kmh": max(0.0, num(self.run3_speed_max_var, 80.0) or 0.0),
            "zone_calibrations": self._run3_clean_zone_calibrations(),
            "lc_zones": zones_of(self.run3_lc_zone_vars),
            "pet_zones": zones_of(self.run3_pet_zone_vars),
            "ttc_zones": zones_of(self.run3_ttc_zone_vars),
            "ldp_zones": zones_of(self.run3_ldp_zone_vars),
            "waiting_threshold": num(self.run3_waiting_speed_threshold_var, GAP_HOLD_SPEED_KMH),
            "hold_min_duration_s": num(self.run3_hold_min_duration_var, GAP_HOLD_MIN_S),
            "lc_heading_window_s": num(self.run3_lc_heading_window_var, 0.5),
            "topview_video": bool(self.run3_topview_video_var.get()),
            "topview_map": bool(self.run3_topview_map_var.get()),
            "road_lines": self.get_road_lines(),
            "lc_along_limit_m": max(0.0, num(self.run3_lc_along_limit_var, 0.0) or 0.0),
            "lc_max_lateral_m": max(0.0, num(self.run3_lc_max_lateral_var, 3.5) or 0.0),
            "lc_motorcycle_pairs_only": bool(self.run3_lc_motorcycle_pairs_only_var.get()),
            "pet_interaction": num(self.run3_pet_interaction_distance_var, 3.0),
            "pet_threshold": num(self.run3_pet_threshold_var, 1.0),
            "pet_max_s": pet_max if (pet_max is not None and pet_max > 0) else None,
            "ttc_max_record_s": num(self.run3_ttc_max_record_var, 3.0),
            "ttc_heading_max_deg": num(self.run3_ttc_heading_max_var, 45.0),
            "ttc_velocity_window_s": num(self.run3_ttc_velocity_window_var, 0.5),
            "ttc_min_speed_kmh": num(self.run3_ttc_min_speed_var, 2.0),
            "ttc_side_enabled": bool(self.run3_ttc_side_enabled_var.get()),
            "ttc_side_window_factor": num(self.run3_ttc_side_factor_var, 1.0),
            "ttc_side_margin_s": num(self.run3_ttc_side_margin_var, 0.0),
            "ttc_side_min_angle_deg": num(self.run3_ttc_side_angle_var, 10.0),
            "ttc_side_mode": {"Later arrival": "later", "Average of arrivals": "average"}.get(
                str(self.run3_ttc_side_mode_var.get()), "earlier"),
            "geometry": geometry,
            "w_entry_m": w_entry, "w_opp_m": w_opp,
            "ldp_smoothing_samples": int(num(self.run3_ldp_smoothing_var, 5) or 1),
            "gap_movements": gap_movements,
            "use_raff": bool(self.run3_use_raff_var.get()),
            "use_mle": bool(self.run3_use_mle_var.get()),
            "mapping_text": mapping_text,
            "widths": {n: num(v, None) for n, v in self.run3_width_vars.items()},
            "lengths": {n: num(v, None) for n, v in self.run3_length_vars.items()},
        }

    # ========================================================
    # RUN 3 — SHARED HELPERS
    # ========================================================

    @staticmethod
    def _run3_calibration_mode(c):
        return "Perspective_Homography" if c["perspective"] is not None else "PPM_Only"

    @staticmethod
    def _run3_qc_calibration(c):
        return "Perspective_Not_Calibrated" if (c["perspective_enabled"] and c["perspective"] is None) else ""

    def _run3_to_metric(self, pts, c):
        """Pixel points (N x 2) -> road-aligned metric points (N x 2).

        Column 0 = longitudinal (along the road), column 1 = lateral.
        Perspective: x axis follows P1->P2, y axis follows P2->P3.
        PPM only: pixel / PPM rotated by the road-direction angle.
        Distances are rotation-invariant, so Speed and PET are unaffected by
        the rotation; only the lateral indicators (LC, LDP) use the axes.
        """
        pts = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
        if len(pts) == 0:
            return pts
        if c.get("lens") is not None:                           # a wide-angle lens bends the picture: straighten the points first
            pts = lens_undistort(pts, c["lens_size"], c["lens"])
        persp = c["perspective"]
        if persp is not None:
            mapped = cv2.perspectiveTransform(pts.reshape(-1, 1, 2).astype(np.float32), persp["H"])
            return mapped.reshape(-1, 2).astype(np.float64)
        m = pts / c["ppm"]
        th = math.radians(c["axis_deg"])
        road_u = np.array([math.cos(th), math.sin(th)])
        lat_u = np.array([-math.sin(th), math.cos(th)])
        return np.stack([m @ road_u, m @ lat_u], axis=1)

    TOPVIEW_FIELDS = ["frame", "timestamp", "track_id", "class_name", "zone", "x_m", "y_m", "cx_m", "cy_m", "calibration_mode"]

    def _run3_topview_rows(self, tracks, c):
        """Every observed point in road-plane metres (the SAME numbers the indicators use):
        x_m, y_m = the Trajectory Position point (zone / speed point); cx_m, cy_m = the box centre."""
        mode = self._run3_calibration_mode(c)
        rows = []
        for tid, trows in tracks.items():
            for r in trows:
                m = r.get("_m")
                if m is None:
                    continue
                mc = r.get("_mc")
                rows.append({
                    "frame": r.get("frame", ""), "timestamp": r.get("timestamp", ""), "track_id": tid,
                    "class_name": r.get("class_name", ""), "zone": r.get("zone", ""),
                    "x_m": f"{m[0]:.4f}", "y_m": f"{m[1]:.4f}",
                    "cx_m": f"{mc[0]:.4f}" if mc is not None else "", "cy_m": f"{mc[1]:.4f}" if mc is not None else "",
                    "calibration_mode": mode,
                })
        rows.sort(key=lambda x: (float(x["timestamp"] or 0), str(x["track_id"])))
        return rows

    def _run3_topview_background(self, video_path, t0, t1, n=15):
        """Median of n frames spread over [t0, t1] = the road without moving vehicles (None if unreadable)."""
        if not video_path or not os.path.isfile(video_path):
            return None
        cap = cv2.VideoCapture(video_path)
        try:
            if not cap.isOpened():
                return None
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            frames = []
            for k in range(n):
                t = t0 + (t1 - t0) * (k + 0.5) / n
                idx = int(t * fps)
                if total:
                    idx = max(0, min(total - 1, idx))
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, fr = cap.read()
                if ok:
                    frames.append(fr)
            if not frames:
                return None
            return np.median(np.stack(frames), axis=0).astype(np.uint8)
        finally:
            cap.release()

    def _run3_write_topview_video(self, tracks, c, output_dir, video_path=None, max_px=1280, display=None):
        """Tracking_Topview.mp4: vehicles drawn on the road plane from the metric points (NOT a warped video, so
        vehicles are never stretched). Background = the road of the video warped by the base calibration (a
        vehicle-free median frame) when the video file is known, else a plain grid. Zones with their own
        calibration are placed correctly by the points but the background uses the base calibration only.
        `display` = the display settings of the normal tracking video (labels, prefixes, trajectory, zone drawing): the
        Topview shows the same things; the vehicle is marked by its reference point (no box)."""
        dsp = dict(display or {})

        def flag(key, default):
            v = dsp.get(key, default)
            return v if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")

        try:
            trail_n = max(1, int(float(dsp.get("trail_length", 30))))
        except (TypeError, ValueError):
            trail_n = 30
        try:
            zone_alpha = max(0.0, min(1.0, float(dsp.get("zone_overlay_opacity", 45)) / 100.0))
        except (TypeError, ValueError):
            zone_alpha = 0.45
        per_frame = defaultdict(list)
        all_pts = []
        for tid, rows in tracks.items():
            valid = [r for r in rows if r.get("_m") is not None]
            if not valid:
                continue
            heads = track_headings([r["_timestamp"] for r in valid], [r["_m"] for r in valid], 0.5, 0.5)
            cls = self._run3_canonical_class(valid[0].get("class_name", ""))
            for r, h in zip(valid, heads):
                try:
                    fr = int(float(r.get("frame", "")))
                except (TypeError, ValueError):
                    fr = int(round(r["_timestamp"] * 1000))
                try:
                    bb = (float(r["bbox_x1"]), float(r["bbox_y1"]), float(r["bbox_x2"]), float(r["bbox_y2"]))
                except (KeyError, TypeError, ValueError):
                    bb = None
                per_frame[fr].append((tid, cls, r["_timestamp"], r["_m"], h, bb, r))
                all_pts.append(r["_m"])
        if not per_frame:
            return None
        zone_m = []
        for zname, poly in self._zone_polygons():
            zone_m.append((zname, self._run3_to_metric(np.asarray(poly, dtype=float), c)))
            all_pts.extend(map(tuple, zone_m[-1][1]))
        aspect, vfps = None, 0.0
        if video_path and os.path.isfile(video_path):
            cap0 = cv2.VideoCapture(video_path)
            vw, vh = cap0.get(cv2.CAP_PROP_FRAME_WIDTH), cap0.get(cv2.CAP_PROP_FRAME_HEIGHT)
            vfps = cap0.get(cv2.CAP_PROP_FPS) or 0.0
            cap0.release()
            if vw > 0 and vh > 0:
                aspect = vw / vh                # the Topview has the same shape as the video that was recorded
        cv = topview_canvas(all_pts, max_px, aspect=aspect)
        W, H = cv["w"], cv["h"]
        # static layer: background, grid, zones
        base = np.full((H, W, 3), 38, np.uint8)
        t_all = [it[2] for items in per_frame.values() for it in items]
        map_style = bool(c.get("topview_map"))
        bg = None if map_style else self._run3_topview_background(video_path, min(t_all), max(t_all))
        bg_used = False
        if bg is not None:
            try:
                # every canvas pixel -> metres -> where it is in the camera picture (homography^-1, then the lens): one remap
                xs, ys = np.meshgrid(np.arange(W, dtype=np.float64), np.arange(H, dtype=np.float64))
                metres = np.stack([xs.ravel() / cv["scale"] + cv["xmin"], ys.ravel() / cv["scale"] + cv["ymin"]], axis=1)
                campx = self._run3_from_metric(metres, c).reshape(H, W, 2).astype(np.float32)
                warped = cv2.remap(bg, campx[..., 0], campx[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(38, 38, 38))
                base = warped
                bg_used = True
            except Exception:
                log.exception("Topview background could not be built; using a plain grid")
        step = 5.0 if max(W, H) / cv["scale"] <= 80 else 10.0
        grid = base.copy()                                         # the metre grid is faint, so the road still looks like a map
        labels = []
        x = math.ceil(cv["xmin"] / step) * step
        while (x - cv["xmin"]) * cv["scale"] < W:
            px = int(round((x - cv["xmin"]) * cv["scale"]))
            cv2.line(grid, (px, 0), (px, H - 1), (255, 255, 255), 1)
            labels.append((f"{x:g}", (px + 2, H - 4)))
            x += step
        y = math.ceil(cv["ymin"] / step) * step
        while (y - cv["ymin"]) * cv["scale"] < H:
            py = int(round((y - cv["ymin"]) * cv["scale"]))
            cv2.line(grid, (0, py), (W - 1, py), (255, 255, 255), 1)
            labels.append((f"{y:g}", (2, py - 3)))
            y += step
        base = cv2.addWeighted(grid, 0.22, base, 0.78, 0)
        for text_, org_ in labels:
            cv2.putText(base, text_, org_, cv2.FONT_HERSHEY_SIMPLEX, 0.4, (235, 235, 235), 1, cv2.LINE_AA)
        road_n = 0
        if map_style:                                              # the road lines clicked on the camera picture, carried to the road plane
            for item in c.get("road_lines") or []:
                kind_, line = normalize_road_line(item)
                pts_px = np.asarray(line, dtype=float).reshape(-1, 2)
                if len(pts_px) < 2:
                    continue
                if c.get("lens") is not None:                      # straight between the clicks in the straightened picture, then bent back
                    u = lens_undistort(pts_px, c["lens_size"], c["lens"])
                else:
                    u = pts_px
                dense = np.concatenate([np.linspace(u[i], u[i + 1], 25, endpoint=False) for i in range(len(u) - 1)] + [u[-1:]])
                rec_px = lens_distort(dense, c["lens_size"], c["lens"]) if c.get("lens") is not None else dense
                q = np.clip(topview_px(cv, self._run3_to_metric(rec_px, c)), -1e5, 1e5)
                draw_road_line(base, q, kind_, cv["scale"])
                road_n += 1
        zlayer = base.copy()                                       # zones: drawn like in the normal video (same switches, same opacity)
        if flag("show_zone_boundary", True) or flag("show_zone_label", True):
            meta_all = getattr(self, "zone_meta", {})
            for zname, pts in zone_m:
                meta = meta_all.get(zname, {})
                try:
                    zcol = tuple(int(max(0, min(255, v))) for v in meta.get("color_bgr", [0, 200, 0])[:3])
                    if len(zcol) != 3:
                        zcol = (0, 200, 0)
                except Exception:
                    zcol = (0, 200, 0)
                q = np.round(topview_px(cv, pts)).astype(np.int32).reshape(-1, 1, 2)
                if flag("show_zone_boundary", True):
                    cv2.polylines(zlayer, [q], True, zcol, 1, cv2.LINE_AA)
                if flag("show_zone_label", True) and meta.get("show_label", True):
                    cx, cy = q.reshape(-1, 2).mean(axis=0)
                    text_ = zname if flag("show_zone_label_prefix", True) else zname.replace("Zone ", "", 1)
                    (tw, th), _ = cv2.getTextSize(text_, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                    cv2.putText(zlayer, text_, (int(cx) - tw // 2, int(cy) + th // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.55, zcol, 1, cv2.LINE_AA)
            base = cv2.addWeighted(zlayer, zone_alpha, base, 1.0 - zone_alpha, 0)
        cv2.putText(base, f"metres (x right, y down)  {cv['scale']:.1f} px/m  " + ("empty road (median of frames), lens corrected, laid flat" if bg_used else (f"map: grid + {road_n} road lines" if map_style else "grid")),
                    (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        frames = sorted(per_frame)
        times = sorted({per_frame[f][0][2] for f in frames})
        dts = np.diff(times)
        dts = dts[dts > 0]
        # one picture per processed frame, played at the rate the frames were sampled (60 fps video -> 60 fps here),
        # so the Topview video lasts as long as the analysed part of the real video
        fps_out = float(min(120.0, max(1.0, 1.0 / float(np.median(dts))))) if len(dts) else 30.0
        out_path = os.path.join(output_dir, "Tracking_Topview.mp4")
        writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps_out, (W, H))
        if not writer.isOpened():
            raise RuntimeError("Unable to create Tracking_Topview.mp4")
        lengths, widths = c["lengths"], c["widths"]
        trails = defaultdict(deque)
        speed_hist = defaultdict(deque)
        try:
            for fr in frames:
                img = base.copy()
                now = per_frame[fr][0][2]
                marks = []
                for tid, cls, t, m, h, bb, rec in per_frame[fr]:
                    pt = topview_px(cv, [m])[0]
                    trails[tid].append(tuple(pt))
                    while len(trails[tid]) > trail_n:
                        trails[tid].popleft()
                    hist = speed_hist[tid]
                    hist.append((t, m))
                    while len(hist) > 1 and hist[0][0] < t - 0.5:
                        hist.popleft()
                    spd = None
                    if len(hist) >= 2 and hist[-1][0] > hist[0][0]:
                        spd = math.hypot(hist[-1][1][0] - hist[0][1][0], hist[-1][1][1] - hist[0][1][1]) / (hist[-1][0] - hist[0][0]) * 3.6
                    marks.append((tid, cls, pt, rec, spd))
                for tid, cls, pt, rec, spd in marks:
                    if flag("draw_trail", False) and len(trails[tid]) > 1:
                        cv2.polylines(img, [np.round(np.array(trails[tid])).astype(np.int32).reshape(-1, 1, 2)], False, (255, 0, 255), 2, cv2.LINE_AA)
                    p_ = (int(round(pt[0])), int(round(pt[1])))
                    cv2.circle(img, p_, 7, (255, 255, 255), -1, cv2.LINE_AA)           # the reference point (yellow = inside a zone)
                    inside = str(rec.get("zone", "")).strip() != ""
                    cv2.circle(img, p_, 5, (0, 255, 255) if inside else (0, 0, 255), -1 if inside else 2, cv2.LINE_AA)
                    parts = []
                    if flag("show_label_id", True):
                        parts.append(f"ID {tid}" if flag("show_prefix_id", False) else str(tid))
                    if flag("show_label_class", True):
                        v_ = str(rec.get("class_name", "")).strip() or cls
                        parts.append(f"Class {v_}" if flag("show_prefix_class", False) else v_)
                    if flag("show_label_conf", True):
                        try:
                            v_ = f"{float(rec.get('confidence', '')):.2f}"
                        except (TypeError, ValueError):
                            v_ = "-"
                        parts.append(f"Conf {v_}" if flag("show_prefix_conf", False) else v_)
                    if flag("show_label_zone", True):
                        zn = re.search(r"(\d+)", str(rec.get("zone", "") or ""))
                        v_ = zn.group(1) if zn else "-"
                        parts.append(f"Zone {v_}" if flag("show_prefix_zone", False) else v_)
                    if flag("show_label_speed", True):
                        v_ = f"{spd:.1f}" if spd is not None else "-"
                        parts.append(f"Speed {v_}" if flag("show_prefix_speed", False) else v_)
                    if parts:
                        cv2.putText(img, " | ".join(parts), (p_[0] + 8, max(14, p_[1] - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(img, f"t = {now:.2f} s   frame {fr}", (6, H - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                writer.write(img)
        finally:
            writer.release()
        return out_path

    def _run3_from_metric(self, pts_m, c):
        """Road-plane metres -> camera pixels (the inverse of _run3_to_metric: homography^-1, then the lens bends it again)."""
        m = np.asarray(pts_m, dtype=np.float64).reshape(-1, 2)
        persp = c["perspective"]
        if persp is not None:
            p = cv2.perspectiveTransform(m.reshape(-1, 1, 2), np.linalg.inv(np.asarray(persp["H"], dtype=np.float64))).reshape(-1, 2)
        else:
            th = math.radians(c["axis_deg"])
            p = (m[:, 0:1] * np.array([math.cos(th), math.sin(th)]) + m[:, 1:2] * np.array([-math.sin(th), math.cos(th)])) * c["ppm"]
        return lens_distort(p, c["lens_size"], c["lens"]) if c.get("lens") is not None else p

    def _run3_remove_duplicate_tracks(self, tracks):
        """Remove the frames of a track that duplicates another track (same vehicle, two IDs).
        Modifies `tracks` in place; returns report rows. Without this, the two IDs look like
        two vehicles standing on top of each other (negative Lateral Clearance, fake TTC/PET)."""
        frame_boxes = defaultdict(list)
        for tid, rows in tracks.items():
            for r in rows:
                try:
                    box = (float(r["bbox_x1"]), float(r["bbox_y1"]), float(r["bbox_x2"]), float(r["bbox_y2"]))
                    frame = int(float(r["frame"]))
                except Exception:
                    continue
                frame_boxes[frame].append((tid, box))
        length = {tid: len(rows) for tid, rows in tracks.items()}
        dup = find_duplicate_tracks(frame_boxes, length)
        report = []
        for drop, info in dup.items():
            rows = tracks.get(drop, [])
            keep_rows = []
            removed = []
            for r in rows:
                try:
                    frame = int(float(r["frame"]))
                except Exception:
                    frame = None
                (removed if frame in info["frames"] else keep_rows).append(r)
            cls = rows[0].get("class_name", "") if rows else ""
            report.append({
                "Duplicate_ID": drop, "Kept_ID": info["keep"], "Vehicle_Class": cls,
                "Frames_Removed": len(removed),
                "First_Frame": min(info["frames"]), "Last_Frame": max(info["frames"]),
                "Remaining_Rows_Of_Duplicate_ID": len(keep_rows),
            })
            if len(keep_rows) >= 2:
                tracks[drop] = keep_rows
            else:
                tracks.pop(drop, None)
        return report

    def _run3_clean_zone_calibrations(self):
        """Valid per-zone calibrations -> {zone number: {"points": [(x, y) x 4], "lengths": [4 floats]}}."""
        out = {}
        for key, cal in self.run3_zone_calibrations.items():
            try:
                z = int(key)
                pts = [(float(a), float(b)) for a, b in cal["points"]]
                lengths = [float(v) for v in cal["lengths"]]
            except (ValueError, TypeError, KeyError):
                continue
            if z in ZONE_IDS and len(pts) == 4 and len(lengths) == 4 and min(lengths) > 0:
                out[z] = {"points": pts, "lengths": lengths}
        return out

    def _run3_apply_zone_calibrations(self, rows_all, c):
        """Samples inside a zone that has its own calibration use that zone's homography (own scale and
        perspective), placed in the common metric frame; all other samples keep the base calibration."""
        info = {}
        for z, cal in (c.get("zone_calibrations") or {}).items():
            base_corners = self._run3_to_metric(cal["points"], c)
            tr = zone_metric_transform(self._run3_undistort(cal["points"], c), cal["lengths"], base_corners)
            info[f"Zone {z}"] = {"alignment_rms_m": round(tr["rms"], 3), "length_m": tr["length_m"], "width_m": tr["width_m"]}
            for src, dst in (("_point", "_m"), ("_center", "_mc")):
                idx = [i for i, r in enumerate(rows_all) if r.get("_zone_num") == z and r.get(src) is not None]
                if idx:
                    mapped = zone_metric_points(tr, self._run3_undistort([rows_all[i][src] for i in idx], c))
                    for j, i in enumerate(idx):
                        rows_all[i][dst] = (float(mapped[j, 0]), float(mapped[j, 1]))
        self._run3_zone_cal_info = info

    def _run3_attach_metric(self, tracks, c):
        """Transform every observed point ONCE (batch) instead of per use."""
        rows_all = [r for rows in tracks.values() for r in rows]
        for src, dst in (("_point", "_m"), ("_center", "_mc")):
            idx = [i for i, r in enumerate(rows_all) if r.get(src) is not None]
            if not idx:
                continue
            mapped = self._run3_to_metric([rows_all[i][src] for i in idx], c)
            for j, i in enumerate(idx):
                rows_all[i][dst] = (float(mapped[j, 0]), float(mapped[j, 1]))
        self._run3_zone_cal_info = {}
        if c.get("zone_calibrations"):
            self._run3_apply_zone_calibrations(rows_all, c)

    @staticmethod
    def _run3_stats(values):
        a = np.asarray([v for v in values if v is not None], dtype=float)
        if a.size == 0:
            return {"N": 0, "Mean": None, "SD": None, "Median": None, "Min": None, "Max": None, "P50": None, "P85": None}
        return {
            "N": int(a.size),
            "Mean": float(np.mean(a)),
            "SD": float(np.std(a, ddof=1)) if a.size > 1 else None,
            "Median": float(np.median(a)),
            "Min": float(np.min(a)),
            "Max": float(np.max(a)),
            "P50": float(np.percentile(a, 50)),
            "P85": float(np.percentile(a, 85)),
        }

    @staticmethod
    def _fmt(v, nd=6):
        return "" if v is None else f"{v:.{nd}f}"

    # ---------------- Risk-level tables (Chapter 2) ----------------
    # TTC: Kronprasert et al. (2021); PET / LDP: กรมทางหลวง (2569).
    # Each table is applied per dimension; the rule for combining the two
    # dimensions (index + speed) is NOT stated in the sources, so both levels
    # are exported separately and no combined level is invented here.

    @staticmethod
    def _level_ttc(ttc):
        if ttc < 1.0: return "High"
        if ttc <= 1.5: return "Moderate"
        if ttc <= 2.0: return "Low"
        return "None"

    @staticmethod
    def _level_ttc_speed(speed_kmh, vehicle_class):
        mc = str(vehicle_class) in ("Motorcycle", "Sidecar")
        hi, mid, lo = (50.0, 30.0, 15.0) if mc else (70.0, 50.0, 25.0)
        if speed_kmh > hi: return "High"
        if speed_kmh >= mid: return "Moderate"
        if speed_kmh >= lo: return "Low"
        return "None"

    @staticmethod
    def _level_pet(pet):
        if pet < 1.0: return "High"
        if pet <= 2.0: return "Moderate"
        if pet <= 3.0: return "Low"
        return "None"

    @staticmethod
    def _level_ldp(ldp):
        """Risk level of LDP (%) - Department of Highways (2026) table for dY / (W/2)."""
        if ldp >= 80.0: return "High"
        if ldp >= 50.0: return "Moderate"
        if ldp >= 30.0: return "Low"
        return "None"

    @staticmethod
    def _level_ldp_speed(speed_kmh):
        if speed_kmh >= 80.0: return "High"
        if speed_kmh >= 50.0: return "Moderate"
        if speed_kmh >= 30.0: return "Low"
        return "None"

    # ========================================================
    # SPEED (per Zone 1-7 and per Movement; V50, V85, Mean, SD)
    # ========================================================

    def _run3_speed(self, tracks, c, movement_by_id, status_by_id):
        """Speed detail rows: one per vehicle x zone and one per vehicle x Movement."""
        mode = self._run3_calibration_mode(c)
        qc_cal = self._run3_qc_calibration(c)
        k = c["speed_smoothing_samples"]
        vmax = c.get("speed_max_kmh", 0)
        results = []
        for tid, rows in tracks.items():
            if not rows:
                continue
            cls = rows[0].get("class_name", "")
            if str(cls).lower() == "person":
                continue
            movement = movement_by_id.get(str(tid), "")
            status = status_by_id.get(str(tid), "")
            for rec in track_speed_records(rows, c["speed_zones"], movement, status, k):
                results.append({
                    "Site_ID": c["site_id"], "Vehicle_ID": tid, "Vehicle_Class": cls,
                    "Scope": rec["Scope"], "Key": rec["Key"],
                    "Movement": movement, "Movement_Status": status,
                    "Start_Time": f"{rec['Start_Time']:.6f}", "End_Time": f"{rec['End_Time']:.6f}",
                    "Start_Frame": str(rec["Start_Frame"]), "End_Frame": str(rec["End_Frame"]),
                    "Samples": rec["Samples"],
                    "Distance_m": f"{rec['Distance_m']:.6f}", "Duration_s": f"{rec['Duration_s']:.6f}",
                    "Speed_kmh": f"{rec['Speed_kmh']:.6f}",
                    "Calibration_Mode": ("Zone_Homography" if rec["Scope"] == "Zone" and rec["Key"].split()[-1].isdigit()
                                         and int(rec["Key"].split()[-1]) in (c.get("zone_calibrations") or {}) else mode),
                    "QC_Flag": ";".join(x for x in (rec["Flag"], qc_cal, "Speed_Above_Max" if is_speed_outlier(rec["Speed_kmh"], vmax) else "") if x),
                })
        return results

    def _run3_speed_vehicle_summary_fields(self):
        fields = ["Site_ID", "Vehicle_ID", "Vehicle_Class", "Zone_Sequence", "Movement", "Movement_Status"]
        for zone in ZONE_IDS:
            fields += [f"Zone{zone}_Speed_kmh", f"Zone{zone}_Distance_m", f"Zone{zone}_Duration_s"]
        return fields + ["Movement_Speed_kmh", "Movement_Distance_m", "Movement_Duration_s", "Calibration_Mode", "QC_Flag"]

    def _run3_speed_vehicle_summary(self, speed_rows, tracks, c, movement_by_id, status_by_id, sequence_by_id):
        """One row per Vehicle_ID: speed in every Zone 1-7 and over the whole Movement."""
        by_vehicle = defaultdict(dict)
        for row in speed_rows:
            by_vehicle[str(row["Vehicle_ID"])][(row["Scope"], row["Key"])] = row
        out = []
        for tid in sorted((str(t) for t in tracks), key=lambda x: (int(x) if x.isdigit() else 10**18, x)):
            rows = tracks.get(tid, [])
            if not rows:
                continue
            cls = str(rows[0].get("class_name", ""))
            if cls.lower() == "person":
                continue
            row = {"Site_ID": c["site_id"], "Vehicle_ID": tid, "Vehicle_Class": cls,
                   "Zone_Sequence": "-".join(str(z) for z in sequence_by_id.get(tid, [])),
                   "Movement": movement_by_id.get(tid, ""), "Movement_Status": status_by_id.get(tid, "")}
            items = by_vehicle.get(tid, {})
            for zone in ZONE_IDS:
                it = items.get(("Zone", f"Zone {zone}"))
                row[f"Zone{zone}_Speed_kmh"] = it["Speed_kmh"] if it else ""
                row[f"Zone{zone}_Distance_m"] = it["Distance_m"] if it else ""
                row[f"Zone{zone}_Duration_s"] = it["Duration_s"] if it else ""
            mv = next((v for (sc, _k), v in items.items() if sc == "Movement"), None)
            row["Movement_Speed_kmh"] = mv["Speed_kmh"] if mv else ""
            row["Movement_Distance_m"] = mv["Distance_m"] if mv else ""
            row["Movement_Duration_s"] = mv["Duration_s"] if mv else ""
            row["Calibration_Mode"] = ";".join(sorted({v["Calibration_Mode"] for v in items.values() if v.get("Calibration_Mode")}))
            row["QC_Flag"] = ";".join(sorted({f for v in items.values() for f in str(v.get("QC_Flag", "")).split(";") if f}))
            out.append(row)
        return out

    def _run3_speed_statistics(self, speed_rows, c):
        """Speed statistics (Mean, SD, V50 = median, V85 = P85) per Zone / per Movement x class."""
        groups = defaultdict(list)
        for r in speed_rows:
            if "Speed_Above_Max" in str(r.get("QC_Flag", "")):
                continue
            v = float(r["Speed_kmh"])
            groups[(r["Scope"], r["Key"], "All")].append(v)
            groups[(r["Scope"], r["Key"], r["Vehicle_Class"])].append(v)

        def order(k):
            scope, key, cls = k
            if scope == "Zone":
                pos = (0, int(key.split()[-1]))
            else:
                pos = (1, MOVEMENT_IDS.index(key) if key in MOVEMENT_IDS else 99)
            return (pos, cls != "All", cls)

        out = []
        for (scope, key, cls) in sorted(groups, key=order):
            s_ = self._run3_stats(groups[(scope, key, cls)])
            out.append({
                "Site_ID": c["site_id"], "Scope": scope, "Key": key, "Vehicle_Class": cls, "N": s_["N"],
                "Mean_kmh": self._fmt(s_["Mean"], 3), "SD_kmh": self._fmt(s_["SD"], 3),
                "V50_kmh": self._fmt(s_["P50"], 3), "V85_kmh": self._fmt(s_["P85"], 3),
                "V85_minus_V50_kmh": self._fmt(None if s_["N"] == 0 else s_["P85"] - s_["P50"], 3),
                "Min_kmh": self._fmt(s_["Min"], 3), "Max_kmh": self._fmt(s_["Max"], 3),
            })
        return out

    # ========================================================
    # REFERENCE LINE MAPPING
    # ========================================================

    def copy_run3_mapping_template(self):
        text = self.run3_reference_text.get("1.0", "end-1c") if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            self.status_var.set("Reference Line Mapping template copied to clipboard")
        except Exception as e:
            self.status_var.set(f"Copy failed: {e}")

    def _run3_parse_reference_mapping(self, text=None):
        if text is None:
            text = self.run3_reference_text.get("1.0", "end-1c") if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text
        mapping = {}
        for raw in str(text).splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3:
                raise ValueError(f"Invalid Reference Line Mapping row: {raw}")
            site, movement, lname = parts
            if movement not in RUN3_ALL_MOVEMENTS:
                raise ValueError(f"Invalid movement in Reference Line Mapping: {movement}")
            if lname not in LINE_NAMES:
                raise ValueError(f"Invalid line name in Reference Line Mapping: {lname}")
            mapping[(site, movement)] = lname
        return mapping

    # ========================================================
    # GAP ACCEPTANCE (two stages: Access / Exit - design of v26(5.14.11) PASS)
    # ========================================================

    @staticmethod
    def _run3_step_speed_kmh(prev, cur):
        if prev.get("_m") is None or cur.get("_m") is None:
            return None
        dt = cur["_timestamp"] - prev["_timestamp"]
        if dt <= 0:
            return None
        return math.hypot(cur["_m"][0] - prev["_m"][0], cur["_m"][1] - prev["_m"][1]) / dt * 3.6

    def _run3_speed_at(self, rows, t):
        """Speed (km/h) from the observed step around time t (no interpolation), or None."""
        valid = [r for r in rows if r.get("_m") is not None and r.get("_timestamp") is not None]
        if len(valid) < 2:
            return None
        import bisect
        ts = [r["_timestamp"] for r in valid]
        i = bisect.bisect_left(ts, t)
        if i >= len(valid):
            i = len(valid) - 1
        if i == 0:
            return self._run3_step_speed_kmh(valid[0], valid[1])
        return self._run3_step_speed_kmh(valid[i - 1], valid[i])

    def _run3_gap(self, tracks, c, mapping, movement_by_id):
        """Binary Gap Acceptance decisions (accepted / rejected gaps) of waiting drivers.

        Subjects: movements 1-3-4, 1-3-6-7, 5-6-3-1 (GAP_PATHS: wait zone -> conflict
        ("middle") zones -> target zone). Conflicting streams: RUN3_GAP_CONFLICT_MAP; several
        streams may apply at once. A stream's reference time per vehicle = its first crossing
        of the mapped Line, or (no usable Line) its first observation in the stream's origin
        zone. Gap = time between consecutive vehicles of one stream.

        Stage 1 - Access: the driver's waiting starts when it is first seen in the waiting
          zone. Gaps that close before it enters the conflict zones are Rejected; the gap
          still open when it enters is Accepted (the smallest remaining gap controls when
          several streams apply) - unless the driver then stops inside the conflict zones.
        Stage 2 - Exit (only after such a stop): that gap becomes Rejected and the driver
          decides again after it resumes: only NEW gaps (starting after the resumption) count;
          the gap that contains the target-zone entry is Accepted, earlier new gaps Rejected.
        The available gap X31 is the time left until the gap closes at the decision time."""
        selected = c["gap_movements"]
        site = c["site_id"]
        thr = c["waiting_threshold"]
        hold_min = c["hold_min_duration_s"]
        diag = {"subjects": 0, "subjects_without_conflict_zone_entry": 0, "access_events": 0, "exit_events": 0,
                "holds_resumed": 0, "holds_censored": 0, "streams": {}}

        # ---- 1) reference events and gap intervals of every stream that is needed ----
        streams = sorted({cm for mv in selected for cm in RUN3_GAP_CONFLICT_MAP.get(mv, [])})
        intervals = {}
        for cm in streams:
            lname = mapping.get((site, cm)) if mapping else None
            line = self.lines.get(lname, []) if lname else []
            events = []
            if len(line) == 2:
                for tid, rows in tracks.items():
                    if movement_by_id.get(str(tid), "") != cm:
                        continue
                    prev = prev_t = None
                    for r in rows:
                        pnt, t = r.get("_point"), r.get("_timestamp")
                        if pnt is None or t is None:
                            continue
                        if prev is not None:
                            cross_t = self._run3_line_crossing_time(prev, prev_t, pnt, t, line)
                            if cross_t is not None:
                                events.append((float(cross_t), str(tid), r.get("class_name", ""), lname, ""))
                                break      # a vehicle crosses its reference line ONCE (first crossing)
                        prev, prev_t = pnt, t
            basis = "Line"
            if len(events) < 2:
                events, basis = [], "Origin_Zone_Entry"
                ref_zone = GAP_REFERENCE_ZONE.get(cm)
                for tid, rows in tracks.items():
                    if movement_by_id.get(str(tid), "") != cm or ref_zone is None:
                        continue
                    cand = [r for r in rows if r.get("_zone_num") == ref_zone and r.get("_timestamp") is not None]
                    if cand:
                        first = min(cand, key=lambda r: r["_timestamp"])
                        events.append((float(first["_timestamp"]), str(tid), first.get("class_name", ""),
                                       f"Observed Zone {ref_zone}",
                                       "Reference_Time_From_Origin_Zone_Entry" + ("" if not lname else "_Line_Unusable")))
            intervals[cm] = build_gap_intervals(events)
            diag["streams"][cm] = {"basis": basis, "vehicles": len({e[1] for e in events}), "gaps": len(intervals[cm])}

        # ---- 2) every subject ----
        rows_out = []
        for tid, raw_rows in tracks.items():
            tid = str(tid)
            movement = movement_by_id.get(tid, "")
            if movement not in selected or movement not in GAP_PATHS:
                continue
            path = GAP_PATHS[movement]
            wait_zones, middle_zones, target_zone = set(path["wait"]), set(path["middle"]), path["target"]
            rows = sorted((r for r in raw_rows if r.get("_timestamp") is not None), key=lambda r: r["_timestamp"])
            decision_rows = [r for r in rows if r.get("_zone_num") in wait_zones | middle_zones]
            if not decision_rows:
                continue
            diag["subjects"] += 1
            wait_rows = [r for r in decision_rows if r.get("_zone_num") in wait_zones]
            if wait_rows:
                wait_start = float(wait_rows[0]["_timestamp"])
            else:                                   # the track starts inside the conflict zones
                wait_start = float(decision_rows[0]["_timestamp"])
            middle_after = [r for r in rows if r["_timestamp"] >= wait_start and r.get("_zone_num") in middle_zones]
            if not middle_after:
                diag["subjects_without_conflict_zone_entry"] += 1
                continue
            entry_t = float(middle_after[0]["_timestamp"])
            conflict_movements = RUN3_GAP_CONFLICT_MAP.get(movement, [])

            # -- Stage 1: Access --
            stage_rows = []
            for cm in conflict_movements:
                for gap in intervals.get(cm, []):
                    gs, ge = gap["gap_start"], gap["gap_end"]
                    if ge <= wait_start or gs > entry_t:
                        continue
                    overlap = [r for r in decision_rows
                               if max(gs, wait_start) <= r["_timestamp"] < min(ge, entry_t + 1e-12)]
                    if not overlap:
                        continue
                    contains = gs <= entry_t < ge
                    eval_t = entry_t if contains else float(overlap[0]["_timestamp"])
                    avail = ge - eval_t
                    if avail <= 0:
                        continue
                    stage_rows.append({**gap, "conflict_movement": cm, "stage": "Access", "gap": avail,
                                       "opportunity_time": eval_t,
                                       "decision_zone": int((middle_after[0] if contains else overlap[0]).get("_zone_num") or 0),
                                       "contains_anchor": contains})

            # did the driver stop inside the conflict zones after entering them?
            samples = [(float(r["_timestamp"]), r["_m"][0], r["_m"][1], r.get("_zone_num") in middle_zones)
                       for r in rows if r["_timestamp"] >= entry_t and r.get("_m") is not None]
            hold = find_hold(samples, thr, hold_min) if samples else {"state": "Continued", "stop_start": None, "resume_time": None}
            confirmed_hold = hold["state"] in ("Stopped_then_Resumed", "Stopped_Censored")

            def pick(cands):
                return min(cands, key=lambda o: (o["gap"], o["conflict_movement"], o["id_a"], o["id_b"])) if cands else None

            controlling = pick([o for o in stage_rows if o["contains_anchor"]])
            for o in stage_rows:
                if o is controlling:
                    o["accepted"] = 0 if confirmed_hold else 1
                    o["basis"] = "Conflict_Zone_Entry_Followed_By_Stop" if confirmed_hold else "Conflict_Zone_Entry_No_Stop"
                elif o["gap_end"] <= entry_t:
                    o["accepted"], o["basis"] = 0, "Gap_Closed_Before_Conflict_Zone_Entry"
                else:
                    o["accepted"], o["basis"] = None, "Simultaneous_Alternative_Omitted"
            stage_rows = [o for o in stage_rows if o["accepted"] is not None]
            diag["access_events"] += int(bool(stage_rows))
            target_entry_t = None

            # -- Stage 2: Exit (only after a stop inside the conflict zones) --
            if confirmed_hold:
                if hold["resume_time"] is None:
                    diag["holds_censored"] += 1
                else:
                    diag["holds_resumed"] += 1
                    resume_t = float(hold["resume_time"])
                    tgt = [r for r in rows if r["_timestamp"] > resume_t and r.get("_zone_num") == target_zone]
                    target_entry_t = float(tgt[0]["_timestamp"]) if tgt else None
                    end_t = target_entry_t if target_entry_t is not None else float(rows[-1]["_timestamp"])
                    exit_rows = []
                    for cm in conflict_movements:
                        for gap in intervals.get(cm, []):
                            gs, ge = gap["gap_start"], gap["gap_end"]
                            if gs < resume_t or (target_entry_t is not None and gs > target_entry_t):
                                continue
                            overlap = [r for r in rows if r.get("_zone_num") in (wait_zones | middle_zones)
                                       and gs <= r["_timestamp"] < min(ge, end_t + 1e-12)]
                            target_overlap = target_entry_t is not None and gs <= target_entry_t < ge
                            if not overlap and not target_overlap:
                                continue
                            eval_t = target_entry_t if target_overlap else float(overlap[0]["_timestamp"])
                            avail = ge - eval_t
                            if avail <= 0:
                                continue
                            exit_rows.append({**gap, "conflict_movement": cm, "stage": "Exit", "gap": avail,
                                              "opportunity_time": eval_t,
                                              "decision_zone": int(target_zone if target_overlap else (overlap[0].get("_zone_num") or 0)),
                                              "contains_anchor": target_overlap})
                    controlling_exit = pick([o for o in exit_rows if o["contains_anchor"]])
                    for o in exit_rows:
                        if o is controlling_exit:
                            o["accepted"], o["basis"] = 1, "Target_Zone_Entry_After_Stop"
                        elif target_entry_t is None:
                            o["accepted"], o["basis"] = 0, "No_Observed_Target_Zone_Entry"
                        elif o["gap_end"] <= target_entry_t:
                            o["accepted"], o["basis"] = 0, "New_Gap_Closed_Before_Target_Zone"
                        else:
                            o["accepted"], o["basis"] = None, "Post_Target_Not_A_Decision"
                    exit_rows = [o for o in exit_rows if o["accepted"] is not None]
                    diag["exit_events"] += int(bool(exit_rows))
                    stage_rows.extend(exit_rows)

            # -- rows --
            subject_class = rows[0].get("class_name", "") if rows else ""
            ordered = sorted(stage_rows, key=lambda o: (o["stage"], o["opportunity_time"], -int(o["accepted"]),
                                                        o["conflict_movement"], o["id_a"], o["id_b"]))
            seen = set()
            number = 0
            for o in ordered:
                key = (o["stage"], o["conflict_movement"], o["id_a"], o["id_b"], round(o["gap_start"], 6), round(o["gap_end"], 6))
                if key in seen:
                    continue
                seen.add(key)
                number += 1
                anchor = entry_t if o["stage"] == "Access" else (target_entry_t if target_entry_t is not None else o["opportunity_time"])
                qc = [o.get("qc", ""), o.get("basis", "")]
                if confirmed_hold:
                    qc.append(f"Stop_{thr:.1f}kmh_{hold_min:.2f}s")
                sp_subject = self._run3_speed_at(rows, o["opportunity_time"])
                sp_a = self._run3_speed_at(tracks.get(o["id_a"], []), o["gap_start"])
                sp_b = self._run3_speed_at(tracks.get(o["id_b"], []), o["gap_end"])
                rows_out.append({
                    "Site_ID": site, "Decision_Event_ID": f"{tid}_{o['stage']}_{anchor:.6f}", "Opportunity_No": number,
                    "Subject_ID": tid, "Subject_Class": subject_class, "Subject_Movement": movement,
                    "Decision_Stage": o["stage"], "Decision_Zone": o["decision_zone"],
                    "Gap_Evaluation_Time": f"{o['opportunity_time']:.6f}",
                    "X32_Waiting_Time": f"{max(0.0, o['opportunity_time'] - wait_start):.6f}",
                    "Conflicting_Movement": o["conflict_movement"],
                    "Conflicting_ID_A": o["id_a"], "Conflicting_Class_A": o["class_a"],
                    "Conflicting_ID_B": o["id_b"], "Conflicting_Class_B": o["class_b"],
                    "Reference_Line": o["reference"],
                    "Gap_Start_Time": f"{o['gap_start']:.6f}", "Gap_End_Time": f"{o['gap_end']:.6f}",
                    "X31_Available_Gap": f"{o['gap']:.6f}",
                    "Subject_Speed_kmh": self._fmt(sp_subject, 3), "Conflict_Speed_A_kmh": self._fmt(sp_a, 3),
                    "Conflict_Speed_B_kmh": self._fmt(sp_b, 3),
                    "Gap_Role": "Accepted" if o["accepted"] == 1 else "Rejected", "Gap_Acceptance": int(o["accepted"]),
                    "Decision_Time": f"{o['opportunity_time']:.6f}",
                    "QC_Flag": ";".join(dict.fromkeys(x for x in qc if x)),
                })
        self._run3_gap_diag = diag
        return rows_out

    @staticmethod
    def _run3_raff(accepted, rejected):
        if not accepted or not rejected:
            return None
        candidates = sorted(set([float(v) for v in accepted + rejected if v is not None and v > 0]))
        if not candidates:
            return None
        acc = np.asarray(accepted, dtype=float); rej = np.asarray(rejected, dtype=float)
        best = None
        for g in candidates:
            diff = abs(np.mean(acc >= g) - np.mean(rej <= g))
            if best is None or diff < best[0]:
                best = (diff, g)
        return float(best[1]) if best else None

    @staticmethod
    def _run3_mle_driver_intervals(intervals):
        if len(intervals) < 1:
            return None
        try:
            from scipy.optimize import minimize
            from scipy.special import ndtr
        except Exception:
            return None
        lowers = np.array([max(1e-6, r) for r, a in intervals], dtype=float)
        uppers = np.array([max(r + 1e-6, a) for r, a in intervals], dtype=float)
        logs_l = np.log(lowers); logs_u = np.log(uppers)
        mu0 = float(np.median((logs_l + logs_u) / 2.0))
        sigma0 = float(max(0.25, np.std((logs_l + logs_u) / 2.0)))
        def nll(x):
            mu, log_sigma = x
            sigma = math.exp(log_sigma)
            probs = ndtr((logs_u - mu) / sigma) - ndtr((logs_l - mu) / sigma)
            return float(-np.sum(np.log(np.clip(probs, 1e-15, None))))
        res = minimize(nll, x0=np.array([mu0, math.log(sigma0)]), method="Nelder-Mead")
        if not res.success:
            return None
        mu, log_sigma = res.x
        return {"mu": float(mu), "sigma": float(math.exp(log_sigma)),
                "critical_gap_median": float(math.exp(mu)), "negative_log_likelihood": float(res.fun)}

    # ========================================================
    # LATERAL CLEARANCE
    # ========================================================

    def _run3_lateral_clearance(self, tracks, c, sequence_by_id):
        """Lateral Clearance (SPEC v28 section 5).

        Pairs (A, B) of ANY two vehicle classes moving in the SAME DIRECTION (their
        zone sequences share a transition touching the zone) and standing in the
        SAME zone at (nearly) the same time. If a pair contains a motorcycle it is
        A; otherwise A is the earlier ID, so each pair is reported once. Axes come
        from A's heading; a sample is only measured when the two boxes overlap
        along the direction of travel. Neighbours are found through a time index."""
        import bisect
        zones = c["lc_zones"]
        moto_pairs_only = c["lc_motorcycle_pairs_only"]
        along_limit = c.get("lc_along_limit_m") or None          # None = (L_A + L_B) / 2
        max_lateral = c.get("lc_max_lateral_m") or None          # None = no sideways limit
        widths = {k: v for k, v in c["widths"].items() if v is not None}
        lengths = {k: v for k, v in c["lengths"].items() if v is not None}
        tol = self._run3_time_tolerance(tracks)
        order = {tid: i for i, tid in enumerate(tracks)}
        perspective = c["perspective"] is not None
        diag = {"a_samples": 0, "a_no_heading": 0, "pairs_same_direction": 0, "pairs_other_direction": 0,
                "time_matched": 0, "no_box_overlap": 0, "too_far_sideways": 0, "rows": 0, "missing_dimension_class": set(),
                "motorcycle_pairs_only": moto_pairs_only,
                "along_limit_m": along_limit if along_limit else "auto (L_A+L_B)/2", "max_lateral_m": max_lateral}

        # zone -> tid -> (timestamps, rows) ; zone -> sorted list of (start, end, tid)
        obs = defaultdict(dict); spans = defaultdict(list)
        classes = {}
        for tid, rows in tracks.items():
            if not rows:
                continue
            cls = self._run3_canonical_class(rows[0].get("class_name", ""))
            classes[tid] = cls
            per_zone = defaultdict(list)
            for r in rows:
                if r.get("_mc") is not None and r.get("_zone_num") in zones:
                    per_zone[r["_zone_num"]].append(r)
            for z, lst in per_zone.items():
                obs[z][tid] = ([r["_timestamp"] for r in lst], lst)
                spans[z].append((lst[0]["_timestamp"], lst[-1]["_timestamp"], tid))
        for z in spans:
            spans[z].sort()
        span_starts = {z: [s_[0] for s_ in spans[z]] for z in spans}

        def has_dims(cls):
            return cls in widths and cls in lengths

        out = []
        for tid_a, rows_a in tracks.items():
            cls_a = classes.get(tid_a)
            if not cls_a or cls_a.lower() == "person":
                continue
            if not has_dims(cls_a):
                diag["missing_dimension_class"].add(cls_a)
                continue
            seq_a = sequence_by_id.get(str(tid_a), [])
            valid = [r for r in rows_a if r.get("_m") is not None]
            if len(valid) < 2:
                continue
            heads = track_headings([r["_timestamp"] for r in valid], [r["_m"] for r in valid],
                                   c["lc_heading_window_s"], 0.5)
            for r, h in zip(valid, heads):
                r["_h"] = h
            a_obs = [r for r in rows_a if r.get("_mc") is not None and r.get("_zone_num") in zones and "_h" in r]
            if not a_obs:
                continue
            neighbours = {}
            for z in {r["_zone_num"] for r in a_obs}:
                a_ts = obs[z][tid_a][0]
                hi = bisect.bisect_right(span_starts[z], a_ts[-1] + tol)
                cands = []
                for (st, en, tid_b) in spans[z][:hi]:
                    if en < a_ts[0] - tol or tid_b == tid_a:
                        continue
                    cls_b = classes.get(tid_b)
                    if not cls_b or cls_b.lower() == "person":
                        continue
                    if not has_dims(cls_b):
                        diag["missing_dimension_class"].add(cls_b)
                        continue
                    a_moto, b_moto = cls_a == "Motorcycle", cls_b == "Motorcycle"
                    if moto_pairs_only and not (a_moto or b_moto):
                        continue
                    # which vehicle of the pair is A?
                    if a_moto != b_moto:
                        if not a_moto:
                            continue                      # the motorcycle is A
                    elif order[tid_b] < order[tid_a]:
                        continue                          # same kind: A = earlier ID
                    if not same_direction_in_zone(seq_a, sequence_by_id.get(str(tid_b), []), z):
                        diag["pairs_other_direction"] += 1
                        continue
                    diag["pairs_same_direction"] += 1
                    cands.append(tid_b)
                neighbours[z] = sorted(cands, key=lambda t: order[t])
            pair_rows = defaultdict(list)
            for r_a in a_obs:
                diag["a_samples"] += 1
                if r_a["_h"] is None:
                    diag["a_no_heading"] += 1
                    continue
                z = r_a["_zone_num"]; ta = r_a["_timestamp"]
                for tid_b in neighbours.get(z, []):
                    ts_b, rows_b = obs[z][tid_b]
                    k = bisect.bisect_left(ts_b, ta)
                    best = None
                    for j in (k - 1, k):
                        if 0 <= j < len(ts_b):
                            d = abs(ts_b[j] - ta)
                            if best is None or d < best[0]:
                                best = (d, j)
                    if best is None or best[0] > tol:
                        continue
                    r_b = rows_b[best[1]]
                    diag["time_matched"] += 1
                    cls_b = classes[tid_b]
                    res = lateral_clearance(r_a["_mc"], r_a["_h"], r_b["_mc"],
                                            lengths[cls_a], lengths[cls_b], widths[cls_a], widths[cls_b],
                                            along_limit, max_lateral)
                    if not res["Overlap"]:
                        diag["no_box_overlap"] += 1
                        continue
                    if res["Too_Far"]:
                        diag["too_far_sideways"] += 1
                        continue
                    pair_rows[tid_b].append({
                        "Site_ID": c["site_id"], "Pair_ID": f"{tid_a}_{tid_b}",
                        "Timestamp": f"{ta:.6f}", "Zone": f"Zone {z}",
                        "Vehicle_A_ID": tid_a, "Vehicle_A_Class": cls_a,
                        "Vehicle_B_ID": tid_b, "Vehicle_B_Class": cls_b,
                        "Zone_Sequence_A": "-".join(str(x) for x in seq_a),
                        "Zone_Sequence_B": "-".join(str(x) for x in sequence_by_id.get(str(tid_b), [])),
                        "Along_m": f"{res['Along_m']:.4f}", "LS_Meter": f"{res['Lateral_m']:.6f}",
                        "Signed_Lateral_m": f"{res['Signed_Lateral_m']:.6f}",
                        "Width_A_m": f"{widths[cls_a]:.6f}", "Width_B_m": f"{widths[cls_b]:.6f}",
                        "Length_A_m": f"{lengths[cls_a]:.6f}", "Length_B_m": f"{lengths[cls_b]:.6f}",
                        "Lateral_Clearance_m": f"{res['Clearance_m']:.6f}",
                        "QC_Flag": ("Negative_Lateral_Clearance" if res["Clearance_m"] < 0 else "") + (";Perspective_Homography" if perspective else ""),
                    })
            for tid_b in sorted(pair_rows, key=lambda t: order[t]):
                out.extend(pair_rows[tid_b])
        diag["rows"] = len(out)
        diag["missing_dimension_class"] = sorted(diag["missing_dimension_class"])
        diag["time_tolerance_s"] = round(tol, 6)
        return out, diag

    @staticmethod
    def _run3_lc_pair_summary(rows):
        """One row per (A, B, zone): number of samples, minimum / mean clearance."""
        groups = defaultdict(list)
        for r in rows:
            groups[(r["Pair_ID"], r["Zone"])].append(r)
        out = []
        for (pair, zone), lst in groups.items():
            ys = [float(r["Lateral_Clearance_m"]) for r in lst]
            ts = [float(r["Timestamp"]) for r in lst]
            first = lst[0]
            out.append({
                "Site_ID": first["Site_ID"], "Pair_ID": pair, "Zone": zone,
                "Vehicle_A_ID": first["Vehicle_A_ID"], "Vehicle_A_Class": first["Vehicle_A_Class"],
                "Vehicle_B_ID": first["Vehicle_B_ID"], "Vehicle_B_Class": first["Vehicle_B_Class"],
                "Zone_Sequence_A": first["Zone_Sequence_A"], "Zone_Sequence_B": first["Zone_Sequence_B"],
                "Start_Time": f"{min(ts):.6f}", "End_Time": f"{max(ts):.6f}", "Samples": len(ys),
                "Lateral_Clearance_Min_m": f"{min(ys):.6f}", "Lateral_Clearance_Mean_m": f"{sum(ys) / len(ys):.6f}",
                "QC_Flag": "Negative_Lateral_Clearance" if min(ys) < 0 else "",
            })
        return out

    # ========================================================
    # PET (Zones 3 and/or 6)
    # ========================================================

    @staticmethod
    def _run3_segment_intersection(a0, a1, b0, b1):
        x1, y1 = a0; x2, y2 = a1; x3, y3 = b0; x4, y4 = b1
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-9:
            return None
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            return t, u, (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
        return None

    @staticmethod
    def _run3_best_intersection(A, B):
        """Vectorised version of the V26 double loop over segment pairs.
        Returns (score, ia, ib, ip) choosing the same pair V26 chose."""
        if len(A) < 2 or len(B) < 2:
            return None
        a0 = A[:-1, None, :]; a1 = A[1:, None, :]
        b0 = B[None, :-1, :]; b1 = B[None, 1:, :]
        x1, y1 = a0[..., 0], a0[..., 1]; x2, y2 = a1[..., 0], a1[..., 1]
        x3, y3 = b0[..., 0], b0[..., 1]; x4, y4 = b1[..., 0], b1[..., 1]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        ok = np.abs(den) >= 1e-9
        with np.errstate(divide="ignore", invalid="ignore"):
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
            u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
        hit = ok & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
        if not hit.any():
            return None
        with np.errstate(invalid="ignore"):
            ipx = x1 + t * (x2 - x1); ipy = y1 + t * (y2 - y1)
        da0 = np.hypot(x1 - ipx, y1 - ipy); da1 = np.hypot(x2 - ipx, y2 - ipy)
        db0 = np.hypot(x3 - ipx, y3 - ipy); db1 = np.hypot(x4 - ipx, y4 - ipy)
        score = np.maximum(np.minimum(da0, da1), np.minimum(db0, db1))
        score = np.where(hit, score, np.inf)
        flat = int(np.argmin(score))
        i, j = np.unravel_index(flat, score.shape)
        ia = i if da0[i, j] <= da1[i, j] else i + 1
        ib = j if db0[i, j] <= db1[i, j] else j + 1
        return float(score[i, j]), int(ia), int(ib), (float(ipx[i, j]), float(ipy[i, j]))

    def _run3_pet(self, tracks, c, movement_by_id, movement_source_by_id, sequence_by_id=None):
        """PET per conflict zone. Timestamps come only from observed frames.

        V27 changes: (1) distances use metric coordinates in BOTH calibration
        modes (V26 compared pixel distances with the metre interaction radius
        when perspective was off); (2) Zone 7 supported; (3) pairs whose zone
        time windows are further apart than PET max are skipped (PET can
        never be smaller than that gap, so no valid event is lost);
        (4) segment intersection is vectorised.
        """
        radius = c["pet_interaction"]; pet_max = c["pet_max_s"]; threshold = c["pet_threshold"]
        ids = list(tracks)
        diag = {"zone_tracks": {}, "pairs_with_both_in_zone": 0, "pairs_skipped_time_window": 0,
                "same_movement_excluded": 0, "no_movement_both": 0, "interaction_candidates": 0,
                "fallback_close_pairs": 0, "overlap_intervals": 0, "above_pet_max": 0,
                "tracks_with_movement": sum(1 for t in ids if movement_by_id.get(t))}
        out = []
        for zone in sorted(c["pet_zones"]):
            zrows = {}
            for tid in ids:
                lst = [r for r in tracks[tid] if r.get("_zone_num") == zone and r.get("_m") is not None]
                if lst:
                    zrows[tid] = (lst, np.array([r["_m"] for r in lst], dtype=float),
                                  np.array([r["_timestamp"] for r in lst], dtype=float))
            diag["zone_tracks"][f"Zone {zone}"] = len(zrows)
            zids = [t for t in ids if t in zrows]
            for i, a_id in enumerate(zids):
                a_rows, A, At = zrows[a_id]
                for b_id in zids[i + 1:]:
                    b_rows, B, Bt = zrows[b_id]
                    diag["pairs_with_both_in_zone"] += 1
                    if pet_max is not None:
                        window_gap = max(At[0], Bt[0]) - min(At[-1], Bt[-1])
                        if window_gap > pet_max:
                            diag["pairs_skipped_time_window"] += 1
                            continue
                    ma = movement_by_id.get(a_id, ""); mb = movement_by_id.get(b_id, "")
                    if not ma and not mb:
                        diag["no_movement_both"] += 1
                        continue
                    if ma and mb and ma == mb:
                        diag["same_movement_excluded"] += 1
                        continue
                    best = self._run3_best_intersection(A, B)
                    if best is not None:
                        ip = best[3]; ctype = "Crossing"
                    else:
                        d = np.hypot(A[:, None, 0] - B[None, :, 0], A[:, None, 1] - B[None, :, 1])
                        flat = int(np.argmin(d))
                        ia, ib = np.unravel_index(flat, d.shape)
                        if d[ia, ib] > radius:
                            continue
                        ip = ((A[ia, 0] + B[ib, 0]) / 2.0, (A[ia, 1] + B[ib, 1]) / 2.0)
                        ctype = conflict_type_from_sequences((sequence_by_id or {}).get(str(a_id), []),
                                                             (sequence_by_id or {}).get(str(b_id), []), False)
                        diag["fallback_close_pairs"] += 1
                    diag["interaction_candidates"] += 1
                    a_near = At[np.hypot(A[:, 0] - ip[0], A[:, 1] - ip[1]) <= radius]
                    b_near = Bt[np.hypot(B[:, 0] - ip[0], B[:, 1] - ip[1]) <= radius]
                    if a_near.size == 0 or b_near.size == 0:
                        continue
                    a_entry, a_exit = float(a_near.min()), float(a_near.max())
                    b_entry, b_exit = float(b_near.min()), float(b_near.max())
                    if a_exit <= b_entry:
                        t1, t2 = a_exit, b_entry
                    elif b_exit <= a_entry:
                        t1, t2 = b_exit, a_entry
                    else:
                        diag["overlap_intervals"] += 1
                        continue
                    pet = t2 - t1
                    if pet <= 0:
                        continue
                    if pet_max is not None and pet > pet_max:
                        diag["above_pet_max"] += 1
                        continue
                    out.append({
                        "Site_ID": c["site_id"],
                        "Interaction_ID": f"{a_id}_{b_id}_Z{zone}_{min(a_entry, b_entry):.6f}",
                        "Vehicle_ID_A": a_id, "Vehicle_Class_A": a_rows[0].get("class_name", ""), "Movement_A": ma,
                        "Vehicle_ID_B": b_id, "Vehicle_Class_B": b_rows[0].get("class_name", ""), "Movement_B": mb,
                        "Conflict_Type": ctype, "Conflict_Zone": f"Zone {zone}",
                        "Interaction_Start": f"{min(a_entry, b_entry):.6f}", "Interaction_End": f"{max(a_exit, b_exit):.6f}",
                        "T1_Exit_Time": f"{t1:.6f}", "T2_Entry_Time": f"{t2:.6f}", "PET_s": f"{pet:.6f}",
                        "PET_Risk_Level": self._level_pet(pet),
                        "QC_Flag": ";".join(x for x in [
                            "Threshold_At_or_Below" if pet <= threshold else "",
                            "Movement_A_Not_Observed" if not ma else "",
                            "Movement_B_Not_Observed" if not mb else "",
                            f"MovementSourceA={movement_source_by_id.get(a_id, '')}" if ma else "",
                            f"MovementSourceB={movement_source_by_id.get(b_id, '')}" if mb else "",
                        ] if x),
                    })
        return out, diag

    # ========================================================
    # TTC (rear-end and side conflicts)
    # ========================================================

    def _run3_ttc(self, tracks, c, movement_by_id):
        """TTC (SPEC v28 section 7) for vehicles standing in the selected zones
        (default Zones 3 and 6) at the same frame.

        RearEnd: TTC = S / CS (same-direction follower / leader).
        Side   : pairs that are not on a rear-end course but whose straight paths
                 cross ahead of both; TTC = min(d_i/v_i, d_j/v_j) when the arrival
                 times differ by at most the time needed to clear the crossing.
        One row per event (pair + type) = its TTCmin. Velocities come from a short
        centred window of observed samples (no interpolation)."""
        zones = c["ttc_zones"]
        win = max(1e-3, c["ttc_velocity_window_s"]) / 2.0
        vmin = c["ttc_min_speed_kmh"] / 3.6
        cos_max = math.cos(math.radians(c["ttc_heading_max_deg"]))
        ttc_max = c["ttc_max_record_s"]
        widths = c["widths"]; lengths = c["lengths"]
        diag = {"frames_with_pairs": 0, "pairs_evaluated": 0, "rear_end_candidates": 0, "side_candidates": 0,
                "skipped_overlap_boxes": 0, "missing_dimension_class": set()}

        per_frame = defaultdict(list)
        for tid, rows in tracks.items():
            if not rows:
                continue
            cls = self._run3_canonical_class(rows[0].get("class_name", ""))
            if cls not in widths or widths.get(cls) is None or lengths.get(cls) is None:
                if str(cls).lower() != "person":
                    diag["missing_dimension_class"].add(cls)
                continue
            valid = [r for r in rows if r.get("_m") is not None]
            if len(valid) < 2:
                continue
            t = np.array([r["_timestamp"] for r in valid]); m = np.array([r["_m"] for r in valid])
            lo = np.searchsorted(t, t - win, side="left")
            hi = np.searchsorted(t, t + win, side="right") - 1
            for k, r in enumerate(valid):
                if r.get("_zone_num") not in zones:
                    continue
                a, b = lo[k], hi[k]
                if b <= a or t[b] <= t[a]:
                    continue
                v = (m[b] - m[a]) / (t[b] - t[a])
                try:
                    fr = int(float(r.get("frame", "")))
                except Exception:
                    fr = int(round(r["_timestamp"] * 1000))
                per_frame[fr].append({"tid": tid, "cls": cls, "t": r["_timestamp"],
                                      "p": (float(m[k][0]), float(m[k][1])),
                                      "v": (float(v[0]), float(v[1])), "zone": r["_zone_num"]})

        cand = defaultdict(list)
        for fr, items in per_frame.items():
            n = len(items)
            if n < 2:
                continue
            diag["frames_with_pairs"] += 1
            for i in range(n):
                for j in range(i + 1, n):
                    A, B = items[i], items[j]
                    diag["pairs_evaluated"] += 1
                    la, lb = lengths[A["cls"]], lengths[B["cls"]]
                    wa, wb = widths[A["cls"]], widths[B["cls"]]
                    on_rear_end_course = False
                    for f, l in ((A, B), (B, A)):
                        res = rear_end_ttc(f["p"], f["v"], l["p"], l["v"],
                                           lengths[f["cls"]], lengths[l["cls"]],
                                           widths[f["cls"]], widths[l["cls"]], vmin, cos_max)
                        if res is None:
                            continue
                        on_rear_end_course = True
                        if res["TTC"] is None:
                            diag["skipped_overlap_boxes"] += 1
                            continue
                        if res["TTC"] <= ttc_max:
                            diag["rear_end_candidates"] += 1
                            cand[("RearEnd", f["tid"], l["tid"])].append({
                                "t": f["t"], "fr": fr, "ttc": res["TTC"], "zone": f["zone"],
                                "a": f, "b": l, "S": res["S"], "CS": res["CS"],
                                "vA": res["Speed_F"], "vB": res["Speed_L"]})
                    if on_rear_end_course:
                        continue
                    if not c["ttc_side_enabled"]:
                        continue
                    sd = side_ttc(A["p"], A["v"], B["p"], B["v"], la, lb, vmin,
                                  c["ttc_side_min_angle_deg"], c["ttc_side_window_factor"],
                                  c["ttc_side_margin_s"], c["ttc_side_mode"])
                    if sd is None or sd["TTC"] > ttc_max:
                        continue
                    diag["side_candidates"] += 1
                    first, second = (A, B) if sd["t_i"] <= sd["t_j"] else (B, A)
                    d_first, d_second = (sd["d_i"], sd["d_j"]) if first is A else (sd["d_j"], sd["d_i"])
                    key_ids = tuple(sorted((A["tid"], B["tid"]), key=lambda x: str(x)))
                    cand[("Side", key_ids[0], key_ids[1])].append({
                        "t": A["t"], "fr": fr, "ttc": sd["TTC"], "zone": first["zone"],
                        "a": first, "b": second, "d_a": d_first, "d_b": d_second,
                        "dt": abs(sd["t_i"] - sd["t_j"]), "angle": sd["angle_deg"],
                        "vA": math.hypot(*first["v"]), "vB": math.hypot(*second["v"])})

        out = []
        event_gap = 1.0
        for (kind, id_a, id_b), lst in cand.items():
            lst.sort(key=lambda x: x["t"])
            events = [[lst[0]]]
            for item in lst[1:]:
                if item["t"] - events[-1][-1]["t"] > event_gap:
                    events.append([item])
                else:
                    events[-1].append(item)
            for ev in events:
                best = min(ev, key=lambda x: x["ttc"])
                a_, b_ = best["a"], best["b"]
                vA_kmh = best["vA"] * 3.6
                rear = kind == "RearEnd"
                out.append({
                    "Site_ID": c["site_id"],
                    "Event_ID": f"{kind}_{a_['tid']}_{b_['tid']}_{ev[0]['t']:.6f}",
                    "TTC_Type": kind,
                    "Vehicle_A_ID": a_["tid"], "Vehicle_A_Class": a_["cls"], "Movement_A": movement_by_id.get(str(a_["tid"]), ""),
                    "Vehicle_B_ID": b_["tid"], "Vehicle_B_Class": b_["cls"], "Movement_B": movement_by_id.get(str(b_["tid"]), ""),
                    "Zone": f"Zone {best['zone']}", "Event_Start": f"{ev[0]['t']:.6f}", "Event_End": f"{ev[-1]['t']:.6f}",
                    "Event_Frames": len(ev), "TTCmin_Time": f"{best['t']:.6f}", "TTCmin_Frame": best["fr"],
                    "S_Conflict_Distance_m": f"{best['S']:.6f}" if rear else "",
                    "CS_Closing_Speed_kmh": f"{best['CS'] * 3.6:.6f}" if rear else "",
                    "Speed_A_kmh": f"{vA_kmh:.6f}", "Speed_B_kmh": f"{best['vB'] * 3.6:.6f}",
                    "Dist_A_to_Crossing_m": "" if rear else f"{best['d_a']:.6f}",
                    "Dist_B_to_Crossing_m": "" if rear else f"{best['d_b']:.6f}",
                    "Arrival_Diff_s": "" if rear else f"{best['dt']:.6f}",
                    "Path_Angle_deg": "" if rear else f"{best['angle']:.2f}",
                    "TTC_s": f"{best['ttc']:.6f}",
                    "TTC_Level": self._level_ttc(best["ttc"]),
                    "Speed_Level": self._level_ttc_speed(vA_kmh, a_["cls"]),
                    "QC_Flag": ";".join(x for x in [
                        "Single_Frame_Event" if len(ev) == 1 else "",
                        "Leader_Stationary" if rear and best["vB"] < vmin else "",
                        self._run3_qc_calibration(c),
                    ] if x),
                })
        out.sort(key=lambda r: float(r["TTCmin_Time"]))
        diag["missing_dimension_class"] = sorted(diag["missing_dimension_class"])
        return out, diag

    # ========================================================
    # LDP (Lane / Lateral Deviation Position)
    # ========================================================

    def _run3_ldp(self, tracks, c, movement_by_id, status_by_id):
        """LDP (SPEC v28 section 4): main-road vehicles only (2-3-4 -> W_entry,
        5-6-7 -> W_opp), zones selected in `ldp_zones`, metric trajectory points."""
        widths = {"entry": c["w_entry_m"], "opposite": c["w_opp_m"]}
        mode = self._run3_calibration_mode(c)
        k = c["ldp_smoothing_samples"]
        out = []
        for tid, rows in tracks.items():
            if not rows:
                continue
            movement = movement_by_id.get(str(tid), "")
            if not movement or not str(status_by_id.get(str(tid), "")).startswith("Exact"):
                continue
            info = MOVEMENT_PATTERNS[movement]
            if not info["main_road"]:
                continue
            cls = self._run3_canonical_class(rows[0].get("class_name", ""))
            if cls.lower() == "person":
                continue
            W = widths[info["side"]]
            if not W:
                raise ValueError(f"LDP needs the lane widths of the {info['side']} side (Road width inputs).")
            for zone in info["sequence"]:
                if zone not in c["ldp_zones"]:
                    continue
                zr = [r for r in rows if r.get("_zone_num") == zone and r.get("_m") is not None]
                res = ldp_for_zone([r["_m"] for r in zr], W, k)
                if res is None:
                    continue
                ldp = res["LDP_percent"]
                dt = zr[-1]["_timestamp"] - zr[0]["_timestamp"]
                dist = self._run3_segment_distance_sum([r["_m"] for r in zr])
                speed = dist / dt * 3.6 if dt > 0 else None
                out.append({
                    "Site_ID": c["site_id"], "Vehicle_ID": tid, "Vehicle_Class": cls,
                    "Movement": movement, "Zone": f"Zone {zone}", "Side": info["side"],
                    "Start_Time": f"{zr[0]['_timestamp']:.6f}", "End_Time": f"{zr[-1]['_timestamp']:.6f}",
                    "Samples": res["Samples"],
                    "P_in_x_m": f"{res['P_in'][0]:.4f}", "P_in_y_m": f"{res['P_in'][1]:.4f}",
                    "P_out_x_m": f"{res['P_out'][0]:.4f}", "P_out_y_m": f"{res['P_out'][1]:.4f}",
                    "Chord_Length_m": f"{res['Chord_Length_m']:.4f}",
                    "Delta_Y_m": f"{res['Delta_Y_m']:.6f}", "Lane_Width_W_m": f"{W:.3f}",
                    "LDP_percent": f"{ldp:.3f}",
                    "LDP_Level": self._level_ldp(ldp),
                    "Mean_Speed_kmh": self._fmt(speed, 3),
                    "Speed_Level": self._level_ldp_speed(speed) if speed is not None else "",
                    "Calibration_Mode": mode,
                    "QC_Flag": ";".join(x for x in [
                        "Short_Chord_Reference_Line_Unreliable" if res["Short_Chord"] else "",
                        "LDP_Above_100_Check_Lane_Width_or_Tracking" if ldp > 100 else "",
                        self._run3_qc_calibration(c),
                    ] if x),
                })
        return out

    # ========================================================
    # RUN 3 — ORCHESTRATION
    # ========================================================

    def run3_processing(self, settings, output_dir, run_name):
        c = getattr(self, "_run3_cfg", None) or self._run3_snapshot_config()
        t_start = time.time()
        timings = {}

        def status(text):
            self.post_ui(lambda t=text: self.status_var.set(t))

        status("Run 3 — loading Run 2 results...")
        detection_rows, id_rows, zone_rows, det_path, id_path, zone_path = self._run3_load_inputs(output_dir, run_name)
        tracks, summaries = self._run3_build_tracks(detection_rows, id_rows)
        duplicate_report = self._run3_remove_duplicate_tracks(tracks)
        self._run3_attach_metric(tracks, c)
        outputs = {}
        mapping = {}; mapping_parse_error = ""
        try:
            mapping = self._run3_parse_reference_mapping(c["mapping_text"])
        except Exception as exc:
            mapping_parse_error = str(exc)
        movement_by_id, movement_source_by_id, sequence_by_id = self._run3_build_movement_index(tracks, summaries, mapping, c["site_id"])
        tracks_by_zone = defaultdict(int)
        for rows in tracks.values():
            for z in {r.get("_zone_num") for r in rows}:
                if z in ZONE_IDS:
                    tracks_by_zone[str(z)] += 1
        summary = {
            "program_version": "PK Studio V28",
            "site_id": c["site_id"],
            "inputs": {"detection": det_path, "id_zone_summary": id_path, "zone_summary": zone_path},
            "calibration": {"mode": self._run3_calibration_mode(c), "ppm": c["ppm"],
                            "perspective_enabled": c["perspective_enabled"],
                            "perspective_configured": c["perspective"] is not None,
                            "road_direction_angle_deg": c["axis_deg"],
                            "zone_calibrations": dict(getattr(self, "_run3_zone_cal_info", {}) or {})},
            "source_counts": {
                "detection_records": len(detection_rows), "track_ids": len(tracks),
                "id_zone_summary_rows": len(id_rows), "tracks_by_zone": dict(tracks_by_zone),
                "movement_counts": {m: sum(1 for t in tracks if movement_by_id.get(str(t), "") == m) for m in RUN3_ALL_MOVEMENTS},
                "movement_status": {st: sum(1 for t in tracks if movement_source_by_id.get(str(t), "") == st)
                                    for st in ("Exact", "Exact_AfterDedupe", "Partial", "Partial_AfterDedupe",
                                               "Ambiguous", "Unclassified", "Insufficient")},
                "selected_zones": {k: sorted(c[k + "_zones"]) for k in ("speed", "lc", "pet", "ttc", "ldp")},
            },
            "diagnostics": {},
            "indicators": {},
        }
        untracked = getattr(self, "_run3_untracked_rows", 0)
        summary["diagnostics"]["untracked_detections"] = {
            "rows_with_track_id_minus_1": untracked,
            "share_of_detection_records": round(untracked / len(detection_rows), 6) if detection_rows else 0.0,
            "note": "detections the tracker gave no ID; they are not used by any indicator",
        }
        summary["diagnostics"]["duplicate_tracks"] = {
            "rule": (f"boxes IoU >= {DUPLICATE_TRACK_IOU} in >= {DUPLICATE_TRACK_MIN_FRAMES} frames (or, for a track shorter than that, in "
                     f"{int(DUPLICATE_SHORT_SHARE * 100)}% of its frames) = one vehicle under two IDs; the shorter track's overlapping frames are removed"),
            "tracks_affected": len(duplicate_report),
            "frames_removed": sum(r["Frames_Removed"] for r in duplicate_report),
        }
        if getattr(self, "_run3_warnings", None):
            summary["diagnostics"]["preflight_warnings"] = list(self._run3_warnings)
        if mapping_parse_error:
            summary["diagnostics"]["reference_mapping"] = f"Invalid Reference Line Mapping: {mapping_parse_error}"
        indicator_rows = []
        row_counts = {}

        def write_csv(filename, fields, rows):
            csv_file, actual = self._run3_open_csv_safe(os.path.join(output_dir, filename))
            with csv_file as f:
                w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
                w.writeheader()
                w.writerows([{k: excel_safe_value(v) for k, v in r.items()} for r in rows])
            return actual

        def indicator(name, domain, unit, group, values, note=""):
            s = self._run3_stats(values)
            indicator_rows.append({
                "Site_ID": c["site_id"], "Indicator": name, "Domain": domain, "Unit": unit,
                "Group": group, "N": s["N"], "Mean": self._fmt(s["Mean"], 4), "SD": self._fmt(s["SD"], 4),
                "Median": self._fmt(s["Median"], 4), "Min": self._fmt(s["Min"], 4), "Max": self._fmt(s["Max"], 4),
                "P85": self._fmt(s["P85"], 4), "Note": note,
            })
            return s

        def run_step(key, filename, func):
            if not c.get(key + "_enabled"):
                return
            t0 = time.time()
            try:
                func()
            except Exception as e:
                outputs[key] = write_csv(filename, ["Error"], [{"Error": str(e)}])
                summary["diagnostics"][key] = f"ERROR: {e}"
            timings[key] = round(time.time() - t0, 3)

        # ---------------- Lateral Clearance (distance) ----------------
        def do_lc():
            status("Run 3 — Lateral Clearance...")
            rows, lc_diag = self._run3_lateral_clearance(tracks, c, sequence_by_id)
            fields = ["Site_ID","Pair_ID","Timestamp","Zone","Vehicle_A_ID","Vehicle_A_Class","Vehicle_B_ID","Vehicle_B_Class","Zone_Sequence_A","Zone_Sequence_B","Along_m","LS_Meter","Signed_Lateral_m","Width_A_m","Width_B_m","Length_A_m","Length_B_m","Lateral_Clearance_m","QC_Flag"]
            row_counts["lc"] = len(rows)
            outputs["lateral_clearance"] = write_csv("Lateral_Clearance.csv", fields, rows)
            pairs = self._run3_lc_pair_summary(rows)
            pair_fields = ["Site_ID","Pair_ID","Zone","Vehicle_A_ID","Vehicle_A_Class","Vehicle_B_ID","Vehicle_B_Class","Zone_Sequence_A","Zone_Sequence_B","Start_Time","End_Time","Samples","Lateral_Clearance_Min_m","Lateral_Clearance_Mean_m","QC_Flag"]
            outputs["lateral_clearance_pairs"] = write_csv("Lateral_Clearance_Pairs.csv", pair_fields, pairs)
            s_ = indicator("Lateral Clearance (all measured samples)", "Distance", "m", "All samples",
                           [float(r["Lateral_Clearance_m"]) for r in rows])
            indicator("Lateral Clearance (minimum per pair and zone)", "Distance", "m", "Pair minimum",
                      [float(r["Lateral_Clearance_Min_m"]) for r in pairs])
            neg_rows = sum(1 for r in rows if float(r["Lateral_Clearance_m"]) < 0)
            neg_pairs = sum(1 for r in pairs if float(r["Lateral_Clearance_Min_m"]) < 0)
            s_["Negative_Samples"] = neg_rows
            s_["Negative_Pairs"] = neg_pairs
            s_["Negative_Pair_Share"] = round(neg_pairs / len(pairs), 6) if pairs else 0.0
            indicator("Lateral Clearance (minimum per pair and zone, overlapping boxes only)", "Distance", "m", "Pair minimum < 0",
                      [float(r["Lateral_Clearance_Min_m"]) for r in pairs if float(r["Lateral_Clearance_Min_m"]) < 0])
            summary["indicators"]["Lateral_Clearance"] = s_
            summary["diagnostics"]["lc"] = lc_diag
        run_step("lc", "Lateral_Clearance.csv", do_lc)

        # ---------------- LDP (distance) ----------------
        def do_ldp():
            status("Run 3 — LDP...")
            rows = self._run3_ldp(tracks, c, movement_by_id, movement_source_by_id)
            fields = ["Site_ID","Vehicle_ID","Vehicle_Class","Movement","Zone","Side","Start_Time","End_Time","Samples","P_in_x_m","P_in_y_m","P_out_x_m","P_out_y_m","Chord_Length_m","Delta_Y_m","Lane_Width_W_m","LDP_percent","LDP_Level","Mean_Speed_kmh","Speed_Level","Calibration_Mode","QC_Flag"]
            row_counts["ldp"] = len(rows)
            outputs["ldp"] = write_csv("LDP.csv", fields, rows)
            vals = [float(r["LDP_percent"]) for r in rows]
            note = f"W_entry={c['w_entry_m']} m; W_opp={c['w_opp_m']} m; smoothing={c['ldp_smoothing_samples']}"
            s_ = indicator("Lane/Lateral Deviation Position (LDP)", "Distance", "%", "All", vals, note)
            s_["Level_Counts"] = {lv: sum(1 for r in rows if r["LDP_Level"] == lv) for lv in ("High", "Moderate", "Low", "None")}
            for z in sorted(c["ldp_zones"]):
                indicator("Lane/Lateral Deviation Position (LDP)", "Distance", "%", f"Zone {z}",
                          [float(r["LDP_percent"]) for r in rows if r["Zone"] == f"Zone {z}"])
            summary["indicators"]["LDP"] = s_
            summary["diagnostics"]["ldp"] = (f"rows={len(rows)}; zones={sorted(c['ldp_zones'])}; all vehicle classes; "
                                             "main-road movements 2-3-4 / 5-6-7 only; LDP = dY / (W/2) x 100; risk level = DOH table")
        run_step("ldp", "LDP.csv", do_ldp)

        # ---------------- Gap Acceptance (time) ----------------
        def do_gap():
            status("Run 3 — Gap Acceptance...")
            gap_rows = self._run3_gap(tracks, c, mapping, movement_by_id)
            fields = ["Site_ID","Decision_Event_ID","Opportunity_No","Subject_ID","Subject_Class","Subject_Movement","Decision_Stage","Decision_Zone","Gap_Evaluation_Time","X32_Waiting_Time","Conflicting_Movement","Conflicting_ID_A","Conflicting_Class_A","Conflicting_ID_B","Conflicting_Class_B","Reference_Line","Gap_Start_Time","Gap_End_Time","X31_Available_Gap","Subject_Speed_kmh","Conflict_Speed_A_kmh","Conflict_Speed_B_kmh","Gap_Role","Gap_Acceptance","Decision_Time","QC_Flag"]
            row_counts["gap"] = len(gap_rows)
            outputs["gap_acceptance"] = write_csv("Gap_Acceptance.csv", fields, gap_rows)
            rejected = defaultdict(list); accepted = defaultdict(list)
            for r in gap_rows:
                key = (r["Subject_Class"], r["Subject_Movement"], r["Subject_ID"])
                (accepted if r["Gap_Acceptance"] == 1 else rejected)[key].append(float(r["X31_Available_Gap"]))
            groups = defaultdict(lambda: {"accepted": [], "rejected": [], "intervals": []})
            for key in set(rejected) | set(accepted):
                acc = accepted.get(key, []); rej = rejected.get(key, [])
                if acc and rej:
                    g = groups[(key[0], key[1])]
                    g["accepted"].append(acc[-1]); g["rejected"].append(max(rej))
                    g["intervals"].append((max(rej), acc[-1]))
            critical = []
            for (cls, movement), g in sorted(groups.items()):
                cr = self._run3_raff(g["accepted"], g["rejected"]) if c["use_raff"] else None
                mle = self._run3_mle_driver_intervals(g["intervals"]) if c["use_mle"] else None
                critical.append({
                    "Site_ID": c["site_id"], "Vehicle_Class": cls, "Movement": movement,
                    "Drivers_With_Pairs": len(g["intervals"]),
                    "Raff_Critical_Gap_s": self._fmt(cr), "MLE_Critical_Gap_Median_s": self._fmt(mle["critical_gap_median"] if mle else None),
                    "MLE_mu": self._fmt(mle["mu"] if mle else None), "MLE_sigma": self._fmt(mle["sigma"] if mle else None),
                })
            if critical:
                outputs["critical_gap"] = write_csv("Critical_Gap.csv", list(critical[0].keys()), critical)
            acc_vals = [float(r["X31_Available_Gap"]) for r in gap_rows if r["Gap_Acceptance"] == 1]
            rej_vals = [float(r["X31_Available_Gap"]) for r in gap_rows if r["Gap_Acceptance"] == 0]
            indicator("Gap Acceptance — accepted gaps", "Time", "s", "Accepted", acc_vals)
            indicator("Gap Acceptance — rejected gaps", "Time", "s", "Rejected", rej_vals)
            summary["indicators"]["Gap_Acceptance"] = {
                "gap_rows": len(gap_rows),
                "decision_events": len({r["Decision_Event_ID"] for r in gap_rows}),
                "accepted_events": len(acc_vals), "rejected_events": len(rej_vals),
                "critical_gap": critical, "reference_mapping_rows": len(mapping),
            }
            summary["diagnostics"]["gap"] = dict(getattr(self, "_run3_gap_diag", {}), rows=len(gap_rows),
                                                 rule="two-stage Access/Exit (v26 5.14.11); Line optional (origin-zone entry fallback)")
        run_step("gap", "Gap_Acceptance.csv", do_gap)

        # ---------------- TTC (time) ----------------
        def do_ttc():
            status("Run 3 — TTC...")
            rows, diag = self._run3_ttc(tracks, c, movement_by_id)
            fields = ["Site_ID","Event_ID","TTC_Type","Vehicle_A_ID","Vehicle_A_Class","Movement_A","Vehicle_B_ID","Vehicle_B_Class","Movement_B","Zone","Event_Start","Event_End","Event_Frames","TTCmin_Time","TTCmin_Frame","S_Conflict_Distance_m","CS_Closing_Speed_kmh","Speed_A_kmh","Speed_B_kmh","Dist_A_to_Crossing_m","Dist_B_to_Crossing_m","Arrival_Diff_s","Path_Angle_deg","TTC_s","TTC_Level","Speed_Level","QC_Flag"]
            row_counts["ttc"] = len(rows)
            outputs["ttc"] = write_csv("TTC.csv", fields, rows)
            vals = [float(r["TTC_s"]) for r in rows]
            s_ = indicator("Time-to-Collision (TTCmin per event)", "Time", "s", "All", vals,
                           f"events with TTCmin <= {c['ttc_max_record_s']} s")
            for kind in ("RearEnd", "Side"):
                indicator("Time-to-Collision (TTCmin per event)", "Time", "s", kind,
                          [float(r["TTC_s"]) for r in rows if r["TTC_Type"] == kind])
            s_["Level_Counts"] = {lv: sum(1 for r in rows if r["TTC_Level"] == lv) for lv in ("High", "Moderate", "Low", "None")}
            summary["indicators"]["TTC"] = s_
            diag["side_rule"] = {"enabled": c["ttc_side_enabled"], "window_factor": c["ttc_side_window_factor"],
                                 "margin_s": c["ttc_side_margin_s"], "min_angle_deg": c["ttc_side_min_angle_deg"],
                                 "ttc_is": c["ttc_side_mode"]}
            summary["diagnostics"]["ttc"] = diag
        run_step("ttc", "TTC.csv", do_ttc)

        # ---------------- PET (time) ----------------
        def do_pet():
            status("Run 3 — PET...")
            rows, diag = self._run3_pet(tracks, c, movement_by_id, movement_source_by_id, sequence_by_id)
            fields = ["Site_ID","Interaction_ID","Vehicle_ID_A","Vehicle_Class_A","Movement_A","Vehicle_ID_B","Vehicle_Class_B","Movement_B","Conflict_Type","Conflict_Zone","Interaction_Start","Interaction_End","T1_Exit_Time","T2_Entry_Time","PET_s","PET_Risk_Level","QC_Flag"]
            row_counts["pet"] = len(rows)
            outputs["pet"] = write_csv("PET.csv", fields, rows)
            vals = [float(r["PET_s"]) for r in rows]
            s = indicator("Post-Encroachment Time", "Time", "s", "All", vals)
            s["At_or_Below_Threshold"] = sum(v <= c["pet_threshold"] for v in vals)
            s["Level_Counts"] = {lv: sum(1 for r in rows if r["PET_Risk_Level"] == lv) for lv in ("High", "Moderate", "Low", "None")}
            for z in sorted(c["pet_zones"]):
                indicator("Post-Encroachment Time", "Time", "s", f"Zone {z}",
                          [float(r["PET_s"]) for r in rows if r["Conflict_Zone"] == f"Zone {z}"])
            for ctype in ("Crossing", "Merging", "Diverging", "Merging/Diverging"):
                sub = [float(r["PET_s"]) for r in rows if r["Conflict_Type"] == ctype]
                if sub:
                    indicator("Post-Encroachment Time", "Time", "s", f"Conflict type {ctype}", sub)
            s["Conflict_Type_Counts"] = {ct: sum(1 for r in rows if r["Conflict_Type"] == ct)
                                         for ct in ("Crossing", "Merging", "Diverging", "Merging/Diverging")}
            summary["indicators"]["PET"] = s
            summary["diagnostics"]["pet"] = diag
        run_step("pet", "PET.csv", do_pet)

        # ---------------- Speed (V50, V85, Mean, SD) ----------------
        def do_speed():
            status("Run 3 — Speed...")
            speed_rows = self._run3_speed(tracks, c, movement_by_id, movement_source_by_id)
            fields = ["Site_ID","Vehicle_ID","Vehicle_Class","Scope","Key","Movement","Movement_Status","Start_Time","End_Time","Start_Frame","End_Frame","Samples","Distance_m","Duration_s","Speed_kmh","Calibration_Mode","QC_Flag"]
            row_counts["speed"] = len(speed_rows)
            outputs["speed_detail"] = write_csv("Speed_Detail.csv", fields, speed_rows)
            vs = self._run3_speed_vehicle_summary(speed_rows, tracks, c, movement_by_id, movement_source_by_id, sequence_by_id)
            outputs["speed"] = write_csv("Speed.csv", self._run3_speed_vehicle_summary_fields(), vs)
            stats = self._run3_speed_statistics(speed_rows, c)
            outputs["speed_statistics"] = write_csv("Speed_Statistics.csv",
                ["Site_ID","Scope","Key","Vehicle_Class","N","Mean_kmh","SD_kmh","V50_kmh","V85_kmh","V85_minus_V50_kmh","Min_kmh","Max_kmh"], stats)
            groups = defaultdict(list)
            n_outliers = sum(1 for r in speed_rows if "Speed_Above_Max" in str(r.get("QC_Flag", "")))
            for r in speed_rows:
                if "Speed_Above_Max" in str(r.get("QC_Flag", "")):
                    continue
                groups[(r["Scope"], r["Key"])].append(float(r["Speed_kmh"]))
            spd = {}
            for (scope, key) in sorted(groups, key=lambda k: (k[0] != "Zone", MOVEMENT_IDS.index(k[1]) if k[1] in MOVEMENT_IDS else 0, k[1])):
                # One row per group: Median column = V50, P85 column = V85
                s_ = indicator("Speed (Mean, SD, V50 = Median, V85 = P85)", "Speed", "km/h",
                               key if scope == "Zone" else f"Movement {key}", groups[(scope, key)])
                spd[f"{scope} {key}"] = {"N": s_["N"], "Mean": s_["Mean"], "SD": s_["SD"], "V50": s_["P50"], "V85": s_["P85"]}
            summary["indicators"]["Speed"] = spd
            summary["diagnostics"]["speed"] = (f"vehicle_rows={len(vs)}; detail_rows={len(speed_rows)}; "
                                               f"zones={sorted(c['speed_zones'])}; smoothing_samples={c['speed_smoothing_samples']}; "
                                               f"max_plausible_kmh={c.get('speed_max_kmh', 0)}; above_max_excluded_from_statistics={n_outliers}")
        run_step("speed", "Speed.csv", do_speed)

        # Topview: the metric points the indicators used, as a file and (optionally) a road-plane video
        try:
            topview_rows = self._run3_topview_rows(tracks, c)
            outputs["topview_records"] = write_csv("Detection_Records_Topview.csv", self.TOPVIEW_FIELDS, topview_rows)
            summary["diagnostics"]["topview"] = {"records": len(topview_rows), "calibration_mode": self._run3_calibration_mode(c)}
            if c.get("topview_video") and topview_rows:
                status("Run 3 — drawing the Topview video...")
                tv = self._run3_write_topview_video(tracks, c, output_dir, (settings or {}).get("video"), display=settings)
                if tv:
                    outputs["topview_video"] = tv
                    summary["diagnostics"]["topview"]["video"] = tv
        except Exception as exc:
            log.exception("Topview output failed")
            summary["diagnostics"]["topview_error"] = str(exc)

        if duplicate_report:
            outputs["duplicate_tracks"] = write_csv(
                "Duplicate_Tracks.csv",
                ["Duplicate_ID", "Kept_ID", "Vehicle_Class", "Frames_Removed", "First_Frame", "Last_Frame", "Remaining_Rows_Of_Duplicate_ID"],
                duplicate_report)

        if indicator_rows:
            outputs["indicator_summary"] = write_csv(
                "Indicator_Summary.csv",
                ["Site_ID","Indicator","Domain","Unit","Group","N","Mean","SD","Median","Min","Max","P85","Note"],
                indicator_rows)

        # Why is an enabled indicator empty? (plain-language reasons, also shown when the run ends)
        empty = []
        mstat = summary["source_counts"]["movement_status"]
        mcount = summary["source_counts"]["movement_counts"]
        seen = (f"Movement ที่จับได้: ครบ {mstat['Exact'] + mstat['Exact_AfterDedupe']}, "
                f"บางส่วน {mstat['Partial'] + mstat['Partial_AfterDedupe']}, "
                f"ไม่ตรงแบบใด {mstat['Unclassified']}, เห็นไม่ครบ {mstat['Insufficient']} จาก {len(tracks)} คัน")
        layout_hint = " — ตรวจว่าไฟล์ Zone/วิดีโอเป็นชุดเดียวกับผังทางแยก (Movement ใหม่ 1-3-4, 2-3-1, 1-3-6-7, 5-6-3-1, 2-3-4, 5-6-7)"
        if c["ldp_enabled"] and row_counts.get("ldp") == 0:
            main = mcount.get("2-3-4", 0) + mcount.get("5-6-7", 0)
            empty.append(f"LDP ไม่มีข้อมูล: LDP คิดเฉพาะรถที่วิ่งครบ 2-3-4 หรือ 5-6-7 ตรง ๆ พบ {main} คัน. {seen}{layout_hint}")
        if c["gap_enabled"] and row_counts.get("gap") == 0:
            subjects = sum(mcount.get(mv, 0) for mv in c["gap_movements"])
            if subjects == 0:
                empty.append(f"Gap Acceptance ไม่มีข้อมูล: ไม่พบรถที่รอ (Movement {', '.join(c['gap_movements'])}) เลย. {seen}{layout_hint}")
            else:
                st_info = getattr(self, "_run3_gap_diag", {}).get("streams", {})
                streams_txt = ", ".join(f"{cm} = {v['vehicles']} คัน" for cm, v in sorted(st_info.items())) or "-"
                empty.append(f"Gap Acceptance ไม่มีข้อมูล: พบรถที่รอ {subjects} คัน แต่ไม่มีคันไหนเข้าโซนกลาง (3/6) ขณะที่มีช่องว่างจากกระแสที่ขัดแย้ง — "
                             f"ช่องว่างต้องมีรถกระแสที่ขัดแย้งอย่างน้อย 2 คันในคลิป (คันหน้าและคันหลัง). รถกระแสที่ขัดแย้งที่พบ: {streams_txt}. ตรวจ Line หรือโซนต้นทางของกระแสเหล่านั้น")
        for key, label in (("lc", "Lateral Clearance"), ("ttc", "TTC"), ("pet", "PET"), ("speed", "Speed")):
            if c[key + "_enabled"] and row_counts.get(key) == 0:
                empty.append(f"{label} ไม่มีข้อมูล (ไม่มีรถ/คู่รถที่เข้าเงื่อนไขในโซนที่เลือก)")
        summary["diagnostics"]["empty_outputs"] = empty
        for line in empty:
            print("Run 3 —", line)

        summary["architecture"] = {
            "indicators": "LDP, Lateral Clearance, Gap Acceptance, TTC, PET, Speed (V50, V85, Mean, SD)",
            "domains": {"Distance": ["LDP", "Lateral Clearance"], "Time": ["Gap Acceptance", "TTC", "PET"], "Speed": ["Speed"]},
            "movement_resolver": "Full flicker-cleaned zone sequence of each track matched to 6 patterns (1-3-4, 2-3-1, 1-3-6-7, 5-6-3-1, 2-3-4, 5-6-7); ambiguous fragments stay unclassified",
            "metric_coordinates": "Computed once per sample (batch); perspective or PPM + road angle",
            "risk_levels": "Exported per dimension; combination rule not defined in sources",
        }
        summary["timings_s"] = dict(timings, total=round(time.time() - t_start, 3))
        summary["outputs"] = outputs
        summary_path = os.path.join(output_dir, "Summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(self._json_safe(summary), f, indent=4, ensure_ascii=False)
        outputs["summary"] = summary_path
        self.run3_last_outputs = outputs
        self.run3_last_summary = summary
        done = [k for k in ("lc", "ldp", "gap", "ttc", "pet", "speed") if c.get(k + "_enabled")]
        msg = f"Run 3 completed in {summary['timings_s']['total']:.1f} s | " + ", ".join(done)
        self.post_ui(lambda m=msg: self.run3_result_text.set(m))
        return outputs

    def finish_integrated_ui(self, stopped, output_video, output_csv, output_settings, output_summary, output_id_zone_summary=None, output_zone_summary=None):
        if getattr(self, "_batch_mode", False):
            return          # the batch worker reports once at the end
        self.running = False
        self._rt = None
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Ⅱ PAUSE")
        self.stop_button.config(state="disabled")
        if stopped:
            self.status_var.set("Run 1 + 2 + 3 stopped — Run 3 analyzed available data")
        if self.run3_was_requested:
            self.status_var.set("Run 1 + 2 + 3 completed" if not stopped else "Run 1 + 2 + 3 stopped — Run 3 analyzed available data")
            message = ("Run 1 + 2 + 3 completed\n\n" if not stopped else "Run 1 + 2 + 3 stopped\nRun 3 was analyzed using the available Run 2 data.\n\n")
        else:
            self.status_var.set("Run 1 + 2 completed" if not stopped else "Run 1 + 2 stopped")
            message = ("Run 1 + 2 completed\n\n" if not stopped else "Run 1 + 2 stopped\n\n")
        self.progress_var.set("100%")
        if self.save_video_var.get():
            message += f"Run 1/2 Video:\n{output_video}\n\n"
        if self.save_csv_var.get():
            message += f"Run 2 Detection Records:\n{output_csv}\n\n"
        message += f"Run 2 ID Zone Summary:\n{output_id_zone_summary}\n\nRun 2 Zone Summary:\n{output_zone_summary}\n\n"
        empty_reasons = (self.run3_last_summary or {}).get("diagnostics", {}).get("empty_outputs", [])
        if empty_reasons:
            message += "ตัวชี้วัดที่ไม่มีข้อมูล (ไฟล์ CSV มีแต่หัวแถว) และสาเหตุ:\n"
            message += "\n".join("• " + r for r in empty_reasons) + "\n\n"
        if self.run3_last_outputs:
            message += "Run 3 Outputs:\n"
            for key, value in self.run3_last_outputs.items():
                if value:
                    message += f"{key}: {value}\n"
            message += "\n"
        message += f"Run 1/2 Summary:\n{output_summary}\n\nSettings:\n{output_settings}"
        messagebox.showinfo("PK Studio V17 Complete", message)

    # ========================================================
    # FORMAT TIME
    # ========================================================

    def format_time(self, seconds):

        seconds = int(
            max(0, seconds)
        )

        hours = seconds // 3600

        minutes = (
            seconds % 3600
        ) // 60

        secs = (
            seconds % 60
        )

        if hours > 0:

            return (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{secs:02d}"
            )

        return (
            f"{minutes:02d}:"
            f"{secs:02d}"
        )

    # ========================================================
    # FINISH UI
    # ========================================================

    def finish_ui(
        self,
        stopped,
        output_video,
        output_csv,
        output_settings,
        output_summary,
        output_track_stats,
        output_id_switch,
        output_detection_loss,
        output_processing_log,
        output_id_zone_summary=None,
        output_zone_summary=None
    ):

        self.running = False

        self.start_button.config(
            state="normal"
        )

        self.pause_button.config(
            state="disabled",
            text="Ⅱ PAUSE"
        )

        self.stop_button.config(
            state="disabled"
        )

        if stopped:

            self.status_var.set(
                "Run 1 stopped"
            )

            messagebox.showinfo(
                "Run 1",
                "Run 1 was stopped"
            )

            return

        self.status_var.set(
            "Run 1 completed"
        )

        self.progress_var.set(
            "100%"
        )

        message = (
            "Run 1 completed\n\n"
        )

        if self.save_video_var.get():

            message += (
                "Video:\n"
                f"{output_video}\n\n"
            )

        if self.save_csv_var.get():

            message += (
                "Detection Records CSV:\n"
                f"{output_csv}\n\n"
            )

        message += (
            "ID Zone Summary CSV:\n"
            f"{output_id_zone_summary}\n\n"
            "Zone Summary CSV:\n"
            f"{output_zone_summary}\n\n"
            "Research Summary JSON:\n"
            f"{output_summary}\n\n"
            "Settings:\n"
            f"{output_settings}"
        )

        messagebox.showinfo(
            "Run 1 Complete",
            message
        )

    # ========================================================
    # ERROR
    # ========================================================

    def show_error(self, error):

        if getattr(self, "_batch_mode", False):
            log.error("Clip failed inside a batch: %s", error)
            return          # reported in the batch summary
        self.running = False

        self.start_button.config(
            state="normal"
        )

        self.pause_button.config(
            state="disabled"
        )

        self.stop_button.config(
            state="disabled"
        )

        self.status_var.set(
            "Error occurred"
        )

        self.progress_var.set(
            "ERROR"
        )

        messagebox.showerror(
            "PK Studio V17 Error",
            error
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def on_close(self):

        if self.running:

            answer = messagebox.askyesno(
                "Exit",
                "PK Studio V17 is currently processing\n\n"
                "Stop the run and close the program?"
            )

            if not answer:
                return

            self.stop_event.set()
            self.pause_event.set()

            self.root.after(
                500,
                self.root.destroy
            )

        else:

            self.root.destroy()


# ============================================================
# MAIN
# ============================================================

def main():

    root = tk.Tk()

    app = Run1App(
        root
    )

    root.mainloop()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
