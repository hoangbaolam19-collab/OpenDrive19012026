import sys
import os
import shutil
import argparse

import pandas as pd
import numpy as np
import ast
from submodule.OpenDRIVE import OpenDRIVE

parser = argparse.ArgumentParser(description='')
parser.add_argument('--connect_all_junction','-a')
parser.add_argument('--file_id','-f')
parser.add_argument('--use_poly3','-p')
parser.add_argument('--use_elevation','-e')

args = parser.parse_args()
if args.file_id != None:
	csv_folder_name = "open_drive_data_"+args.file_id+"/"
	xml_file_name = "open_drive_format_"+ args.file_id
	input_file_name = "road_data_" + args.file_id
	center_point_file_name = "search_point_" + args.file_id
else:
	input_file_name = "road_data"
	center_point_file_name = "search_point"
	csv_folder_name = "open_drive_data/"
	xml_file_name = "open_drive_format"

input_file = "./road_data/" + input_file_name +".csv"
center_point_file = "./search_point/" + center_point_file_name + ".csv"

output_folder = "./open_drive_format/"
output_xml_file = output_folder + xml_file_name +".xodr"

center_point_df = pd.read_csv(center_point_file)
latitude = center_point_df["latitude"].values[0]
longitude = center_point_df["longitude"].values[0]
center_point = [latitude, longitude]

road_data_df= pd.read_csv(input_file)
road_data_df['polyline'] = [ast.literal_eval(d) for d in road_data_df['polyline']]
road_data_df['elevation'] = [ast.literal_eval(d) for d in road_data_df['elevation']]

open_drive = OpenDRIVE(road_data_df, center_point)

if args.connect_all_junction == "1":
	open_drive.connect_all = True
else:
	open_drive.connect_all = False
	
if args.use_poly3 == "1":
	open_drive.use_parametric_cubic()

if args.use_elevation == "0":
	open_drive.not_use_elevation()

open_drive.convert_road()
open_drive.convert_junction()

open_drive.output_xml(output_xml_file)