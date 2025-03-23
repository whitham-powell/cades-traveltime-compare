import re
import pandas as pd
import matplotlib.pyplot as plt

from datafiles import PortalInrixDataFiles


# Function to ensure timezone offsets include minutes (e.g. "-08" becomes "-08:00")
def normalize_timezone(timestamp):
    return re.sub(r"([-+]\d{2})$", r"\1:00", timestamp)


# Function to insert default microseconds if not present
def add_default_microseconds(timestamp):
    if "." not in timestamp:
        match = re.search(r"([-+]\d{2}:\d{2})$", timestamp)
        if match:
            tz = match.group(1)
            timestamp = timestamp[: match.start()] + ".000000" + tz
    return timestamp


# Combined normalization function
def normalize_timestamp(timestamp):
    if pd.isna(timestamp):
        return None
    timestamp = normalize_timezone(timestamp)
    timestamp = add_default_microseconds(timestamp)
    return timestamp


# Specify the route name, year, and bounds, and the start and end timestamps
# of the data to be processed
year = 2023
year_str = str(year)
route_name = "I205"
adjusted_route_name = re.sub(r"([A-Za-z]+)(\d+)", r"\1-\2", route_name)
bound_1 = "NB"
bound_2 = "SB"

start_dt = pd.Timestamp(
    year=year,
    month=10,
    day=1,
    hour=0,
    minute=0,
    second=0,
    tz="America/Los_Angeles",
)
end_dt = pd.Timestamp(
    year=year,
    month=12,
    day=31,
    hour=23,
    minute=59,
    second=59,
    tz="America/Los_Angeles",
)

meta_columns_of_interest = [
    "Tmc",
    # "LinearTMC",
    "Direction",
    "stationid",
    "highwayid",
    "RoadNumb_1",
    "direction",
    "Miles",
    "bound",
    "standardized_direction_portal",
    "standardized_direction_inrix",
    "StartLat",
    "StartLong",
    "EndLat",
    "EndLong",
    "milepost",
    # "length",
    "lon",
    "lat",
    "highwayname",
    "start_date",
    "end_date",
    "active_dates",
]

# Initialize the data files object as in the sjoin script again with
# caveat that this can be replaced with the actual file paths if preferred.
example_datafiles = PortalInrixDataFiles(data_root="path/to/data")
example_datafiles.portal_file_summary()
example_datafiles.inrix_file_summary()

# The data can be accessed from a database directly.
# pd.read_csv() can be replaced with pd.read_sql() if you have a database connection
# However, the SQL query would need to be written to extract the same data as the CSVs
# and there is additional setup required for the database connection as seen in the
# pandas documentation.
# - https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html#pandas.read_sql

# Load the spatial join of the portal and INRIX data created
# in the demo_sjoin_portal_inrix_meta.py script
sjoined_portal_inrix_df = pd.read_csv("data/portal_inrix_spatial_join.csv")

# Ensure the data types are correctly set and normalize timestamps
sjoined_portal_inrix_df = sjoined_portal_inrix_df.convert_dtypes()
sjoined_portal_inrix_df["stationid"] = sjoined_portal_inrix_df["stationid"].astype(
    "string"
)
sjoined_portal_inrix_df["start_date"] = sjoined_portal_inrix_df["start_date"].apply(
    normalize_timestamp
)
sjoined_portal_inrix_df["end_date"] = sjoined_portal_inrix_df["end_date"].apply(
    normalize_timestamp
)

# Convert the start and end dates to datetime objects and convert to Pacific time
sjoined_portal_inrix_df["start_date"] = pd.to_datetime(
    sjoined_portal_inrix_df["start_date"],
    utc=True,
    errors="coerce",
).dt.tz_convert("America/Los_Angeles")
sjoined_portal_inrix_df["end_date"] = pd.to_datetime(
    sjoined_portal_inrix_df["end_date"],
    utc=True,
    errors="coerce",
).dt.tz_convert("America/Los_Angeles")


print(f"Processing {route_name} {year_str} {bound_1} and {bound_2} data")
print(
    f"Portal data files: {example_datafiles.get_portal_data(route_name, year_str, bound_1)}"
)
print(f"Building dataframe (concat 1) {bound_1}")

# Load the portal data files for the specified route, year, and bounds
# and concatenate them into a single DataFrame.
bound_1_portal_data_df = pd.concat(
    [
        pd.read_csv(file)
        for file in example_datafiles.get_portal_data(route_name, year_str, bound_1)
    ]
)

print(f"Building dataframe (concat 2) {bound_2}")
bound_2_portal_data_df = pd.concat(
    [
        pd.read_csv(file)
        for file in example_datafiles.get_portal_data(route_name, year_str, bound_2)
    ]
)

print(f"Building dataframe (concat ) {bound_1} and {bound_2}")
portal_data_df = pd.concat([bound_1_portal_data_df, bound_2_portal_data_df])

print(f"Portal data shape: {portal_data_df.shape}")
print(f"Portal data initial dtypes:\n{portal_data_df.dtypes}, converting...")

