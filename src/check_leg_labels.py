"""Data check: are the paretic (P) and non-paretic (N) labels on the right legs?

Why: in the midterm check the "paretic" leg had the longer stance phase in most
survivors, the reverse of the usual hemiparetic pattern (the paretic leg usually has
the shorter stance and less knee flexion in swing).

What this script tests, per survivor and leg
  1. Toe-off events vs each foot's own toe marker. Event toe-off (P_TOnorm/N_TOnorm)
     is compared with the first sample after 35% of the stride at which the toe
     marker's horizontal speed exceeds 25% of its stride maximum. If they agree, the
     events belong to the foot whose data they sit with.
  2. Stance phase (% of stride) on each leg.
  3. Peak knee flexion in swing (sagittal KneeAngles, 50-100% of the stride).

The physical side (left/right) of each leg cannot be checked from the markers,
because every leg's markers are expressed in the same mirrored frame.

Run after src/build_participants.py.

Output
  results/tables/leg_label_check.csv   one row per survivor
"""
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from load_data import MAT_FILES, participant_ids

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "tables" / "leg_label_check.csv"


def marker_toe_off(seg) -> np.ndarray:
    x, y = np.array(seg["TOE"]["x"]), np.array(seg["TOE"]["y"])
    out = []
    for s in range(x.shape[0]):
        v = np.hypot(np.diff(x[s]), np.diff(y[s]))
        if np.isnan(v).all():
            out.append(np.nan)
            continue
        i = np.where(v[350:] > 0.25 * np.nanmax(v))[0]
        out.append((350 + i[0]) / 10 if len(i) else np.nan)
    return np.array(out)


def main() -> None:
    meta = pd.read_csv(ROOT / "data" / "metadata" / "participants.csv")
    rows = []
    with h5py.File(MAT_FILES["stroke"], "r") as f:
        sub = f["Sub"]
        for i, pid in enumerate(participant_ids("stroke")):
            ev, r = f[sub["events"][i, 0]], {"id": pid}
            for side in "PN":
                seg = f[sub[f"{side}sideSegm_{side}sideData"][i, 0]]
                ev_to = np.array(ev[f"{side}_TOnorm"]).ravel() / 10
                mk = marker_toe_off(seg)
                n = min(len(mk), len(ev_to))
                knee = np.array(seg["KneeAngles"]["x"])[:, 500:]
                ok = ~np.isnan(knee).all(axis=1)
                r[f"stance_pct_{side}"] = np.nanmean(ev_to)
                r[f"toe_off_marker_vs_event_{side}"] = np.nanmedian(np.abs(mk[:n] - ev_to[:n]))
                r[f"peak_swing_knee_flex_{side}"] = np.nanmax(knee[ok], axis=1).mean() if ok.any() else np.nan
            rows.append(r)
    d = pd.DataFrame(rows).merge(meta[["id", "paretic_side", "speed_mps"]], on="id")
    d["P_longer_stance"] = d.stance_pct_P > d.stance_pct_N
    d["P_more_knee_flex"] = d.peak_swing_knee_flex_P > d.peak_swing_knee_flex_N
    d["both_atypical"] = d.P_longer_stance & d.P_more_knee_flex
    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.round(2).to_csv(OUT, index=False)
    k = d[["peak_swing_knee_flex_P", "peak_swing_knee_flex_N"]].notna().all(axis=1)
    print(f"Toe-off marker vs event, median |diff| (% stride): P {d.toe_off_marker_vs_event_P.median():.1f}, "
          f"N {d.toe_off_marker_vs_event_N.median():.1f}")
    print(f"'Paretic' leg has the longer stance:      {d.P_longer_stance.sum()} / {len(d)}")
    print(f"'Paretic' leg has more swing knee flexion: {d[k].P_more_knee_flex.sum()} / {k.sum()}")
    print(f"Both (the non-paretic pattern):            {d[k].both_atypical.sum()} / {k.sum()}")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
