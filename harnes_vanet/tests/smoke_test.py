"""Smoke test: trace generation, FCD round-trip, link model, all policies.
Run from project root:  python tests/smoke_test.py"""
import os, sys, tempfile, time
import numpy as np, yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from vanet.trace import synthetic_grid_trace, write_fcd_xml, fcd_to_arrays
from vanet.link_model import precompute, prediction_quality
from vanet.simulator import simulate

cfg = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "..", "config.yaml")))
dt = cfg["step_s"]
T = 301
pos, vel = synthetic_grid_trace(50, T, seed=1)
side = (cfg["map"]["grid_number"] - 1) * cfg["map"]["grid_length_m"]
assert pos.min() >= -1e-6 and pos.max() <= side + 1e-6, "vehicles left the map"
sp = np.linalg.norm(vel, axis=2)
assert 3.9 <= sp.min() and sp.max() <= 14.1, "speed out of range"
step_len = np.linalg.norm(np.diff(pos, axis=0), axis=2)
assert step_len.max() <= 14.1 + 1e-6, "teleporting"
print("synthetic trace ok: max step %.1f m, speeds %.1f-%.1f" % (step_len.max(), sp.min(), sp.max()))

with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "fcd.xml")
    write_fcd_xml(pos, vel, f, dt)
    p2, v2 = fcd_to_arrays(f, 0, T - 1, dt)
    assert p2.shape == pos.shape and np.abs(p2 - pos).max() < 1e-2
    assert np.abs(v2 - vel).max() < 0.05
print("FCD xml round-trip ok")

pre = precompute(pos, vel, cfg, dt)
q = prediction_quality(pre, cfg)
print("prediction quality:", {k: round(v, 4) for k, v in q.items()})
assert q["brier_prob_model"] < q["brier_constant_rate"], "predictor no better than a constant"

for name in ["periodic", "costaware"]:
    t0 = time.time()
    r = simulate(pre, cfg, name, dt)
    print(f"{name:10s} elections/min={r['ch_elections_per_min']:.2f} tenure={r['avg_ch_tenure_s']:.1f}s "
          f"msgs/min={r['control_msgs_per_min']:.0f} bc_calls={r['bc_calls']} bc_nodes={r['bc_nodes_processed']} "
          f"cpu/step={r['cpu_ms_per_step']:.2f}ms unaff={r['unaffiliated_frac']:.2f} "
          f"clusters={r['avg_clusters']:.1f} size={r['avg_cluster_size']:.1f} ({time.time()-t0:.1f}s)")
print("ALL OK")
