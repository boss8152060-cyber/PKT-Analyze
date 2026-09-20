# ============================================================
# PK Studio - Run 1
# ============================================================
#
# Vehicle Detection + Tracking + Trajectory + Zone/Line Measurement Research
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
import subprocess
import shutil
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
            timeout=15
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
            timeout=15
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

DEFAULT_MODEL = (
    r"F:\motorcycle group project\PSU Transport Project 2026"
    r"\Test\Run1\Model\best.pt"
)

DEFAULT_VIDEO = (
    r"F:\motorcycle group project\PSU Transport Project 2026"
    r"\Test\Run1\Input\20260907_073251A_.mp4"
)

DEFAULT_OUTPUT = (
    r"F:\motorcycle group project\PSU Transport Project 2026"
    r"\Test\Run1\Output"
)


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
    "draw_center": True,
    "draw_trail": True,
    "trail_length": "30",

    "save_video": True,
    "save_csv": True,
    "csv_flush": "100",

    "research_mode": True,

    # Zone assignment / reference-point settings
    "zone_assignment_method": "Weighted",
    "zone_point_preset": "Bottom Center",
    "zone_point_x": "50",
    "zone_point_y": "50",
    "zone_bottom_weight": "50",
    "zone_bbox_weight": "35",
    "zone_custom_weight": "15",
    "zone_min_confidence": "60",
    "zone_min_difference": "15",
    "zone_confirmation_frames": "3",
}


# ============================================================
# APPLICATION
# ============================================================

ZONE_NAMES = [f"Zone {i}" for i in range(1, 7)]
LINE_NAMES = [f"Line {i}" for i in range(1, 7)]


