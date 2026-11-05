# Specification: HARNES baseline + predictive cost-aware cluster maintenance (Semester 1)

## 1. Scope (agreed constraints: 1 person, 7 days, SUMO throughout, Ubuntu 24.04 PC)

**In scope (Semester 1)**
- HARNES cluster layer: link reliability model, betweenness-centrality (BC) cluster-head (CH) election, cluster formation, three-tier FEC/LEC/GEC logic (as logical entities, as in the paper).
- Our contribution: predictive link survival + **cost-aware CH switching and re-clustering**.
- Comparison of stability, control overhead and maintenance compute between HARNES-style maintenance and ours.

**Deferred to Semester 2**: Theta\*/D\*-Lite/A\*/EG-Dijkstra routing on the clusters, route stability prediction, routing metrics (path length, POR, PDR, delay), real map (OSM), packet-level simulator.

> Assumption to confirm with the guide: "implement the base paper" for Semester 1 means the cluster layer. The paper's routing algorithms are Semester 2 work.

## 2. Architecture

```
SUMO grid map --> FCD trace (x, y, speed, angle) --> numpy (pos, vel) per 1 s step
      --> link_model: D, S_ij(tau), L_ij, online sigma   (shared by all policies)
      --> policy (periodic | eager | costaware) maintains clusters each step
      --> metrics: CH changes, tenure, messages, CPU time, link breaks
```
Controllers (FEC/LEC/GEC) are logical: the policy object plays the zone controller. This matches the paper, whose SDN controllers are also simulated logic.

## 3. Parameters

| Parameter | Value | Source |
|---|---|---|
| Node counts | 10 to 100 step 10 | paper Table 2 |
| Map | SUMO grid, 8x8 junctions, 200 m spacing (1.4 km square), 50 km/h | paper: grid; size ours |
| Radio range R | 250 m | ours (paper omits T_R) |
| Step / beacon rate | 1 s / 1 Hz | ours |
| Warm-up / measured run | 60 s / 300 s | ours |
| Seeds per N | 10 (95% CI, paired t-test) | ours (paper: single curves) |
| Horizon tau | 10 s; L_max = 60 s | ours |
| Join threshold theta | S >= 0.6 | ours |
| BC edge weight | 1 + 1.0 * (-ln S) | ours |

## 4. Models

**Paper link model.** D_l = T_R / dv; dv ~ Normal(mu, sigma); R_l(t) = integral of g(T) over [t, t+D_l].

