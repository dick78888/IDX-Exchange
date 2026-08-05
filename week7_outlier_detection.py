"""
Week 7 - Outlier Detection and Data Quality
edian values before vs. after filtering.
"""

import pandas as pd



INPUT_FILE = r"C:\IDX-Exchange\csv\week6_feature_engineered_sold.csv"
OUTPUT_FLAGGED = r"C:\IDX-Exchange\csv\week7_flagged_sold.csv"
OUTPUT_FILTERED = r"C:\IDX-Exchange\csv\week7_filtered_sold.csv"

FIELDS_TO_CHECK = ["ClosePrice", "LivingArea", "DaysOnMarket"]




df = pd.read_csv(INPUT_FILE)
original_row_count = len(df)

print(f"Loaded {original_row_count:,} rows from {INPUT_FILE}")


df["Flag_InvalidClosePrice"] = df["ClosePrice"] <= 0


bounds = {}

for field in FIELDS_TO_CHECK:
    Q1 = df[field].quantile(0.25)
    Q3 = df[field].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    bounds[field] = (lower, upper)

    flag_col = f"Flag_Outlier_{field}"
    df[flag_col] = (df[field] < lower) | (df[field] > upper)

    print(f"{field}: Q1={Q1:,.2f}, Q3={Q3:,.2f}, IQR={IQR:,.2f}, "
          f"lower={lower:,.2f}, upper={upper:,.2f}, "
          f"flagged={df[flag_col].sum():,}")

# Combined flag: True if any rule (business rule or IQR) marks the row bad
outlier_flag_cols = ["Flag_InvalidClosePrice"] + [f"Flag_Outlier_{f}" for f in FIELDS_TO_CHECK]
df["Flag_AnyOutlier"] = df[outlier_flag_cols].any(axis=1)


df.to_csv(OUTPUT_FLAGGED, index=False)
print(f"\nSaved full flagged dataset: {OUTPUT_FLAGGED} ({len(df):,} rows)")


df_clean = df[~df["Flag_AnyOutlier"]].copy()
df_clean.to_csv(OUTPUT_FILTERED, index=False)
print(f"Saved clean filtered dataset: {OUTPUT_FILTERED} ({len(df_clean):,} rows)")


removed = original_row_count - len(df_clean)
pct_removed = removed / original_row_count * 100

print("\n=== Comparison: Before vs. After Filtering ===")
print(f"Row count before: {original_row_count:,}")
print(f"Row count after:  {len(df_clean):,}")
print(f"Rows removed:     {removed:,} ({pct_removed:.2f}%)")

print("\nMedian values before vs. after:")
for field in FIELDS_TO_CHECK:
    median_before = df[field].median()
    median_after = df_clean[field].median()
    print(f"  {field}: before={median_before:,.2f}  after={median_after:,.2f}")
