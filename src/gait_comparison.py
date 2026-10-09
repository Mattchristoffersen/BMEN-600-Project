"""Gait comparison: stroke survivors vs. age-matched able-bodied adults.

Two spatiotemporal gait measures, no EMG:
  - walking speed (m/s), one value per participant
  - stance phase (% of the gait cycle from heel strike to toe-off), per leg

Uses the same analysis set and 1:1 age-matching as src/preliminary_check.py.
Descriptive only (medians and IQRs); no hypothesis tests.

Run after src/build_participants.py and src/compute_outcomes.py.

Outputs
  results/tables/fig2_points.csv   (data behind Figure 2)
  results/figures/fig2_gait_stroke_vs_able_bodied.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from preliminary_check import FIGS, PAIRS, ROOT, TABLES, age_match, per_participant

COLORS = {"Able-bodied (age-matched)": "0.55", "Stroke, non-paretic leg": "#9db9ec",
          "Stroke, paretic leg": "#2f6fdb", "Stroke": "#2f6fdb"}


def main() -> None:
    meta = pd.read_csv(ROOT / "data" / "metadata" / "participants.csv")
    outcomes = pd.read_csv(TABLES / "outcomes_per_leg.csv")
    st_cci, ab_cci = per_participant(outcomes)
    st = meta[meta.group == "stroke"].merge(st_cci, on="id")
    ab = meta[meta.group == "able-bodied"].merge(ab_cci, on="id")
    st_use = st[st[[f"CCI_{p}_P" for p in PAIRS]].notna().any(axis=1)].reset_index(drop=True)
    ab_use = ab[ab[[f"CCI_{p}" for p in PAIRS]].notna().all(axis=1)].reset_index(drop=True)
    ab_matched = age_match(st_use, ab_use)

    stance = outcomes.pivot_table(index="id", columns="leg", values="stance_pct")
    ab_stance = outcomes[outcomes.group == "able-bodied"].groupby("id").stance_pct.mean()

    pts = pd.concat([
        pd.DataFrame({"id": ab_matched.id, "series": "Able-bodied (age-matched)",
                      "speed_mps": ab_matched.speed_mps.values,
                      "stance_pct": ab_stance.reindex(ab_matched.id).values}),
        pd.DataFrame({"id": st_use.id, "series": "Stroke, paretic leg", "speed_mps": st_use.speed_mps,
                      "stance_pct": stance["paretic"].reindex(st_use.id).values}),
        pd.DataFrame({"id": st_use.id, "series": "Stroke, non-paretic leg", "speed_mps": st_use.speed_mps,
                      "stance_pct": stance["non-paretic"].reindex(st_use.id).values}),
    ])
    pts.round(3).to_csv(TABLES / "fig2_points.csv", index=False)

    rng = np.random.default_rng(0)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.4), dpi=200, gridspec_kw={"width_ratios": [2, 3]})

    def strip(ax, groups, col, labels):
        data = [g[col].dropna().values for g in groups]
        bp = ax.boxplot(data, widths=0.5, showfliers=False, patch_artist=True,
                        medianprops={"color": "k", "lw": 1.5}, whiskerprops={"color": "0.4"},
                        capprops={"color": "0.4"})
        for patch in bp["boxes"]:
            patch.set(facecolor="none", edgecolor="0.4")
        for i, (d, lab) in enumerate(zip(data, labels), start=1):
            ax.scatter(i + rng.uniform(-0.15, 0.15, len(d)), d, s=14, alpha=0.8,
                       c=COLORS[lab], edgecolors="none", zorder=3)
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels([f"{lab.replace(', ', chr(10))}\n(n = {len(d)})" for lab, d in zip(labels, data)],
                           fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        return data

    a = pts[pts.series == "Able-bodied (age-matched)"]
    p = pts[pts.series == "Stroke, paretic leg"]
    n = pts[pts.series == "Stroke, non-paretic leg"]

    sp = strip(ax1, [a, p], "speed_mps", ["Able-bodied (age-matched)", "Stroke"])
    ax1.set_ylabel("Walking speed (m/s)")
    ax1.set_ylim(0, 1.8)
    ax1.set_title("A  Walking speed", fontsize=10, loc="left")

    sd = strip(ax2, [a, n, p], "stance_pct", ["Able-bodied (age-matched)", "Stroke, non-paretic leg",
                                              "Stroke, paretic leg"])
    ax2.axhline(60, color="0.3", ls="--", lw=0.8, zorder=0)
    ax2.text(0.55, 59.6, "typical adult ~60%", fontsize=7, color="0.35", ha="left", va="top")
    ax2.set_ylabel("Stance phase (% of gait cycle)")
    ax2.set_title("B  Time spent in stance", fontsize=10, loc="left")

    fig.suptitle(f"Stroke survivors walk {np.median(sp[0]) / np.median(sp[1]):.0f}× slower and stay "
                 "longer in stance than age-matched adults", fontsize=11, x=0.01, ha="left")
    fig.text(0.01, 0.005, "Boxes: median and IQR; dots: one per participant (stance = mean of strides; "
             "able-bodied = mean of left and right legs). Van Criekinge et al. 2023.",
             fontsize=6.5, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    fig.savefig(FIGS / "fig2_gait_stroke_vs_able_bodied.png")

    def med(x):
        q1, q2, q3 = np.percentile(x, [25, 50, 75])
        return f"{q2:.2f} [{q1:.2f}–{q3:.2f}]"
    print("Speed  AB:", med(sp[0]), " stroke:", med(sp[1]))
    print("Stance AB:", med(sd[0]), " non-paretic:", med(sd[1]), " paretic:", med(sd[2]))
    print("Paretic minus non-paretic stance, median:", round(np.nanmedian(p.stance_pct.values - n.stance_pct.values), 2))


if __name__ == "__main__":
    main()
