import pandas as pd
import numpy as np
import math
import copy

# from osgeo import ogr, osr, gdal
from pyproj import CRS, Transformer
from tqdm import tqdm
import matplotlib.pyplot as plt

from opendrive.submodule import link_util
from opendrive.submodule import polyline_point_util as polyline_util
from opendrive.submodule.Dijkstra import Dijkstra
from opendrive.submodule.coord_systems import get_coordinate_systems


class LinkData(object):
	
	def __init__(self, road_df, origin_point, flag, location_prefecture=None):
		"""
		Initialize LinkData with coordinate transformation.
		
		Args:
			road_df: Road dataframe
			origin_point: [latitude, longitude] of origin
			flag: Whether to use projection (True) or simple swap (False)
			location_prefecture: Prefecture name for zone selection (e.g., "Nagano", "Hiroshima")
		"""
		self.flag = flag
		self.location_prefecture = location_prefecture

		self.intersection_offset = 10000
		self.junction_margin = 5.0
		self.polyline_sampling_interval = 25.0  

		self.use_fixed_lane_count = False
		self.two_way_traffic_lane_count = 1
		self.one_way_traffic_lane_count = 1

		self.enable_highway = True
		
		self.road_df = road_df
		self.road_dict = road_df.to_dict(orient='index')
		self.road_df["road_key"] = list(self.road_dict.keys())
		
		self.polyline_list = []
		self.node_list = []
		self.df = []

		self.junction_node = []
		self.intersection_list = []

		self.connect_node = []
		self.connect_node_polyline_dict = dict()
		self.merged_df = pd.DataFrame(columns=["polyline_id", "start_node", "end_node", "xy", "oneway_code", "latlon", "start_junction", "end_junction", "elevation"])
		# self.merged_df = pd.DataFrame()
		self.merged_polyline = set()
		
		self.isolated_node = []

		# EPSG:4612 = JGD2000 geographic (lat/lon)
		# EPSG:6676 = JGD2011 planar Zone VIII (or other zones based on location)
		src_srs, dst_srs, self.zone_epsg = get_coordinate_systems(
			location_prefecture=location_prefecture,
			lat=origin_point[0] if origin_point else None,
			lon=origin_point[1] if origin_point else None
		)
		self.transformation = Transformer.from_crs(src_srs, dst_srs)

		if self.flag:
			self.origin_x, self.origin_y = self.latlon2xy(origin_point)
		else:
			self.origin_x, self.origin_y = (0,0)

		self.set_dataframe()
		
		print("Classify nodes into 3 types: junction_node, connect_node, isolated_node.")
		for i in tqdm(range(0, len(self.node_list))):
			self.set_junction_node(i)
		
		self.set_intersection_list(self.get_intersection_link())
		self.add_remain_intersection_polyline()
		
		self.set_junction_id()
		
		self.set_connect_node_polyline()
		self.set_merged_dataframe()
		
		self.df['branch'] = -1
		self.df['merge'] = -1
		self.merged_df['branch'] = -1
		self.merged_df['merge'] = -1
	
	def latlon2xy(self, node):
		if self.flag:
			node_xy = self.transformation.transform(node[0],node[1])
		else:
			node_xy = (node[1],node[0])
		return node_xy[1], node_xy[0]

	def polyline_latlon2xy(self, polyline, origin_x, origin_y ):
		polyline_xy = []
		for i in range(0,len(polyline)):
			x,y = self.latlon2xy(polyline[i])
			polyline_xy.append([x-self.origin_x,y - self.origin_y])
		return polyline_xy

	def get_oneway_code( self, order, oneway_code ):
		if order == "EO":
			if oneway_code == 1:
				result_code = 2
			elif oneway_code == 2:
				result_code == 1
			else:
				result_code = oneway_code
		else:
			result_code = oneway_code
			
		return result_code
		
	def set_polyline_list(self):
		
		for road_key in self.road_dict.keys():
			polyline = self.road_dict[road_key]["polyline"]
			point_count = int(len(polyline)/2)
			order = self.road_dict[road_key]["order"]
			road_oneway_code = self.road_dict[road_key]["oneway_code"]
			
			polyline_id = road_key
			oneway_code = self.get_oneway_code( order, road_oneway_code)
			polyline_point=[]
			if order == 'OE':
				for i in range(0,point_count):
					latitude = polyline[i*2]
					longitude = polyline[i*2+1]
					polyline_point.append([latitude,longitude])
			else:
				for i in range(0,point_count):
					latitude = polyline[(point_count*2-1) - (i*2+1)]
					longitude = polyline[(point_count*2-1) - (i*2)]
					polyline_point.append([latitude,longitude])
			
			self.polyline_list.append([polyline_id, polyline_point, oneway_code])
	
	def set_node_list(self):
		
		self.node_list = []
		for polyline in self.polyline_list:
			self.node_list.append([polyline[1][0][0],polyline[1][0][1]])
			self.node_list.append([polyline[1][-1][0],polyline[1][-1][1]])
		
		node_df = pd.DataFrame(self.node_list)
		node_df.columns = ["latitude","longitude"]
		node_df = node_df.drop_duplicates()
		self.node_list = node_df.to_numpy().tolist()

	def find_node_id(self, node ):
		node_id = -1
		for i in range(0, len(self.node_list)):
			if node == self.node_list[i]:
				node_id = i
		return node_id
		
	def get_road_elevation(self, road_key):
		elevation_list = self.road_dict[road_key]["elevation"]
		order = self.road_dict[road_key]["order"]
		point_count = len(elevation_list)
		road_elevation = []
		if order == "OE":
			for element in elevation_list:
				latitude = element[0]
				longitude = element[1]
				hight = element[2]
				x,y = self.latlon2xy([latitude, longitude])
				road_elevation.append([x-self.origin_x,y-self.origin_y,hight])
		else:
			for i in range(0, point_count):
				index = point_count - (i+1)
				latitude = elevation_list[index][0]
				longitude = elevation_list[index][1]
				hight = elevation_list[index][2]
				x,y = self.latlon2xy([latitude, longitude])
				road_elevation.append([x-self.origin_x,y-self.origin_y,hight])
				
		return road_elevation
	
	def get_road_speed(self, road_key):
		speed = self.road_dict[road_key]["speed"]

		return speed
		
	def set_dataframe(self):
		
		self.set_polyline_list()
		self.set_node_list()
		
		link_data = []
		link_data_speed = []
		print("Creates a DataFrame from a list of polylines and associated information.")
		for polyline in tqdm(self.polyline_list):
			polyline_id = polyline[0]
			start_node_point = polyline[1][0]
			end_node_point = polyline[1][-1]
			start_node = self.find_node_id(start_node_point)
			end_node = self.find_node_id(end_node_point)
			elevation = self.get_road_elevation(polyline_id)
			speed = self.get_road_speed(polyline_id)
			oneway_code = polyline[2]

			polyline[1] = self.sampling(self.polyline_latlon2xy(polyline[1], self.origin_x, self.origin_y), self.polyline_sampling_interval)
			
			link_data.append([polyline_id, start_node, end_node, polyline[1], oneway_code, [polyline] ,start_node,end_node, elevation])
			link_data_speed.append([polyline_id, start_node, end_node, polyline[1], oneway_code, [polyline] ,start_node,end_node, elevation, speed])

		self.plot_polylines(save_path="polylines.png", show=False)

		# restore dataframe creation and speed update
		self.update_road_speeds(link_data_speed)
		self.df = pd.DataFrame(link_data)
		self.df.columns=["polyline_id","start_node","end_node","xy","oneway_code","latlon", "start_junction", "end_junction","elevation"]

	def plot_polylines(self, save_path=None, show=True, figsize=(8,8), dpi=120, linewidth=0.8, annotate=True, fontsize=8):
		"""Plot XY points of each polyline using matplotlib.

		Args:
			save_path (str|None): Path to save the figure. If None, not saved.
			show (bool): Whether to display the plot window.
			figsize (tuple): Figure size in inches.
			dpi (int): Figure DPI.
			linewidth (float): Line width for polylines.
		"""
		fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
		for polyline in self.polyline_list:
			xy = polyline[1]
			if xy is None or len(xy) < 2:
				continue
			xs = [p[0] for p in xy]
			ys = [p[1] for p in xy]
			ax.plot(xs, ys, '-', linewidth=linewidth)
			if annotate:
				# annotate with polyline id at geometric midpoint (by arc length)
				polyline_id = polyline[0]
				# compute cumulative distances
				cum = [0.0]
				for i in range(1, len(xs)):
					dx = float(xs[i]) - float(xs[i-1])
					dy = float(ys[i]) - float(ys[i-1])
					cum.append(cum[-1] + math.hypot(dx, dy))
				total = cum[-1]
				if total <= 0:
					mx, my = xs[len(xs)//2], ys[len(ys)//2]
				else:
					target = total * 0.5
					j = 1
					while j < len(cum) and cum[j] < target:
						j += 1
					if j >= len(cum):
						mx, my = xs[-1], ys[-1]
					else:
						seg_len = max(1e-9, cum[j] - cum[j-1])
						alpha = (target - cum[j-1]) / seg_len
						mx = (1 - alpha) * float(xs[j-1]) + alpha * float(xs[j])
						my = (1 - alpha) * float(ys[j-1]) + alpha * float(ys[j])
				ax.text(mx, my, str(polyline_id), fontsize=fontsize, ha='center', va='center',
						bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.6))
		ax.set_aspect('equal', adjustable='box')
		ax.set_xlabel('X')
		ax.set_ylabel('Y')
		ax.grid(True, linestyle=':', linewidth=0.5)
		if save_path is not None:
			fig.savefig(save_path, bbox_inches='tight')
		if show:
			plt.show()
		else:
			plt.close(fig)

	def sampling( self, point_list, sampling_length):
		sampling_list = []
		previous_point = point_list[0]
		total_distance = 0
		sampling_list.append([point_list[0][0],point_list[0][1]])
		for i in range(1,len(point_list)-1):
			diff_x = float(point_list[i][0]) - float(previous_point[0])
			diff_y = float(point_list[i][1]) - float(previous_point[1])
			point_length = math.sqrt(diff_x**2 + diff_y**2)
			total_distance = total_distance + point_length
			previous_point = point_list[i]
			if total_distance+point_length*0.5 > sampling_length:
				sampling_list.append([point_list[i][0],point_list[i][1]])
				total_distance = 0
		if len(point_list) > 1:
			sampling_list.append([point_list[-1][0],point_list[-1][1]])   
		return sampling_list

	def get_intersection_point(self, in_polyline, out_polyline):
		if in_polyline[1] == 0:
			node_point = in_polyline[2][0]
			previous_point = in_polyline[2][1]
		else:
			node_point = in_polyline[2][-1]
			previous_point = in_polyline[2][-2]
		if out_polyline[1] == 0:
			next_point = out_polyline[2][1]
		else:
			next_point = out_polyline[2][-2]
			
		diff_x = node_point[0] - previous_point[0]
		diff_y = node_point[1] - previous_point[1]
		in_direction = np.rad2deg(math.atan2(diff_y, diff_x))
		
		diff_x = next_point[0] - node_point[0]
		diff_y = next_point[1] - node_point[1]
		out_direction = np.rad2deg(math.atan2(diff_y, diff_x))
		
		direction_variation = out_direction - in_direction
		if direction_variation > 180.0:
			direction_variation -= 360
		if direction_variation < -180:
			direction_variation += 360
		
		incoming_road_width = self.get_left_side_road_width(in_polyline[0])
		outgoing_road_width = self.get_left_side_road_width(out_polyline[0])
		incoming_left_lane, incoming_right_lane = self.get_lane_count(in_polyline[0], in_polyline[3])
		outgoing_left_lane, outgoing_right_lane = self.get_lane_count(out_polyline[0], out_polyline[3])
		if direction_variation > 0.0:
			incoming_road_width /= incoming_left_lane
			incoming_road_width *= 0.5
			if outgoing_right_lane == 0:
				outgoing_road_width *= 0.5
		else:
			incoming_road_width /= incoming_left_lane
			incoming_road_width *= 0.5
			if outgoing_right_lane == 0:
				outgoing_road_width *= 0.5
		return link_util.calc_turning_point(incoming_road_width, outgoing_road_width, direction_variation);
		
	def check_through_node(self, from_polyline, to_polyline):
		result = True
		if from_polyline[1] == 1:
			from_direction = polyline_util.last_direction(from_polyline[2], 0)
			if from_polyline[3] == 2:
				result = False
		else:
			from_direction = polyline_util.last_direction(from_polyline[2], 1)
			if from_polyline[3] == 1:
				result = False
		        
		if to_polyline[1] == 1:
			to_direction = polyline_util.first_direction(to_polyline[2], 1)
			if to_polyline[3] == 1:
				result = False
		else:
			to_direction = polyline_util.first_direction(to_polyline[2], 0)
			if to_polyline[3] == 2:
				result = False
		result = True
		if result:
			direction_variation = link_util.normalize_direction(to_direction - from_direction)
			if abs(direction_variation) > 160:
				result = False
		result = True
		return result

	def get_from_polyline_direction(self, from_polyline):
		if from_polyline[1] == 1:
			return polyline_util.last_direction(from_polyline[2], 0)
		else:
			return polyline_util.last_direction(from_polyline[2], 1)
			
	def get_to_polyline_direction(self, to_polyline):
		if to_polyline[1] == 1:
			return	polyline_util.first_direction(to_polyline[2], 1)
		else:
			return  polyline_util.first_direction(to_polyline[2], 0)
		
	def get_junction_point_distance(self, node_id):
		polyline_list = self.get_same_node_polyline(node_id)
		max_distance = 0
		mean_distance = 0.0
		count = 0
		for i in range(0, len(polyline_list)):
			for j in range(0,len(polyline_list)):
				if i != j:
					in_polyline = polyline_list[i]
					out_polyline = polyline_list[j]
					if self.check_through_node(in_polyline, out_polyline):
						distance = self.get_intersection_point(in_polyline, out_polyline)
						in_length = self.road_dict[in_polyline[0]]["length"]
						out_length = self.road_dict[out_polyline[0]]["length"]
						if distance > in_length:
							distance = in_length
						if distance > out_length:
							distance = out_length
							
						mean_distance += distance
						count += 1
						if max_distance < distance :
							max_distance = distance
		if count > 1:
			mean_distance /= count
		return max_distance

	def get_junction_point_distance_dict(self, node_id):
		polyline_list = self.get_same_node_polyline(node_id)
		result_dict = dict()
		for i in range(0, len(polyline_list)):
			max_distance = 0
			in_polyline = polyline_list[i]
			for j in range(0,len(polyline_list)):
				if i != j:
					out_polyline = polyline_list[j]
					if self.check_through_node(in_polyline, out_polyline):
						distance = self.get_intersection_point(in_polyline, out_polyline)
						in_length = self.road_dict[in_polyline[0]]["length"]
						out_length = self.road_dict[out_polyline[0]]["length"]
						if distance > in_length:
							distance = in_length
						in_direction = self.get_from_polyline_direction(in_polyline)
						out_direction = self.get_to_polyline_direction(out_polyline)
						direction_variation = link_util.normalize_direction(out_direction - in_direction)
						if abs(direction_variation) > 90:
							#distance += abs(5*math.cos(np.deg2rad(direction_variation)))
							distance /= abs(math.sin(np.deg2rad(direction_variation)))
						if max_distance < distance:
							max_distance = distance
			result_dict[in_polyline[0]] = max_distance
		return result_dict

	def set_junction_node( self, node_id ):

		intersection_distance = self.get_junction_point_distance(node_id)
		distance_dict = self.get_junction_point_distance_dict(node_id)
		initial_target_distance = self.junction_margin + intersection_distance
		start_target_data = self.df[self.df["start_node"] == node_id]
		end_target_data = self.df[self.df["end_node"] == node_id]
		
		if (len(start_target_data) + len(end_target_data)) > 2:
			self.junction_node.append(node_id)
			
			for index, row in start_target_data.iterrows():
				polyline_id = row["polyline_id"]
				length = self.road_dict[polyline_id]["length"]
				if polyline_id in distance_dict.keys():
					target_distance = distance_dict[polyline_id] + 5.0
				else:
					target_distance = initial_target_distance
				if target_distance > length*0.5 - 1.0:
					target_distance = length*0.5 - 1.0
				if target_distance < 0.0:
					target_distance = length*0.5
				
				xy_list = row["xy"]
				center_node = xy_list[0]
				target_node = xy_list[1]
				target_index = 1
				node_distance = link_util.get_distance(target_node, center_node)
				
				if node_distance > target_distance:
					if target_distance > 0.0:
						n_node = link_util.get_node_point(center_node, target_node, target_distance)
						new_xy_list = link_util.add_node(xy_list, n_node, target_index)
						self.df.at[index,"xy"] = new_xy_list
				elif len(xy_list) > 2:
					previous_node = xy_list[2]
					previous_node_distance = link_util.get_distance(previous_node, target_node)
					if node_distance+previous_node_distance > target_distance:
						n_node = link_util.reposition(center_node, target_node, previous_node, target_distance)
						new_xy_list = link_util.replace_node(xy_list, n_node, target_index)
						self.df.at[index,"xy"] = new_xy_list
					else:
						new_xy_list = link_util.remove_node(xy_list, target_index)
						self.df.at[index,"xy"] = new_xy_list
						
			for index, row in end_target_data.iterrows():
				polyline_id = row["polyline_id"]
				length = self.road_dict[polyline_id]["length"]
				if polyline_id in distance_dict.keys():
					target_distance = distance_dict[polyline_id] + 5.0
				else:
					target_distance = initial_target_distance
				if target_distance > length*0.5 - 1.0:
					target_distance = length*0.5 - 1.0
				if target_distance < 0.0:
					target_distance = length*0.5
					
				xy_list = row["xy"]
				center_index = len(xy_list)-1
				target_index = center_index - 1
				center_node = xy_list[center_index]
				target_node = xy_list[target_index]
				node_distance = link_util.get_distance(target_node, center_node)
				if node_distance > target_distance:
					if target_distance > 0.0:
						n_node = link_util.get_node_point(center_node, target_node, target_distance)
						new_xy_list =link_util.add_node(xy_list, n_node, target_index+1)
						self.df.at[index,"xy"] = new_xy_list
				elif len(xy_list) > 2:
					previous_node = xy_list[-3]
					previous_node_distance = link_util.get_distance(previous_node, target_node)
					if node_distance+previous_node_distance > target_distance:
						n_node = link_util.reposition(center_node, target_node, previous_node, target_distance)
						new_xy_list = link_util.replace_node(xy_list, n_node, target_index)
						self.df.at[index,"xy"] = new_xy_list
					else:
						new_xy_list = link_util.remove_node(xy_list, target_index)
						self.df.at[index,"xy"] = new_xy_list
		else:
			if len(start_target_data) + len(end_target_data) == 1:
				self.isolated_node.append(node_id)
			else:
				self.connect_node.append(node_id)
			
	def is_junction(self, node_id):
		result = False
		for i in range(0,len(self.junction_node)):
			if node_id == self.junction_node[i]:
				result = True
				break
		return result
		
	def get_road_segment(self, start_node, end_node, width):
		length = link_util.get_distance(start_node, end_node)
		direction = link_util.get_direction(start_node, end_node)
		return [start_node, end_node, length, direction, width]
		
	def get_same_node_all_polyline(self, node_id):
		polyline_list = []
		
		target_data = self.df[self.df["start_node"]==node_id]
		for index, row in target_data.iterrows():
			oneway_code = row["oneway_code"]
			polyline_id = row["polyline_id"]
			if not polyline_id in self.merged_polyline:
				polyline_list.append([polyline_id, 0, row["xy"], oneway_code])
		
		target_data = self.df[self.df["end_node"]==node_id]
		for index, row in target_data.iterrows():
			oneway_code = row["oneway_code"]
			polyline_id = row["polyline_id"]
			if not polyline_id in self.merged_polyline:
				polyline_list.append([polyline_id, 1, row["xy"], oneway_code])
		
		target_data = self.merged_df[self.merged_df["start_node"]==node_id]
		for index, row in target_data.iterrows():
			oneway_code = row["oneway_code"]
			polyline_list.append([row["polyline_id"], 0, row["xy"], oneway_code])
		
		target_data = self.merged_df[self.merged_df["end_node"]==node_id]
		for index, row in target_data.iterrows():
			oneway_code = row["oneway_code"]
			polyline_list.append([row["polyline_id"], 1, row["xy"], oneway_code])
		
		return polyline_list

	def get_same_node_polyline(self, node_id):
		find_flag = False
		polyline_list = []
		target_data = self.df[self.df["start_node"]==node_id]
		for index, row in target_data.iterrows():
			oneway_code = row["oneway_code"]
			polyline_list.append([row["polyline_id"], 0, row["xy"], oneway_code])
		target_data = self.df[self.df["end_node"]==node_id]
		for index, row in target_data.iterrows():
			oneway_code = row["oneway_code"]
			polyline_list.append([row["polyline_id"], 1, row["xy"], oneway_code])
		return polyline_list

	def get_same_node_merged_polyline(self, node_id):
		find_flag = False
		polyline_list = []
		target_data = self.merged_df[self.merged_df["start_node"]==node_id]
		for index, row in target_data.iterrows():
			oneway_code = row["oneway_code"]
			polyline_list.append([row["polyline_id"], 0, row["xy"], oneway_code])
		target_data = self.merged_df[self.merged_df["end_node"]==node_id]
		for index, row in target_data.iterrows():
			oneway_code = row["oneway_code"]
			polyline_list.append([row["polyline_id"], 1, row["xy"], oneway_code])
		return polyline_list
		
	def get_next_segment( self, polyline_id ):
		target_polyline = self.df[self.df["polyline_id"]==polyline_id]
		target_node = target_polyline["end_node"].to_list()[0]
		polyline_list = self.get_same_node_polyline(target_node)
		next_segment = []
		for polyline in polyline_list:
			if polyline[0] != polyline_id:
				road_key = polyline[0]
				width = self.road_dict[road_key]["width"]
				oneway_code = polyline[3]
				if polyline[1] == 0:
					if oneway_code == 0 or oneway_code == 1:
						segment = self.get_road_segment(polyline[2][0], polyline[2][1], width)
						next_segment.append(segment)
				else:
					if oneway_code == 0 or oneway_code == 2:
						segment = self.get_road_segment(polyline[2][-1], polyline[2][-2], width)
						next_segment.append(segment)
		return next_segment
	
	def get_previous_segment( self, target_road_key ):
		target_polyline = self.df[self.df["polyline_id"]==target_road_key]
		target_node = target_polyline["start_node"].to_list()[0]
		polyline_list = self.get_same_node_polyline(target_node)
		previous_segment = []    
		for polyline in polyline_list:
			if polyline[0] != target_road_key:
				road_key = polyline[0]
				width = self.road_dict[road_key]["width"]
				oneway_code = polyline[3]
				if polyline[1] == 0:
					if oneway_code == 0 or oneway_code == 2:
						segment = self.get_road_segment(polyline[2][1], polyline[2][0], width)
						previous_segment.append(segment)
				else:
					if oneway_code == 0 or oneway_code == 1:
						segment = self.get_road_segment(polyline[2][-2], polyline[2][-1], width)
						previous_segment.append(segment)
		return previous_segment
	
	def get_junction_start_range(self, target_segment, next_segment_list):
		result_range = 0
		target_direction = target_segment[3]
		target_road_width = target_segment[4]
		max_range = 0
		mean_range = 0
		range_count = 0
		if len(next_segment_list) > 0:
			for next_segment in next_segment_list:
				next_direction = next_segment[3]
				next_road_width = next_segment[4]
				direction_variation = next_direction - target_direction
				if direction_variation > 180:
					direction_variation -= 360
				if direction_variation < -180:
					direction_variation += 360
				intersection_range = link_util.calc_turning_point(target_road_width, next_road_width, direction_variation)
				if abs(direction_variation) > 20:
					mean_range += intersection_range
					range_count += 1
				if intersection_range > max_range:
					max_range = intersection_range
		else:
			result_range = 0
		if range_count > 1:
			result_range = mean_range/range_count
		else:
			result_range = mean_range
		if result_range < 3.0:
			result_range = 3.0
		return result_range
		
	def get_junction_end_range(self, target_segment, previous_segment_list):
		result_range = 0
		target_direction = target_segment[3]
		target_road_width = target_segment[4]
		mean_range = 0
		range_count = 0
		max_range = 0
		if len(previous_segment_list) > 0:
			for previous_segment in previous_segment_list:
				previous_direction = previous_segment[3]
				previous_road_width = previous_segment[4]
				direction_variation = target_direction - previous_direction
				if direction_variation > 180:
					direction_variation -= 360
				if direction_variation < -180:
					direction_variation += 360
				intersection_range = link_util.calc_turning_point(previous_road_width, target_road_width, direction_variation)
				if abs(direction_variation) > 20:
					mean_range += intersection_range
					range_count += 1
				if intersection_range > max_range:
					max_range = intersection_range
		else:
			result_range = 0
		if range_count > 1:
			result_range = mean_range/range_count
		else:
			result_range = mean_range
		if result_range < 3.0:
			result_range = 3.0
			
		return result_range
		
	def polyline2node(self, polyline):
		node_list = []
		point_count = int(len(polyline)/2)
		for i in range(0,point_count):
			latitude = polyline[i*2]
			longitude = polyline[i*2+1]
			node_list.append([latitude,longitude])
		return node_list

	def get_target(self, polyline_id):
		if polyline_id in self.merged_polyline:
			target_link = self.merged_df[self.merged_df["polyline_id"] == polyline_id]
		else:
			target_link = self.df[self.df["polyline_id"]==polyline_id]
		return target_link
		
	def get_node_id(self, polyline_id):
		target_link = self.get_target(polyline_id)
		start_node = target_link["start_node"].to_list()[0]
		end_node = target_link["end_node"].to_list()[0]
		return start_node, end_node
	
	def get_junction_id(self, polyline_id):
		target_link = self.get_target(polyline_id)
		start_junction = target_link["start_junction"].to_list()[0]
		end_junction = target_link["end_junction"].to_list()[0]
		return start_junction, end_junction
		
	def check_connect_polyline(self, polyline_id):
		target_polyline = self.df[self.df["polyline_id"] == polyline_id]
		start_node = int(target_polyline["start_node"].to_list()[0])
		end_node = int(target_polyline["end_node"].to_list()[0])

		same_start_node_polyline_count = 0
		same_end_node_polyline_count = 0

		same_start_node_polyline = self.df[self.df["start_node"] == start_node]
		same_end_node_polyline = self.df[self.df["end_node"] == end_node]

		same_start_node_polyline_count = len(same_start_node_polyline) - 1
		same_end_node_polyline = len(same_end_node_polyline) - 1

		same_start_node_polyline = self.df[self.df["end_node"] == start_node]
		same_end_node_polyline = self.df[self.df["start_node"] == end_node]

		result = False
		same_start_node_polyline_count = same_start_node_polyline_count + len(same_start_node_polyline)
		same_end_node_polyline_count = same_end_node_polyline_count + len(same_end_node_polyline)

		if same_start_node_polyline_count == 1 and same_end_node_polyline_count == 1:
			result = True
		return result
		
	def get_intersection_link(self):
		if self.enable_highway:
			target_road_df = self.road_df
		else:
			target_road_df = self.road_df[self.road_df["is_highway"] == False]
		short_length_road = target_road_df[target_road_df["length"] < 200]
		candidate_list = []
		for index, row in short_length_road.iterrows():
			if( len(row["polyline"]) < 9):
				candidate_list.append([row["road_key"], self.polyline2node(row["polyline"]), row["length"],row["width"]])
		self.intersection_polyline_id = set()
		intersection_link = []
		print("Identifies potential intersection links.")
		for candidate in tqdm(candidate_list):       
			next_segment = self.get_next_segment(candidate[0])
			previous_segment = self.get_previous_segment(candidate[0])
			target_link = self.get_target(candidate[0])
			target_xy_list = target_link["xy"].to_list()[0]
			target_width = self.road_dict[candidate[0]]["width"]
			target_segment = self.get_road_segment(target_xy_list[-2], target_xy_list[-1], target_width)        
			start_range = self.get_junction_start_range(target_segment, next_segment)
			target_segment = self.get_road_segment(target_xy_list[0], target_xy_list[1], target_width)        
			end_range = self.get_junction_end_range(target_segment, previous_segment)
			target_length = candidate[2]
			margin = 0
			is_connect_polyline = self.check_connect_polyline(candidate[0])
			if len(next_segment) > 1 or len(previous_segment) > 1:
				margin = 5.0
			if target_length < (start_range + end_range + margin) and is_connect_polyline == False:# and candidate[0] != 623:
				self.intersection_polyline_id.add(candidate[0])
				intersection_link.append(candidate)
		return intersection_link
		
	def get_connect_link_index(self, target_index, link_list, link_index_list):
		target_start_node = link_list[target_index][1][0]
		target_end_node = link_list[target_index][1][-1]
		index_list = []
		for index in link_index_list:
			start_node = link_list[index][1][0]
			end_node = link_list[index][1][-1]
			if start_node == target_start_node or start_node == target_end_node:
				index_list.append(index)
			elif end_node == target_start_node or end_node == target_end_node:
				index_list.append(index)
				
		return index_list

	def set_intersection_list(self, intersection_link):
		link_index_list = []
		node_index_list = []
		for i in range(0,len(intersection_link)):
			link_index_list.append(i)
			
		if len(link_index_list) > 0:
			group_index_list = []
			for i in range(0,len(intersection_link)*1000):
				target_index = link_index_list.pop(0)
				node_index_list = []
				node_index_list.append(target_index)
				group_index = []
				group_index.append(target_index)
				for j in range(0,len(intersection_link)*1000):
					if len(node_index_list) == 0:
						break
					target_index = node_index_list.pop(0)
					connect_link_list = self.get_connect_link_index(target_index, intersection_link, link_index_list)
					if len(connect_link_list) > 0:
						group_index.extend(connect_link_list)
						node_index_list.extend(connect_link_list)
						for index in connect_link_list:
							link_index_list.remove(index)
				group_index_list.append(group_index)
				if len(link_index_list) == 0:
					break;
		else:
			group_index_list = []
			
		self.intersection_list = []
		print("Group intersecting lines and identify the nodes and polylines that belong to each intersecting group.")
		for group_index in tqdm(group_index_list):
			node_set = set()
			polyline_set = set()
			for index in group_index:
				roadkey = intersection_link[index][0]
				start_node, end_node = self.get_node_id(roadkey)
				node_set.add(start_node)
				node_set.add(end_node)
				polyline_set.add(roadkey)
			self.intersection_list.append([polyline_set,node_set])
			
	def add_remain_intersection_polyline(self):
		for index, row in self.df.iterrows():
			if not row["polyline_id"] in self.intersection_polyline_id:
				for i in range(0, len(self.intersection_list)):
					if row["start_node"] in self.intersection_list[i][1] and row["end_node"] in self.intersection_list[i][1]:
						self.intersection_list[i][0].add(row["polyline_id"])
						self.intersection_polyline_id.add(row["polyline_id"])
						
	def find_intersection_node(self,node_id):
		exist_node = False
		intersection_index = 0
		for index in range(0, len(self.intersection_list)):
			if node_id in self.intersection_list[index][1]:
				exist_node = True
				intersection_index = index
				break
		return exist_node, intersection_index
		
	def set_junction_id(self):
		for index, row in self.df.iterrows():
			if row["polyline_id"] in self.intersection_polyline_id:
				self.df.at[index,"start_junction"] = -1
				self.df.at[index,"end_junction"] = -1
				exist_node, intersection_index = self.find_intersection_node(row["start_node"])
				if exist_node :
					self.df.at[index,"start_junction"] = (self.intersection_offset+intersection_index)
					
				exist_node, intersection_index = self.find_intersection_node(row["end_node"])
				if exist_node :
					self.df.at[index,"end_junction"] = (self.intersection_offset+intersection_index)
			else:
				exist_node, intersection_index = self.find_intersection_node(row["start_node"])
				if exist_node :
					self.df.at[index,"start_junction"] = (self.intersection_offset+intersection_index)
					
				exist_node, intersection_index = self.find_intersection_node(row["end_node"])
				if exist_node :
					self.df.at[index,"end_junction"] = (self.intersection_offset+intersection_index)

	def set_connect_node_polyline(self):
		for node_id in self.connect_node:
			polyline_list = self.get_same_node_polyline(node_id)
			self.connect_node_polyline_dict[node_id] = []
			for polyline in polyline_list:
				if not polyline[0] in self.intersection_polyline_id:
					self.connect_node_polyline_dict[node_id].append(polyline)

	def get_inverse_point_list(self, point_list ):
		inverse_point = []
		for point in point_list:
			inverse_point.insert(0, point)
		return inverse_point
		
	def get_inverse_elevation(self, elevation):
		inverse_elevation = []
		for element in elevation:
			inverse_elevation.insert(0,element)
		return inverse_elevation
		
	def get_inverse_link( self, link_data ):
		polyline_id = link_data["polyline_id"].values[0]
		start_node = link_data["end_node"].values[0]
		end_node = link_data["start_node"].values[0]
		polyline = self.get_inverse_point_list(link_data["xy"].values[0])
		oneway_code = link_data["oneway_code"].values[0]
		if oneway_code == 1:
			oneway_code = 2
		elif oneway_code == 2:
			oneway_code = 1
		latlon = link_data["latlon"].values[0]
		start_junction = link_data["end_junction"].values[0]
		end_junction = link_data["start_junction"].values[0]
		elevation = self.get_inverse_elevation(link_data["elevation"].values[0])
		inverse_link = pd.DataFrame([[polyline_id, start_node, end_node, polyline, oneway_code, latlon, start_junction, end_junction, elevation]])
		inverse_link.columns = link_data.columns
		return inverse_link
				
	def get_merged_point_list(self, first_list, second_list):
		merged_list = copy.deepcopy(first_list)
		merged_list.pop()
		merged_list.extend(copy.deepcopy(second_list))
		return merged_list
		
	def merge_link( self, first_link, next_link):
		polyline_id = first_link["polyline_id"].values[0]
		start_node = first_link["start_node"].values[0]
		end_node = next_link["end_node"].values[0]
		xy_list = self.get_merged_point_list(first_link["xy"].values[0], next_link["xy"].values[0])
		first_oneway_code = first_link["oneway_code"].values[0]
		next_oneway_code = next_link["oneway_code"].values[0]
		if first_oneway_code == next_oneway_code:
			oneway_code = first_oneway_code
		else:
			oneway_code = 0
			
		latlon = copy.deepcopy(first_link["latlon"].values[0])
		latlon.extend(copy.deepcopy(next_link["latlon"].values[0]))
		start_junction = first_link["start_junction"].values[0]
		end_junction = next_link["end_junction"].values[0]
		elevation = copy.deepcopy(first_link["elevation"].values[0])
		elevation.extend(copy.deepcopy(next_link["elevation"].values[0]))
		merged_link_data = pd.DataFrame([[polyline_id,start_node,end_node,xy_list,oneway_code,latlon,start_junction,end_junction,elevation]])
		merged_link_data.columns = first_link.columns
		return merged_link_data
		
	def get_merged_link(self, first_df, second_df):
		if first_df[0] == 1 and second_df[0] == 0:
			merged_link = self.merge_link(first_df[1], second_df[1])
		elif first_df[0] == 1 and second_df[0] == 1:
			inverse_second_df = self.get_inverse_link(second_df[1])
			merged_link = self.merge_link(first_df[1], inverse_second_df)
		elif first_df[0] == 0 and second_df[0] == 1:
			merged_link = self.merge_link(second_df[1], first_df[1])
		elif first_df[0] == 0 and second_df[0] == 0:
			inverse_second_df = self.get_inverse_link(second_df[1])
			merged_link = self.merge_link(inverse_second_df, first_df[1])
		return merged_link
		
	def find_same_node_merged_link(self,node_id):
		exist_df = False
		if len(self.merged_df[self.merged_df["start_node"] == node_id]) == 1:
			exist_df = True
			merged_link_data = [0, self.merged_df[self.merged_df["start_node"] == node_id]]
		elif len(self.merged_df[self.merged_df["end_node"] == node_id]) == 1:
			exist_df = True
			merged_link_data = [1, self.merged_df[self.merged_df["end_node"] == node_id]]
		else:
			merged_link_data = []
		return exist_df, merged_link_data
	
	def find_same_node_merged_link_2(self,node_id):
		exist_df = False
		if len(self.merged_df[self.merged_df["start_node"] == node_id]) == 1:
			exist_df = True
			merged_link_data_1 = [0, self.merged_df[self.merged_df["start_node"] == node_id]]
		else:
			merged_link_data_1 = []
			exist_df = False


		if len(self.merged_df[self.merged_df["end_node"] == node_id]) == 1:
			exist_df = True
			merged_link_data_2 = [1, self.merged_df[self.merged_df["end_node"] == node_id]]
		else:
			merged_link_data_2 = []
			exist_df = False

		return exist_df, merged_link_data_1, merged_link_data_2
		
	def drop_merged_dataframe(self, target_node):
		delete_list = self.merged_df[self.merged_df["start_node"] == target_node].index.to_list()
		if len(delete_list) > 0:
			self.merged_df = self.merged_df.drop(index=delete_list)
		delete_list = self.merged_df[self.merged_df["end_node"] == target_node].index.to_list()
		if len(delete_list) > 0:
			self.merged_df = self.merged_df.drop(index=delete_list)
			
	def check_mergeable(self, first_polyline, second_polyline):
		if self.road_dict[first_polyline[0]]["is_highway"] == True or self.road_dict[second_polyline[0]]["is_highway"] == True:
			if self.road_dict[first_polyline[0]]["oneway_code"] == self.road_dict[second_polyline[0]]["oneway_code"]:
				if first_polyline[1] != second_polyline[1]:
					result = True
				else:
					result = False
			else:
				result = False
		elif self.road_dict[first_polyline[0]]["is_highway"] == False and self.road_dict[second_polyline[0]]["is_highway"] == False:
			if self.road_dict[first_polyline[0]]["oneway_code"] == self.road_dict[second_polyline[0]]["oneway_code"]:
				result = True
			else:
				result = False
		else:
			result = False
		return result
			
	def set_merged_dataframe(self):
		for node_id in self.connect_node:
			if len(self.connect_node_polyline_dict[node_id]) == 2:
				first_polyline = self.connect_node_polyline_dict[node_id][0]
				second_polyline = self.connect_node_polyline_dict[node_id][1]
				if self.check_mergeable(first_polyline, second_polyline) == False:
					pass
				elif first_polyline[0] in self.merged_polyline and second_polyline[0] in self.merged_polyline:
					exist_df, first_df, second_df = self.find_same_node_merged_link_2(node_id)
					if exist_df:
						merged_link = self.get_merged_link(first_df, second_df)
						self.drop_merged_dataframe(node_id)
						self.merged_df = pd.concat([self.merged_df, merged_link],ignore_index=True)
						self.merged_polyline.add(first_polyline[0])      
						self.merged_polyline.add(second_polyline[0])
				elif first_polyline[0] in self.merged_polyline:
					exist_first_df, first_df = self.find_same_node_merged_link(node_id)
					if exist_first_df:
						if not second_polyline[0] in self.merged_polyline:
							target_link_df = self.df[self.df["polyline_id"] == second_polyline[0]]
							second_df = [second_polyline[1],target_link_df]
							merged_link = self.get_merged_link(first_df, second_df)
							self.drop_merged_dataframe(node_id)
							self.merged_df = pd.concat([self.merged_df, merged_link],ignore_index=True)
							self.merged_polyline.add(first_polyline[0])      
							self.merged_polyline.add(second_polyline[0])
				elif second_polyline[0] in self.merged_polyline:
					exist_second_df, second_df = self.find_same_node_merged_link(node_id)
					if exist_second_df:
						if not first_polyline[0] in self.merged_polyline:
							target_link_df = self.df[self.df["polyline_id"] == first_polyline[0]]
							first_df = [first_polyline[1], target_link_df]
							merged_link = self.get_merged_link(first_df, second_df)
							self.drop_merged_dataframe(node_id)
							self.merged_df = pd.concat([self.merged_df, merged_link],ignore_index=True)
							self.merged_polyline.add(first_polyline[0])      
							self.merged_polyline.add(second_polyline[0])
				else:
					target_link_df = self.df[self.df["polyline_id"] == first_polyline[0]]
					first_df = [first_polyline[1], target_link_df]
					target_link_df = self.df[self.df["polyline_id"] == second_polyline[0]]
					second_df = [second_polyline[1],target_link_df]
					merged_link = self.get_merged_link(first_df, second_df)
					self.merged_df = pd.concat([self.merged_df, merged_link],ignore_index=True)
					self.merged_polyline.add(first_polyline[0])      
					self.merged_polyline.add(second_polyline[0])
					
	def get_general_road_polyline_id(self):
		polyline_id_list = []
		for index, row in self.df.iterrows():
			if self.enable_highway or self.road_dict[row["polyline_id"]]["is_highway"] == False:
				if not row["polyline_id"] in self.intersection_polyline_id: 
					polyline_id_list.append(row["polyline_id"])
		return polyline_id_list
					
	def get_general_merged_road_polyline_id(self):
		polyline_id_list = []
		for index, row in self.merged_df.iterrows():
			if self.enable_highway or self.road_dict[row["polyline_id"]]["is_highway"] == False:
				if not row["polyline_id"] in self.intersection_polyline_id: 
					polyline_id_list.append(row["polyline_id"])
		return polyline_id_list

	def get_road_polyline( self, polyline_id ):
		target_link = self.get_target(polyline_id)
		xy_list = target_link["xy"].to_list()[0]
		start_node = target_link["start_node"].to_list()[0]
		end_node = target_link["end_node"].to_list()[0]
		if self.is_junction(start_node):
			start_index = 1
			if polyline_id in self.merged_polyline:
				center_node = xy_list[0]
				target_node = xy_list[1]
				target_distance = self.junction_margin
				target_index = 1
				node_distance = link_util.get_distance(target_node, center_node)
				if node_distance < self.junction_margin:
					previous_node = xy_list[2]
					previous_node_distance = link_util.get_distance(previous_node, target_node)
					if node_distance+previous_node_distance > target_distance:
						n_node = link_util.reposition(center_node, target_node, previous_node, target_distance)
						xy_list = link_util.replace_node(xy_list, n_node, target_index)
					else:
						xy_list = link_util.remove_node(xy_list, target_index)
		else:
			center_node = xy_list[0]
			target_node = xy_list[1]
			target_index = 1
			target_distance = self.junction_margin
			node_distance = link_util.get_distance(target_node, center_node)
			if node_distance > target_distance:
				n_node = link_util.get_node_point(center_node, target_node, target_distance)
				xy_list = link_util.add_node(xy_list, n_node, target_index)
				start_index = 1
			else:
				start_index = 0
			
		if self.is_junction(end_node):
			end_index = len(xy_list) - 1
			if polyline_id in self.merged_polyline:
				center_index = len(xy_list)-1
				target_index = center_index - 1
				center_node = xy_list[center_index]
				target_node = xy_list[target_index]
				target_distance = self.junction_margin
				node_distance = link_util.get_distance(target_node, center_node)
				if node_distance < target_distance:
					previous_node = xy_list[-3]
					previous_node_distance = link_util.get_distance(previous_node, target_node)
					if node_distance+previous_node_distance > target_distance:
						n_node = link_util.reposition(center_node, target_node, previous_node, target_distance)
						xy_list = link_util.replace_node(xy_list, n_node, target_index)
					else:
						xy_list = link_util.remove_node(xy_list, target_index)
						end_index = len(xy_list) - 1
		else:
			center_index = len(xy_list)-1
			target_index = center_index - 1
			center_node = xy_list[center_index]
			target_node = xy_list[target_index]
			target_distance = self.junction_margin
			node_distance = link_util.get_distance(target_node, center_node)
			if node_distance > target_distance:
				n_node = link_util.get_node_point(center_node, target_node, target_distance)
				xy_list =link_util.add_node(xy_list, n_node, target_index+1)
				end_index = len(xy_list)-1
			else:
				end_index = len(xy_list)

		if end_index - start_index == 1:
			end_index = end_index + 1
			start_index = start_index - 1

		xy_point = []
		for i in range(start_index, end_index):
			xy_point.append(xy_list[i])
			
		start_junction_part = []
		for i in range(0, start_index+1):
			start_junction_part.append(xy_list[i])
			
		end_junction_part = []
		for i in range(end_index-1, len(xy_list)):
			end_junction_part.append(xy_list[i])
			
		return [start_node,end_node,xy_point], [start_junction_part, end_junction_part]
		
	def get_junction(self, junction_id):
		find_flag = False
		incoming_link = []
		
		target_data = self.df[self.df["start_junction"]==junction_id]
		for index, row in target_data.iterrows():
			if not row["polyline_id"] in self.intersection_polyline_id:
				if not row["polyline_id"] in self.merged_polyline:
					incoming_link.append([row["polyline_id"], 0, row["xy"]])
					
		target_data = self.df[self.df["end_junction"]==junction_id]
		for index, row in target_data.iterrows():
			if not row["polyline_id"] in self.intersection_polyline_id:
				if not row["polyline_id"] in self.merged_polyline:
					incoming_link.append([row["polyline_id"], 1, row["xy"]])
					
		target_data = self.merged_df[self.merged_df["start_junction"]==junction_id]
		for index, row in target_data.iterrows():
			if not row["polyline_id"] in self.intersection_polyline_id:
				incoming_link.append([row["polyline_id"], 0, row["xy"]])
				
		target_data = self.merged_df[self.merged_df["end_junction"]==junction_id]
		for index, row in target_data.iterrows():
			if not row["polyline_id"] in self.intersection_polyline_id:
				incoming_link.append([row["polyline_id"], 1, row["xy"]])
			
		if len(incoming_link) > 2:
			find_flag = True
			
		return find_flag, incoming_link
		
	def get_junction_node_id(self, polyline_id, junction_id):
		start_junction, end_junction = self.get_junction_id(polyline_id)
		start_node, end_node = self.get_node_id(polyline_id)
		if start_junction == junction_id:
			target_node = start_node
		else:
			target_node = end_node
			
		return target_node
		
	def check_enter( self, polyline_id, junction_id):
		target_link = self.get_target(polyline_id)
		start_junction = target_link["start_junction"].to_list()[0]
		end_junction = target_link["end_junction"].to_list()[0]
		oneway_code = target_link["oneway_code"].to_list()[0]
		result = False
		if oneway_code == 0:
			result = True
		elif oneway_code ==1:
			if end_junction == junction_id:
				result = True
		elif oneway_code == 2:
			if start_junction == junction_id:
				result = True
		return result
		
	def check_leave(self, polyline_id, junction_id):
		target_link = self.get_target(polyline_id)
		start_junction = target_link["start_junction"].to_list()[0]
		end_junction = target_link["end_junction"].to_list()[0]
		oneway_code = target_link["oneway_code"].to_list()[0]
		result = False
		if oneway_code == 0:
			result = True
		elif oneway_code ==1:
			if start_junction == junction_id:
				result = True
		elif oneway_code == 2:
			if end_junction == junction_id:
				result = True
		return result
		
	def get_elevation(self,polyline_id):
		target_link = self.get_target(polyline_id)
		return target_link["elevation"].values[0]
	
	def get_speed(self,polyline_id):
		road = self.get_target(polyline_id)
		latlon = road["latlon"].to_list()[0]
		speed = []
		s = 0
		if len(latlon) > 1:
			for i in range(len(latlon)):
				speed.append([self.road_dict[latlon[i][0]]["speed"], s])
				s += self.road_dict[latlon[i][0]]["length"]
		elif polyline_id in self.road_dict.keys():
			speed.append([self.road_dict[polyline_id]["speed"], s])
		else:
			speed.append([60, s])
		return speed
	
	def get_speed_junction(self,polyline_id):
		road = self.get_target(polyline_id)
		latlon = road["latlon"].to_list()[0]
		speed = []
		s = 0
		if len(latlon) > 1:
			speed.append([self.road_dict[latlon[-1][0]]["speed"], s])
		elif polyline_id in self.road_dict.keys():
			speed.append([self.road_dict[polyline_id]["speed"], s])
		else:
			speed.append([60, s])
			
		return speed

	def get_lane_count_new(self, polyline_id, oneway_code, flag = False):

		road = self.get_target(polyline_id)
		latlon = road["latlon"].to_list()[0]

		if self.use_fixed_lane_count:
			if oneway_code == 0:
				left_lane_count = self.two_way_traffic_lane_count
				right_lane_count = self.two_way_traffic_lane_count
			elif oneway_code == 1:
				left_lane_count = self.one_way_traffic_lane_count
				right_lane_count = 0
			elif oneway_code == 2:
				left_lane_count = 0
				right_lane_count = self.one_way_traffic_lane_count
		else:
			if len(latlon) > 1:
				lane_count_start = self.road_dict[latlon[0][0]]["lane"]
				lane_count_end = self.road_dict[latlon[-1][0]]["lane"]
				if lane_count_start == lane_count_end:
					lane_count = lane_count_start
				else:
					lane_count = [lane_count_start, lane_count_end]
					

			elif polyline_id in self.road_dict.keys():
				lane_count = self.road_dict[polyline_id]["lane"]
			else:
				lane_count = 2
			
			if oneway_code == 0:
				if isinstance(lane_count, list) and lane_count:
					lane_count = max(lane_count)

				if lane_count < 2:
					left_lane_count = 1
					right_lane_count = 1
				elif lane_count == 2:
					left_lane_count = 1
					right_lane_count = 1
				else:
					left_lane_count = 2
					right_lane_count = 2
			elif oneway_code == 1:
				if lane_count == 0:
					left_lane_count = 1
					right_lane_count = 0
				else:
					left_lane_count = lane_count
					right_lane_count = 0
			elif oneway_code == 2:
				if lane_count == 0:
					left_lane_count = 0
					right_lane_count = 1
				else:
					left_lane_count = 0
					right_lane_count = lane_count
			else:
				if lane_count < 2:
					left_lane_count = 1
					right_lane_count = 1
				elif lane_count == 2:
					left_lane_count = 1
					right_lane_count = 1
				else:
					left_lane_count = 2
					right_lane_count = 2
					
		return left_lane_count, right_lane_count
		
	def get_lane_count(self, polyline_id, oneway_code, flag = False):

		road = self.get_target(polyline_id)
		latlon = road["latlon"].to_list()[0]

		if self.use_fixed_lane_count:
			if oneway_code == 0:
				left_lane_count = self.two_way_traffic_lane_count
				right_lane_count = self.two_way_traffic_lane_count
			elif oneway_code == 1:
				left_lane_count = self.one_way_traffic_lane_count
				right_lane_count = 0
			elif oneway_code == 2:
				left_lane_count = 0
				right_lane_count = self.one_way_traffic_lane_count
		else:
			if len(latlon) > 1:
				lane_count_start = self.road_dict[latlon[0][0]]["lane"]
				lane_count_end = self.road_dict[latlon[-1][0]]["lane"]
					
				lane_count = self.road_dict[polyline_id]["lane"]
				if flag:
					lane_count = lane_count_end

			elif polyline_id in self.road_dict.keys():
				lane_count = self.road_dict[polyline_id]["lane"]
			else:
				lane_count = 2
			
			if oneway_code == 0:
				if lane_count < 2:
					left_lane_count = 1
					right_lane_count = 1
				elif lane_count == 2:
					left_lane_count = 1
					right_lane_count = 1
				else:
					left_lane_count = 2
					right_lane_count = 2
			elif oneway_code == 1:
				if lane_count == 0:
					left_lane_count = 1
					right_lane_count = 0
				else:
					left_lane_count = lane_count
					right_lane_count = 0
			elif oneway_code == 2:
				if lane_count == 0:
					left_lane_count = 0
					right_lane_count = 1
				else:
					left_lane_count = 0
					right_lane_count = lane_count
			else:
				if lane_count < 2:
					left_lane_count = 1
					right_lane_count = 1
				elif lane_count == 2:
					left_lane_count = 1
					right_lane_count = 1
				else:
					left_lane_count = 2
					right_lane_count = 2
					
		return left_lane_count, right_lane_count
		
	def get_lane_width(self, road_width, lane_count):
		if self.use_fixed_lane_count:
			lane_width = 3.0
		else:
			lane_width = road_width/lane_count
		return lane_width
		
	def get_road_width(self, polyline_id):
		return self.road_dict[polyline_id]["width"]
		
	def get_left_side_road_width(self, polyline_id):
		if self.use_fixed_lane_count:
			target_data = self.get_target(polyline_id)
			oneway_code = int(target_data["oneway_code"])
			if oneway_code == 0:
				return self.two_way_traffic_lane_count*3.0
			else:
				return self.one_way_traffic_lane_count*3.0
		else:
			road_width = self.get_road_width(polyline_id)
			target_data = self.get_target(polyline_id)
			oneway_code = int(target_data["oneway_code"].to_list()[0])
			if oneway_code == 0:
				return road_width*0.5
			else:
				return road_width*1.0
		
	def get_first_link(self, polyline_id, order):
		target_link = self.get_target(polyline_id)
		target_xy = target_link["xy"]
		xy_list = target_xy.to_list()[0]
		if order == 0:
			first_link = link_util.node2link(xy_list[0], xy_list[1])
		else:
			first_link = link_util.node2link(xy_list[-1], xy_list[-2])
		return first_link
		
	def get_last_link(self, polyline_id, order):
		target_link = self.get_target(polyline_id)
		target_xy = target_link["xy"]
		xy_list = target_xy.to_list()[0]
		if order == 0:
			last_link = link_util.node2link(xy_list[-2], xy_list[-1])
		else:
			last_link = link_util.node2link(xy_list[1], xy_list[0])
		return last_link
		
	def get_previous_link(self, polyline_id, order):
		target_link = self.get_target(polyline_id)
		target_xy = target_link["xy"]
		xy_list = target_xy.to_list()[0]
		if order == 1:
			previous_link = link_util.node2link(xy_list[-2], xy_list[-1])
		else:
			previous_link = link_util.node2link(xy_list[1], xy_list[0])
		return previous_link
		
	def get_same_node_intersection_polyline(self, node_id, junction_index):
		find_flag = False
		polyline_list = []
		
		target_data = self.df[self.df["start_node"]==node_id]
		for index, row in target_data.iterrows():
			if row["polyline_id"] in self.intersection_list[junction_index][0]:
				oneway_code = row["oneway_code"]
				polyline_list.append([row["polyline_id"], 0, row["xy"], oneway_code])
		
		target_data = self.df[self.df["end_node"]==node_id]
		for index, row in target_data.iterrows():
			if row["polyline_id"] in self.intersection_list[junction_index][0]:
				oneway_code = row["oneway_code"]
				polyline_list.append([row["polyline_id"], 1, row["xy"], oneway_code])
		
		return polyline_list
		
	def polyline_node2polyline(self, polyline_node ):
		polyline_id = polyline_node[0]
		order = polyline_node[2]
		target_link = self.get_target(polyline_id)
		polyline_point = target_link["xy"].to_list()[0]
		oneway_code = target_link["oneway_code"].to_list()[0]
		return [polyline_id, order, polyline_point, oneway_code]

	def get_first_segment_direction( self, polyline ):
		return polyline_util.first_direction(polyline[2], polyline[1])
	
	def get_last_segment_direction( self, polyline ):
		return polyline_util.last_direction(polyline[2], polyline[1])
	
	def is_passable_shape(self, from_polyline, to_polyline):
		from_width = self.road_dict[from_polyline[0]]["width"]
		to_width = self.road_dict[to_polyline[0]]["width"]
		from_direction = self.get_last_segment_direction(from_polyline)
		to_direction = self.get_first_segment_direction(to_polyline)
		direction_variation = link_util.normalize_direction(to_direction - from_direction)
		result = False
		if abs(direction_variation) > 100:
			turning_point = link_util.calc_turning_point(from_width, to_width, direction_variation)
			if turning_point < (from_width + to_width):
				result = True
		else:
			result = True
			
		return result
	
	def is_passable_path(self, from_polyline, to_polyline ):
		order = to_polyline[1]
		oneway_code = to_polyline[3]
		result = False
		if oneway_code == 0:
			result = True
		elif oneway_code == 1:
			if order == 0:
				result = True
		elif oneway_code == 2:
			if order == 1:
				result = True
				
		if result:
			result = self.is_passable_shape(from_polyline, to_polyline)

		return result
		
	def get_path_target_node(self, polyline_id, order, junction_id):
		start_junction, end_junction = self.get_junction_id(polyline_id)
		start_node, end_node = self.get_node_id(polyline_id)
		exist_target = False
		if order == 0:
			target_node = start_node
			if start_junction == junction_id:
				exist_target = True
			else:
				print("data error")
		else:
			target_node = end_node
			if end_junction == junction_id:
				exist_target = True
			else:
				print("data error")
		
		return exist_target, target_node
		
	def get_start_polyline_node(self, polyline_id, order):
		return [polyline_id, 0, order]

	def get_end_polyline_node(self, polyline_id, order):
		length = self.road_dict[polyline_id]["length"]
		return [polyline_id, length+1, order]
			
	def get_path( self, start_polyline_id, start_order, target_polyline_id, target_order, junction_id ):
		passed_link_id = set()
		exist_path = False
		dijkstra = Dijkstra(self.get_start_polyline_node(start_polyline_id, start_order))
		exist_target, target_node = self.get_path_target_node(target_polyline_id, target_order, junction_id)
		if exist_target:
			junction_index = junction_id - self.intersection_offset
			for i in range(0, len(self.intersection_list[junction_index][0])+1):
				valid_node, current_node = dijkstra.pop_node()
				if valid_node:
					start_node, end_node = self.get_node_id(current_node[0])
					if current_node[2] == 0:
						end_node_id = end_node
					else:
						end_node_id = start_node
				else:
					break
				if end_node_id == target_node:
					exist_path = True
					break
				from_polyline = self.polyline_node2polyline(current_node)
				connect_intersection = self.get_same_node_intersection_polyline(end_node_id, junction_index)
				next_list = []
				for i in range(0, len(connect_intersection)):
					if not connect_intersection[i][0] in passed_link_id :
						if self.is_passable_path(from_polyline, connect_intersection[i]):
							polyline_id = connect_intersection[i][0]
							length = self.road_dict[polyline_id]["length"]
							order = connect_intersection[i][1]
							next_polyline = [polyline_id, length+1, order]
							next_list.append(next_polyline)
							passed_link_id.add(polyline_id)
						else:
							pass
				dijkstra.update(next_list)
				
		if exist_path:
			end_node = self.get_end_polyline_node(target_polyline_id, target_order)
			result_path = dijkstra.get_path()
			result_path.append(end_node)
			return exist_path, result_path
		else:
			return exist_path, []

	def update_road_speeds(self, link_data_speed):
		"""
		Updates the speed limits of roads that have speeds less than 0 km/h based on their connected roads.
		
		This function implements an iterative algorithm that:
		1. Identifies roads with speed < 0 km/h
		2. For each such road, looks at its connected roads (predecessors and successors)
		3. If any connected road has speed > 0 km/h, updates the current road's speed
		4. Repeats until no more roads can be updated
		
		The update rules are:
		- If a road has predecessor roads with speed > 0 km/h, use the highest speed among them
		- If no predecessor roads have speed > 0 km/h, check successor roads
		- If successor roads have speed > 0 km/h, use the highest speed among them
		- If no connected roads have speed > 0 km/h, leave the road's speed unchanged
		
		Args:
			link_data_speed (list): List of road data where each road is represented as a list with:
				- Index 0: polyline_id (unique identifier for the road)
				- Index 1: start_node
				- Index 2: end_node
				- Index 9: speed (in km/h)
		
		Note:
			- The function modifies link_data_speed in-place
			- The function also updates self.road_dict with the final speeds
			- Roads are considered connected if they share a node (start or end)
			- The algorithm prioritizes predecessor roads over successor roads
		"""
		# Build a mapping from polyline_id to index for easy access
		road_id_to_index = {road[0]: idx for idx, road in enumerate(link_data_speed)}
		
		# Create list of roads with speed < 0 km/h
		link_data_speed_0 = [road for road in link_data_speed if road[9] < 0]

		iteration = 1
		while True:
			print(f"\nIteration {iteration}")
			print(f"Number of roads to process: {len(link_data_speed_0)}")
			
			updated_roads = []

			for current_road in link_data_speed_0:
				current_id = current_road[0]
				current_start_node = current_road[1]
				current_end_node = current_road[2]

				predecessor_speeds = []
				successor_speeds = []

				for other_road in link_data_speed:
					if other_road[0] == current_id:
						continue
					if other_road[9] <= 0:
						continue

					# Check if this road connects to start node (as predecessor)
					if other_road[2] == current_start_node:
						predecessor_speeds.append(other_road[9])
					# Check if this road connects to end node (as successor)
					if other_road[1] == current_end_node:
						successor_speeds.append(other_road[9])

				new_speed = None
				if predecessor_speeds:
					new_speed = max(predecessor_speeds)
				elif successor_speeds:
					new_speed = max(successor_speeds)

				if new_speed is not None:
					idx = road_id_to_index[current_id]
					link_data_speed[idx] = list(link_data_speed[idx])  # make mutable if tuple
					link_data_speed[idx][9] = new_speed
					updated_roads.append(current_id)

			if not updated_roads:
				print("\nNo more roads need updating!")
				break

			# Update remaining roads to process
			link_data_speed_0 = [road for road in link_data_speed if road[9] < 0]

			print(f"Roads updated in this iteration: {len(updated_roads)}")
			print(f"Remaining roads to process: {len(link_data_speed_0)}")
			iteration += 1

		# Update self.road_dict
		for road in link_data_speed:
			self.road_dict[road[0]]["speed"] = int(road[9])


