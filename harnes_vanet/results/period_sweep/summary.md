# Pooled results (mean over all N and seeds)

|                                              |   costaware |   periodic_10 |   periodic_20 |   periodic_30 |   periodic_5 |
|:---------------------------------------------|------------:|--------------:|--------------:|--------------:|-------------:|
| CH elections / min (lower = more stable)     |      28.3   |        76.14  |        49.654 |        40.484 |      104.804 |
| Average CH tenure (s) (higher = more stable) |      24.126 |        10.732 |        15.556 |        18.722 |        8.313 |
| Member affiliation switches / min            |      81.582 |       133.714 |        90.786 |        75.896 |      186.718 |
| Forced re-joins / min (link broke)           |      24.602 |        16.26  |        36.608 |        45.486 |        4.86  |
| Control messages / min (excl. beacons)       |     177.92  |       776.886 |       446.882 |       337.148 |     1408.8   |
| Control share of all messages                |       0.045 |         0.189 |         0.117 |         0.09  |        0.299 |
| Maintenance CPU time (ms / step)             |       1.52  |         0.947 |         0.53  |         0.393 |        1.763 |
| Nodes processed by BC (work proxy)           |    8511.65  |      2373.46  |      1554.08  |      1282.96  |     3747.95  |
| Unaffiliated vehicles (fraction)             |       0.171 |         0.211 |         0.19  |         0.183 |        0.223 |
| Average cluster size                         |       3.852 |         3.405 |         3.585 |         3.635 |        3.181 |


# costaware vs baselines (paired by N and seed)

| Metric | Baseline | Baseline mean | Ours mean | Change | p-value | Verdict |
|---|---|---|---|---|---|---|
| CH elections / min (lower = more stable) | periodic_5 | 104.804 | 28.300 | -73.0% | 5.79e-31 | better (sig.) |
| Average CH tenure (s) (higher = more stable) | periodic_5 | 8.313 | 24.126 | +190.2% | 2.75e-76 | better (sig.) |
| Member affiliation switches / min | periodic_5 | 186.718 | 81.582 | -56.3% | 3.43e-19 | better (sig.) |
| Forced re-joins / min (link broke) | periodic_5 | 4.860 | 24.602 | +406.2% | 5.61e-45 | WORSE (sig.) |
| Control messages / min (excl. beacons) | periodic_5 | 1408.802 | 177.920 | -87.4% | 3.97e-36 | better (sig.) |
| Control share of all messages | periodic_5 | 0.299 | 0.045 | -84.9% | 1.96e-134 | better (sig.) |
| Maintenance CPU time (ms / step) | periodic_5 | 1.763 | 1.520 | -13.8% | 0.00062 | better (sig.) |
| Nodes processed by BC (work proxy) | periodic_5 | 3747.950 | 8511.650 | +127.1% | 3.85e-19 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | periodic_5 | 0.223 | 0.171 | -23.2% | 1.4e-22 | better (sig.) |
| Average cluster size | periodic_5 | 3.181 | 3.852 | +21.1% | 4.02e-34 | context |
| CH elections / min (lower = more stable) | periodic_10 | 76.140 | 28.300 | -62.8% | 4.8e-31 | better (sig.) |
| Average CH tenure (s) (higher = more stable) | periodic_10 | 10.732 | 24.126 | +124.8% | 3.26e-72 | better (sig.) |
| Member affiliation switches / min | periodic_10 | 133.714 | 81.582 | -39.0% | 2.72e-19 | better (sig.) |
| Forced re-joins / min (link broke) | periodic_10 | 16.260 | 24.602 | +51.3% | 1.25e-39 | WORSE (sig.) |
| Control messages / min (excl. beacons) | periodic_10 | 776.886 | 177.920 | -77.1% | 2.44e-36 | better (sig.) |
| Control share of all messages | periodic_10 | 0.189 | 0.045 | -76.1% | 3.33e-123 | better (sig.) |
| Maintenance CPU time (ms / step) | periodic_10 | 0.947 | 1.520 | +60.5% | 1.4e-33 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | periodic_10 | 2373.460 | 8511.650 | +258.6% | 4.53e-22 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | periodic_10 | 0.211 | 0.171 | -18.9% | 6.27e-29 | better (sig.) |
| Average cluster size | periodic_10 | 3.405 | 3.852 | +13.1% | 2.99e-32 | context |
| CH elections / min (lower = more stable) | periodic_20 | 49.654 | 28.300 | -43.0% | 7.46e-29 | better (sig.) |
| Average CH tenure (s) (higher = more stable) | periodic_20 | 15.556 | 24.126 | +55.1% | 1.45e-59 | better (sig.) |
| Member affiliation switches / min | periodic_20 | 90.786 | 81.582 | -10.1% | 1.2e-12 | better (sig.) |
| Forced re-joins / min (link broke) | periodic_20 | 36.608 | 24.602 | -32.8% | 9.38e-15 | better (sig.) |
| Control messages / min (excl. beacons) | periodic_20 | 446.882 | 177.920 | -60.2% | 2e-37 | better (sig.) |
| Control share of all messages | periodic_20 | 0.117 | 0.045 | -61.3% | 6.71e-101 | better (sig.) |
| Maintenance CPU time (ms / step) | periodic_20 | 0.530 | 1.520 | +187.0% | 1.4e-24 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | periodic_20 | 1554.080 | 8511.650 | +447.7% | 1.69e-23 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | periodic_20 | 0.190 | 0.171 | -10.1% | 1.21e-21 | better (sig.) |
| Average cluster size | periodic_20 | 3.585 | 3.852 | +7.4% | 3.26e-29 | context |
| CH elections / min (lower = more stable) | periodic_30 | 40.484 | 28.300 | -30.1% | 1.32e-26 | better (sig.) |
| Average CH tenure (s) (higher = more stable) | periodic_30 | 18.722 | 24.126 | +28.9% | 3.04e-49 | better (sig.) |
| Member affiliation switches / min | periodic_30 | 75.896 | 81.582 | +7.5% | 4.19e-15 | WORSE (sig.) |
| Forced re-joins / min (link broke) | periodic_30 | 45.486 | 24.602 | -45.9% | 5.88e-20 | better (sig.) |
| Control messages / min (excl. beacons) | periodic_30 | 337.148 | 177.920 | -47.2% | 8.19e-39 | better (sig.) |
| Control share of all messages | periodic_30 | 0.090 | 0.045 | -49.6% | 2.36e-85 | better (sig.) |
| Maintenance CPU time (ms / step) | periodic_30 | 0.393 | 1.520 | +286.4% | 4.05e-23 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | periodic_30 | 1282.960 | 8511.650 | +563.4% | 5.87e-24 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | periodic_30 | 0.183 | 0.171 | -6.4% | 1.12e-16 | better (sig.) |
| Average cluster size | periodic_30 | 3.635 | 3.852 | +6.0% | 3.85e-29 | context |

# Link-survival predictor quality (pooled)

|                     |   mean |
|:--------------------|-------:|
| survival_rate       | 0.6715 |
| brier_prob_model    | 0.1321 |
| brier_constant_rate | 0.2203 |
| acc_prob_model@0.5  | 0.8144 |
| acc_kinematic@tau   | 0.8144 |
