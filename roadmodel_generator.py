import os
import sys
import glob
import numpy as np
from tkinter import Tk, ttk, StringVar, BooleanVar, E
from tkinter import filedialog
from tqdm import tqdm
import matplotlib.pyplot as plt
import pandas as pd
import traceback
import json
import warnings
import ast
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles.fonts import Font
from submodule import latlon_conv
from submodule import vincenty_method as vm
from submodule.latlon2grid import latlon2grid
from road_structures import RoadStructures
from opendrive_xml import OpenDriveXml
from opendrive.submodule.OpenDRIVE import OpenDRIVE
from opendrive.submodule import oauth_call
from opendrive.submodule import road_data_util
from route_extract import RouteExtract
from automatic_sign_placement_script import automatic_sign_placement_script

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


class RoadModelGenerator:
    def __init__(self):
        self.latlon_range = [0, 0, 0, 0]  
        self.road_condtion = "route"  
        self.store_path = "./output/"  
        self.highway_only = True
        self.path = r"2202DB"
        self.data_path = r""
        self.meshcode = []  # Secondary mesh code
        self.enable_sign_placement = True  # Enable automatic sign placement
        self.only_route = True  # True => search_range = 2, False => search_range = 500

    def add_automatic_sign_placement(self, output_filename):
        """
        Add automatic sign placement to the generated XODR file if enabled.
        
        Args:
            output_filename (str): Path to the XODR file to add signs to
            
        Returns:
            str: Path to the final output file with signs (if successful) or original file
        """
        if not self.enable_sign_placement:
            return output_filename
            
        print("Adding automatic sign placement...")
        try:
            output_path, success = automatic_sign_placement_script(
                xodr_input_path=output_filename,
                meshcode_list=self.meshcode,
                latitude0=self.latlon_range[0],
                longitude0=self.latlon_range[1],
                db_folder=self.data_path,
                distance_threshold=50.0,  # Increased from 10.0m to 50.0m
                output_dir=self.store_path,
                skip_coordinate_conversion=False
            )
            
            if success:
                try:
                    os.remove(output_filename)
                    print(f"Sign placement completed. Output saved to: {output_path}")
                    return output_path
                except Exception as e:
                    print("Error details:")
                    print(traceback.format_exc())
                    print(f"Warning: Could not remove temporary file {output_filename}: {e}")
                    return output_filename
            else:
                print("Warning: Sign placement failed, but basic road model was created.")
                return output_filename
                
        except Exception as e:
            print(f"Error during sign placement: {e}")
            print("Error details:")
            print(traceback.format_exc())
            return output_filename

    def generate_road_model(self, version="new"):
        """
        Generate road model with specified version
        Args:
            version (str): Version of generation method - "new" or "noshapedata"
        """

        #Display road model generation start
        print("Starting road model creation.")
        
        # Create directories if not exist
        if not os.path.isdir("./debug_output"):
            os.mkdir("./debug_output")
        if not os.path.isdir(self.store_path):
            os.mkdir(self.store_path)

        if not self.highway_only:
            version = "noshapedata"
        
        try:
            self.determine_data_path() 
            if version == "new":
                file_label = (
                    "debug_output/data_route_"
                    f"{self.latlon_range[0]}_{self.latlon_range[1]}_"
                    f"{self.latlon_range[2]}_{self.latlon_range[3]}.csv"
                )

                if os.path.isfile(file_label):
                # if False:
                    print("Loading existing road data...")
                    road_data_df = pd.read_csv(file_label)
                else:
                    # Create road structure for specified range and conditions
                    obj_road_structures = RoadStructures()
                    obj_road_structures.make_road_structures(
                        self.latlon_range, self.road_condtion, self.highway_only, self.data_path, self.meshcode
                    )
                    
                    df = pd.DataFrame()

                    for i in range(len(obj_road_structures.str_obj_branch_list)):

                        if obj_road_structures.str_obj_branch_list[i].error_is == "None":

                            df_polyline = obj_road_structures.str_obj_branch_list[i].df_polyline
                            df_lane_info = obj_road_structures.str_obj_branch_list[i].df_lane_info

                            road_id = [[2, 1], [5, 3], [4, 0]]

                            for k in road_id:
                                road_lengths = 0
                                x_list = []
                                y_list = []
                                z_list = []
                                for i in k:
                                    df_filtered = df_polyline[df_polyline["ID"] == i]

                                    road_length = df_filtered["length"].iloc[:-1].sum()

                                    if road_lengths == 0:
                                        x_list += df_filtered["x"].tolist()[:-1]
                                        y_list += df_filtered["y"].tolist()[:-1]
                                        z_list += df_filtered["elev"].tolist()[:-1]
                                        lane = df_lane_info[df_lane_info["road_id"] == i].shape[0] - 1
                                        speed = df_lane_info[df_lane_info["road_id"] == i].iloc[0]["speed"]
                                    else:
                                        x_list += df_filtered["x"].tolist()
                                        y_list += df_filtered["y"].tolist()
                                        z_list += df_filtered["elev"].tolist()

                                    road_lengths += int(road_length)

                                road_data_list = []
                                polyline = []
                                roadelevation = []
                                for j in range(len(x_list)):
                                    polyline.append(x_list[j])
                                    polyline.append(y_list[j])

                                    roadelevation.append([x_list[j], y_list[j], z_list[j]])

                                order = "OE"
                                width = lane * 3.5
                                one_way_code = 1
                                is_highway = True
                                roadType = "1"

                                road_data_list.append([order, polyline, lane, width, road_lengths, speed, one_way_code, is_highway, roadelevation, roadType])
                                road_data_df = pd.DataFrame(road_data_list)

                                df = pd.concat([df, road_data_df], ignore_index=True)

                        else:
                            print(" has error : " + obj_road_structures.str_obj_branch_list[i].error_is)

                    for i in range(len(obj_road_structures.str_obj_merge_list)):

                        if obj_road_structures.str_obj_merge_list[i].error_is == "None":

                            df_polyline = obj_road_structures.str_obj_merge_list[i].df_polyline
                            df_lane_info = obj_road_structures.str_obj_merge_list[i].df_lane_info

                            road_id = [[1, 2], [3, 5], [0, 4]]

                            for k in road_id:
                                road_lengths = 0
                                x_list = []
                                y_list = []
                                z_list = []
                                for i in k:
                                    df_filtered = df_polyline[df_polyline["ID"] == i]

                                    road_length = df_filtered["length"].iloc[:-1].sum()

                                    if road_lengths == 0:
                                        x_list += df_filtered["x"].tolist()[:-1]
                                        y_list += df_filtered["y"].tolist()[:-1]
                                        z_list += df_filtered["elev"].tolist()[:-1]

                                    else:
                                        x_list += df_filtered["x"].tolist()
                                        y_list += df_filtered["y"].tolist()
                                        z_list += df_filtered["elev"].tolist()
                                        lane = df_lane_info[df_lane_info["road_id"] == i].shape[0] - 1
                                        speed = df_lane_info[df_lane_info["road_id"] == i].iloc[0]["speed"]

                                    road_lengths += int(road_length)

                                road_data_list = []
                                polyline = []
                                roadelevation = []
                                for j in range(len(x_list)):
                                    polyline.append(x_list[j])
                                    polyline.append(y_list[j])

                                    roadelevation.append([x_list[j], y_list[j], z_list[j]])

                                order = "OE"
                                width = lane * 3.5
                                one_way_code = 1
                                is_highway = True
                                roadType = "1"

                                road_data_list.append([order, polyline, lane, width, road_lengths, speed, one_way_code, is_highway, roadelevation, roadType])
                                road_data_df = pd.DataFrame(road_data_list)

                                df = pd.concat([df, road_data_df], ignore_index=True)

                        else:
                            print(" has error : " + obj_road_structures.str_obj_merge_list[i].error_is)

                    for i in range(len(obj_road_structures.str_obj_mainlane_list)):

                        if obj_road_structures.str_obj_mainlane_list[i].error_is == "None":

                            df_polyline = obj_road_structures.str_obj_mainlane_list[i].df_polyline
                            df_lane_info = obj_road_structures.str_obj_mainlane_list[i].df_lane_info

                            road_id = list(range(df_polyline["ID"].iloc[-1] + 1))

                            for i in road_id:
                                df_filtered = df_polyline[df_polyline["ID"] == i]

                                if len(df_filtered) > 1:
                                    road_length = df_filtered["length"].iloc[:-1].sum()
                                else:
                                    road_length = 0

                                road_lengths = int(road_length)

                                x_list = df_filtered["x"].tolist()
                                y_list = df_filtered["y"].tolist()
                                z_list = df_filtered["elev"].tolist()

                                road_data_list = []
                                polyline = []
                                roadelevation = []
                                for j in range(len(x_list)):
                                    polyline.append(x_list[j])
                                    polyline.append(y_list[j])

                                    roadelevation.append([x_list[j], y_list[j], z_list[j]])

                                order = "OE"
                                lane = df_lane_info[df_lane_info["road_id"] == i].shape[0] - 1
                                speed = df_lane_info[df_lane_info["road_id"] == i].iloc[0]["speed"]
                                width = lane * 3.5
                                one_way_code = 1
                                is_highway = True
                                roadType = "1"

                                road_data_list.append([order, polyline, lane, width, road_lengths, speed, one_way_code, is_highway, roadelevation, roadType])
                                road_data_df = pd.DataFrame(road_data_list)

                                df = pd.concat([df, road_data_df], ignore_index=True)
                        else:
                            print(" has error : " + obj_road_structures.str_obj_mainlane_list[i].error_is)

                    if df.empty:
                        error_msg = f"Error 1: No road data found in the specified area: lat={self.latlon_range[0]}, lon={self.latlon_range[1]} to lat={self.latlon_range[2]}, lon={self.latlon_range[3]}"
                        raise ValueError(error_msg)

                    df.columns = ["order", "polyline", "lane", "width", "length", "speed", 
                                "oneway_code", "is_highway", "elevation", "roadType"]
                    df.to_csv(file_label)
                    road_data_df = pd.read_csv(file_label)

                road_data_df["polyline"] = [ast.literal_eval(d) for d in road_data_df["polyline"]]
                road_data_df["elevation"] = [ast.literal_eval(d) for d in road_data_df["elevation"]]

                center_point = [self.latlon_range[0], self.latlon_range[1]]
                open_drive = OpenDRIVE(road_data_df, center_point)
                open_drive.connect_all = False
                open_drive.convert_road()
                open_drive.convert_junction()

                output_filename = (
                    f"{self.store_path}/openDRIVE_data_"
                    f"{self.latlon_range[0]}_{self.latlon_range[1]}_"
                    f"{self.latlon_range[2]}_{self.latlon_range[3]}_"
                    f"{self.road_condtion}.xodr"
                )
                open_drive.output_xml(output_filename)
                
                # Add automatic sign placement if enabled
                final_output = self.add_automatic_sign_placement(output_filename)
                    
            elif version == "noshapedata":
                self.generate_road_model_without_shape()

            else:  # version == "old"
                self.generate_road_model_old()

        except (FileNotFoundError, IndexError) as e:
            print(f"Error 2: This area has no Shape data.")
            print("Shape data not available. Generating simplified road model...")
            self.generate_road_model_without_shape()
        except Exception as e:
            print(f"An error occurred during road model generation: \"{e}\" ")
            print(traceback.format_exc())

    def gui(self):
        # List for combobox items
        cb_road_condtion = ["route"]

        # Create main window
        root = Tk()

        # Set window size
        root.geometry("320x240")

        # Set window title
        root.title("RoadModelGenerator")

        frame1 = ttk.Frame(root, padding=(32))
        frame1.grid()

        # Latitude/Longitude range label
        label1 = ttk.Label(frame1, text="Lat/Lon Range", padding=(5, 2))
        label1.grid(row=0, column=1)

        # Start point label
        label2 = ttk.Label(frame1, text="Start Point", padding=(5, 2))
        label2.grid(row=1, column=0, sticky=E)

        # End point label 
        label3 = ttk.Label(frame1, text="End Point", padding=(5, 2))
        label3.grid(row=2, column=0, sticky=E)

        # Start point text form
        sw_latlon = StringVar()
        sw_latlon_txt = ttk.Entry(frame1, textvariable=sw_latlon, width=20)
        sw_latlon_txt.grid(row=1, column=1)

        # End point text form
        ne_latlon = StringVar()
        ne_latlon_txt = ttk.Entry(frame1, textvariable=ne_latlon, width=20)
        ne_latlon_txt.grid(row=2, column=1)

        # Create BooleanVar for checkbox state
        highway_only = BooleanVar(value=True)
        only_route = BooleanVar(value=True)  # True => search_range=2; False => search_range=500
        enable_sign_placement = BooleanVar(value=self.enable_sign_placement)

        # Create checkbox
        highway_only_cb = ttk.Checkbutton(frame1, text="Only Highways", variable=highway_only)
        highway_only_cb.grid(row=5, column=1)

        # Checkbox to choose only route; visible only when Highways Only is unchecked
        only_route_cb = ttk.Checkbutton(frame1, text="Only Route", variable=only_route)

        def update_only_route_visibility(*_args):
            if highway_only.get():
                try:
                    only_route_cb.grid_remove()
                except Exception:
                    pass
            else:
                only_route_cb.grid(row=6, column=1)

        # Bind visibility update when highway_only changes
        try:
            highway_only.trace_add('write', update_only_route_visibility)
        except AttributeError:
            highway_only.trace('w', update_only_route_visibility)

        # Initialize correct visibility
        update_only_route_visibility()

        # Checkbox to enable or disable automatic sign placement
        sign_cb = ttk.Checkbutton(frame1, text="Auto Signs", variable=enable_sign_placement)
        sign_cb.grid(row=7, column=1)

        # Button
        button1 = ttk.Button(
            frame1,
            text="OK",
            command=lambda: self.setting_parameter(sw_latlon.get(), ne_latlon.get(), highway_only.get(), only_route.get(), enable_sign_placement.get()),
        )
        button1.grid(row=8, column=1)

        # Keep window displayed
        root.mainloop()

    def setting_parameter(self, sw_latlon, ne_latlon, highway_only, only_route, enable_sign_placement):
        try:
            iDir = os.path.abspath(os.path.dirname(__file__))
            self.store_path = filedialog.askdirectory(initialdir=iDir)
            
            try:
                sw_coords = eval(sw_latlon)
                ne_coords = eval(ne_latlon)
                
                if not (isinstance(sw_coords, (tuple, list)) and len(sw_coords) == 2 and 
                       isinstance(ne_coords, (tuple, list)) and len(ne_coords) == 2):
                    error_msg = ("Error 4: Input syntax error - Please enter coordinates in format: (lat, lon)")
                    raise ValueError(error_msg)
                
                self.latlon_range = list(sw_coords) + list(ne_coords)
                self.highway_only = highway_only
                self.only_route = only_route
                self.enable_sign_placement = enable_sign_placement
                if self.highway_only:
                    self.generate_road_model()
                else:
                    self.generate_road_model(version="noshapedata")
                
            except SyntaxError:
                print("Error 4: Input syntax error - Please enter coordinates in format: (lat, lon)")
                print("Example: (34.375228, 132.408491)")
                error_msg = ("Error 4: Input syntax error")
                raise ValueError(error_msg)
                
        except Exception as e:
            raise

    def generate_road_model_without_shape(self):
        """
        Generate a basic road model when Shape data is not available.
        This function creates a simplified road network based on the latitude/longitude range.
        """
        try:
            search_range = 2 if getattr(self, 'only_route', True) else 500
            search_range_name = "only_route" if getattr(self, 'only_route', True) else "all_road"
            output_file = (
                    "debug_output/dataroute_noshapedata_"
                    f"{self.latlon_range[0]}_{self.latlon_range[1]}_"
                    f"{self.latlon_range[2]}_{self.latlon_range[3]}_{search_range_name}.csv"
                )
            starting_point =  {"lat": self.latlon_range[0], "lon": self.latlon_range[1]}       

            if os.path.isfile(output_file):
                print("Loading existing road data...")
                road_data_df = pd.read_csv(output_file)
                road_data_df['polyline'] = [ast.literal_eval(d) for d in road_data_df['polyline']]
                road_data_df['elevation'] = [ast.literal_eval(d) for d in road_data_df['elevation']]
            else:
                data_path = r"debug_output";
                obj_route_extract = RouteExtract(data_path)
                # Identify selected route data from ItsumoNAVIAPI.
                obj_route_extract.line_ls = obj_route_extract.determine_line(data_path, self.latlon_range, self.highway_only)

                j_data_list = []
                for i in range(0, len(obj_route_extract.line_ls)):
                    latitude = obj_route_extract.line_ls[i][0]
                    longitude = obj_route_extract.line_ls[i][1]
                    search_point_str = [str(n) for n in [latitude, longitude]]
                    search_point = ",".join(search_point_str)
                    j_data_list.append(json.loads(oauth_call.drive_route_multi(search_point, search_range)))

                road_data_df, delete_data_df = road_data_util.get_merged_road_data(j_data_list, highway_only=self.highway_only)
                road_data_df.to_csv(output_file, index=False)

            center_point = [starting_point["lat"], starting_point["lon"]]

            open_drive = OpenDRIVE(road_data_df, center_point, flag = True)

            open_drive.connect_all = False

            open_drive.convert_road()
            open_drive.convert_junction()

            output_filename = './output/'+'opendrive_noshapedata_'+ str(self.latlon_range[0])+ "_"+ str(self.latlon_range[1])+ "_"+ str(self.latlon_range[2])+ "_"+ str(self.latlon_range[3]) + "_" + search_range_name + '.xodr'
            open_drive.output_xml(output_filename)
            
            # Add automatic sign placement if enabled
            final_output = self.add_automatic_sign_placement(output_filename)

            print("Simplified road model generated successfully!")
        except Exception as e:
            print(f"Error creating simplified road model: \"{e}\" ")
            print("Error details:")
            print(traceback.format_exc())

    def generate_road_model_old(self):
        # Create road structure for specified range and conditions
        obj_road_structures = RoadStructures()
        obj_road_structures.make_road_structures(
            self.latlon_range, self.road_condtion, self.highway_only, self.data_path, self.meshcode
        )

        # Create and save OpenDrive file from road structure
        obj_open_drive_xml = OpenDriveXml()
        print("Generating OpenDrive...")

        if self.road_condtion == "mainlane":
            obj_open_drive_xml.make_mainlane_xml_combine(
                obj_road_structures.str_obj_mainlane_list
            )
        elif self.road_condtion == "route":
            obj_open_drive_xml.make_route_xml(
                obj_road_structures.str_obj_mainlane_list,
                obj_road_structures.str_obj_branch_list,
                obj_road_structures.str_obj_merge_list,
                obj_road_structures.connect_merge_branch_list,
            )

        output_filename = (
            f"{self.store_path}/openDRIVE_data_"
            f"{self.latlon_range[0]}_{self.latlon_range[1]}_"
            f"{self.latlon_range[2]}_{self.latlon_range[3]}_"
            f"{self.road_condtion}_old.xodr"
        )
        obj_open_drive_xml.xodr_xml.write(
            output_filename, 
            encoding="utf-8", 
            xml_declaration=True
        )

        print("complete!")

    def determine_data_path(self):
        """
        Determine the appropriate data path based on the latitude and longitude range.
        This function identifies which database should be used for a given geographic area.
        
        Returns:
        - str: The path to the appropriate data directory
        """
        try:
            self.data_path = r""
            self.meshcode = []
            data_path_list = []
            meshcode_list = self.latlon_conversion(self.latlon_range)
            db_path = glob.glob(os.path.join(self.path, "*"))
            for meshcode in meshcode_list:
                flag = False           
                for path in db_path:
                    folder_path = os.path.join(path, "SHAPE", "25K", meshcode)
                    if os.path.isdir(folder_path):
                        flag = True
                        data_path_list.append(path)
                        break
                    else:
                        flag = False
                        # print(f"Folder not found: {folder_path}")   
                if flag:
                    self.meshcode.append(meshcode)
                else:
                    print(f"Meshcode not found: {meshcode}")


            # Check if all paths in the list are the same
            if all(path == data_path_list[0] for path in data_path_list):
                self.data_path = data_path_list[0]
                print(f"Selected data path: {self.data_path}")
                print(f"Selected meshcode: {self.meshcode}")
            else:
                # Paths are different - report the inconsistency
                unique_paths = set(data_path_list)
                error_msg = f"Inconsistent data paths found: {', '.join(unique_paths)}"
                print(error_msg)
                raise ValueError(error_msg)
            
        except Exception as e:
            # print(f"Error determining data path: {e}")
            raise
        
    def latlon_conversion(self, latlon):
        lat_min, lat_max = min(latlon[0], latlon[2]), max(latlon[0], latlon[2])
        lon_min, lon_max = min(latlon[1], latlon[3]), max(latlon[1], latlon[3])

        lat_step, lon_step = 5 / 60, (7 / 60 + 30 / 60 / 60)
        lat_range = np.arange(lat_min, lat_max, lat_step)
        lon_range = np.arange(lon_min, lon_max, lon_step)

        lat_list = np.append(lat_range, lat_max)
        lon_list = np.append(lon_range, lon_max)

        lat_step, lon_step = 5 / 60, (7 / 60 + 30 / 60 / 60)
        lat_range = np.arange(lat_min, lat_max, lat_step)
        lon_range = np.arange(lon_min, lon_max, lon_step)

        lat_list = np.append(lat_range, lat_max)
        lon_list = np.append(lon_range, lon_max)

        grid = [[lat, lon] for lat in lat_list for lon in lon_list]

        if not grid:
            grid = [
                [latlon[0], latlon[1]],
                [latlon[2], latlon[3]],
                [latlon[0], latlon[3]],
                [latlon[2], latlon[1]],
            ]

        meshcode_2nd_list = {"Z" + str(latlon2grid.grid2nd(lon, lat)) for lat, lon in grid}
        return sorted(meshcode_2nd_list)


