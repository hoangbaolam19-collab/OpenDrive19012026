import glob
import os

import pandas as pd
import geopandas as gpd


class DetailNaviData:
    def __init__(self, file, path):
        """
        Initialize the DetailNaviData class with file and path information.

        Parameters:
        - file (str): The name of the file to process.
        - path (str): The directory path where the file is located.
        """
        self.file = file
        self.path = path
        self.df_all = {
            "turnoff": 0,
            "node": 0,
            "oneway": 0,
            "enterexit": 0,
            "roadhiway": 0,
            "lanechangepoint": 0,
            "maxspeed": 0,
        }

    #########################################################
    def load_turnoff(self):
        """
        Load turnoff data from the specified DBF file and update the df_all dictionary.

        Returns:
        - str: "NotFound" if the file is not found, otherwise updates the df_all dictionary.
        """
        file_path = os.path.join(self.path, "SHAPE", "25K", self.file, f"{self.file}_TURNOFF_BORDER.dbf")
        if os.path.isfile(file_path):
            df_turn = gpd.read_file(file_path, sep=",")
            df_turn.iloc[:, [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]] /= 1000 * 3600
            df_turn_node = df_turn.loc[
                :,
                [
                    "nodeno",
                    "ido1",
                    "keido1",
                    "ido2",
                    "keido2",
                    "ido3",
                    "keido3",
                    "ido4",
                    "keido4",
                    "ido5",
                    "keido5",
                ],
            ]

            self.df_all["turnoff"] = df_turn_node
            return
            
        print(f"Turnoff file not found: {file_path}")
        raise FileNotFoundError(f"Turnoff file not found: {file_path}")

    def load_node(self):
        """
        Load node data from the specified DBF file and update the df_all dictionary.

        Returns:
        - str: "NotFound" if the file is not found, otherwise updates the df_all dictionary.
        """
        file_path = os.path.join(self.path, "SHAPE", "25K", self.file, f"{self.file}_NODE.dbf")
        if os.path.isfile(file_path):
            df_node = gpd.read_file(file_path, sep=",")
            df_node.iloc[:, [2, 3]] /= 1000 * 3600
            df_node_data = df_node.loc[
                :, ["meshcode", "nodeno", "x", "y", "linkno"]
            ]
            self.df_all["node"] = df_node_data
            return

        print(f"Node file not found: {file_path}")  
        raise FileNotFoundError(f"Node file not found: {file_path}")

    def load_oneway(self):
        """
        Load one-way data from the specified DBF file and update the df_all dictionary.

        Returns:
        - str: "NotFound" if the file is not found, otherwise updates the df_all dictionary.
        """
        file_path = os.path.join(self.path, "SHAPE", "25K", self.file, f"{self.file}_ONE-WAY.dbf")
        if os.path.isfile(file_path):
            df_oneway = gpd.read_file(file_path, sep=",")
            df_oneway_data = df_oneway.loc[
                :, ["meshcode", "linkno", "snodeno", "enodeno"]
            ]
            self.df_all["oneway"] = df_oneway_data
            return

        print(f"Oneway file not found: {file_path}")
        raise FileNotFoundError(f"Oneway file not found: {file_path}")

    def load_enterexit(self):
        """
        Load enter/exit lane data from the specified DBF file and update the df_all dictionary.

        Returns:
        - str: "NotFound" if the file is not found, otherwise updates the df_all dictionary.
        """
        file_path = os.path.join(self.path, "SHAPE", "25K", self.file, f"{self.file}_ENTEREXIT_LANE.dbf")
        if os.path.isfile(file_path):
            df_enterexit = gpd.read_file(file_path, sep=",", dtype={
                "tnodeno": "int",
                "snodeno": "int",
                "enodeno": "int",
                "slanecnt": "int",
                "slaneinfo": "str",
                "elanecnt": "int",
                "elaneinfo": "str",
            })
            df_enterexit_data = df_enterexit.loc[
                :,
                [
                    "tnodeno",
                    "snodeno",
                    "enodeno",
                    "slanecnt",
                    "slaneinfo",
                    "elanecnt",
                    "elaneinfo",
                ],
            ]
            self.df_all["enterexit"] = df_enterexit_data
            return

        print(f"Oneway file not found: {file_path}")
        raise FileNotFoundError(f"Oneway file not found: {file_path}")

    ####################################################################################

    def load_roadhiway(self):
        """
        Load road highway data from the specified DBF files and update the df_all dictionary.

        Returns:
        - str: "NotFound" if the files are not found, otherwise updates the df_all dictionary.
        """
        df_roadhiway1_data = []
        df_roadhiway2_data = []
        file_path1 = os.path.join(self.path, "SHAPE", "25K", self.file, f"{self.file}_ROAD_HIWAY1.dbf")
        file_path2 = os.path.join(self.path, "SHAPE", "25K", self.file, f"{self.file}_ROAD_HIWAY2.dbf")
        if os.path.isfile(file_path1) or os.path.isfile(file_path2):
            if os.path.isfile(file_path1):
                df_roadhiway1 = gpd.read_file(file_path1, sep=",")
                df_roadhiway1_data = df_roadhiway1.loc[
                    :, ["meshcode", "linkno", "snodeno", "enodeno"]
                ]
                self.df_all["roadhiway"] = df_roadhiway1_data

            if os.path.isfile(file_path2):
                df_roadhiway2 = gpd.read_file(file_path2, sep=",")
                df_roadhiway2_data = df_roadhiway2.loc[
                    :, ["meshcode", "linkno", "snodeno", "enodeno"]
                ]
                self.df_all["roadhiway"] = self.df_all["roadhiway"].append(
                    df_roadhiway2_data, ignore_index=True
                )

            return

        print(f"Roadhiway file not found: {file_path1} or {file_path2}")
        raise FileNotFoundError(f"Roadhiway file not found: {file_path1} or {file_path2}")

    def load_lanechangepoint(self):
        """
        Load lane change point data from the specified DBF file and update the df_all dictionary.

        Returns:
        - str: "NotFound" if the file is not found, otherwise updates the df_all dictionary.
        """
        file_path = os.path.join(self.path, "SHAPE", "25K", self.file, f"{self.file}_LANECHANGE_POINT.dbf")
        if os.path.isfile(file_path):
            df_lanechangepoint = gpd.read_file(file_path, sep=",")
            df_lanechangepoint_data = df_lanechangepoint.loc[
                :,
                [
                    "tnodeno",
                    "snodeno",
                    "linkno",
                    "slanecnt",
                    "slaneinfo",
                    "elanecnt",
                    "elaneinfo",
                ],
            ]
            self.df_all["lanechangepoint"] = df_lanechangepoint_data
            return

        print(f"Lanechangepoint file not found: {file_path}")
        raise FileNotFoundError(f"Lanechangepoint file not found: {file_path}")

    ####################################################################################

    def load_maxspeed(self):
        """
        Load maxspeed data from the corresponding CSV file and update the df_all dictionary.

        Returns:
        - str: "NotFound" if no files are found, otherwise updates the df_all dictionary.
        """
        file_path = os.path.join(self.path, "SHAPE", "25K", self.file, f"{self.file}_MAXSPEED_SECTION.dbf")
        file_path_highway = os.path.join(self.path, "SHAPE", "25K", self.file, f"{self.file}_TOLLMS_SECTION.dbf")
        
        # Initialize empty DataFrame if needed
        if self.df_all["maxspeed"] == 0:
            self.df_all["maxspeed"] = pd.DataFrame(columns=["meshcode", "linkno", "maxspeed"])
        
        files_found = False
        
        # Load regular maxspeed data
        if os.path.isfile(file_path):
            df_maxspeed = gpd.read_file(file_path, sep=",")
            df_maxspeed_data = df_maxspeed.loc[:, ["meshcode", "linkno", "maxspeed"]]
            self.df_all["maxspeed"] = df_maxspeed_data
            files_found = True
        
        # Load highway maxspeed data
        if os.path.isfile(file_path_highway):
            df_maxspeed_highway = gpd.read_file(file_path_highway, sep=",")
            df_maxspeed_highway_data = df_maxspeed_highway.loc[:, ["meshcode", "linkno", "maxspeed"]]
            self.df_all["maxspeed"] = pd.concat([self.df_all["maxspeed"], df_maxspeed_highway_data], ignore_index=True)
            files_found = True
        
        if not files_found:
            print(f"Maxspeed files not found: {file_path} and {file_path_highway}")
            return "NotFound"
        
        return

    def dbf_to_csv(self):
        """
        Convert DBF files to CSV format and save them in the specified directory.
        """
        print(os.path.join(self.path[0], "SHAPE", "25K", self.file[0]))
        print(0)
        dbf_path = os.path.join(self.path[0], "SHAPE", "25K", self.file[0])  # Set path to DBF files

        for fp in glob.glob(os.path.join(dbf_path, "*.dbf")):  # Extract files with .dbf extension
            data = gpd.read_file(fp)  # Read data

            csv_path = os.path.join(self.path[0], "CSV", self.file[0])  # Specify path to CSV folder
            os.makedirs(csv_path, exist_ok=True)  # Create folder in CSV directory
            f_name = fp.replace("SHAPE", "CSV").replace("25K\\", "").replace(".dbf", ".csv")

            data.to_csv(f_name)  # Save data as CSV

    def msec_to_degree(self, input):
        """
        Convert milliseconds to degrees.

        Parameters:
        - input (float): The value in milliseconds to convert.

        Returns:
        - float: The converted value in degrees.
        """
        input = input / 1000 / 3600
        input.round(7)
        """
            #########################################################################################
            ## The round function is not working properly. Using the round function for rounding is not appropriate.
            ## Although the data can be used without rounding, improvement is needed.
            #########################################################################################
            """
        return input

    def data_forming(self):
        """
        Convert latitude and longitude values from seconds to degrees, minutes, seconds
        in NODE and TURNOFF files and save the updated data.
        """
        for f in self.file:
            csv_path = os.path.join(self.path[0], "CSV", f)

            for fp in glob.glob(os.path.join(csv_path, f"{f}_NODE*")):
                df = pd.read_csv(fp, sep=",")
                df.iloc[:, [3, 4]] /= 1000 * 3600
                df.to_csv(fp)

            for fp in glob.glob(os.path.join(csv_path, "*TURNOFF_BORDER*")):
                df = pd.read_csv(fp, sep=",")
                df.iloc[:, [7, 8, 9, 10, 11, 12, 13, 14, 15, 16]] /= 1000 * 3600
                df.to_csv(fp)


if __name__ == "__main__":
    meshcode = ["Z533936"]
    path = [r"2202DB\TOKYO"]
    detail = DetailNaviData(meshcode, path)
    detail.dbf_to_csv()
    detail.data_forming()
