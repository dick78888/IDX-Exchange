"""
Week 8 - Tableau Data Preparation 


"""

import pandas as pd
import numpy as np
from pathlib import Path


DATA_DIR = Path(r"C:\IDX-Exchange\csv")
LISTING_FILE = DATA_DIR / "week4_cleaned_listing.csv"
SOLD_FILE = DATA_DIR / "week4_cleaned_sold.csv"
OUTPUT_FILE = DATA_DIR / "tableau_market_analysis_summary.csv"

GROUP_COLS = ["City", "CountyOrParish", "PostalCode", "PropertySubType"]

DATE_COL_LISTING = "ListingContractDate"   
DATE_COL_SOLD = "CloseDate"                

CLOSE_PRICE_COL = "ClosePrice"
ORIGINAL_LIST_PRICE_COL = "OriginalListPrice"
DAYS_ON_MARKET_COL = "DaysOnMarket"

print("Loading cleaned datasets...")
listing = pd.read_csv(LISTING_FILE, low_memory=False)
sold = pd.read_csv(SOLD_FILE, low_memory=False)
print(f"Listing rows: {len(listing):,} | Sold rows: {len(sold):,}")


listing[DATE_COL_LISTING] = pd.to_datetime(listing[DATE_COL_LISTING], errors="coerce")
sold[DATE_COL_SOLD] = pd.to_datetime(sold[DATE_COL_SOLD], errors="coerce")

listing["YrMo"] = listing[DATE_COL_LISTING].dt.to_period("M").astype(str)
sold["YrMo"] = sold[DATE_COL_SOLD].dt.to_period("M").astype(str)


def is_valid(df, flag_col):
    if flag_col not in df.columns:
        return pd.Series(True, index=df.index)
    return ~df[flag_col].fillna(0).astype(bool)

sold_price_valid = sold[is_valid(sold, "invalid_price_flag")]
sold_dom_valid = sold[is_valid(sold, "invalid_dom_flag")]

print(f"Sold rows after dropping invalid_price_flag: {len(sold_price_valid):,}")
print(f"Sold rows after dropping invalid_dom_flag: {len(sold_dom_valid):,}")


ratio_df = sold_price_valid.copy()
valid_orig_price = (ratio_df[ORIGINAL_LIST_PRICE_COL] > 0) & ratio_df[ORIGINAL_LIST_PRICE_COL].notna()
ratio_df["CloseToOriginalListRatio"] = np.where(
    valid_orig_price,
    ratio_df[CLOSE_PRICE_COL] / ratio_df[ORIGINAL_LIST_PRICE_COL],
    np.nan,
)


new_listings = (
    listing.groupby(GROUP_COLS + ["YrMo"])
    .size()
    .reset_index(name="NewListings")
)


price_metrics = (
    sold_price_valid.groupby(GROUP_COLS + ["YrMo"])
    .agg(
        MedianClosePrice=(CLOSE_PRICE_COL, "median"),
        ClosedSales=(CLOSE_PRICE_COL, "count"),
    )
    .reset_index()
)


dom_metrics = (
    sold_dom_valid.groupby(GROUP_COLS + ["YrMo"])
    .agg(AvgDaysOnMarket=(DAYS_ON_MARKET_COL, "mean"))
    .reset_index()
)


ratio_metrics = (
    ratio_df.groupby(GROUP_COLS + ["YrMo"])
    .agg(AvgCloseToOriginalListRatio=("CloseToOriginalListRatio", "mean"))
    .reset_index()
)


summary = new_listings.merge(price_metrics, on=GROUP_COLS + ["YrMo"], how="outer")
summary = summary.merge(dom_metrics, on=GROUP_COLS + ["YrMo"], how="outer")
summary = summary.merge(ratio_metrics, on=GROUP_COLS + ["YrMo"], how="outer")

summary["NewListings"] = summary["NewListings"].fillna(0).astype(int)
summary["ClosedSales"] = summary["ClosedSales"].fillna(0).astype(int)
summary["MedianClosePrice"] = summary["MedianClosePrice"].round(0)
summary["AvgDaysOnMarket"] = summary["AvgDaysOnMarket"].round(1)
summary["AvgCloseToOriginalListRatio"] = summary["AvgCloseToOriginalListRatio"].round(4)

summary = summary.sort_values(GROUP_COLS + ["YrMo"]).reset_index(drop=True)

print(f"Final summary rows: {len(summary):,}")
print(summary.head(10))

summary.to_csv(OUTPUT_FILE, index=False)
print(f"Saved Tableau-ready summary to {OUTPUT_FILE}")
