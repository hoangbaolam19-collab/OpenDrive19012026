import pandas as pd
import numpy as np

import math
import matplotlib.pyplot as plt
from tqdm import tqdm

from opendrive.submodule import road_point
from opendrive.submodule import open_drive_format
from opendrive.submodule import link_util

class OpenDRIVE_Road(object):
	
	def __init__(self, first_element_no = 0):
		self.road_list = []
		self.df = []
		self.first_element_no = first_element_no
		self.next_element_no = first_element_no
		
		self.devide_spiral = True
		self.use_parametric_cubic = False
		self.connect_intersection = False
		
	def clear(self):
		self.road_list = []
		self.df = []
		self.first_element_no = 0
		self.next_element_no = 0

		self.devide_spiral = True
		self.use_parametric_cubic = False
		self.connect_intersection = False
	
	def get_road_point(self, polyline_id, polyline):
		road_point_df = pd.DataFrame(polyline[2])
		road_point_df.columns = ["x","y","length"]
		return [polyline_id, polyline[0], polyline[1], road_point_df]
		
	def add(self, polyline_id, road_polyline):
		self.road_list.append(self.get_road_point(polyline_id, road_polyline))
		
	def get_opendrive(self, road_data_df):
		data_size = road_data_df.shape[0]
		if data_size > 2:
			S = 1
			b_spline_point_df = road_point.B_spline_interpolate(road_data_df, S)
			road_data_df = road_point.point2spiral(b_spline_point_df)
			threshold_diff_radius = 1
			road_data_df = road_point.spiral2arc(road_data_df, threshold_diff_radius)
			threshold_radius = 3000000
			threshold_diff_angle = 0.001
			road_data_df = road_point.spiral2line(road_data_df, threshold_radius, threshold_diff_angle)
			
			if self.use_parametric_cubic:
				road_data_df = road_point.spiral2parametric_cubic(road_data_df)
			if self.devide_spiral:
				road_data_df = road_point.devide_spiral(road_data_df)
		else:
			road_data_df = road_point.point2line(road_data_df)
			
		return open_drive_format.convert(road_data_df)
		
	def get_road_length(self, df):
		road_length = 0.0
		for i in range(0, df.shape[0]-1):
			road_length += df.at[i,"length"]
		return road_length
		
	def convert(self):
		open_drive_data_list = []
		print("Convert information from road objects into OpenDrive format.")
		for i in tqdm(range(0, len(self.road_list))):
			if self.road_list[i][3].shape[0] > 1:
				polyline_id = self.road_list[i][0]
				start_node = self.road_list[i][1]
				end_node = self.road_list[i][2]
				x_list,y_list,open_drive_df = self.get_opendrive(self.road_list[i][3])
				road_length = self.get_road_length(open_drive_df)
				open_drive_data = [polyline_id, start_node, end_node, x_list, y_list, open_drive_df, road_length]
				open_drive_data_list.append(open_drive_data)
		self.df = pd.DataFrame(open_drive_data_list)
		self.df.columns = ["polyline_id","start_node","end_node","x","y","df","road_length"]
		
	def spiral2parametric_cubic(self):
		for i in range(0, self.df.shape[0]):
			for j in range(0, self.df.at[i,"df"].shape[0]-1):
				if self.df.at[i,"df"].at[j, "type"] == "spiral":
					start_radius = self.df.at[i,"df"].at[j,"radius"]
					end_radius = self.df.at[i,"df"].at[j+1,"radius"]
					if start_radius*end_radius < 0:
						self.df.at[i,"df"].at[j, "type"] = "parametric_cubic"
	
	def get_polyline_start_node_point(self, polyline_id, node_id):
		
		exist_point = False
		node_point = []
		target_df = self.df[self.df["polyline_id"] == polyline_id]

		target_start = target_df[target_df["start_node"] == node_id]
		for index, row in target_start.iterrows():
			df = row["df"]
			x = df.at[0,"x"]
			y = df.at[0,"y"]
			direction = link_util.normalize_direction(df.at[0,"initial_direction"])
			direction += 180
			if direction > 180:
				direction -= 360
			exist_point = True
			node_point = [[x,y],direction,0.0]
			
		return exist_point, node_point
		
	def get_polyline_end_node_point(self, polyline_id, node_id):
		
		exist_point = False
		node_point = []
		target_df = self.df[self.df["polyline_id"] == polyline_id]
		
		target_end = target_df[target_df["end_node"] == node_id]
		for index, row in target_end.iterrows():
			df = row["df"]
			point_size = len(df["x"])
			x = df.at[point_size-1,"x"]
			y = df.at[point_size-1,"y"]
			direction = link_util.normalize_direction(df.at[point_size-1,"initial_direction"])
			node_point = [[x,y],direction,0.0]
			exist_point = True
			
		return exist_point, node_point