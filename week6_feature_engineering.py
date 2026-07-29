"""
Week 6 - Feature Engineering and Market Metrics

"""


import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


DATA_DIR = r"C:\IDX-Exchange\csv"
SOLD_INPUT = os.path.join(DATA_DIR, "week4_cleaned_sold.csv")
SOLD_OUTPUT = os.path.join(DATA_DIR, "week6_feature_engineered_sold.csv")



SCHOOL_DISTRICT_GEOJSON_URL = (
    "https://gis.data.ca.gov/api/download/v1/items/"
    "b0e3b936426a47ce9d9a2e77e2bb86cc/geojson?layers=0"
)
SCHOOL_DISTRICT_LOCAL_CACHE = os.path.join(
    DATA_DIR, "ca_school_district_areas_2024_25.geojson"
)


def safe_divide(numerator, denominator):
    """Element-wise division that returns NaN instead of raising on 0 / missing denominators."""
    denominator = denominator.replace(0, np.nan)
    return numerator / denominator


def load_data():
    print(f"Loading {SOLD_INPUT} ...")
    sold = pd.read_csv(SOLD_INPUT, low_memory=False)
    print(f"Sold dataset: {sold.shape[0]:,} rows, {sold.shape[1]} columns")
    return sold


def build_core_metrics(df):
    df = df.copy()

    # Price Ratio -- negotiation strength
    if {"ClosePrice", "OriginalListPrice"}.issubset(df.columns):
        df["PriceRatio"] = safe_divide(df["ClosePrice"], df["OriginalListPrice"])
    else:
        print("WARNING: ClosePrice / OriginalListPrice not found, skipping PriceRatio")

    # Price Per Sq Ft -- normalizes price across sizes
    if {"ClosePrice", "LivingArea"}.issubset(df.columns):
        df["PricePerSqFt"] = safe_divide(df["ClosePrice"], df["LivingArea"])
    else:
        print("WARNING: ClosePrice / LivingArea not found, skipping PricePerSqFt")

    # Days on Market -- raw field, kept as-is if present
    if "DaysOnMarket" not in df.columns:
        print("WARNING: DaysOnMarket not found in dataset")

    # Year / Month -- enables time-series analysis, derived from CloseDate
    if "CloseDate" in df.columns:
        df["CloseDate"] = pd.to_datetime(df["CloseDate"], errors="coerce")
        df["YrMo"] = df["CloseDate"].dt.to_period("M").astype(str)
    else:
        print("WARNING: CloseDate not found, skipping YrMo")

    
    if "PriceRatio" in df.columns:
        df["CloseToOriginalListRatio"] = df["PriceRatio"]

    # Listing to Contract Days
    if {"PurchaseContractDate", "ListingContractDate"}.issubset(df.columns):
        df["PurchaseContractDate"] = pd.to_datetime(df["PurchaseContractDate"], errors="coerce")
        df["ListingContractDate"] = pd.to_datetime(df["ListingContractDate"], errors="coerce")
        df["ListingToContractDays"] = (
            df["PurchaseContractDate"] - df["ListingContractDate"]
        ).dt.days
    else:
        print("WARNING: PurchaseContractDate / ListingContractDate not found, "
              "skipping ListingToContractDays")

    # Contract to Close Days
    if {"CloseDate", "PurchaseContractDate"}.issubset(df.columns):
        df["ContractToCloseDays"] = (
            df["CloseDate"] - df["PurchaseContractDate"]
        ).dt.days
    else:
        print("WARNING: CloseDate / PurchaseContractDate not found, "
              "skipping ContractToCloseDays")

    return df


def flag_invalid_day_counts(df):
    """Negative day counts indicate data entry errors; flag rather than silently drop."""
    for col in ["ListingToContractDays", "ContractToCloseDays"]:
        if col in df.columns:
            flag_col = f"{col}_Invalid"
            df[flag_col] = df[col] < 0
            n_invalid = int(df[flag_col].sum())
            if n_invalid:
                print(f"{col}: {n_invalid:,} negative values flagged in {flag_col}")
    return df


