# %%
# Code used to map data (CSV) files to handy dictionaries
from pathlib import Path
from typing import Dict, List, TypeAlias, TypedDict


# Types for type hinting
class CorridorInfo(TypedDict):
    dirpath: Path
    directions: List[str]


PathDict: TypeAlias = Dict[str, Path]
DirectionList: TypeAlias = List[str]
PortalCorridorDict: TypeAlias = Dict[str, CorridorInfo]
PortalFileCollection: TypeAlias = Dict[str, Dict[str, Dict[str, List[Path]]]]


class PortalInrixDataFiles:
    """
    PortalInrixDataFiles is a class to access data files for the INRIX and PORTAL data.
    It provides methods to access metadata, data files, and summaries for both INRIX and PORTAL datasets.
    Attributes:
        data_root_str (str): The root directory for the data files as a string.
        data_root_path (Path): The root directory for the data files as a Path object.
        years (List[str]): A list of years for which data is available.
        inrix_dir (Path): The directory containing INRIX data files.
        inrix_data_files (Dict[str, Dict[str, Path]]): A dictionary mapping years to INRIX data and metadata file paths.
        portal_dir (Path): The directory containing PORTAL data files.
        portal_meta_dir (Path): The directory containing PORTAL metadata files.
        portal_meta_files (Dict[str, Path]): A dictionary mapping metadata file types to their file paths.
        portal_data_files (Dict[str, Dict[str, Dict[str, List[Path]]]]): A nested dictionary organizing PORTAL data files by corridor, year, and direction.
    Methods:
        __init__(data_root, years=(2019, 2025)):
            Initializes the PortalInrixDataFiles instance with the given data root and year range.
        _setup_inrix_data_files():
            Internal method to set up the INRIX data files dictionary.
        _setup_portal_data_files():
            Internal method to set up the PORTAL data files dictionary.
        get_portal_meta(name):
            Retrieves the file path for a specified PORTAL metadata file.
        get_portal_data(corridor, year, direction):
            Retrieves the list of PORTAL data files for a specified corridor, year, and direction.
        get_inrix(year, name):
            Retrieves the file path for a specified INRIX data or metadata file for a given year.
        get_inrix_data(year):
            Retrieves the INRIX data file path for a given year.
        get_inrix_meta(year):
            Retrieves the INRIX metadata file path for a given year.
        inrix_file_summary():
            Prints a summary of the INRIX data and metadata files available for each year.
        portal_file_summary():
            Prints a summary of the PORTAL data files available for each corridor, year, and direction.

    Example Usage:

    import pandas as pd
    datafiles = PortalInrixDataFiles("path/to/data")

    # PORTAL
    datafiles.portal_file_summary()

    df_portal_meta_detectors = pd.read_csv(datafiles.get_portal_meta("detectors"))
    df_portal_meta_highways = pd.read_csv(datafiles.get_portal_meta("highways"))
    df_portal_meta_stations = pd.read_csv(datafiles.get_portal_meta("stations"))


    df_portal_i5_2021_nb = pd.read_csv(
        datafiles.get_portal_data("I5", "2021", "NB")[0]
    ) # TODO: this needs to be modified to handle multiple files matching the criteria


    # Example usage: INRIX
    year = "2021"
    df_inrix_data = pd.read_csv(datafiles.get_inrix_data(year))
    df_inrix_meta = pd.read_csv(datafiles.get_inrix_meta(year))
    datafiles.inrix_file_summary()
    """

    def __init__(self, data_root, years=(2019, 2025)):
        self.data_root_str = data_root
        self.data_root_path = Path(self.data_root_str)
        self.years = [str(year) for year in range(*years)]
        self.inrix_dir = self.data_root_path / "CADES_INRIX"
        self.inrix_data_files: Dict[str, PathDict] = self._setup_inrix_data_files()
        self.portal_dir = self.data_root_path / "CADES_PORTAL"
        self.portal_meta_dir = self.portal_dir / "metadata"
        self.portal_meta_files = {
            "detectors": self.portal_meta_dir / "detectors.csv",
            "highways": self.portal_meta_dir / "highways.csv",
            "stations": self.portal_meta_dir / "stations.csv",
        }
        self.portal_data_files = self._setup_portal_data_files()

    def _setup_inrix_data_files(self):
        # INRIX data files dictionary
        inrix_data_files: Dict[str, PathDict] = {year: {} for year in self.years}

        for year in self.years:
            year_dir = self.inrix_dir / f"INRIX_CADES_{year}"
            if year_dir.exists():
                for file in year_dir.iterdir():
                    if file.is_file() and file.suffix == ".csv":
                        filename = file.name
                        if "INRIX_CADES" in filename:
                            inrix_data_files[year]["data"] = file
                        elif "TMC_Identification" in filename:
                            inrix_data_files[year]["meta"] = file
        return inrix_data_files
    
    def _setup_inrix_shapefiles(self):
        # INRIX shapefiles dictionary
        pass

    def _setup_portal_data_files(self):
        # Corridor Directories
        portal_corridors: PortalCorridorDict = {
            "I5": {
                "dirpath": self.portal_dir / "I-5 Corridor",
                "directions": ["NB", "SB"],
            },
            "I205": {
                "dirpath": self.portal_dir / "I-205 Corridor",
                "directions": ["NB", "SB"],
            },
            "SR14": {
                "dirpath": self.portal_dir / "SR-14 Corridor",
                "directions": ["EB", "WB"],
            },
        }

        # Portal data files dictionary
        portal_data_files: PortalFileCollection = {
            corridor: {
                year: {direction: list() for direction in info["directions"]}
                for year in self.years
            }
            for corridor, info in portal_corridors.items()
        }

        # Fill in the portal data files dictionary
        for corridor, info in portal_corridors.items():
            dirpath = info["dirpath"]
            directions = info["directions"]

            for file in dirpath.iterdir():
                if file.is_file():
                    filename = file.name
                    for year in self.years:
                        if year in filename:
                            for direction in directions:
                                if direction in filename:
                                    portal_data_files[corridor][year][direction].append(
                                        file
                                    )
        return portal_data_files

    def get_portal_meta(self, name):
        return self.portal_meta_files[name]

    def get_portal_data(self, corridor, year, direction):
        return self.portal_data_files[corridor][year][direction]

    def get_inrix(self, year, name):
        return self.inrix_data_files[year][name]

    def get_inrix_data(self, year):
        return self.get_inrix(year, "data")

    def get_inrix_meta(self, year):
        return self.get_inrix(year, "meta")

    def inrix_file_summary(self):
        for year, files in self.inrix_data_files.items():
            data_file = files.get("data", "Missing")
            meta_file = files.get("meta", "Missing")
            print(f"{year}: Data -> {data_file}, Meta -> {meta_file}")

    def portal_file_summary(self):
        for corridor, years_dict in self.portal_data_files.items():
            for year, directions in years_dict.items():
                for direction, files in directions.items():
                    print(f"{corridor} {year} {direction}: {len(files)} files")
                    print(f"    {files}")


# INRIX Shapefiles
# TODO: Add INRIX shapefiles to the dictionary
