import pandas as pd
import os

# ── Configuration ──────────────────────────────────────────────
DATA_DIR = r"C:\IDX-Exchange\csv"   # Change if needed
MONTHS = [
    "202401", "202402", "202403", "202404", "202405", "202406",
    "202407", "202408", "202409", "202410", "202411", "202412",
    "202501", "202502", "202503", "202504", "202505", "202506",
    "202507", "202508", "202509", "202510", "202511", "202512",
    "202601", "202602", "202603", "202604",
]

# ── Helper: pick filled version if available ───────────────────
def pick_file(prefix, month):
    filled = os.path.join(DATA_DIR, f"{prefix}{month}_filled.csv")
    original = os.path.join(DATA_DIR, f"{prefix}{month}.csv")
    if os.path.exists(filled):
        print(f"  [INFO] Using filled version: {prefix}{month}_filled.csv")
        return filled
    elif os.path.exists(original):
        return original
    else:
        print(f"  [WARNING] Missing: {prefix}{month}.csv")
        return None

# ── Load and concatenate ───────────────────────────────────────
listing_frames = []
sold_frames = []

for month in MONTHS:
    lpath = pick_file("CRMLSListing", month)
    spath = pick_file("CRMLSSold", month)
    if lpath:
        listing_frames.append(pd.read_csv(lpath, low_memory=False, encoding='latin-1'))
    if spath:
        sold_frames.append(pd.read_csv(spath, low_memory=False, encoding='latin-1'))

listing = pd.concat(listing_frames, ignore_index=True)
sold    = pd.concat(sold_frames,    ignore_index=True)

# Row counts after concatenation (before filter)
print(f"\n[INFO] Listing rows after concat : {len(listing):,}")
print(f"[INFO] Sold    rows after concat : {len(sold):,}")

# ── Filter: Residential only ───────────────────────────────────
listing_res = listing[listing["PropertyType"] == "Residential"].copy()
sold_res    = sold[sold["PropertyType"]        == "Residential"].copy()

# Row counts after filter
print(f"[INFO] Listing rows after filter : {len(listing_res):,}")
print(f"[INFO] Sold    rows after filter : {len(sold_res):,}")

# ── Export ─────────────────────────────────────────────────────
listing_res.to_csv(os.path.join(DATA_DIR, "CRMLSListing_Combined_Residential.csv"), index=False)
sold_res.to_csv(   os.path.join(DATA_DIR, "CRMLSSold_Combined_Residential.csv"),    index=False)

print("\n[DONE] Output files saved to csv folder.")
