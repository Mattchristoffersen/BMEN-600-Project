"""Build one participant table from the MAT files, cross-checked against the paper.

Inputs
  data/raw/MAT_normalizedData_PostStrokeAdults_v27-02-23.mat
  data/raw/MAT_normalizedData_AbleBodiedAdults_v06-03-23.mat
  data/raw/supplementary_information.pdf  (Van Criekinge et al., Sci. Data 10, 852, 2023)
Output
  data/metadata/participants.csv  (one row per participant, ordered as Data.Sub(1..n))

What we found while building it (see README, "Data checks"):
  * Supplementary Table 5 (walking speed) and the paper's list of participants without
    EMG follow the MAT order, Sub(n) = SUBJn. Supplementary Table 1 (able-bodied age,
    height) uses a different order from SUBJ15 onwards, so age, sex and body size are
    taken from the MAT file (sub_char), not from Table 1.
  * Stroke participants are in the same order in the MAT file and Tables 2 and 5.
  * Walking speed is computed from the MAT file (centre-of-mass travel per stride /
    stride time) and checked against Table 5.
"""
import re
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from pypdf import PdfReader

from load_data import LEGS, MAT_FILES, MUSCLES

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data" / "raw" / "supplementary_information.pdf"
OUT = ROOT / "data" / "metadata" / "participants.csv"
HAND_HELD = {"TVC48", "TVC51", "TVC54"}  # walked holding a physiotherapist's hand


def pdf_tables() -> tuple[pd.DataFrame, dict]:
    """Stroke rows of Supplementary Table 2 (in order) and all Table 5 speeds."""
    text = "\n".join(p.extract_text(extraction_mode="layout") for p in PdfReader(PDF).pages)
    t2 = text[text.index("Supplementary Table 2"):text.index("Supplementary Table 3")]
    rows = [dict(id=m[0], t2_age=int(m[1]), t2_height=int(m[4]), stroke_type=m[8])
            for m in re.findall(r"(TVC\d+)\s+(\d+)\s+([MF])\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)"
                                r"\s+([LR])\s+([IH])\s+\d\s+\d+\s+\d+", t2)]
    t5 = text[text.index("Supplementary table 5"):]
    speeds = {m[0].replace(" ", ""): (float(m[1]) + float(m[2])) / 2
              for m in re.findall(r"(SUBJ\s*\d+|TVC\d+)\s+(\d\.\d+)\s+(\d\.\d+)", t5)}
    return pd.DataFrame(rows), speeds


def scalar(group, key):
    return float(np.array(group[key]).ravel()[0]) if key in group else np.nan


def main() -> None:
    t2, t5 = pdf_tables()
    out = []
    for group, mat in MAT_FILES.items():
        with h5py.File(mat, "r") as f:
            sub = f["Sub"]
            n = sub["sub_char"].shape[0]
            for i in range(n):
                sc, ev, mc = (f[sub[k][i, 0]] for k in ("sub_char", "events", "meas_char"))
                rate = scalar(mc, "VideoFrameRate")
                row = {"mat_index": i + 1, "group": group, "age": scalar(sc, "Age"),
                       "sex": "M" if scalar(sc, "Male") == 1 else "F",
                       "height_mm": scalar(sc, "Height"), "leg_mm": scalar(sc, "LegLength"),
                       "mass_kg": scalar(sc, "Weight")}
                if group == "stroke":
                    row.update(days_post_stroke=scalar(sc, "TPS"),
                               paretic_side="L" if scalar(sc, "LesionLeft") == 0 else "R",
                               FAC=scalar(sc, "FAC"), POMA=scalar(sc, "POMA"), TIS=scalar(sc, "TIS"))
                speeds = []
                for field, prefix, leg in LEGS[group]:
                    seg = prefix + "sideSegm_BsideData"
                    com = np.array(f[sub[seg][i, 0]]["CentreOfMass"]["x"])  # strides x 1001, mm
                    dur = (np.array(ev[f"{prefix}_ICstop"]).ravel() - np.array(ev[f"{prefix}_ICstart"]).ravel()) / rate
                    speeds.append(np.nanmean(np.abs(com[:, -1] - com[:, 0]) / 1000 / dur))
                    data = f[sub[field][i, 0]]
                    ok = {m: int((~np.isnan(np.array(data[f"{m}norm"]["n"])).any(axis=1)).sum())
                          for m in MUSCLES}
                    row[f"strides_{leg}"] = int(np.array(data["VLnorm"]["n"]).shape[0])
                    row[f"emg_all5_{leg}"] = all(v > 0 for v in ok.values())
                    row[f"emg_any_{leg}"] = any(v > 0 for v in ok.values())
                row["speed_mps"] = float(np.nanmean(speeds))
                out.append(row)

    df = pd.DataFrame(out)
    st = df.group == "stroke"
    if st.sum() != len(t2):
        sys.exit("Stroke count differs between the MAT file and Supplementary Table 2")
    df.loc[st, "id"] = t2.id.values
    df.loc[st, "stroke_type"] = t2.stroke_type.values
    order_ok = (np.abs(df.loc[st, "age"].values - t2.t2_age.values) <= 1).all() and \
               (np.abs(df.loc[st, "height_mm"].values - t2.t2_height.values) <= 10).all()
    if not order_ok:
        sys.exit("Stroke order in the MAT file does not match Supplementary Table 2")
    df.loc[~st, "id"] = [f"SUBJ{k}" for k in df.loc[~st, "mat_index"]]
    df["speed_table5_mps"] = df.id.map(t5)
    df["speed_source"] = np.where(df.speed_mps.notna(), "MAT", "Table 5")
    diff = (df.speed_mps - df.speed_table5_mps).abs()
    df["speed_mps"] = df.speed_mps.fillna(df.speed_table5_mps)  # no centre-of-mass data
    df["hand_held"] = df.id.isin(HAND_HELD)
    print(f"Speed from MAT vs Table 5: median |diff| {diff.median():.3f} m/s, "
          f"max {diff.max():.3f} m/s ({df.id[diff.idxmax()]})")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = ["id", "group", "mat_index"] + [c for c in df.columns if c not in ("id", "group", "mat_index")]
    df[cols].round(4).to_csv(OUT, index=False)
    print(f"Wrote {OUT.relative_to(ROOT)}: {(~st).sum()} able-bodied, {st.sum()} stroke")


if __name__ == "__main__":
    main()
