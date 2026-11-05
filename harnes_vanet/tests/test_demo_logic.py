"""Checks demo_live.py without SUMO: a fake TraCI replays a synthetic trace, and the
demo's results must equal the batch simulator's on the same trace (except CPU time).
Run from project root:  python tests/test_demo_logic.py"""
import os
import sys
import types

import numpy as np
import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, ROOT)
from vanet.link_model import precompute        # noqa: E402
from vanet.simulator import simulate           # noqa: E402
from vanet.trace import synthetic_grid_trace   # noqa: E402
import demo_live                               # noqa: E402

N, WARM, DUR = 40, 20, 120
pos, vel = synthetic_grid_trace(N, WARM + DUR + 3, seed=7)
ids = [f"v{i:04d}" for i in range(N)]


def make_fake_traci():
    st = {"t": 0, "colors": {}, "pois": {}}
    tr = types.SimpleNamespace()
    tr.simulationStep = lambda: st.__setitem__("t", st["t"] + 1)
    tr.close = lambda wait=True: None
    tr.simulation = types.SimpleNamespace(getTime=lambda: float(st["t"]),
                                          getNetBoundary=lambda: ((0, 0), (1400, 1400)))
    i_of = {v: i for i, v in enumerate(ids)}

    def ang(v):
        vx, vy = vel[st["t"], i_of[v]]
        return float(np.degrees(np.arctan2(vx, vy)) % 360)
    tr.vehicle = types.SimpleNamespace(
        getIDList=lambda: list(ids),
        getPosition=lambda v: tuple(pos[st["t"], i_of[v]]),
        getSpeed=lambda v: float(np.hypot(*vel[st["t"], i_of[v]])),
        getAngle=ang,
        setColor=lambda v, c: st["colors"].__setitem__(v, c))
    tr.poi = types.SimpleNamespace(
        add=lambda pid, x, y, c, **kw: st["pois"].__setitem__(pid, (x, y)),
        setPosition=lambda pid, x, y: st["pois"].__setitem__(pid, (x, y)),
        remove=lambda pid: st["pois"].pop(pid))
    st["polys"] = {}
    tr.polygon = types.SimpleNamespace(
        add=lambda pid, shape, color, *a: st["polys"].__setitem__(pid, [shape, color]),
        setShape=lambda pid, shape: st["polys"][pid].__setitem__(0, shape),
        setColor=lambda pid, color: st["polys"][pid].__setitem__(1, color))
    tr.gui = types.SimpleNamespace(setBoundary=lambda *a: None)
    return tr, st


tr, st = make_fake_traci()
args = demo_live.parse(["--nodes", str(N), "--warmup", str(WARM), "--duration", str(DUR),
                        "--no-wait", "--no-browser", "--tag", "_test_demo"])
args.nogui = False          # exercise the GUI code paths (markers) with the fake
res = demo_live.run(args, traci=tr, sumocfg="fake")

cfg = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
pre = precompute(pos[WARM:WARM + DUR + 1], vel[WARM:WARM + DUR + 1], cfg, cfg["step_s"])
skip = {"cpu_ms_per_step", "cpu_total_s", "wall_s", "policy"}
for key, pol in demo_live.MODELS.items():
    ref = simulate(pre, cfg, pol, cfg["step_s"])
    for m, v in ref.items():
        if m in skip:
            continue
        assert np.isclose(res[key][m], v), (key, m, res[key][m], v)
print("demo == batch simulator on the same trace: OK")

# SUMO overlay: one visible ring per CH, one visible line per member, every car coloured
head = res_head = None
cols = st["colors"]
assert len(cols) == N
polys = st["polys"]
rings = sum(1 for k, (sh, c) in polys.items() if k.startswith("R") and c[3] > 0)
lines = sum(1 for k, (sh, c) in polys.items() if k.startswith("L") and c[3] > 0)
discs = sum(1 for k in polys if k.startswith("D"))
assert discs == N and rings > 0 and lines > 0, (discs, rings, lines)
assert rings + lines <= N
print(f"overlay OK: {discs} discs, {rings} CH rings, {lines} member links")
assert os.path.exists(os.path.join(ROOT, "results", "_test_demo", "dashboard_final.png"))
import shutil
shutil.rmtree(os.path.join(ROOT, "results", "_test_demo"))
print("ALL OK")
