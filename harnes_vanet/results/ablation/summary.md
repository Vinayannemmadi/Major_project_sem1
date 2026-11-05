# Results: ablation

## Mean over all runs

|                                        |   HARNES (periodic 10 s) |   Ours (cost-aware) |   costaware_naive |   costaware_nocost |   costaware_nohyst |   costaware_noproactive |
|:---------------------------------------|-------------------------:|--------------------:|------------------:|-------------------:|-------------------:|------------------------:|
| CH elections / min                     |                   89.26  |              33.5   |            73.42  |             51     |             34.6   |                  36.92  |
| Average CH tenure (s)                  |                    9.883 |              22.456 |            10.846 |             15.283 |             21.699 |                  20.823 |
| Member affiliation switches / min      |                  129.6   |              79.66  |           153.22  |            110.56  |             82.66  |                  65.66  |
| Forced re-joins / min (link broke)     |                   16.98  |              27.96  |            19.4   |             24.26  |             26.78  |                  46.54  |
| Control messages / min (excl. beacons) |                  848.08  |             192.06  |           403.66  |            283.48  |            199.64  |                 189.12  |
| Control share of all messages          |                    0.191 |               0.051 |             0.101 |              0.073 |              0.053 |                   0.05  |
| Maintenance CPU time (ms / step)       |                    0.707 |               1.349 |             4.585 |              2.465 |              1.554 |                   1.762 |
| Nodes processed by BC (work proxy)     |                 2623.4   |            8845.3   |         35713.1   |          18224.2   |          10393.8   |               12230.6   |
| Unaffiliated vehicles (fraction)       |                    0.126 |               0.097 |             0.104 |              0.102 |              0.098 |                   0.1   |
| Average cluster size                   |                    3.498 |               4.003 |             3.942 |              3.956 |              4.018 |                   3.943 |

## Ours (cost-aware) vs HARNES (periodic 10 s)  (paired by N and seed, n = 10)

| Metric | Baseline | Ours | Change | p-value | Verdict |
|---|---|---|---|---|---|
| CH elections / min | 89.260 | 33.500 | -62.5% | 5.3e-12 | better (sig.) |
| Average CH tenure (s) | 9.883 | 22.456 | +127.2% | 2.4e-10 | better (sig.) |
| Member affiliation switches / min | 129.600 | 79.660 | -38.5% | 6.8e-11 | better (sig.) |
| Forced re-joins / min (link broke) | 16.980 | 27.960 | +64.7% | 3.3e-08 | WORSE (sig.) |
| Control messages / min (excl. beacons) | 848.080 | 192.060 | -77.4% | 3.6e-17 | better (sig.) |
| Control share of all messages | 0.191 | 0.051 | -73.4% | 4.3e-17 | better (sig.) |
| Maintenance CPU time (ms / step) | 0.707 | 1.349 | +90.9% | 1.4e-09 | WORSE (sig.) |
| Nodes processed by BC (work proxy) | 2623.400 | 8845.300 | +237.2% | 9.4e-11 | WORSE (sig.) |
| Unaffiliated vehicles (fraction) | 0.126 | 0.097 | -22.9% | 5e-06 | better (sig.) |
| Average cluster size | 3.498 | 4.003 | +14.4% | 2.5e-10 | context |

## Ablation: change vs HARNES (periodic 10 s)

| Variant | CH elections / min | Control messages / min (excl. beacons) | Forced re-joins / min (link broke) | Maintenance CPU time (ms / step) | Unaffiliated vehicles (fraction) |
|---|---|---|---|---|---|
| costaware | -62.5% | -77.4% | +64.7% | +90.9% | -22.9% |
| costaware_naive | -17.7% | -52.4% | +14.3% | +548.7% | -18.0% |
| costaware_nocost | -42.9% | -66.6% | +42.9% | +248.8% | -19.1% |
| costaware_nohyst | -61.2% | -76.5% | +57.7% | +119.8% | -22.7% |
| costaware_noproactive | -58.6% | -77.7% | +174.1% | +149.3% | -20.4% |

## Link-survival predictor quality

| Measure | Value |
|---|---|
| Links that really survived the next 10 s | 0.676 |
| Accuracy (survive / break) | 0.819 |
| Brier score, our probabilistic model | 0.1291 |
| Brier score, deterministic kinematic prediction | 0.1809 |
| Brier score, constant guess | 0.2190 |

(Brier = mean squared error of the predicted probability; lower is better.)
