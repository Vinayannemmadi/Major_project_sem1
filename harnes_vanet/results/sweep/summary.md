# Results: sweep

## Mean over all runs

|                                        |   HARNES (periodic 10 s) |   HARNES (periodic 20s) |   HARNES (periodic 30s) |   HARNES (periodic 5s) |   Ours (cost-aware) |
|:---------------------------------------|-------------------------:|------------------------:|------------------------:|-----------------------:|--------------------:|
| CH elections / min                     |                   89.26  |                  57.3   |                  45.98  |                122.76  |              33.5   |
| Average CH tenure (s)                  |                    9.883 |                  14.561 |                  17.775 |                  7.66  |              22.456 |
| Member affiliation switches / min      |                  129.6   |                  88.24  |                  73.94  |                180.86  |              79.66  |
| Forced re-joins / min (link broke)     |                   16.98  |                  39.18  |                  48.04  |                  5.36  |              27.96  |
| Control messages / min (excl. beacons) |                  848.08  |                 486.34  |                 364.8   |               1540.36  |             192.06  |
| Control share of all messages          |                    0.191 |                   0.119 |                   0.092 |                  0.3   |               0.051 |
| Maintenance CPU time (ms / step)       |                    0.71  |                   0.414 |                   0.323 |                  1.268 |               1.35  |
| Nodes processed by BC (work proxy)     |                 2623.4   |                1714.2   |                1405.1   |               4116.2   |            8845.3   |
| Unaffiliated vehicles (fraction)       |                    0.126 |                   0.11  |                   0.104 |                  0.132 |               0.097 |
| Average cluster size                   |                    3.498 |                   3.7   |                   3.756 |                  3.273 |               4.003 |

## Ours (cost-aware) vs HARNES (periodic 10 s)  (paired by N and seed, n = 10)

| Metric | Baseline | Ours | Change | p-value | Verdict |
|---|---|---|---|---|---|
| CH elections / min | 89.260 | 33.500 | -62.5% | 5.3e-12 | better (sig.) |
| Average CH tenure (s) | 9.883 | 22.456 | +127.2% | 2.4e-10 | better (sig.) |
| Member affiliation switches / min | 129.600 | 79.660 | -38.5% | 6.8e-11 | better (sig.) |
| Forced re-joins / min (link broke) | 16.980 | 27.960 | +64.7% | 3.3e-08 | WORSE (sig.) |
| Control messages / min (excl. beacons) | 848.080 | 192.060 | -77.4% | 3.6e-17 | better (sig.) |
| Control share of all messages | 0.191 | 0.051 | -73.4% | 4.3e-17 | better (sig.) |
| Maintenance CPU time (ms / step) | 0.710 | 1.350 | +90.3% | 2.1e-09 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | 2623.400 | 8845.300 | +237.2% | 9.4e-11 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | 0.126 | 0.097 | -22.9% | 5e-06 | better (sig.) |
| Average cluster size | 3.498 | 4.003 | +14.4% | 2.5e-10 | context |

## Ours (cost-aware) vs HARNES (periodic 20s)  (paired by N and seed, n = 10)

| Metric | Baseline | Ours | Change | p-value | Verdict |
|---|---|---|---|---|---|
| CH elections / min | 57.300 | 33.500 | -41.5% | 3.9e-09 | better (sig.) |
| Average CH tenure (s) | 14.561 | 22.456 | +54.2% | 1.9e-08 | better (sig.) |
| Member affiliation switches / min | 88.240 | 79.660 | -9.7% | 0.00066 | better (sig.) |
| Forced re-joins / min (link broke) | 39.180 | 27.960 | -28.6% | 2e-06 | better (sig.) |
| Control messages / min (excl. beacons) | 486.340 | 192.060 | -60.5% | 3.9e-15 | better (sig.) |
| Control share of all messages | 0.119 | 0.051 | -57.4% | 5.3e-15 | better (sig.) |
| Maintenance CPU time (ms / step) | 0.414 | 1.350 | +226.0% | 1.2e-10 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | 1714.200 | 8845.300 | +416.0% | 3e-11 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | 0.110 | 0.097 | -11.4% | 0.00025 | better (sig.) |
| Average cluster size | 3.700 | 4.003 | +8.2% | 1.2e-07 | context |

## Ours (cost-aware) vs HARNES (periodic 30s)  (paired by N and seed, n = 10)

| Metric | Baseline | Ours | Change | p-value | Verdict |
|---|---|---|---|---|---|
| CH elections / min | 45.980 | 33.500 | -27.1% | 2.2e-07 | better (sig.) |
| Average CH tenure (s) | 17.775 | 22.456 | +26.3% | 1.9e-06 | better (sig.) |
| Member affiliation switches / min | 73.940 | 79.660 | +7.7% | 0.0041 | WORSE (sig.) |
| Forced re-joins / min (link broke) | 48.040 | 27.960 | -41.8% | 3.9e-07 | better (sig.) |
| Control messages / min (excl. beacons) | 364.800 | 192.060 | -47.4% | 9.5e-14 | better (sig.) |
| Control share of all messages | 0.092 | 0.051 | -45.0% | 1.1e-13 | better (sig.) |
| Maintenance CPU time (ms / step) | 0.323 | 1.350 | +318.3% | 8.8e-11 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | 1405.100 | 8845.300 | +529.5% | 3.1e-11 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | 0.104 | 0.097 | -6.5% | 0.015 | better (sig.) |
| Average cluster size | 3.756 | 4.003 | +6.6% | 3.5e-06 | context |

## Ours (cost-aware) vs HARNES (periodic 5s)  (paired by N and seed, n = 10)

| Metric | Baseline | Ours | Change | p-value | Verdict |
|---|---|---|---|---|---|
| CH elections / min | 122.760 | 33.500 | -72.7% | 1.5e-14 | better (sig.) |
| Average CH tenure (s) | 7.660 | 22.456 | +193.2% | 2.2e-11 | better (sig.) |
| Member affiliation switches / min | 180.860 | 79.660 | -56.0% | 2.7e-11 | better (sig.) |
| Forced re-joins / min (link broke) | 5.360 | 27.960 | +421.6% | 1.1e-11 | WORSE (sig.) |
| Control messages / min (excl. beacons) | 1540.360 | 192.060 | -87.5% | 4.9e-21 | better (sig.) |
| Control share of all messages | 0.300 | 0.051 | -83.1% | 2e-20 | better (sig.) |
| Maintenance CPU time (ms / step) | 1.268 | 1.350 | +6.5% | 0.035 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | 4116.200 | 8845.300 | +114.9% | 2.1e-09 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | 0.132 | 0.097 | -26.2% | 4.5e-07 | better (sig.) |
| Average cluster size | 3.273 | 4.003 | +22.3% | 1.1e-12 | context |

## Link-survival predictor quality

| Measure | Value |
|---|---|
| Links that really survived the next 10 s | 0.676 |
| Accuracy (survive / break) | 0.819 |
| Brier score, our probabilistic model | 0.1291 |
| Brier score, deterministic kinematic prediction | 0.1809 |
| Brier score, constant guess | 0.2190 |

(Brier = mean squared error of the predicted probability; lower is better.)
