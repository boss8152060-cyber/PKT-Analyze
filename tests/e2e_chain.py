"""Real test: consecutive clips analysed as ONE video, and vehicle IDs that continue over the clips of a folder.

Run from the Run folder:   py -3.12 tests/e2e_chain.py     (needs YOLO + a sample video; skips otherwise)
List:  Site/a.mp4, Site/b.mp4 (continues a: frames 1-120 and 121-240 of the same recording), Site/c.mp4 (another place in time)
Expected: Site/a_to_b/ (one result, continuous frames/time, a vehicle that crosses the cut keeps its ID),
Site/c/ (its IDs start after the highest ID of a_to_b), Site/All_Clips/ lists both.
"""
import csv
import json
import os
import shutil
import sys
import tempfile
import time
import tkinter as tk
from tkinter import messagebox

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import batch_run  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def wait_in_mainloop(done, timeout):
    end = time.time() + timeout

    def poll():
        if done() or time.time() > end:
            root.quit()
        else:
            root.after(50, poll)
    root.after(50, poll)
    root.mainloop()


vid_dir = os.path.join(HERE, "..", "..", "Input", "Video")
src = next((os.path.join(vid_dir, f) for f in sorted(os.listdir(vid_dir)) if f.lower().endswith(".mp4")), None) if os.path.isdir(vid_dir) else None
zone = os.path.join(HERE, "..", "..", "Input", "Zone", "20260907_084751A_zones.json")
if not src or not os.path.isfile(zone):
    print("SKIP: no sample video / zone file in PK STUDIO/Input")
    sys.exit(0)

tmp = tempfile.mkdtemp(prefix="pk_chain_")
tree = os.path.join(tmp, "in", "Site")
os.makedirs(tree)
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
w, h = int(cap.get(3)), int(cap.get(4))
n = int(2 * fps)
for name, first in (("a.mp4", 600), ("b.mp4", 600 + n), ("c.mp4", 2400)):      # b starts right where a ends
    out = cv2.VideoWriter(os.path.join(tree, name), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    for _ in range(n):
        ok, f = cap.read()
        if not ok:
            break
        out.write(f)
    out.release()
cap.release()

mod = batch_run.load_pkstudio()
root = tk.Tk()
root.withdraw()
app = mod.Run1App(root)
messagebox.showinfo = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: print("ERROR BOX:", a)
messagebox.askokcancel = lambda *a, **k: True
for key, val in (("lane_entry_motorcycle_m", "1.5"), ("lane_entry_car_m", "3.25"), ("lane_opp_motorcycle_m", "1.2"),
                 ("lane_opp_car_m", "3.0"), ("median_m", "0")):
    app.run3_geometry_vars[key].set(val)
app.zone_line_config_var.set(zone)
app.load_pkstudio_zones()
o = os.path.join(tmp, "out")
app.output_var.set(o)
panel = app.clips_panel
panel.add_videos(batch_run.find_videos([tree]))
check("three clips listed in order a, b, c", [os.path.basename(c["video"]) for c in panel.clips] == ["a.mp4", "b.mp4", "c.mp4"])
panel.tree.selection_set(["1"])
panel.toggle_continue()
check("b is marked as the continuation of a", panel.clips[1]["continues_previous"] is True and panel.clips[0]["continues_previous"] is False)
vals = [panel.tree.item(i, "values") for i in panel.tree.get_children()]
check("the list shows it", vals[1][3].startswith("↳") and vals[0][3] == "" and vals[2][3] == "", str(vals))
panel.tree.selection_set(["0"])
panel.toggle_continue()
check("the first clip of the list cannot continue anything", panel.clips[0]["continues_previous"] is False)
panel.skip_done_var.set(False)
app.start_analysis()
wait_in_mainloop(lambda: not app.running, 900)
wait_in_mainloop(lambda: False, 1)
check("batch finished", not app.running)

site = os.path.join(o, "Site")
check("a and b are ONE result folder a_to_b; c has its own; no separate a / b", sorted(d for d in os.listdir(site) if d != "All_Clips") == ["a_to_b", "c"], str(sorted(os.listdir(site))))
chain_dir, c_dir = os.path.join(site, "a_to_b"), os.path.join(site, "c")


def det(d, name):
    return list(csv.DictReader(open(os.path.join(d, name + "_Detection_Records.csv"), encoding="utf-8-sig")))


dc = det(chain_dir, "a_to_b")
frames = sorted({int(r["frame"]) for r in dc})
check("the chain has one continuous frame numbering 1..%d (no restart at the cut)" % (2 * n), frames[0] >= 1 and frames[-1] > n and frames[-1] <= 2 * n, f"{frames[0]}..{frames[-1]}")
stamps = [float(r["timestamp"]) for r in dc]
check("time runs on past the first clip (no restart)", max(stamps) > n / fps - 0.05 and max(stamps) <= 2 * n / fps, f"max {max(stamps):.2f} s, first clip is {n / fps:.2f} s")
spans = {}
for r in dc:
    spans.setdefault(r["track_id"], []).append(int(r["frame"]))
across = [t for t, fr in spans.items() if min(fr) <= n < max(fr)]
check("at least one vehicle crosses the cut and keeps ONE ID", len(across) >= 1, f"IDs crossing the cut: {across[:6]}")
summ = json.load(open(os.path.join(chain_dir, "a_to_b_Research_Run_Summary.json"), encoding="utf-8"))
check("the run summary records the chain", summ.get("video_chain") and len(summ["video_chain"]) == 2 and summ["id_offset"] == 0, str(summ.get("video_chain")))
dcc = det(c_dir, "c")
ids_chain = {int(r["track_id"]) for r in dc if int(r["track_id"]) >= 0}
ids_c = {int(r["track_id"]) for r in dcc if int(r["track_id"]) >= 0}
check("clip c continues the numbering: all its IDs are above the highest ID of a_to_b", ids_c and min(ids_c) > max(ids_chain), f"a_to_b max {max(ids_chain)}, c min {min(ids_c)}")
check("so no vehicle ID is used twice in the folder", not (ids_chain & ids_c))
csum = json.load(open(os.path.join(c_dir, "c_Research_Run_Summary.json"), encoding="utf-8"))
check("c's run summary says where its numbering started", csum["id_offset"] == max(ids_chain) and csum["max_track_id"] == max(ids_c), f"{csum['id_offset']} / {csum['max_track_id']}")
ac = [r["Clip"] for r in csv.DictReader(open(os.path.join(site, "All_Clips", "All_Clips.csv"), encoding="utf-8-sig"))]
check("the combined files list the chain and c", sorted(ac) == ["Site/a_to_b", "Site/c"], str(ac))

root.destroy()
shutil.rmtree(tmp, ignore_errors=True)
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
