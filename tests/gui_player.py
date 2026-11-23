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
    "analysis_start_s": "1.0", "analysis_end_s": "4", "save_video": True, "record_start_s": "1.5", "record_end_s": "2.5",
    "xy_video": True, "xy_start_s": "", "xy_end_s": "", "drone_video": False, "drone_start_s": "", "drone_end_s": ""}, str(dlg2.result))

# the X-Y video and the X-Y-on-drone video are chosen independently of the roadside video
dlg4 = m.ClipPlayerDialog(app, path, {"analysis_start_s": "1.0", "analysis_end_s": "4", "save_video": False, "xy_video": False,
                                       "drone_video": True, "drone_start_s": "2", "drone_end_s": "3"}, modal=False)
check("the three record choices open independently", (dlg4.rec_mode.get(), dlg4.xy_mode.get(), dlg4.drone_mode.get()) == ("none", "none", "range"))
dlg4.xy_mode.set("range")
dlg4.xy_start.set("1.5")
dlg4.xy_end.set("2.5")
check("each video keeps its own record choice", dlg4.apply() and dlg4.result["save_video"] is False and dlg4.result["xy_video"] is True
      and (dlg4.result["xy_start_s"], dlg4.result["xy_end_s"]) == ("1.5", "2.5") and dlg4.result["drone_video"] is True
      and (dlg4.result["drone_start_s"], dlg4.result["drone_end_s"]) == ("2", "3"), str(dlg4.result))
dlg5 = m.ClipPlayerDialog(app, path, {"xy_video": True, "drone_video": False}, modal=False)
dlg5.xy_mode.set("range")
dlg5.xy_start.set("3")
dlg5.xy_end.set("2")
errors.clear()
check("a wrong X-Y record range is refused", dlg5.apply() is False and len(errors) == 1, str(errors))
errors.clear()

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
# ---- copy / paste a range of times, and take the analysed range (1.60.12)
parse = m.parse_time_range_text
check("a pasted range: the usual ways to write it", parse("0:10.0 – 0:20.0") == ("0:10.0", "0:20.0") and parse("0:10-0:20") == ("0:10", "0:20") and parse("10 to 20") == ("10", "20")
      and parse("1:05, 2:00") == ("1:05", "2:00") and parse("10 20") == ("10", "20") and parse("10 - 20") == ("10", "20"), str([parse("0:10-0:20"), parse("10 - 20")]))
check("a range with an empty side is kept (from the start / to the end)", parse(" – 0:20") == ("", "0:20") and parse("0:10 – ") == ("0:10", ""))
check("text that is not a range of times is not one", parse("hello") is None and parse("") is None and parse("a - b") is None and parse("1 2 3") is None and parse(None) is None)
dlg.a_start.set("0:30"); dlg.a_end.set("1:45"); dlg.r_start.set(""); dlg.r_end.set(""); dlg.xy_start.set(""); dlg.xy_end.set("")
root.clipboard_clear()
dlg.copy_range(dlg.a_start, dlg.a_end)
check("copy: the clipboard has 'start – end'", root.clipboard_get() == "0:30 – 1:45", root.clipboard_get())
dlg.paste_range(dlg.xy_start, dlg.xy_end)
check("paste into another box: both times", (dlg.xy_start.get(), dlg.xy_end.get()) == ("0:30", "1:45"), str((dlg.xy_start.get(), dlg.xy_end.get())))
root.clipboard_clear(); root.clipboard_append("2:00 – 2:30")
dlg.paste_range(dlg.drone_start, dlg.drone_end)
check("paste text copied from anywhere (a range of times)", (dlg.drone_start.get(), dlg.drone_end.get()) == ("2:00", "2:30"))
root.clipboard_clear(); root.clipboard_append("nothing to do with times")
dlg.paste_range(dlg.r_start, dlg.r_end)
check("the clipboard holds other text: the range copied last in the program is pasted", (dlg.r_start.get(), dlg.r_end.get()) == ("0:30", "1:45"), str((dlg.r_start.get(), dlg.r_end.get())))
dlg2 = m.ClipPlayerDialog(app, path, {}, modal=False)
root.update()
root.clipboard_clear()
dlg2.paste_range(dlg2.xy_start, dlg2.xy_end)
check("the range copied survives into the next clip's window", (dlg2.xy_start.get(), dlg2.xy_end.get()) == ("0:30", "1:45"))
dlg2.close()
dlg.a_start.set("0:10"); dlg.a_end.set("0:40")
dlg.take_analysis_range(dlg.drone_start, dlg.drone_end)
check("'= the analysed range': the box gets the analysed start and end", (dlg.drone_start.get(), dlg.drone_end.get()) == ("0:10", "0:40"))
dlg.a_start.set(""); dlg.a_end.set("")
dlg.take_analysis_range(dlg.drone_start, dlg.drone_end)
check("... and an empty analysed range (the whole clip) is empty there too", (dlg.drone_start.get(), dlg.drone_end.get()) == ("", ""))
dlg.drone_mode.set("none")
dlg.a_start.set("0:10"); dlg.a_end.set("0:40")
dlg.take_analysis_range(dlg.drone_start, dlg.drone_end, dlg.drone_mode)
check("taking the analysed range into a box that says 'do not record' switches it to 'only this range'", dlg.drone_mode.get() == "range")
dlg.xy_mode.set("none")
root.clipboard_clear(); root.clipboard_append("0:05 – 0:15")
dlg.paste_range(dlg.xy_start, dlg.xy_end, dlg.xy_mode)
check("a pasted range switches the box to 'only this range'", dlg.xy_mode.get() == "range" and (dlg.xy_start.get(), dlg.xy_end.get()) == ("0:05", "0:15"))
texts = []


def walk(w_):
    for c in w_.winfo_children():
        try:
            texts.append(str(c.cget("text")))
        except tk.TclError:
            pass
        walk(c)


walk(dlg.top)
check("every box has the buttons: 4 x copy, 4 x paste, 3 x '= analysed range'", texts.count("คัดลอกช่วง") == 4 and texts.count("วางช่วง") == 4 and texts.count("= ช่วงวิเคราะห์") == 3, str((texts.count("คัดลอกช่วง"), texts.count("วางช่วง"))))
# the keys of the player do not take over a time that is being typed
ent = [c for c in dlg.top.winfo_children()[0:0]]
entries = []


def find_entries(w_):
    for c in w_.winfo_children():
        if isinstance(c, m.ttk.Entry):
            entries.append(c)
        find_entries(c)


find_entries(dlg.top)
dlg.top.update()
pos_before, playing_before = dlg.pos, getattr(dlg, "playing", None)
entries[0].focus_force()
dlg.top.update()
entries[0].event_generate("<space>")
entries[0].event_generate("<Right>")
dlg.top.update()
check("space and the arrow keys in a time box do not play / step the video", dlg.pos == pos_before and getattr(dlg, "playing", None) == playing_before, f"{dlg.pos} {pos_before}")
dlg.top.focus_force()
dlg.canvas.focus_force()
dlg.top.update()
dlg.canvas.event_generate("<Right>")
dlg.top.update()
check("... but the arrow keys still step the video when no time box has the focus", dlg.pos == pos_before + 1, f"{dlg.pos} {pos_before}")
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