# Convert the data types and normalize the timestamps
portal_data_df = portal_data_df.convert_dtypes()
portal_data_df["stationid"] = portal_data_df["stationid"].astype("string")

print(f"Processing timestamp")
portal_data_df["starttime"] = portal_data_df["starttime"].apply(normalize_timestamp)
portal_data_df["starttime"] = pd.to_datetime(
    portal_data_df["starttime"],
    utc=True,
    errors="coerce",
).dt.tz_convert("America/Los_Angeles")
portal_data_df["stationtt"] = (
    portal_data_df["stationtt"] * 60
)  # convert from minutes to seconds

print(
    f"dtype and timezone conversion complete \n Portal data final dtypes:\n{portal_data_df.dtypes}"
)
print(portal_data_df.head(5))

print(f"INRIX data files: {example_datafiles.get_inrix_data(year_str)}")
inrix_data_df = pd.read_csv(example_datafiles.get_inrix_data(year_str))

print(f"INRIX data shape: {inrix_data_df.shape}")
print(f"INRIX data initial dtypes:\n{inrix_data_df.dtypes}, converting...")
inrix_data_df = inrix_data_df.convert_dtypes()

print(f"Processing timestamp")
old_inrix_timestamps = inrix_data_df["measurement_tstamp"].copy()
inrix_data_df["measurement_tstamp"] = pd.to_datetime(
    inrix_data_df["measurement_tstamp"],
).dt.tz_localize("America/Los_Angeles", ambiguous=True)

print(
    f"dtype and timezone conversion complete \n INRIX data final dtypes:\n{inrix_data_df.dtypes}"
)
print(inrix_data_df.head(5))

# Filter metadata and data by route name and year
portal_inrix_meta_df_filtered = sjoined_portal_inrix_df[meta_columns_of_interest][
    (sjoined_portal_inrix_df.RoadNumb_1 == adjusted_route_name)
    & (sjoined_portal_inrix_df.start_date.dt.year <= year)
    & (
        (sjoined_portal_inrix_df.end_date.dt.year >= year)
        | (
            sjoined_portal_inrix_df.end_date.isna()
        )  # It was assumed that if the end date is NA, the segment is still active
    )
]

# Filter INRIX data by TMCs of interest and timestamp range (start_dt to end_dt)
tmcs_of_interest = portal_inrix_meta_df_filtered["Tmc"].unique().tolist()
print(f"INRIX TMCs of interest: {tmcs_of_interest}")

inrix_data_filtered_df = inrix_data_df[
    (inrix_data_df.tmc_code.isin(tmcs_of_interest))
    & inrix_data_df["measurement_tstamp"].between(start_dt, end_dt, inclusive="both")
]

print(
    f"INRIX data filtered by TMC codes of interest and timestamp: {start_dt} to {end_dt} inclusive"
)
print(inrix_data_filtered_df.head())

# Filter PORTAL data by station IDs of interest and timestamp range (start_dt to end_dt)
station_ids_of_interest = portal_inrix_meta_df_filtered["stationid"].unique().tolist()
print(f"PORTAL station ids of interest: {station_ids_of_interest}")

portal_data_filtered_df = portal_data_df[
    (portal_data_df.stationid.isin(station_ids_of_interest))
    & portal_data_df["starttime"].between(start_dt, end_dt, inclusive="both")
]
print(
    f"PORTAL data filtered by station IDs of interest and timestamp: {start_dt} to {end_dt} inclusive"
)
print(portal_data_filtered_df.head())

# Merge the filtered portal and INRIX dataframes with the spatial join metadata
# Done in this order to preserve timestamp ordering
# Step 1 - Merge INRIX data with spatial join metadata
inrix_enriched = pd.merge(
    inrix_data_filtered_df,
    sjoined_portal_inrix_df[["Tmc", "stationid"]],
    left_on="tmc_code",
    right_on="Tmc",
    how="left",
)

print(inrix_enriched[["tmc_code", "Tmc", "stationid"]].head())
# Step 2 - Merge portal data with spatial join metadata
merged_df = pd.merge(
    portal_data_filtered_df,
    inrix_enriched,
    left_on=["stationid", "starttime"],
    right_on=["stationid", "measurement_tstamp"],
    how="inner",
    suffixes=("_portal", "_inrix"),
)

# Calculate the difference between the station travel time and the INRIX travel time
# Not strictly necessary, but can be useful for analysis
merged_df["diff"] = merged_df["stationtt"] - merged_df["travel_time_seconds"]

# Select the minimal set of columns used to compare travel times
merged_df[
    [
        "stationid",
        "Tmc",
        "starttime",
        "measurement_tstamp",
        "stationtt",
        "travel_time_seconds",
    ]
].head(10)

merged_df.to_csv(
    f"{route_name}_{bound_1}_{bound_2}__{start_dt:%Y%m%d}-{end_dt:%Y%m%d}_merged.csv",
    index=False,
)
