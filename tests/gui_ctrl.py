"""Control points of the junction setup (1.60.16): extra pins that belong to no zone, put on the video and on the drone picture to make the Align stronger.

The scene: a ground plane seen by a tilted camera with a lens that bends the lanes (radial distortion), and from straight above (20 drone pixels per metre). The Align (kind: lens) is
made once from the corners of the zones only and once with control points added; the places of points that were NOT used are compared with where they really are.

Run from the Run folder:   python tests/gui_ctrl.py
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
tmp = tempfile.mkdtemp(prefix="pk_ctrl_")
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


CW, CH = 1280, 720
H_CAM = cv2.getPerspectiveTransform(np.float32([(0, 0), (60, 0), (60, 20), (0, 20)]), np.float32([(100, 330), (1200, 280), (1260, 600), (40, 630)]))
CENTER = np.array([CW / 2.0, CH / 2.0])
K_LENS, K_LENS2 = 0.10, 0.10                                           # the lens: a point at the edge is moved by 10 % x r^2 and 10 % x r^4 (the lanes bend; more than a simple one-term lens fits)


def video_px(g):
    p = cv2.perspectiveTransform(np.asarray(g, float).reshape(-1, 1, 2), H_CAM).reshape(-1, 2)
    d = (p - CENTER) / (CW / 2.0)
    r2 = (d ** 2).sum(axis=1, keepdims=True)
    return CENTER + (CW / 2.0) * d * (1.0 + K_LENS * r2 + K_LENS2 * r2 * r2)


def drone_px(g):
    return np.asarray(g, float) * 20.0 + [60.0, 80.0]


RNG = np.random.default_rng(11)


def clicked(p, sigma):
    """Where a person really clicks: the true spot and a little off (sigma pixels)."""
    return np.asarray(p, float) + RNG.normal(0.0, sigma, size=np.shape(p))


video = os.path.join(tmp, "20260907_084751A_.mp4")
vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), 10, (CW, CH))
for _ in range(3):
    vw.write(np.full((CH, CW, 3), 90, np.uint8))
vw.release()
drone_file = os.path.join(tmp, "drone.png")
cv2.imencode(".png", np.full((560, 1400, 3), 120, np.uint8))[1].tofile(drone_file)

G = {"Zone 2": [(4, 5), (18, 5), (18.9, 12), (4.7, 12)], "Zone 3": [(18, 5), (32, 5), (32.9, 12), (18.9, 12)], "Zone 4": [(32, 5), (36, 8.2), (32.9, 12)]}
# the control points: spots on the road that are not corners of a zone, spread over the scene (4 along each lane edge and some in the middle)
CTRL = [(7, 6), (12, 8), (16, 11), (22, 6), (26, 9), (30, 11.5), (10, 11), (34, 9.5)]
TEST = [(x, y) for x in np.arange(5.0, 34.0, 3.0) for y in np.arange(6.0, 11.5, 2.0)]        # places that nothing was pinned at

root = tk.Tk()
root.geometry("1500x900+0+0")
app = m.Run1App(root)
m.messagebox.showinfo = lambda *a, **k: None
m.messagebox.showerror = lambda *a, **k: None
m.messagebox.askyesno = lambda *a, **k: True
app.video_var.set(video)


def make_studio(with_ctrl):
    app.zones = {z: [] for z in m.ZONE_NAMES}
    app.run3_align_var.set("")
    app.run3_align_enabled_var.set(False)
    st = app.open_site_studio(ask_drone=False)
    root.update()
    st.load_drone(drone_file)
    st.set_kind("lens")
    for name, pts in G.items():
        st.cur_zone = name
        for q in clicked(video_px(pts), 1.5):
            st.on_click("video")(float(q[0]), float(q[1]))
        st.finish_zone()
    allg = np.array(sorted({tuple(q) for g in G.values() for q in g}))
    allv, alld = video_px(allg), clicked(drone_px(allg), 1.5)
    for nid in sorted(st.nodes):
        v = np.array(st.nodes[nid]["v"])
        j = int(np.argmin(np.hypot(*(allv - v).T)))
        st.sel = nid
        st._click_drone(*alld[j])
    st.scale = 0.05
    st.scale_var.set("0.05")
    st.set_scale_text()
    return st


def rms_error(st):
    v = video_px(np.array(TEST))
    d_est = st.drone_of(v)
    d_true = drone_px(np.array(TEST))
    return float(np.sqrt(((d_est - d_true) ** 2).sum(axis=1).mean()))


# ------------------------------------------------------------------ zone corners only
st = make_studio(False)
check("7 zone corners are pinned and the Align (lens, 6 pins or more) fits", st._pin_counts()["done"] == 7 and st.aligned, str(st._pin_counts()))
base = rms_error(st)
print("   error at 70 places that were not pinned, zone corners only: %.2f drone pixels" % base)

# ------------------------------------------------------------------ control points
check("'control point' is off to start with", st.ctrl_mode is False)
check("the button is in the pins tab", st.ctrl_button.winfo_exists())
st.toggle_control_mode()
check("the button turns it on", st.ctrl_mode is True)
n_zone_nodes = len(st.nodes)
for k, g in enumerate(CTRL, start=1):
    v = clicked(video_px([g])[0], 1.5)
    d = clicked(drone_px([g])[0], 1.5)
    st.on_click("video")(float(v[0]), float(v[1]))
    check(f"C{k}: a click on the video puts a control point that waits for the drone", st.sel in st.nodes and st._is_ctrl(st.sel) and st.nodes[st.sel]["d"] is None and st._label(st.sel) == f"C{k}", str(st._label(st.sel)))
    st.on_click("drone")(float(d[0]), float(d[1]))
    check(f"C{k}: the click on the drone picture pins it", all(st.nodes[i]["d"] is not None for i in st.nodes if st._is_ctrl(i)))
    if k == 2:
        break
for k, g in enumerate(CTRL[2:], start=3):
    v = clicked(video_px([g])[0], 1.5)
    d = clicked(drone_px([g])[0], 1.5)
    st.on_click("video")(float(v[0]), float(v[1]))
    st.on_click("drone")(float(d[0]), float(d[1]))
check("8 control points are pinned", sum(1 for i in st.nodes if st._is_ctrl(i) and st.nodes[i]["d"] is not None) == 8, str(len([i for i in st.nodes if st._is_ctrl(i)])))
check("they are not zone corners: no zone changed, the corners of the zones are the same 7", len(st.nodes) == n_zone_nodes + 8 and sum(len(st.zones[z]) for z in m.ZONE_NAMES) == 4 + 4 + 3 + 0)
check("they count as pins for the Align (7 + 8 = 15)", len(st._pairs()) == 15, str(len(st._pairs())))
better = rms_error(st)
print("   error at 70 places that were not pinned, with 8 control points: %.2f drone pixels" % better)
check("with clicks that are a little off (as by hand) the control points make the Align more exact (error down by at least a quarter)", better < base * 0.75, "%.2f -> %.2f px" % (base, better))
st.cancel_control_mode()
check("Esc / the button ends it", st.ctrl_mode is False)

# ------------------------------------------------------------------ what a control point is not
for z in m.ZONE_NAMES:
    st.zones[z] = list(st.zones[z])
st._prune()
check("cleaning up the zones does not take control points away", sum(1 for i in st.nodes if st._is_ctrl(i)) == 8)
c1 = [i for i in sorted(st.nodes) if st._is_ctrl(i)][0]
vc = list(st.nodes[c1]["v"])
st.cur_zone = "Zone 5"
st.on_click("video")(vc[0] + 1.0, vc[1] + 1.0)                          # a corner of a new zone near a control point...
node_new = max(st.nodes)
check("a corner of a zone does not snap onto a control point (they stay separate points)", not st._is_ctrl(node_new) and node_new != c1 and st.nodes[node_new]["v"] != vc, str(st.nodes[node_new]["v"]))
st.cancel_draft()
st._prune()

# ------------------------------------------------------------------ saved with the Align and read back
saved = json.loads(app.run3_align_var.get())
labels = [q.get("l") for q in saved["pairs"]]
check("the Align that is saved has the control points as C1 ... C8 (video place + drone place)", [l for l in labels if str(l).startswith("C")] == [f"C{k}" for k in range(1, 9)], str(labels))
st.use()
st.close()
st = app.open_site_studio(ask_drone=False)
root.update()
check("opened again the 8 control points are back, pinned on both pictures", sum(1 for i in st.nodes if st._is_ctrl(i) and st.nodes[i]["d"] is not None) == 8)
check("... and the zones are as they were (3 zones)", sum(1 for z in m.ZONE_NAMES if len(st.zones[z]) >= 3) == 3)
check("... and the Align is as good as before", abs(rms_error(st) - better) < 0.5, "%.2f vs %.2f" % (rms_error(st), better))

# ------------------------------------------------------------------ undo, delete, the worst pin
n0 = len([i for i in st.nodes if st._is_ctrl(i)])
st.toggle_control_mode()
v = video_px([(20, 7)])[0]
st.on_click("video")(float(v[0]), float(v[1]))
check("a control point that waits is a pin of the list", len([i for i in st.nodes if st._is_ctrl(i)]) == n0 + 1)
st.on_click("video")(float(v[0]) + 30, float(v[1]) + 5)
check("a second click on the video before the drone moves the one that waits (no second point)", len([i for i in st.nodes if st._is_ctrl(i)]) == n0 + 1)
st.undo()
st.undo()
check("undo takes it away step by step", len([i for i in st.nodes if st._is_ctrl(i)]) in (n0, n0 + 1))
st.cancel_control_mode()
c_last = [i for i in sorted(st.nodes) if st._is_ctrl(i)][-1]
st.sel = c_last
st.delete_selected_corner()
check("Delete takes the picked control point away", c_last not in st.nodes)
bad = [i for i in sorted(st.nodes) if st._is_ctrl(i)][0]
st.nodes[bad]["d"] = [st.nodes[bad]["d"][0] + 90.0, st.nodes[bad]["d"][1] - 60.0]         # one clicked in the wrong place on the drone picture
st._refit()
w = st.worst_pair()
check("the worst pin can be a control point (a wrong one is found)", w == bad, str(w))
st.delete_worst_pair()
check("... and 'lift the worst pin' removes it altogether (a control point has nothing to wait for)", bad not in st.nodes)

root.destroy()
print("FAILED: " + ", ".join(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
