"""Summaries, significance tests and plots from results/<tag>/runs.csv.
  python analyze.py --tag main
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
METRICS = {
    "ch_elections_per_min": "CH elections / min (lower = more stable)",
    "avg_ch_tenure_s": "Average CH tenure (s) (higher = more stable)",
    "affil_switches_per_min": "Member affiliation switches / min",
    "forced_rejoins_per_min": "Forced re-joins / min (link broke)",
    "control_msgs_per_min": "Control messages / min (excl. beacons)",
    "overhead_ratio": "Control share of all messages",
    "cpu_ms_per_step": "Maintenance CPU time (ms / step)",
    "bc_nodes_processed": "Nodes processed by BC (work proxy)",
    "unaffiliated_frac": "Unaffiliated vehicles (fraction)",
    "avg_cluster_size": "Average cluster size",
}
LOWER_BETTER = {"ch_elections_per_min", "affil_switches_per_min", "forced_rejoins_per_min",
                "control_msgs_per_min", "overhead_ratio", "cpu_ms_per_step",
                "bc_nodes_processed", "unaffiliated_frac"}


def ci95(x):
    x = np.asarray(x, float)
    if len(x) < 2:
        return 0.0
    return stats.sem(x) * stats.t.ppf(0.975, len(x) - 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="main")
    args = ap.parse_args()
    d = os.path.join(HERE, "results", args.tag)
    df = pd.read_csv(os.path.join(d, "runs.csv"))
    pols = list(df["policy"].unique())

    # ---- per-N plots with 95% CI ----
    cols = ["ch_elections_per_min", "avg_ch_tenure_s", "control_msgs_per_min",
            "cpu_ms_per_step", "forced_rejoins_per_min", "unaffiliated_frac"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, m in zip(axes.ravel(), cols):
        for p in pols:
            g = df[df.policy == p].groupby("N")[m]
            mean, err = g.mean(), g.apply(ci95)
            ax.errorbar(mean.index, mean.values, yerr=err.values, marker="o", capsize=3, label=p)
        ax.set_title(METRICS[m], fontsize=10)
        ax.set_xlabel("Number of vehicles")
        ax.grid(alpha=.3)
    axes[0, 0].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(d, "comparison.png"), dpi=140)

    # ---- pooled summary + paired tests: costaware vs each baseline ----
    lines = ["# Pooled results (mean over all N and seeds)\n"]
    piv = df.groupby("policy")[list(METRICS)].mean().T
    piv.index = [METRICS[i] for i in piv.index]
    lines.append(piv.round(3).to_markdown() + "\n")
    ours = [p for p in pols if p.startswith("costaware")]
    if "costaware" in pols:
        lines.append("\n# costaware vs baselines (paired by N and seed)\n")
        lines.append("| Metric | Baseline | Baseline mean | Ours mean | Change | p-value | Verdict |")
        lines.append("|---|---|---|---|---|---|---|")
        key = ["N", "seed"]
        a = df[df.policy == "costaware"].set_index(key)
        for b_name in [p for p in pols if not p.startswith("costaware")]:
            b = df[df.policy == b_name].set_index(key)
            for m in METRICS:
                x, y = a[m].values, b[m].reindex(a.index).values
                chg = 100 * (x.mean() - y.mean()) / y.mean() if y.mean() != 0 else float("nan")
                p = stats.ttest_rel(x, y).pvalue if len(x) > 2 and np.any(x != y) else float("nan")
                better = (x.mean() < y.mean()) if m in LOWER_BETTER else (x.mean() > y.mean())
                if m in ("avg_cluster_size",):
                    verdict = "context"
                else:
                    verdict = ("better" if better else "WORSE") + (" (sig.)" if p < 0.05 else " (n.s.)")
                lines.append(f"| {METRICS[m]} | {b_name} | {y.mean():.3f} | {x.mean():.3f} | "
                             f"{chg:+.1f}% | {p:.3g} | {verdict} |")
    q = os.path.join(d, "prediction_quality.csv")
    if os.path.exists(q):
        pq = pd.read_csv(q)
        lines.append("\n# Link-survival predictor quality (pooled)\n")
        lines.append(pq[["survival_rate", "brier_prob_model", "brier_constant_rate",
                         "acc_prob_model@0.5", "acc_kinematic@tau"]].mean().round(4).to_frame("mean").to_markdown())
    if len(ours) > 1:
        lines.append("\n# Ablation (pooled means)\n")
        ab = df.groupby("policy")[["ch_elections_per_min", "control_msgs_per_min",
                                   "cpu_ms_per_step", "forced_rejoins_per_min",
                                   "unaffiliated_frac"]].mean().round(3)
        lines.append(ab.to_markdown())
    open(os.path.join(d, "summary.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nplots:", os.path.join(d, "comparison.png"))


if __name__ == "__main__":
    main()
