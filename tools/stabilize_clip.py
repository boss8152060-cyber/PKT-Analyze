"""Undo a camera move inside a finished clip WITHOUT detecting again (PKT-Analyze 1.61.9).

When the camera was bumped during recording, the zones and the calibration (drawn on the view before the move) no
longer fit the frames after it: vehicles get the wrong zones and the wrong positions in metres. This tool measures,
every few seconds of the clip's video, how the view moved compared with a reference frame (ORB features + RANSAC
homography on the whole picture), maps every detection of the clip (trajectory point and box) back into the reference
view, and then gives the zones again (rezone_detection_records). Run the indicators again from the raw data afterwards.

    python tools/stabilize_clip.py <clip folder> --video <the clip's video> --ref-video <video> --ref-time <s>
                                   [--step 10] [--dry-run]

--ref-video / --ref-time = a frame of the view the zones and the calibration were drawn on (e.g. a clip of the same
camera before the move). Writes 0_Raw/Camera_Shift.csv (time, shift of the frame centre in px, matched points, the
homography), keeps the old files once as *_before_stabilize, notes "stabilized_from_raw" in Run_Summary.json.
Samples with too few matched points (< MIN_INLIERS, e.g. a bus in front of the camera) take the nearest good sample.
"""
import csv
import json
import os
import shutil
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import combine_clips as cc  # noqa: E402
import rezone_clip as rz  # noqa: E402

MIN_INLIERS = 60
N_FEATURES = 4000


class ViewMatcher:
    def __init__(self, ref_img):
        self.orb = cv2.ORB_create(N_FEATURES)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.k1, self.d1 = self.orb.detectAndCompute(cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY), None)

    def homography(self, img):
        """(H mapping reference pixels -> this frame's pixels, inliers) or (None, 0)."""
        k2, d2 = self.orb.detectAndCompute(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), None)
        if d2 is None or self.d1 is None:
            return None, 0
        m = sorted(self.bf.match(self.d1, d2), key=lambda x: x.distance)[:800]
        if len(m) < 8:
            return None, 0
        H, inl = cv2.findHomography(np.float32([self.k1[x.queryIdx].pt for x in m]),
                                    np.float32([k2[x.trainIdx].pt for x in m]), cv2.RANSAC, 4.0)
        return (H, int(inl.sum())) if H is not None else (None, 0)


def read_frame(path, sec):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(sec * (cap.get(cv2.CAP_PROP_FPS) or 30))))
    ok, img = cap.read()
    cap.release()
    return img if ok else None


def measure(video, matcher, step, log=print):
    """[(t, H, inliers)] every `step` s of the video; bad samples take the nearest good H."""
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    length = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    samples = []
    t = 0.0
    while t < length:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * fps)))
        ok, img = cap.read()
        H, n = matcher.homography(img) if ok else (None, 0)
        samples.append([t, H if n >= MIN_INLIERS else None, n])
        t += step
    cap.release()
    good = [i for i, s in enumerate(samples) if s[1] is not None]
    if not good:
        raise RuntimeError("no frame of the video matches the reference frame")
    for i, s in enumerate(samples):
        if s[1] is None:
            j = min(good, key=lambda g: abs(g - i))
            s[1] = samples[j][1]
    log(f"  {len(samples)} samples, {len(samples) - len(good)} filled from neighbours")
    return samples


def shift_px(H, pt=(960.0, 540.0)):
    q = cv2.perspectiveTransform(np.float32([[pt]]), H)[0, 0]
    return float(q[0] - pt[0]), float(q[1] - pt[1])


def stabilize_rows(rows, samples):
    """Map every row's trajectory point and box from its frame's view back into the reference view."""
    times = np.array([s[0] for s in samples])
    inv = [np.linalg.inv(s[1]) for s in samples]
    out = []
    for r in rows:
        r2 = dict(r)
        try:
            t = float(r.get("timestamp") or 0)
        except ValueError:
            out.append(r2)
            continue
        Hi = inv[int(np.abs(times - t).argmin())]
        try:
            x, y = float(r["trajectory_x"]), float(r["trajectory_y"])
            q = cv2.perspectiveTransform(np.float32([[[x, y]]]), Hi)[0, 0]
            r2["trajectory_x"], r2["trajectory_y"] = f"{q[0]:.0f}", f"{q[1]:.0f}"
        except (KeyError, ValueError):
            pass
        try:
            x1, y1, x2, y2 = (float(r[k]) for k in ("bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2"))
            c = cv2.perspectiveTransform(np.float32([[[x1, y1]], [[x2, y1]], [[x2, y2]], [[x1, y2]]]), Hi).reshape(-1, 2)
            r2["bbox_x1"], r2["bbox_y1"] = f"{c[:, 0].min():.0f}", f"{c[:, 1].min():.0f}"
            r2["bbox_x2"], r2["bbox_y2"] = f"{c[:, 0].max():.0f}", f"{c[:, 1].max():.0f}"
        except (KeyError, ValueError):
            pass
        out.append(r2)
    return out


