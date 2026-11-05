# Pooled results (mean over all N and seeds)

|                                              |   costaware |     eager |   periodic |
|:---------------------------------------------|------------:|----------:|-----------:|
| CH elections / min (lower = more stable)     |      27.633 |   220.9   |     74.267 |
| Average CH tenure (s) (higher = more stable) |      26.699 |     6.987 |     11.952 |
| Member affiliation switches / min            |      87.567 |   300.333 |    145.967 |
| Forced re-joins / min (link broke)           |      23.3   |     8.3   |      7.467 |
| Control messages / min (excl. beacons)       |     180.667 |  1147.73  |    818.633 |
| Control share of all messages                |       0.042 |     0.193 |      0.184 |
| Maintenance CPU time (ms / step)             |       1.571 |    10.081 |      1.109 |
| Nodes processed by BC (work proxy)           |    8685     | 19189.7   |   2393.67  |
| Unaffiliated vehicles (fraction)             |       0.148 |     0.178 |      0.185 |
| Average cluster size                         |       3.999 |     3.089 |      3.519 |


# costaware vs baselines (paired by N and seed)

| Metric | Baseline | Baseline mean | Ours mean | Change | p-value | Verdict |
|---|---|---|---|---|---|---|
| CH elections / min (lower = more stable) | periodic | 74.267 | 27.633 | -62.8% | 0.0142 | better (sig.) |
| Average CH tenure (s) (higher = more stable) | periodic | 11.952 | 26.699 | +123.4% | 0.000163 | better (sig.) |
| Member affiliation switches / min | periodic | 145.967 | 87.567 | -40.0% | 0.0691 | better (n.s.) |
| Forced re-joins / min (link broke) | periodic | 7.467 | 23.300 | +212.1% | 0.000288 | WORSE (sig.) |
| Control messages / min (excl. beacons) | periodic | 818.633 | 180.667 | -77.9% | 0.00775 | better (sig.) |
| Control share of all messages | periodic | 0.184 | 0.042 | -77.3% | 4.91e-07 | better (sig.) |
| Maintenance CPU time (ms / step) | periodic | 1.109 | 1.571 | +41.7% | 0.00556 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | periodic | 2393.667 | 8685.000 | +262.8% | 0.044 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | periodic | 0.185 | 0.148 | -19.7% | 0.014 | better (sig.) |
| Average cluster size | periodic | 3.519 | 3.999 | +13.6% | 0.0162 | context |
| CH elections / min (lower = more stable) | eager | 220.900 | 27.633 | -87.5% | 0.0324 | better (sig.) |
| Average CH tenure (s) (higher = more stable) | eager | 6.987 | 26.699 | +282.2% | 7.27e-06 | better (sig.) |
| Member affiliation switches / min | eager | 300.333 | 87.567 | -70.8% | 0.0721 | better (n.s.) |
| Forced re-joins / min (link broke) | eager | 8.300 | 23.300 | +180.7% | 0.0106 | WORSE (sig.) |
| Control messages / min (excl. beacons) | eager | 1147.733 | 180.667 | -84.3% | 0.0379 | better (sig.) |
| Control share of all messages | eager | 0.193 | 0.042 | -78.3% | 0.00572 | better (sig.) |
| Maintenance CPU time (ms / step) | eager | 10.081 | 1.571 | -84.4% | 0.107 | better (n.s.) |
| Nodes processed by BC (work proxy) | eager | 19189.667 | 8685.000 | -54.7% | 0.00273 | better (sig.) |
| Unaffiliated vehicles (fraction) | eager | 0.178 | 0.148 | -16.8% | 0.00227 | better (sig.) |
| Average cluster size | eager | 3.089 | 3.999 | +29.4% | 0.0349 | context |

# Link-survival predictor quality (pooled)

|                     |   mean |
|:--------------------|-------:|
| survival_rate       | 0.6925 |
| brier_prob_model    | 0.0823 |
| brier_constant_rate | 0.2128 |
| acc_prob_model@0.5  | 0.9079 |
| acc_kinematic@tau   | 0.9079 |
