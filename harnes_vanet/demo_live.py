#!/usr/bin/env python3
"""LIVE DEMO: SUMO traffic + HARNES clustering + our cost-aware clustering, side by side.

What happens
  1. Builds the SUMO scenario (grid road network + N cars with random routes) with the same
     generator and seeds as the batch experiments (scripts/gen_sumo_traces.py).
  2. Starts SUMO with its GUI and controls it second by second through TraCI
     (SUMO's "Traffic Control Interface": Python asks SUMO for every car's position,
     speed and heading each second).
  3. Every second BOTH clustering models run on exactly the same cars:
        HARNES = betweenness-centrality cluster heads, re-clustering every 10 s
        OURS   = predictive, cost-aware cluster maintenance
  4. SUMO window (clusters of the model chosen with --show):
        big disc + black ring = cluster head (CH)
        small disc + line to its CH = member (colour = its cluster)
        small grey disc = car in no cluster
  5. Browser dashboard (opens by itself at http://127.0.0.1:8765): the clusters of BOTH
     models on two maps side by side, live graphs of control messages, CH elections, forced
     re-joins and CPU time, and the final comparison table. Served by Python's built-in web
     server: no Qt/Tk needed.
  6. At the end: comparison table + dashboard snapshot saved to results/demo/.

Run (from the project folder, venv active):
  python demo_live.py                         # 50 cars, SUMO shows OUR clusters
  python demo_live.py --show harnes           # SUMO shows HARNES clusters instead
  python demo_live.py --nodes 80 --delay 50 --duration 120
  python demo_live.py --nogui --no-plot       # headless check (no windows)

Inputs to SUMO : results/demo/_scenario/grid.net.xml   (road network, from netgenerate)
                 results/demo/_scenario/routes.rou.xml (cars and their routes)
                 results/demo/_scenario/demo.sumocfg   (SUMO configuration; also opens on
                                                         its own: sumo-gui -c ...)
Outputs        : results/demo/summary.md, timeseries.csv, dashboard_final.png, live_chart.png
"""
import argparse
import os
import shutil
import sys
import time

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
sys.path.insert(0, os.path.join(HERE, "scripts"))
if os.environ.get("SUMO_HOME"):
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

from vanet.link_model import OnlineLinkModel   # noqa: E402
from vanet.policies import Ctx, make_policy    # noqa: E402
from vanet.simulator import summarize          # noqa: E402
from vanet.web_dashboard import WebDashboard   # noqa: E402

MODELS = {"harnes": "periodic", "ours": "costaware"}
NAMES = {"harnes": "HARNES (periodic 10 s)", "ours": "Ours (cost-aware)"}
LINE_COL = {"harnes": "#777777", "ours": "#2b6cb0"}
# 12 clearly different colours; red is avoided so nothing looks like an error
PALETTE = [(31, 119, 180), (44, 160, 44), (255, 127, 14), (148, 103, 189), (23, 190, 207),
           (140, 86, 75), (227, 119, 194), (188, 189, 34), (0, 128, 128), (90, 60, 200),
           (255, 190, 0), (110, 110, 30)]
GREY = (160, 160, 160)
BLACK = (0, 0, 0)
R_CH, R_MEMBER, R_FREE = 26.0, 13.0, 9.0      # disc radii in metres (map is 1.4 km wide)


def cluster_rgb(h):
    return GREY if h < 0 else PALETTE[h % len(PALETTE)]


def circle(x, y, r, n=16):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return [(float(x + r * np.cos(t)), float(y + r * np.sin(t))) for t in a]


# ----------------------------------------------------------------- scenario
def build_scenario(cfg, n, seed, out_dir, end_s):
    """Writes net, routes and a .sumocfg. Same generator and seeds as the batch traces,
    so --nodes N --seed S drives the same traffic as traces/sumo/N{N}_s{S}.npz."""
    import sumolib
    from gen_sumo_traces import make_net, make_routes
    os.makedirs(out_dir, exist_ok=True)
    netfile = make_net(cfg, out_dir)
    rou = os.path.join(out_dir, "routes.rou.xml")
    make_routes(sumolib.net.readNet(netfile), n, 1000 * n + seed, rou)
    sumocfg = os.path.join(out_dir, "demo.sumocfg")
    with open(sumocfg, "w") as f:
        f.write(f"""<configuration>
    <input>
        <net-file value="{os.path.basename(netfile)}"/>
        <route-files value="{os.path.basename(rou)}"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="{end_s}"/>
        <step-length value="{cfg['step_s']}"/>
    </time>
    <processing>
        <time-to-teleport value="-1"/>
    </processing>
    <random_number>
        <seed value="{seed}"/>
    </random_number>
    <report>
        <no-step-log value="true"/>
        <no-warnings value="true"/>
    </report>
</configuration>
""")
    return sumocfg, netfile


