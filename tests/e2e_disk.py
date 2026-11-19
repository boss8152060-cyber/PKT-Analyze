"""Real test of a disk that is lost in the middle of a batch (1.58.0): the program tells apart a clip that was read to its end, a clip the user stopped, and a clip whose video
could not be read on (the disk was disconnected); the batch waits for the disk and does that clip again; a video that ends early is not counted as done.

Run from the Run folder:   py -3.12 tests/e2e_disk.py     (needs YOLO + a sample video; skips otherwise)
The disk is played by a switch: while it is "gone" path_reachable() says no and the reading of the video ends at once.
"""
import csv
import json
import os
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import messagebox

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import batch_run  # noqa: E402
import combine_clips  # noqa: E402
RF = combine_clips.result_file

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


vid_dir = os.path.join(HERE, "..", "..", "Input", "Video")
src = next((os.path.join(vid_dir, f) for f in sorted(os.listdir(vid_dir)) if f.lower().endswith(".mp4")), None) if os.path.isdir(vid_dir) else None
zone = os.path.join(HERE, "..", "..", "Input", "Zone", "20260907_084751A_zones.json")
if not src or not os.path.isfile(zone):
    print("SKIP: no sample video / zone file in PK STUDIO/Input")
    sys.exit(0)

tmp = tempfile.mkdtemp(prefix="pk_disk_")
tree = os.path.join(tmp, "in", "Site", "day1")
os.makedirs(tree)
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
w, h = int(cap.get(3)), int(cap.get(4))
for name in ("a.mp4", "b.mp4", "c.mp4"):
    out = cv2.VideoWriter(os.path.join(tree, name), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 600)
    for _ in range(int(3 * fps)):
        ok, f = cap.read()
        if not ok:
            break
        out.write(f)
    out.release()
