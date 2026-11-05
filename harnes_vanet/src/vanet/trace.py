"""Mobility traces: SUMO FCD output -> numpy arrays, plus a synthetic grid
generator used only for testing the pipeline when SUMO is not available.

Trace format (.npz): pos (T,N,2) metres, vel (T,N,2) m/s, dt seconds.
"""
import xml.etree.ElementTree as ET

import numpy as np


def save_trace(path, pos, vel, dt):
    np.savez_compressed(path, pos=pos, vel=vel, dt=dt)


def load_trace(path):
    z = np.load(path)
    return z["pos"], z["vel"], float(z["dt"])


def fcd_to_arrays(fcd_xml, t_start, t_end, dt=1.0):
    """Parse a SUMO --fcd-output file. Keeps only vehicles present at every
    step in [t_start, t_end]. SUMO angle: 0 = north, clockwise."""
    rec = {}
    last_t = None
    for _, el in ET.iterparse(fcd_xml, events=("end",)):
        if el.tag == "timestep":
            t = float(el.get("time"))
            last_t = t
            if t_start - 1e-9 <= t <= t_end + 1e-9:
                k = int(round((t - t_start) / dt))
                for v in el.findall("vehicle"):
                    a = np.radians(float(v.get("angle")))
                    s = float(v.get("speed"))
                    rec.setdefault(v.get("id"), {})[k] = (
                        float(v.get("x")), float(v.get("y")),
                        s * np.sin(a), s * np.cos(a))
            el.clear()
    T = int(round((t_end - t_start) / dt)) + 1
    ids = sorted(i for i, r in rec.items() if len(r) == T)
    if not ids:
        counts = sorted((len(r) for r in rec.values()), reverse=True)
        raise ValueError(
            f"no vehicle present for the whole window [{t_start}, {t_end}] ({T} steps). "
            f"FCD file: {len(rec)} vehicles seen in window, last timestep read = {last_t}, "
            f"best vehicle has {counts[0] if counts else 0}/{T} steps, "
            f"median {counts[len(counts)//2] if counts else 0}.")
    pos = np.zeros((T, len(ids), 2))
    vel = np.zeros((T, len(ids), 2))
    for j, i in enumerate(ids):
        for k in range(T):
            x, y, vx, vy = rec[i][k]
            pos[k, j] = (x, y)
            vel[k, j] = (vx, vy)
    return pos, vel


def write_fcd_xml(pos, vel, path, dt=1.0):
    """Write a SUMO-style FCD file from arrays (used to test the parser)."""
    T, N, _ = pos.shape
    with open(path, "w") as f:
        f.write('<fcd-export>\n')
        for t in range(T):
            f.write(f'  <timestep time="{t * dt:.2f}">\n')
            for i in range(N):
                vx, vy = vel[t, i]
                ang = np.degrees(np.arctan2(vx, vy)) % 360
                sp = float(np.hypot(vx, vy))
                f.write(f'    <vehicle id="v{i:04d}" x="{pos[t, i, 0]:.3f}" '
                        f'y="{pos[t, i, 1]:.3f}" angle="{ang:.2f}" '
                        f'speed="{sp:.3f}"/>\n')
            f.write('  </timestep>\n')
        f.write('</fcd-export>\n')


def synthetic_grid_trace(n, T, seed, grid=8, L=200.0, dt=1.0):
    """Manhattan-style mobility on a grid road network (testing only).
    Vehicles move along grid lines at 4-14 m/s and pick straight (60%),
    left (20%) or right (20%) at each junction; U-turn only at dead ends."""
    rng = np.random.default_rng(seed)
    dirs = np.array([(1, 0), (0, 1), (-1, 0), (0, -1)])

    def next_idx(coord, dr):
        c = coord / L
        return int(np.floor(c + 1e-9)) + 1 if dr > 0 else int(np.ceil(c - 1e-9)) - 1

    def valid(x, y, d):
        dx, dy = dirs[d]
        k = next_idx(x if dx != 0 else y, dx if dx != 0 else dy)
        return 0 <= k <= grid - 1

    x = np.zeros(n)
    y = np.zeros(n)
    d = np.zeros(n, dtype=int)
    for i in range(n):
        gx, gy = rng.integers(0, grid, 2)
        x[i], y[i] = gx * L, gy * L
        ok = [k for k in range(4) if valid(x[i], y[i], k)]
        d[i] = rng.choice(ok)
        off = rng.uniform(0, L * 0.99)
        x[i] += dirs[d[i]][0] * off
        y[i] += dirs[d[i]][1] * off
    speed = rng.uniform(8, 14, n)
    pos = np.zeros((T, n, 2))
    vel = np.zeros((T, n, 2))
    for t in range(T):
        speed = np.clip(speed + rng.normal(0, 0.3, n), 4, 14)
        for i in range(n):
            dist = speed[i] * dt
            while True:
                dx, dy = dirs[d[i]]
                cur = x[i] if dx != 0 else y[i]
                sgn = dx if dx != 0 else dy
                to_j = abs(next_idx(cur, sgn) * L - cur)
                if dist < to_j:
                    x[i] += dx * dist
                    y[i] += dy * dist
                    break
                x[i] += dx * to_j
                y[i] += dy * to_j
                dist -= to_j
                r = rng.random()
                pref = d[i] if r < 0.6 else ((d[i] + 1) % 4 if r < 0.8 else (d[i] + 3) % 4)
                if valid(x[i], y[i], pref):
                    d[i] = pref
                else:
                    ok = [k for k in range(4) if valid(x[i], y[i], k) and k != (d[i] + 2) % 4]
                    if not ok:
                        ok = [(d[i] + 2) % 4]
                    d[i] = rng.choice(ok)
            pos[t, i] = (x[i], y[i])
            vel[t, i] = dirs[d[i]] * speed[i]
    return pos, vel
