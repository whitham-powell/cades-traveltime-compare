# CADES Computational and Data-Enabled Sciences (CADES) Project

Code the demonstrates an approach to joining two travel time datasets via spatial information.

## Dependencies
- Python 3.12 or higher
- Pandas
- Geopandas
- Matplotlib (optional if you do not want to plot the data)
- mapclassify (optional if you do not want to plot segment maps)

## Installation
To install the dependencies, run the following command:
```bash
git clone git@github.com:whitham-powell/cades-traveltime-compare.git
cd cades-traveltime-compare
pipenv install
```

## Project Overview

This project explored two primary sources of traffic data—PORTAL (managed by ODOT and WSDOT) and INRIX (a commercial provider)—to investigate travel time trends on highways in the Portland metropolitan area. Each dataset presents unique strengths and limitations, ranging from sensor coverage and data frequency to the way road segments are defined. Integrating the datasets required a robust approach to handling differences in geometry (e.g., segment boundaries), time intervals, and data quality or availability.

A core portion of the work involved "cleaning" and "harmonizing" the two datasets so that they could be combined in a single framework. This included transforming hex-encoded road segments (in PORTAL) into usable geometry objects, standardizing coordinate reference systems, normalizing timestamps across multiple years, and filtering records to ensure consistency in coverage. Ultimately, the merged dataset enables more comprehensive analyses—such as year-to-year trend detection but also potential pit falls in the data, such as not enough coverage between the segments in PORTAL and INRIX.

- **Metadata Integration:** Successfully joined PORTAL station segments with INRIX TMC (Traffic Message Channel) segments via spatial intersection. This step highlighted how different segmentation and directional labeling can lead to data mismatches.
- **Time-Series Standardization:** Unified 15-minute interval data from both sources, converting timestamps to a consistent time zone and format for seamless comparison.
- **Validation and Visualization:** Used GeoPandas plotting to confirm that station coverage areas correctly overlapped with TMC segments. This allowed identification of potential misalignments or missing station geometry.

## Data Sources

### PORTAL
PORTAL is a public transportation data platform that provides access to a variety of transportation data sources. PORTAL data includes real-time transit data, historical transit data, and transit schedules. PORTAL data is used by transportation agencies, businesses, and researchers to monitor transit operations, plan transit projects, and analyze transit patterns.

### INRIX
INRIX is a private company that collects and analyzes traffic data. They provide a variety of data products, including real-time traffic data, historical traffic data, and traffic forecasts. INRIX data is collected from a variety of sources, including GPS data from vehicles, mobile devices, and road sensors. INRIX data is used by transportation agencies, businesses, and researchers to monitor traffic conditions, plan transportation projects, and analyze traffic patterns.
