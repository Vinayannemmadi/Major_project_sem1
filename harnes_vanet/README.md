# HARNES baseline + cost-aware cluster maintenance (Semester 1)

Compares HARNES-style cluster-head election/re-clustering against our predictive,
cost-aware maintenance policy on SUMO grid-map mobility. Full design and the list of
paper gaps we filled: **docs/SPEC.md**.

## Setup (Ubuntu 24.04)

```bash
sudo apt update && sudo apt install -y sumo sumo-tools python3-venv
echo 'export SUMO_HOME=/usr/share/sumo' >> ~/.bashrc && source ~/.bashrc
cd harnes_vanet
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run order

```bash
# 0. sanity check (no SUMO needed): synthetic traces + all policies
python tests/smoke_test.py

# 1. ONE SUMO trace first, to verify your SUMO install and the script
python scripts/gen_sumo_traces.py --nodes 50 --seeds 1

# 2. all traces: N = 10..100, 10 seeds each  (~100 short SUMO runs)
python scripts/gen_sumo_traces.py

# 3. main experiment (keep --workers 1 so CPU timings are clean)
python run_experiments.py --source sumo --tag main
python analyze.py --tag main          # -> results/main/summary.md, comparison.png

# 4. baseline fairness: HARNES with 5/10/15/20/30 s re-clustering period, N = 60
python run_experiments.py --source sumo --set sweep --nodes 60 --tag sweep
python analyze.py --tag sweep

# 5. ablation at N = 60: which part of our method gives the gain
python run_experiments.py --source sumo --set ablation --nodes 60 --tag ablation
python analyze.py --tag ablation
```

## Live demo (for the presentation)

```bash
python demo_live.py                    # 50 cars; SUMO window shows OUR clusters
python demo_live.py --show harnes      # SUMO window shows HARNES clusters
python demo_live.py --nodes 80 --delay 50 --duration 120   # more cars, faster, shorter
```
**SUMO window** (clusters of the `--show` model): big disc with a black ring = cluster
head, small disc + line to its head = member (colour = its cluster), small grey disc = car
in no cluster. Drawn with TraCI polygons, visual only.
**Browser dashboard** (opens by itself; else go to http://127.0.0.1:8765): the clusters of
BOTH models on two maps side by side, live graphs (control messages, CH elections, link
breaks, CPU time) and, at the end, the comparison table. It is served by Python's built-in
web server, so no Qt/Tk is needed. Press Enter in the terminal to finish; until then the
dashboard and the SUMO window stay open.
Saved in `results/demo/`: `summary.md`, `dashboard_final.png`, `live_chart.png`,
`timeseries.csv`. The demo gives the same results as the batch experiment for the same
`--nodes/--seed` (checked by `tests/test_demo_logic.py`).

## Where SUMO is used

| Step | SUMO tool | Input | Output |
|---|---|---|---|
| road network | `netgenerate` | grid size, spacing, speed (config.yaml) | `grid.net.xml` |
| traffic | our route generator (sumolib) | network, N, seed | `*.rou.xml` (cars + routes) |
| batch simulation | `sumo` (no window) | net + routes | FCD trace (x, y, speed, angle per car per second) -> `traces/sumo/*.npz` |
| live demo | `sumo-gui` + **TraCI** | `results/demo/_scenario/demo.sumocfg` | live positions every second; we colour the cars |

To just watch the traffic: `sumo-gui -c results/demo/_scenario/demo.sumocfg` (after one demo run).
The base paper used MATLAB for its routing/analysis; we do that part in Python
(numpy, networkx), which also talks to SUMO directly through TraCI.

`--source synthetic` runs the same pipeline on built-in Manhattan-style traces
(used only to validate the code; do not report those numbers as results).

## Layout

| Path | Purpose |
|---|---|
| `config.yaml` | every parameter, marked (paper) or (ours) |
| `src/vanet/link_model.py` | link survival prediction S_ij(tau), kinematic lifetime L_ij, predictor quality |
| `src/vanet/clustering.py` | betweenness centrality, greedy cluster formation, composite score |
| `src/vanet/policies.py` | periodic (HARNES baseline) and costaware (ours) |
| `src/vanet/simulator.py` | runs a policy over a trace, collects metrics |
| `scripts/gen_sumo_traces.py` | SUMO grid map -> constant-N traces |
| `run_experiments.py`, `analyze.py` | experiments, statistics, plots (`tradeoff.png` for the sweep) |
| `demo_live.py` | live SUMO-GUI demo, both models on the same cars |
| `src/vanet/web_dashboard.py`, `dashboard.html` | live browser dashboard for the demo |

## Tuning rule

Do any parameter tuning with `--seed-offset 1000` (seeds 1000+). Never tune on the
seeds used for the reported results.