def road_segments(netfile):
    """Road centre lines for the dashboard maps."""
    try:
        import sumolib
        net = sumolib.net.readNet(netfile)
        return [e.getShape() for e in net.getEdges()]
    except Exception:
        return None


# ----------------------------------------------------------------- dashboard
class Snapshot:
    """Off-screen matplotlib version of the dashboard (Agg backend: never opens a window,
    so it cannot crash on desktop-toolkit problems). Saves dashboard_final.png."""

    def __init__(self, roads=None, title=""):
        import matplotlib
        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        self.plt, self.LC = plt, LineCollection
        self.interactive = False
        self.fig = plt.figure(figsize=(15, 9))
        gs = self.fig.add_gridspec(3, 4, height_ratios=[1, 1, 0.75], hspace=0.45, wspace=0.3)
        self.map_ax = {"harnes": self.fig.add_subplot(gs[0:2, 0:2]),
                       "ours": self.fig.add_subplot(gs[0:2, 2:4])}
        self.ts_ax = [self.fig.add_subplot(gs[2, i]) for i in range(4)]
        self.title = title
        self.roads = roads
        self.state = None
        self.art = {}
        for k, ax in self.map_ax.items():
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
            if roads:
                ax.add_collection(LineCollection(roads, colors="#d0d0d0", linewidths=2, zorder=0))
            links = LineCollection([], linewidths=1.6, zorder=1)
            ax.add_collection(links)
            free = ax.scatter([], [], s=28, c="#a0a0a0", edgecolors="none", zorder=2)
            mem = ax.scatter([], [], s=70, edgecolors="white", linewidths=0.6, zorder=3)
            chs = ax.scatter([], [], s=330, marker="*", edgecolors="black", linewidths=1.2, zorder=4)
            self.art[k] = (links, free, mem, chs)
        self.ts_titles = ["Control messages", "CH elections", "Forced re-joins", "CPU time (ms)"]
        self.ts_keys = ["msgs", "elections", "rejoins", "cpu_ms"]
        self.ts_lines = {}
        for ax, ttl in zip(self.ts_ax, self.ts_titles):
            ax.set_title(ttl + " (cumulative)", fontsize=9)
            ax.set_xlabel("time (s)", fontsize=8)
            ax.tick_params(labelsize=8)
            ax.grid(alpha=.3)
            for k in MODELS:
                self.ts_lines[(ttl, k)], = ax.plot([], [], color=LINE_COL[k], lw=2, label=NAMES[k])
        self.ts_ax[0].legend(fontsize=7, loc="upper left")
        self.fig.text(0.5, 0.015, "★ cluster head (CH)     ● member, colour = its "
                      "cluster, line = link to its CH     ● grey = in no cluster",
                      ha="center", fontsize=10)

    def update(self, t, pos, heads, pols, ts):
        self.state = (t, pos.copy(), {k: h.copy() for k, h in heads.items()},
                      {k: (p.m["control_msgs"], p.m["ch_elections"], len(p.chs()))
                       for k, p in pols.items()}, ts)

    def _draw(self):
        t, pos, heads, nums, ts = self.state
        for k, ax in self.map_ax.items():
            head = heads[k]
            links, free, mem, chs = self.art[k]
            idx = np.arange(len(head))
            is_ch = head == idx
            is_mem = (head >= 0) & ~is_ch
            is_free = head < 0
            col = lambda ids: [tuple(c / 255 for c in cluster_rgb(head[i])) for i in ids]  # noqa: E731
            mi, ci = idx[is_mem], idx[is_ch]
            links.set_segments([[pos[i], pos[head[i]]] for i in mi])
            links.set_colors(col(mi))
            free.set_offsets(pos[is_free] if is_free.any() else np.empty((0, 2)))
            mem.set_offsets(pos[mi] if len(mi) else np.empty((0, 2)))
            mem.set_facecolors(col(mi))
            chs.set_offsets(pos[ci] if len(ci) else np.empty((0, 2)))
            chs.set_facecolors(col(ci))
            msgs, elec, ncl = nums[k]
            ax.set_title(f"{NAMES[k]}\n{ncl} clusters | {elec} CH elections | {msgs} control "
                         f"messages", fontsize=11, color=LINE_COL[k], fontweight="bold")
            if self.roads:
                pts = np.concatenate([np.asarray(r) for r in self.roads])
            else:
                pts = pos
            lo, hi = pts.min(0) - 60, pts.max(0) + 60
            ax.set_xlim(lo[0], hi[0])
            ax.set_ylim(lo[1], hi[1])
        for ax, ttl, key in zip(self.ts_ax, self.ts_titles, self.ts_keys):
            for k in MODELS:
                self.ts_lines[(ttl, k)].set_data(ts["t"], ts[f"{k}_{key}"])
            ax.relim()
            ax.autoscale_view()
        self.fig.suptitle(f"{self.title}   |   t = {t:.0f} s", fontsize=13)

    def save(self, path):
        if self.state is None:
            return
        self._draw()
        self.fig.savefig(path, dpi=120)