class Run1App:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "PK Studio - Run 1 Research"
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

        self.create_variables()
        self.build_gui()
        self.update_hardware_info()

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

        # Zone assignment / reference point controls.
        self.zone_assignment_method_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_assignment_method"])
        self.zone_point_preset_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_point_preset"])
        self.zone_point_x_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_point_x"])
        self.zone_point_y_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_point_y"])
        self.zone_bottom_weight_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_bottom_weight"])
        self.zone_bbox_weight_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_bbox_weight"])
        self.zone_custom_weight_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_custom_weight"])
        self.zone_min_confidence_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_min_confidence"])
        self.zone_min_difference_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_min_difference"])
        self.zone_confirmation_frames_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_confirmation_frames"])

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

        main = ttk.Frame(
            self.root,
            padding=10
        )

        main.pack(
            fill="both",
            expand=True
        )

        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        header = ttk.Frame(main)

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8)
        )

        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="PK Studio - Run 1 Research",
            font=("Segoe UI", 20, "bold")
        ).grid(row=0, column=0)

        ttk.Label(
            header,
            text="Vehicle Detection + Tracking + Trajectory Research",
            font=("Segoe UI", 10)
        ).grid(row=1, column=0, pady=(2, 0))

        center = ttk.Frame(main)

        center.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        center.rowconfigure(0, weight=1)
        center.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            center,
            highlightthickness=0
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar = ttk.Scrollbar(
            center,
            orient="vertical",
            command=self.canvas.yview
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.content = ttk.Frame(
            self.canvas,
            padding=(5, 5, 10, 20)
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw"
        )

        self.content.bind(
            "<Configure>",
            self.on_content_configure
        )

        self.canvas.bind(
            "<Configure>",
            self.on_canvas_configure
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            self.on_mousewheel
        )

        self.content.columnconfigure(0, weight=1)
        self.content.columnconfigure(1, weight=1)

        self.build_preset_section()
        self.build_file_section()
        self.build_detection_section()
        self.build_processing_section()
        self.build_bytetrack_section()
        self.build_output_section()
        self.build_information_section()
        self.build_measurement_section()

        bottom = ttk.Frame(main)

        bottom.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(8, 0)
        )

        bottom.columnconfigure(0, weight=1)

        ttk.Label(
            bottom,
            textvariable=self.hardware_var,
            anchor="w"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Label(
            bottom,
            textvariable=self.status_var,
            anchor="w"
        ).grid(
            row=1,
            column=0,
            sticky="w"
        )

        ttk.Label(
            bottom,
            textvariable=self.progress_var,
            anchor="e"
        ).grid(
            row=1,
            column=1,
            padx=10
        )

        ttk.Label(
            bottom,
            textvariable=self.time_var,
            anchor="e"
        ).grid(
            row=1,
            column=2,
            padx=10
        )

        self.pause_button = ttk.Button(
            bottom,
            text="Ⅱ PAUSE",
            command=self.toggle_pause,
            state="disabled"
        )

        self.pause_button.grid(
            row=0,
            column=3,
            rowspan=2,
            padx=5,
            ipadx=10,
            ipady=8
        )

        self.start_button = ttk.Button(
            bottom,
            text="▶ START RUN 1",
            command=self.start_run
        )

        self.start_button.grid(
            row=0,
            column=4,
            rowspan=2,
            padx=5,
            ipadx=15,
            ipady=8
        )

        self.stop_button = ttk.Button(
            bottom,
            text="■ STOP",
            command=self.request_stop,
            state="disabled"
        )

        self.stop_button.grid(
            row=0,
            column=5,
            rowspan=2,
            padx=(5, 0),
            ipadx=12,
            ipady=8
        )

    # ========================================================
    # INTEGRATED ZONE / LINE MEASUREMENT
    # ========================================================

    def build_measurement_section(self):

        frame = ttk.LabelFrame(
            self.content,
            text="Measurement: PK Studio Zones (Integrated with Run 1)",
            padding=10
        )
        frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=5)
        frame.columnconfigure(1, weight=1)

        ttk.Label(
            frame,
            text="Load a PK Studio Zone export. Both .JSON and .PY formats are supported.",
        ).grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 8))

        ttk.Label(frame, text="PK Studio Zone File").grid(
            row=1, column=0, sticky="w", padx=(0, 8)
        )
        ttk.Entry(frame, textvariable=self.zone_line_config_var).grid(
            row=1, column=1, columnspan=4, sticky="ew"
        )
        ttk.Button(frame, text="Browse", command=self.load_measurement_config).grid(
            row=1, column=5, padx=4
        )
        ttk.Button(frame, text="Reload", command=self.load_measurement_config).grid(
            row=1, column=6, padx=4
        )

        ttk.Label(frame, text="Zone Assignment Method").grid(row=2, column=0, sticky="w", pady=(8, 3))
        ttk.Combobox(
            frame, textvariable=self.zone_assignment_method_var,
            values=["Point", "Bottom Center", "Bounding Box Majority", "Weighted"],
            state="readonly", width=24
        ).grid(row=2, column=1, sticky="w", pady=(8, 3))

        ttk.Label(frame, text="Reference Point").grid(row=2, column=2, sticky="e", padx=(15, 5), pady=(8, 3))
        ttk.Combobox(
            frame, textvariable=self.zone_point_preset_var,
            values=["Top Center", "Center", "Bottom Center", "Bottom 25%", "Custom"],
            state="readonly", width=18
        ).grid(row=2, column=3, sticky="w", pady=(8, 3))

        ttk.Label(frame, text="X %").grid(row=2, column=4, sticky="e", padx=(10, 3), pady=(8, 3))
        ttk.Entry(frame, textvariable=self.zone_point_x_var, width=7).grid(row=2, column=5, sticky="w", pady=(8, 3))
        ttk.Label(frame, text="Y %").grid(row=2, column=6, sticky="e", padx=(8, 3), pady=(8, 3))
        ttk.Entry(frame, textvariable=self.zone_point_y_var, width=7).grid(row=2, column=7, sticky="w", pady=(8, 3))

        ttk.Label(frame, text="Weighted: Bottom %").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.zone_bottom_weight_var, width=8).grid(row=3, column=1, sticky="w", pady=3)
        ttk.Label(frame, text="BBox %").grid(row=3, column=2, sticky="e", padx=(10, 5), pady=3)
        ttk.Entry(frame, textvariable=self.zone_bbox_weight_var, width=8).grid(row=3, column=3, sticky="w", pady=3)
        ttk.Label(frame, text="Custom Point %").grid(row=3, column=4, sticky="e", padx=(10, 5), pady=3)
        ttk.Entry(frame, textvariable=self.zone_custom_weight_var, width=8).grid(row=3, column=5, sticky="w", pady=3)
        ttk.Label(frame, text="Weights are normalized automatically").grid(row=3, column=6, columnspan=2, sticky="w", pady=3)

        ttk.Label(frame, text="Minimum Confidence %").grid(row=4, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.zone_min_confidence_var, width=8).grid(row=4, column=1, sticky="w", pady=3)
        ttk.Label(frame, text="Minimum Difference %").grid(row=4, column=2, sticky="e", padx=(10, 5), pady=3)
        ttk.Entry(frame, textvariable=self.zone_min_difference_var, width=8).grid(row=4, column=3, sticky="w", pady=3)
        ttk.Label(frame, text="Temporal Confirmation (frames)").grid(row=4, column=4, sticky="e", padx=(10, 5), pady=3)
        ttk.Entry(frame, textvariable=self.zone_confirmation_frames_var, width=8).grid(row=4, column=5, sticky="w", pady=3)

        ttk.Label(
            frame,
            text="Primary default: Bottom Center + BBox Area + Custom Point | Ambiguous results stay Uncertain until confirmed.",
        ).grid(row=5, column=0, columnspan=8, sticky="w", pady=(5, 2))

        ttk.Label(
            frame,
            textvariable=self.measurement_status_var,
            anchor="w"
        ).grid(row=6, column=0, columnspan=8, sticky="w", pady=(8, 0))

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
            raise ValueError("No valid Zone 1-6 definitions were found in the selected PK Studio file.")

        # JSON is Zone-only in the current PK Studio format.
        lines = {name: [] for name in LINE_NAMES}
        raw_lines = data.get("lines", {})
        if isinstance(raw_lines, dict):
            for name, pts in raw_lines.items():
                if name in lines and isinstance(pts, list):
                    cleaned = []
                    for p in pts:
                        try:
                            cleaned.append((int(p[0]), int(p[1])))
                        except Exception:
                            pass
                    if len(cleaned) == 2:
                        lines[name] = cleaned

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
            raise ValueError("No Zone 1-6 definitions were found in the PK Studio Python export.")

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
        """Draw PK Studio zones/lines and live zone timing/counts on the preview/output frame."""
        # Draw polygons and labels even when no detection exists.
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
            cv2.polylines(frame, [pts], True, color, 3, cv2.LINE_AA)
            if meta.get("show_label", True):
                x, y = map(int, polygon[0])
                cv2.putText(frame, f"{zname} | entries: {zone_entry_count.get(zname, 0)}", (x, max(20, y - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2, cv2.LINE_AA)

        # Draw line geometry when supplied by a compatible config.
        for lname in LINE_NAMES:
            line = self.lines.get(lname, [])
            if len(line) != 2:
                continue
            p1 = tuple(map(int, line[0])); p2 = tuple(map(int, line[1]))
            cv2.line(frame, p1, p2, (255, 255, 255), 4, cv2.LINE_AA)
            cv2.circle(frame, p1, 6, (255, 255, 255), -1)
            cv2.circle(frame, p2, 6, (255, 255, 255), -1)
            mx, my = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
            cv2.putText(frame, f"{lname} | crossings: {line_cross_count.get(lname, 0)}",
                        (mx, max(20, my - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        # Live per-track zone timer. The timer begins at the exact frame where
        # the tracked centroid is first detected inside the zone.
        now = frame_index / fps if fps > 0 else 0.0
        for track_id, zmap in zone_track_state.items():
            zone_states = zmap.get("zone_states", {})
            active = []
            for zname, zs in zone_states.items():
                if zs.get("inside") and zs.get("entry_time") is not None:
                    duration = max(0.0, now - float(zs["entry_time"]))
                    active.append(f"{zname}: {duration:.1f}s")

            point = zmap.get("last_point") or zmap.get("previous_confirmed_point")
            if point is None:
                continue

            x, y = map(int, point)
            confirmed = zmap.get("confirmed_zone") or "Uncertain"
            conf = float(zmap.get("confirmed_confidence", 0.0)) * 100.0
            cv2.putText(
                frame,
                f"ID {track_id} | Zone: {confirmed} ({conf:.0f}%)",
                (x + 8, max(20, y - 22)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2, cv2.LINE_AA
            )
            for idx, text in enumerate(active):
                cv2.putText(
                    frame, f"ID {track_id} | {text}",
                    (x + 8, y + 22 + idx * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA
                )

    def get_zone_reference_point(self, x1, y1, x2, y2):
        """Return the user-selected reference point inside a bounding box."""
        preset = self.zone_point_preset_var.get().strip()
        presets = {
            "Top Center": (50.0, 0.0),
            "Center": (50.0, 50.0),
            "Bottom Center": (50.0, 100.0),
            "Bottom 25%": (50.0, 75.0),
        }
        if preset in presets:
            px, py = presets[preset]
        else:
            px = float(self.zone_point_x_var.get())
            py = float(self.zone_point_y_var.get())
        px = max(0.0, min(100.0, px))
        py = max(0.0, min(100.0, py))
        return (
            int(round(x1 + (x2 - x1) * px / 100.0)),
            int(round(y1 + (y2 - y1) * py / 100.0)),
        )

    @staticmethod
    def bbox_zone_overlap_ratio(x1, y1, x2, y2, polygon):
        """Return the fraction of the detection bounding-box area inside a Zone polygon."""
        if len(polygon) < 3 or x2 <= x1 or y2 <= y1:
            return 0.0
        bx1, by1, bx2, by2 = int(x1), int(y1), int(x2), int(y2)
        w, h = bx2 - bx1, by2 - by1
        shifted = np.array([[(int(px) - bx1, int(py) - by1) for px, py in polygon]], dtype=np.int32)
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, shifted, 1)
        return float(np.count_nonzero(mask)) / float(w * h)

    def assign_zone_candidate(self, x1, y1, x2, y2):
        """Calculate the best Zone candidate using point, bottom-center and bbox overlap."""
        zones = [z for z in ZONE_NAMES if len(self.zones.get(z, [])) >= 3]
        if not zones:
            return None, 0.0, {}, None, {}

        custom_point = self.get_zone_reference_point(x1, y1, x2, y2)
        bottom_point = (int(round((x1 + x2) / 2.0)), int(y2))
        custom_zone = next((z for z in zones if self.point_in_zone(*custom_point, self.zones[z])), None)
        bottom_zone = next((z for z in zones if self.point_in_zone(*bottom_point, self.zones[z])), None)
        overlaps = {z: self.bbox_zone_overlap_ratio(x1, y1, x2, y2, self.zones[z]) for z in zones}

        method = self.zone_assignment_method_var.get().strip() or "Weighted"
        if method == "Point":
            scores = {z: (1.0 if z == custom_zone else 0.0) for z in zones}
            return custom_zone, (1.0 if custom_zone else 0.0), overlaps, custom_point, scores

        if method == "Bottom Center":
            scores = {z: (1.0 if z == bottom_zone else 0.0) for z in zones}
            return bottom_zone, (1.0 if bottom_zone else 0.0), overlaps, bottom_point, scores

        if method == "Bounding Box Majority":
            scores = dict(overlaps)
            ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            if not ordered or ordered[0][1] <= 0:
                return None, 0.0, overlaps, custom_point, scores
            return ordered[0][0], ordered[0][1], overlaps, custom_point, scores

        # Weighted mode: Bottom Center + BBox Area + Custom Point.
        try:
            wb = max(0.0, float(self.zone_bottom_weight_var.get()))
            wbox = max(0.0, float(self.zone_bbox_weight_var.get()))
            wc = max(0.0, float(self.zone_custom_weight_var.get()))
        except Exception:
            wb, wbox, wc = 50.0, 35.0, 15.0
        total_w = wb + wbox + wc
        if total_w <= 0:
            wb, wbox, wc, total_w = 50.0, 35.0, 15.0, 100.0
        wb, wbox, wc = wb / total_w, wbox / total_w, wc / total_w

        scores = {z: wbox * overlaps.get(z, 0.0) for z in zones}
        if bottom_zone:
            scores[bottom_zone] += wb
        if custom_zone:
            scores[custom_zone] += wc

        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        if not ordered or ordered[0][1] <= 0:
            return None, 0.0, overlaps, custom_point, scores
        return ordered[0][0], float(ordered[0][1]), overlaps, custom_point, scores


    def zone_has_any_overlap(self, x1, y1, x2, y2):
        """True when the detection bbox or its reference points touch any configured Zone."""
        zones = [z for z in ZONE_NAMES if len(self.zones.get(z, [])) >= 3]
        if not zones:
            return False
        custom_point = self.get_zone_reference_point(x1, y1, x2, y2)
        bottom_point = (int(round((x1 + x2) / 2.0)), int(y2))
        if any(self.point_in_zone(*custom_point, self.zones[z]) for z in zones):
            return True
        if any(self.point_in_zone(*bottom_point, self.zones[z]) for z in zones):
            return True
        return any(self.bbox_zone_overlap_ratio(x1, y1, x2, y2, self.zones[z]) > 0 for z in zones)

    def confirm_zone(self, track_state, candidate, candidate_confidence, frame_index, confirmation_frames):
        """Apply temporal confirmation so Zone changes do not flicker frame-to-frame."""
        if candidate is None:
            track_state["candidate_zone"] = None
            track_state["candidate_count"] = 0
            track_state["candidate_confidence"] = 0.0
            return track_state.get("confirmed_zone"), False

        if candidate == track_state.get("candidate_zone"):
            track_state["candidate_count"] = track_state.get("candidate_count", 0) + 1
        else:
            track_state["candidate_zone"] = candidate
            track_state["candidate_count"] = 1
            track_state["candidate_confidence"] = candidate_confidence

        track_state["candidate_confidence"] = candidate_confidence
        if track_state["candidate_count"] >= max(1, confirmation_frames):
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

    def on_content_configure(self, event=None):

        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def on_canvas_configure(self, event):

        self.canvas.itemconfig(
            self.canvas_window,
            width=event.width
        )

    def on_mousewheel(self, event):

        if event.delta:
            self.canvas.yview_scroll(
                int(-event.delta / 120),
                "units"
            )

    # ========================================================
    # SECTION
    # ========================================================

    def section(self, title, column, row):

        frame = ttk.LabelFrame(
            self.content,
            text=title,
            padding=10
        )

        frame.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=5,
            pady=5
        )

        frame.columnconfigure(1, weight=1)

        return frame

    # ========================================================
    # PRESET
    # ========================================================

    def build_preset_section(self):

        frame = ttk.LabelFrame(
            self.content,
            text="Preset / Experiment",
            padding=10
        )

        frame.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=5,
            pady=5
        )

        frame.columnconfigure(1, weight=1)

        ttk.Label(
            frame,
            text="Preset"
        ).grid(
            row=0,
            column=0,
            padx=(0, 10)
        )

        self.preset_var = tk.StringVar(
            value="Research Mode"
        )

        ttk.Combobox(
            frame,
            textvariable=self.preset_var,
            values=[
                "Research Mode",
                "ID Stability Test",
                "Fast Test",
                "Custom"
            ],
            state="readonly",
            width=25
        ).grid(
            row=0,
            column=1,
            sticky="w"
        )

        ttk.Button(
            frame,
            text="Apply Preset",
            command=self.apply_preset
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            frame,
            text="Save Settings",
            command=self.save_settings
        ).grid(row=0, column=3, padx=5)

        ttk.Button(
            frame,
            text="Load Settings",
            command=self.load_settings
        ).grid(row=0, column=4, padx=5)

        ttk.Checkbutton(
            frame,
            text="Research Mode",
            variable=self.research_mode_var
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0)
        )

    # ========================================================
    # FILE
    # ========================================================

    def build_file_section(self):

        frame = self.section(
            "File Settings",
            0,
            1
        )

        self.add_entry(
            frame, 0, "Run Name",
            self.run_name_var
        )

        self.add_entry(
            frame, 1, "Model",
            self.model_var,
            self.browse_model
        )

        self.add_entry(
            frame, 2, "Video",
            self.video_var,
            self.browse_video
        )

        self.add_entry(
            frame, 3, "Output",
            self.output_var,
            self.browse_output
        )

    # ========================================================
    # DETECTION
    # ========================================================

    def build_detection_section(self):

        frame = self.section(
            "Detection Settings",
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
            "Processing Settings",
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
            text="GPU 0 = NVIDIA GeForce GTX 1650"
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
            "ByteTrack Settings",
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
    # OUTPUT
    # ========================================================

    def build_output_section(self):

        frame = self.section(
            "Output Settings",
            0,
            3
        )

        ttk.Checkbutton(
            frame,
            text="Show Preview",
            variable=self.show_preview_var
        ).grid(row=0, column=0, sticky="w", pady=3)

        ttk.Checkbutton(
            frame,
            text="Draw Center Point",
            variable=self.draw_center_var
        ).grid(row=0, column=1, sticky="w", pady=3)

        ttk.Checkbutton(
            frame,
            text="Draw Track Trail",
            variable=self.draw_trail_var
        ).grid(row=1, column=0, sticky="w", pady=3)

        ttk.Label(
            frame,
            text="Trail Length"
        ).grid(
            row=1,
            column=1,
            sticky="w"
        )

        ttk.Entry(
            frame,
            textvariable=self.trail_length_var,
            width=10
        ).grid(
            row=1,
            column=2,
            sticky="w"
        )

        ttk.Checkbutton(
            frame,
            text="Save Video",
            variable=self.save_video_var
        ).grid(row=2, column=0, sticky="w", pady=3)

        ttk.Checkbutton(
            frame,
            text="Save CSV Trajectory",
            variable=self.save_csv_var
        ).grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(
            frame,
            text="CSV Flush Every"
        ).grid(
            row=3,
            column=0,
            sticky="w"
        )

        ttk.Entry(
            frame,
            textvariable=self.csv_flush_var,
            width=10
        ).grid(
            row=3,
            column=1,
            sticky="w"
        )

    # ========================================================
    # INFORMATION
    # ========================================================

    def build_information_section(self):

        frame = self.section(
            "Run 1 Information",
            1,
            3
        )

        text = (
            "Run 1 Research Processing Flow\n\n"
            "Input Video\n"
            "      ↓\n"
            "Vehicle Detection\n"
            "      ↓\n"
            "ByteTrack / BoT-SORT\n"
            "      ↓\n"
            "Persistent Track ID\n"
            "      ↓\n"
            "Reference Point + BBox Zone Assignment\n"
            "      ↓\n"
            "Temporal Zone Confirmation\n"
            "      ↓\n"
            "Trajectory / Zone CSV\n\n"
            "CSV:\n"
            "frame\n"
            "timestamp\n"
            "track_id\n"
            "class_id\n"
            "class_name\n"
            "confidence\n"
            "bbox_x1 / y1 / x2 / y2\n"
            "center_x / center_y"
        )

        ttk.Label(
            frame,
            text=text,
            justify="left"
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w"
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
            textvariable=variable
        )

        entry.grid(
            row=row,
            column=1,
            sticky="ew",
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
    # PRESETS
    # ========================================================

    def set_zone_assignment_defaults(self):
        """Apply the research defaults described in the PK Studio Zone guidance."""
        self.zone_assignment_method_var.set("Weighted")
        self.zone_point_preset_var.set("Bottom Center")
        self.zone_point_x_var.set("50")
        self.zone_point_y_var.set("50")
        self.zone_bottom_weight_var.set("50")
        self.zone_bbox_weight_var.set("35")
        self.zone_custom_weight_var.set("15")
        self.zone_min_confidence_var.set("60")
        self.zone_min_difference_var.set("15")
        self.zone_confirmation_frames_var.set("3")

    def apply_preset(self):

        preset = self.preset_var.get()

        if preset == "Research Mode":

            self.conf_var.set("0.25")
            self.iou_var.set("0.50")
            self.img_size_var.set("640")
            self.tracker_var.set("ByteTrack")

            self.device_var.set("Auto")
            self.precision_var.set("Auto")

            self.frame_skip_var.set(
                "NO - Process every frame"
            )

            self.track_high_var.set("0.25")
            self.track_low_var.set("0.10")
            self.new_track_var.set("0.25")
            self.track_buffer_var.set("30")
            self.match_threshold_var.set("0.80")

            self.show_preview_var.set(True)
            self.draw_center_var.set(True)
            self.draw_trail_var.set(True)

            self.trail_length_var.set("30")

            self.save_video_var.set(True)
            self.save_csv_var.set(True)

            self.research_mode_var.set(True)
            self.set_zone_assignment_defaults()

        elif preset == "ID Stability Test":

            self.conf_var.set("0.25")
            self.iou_var.set("0.50")
            self.img_size_var.set("640")
            self.tracker_var.set("ByteTrack")

            self.device_var.set("Auto")
            self.precision_var.set("Auto")

            self.frame_skip_var.set(
                "NO - Process every frame"
            )

            self.track_high_var.set("0.20")
            self.track_low_var.set("0.05")
            self.new_track_var.set("0.20")
            self.track_buffer_var.set("60")
            self.match_threshold_var.set("0.80")

            self.show_preview_var.set(True)
            self.draw_center_var.set(True)
            self.draw_trail_var.set(True)

            self.trail_length_var.set("60")

            self.save_video_var.set(True)
            self.save_csv_var.set(True)

            self.research_mode_var.set(False)

        elif preset == "Fast Test":

            self.conf_var.set("0.25")
            self.iou_var.set("0.50")
            self.img_size_var.set("416")
            self.tracker_var.set("ByteTrack")

            self.device_var.set("Auto")
            self.precision_var.set("Auto")

            self.frame_skip_var.set(
                "1 - Process every 2nd frame"
            )

            self.track_high_var.set("0.25")
            self.track_low_var.set("0.10")
            self.new_track_var.set("0.25")
            self.track_buffer_var.set("30")
            self.match_threshold_var.set("0.80")

            self.show_preview_var.set(False)
            self.draw_center_var.set(False)
            self.draw_trail_var.set(False)

            self.trail_length_var.set("30")

            self.save_video_var.set(False)
            self.save_csv_var.set(True)

            self.research_mode_var.set(False)

        self.status_var.set(
            f"Preset applied: {preset}"
        )

    # ========================================================
    # SAVE SETTINGS
    # ========================================================

    def get_settings(self):

        return {
            "run_name": self.run_name_var.get(),

            "model": self.model_var.get(),
            "video": self.video_var.get(),
            "output": self.output_var.get(),

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
            "save_csv": self.save_csv_var.get(),

            "csv_flush": self.csv_flush_var.get(),

            "research_mode": self.research_mode_var.get(),

            "zone_assignment_method": self.zone_assignment_method_var.get(),
            "zone_point_preset": self.zone_point_preset_var.get(),
            "zone_point_x": self.zone_point_x_var.get(),
            "zone_point_y": self.zone_point_y_var.get(),
            "zone_bottom_weight": self.zone_bottom_weight_var.get(),
            "zone_bbox_weight": self.zone_bbox_weight_var.get(),
            "zone_custom_weight": self.zone_custom_weight_var.get(),
            "zone_min_confidence": self.zone_min_confidence_var.get(),
            "zone_min_difference": self.zone_min_difference_var.get(),
            "zone_confirmation_frames": self.zone_confirmation_frames_var.get(),
        }

    def save_settings(self):

        settings = self.get_settings()

        path = filedialog.asksaveasfilename(
            title="Save Run 1 Settings",
            defaultextension=".json",
            filetypes=[
                ("JSON", "*.json")
            ],
            initialfile=(
                self.run_name_var.get()
                + "_settings.json"
            )
        )

        if not path:
            return

        try:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    settings,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            messagebox.showinfo(
                "Settings",
                f"Settings saved\n\n{path}"
            )

        except Exception as e:

            messagebox.showerror(
                "Save Error",
                str(e)
            )

    # ========================================================
    # LOAD SETTINGS
    # ========================================================

    def load_settings(self):

        path = filedialog.askopenfilename(
            title="Load Run 1 Settings",
            filetypes=[
                ("JSON", "*.json"),
                ("All Files", "*.*")
            ]
        )

        if not path:
            return

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                settings = json.load(f)

            self.set_settings(settings)

            messagebox.showinfo(
                "Settings",
                "Settings loaded"
            )

        except Exception as e:

            messagebox.showerror(
                "Load Error",
                str(e)
            )

    def set_settings(self, settings):

        pairs = [
            ("run_name", self.run_name_var),
            ("model", self.model_var),
            ("video", self.video_var),
            ("output", self.output_var),
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
            ("save_csv", self.save_csv_var),
            ("csv_flush", self.csv_flush_var),
            ("research_mode", self.research_mode_var),
            ("zone_assignment_method", self.zone_assignment_method_var),
            ("zone_point_preset", self.zone_point_preset_var),
            ("zone_point_x", self.zone_point_x_var),
            ("zone_point_y", self.zone_point_y_var),
            ("zone_bottom_weight", self.zone_bottom_weight_var),
            ("zone_bbox_weight", self.zone_bbox_weight_var),
            ("zone_custom_weight", self.zone_custom_weight_var),
            ("zone_min_confidence", self.zone_min_confidence_var),
            ("zone_min_difference", self.zone_min_difference_var),
            ("zone_confirmation_frames", self.zone_confirmation_frames_var),
        ]

        for key, variable in pairs:

            variable.set(
                settings.get(
                    key,
                    DEFAULT_SETTINGS[key]
                )
            )

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
            for value in [
                float(self.zone_point_x_var.get()),
                float(self.zone_point_y_var.get()),
                float(self.zone_bottom_weight_var.get()),
                float(self.zone_bbox_weight_var.get()),
                float(self.zone_custom_weight_var.get()),
                float(self.zone_min_confidence_var.get()),
                float(self.zone_min_difference_var.get()),
            ]:
                if value < 0:
                    raise ValueError("Zone assignment numeric values cannot be negative")
            if not 0 <= float(self.zone_point_x_var.get()) <= 100:
                raise ValueError("Reference Point X must be between 0 and 100%")
            if not 0 <= float(self.zone_point_y_var.get()) <= 100:
                raise ValueError("Reference Point Y must be between 0 and 100%")
            if not 0 <= float(self.zone_min_confidence_var.get()) <= 100:
                raise ValueError("Minimum Confidence must be between 0 and 100%")
            if not 0 <= float(self.zone_min_difference_var.get()) <= 100:
                raise ValueError("Minimum Difference must be between 0 and 100%")
            if int(self.zone_confirmation_frames_var.get()) < 1:
                raise ValueError("Temporal Confirmation must be at least 1 frame")
            if (float(self.zone_bottom_weight_var.get()) + float(self.zone_bbox_weight_var.get()) + float(self.zone_custom_weight_var.get())) <= 0:
                raise ValueError("At least one Weighted Zone component must be greater than 0")
        except Exception as e:
            messagebox.showerror("Zone Assignment Settings", str(e))
            return False

        if self.research_mode_var.get():

            self.frame_skip_var.set(
                "NO - Process every frame"
            )

            self.save_csv_var.set(True)

        return True

    # ========================================================
    # DEVICE
    # ========================================================

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

    def create_bytetrack_yaml(self, output_dir):

        yaml_path = os.path.join(
            output_dir,
            "Run_1_Research_ByteTrack.yaml"
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

    def start_run(self):
        try:
            self.validate_measurements()
        except Exception as exc:
            messagebox.showerror("Measurement Configuration", str(exc))
            return

        if self.running:
            return

        if not self.validate_settings():
            return

        # Check CUDA before starting the worker.
        # This makes an invalid GPU selection visible immediately.
        try:
            selected_device = self.resolve_device()
        except Exception as e:
            messagebox.showerror(
                "CUDA / Device Error",
                str(e)
            )
            return

        settings = self.get_settings()

        self.running = True

        self.stop_event.clear()
        self.pause_event.set()

        self.start_button.config(
            state="disabled"
        )

        self.pause_button.config(
            state="normal",
            text="Ⅱ PAUSE"
        )

        self.stop_button.config(
            state="normal"
        )

        self.status_var.set(
            f"Starting Run 1 | Device = {selected_device}"
        )

        self.progress_var.set("")
        self.time_var.set("")

        self.worker_thread = threading.Thread(
            target=self.run_processing,
            args=(settings,),
            daemon=True
        )

        self.worker_thread.start()

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

        self.root.after(
            0,
            update
        )

    # ========================================================
    # PROCESSING
    # ========================================================

    def run_processing(self, settings):

        cap = None
        writer = None
        csv_file = None

        try:

            model_path = settings["model"]
            video_path = settings["video"]
            output_dir = settings["output"]

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            run_name = self.safe_filename(
                settings["run_name"]
            )

            # Research outputs required by Run 1.5 specification.
            output_video = os.path.join(
                output_dir,
                run_name + "_Research_Tracking_Result.mp4"
            )

            output_csv = os.path.join(
                output_dir,
                run_name + "_Research_Trajectory.csv"
            )

            output_track_stats = os.path.join(
                output_dir,
                run_name + "_Research_Track_Statistics.csv"
            )

            output_id_switch = os.path.join(
                output_dir,
                run_name + "_Research_ID_Switch_Warnings.csv"
            )

            output_detection_loss = os.path.join(
                output_dir,
                run_name + "_Research_Detection_Loss.csv"
            )

            output_processing_log = os.path.join(
                output_dir,
                run_name + "_Research_Processing_Log.csv"
            )

            output_summary = os.path.join(
                output_dir,
                run_name + "_Research_Run_Summary.json"
            )

            output_settings = os.path.join(
                output_dir,
                run_name + "_Research_Settings.json"
            )

            output_tracker_yaml = os.path.join(
                output_dir,
                run_name + "_Research_ByteTrack.yaml"
            )
            output_measurement_events = os.path.join(
                output_dir, run_name + "_Research_Zone_Line_Events.csv"
            )
            output_zone_summary = os.path.join(
                output_dir, run_name + "_Research_Zone_Summary.csv"
            )
            output_line_summary = os.path.join(
                output_dir, run_name + "_Research_Line_Summary.csv"
            )
            output_measurement_summary = os.path.join(
                output_dir, run_name + "_Research_Measurement_Summary.json"
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
                    use_fp16 = True

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

            model = YOLO(
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

            tracker_name = settings["tracker"]

            if tracker_name == "ByteTrack":

                tracker_path = (
                    self.create_bytetrack_yaml(
                        output_dir
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
                    "frame",
                    "timestamp",
                    "track_id",
                    "class_id",
                    "class_name",
                    "confidence",
                    "bbox_x1",
                    "bbox_y1",
                    "bbox_x2",
                    "bbox_y2",
                    "center_x",
                    "center_y",
                    "reference_x",
                    "reference_y",
                    "zone_assigned",
                    "zone_confidence",
                    "zone_method"
                ])

            else:

                csv_writer = None

            # =================================================
            # RESEARCH OUTPUT FILES / TRACK STATE
            # =================================================

            track_stats_file = open(
                output_track_stats,
                "w",
                newline="",
                encoding="utf-8-sig"
            )
            track_stats_writer = csv.writer(track_stats_file)
            track_stats_writer.writerow([
                "track_id",
                "class_id",
                "class_name",
                "first_frame",
                "last_frame",
                "observed_frames",
                "duration_seconds",
                "detection_count",
                "continuity_ratio",
                "loss_events",
                "max_gap_frames",
                "average_confidence",
                "average_center_x",
                "average_center_y",
                "total_distance_px",
                "average_step_px",
                "status"
            ])

            id_switch_file = open(
                output_id_switch,
                "w",
                newline="",
                encoding="utf-8-sig"
            )
            id_switch_writer = csv.writer(id_switch_file)
            id_switch_writer.writerow([
                "frame",
                "timestamp",
                "old_track_id",
                "new_track_id",
                "class_name",
                "distance_px",
                "reason",
                "warning_level"
            ])

            detection_loss_file = open(
                output_detection_loss,
                "w",
                newline="",
                encoding="utf-8-sig"
            )
            detection_loss_writer = csv.writer(detection_loss_file)
            detection_loss_writer.writerow([
                "track_id",
                "class_name",
                "loss_start_frame",
                "loss_end_frame",
                "gap_frames",
                "loss_start_timestamp",
                "loss_end_timestamp",
                "recovered",
                "recovery_frame"
            ])

            processing_log_file = open(
                output_processing_log,
                "w",
                newline="",
                encoding="utf-8-sig"
            )
            processing_log_writer = csv.writer(processing_log_file)
            processing_log_writer.writerow([
                "frame",
                "timestamp",
                "processed_frames",
                "fps",
                "detections",
                "active_tracks",
                "device",
                "precision",
                "status"
            ])

            measurement_events_file = open(output_measurement_events, "w", newline="", encoding="utf-8-sig")
            measurement_events_writer = csv.writer(measurement_events_file)
            measurement_events_writer.writerow([
                "frame", "timestamp", "track_id", "class_name", "measurement_type",
                "measurement_name", "event", "duration_seconds", "distance_px", "speed_px_s", "direction"
            ])

            zone_summary_file = open(output_zone_summary, "w", newline="", encoding="utf-8-sig")
            zone_summary_writer = csv.writer(zone_summary_file)
            zone_summary_writer.writerow([
                "zone", "track_id", "class_name", "entry_frame", "entry_timestamp",
                "exit_frame", "exit_timestamp", "duration_seconds", "distance_px", "average_speed_px_s"
            ])

            line_summary_file = open(output_line_summary, "w", newline="", encoding="utf-8-sig")
            line_summary_writer = csv.writer(line_summary_file)
            line_summary_writer.writerow([
                "line", "track_id", "class_name", "crossing_frame", "crossing_timestamp", "direction"
            ])

            # Integrated measurement state. This is updated directly from Run 1 tracking.
            zone_track_state = {}
            line_track_state = {}
            zone_assignment_summary = defaultdict(lambda: defaultdict(int))
            zone_assignment_method = settings.get("zone_assignment_method", "Weighted")
            zone_min_confidence = float(settings.get("zone_min_confidence", "60")) / 100.0
            zone_min_difference = float(settings.get("zone_min_difference", "15")) / 100.0
            zone_confirmation_frames = max(1, int(settings.get("zone_confirmation_frames", "3")))
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
                print("Zone Method :", self.zone_assignment_method_var.get())
                print("Zone Point  :", self.zone_point_preset_var.get())
                print("Zone Confirm:", zone_confirmation_frames, "frames")

            window_name = "PK Studio - Run 1"

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

            frame_index = 0
            processed_frames = 0
            total_detections = 0

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

                success, frame = cap.read()

                if not success:
                    input_finished = True
                    break

                frame_index += 1

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

                        track_kwargs[
                            "quantize"
                        ] = 16

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

                            if track_id >= 0:
                                # Create/update research statistics for this track.
                                timestamp = frame_index / fps
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
                                    # Multi-signal Zone assignment: reference point + bottom
                                    # center + bounding-box overlap, followed by temporal confirmation.
                                    point = self.get_zone_reference_point(x1, y1, x2, y2)
                                    candidate, raw_confidence, overlap_map, custom_point, decision_scores = self.assign_zone_candidate(
                                        x1, y1, x2, y2
                                    )

                                    method_now = self.zone_assignment_method_var.get().strip() or zone_assignment_method
                                    ordered_scores = sorted(decision_scores.values(), reverse=True)
                                    top2_difference = (
                                        ordered_scores[0] - ordered_scores[1]
                                        if len(ordered_scores) >= 2
                                        else (ordered_scores[0] if ordered_scores else 0.0)
                                    )

                                    # Dead Zone: area/weighted assignments must have both
                                    # enough confidence and enough separation from the runner-up.
                                    if method_now in ("Bounding Box Majority", "Weighted"):
                                        if raw_confidence < zone_min_confidence or top2_difference < zone_min_difference:
                                            candidate = None

                                    no_zone = not self.zone_has_any_overlap(x1, y1, x2, y2)
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
                                    })

                                    if no_zone:
                                        zstate["no_zone_count"] = zstate.get("no_zone_count", 0) + 1
                                        if zstate["no_zone_count"] >= zone_confirmation_frames:
                                            zstate["confirmed_zone"] = None
                                            zstate["confirmed_confidence"] = 0.0
                                    else:
                                        zstate["no_zone_count"] = 0

                                    confirmed_zone, zone_changed = self.confirm_zone(
                                        zstate, candidate, raw_confidence,
                                        frame_index, zone_confirmation_frames
                                    )
                                    zstate["last_point"] = point
                                    zstate["last_bbox"] = (x1, y1, x2, y2)
                                    zstate["last_candidate"] = candidate
                                    zstate["last_candidate_confidence"] = raw_confidence
                                    zstate["last_overlap"] = overlap_map
                                    zstate["last_method"] = method_now

                                    if candidate:
                                        zone_assignment_summary[candidate]["observations"] += 1
                                    if confirmed_zone:
                                        zone_assignment_summary[confirmed_zone]["confirmed_frames"] += 1

                                    timestamp_now = frame_index / fps
                                    previous_zone_point = zstate.get("previous_confirmed_point")
                                    previous_confirmed_zone = zstate.get("previous_confirmed_zone")

                                    # Close the previous confirmed Zone when a new Zone is confirmed.
                                    if previous_confirmed_zone and previous_confirmed_zone != confirmed_zone:
                                        oldzs = zstate.get("zone_states", {}).get(previous_confirmed_zone)
                                        if oldzs and oldzs.get("inside"):
                                            duration = max(0.0, timestamp_now - float(oldzs["entry_time"]))
                                            avg_speed = oldzs["distance_px"] / duration if duration > 0 else 0.0
                                            zone_exit_count[previous_confirmed_zone] += 1
                                            measurement_events_writer.writerow([
                                                frame_index, f"{timestamp_now:.6f}", track_id, class_name,
                                                "ZONE", previous_confirmed_zone, "EXIT",
                                                f"{duration:.6f}", f"{oldzs['distance_px']:.3f}",
                                                f"{avg_speed:.6f}", "ZONE_CHANGE"
                                            ])
                                            zone_summary_writer.writerow([
                                                previous_confirmed_zone, track_id, class_name,
                                                oldzs["entry_frame"], f"{oldzs['entry_time']:.6f}",
                                                frame_index, f"{timestamp_now:.6f}", f"{duration:.6f}",
                                                f"{oldzs['distance_px']:.3f}", f"{avg_speed:.6f}"
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
                                            "distance_px": 0.0,
                                            "last_point": None,
                                        })

                                        if confirmed_zone == zname:
                                            if not zs["inside"]:
                                                zs["inside"] = True
                                                zs["entry_frame"] = frame_index
                                                zs["entry_time"] = timestamp_now
                                                zs["distance_px"] = 0.0
                                                zs["last_point"] = point
                                                zone_entry_count[zname] += 1
                                                measurement_events_writer.writerow([
                                                    frame_index, f"{timestamp_now:.6f}", track_id, class_name,
                                                    "ZONE", zname, "ENTRY", "0.000000", "0.000", "", "CONFIRMED"
                                                ])
                                            elif previous_confirmed_zone == zname and previous_zone_point is not None:
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
                                    timestamp_now = frame_index / fps
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

                                    trails[
                                        track_id
                                    ] = deque(
                                        maxlen=trail_length
                                    )

                                trails[
                                    track_id
                                ].append(
                                    (
                                        center_x,
                                        center_y
                                    )
                                )

                            cv2.rectangle(
                                frame,
                                (x1, y1),
                                (x2, y2),
                                (0, 255, 0),
                                2
                            )

                            if settings["draw_center"]:
                                # Red = geometric center; cyan = selected Zone reference point.
                                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                                try:
                                    ref_x, ref_y = self.get_zone_reference_point(x1, y1, x2, y2)
                                    cv2.circle(frame, (ref_x, ref_y), 6, (255, 255, 0), -1)
                                except Exception:
                                    pass

                            if (
                                settings["draw_trail"]
                                and track_id >= 0
                                and track_id in trails
                            ):

                                points = list(
                                    trails[
                                        track_id
                                    ]
                                )

                                for p in range(
                                    1,
                                    len(points)
                                ):

                                    cv2.line(
                                        frame,
                                        points[p - 1],
                                        points[p],
                                        (255, 0, 255),
                                        2
                                    )

                            zone_label = ""
                            if measurement_enabled and track_id >= 0:
                                zs_for_label = zone_track_state.get(track_id, {})
                                confirmed_label = zs_for_label.get("confirmed_zone") or "Uncertain"
                                zone_label = f" | Z:{confirmed_label}"
                            label = (
                                f"ID {track_id} | "
                                f"{class_name} | "
                                f"{confidence:.2f}"
                                f"{zone_label}"
                            )

                            label_y = max(
                                y1 - 10,
                                20
                            )

                            cv2.putText(
                                frame,
                                label,
                                (
                                    x1,
                                    label_y
                                ),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.55,
                                (0, 255, 0),
                                2,
                                cv2.LINE_AA
                            )

                            if csv_writer is not None:

                                timestamp = (
                                    frame_index / fps
                                )

                                csv_writer.writerow([
                                    frame_index,
                                    f"{timestamp:.6f}",
                                    track_id,
                                    class_id,
                                    class_name,
                                    f"{confidence:.6f}",
                                    x1,
                                    y1,
                                    x2,
                                    y2,
                                    center_x,
                                    center_y,
                                    (self.get_zone_reference_point(x1, y1, x2, y2)[0] if measurement_enabled else center_x),
                                    (self.get_zone_reference_point(x1, y1, x2, y2)[1] if measurement_enabled else center_y),
                                    (zone_track_state.get(track_id, {}).get("confirmed_zone", "") if measurement_enabled else ""),
                                    (f"{zone_track_state.get(track_id, {}).get('confirmed_confidence', 0.0):.6f}" if measurement_enabled else ""),
                                    (zone_track_state.get(track_id, {}).get("last_method", "") if measurement_enabled else "")
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
                    frame_index
                    / total_frames
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

                if measurement_enabled:
                    self.draw_measurement_overlay(
                        frame, frame_index, fps, zone_track_state, line_track_state,
                        zone_entry_count, line_cross_count
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

                for line in info_lines:

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

                if writer is not None:

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

            # Finalize integrated Zone/Line measurements before closing any files.
            if measurement_enabled:
                for track_id, zmap in zone_track_state.items():
                    state_info = track_stats.get(track_id, {})
                    class_name_final = state_info.get("class_name", "")
                    last_frame_final = state_info.get("last_frame", frame_index)
                    last_time_final = last_frame_final / fps
                    for zname, zs in zmap.get("zone_states", {}).items():
                        if zs.get("inside") and zs.get("entry_time") is not None:
                            duration = max(0.0, last_time_final - float(zs["entry_time"]))
                            avg_speed = zs["distance_px"] / duration if duration > 0 else 0.0
                            zone_summary_writer.writerow([
                                zname, track_id, class_name_final, zs["entry_frame"],
                                f"{zs['entry_time']:.6f}", last_frame_final,
                                f"{last_time_final:.6f}", f"{duration:.6f}",
                                f"{zs['distance_px']:.3f}", f"{avg_speed:.6f}"
                            ])
                            measurement_events_writer.writerow([
                                last_frame_final, f"{last_time_final:.6f}", track_id,
                                class_name_final, "ZONE", zname, "EXIT_END_OF_TRACK",
                                f"{duration:.6f}", f"{zs['distance_px']:.3f}",
                                f"{avg_speed:.6f}", ""
                            ])

                measurement_events_file.flush()
                zone_summary_file.flush()
                line_summary_file.flush()
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
                            "method": self.zone_assignment_method_var.get(),
                            "reference_point_preset": self.zone_point_preset_var.get(),
                            "reference_point_xy_percent": [
                                float(self.zone_point_x_var.get()),
                                float(self.zone_point_y_var.get())
                            ],
                            "weights_percent": {
                                "bottom_center": float(self.zone_bottom_weight_var.get()),
                                "bbox_area": float(self.zone_bbox_weight_var.get()),
                                "custom_point": float(self.zone_custom_weight_var.get()),
                            },
                            "minimum_confidence_percent": float(self.zone_min_confidence_var.get()),
                            "minimum_difference_percent": float(self.zone_min_difference_var.get()),
                            "temporal_confirmation_frames": zone_confirmation_frames,
                            "assignment_observations": {
                                z: dict(v) for z, v in zone_assignment_summary.items()
                            },
                        },
                        "outputs": {
                            "events": output_measurement_events,
                            "zone_summary": output_zone_summary,
                            "line_summary": output_line_summary,
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

            for research_file in (
                track_stats_file,
                id_switch_file,
                detection_loss_file,
                processing_log_file,
            ):
                try:
                    research_file.flush()
                except Exception:
                    pass

            # Close files only AFTER every final row has been written.
            if csv_file is not None:
                try:
                    csv_file.flush()
                    csv_file.close()
                except Exception:
                    pass

            for research_file in (
                track_stats_file,
                id_switch_file,
                detection_loss_file,
                processing_log_file,
                measurement_events_file,
                zone_summary_file,
                line_summary_file,
            ):
                try:
                    research_file.close()
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
                print("CSV:")
                print(output_csv)

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
                "total_frames": total_frames,
                "processed_frames": processed_frames,
                "frames_with_detection": total_frames_with_detection,
                "total_detections": total_detections,
                "unique_track_ids": len(track_stats),
                "max_active_tracks": max_active_tracks,
                "id_switch_warnings": id_switch_warning_count,
                "detection_loss_events": detection_loss_count,
                "zone_assignment": {
                    "method": self.zone_assignment_method_var.get(),
                    "reference_point_preset": self.zone_point_preset_var.get(),
                    "reference_point_xy_percent": [
                        float(self.zone_point_x_var.get()),
                        float(self.zone_point_y_var.get())
                    ],
                    "weights_percent": {
                        "bottom_center": float(self.zone_bottom_weight_var.get()),
                        "bbox_area": float(self.zone_bbox_weight_var.get()),
                        "custom_point": float(self.zone_custom_weight_var.get()),
                    },
                    "minimum_confidence_percent": float(self.zone_min_confidence_var.get()),
                    "minimum_difference_percent": float(self.zone_min_difference_var.get()),
                    "temporal_confirmation_frames": zone_confirmation_frames,
                },
                "processing_time_seconds": round(total_time, 6),
                "average_fps": round(average_fps, 6),
                "outputs": {
                    "trajectory": output_csv,
                    "tracking_result": output_video if settings["save_video"] else None,
                    "track_statistics": output_track_stats,
                    "id_switch_warnings": output_id_switch,
                    "detection_loss": output_detection_loss,
                    "processing_log": output_processing_log,
                    "run_summary": output_summary,
                    "settings": output_settings,
                    "bytetrack_yaml": output_tracker_yaml if tracker_name == "ByteTrack" else None,
                    "zone_line_events": output_measurement_events if measurement_enabled else None,
                    "zone_summary": output_zone_summary if measurement_enabled else None,
                    "line_summary": output_line_summary if measurement_enabled else None,
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
            if measurement_enabled:
                print("Zone/Line Events    :", output_measurement_events)
                print("Zone Summary        :", output_zone_summary)
                print("Line Summary        :", output_line_summary)
            print("Track Statistics    :", output_track_stats)
            print("ID Switch Warnings  :", output_id_switch)
            print("Detection Loss      :", output_detection_loss)
            print("Processing Log      :", output_processing_log)
            print("Run Summary         :", output_summary)
            print("=" * 75)

            self.root.after(
                0,
                lambda: self.finish_ui(
                    stopped,
                    output_video,
                    output_csv,
                    output_settings,
                    output_summary,
                    output_track_stats,
                    output_id_switch,
                    output_detection_loss,
                    output_processing_log
                )
            )

        except Exception as e:

            try:
                if cap is not None:
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

            for research_file in (
                locals().get("track_stats_file"),
                locals().get("id_switch_file"),
                locals().get("detection_loss_file"),
                locals().get("processing_log_file"),
                locals().get("measurement_events_file"),
                locals().get("zone_summary_file"),
                locals().get("line_summary_file"),
            ):
                try:
                    if research_file is not None:
                        research_file.close()
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
            self.root.after(
                0,
                lambda message=error_message: self.show_error(
                    message
                )
            )

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
        output_processing_log
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
                "Trajectory CSV:\n"
                f"{output_csv}\n\n"
            )

        message += (
            "Research Summary:\n"
            f"{output_summary}\n\n"
            "Track Statistics:\n"
            f"{output_track_stats}\n\n"
            "ID Switch Warnings:\n"
            f"{output_id_switch}\n\n"
            "Detection Loss:\n"
            f"{output_detection_loss}\n\n"
            "Processing Log:\n"
            f"{output_processing_log}\n\n"
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
            "Run 1 Error",
            error
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def on_close(self):

        if self.running:

            answer = messagebox.askyesno(
                "Exit",
                "Run 1 is currently processing\n\n"
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
