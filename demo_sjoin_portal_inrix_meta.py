# %%
import struct

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from shapely.wkb import loads as wkb_loads

from datafiles import (
    PortalInrixDataFiles,
)  # This is the helper class to manage the file paths


def standardize_direction(direction, bound=None):
    """
    Standardize direction formats between PORTAL and INRIX
    """
    direction_map = {
        # INRIX formats
        "NORTHBOUND": "NORTH",
        "SOUTHBOUND": "SOUTH",
        "WESTBOUND": "WEST",
        "EASTBOUND": "EAST",
        # PORTAL formats
        "NORTH": "NORTH",
        "SOUTH": "SOUTH",
        "WEST": "WEST",
        "EAST": "EAST",
        "NORT": "NORTH",  # Handle the truncated 'NORT'
        "CONST": None,  # Handle construction case separately
    }

    # If direction is not valid, try to use bound
    bound_map = {
        "NB": "NORTH",
        "SB": "SOUTH",
        "WB": "WEST",
        "EB": "EAST",
        "JB": None,  # Special cases
        "ZB": None,
    }

    std_direction = direction_map.get(direction.upper())
    if std_direction is None and bound is not None:
        std_direction = bound_map.get(bound.upper())

    return std_direction


def check_ewkb_srid(wkb_hex):
    # Convert hex to bytes
    wkb_bytes = bytes.fromhex(wkb_hex)

    # Check endianness (byte order)
    endian = ">" if wkb_bytes[0] == 0 else "<"

    # Check if it's EWKB (has SRID)
    has_srid = bool(struct.unpack(endian + "I", wkb_bytes[1:5])[0] & 0x20000000)

    if has_srid:
        # SRID is stored after the type indicator
        srid = struct.unpack(endian + "I", wkb_bytes[5:9])[0]
        return srid
    return None


def wkb_to_geom(wkb_hex):
    try:
        if pd.isna(wkb_hex) or not wkb_hex.strip():
            return None
        geom = wkb_loads(bytes.fromhex(wkb_hex))
        # print(f"ekwb_srid: {check_ewkb_srid(wkb_hex)}") # Uncomment to check SRID
        return geom
    except (ValueError, TypeError) as e:
        print(f"Conversion error: {e}")
        return None


# The datafiles object is a helper class to manage the file paths and
# the file summary methods should confirm it found the files expected.
# example_datafiles.get_* methods return the file paths and could be replace
# with the actual file paths if you prefer.

example_datafiles = PortalInrixDataFiles(data_root="/home/oms/gdrive/STAT 570/CADES_DATA")
example_datafiles.portal_file_summary()
example_datafiles.inrix_file_summary()

# Load CSVs
portal_stations_df = pd.read_csv(example_datafiles.get_portal_meta("stations"))
portal_highways_df = pd.read_csv(example_datafiles.get_portal_meta("highways"))
# pd.read_csv() can be replaced with pd.read_sql() if you have a database connection
# However, the SQL query would need to be written to extract the same data as the CSVs
# and there is additional setup required for the database connection as seen in the
# pandas documentation.
# - https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html#pandas.read_sql

# %%
# Convert hex WKB to geometries
portal_stations_df["segment_geom"] = portal_stations_df["segment_geom"].apply(
    wkb_to_geom
)
portal_stations_df["station_geom"] = portal_stations_df["station_geom"].apply(
    wkb_to_geom
)

# After your wkb_to_geom conversions
print(f"Total rows in DataFrame: {len(portal_stations_df)}")
print(
    f"Successful segment conversions: {portal_stations_df['segment_geom'].notna().sum()}"
)
print(
    f"Successful station conversions: {portal_stations_df['station_geom'].notna().sum()}"
)

# Merge highways data for additional station direction coverage and highway names
portal_stations_df = portal_stations_df.merge(
    portal_highways_df[["highwayid", "direction", "bound", "highwayname"]],
    on="highwayid",
    how="left",
)

# Standardize direction formats
portal_stations_df["standardized_direction"] = portal_stations_df.apply(
    lambda row: standardize_direction(row["direction"], row["bound"]),
    axis=1,
)

# %%
# Convert to GeoDataFrame with Web Mercator CRS
the_CRS = "EPSG:3857"
portal_gdf = gpd.GeoDataFrame(portal_stations_df, geometry="segment_geom", crs=the_CRS)

# Load INRIX TMC Shapefiles - Oregon and Clark County, WA
oregon_gdf = gpd.read_file(
    "path/to/oregon_shapefile.shp"
)

clark_gdf = gpd.read_file(
    "path/to/clark_county_shapefile.shp"
)

# Convert all to a common CRS ("EPSG:4326" lon/lat)
oregon_gdf = oregon_gdf.to_crs("EPSG:4326")
clark_gdf = clark_gdf.to_crs("EPSG:4326")
portal_gdf = portal_gdf.to_crs("EPSG:4326")

# Specify the year for INRIX data
year_str = "2023"

# %%
# Load INRIX TMC Identification data this is used to find the unique TMCs
# to filter to the same which are the given 139 TMCs of interest.
tmc_identification_df = pd.read_csv(example_datafiles.get_inrix_meta(year_str))

# Merge Oregon and Clark County TMCs into 1 dataframe
inrix_full_df = pd.concat([oregon_gdf, clark_gdf], ignore_index=True)
inrix_full_df["standardized_direction"] = inrix_full_df.apply(
    lambda row: standardize_direction(row["Direction"]), axis=1
)
unique_tmc_ids = tmc_identification_df.tmc.unique().tolist()
inrix_filtered_by_tmc = inrix_full_df[inrix_full_df["Tmc"].isin(unique_tmc_ids)]

portal_inrix_spatial_join = inrix_filtered_by_tmc.sjoin(
    portal_gdf, how="inner", predicate="intersects", lsuffix="inrix", rsuffix="portal"
)

# Visualize the segments to ensure it looks correct
fig, ax = plt.subplots(figsize=(12, 10))
portal_gdf.plot(
    ax=ax,
    color="red",
    edgecolor="red",
    alpha=0.1,
    markersize=10,
    label="Portal Segments",
)
inrix_filtered_by_tmc.plot(
    ax=ax,
    color="lightblue",
    edgecolor="lightblue",
    alpha=0.5,
    markersize=1,
    label="INRIX TMCs Segments (Filtered by 139 TMC locations)",
)

plt.title("INRIX TMCs vs Portal StationID Segments: 2023")
plt.legend()
plt.grid(True)
plt.show()

# %%
# Visualize the spatial join to ensure it looks correct
fig, ax = plt.subplots(figsize=(12, 10))
portal_inrix_spatial_join.plot(
    ax=ax, color="green", edgecolor="green", alpha=0.5, markersize=10
)
plt.title("Intersecting INRIX TMCs and Portal Segments Spatial Join")
plt.grid(True)
plt.xticks(rotation=45)
plt.show()

# List of columns to save to the file (can be modified as needed)
columns_of_interest = [
    "Tmc",
    "Direction",
    "stationid",
    "highwayid",
    "RoadNumb_1",
    "direction",
    "bound",
    "standardized_direction_portal",
    "standardized_direction_inrix",
    "StartLat",
    "StartLong",
    "milepost",
    "lon",
    "lat",
    "highwayname",
    "start_date",
    "end_date",
]

# Select columns of interest
portal_inrix_spatial_join[columns_of_interest]

# Save the spatial join to a CSV
# - comment out this line if you don't want to save to file
portal_inrix_spatial_join[columns_of_interest].to_csv("data/portal_inrix_spatial_join.csv")

# %%
