"""Final-report figures for the primary result and the speed analysis.

Run after src/analysis_stats.py.

Outputs (results/figures/)
  fig3_cci_by_group.png       CCI per muscle pair: paretic, non-paretic, age-matched
                              able-bodied (one dot per participant, median and IQR)
  fig4_effects_forest.png     every group difference with its 95% CI: paretic and
                              non-paretic vs age-matched, paretic minus non-paretic,
                              and the regression group effect before/after speed
  fig5_cci_vs_speed.png       CCI against walking speed for all three pairs, with the
                              within-group regression lines
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_stats import PAIR_LABEL, PAIRS, build_sets

ROOT = Path(__file__).resolve().parents[1]
TABLES, FIGS = ROOT / "results" / "tables", ROOT / "results" / "figures"
C_P, C_N, C_AB = "#2f6fdb", "#9db9ec", "0.55"


def strip(ax, x, vals, color, rng):
    v = np.asarray(vals)[~np.isnan(vals)]
    ax.scatter(x + rng.uniform(-0.12, 0.12, len(v)), v, s=12, color=color, alpha=0.8, lw=0, zorder=2)
    q1, q2, q3 = np.percentile(v, [25, 50, 75])
    ax.plot([x - 0.22, x + 0.22], [q2, q2], color="k", lw=2, zorder=3)
    ax.plot([x, x], [q1, q3], color="k", lw=1, zorder=3)


def fig3(st, matched):
    rng = np.random.default_rng(1)
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.8), dpi=200, sharey=True)
    for ax, p in zip(axes, PAIRS):
        strip(ax, 0, st[f"CCI_{p}_P"].values, C_P, rng)
        strip(ax, 1, st[f"CCI_{p}_N"].values, C_N, rng)
        strip(ax, 2, matched[f"CCI_{p}"].values, C_AB, rng)
        ax.set_xticks([0, 1, 2], ["Paretic", "Non-\nparetic", "Able-bodied\n(age-matched)"], fontsize=8)
        ax.set_title(PAIR_LABEL[p], fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Co-contraction index (%)")
    fig.text(0.01, 0.01, f"One dot per participant (stroke n = {len(st)}, age-matched able-bodied n = "
             f"{len(matched)}). Black: median and IQR.", fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGS / "fig3_cci_by_group.png")


def fig4():
    prim = pd.read_csv(TABLES / "stats_primary.csv")
    wp = pd.read_csv(TABLES / "stats_within_person.csv")
    reg = pd.read_csv(TABLES / "stats_regression.csv")
    rows = []
    for _, r in prim.iterrows():
        rows.append((r.pair, f"{r.leg.capitalize()} vs age-matched", r.HL_diff, r.ci_low, r.ci_high, r.p_holm))
    for _, r in wp.iterrows():
        rows.append((r.pair, "Paretic minus non-paretic", r.median_diff_P_minus_N, r.ci_low, r.ci_high, r.p_holm))
    for _, r in reg.iterrows():
        rows.append((r.pair, "Stroke effect, age-adjusted", r.group_effect_age_only, r.ci_low_age_only,
                     r.ci_high_age_only, np.nan))
        rows.append((r.pair, "Stroke effect, speed + age adjusted", r.group_effect_adjusted, r.ci_low,
                     r.ci_high, r.p_holm))
    d = pd.DataFrame(rows, columns=["pair", "comp", "est", "lo", "hi", "p"])
    comps = list(dict.fromkeys(d.comp))
    colors = dict(zip(comps, [C_P, C_N, "#e08b2c", "0.6", "#b03a2e"]))
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.6), dpi=200, sharey=True)
    for ax, pl in zip(axes, [PAIR_LABEL[p] for p in PAIRS]):
        s = d[d.pair == pl].set_index("comp").loc[comps]
        y = np.arange(len(comps))[::-1]
        ax.axvline(0, color="0.3", lw=0.8)
        for yi, (c, r) in zip(y, s.iterrows()):
            ax.errorbar(r.est, yi, xerr=[[r.est - r.lo], [r.hi - r.est]], fmt="o", color=colors[c],
                        capsize=3, ms=5)
        ax.set_title(pl, fontsize=10)
        ax.set_xlabel("Difference in CCI (percentage points)", fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_yticks(np.arange(len(comps))[::-1], comps, fontsize=8)
    fig.text(0.01, 0.01, "Points: Hodges-Lehmann shift (group comparisons), median paired difference "
             "(paretic minus non-paretic) or OLS coefficient (stroke effect). Bars: 95% CI.",
             fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIGS / "fig4_effects_forest.png")


def fig5(st, ab):
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.6), dpi=200, sharey=True)
    slowest = ab.speed_mps.min()
    for ax, p in zip(axes, PAIRS):
        for d, col, c, lab in [(ab, f"CCI_{p}", C_AB, "Able-bodied"), (st, f"CCI_{p}_P", C_P, "Stroke, paretic")]:
            x, y = d.speed_mps.values, d[col].values
            ok = ~np.isnan(y)
            ax.scatter(x[ok], y[ok], s=10, color=c, alpha=0.8, lw=0, label=f"{lab} (n = {ok.sum()})")
            b = np.polyfit(x[ok], y[ok], 1)
            xs = np.linspace(x[ok].min(), x[ok].max(), 2)
            ax.plot(xs, np.polyval(b, xs), color=c, lw=1.5)
        ax.axvspan(0, slowest, color="0.94", zorder=0)
        ax.axvline(slowest, color="0.3", ls="--", lw=0.8)
        ax.set_title(PAIR_LABEL[p], fontsize=10)
        ax.set_xlabel("Walking speed (m/s)")
        ax.set_xlim(0, 1.7)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Co-contraction index (%)")
    axes[0].legend(frameon=False, fontsize=7, loc="lower left")
    fig.text(0.01, 0.01, f"Shaded: slower than any able-bodied adult (< {slowest:.2f} m/s). "
             "Lines: least-squares fit within each group.", fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIGS / "fig5_cci_vs_speed.png")


def main() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    meta = pd.read_csv(ROOT / "data" / "metadata" / "participants.csv")
    outcomes = pd.read_csv(TABLES / "outcomes_per_leg.csv")
    cols = [f"CCI_{p}" for p in PAIRS]
    st, ab, matched = build_sets(meta, outcomes, cols)
    fig3(st, matched)
    fig4()
    fig5(st, ab)
    print("Wrote fig3_cci_by_group.png, fig4_effects_forest.png, fig5_cci_vs_speed.png")


if __name__ == "__main__":
    main()