# a video that is cut short: written as MJPG (readable up to where it is cut), the file cut in two
short = os.path.join(tree, "d_short.avi")
out = cv2.VideoWriter(short, cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
cap.set(cv2.CAP_PROP_POS_FRAMES, 600)
for _ in range(int(3 * fps)):
    ok, f = cap.read()
    if not ok:
        break
    out.write(f)
out.release()
cap.release()
size = os.path.getsize(short)
with open(short, "r+b") as f:
    f.truncate(int(size * 0.45))

mod = batch_run.load_pkstudio()
root = tk.Tk()
root.withdraw()
app = mod.Run1App(root)
shown = []
messagebox.showinfo = lambda *a, **k: shown.append(("info", a))
messagebox.showerror = lambda *a, **k: shown.append(("error", a))
messagebox.showwarning = lambda *a, **k: shown.append(("warning", a))
messagebox.askokcancel = lambda *a, **k: True
for key, val in (("lane_entry_motorcycle_m", "1.5"), ("lane_entry_car_m", "3.25"), ("lane_opp_motorcycle_m", "1.2"),
                 ("lane_opp_car_m", "3.0"), ("median_m", "0")):
    app.run3_geometry_vars[key].set(val)
app.zone_line_config_var.set(zone)
app.load_pkstudio_zones()


def wait_in_mainloop(done, timeout):
    end = time.time() + timeout

    def poll():
        if done() or time.time() > end:
            root.quit()
        else:
            root.after(50, poll)
    root.after(50, poll)
    root.mainloop()


# ---------------------------------------------------------------- the pieces
check("run_end_state: video read to the end = completed", mod.run_end_state(False, True, 3600, 1, 3600) == ("completed", True))
check("run_end_state: the user stopped = stopped", mod.run_end_state(True, False, 1200, 1, 3600) == ("stopped", False))
check("run_end_state: the video gave no more frames at 40% = interrupted", mod.run_end_state(False, True, 1440, 1, 3600) == ("interrupted", False))
check("run_end_state: 98% is the end of the video (a few frames fewer than the file says)", mod.run_end_state(False, True, 3530, 1, 3600) == ("completed", True))
check("run_end_state: the analysis window counts from its first frame", mod.run_end_state(False, True, 3600, 1801, 3600) == ("completed", True)
      and mod.run_end_state(False, True, 2000, 1801, 3600) == ("interrupted", False))
check("path_reachable: a file is, a missing one is not", mod.path_reachable(src) and not mod.path_reachable(os.path.join(tmp, "nothing.mp4")))

# ---------------------------------------------------------------- 1) a disk lost in the middle of a clip: the batch waits and does it again
state = {"up": True, "lost_once": False, "frames": 0, "attempts": 0}
real_reachable = mod.path_reachable
real_next = mod.BackgroundFrameReader.next


def fake_reachable(path, timeout=5.0):
    if not state["up"] and str(path).startswith(tmp):
        return False
    return real_reachable(path, timeout)


def fake_next(self, timeout=None):
    r = real_next(self, timeout)
    if r is not None and r[0] and os.path.basename(self.cap_path) == "b.mp4" if hasattr(self, "cap_path") else False:
        pass
    return r


mod.path_reachable = fake_reachable
orig_init = mod.BackgroundFrameReader.__init__


def tracked_init(self, cap, decode, frames_read, last_frame=None, maxsize=6):
    orig_init(self, cap, decode, frames_read, last_frame, maxsize)
    state["attempts"] += 1
    self._test_attempt = state["attempts"]


mod.BackgroundFrameReader.__init__ = tracked_init
count = {"n": 0}


def lossy_next(self, timeout=None):
    r = real_next(self, timeout)
    if r is not None and r[0]:
        count["n"] += 1
        # the 2nd clip (the 2nd reader), after 25 frames: the disk goes (the reading ends at once)
        if getattr(self, "_test_attempt", 0) == 2 and not state["lost_once"] and count["n"] > 25 + state.get("base", 0):
            state["lost_once"] = True
            state["up"] = False
            threading.Timer(0.6, lambda: state.__setitem__("up", True)).start()      # ... and it comes back after a moment
            return False, None
    elif r is not None:
        pass
    return r


def start_count(self_reader):
    pass


mod.BackgroundFrameReader.next = lossy_next
app.storage_poll_s = 0.1
dlg = app.clips_panel
dlg.add_videos(batch_run.find_videos([os.path.join(tmp, "in", "Site")]))
dlg.clips = [c for c in dlg.clips if not c["video"].endswith("d_short.avi")]
dlg.refresh()
dlg.skip_done_var.set(True)
app.output_var.set(os.path.join(tmp, "out"))
state["base"] = 0
app.start_analysis()
check("the batch started", app.running is True, str(shown))
wait_in_mainloop(lambda: not app.running, 900)
wait_in_mainloop(lambda: False, 1)
mod.BackgroundFrameReader.next = real_next
mod.path_reachable = real_reachable
check("the batch finished and the window is usable again", not app.running and str(app.start_button.cget("state")) == "normal")
check("the disk was lost once during the batch and the program noticed", state["lost_once"] and len(getattr(app, "_disk_events", [])) == 1, str(getattr(app, "_disk_events", None)))
o = os.path.join(tmp, "out")
dirs = {n: os.path.join(o, "Site", "day1", n) for n in ("a", "b", "c")}
sums = {n: batch_run.read_json(RF(d, "Run_Summary.json") or "") for n, d in dirs.items()}
check("every clip ended completed - the one that lost its disk was done again from its start", all(s.get("status") == "completed" for s in sums.values()), str({n: s.get("status") for n, s in sums.items()}))
check("each clip says it was read to its end", all((s.get("input") or {}).get("read_to_the_end") is True for s in sums.values()), str({n: s.get("input") for n, s in sums.items()}))
check("the clip that lost its disk has all its frames (not the 25 it had read)", sums["b"].get("processed_frames", 0) > 60, str(sums["b"].get("processed_frames")))
check("every clip has its results (Summary.json)", all(RF(d, "Summary.json") for d in dirs.values()))
win = app.batch_win
check("the progress window ended with three clips done", win is not None and win.state == [win.DONE] * 3 and win.finished, str(win.state if win else None))
check("the final report names the disk that was lost", any(k == "info" and "ฮาร์ดดิสก์หลุด" in str(a) for k, a in shown), str([str(a)[:80] for k, a in shown]))
rows = list(csv.DictReader(open(os.path.join(o, "Batch_Comparison.csv"), encoding="utf-8-sig")))
check("the comparison table has the three clips completed", sorted(r["Status"] for r in rows) == ["completed"] * 3, str([r["Status"] for r in rows]))

# ---------------------------------------------------------------- 2) the user stops: status stopped, not counted as done, done again next time
shown.clear()
dirs_b = dirs["b"]
import shutil
shutil.rmtree(o, ignore_errors=True)
stop_state = {"n": 0}


def stopping_next(self, timeout=None):
    r = real_next(self, timeout)
    if r is not None and r[0]:
        stop_state["n"] += 1
        if stop_state["n"] == 20:
            app.stop_event.set()
    return r


mod.BackgroundFrameReader.next = stopping_next
dlg.clips = [c for c in dlg.clips if c["video"].endswith("a.mp4")]
dlg.refresh()
app.start_analysis()
wait_in_mainloop(lambda: not app.running, 600)
wait_in_mainloop(lambda: False, 1)
mod.BackgroundFrameReader.next = real_next
a_dir = os.path.join(o, "Site", "day1", "a")
s_a = batch_run.read_json(RF(a_dir, "Run_Summary.json") or "")
check("a clip the user stopped is 'stopped' (not completed, not interrupted)", s_a.get("status") == "stopped" and s_a.get("stop_reason") == "Stopped by user", str(s_a.get("status")))
check("it is not counted as done: the next batch does it again", batch_run.run_complete(a_dir, "a") is False)

# ---------------------------------------------------------------- 3) a video that ends early (file cut short, not a lost disk): interrupted, no Run 3, not done
shutil.rmtree(o, ignore_errors=True)
shown.clear()
dlg.clear()
dlg.add_videos(batch_run.find_videos([os.path.join(tmp, "in", "Site")]))
dlg.clips = [c for c in dlg.clips if c["video"].endswith("d_short.avi")]
dlg.refresh()
app.start_analysis()
wait_in_mainloop(lambda: not app.running, 600)
wait_in_mainloop(lambda: False, 1)
d_dir = os.path.join(o, "Site", "day1", "d_short")
s_d = batch_run.read_json(RF(d_dir, "Run_Summary.json") or "")
check("a video that ends early is 'interrupted' (the file can be reached: not a lost disk)", s_d.get("status") == "interrupted" and (s_d.get("input") or {}).get("video_lost") is False
      and (s_d.get("input") or {}).get("read_to_the_end") is False, str(s_d.get("status")) + " " + str(s_d.get("stop_reason")))
check("no Run 3 was made on the part (no Summary.json), so it does not count as done", RF(d_dir, "Summary.json") is None and batch_run.run_complete(d_dir, "d_short") is False)
check("the batch did not wait for a disk that is there (one try only)", len(getattr(app, "_disk_events", [])) == 0)
win = app.batch_win
check("the progress window shows it as a problem, with the reason", win is not None and win.state == [win.ERR] and "ก่อนครบ" in win.notes[0], str((win.state, win.notes) if win else None))
check("the final report lists it as not finished", any(k == "info" and "อ่านวิดีโอไม่ถึงท้าย" in str(a) for k, a in shown), str([str(a)[:60] for k, a in shown]))

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
