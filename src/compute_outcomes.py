"""Compute co-contraction and activation outcomes for every stride, then average
them per participant leg, so each leg contributes one value to later statistics.

Outputs
  results/tables/strides_per_leg.csv   valid strides per muscle and leg (data quality)
  results/tables/outcomes_per_leg.csv  one row per participant leg

Co-contraction index (Falconer & Winter, 1985):
    CCI = 2 * sum(min(A, B)) / sum(A + B) * 100
A and B are the two muscles' amplitude-normalized envelopes. CCI is computed over
the whole stride and separately over stance (heel strike to toe-off) and swing.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from load_data import MUSCLES, iter_legs

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
PAIRS = {"VL_BF": ("VL", "BF"), "VL_ST": ("VL", "ST"), "TA_GAS": ("TA", "GAS")}
ON_THRESHOLD = 0.25  # muscle counted "on" above 25% of its maximum (sensitivity: 0.15, 0.35)


def cci(a: np.ndarray, b: np.ndarray) -> float:
    total = np.sum(a + b)
    return np.nan if total == 0 else 200.0 * np.sum(np.minimum(a, b)) / total


def leg_outcomes(leg: dict) -> tuple[dict, dict]:
    emg, toe_off = leg["emg"], leg["toe_off"]
    n_strides = emg["VL"].shape[0]
    counts = {m: int((~np.isnan(emg[m]).any(axis=1)).sum()) for m in MUSCLES}
    out = {"n_strides": n_strides}

    for name, (m1, m2) in PAIRS.items():
        whole, stance, swing = [], [], []
        for s in range(n_strides):
            a, b = emg[m1][s], emg[m2][s]
            if np.isnan(a).any() or np.isnan(b).any():
                continue
            whole.append(cci(a, b))
            to = toe_off[s] if s < len(toe_off) else np.nan
            if np.isfinite(to):
                k = int(round(to)) - 1  # events are 1-based sample numbers
                stance.append(cci(a[:k], b[:k]))
                swing.append(cci(a[k:], b[k:]))
        out[f"CCI_{name}"] = np.nanmean(whole) if whole else np.nan
        out[f"CCI_{name}_stance"] = np.nanmean(stance) if stance else np.nan
        out[f"CCI_{name}_swing"] = np.nanmean(swing) if swing else np.nan
        out[f"n_strides_{name}"] = len(whole)

    for m in MUSCLES:
        valid = emg[m][~np.isnan(emg[m]).any(axis=1)]
        out[f"pct_active_{m}"] = (100 * (valid > ON_THRESHOLD).mean(axis=1).mean()
                                  if len(valid) else np.nan)
    stance_pct = toe_off[np.isfinite(toe_off)] / 10.0
    out["stance_pct"] = stance_pct.mean() if len(stance_pct) else np.nan
    return counts, out


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    count_rows, outcome_rows = [], []
    for group in ["stroke", "able-bodied"]:
        for leg in iter_legs(group):
            counts, out = leg_outcomes(leg)
            key = {"id": leg["id"], "group": group, "leg": leg["leg"]}
            count_rows.append({**key, "n_strides": out["n_strides"], **counts})
            outcome_rows.append({**key, **out})
    pd.DataFrame(count_rows).to_csv(TABLES / "strides_per_leg.csv", index=False)
    pd.DataFrame(outcome_rows).round(3).to_csv(TABLES / "outcomes_per_leg.csv", index=False)
    print(f"Wrote {len(outcome_rows)} legs to {TABLES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
