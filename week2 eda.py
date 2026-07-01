import pandas as pd
import os

# ── Display settings ───────────────────────────────────────────
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 200)

# ── Configuration ──────────────────────────────────────────────
DATA_DIR = r"C:\IDX-Exchange\csv"

LISTING_FILE = os.path.join(DATA_DIR, "CRMLSListing_Combined_Residential.csv")
SOLD_FILE    = os.path.join(DATA_DIR, "CRMLSSold_Combined_Residential.csv")

# ── Load datasets ──────────────────────────────────────────────
print("Loading datasets...")
listings = pd.read_csv(LISTING_FILE, low_memory=False, encoding='latin-1')
sold     = pd.read_csv(SOLD_FILE,    low_memory=False, encoding='latin-1')

# ══════════════════════════════════════════════════════════════
# SECTION 1 — Unique Property Types
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 1 — UNIQUE PROPERTY TYPES")
print("=" * 60)

print("\n--- PropertyType (Listings) ---")
print(listings['PropertyType'].value_counts())

print("\n--- PropertyType (Sold) ---")
print(sold['PropertyType'].value_counts())

print("\n--- PropertySubType (Listings) ---")
print(listings['PropertySubType'].value_counts())

print("\n--- PropertySubType (Sold) ---")
print(sold['PropertySubType'].value_counts())

# Filtering logic (already done in Week 1, re-confirming)
listings = listings[listings['PropertyType'] == 'Residential'].copy()
sold     = sold[sold['PropertyType'] == 'Residential'].copy()

print(f"\n[INFO] Listings after Residential filter : {len(listings):,} rows")
print(f"[INFO] Sold after Residential filter     : {len(sold):,} rows")

# ══════════════════════════════════════════════════════════════
# SECTION 2 — Missing Value Report
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 2 — MISSING VALUE REPORT")
print("=" * 60)

def missing_report(df, label):
    total = len(df)
    missing = df.isnull().sum()
    pct = (missing / total * 100).round(2)
    report = pd.DataFrame({
        'missing_count': missing,
        'missing_pct':   pct
    })
    report = report[report['missing_count'] > 0].sort_values('missing_pct', ascending=False)
    high_missing = report[report['missing_pct'] > 90]
    print(f"\n--- {label}: Columns with >90% missing ({len(high_missing)} columns flagged) ---")
    print(high_missing.to_string())
    return report

listing_missing = missing_report(listings, "Listings")
sold_missing    = missing_report(sold,     "Sold")

# ══════════════════════════════════════════════════════════════
# SECTION 3 — Numeric Distribution Summary
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 3 — NUMERIC DISTRIBUTION SUMMARY")
print("=" * 60)

KEY_FIELDS = ['ClosePrice', 'ListPrice', 'OriginalListPrice',
              'LivingArea', 'LotSizeAcres', 'BedroomsTotal',
              'BathroomsTotalInteger', 'DaysOnMarket', 'YearBuilt']

print("\n--- Distribution Summary (Sold) ---")
sold_fields = [f for f in KEY_FIELDS if f in sold.columns]
print(sold[sold_fields].describe(percentiles=[.25, .5, .75, .9, .95]).round(2).to_string())

print("\n--- Distribution Summary (Listings) ---")
listing_fields = [f for f in KEY_FIELDS if f in listings.columns]
print(listings[listing_fields].describe(percentiles=[.25, .5, .75, .9, .95]).round(2).to_string())

# ── Export filtered datasets ───────────────────────────────────
listings.to_csv(os.path.join(DATA_DIR, "CRMLSListing_Filtered.csv"), index=False)
sold.to_csv(    os.path.join(DATA_DIR, "CRMLSSold_Filtered.csv"),    index=False)

print("\n[DONE] Filtered datasets saved:")
print(f"  → CRMLSListing_Filtered.csv")
print(f"  → CRMLSSold_Filtered.csv")
