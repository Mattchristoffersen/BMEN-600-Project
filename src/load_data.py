"""Read the stride-normalized EMG and gait events from the dataset's MAT files.

The MAT files are MATLAB v7.3 (HDF5), so they are read with h5py.
Each participant's legs are returned as a dictionary:

    {"id": "TVC03", "group": "stroke", "leg": "paretic",
     "emg": {"VL": array(strides, 1001), ...},   # amplitude-normalized envelopes (0-1)
     "toe_off": array(strides)}                  # toe-off as a sample index (1-1001)

Only ipsilateral data are used: e.g. paretic-leg EMG from strides segmented on
paretic-leg heel strikes (PsideSegm_PsideData).
"""
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MAT_FILES = {
    "stroke": RAW / "MAT_normalizedData_PostStrokeAdults_v27-02-23.mat",
    "able-bodied": RAW / "MAT_normalizedData_AbleBodiedAdults_v06-03-23.mat",
}
MUSCLES = ["VL", "BF", "ST", "TA", "GAS"]

# (field with the leg's own strides, event prefix, leg label)
LEGS = {
    "stroke": [("PsideSegm_PsideData", "P", "paretic"),
               ("NsideSegm_NsideData", "N", "non-paretic")],
    "able-bodied": [("LsideSegm_LsideData", "L", "left"),
                    ("RsideSegm_RsideData", "R", "right")],
}


def participant_ids(group: str) -> list[str]:
    """IDs in the order of Data.Sub(1..n), from data/metadata/participants.csv
    (built by src/build_participants.py)."""
    meta = pd.read_csv(ROOT / "data" / "metadata" / "participants.csv")
    meta = meta[meta.group == group].sort_values("mat_index")
    return meta["id"].tolist()


def iter_legs(group: str):
    """Yield one dictionary per participant leg (see module docstring)."""
    ids = participant_ids(group)
    with h5py.File(MAT_FILES[group], "r") as f:
        sub = f["Sub"]
        for i, pid in enumerate(ids):
            events = f[sub["events"][i, 0]]
            for field, prefix, leg in LEGS[group]:
                data = f[sub[field][i, 0]]
                emg = {m: np.array(data[f"{m}norm"]["n"]) for m in MUSCLES}
                toe_off = np.array(events[f"{prefix}_TOnorm"]).ravel()
                yield {"id": pid, "group": group, "leg": leg, "emg": emg, "toe_off": toe_off}