**Our predicted survival (extends the paper's Gaussian idea).** With relative position dp and velocity dv, predict the pair distance at tau: d_hat = |dp + dv*tau|. Distance is convex in time, so a link that is in range now and at tau stays in range throughout. Hence

    S_ij(tau) = Phi( (R - d_hat) / sigma_p )

sigma_p is the std of the prediction error, estimated online (60 s window) from errors the predictor actually made tau seconds earlier (sigma_p grows like sigma_dv * tau, the paper's velocity-noise term). This handles vehicles passing each other, which a relative-speed-only formula does not.

**Kinematic lifetime** L_ij: positive root of |dp + dv*t|^2 = R^2, capped at L_max.

**Betweenness (paper Eq. 3)** computed on the in-range graph with edge weight 1 + lambda*(-ln S), so "reliability-weighted shortest path" (undefined in the paper) is well defined and additive.

**Cluster formation (paper Eq. 4).** Greedy: highest score becomes CH and absorbs unassigned in-range neighbours with S >= theta (1-hop clusters). Unreachable vehicles stay unaffiliated.

**Our CH score.** `Score(v) = 0.3*BC~ + 0.5*mean_j S_vj + 0.2*mean_j min(L_vj/L_max, 1)` over cluster members j.

## 5. Policies (all share local repair: rejoin after a break, local formation among unaffiliated vehicles, merge of CHs that stay adjacent 5 s)

| Policy | When it changes CHs | Role |
|---|---|---|
| `periodic` | full BC re-clustering every 10 s | HARNES-style baseline 1 |
| `eager` | every step; any member with higher BC replaces the CH | HARNES-style baseline 2 (HARNES: "highest BC is CH") |
| `costaware` | see below | **ours** |

**costaware, per step**
1. *Predictive member re-affiliation*: a member whose S to its CH falls below 0.3 moves to a clearly better CH in range (1 message instead of a link break).
2. *Trigger*: evaluate a cluster only if the **upper bound on benefit** exceeds the switching cost: `hazard(CH) * c_event > gamma * cost`, where hazard(v) = sum over members of -ln S_vj (expected link breaks within tau). This is a necessary condition, so no useful switch is missed, and BC is not computed otherwise.
3. *Cluster-local BC* on the cluster plus its 1-hop neighbours.
4. *Switch* to the best-scoring member b only if all hold: score gain > 0.15 (hysteresis); current CH has served >= 10 s (dwell); and
   `Benefit = (hazard(c) - hazard(b)) * c_event  >  gamma * Cost`, with `Cost = |C| + 1` (|C|-1 JOINs + CH_ADV + controller sync), `c_event = 2`, `gamma = 1`.
5. Global re-clustering only if > 30% of vehicles with neighbours are unaffiliated (min gap 10 s).

## 6. Control-message model (counted from protocol rules, not packet level)
JOIN = 1 per (re)affiliation; CH_ADV = 1 per new or handed-over cluster; controller sync = 1 per handover; full re-clustering = 2N. Beacons (N per step) are identical for all policies and reported separately. Packet-level validation is Semester 2.

## 7. Metrics
Stability: CH elections/min, average CH tenure, affiliation switches/min, **forced re-joins/min** (member link actually broke). Overhead: control messages/min, control share of all messages. Compute: maintenance CPU ms/step (`time.process_time`, measured, not modelled), BC calls and nodes processed. Quality guards: unaffiliated fraction, cluster count and size. Predictor: Brier score vs constant-rate guess, accuracy vs deterministic kinematic prediction.

## 8. Experiment design
10 N values x 10 seeds x 3 policies; 95% CI; paired t-test of costaware vs each baseline. Ablation at N=60: no hysteresis/dwell, no cost rule, no proactive re-affiliation, none of these. Tune only on seeds >= 1000.

## 9. Gaps in the paper and how we resolved them

| Gap / problem in the paper | Resolution |
|---|---|
| T_R, mu, sigma, beacon rate, run length, vehicle density, seeds not given | values in section 3; mu/sigma replaced by online prediction-error std |
| Eqs. (1)-(2) maximise a **sum** of link reliabilities (favours long paths; not a path survival probability) | path survival = product, implemented as additive -ln S |
| R_l(t) integration limits unclear | survival over a stated horizon tau |
| "Reliability-weighted shortest path" in BC undefined | edge weight 1 + lambda(-ln S) |
| Circular dependency: CH <- BC <- paths <- clusters | bootstrap with BC on the in-range graph, then form clusters |
| Clusters fixed as 2x2 quadrants; no CH-change or re-clustering rule | 1-hop greedy clusters; maintenance rules are our contribution |
| LOS undefined, no obstacles (Theta\* trivially favoured on an obstacle-free grid) | not needed for the cluster layer; Semester 2 adds building obstacles and requires shortcut length <= R |
| Algorithm 1 is not full D\*-Lite (no km, no edge-change handling) | Semester 2: implement Koenig-Likhachev D\*-Lite |
| Computation time is *modelled*; "discovery messages" are neighbour evaluations | we measure CPU time and count protocol messages |
| Clustering overhead excluded from the paper's savings | we count it explicitly |

## 10. Known limitations (state these to the guide)
- Message counts and CPU are model/measured on a logical simulator, not packet-level 802.11p.
- Grid map has no obstacles; urban LOS effects come in Semester 2.
- Constant-velocity prediction is weaker at junctions.
- Preliminary synthetic-trace run (pipeline validation only, not results): costaware cut CH elections ~63% vs periodic and ~88% vs eager and control messages ~78% / ~84%. It also showed **more forced link re-joins** than the baselines (about 3x) and **higher CPU than periodic** (BC on demand vs once per 10 s), though lower than eager. Whether this holds on SUMO traces is what the experiment will show; report it as it comes out.

## 11. Seven-day plan

| Day | Work | Output |
|---|---|---|
| 1 | Install SUMO, run smoke test, generate one SUMO trace, check it | working environment |
| 2 | Generate all 100 traces; verify vehicle counts and speeds; predictor quality check | traces, `prediction_quality.csv` |
| 3 | Main experiment (3 policies x 100 traces), first analysis | `results/main` |
| 4 | Ablation at N=60; sensitivity to tau, gamma, hysteresis (tuning seeds only) | `results/ablation` |
| 5 | Fix issues found; final runs; figures and tables | final plots, `summary.md` |
| 6 | Write report/slides for the guide | draft |
| 7 | Buffer, rehearse, Semester 2 plan | submission |
