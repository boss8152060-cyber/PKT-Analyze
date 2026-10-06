"""The display table of tab 1: every switch exists for the normal video AND for the X-Y video, independently.

Checks: the X-Y video follows its own (xy_) switches and not the normal-video ones; the settings round trip; an older settings file (without the xy_
keys) copies the normal-video choices to the X-Y ones; the normal video's info-text switch reaches the run-time settings.

Run from the Run folder:   python tests/gui_displaytable.py
"""
import importlib.util
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


tmp = tempfile.mkdtemp(prefix="pk_disp_")
video = os.path.join(tmp, "clip.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (1280, 720))
for _ in range(5):
    vw.write(np.full((720, 1280, 3), 60, np.uint8))
vw.release()

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
app.zones = {name: [] for name in m.ZONE_NAMES}
app.zones["Zone 1"] = [(100, 100), (1500, 100), (1500, 600), (100, 600)]
tracks = {1: [], 2: []}
for k in range(40):
    t = k / 10.0
    tracks[1].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Car", "zone": "Zone 1" if k < 20 else "",
                      "confidence": "0.91", "_m": (2.0 + 0.9 * k, 5.0), "_mc": (2.0 + 0.9 * k, 5.0)})
    tracks[2].append({"frame": str(k + 1), "timestamp": f"{t:.6f}", "_timestamp": t, "class_name": "Motorcycle", "zone": "",
                      "confidence": "0.80", "_m": (30.0 - 0.7 * k, 12.0 + 0.1 * k), "_mc": (30.0 - 0.7 * k, 12.0 + 0.1 * k)})
c = {"perspective": None, "ppm": 40.0, "axis_deg": 0.0}


def frame_at(path, idx=15):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, f = cap.read()
    cap.release()
    return f.astype(np.int16) if ok else None


def differs(a, b):
    return int((np.abs(a - b).sum(axis=2) > 60).sum())


def xy(display):
    return frame_at(app._run3_write_topview_video(tracks, c, tempfile.mkdtemp(dir=tmp), video, display=display))


none_off = {f"show_label_{n}": False for n in ("id", "class", "conf", "zone", "speed")}
base = xy(dict(none_off, draw_trail=False))

# ---- every X-Y switch acts alone: the normal-video switch of the same name does not
lab_normal_on = xy(dict(none_off, show_label_id=True, draw_trail=False))
check("a caller that gives no xy_ key (an old one) still gets the normal-video switch of the same name for the X-Y video",
      differs(lab_normal_on, base) > 20)
lab_xy_off = xy(dict(show_label_id=True, xy_show_label_id=False, xy_show_label_class=False, xy_show_label_conf=False, xy_show_label_zone=False, xy_show_label_speed=False, draw_trail=False))
check("normal ID label ON but the X-Y twin OFF: the X-Y video has no labels (same picture as all off)", differs(lab_xy_off, base) < 5, str(differs(lab_xy_off, base)))
lab_xy_on = xy(dict(show_label_id=False, xy_show_label_id=True, xy_show_label_class=False, xy_show_label_conf=False, xy_show_label_zone=False, xy_show_label_speed=False, draw_trail=False))
check("normal ID label OFF but the X-Y twin ON: the X-Y video shows the label", differs(lab_xy_on, base) > 20, str(differs(lab_xy_on, base)))

full = dict(xy_show_label_id=True, xy_show_label_class=True, xy_show_label_conf=True, xy_show_label_zone=True, xy_show_label_speed=True, xy_draw_trail=False)
ref = xy(full)
check("X-Y point off: the dots disappear", differs(xy(dict(full, xy_show_point=False)), ref) > 100)
check("X-Y grid off: the metre grid disappears", differs(xy(dict(full, xy_show_grid=False)), ref) > 1000)
check("X-Y time text off: the 't = ... frame ...' text disappears", differs(xy(dict(full, xy_show_time=False)), ref) > 50)
check("X-Y zone frame off: the zone outline disappears", differs(xy(dict(full, xy_show_zone_boundary=False, xy_show_zone_label=False)), ref) > 100)
trail_on = xy(dict(full, xy_draw_trail=True, xy_trail_length=15))
check("X-Y trajectory on (xy_draw_trail): a trail is drawn", differs(trail_on, ref) > 50)
check("the normal draw_trail alone does not draw an X-Y trail when xy_draw_trail is off", differs(xy(dict(full, draw_trail=True, xy_draw_trail=False)), ref) < 5)
check("X-Y zone opacity has its own value (xy_zone_overlay_opacity 100 differs from 45)", differs(xy(dict(full, xy_zone_overlay_opacity="100")), xy(dict(full, xy_zone_overlay_opacity="45"))) > 100)

# ---- the settings: both sets are written and read back
for key in m.XY_DISPLAY_KEYS:
    check(f"the settings have {key}", key in app.get_settings())
st = app.get_settings()
app.xy_vars["xy_show_label_speed"].set(False)
app.show_label_speed_var.set(True)
st2 = app.get_settings()
check("both are kept apart in the settings (normal Speed on, X-Y Speed off)", st2["show_label_speed"] is True and st2["xy_show_label_speed"] is False)
app.show_info_text_var.set(False)
check("the normal video's info-text switch is in the settings and in the run-time settings", app.get_settings()["show_info_text"] is False and app._runtime_snapshot()["show_info_text"] is False)
app.show_info_text_var.set(True)

# ---- an older settings file: the X-Y video gets the normal-video choices
old = {k: v for k, v in app.get_settings().items() if not k.startswith("xy_") and k != "show_info_text"}
old.update({"show_label_speed": False, "show_zone_boundary": False, "draw_trail": True, "trail_length": "77", "zone_overlay_opacity": "20"})
for var in app.xy_vars.values():
    var.set(var.get())                                                    # touch
app.set_settings(old)
x = app.xy_vars
check("an older settings file copies the normal-video choices to the X-Y ones (speed off, zone frame off, trail on, length 77, opacity 20)",
      x["xy_show_label_speed"].get() is False and x["xy_show_zone_boundary"].get() is False and x["xy_draw_trail"].get() is True
      and str(x["xy_trail_length"].get()) == "77" and str(x["xy_zone_overlay_opacity"].get()) == "20",
      str({k: x[k].get() for k in ("xy_show_label_speed", "xy_show_zone_boundary", "xy_draw_trail", "xy_trail_length", "xy_zone_overlay_opacity")}))
check("... and the switches that did not exist before keep their defaults (point, grid, time on)", x["xy_show_point"].get() and x["xy_show_grid"].get() and x["xy_show_time"].get())

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
