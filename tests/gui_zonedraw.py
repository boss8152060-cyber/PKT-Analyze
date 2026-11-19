"""The window that draws the zones and the Lines in PKT Analyze (1.55.0): clicks make corners, a corner near another zone snaps (shared corners move
together), Enter closes a zone, undo / redo, delete a corner, Lines of two clicks, and the result is a zone file in the program's own data folder that the
program loads - without touching the video or a zone file made elsewhere.

Run from the Run folder:   python tests/gui_zonedraw.py
"""
import importlib.util
import json
import os
import sys
import tempfile
import tkinter as tk

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(prefix="pk_zdraw_")
os.environ["PKT_USER_DATA"] = os.path.join(tmp, "user_data")          # the zone files of this test go here, not into the real data folder
os.makedirs(os.environ["PKT_USER_DATA"])
os.environ["PK_STUDIO_CUDA_RELAUNCHED"] = "1"
spec = importlib.util.spec_from_file_location("pkstudio_main", os.path.join(HERE, "..", "PKStudio.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


CW, CH = 1280, 720
video = os.path.join(tmp, "20260907_084751A_.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(5):
    vw.write(np.full((CH, CW, 3), 90, np.uint8))
vw.release()
video_before = os.path.getsize(video)

root = tk.Tk()
root.geometry("1400x900+0+0")
app = m.Run1App(root)
shown = []
m.messagebox.showinfo = lambda *a, **k: shown.append(("info", a))
m.messagebox.showerror = lambda *a, **k: shown.append(("error", a))
app.video_var.set(video)
m.filedialog.askopenfilename = lambda **k: ""                           # (the zone editor asks for the drone picture: nothing is chosen in a test)

# ---- the entry points
check("without a video the window refuses to open", (lambda: (app.video_var.set(""), app.open_zone_line_editor())[1])() is None)
app.video_var.set(video)
ed = app.open_zone_line_editor()
root.update()
check("the window opens on a frame of the video with the 7 zones and 6 Lines listed", ed is not None and ed.img.shape[:2] == (CH, CW)
      and ed.zone_list.size() == 7 and ed.line_list.size() == 6, str(ed.img.shape if ed else ""))
check("it starts on Zone 1 (nothing is drawn yet)", ed.cur_zone == "Zone 1" and not any(ed.zones.values()))


def click(x, y):
    """A click on the picture at image position (x, y), the way the pane gives it."""
    return ed.on_click(float(x), float(y))


# ---- draw Zone 1 (4 corners) and close it with Enter
for p in ((200, 300), (500, 300), (520, 500), (180, 500)):
    click(*p)
check("the corners are placed where they were clicked", ed.draft == [[200.0, 300.0], [500.0, 300.0], [520.0, 500.0], [180.0, 500.0]], str(ed.draft))
check("fewer than 3 corners cannot be closed", (lambda: (ed.draft.__setitem__(slice(None), ed.draft[:2]), ed.finish_zone())[1])() is False)
click(520, 500)
click(180, 500)
check("Enter closes the zone and goes on to the next zone", ed.finish_zone() is True and len(ed.zones["Zone 1"]) == 4 and ed.cur_zone == "Zone 2" and not ed.draft)
check("the list shows what is drawn", "✓" in ed.zone_list.get(0) and "—" in ed.zone_list.get(1), ed.zone_list.get(0))

# ---- Zone 2 shares the right edge of Zone 1: corners clicked a few pixels away snap onto the corners of Zone 1
k = ed._k()
near = 4.0 / k
for p in ((500 + near, 300 - near), (800, 310), (820, 510), (520 - near, 500 + near)):
    click(*p)
check("a corner near a corner of another zone snaps onto it exactly", ed.draft[0] == [500.0, 300.0] and ed.draft[3] == [520.0, 500.0], str(ed.draft))
ed.finish_zone()
check("Zone 2 is closed and shares two corners with Zone 1", len(ed.zones["Zone 2"]) == 4 and ed.zones["Zone 2"][0] == ed.zones["Zone 1"][1] and ed.zones["Zone 2"][3] == ed.zones["Zone 1"][2])
# a corner near an EDGE of another zone snaps onto the edge
click(350, 300 + 5.0 / k)
check("a corner near an edge snaps onto the edge", abs(ed.draft[0][1] - 300.0) < 1e-6 and abs(ed.draft[0][0] - 350.0) < 1e-6, str(ed.draft))
ed.cancel_draft()
check("Esc cancels the zone being drawn", ed.draft == [])
ed.snap_var.set(False)
click(350, 300 + 5.0 / k)
check("with the switch off nothing snaps", abs(ed.draft[0][1] - (300 + 5.0 / k)) < 1e-6)
ed.cancel_draft()
ed.snap_var.set(True)

# ---- drag a shared corner: both zones follow
ex, ey = ed.pane.to_view(500, 300)
check("pressing on a corner grabs it", ed.on_press(500, 300, ex, ey) is True and len(ed.drag["members"]) == 2)
ed.on_drag(540, 280)
ed.on_release()
check("the corner shared by the two zones moved in both", ed.zones["Zone 1"][1] == [540.0, 280.0] and ed.zones["Zone 2"][0] == [540.0, 280.0], f"{ed.zones['Zone 1'][1]} {ed.zones['Zone 2'][0]}")
check("a press on empty picture grabs nothing (the picture can be panned)", ed.on_press(1000, 650, *ed.pane.to_view(1000, 650)) is False)
ed.undo()
check("undo puts the corner back in both zones", ed.zones["Zone 1"][1] == [500.0, 300.0] and ed.zones["Zone 2"][0] == [500.0, 300.0])
ed.redo()
check("redo moves it again", ed.zones["Zone 1"][1] == [540.0, 280.0])
ed.undo()

# ---- delete a corner, but never below 3
ex, ey = ed.pane.to_view(180, 500)
ed.on_press(180, 500, ex, ey)
ed.on_release()
check("the corner picked last is selected", ed.sel == ("Zone 1", 3))
check("a corner can be deleted while 4 are left", ed.delete_selected_corner() is True and len(ed.zones["Zone 1"]) == 3)
ed.sel = ("Zone 1", 0)
check("the 3rd corner cannot be deleted", ed.delete_selected_corner() is False and len(ed.zones["Zone 1"]) == 3)
ed.undo()
check("undo brings the deleted corner back", len(ed.zones["Zone 1"]) == 4)

# ---- clearing and drawing again
ed.cur_zone = "Zone 2"
ed.clear_current()
check("clear zone empties only that zone", ed.zones["Zone 2"] == [] and len(ed.zones["Zone 1"]) == 4)
ed.cur_zone = "Zone 1"
check("a drawn zone is not drawn over by a click (it asks to clear it first)", click(10, 10) is False and not ed.draft)
ed.cur_zone = "Zone 2"
for p in ((500, 300), (800, 310), (820, 510), (520, 500)):
    click(*p)
ed.finish_zone()
check("Zone 2 drawn again", len(ed.zones["Zone 2"]) == 4)

# ---- click the first corner again to close
ed.cur_zone = "Zone 3"
for p in ((900, 100), (1100, 100), (1100, 250)):
    click(*p)
fx, fy = ed.pane.to_view(900, 100)
ix, iy = ed.pane.to_image(fx + 3, fy + 2)
check("a click on the first corner closes the zone", click(ix, iy) is True and len(ed.zones["Zone 3"]) == 3 and not ed.draft)

# ---- Lines
ed.mode_var.set("line")
ed.cur_line = "Line 1"
click(100, 650)
check("one click starts a Line", len(ed.line_draft) == 1 and ed.lines["Line 1"] == [])
click(600, 660)
check("the second click completes it and the next Line is picked", ed.lines["Line 1"] == [[100.0, 650.0], [600.0, 660.0]] and ed.cur_line == "Line 2", str(ed.lines["Line 1"]))
ex, ey = ed.pane.to_view(600, 660)
check("a Line end can be grabbed and moved", ed.on_press(600, 660, ex, ey) is True)
ed.on_drag(700, 640)
ed.on_release()
check("the Line end moved", ed.lines["Line 1"][1] == [700.0, 640.0])
ed.mode_var.set("zone")

# ---- the picture draws without error (zones, corners, Lines, a zone being drawn)
img = np.zeros((600, 900, 3), np.uint8)
ed.cur_zone = "Zone 4"
click(300, 100)
click(400, 100)
click(400, 200)
ed.draw(img, ed.pane)
check("the overlay is drawn", int((img.sum(axis=2) > 0).sum()) > 500)
ed.cancel_draft()

# ---- the result: a zone file in the program's own data folder, loaded as the zone file
src_dir_before = sorted(os.listdir(tmp))
path = ed.use()
zones_dir = os.path.join(os.environ["PKT_USER_DATA"], "Zones")
check("the zone file is written in the data folder of the program (Zones), named after the video", path is not None and os.path.dirname(path) == zones_dir
      and os.path.basename(path) == "20260907_084751A__zones.json", str(path))
data = json.load(open(path, encoding="utf-8"))
check("it has the format of the PKT Data zone file (size, zones with points / points_norm / id / name, Lines)", data["frame_width"] == CW and data["frame_height"] == CH
      and [z["name"] for z in data["zones"]] == ["Zone 1", "Zone 2", "Zone 3"] and all({"points", "points_norm", "id", "area_px", "color_bgr"} <= set(z) for z in data["zones"])
      and data["lines"]["Line 1"] == [[100, 650], [700, 640]] and data["lines_frame_width"] == CW, str(list(data)))
check("the corners are whole pixels and the normalised ones fit", data["zones"][0]["points"][0] == [200, 300] and abs(data["zones"][0]["points_norm"][0][0] - 200 / CW) < 1e-6)
check("the program loaded it as its zone file", app.zone_line_config_var.get() == path and [z for z in m.ZONE_NAMES if len(app.zones[z]) >= 3] == ["Zone 1", "Zone 2", "Zone 3"]
      and len(app.lines["Line 1"]) == 2, str(app.zone_line_config_var.get()))
check("the video was not touched and nothing was written beside it", os.path.getsize(video) == video_before and sorted(os.listdir(tmp)) == src_dir_before)
path2 = ed.use()
check("using it again goes on writing the same file", path2 == path)

# ---- a zone file made somewhere else is never overwritten (a new file is made instead)
other = os.path.join(tmp, "from_data.json")
json.dump({"video_path": video, "frame_width": CW, "frame_height": CH, "my_note": "keep me",
           "zones": [{"id": 5, "name": "Zone 5", "points": [[10, 10], [100, 10], [100, 100]], "color_bgr": [1, 2, 3], "show_label": False}]},
          open(other, "w", encoding="utf-8"))
other_text = open(other, encoding="utf-8").read()
check("a zone file can be opened in the window", ed.open_file(other) is True and len(ed.zones["Zone 5"]) == 3 and len(ed.zones["Zone 1"]) == 0)
ed.cur_zone = "Zone 6"
for p in ((300, 300), (400, 300), (400, 400)):
    click(*p)
ed.finish_zone()
path3 = ed.use()
data3 = json.load(open(path3, encoding="utf-8"))
check("it was saved as a NEW file in the data folder (the other file is untouched)", path3 != other and os.path.dirname(path3) == zones_dir and open(other, encoding="utf-8").read() == other_text, str(path3))
check("what the old file had besides the zones is kept (a note, the colour and label of Zone 5)", data3.get("my_note") == "keep me"
      and [z for z in data3["zones"] if z["name"] == "Zone 5"][0]["color_bgr"] == [1, 2, 3] and [z for z in data3["zones"] if z["name"] == "Zone 5"][0]["show_label"] is False)

# ---- nothing drawn: no file
ed2 = app.open_zone_line_editor()
root.update()
for z in m.ZONE_NAMES:
    ed2.zones[z] = []
shown.clear()
check("with no zone drawn it says so and writes nothing", ed2.use() is None and shown and shown[-1][0] == "error")
ed2.close()

# ---- the way on: use + Align
opened = []
app.open_site_studio = lambda: (opened.append("editor"), None)[1]
ed.cur_zone = "Zone 7"
for p in ((50, 50), (150, 50), (150, 150)):
    click(*p)
ed.finish_zone()
check("'use, then go on' writes the zone file and opens the window that aligns and edits the zones", ed.use_and_align() is True and opened == ["editor"])
del app.open_site_studio

# ---- the single button: no zones -> the drawing window; zones but no Align -> the Align
app.zones = {z: [] for z in m.ZONE_NAMES}
app.run3_align_var.set("")
w = app.open_align_and_zones()
root.update()
check("one button: it opens the one window of the site setup (here with no zones yet)", isinstance(w, m.SiteStudio))
w.close()
app.zones["Zone 2"] = [(1, 1), (50, 1), (50, 50)]
w = app.open_align_and_zones()
root.update()
check("one button: with zones but no Align it opens the same window, nothing aligned yet", isinstance(w, m.SiteStudio) and not w.aligned and len(w.nodes) == 3)
w.close()

# ---- the helper that builds the file
d = m.build_zone_file({"Zone 2": [(1.4, 2.6), (10, 2), (10, 9)], "Zone 9": [(0, 0), (1, 1)], "Zone 1": [(0, 0), (4, 0), (4, 4)]}, {"Line 1": [(1, 1), (2, 2)], "Line 2": [(1, 1)]}, 20, 10)
check("build_zone_file: zones in order, short ones and half Lines left out, norm and area", [z["name"] for z in d["zones"]] == ["Zone 1", "Zone 2"]
      and d["zones"][0]["area_px"] == 8.0 and d["zones"][1]["points"][0] == [1, 3] and list(d["lines"]) == ["Line 1"] and d["zones"][0]["points_norm"][1] == [0.2, 0.0], str(d)[:200])

ed.close()
root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
