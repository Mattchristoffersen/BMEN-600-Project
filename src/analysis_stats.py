"""Main statistical analysis: is co-contraction higher on the paretic leg than in
age-matched able-bodied adults and than on the non-paretic leg, and does any
difference remain once walking speed is accounted for?

Run after src/build_participants.py and src/compute_outcomes.py.

Approach (fixed in the midterm plan, Section 4)
  Primary outcome   whole-stride CCI (Falconer & Winter) for VL-BF, VL-ST, TA-GAS,
                    one value per leg (legs need >= MIN_STRIDES valid strides).
  Main comparison   paretic leg vs 1:1 age-matched able-bodied adults:
                    Mann-Whitney U, Hodges-Lehmann shift, 95% bootstrap CI.
  Speed, 3 ways     1. within person: paretic vs non-paretic leg (Wilcoxon signed-rank)
                    2. speed-matched subset: survivors at or above the slowest
                       able-bodied speed, each compared with the able-bodied adults
                       within 0.10 m/s and 10 years (descriptive only)
                    3. regression CCI ~ group + speed + age (HC3 robust SEs) on all
                       survivors and all able-bodied adults, plus the speed slope
                       within the stroke group alone
  Multiplicity      Holm correction across the three muscle pairs within each test.
  Secondary         stance and swing CCI; % of the stride both muscles are active.
  Sensitivity       minimum strides 1 and 5; activity threshold 15% and 35% (timing);
                    dropping TVC48 (the only hand-supported participant with EMG).

Outputs (results/tables/)
  stats_primary.csv        paretic and non-paretic legs vs age-matched able-bodied
  stats_within_person.csv  paretic vs non-paretic leg
  stats_speed_matched.csv  speed-matched subset (descriptive)
  stats_regression.csv     group effect adjusted for speed and age; within-stroke slope
  stats_secondary.csv      stance, swing and co-activation outcomes
  stats_sensitivity.csv    primary comparison under each sensitivity setting
  analysis_set.csv         who is in the analysis and their matches
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import mannwhitneyu, spearmanr, wilcoxon
from statsmodels.stats.multitest import multipletests

from preliminary_check import age_match

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
PAIRS = ["VL_BF", "VL_ST", "TA_GAS"]
PAIR_LABEL = {"VL_BF": "VL-BF (knee)", "VL_ST": "VL-ST (knee)", "TA_GAS": "TA-GAS (ankle)"}
N_BOOT = 5000
SEED = 600
SPEED_TOL, AGE_TOL = 0.10, 10.0
HAND_HELD_WITH_EMG = ["TVC48"]


# ----------------------------------------------------------------------------- data
def legs_table(outcomes: pd.DataFrame, cols: list[str], min_strides: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Stroke: one row per survivor with _P and _N columns. Able-bodied: mean of the
    available legs. A pair's values are dropped on a leg with < min_strides strides."""
    o = outcomes.copy()
    for p in PAIRS:
        bad = o[f"n_strides_{p}"] < min_strides
        for c in [c for c in cols if p in c]:
            o.loc[bad, c] = np.nan
    st = o[o.group == "stroke"].pivot(index="id", columns="leg", values=cols)
    st.columns = [f"{c}_{'P' if leg == 'paretic' else 'N'}" for c, leg in st.columns]
    ab = o[o.group == "able-bodied"].groupby("id")[cols].mean()
    return st.reset_index(), ab.reset_index()


def build_sets(meta, outcomes, cols, min_strides=3, drop=()):
    st_cci, ab_cci = legs_table(outcomes, cols, min_strides)
    st = meta[(meta.group == "stroke") & ~meta.id.isin(drop)].merge(st_cci, on="id")
    ab = meta[meta.group == "able-bodied"].merge(ab_cci, on="id")
    st_use = st[st[[f"CCI_{p}_P" for p in PAIRS]].notna().any(axis=1)].reset_index(drop=True)
    ab_use = ab[ab[[f"CCI_{p}" for p in PAIRS]].notna().all(axis=1)].reset_index(drop=True)
    matched = age_match(st_use, ab_use).reset_index(drop=True)
    return st_use, ab_use, matched


# ------------------------------------------------------------------------ estimators
def hodges_lehmann(x, y) -> float:
    """Median of all pairwise differences x_i - y_j."""
    return float(np.median(np.subtract.outer(x, y)))


