# Pooled results (mean over all N and seeds)

|                                              |   costaware |     eager |   periodic |
|:---------------------------------------------|------------:|----------:|-----------:|
| CH elections / min (lower = more stable)     |      28.3   |   221.692 |     76.14  |
| Average CH tenure (s) (higher = more stable) |      24.126 |     6.419 |     10.732 |
| Member affiliation switches / min            |      81.582 |   268.916 |    133.714 |
| Forced re-joins / min (link broke)           |      24.602 |     9.218 |     16.26  |
| Control messages / min (excl. beacons)       |     177.92  |  1117.38  |    776.886 |
| Control share of all messages                |       0.045 |     0.209 |      0.189 |
| Maintenance CPU time (ms / step)             |       1.51  |     8.405 |      0.942 |
| Nodes processed by BC (work proxy)           |    8511.65  | 17844     |   2373.46  |
| Unaffiliated vehicles (fraction)             |       0.171 |     0.21  |      0.211 |
| Average cluster size                         |       3.852 |     2.988 |      3.405 |


# costaware vs baselines (paired by N and seed)

| Metric | Baseline | Baseline mean | Ours mean | Change | p-value | Verdict |
|---|---|---|---|---|---|---|
| CH elections / min (lower = more stable) | periodic | 76.140 | 28.300 | -62.8% | 4.8e-31 | better (sig.) |
| Average CH tenure (s) (higher = more stable) | periodic | 10.732 | 24.126 | +124.8% | 3.26e-72 | better (sig.) |
| Member affiliation switches / min | periodic | 133.714 | 81.582 | -39.0% | 2.72e-19 | better (sig.) |
| Forced re-joins / min (link broke) | periodic | 16.260 | 24.602 | +51.3% | 1.25e-39 | WORSE (sig.) |
| Control messages / min (excl. beacons) | periodic | 776.886 | 177.920 | -77.1% | 2.44e-36 | better (sig.) |
| Control share of all messages | periodic | 0.189 | 0.045 | -76.1% | 3.33e-123 | better (sig.) |
| Maintenance CPU time (ms / step) | periodic | 0.942 | 1.510 | +60.3% | 2.58e-33 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | periodic | 2373.460 | 8511.650 | +258.6% | 4.53e-22 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | periodic | 0.211 | 0.171 | -18.9% | 6.27e-29 | better (sig.) |
| Average cluster size | periodic | 3.405 | 3.852 | +13.1% | 2.99e-32 | context |
| CH elections / min (lower = more stable) | eager | 221.692 | 28.300 | -87.2% | 4.48e-25 | better (sig.) |
| Average CH tenure (s) (higher = more stable) | eager | 6.419 | 24.126 | +275.9% | 1.97e-66 | better (sig.) |
| Member affiliation switches / min | eager | 268.916 | 81.582 | -69.7% | 2.62e-17 | better (sig.) |
| Forced re-joins / min (link broke) | eager | 9.218 | 24.602 | +166.9% | 3.04e-32 | WORSE (sig.) |
| Control messages / min (excl. beacons) | eager | 1117.384 | 177.920 | -84.1% | 9.1e-24 | better (sig.) |
| Control share of all messages | eager | 0.209 | 0.045 | -78.4% | 7.03e-41 | better (sig.) |
| Maintenance CPU time (ms / step) | eager | 8.405 | 1.510 | -82.0% | 7.69e-14 | better (sig.) |
| Nodes processed by BC (work proxy) | eager | 17843.990 | 8511.650 | -52.3% | 2.14e-47 | better (sig.) |
| Unaffiliated vehicles (fraction) | eager | 0.210 | 0.171 | -18.5% | 7.8e-41 | better (sig.) |
| Average cluster size | eager | 2.988 | 3.852 | +28.9% | 8.81e-26 | context |

# Link-survival predictor quality (pooled)

|                     |   mean |
|:--------------------|-------:|
| survival_rate       | 0.6715 |
| brier_prob_model    | 0.1321 |
| brier_constant_rate | 0.2203 |
| acc_prob_model@0.5  | 0.8144 |
| acc_kinematic@tau   | 0.8144 |
