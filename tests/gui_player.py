"""Headless test of the in-program video player / time-range dialog (needs torch/cv2/ultralytics).

Run from the Run folder:   python tests/gui_player.py
"""
import importlib.util
import os
import sys
import tempfile
import time
import tkinter as tk
from tkinter import messagebox

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


tmp = tempfile.mkdtemp(prefix="pk_player_")
path = os.path.join(tmp, "v.mp4")
w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 30.0, (320, 180))
for i in range(150):                       # 5 s at 30 fps
    f = np.full((180, 320, 3), i, dtype=np.uint8)
    cv2.putText(f, str(i), (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    w.write(f)
w.release()

root = tk.Tk()
root.withdraw()
app = m.Run1App(root)
errors = []
messagebox.showerror = lambda *a, **k: errors.append(a)

dlg = m.ClipPlayerDialog(app, path, {"analysis_start_s": "1.0", "analysis_end_s": "4", "save_video": True}, modal=False)
root.update()
check("the dialog fits on the screen, OK button visible", dlg.top.winfo_reqheight() <= root.winfo_screenheight() - 60
      and dlg.ok_button.winfo_rooty() + dlg.ok_button.winfo_height() <= root.winfo_screenheight(),
      f"dialog {dlg.top.winfo_reqheight()} px, screen {root.winfo_screenheight()} px, OK bottom {dlg.ok_button.winfo_rooty() + dlg.ok_button.winfo_height()}")
check("video info read: 150 frames at 30 fps = 5 s", dlg.total == 150 and abs(dlg.fps - 30) < 0.01 and abs(dlg.duration - 5.0) < 0.01)
check("opens at the analysis start (1.0 s = frame index 30)", dlg.pos == 30, str(dlg.pos))
dlg.step(1)
check("step +1 frame", dlg.pos == 31)
dlg.step(-2)
check("step -2 frames", dlg.pos == 29)
dlg.show_frame(90)
check("jump to 3.0 s", dlg.pos == 90 and abs(dlg.current_time() - 3.0) < 1e-6)
check("time label shows position / length", dlg.time_text.get().startswith("0:03.0 / 0:05.0"), dlg.time_text.get())

# "use this time" buttons put the current time into the entry
dlg.a_end.set(m.format_clock_time(dlg.current_time()))
check("end time taken from the player", dlg.a_end.get() == "0:03.0", dlg.a_end.get())

# playing advances the frame
dlg.show_frame(10)
dlg.toggle_play()
end = time.time() + 0.6
while time.time() < end:
    root.update()
    time.sleep(0.01)
dlg.toggle_play()
check("playing moves forward", dlg.pos > 10, str(dlg.pos))

# recording modes
errors.clear()
dlg2 = m.ClipPlayerDialog(app, path, {"analysis_start_s": "1.0", "analysis_end_s": "4", "save_video": True,
                                       "record_start_s": "1.5", "record_end_s": "2.5"}, modal=False)
check("existing record range opens in range mode", dlg2.rec_mode.get() == "range")
check("apply returns the chosen times", dlg2.apply() and dlg2.result == {
    "analysis_start_s": "1.0", "analysis_end_s": "4", "save_video": True, "record_start_s": "1.5", "record_end_s": "2.5"}, str(dlg2.result))

dlg3 = m.ClipPlayerDialog(app, path, {"analysis_start_s": "3", "analysis_end_s": "2"}, modal=False)
check("end before start is refused with a message", dlg3.apply() is False and len(errors) == 1 and dlg3.result is None, str(errors))
dlg3.rec_mode.set("none")
dlg3.a_end.set("")
dlg3.a_start.set("9")
errors.clear()
check("start after the end of the video is refused", dlg3.apply() is False and len(errors) == 1)
dlg3.a_start.set("")
dlg3.a_end.set("4")
check("no recording -> save_video False, record times cleared", dlg3.apply() and dlg3.result["save_video"] is False and dlg3.result["record_start_s"] == "", str(dlg3.result))

dlg4 = m.ClipPlayerDialog(app, path, {}, modal=False)
dlg4.cancel()
check("cancel returns nothing", dlg4.result is None)

# main window: the four fields exist, are saved and restored, are validated
app.analysis_start_var.set("0:30")
app.analysis_end_var.set("2:15")
app.record_start_var.set("1:00")
app.record_end_var.set("1:30")
st = app.get_settings()
check("settings carry the time range", (st["analysis_start_s"], st["analysis_end_s"], st["record_start_s"], st["record_end_s"]) == ("0:30", "2:15", "1:00", "1:30"))
for v in (app.analysis_start_var, app.analysis_end_var, app.record_start_var, app.record_end_var):
    v.set("")
app.set_settings(st)
check("settings restore the time range", app.analysis_start_var.get() == "0:30" and app.record_end_var.get() == "1:30")
root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