def boot_ci(stat, *samples, paired=False, rng=None) -> tuple[float, float]:
    """Percentile bootstrap, resampling participants (within each group)."""
    rng = rng or np.random.default_rng(SEED)
    vals = np.empty(N_BOOT)
    for b in range(N_BOOT):
        if paired:
            idx = rng.integers(0, len(samples[0]), len(samples[0]))
            vals[b] = stat(*(s[idx] for s in samples))
        else:
            vals[b] = stat(*(s[rng.integers(0, len(s), len(s))] for s in samples))
    return tuple(np.percentile(vals, [2.5, 97.5]))


def med_iqr(x) -> str:
    q1, q2, q3 = np.percentile(x, [25, 50, 75])
    return f"{q2:.1f} [{q1:.1f}-{q3:.1f}]"


def holm(df: pd.DataFrame, pcol="p", out="p_holm") -> pd.DataFrame:
    df[out] = multipletests(df[pcol].values, method="holm")[1]
    return df


# ----------------------------------------------------------------------- comparisons
def between_groups(st, ref, col_st, col_ref, label) -> dict:
    x = st[col_st].dropna().values
    y = ref[col_ref].dropna().values
    u, p = mannwhitneyu(x, y, alternative="two-sided")
    lo, hi = boot_ci(hodges_lehmann, x, y)
    return {"comparison": label, "n_stroke": len(x), "n_ref": len(y),
            "stroke_median_iqr": med_iqr(x), "ref_median_iqr": med_iqr(y),
            "HL_diff": hodges_lehmann(x, y), "ci_low": lo, "ci_high": hi,
            "rank_biserial": 1 - 2 * u / (len(x) * len(y)), "U": u, "p": p}


def within_person(st, col) -> dict:
    d = st[[f"{col}_P", f"{col}_N"]].dropna()
    diff = (d[f"{col}_P"] - d[f"{col}_N"]).values
    w, p = wilcoxon(diff)
    lo, hi = boot_ci(np.median, diff, paired=True)
    return {"n_pairs": len(diff), "paretic_median_iqr": med_iqr(d[f"{col}_P"]),
            "nonparetic_median_iqr": med_iqr(d[f"{col}_N"]),
            "median_diff_P_minus_N": float(np.median(diff)), "ci_low": lo, "ci_high": hi,
            "n_paretic_higher": int((diff > 0).sum()), "W": w, "p": p}


def speed_matched(st_use, ab_use, col_st, col_ab) -> tuple[dict, pd.DataFrame]:
    rows = []
    for _, s in st_use[st_use.speed_mps >= ab_use.speed_mps.min()].iterrows():
        if pd.isna(s[col_st]):
            continue
        near = ab_use[((ab_use.speed_mps - s.speed_mps).abs() <= SPEED_TOL) &
                      ((ab_use.age - s.age).abs() <= AGE_TOL)][col_ab].dropna()
        if len(near):
            rows.append({"id": s.id, "speed": s.speed_mps, "age": s.age, "stroke": s[col_st],
                         "ab_mean": near.mean(), "n_ab": len(near), "diff": s[col_st] - near.mean()})
    r = pd.DataFrame(rows)
    if r.empty:
        return {"n_survivors": 0}, r
    return {"n_survivors": len(r), "median_n_ab_per_survivor": float(r.n_ab.median()),
            "stroke_median_iqr": med_iqr(r.stroke), "ab_median_iqr": med_iqr(r.ab_mean),
            "median_diff": float(r["diff"].median()),
            "n_stroke_higher": int((r["diff"] > 0).sum())}, r