def add_school_districts(df):
    """Spatial join properties to CA school district areas using lat/long."""
    if not {"Latitude", "Longitude"}.issubset(df.columns):
        print("WARNING: Latitude / Longitude not found, skipping school district join")
        return df

    if os.path.exists(SCHOOL_DISTRICT_LOCAL_CACHE):
        print(f"Loading cached school district boundaries from {SCHOOL_DISTRICT_LOCAL_CACHE}")
        districts = gpd.read_file(SCHOOL_DISTRICT_LOCAL_CACHE)
    else:
        print("Downloading CA school district boundaries (this may take a minute) ...")
        districts = gpd.read_file(SCHOOL_DISTRICT_GEOJSON_URL)
        districts.to_file(SCHOOL_DISTRICT_LOCAL_CACHE, driver="GeoJSON")

    if districts.crs is None:
        districts = districts.set_crs(epsg=4326)
    districts = districts.to_crs(epsg=4326)

    # District name column varies by CDE export vintage -- try common candidates
    name_col_candidates = ["DistrictName", "DISTRICTNA", "District", "NAME"]
    district_name_col = next((c for c in name_col_candidates if c in districts.columns), None)
    if district_name_col is None:
        print(f"WARNING: could not find a district name column, "
              f"available columns: {list(districts.columns)}")
        district_name_col = districts.columns[0]

    geo_df = df.dropna(subset=["Latitude", "Longitude"]).copy()
    geometry = [Point(xy) for xy in zip(geo_df["Longitude"], geo_df["Latitude"])]
    geo_points = gpd.GeoDataFrame(geo_df, geometry=geometry, crs="EPSG:4326")

    joined = gpd.sjoin(
        geo_points, districts[[district_name_col, "geometry"]],
        how="left", predicate="within"
    )
    joined = joined.rename(columns={district_name_col: "SchoolDistrict"})
    joined = joined.drop(columns=["geometry", "index_right"], errors="ignore")

    matched = joined["SchoolDistrict"].notna().sum()
    print(f"School district match: {matched:,} / {len(joined):,} properties matched "
          f"({matched / len(joined):.1%})")

    result = df.merge(
        joined[["SchoolDistrict"]], left_index=True, right_index=True, how="left"
    )
    return result


def segment_summary(df, group_cols, metrics, label):
    """Return count + mean/median for the given metrics grouped by group_cols."""
    available_group_cols = [c for c in group_cols if c in df.columns]
    available_metrics = [c for c in metrics if c in df.columns]
    if len(available_group_cols) < len(group_cols):
        missing = set(group_cols) - set(available_group_cols)
        print(f"WARNING ({label}): missing group columns {missing}")
    if not available_group_cols or not available_metrics:
        print(f"Skipping segment summary '{label}': insufficient columns")
        return None

    agg_dict = {m: ["count", "mean", "median"] for m in available_metrics}
    summary = df.groupby(available_group_cols).agg(agg_dict)
    summary.columns = ["_".join(c) for c in summary.columns]
    summary = summary.reset_index()
    return summary


def main():
    sold = load_data()
    sold = build_core_metrics(sold)
    sold = flag_invalid_day_counts(sold)
    sold = add_school_districts(sold)

    print("\nSample output (first 5 rows of engineered columns):")
    engineered_cols = [c for c in [
        "PriceRatio", "PricePerSqFt", "DaysOnMarket", "YrMo",
        "CloseToOriginalListRatio", "ListingToContractDays",
        "ContractToCloseDays", "SchoolDistrict"
    ] if c in sold.columns]
    print(sold[engineered_cols].head())

    metrics = ["PriceRatio", "PricePerSqFt", "DaysOnMarket",
               "ListingToContractDays", "ContractToCloseDays"]

    segments = {
        "by_property_type": (["PropertyType", "PropertySubType"], metrics),
        "by_county_area": (["CountyOrParish", "MLSAreaMajor"], metrics),
        "by_office": (["ListOfficeName", "BuyerOfficeName"], metrics),
    }

    for label, (group_cols, m) in segments.items():
        print(f"\nBuilding segment summary: {label}")
        summary = segment_summary(sold, group_cols, m, label)
        if summary is not None:
            out_path = os.path.join(DATA_DIR, f"week6_segment_{label}.csv")
            summary.to_csv(out_path, index=False)
            print(f"Saved {label} summary to {out_path} ({len(summary):,} rows)")
            print(summary.head())

    sold.to_csv(SOLD_OUTPUT, index=False)
    print(f"\nSaved feature-engineered dataset to {SOLD_OUTPUT} "
          f"({sold.shape[0]:,} rows, {sold.shape[1]} columns)")


if __name__ == "__main__":
    main()
