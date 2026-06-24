# IDX Exchange – Data Analyst Internship

This repository contains Python scripts developed during the IDX Exchange Data Analyst Internship (Summer 2026), analyzing CRMLS real estate data.

## Week 1 – Monthly Dataset Aggregation
**Script:** `week1_aggregation.py`

Concatenates all monthly CRMLS Listing and Sold files from January 2024 through the most recently completed calendar month. Automatically uses `_filled` versions where available. Filters both datasets to `PropertyType == 'Residential'` and exports two combined CSVs.

**Output:**
- `CRMLSListing_Combined_Residential.csv` — 534,664 rows
- `CRMLSSold_Combined_Residential.csv` — 414,054 rows