def regression(st_use, ab_use, col_st, col_ab) -> dict:
    d = pd.concat([
        pd.DataFrame({"cci": st_use[col_st], "speed": st_use.speed_mps, "age": st_use.age, "stroke": 1}),
        pd.DataFrame({"cci": ab_use[col_ab], "speed": ab_use.speed_mps, "age": ab_use.age, "stroke": 0}),
    ]).dropna()
    full = smf.ols("cci ~ stroke + speed + age", d).fit(cov_type="HC3")
    unadj = smf.ols("cci ~ stroke + age", d).fit(cov_type="HC3")
    s = d[d.stroke == 1]
    within = smf.ols("cci ~ speed", s).fit(cov_type="HC3")
    a = d[d.stroke == 0]
    within_ab = smf.ols("cci ~ speed", a).fit(cov_type="HC3")
    ci, ciu, ciw, cia = full.conf_int(), unadj.conf_int(), within.conf_int(), within_ab.conf_int()
    return {"n_stroke": int(s.shape[0]), "n_ab": int(a.shape[0]),
            "group_effect_age_only": unadj.params["stroke"], "ci_low_age_only": ciu.loc["stroke", 0],
            "ci_high_age_only": ciu.loc["stroke", 1], "p_age_only": unadj.pvalues["stroke"],
            "group_effect_adjusted": full.params["stroke"], "ci_low": ci.loc["stroke", 0],
            "ci_high": ci.loc["stroke", 1], "p": full.pvalues["stroke"],
            "speed_coef_pooled": full.params["speed"], "r2": full.rsquared,
            "stroke_slope_per_mps": within.params["speed"], "stroke_slope_ci_low": ciw.loc["speed", 0],
            "stroke_slope_ci_high": ciw.loc["speed", 1], "stroke_slope_p": within.pvalues["speed"],
            "stroke_spearman_rho": spearmanr(s.speed, s.cci)[0],
            "ab_slope_per_mps": within_ab.params["speed"], "ab_slope_ci_low": cia.loc["speed", 0],
            "ab_slope_ci_high": cia.loc["speed", 1], "ab_slope_p": within_ab.pvalues["speed"],
            "stroke_speed_range": f"{s.speed.min():.2f}-{s.speed.max():.2f}",
            "ab_speed_range": f"{a.speed.min():.2f}-{a.speed.max():.2f}"}


