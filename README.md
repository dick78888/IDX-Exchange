# IDX Exchange – Data Analyst Internship

This repository contains Python scripts developed during the IDX Exchange Data Analyst Internship (Summer 2026), analyzing CRMLS real estate data.

## Week 1 – Monthly Dataset Aggregation
**Script:** `week1_aggregation.py`

Concatenates all monthly CRMLS Listing and Sold files from January 2024 through the most recently completed calendar month. Automatically uses `_filled` versions where available. Filters both datasets to `PropertyType == 'Residential'` and exports two combined CSVs.

**Output:**
- `CRMLSListing_Combined_Residential.csv` — 534,664 rows
- `CRMLSSold_Combined_Residential.csv` — 414,054 rows

## Week 2 – Dataset Structuring and Validation (EDA)
**Script:** `week2 eda.py`

Performs exploratory data analysis on the combined Residential datasets. Identifies unique property types and subtypes, flags columns with >90% missing values, and produces a numeric distribution summary for key fields including ClosePrice, LivingArea, and DaysOnMarket.

**Output:**
- `CRMLSListing_Filtered.csv` — 534,664 rows
- `CRMLSSold_Filtered.csv` — 414,054 rows

**EDA Findings:**

**1. Residential vs. other property type share**
Both datasets are pre-filtered to PropertyType == 'Residential' from Week 1. All 534,664 listing rows and 414,054 sold rows are Residential.

**2. Median and average close prices**
- Median close price: $823,000
- Average close price: $1,193,864
- The gap between median and mean indicates a right-skewed distribution driven by high-end luxury properties.

**3. Days on Market distribution**
- Median: 18 days
- Mean: 37 days
- Anomalies detected: min = -288 days, max = 12,430 days — flagged for cleaning.

**4. Homes sold above vs. below list price**
- To be calculated in cleaning phase using ClosePrice vs. ListPrice comparison.

**5. Date consistency issues**
- Negative DaysOnMarket values detected (min = -288), suggesting CloseDate recorded before ListingContractDate in some records — flagged for cleaning.

**6. Missing value flags**
- 15 columns flagged with >90% missing in both Listings and Sold datasets.
- Key columns flagged: BusinessType, FireplacesTotal, TaxYear, CoveredSpaces, AboveGradeFinishedArea, ElementarySchoolDistrict (100% missing).
- These columns are candidates for removal in the cleaning phase.

## Week 3 – Mortgage Rate Enrichment
**Script:** `week3 mortgage.py`

Fetches the MORTGAGE30US series directly from the St. Louis Federal Reserve (FRED), resamples weekly rates to monthly averages, and merges onto both combined datasets using a year-month key derived from transaction dates. Validates that no null rate values exist after the merge.

**Methodology:**
- Source: FRED MORTGAGE30US series (30-year fixed rate, published weekly by Freddie Mac)
- Total observations fetched: 2,883 weekly records (1971-04 to 2026-06)
- Resampled to 663 monthly averages
- Join key: year_month derived from CloseDate (Sold) and ListingContractDate (Listings)
- Merge type: Left join to preserve all MLS records
- MLS data range: 2024-01 to 2026-04

**Validation:**
- Sold — null rate values after merge: 0
- Listings — null rate values after merge: 0
- All records successfully matched to a monthly mortgage rate.

**Output:**
- `CRMLSSold_Enriched.csv` — 414,054 rows (rate_30yr_fixed added)
- `CRMLSListing_Enriched.csv` — 534,664 rows (rate_30yr_fixed added)

Week 4 - Merge and Clean

Added two new months (202605, 202606) to the pipeline. After Residential filtering: Listing 582,611 rows (+47,947), Sold 448,036 rows (+33,982)
Dropped 11 duplicate-named columns (.1 suffix) from raw exports
All 4 date columns converted with 0 parse failures (both datasets)
Invalid value flags: Listing invalid_area_flag 377, invalid_dom_flag 19, invalid_price_flag 0, invalid_beds_baths_flag 0; Sold invalid_area_flag 165, invalid_dom_flag 51, invalid_price_flag 1, invalid_beds_baths_flag 0
Date consistency flags: listing_after_close_flag 81 (Listing) / 68 (Sold); purchase_after_close_flag 244 / 240; negative_timeline_flag 287 / 290
Geographic flags: missing_coord_flag 72,411 (12.4%) for Listing vs 4,378 (1.0%) for Sold; out_of_ca_bounds_flag 72,721 (12.5%) vs 4,478 (1.0%) — Listing's much higher rate likely reflects active/pending records not yet geocoded, worth verifying
Outputs: week4_cleaned_listing.csv (582,611 rows), week4_cleaned_sold.csv (448,036 rows), row counts unchanged since invalid records are flagged, not dropped

Week 5 - Merge and Clean

Dropped 14 unnecessary/redundant columns (fully empty fields like TaxYear and FireplacesTotal, plus duplicates of existing fields like LivingArea and LotSizeAcres). Three fields (WaterfrontYN, BasementYN, BelowGradeFinishedArea) had their missing values filled with N/0 instead of being dropped, since a blank there means "not marked" rather than "unknown."

After cleaning, Listing has 70 columns and Sold has 81, with row counts unchanged (582,611 / 448,036) — same as before, invalid values are flagged rather than dropped, and no records were removed.