def save_chart(ts, path):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    fig = Figure(figsize=(11, 7))
    FigureCanvasAgg(fig)
    axes = fig.subplots(2, 2)
    for ax, (c, ttl) in zip(axes.ravel(), [("msgs", "Control messages (cumulative)"),
                                           ("elections", "CH elections (cumulative)"),
                                           ("rejoins", "Forced re-joins (cumulative)"),
                                           ("cpu_ms", "Maintenance CPU (ms, cumulative)")]):
        for k in MODELS:
            ax.plot(ts["t"], ts[f"{k}_{c}"], color=LINE_COL[k], lw=2, label=NAMES[k])
        ax.set_title(ttl, fontsize=10)
        ax.set_xlabel("time (s)")
        ax.grid(alpha=.3)
    axes[0, 0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=140)


# ----------------------------------------------------------------- SUMO overlay
class SumoOverlay:
    """Draws the clusters into the SUMO window with polygons (visual only, they do not
    affect traffic): per car a disc, per CH a black ring, per member a line to its CH."""

    def __init__(self, traci, ids, enabled):
        self.tr, self.ids, self.ok = traci, ids, enabled
        self.prev = {}                    # i -> (role, colour) last drawn
        if not enabled:
            return
        try:
            for i in range(len(ids)):
                far = [(-1e4, -1e4), (-1e4 + 0.1, -1e4)]
                traci.polygon.add(f"L{i}", far, BLACK + (0,), False, "link", 10, 2.5)
                traci.polygon.add(f"D{i}", far + [(-1e4, -1e4 + 0.1)], GREY + (255,), True,
                                  "car", 11)
                traci.polygon.add(f"R{i}", far, BLACK + (0,), False, "ch", 12, 5)
        except Exception as e:
            print("NOTE: SUMO overlays disabled, cars are only coloured:", e)
            self.ok = False

    def paint(self, head, pos):
        tr = self.tr
        for i, vid in enumerate(self.ids):
            h = int(head[i])
            role = "free" if h < 0 else ("ch" if h == i else "mem")
            rgb = cluster_rgb(h)
            tr.vehicle.setColor(vid, rgb + (255,))
            if not self.ok:
                continue
            try:
                x, y = pos[i]
                r = R_CH if role == "ch" else (R_MEMBER if role == "mem" else R_FREE)
                tr.polygon.setShape(f"D{i}", circle(x, y, r))
                if self.prev.get(i) != (role, rgb):
                    tr.polygon.setColor(f"D{i}", rgb + (255,))
                    tr.polygon.setColor(f"L{i}", rgb + (255 if role == "mem" else 0,))
                    tr.polygon.setColor(f"R{i}", BLACK + (255 if role == "ch" else 0,))
                if role == "mem":
                    hx, hy = pos[h]
                    tr.polygon.setShape(f"L{i}", [(float(x), float(y)), (float(hx), float(hy))])
                elif self.prev.get(i, ("",))[0] == "mem":
                    tr.polygon.setShape(f"L{i}", [(-1e4, -1e4), (-1e4 + 0.1, -1e4)])
                if role == "ch":
                    ring = circle(x, y, R_CH + 4, 20)
                    tr.polygon.setShape(f"R{i}", ring + ring[:1])
                elif self.prev.get(i, ("",))[0] == "ch":
                    tr.polygon.setShape(f"R{i}", [(-1e4, -1e4), (-1e4 + 0.1, -1e4)])
                self.prev[i] = (role, rgb)
            except Exception as e:     # overlays are cosmetic; never stop the demo for them
                print("NOTE: SUMO overlays disabled, cars are only coloured:", e)
                self.ok = False


