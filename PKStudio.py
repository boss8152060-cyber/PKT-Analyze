# ============================================================
# PK Studio V17 - Run 1 + 2 + 3
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
import math
import re
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

class _NullCSVWriter:
    """No-op writer used for legacy research outputs that are no longer exported."""
    def writerow(self, *args, **kwargs):
        pass

    def flush(self):
        pass

    def close(self):
        pass


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
    "draw_center": False,  # retained for settings compatibility; reference point is never drawn
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
}


# ============================================================
# RUN 3 DEFAULTS
# ============================================================

RUN3_VEHICLE_CLASSES = [
    "Bus", "Car", "Motorcycle", "Pickup", "Sidecar", "Truck", "Van"
]

RUN3_MOVEMENTS = ["1→3", "1→5", "4→1"]
RUN3_ALL_MOVEMENTS = ["1→3", "1→5", "4→1", "2→3", "4→5"]

RUN3_DEFAULTS = {
    # Starter preset based on the values currently entered in the researcher UI.
    # NOTE: values marked as implementation defaults are editable and are NOT
    # source-derived research constants.
    "site_id": "8",
    "speed_enabled": True,
    "gap_enabled": False,
    "lc_enabled": False,
    "pet_enabled": False,
    "ppm": "57.822",
    "waiting_speed_threshold": "1.00",      # implementation starter value
    "lateral_axis_angle_deg": "0.00",       # implementation starter value; verify per video
    "lc_longitudinal_window_m": "2.00",     # implementation starter value
    "pet_interaction_distance_m": "3.00",   # implementation starter value
    "pet_threshold_s": "1.00",
    "gap_movement_13": True,
    "gap_movement_15": True,
    "gap_movement_41": True,
    "use_raff": True,
    "use_mle": True,
    # Copy/paste template for Reference Line Mapping.
    # Lines beginning with # are ignored by the program. Replace the Line N
    # entries with the ACTUAL Line 1–6 geometry for the selected Site before
    # enabling Gap Acceptance.
    "reference_line_mapping": "# Site_ID|Movement|Line N\n# 8|1→3|Line N\n# 8|1→5|Line N\n# 8|4→1|Line N\n# 8|2→3|Line N\n# 8|4→5|Line N",
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

        # Trajectory Position controls.
        self.trajectory_position_var = tk.StringVar(value=DEFAULT_SETTINGS["trajectory_position"])
        self.trajectory_offset_var = tk.StringVar(value=DEFAULT_SETTINGS["trajectory_offset"])

        # Zone overlay display controls.
        self.show_zone_boundary_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_zone_boundary"])
        self.show_zone_label_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_zone_label"])
        self.show_zone_label_prefix_var = tk.BooleanVar(value=DEFAULT_SETTINGS["show_zone_label_prefix"])
        self.zone_overlay_opacity_var = tk.StringVar(value=DEFAULT_SETTINGS["zone_overlay_opacity"])


        # ========================================================
        # RUN 3 SAFETY ANALYSIS VARIABLES
        # ========================================================
        self.run3_site_id_var = tk.StringVar(value=RUN3_DEFAULTS["site_id"])
        self.run3_speed_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["speed_enabled"])
        self.run3_gap_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["gap_enabled"])
        self.run3_lc_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["lc_enabled"])
        self.run3_pet_enabled_var = tk.BooleanVar(value=RUN3_DEFAULTS["pet_enabled"])
        self.run3_ppm_var = tk.StringVar(value=RUN3_DEFAULTS["ppm"])
        self.run3_waiting_speed_threshold_var = tk.StringVar(value=RUN3_DEFAULTS["waiting_speed_threshold"])
        self.run3_lateral_axis_angle_var = tk.StringVar(value=RUN3_DEFAULTS["lateral_axis_angle_deg"])
        self.run3_lc_longitudinal_window_var = tk.StringVar(value=RUN3_DEFAULTS["lc_longitudinal_window_m"])
        self.run3_pet_interaction_distance_var = tk.StringVar(value=RUN3_DEFAULTS["pet_interaction_distance_m"])
        self.run3_pet_threshold_var = tk.StringVar(value=RUN3_DEFAULTS["pet_threshold_s"])
        self.run3_gap_movement_13_var = tk.BooleanVar(value=RUN3_DEFAULTS["gap_movement_13"])
        self.run3_gap_movement_15_var = tk.BooleanVar(value=RUN3_DEFAULTS["gap_movement_15"])
        self.run3_gap_movement_41_var = tk.BooleanVar(value=RUN3_DEFAULTS["gap_movement_41"])
        self.run3_use_raff_var = tk.BooleanVar(value=RUN3_DEFAULTS["use_raff"])
        self.run3_use_mle_var = tk.BooleanVar(value=RUN3_DEFAULTS["use_mle"])
        self.run3_reference_mapping_text = RUN3_DEFAULTS["reference_line_mapping"]
        self.run3_width_vars = {
            name: tk.StringVar(value=RUN3_DEFAULTS["vehicle_widths"].get(name, ""))
            for name in RUN3_VEHICLE_CLASSES
        }
        self.run3_result_text = tk.StringVar(value="Run 3: not executed")
        self.run3_last_outputs = {}
        self.run3_last_summary = {}
        self.run3_was_requested = False

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
            text="PK Studio V17 - Run 1 + 2 + 3 Research",
            font=("Segoe UI", 20, "bold")
        ).grid(row=0, column=0)

        ttk.Label(
            header,
            text="Vehicle Detection + Tracking + Trajectory + Safety Analysis",
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

        # ----------------------------------------------------
        # Main settings layout (2 columns)
        # Row 0: Settings (full width)
        # Row 1: File & Zone | Detection
        # Row 2: Processing | ByteTrack
        # Row 3: Display & Output | Run 1 Flow
        # ----------------------------------------------------
        self.build_settings_section()
        self.build_file_section()
        self.build_detection_section()
        self.build_processing_section()
        self.build_bytetrack_section()
        self.build_output_section()
        self.build_information_section()
        self.build_run3_section()

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
            text="▶ START RUN",
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
    # RUN 3 GUI
    # ========================================================

    def build_run3_section(self):
        frame = ttk.LabelFrame(
            self.content,
            text="RUN 3 — Safety Analysis",
            padding=10
        )
        frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

        ttk.Label(frame, text="Site_ID").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(frame, textvariable=self.run3_site_id_var, width=18).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="PPM").grid(row=0, column=2, sticky="e", padx=(12, 8), pady=4)
        ttk.Entry(frame, textvariable=self.run3_ppm_var, width=18).grid(row=0, column=3, sticky="w", pady=4)

        ttk.Label(frame, text="Analysis").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Checkbutton(frame, text="Speed", variable=self.run3_speed_enabled_var).grid(row=1, column=1, sticky="w")
        ttk.Checkbutton(frame, text="Gap Acceptance", variable=self.run3_gap_enabled_var).grid(row=1, column=2, sticky="w")
        ttk.Checkbutton(frame, text="Lateral Clearance", variable=self.run3_lc_enabled_var).grid(row=1, column=3, sticky="w")
        ttk.Checkbutton(frame, text="PET", variable=self.run3_pet_enabled_var).grid(row=2, column=1, sticky="w")

        ttk.Label(frame, text="Waiting detection speed threshold (km/h)").grid(row=2, column=2, sticky="e", padx=(12, 8), pady=4)
        ttk.Entry(frame, textvariable=self.run3_waiting_speed_threshold_var, width=18).grid(row=2, column=3, sticky="w", pady=4)

        ttk.Label(frame, text="Road direction angle (deg) — implementation").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(frame, textvariable=self.run3_lateral_axis_angle_var, width=18).grid(row=3, column=1, sticky="w", pady=4)
        ttk.Label(frame, text="LC longitudinal window (m) — implementation").grid(row=3, column=2, sticky="e", padx=(12, 8), pady=4)
        ttk.Entry(frame, textvariable=self.run3_lc_longitudinal_window_var, width=18).grid(row=3, column=3, sticky="w", pady=4)

        ttk.Label(frame, text="PET interaction distance (m) — implementation").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(frame, textvariable=self.run3_pet_interaction_distance_var, width=18).grid(row=4, column=1, sticky="w", pady=4)
        ttk.Label(frame, text="PET threshold (s)").grid(row=4, column=2, sticky="e", padx=(12, 8), pady=4)
        ttk.Entry(frame, textvariable=self.run3_pet_threshold_var, width=18).grid(row=4, column=3, sticky="w", pady=4)

        ttk.Separator(frame, orient="horizontal").grid(row=5, column=0, columnspan=4, sticky="ew", pady=(8, 6))

        ttk.Label(frame, text="Gap Acceptance — Subject Movement").grid(row=6, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Checkbutton(frame, text="1 → 3", variable=self.run3_gap_movement_13_var).grid(row=6, column=1, sticky="w")
        ttk.Checkbutton(frame, text="1 → 5", variable=self.run3_gap_movement_15_var).grid(row=6, column=2, sticky="w")
        ttk.Checkbutton(frame, text="4 → 1", variable=self.run3_gap_movement_41_var).grid(row=6, column=3, sticky="w")

        ttk.Label(frame, text="Critical Gap").grid(row=7, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Checkbutton(frame, text="Raff", variable=self.run3_use_raff_var).grid(row=7, column=1, sticky="w")
        ttk.Checkbutton(frame, text="MLE", variable=self.run3_use_mle_var).grid(row=7, column=2, sticky="w")

        ttk.Label(frame, text="Reference Line Mapping (copy/paste): Site_ID|Movement|Line N").grid(row=8, column=0, columnspan=3, sticky="w", pady=(4, 2))
        ttk.Button(frame, text="Copy Template", command=self.copy_run3_mapping_template).grid(row=8, column=3, sticky="e", pady=(4, 2))
        self.run3_reference_text = tk.Text(frame, height=6, width=90, wrap="none")
        self.run3_reference_text.grid(row=9, column=0, columnspan=4, sticky="ew", pady=(0, 6))
        self.run3_reference_text.insert("1.0", self.run3_reference_mapping_text)

        ttk.Label(frame, text="Vehicle Widths (m) — source values supplied by researcher").grid(row=10, column=0, columnspan=4, sticky="w", pady=(2, 4))
        width_pairs = [("Bus", 0), ("Car", 2), ("Motorcycle", 0), ("Pickup", 2), ("Sidecar", 0), ("Truck", 2), ("Van", 0)]
        for idx, (name, pair_col) in enumerate(width_pairs):
            row = 11 + idx // 2
            ttk.Label(frame, text=name).grid(row=row, column=pair_col, sticky="e", padx=(4, 4), pady=2)
            ttk.Entry(frame, textvariable=self.run3_width_vars[name], width=10).grid(row=row, column=pair_col + 1, sticky="w", padx=(0, 8), pady=2)

        ttk.Label(
            frame,
            text="Starter preset: Site 8 + PPM 57.822 + width values. Implementation defaults must be verified per site/video; fill Reference Line Mapping before enabling Gap Acceptance.",
            foreground="#666666"
        ).grid(row=15, column=0, columnspan=4, sticky="w", pady=(6, 2))
        ttk.Label(frame, textvariable=self.run3_result_text, foreground="#444444").grid(
            row=16, column=0, columnspan=4, sticky="w", pady=(2, 0)
        )

    # ========================================================
    # INTEGRATED ZONE / LINE MEASUREMENT
    # ========================================================

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
        """Draw optional, faint Zone boundaries and labels.

        Zone fill/background is never drawn. The user can independently toggle
        the Zone boundary and Zone label. Label text can be shown as either
        ``Zone 6`` or simply ``6``. Both are blended onto the original frame
        so they remain visually faint without a solid background rectangle.
        """
        try:
            opacity = max(0.0, min(1.0, float(self.zone_overlay_opacity_var.get()) / 100.0))
        except Exception:
            opacity = 0.45

        show_boundary = bool(self.show_zone_boundary_var.get())
        show_label = bool(self.show_zone_label_var.get())

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
                    label = zname if self.show_zone_label_prefix_var.get() else zname.replace("Zone ", "", 1)
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

    def get_zone_reference_point(self, x1, y1, x2, y2):
        """Return the selected Trajectory Position inside the bounding box.

        Nine anchors are supported: Top, Center, Bottom, Left, Right,
        Top Left, Top Right, Bottom Left, Bottom Right.
        Offset (%) moves the anchor inward from the selected edge(s).
        """
        position = self.trajectory_position_var.get().strip()
        try:
            offset = max(0.0, min(50.0, float(self.trajectory_offset_var.get())))
        except Exception:
            offset = 0.0

        anchors = {
            "Top": (50.0, 0.0),
            "Center": (50.0, 50.0),
            "Bottom": (50.0, 100.0),
            "Left": (0.0, 50.0),
            "Right": (100.0, 50.0),
            "Top Left": (0.0, 0.0),
            "Top Right": (100.0, 0.0),
            "Bottom Left": (0.0, 100.0),
            "Bottom Right": (100.0, 100.0),
        }
        px, py = anchors.get(position, anchors["Center"])

        # Move only the coordinates that touch an edge.
        if px == 0.0:
            px = offset
        elif px == 100.0:
            px = 100.0 - offset

        if py == 0.0:
            py = offset
        elif py == 100.0:
            py = 100.0 - offset

        return (
            int(round(x1 + (x2 - x1) * px / 100.0)),
            int(round(y1 + (y2 - y1) * py / 100.0)),
        )


    def get_zone_from_trajectory_point(self, point):
        """Return the first Zone containing the selected Trajectory Position point.

        Zone membership is based ONLY on the selected Trajectory Position.
        The bounding-box area, overlap ratio, confidence score, and weighting
        are not calculated.
        """
        if point is None:
            return None
        px, py = point
        for zname in ZONE_NAMES:
            polygon = self.zones.get(zname, [])
            if len(polygon) >= 3 and self.point_in_zone(px, py, polygon):
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

        # Main content uses exactly two visible columns.
        # Keeping all sections inside columns 0-1 prevents a section
        # from being placed outside the scrollable content area.

        frame.columnconfigure(1, weight=1)

        return frame

    # ========================================================
    # SETTINGS
    # ========================================================

    def build_settings_section(self):

        frame = ttk.LabelFrame(
            self.content,
            text="Settings",
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

        ttk.Label(
            frame,
            text="Save or load all Run 1 settings, including Zone geometry and Zone display settings."
        ).grid(
            row=0, column=0, sticky="w", padx=(0, 15)
        )

        ttk.Button(
            frame,
            text="Save Settings",
            command=self.save_settings
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            frame,
            text="Load Settings",
            command=self.load_settings
        ).grid(row=0, column=2, padx=5)

    # ========================================================
    # FILE
    # ========================================================

    def build_file_section(self):

        frame = self.section(
            "File & Zone Settings",
            0,
            1
        )

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=0)
        frame.columnconfigure(3, weight=0)

        self.add_entry(frame, 0, "Run Name", self.run_name_var)
        self.add_entry(frame, 1, "Model", self.model_var, self.browse_model)
        self.add_entry(frame, 2, "Video", self.video_var, self.browse_video)
        self.add_entry(frame, 3, "Output", self.output_var, self.browse_output)

        ttk.Separator(frame, orient="horizontal").grid(
            row=4, column=0, columnspan=4, sticky="ew", pady=(10, 8)
        )

        ttk.Label(
            frame, text="PK Studio Zone & Trajectory", font=("Segoe UI", 10, "bold")
        ).grid(row=5, column=0, columnspan=4, sticky="w", pady=(0, 5))

        ttk.Label(frame, text="Zone File").grid(
            row=6, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(frame, textvariable=self.zone_line_config_var).grid(
            row=6, column=1, columnspan=2, sticky="ew", pady=4
        )
        ttk.Button(
            frame, text="Browse", command=self.load_measurement_config
        ).grid(row=6, column=3, padx=(5, 0))

        ttk.Label(
            frame, text="Trajectory Position"
        ).grid(row=7, column=0, sticky="w", padx=(0, 8), pady=4)

        self.trajectory_position_combo = ttk.Combobox(
            frame,
            textvariable=self.trajectory_position_var,
            values=[
                "Top", "Center", "Bottom",
                "Left", "Right",
                "Top Left", "Top Right",
                "Bottom Left", "Bottom Right"
            ],
            state="readonly",
            width=16
        )
        self.trajectory_position_combo.grid(row=7, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Offset %").grid(
            row=7, column=2, sticky="e", padx=(12, 4), pady=4
        )
        self.trajectory_offset_spin = ttk.Spinbox(
            frame, from_=0, to=50, increment=1,
            textvariable=self.trajectory_offset_var, width=7
        )
        self.trajectory_offset_spin.grid(row=7, column=3, sticky="w", pady=4)

        ttk.Label(frame, text="Zone Display").grid(
            row=8, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Checkbutton(
            frame, text="กรอบ Zone", variable=self.show_zone_boundary_var
        ).grid(row=8, column=1, sticky="w", pady=4)
        ttk.Checkbutton(
            frame, text="ชื่อ Zone", variable=self.show_zone_label_var
        ).grid(row=8, column=2, sticky="w", pady=4)

        ttk.Checkbutton(
            frame, text="แสดงคำว่า Zone", variable=self.show_zone_label_prefix_var
        ).grid(row=8, column=3, sticky="w", pady=4)

        ttk.Label(frame, text="ความจาง %").grid(
            row=9, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Spinbox(
            frame, from_=0, to=100, increment=5,
            textvariable=self.zone_overlay_opacity_var, width=7
        ).grid(row=9, column=1, sticky="w", pady=4)
        ttk.Label(
            frame, text="0 = ไม่เห็น | 100 = ชัดสุด", foreground="#666666"
        ).grid(row=9, column=2, columnspan=2, sticky="w", pady=4)

        ttk.Label(
            frame,
            text="Zone ใช้ Trajectory Position เป็นจุดตัดสิน | ไม่มีพื้นหลังใต้ชื่อ Zone",
            foreground="#666666"
        ).grid(row=10, column=1, columnspan=3, sticky="w", pady=(0, 2))

        ttk.Label(
            frame, textvariable=self.measurement_status_var,
            foreground="#666666", anchor="w"
        ).grid(row=11, column=0, columnspan=4, sticky="w", pady=(4, 0))

        self.update_trajectory_position_controls()

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
            "Display & Output",
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
            text="Show Trajectory",
            variable=self.draw_trail_var
        ).grid(row=1, column=0, sticky="w", pady=3)

        ttk.Label(frame, text="Trail Length").grid(
            row=1, column=1, sticky="e", padx=(15, 5)
        )
        ttk.Spinbox(
            frame, from_=1, to=300, textvariable=self.trail_length_var, width=8
        ).grid(row=1, column=2, sticky="w")

        ttk.Checkbutton(
            frame,
            text="Save Video",
            variable=self.save_video_var
        ).grid(row=2, column=0, sticky="w", pady=3)

        ttk.Checkbutton(
            frame,
            text="Save CSV",
            variable=self.save_csv_var
        ).grid(row=2, column=1, sticky="w", pady=3)

        ttk.Separator(frame, orient="horizontal").grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=(8, 6)
        )
        ttk.Label(
            frame,
            text="Trajectory ใช้จุดเดียวกับ Trajectory Position ด้านบน",
            foreground="#666666"
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(0, 2))
        ttk.Label(
            frame,
            text="กรอบและข้อมูล ID แสดงเฉพาะเมื่อจุด Trajectory อยู่ใน Zone",
            foreground="#666666"
        ).grid(row=5, column=0, columnspan=3, sticky="w")

    # ========================================================
    # INFORMATION
    # ========================================================


    # ========================================================

    def build_information_section(self):

        frame = self.section(
            "Run 1 Flow",
            1,
            3
        )

        text = (
            "Video → Detection → ByteTrack → Trajectory Position → Zone → CSV\n\n"
            "Zone decision: ใช้ตำแหน่งที่เลือกบน Bounding Box เพียงจุดเดียว\n"
            "Positions: Top / Center / Bottom / Left / Right / 4 Corners\n"
            "Offset: เลื่อนตำแหน่งเข้าด้านในจากขอบกรอบได้ 0–50%\n"
            "Display: แสดงกรอบเฉพาะวัตถุที่ตำแหน่งนี้อยู่ใน Zone"
        )

        ttk.Label(
            frame, text=text, justify="left", foreground="#444444"
        ).grid(row=0, column=0, sticky="w")

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
            "save_csv": self.save_csv_var.get(),
            "csv_flush": self.csv_flush_var.get(),
            "research_mode": self.research_mode_var.get(),
            "trajectory_position": self.trajectory_position_var.get(),
            "trajectory_offset": self.trajectory_offset_var.get(),
            "show_zone_boundary": self.show_zone_boundary_var.get(),
            "show_zone_label": self.show_zone_label_var.get(),
            "show_zone_label_prefix": self.show_zone_label_prefix_var.get(),
            "zone_overlay_opacity": self.zone_overlay_opacity_var.get(),
            "run3": {
                "site_id": self.run3_site_id_var.get(),
                "speed_enabled": self.run3_speed_enabled_var.get(),
                "gap_enabled": self.run3_gap_enabled_var.get(),
                "lc_enabled": self.run3_lc_enabled_var.get(),
                "pet_enabled": self.run3_pet_enabled_var.get(),
                "ppm": self.run3_ppm_var.get(),
                "waiting_speed_threshold": self.run3_waiting_speed_threshold_var.get(),
                "lateral_axis_angle_deg": self.run3_lateral_axis_angle_var.get(),
                "lc_longitudinal_window_m": self.run3_lc_longitudinal_window_var.get(),
                "pet_interaction_distance_m": self.run3_pet_interaction_distance_var.get(),
                "pet_threshold_s": self.run3_pet_threshold_var.get(),
                "gap_movement_13": self.run3_gap_movement_13_var.get(),
                "gap_movement_15": self.run3_gap_movement_15_var.get(),
                "gap_movement_41": self.run3_gap_movement_41_var.get(),
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
            ("save_csv", self.save_csv_var),
            ("csv_flush", self.csv_flush_var),
            ("research_mode", self.research_mode_var),
            ("trajectory_position", self.trajectory_position_var),
            ("trajectory_offset", self.trajectory_offset_var),
            ("show_zone_boundary", self.show_zone_boundary_var),
            ("show_zone_label", self.show_zone_label_var),
            ("show_zone_label_prefix", self.show_zone_label_prefix_var),
            ("zone_overlay_opacity", self.zone_overlay_opacity_var),
        ]

        for key, variable in pairs:
            if key in settings:
                variable.set(settings[key])

        run3 = settings.get("run3", {})
        if isinstance(run3, dict):
            mapping_pairs = [
                ("site_id", self.run3_site_id_var),
                ("speed_enabled", self.run3_speed_enabled_var),
                ("gap_enabled", self.run3_gap_enabled_var),
                ("lc_enabled", self.run3_lc_enabled_var),
                ("pet_enabled", self.run3_pet_enabled_var),
                ("ppm", self.run3_ppm_var),
                ("waiting_speed_threshold", self.run3_waiting_speed_threshold_var),
                ("lateral_axis_angle_deg", self.run3_lateral_axis_angle_var),
                ("lc_longitudinal_window_m", self.run3_lc_longitudinal_window_var),
                ("pet_interaction_distance_m", self.run3_pet_interaction_distance_var),
                ("pet_threshold_s", self.run3_pet_threshold_var),
                ("gap_movement_13", self.run3_gap_movement_13_var),
                ("gap_movement_15", self.run3_gap_movement_15_var),
                ("gap_movement_41", self.run3_gap_movement_41_var),
                ("use_raff", self.run3_use_raff_var),
                ("use_mle", self.run3_use_mle_var),
            ]
            for key, variable in mapping_pairs:
                if key in run3:
                    variable.set(run3[key])
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

    def validate_run3_settings(self):
        enabled = any([
            self.run3_speed_enabled_var.get(),
            self.run3_gap_enabled_var.get(),
            self.run3_lc_enabled_var.get(),
            self.run3_pet_enabled_var.get(),
        ])
        if not enabled:
            return True

        if not self.run3_site_id_var.get().strip():
            raise ValueError("Run 3 Site_ID is required when Run 3 is enabled.")

        if self.run3_speed_enabled_var.get() or self.run3_lc_enabled_var.get():
            self._run3_float(self.run3_ppm_var.get(), "PPM")

        if self.run3_gap_enabled_var.get():
            if not any([
                self.run3_gap_movement_13_var.get(),
                self.run3_gap_movement_15_var.get(),
                self.run3_gap_movement_41_var.get(),
            ]):
                raise ValueError("Select at least one Gap Acceptance subject movement.")
            self._run3_float(self.run3_waiting_speed_threshold_var.get(), "waiting detection speed threshold (km/h)")
            if not (self.run3_use_raff_var.get() or self.run3_use_mle_var.get()):
                raise ValueError("Select at least one Critical Gap method.")
            mapping_text = self.run3_reference_text.get("1.0", "end-1c").strip() if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text.strip()
            if not mapping_text:
                raise ValueError("Reference Line Mapping is required for Gap Acceptance.")
            self.run3_reference_mapping_text = mapping_text

        if self.run3_lc_enabled_var.get():
            self._run3_float(self.run3_lateral_axis_angle_var.get(), "road direction angle (deg)", positive=False)
            self._run3_float(self.run3_lc_longitudinal_window_var.get(), "LC longitudinal window (m)")
            for name in RUN3_VEHICLE_CLASSES:
                self._run3_float(self.run3_width_vars[name].get(), f"vehicle width for {name}")

        if self.run3_pet_enabled_var.get():
            self._run3_float(self.run3_pet_interaction_distance_var.get(), "PET interaction distance (m)")
            self._run3_float(self.run3_pet_threshold_var.get(), "PET threshold (s)")

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
            self.validate_run3_settings()
        except Exception as exc:
            messagebox.showerror("Run 3 / Measurement Configuration", str(exc))
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
            f"Starting Run 1 + 2 + 3 | Device = {selected_device}"
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
                run_name + "_Research_Tracking_Result.mp4"
            )

            output_csv = os.path.join(
                output_dir,
                run_name + "_Detection_Records.csv"
            )

            output_id_zone_summary = os.path.join(
                output_dir,
                run_name + "_ID_Zone_Summary.csv"
            )

            output_zone_summary = os.path.join(
                output_dir,
                run_name + "_Zone_Summary.csv"
            )

            # Non-CSV metadata files are still allowed.
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

            output_measurement_summary = os.path.join(
                output_dir,
                run_name + "_Research_Measurement_Summary.json"
            )

            # Remove obsolete CSV files created by older versions of PK Studio
            # for this same Run name. Do not touch unrelated files.
            legacy_csv_names = [
                run_name + "_Research_Track_Statistics.csv",
                run_name + "_Research_ID_Switch_Warnings.csv",
                run_name + "_Research_Detection_Loss.csv",
                run_name + "_Research_Processing_Log.csv",
                run_name + "_Research_Zone_Line_Events.csv",
                run_name + "_Research_Line_Summary.csv",
            ]
            for legacy_name in legacy_csv_names:
                legacy_path = os.path.join(output_dir, legacy_name)
                try:
                    if os.path.isfile(legacy_path):
                        os.remove(legacy_path)
                except OSError:
                    pass

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
            id_zone_history = defaultdict(list)
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

                # Draw Zone overlay BEFORE detections/tracks so bounding boxes and
                # trajectory lines are rendered on top of the translucent Zone.
                if measurement_enabled:
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

                                    if candidate:
                                        zone_assignment_summary[candidate]["observations"] += 1
                                    if confirmed_zone:
                                        zone_assignment_summary[confirmed_zone]["confirmed_frames"] += 1

                                    timestamp_now = frame_index / fps
                                    previous_zone_point = zstate.get("previous_confirmed_point")
                                    previous_confirmed_zone = zstate.get("previous_confirmed_zone")

                                    # Keep a compact per-ID route history: Zone A -> Zone B -> ...
                                    if confirmed_zone and confirmed_zone != previous_confirmed_zone:
                                        id_zone_history[track_id].append({
                                            "zone": confirmed_zone,
                                            "timestamp": timestamp_now,
                                        })

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

                            zones_available = any(
                                len(self.zones.get(z, [])) >= 3 for z in ZONE_NAMES
                            )
                            show_object = (
                                not zones_available
                                or confirmed_label is not None
                            )

                            if show_object:
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
                                    # Single compact object label.
                                    # Show ID + class + detection confidence + Zone once only.
                                    # No separate yellow Zone-duration label is drawn.
                                    label = (
                                        f"ID {track_id} | {class_name} | "
                                        f"Conf {confidence:.2f} | {confirmed_label}"
                                    )
                                    label_y = max(y1 - 10, 20)
                                    cv2.putText(
                                        frame, label, (x1, label_y),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                                        (0, 255, 0), 2, cv2.LINE_AA
                                    )

                            if csv_writer is not None:

                                timestamp = (
                                    frame_index / fps
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

            # Finalize a compact per-ID route summary before closing any files.
            if measurement_enabled:
                for track_id, history in sorted(id_zone_history.items()):
                    if not history:
                        continue
                    state_info = track_stats.get(track_id, {})
                    class_name_final = state_info.get("class_name", "")
                    zones_sequence = [item["zone"] for item in history]
                    timestamps = [float(item["timestamp"]) for item in history]
                    total_zone_time = 0.0
                    zmap = zone_track_state.get(track_id, {}).get("zone_states", {})
                    for zs in zmap.values():
                        if zs.get("entry_time") is not None:
                            if zs.get("inside"):
                                end_t = state_info.get("last_frame", frame_index) / fps
                            else:
                                end_t = zs.get("last_exit_time")
                            if end_t is not None:
                                total_zone_time += max(0.0, float(end_t) - float(zs["entry_time"]))
                    track_state_final = track_stats.get(track_id, {})
                    first_seen_final = float(track_state_final.get("first_frame", 0)) / fps if fps > 0 else 0.0
                    last_seen_final = float(track_state_final.get("last_frame", frame_index)) / fps if fps > 0 else 0.0
                    unique_zones = []
                    for z in zones_sequence:
                        if z not in unique_zones:
                            unique_zones.append(z)
                    transitions = sum(1 for i in range(1, len(zones_sequence)) if zones_sequence[i] != zones_sequence[i-1])
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
                    last_time_final = last_frame_final / fps if fps > 0 else 0.0
                    for zname, zs in zmap.get("zone_states", {}).items():
                        if zs.get("entry_time") is None:
                            continue
                        start_t = float(zs["entry_time"])
                        end_t = (last_time_final if zs.get("inside") else zs.get("last_exit_time"))
                        if end_t is None:
                            continue
                        duration = max(0.0, float(end_t) - start_t)
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
                "total_frames": total_frames,
                "processed_frames": processed_frames,
                "frames_with_detection": total_frames_with_detection,
                "total_detections": total_detections,
                "unique_track_ids": len(track_stats),
                "max_active_tracks": max_active_tracks,
                "id_switch_warnings": id_switch_warning_count,
                "detection_loss_events": detection_loss_count,
                "zone_assignment": {
                    "method": "Trajectory Position",
                    "trajectory_position": self.trajectory_position_var.get(),
                    "trajectory_offset_percent": float(self.trajectory_offset_var.get()),
                    "temporal_confirmation_frames": 0,
                             "zone_assignment_rule": "Trajectory Position point-in-polygon only",
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
            self.run3_was_requested = any([
                self.run3_speed_enabled_var.get(),
                self.run3_gap_enabled_var.get(),
                self.run3_lc_enabled_var.get(),
                self.run3_pet_enabled_var.get(),
            ])
            if (not stopped) and self.run3_was_requested:
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
                    pass

            self.root.after(
                0,
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
            self.root.after(
                0,
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

    @staticmethod
    def _run3_parse_zone_sequence(text):
        nums = []
        for match in re.finditer(r"Zone\s*(\d+)", str(text or ""), flags=re.I):
            n = int(match.group(1))
            if not nums or nums[-1] != n:
                nums.append(n)
        return nums

    @staticmethod
    def _run3_movement_from_sequence(sequence):
        seq = Run1App._run3_parse_zone_sequence(sequence)
        supported = {
            (1, 3): "1→3",
            (1, 5): "1→5",
            (4, 1): "4→1",
            (2, 3): "2→3",
            (4, 5): "4→5",
        }
        for a, b in zip(seq, seq[1:]):
            if (a, b) in supported:
                return supported[(a, b)]
        return ""

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
            u = abs(s0) / (abs(s0) + abs(s1))
            return prev_t + u * (curr_t - prev_t)
        return None

    def _run3_load_inputs(self, output_dir, run_name):
        det = os.path.join(output_dir, run_name + "_Detection_Records.csv")
        ids = os.path.join(output_dir, run_name + "_ID_Zone_Summary.csv")
        zone = os.path.join(output_dir, run_name + "_Zone_Summary.csv")
        return (
            self._run3_read_csv(det),
            self._run3_read_csv(ids),
            self._run3_read_csv(zone),
            det, ids, zone,
        )

    def _run3_build_tracks(self, detection_rows, id_rows):
        tracks = defaultdict(list)
        for row in detection_rows:
            tid = str(row.get("track_id", "")).strip()
            if not tid or tid == "-1":
                continue
            ts = self._run3_float_safe(row.get("timestamp"))
            if ts is None:
                continue
            row2 = dict(row)
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

    def _run3_speed(self, tracks, ppm):
        results = []
        for tid, rows in tracks.items():
            if not rows:
                continue
            cls = rows[0].get("class_name", "")
            if str(cls).lower() == "person":
                continue

            metrics = {}
            for zone, label in [(2, "Y1"), (4, "Y1"), (3, "Y2"), (5, "Y2")]:
                zr = [r for r in rows if r.get("_zone_num") == zone and r.get("_point") is not None]
                if len(zr) < 2:
                    continue
                d_px = self._run3_segment_distance_sum([r["_point"] for r in zr])
                dt = zr[-1]["_timestamp"] - zr[0]["_timestamp"]
                if dt <= 0 or d_px <= 0:
                    continue
                speed_kmh = (d_px / ppm) / dt * 3.6
                if label not in metrics:
                    metrics[label] = {
                        "zone": f"Zone {zone}",
                        "start": zr[0]["_timestamp"],
                        "end": zr[-1]["_timestamp"],
                        "distance": d_px / ppm,
                        "speed": speed_kmh,
                    }

            y1 = metrics.get("Y1")
            y2 = metrics.get("Y2")
            if not y1 and not y2:
                continue
            delta = (y2["speed"] - y1["speed"]) if y1 and y2 else None
            results.append({
                "Site_ID": self.run3_site_id_var.get().strip(),
                "Vehicle_ID": tid,
                "Vehicle_Class": cls,
                "Approach_Zone": y1["zone"] if y1 else "",
                "Exit_Zone": y2["zone"] if y2 else "",
                "Approach_Start_Time": "" if not y1 else f"{y1['start']:.6f}",
                "Approach_End_Time": "" if not y1 else f"{y1['end']:.6f}",
                "Approach_Distance_m": "" if not y1 else f"{y1['distance']:.6f}",
                "Y1_Approach_Speed": "" if not y1 else f"{y1['speed']:.6f}",
                "Exit_Start_Time": "" if not y2 else f"{y2['start']:.6f}",
                "Exit_End_Time": "" if not y2 else f"{y2['end']:.6f}",
                "Exit_Distance_m": "" if not y2 else f"{y2['distance']:.6f}",
                "Y2_Exit_Speed": "" if not y2 else f"{y2['speed']:.6f}",
                "Delta_Speed": "" if delta is None else f"{delta:.6f}",
                "QC_Flag": "Incomplete_Y1_or_Y2" if (not y1 or not y2) else "",
            })
        return results

    def copy_run3_mapping_template(self):
        text = self.run3_reference_text.get("1.0", "end-1c") if hasattr(self, "run3_reference_text") else self.run3_reference_mapping_text
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            self.status_var.set("Reference Line Mapping template copied to clipboard")
        except Exception as e:
            self.status_var.set(f"Copy failed: {e}")

    def _run3_parse_reference_mapping(self):
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

    def _run3_gap(self, tracks, summaries, mapping):
        selected = []
        if self.run3_gap_movement_13_var.get(): selected.append("1→3")
        if self.run3_gap_movement_15_var.get(): selected.append("1→5")
        if self.run3_gap_movement_41_var.get(): selected.append("4→1")
        wait_threshold = float(self.run3_waiting_speed_threshold_var.get())

        movement_by_id = {}
        for tid, rows in tracks.items():
            if tid in summaries:
                movement_by_id[tid] = self._run3_movement_from_sequence(summaries[tid].get("zone_sequence", ""))
            else:
                movement_by_id[tid] = ""

        line_times = defaultdict(list)
        for tid, rows in tracks.items():
            movement = movement_by_id.get(tid, "")
            if movement not in RUN3_ALL_MOVEMENTS:
                continue
            lname = mapping.get((self.run3_site_id_var.get().strip(), movement))
            if not lname:
                continue
            line = self.lines.get(lname, [])
            prev = None
            prev_t = None
            for r in rows:
                p = r.get("_point")
                t = r.get("_timestamp")
                if p is None:
                    continue
                if prev is not None:
                    cross_t = self._run3_line_crossing_time(prev, prev_t, p, t, line)
                    if cross_t is not None:
                        line_times[movement].append((cross_t, tid, r.get("class_name", ""), lname))
                prev, prev_t = p, t
        for key in list(line_times):
            line_times[key].sort(key=lambda x: x[0])

        rows_out = []
        for tid, rows in tracks.items():
            movement = movement_by_id.get(tid, "")
            if movement not in selected:
                continue
            wait_zone = 1 if movement in ("1→3", "1→5") else 4
            wr = []
            for idx, r in enumerate(rows):
                if r.get("_zone_num") != wait_zone or r.get("_point") is None:
                    continue
                if idx == 0:
                    continue
                prev = rows[idx-1]
                if prev.get("_point") is None:
                    continue
                dt = r["_timestamp"] - prev["_timestamp"]
                if dt <= 0:
                    continue
                step_kmh = (math.hypot(r["_point"][0]-prev["_point"][0], r["_point"][1]-prev["_point"][1])) / max(1e-9, 1.0) / dt
                # step_kmh above is pixel/s only; convert to km/h via PPM below.
                ppm = float(self.run3_ppm_var.get())
                step_kmh = (math.hypot(r["_point"][0]-prev["_point"][0], r["_point"][1]-prev["_point"][1]) / ppm) / dt * 3.6
                if step_kmh <= wait_threshold:
                    wr.append(r)
            if not wr:
                continue
            wait_start = wr[0]["_timestamp"]
            accepted_time = None
            for idx in range(1, len(rows)):
                prev = rows[idx-1]; cur = rows[idx]
                if prev.get("_zone_num") == wait_zone and cur.get("_point") is not None and prev.get("_point") is not None:
                    dt = cur["_timestamp"] - prev["_timestamp"]
                    if dt <= 0:
                        continue
                    speed = (math.hypot(cur["_point"][0]-prev["_point"][0], cur["_point"][1]-prev["_point"][1]) / float(self.run3_ppm_var.get())) / dt * 3.6
                    if speed > wait_threshold:
                        accepted_time = cur["_timestamp"]
                        break
            if accepted_time is None:
                continue

            candidates = []
            # Conflict mapping fixed by the study design for the three subject movements.
            conflict_movements = {
                "1→3": ["2→3"],
                "1→5": ["2→3", "4→5"],
                "4→1": ["2→3", "1→5"],
            }.get(movement, [])
            # The mapping may only contain the subject movements; conflict streams are derived from all IDs.
            for cm in conflict_movements:
                events = line_times.get(cm, [])
                for a, b in zip(events, events[1:]):
                    if b[0] <= a[0]:
                        continue
                    candidates.append({
                        "conflict_movement": cm,
                        "conflicting_id_a": a[1],
                        "conflicting_class_a": a[2],
                        "conflicting_id_b": b[1],
                        "conflicting_class_b": b[2],
                        "reference_line": a[3],
                        "gap_start": a[0],
                        "gap_end": b[0],
                        "gap": b[0]-a[0],
                    })
            active = [c for c in candidates if c["gap_start"] <= accepted_time <= c["gap_end"]]
            controlling = min(active, key=lambda c: c["gap"]) if active else None
            prior = [c for c in candidates if wait_start <= c["gap_end"] < accepted_time]
            # Deduplicate identical intervals across repeated candidate generation.
            seen = set()
            prior2 = []
            for c in sorted(prior, key=lambda x: x["gap_end"]):
                key = (c["conflict_movement"], round(c["gap_start"], 6), round(c["gap_end"], 6))
                if key not in seen:
                    seen.add(key); prior2.append(c)
            decision_id = f"{tid}_{accepted_time:.6f}"
            waiting_time = accepted_time - wait_start
            if prior2:
                for c in prior2:
                    rows_out.append({
                        "Site_ID": self.run3_site_id_var.get().strip(),
                        "Decision_Event_ID": decision_id,
                        "Subject_ID": tid,
                        "Subject_Class": rows[0].get("class_name", ""),
                        "Subject_Movement": movement,
                        "Conflicting_Movement": c["conflict_movement"],
                        "Conflicting_ID_A": c["conflicting_id_a"],
                        "Conflicting_ID_B": c["conflicting_id_b"],
                        "Reference_Line": c["reference_line"],
                        "Gap_Start_Time": f"{c['gap_start']:.6f}",
                        "Gap_End_Time": f"{c['gap_end']:.6f}",
                        "X31_Available_Gap": f"{c['gap']:.6f}",
                        "X32_Waiting_Time": f"{waiting_time:.6f}",
                        "Gap_Role": "Rejected",
                        "Y5_Gap_Acceptance": 0,
                        "Acceptance_Time": "",
                        "QC_Flag": "",
                    })
            if controlling:
                rows_out.append({
                    "Site_ID": self.run3_site_id_var.get().strip(),
                    "Decision_Event_ID": decision_id,
                    "Subject_ID": tid,
                    "Subject_Class": rows[0].get("class_name", ""),
                    "Subject_Movement": movement,
                    "Conflicting_Movement": controlling["conflict_movement"],
                    "Conflicting_ID_A": controlling["conflicting_id_a"],
                    "Conflicting_ID_B": controlling["conflicting_id_b"],
                    "Reference_Line": controlling["reference_line"],
                    "Gap_Start_Time": f"{controlling['gap_start']:.6f}",
                    "Gap_End_Time": f"{controlling['gap_end']:.6f}",
                    "X31_Available_Gap": f"{controlling['gap']:.6f}",
                    "X32_Waiting_Time": f"{waiting_time:.6f}",
                    "Gap_Role": "Accepted / Controlling",
                    "Y5_Gap_Acceptance": 1,
                    "Acceptance_Time": f"{accepted_time:.6f}",
                    "QC_Flag": "",
                })
        return rows_out

    @staticmethod
    def _run3_raff(accepted, rejected):
        if not accepted or not rejected:
            return None
        candidates = sorted(set([float(v) for v in accepted + rejected if v is not None and v > 0]))
        if not candidates:
            return None
        best = None
        for g in candidates:
            fa = np.mean([v >= g for v in accepted])
            fr = np.mean([v <= g for v in rejected])
            diff = abs(fa - fr)
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
        logs_l = np.log(lowers)
        logs_u = np.log(uppers)
        mu0 = float(np.median((logs_l + logs_u) / 2.0))
        sigma0 = float(max(0.25, np.std((logs_l + logs_u) / 2.0)))
        def nll(x):
            mu, log_sigma = x
            sigma = math.exp(log_sigma)
            z_u = (logs_u - mu) / sigma
            z_l = (logs_l - mu) / sigma
            probs = ndtr(z_u) - ndtr(z_l)
            probs = np.clip(probs, 1e-15, None)
            return float(-np.sum(np.log(probs)))
        res = minimize(nll, x0=np.array([mu0, math.log(sigma0)]), method="Nelder-Mead")
        if not res.success:
            return None
        mu, log_sigma = res.x
        return {
            "mu": float(mu),
            "sigma": float(math.exp(log_sigma)),
            "critical_gap_median": float(math.exp(mu)),
            "negative_log_likelihood": float(res.fun),
        }

    def _run3_lateral_clearance(self, tracks, ppm, axis_deg, long_window_m):
        theta = math.radians(axis_deg)
        road_u = (math.cos(theta), math.sin(theta))
        lat_u = (-math.sin(theta), math.cos(theta))
        widths = {name: float(self.run3_width_vars[name].get()) for name in RUN3_VEHICLE_CLASSES}
        out = []
        for tid_a, rows_a in tracks.items():
            if not rows_a or rows_a[0].get("class_name", "") != "Motorcycle":
                continue
            by_time = {round(r["_timestamp"], 6): r for r in rows_a if r.get("_center") is not None and r.get("_zone_num") in (2,4)}
            for tid_b, rows_b in tracks.items():
                if tid_b == tid_a or not rows_b:
                    continue
                cls_b = rows_b[0].get("class_name", "")
                if cls_b not in widths:
                    continue
                for r_b in rows_b:
                    if r_b.get("_center") is None or r_b.get("_zone_num") not in (2,4):
                        continue
                    key = round(r_b["_timestamp"], 6)
                    r_a = by_time.get(key)
                    if not r_a:
                        continue
                    if r_a.get("_zone_num") != r_b.get("_zone_num"):
                        continue
                    dx = r_b["_center"][0] - r_a["_center"][0]
                    dy = r_b["_center"][1] - r_a["_center"][1]
                    lateral_px = abs(dx * lat_u[0] + dy * lat_u[1])
                    longitudinal_px = abs(dx * road_u[0] + dy * road_u[1])
                    longitudinal_m = longitudinal_px / ppm
                    if longitudinal_m > long_window_m:
                        continue
                    ls_m = lateral_px / ppm
                    y3 = ls_m - (widths["Motorcycle"] + widths[cls_b]) / 2.0
                    side = "Left" if (dx * lat_u[0] + dy * lat_u[1]) > 0 else "Right"
                    out.append({
                        "Site_ID": self.run3_site_id_var.get().strip(),
                        "Pair_ID": f"{tid_a}_{tid_b}",
                        "Timestamp": f"{r_a['_timestamp']:.6f}",
                        "Zone": f"Zone {r_a['_zone_num']}",
                        "Motorcycle_ID": tid_a,
                        "Motorcycle_Class": "Motorcycle",
                        "Neighbor_ID": tid_b,
                        "Neighbor_Class": cls_b,
                        "Neighbor_Side": side,
                        "LS_Pixel": f"{lateral_px:.6f}",
                        "PPM": f"{ppm:.6f}",
                        "LS_Meter": f"{ls_m:.6f}",
                        "Wm": f"{widths['Motorcycle']:.6f}",
                        "Wv": f"{widths[cls_b]:.6f}",
                        "Y3_Lateral_Clearance": f"{y3:.6f}",
                        "QC_Flag": "Negative_Y3" if y3 < 0 else "",
                    })
        return out

    @staticmethod
    def _run3_segment_intersection(a0, a1, b0, b1):
        x1,y1=a0; x2,y2=a1; x3,y3=b0; x4,y4=b1
        den=(x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
        if abs(den) < 1e-9:
            return None
        t=((x1-x3)*(y3-y4)-(y1-y3)*(x3-x4))/den
        u=-((x1-x2)*(y1-y3)-(y1-y2)*(x1-x3))/den
        if 0 <= t <= 1 and 0 <= u <= 1:
            return t, u, (x1+t*(x2-x1), y1+t*(y2-y1))
        return None

    @staticmethod
    def _run3_conflict_type(movement_a, movement_b, trajectory_intersects=False):
        if trajectory_intersects:
            return "Crossing"
        seq_a = tuple(int(x) for x in re.findall(r"\d+", str(movement_a)))
        seq_b = tuple(int(x) for x in re.findall(r"\d+", str(movement_b)))
        if len(seq_a) == 2 and len(seq_b) == 2:
            if seq_a[1] == seq_b[1]:
                return "Merging"
            if seq_a[0] == seq_b[0]:
                return "Diverging"
        return "Merging/Diverging"

    def _run3_pet(self, tracks, summaries, ppm, axis_deg, interaction_distance_m):
        candidates = []
        ids = list(tracks)
        movement_by_id = {tid: self._run3_movement_from_sequence(summaries.get(tid, {}).get("zone_sequence", "")) if tid in summaries else "" for tid in ids}
        for i, a_id in enumerate(ids):
            for b_id in ids[i+1:]:
                a_rows = [r for r in tracks[a_id] if r.get("_zone_num") == 6 and r.get("_point") is not None]
                b_rows = [r for r in tracks[b_id] if r.get("_zone_num") == 6 and r.get("_point") is not None]
                if len(a_rows) < 2 or len(b_rows) < 2:
                    continue
                ma = movement_by_id.get(a_id, ""); mb = movement_by_id.get(b_id, "")
                if not ma and not mb:
                    continue
                # Exclude simple same-direction movement pairs.
                if ma and mb and ma == mb:
                    continue
                best = None
                for ra0, ra1 in zip(a_rows, a_rows[1:]):
                    for rb0, rb1 in zip(b_rows, b_rows[1:]):
                        hit = self._run3_segment_intersection(ra0["_point"], ra1["_point"], rb0["_point"], rb1["_point"])
                        if hit:
                            ta_frac, tb_frac, ip = hit
                            ta = ra0["_timestamp"] + ta_frac*(ra1["_timestamp"]-ra0["_timestamp"])
                            tb = rb0["_timestamp"] + tb_frac*(rb1["_timestamp"]-rb0["_timestamp"])
                            best = (ta, tb, ip, self._run3_conflict_type(ma, mb, trajectory_intersects=True))
                            break
                    if best:
                        break
                if best is None:
                    # Merging/Diverging: closest sampled trajectory points inside Zone 6.
                    min_pair = None
                    for ra in a_rows:
                        for rb in b_rows:
                            dpx = math.hypot(ra["_point"][0]-rb["_point"][0], ra["_point"][1]-rb["_point"][1])
                            dm = dpx / ppm
                            if dm <= interaction_distance_m and (min_pair is None or dm < min_pair[0]):
                                min_pair = (dm, ra, rb)
                    if min_pair:
                        _, ra, rb = min_pair
                        best = (ra["_timestamp"], rb["_timestamp"], ((ra["_point"][0]+rb["_point"][0])/2, (ra["_point"][1]+rb["_point"][1])/2), self._run3_conflict_type(ma, mb, trajectory_intersects=False))
                if best is None:
                    continue
                ta, tb, ip, ctype = best
                if ta <= tb:
                    first_id, second_id = a_id, b_id
                    t_first, t_second = ta, tb
                else:
                    first_id, second_id = b_id, a_id
                    t_first, t_second = tb, ta
                pet = t_second - t_first
                if pet <= 0:
                    continue
                candidates.append({
                    "Site_ID": self.run3_site_id_var.get().strip(),
                    "Interaction_ID": f"{a_id}_{b_id}_{min(ta,tb):.6f}",
                    "Vehicle_ID_A": a_id,
                    "Vehicle_Class_A": tracks[a_id][0].get("class_name", ""),
                    "Movement_A": ma,
                    "Vehicle_ID_B": b_id,
                    "Vehicle_Class_B": tracks[b_id][0].get("class_name", ""),
                    "Movement_B": mb,
                    "Conflict_Type": ctype,
                    "Conflict_Zone": "Zone 6",
                    "Interaction_Start": f"{min(ta,tb):.6f}",
                    "Interaction_End": f"{max(ta,tb):.6f}",
                    "T1_Exit_Time": f"{t_first:.6f}",
                    "T2_Entry_Time": f"{t_second:.6f}",
                    "Y4_PET": f"{pet:.6f}",
                    "QC_Flag": "Threshold_At_or_Below" if pet <= float(self.run3_pet_threshold_var.get()) else "",
                })
        return candidates

    def run3_processing(self, settings, output_dir, run_name):
        self.root.after(0, lambda: self.status_var.set("Run 3 — loading Run 2 results..."))
        detection_rows, id_rows, zone_rows, det_path, id_path, zone_path = self._run3_load_inputs(output_dir, run_name)
        tracks, summaries = self._run3_build_tracks(detection_rows, id_rows)
        outputs = {}
        summary = {"site_id": self.run3_site_id_var.get().strip(), "inputs": {"detection": det_path, "id_zone_summary": id_path, "zone_summary": zone_path}}

        # Speed
        if self.run3_speed_enabled_var.get():
            ppm = float(self.run3_ppm_var.get())
            speed_rows = self._run3_speed(tracks, ppm)
            path = os.path.join(output_dir, "Run_3_Speed.csv")
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                fields = [
                    "Site_ID","Vehicle_ID","Vehicle_Class","Approach_Zone","Exit_Zone",
                    "Approach_Start_Time","Approach_End_Time","Approach_Distance_m","Y1_Approach_Speed",
                    "Exit_Start_Time","Exit_End_Time","Exit_Distance_m","Y2_Exit_Speed","Delta_Speed","QC_Flag"
                ]
                w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(speed_rows)
            vals_y1 = [float(r["Y1_Approach_Speed"]) for r in speed_rows if r["Y1_Approach_Speed"] not in ("", None)]
            vals_y2 = [float(r["Y2_Exit_Speed"]) for r in speed_rows if r["Y2_Exit_Speed"] not in ("", None)]
            summary["speed"] = {
                "Y1_P85": float(np.percentile(vals_y1,85)) if vals_y1 else None,
                "Y2_P85": float(np.percentile(vals_y2,85)) if vals_y2 else None,
                "Y1_N": len(vals_y1), "Y2_N": len(vals_y2)
            }
            outputs["speed"] = path

        # Gap Acceptance
        if self.run3_gap_enabled_var.get():
            mapping = self._run3_parse_reference_mapping()
            gap_rows = self._run3_gap(tracks, summaries, mapping)
            path = os.path.join(output_dir, "Run_3_Gap_Acceptance.csv")
            fields = ["Site_ID","Decision_Event_ID","Subject_ID","Subject_Class","Subject_Movement","Conflicting_Movement","Conflicting_ID_A","Conflicting_ID_B","Reference_Line","Gap_Start_Time","Gap_End_Time","X31_Available_Gap","X32_Waiting_Time","Gap_Role","Y5_Gap_Acceptance","Acceptance_Time","QC_Flag"]
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(gap_rows)
            rejected_by_driver = defaultdict(list); accepted_by_driver = defaultdict(list)
            for r in gap_rows:
                key = (r["Subject_Class"], r["Subject_Movement"], r["Subject_ID"])
                gap = float(r["X31_Available_Gap"])
                if r["Y5_Gap_Acceptance"] == 0: rejected_by_driver[key].append(gap)
                else: accepted_by_driver[key].append(gap)
            critical = []
            groups = defaultdict(lambda: {"accepted": [], "rejected": [], "intervals": []})
            for key in set(rejected_by_driver)|set(accepted_by_driver):
                acc = accepted_by_driver.get(key, []); rej = rejected_by_driver.get(key, [])
                if acc and rej:
                    groups[(key[0], key[1])]["accepted"].append(acc[-1])
                    groups[(key[0], key[1])]["rejected"].append(max(rej))
                    groups[(key[0], key[1])]["intervals"].append((max(rej), acc[-1]))
            for (cls, movement), g in groups.items():
                cr = self._run3_raff(g["accepted"], g["rejected"]) if self.run3_use_raff_var.get() else None
                mle = self._run3_mle_driver_intervals(g["intervals"]) if self.run3_use_mle_var.get() else None
                critical.append({
                    "Site_ID": self.run3_site_id_var.get().strip(), "Vehicle_Class": cls, "Movement": movement,
                    "Drivers_With_Pairs": len(g["intervals"]),
                    "Raff_Critical_Gap_s": "" if cr is None else f"{cr:.6f}",
                    "MLE_Critical_Gap_Median_s": "" if mle is None else f"{mle['critical_gap_median']:.6f}",
                    "MLE_mu": "" if mle is None else f"{mle['mu']:.6f}",
                    "MLE_sigma": "" if mle is None else f"{mle['sigma']:.6f}",
                })
            summary["gap_acceptance"] = {
                "gap_events": len(gap_rows),
                "decision_events": len(set(r["Decision_Event_ID"] for r in gap_rows)),
                "accepted_events": sum(1 for r in gap_rows if r["Y5_Gap_Acceptance"] == 1),
                "rejected_events": sum(1 for r in gap_rows if r["Y5_Gap_Acceptance"] == 0),
                "critical_gap": critical,
            }
            outputs["gap_acceptance"] = path

        # Lateral Clearance
        if self.run3_lc_enabled_var.get():
            ppm = float(self.run3_ppm_var.get()); axis = float(self.run3_lateral_axis_angle_var.get()); long_window = float(self.run3_lc_longitudinal_window_var.get())
            lc_rows = self._run3_lateral_clearance(tracks, ppm, axis, long_window)
            path = os.path.join(output_dir, "Run_3_Lateral_Clearance.csv")
            fields = ["Site_ID","Pair_ID","Timestamp","Zone","Motorcycle_ID","Motorcycle_Class","Neighbor_ID","Neighbor_Class","Neighbor_Side","LS_Pixel","PPM","LS_Meter","Wm","Wv","Y3_Lateral_Clearance","QC_Flag"]
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(lc_rows)
            vals = [float(r["Y3_Lateral_Clearance"]) for r in lc_rows]
            summary["lateral_clearance"] = {"N": len(vals), "Mean_m": float(np.mean(vals)) if vals else None, "Median_m": float(np.median(vals)) if vals else None, "Minimum_m": float(np.min(vals)) if vals else None, "Maximum_m": float(np.max(vals)) if vals else None}
            outputs["lateral_clearance"] = path

        # PET
        if self.run3_pet_enabled_var.get():
            ppm = float(self.run3_ppm_var.get()); axis = float(self.run3_lateral_axis_angle_var.get()); interaction = float(self.run3_pet_interaction_distance_var.get())
            pet_rows = self._run3_pet(tracks, summaries, ppm, axis, interaction)
            path = os.path.join(output_dir, "Run_3_PET.csv")
            fields = ["Site_ID","Interaction_ID","Vehicle_ID_A","Vehicle_Class_A","Movement_A","Vehicle_ID_B","Vehicle_Class_B","Movement_B","Conflict_Type","Conflict_Zone","Interaction_Start","Interaction_End","T1_Exit_Time","T2_Entry_Time","Y4_PET","QC_Flag"]
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(pet_rows)
            vals = [float(r["Y4_PET"]) for r in pet_rows]
            threshold = float(self.run3_pet_threshold_var.get())
            summary["pet"] = {"Total_Events": len(vals), "Mean_s": float(np.mean(vals)) if vals else None, "Median_s": float(np.median(vals)) if vals else None, "Minimum_s": float(np.min(vals)) if vals else None, "Maximum_s": float(np.max(vals)) if vals else None, "PET_At_Or_Below_Threshold": sum(v <= threshold for v in vals)}
            outputs["pet"] = path

        summary_path = os.path.join(output_dir, "Run_3_Summary.json")
        summary["outputs"] = outputs
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        outputs["summary"] = summary_path
        self.run3_last_outputs = outputs
        self.run3_last_summary = summary
        self.root.after(0, lambda: self.run3_result_text.set(f"Run 3 completed | outputs: {len([p for p in outputs.values() if p])}"))
        return outputs

    def finish_integrated_ui(self, stopped, output_video, output_csv, output_settings, output_summary, output_id_zone_summary=None, output_zone_summary=None):
        self.running = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Ⅱ PAUSE")
        self.stop_button.config(state="disabled")
        if stopped:
            self.status_var.set("Run 1 + 2 + 3 stopped")
            messagebox.showinfo("PK Studio V17", "Processing was stopped by user.")
            return
        if self.run3_was_requested:
            self.status_var.set("Run 1 + 2 + 3 completed")
            message = "Run 1 + 2 + 3 completed\n\n"
        else:
            self.status_var.set("Run 1 + 2 completed")
            message = "Run 1 + 2 completed\n\n"
        self.progress_var.set("100%")
        if self.save_video_var.get():
            message += f"Run 1/2 Video:\n{output_video}\n\n"
        if self.save_csv_var.get():
            message += f"Run 2 Detection Records:\n{output_csv}\n\n"
        message += f"Run 2 ID Zone Summary:\n{output_id_zone_summary}\n\nRun 2 Zone Summary:\n{output_zone_summary}\n\n"
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
