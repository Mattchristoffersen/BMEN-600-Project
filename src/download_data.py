"""Download the files this project needs into data/raw/ (about 9.2 GB in total).

Sources
  Figshare collection (CC0): doi:10.6084/m9.figshare.c.6503791.v1
  Supplementary Information of Van Criekinge et al., Sci. Data 10, 852 (2023), CC BY 4.0

Files that already exist with the expected size are skipped, so the script can be
rerun after an interrupted download.
"""
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

FILES = {
    # name in data/raw: (url, size in bytes or None)
    "MAT_normalizedData_PostStrokeAdults_v27-02-23.mat":
        ("https://ndownloader.figshare.com/files/42450087", 2906058754),
    "MAT_normalizedData_AbleBodiedAdults_v06-03-23.mat":
        ("https://ndownloader.figshare.com/files/42450096", 6244593847),
    "MATdatafiles_description_v1.3_LST.xlsx":
        ("https://ndownloader.figshare.com/files/42450093", None),
    "supplementary_information.pdf":
        ("https://static-content.springer.com/esm/art%3A10.1038%2Fs41597-023-02767-y/"
         "MediaObjects/41597_2023_2767_MOESM1_ESM.pdf", None),
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name, (url, size) in FILES.items():
        path = RAW / name
        if path.exists() and (size is None or path.stat().st_size == size):
            print(f"have  {name}")
            continue
        print(f"get   {name} ...", flush=True)
        tmp = path.with_suffix(path.suffix + ".part")
        with urllib.request.urlopen(url) as r, open(tmp, "wb") as out:
            shutil.copyfileobj(r, out, length=16 * 1024 * 1024)
        if size is not None and tmp.stat().st_size != size:
            raise SystemExit(f"{name}: expected {size} bytes, got {tmp.stat().st_size}")
        tmp.rename(path)
    print("All files in", RAW.relative_to(ROOT))


if __name__ == "__main__":
    main()
