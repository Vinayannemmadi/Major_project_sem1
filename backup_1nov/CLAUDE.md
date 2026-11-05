# CLAUDE.md: full project context (handoff from a previous Claude chat)

Read this file completely before doing anything. It records everything decided and built
so far in an earlier conversation, so you don't need to re-derive it. When the code and
this file disagree, the code on disk is the truth. Tell the user about the mismatch.

---

## 0. Who / what / when

- **User:** Computer Science student. This is their **major project** (2 semesters). Solo:
  only the user and Claude work on it. They report to an academic **guide** (supervisor).
- **Deadline:** the user has **7–10 days** (from 31 Oct 2026) to implement Semester 1 and
  report to the guide. Treat time as the hard constraint: prefer simple, finished and
  honest over ambitious and half done.
- **Machine:** HP Elite Tower 600 G9, **Ubuntu 24.04**, 32 GB RAM, 512 GB SSD. VS Code.
  Project path: `~/Desktop/Major Project/harnes_vanet` (**the path contains a space**, so
  always quote paths in shell commands). Python venv at `venv/` (activate:
  `source venv/bin/activate`). SUMO is installed and works (`sumo`, `netgenerate` on PATH,
  `SUMO_HOME=/usr/share/sumo`).
- **Simulator decision (user's):** use **SUMO** now and for the whole project. A real map
  (city/OSM) is "future days", **not now**.
- **Parameter decision (user's):** "use the same parameters and values as the base paper;
  go for alternatives only if they don't work." The paper omits most values, so the gaps
  were filled with our own choices (see §5). Keep the paper-like grid map for now.

## 1. Base paper (in this folder or attached as PDF)

"HARNES: Heuristic Algorithm for Routing and Network Efficiency Using SDN in Intelligent
Transportation Systems", IEEE Journal, 2026.

Summary:
- Vehicular network (VANET/IoV) with SDN controllers in 5G RSUs. Three-tier controller
  hierarchy: **FEC** (Foundational Edge Controller: vehicle layer, info exchange, topology,
  cluster formation, CH selection), **LEC** (Local Edge Controller: zone, intra-cluster and
  local inter-cluster routing), **GEC** (Global Edge Controller: network-wide, used only if
  the destination is outside the local zone).
- Three communication types: intra-cluster, local inter-cluster (same RSU), global
  inter-cluster (via GEC).
- **Link reliability model:** link duration `D_l = T_R / Δv` (T_R = transmission range,
  Δv = relative velocity); Δv ~ Normal(μ_Δv, σ_Δv); pdf of communication duration
  `g(T) = T_R / (σ√(2π) T²) · exp(-(T_R/T − μ)² / (2σ²))`; reliability
  `R_l(t) = ∫_t^{t+D_l} g(T) dT` if D_l > 0.
- **Eq.1/Eq.2:** reliable path = argmax over paths found by D\*-Lite / Theta\* of the
  **sum** of link reliabilities.
- **Eq.3 Betweenness Centrality** (cluster-head selection):
  `BC(v) = Σ_{s≠t, v∉{s,t}} σ_st(v)/σ_st` over "reliability-weighted shortest paths".
- **Eq.4 cluster formation:** each vehicle joins the head with the most reliable path to it.
- **Eq.5 D\*-Lite update:** `min_{s'∈Succ(s)} (c(s,s') + g(s'))`. **Eq.6 LOS:** true if no
  obstacle between s and s'. **Eq.7 grid:** `rows = ⌊√n⌋, cols = ⌈n/rows⌉`.
- Algorithms 1–6: D\*-Lite and Theta\* at intra-cluster, LEC inter-cluster and GEC levels.
- Simulation: SUMO traces + MATLAB; 2-D 8-connected grid; n = 10..100 step 10; source
  top-left, goal bottom-right; 2×2 quadrant clusters, one CH each; Euclidean cost, hop count
  path length. Metrics: Computation Time (CT, *modelled*, not measured), Discovery Messages
  (DM = neighbour evaluations), Path Length (PL), Expanded Nodes (EX), Average Degree (AD),
  Path Optimality Ratio (POR = Dijkstra length / algorithm length).
- Claimed results: cluster Theta\* up to 42% faster than A\*, 88% fewer DM and 47% fewer
  expanded nodes than EG-Dijkstra, POR within ~3.1% of optimal. Table 3 (avg CT ms / DM /
  EX): Theta\* 16.39/54.5/7.6; cluster Theta\* 14.95/53.7/6.7; D\*-Lite 23.05/77.8/11.0;
  cluster D\*-Lite 16.05/56.1/7.0.
- **The paper's own stated gap (our motivation):** clustering has coordination overhead,
  and **re-clustering frequency / CH sensitivity under high mobility is left as future
  work**. Our project targets exactly this.

Weaknesses already identified (useful for the report): CT is modelled, not measured; the
headline % use different baselines; an artificial obstacle-free grid flatters Theta\*;
Fig.5 (Theta\* shorter) vs POR<1 (Theta\* longer) is inconsistent; clustering overhead is
excluded from the savings; link-reliability equations are defined but the simulation uses
Euclidean cost.

## 2. The user's project

**Title:** "Predictive and Adaptive Routing with Cost-Aware Cluster Maintenance in
SDN-Enabled Vehicular Ad Hoc Networks"

**Problem statement:** design and develop an SDN framework to improve the stability and
efficiency of routing in highly dynamic VANETs, addressing frequent route and cluster changes
caused by vehicle mobility, while minimizing the overhead of unnecessary Cluster Head
switching and re-clustering.

**Objectives:**
1. Understand the baseline SDN-VANET routing framework.
2. Design and develop a predictive Stability-Aware Clustering algorithm with Cost-Aware
   Cluster Maintenance.
3. Extend the clustering algorithm to predict link and route stability for optimal route
   selection and maintenance.
4. Evaluate the framework under dynamic VANET conditions.

**Semester split (user's decision):**
- **Semester 1 (now, 7 days):** implement the base paper's cluster layer plus cost-aware
  clustering with predictive lifetimes and probabilities. Compare baseline vs ours on how
  much **time, CPU usage, number of messages, network overhead etc.** our re-clustering
  decision model reduces.
- **Semester 2:** routing (Theta\*, D\*-Lite, A\*, EG-Dijkstra on the clusters), route
  stability prediction, full comparison. Possibly real map, obstacles/LOS, packet-level
  (Veins/ns-3).

**Assumption still to confirm with the guide:** "implement the base paper" in Semester 1
means the **cluster layer** (link model, BC CH election, cluster formation). The routing
algorithms are Semester 2. If the guide wants routing now, it's extra work.

Advice already given to the user (keep consistent): reword Objective 1 as "reproduce the
baseline and quantify its CH-change / re-clustering behaviour"; treat prediction as a
separate module that clustering and routing both use; route stability = product (or min)
of link survivals, **not sum**; account for net overhead including our own method's cost.

## 3. What is built (all in this folder)

```
config.yaml                 every parameter, marked (paper) or (ours)
requirements.txt            numpy scipy pandas networkx matplotlib pyyaml tabulate
README.md                   setup + run order
docs/SPEC.md                spec for the guide: scope, params, models, policies,
                            metrics, paper gaps, limitations, 7-day plan
src/vanet/trace.py          SUMO FCD XML -> numpy (pos, vel); synthetic Manhattan
                            generator (testing only); FCD writer (tests)
src/vanet/link_model.py     precompute D, S_ij(tau), L_ij, online sigma; predictor quality
src/vanet/clustering.py     bc_scores (Eq.3), greedy_form (Eq.4), composite_scores (ours)
src/vanet/policies.py       Base, Periodic, Eager (baselines), CostAware (ours)
src/vanet/simulator.py      runs one policy over one trace, returns metrics dict
scripts/gen_sumo_traces.py  netgenerate grid + random routes + sumo -> traces/sumo/N{n}_s{seed}.npz
run_experiments.py          policies x (N, seed) -> results/<tag>/runs.csv, prediction_quality.csv
analyze.py                  pooled table, paired t-tests, 95% CI plots -> summary.md, comparison.png
tests/smoke_test.py         end-to-end check on synthetic traces (no SUMO needed)
```

### 3.1 Pipeline
SUMO grid → FCD trace (x, y, speed, angle per vehicle per second) → numpy pos/vel (T, N, 2)
→ `link_model.precompute` (shared by all policies, so the comparison is fair) → each policy
maintains clusters every 1 s step → metrics. SDN controllers (FEC/LEC/GEC) are **logical**:
the policy object plays the zone controller, as in the paper (also simulated logic there).

### 3.2 SUMO trace generation (`scripts/gen_sumo_traces.py`)
- `netgenerate --grid --grid.number=8 --grid.length=200 --default.speed=13.89
  --no-turnarounds true --default-junction-type priority` (falls back without junction type).
- Routes: N vehicles, all `depart="0"`, `departPos="random"`, each a random walk of ~120
  edges (no immediate U-turn) so vehicles stay in the network for the whole run.
  vType car: accel 2.6, decel 4.5, sigma 0.5, maxSpeed 13.89, speedFactor normc(1,0.1,0.8,1.2).
  Route RNG seed = 1000*N + seed; SUMO `--seed seed`.
- SUMO run: `--begin 0 --end warmup+duration+2*dt` (= 362 s; the +2 s margin fixed a bug
  where SUMO didn't write the last step and the parser found "no vehicle present for the
  whole window"), `--time-to-teleport -1`, step 1 s.
- Keeps window [60, 360] s = 301 steps; only vehicles present for every step are kept; warns
  if fewer than N. Saves `traces/sumo/N{n}_s{seed}.npz`, deletes the big FCD XML.
- FCD angle convention: 0 = north, clockwise → vx = s·sin(a), vy = s·cos(a).
- `fcd_to_arrays` raises a diagnostic error (vehicles seen, last timestep, best/median
  coverage) if no vehicle covers the window.

### 3.3 Link model (`link_model.py`), our extension of the paper's Gaussian idea
- Predicted distance at horizon τ: `d̂ = |Δp + Δv·τ|` (constant relative velocity).
  Distance is convex in time, so in range now and at τ ⇒ in range throughout.
- **Survival probability** `S_ij(τ) = Φ((R − d̂) / σ_p)`; S = 0 if currently out of range.
- σ_p = online std of the predictor's *actual* errors made τ seconds ago, over a 60 s
  window, causal, floor 5 m, initial 30 m until ≥30 samples. (σ_p ≈ σ_Δv·τ: the paper's
  velocity-noise term.) Handles passing vehicles, which a relative-speed-only formula doesn't.
- **Kinematic lifetime** L_ij = positive root of `|Δp+Δv t|² = R²`, clipped to [0, L_max=60].
- `prediction_quality`: Brier score of S vs actual survival over τ, a constant-rate
  baseline Brier score, accuracy at 0.5, and kinematic accuracy.

### 3.4 Clustering primitives (`clustering.py`)
- `bc_scores`: networkx betweenness (normalized) on the in-range sub-graph with edge weight
  `1 + λ(−ln S)`, λ = 1. Defines the paper's undefined "reliability-weighted shortest path".
- `greedy_form`: highest score becomes CH and absorbs unassigned neighbours with
  `S ≥ θ = 0.6` (1-hop clusters). Vehicles with no reliable neighbour stay unaffiliated.
- `composite_scores` (ours): `0.3·BC~ + 0.5·mean S_vj + 0.2·mean min(L_vj/L_max, 1)`.

### 3.5 Policies (`policies.py`)
**Shared local maintenance for all policies** (`local_repair`): a member whose link to its
CH broke, or whose CH is no longer CH, becomes unaffiliated (counted as **forced re-join**).
Unaffiliated vehicles rejoin the best reachable CH. Remaining unaffiliated vehicles form
local clusters (greedy, local scoring). Two CHs in range for ≥5 s **merge** (the smaller
cluster resigns; ties broken by id). A "CH" with fewer than 2 members is normalized away.

- **`periodic`** (HARNES-style baseline 1): local repair each step + full BC re-clustering
  every 10 s (`period_s`).
- **`eager`** (HARNES-style baseline 2, "highest BC is CH"): local repair + full BC every
  step; if any member has higher BC than its CH → handover immediately (no hysteresis, no
  cost check).
- **`costaware`** (OURS), each step after local repair:
  0. **Proactive re-affiliation:** a member with S(to CH) < `proactive_leave = 0.3` moves to
     a better reachable CH (1 message instead of a later link break).
  1. **Global trigger:** if >30% of vehicles that have reliable neighbours are unaffiliated
     (and ≥10 s since the last one) → full re-cluster with composite score.
  2. **Predictive, cost-bounded trigger:** hazard(v) = Σ_members −ln S_vj (expected member
     link breaks within τ). Evaluate cluster c only if `hazard(c)·c_event > γ·(|C|+1)`
     (the most a switch could save > its cost: a necessary condition, so no useful switch
     is missed) **and** CH tenure ≥ `dwell_s = 10`. No BC is computed otherwise.
  3. **Cluster-local BC** on members + their 1-hop neighbours only.
  4. **Switch** to the best composite-score member b only if: score gain > `hysteresis
     0.15`, **and** `Benefit = (hazard(c) − hazard(b))·c_event > γ·Cost`, with
     `Cost = |C|+1`, `c_event = 2`, `γ = 1`.
  Formation and local formation use the composite score instead of plain BC.

History: the first trigger version (mean member survival < 0.75) fired almost every step and
saved no CPU. It was replaced by the cost-bounded trigger, and BC was made cluster-local.
(The stale module docstring in `policies.py` was fixed on 31 Oct 2026.)

### 3.6 Message model (counted from protocol rules, not packet-level)
JOIN = 1 per (re)affiliation; CH_ADV = 1 per new/handed-over cluster; controller sync = 1
per handover (so a handover costs 2 + JOINs); full re-cluster = 2N (N reports up, N
assignments down). Beacons = N per step, identical for all policies, reported separately.

### 3.7 Metrics (`simulator.py`)
ch_elections_per_min, handovers_per_min, full_reclusters, avg_ch_tenure_s (censored at run
end), affil_switches_per_min, forced_rejoins_per_min, control_msgs_per_min/total,
beacons_total, overhead_ratio = ctrl/(ctrl+beacons), bc_calls, bc_nodes_processed (BC work
proxy), cpu_ms_per_step (`time.process_time`, maintenance only, *measured*), cpu_total_s,
wall_s, unaffiliated_frac, avg_clusters, avg_cluster_size, merges, seed.

### 3.8 Experiments
- `run_experiments.py --source sumo|synthetic --seeds K --seed-offset O --nodes ...
  --ablation --workers 1 --tag NAME`. Keep `--workers 1` so CPU timings are clean.
- Ablation variants (run with `--ablation`, intended at N = 60): `costaware`,
  `costaware_nohyst` (hysteresis 0, dwell 0), `costaware_nocost` (γ = 0),
  `costaware_noproactive` (proactive_leave 0), `costaware_naive` (all three off).
- **Tuning rule:** tune only on seeds ≥1000 (`--seed-offset 1000`). Never tune on the
  reported seeds 0–9.
- `analyze.py --tag NAME`: pooled means, paired t-tests (costaware vs each baseline, paired
  by N and seed), verdict better/WORSE (sig./n.s.), predictor quality table, ablation table,
  6-panel plot with 95% CI.

## 4. Status / results so far

- Smoke test passes on the user's PC (identical numbers to the sandbox).
- All 100 SUMO traces generated (`traces/sumo/N{10..100}_s{0..9}.npz`).
- Main experiment run: `results/main/runs.csv` (300 rows = 3 policies × 10 N × 10 seeds).
- One-trace check run done: `results/check/runs.csv` (N = 50, seed 0):

| metric | periodic | eager | costaware |
|---|---|---|---|
| CH elections/min | 75.2 | 196.2 | 26.0 |
| handovers/min | 0 | 193.2 | 9.0 |
| full reclusters | 30 | 0 | 0 |
| avg CH tenure s | 9.95 | 4.43 | 24.4 |
| affil switches/min | 93.6 | 163.2 | 62.2 |
| **forced rejoins/min** | 17.2 | 11.2 | **24.0 (worse)** |
| control msgs/min | 706.4 | 919.2 | 148.4 |
| overhead ratio | 0.191 | 0.235 | 0.047 |
| bc_calls / bc_nodes | 31 / 2403 | 301 / 16563 | 766 / 7028 |
| **CPU ms/step** | 0.47 | 3.58 | **1.06 (worse than periodic)** |
| unaffiliated frac | 0.161 | 0.173 | 0.128 |
| avg clusters / size | 12.9 / 3.30 | 14.7 / 2.85 | 11.8 / 3.76 |
| merges | 126 | 112 | 62 |

Interpretation given to the user: stability and message overhead are strongly better
(−65%/−87% elections, −79%/−84% messages vs periodic/eager) and coverage is better. **Honest
weaknesses:** more forced re-joins (cluster edges age between switches) and more CPU than
`periodic` (on-demand BC vs once per 10 s), though much less CPU than `eager`. These must be
reported, not hidden. One seed proves nothing. The synthetic-trace numbers in SPEC.md §10 are
pipeline validation only and must not be reported as results.

## 5. Parameters (paper gaps filled with our choices)

| Parameter | Value | Source |
|---|---|---|
| node counts | 10..100 step 10 | paper |
| map | SUMO grid 8×8 junctions, 200 m spacing (1.4 km square), 50 km/h | paper says grid; size ours |
| radio range R (T_R) | 250 m | ours (802.11p-typical) |
| step / beacon | 1 s / 1 Hz | ours |
| warm-up / measured | 60 s / 300 s | ours |
| seeds | 10 per N | ours |
| τ / L_max | 10 s / 60 s | ours |
| θ join | 0.6 | ours |
| BC λ | 1.0 | ours |
| merge | 5 s | ours |
| periodic period | 10 s | ours (**must sweep; see §6**) |
| costaware | weights (0.3, 0.5, 0.2), hysteresis 0.15, dwell 10 s, γ 1, c_event 2, proactive_leave 0.3, global 30% / 10 s | ours |

Paper gaps documented in SPEC.md §9: missing T_R/μ/σ/beacon/duration/density/seeds; sum
of reliabilities in Eq.1–2 (we use product via −ln S); unclear R_l integration limits; BC
weighting undefined; circular CH↔BC↔cluster dependency (we bootstrap); fixed 2×2 clusters
with no CH-change rule (our contribution); no LOS obstacle model (Semester 2: buildings, and
a shortcut must be ≤ R); Algorithm 1 isn't full D\*-Lite (Semester 2: Koenig–Likhachev
with km); CT modelled and DM = neighbour evaluations (we measure CPU and count protocol
messages); clustering overhead excluded (we count it).

## 6. Next steps (in order)

1. ~~Generate all traces~~ (done).
2. ~~Main experiment + analyze~~ (done, `results/main/`). Pooled vs periodic(10 s):
   elections −63%, control msgs −77%, unaffiliated −19%; WORSE: forced re-joins +51%,
   CPU/step +60%. Predictor Brier 0.132 vs constant-rate 0.220 (beats baseline). Note:
   accuracy@0.5 equals kinematic accuracy by construction (Φ(x)≥0.5 ⇔ d̂≤R), so the
   probabilistic model adds calibration, not classification accuracy.
3. ~~Period sweep~~ (done, `run_experiments.py --period-sweep`, `results/period_sweep/`).
   Ours beats periodic 5/10/20/30 on elections and messages (−87/−77/−60/−47% msgs).
   Forced re-joins: periodic_5/10 are better (4.9/16.3 vs 24.6), periodic_20/30 worse
   (36.6/45.5). CPU: ours lower than periodic_5 only (1.52 vs 1.76 ms); higher than 10/20/30.
4. ~~Ablation at N = 60~~ (done, `results/ablation/`, pooled means only, no t-tests):
   cost check matters most (γ=0: elections 33.5→51, msgs 192→283, CPU 1.37→2.52);
   hysteresis+dwell alone adds little (34.6 elections); proactive leave halves forced
   re-joins (46.5→28.0); naive: 73 elections, 404 msgs, 4.7 ms CPU, but 19.4 forced re-joins.
5. **Sensitivity** (tuning seeds ≥1000 only; traces for seeds ≥1000 must be generated
   first): τ (5/10/20), γ, hysteresis, proactive_leave.
   Goal: reduce forced re-joins without losing the message savings.
6. Update SPEC.md §10 with real SUMO results (docstring already fixed).
7. Final figures and tables → report/slides for the guide → Semester 2 plan.

7-day plan (from SPEC.md): Day 1 environment + one trace (**done**); Day 2 all traces +
predictor check; Day 3 main experiment; Day 4 ablation + sensitivity + period sweep; Day 5
fixes, final runs, figures; Day 6 report/slides; Day 7 buffer/rehearsal/Semester 2 plan.

## 7. Working rules for you (Claude Code)

- Be honest about results: report weaknesses (forced re-joins, CPU vs periodic) and say
  when something is one seed or synthetic. Never present synthetic-trace numbers as results.
- Don't change parameters to make our method look better on evaluation seeds. Tuning goes
  on seeds ≥1000. If a value is changed, mark it in config.yaml and SPEC.md.
- Keep runs reproducible (fixed seeds, config-driven). Keep `--workers 1` for timing runs.
- Quote paths (the folder name has a space). Use the venv.
- Run `python tests/smoke_test.py` after any code change to policies/link model.
- Explain to the user what each step did and how it connects to the project (they asked
  for this explicitly), at a beginner-friendly level, without skipping technical terms.
- Messages and CPU are from a logical simulator, not packet-level. Say so in anything
  written for the guide.
- README.md says `.venv`, but the real venv folder is `venv/`.