# ------------------------------------------------------------------------------ main
def main() -> None:
    meta = pd.read_csv(ROOT / "data" / "metadata" / "participants.csv")
    outcomes = pd.read_csv(TABLES / "outcomes_per_leg.csv")
    cci_cols = [f"CCI_{p}{s}" for p in PAIRS for s in ("", "_stance", "_swing")]
    coact_cols = [c for c in outcomes.columns if c.startswith("pct_coactive_")]
    cols = cci_cols + coact_cols

    st_use, ab_use, matched = build_sets(meta, outcomes, cols)
    pd.concat([st_use[["id", "group", "age", "sex", "speed_mps"]].assign(matched_to=np.nan),
               matched[["id", "group", "age", "sex", "speed_mps", "matched_to"]]]
              ).to_csv(TABLES / "analysis_set.csv", index=False)

    # Primary: paretic vs age-matched; also non-paretic vs age-matched
    prim = []
    for leg, tag in [("paretic", "P"), ("non-paretic", "N")]:
        rows = [{"pair": PAIR_LABEL[p], "leg": leg,
                 **between_groups(st_use, matched, f"CCI_{p}_{tag}", f"CCI_{p}", f"{leg} vs age-matched AB")}
                for p in PAIRS]
        prim.append(holm(pd.DataFrame(rows)))
    primary = pd.concat(prim)
    primary.round(4).to_csv(TABLES / "stats_primary.csv", index=False)

    # Speed 1: within person
    wp = holm(pd.DataFrame([{"pair": PAIR_LABEL[p], **within_person(st_use, f"CCI_{p}")} for p in PAIRS]))
    wp.round(4).to_csv(TABLES / "stats_within_person.csv", index=False)

    # Speed 2: speed-matched subset (descriptive)
    sm_rows, sm_detail = [], []
    for p in PAIRS:
        summ, det = speed_matched(st_use, ab_use, f"CCI_{p}_P", f"CCI_{p}")
        sm_rows.append({"pair": PAIR_LABEL[p], **summ})
        sm_detail.append(det.assign(pair=PAIR_LABEL[p]))
    pd.DataFrame(sm_rows).round(3).to_csv(TABLES / "stats_speed_matched.csv", index=False)
    pd.concat(sm_detail).round(3).to_csv(TABLES / "speed_matched_detail.csv", index=False)

    # Speed 3: regression
    reg = pd.DataFrame([{"pair": PAIR_LABEL[p], **regression(st_use, ab_use, f"CCI_{p}_P", f"CCI_{p}")}
                        for p in PAIRS])
    reg = holm(reg, "p", "p_holm")
    reg.round(4).to_csv(TABLES / "stats_regression.csv", index=False)

    # Secondary: stance, swing, co-activation (paretic vs age-matched, and P vs N)
    sec = []
    sec_specs = [(f"CCI_{p}_{ph}", f"CCI {ph}", p) for ph in ("stance", "swing") for p in PAIRS]
    sec_specs += [(f"pct_coactive_{p}_25", "% stride co-active (25%)", p) for p in PAIRS
                  if f"pct_coactive_{p}_25" in outcomes.columns]
    for col, name, p in sec_specs:
        bg = between_groups(st_use, matched, f"{col}_P", col, "paretic vs age-matched AB")
        w = within_person(st_use, col)
        sec.append({"outcome": name, "pair": PAIR_LABEL[p],
                    "paretic": bg["stroke_median_iqr"], "nonparetic": w["nonparetic_median_iqr"],
                    "ab_matched": bg["ref_median_iqr"],
                    "HL_P_vs_AB": bg["HL_diff"], "ci_low": bg["ci_low"], "ci_high": bg["ci_high"],
                    "p_P_vs_AB": bg["p"], "median_P_minus_N": w["median_diff_P_minus_N"], "p_P_vs_N": w["p"]})
    sec = pd.DataFrame(sec)
    for name in sec.outcome.unique():
        m = sec.outcome == name
        sec.loc[m, "p_holm_P_vs_AB"] = multipletests(sec.loc[m, "p_P_vs_AB"], method="holm")[1]
        sec.loc[m, "p_holm_P_vs_N"] = multipletests(sec.loc[m, "p_P_vs_N"], method="holm")[1]
    sec.round(4).to_csv(TABLES / "stats_secondary.csv", index=False)

    # Sensitivity: primary comparison under alternative settings
    sens = []
    settings = [("main (min 3 strides)", 3, ()), ("min 1 stride", 1, ()), ("min 5 strides", 5, ()),
                ("drop TVC48 (hand-held)", 3, tuple(HAND_HELD_WITH_EMG))]
    for name, ms, drop in settings:
        s_use, a_use, mt = build_sets(meta, outcomes, cols, ms, drop)
        rows = [between_groups(s_use, mt, f"CCI_{p}_P", f"CCI_{p}", "") | {"pair": PAIR_LABEL[p]} for p in PAIRS]
        r = holm(pd.DataFrame(rows))
        wpr = holm(pd.DataFrame([within_person(s_use, f"CCI_{p}") for p in PAIRS]))
        for i, p in enumerate(PAIRS):
            sens.append({"setting": name, "pair": PAIR_LABEL[p], "n_stroke": r.n_stroke[i],
                         "HL_P_vs_AB": r.HL_diff[i], "ci_low": r.ci_low[i], "ci_high": r.ci_high[i],
                         "p_holm_P_vs_AB": r.p_holm[i], "median_P_minus_N": wpr.median_diff_P_minus_N[i],
                         "p_holm_P_vs_N": wpr.p_holm[i]})
    for thr in (15, 25, 35):
        cols_t = [f"pct_coactive_{p}_{thr}" for p in PAIRS]
        if not all(c in outcomes.columns for c in cols_t):
            continue
        rows = [between_groups(st_use, matched, f"pct_coactive_{p}_{thr}_P", f"pct_coactive_{p}_{thr}", "")
                for p in PAIRS]
        r = holm(pd.DataFrame(rows))
        for i, p in enumerate(PAIRS):
            sens.append({"setting": f"co-active %, threshold {thr}%", "pair": PAIR_LABEL[p],
                         "n_stroke": r.n_stroke[i], "HL_P_vs_AB": r.HL_diff[i], "ci_low": r.ci_low[i],
                         "ci_high": r.ci_high[i], "p_holm_P_vs_AB": r.p_holm[i]})
    pd.DataFrame(sens).round(4).to_csv(TABLES / "stats_sensitivity.csv", index=False)

    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(f"Analysis set: {len(st_use)} stroke, {len(ab_use)} able-bodied, {len(matched)} age-matched "
          f"(age gap mean {matched.age_gap.mean():.1f}, max {matched.age_gap.max():.0f} y)\n")
    print("PRIMARY\n", primary[["pair", "leg", "stroke_median_iqr", "ref_median_iqr", "HL_diff", "ci_low",
                                "ci_high", "p", "p_holm"]].round(3).to_string(index=False), "\n")
    print("WITHIN PERSON\n", wp[["pair", "n_pairs", "median_diff_P_minus_N", "ci_low", "ci_high",
                                 "n_paretic_higher", "p_holm"]].round(3).to_string(index=False), "\n")
    print("SPEED-MATCHED\n", pd.DataFrame(sm_rows).round(2).to_string(index=False), "\n")
    print("REGRESSION\n", reg[["pair", "group_effect_age_only", "group_effect_adjusted", "ci_low", "ci_high",
                               "p_holm", "stroke_slope_per_mps", "stroke_slope_ci_low", "stroke_slope_ci_high",
                               "ab_slope_per_mps"]].round(2).to_string(index=False), "\n")
    print("SECONDARY\n", sec.round(3).to_string(index=False), "\n")
    print("SENSITIVITY\n", pd.DataFrame(sens).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
