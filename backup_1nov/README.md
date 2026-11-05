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

# 4. ablation at N = 60
python run_experiments.py --source sumo --ablation --nodes 60 --tag ablation
python analyze.py --tag ablation
```

`--source synthetic` runs the same pipeline on built-in Manhattan-style traces
(used only to validate the code; do not report those numbers as results).

## Layout

| Path | Purpose |
|---|---|
| `config.yaml` | every parameter, marked (paper) or (ours) |
| `src/vanet/link_model.py` | link survival prediction S_ij(tau), kinematic lifetime L_ij, predictor quality |
| `src/vanet/clustering.py` | betweenness centrality, greedy cluster formation, composite score |
| `src/vanet/policies.py` | periodic / eager (HARNES-style) and costaware (ours) |
| `src/vanet/simulator.py` | runs a policy over a trace, collects metrics |
| `scripts/gen_sumo_traces.py` | SUMO grid map -> constant-N traces |
| `run_experiments.py`, `analyze.py` | experiments, statistics, plots |

## Tuning rule

Do any parameter tuning with `--seed-offset 1000` (seeds 1000+). Never tune on the
seeds used for the reported results.
