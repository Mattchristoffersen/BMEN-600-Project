"""Midterm progress check: sample, data quality, speed overlap and a first look at
co-contraction (descriptive only, no hypothesis tests yet).

Run after src/build_participants.py and src/compute_outcomes.py.

Outputs
  results/tables/table1_sample_and_quality.csv
  results/tables/table2_cci_by_group.csv
  results/tables/fig1_points.csv              (data behind Figure 1)
  results/figures/fig1_ankle_cci_vs_speed.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
TABLES, FIGS = ROOT / "results" / "tables", ROOT / "results" / "figures"
PAIRS = ["VL_BF", "VL_ST", "TA_GAS"]
MIN_STRIDES = 3  # a leg needs at least 3 valid strides for a pair


def per_participant(outcomes: pd.DataFrame) -> pd.DataFrame:
    """One row per participant: paretic and non-paretic legs for stroke, and the mean
    of the available legs for able-bodied adults (left TA is often missing)."""
    o = outcomes.copy()
    for p in PAIRS:
        o.loc[o[f"n_strides_{p}"] < MIN_STRIDES, f"CCI_{p}"] = np.nan
    st = o[o.group == "stroke"].pivot(index="id", columns="leg", values=[f"CCI_{p}" for p in PAIRS])
    st.columns = [f"{c}_{'P' if leg == 'paretic' else 'N'}" for c, leg in st.columns]
    ab = o[o.group == "able-bodied"].groupby("id")[[f"CCI_{p}" for p in PAIRS]].mean()
    return st.reset_index(), ab.reset_index()


def age_match(stroke: pd.DataFrame, ab: pd.DataFrame) -> pd.DataFrame:
    """1:1 nearest-age matching without replacement (minimizes total age difference)."""
    cost = np.abs(stroke.age.values[:, None] - ab.age.values[None, :])
    r, c = linear_sum_assignment(cost)
    return ab.iloc[c].assign(matched_to=stroke.id.values[r], age_gap=cost[r, c])


def med_iqr(s: pd.Series, dp: int = 1) -> str:
    s = s.dropna()
    q1, q2, q3 = np.percentile(s, [25, 50, 75])
    return f"{q2:.{dp}f} [{q1:.{dp}f}–{q3:.{dp}f}]"


def main() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    meta = pd.read_csv(ROOT / "data" / "metadata" / "participants.csv")
    outcomes = pd.read_csv(TABLES / "outcomes_per_leg.csv")
    st_cci, ab_cci = per_participant(outcomes)

    st = meta[meta.group == "stroke"].merge(st_cci, on="id")
    ab = meta[meta.group == "able-bodied"].merge(ab_cci, on="id")
    st_use = st[st[[f"CCI_{p}_P" for p in PAIRS]].notna().any(axis=1)]          # paretic EMG
    ab_use = ab[ab[[f"CCI_{p}" for p in PAIRS]].notna().all(axis=1)]            # all 3 pairs
    ab_matched = age_match(st_use.reset_index(drop=True), ab_use.reset_index(drop=True))

    slowest_ab = ab_use.speed_mps.min()
    overlap = st_use[st_use.speed_mps >= slowest_ab]

    # Table 1: sample and data quality
    strides = outcomes.groupby(["group"]).n_strides.median()
    t1 = pd.DataFrame({
        "Stroke": [50, 47, int((st.emg_any_paretic | st["emg_any_non-paretic"]).sum()),
                   len(st_use), f"{st_use.age.median():.0f} ({st_use.age.min():.0f}–{st_use.age.max():.0f})",
                   med_iqr(st_use.speed_mps, 2), f"{int(strides['stroke'])}", len(overlap)],
        "Able-bodied (all with EMG)": [138, 111, int((ab.emg_any_left | ab.emg_any_right).sum()), len(ab_use),
                                       f"{ab_use.age.median():.0f} ({ab_use.age.min():.0f}–{ab_use.age.max():.0f})",
                                       med_iqr(ab_use.speed_mps, 2), f"{int(strides['able-bodied'])}", "—"],
        "Able-bodied (age-matched)": ["—", "—", "—", len(ab_matched),
                                      f"{ab_matched.age.median():.0f} ({ab_matched.age.min():.0f}–{ab_matched.age.max():.0f})",
                                      med_iqr(ab_matched.speed_mps, 2), "—", "—"],
    }, index=["Participants in dataset", "With EMG (paper)", "With any EMG in MAT file",
              "Analysis set", "Age, years: median (range)", "Speed, m/s: median [IQR]",
              "Strides per leg: median", f"Stroke at or above slowest able-bodied speed ({slowest_ab:.2f} m/s)"])
    t1.to_csv(TABLES / "table1_sample_and_quality.csv")

    # Table 2: CCI by group (descriptive) and correlation with speed
    rows = []
    for p in PAIRS:
        rows.append({"pair": p,
                     "paretic": med_iqr(st_use[f"CCI_{p}_P"]), "n_P": st_use[f"CCI_{p}_P"].notna().sum(),
                     "non_paretic": med_iqr(st_use[f"CCI_{p}_N"]), "n_N": st_use[f"CCI_{p}_N"].notna().sum(),
                     "able_bodied_age_matched": med_iqr(ab_matched[f"CCI_{p}"]), "n_AB": len(ab_matched),
                     "paired_diff_P_minus_N": med_iqr(st_use[f"CCI_{p}_P"] - st_use[f"CCI_{p}_N"]),
                     "rho_speed_stroke_P": round(spearmanr(st_use.speed_mps, st_use[f"CCI_{p}_P"], nan_policy="omit")[0], 2),
                     "rho_speed_AB_all": round(spearmanr(ab_use.speed_mps, ab_use[f"CCI_{p}"], nan_policy="omit")[0], 2)})
    pd.DataFrame(rows).to_csv(TABLES / "table2_cci_by_group.csv", index=False)

    # Figure 1: ankle CCI against walking speed
    pts = pd.concat([
        pd.DataFrame({"id": ab_use.id, "series": "Able-bodied", "speed_mps": ab_use.speed_mps,
                      "cci": ab_use.CCI_TA_GAS, "age_matched": ab_use.id.isin(ab_matched.id)}),
        pd.DataFrame({"id": st_use.id, "series": "Stroke, paretic leg", "speed_mps": st_use.speed_mps,
                      "cci": st_use.CCI_TA_GAS_P, "age_matched": True}),
    ]).dropna(subset=["cci"])
    pts.round(3).to_csv(TABLES / "fig1_points.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)
    a = pts[pts.series == "Able-bodied"]
    s = pts[pts.series != "Able-bodied"]
    ax.scatter(a.speed_mps, a.cci, s=18, c="0.65", label=f"Able-bodied (n = {len(a)})")
    ax.scatter(s.speed_mps, s.cci, s=22, c="#2f6fdb", label=f"Stroke, paretic leg (n = {len(s)})")
    ax.set_ylim(10, 75)
    ax.axvspan(0, slowest_ab, color="0.94", zorder=0)
    ax.axvline(slowest_ab, color="0.3", ls="--", lw=1)
    ax.text(0.02, 73, "No able-bodied adult walked this slowly", va="top", fontsize=8, color="0.35")
    ax.text(slowest_ab + 0.01, 11.5, f"slowest able-bodied adult: {slowest_ab:.2f} m/s",
            va="bottom", fontsize=8, color="0.3")
    ax.set_xlim(0, 1.7)
    ax.set_title(f"Only {len(overlap)} of {len(st_use)} stroke survivors walk as fast as the slowest "
                 "able-bodied adult", fontsize=10, loc="left")
    ax.set_xlabel("Walking speed (m/s)")
    ax.set_ylabel("TA–GAS co-contraction index (%)")
    ax.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1, 1.0))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGS / "fig1_ankle_cci_vs_speed.png")

    print(t1.to_string())
    print(pd.DataFrame(rows).to_string())
    print(f"Age gap after matching: mean {ab_matched.age_gap.mean():.1f} y, max {ab_matched.age_gap.max():.0f} y")
    print("Stroke within able-bodied speed range:", ", ".join(overlap.id))


if __name__ == "__main__":
    main()