def stabilize_clip(clip, video, ref_video, ref_time, step=10.0, dry_run=False, log=print):
    name = os.path.basename(os.path.normpath(clip))
    settings_path = cc.result_file(clip, "Settings.json", name)
    det_path = cc.result_file(clip, "Detection_Records.csv", name)
    ids_path = cc.result_file(clip, "ID_Zone_Summary.csv", name)
    zone_path = cc.result_file(clip, "Zone_Summary.csv", name) or os.path.join(clip, cc.SUMMARY_DIR, "Zone_Summary.csv")
    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)
    ref = read_frame(ref_video, ref_time)
    if ref is None:
        raise RuntimeError("cannot read the reference frame")
    log(f"{name}: measuring the camera view every {step:g} s")
    samples = measure(video, ViewMatcher(ref), step, log)
    shifts = [shift_px(s[1]) for s in samples]
    big = [(s[0], d) for s, d in zip(samples, shifts) if abs(d[0]) + abs(d[1]) > 5]
    log(f"  largest shift {max(abs(a) + abs(b) for a, b in shifts):.0f} px; moved from t = {big[0][0]:.0f} s" if big else "  the view did not move")
    fields, rows = rz.read_rows(det_path)
    new_rows = stabilize_rows(rows, samples)
    core = rz.load_core()
    new_rows, id_rows, zone_rows = core["rezone_detection_records"](new_rows, settings["zone_snapshot"]["zones"], 1)
    old_ids = {r["track_id"]: r["zone_sequence"] for r in rz.read_rows(ids_path)[1]}
    routes = sum(1 for r in id_rows if old_ids.get(r["track_id"]) != r["zone_sequence"])
    log(f"  {routes} of {len(id_rows)} routes change")
    if dry_run:
        return samples, routes
    raw_dir = os.path.dirname(det_path)
    rz.keep_once(det_path, os.path.join(raw_dir, "Detection_Records_before_stabilize.csv"))
    rz.keep_once(ids_path, os.path.join(raw_dir, "ID_Zone_Summary_before_stabilize.csv"))
    with open(os.path.join(raw_dir, "Camera_Shift.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["time_s", "shift_x_px", "shift_y_px", "matched_points"] + [f"h{i}{j}" for i in range(3) for j in range(3)])
        for (t, H, n), (dx, dy) in zip(samples, shifts):
            w.writerow([f"{t:.1f}", f"{dx:.1f}", f"{dy:.1f}", n] + [f"{v:.8g}" for v in H.reshape(-1)])
    rz.write_rows(det_path, fields, new_rows)
    rz.write_rows(ids_path, list(id_rows[0].keys()), id_rows)
    rz.write_rows(zone_path, list(zone_rows[0].keys()), zone_rows)
    rs = cc.result_file(clip, "Run_Summary.json", name)
    if rs:
        with open(rs, encoding="utf-8") as f:
            data = json.load(f)
        data["stabilized_from_raw"] = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "reference": f"{ref_video} @ {ref_time} s",
                                       "max_shift_px": round(max(abs(a) + abs(b) for a, b in shifts), 1), "routes_changed": routes}
        with open(rs, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    return samples, routes


def main(argv):
    def opt(k, default=None):
        return argv[argv.index(k) + 1] if k in argv else default
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    if len(args) != 1 or not opt("--video") or not opt("--ref-video") or opt("--ref-time") is None:
        print(__doc__)
        return 1
    stabilize_clip(args[0], opt("--video"), opt("--ref-video"), float(opt("--ref-time")), float(opt("--step", 10)),
                   dry_run="--dry-run" in argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
