"""Headless test of the Line editor dialog (needs torch/cv2/ultralytics; no real video).

Run from the Run folder:   python tests/gui_line_editor.py
Builds a tiny synthetic video + Zone JSON in a temp folder, opens the real
LineEditorDialog (window hidden), "clicks" the canvas through add_point(),
saves, and checks the Zone JSON, app.lines and the Reference Line Mapping text.
"""
import importlib.util
import json
import os
import sys
import tempfile
import tkinter as tk

import cv2
import numpy as np

os.environ["PK_STUDIO_CUDA_RELAUNCHED"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def make_video(path, w=640, h=360, n=5):
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 30.0, (w, h))
    for i in range(n):
        frame = np.full((h, w, 3), 90 + i * 10, dtype=np.uint8)
        cv2.putText(frame, "test frame", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        writer.write(frame)
    writer.release()


def make_zone_json(path, video, w, h):
    zones = []
    for z in range(1, 8):
        x0 = 20 + (z - 1) * 80
        zones.append({"id": z, "name": f"Zone {z}", "points": [[x0, 100], [x0 + 70, 100], [x0 + 70, 200], [x0, 200]]})
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"video_path": video, "frame_width": w, "frame_height": h, "zones": zones}, f, indent=2)


def main():
    tmp = tempfile.mkdtemp(prefix="pk_lines_")
    video = os.path.join(tmp, "v.mp4")
    zpath = os.path.join(tmp, "zones.json")
    make_video(video)
    make_zone_json(zpath, video, 640, 360)

    root = tk.Tk()
    root.withdraw()
    app = m.Run1App(root)
    m.messagebox.askyesno = lambda *a, **k: True
    m.messagebox.showerror = lambda *a, **k: print("showerror:", a[1:2])
    m.messagebox.showwarning = lambda *a, **k: None
    app.video_var.set(video)
    app.zone_line_config_var.set(zpath)
    check("zone file loads", app.load_pkstudio_zones() is True)
    app.run3_site_id_var.set("8")
    check("template mapping present before editing", "# 8|2-3-4|Line N" in app.run3_reference_text.get("1.0", "end-1c"))

    dlg = app.open_line_editor()
    check("editor opens", dlg is not None)
    check("rows = the four conflicting streams", dlg.movements == ["2-3-4", "5-6-7", "5-6-3-1", "1-3-6-7"], str(dlg.movements))
    check("lines assigned Line 1..4", [dlg.assign[mv] for mv in dlg.movements] == ["Line 1", "Line 2", "Line 3", "Line 4"])
    check("frame shown at scale 1 (640x360)", abs(dlg.scale - 1.0) < 1e-9, str(dlg.scale))

    # click: two points per line; the editor advances to the next undrawn stream by itself
    clicks = {"2-3-4": ((400, 200), (400, 340)), "5-6-7": ((300, 20), (300, 120)),
              "5-6-3-1": ((120, 220), (200, 220)), "1-3-6-7": ((500, 10), (560, 100))}
    check("starts on the first stream", dlg.current == "2-3-4")
    for mv, (p1, p2) in clicks.items():
        check(f"current stream is {mv}", dlg.current == mv, dlg.current)
        dlg.add_point(*p1)
        check(f"first click of {mv} is pending", dlg.pending == p1)
        dlg.add_point(*p2)
    check("all four lines drawn", all(len(dlg.points[mv]) == 2 for mv in dlg.movements))
    dlg.add_point(99999, -50)                       # outside the frame is clamped (starts a new pending point)
    check("clamped to the frame", dlg.pending == (639, 0), str(dlg.pending))
    dlg.clear(dlg.current)
    dlg.points["1-3-6-7"] = [(500, 10), (560, 100)]

    check("save returns True", dlg.save() is True)
    with open(zpath, encoding="utf-8") as f:
        data = json.load(f)
    check("Zone JSON has the 4 lines", data.get("lines", {}).get("Line 1") == [[400, 200], [400, 340]]
          and data["lines"]["Line 4"] == [[500, 10], [560, 100]], str(data.get("lines")))
    check("lines frame size recorded", data.get("lines_frame_width") == 640 and data.get("lines_frame_height") == 360)
    check("zones untouched", len(data["zones"]) == 7)
    check("backup written once", os.path.isfile(zpath + ".bak"))
    check("app.lines updated", app.lines["Line 2"] == [(300, 20), (300, 120)], str(app.lines["Line 2"]))
    text = app.run3_reference_text.get("1.0", "end-1c")
    print(text)
    check("mapping rows filled", all(row in text.splitlines() for row in
          ["8|2-3-4|Line 1", "8|5-6-7|Line 2", "8|5-6-3-1|Line 3", "8|1-3-6-7|Line 4"]))
    check("commented template rows of those streams replaced", "# 8|2-3-4|Line N" not in text)
    check("header comment kept", "# Site_ID|Movement|Line N" in text)
    mapping = app._run3_parse_reference_mapping(text)
    check("mapping parses", mapping.get(("8", "5-6-3-1")) == "Line 3", str(mapping))
    check("no preflight warning about Gap Acceptance mapping",
          not any("Gap Acceptance" in w for w in app.collect_run3_warnings()), str(app.collect_run3_warnings()))

    # re-open: existing lines and assignments are shown again
    dlg2 = app.open_line_editor()
    check("re-open shows existing lines", dlg2.points["5-6-7"] == [(300, 20), (300, 120)])
    dlg2.top.destroy()

    # lines drawn on a smaller frame are scaled to the real video size when loaded
    data["lines"] = {"Line 1": [[100, 50], [200, 150]]}
    data["lines_frame_width"], data["lines_frame_height"] = 320, 180
    with open(zpath, "w", encoding="utf-8") as f:
        json.dump(data, f)
    app.load_pkstudio_zones()
    check("lines scaled x2 to the 640x360 video", app.lines["Line 1"] == [(200, 100), (400, 300)], str(app.lines["Line 1"]))

    root.destroy()
    print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
