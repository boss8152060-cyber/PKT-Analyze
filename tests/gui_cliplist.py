"""The clip list of step 1 (1.59.4): a number for every clip, 'record / do not record' for every clip for each of the 3 kinds of video, select all, a scroll bar, and a mouse wheel
that scrolls the list by itself (not the page behind it) when the pointer is over it.

Run from the Run folder:   python tests/gui_cliplist.py
"""
import importlib.util
import os
import sys
import tempfile
import tkinter as tk

HERE = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(prefix="pk_cliplist_")
os.environ["PKT_USER_DATA"] = os.path.join(tmp, "user_data")
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


root = tk.Tk()
root.geometry("1500x900+0+0")
app = m.Run1App(root)
panel = app.clips_panel
vids = []
for i in range(25):
    pth = os.path.join(tmp, "Site", "day1", f"clip_{i:02d}.mp4")
    os.makedirs(os.path.dirname(pth), exist_ok=True)
    open(pth, "wb").write(b"x")
    vids.append(pth)
panel.add_videos(panel.bt.find_videos([os.path.join(tmp, "Site")]))
root.update()
check("25 clips are listed", len(panel.clips) == 25 and len(panel.tree.get_children()) == 25)

# ------------------------------------------------------------------ the number of every clip
check("the first column is the number of the clip (1, 2, 3 ...)", [panel.tree.item(i, "values")[0] for i in panel.tree.get_children()][:3] == ["1", "2", "3"] or
      [str(panel.tree.item(i, "values")[0]) for i in panel.tree.get_children()][:3] == ["1", "2", "3"], str([panel.tree.item(i, "values")[:2] for i in panel.tree.get_children()][:3]))
check("... up to the last clip", str(panel.tree.item(panel.tree.get_children()[-1], "values")[0]) == "25")
check("the column is called 'ลำดับ' and sits first", panel.tree.heading("no", "text") == "ลำดับ" and panel.tree["columns"][0] == "no")
check("the clip name is in the next column", str(panel.tree.item("0", "values")[1]).endswith("clip_00.mp4"), str(panel.tree.item("0", "values")))
panel.clips[1]["continues_previous"] = True
panel.refresh()
check("the numbers stay right after a refresh (and the continuation mark is in the last column)", str(panel.tree.item("1", "values")[0]) == "2" and "ต่อจาก" in str(panel.tree.item("1", "values")[-1]))

# ------------------------------------------------------------------ record / do not record, every clip, each kind of video
kinds = (("save_video", "วิดีโอปกติ"), ("xy_video", "วิดีโอ X–Y"), ("drone_video", "X–Y บนภาพโดรน"))
panel.set_all_record(False, ("save_video", "xy_video", "drone_video"))
check("all three off for every clip", all(not c.get(k) for c in panel.clips for k, _ in kinds))
for key, name in kinds:
    panel.set_all_record(True, (key,))
    check(f"'{name}': record every clip - only this kind turns on", all(c.get(key) for c in panel.clips) and all(not c.get(o) for c in panel.clips for o, _ in kinds if o != key),
          str({o: sum(1 for c in panel.clips if c.get(o)) for o, _ in kinds}))
    panel.set_all_record(False, (key,))
    check(f"'{name}': do not record every clip - off again", all(not c.get(key) for c in panel.clips))
panel.set_all_record(True, ("xy_video",))
panel.set_all_record(False, ("save_video",))
check("a kind that is not touched keeps its answer", all(c.get("xy_video") for c in panel.clips) and all(not c.get("save_video") for c in panel.clips))
rec_buttons = [w for w in panel.winfo_children()[0:0]]
texts = []


def walk(w):
    for c in w.winfo_children():
        try:
            texts.append(str(c.cget("text")))
        except tk.TclError:
            pass
        walk(c)


walk(panel)
check("the window has the 'record / do not record' buttons for the 3 kinds and for all 3 together (4 of each) and 'select all'",
      texts.count("บันทึกทุกคลิป") == 4 and texts.count("ไม่บันทึกทุกคลิป") == 4 and "เลือกทั้งหมด" in texts, str(texts.count("บันทึกทุกคลิป")))
panel.select_all()
check("'select all' selects every clip", len(panel.selected_indexes()) == 25)

# ------------------------------------------------------------------ the mouse wheel
app.notebook.select(0)
root.update()
calls = []


class Page:
    def yview_scroll(self, n, unit):
        calls.append(n)


tab = app.notebook.index(app.notebook.select())
real_canvas = app._page_canvases[tab]
app._page_canvases[tab] = Page()


class Ev:
    def __init__(self, widget, delta):
        self.widget, self.delta = widget, delta


calls.clear()
app.on_mousewheel(Ev(panel.tree, -120))
check("the pointer is over the list and the list has more rows than it shows: the page does not scroll with it", calls == [], str(calls))
app.on_mousewheel(Ev(app.status_label if hasattr(app, "status_label") else root, -120))
check("the pointer is anywhere else: the page scrolls", calls == [1], str(calls))
calls.clear()
for _ in range(8):
    app.on_mousewheel(Ev(root, -30))                                  # a touch pad: small steps
check("small steps (a touch pad) add up and the page does scroll (2 of 8 x 30/120)", sum(calls) == 2, str(calls))
panel.clear()
root.update()
calls.clear()
app.on_mousewheel(Ev(panel.tree, -120))
check("a list with nothing to scroll lets the page scroll (the wheel is not lost over it)", calls == [1], str(calls))
app._page_canvases[tab] = real_canvas
check("the list has a scroll bar", any(isinstance(w, m.ttk.Scrollbar) for w in panel.tree.master.winfo_children()))

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
