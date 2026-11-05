#!/usr/bin/env python3
"""Generate SUMO grid-map mobility traces (constant vehicle count) for all (N, seed).

Needs: SUMO installed (sudo apt install sumo sumo-tools) and
       export SUMO_HOME=/usr/share/sumo

  python scripts/gen_sumo_traces.py                # N = 10..100, seeds from config.yaml
  python scripts/gen_sumo_traces.py --nodes 50 --seeds 1     # quick test

NOTE: written without access to a SUMO install, so first run it for ONE case
(--nodes 50 --seeds 1) and check the printed commands/errors.
"""
import argparse
import os
import random
import shutil
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
if os.environ.get("SUMO_HOME"):
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import sumolib  # noqa: E402
from vanet.trace import fcd_to_arrays, save_trace  # noqa: E402


def run(cmd):
    print("$", " ".join(cmd), flush=True)
    return subprocess.run(cmd, capture_output=True, text=True)


def make_net(cfg, out_dir):
    net = os.path.join(out_dir, "grid.net.xml")
    m = cfg["map"]
    base = ["netgenerate", "--grid", f"--grid.number={m['grid_number']}",
            f"--grid.length={m['grid_length_m']}", f"--default.speed={m['speed_mps']}",
            "--no-turnarounds", "true", "-o", net]
    # try to avoid traffic lights; fall back if this option is not accepted
    for extra in (["--default-junction-type", "priority"], []):
        r = run(base + extra)
        if r.returncode == 0:
            return net
        print(r.stderr)
    sys.exit("netgenerate failed")


def make_routes(net, n, seed, path, steps=120):
    rnd = random.Random(seed)
    edges = [e for e in net.getEdges() if e.allows("passenger")]
    with open(path, "w") as f:
        f.write('<routes>\n  <vType id="car" accel="2.6" decel="4.5" sigma="0.5" length="5" '
                'minGap="2.5" maxSpeed="13.89" speedFactor="normc(1,0.1,0.8,1.2)"/>\n')
        for i in range(n):
            cur = rnd.choice(edges)
            route = [cur]
            for _ in range(steps):
                outs = [o for o in cur.getOutgoing()
                        if o.allows("passenger") and o.getToNode() != cur.getFromNode()]
                if not outs:
                    break
                cur = rnd.choice(outs)
                route.append(cur)
            ids = " ".join(e.getID() for e in route)
            f.write(f'  <vehicle id="v{i:04d}" type="car" depart="0" departPos="random" '
                    f'departLane="best" departSpeed="random"><route edges="{ids}"/></vehicle>\n')
        f.write('</routes>\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", type=int, nargs="*", default=None)
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--seed-offset", type=int, default=0)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
    if not shutil.which("sumo"):
        sys.exit("sumo not found. Install: sudo apt install sumo sumo-tools; export SUMO_HOME=/usr/share/sumo")
    out = os.path.join(ROOT, "traces", "sumo")
    work = os.path.join(out, "_work")
    os.makedirs(work, exist_ok=True)
    netfile = make_net(cfg, work)
    net = sumolib.net.readNet(netfile)
    warm, dur, dt = cfg["warmup_s"], cfg["duration_s"], cfg["step_s"]
    for n in (args.nodes or cfg["node_counts"]):
        for s in range(args.seed_offset, args.seed_offset + (args.seeds or cfg["seeds"])):
            rou = os.path.join(work, f"routes_N{n}_s{s}.rou.xml")
            fcd = os.path.join(work, f"fcd_N{n}_s{s}.xml")
            make_routes(net, n, 1000 * n + s, rou)
            r = run(["sumo", "-n", netfile, "-r", rou, "--fcd-output", fcd,
                     "--begin", "0", "--end", str(warm + dur + 2 * dt), "--step-length", str(dt),
                     "--seed", str(s), "--no-step-log", "true", "--no-warnings", "true",
                     "--time-to-teleport", "-1"])
            if r.returncode != 0:
                print(r.stderr)
                sys.exit("sumo failed")
            pos, vel = fcd_to_arrays(fcd, warm, warm + dur, dt)
            if pos.shape[1] != n:
                print(f"  WARNING: wanted {n} vehicles for the full window, got {pos.shape[1]}")
            save_trace(os.path.join(out, f"N{n}_s{s}.npz"), pos, vel, dt)
            os.remove(fcd)
            print(f"  saved N{n}_s{s}.npz  ({pos.shape[1]} vehicles, {pos.shape[0]} steps)", flush=True)


if __name__ == "__main__":
    main()
