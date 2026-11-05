"""Summaries, significance tests and plots from results/<tag>/runs.csv.
  python analyze.py --tag main       # HARNES (periodic) vs ours, over N = 10..100
  python analyze.py --tag sweep      # ours vs HARNES with 5/10/20/30 s periods
  python analyze.py --tag ablation   # which component of ours gives the gain
Only the HARNES baseline ("periodic*") and our method ("costaware*") are reported;
any other policy found in runs.csv (e.g. old "eager" rows) is ignored.
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
    "ch_elections_per_min": "CH elections / min",
    "avg_ch_tenure_s": "Average CH tenure (s)",
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
PLOT = ["ch_elections_per_min", "avg_ch_tenure_s", "control_msgs_per_min",
        "cpu_ms_per_step", "forced_rejoins_per_min", "unaffiliated_frac"]
LABEL = {"periodic": "HARNES (periodic 10 s)", "costaware": "Ours (cost-aware)"}


def label(p):
    if p in LABEL:
        return LABEL[p]
    if p.startswith("periodic_"):
        return "HARNES (periodic " + p.split("_", 1)[1] + ")"
    return p


def ci95(x):
    x = np.asarray(x, float)
    return 0.0 if len(x) < 2 else stats.sem(x) * stats.t.ppf(0.975, len(x) - 1)


def compare(df, ours, base):
    """Paired comparison (same N and seed) of policy `ours` against `base`."""
    key = ["N", "seed"]
    a = df[df.policy == ours].set_index(key)
    b = df[df.policy == base].set_index(key).reindex(a.index)
    rows = []
    for m in METRICS:
        x, y = a[m].values, b[m].values
        chg = 100 * (x.mean() - y.mean()) / y.mean() if y.mean() != 0 else float("nan")
        p = stats.ttest_rel(x, y).pvalue if len(x) > 2 and np.any(x != y) else float("nan")
        if m == "avg_cluster_size":
            verdict = "context"
        else:
            better = (x.mean() < y.mean()) if m in LOWER_BETTER else (x.mean() > y.mean())
            verdict = ("better" if better else "WORSE") + (" (sig.)" if p < 0.05 else " (n.s.)")
        rows.append(f"| {METRICS[m]} | {y.mean():.3f} | {x.mean():.3f} | {chg:+.1f}% | {p:.2g} | {verdict} |")
    head = [f"\n## {label(ours)} vs {label(base)}  (paired by N and seed, n = {len(a)})\n",
            "| Metric | Baseline | Ours | Change | p-value | Verdict |", "|---|---|---|---|---|---|"]
    return head + rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="main")
    args = ap.parse_args()
    d = os.path.join(HERE, "results", args.tag)
    df = pd.read_csv(os.path.join(d, "runs.csv"))
    df = df[df.policy.str.startswith(("periodic", "costaware"))]
    pols = sorted(df.policy.unique(), key=lambda p: (not p.startswith("periodic"), p != "periodic", p))
    bases = [p for p in pols if p.startswith("periodic")]
    ours = [p for p in pols if p.startswith("costaware")]

    # ---- plots ----
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    multi_n = df.N.nunique() > 1
    for ax, m in zip(axes.ravel(), PLOT):
        if multi_n:
            for p in pols:
                g = df[df.policy == p].groupby("N")[m]
                ax.errorbar(g.mean().index, g.mean().values, yerr=g.apply(ci95).values,
                            marker="o", capsize=3, label=label(p))
            ax.set_xlabel("Number of vehicles")
        else:
            g = df.groupby("policy")[m]
            mean, err = g.mean().reindex(pols), g.apply(ci95).reindex(pols)
            ax.bar(range(len(pols)), mean.values, yerr=err.values, capsize=3,
                   color=["#888888" if p.startswith("periodic") else "#2b6cb0" for p in pols])
            ax.set_xticks(range(len(pols)))
            ax.set_xticklabels([label(p) for p in pols], rotation=30, ha="right", fontsize=8)
        ax.set_title(METRICS[m], fontsize=10)
        ax.grid(alpha=.3)
    if multi_n:
        axes[0, 0].legend(fontsize=8)
    fig.suptitle(f"results/{args.tag}  (error bars: 95% CI)")
    fig.tight_layout()
    fig.savefig(os.path.join(d, "comparison.png"), dpi=140)

    # ---- trade-off plot (sweep): messages vs link breaks ----
    if len(bases) >= 2 and "costaware" in ours:
        def period(p):
            return 10.0 if p == "periodic" else float(p.split("_", 1)[1].rstrip("s"))
        g = df.groupby("policy")
        mx, my = g["control_msgs_per_min"].mean(), g["forced_rejoins_per_min"].mean()
        ex, ey = g["control_msgs_per_min"].apply(ci95), g["forced_rejoins_per_min"].apply(ci95)
        bs = sorted(bases, key=period)
        fig2, ax = plt.subplots(figsize=(7, 5))
        ax.errorbar(mx[bs], my[bs], xerr=ex[bs], yerr=ey[bs], marker="o", color="#777777",
                    capsize=3, lw=2, label="HARNES, re-clustering period varied")
        for p in bs:
            ax.annotate(f"{period(p):g} s", (mx[p], my[p]), textcoords="offset points",
                        xytext=(6, 6), fontsize=9, color="#555555")
        ax.errorbar([mx["costaware"]], [my["costaware"]], xerr=[ex["costaware"]],
                    yerr=[ey["costaware"]], marker="*", ms=16, color="#2b6cb0", capsize=3,
                    ls="none", label="Ours (cost-aware)")
        ax.set_xlabel("Control messages / min (lower is better)")
        ax.set_ylabel("Forced re-joins / min, i.e. member links that broke (lower is better)")
        ax.set_title("Trade-off: overhead vs link breaks (bottom-left is best)", fontsize=10)
        ax.grid(alpha=.3)
        ax.legend(fontsize=9)
        fig2.tight_layout()
        fig2.savefig(os.path.join(d, "tradeoff.png"), dpi=140)

    # ---- tables ----
    lines = [f"# Results: {args.tag}\n", "## Mean over all runs\n"]
    piv = df.groupby("policy")[list(METRICS)].mean().T[pols]
    piv.index = [METRICS[i] for i in piv.index]
    piv.columns = [label(p) for p in piv.columns]
    lines.append(piv.round(3).to_markdown())

    if "costaware" in ours:
        for b in bases:                       # main: 1 table; sweep: one per period
            lines += compare(df, "costaware", b)
    if len(ours) > 1 and "periodic" in bases:  # ablation: each variant vs HARNES
        lines.append("\n## Ablation: change vs HARNES (periodic 10 s)\n")
        key = ["N", "seed"]
        base = df[df.policy == "periodic"].set_index(key)
        cols = ["ch_elections_per_min", "control_msgs_per_min", "forced_rejoins_per_min",
                "cpu_ms_per_step", "unaffiliated_frac"]
        lines.append("| Variant | " + " | ".join(METRICS[c] for c in cols) + " |")
        lines.append("|---|" + "---|" * len(cols))
        for v in ours:
            a = df[df.policy == v].set_index(key)
            b = base.reindex(a.index)
            cells = [f"{100 * (a[c].mean() - b[c].mean()) / b[c].mean():+.1f}%" for c in cols]
            lines.append(f"| {v} | " + " | ".join(cells) + " |")

    q = os.path.join(d, "prediction_quality.csv")
    if os.path.exists(q):
        pq = pd.read_csv(q).mean()
        lines.append("\n## Link-survival predictor quality\n")
        lines.append("| Measure | Value |\n|---|---|")
        lines.append(f"| Links that really survived the next 10 s | {pq['survival_rate']:.3f} |")
        lines.append(f"| Accuracy (survive / break) | {pq['acc_prob_model@0.5']:.3f} |")
        lines.append(f"| Brier score, our probabilistic model | {pq['brier_prob_model']:.4f} |")
        lines.append(f"| Brier score, deterministic kinematic prediction | {1 - pq['acc_kinematic@tau']:.4f} |")
        lines.append(f"| Brier score, constant guess | {pq['brier_constant_rate']:.4f} |")
        lines.append("\n(Brier = mean squared error of the predicted probability; lower is better.)")

    open(os.path.join(d, "summary.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nplots:", os.path.join(d, "comparison.png"))


if __name__ == "__main__":
    main()
