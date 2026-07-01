import pandas as pd
import os

# ── Configuration ──────────────────────────────────────────────
DATA_DIR = r"C:\IDX-Exchange\csv"

LISTING_FILE = os.path.join(DATA_DIR, "CRMLSListing_Filtered.csv")
SOLD_FILE    = os.path.join(DATA_DIR, "CRMLSSold_Filtered.csv")

# ── Load datasets ──────────────────────────────────────────────
print("Loading datasets...")
listings = pd.read_csv(LISTING_FILE, low_memory=False, encoding='latin-1')
sold     = pd.read_csv(SOLD_FILE,    low_memory=False, encoding='latin-1')

# ══════════════════════════════════════════════════════════════
# STEP 1 — Fetch mortgage rate data from FRED
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("STEP 1 — FETCH MORTGAGE RATE DATA FROM FRED")
print("=" * 60)

url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url, parse_dates=['observation_date'])
mortgage.columns = ['date', 'rate_30yr_fixed']

# Remove any rows with missing rate (FRED occasionally has gaps)
mortgage = mortgage.dropna(subset=['rate_30yr_fixed'])

print(f"[INFO] Fetched {len(mortgage):,} weekly observations from FRED")
print(mortgage.head())

# ══════════════════════════════════════════════════════════════
# STEP 2 — Resample weekly rates to monthly averages
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("STEP 2 — RESAMPLE TO MONTHLY AVERAGES")
print("=" * 60)

mortgage['year_month'] = mortgage['date'].dt.to_period('M')
mortgage_monthly = (
    mortgage.groupby('year_month')['rate_30yr_fixed']
    .mean()
    .reset_index()
)
mortgage_monthly['rate_30yr_fixed'] = mortgage_monthly['rate_30yr_fixed'].round(4)

print(f"[INFO] Resampled to {len(mortgage_monthly):,} monthly averages")
print(mortgage_monthly.tail(10).to_string())

# ══════════════════════════════════════════════════════════════
# STEP 3 — Create year_month key on MLS datasets
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("STEP 3 — CREATE YEAR_MONTH KEY ON MLS DATASETS")
print("=" * 60)

# Sold dataset — key off CloseDate
sold['year_month'] = pd.to_datetime(sold['CloseDate'], errors='coerce').dt.to_period('M')

# Listings dataset — key off ListingContractDate
listings['year_month'] = pd.to_datetime(
    listings['ListingContractDate'], errors='coerce'
).dt.to_period('M')

print(f"[INFO] Sold year_month range    : {sold['year_month'].min()} to {sold['year_month'].max()}")
print(f"[INFO] Listings year_month range: {listings['year_month'].min()} to {listings['year_month'].max()}")

# ══════════════════════════════════════════════════════════════
# STEP 4 — Merge mortgage rates onto both datasets
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("STEP 4 — MERGE MORTGAGE RATES")
print("=" * 60)

sold_with_rates     = sold.merge(mortgage_monthly, on='year_month', how='left')
listings_with_rates = listings.merge(mortgage_monthly, on='year_month', how='left')

print(f"[INFO] Sold rows after merge    : {len(sold_with_rates):,}")
print(f"[INFO] Listings rows after merge: {len(listings_with_rates):,}")

# ══════════════════════════════════════════════════════════════
# STEP 5 — Validate the merge (no null rate values)
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("STEP 5 — VALIDATE MERGE")
print("=" * 60)

sold_null     = sold_with_rates['rate_30yr_fixed'].isnull().sum()
listings_null = listings_with_rates['rate_30yr_fixed'].isnull().sum()

print(f"[VALIDATE] Sold — null rate values after merge    : {sold_null:,}")
print(f"[VALIDATE] Listings — null rate values after merge: {listings_null:,}")

if sold_null == 0 and listings_null == 0:
    print("[PASS] No null rate values — merge successful.")
else:
    print("[WARNING] Some rows could not be matched to a mortgage rate.")

# Preview
print("\n--- Preview: Sold with Mortgage Rates ---")
print(sold_with_rates[['CloseDate', 'year_month', 'ClosePrice', 'rate_30yr_fixed']].head(10).to_string())

# ── Export enriched datasets as new CSVs ───────────────────────
sold_with_rates.to_csv(
    os.path.join(DATA_DIR, "CRMLSSold_Enriched.csv"), index=False)
listings_with_rates.to_csv(
    os.path.join(DATA_DIR, "CRMLSListing_Enriched.csv"), index=False)

print("\n[DONE] Enriched datasets saved:")
print(f"  → CRMLSSold_Enriched.csv")
print(f"  → CRMLSListing_Enriched.csv")
