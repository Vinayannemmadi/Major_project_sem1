"""Run policies over many (N, seed) traces and write results/<tag>/runs.csv.

Examples
  python run_experiments.py --source synthetic --seeds 3 --tag test
  python run_experiments.py --source sumo --seeds 10 --tag main
  python run_experiments.py --source sumo --seeds 10 --ablation --nodes 60 --tag ablation
  python run_experiments.py --source sumo --period-sweep --tag period_sweep

--workers 1 (default) keeps CPU-time measurements clean; use more only for quick checks.
Use --seed-offset >= 1000 for any parameter tuning so evaluation seeds stay untouched.
"""
import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
from vanet.link_model import precompute, prediction_quality   # noqa: E402
from vanet.simulator import simulate                          # noqa: E402
from vanet.trace import load_trace, synthetic_grid_trace      # noqa: E402

MAIN = ["periodic", "eager", "costaware"]
ABLATION = {
    "costaware": {},
    "costaware_nohyst": {"hysteresis": 0.0, "dwell_s": 0},
    "costaware_nocost": {"gamma": 0.0},
    "costaware_noproactive": {"proactive_leave": 0.0},
    "costaware_naive": {"hysteresis": 0.0, "dwell_s": 0, "gamma": 0.0},
}
# Baseline fairness: periodic re-clustering with different periods vs our method
PERIOD_SWEEP = {f"periodic_{p}": {"period_s": p} for p in (5, 10, 20, 30)}
PERIOD_SWEEP["costaware"] = {}


def get_trace(args, cfg, n, seed):
    T = int(cfg["duration_s"] / cfg["step_s"]) + 1
    if args.source == "synthetic":
        m = cfg["map"]
        return synthetic_grid_trace(n, T, seed, m["grid_number"], m["grid_length_m"], cfg["step_s"])
    pos, vel, _ = load_trace(os.path.join(HERE, "traces", "sumo", f"N{n}_s{seed}.npz"))
    return pos, vel


def job(task):
    args, cfg, n, seed = task
    dt = cfg["step_s"]
    pos, vel = get_trace(args, cfg, n, seed)
    pre = precompute(pos, vel, cfg, dt)
    q = prediction_quality(pre, cfg)
    q.update(N=n, seed=seed)
    rows = []
    if args.ablation:
        variants = ABLATION
    elif args.period_sweep:
        variants = PERIOD_SWEEP
    else:
        variants = {p: {} for p in MAIN}
    for name, ov in variants.items():
        r = simulate(pre, cfg, name, dt, ov)
        r["seed"] = seed
        rows.append(r)
    return rows, q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["synthetic", "sumo"], default="sumo")
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--seed-offset", type=int, default=0)
    ap.add_argument("--nodes", type=int, nargs="*", default=None)
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--period-sweep", action="store_true")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--tag", default="main")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(os.path.join(HERE, "config.yaml")))
    nodes = args.nodes or cfg["node_counts"]
    seeds = range(args.seed_offset, args.seed_offset + (args.seeds or cfg["seeds"]))
    tasks = [(args, cfg, n, s) for n in nodes for s in seeds]
    out = os.path.join(HERE, "results", args.tag)
    os.makedirs(out, exist_ok=True)

    rows, quals = [], []
    if args.workers > 1:
        with ProcessPoolExecutor(args.workers) as ex:
            results = list(ex.map(job, tasks))
    else:
        results = []
        for i, t in enumerate(tasks, 1):
            results.append(job(t))
            print(f"[{i}/{len(tasks)}] N={t[2]} seed={t[3]} done", flush=True)
    for r, q in results:
        rows += r
        quals.append(q)
    pd.DataFrame(rows).to_csv(os.path.join(out, "runs.csv"), index=False)
    pd.DataFrame(quals).to_csv(os.path.join(out, "prediction_quality.csv"), index=False)
    print("wrote", out)


if __name__ == "__main__":
    main()
