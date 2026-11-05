# Live demo: 50 cars, seed 0, 220 s measured

| Metric | HARNES (periodic 10 s) | Ours (cost-aware) | Change |
|---|---|---|---|
| CH elections / min | 71.455 | 25.636 | -64.1% (better) |
| Average CH tenure (s) | 10.258 | 24.259 | +136.5% (better) |
| Control messages / min | 699.545 | 147.273 | -78.9% (better) |
| Control share of all messages | 0.189 | 0.047 | -75.3% (better) |
| Forced re-joins / min | 14.455 | 23.182 | +60.4% (worse) |
| Maintenance CPU (ms / step) | 1.323 | 2.988 | +125.8% (worse) |
| Unaffiliated vehicles (fraction) | 0.164 | 0.123 | -25.1% (better) |
| Average cluster size | 3.321 | 3.766 | +13.4% |

One run (one seed): for the reported results use run_experiments.py (10 seeds, confidence intervals).
