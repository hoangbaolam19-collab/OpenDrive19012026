import pandas as pd
import numpy as np

from tqdm import tqdm

from opendrive.submodule import junction
from opendrive.submodule.LinkData import LinkData

class OpenDRIVE_Junction(object):

	def __init__(self, road_line_df, road_search_point, flag = False):
		self.dict = dict()
		self.intersection_dict = dict()
		self.path_dict = dict()
		self.df = []
		self.link_data = LinkData(road_line_df, road_search_point, flag)
	
	def clear(self):
		self.dict = dict()
		self.path_dict = dict()
		self.df = []
	
	def add(self, junction_id, junction_point_list):
		self.dict[junction_id] = junction_point_list
	
	def add_path(self, junction_id, path_point_list):
		self.path_dict[junction_id] = path_point_list
		
	def get_road_length(self, df):
		road_length = 0.0
		for i in range(0, df.shape[0]-1):
			road_length += df.at[i,"length"]
		return road_length
		
	def convert(self):
		open_drive_data_list = []
		junction_id_set = set(self.dict.keys()) | set(self.path_dict.keys())
		print("Convert information from junction objects into OpenDrive format.")
		for junction_id in tqdm(junction_id_set):
			data_list = self.get_junction(junction_id)
			if len(data_list) > 0:
				open_drive_data_list.extend(data_list)
			path_data_list = self.get_junction_path(junction_id)
			if len(path_data_list) > 0:
				open_drive_data_list.extend(path_data_list)
		
		if len(open_drive_data_list) > 0:
			self.df = pd.DataFrame(open_drive_data_list)
			self.df.columns = ["junction_id","from_polyline","to_polyline","path","x","y","df","lane_count","lane_linkage", "lane_width", "road_length", "speed"]
		else:
			# Create empty DataFrame with correct columns if no data
			self.df = pd.DataFrame(columns=["junction_id","from_polyline","to_polyline","path","x","y","df","lane_count","lane_linkage", "lane_width", "road_length", "speed"])
	
	def get_junction(self, junction_id):
		open_drive_data_list = []
		if junction_id in self.dict.keys():
			junction_point_list = self.dict[junction_id]
			for junction_point in junction_point_list:
				polyline_part = junction_point[0]
				from_polyline = polyline_part[0]
				to_polyline = polyline_part[1]
				
				point_part = junction_point[1]
				point1 = point_part[0]
				point2 = point_part[1]
				
				lane_part = junction_point[2]
				lane_count = lane_part[0]
				lane_width = lane_part[1]
				lane_linkage = lane_part[2]

				speed = self.link_data.get_speed_junction(from_polyline[0])
				
				x_list,y_list,open_drive_df = junction.get_intersection_line(point1, point2)
				road_length = self.get_road_length(open_drive_df)
				
				open_drive_data = [junction_id, from_polyline, to_polyline, [], x_list, y_list, open_drive_df, lane_count, lane_linkage, lane_width, road_length, speed]
				open_drive_data_list.append(open_drive_data)
			
		return open_drive_data_list
		
	def get_junction_path(self, junction_id):
		open_drive_data_list = []
		if junction_id in self.path_dict.keys():
			junction_path_point_list = self.path_dict[junction_id]
			for junction_path_point in junction_path_point_list:
				polyline_part = junction_path_point[0]
				from_polyline = polyline_part[0]
				to_polyline = polyline_part[1]
				path = polyline_part[2]
				
				point_part = junction_path_point[1]
				
				x_list,y_list,open_drive_df = junction.get_intersection_line(point_part[0], point_part[1][0])
				path_part = point_part[1][1]
				path_df = path_part[2]
				
				x_list.extend(path_part[0])
				y_list.extend(path_part[1])
				last_index = open_drive_df.index[-1]
				merged_df = open_drive_df.drop(last_index)
				merged_df = pd.concat([merged_df,path_df],ignore_index=True)
				
				lane_part = junction_path_point[2]
				lane_count = lane_part[0]
				lane_linkage = lane_part[2]
				lane_width = lane_part[1]
				
				to_x_list,to_y_list,open_drive_df = junction.get_intersection_line(point_part[1][2], point_part[2])
				x_list.extend(to_x_list)
				y_list.extend(to_y_list)
				last_index = merged_df.index[-1]
				merged_df = merged_df.drop(last_index)
				merged_df = pd.concat([merged_df, open_drive_df],ignore_index=True)
				road_length = self.get_road_length(merged_df)
				
				open_drive_data = [junction_id, from_polyline, to_polyline, path, x_list, y_list, merged_df, lane_count, lane_linkage, lane_width, road_length]
				open_drive_data_list.append(open_drive_data)
			
		return open_drive_data_list