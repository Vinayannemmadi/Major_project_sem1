"""Runs one policy over one precomputed mobility trace and returns metrics."""
import time

import numpy as np

from .policies import Ctx, make_policy


def simulate(pre, cfg, policy_name, dt, override=None):
    R = cfg["radio_range_m"]
    theta = cfg["join_threshold"]
    T, N = pre["T"], pre["N"]
    pol = make_policy(policy_name, N, cfg, dt, override)
    t_wall = time.perf_counter()
    pol.initial(Ctx(0, pre["D"][0], pre["S"][0], pre["L"][0], R, theta))
    for t in range(1, T):
        ctx = Ctx(t, pre["D"][t], pre["S"][t], pre["L"][t], R, theta)
        pol.timed_step(ctx)
    pol.finish(T - 1)
    wall = time.perf_counter() - t_wall
    return summarize(pol, policy_name, N, T, dt, wall)


def summarize(pol, policy_name, N, T, dt, wall):
    """Metrics of a finished policy run over T steps (T-1 maintenance steps)."""
    m = pol.m
    minutes = (T - 1) * dt / 60.0
    steps = max(1, m["steps"])
    ten = np.array(m["tenures"]) * dt if m["tenures"] else np.array([0.0])
    beacons = N * (T - 1)                      # one beacon per vehicle per step, all policies
    ctrl = m["control_msgs"]
    return {
        "policy": policy_name, "N": N,
        # stability
        "ch_elections_per_min": m["ch_elections"] / minutes,
        "handovers_per_min": m["handovers"] / minutes,
        "full_reclusters": m["full_reclusters"],
        "avg_ch_tenure_s": float(ten.mean()),
        "affil_switches_per_min": m["affil_switches"] / minutes,
        "forced_rejoins_per_min": m["forced_rejoins"] / minutes,
        # overhead
        "control_msgs_per_min": ctrl / minutes,
        "control_msgs_total": ctrl,
        "beacons_total": beacons,
        "overhead_ratio": ctrl / (ctrl + beacons),
        # compute
        "bc_calls": m["bc_calls"],
        "bc_nodes_processed": m["bc_nodes"],
        "cpu_ms_per_step": 1000 * m["cpu_s"] / (T - 1),
        "cpu_total_s": m["cpu_s"],
        "wall_s": wall,
        # sanity / cluster quality
        "unaffiliated_frac": m["iso_sum"] / steps,
        "avg_clusters": m["clusters_sum"] / steps,
        "avg_cluster_size": m["size_sum"] / steps,
        "merges": m["merges"],
    }