if __name__ == "__main__":
    obj = RoadModelGenerator()
    # obj.gui()

    # Error 1: No road data found in the specified area: 
    # obj.latlon_range = [34.35951516249397, 132.49736493576404, 34.35687616648195, 132.49958507032864]
    # obj.generate_road_model()

    # obj.latlon_range = [35.63271899375765, 139.720433252148, 35.634529077339806, 139.71973549584544]
    # obj.generate_road_model()

    # Error 2: This area has no Shape data. 
    # obj.latlon_range = [34.788918, 135.447942, 34.680313, 135.624046]
    # obj.generate_road_model()

    # Error 3: Unable to retrieve data from "Itsumo NAVI API"
    # obj.latlon_range = [135.447942, 34.788918, 135.62403, 34.680313]
    # obj.generate_road_model()

    # Error 4: Input syntax error
    # obj.latlon_range = [34.35951516249397, 132.49736493576404 34.35687616648195, 132.49958507032864]
    # obj.generate_road_model()

    # 高度方向のがたつき対応
    # obj.latlon_range = [34.38450787998186, 132.49864639503264, 34.356974345301396, 132.48758288929938]
    # obj.generate_road_model()

    # version により、生成方法が変更されることを確認する
    # obj.latlon_range = [44.18003518, 142.3685189, 44.17843719, 142.37911461]
    # obj.generate_road_model(version="noshapedata")
    # obj.generate_road_model(version="old")


    # obj.latlon_range = [34.69790472052763, 135.48988452516804, 34.69737638124318, 135.49158812523135]
    # obj.latlon_range = [34.38450787998186, 132.49864639503264, 34.35689848650365, 132.48759687223688]
    # obj.generate_road_model()

    # obj.latlon_range = [34.389712, 132.502909, 34.408817, 132.455349]
    # obj.latlon_range = [34.390402, 132.387588, 34.400012, 132.387077]
    # obj.highway_only = False
    # obj.generate_road_model()


    # # 広島高速３号線

    obj.latlon_range = [34.375228, 132.408491, 34.355420, 132.517107]
    obj.generate_road_model()
    
    # obj.latlon_range = [34.355198, 132.517380, 34.375421, 132.410155]
    # obj.generate_road_model()
    

    # # #広島高速２号線
    
    # obj.latlon_range = [34.353598, 132.497055, 34.405033, 132.510235]     #XXXXXXXXXXXXX test route_extract.py
    # obj.generate_road_model()
    
    # obj.latlon_range = [34.404866, 132.510363, 34.354237, 132.497167]
    # obj.generate_road_model()

    # #広島高速１号線    
    
    # obj.latlon_range = [34.405034, 132.510229, 34.448782, 132.541259]
    # obj.generate_road_model()
    
    # obj.latlon_range = [34.448748, 132.541546, 34.404924, 132.510440]
    # obj.generate_road_model()

    # #吹田山口線1_E2
    
    # obj.latlon_range = [34.338214, 132.294597, 34.463743, 132.422655]      #XXXXXXXXXXXXX test road_structures.py
    # obj.generate_road_model()
    
    # obj.latlon_range = [34.463664, 132.422770, 34.338211, 132.294767]
    # obj.generate_road_model()

    # # # 吹田山口線_E74
    
    # obj.latlon_range = [34.447746, 132.410940, 34.505743, 132.410102]
    # obj.generate_road_model()
    
    # obj.latlon_range = [34.505688, 132.410482, 34.450684, 132.408867]
    # obj.generate_road_model()

    # #E74_Hiroshima_Expwy_2
    
    # obj.latlon_range = [34.505881, 132.410157, 34.573495, 132.456668]
    # obj.generate_road_model()
    
    # obj.latlon_range = [34.573464, 132.456831, 34.505721, 132.410515]
    # obj.generate_road_model()

    # #E74_Hiroshima_Expwy_3
    
    # obj.latlon_range = [34.574470, 132.457158, 34.660080, 132.525031]
    # obj.generate_road_model()
    
    # obj.latlon_range = [34.660106, 132.525230, 34.574264, 132.457219]
    # obj.generate_road_model()

    # #E2A_Chugoku_Expwy_1
    
    # obj.latlon_range = [34.546953, 132.227732, 34.574290, 132.456225]
    # obj.generate_road_model()
    
    # obj.latlon_range = [34.573550, 132.455992, 34.546561, 132.230385]
    # obj.generate_road_model()

    # #E2_San-yo_Expwy_2
    
    # obj.latlon_range = [34.463743, 132.422655, 34.451064, 132.543449]
    # obj.generate_road_model()
    
    # obj.latlon_range = [34.450949, 132.543347, 34.463664, 132.422770]
    # obj.generate_road_model()

    # #E2_San-yo_Expwy_3
    
    # obj.latlon_range = [34.453438, 132.539739, 34.468337, 132.594225]
    # obj.generate_road_model()
    
    # obj.latlon_range = [34.468108, 132.594557, 34.450949, 132.543347]
    # obj.generate_road_model()

    # # Bayshore Route
    
    # obj.latlon_range = [35.536105, 139.795071, 35.686947, 139.946786]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.686822, 139.946905, 35.536136, 139.795277]
    # obj.generate_road_model()

    # # No. 1 Ueno Route
    
    # obj.latlon_range = [35.683545, 139.778208, 35.718891, 139.783018]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.718847, 139.783155, 35.683517, 139.778277]
    # obj.generate_road_model()

    # # No. 1 Haneda Route
    
    # obj.latlon_range = [35.544978, 139.743229, 35.651451, 139.759406]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.651686, 139.759739, 35.545002, 139.743368]
    # obj.generate_road_model()

    # # No. 2 Meguro Route
    
    # obj.latlon_range = [35.654831, 139.737680, 35.617455, 139.717752]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.617616, 139.717719, 35.654815, 139.737740] #XXXXXXXXXXXXX
    # obj.generate_road_model()

    # # No. 3 Shibuya Route 
    
    # obj.latlon_range = [35.627374, 139.626510, 35.666181, 139.737647] #XXXXXXXXXXXXX
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.666101, 139.737733, 35.627222, 139.626573] #XXXXXXXXXXXXX
    # obj.generate_road_model()

    # # No. 4 Shinjuku Route 
    
    # obj.latlon_range = [35.677287, 139.614673, 35.681250, 139.726270]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.681153, 139.726360, 35.677063, 139.614567]
    # obj.generate_road_model()

    # # No. 5 Ikebukuro Route
    
    # obj.latlon_range = [35.693736, 139.755318, 35.826492, 139.638344]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.826583, 139.638504, 35.693932, 139.755465]
    # obj.generate_road_model()

    # # No. 6 Mukojima-Misato Route
    
    # obj.latlon_range = [35.681597, 139.780517, 35.836387, 139.859487]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.836306, 139.859590, 35.681500, 139.780341]
    # obj.generate_road_model()

    # # No. 7 Komatsugawa Route 
    
    # obj.latlon_range = [35.691329, 139.789935, 35.707196, 139.912178]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.707132, 139.912370, 35.691246, 139.790001]
    # obj.generate_road_model()

    # # No. 9 Fukagawa Route 
    
    # obj.latlon_range = [35.644563, 139.812218, 35.681129, 139.785643]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.681877, 139.787221, 35.645053, 139.814052]
    # obj.generate_road_model()

    # # No. 10 Harumi Route 
    
    # obj.latlon_range = [35.637726, 139.795707, 35.654120, 139.782855]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.654206, 139.782944, 35.639215, 139.798263]
    # obj.generate_road_model()

    # # No. 11 Daiba Route
    
    # obj.latlon_range = [35.630882, 139.782908, 35.646248, 139.757144]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.646294, 139.757283, 35.631758, 139.784604]
    # obj.generate_road_model()

    # # Y Yaesu Route
    
    # obj.latlon_range = [35.662658, 139.762005, 35.676594, 139.766404]
    # obj.generate_road_model()
    
    # obj.latlon_range = [35.676280, 139.766247, 35.662406, 139.762125]
    # obj.generate_road_model()