# ----------------------------------------------------------------- main loop
def run(args, traci=None, sumocfg=None):
    cfg = yaml.safe_load(open(os.path.join(HERE, "config.yaml")))
    dt, R, theta = cfg["step_s"], cfg["radio_range_m"], cfg["join_threshold"]
    warm = args.warmup if args.warmup is not None else cfg["warmup_s"]
    dur = args.duration if args.duration is not None else cfg["duration_s"]
    out = os.path.join(HERE, "results", args.tag)
    os.makedirs(out, exist_ok=True)

    roads = None
    if traci is None:
        import traci
    if sumocfg is None:
        binary = "sumo" if args.nogui else "sumo-gui"
        if not shutil.which(binary):
            sys.exit(f"'{binary}' not found. Install SUMO: sudo apt install sumo sumo-tools sumo-doc")
        sumocfg, netfile = build_scenario(cfg, args.nodes, args.seed,
                                          os.path.join(out, "_scenario"), warm + dur + 2 * dt)
        roads = road_segments(netfile)
        cmd = [binary, "-c", sumocfg]
        if not args.nogui:
            cmd += ["--start", "--delay", str(args.delay)]
            if args.quit_on_end:
                cmd += ["--quit-on-end"]
        print("starting SUMO (the 'Retrying' line below is normal while its window opens)")
        traci.start(cmd)
    gui = not args.nogui

    # ---- warm-up: let the cars spread over the map
    print(f"warm-up {warm:.0f} s ...", flush=True)
    while traci.simulation.getTime() < warm - 1e-9:
        traci.simulationStep()
    ids = sorted(traci.vehicle.getIDList())
    N = len(ids)
    if N != args.nodes:
        print(f"WARNING: wanted {args.nodes} cars, {N} are in the network")
    if gui:
        try:
            (x0, y0), (x1, y1) = traci.simulation.getNetBoundary()
            traci.gui.setBoundary("View #0", x0 - 60, y0 - 60, x1 + 60, y1 + 60)
        except Exception:
            pass

    link = OnlineLinkModel(N, cfg, dt)
    pols = {k: make_policy(v, N, cfg, dt) for k, v in MODELS.items()}
    overlay = SumoOverlay(traci, ids, gui and not args.plain)
    title = f"{N} cars, seed {args.seed}, radio range {R:.0f} m; SUMO window shows {NAMES[args.show]}"
    snap = Snapshot(roads, title)
    web = None
    if not args.no_plot:
        web = WebDashboard(args.port, open_browser=not args.no_browser)
        web.static = {"title": title, "t_end": dur,
                      "roads": [[list(map(float, p)) for p in r] for r in roads] if roads else []}

    def publish(t_now, done=False, summary=None):
        if web is None:
            return
        web.publish({"t": t_now, "done": done, "summary": summary,
                     "pos": [[float(x), float(y)] for x, y in pos],
                     "models": {k: {"head": [int(h) for h in p.head],
                                    "msgs": int(p.m["control_msgs"]),
                                    "elections": int(p.m["ch_elections"]),
                                    "rejoins": int(p.m["forced_rejoins"]),
                                    "clusters": len(p.chs())} for k, p in pols.items()},
                     "ts": {k: [float(v) for v in vals] for k, vals in ts.items()}})
    ts = {"t": []}
    for k in MODELS:
        for c in ("msgs", "elections", "rejoins", "cpu_ms", "clusters"):
            ts[f"{k}_{c}"] = []

    def read_state():
        pos = np.zeros((N, 2))
        vel = np.zeros((N, 2))
        for i, vid in enumerate(ids):
            pos[i] = traci.vehicle.getPosition(vid)
            a = np.radians(traci.vehicle.getAngle(vid))
            s = traci.vehicle.getSpeed(vid)
            vel[i] = (s * np.sin(a), s * np.cos(a))
        return pos, vel

    steps = int(round(dur / dt)) + 1
    print(f"running {dur:.0f} s with {N} cars; SUMO window shows: {NAMES[args.show]}", flush=True)
    t_wall = {k: 0.0 for k in MODELS}
    pos = None
    for t in range(steps):
        if t > 0:
            traci.simulationStep()
            if len(traci.vehicle.getIDList()) < N:
                print("A car left the network; stopping early.")
                steps = t
                break
        pos, vel = read_state()
        D, S, L = link.update(pos, vel)
        ctx = Ctx(t, D, S, L, R, theta)
        for k, p in pols.items():
            t0 = time.perf_counter()
            if t == 0:
                p.initial(ctx)
            else:
                p.timed_step(ctx)
            t_wall[k] += time.perf_counter() - t0
        overlay.paint(pols[args.show].head, pos)

        ts["t"].append(t * dt)
        for k, p in pols.items():
            ts[f"{k}_msgs"].append(p.m["control_msgs"])
            ts[f"{k}_elections"].append(p.m["ch_elections"])
            ts[f"{k}_rejoins"].append(p.m["forced_rejoins"])
            ts[f"{k}_cpu_ms"].append(1000 * p.m["cpu_s"])
            ts[f"{k}_clusters"].append(len(p.chs()))
        snap.update(t * dt, pos, {k: p.head for k, p in pols.items()}, pols, ts)
        if t % args.plot_every == 0:
            publish(t * dt)
        if t % 10 == 0:
            print(f"t={t * dt:5.0f}s | " + " | ".join(
                f"{NAMES[k]}: msgs={p.m['control_msgs']:5d} CH-elections={p.m['ch_elections']:4d} "
                f"clusters={len(p.chs()):2d}" for k, p in pols.items()), flush=True)
    try:
        traci.close(False)          # SUMO window stays open on the final state
    except TypeError:
        traci.close()

    # ---- results
    for p in pols.values():
        p.finish(steps - 1)
    res = {k: summarize(p, MODELS[k], N, steps, dt, t_wall[k]) for k, p in pols.items()}
    rows = [("CH elections / min", "ch_elections_per_min", True),
            ("Average CH tenure (s)", "avg_ch_tenure_s", False),
            ("Control messages / min", "control_msgs_per_min", True),
            ("Control share of all messages", "overhead_ratio", True),
            ("Forced re-joins / min", "forced_rejoins_per_min", True),
            ("Maintenance CPU (ms / step)", "cpu_ms_per_step", True),
            ("Unaffiliated vehicles (fraction)", "unaffiliated_frac", True),
            ("Average cluster size", "avg_cluster_size", None)]
    web_rows = []
    lines = [f"# Live demo: {N} cars, seed {args.seed}, {(steps - 1) * dt:.0f} s measured\n",
             f"| Metric | {NAMES['harnes']} | {NAMES['ours']} | Change |", "|---|---|---|---|"]
    for name, key, lower in rows:
        a, b = res["harnes"][key], res["ours"][key]
        chg = f"{100 * (b - a) / a:+.1f}%" if a else "n/a"
        mark = "" if lower is None else (" (better)" if (b < a) == lower else " (worse)")
        lines.append(f"| {name} | {a:.3f} | {b:.3f} | {chg}{mark} |")
        web_rows.append([name, f"{a:.3f}", f"{b:.3f}", chg + mark,
                         "" if lower is None else ("better" if (b < a) == lower else "worse")])
    lines.append("\nOne run (one seed): for the reported results use run_experiments.py "
                 "(10 seeds, confidence intervals).")
    txt = "\n".join(lines)
    print("\n" + txt)
    open(os.path.join(out, "summary.md"), "w").write(txt + "\n")
    import csv
    with open(os.path.join(out, "timeseries.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(list(ts))
        w.writerows(zip(*ts.values()))
    snap.save(os.path.join(out, "dashboard_final.png"))
    publish((steps - 1) * dt, done=True, summary=web_rows)
    save_chart(ts, os.path.join(out, "live_chart.png"))
    print("saved in", out + ": summary.md, timeseries.csv, dashboard_final.png, live_chart.png")
    if web is not None:
        if not args.no_wait:
            try:
                input(f"\nThe dashboard ({web.url}) and the SUMO window stay open. "
                      "Press Enter here to finish. ")
            except EOFError:
                pass
        web.close()
    return res


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nodes", type=int, default=50, help="number of cars")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--show", choices=["ours", "harnes"], default="ours",
                    help="whose clusters are drawn in the SUMO window")
    ap.add_argument("--delay", type=int, default=100, help="SUMO-GUI delay per step (ms)")
    ap.add_argument("--warmup", type=float, default=None)
    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--plot-every", type=int, default=1, help="update the dashboard every k steps")
    ap.add_argument("--port", type=int, default=8765, help="dashboard port (http://127.0.0.1:PORT)")
    ap.add_argument("--no-browser", action="store_true", help="do not open the browser automatically")
    ap.add_argument("--plain", action="store_true", help="no discs/lines in SUMO, only car colours")
    ap.add_argument("--quit-on-end", action="store_true", help="close SUMO window at the end")
    ap.add_argument("--nogui", action="store_true", help="run SUMO without its window")
    ap.add_argument("--no-plot", action="store_true", help="no live browser dashboard")
    ap.add_argument("--no-wait", action="store_true", help="exit at the end without waiting for Enter")
    ap.add_argument("--tag", default="demo")
    return ap.parse_args(argv)


if __name__ == "__main__":
    run(parse())
