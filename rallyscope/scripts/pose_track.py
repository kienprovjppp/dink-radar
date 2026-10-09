"""Four players tracked frame by frame, each in their own crop.

  pose_track.py track work60.mp4 court.json pose.npz --seeds "x,y x,y x,y x,y" --model pose_landmarker_heavy.task
  pose_track.py check work60.mp4 pose.npz out.png [--every 45]

Seeds are the hip centres on frame 0 in the order P1 near right, P2 near left,
P3 far left, P4 far right. Crop side = 2.4 x the player's pixel height, where
the height comes from perspective: h = 0.42 x (hip y - horizon y).
"""
import argparse
import multiprocessing as mproc

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d

from common import load, read_frames, frame_count

EDGES = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 24),
         (23, 25), (25, 27), (24, 26), (26, 28), (27, 29), (29, 31), (27, 31), (28, 30), (30, 32), (28, 32)]
COLS = [(61, 122, 255), (87, 255, 156), (210, 95, 255), (255, 227, 77)]  # BGR of P1..P4


def track_one(args):
    pid, video, seed, horizon, model, kh, n = args
    import mediapipe as mp
    opts = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model),
        running_mode=mp.tasks.vision.RunningMode.IMAGE, num_poses=2,
        min_pose_detection_confidence=0.3, min_pose_presence_confidence=0.3)
    det = mp.tasks.vision.PoseLandmarker.create_from_options(opts)
    L = np.full((n, 33, 3), np.nan, np.float32)
    Wd = np.full((n, 33, 3), np.nan, np.float32)
    Hh = np.zeros(n, np.float32)
    c = np.array(seed, np.float64)
    v = np.zeros(2)
    miss = 0
    for i, fr in read_frames(video):
        if i >= n:
            break
        fh, fw = fr.shape[:2]
        pred = c + v
        h = max(40.0, kh * (pred[1] - horizon))
        Hh[i] = h
        side = h * 2.4 * (1.15 ** min(miss, 6))
        x0, y0 = int(round(pred[0] - side / 2)), int(round(pred[1] - side * 0.55))
        s = int(round(side))
        crop = np.zeros((s, s, 3), np.uint8)
        sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(fw, x0 + s), min(fh, y0 + s)
        if sx1 > sx0 and sy1 > sy0:
            crop[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = fr[sy0:sy1, sx0:sx1]
        scale = 768.0 / s
        crop = cv2.resize(crop, (768, 768), interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
        res = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))
        best, bd = None, 1e9
        for k, pl in enumerate(res.pose_landmarks):
            pts = np.array([[p.x * s + x0, p.y * s + y0, p.visibility] for p in pl])
            hip = pts[[23, 24], :2].mean(0)
            d = np.hypot(*(hip - pred))
            if d < bd:
                best, bd = (pts, k), d
        if best is not None and bd < 0.35 * h * (1 + 0.25 * min(miss, 4)):
            pts, k = best
            L[i] = pts
            Wd[i] = np.array([[p.x, p.y, p.z] for p in res.pose_world_landmarks[k]])
            hip = pts[[23, 24], :2].mean(0)
            v = 0.5 * (hip - c) / (miss + 1) + 0.5 * v
            c = hip
            miss = 0
        else:
            miss += 1
            c = pred
            v *= 0.8
        if i % 150 == 0:
            print(f"P{pid + 1} frame {i}: hip=({c[0]:.0f},{c[1]:.0f}) h={h:.0f} miss={miss}", flush=True)
    det.close()
    return pid, L, Wd, Hh


def fill_smooth(A, sigma=1.6):
    """Linear gap fill then Gaussian along time, per coordinate."""
    A = A.copy()
    n = A.shape[0]
    t = np.arange(n)
    flat = A.reshape(n, -1)
    for j in range(flat.shape[1]):
        col = flat[:, j]
        ok = ~np.isnan(col)
        if ok.sum() == 0:
            continue
        col[~ok] = np.interp(t[~ok], t[ok], col[ok])
        flat[:, j] = gaussian_filter1d(col, sigma, mode="nearest")
    return flat.reshape(A.shape)


def cmd_track(a):
    court = load(a.court)
    seeds = [[float(v) for v in p.split(",")] for p in a.seeds.split()]
    n = frame_count(a.video)
    jobs = [(k, a.video, seeds[k], court["horizon_y"], a.model, a.kh, n) for k in range(len(seeds))]
    with mproc.get_context("spawn").Pool(min(a.jobs, len(jobs))) as pool:
        out = sorted(pool.map(track_one, jobs), key=lambda r: r[0])
    P = len(out)
    raw = np.stack([o[1] for o in out])
    world = np.stack([o[2] for o in out])
    hh = np.stack([o[3] for o in out])
    ok = ~np.isnan(raw[..., 0, 0])
    lm = np.stack([fill_smooth(raw[p]) for p in range(P)])
    wd = np.stack([fill_smooth(world[p]) for p in range(P)])
    np.savez_compressed(a.out, lm=lm, world=wd, ok=ok, h=hh, raw=raw)
    for p in range(P):
        print(f"P{p + 1}: detected in {ok[p].sum()}/{n} frames ({100 * ok[p].mean():.0f}%)")
    # identity check: two players on the same body
    hips = lm[:, :, [23, 24], :2].mean(2)
    for p in range(P):
        for q in range(p + 1, P):
            d = np.hypot(*(hips[p] - hips[q]).T)
            close = d < 0.15 * hh[p].clip(40)
            if close.sum() > 5:
                print(f"!! P{p + 1} and P{q + 1} share a body in {close.sum()} frames, e.g. {np.where(close)[0][:8]}")


def draw_skel(img, pts, col, th=2):
    for i, j in EDGES:
        p, q = pts[i], pts[j]
        if np.isnan(p[0]) or np.isnan(q[0]):
            continue
        cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), col, th, cv2.LINE_AA)


def cmd_check(a):
    d = np.load(a.pose)
    lm = d["lm"]
    tiles = []
    for i, fr in read_frames(a.video, step=a.every):
        if i >= lm.shape[1]:
            break
        for p in range(lm.shape[0]):
            draw_skel(fr, lm[p, i], COLS[p % 4], 3)
            hp = lm[p, i, [23, 24], :2].mean(0)
            cv2.putText(fr, f"P{p + 1}", (int(hp[0]) + 10, int(hp[1])), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        COLS[p % 4], 2)
        cv2.putText(fr, str(i), (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        tiles.append(cv2.resize(fr, (640, int(640 * fr.shape[0] / fr.shape[1]))))
    cols = 3
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[r:r + cols]) for r in range(0, len(tiles), cols)]
    cv2.imwrite(a.out, np.vstack(rows))
    print("->", a.out, f"({len(tiles)} tiles)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("track")
    t.add_argument("video"); t.add_argument("court"); t.add_argument("out")
    t.add_argument("--seeds", required=True); t.add_argument("--model", required=True)
    t.add_argument("--kh", type=float, default=0.42); t.add_argument("--jobs", type=int, default=4)
    c = sub.add_parser("check")
    c.add_argument("video"); c.add_argument("pose"); c.add_argument("out")
    c.add_argument("--every", type=int, default=45)
    a = ap.parse_args()
    {"track": cmd_track, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
