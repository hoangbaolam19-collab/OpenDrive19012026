import sys

import pandas as pd
import numpy as np
import json
from submodule import oauth_call
from submodule import road_data_util

args = sys.argv
if len(args) == 2:
	data_id = args[1]
	input_file_name = "search_point_" + data_id
	output_file_name = "road_data_" + data_id
else:
	input_file_name = "search_point_test7"
	output_file_name = "road_data"

input_file = "./search_point/" + input_file_name + ".csv"
output_file = "./road_data/" + output_file_name + ".csv"

search_point_df = pd.read_csv(input_file)

j_data_list = []
for i in range(0, len(search_point_df)):
	latitude = search_point_df.at[i,"latitude"]
	longitude = search_point_df.at[i,"longitude"]
	search_range = search_point_df.at[i,"range"]
	search_point_str = [str(n) for n in [latitude, longitude]]
	search_point = ",".join(search_point_str)
	j_data_list.append(json.loads(oauth_call.drive_route_multi(search_point, search_range)))

road_data_df, delete_data_df = road_data_util.get_merged_road_data(j_data_list)

road_data_df.to_csv(output_file, index=False)