import pandas as pd
import numpy as np

import math
import matplotlib.pyplot as plt
from tqdm import tqdm

from opendrive.submodule import link_util
from opendrive.submodule import elevation_util
from opendrive.submodule import junction_lane
from opendrive.submodule import parametric_cubic

from opendrive.submodule.LinkData import LinkData
from opendrive.submodule.OpenDRIVE_Road import OpenDRIVE_Road
from opendrive.submodule.OpenDRIVE_Junction import OpenDRIVE_Junction
from opendrive.submodule import open_drive_format

from opendrive.submodule import polyline_point_util

class OpenDRIVE(object):
	
	def __init__(self, road_line_df, road_search_point, flag = False):
		
		self.use_oneway_code = True
		self.use_elevation = True
		self.use_junction_path = True
		
		self.junction_direction_variation_threshold = 130
		self.valid_junction_path_length = 5 #25
		self.valid_junction_path_count = 1
		
		self.link_data = LinkData(road_line_df, road_search_point, flag)
		self.road = OpenDRIVE_Road()
		self.junction = OpenDRIVE_Junction(road_line_df, road_search_point, flag)
		self.polyline_id_list = []
		self.merged_polyline_id_list = []
		self.road_dict = dict()
		self.junction_dict = dict()
		self.junction_road_dict = dict()
		self.next_element_no = 0
		self.road_elevation_dict = dict()
		self.origin_point = road_search_point
		
		self.lane_shift = True
		self.junction_lane_shift = True
		
	def use_parametric_cubic(self):
		self.road.devide_spiral = False
		self.road.use_parametric_cubic = True
	
	def devide_spiral(self):
		self.road.devide_spiral = True
		self.road.use_parametric_cubic = False
		
	def not_use_elevation(self):
		self.use_elevation = False
		
	def convert_road(self):
		self.polyline_id_list = self.link_data.get_general_road_polyline_id()
		self.merged_polyline_id_list = self.link_data.get_general_merged_road_polyline_id()
		self.set_road_polyline()
		self.road.convert()
		
	def restruction_point(self, point_list, sampling_interval = 1):
		restruction_point_list = []
		point_count = len(point_list)
		current_point = point_list[0]
		for i in range(0, point_count-1):
			current_point = point_list[i]
			restruction_point_list.append(current_point)
			next_point = point_list[i+1]
			angle = link_util.get_direction(current_point, next_point)
			length = link_util.get_distance(current_point, next_point)
			restruction_point_count = int(length/sampling_interval)
			if restruction_point_count > 1:
				for i in range(0,restruction_point_count):
					point_x = current_point[0] + math.cos(np.deg2rad(angle))*sampling_interval
					point_y = current_point[1] + math.sin(np.deg2rad(angle))*sampling_interval
					current_point = [point_x, point_y]
					restruction_point_list.append(current_point)
		end_point = point_list[-1]
		if link_util.get_distance(current_point, end_point) > 0.0:
			restruction_point_list.append(end_point)
		return restruction_point_list
		
	def sampling( self, point_list, sampling_length):
		sampling_list = []
		previous_point = point_list[0]
		total_distance = 0
		sampling_list.append([point_list[0][0],point_list[0][1],total_distance])
		for i in range(1,len(point_list)-1):
			diff_x = float(point_list[i][0]) - float(previous_point[0])
			diff_y = float(point_list[i][1]) - float(previous_point[1])
			point_length = math.sqrt(diff_x**2 + diff_y**2)
			total_distance = total_distance + point_length
			previous_point = point_list[i]
			if total_distance+point_length*0.5 > sampling_length:
				sampling_list.append([point_list[i][0],point_list[i][1],total_distance])
				total_distance = 0
		if len(point_list) > 1:
			sampling_list.append([point_list[-1][0],point_list[-1][1],total_distance])   
		return sampling_list
		
	def get_polyline_length(self, point_list):
		length = 0
		previous_point = point_list[0]
		for i in range(0,len(point_list)):
			diff_x = point_list[i][0] - previous_point[0]
			diff_y = point_list[i][1] - previous_point[1]
			length += math.sqrt(diff_x**2+diff_y**2)
			previous_point = point_list[i]
		return length
	
	def get_road_rate(self, start_junction_part, road_part, end_junction_part):
		start_length = self.get_polyline_length(start_junction_part)
		road_length = self.get_polyline_length(road_part)
		end_length = self.get_polyline_length(end_junction_part)
		total_length = start_length + road_length + end_length
		road_part_rate = [start_length/total_length, (start_length+road_length)/total_length]
		return road_part_rate
		
	def set_elevation_dict(self, polyline_id, road_polyline, junction_part ):
		road_part_rate = self.get_road_rate(junction_part[0], road_polyline[2], junction_part[1])
		elevation_list = self.link_data.get_elevation(polyline_id)
		sz_list = elevation_util.get_szlist(elevation_list)
		restruction_sz = self.restruction_point(sz_list, 0.1)
		sampling_sz = self.sampling(restruction_sz, 1)
		self.road_elevation_dict[polyline_id] = [sampling_sz, road_part_rate]
		
	def set_road_polyline(self):
		road_set = set()
		print("Set the polylines of the roads from the merged_polyline_id_list.")
		for polyline_id in tqdm(self.merged_polyline_id_list):
			road_polyline, junction_part = self.link_data.get_road_polyline(polyline_id)
			point_list = self.sampling(self.restruction_point(road_polyline[2],0.1),5.0)
			restraction_polyline = [road_polyline[0],road_polyline[1], point_list]
			self.road.add(polyline_id, restraction_polyline)
			road_set.add(polyline_id)
			self.set_elevation_dict(polyline_id, road_polyline, junction_part)
		print("Set the polylines of the roads from the polyline_id_list.")
		for polyline_id in tqdm(self.polyline_id_list):
			if not polyline_id in self.link_data.merged_polyline:
				road_polyline, junction_part = self.link_data.get_road_polyline(polyline_id)
				point_list = self.sampling(self.restruction_point(road_polyline[2],0.1),5.0)
				restraction_polyline = [road_polyline[0],road_polyline[1], point_list]
				self.road.add(polyline_id, restraction_polyline)
				road_set.add(polyline_id)
				self.set_elevation_dict(polyline_id, road_polyline, junction_part)
				
		road_list = list(road_set)
		element_no = self.next_element_no
		for polyline_id in road_list:
			self.road_dict[polyline_id] = element_no
			element_no += 1
		self.next_element_no = element_no
		self.set_junction_element_no()
		
	def set_junction_element_no(self):
		junction_set = set(self.link_data.df["start_junction"].to_list()) | set(self.link_data.df["end_junction"].to_list())
		junction_list = list(junction_set)
		element_no = self.next_element_no
		for junction_id in junction_list:
			if junction_id < self.link_data.intersection_offset:
				if self.link_data.is_junction(junction_id):
					self.junction_dict[junction_id] = element_no
					element_no += 1
			else:
					self.junction_dict[junction_id] = element_no
					element_no += 1
					
		self.next_element_no = element_no
		
	def previous_road_element(self, polyline_id):
		start_node, end_node = self.link_data.get_node_id(polyline_id)
		polyline_list = self.link_data.get_same_node_polyline(start_node)
		previous_connect_element = []
	    
		for polyline in polyline_list:
			if polyline_id != polyline[0] and polyline[0] in self.road_dict.keys():
				if polyline[1] == 0:
					previous_connect_element.append([self.road_dict[polyline[0]], 0])
				else:
					previous_connect_element.append([self.road_dict[polyline[0]], 1])
		return previous_connect_element
	
	def next_road_element(self, polyline_id):
		start_node, end_node = self.link_data.get_node_id(polyline_id)

		polyline_list = self.link_data.get_same_node_polyline(end_node)
		next_connect_element = []
	    
		for polyline in polyline_list:
			if polyline_id != polyline[0] and polyline[0] in self.road_dict.keys():
				if polyline[1] == 0:
					next_connect_element.append([self.road_dict[polyline[0]], 0])
				else:
					next_connect_element.append([self.road_dict[polyline[0]], 1])
		return next_connect_element
		
	def get_linked_element(self, index):
		polyline_id = self.road.df.at[index,"polyline_id"]
		start_jct, end_jct = self.link_data.get_junction_id(polyline_id)
		
		if start_jct in self.junction_dict.keys():
			element_no = self.junction_dict[start_jct]
			element_type = "junction"
			contact_point = "NA"
		else:
			previous_element = self.previous_road_element(polyline_id)
			if len(previous_element) > 0:
				element_no = previous_element[0][0]
				element_type = "road"
				if previous_element[0][1] == 0:
					contact_point = "start"
				else:
					contact_point = "end"
			else:
				element_no = 0
				element_type = "none"
				contact_point = "NA"
		predecessor =  [element_no, element_type, contact_point]

		if end_jct in self.junction_dict.keys():
			element_no = self.junction_dict[end_jct]
			element_type = "junction"
			contact_point = "NA"
		else:
			next_element = self.next_road_element(polyline_id)
			if len(next_element) > 0:
				element_no = next_element[0][0]
				element_type = "road"
				if next_element[0][1] == 0:
					contact_point = "start"
				else:
					contact_point = "end"
			else:
				element_no = 0
				element_type = "none"
				contact_point = "NA"
		succesor =  [element_no, element_type, contact_point]
		        
		return predecessor, succesor
		
	def get_lane_width_parameter(self, initial_width, end_width, road_length):
		point_list = []
		diff_x = road_length/3.0
			
		point_list.append([0.0, initial_width])
		point_list.append([diff_x, initial_width])
		point_list.append([road_length-diff_x, end_width])
		point_list.append([road_length, end_width])
		pa, pb, pc, pd = parametric_cubic.get_curve(point_list)
		s_offset = 0
		a = pa[1]
		b = pb[1]/(road_length)
		c = pc[1]/(road_length**2)
		d = pd[1]/(road_length**3)
		
		return a, b, c, d
	
	def get_road_lane_parameter(self, polyline_id, road_length):
		road = self.link_data.get_target(polyline_id)
		
		oneway_code = int(road["oneway_code"].to_list()[0])
			
		left_lane_count, right_lane_count = self.link_data.get_lane_count_new(polyline_id, oneway_code)
		# lane_width = 3.5
		left_lane_count_new = 0
		road_width = self.link_data.get_road_width(polyline_id)
		if isinstance(left_lane_count, list):
			left_lane_count_new = left_lane_count[0]
		else:
			left_lane_count_new = left_lane_count

		lane_count = left_lane_count_new + right_lane_count
		if lane_count != 0:
			lane_width = self.link_data.get_lane_width(road_width, lane_count)
		
		s_offset = 0
		a = lane_width
		b = 0
		c = 0
		d = 0

		branch = int(road["branch"].to_list()[0])
		merge = int(road["merge"].to_list()[0])

		if isinstance(left_lane_count, list):
			offset_s = (-0.5)*lane_width*(left_lane_count[0] - right_lane_count)
			offset_e = (-0.5)*lane_width*(left_lane_count[1] - right_lane_count)			

		else:
			offset_a = (-0.5)*lane_width*(left_lane_count - right_lane_count)

			offset_s = offset_a
			offset_e = offset_a


		if branch == 0 and merge == -1:
			a_offset = 0.0
			b_offset = (offset_e-a_offset)/road_length
			lane_offset = [0.0, a_offset, b_offset, 0.0, 0.0]
		elif branch == 1 and merge == -1:
			a_offset = 2*offset_s
			b_offset = (offset_e-a_offset)/road_length
			lane_offset = [0.0, a_offset, b_offset, 0.0, 0.0]
		elif branch == -1 and merge == 0:
			a_offset = offset_s
			b_offset = (0.0-a_offset)/road_length
			lane_offset = [0.0, a_offset, b_offset, 0.0, 0.0]
		elif branch == -1 and merge == 1:
			a_offset = offset_s
			b_offset = (2*offset_e-a_offset)/road_length
			lane_offset = [0.0, a_offset, b_offset, 0.0, 0.0]
		elif branch == 0 and merge == 0:
			a_offset = 0.0
			b_offset = (0.0-a_offset)/road_length
			lane_offset = [0.0, a_offset, b_offset, 0.0, 0.0]
		elif branch == 0 and merge == 1:
			a_offset = 0.0
			b_offset = (2*offset_e-a_offset)/road_length
			lane_offset = [0.0, a_offset, b_offset, 0.0, 0.0]			
		elif branch == 1 and merge == 0:
			a_offset = 2*offset_s
			b_offset = (0.0-a_offset)/road_length
			lane_offset = [0.0, a_offset, b_offset, 0.0, 0.0]
		elif branch == 1 and merge == 1:
			a_offset = 2*offset_s
			b_offset = (2*offset_e-a_offset)/road_length
			lane_offset = [0.0, a_offset, b_offset, 0.0, 0.0]
		elif branch == -1 and merge == -1:
			a_offset = offset_s
			b_offset = (offset_e-a_offset)/road_length
			lane_offset = [0.0, a_offset, b_offset, 0.0, 0.0]

			
		lane_width_parameter = [s_offset, a, b, c, d]
		lane_type ="driving"
		lane_level = "false"
		lane_linkage = []
		lane = [lane_type, lane_level, lane_width_parameter, lane_linkage]
		
		left_lane = []
		if isinstance(left_lane_count, list):
			for i in range(0,min(left_lane_count)):
				left_lane.append(lane)
			if left_lane_count[0]-left_lane_count[1] == -1:
				lane_width_parameter_new = [s_offset, 0, lane_width/road_length, c, d]
				lane_new = [lane_type, lane_level, lane_width_parameter_new, lane_linkage]
				left_lane.append(lane_new)
			elif left_lane_count[0]-left_lane_count[1] == 1:
				lane_width_parameter_new = [s_offset, lane_width, -lane_width/road_length, c, d]
				lane_new = [lane_type, lane_level, lane_width_parameter_new, lane_linkage]
				left_lane.append(lane_new)
			elif left_lane_count[0]-left_lane_count[1] == -2:
				lane_width_parameter_new = [s_offset, 0, 3*lane_width/road_length, -2*lane_width/(road_length*road_length), d]
				lane_new = [lane_type, lane_level, lane_width_parameter_new, lane_linkage]
				left_lane.append(lane_new)

				lane_width_parameter_new = [s_offset, 0, -lane_width/road_length, 2*lane_width/(road_length*road_length), d]
				lane_new = [lane_type, lane_level, lane_width_parameter_new, lane_linkage]
				left_lane.append(lane_new)

			elif left_lane_count[0]-left_lane_count[1] == 2:
				lane_width_parameter_new = [s_offset, lane_width, lane_width/road_length, -2*lane_width/(road_length*road_length), d]
				lane_new = [lane_type, lane_level, lane_width_parameter_new, lane_linkage]
				left_lane.append(lane_new)

				lane_width_parameter_new = [s_offset, lane_width, -3*lane_width/road_length, 2*lane_width/(road_length*road_length), d]
				lane_new = [lane_type, lane_level, lane_width_parameter_new, lane_linkage]
				left_lane.append(lane_new)
		else:
			for i in range(0,left_lane_count):
				left_lane.append(lane)
		
		right_lane = []
		for i in range(0,right_lane_count):
			right_lane.append(lane)
		
		return lane_offset, left_lane, right_lane
		
	def get_elevation_parameter(self, polyline_id, road_length):
		elevation = self.road_elevation_dict[polyline_id]
		road_szlist = elevation_util.get_elevation_part(elevation[0], elevation[1][0], elevation[1][1])
		a,b,c,d = parametric_cubic.get_curve(road_szlist)
		return [[0,a[1],b[1]/(road_length),c[1]/(road_length**2),d[1]/(road_length**3)]]
		
	def devide_road_szlist(self, road_szlist, devide_count):
		devided_szlist =[]
		if len(road_szlist) > devide_count+1:
			next_index = 0
			for i in range(0, len(road_szlist)-(devide_count), devide_count-1):
				devided_szlist.append(road_szlist[i:i+(devide_count)])
				next_index = i+devide_count-1
			
			remaining_data_count = len(road_szlist) - (next_index+1)
			if remaining_data_count > int(devide_count*0.5+0.5) + 10 :
				devided_szlist.append(road_szlist[next_index:])
			else:
				devided_szlist[-1].extend(road_szlist[next_index:])
		else:
			devided_szlist.append(road_szlist[0:])
			
		return devided_szlist
	
	def calculate_optimized_coefficients(self, points):
		try:
			import numpy as np
			from scipy.optimize import curve_fit
			
			# Extract s and z coordinates
			s_values = np.array([p[0] for p in points])
			z_values = np.array([p[1] for p in points])
			
			# Get actual start point
			s_start = s_values[0]
			
			# Normalize s to range [0, segment_length]
			s_normalized = [(s - s_start) for s in s_values]

			# Cubic polynomial function
			def cubic_function(s, a, b, c, d):
				return a + b*s + c*(s**2) + d*(s**3)
			
			if len(points) == 2:
				a = z_values[0]
				b = (z_values[1] - z_values[0]) / (s_normalized[1])
				return a, b, 0, 0, s_start
			elif len(points) == 3:
				coeffs = np.polyfit(s_normalized, z_values, 2)
				c, b, a = coeffs
				return a, b, c, 0, s_start
			else:
				initial_guess = [z_values[0], 0, 0, 0]  # Initial values
				params, _ = curve_fit(cubic_function, s_normalized, z_values, p0=initial_guess)
				a, b, c, d = params
			return a, b, c, d, s_start
			
		except Exception as e:
			print(f"Error in calculate_optimized_coefficients: {e}")
			return None, None, None, None, 0
    
	def get_elevation_parameter_list(self, polyline_id, road_length):
		elevation = self.road_elevation_dict[polyline_id]
		road_szlist = elevation_util.get_elevation_part(elevation[0], elevation[1][0], elevation[1][1])
		devided_szlist = self.devide_road_szlist(road_szlist, 20)
		s = 0
		total_elevation_length = road_szlist[-1][0] - road_szlist[0][0]
		length_rate = road_length/total_elevation_length
		parameter_list = []
		
		for i in range(0, len(devided_szlist)): 
			segment_length = (devided_szlist[i][-1][0] - devided_szlist[i][0][0])*length_rate
			
			# calculate_optimized_coefficients already has its own try-except block
			opt_a, opt_b, opt_c, opt_d, opt_s_start = self.calculate_optimized_coefficients(devided_szlist[i])
			if opt_a is not None and opt_b is not None and opt_c is not None and opt_d is not None:
				# Use optimized coefficients when successfully calculated
				parameter_list.append([s, opt_a, opt_b, opt_c, opt_d])
			else:
				# Fall back to cubic coefficients if optimization returned None values
				a, b, c, d = parametric_cubic.get_curve(devided_szlist[i])
				cubic_coeffs = [s, a[1], b[1]/(segment_length), c[1]/(segment_length**2), d[1]/(segment_length**3)]
				parameter_list.append(cubic_coeffs)

			s += segment_length

		return parameter_list
    
	def get_road_part_xml(self):
		result_str = ""
		self.ng_data_list = []
		print("Generates an XML string for the road of parts.")
		for target_index in tqdm(range(0, self.road.df.shape[0])):
			predecessor, succesor = self.get_linked_element(target_index)
			polyline_id = self.road.df.at[target_index,"polyline_id"]
			road_no = self.road_dict[polyline_id]
			junction_no = -1
			road_length = self.road.df.at[target_index,"road_length"]
			lane_offset, left_lane, right_lane = self.get_road_lane_parameter(polyline_id, road_length)
			speed = self.link_data.get_speed(polyline_id)
			
			if self.use_elevation:
				elevation_list = self.get_elevation_parameter_list(polyline_id, road_length)
			else:
				elevation_list = []
				elevation_list.append([0,0,0,0,0])
			road_str, ng_data = open_drive_format.convert_road_part(self.road.df.at[target_index,"df"], road_no, junction_no, predecessor, succesor, lane_offset, left_lane, right_lane, elevation_list, speed)
			result_str += road_str
			self.ng_data_list.extend(ng_data)
		return result_str

	def check_through( self, junction_id, from_polyline, to_polyline ):
		result = False
		if self.use_oneway_code:
			if self.link_data.check_enter(from_polyline, junction_id):
				if self.link_data.check_leave(to_polyline, junction_id):
					result = True
		else:
			result = True
		return result
	
	def get_junction_point(self, junction_id, from_polyline, to_polyline):
		exist_point = False

		from_start_node, from_end_node = self.link_data.get_node_id(from_polyline[0])
		to_start_node, to_end_node = self.link_data.get_node_id(to_polyline[0])
		    
		if from_polyline[1] == 0:
			exist_point1, point1 = self.road.get_polyline_start_node_point(from_polyline[0], from_start_node)
		else:
			exist_point1, point1 = self.road.get_polyline_end_node_point(from_polyline[0], from_end_node)
		
		if to_polyline[1] == 0:
			exist_point2, point2 = self.road.get_polyline_start_node_point(to_polyline[0], to_start_node)
		else:
			exist_point2, point2 = self.road.get_polyline_end_node_point(to_polyline[0], to_end_node)
		
		if exist_point1 and exist_point2:
			junction_point = [point1, point2]
			if not self.check_uturn(from_polyline, to_polyline, junction_point):
				exist_point = True
		else:
			junction_point = []
		
		return exist_point, junction_point
	
	def get_junction_path(self, junction_id, from_polyline, to_polyline):
		from_connect_point = from_polyline[1]
		if from_connect_point == 0:
			from_order = 1
		else:
			from_order = 0
		to_connect_point = to_polyline[1]
		if to_connect_point == 0:
			to_order = 0
		else:
			to_order = 1
			
		if junction_id < self.link_data.intersection_offset:
			path = []
			path.append(self.link_data.get_start_polyline_node(from_polyline[0], from_order))
			path.append(self.link_data.get_end_polyline_node(to_polyline[0], to_order))
			return True, path
		else:
			return self.link_data.get_path(from_polyline[0],from_order, to_polyline[0], to_order, junction_id)
	
	def shift_junction_point(self, junction_point, point_offset):
	
		from_point = junction_point[0]
		to_point = junction_point[1]
		
		from_shift = point_offset[0][0]+point_offset[1][0]
		to_shift = point_offset[0][1]+point_offset[1][1]

		link_direction = from_point[1]
		direction = link_direction + 90
		distance = from_shift
		shifted_point_x, shifted_point_y = link_util.shift_point(from_point[0][0], from_point[0][1], direction , distance)
		shifted_from_point = [[shifted_point_x, shifted_point_y], from_point[1], 0.0]
		
		link_direction = to_point[1]
		link_direction += 180.0
		direction = link_direction + 90
		distance = to_shift
		shifted_point_x, shifted_point_y = link_util.shift_point(to_point[0][0], to_point[0][1], direction , distance)
		shifted_to_point = [[shifted_point_x, shifted_point_y], to_point[1], 0.0]
		
		return shifted_from_point, shifted_to_point

	def get_junction_path_data(self, from_polyline, to_polyline, path, junction_point, junction_path, point_offset, junction_lane):
		polyline_part = junction_point[0]

		from_jct_point = junction_path[0]
		path_part = junction_path[1]
		to_jct_point = junction_path[2]
		
		from_point, to_point = self.shift_junction_point(junction_point, point_offset)
		point_part = [from_point, junction_path, to_point]
		polyline_part = [from_polyline, to_polyline, path]

		return [polyline_part, point_part, junction_lane]

	def get_junction_data(self, from_polyline, to_polyline, junction_point, point_offset, junction_lane):
		from_point, to_point = self.shift_junction_point(junction_point, point_offset)
		return [[from_polyline, to_polyline], [from_point, to_point], junction_lane]

	def is_valid_junction_path(self, path):
		
		if self.use_junction_path == False:
			return False
		
		result = False
		if len(path) > (2+self.valid_junction_path_count-1):
			path_length = 0;
			delete_start_count = 1
			delete_end_count = 1
			for i in range(delete_start_count,len(path)-delete_end_count):
				path_length += path[i][1]
			if path_length > self.valid_junction_path_length:
				result = True
		return result

	def get_path_offset(self, path, center_offset_dict, lane_offset_dict):
		
		path_offset_dict = dict()
		for i in range(0,len(path)):
			polyline_id = path[i][0]
			path_offset = 0.0
			if polyline_id in center_offset_dict.keys():
				path_offset = center_offset_dict[polyline_id]
			if self.junction_lane_shift:
				if polyline_id in lane_offset_dict.keys():
					path_offset += lane_offset_dict[polyline_id]
			path_offset_dict[polyline_id] = path_offset
		return path_offset_dict

	def get_path_point(self, junction_lane_count, path, path_lane, point_offset, path_direction_variation):
		
		valid_path = self.is_valid_junction_path(path)
		if valid_path:
			center_offset_dict = self.get_path_center_offset(path, path_lane, point_offset, path_direction_variation)
			lane_offset_dict = self.get_path_lane_offset(junction_lane_count, path, path_lane, path_direction_variation, point_offset[1][0], point_offset[1][1])
			path_offset_dict = self.get_path_offset(path, center_offset_dict, lane_offset_dict)
		
			valid_path, path_polyline_point, delete_distance = self.get_path_polyline_point(path, path_offset_dict)
		else:
			valid_path = False
			path_polyline_point = []
			delete_distance = [0.0, 0.0]
		
		if valid_path:
			exist_point = True
			sampling_point = self.get_sampling_path_point(path_polyline_point, delete_distance)
			path_x, path_y, path_df = self.get_junction_path_df(sampling_point)
			path_point_x = []
			path_point_y = []
			for segment in path_x:
				for segment_point in segment:
					path_point_x.append(segment_point)
			for segment in path_y:
				for segment_point in segment:
					path_point_y.append(segment_point)
			path_part = [path_point_x, path_point_y, path_df]
			from_jct_point, to_jct_point = self.get_path_junction_point(path_df)
			
			path_point = [from_jct_point, path_part, to_jct_point]
		else:
			exist_point = False
			path_point = []
			
		return exist_point, path_point
	    
	def get_junction_data_list(self, junction_id, polyline_id_list):
		junction_data_list = []
		junction_path_data_list = []
		for from_polyline in polyline_id_list:
			for to_polyline in polyline_id_list:
				if from_polyline[0] != to_polyline[0] or from_polyline[1] != to_polyline[1]:
					if self.check_through(junction_id, from_polyline[0], to_polyline[0]):
						exist_point, junction_point = self.get_junction_point(junction_id, from_polyline, to_polyline)
						if exist_point:
							exist_path, path = self.get_junction_path(junction_id, from_polyline, to_polyline)
							if exist_path:
								path_direction_variation = self.get_path_direction_variation(path)
								for other_polyline in polyline_id_list:
									flag_branch = -1
									flag_merge = -1
									if len(polyline_id_list) == 3 and other_polyline[0] != from_polyline[0] and other_polyline[0] != to_polyline[0]:
										if other_polyline[1] == 0:
											# Branch
											other_exist_path, other_path = self.get_junction_path(junction_id, from_polyline, other_polyline)
											if other_exist_path:
												other_path_direction_variation = self.get_path_direction_variation(other_path)
												if path_direction_variation < other_path_direction_variation:
													flag_branch = 1
												else:
													flag_branch = 0

												if to_polyline[0] in self.link_data.merged_polyline:
													self.link_data.merged_df.loc[self.link_data.merged_df['polyline_id'] == to_polyline[0], 'branch'] = flag_branch
												else:
													self.link_data.df.loc[self.link_data.df['polyline_id'] == to_polyline[0], 'branch'] = flag_branch

										else:
											# Merge
											other_exist_path, other_path = self.get_junction_path(junction_id, other_polyline, to_polyline)
											if other_exist_path:
												other_path_direction_variation = self.get_path_direction_variation(other_path)
												if path_direction_variation < other_path_direction_variation:
													flag_merge = 1
												else:
													flag_merge = 0

												if from_polyline[0] in self.link_data.merged_polyline:
													self.link_data.merged_df.loc[self.link_data.merged_df['polyline_id'] == from_polyline[0], 'merge'] = flag_merge
												else:
													self.link_data.df.loc[self.link_data.df['polyline_id'] == from_polyline[0], 'merge'] = flag_merge

										break

								point_offset, junction_lane, path_lane = self.get_junction_lane(junction_id, from_polyline, to_polyline, path, path_direction_variation,flag_branch,flag_merge)
								exist_path_point, path_point = self.get_path_point(junction_lane[0], path, path_lane, point_offset, path_direction_variation)
								
								if exist_path_point:
									junction_path_data = self.get_junction_path_data(from_polyline, to_polyline, path, junction_point, path_point, point_offset, junction_lane)
									junction_path_data_list.append(junction_path_data)
								else:
									junction_data = self.get_junction_data(from_polyline, to_polyline, junction_point, point_offset, junction_lane)
									junction_data_list.append(junction_data)

		return junction_data_list, junction_path_data_list

	def set_junction_data(self):
		junction_id_list = list(self.junction_dict.keys())
		print("Set data for junctions on information from link_data and junction_dict objects.")
		for i in tqdm(range(0, len(junction_id_list))):
			junction_id = junction_id_list[i]
			junction_flag, junction_link = self.link_data.get_junction(junction_id)
			polyline_id_list = []
			for i in range(0,len(junction_link)):
				polyline_id_list.append([junction_link[i][0], junction_link[i][1]])
			if junction_flag:
				if junction_id < self.link_data.intersection_offset:
					junction_data_list, junction_path_data_list = self.get_junction_data_list(junction_id, polyline_id_list)
				else:
					junction_data_list, junction_path_data_list = self.get_junction_data_list(junction_id, polyline_id_list)
				
				if len(junction_data_list) > 0:
					self.junction.add(junction_id, junction_data_list)
				if len(junction_path_data_list) > 0:
					self.junction.add_path(junction_id, junction_path_data_list)
	
	def get_junction_contact_point(self, junction_id, polyline_id):
		start_jct, end_jct = self.link_data.get_junction_id(polyline_id[0])
		
		if junction_id == start_jct and polyline_id[1] == 0:
			contact_point = "start"
		elif junction_id == end_jct and polyline_id[1] == 1:
			contact_point = "end"
		else:
			contact_point = "none"
		return contact_point

	def get_junction_linked_element(self, target_index):
		
		junction_id = self.junction.df.at[target_index,"junction_id"]
		from_polyline = self.junction.df.at[target_index,"from_polyline"]
		to_polyline = self.junction.df.at[target_index,"to_polyline"]
		
		element_type = "road"
		
		element_no = self.road_dict[from_polyline[0]]
		contact_point = self.get_junction_contact_point(junction_id, from_polyline)
		predecessor =  [element_no, element_type, contact_point]
		
		element_no = self.road_dict[to_polyline[0]]
		contact_point = self.get_junction_contact_point(junction_id, to_polyline)
		succesor =  [element_no, element_type, contact_point]
		
		return predecessor, succesor
		
	def get_oneway_code( self, order, oneway_code ):
		if order == 1:
			if oneway_code == 1:
				result_code = 2
			elif oneway_code == 2:
				result_code == 1
			else:
				result_code = oneway_code
		else:
			result_code = oneway_code
			
		return result_code
		
	def is_passable(self, polyline_id, order):
		target_data = self.link_data.get_target(polyline_id)
		if order == 1:
			target_node = int(target_data["start_node"].to_list()[0])
		else:
			target_node = int(target_data["end_node"].to_list()[0])
		same_node_polyline_list = self.link_data.get_same_node_polyline(target_node)
		
		next_polyline_list = []
		for same_node_polyline in same_node_polyline_list:
			if same_node_polyline[0] != polyline_id:
				next_polyline_list.append(same_node_polyline)
		
		if len(next_polyline_list) == 1:
			next_polyline = next_polyline_list[0]
			next_order = next_polyline[1]
			next_oneway_code = next_polyline[3]
			oneway_code = self.get_oneway_code(next_oneway_code, next_order)
		else:
			polyline_oneway_code = int(target_data["oneway_code"].to_list()[0])
			oneway_code = self.get_oneway_code(polyline_oneway_code, order)
		    
		if oneway_code == 2:
			return False
		else:
			return True
			
	def check_same_path(self, test_polyline_id, test_polyline_order, target_polyline_id, target_direction):
		current_polyline_id = test_polyline_id
		current_order = test_polyline_order
		result = False
		same_path = list()
		same_path.append(current_polyline_id)
		for i in range(0, 2):
			next_link_dict = self.get_next_link_dict(current_polyline_id, current_order)
			if len(next_link_dict) > 1:
				if target_polyline_id in next_link_dict.keys():
					result = True
				break
			elif len(next_link_dict) == 1:
				current_polyline_id = list(next_link_dict.keys())[0]
				current_order = next_link_dict[current_polyline_id][1]
				same_path.append(current_polyline_id)
		if result == False:
			same_path = []
		return result, same_path
	
	def get_next_same_path_polyline( self, next_link_dict ):
		same_path_polyline = dict()
		for polyline_id in next_link_dict.keys():
			for test_polyline_id in next_link_dict.keys():
				if polyline_id != test_polyline_id:
					direction = next_link_dict[polyline_id][0][2]
					test_direction = next_link_dict[test_polyline_id][0][2]
					diff_direction = link_util.normalize_direction(test_direction-direction)
					if abs(diff_direction) < 10.0 and not test_polyline_id in same_path_polyline.keys():
						order = next_link_dict[test_polyline_id][1]
						exit_same_path, same_path = self.check_same_path(test_polyline_id, order, polyline_id, direction)
						if(exit_same_path):
							same_path_polyline[polyline_id] = same_path
		return same_path_polyline
		
	def get_next_link_dict(self, polyline_id, order):
		result_dict = dict()
		target_link = self.link_data.get_target(polyline_id)
		if order == 0:
			target_node = int(target_link["end_node"].to_list()[0])
		else:
			target_node = int(target_link["start_node"].to_list()[0])
		
		same_node_polyline = self.link_data.get_same_node_polyline(target_node)
		for polyline in same_node_polyline:
			if polyline[0] != polyline_id and not polyline[0] in self.link_data.merged_polyline:
				if self.is_passable(polyline[0], polyline[1]):
					next_link = self.link_data.get_first_link(polyline[0], polyline[1])
					result_dict[polyline[0]] = [next_link, polyline[1]]
		
		same_node_merged_polyline = self.link_data.get_same_node_merged_polyline(target_node)
		for polyline in same_node_merged_polyline:
			if polyline[0] != polyline_id:
				if self.is_passable(polyline[0], polyline[1]):
					next_link = self.link_data.get_first_link(polyline[0], polyline[1])
					result_dict[polyline[0]] = [next_link, polyline[1]]
		return result_dict
		
	def get_previous_link_dict(self, polyline_id, order):
		result_dict = dict()
		target_link = self.link_data.get_target(polyline_id)
		if order == 1:
			target_node = int(target_link["end_node"].to_list()[0])
		else:
			target_node = int(target_link["start_node"].to_list()[0])
			
		same_node_polyline = self.link_data.get_same_node_polyline(target_node)
		for polyline in same_node_polyline:
			if polyline[0] != polyline_id and not polyline[0] in self.link_data.merged_polyline:
				if polyline[1] == 0:
					previous_polyline_order = 1
				else:
					previous_polyline_order = 0
				if self.is_passable(polyline[0], previous_polyline_order):
					previous_link = self.link_data.get_previous_link(polyline[0], polyline[1])
					result_dict[polyline[0]] = previous_link
		
		same_node_merged_polyline = self.link_data.get_same_node_merged_polyline(target_node)
		for polyline in same_node_merged_polyline:
			if polyline[0] != polyline_id:
				if polyline[1] == 0:
					previous_polyline_order = 1
				else:
					previous_polyline_order = 0
				if self.is_passable(polyline[0], previous_polyline_order):
					previous_link = self.link_data.get_previous_link(polyline[0], polyline[1])
					result_dict[polyline[0]] = previous_link
		return result_dict
	
	def get_direction_variation_df( self, incoming_link, next_link_dict):
		result_list = []
		for polyline_id in next_link_dict.keys():
			direction_variation = link_util.normalize_direction(next_link_dict[polyline_id][0][2] - incoming_link[2])
			variation_type = junction_lane.direction_variation2variation_type(direction_variation)
			if variation_type != "uturn":
				result_list.append([polyline_id, direction_variation, abs(direction_variation), variation_type])
		if len(result_list) == 0:
			result_list.append([-1,0,0,0])
		result_df = pd.DataFrame(result_list)
		result_df.columns = ["polyline_id", "direction_variation", "absolute_variation", "variation_type"]
		return result_df #.sort_values("direction_variation").reset_index(drop=True)

	def get_outgoing_direction_variation_df(self, previous_link_dict, outgoing_link):
		result_list = []
		for polyline_id in previous_link_dict.keys():
			direction_variation = link_util.normalize_direction(outgoing_link[2] - previous_link_dict[polyline_id][2])
			variation_type = junction_lane.direction_variation2variation_type(direction_variation)
			if variation_type != "uturn":
				result_list.append([polyline_id, direction_variation, abs(direction_variation), variation_type])
		if len(result_list) == 0:
			result_list.append([-1,0,0,0])
		result_df = pd.DataFrame(result_list)
		result_df.columns = ["polyline_id", "direction_variation", "absolute_variation", "variation_type"]
		return result_df #.sort_values("direction_variation").reset_index(drop=True)
		
	def get_total_connect_lane_count(self, link_dict):
		total_left_lane = 0
		for polyline_id in link_dict.keys():
			oneway_code = int(self.link_data.get_target(polyline_id)["oneway_code"].to_list()[0])
			left_lane, right_lane = self.link_data.get_lane_count(polyline_id, oneway_code)
			total_left_lane = total_left_lane + left_lane
		return total_left_lane
		
	def get_lane_index_uturn(self, incoming_lane, outgoing_lane, first_direction_variation):
		connect_lane = []
		if first_direction_variation < 0.0:
			connect_lane.append([0,outgoing_lane[-1],"constant"])
		else:
			connect_lane.append([incoming_lane[-1],outgoing_lane[-1],"constant"])
		return connect_lane
	
	def get_lane_index_straight(self, lane_count, incoming_lane, outgoing_lane, first_direction_variation, first_direction_variation_df, outgoing_direction_variation, outgoing_direction_variation_df, last_path_node):
		connect_lane = []

		if len(outgoing_lane) < len(incoming_lane) and len(first_direction_variation_df) > 1:
			incoming_offset = len(incoming_lane) - lane_count
			outgoing_offset = len(outgoing_lane) - lane_count
			relative_left_turn_count = junction_lane.get_relative_left_turn_count(first_direction_variation, first_direction_variation_df)
			relative_right_turn_count = junction_lane.get_relative_right_turn_count(first_direction_variation, first_direction_variation_df)

			last_polyline_id = last_path_node[0]
			next_link_dict = self.get_next_link_dict(last_path_node[0], last_path_node[2])
			total_outgoing_polyline_count = len(next_link_dict)
			next_connect_lane_count = self.get_total_connect_lane_count(next_link_dict)

			if relative_left_turn_count > 0 and relative_right_turn_count == 0:
				if incoming_offset > 1:
					incoming_offset = incoming_offset - 1
				else:
					incoming_offset = 0

			#if next_connect_lane_count < len(incoming_lane) and incoming_offset > 0:
			#	connect_lane.append([0,0,"decrease"])

			for i in range(0, lane_count):
				connect_lane.append([incoming_lane[i+incoming_offset], outgoing_lane[i+outgoing_offset],"constant"])
		elif len(incoming_lane) < len(outgoing_lane):
			relative_left_turn_count = junction_lane.get_relative_left_turn_count(outgoing_direction_variation, outgoing_direction_variation_df)
			relative_right_turn_count = junction_lane.get_relative_right_turn_count(outgoing_direction_variation, outgoing_direction_variation_df)
			incoming_offset = len(incoming_lane) - lane_count
			if relative_right_turn_count > 0:
				remain_lane_count = len(outgoing_lane) - (lane_count+1)
			else:
				remain_lane_count = len(outgoing_lane) - lane_count
			if remain_lane_count > relative_left_turn_count:
				outgoing_offset = len(outgoing_lane) - (lane_count + relative_left_turn_count)
			else:
				outgoing_offset = len(outgoing_lane) - (lane_count + remain_lane_count)
			for i in range(0, lane_count):
				connect_lane.append([incoming_lane[i+incoming_offset], outgoing_lane[i+outgoing_offset],"constant"])        
		else:
			incoming_offset = len(incoming_lane) - lane_count
			outgoing_offset = len(outgoing_lane) - lane_count
			for i in range(0, lane_count):
				connect_lane.append([incoming_lane[i+incoming_offset], outgoing_lane[i+outgoing_offset],"constant"])
			
		return connect_lane

	def get_lane_index_left_turn(self, lane_count, incoming_lane, outgoing_lane):
		connect_lane = []
		incoming_offset = len(incoming_lane) - lane_count
		outgoing_offset = len(outgoing_lane) - lane_count
		for i in range(0, lane_count):
			connect_lane.append([incoming_lane[i+incoming_offset], outgoing_lane[i+outgoing_offset],"constant"])
		return connect_lane
	
	def get_lane_index_right_turn(self, lane_count, incoming_lane, outgoing_lane):
		connect_lane = []
		for i in range(0, lane_count):
			connect_lane.append([incoming_lane[i], outgoing_lane[i],"constant"])
		return connect_lane
		
	def get_lane_index_merge(self, incoming_lane, outgoing_lane, outgoing_direction_variation, outgoing_direction_variation_df):
		relative_left_polyline_df = outgoing_direction_variation_df[outgoing_direction_variation_df["direction_variation"] > outgoing_direction_variation]
		relative_left_lane_count = 0
		for i in range(0, len(outgoing_direction_variation_df)):
			direction_variation = outgoing_direction_variation_df.at[i,"direction_variation"]
			if direction_variation > outgoing_direction_variation:
				polyline_id = outgoing_direction_variation_df.at[i, "polyline_id"]
				polyline_lane = self.get_polyline_lane(polyline_id)
				relative_left_lane_count += polyline_lane[0]
				
		outgoing_lane_count = len(outgoing_lane)
		incoming_lane_count = len(incoming_lane)
		
		if relative_left_lane_count + incoming_lane_count > outgoing_lane_count:
			lane_offset = 0
		else:
			lane_offset = outgoing_lane_count - (relative_left_lane_count + incoming_lane_count)
			
		lane_count = incoming_lane_count
		connect_lane = []
		for i in range(0, lane_count):
			connect_lane.append([incoming_lane[i], outgoing_lane[i+lane_offset],"constant"])
		
		return connect_lane
		
	def get_lane_index_diverge(self, incoming_lane, outgoing_lane, first_direction_variation, first_direction_variation_df):
		relative_left_lane_count = 0
		for i in range(0, len(first_direction_variation_df)):
			direction_variation = first_direction_variation_df.at[i, "direction_variation"]
			if direction_variation > first_direction_variation:
				polyline_id = first_direction_variation_df.at[i, "polyline_id"]
				polyline_lane = self.get_polyline_lane(polyline_id)
				relative_left_lane_count += polyline_lane[0]
				
		outgoing_lane_count = len(outgoing_lane)
		incoming_lane_count = len(incoming_lane)
		lane_count = len(outgoing_lane)
		
		if relative_left_lane_count > 0:# + outgoing_lane_count > incoming_lane_count:
			lane_offset = 0
		else:
			lane_offset = incoming_lane_count - outgoing_lane_count #(relative_left_lane_count + outgoing_lane_count) - incoming_lane_count
			over_count = lane_offset+lane_count - incoming_lane_count
			if over_count > 0:
				lane_offset -= over_count
		
		connect_lane = []
		for i in range(0, lane_count):
			connect_lane.append([incoming_lane[i+lane_offset], outgoing_lane[i],"constant"])
		
		return connect_lane
		
	def get_lane_index_pallalel(self, incoming_lane, outgoing_lane, first_direction_variation):
		connect_lane = []
		if first_direction_variation < 0.0:
			connect_lane.append([0,outgoing_lane[-1],"constant"])
		else:
			connect_lane.append([incoming_lane[-1],0,"constant"])
		return connect_lane
		
	def get_lane_index_compound(self, lane_count, incoming_variation_type, outgoing_variation_type, incoming_lane, outgoing_lane, total_outgoing_polyline_count):
		connect_lane = []
		if len(incoming_lane) == len(outgoing_lane):
			if outgoing_variation_type == "right_turn":
				incoming_offset = 0
				outgoing_offset = 0
			else:
				incoming_offset = len(incoming_lane) - lane_count
				outgoing_offset = len(outgoing_lane) - lane_count
			for i in range(0, lane_count):
				connect_lane.append([incoming_lane[i+incoming_offset], outgoing_lane[i+outgoing_offset],"constant"])
		
		elif len(incoming_lane) < len(outgoing_lane):
			if incoming_variation_type == "left_turn" or incoming_variation_type == "straight":
				incoming_offset = len(incoming_lane) - lane_count
			else:
				incoming_offset = 0
			
			if outgoing_variation_type == "straight":
				if incoming_variation_type == "right_turn":
					outgoing_offset = 0
				else:
					outgoing_offset = len(outgoing_lane) - lane_count
			elif outgoing_variation_type == "left_turn":
				outgoing_offset = len(outgoing_lane) - lane_count
			else:
				outgoing_offset = 0
			
			for i in range(0, lane_count):
				connect_lane.append([incoming_lane[i+incoming_offset], outgoing_lane[i+outgoing_offset],"constant"])
			
		elif len(outgoing_lane) < len(incoming_lane):
			if incoming_variation_type == "left_turn" or incoming_variation_type == "straight":
				if outgoing_variation_type != "right_turn":
					incoming_offset = len(incoming_lane) - lane_count
				else:
					incoming_offset = 0
			else:
				incoming_offset = 0

			if outgoing_variation_type == "left_turn" or outgoing_variation_type == "straight":
				outgoing_offset = len(outgoing_lane) - lane_count
			else:
				outgoing_offset = 0
			
			#if total_outgoing_polyline_count == 1 and incoming_offset > 0:
			#	connect_lane.append([0,0,"decrease"])

			for i in range(0, lane_count):
				connect_lane.append([incoming_lane[i+incoming_offset], outgoing_lane[i+outgoing_offset],"constant"])

			#if total_outgoing_polyline_count == 1 and incoming_offset == 0:
			#	connect_lane.append([len(incoming_lane)-1,0,"decrease"])
			
		return connect_lane 
		
	def get_max_branch_index(self, path):
		result_index = 0
		max_branch_count = 0
		for i in range(0, len(path)-1):
			polyline_id = path[i][0]
			order = path[i][2]
			target_link = self.link_data.get_target(polyline_id)
			if order == 0:
				target_node = int(target_link["end_node"])
			else:
				target_node = int(target_link["start_node"])
			same_node_polyline = self.link_data.get_same_node_all_polyline(target_node)
			if len(same_node_polyline) > max_branch_count:
				result_index = i
				max_branch_count = len(same_node_polyline)
				break
		return result_index
		
	def get_first_branch_index(self, path):
		result_index = 0
		for i in range(0, len(path)-1):
			polyline_id = path[i][0]
			order = path[i][2]
			target_link = self.link_data.get_target(polyline_id)
			if order == 0:
				target_node = int(target_link["end_node"])
			else:
				target_node = int(target_link["start_node"])
			same_node_polyline = self.link_data.get_same_node_all_polyline(target_node)
			if len(same_node_polyline) > 2:
				result_index = i
				break
		return result_index
    
	def get_last_branch_index(self, path):
		result_index = len(path)-2
		for i in range(0, len(path)-1):
			polyline_id = path[i][0]
			order = path[i][2]
			target_link = self.link_data.get_target(polyline_id)
			if order == 0:
				target_node = int(target_link["end_node"])
			else:
				target_node = int(target_link["start_node"])
			same_node_polyline = self.link_data.get_same_node_all_polyline(target_node)
			if len(same_node_polyline) > 2:
				result_index = i
		return result_index
		
	def get_branch_index(self, path):
		branch_index_list = []
		for i in range(0, len(path)-1):
			polyline_id = path[i][0]
			order = path[i][2]
			target_link = self.link_data.get_target(polyline_id)
			if order == 0:
				target_node = int(target_link["end_node"].to_list()[0])
			else:
				target_node = int(target_link["start_node"].to_list()[0])
			same_node_polyline = self.link_data.get_same_node_all_polyline(target_node)
			if len(same_node_polyline) > 2:
				branch_index_list.append(i)
		return branch_index_list
		
	def is_merge_type(self, incoming_lane_count, outgoing_lane_count, outgoing_direction_variation_df):
		if len(outgoing_direction_variation_df) > 0:
			straight_variation_df = outgoing_direction_variation_df[outgoing_direction_variation_df["absolute_variation"] < 15.0]
			total_previous_lane_count = 0
			for i in range(0,len(outgoing_direction_variation_df)):
				polyline_id = outgoing_direction_variation_df.at[i, "polyline_id"]
				absolute_variation = outgoing_direction_variation_df.at[i, "absolute_variation"]
				if absolute_variation < 20.0:
					polyline_lane = self.get_polyline_lane(polyline_id)
					total_previous_lane_count += polyline_lane[0]
			
			if outgoing_lane_count > incoming_lane_count and total_previous_lane_count >= outgoing_lane_count:
				return True
			else:
				return False
		else:
			return False
			
	def is_diverge_type(self, incoming_lane_count, outgoing_lane_count, first_direction_variation_df):
		if len(first_direction_variation_df) > 0:
			total_previous_lane_count = 0
			for i in range(0,len(first_direction_variation_df)):
				absolute_variation = first_direction_variation_df.at[i, "absolute_variation"]
				if absolute_variation < 20.0:
					polyline_id = first_direction_variation_df.at[i, "polyline_id"]
					if polyline_id >= 0:
						polyline_lane = self.get_polyline_lane(polyline_id)
						total_previous_lane_count += polyline_lane[0]
			
			if outgoing_lane_count < incoming_lane_count and total_previous_lane_count >= incoming_lane_count:
				return True
			else:
				return False
		else:
			return False
	
	def get_junction_lane_index(self, path, path_direction_variation, incoming_lane_count, junction_lane_count, outgoing_lane_count):
		total_variation = path_direction_variation[0]
		first_variation = path_direction_variation[1][0]
		last_variation = path_direction_variation[1][1]

		valid_variation_count = path_direction_variation[2]
		path_direction_variation_dict = path_direction_variation[3]

		branch_index = self.get_branch_index(path)
		if len(branch_index) == 0:
			incoming_path_index = 0
			last_path_index = len(path) - 2
		else:
			incoming_path_index = branch_index[0]
			last_path_index = branch_index[-1]

		first_path_index = incoming_path_index+1
		if first_path_index > len(path) - 1:
			first_path_index = len(path) - 1

		outgoing_path_index = last_path_index+1
		if outgoing_path_index > len(path) - 1:
			outgoing_path_index = len(path) - 1

		incoming_link = self.link_data.get_last_link(path[incoming_path_index][0], path[incoming_path_index][2])
		first_link = self.link_data.get_first_link(path[first_path_index][0], path[first_path_index][2])
		first_link_dict = self.get_next_link_dict(path[incoming_path_index][0], path[incoming_path_index][2])
		total_outgoing_polyline_count = len(first_link_dict)
		same_path_polyline_dict = self.get_next_same_path_polyline(first_link_dict)
		for polyline_id in same_path_polyline_dict.keys():
			for delete_polyline in same_path_polyline_dict[polyline_id]:
				if delete_polyline in first_link_dict:
					first_link_dict.pop(delete_polyline)    
		first_direction_variation = link_util.get_direction_variation(incoming_link[0], first_link[0], first_link[1])
		
		if len(first_link_dict) == 0:
			first_link_dict[path[first_path_index][0]] = [first_link, path[first_path_index][2]]
		first_direction_variation_df = self.get_direction_variation_df(incoming_link, first_link_dict)
		incoming_variation_type, incoming_lane = junction_lane.get_incoming_lane_index(incoming_lane_count, first_direction_variation, first_direction_variation_df)

		last_link = self.link_data.get_last_link(path[last_path_index][0], path[last_path_index][2])
		outgoing_link = self.link_data.get_first_link(path[outgoing_path_index][0], path[outgoing_path_index][2])
		outgoing_direction_variation = link_util.get_direction_variation(last_link[0], outgoing_link[0], outgoing_link[1])
		previous_link_dict = self.get_previous_link_dict(path[outgoing_path_index][0], path[outgoing_path_index][2])
		for target_polyline_id in same_path_polyline_dict.keys():
			if  target_polyline_id in previous_link_dict.keys():
				for delete_polyline in same_path_polyline_dict[polyline_id]:
					if delete_polyline in previous_link_dict:
						previous_link_dict.pop(delete_polyline)
		
		if len(previous_link_dict) == 0:
			previous_link_dict[path[last_path_index][0]] = last_link
		outgoing_direction_variation_df = self.get_outgoing_direction_variation_df(previous_link_dict, outgoing_link)
		outgoing_variation_type, outgoing_lane = junction_lane.get_outgoing_lane_index(outgoing_lane_count, outgoing_direction_variation, outgoing_direction_variation_df)

		if incoming_variation_type == outgoing_variation_type:
			if incoming_variation_type == "straight":
				if total_variation < -20.0:
					junction_type = "right_turn"
				elif total_variation > 20.0:
					junction_type = "left_turn"
				elif incoming_lane_count == len(incoming_lane) and self.is_merge_type(len(incoming_lane), len(outgoing_lane), outgoing_direction_variation_df):
					junction_type = "merge"
				elif self.is_diverge_type(len(incoming_lane), len(outgoing_lane), first_direction_variation_df):
					junction_type = "diverge"
				else:
					junction_type = "straight"
			else:
				junction_type = incoming_variation_type
		else:
			junction_type = "compound"

		if valid_variation_count != 0 and abs(total_variation) > 170:
			junction_type = "uturn"

		if valid_variation_count == 0 and abs(total_variation) < 10.0:
			if incoming_variation_type != "straight" or outgoing_variation_type != "straight":
				junction_type = "pallalel"

		if len(incoming_lane) < len(outgoing_lane):
			if len(incoming_lane) <= junction_lane_count:
				lane_count = len(incoming_lane)
			else:
				lane_count = junction_lane_count
		else:
			if len(outgoing_lane) <= junction_lane_count:
				lane_count = len(outgoing_lane)
			else:
				lane_count = junction_lane_count        
				
		if junction_type == "uturn":
			connect_lane = self.get_lane_index_uturn(incoming_lane, outgoing_lane, first_direction_variation)
		elif junction_type == "straight":
			connect_lane = self.get_lane_index_straight(lane_count, incoming_lane, outgoing_lane, first_direction_variation, first_direction_variation_df, outgoing_direction_variation, outgoing_direction_variation_df, path[-2])
		elif junction_type == "merge":
			connect_lane = self.get_lane_index_merge(incoming_lane, outgoing_lane, outgoing_direction_variation, outgoing_direction_variation_df)
		elif junction_type == "diverge":
			connect_lane = self.get_lane_index_diverge(incoming_lane, outgoing_lane, first_direction_variation, first_direction_variation_df)        
		elif junction_type == "left_turn":
			connect_lane = self.get_lane_index_left_turn(lane_count, incoming_lane, outgoing_lane)
		elif junction_type == "right_turn":
			connect_lane = self.get_lane_index_right_turn(lane_count, incoming_lane, outgoing_lane)
		elif junction_type == "pallalel":
			connect_lane = self.get_lane_index_pallalel(incoming_lane, outgoing_lane, first_direction_variation)
		else:
			connect_lane = self.get_lane_index_compound(lane_count, incoming_variation_type, outgoing_variation_type, incoming_lane, outgoing_lane, total_outgoing_polyline_count)

		return [junction_type, incoming_variation_type, outgoing_variation_type], connect_lane

	def get_highway_junction_lane_index(self, path, path_direction_variation, incoming_lane_count, junction_lane_count, outgoing_lane_count):
		total_variation = path_direction_variation[0]
		first_variation = path_direction_variation[1][0]
		last_variation = path_direction_variation[1][1]

		valid_variation_count = path_direction_variation[2]
		path_direction_variation_dict = path_direction_variation[3]

		branch_index = self.get_branch_index(path)
		if len(branch_index) == 0:
			incoming_path_index = 0
			last_path_index = len(path) - 2
		else:
			incoming_path_index = branch_index[0]
			last_path_index = branch_index[-1]

		first_path_index = incoming_path_index+1
		if first_path_index > len(path) - 1:
			first_path_index = len(path) - 1

		outgoing_path_index = last_path_index+1
		if outgoing_path_index > len(path) - 1:
			outgoing_path_index = len(path) - 1

		incoming_link = self.link_data.get_last_link(path[incoming_path_index][0], path[incoming_path_index][2])
		first_link = self.link_data.get_first_link(path[first_path_index][0], path[first_path_index][2])
		first_link_dict = self.get_next_link_dict(path[incoming_path_index][0], path[incoming_path_index][2])
		total_outgoing_polyline_count = len(first_link_dict)
		same_path_polyline_dict = self.get_next_same_path_polyline(first_link_dict)
		for polyline_id in same_path_polyline_dict.keys():
			for delete_polyline in same_path_polyline_dict[polyline_id]:
				if delete_polyline in first_link_dict:
					first_link_dict.pop(delete_polyline)    
		first_direction_variation = link_util.get_direction_variation(incoming_link[0], first_link[0], first_link[1])

		if len(first_link_dict) == 0:
			first_link_dict[path[first_path_index][0]] = [first_link, path[first_path_index][2]]
		first_direction_variation_df = self.get_direction_variation_df(incoming_link, first_link_dict)
		# if abs(first_direction_variation) < 20.0 and len(first_link_dict) == 1:
		incoming_variation_type = "straight"
		if incoming_lane_count == 4:
			incoming_lane = [0,1,2,3]
		elif incoming_lane_count == 3:
			incoming_lane = [0,1,2]
		elif incoming_lane_count == 2:
			incoming_lane = [0,1]
		else:
			incoming_lane = [0]
		# else:
		# 	incoming_variation_type, incoming_lane = junction_lane.get_incoming_lane_index(incoming_lane_count, first_direction_variation, first_direction_variation_df)
			
		last_link = self.link_data.get_last_link(path[last_path_index][0], path[last_path_index][2])
		outgoing_link = self.link_data.get_first_link(path[outgoing_path_index][0], path[outgoing_path_index][2])
		outgoing_direction_variation = link_util.get_direction_variation(last_link[0], outgoing_link[0], outgoing_link[1])
		previous_link_dict = self.get_previous_link_dict(path[outgoing_path_index][0], path[outgoing_path_index][2])
		for target_polyline_id in same_path_polyline_dict.keys():
			if  target_polyline_id in previous_link_dict.keys():
				for delete_polyline in same_path_polyline_dict[polyline_id]:
					if delete_polyline in previous_link_dict:
						previous_link_dict.pop(delete_polyline)
		
		if len(previous_link_dict) == 0:
			previous_link_dict[path[last_path_index][0]] = last_link
		
		outgoing_direction_variation_df = self.get_outgoing_direction_variation_df(previous_link_dict, outgoing_link)
		# if abs(outgoing_direction_variation) < 20.0:
		outgoing_variation_type = "straight"
		if outgoing_lane_count == 4:
			outgoing_lane = [0,1,2,3]
		elif outgoing_lane_count == 3:
			outgoing_lane = [0,1,2]
		elif outgoing_lane_count == 2:
			outgoing_lane = [0,1]
		else:
			outgoing_lane = [0]
		# else:
		# 	outgoing_variation_type, outgoing_lane = junction_lane.get_outgoing_lane_index(outgoing_lane_count, outgoing_direction_variation, outgoing_direction_variation_df)

		if incoming_variation_type == outgoing_variation_type:
			if incoming_variation_type == "straight":
				if total_variation < -20.0:
					junction_type = "right_turn"
				elif total_variation > 20.0:
					junction_type = "left_turn"
				elif incoming_lane_count == len(incoming_lane) and self.is_merge_type(len(incoming_lane), len(outgoing_lane), outgoing_direction_variation_df):
					junction_type = "merge"
				elif self.is_diverge_type(len(incoming_lane), len(outgoing_lane), first_direction_variation_df):
					junction_type = "diverge"
				else:
					junction_type = "straight"
			else:
				junction_type = incoming_variation_type
		else:
			junction_type = "compound"

		if valid_variation_count != 0 and abs(total_variation) > 170:
			junction_type = "uturn"

		if valid_variation_count == 0 and abs(total_variation) < 10.0:
			if incoming_variation_type != "straight" or outgoing_variation_type != "straight":
				junction_type = "pallalel"
		
		if len(incoming_lane) < len(outgoing_lane):
			if len(incoming_lane) <= junction_lane_count:
				lane_count = len(incoming_lane)
			else:
				lane_count = junction_lane_count
		else:
			if len(outgoing_lane) <= junction_lane_count:
				lane_count = len(outgoing_lane)
			else:
				lane_count = junction_lane_count
				
		if junction_type == "uturn":
			connect_lane = self.get_lane_index_uturn(incoming_lane, outgoing_lane, first_direction_variation)
		elif junction_type == "straight":
			connect_lane = self.get_lane_index_straight(lane_count, incoming_lane, outgoing_lane, first_direction_variation, first_direction_variation_df, outgoing_direction_variation, outgoing_direction_variation_df, path[-2])
		elif junction_type == "merge":
			connect_lane = self.get_lane_index_merge(incoming_lane, outgoing_lane, outgoing_direction_variation, outgoing_direction_variation_df)
		elif junction_type == "diverge":
			connect_lane = self.get_lane_index_diverge(incoming_lane, outgoing_lane, first_direction_variation, first_direction_variation_df)        
		elif junction_type == "left_turn":
			connect_lane = self.get_lane_index_left_turn(lane_count, incoming_lane, outgoing_lane)
		elif junction_type == "right_turn":
			connect_lane = self.get_lane_index_right_turn(lane_count, incoming_lane, outgoing_lane)
		elif junction_type == "pallalel":
			connect_lane = self.get_lane_index_pallalel(incoming_lane, outgoing_lane, first_direction_variation)
		else:
			connect_lane = self.get_lane_index_compound(lane_count, incoming_variation_type, outgoing_variation_type, incoming_lane, outgoing_lane, total_outgoing_polyline_count)

		return [junction_type, incoming_variation_type, outgoing_variation_type], connect_lane

	
	def test_path_lane(self, path):
		test_path_lane_dict = dict()
		for i in range(0, len(path)):
			polyline_node = path[i]
			polyline_id = polyline_node[0]
			order = polyline_node[2]
			target_link = self.link_data.get_target(polyline_id)
			oneway_code = int(target_link["oneway_code"])

			left_lane_count, right_lane_count = self.link_data.get_lane_count(polyline_id, oneway_code)
			lane_count = left_lane_count;
			lane_width = self.link_data.get_lane_width(self.link_data.get_road_width(polyline_id), left_lane_count+right_lane_count)
			test_path_lane_dict[polyline_id] = [left_lane_count, right_lane_count, lane_width, oneway_code]
		return test_path_lane_dict

	def get_previous_reference_id(self, current_id, order):
		target_data = self.link_data.get_target(current_id)
		current_point = target_data["xy"].to_list()[0]
		if order == 1:
			current_direction = link_util.get_direction(current_point[-1], current_point[-2])
			start_node = int(target_data["end_node"].to_list()[0])
		else:
			current_direction = link_util.get_direction(current_point[0], current_point[1])
			start_node = int(target_data["start_node"].to_list()[0])

		start_node_polyline_list = self.link_data.get_same_node_all_polyline(start_node)
		min_diff_direction = 180.0

		reference_id = current_id
		for polyline in start_node_polyline_list:
			previous_id = polyline[0]
			previous_order = polyline[1]
			previous_point = polyline[2]
			oneway_code = polyline[3]

			if previous_id != current_id:
				if previous_order == 0:
					previous_direction = link_util.get_direction(previous_point[1], previous_point[0])
				else:
					previous_direction = link_util.get_direction(previous_point[-2], previous_point[-1])
				
				diff_direction = link_util.normalize_direction(current_direction - previous_direction)
				if abs(diff_direction) < min_diff_direction:
					min_diff_direction = abs(diff_direction)
					previous_oneway_code = self.get_oneway_code(order, oneway_code)
					if previous_oneway_code == 0 or previous_oneway_code == 1:
						reference_id = previous_id
		return reference_id
	
	def get_next_reference_id(self, current_id, order):
		target_data = self.link_data.get_target(current_id)
		current_point = target_data["xy"].to_list()[0]
		if order == 1:
			current_direction = link_util.get_direction(current_point[-1], current_point[-2])
			end_node = int(target_data["start_node"].to_list()[0])
		else:
			current_direction = link_util.get_direction(current_point[0], current_point[1])
			end_node = int(target_data["end_node"].to_list()[0])
		
		next_polyline_list = self.link_data.get_same_node_all_polyline(end_node)
		min_diff_direction = 180.0
		
		reference_id = current_id
		for polyline in next_polyline_list:
			next_id = polyline[0]
			next_order = polyline[1]
			next_point = polyline[2]
			oneway_code = polyline[3]
			if next_id != current_id:
				if next_order == 0:
					next_direction = link_util.get_direction(next_point[0], next_point[1])
				else:
					next_direction = link_util.get_direction(next_point[-1], next_point[-2])
				
				diff_direction = link_util.normalize_direction(next_direction - current_direction)
				if abs(diff_direction) < min_diff_direction:
					min_diff_direction = abs(diff_direction)
					next_oneway_code = self.get_oneway_code(order, oneway_code)
					if next_oneway_code == 0 or next_oneway_code == 1:
						reference_id = next_id
		return reference_id
		
	def get_polyline_lane(self, polyline_id, flag = False):
		road = self.link_data.get_target(polyline_id)
		oneway_code = int(road["oneway_code"].to_list()[0])
		left_lane_count, right_lane_count = self.link_data.get_lane_count(polyline_id, oneway_code, flag)
		# lane_width = 3.5
		left_lane_count_new, right_lane_count_new = self.link_data.get_lane_count_new(polyline_id, oneway_code)
		road_width = self.link_data.get_road_width(polyline_id)
		if isinstance(left_lane_count_new, list):
			left_lane_count_new = left_lane_count_new[0]
		else:
			left_lane_count_new = left_lane_count_new
		lane_count = left_lane_count_new + right_lane_count_new
		if lane_count != 0:
			lane_width = self.link_data.get_lane_width(road_width, lane_count)
		return [left_lane_count, right_lane_count, lane_width, oneway_code]
    
	def get_path_lane(self, path):
		path_lane_dict = dict()

		polyline_id = path[0][0]
		polyline_lane = self.get_polyline_lane(polyline_id, True)

		path_lane_dict[polyline_id] = polyline_lane
		path_lane = polyline_lane[0]

		polyline_count = len(path)
		center_count = int(len(path)*0.5)
		last_index = len(path)-2
		for i in range(1,len(path)-1):
			polyline_id = path[i][0]
			order = path[i][2]
			if i == 1 and i == last_index:
				incoming_last_link = self.link_data.get_last_link(path[0][0], path[0][2])
				target_first_link = self.link_data.get_first_link(polyline_id, order)
				target_last_link = self.link_data.get_last_link(polyline_id, order)
				outgoing_first_link = self.link_data.get_first_link(path[-1][0], path[-1][2])
				diff_incoming_direction = link_util.normalize_direction(target_first_link[2]-incoming_last_link[2])
				diff_outgoing_direction = link_util.normalize_direction(outgoing_first_link[2]-target_last_link[2])
				if abs(diff_incoming_direction) < 20.0 or abs(diff_outgoing_direction) < 20.0:
					if abs(diff_incoming_direction)+5.0 < abs(diff_outgoing_direction):
						reference_id = path[0][0]
					else:
						reference_id = path[-1][0]
				else:
					reference_id = self.get_previous_reference_id(polyline_id, order)
			elif i == 1:
				incoming_last_link = self.link_data.get_last_link(path[0][0], path[0][2])
				target_first_link = self.link_data.get_first_link(polyline_id, order)
				diff_incoming_direction = link_util.normalize_direction(target_first_link[2]-incoming_last_link[2])
				if abs(diff_incoming_direction) < 20.0:
					reference_id = path[0][0]
				else:
					reference_id = self.get_previous_reference_id(polyline_id, order)
			elif i == last_index:
				target_last_link = self.link_data.get_last_link(polyline_id, order)
				outgoing_first_link = self.link_data.get_first_link(path[-1][0], path[-1][2])
				diff_outgoing_direction = link_util.normalize_direction(outgoing_first_link[2]-target_last_link[2])
				if abs(diff_outgoing_direction) < 20.0:
					reference_id = path[-1][0]
				else:
					reference_id = self.get_next_reference_id(polyline_id, order)
			elif i < center_count+1:
				reference_id = self.get_previous_reference_id(polyline_id, order)
			else:
				reference_id = self.get_next_reference_id(polyline_id, order)
			reference_lane = self.get_polyline_lane(reference_id)
			polyline_lane = self.get_polyline_lane(polyline_id)

			if reference_lane[0] == 0:
				reference_lane[0] = 1

			if path_lane > reference_lane[0] and polyline_id != 150:
				path_lane = reference_lane[0]

			if reference_lane[0] > polyline_lane[0]:
				path_lane_dict[polyline_id] = reference_lane
			else:
				path_lane_dict[polyline_id] = polyline_lane
		
		polyline_id = path[-1][0]
		polyline_lane = self.get_polyline_lane(polyline_id)
		path_lane_dict[polyline_id] = polyline_lane
		if path_lane > polyline_lane[0]:
			path_lane = polyline_lane[0]
		
		return path_lane, path_lane_dict

	def get_junction_lane_linkage(self, path, lane_count, incoming_lane_id, outgoing_lane_id, path_direction_variation):
		incoming_lane_count = len(incoming_lane_id)
		outgoing_lane_count = len(outgoing_lane_id)
		if self.link_data.road_dict[path[-1][0]]["is_highway"] != True:
			variation_type, connect_lane_index = self.get_junction_lane_index(path, path_direction_variation, incoming_lane_count, lane_count, outgoing_lane_count)
		else:
			variation_type, connect_lane_index = self.get_highway_junction_lane_index(path, path_direction_variation, incoming_lane_count, lane_count, outgoing_lane_count)
			
		lane_count = len(connect_lane_index)
		
		lane_linkage_list = []
		for lane_index in connect_lane_index:
			# lane_predecessor = incoming_lane_id[lane_index[0]]
			# lane_successor = outgoing_lane_id[lane_index[1]]
			if lane_index[0] > (len(incoming_lane_id)-1):
				lane_predecessor = incoming_lane_id[-1]
				print("ERROR: ",lane_index[0], incoming_lane_id)
			else:
				lane_predecessor = incoming_lane_id[lane_index[0]]

			if lane_index[1] > (len(outgoing_lane_id)-1):
				lane_successor = outgoing_lane_id[-1]
				print("ERROR: ",lane_index[1], outgoing_lane_id)
			else:
				lane_successor = outgoing_lane_id[lane_index[1]]
			lane_linkage_list.append([lane_predecessor, lane_successor,lane_index[2]])

		return lane_linkage_list

	def get_predecessor_lane_id(self, junction_id, polyline_id, left_lane_count, right_lane_count):
		start_jct, end_jct = self.link_data.get_junction_id(polyline_id[0])
		if start_jct == junction_id and polyline_id[1] == 0 :
			t_direction = -1
		elif end_jct == junction_id and polyline_id[1] == 1:
			t_direction = 1
		else:
			t_direction = 1

		lane_vector = np.array(list(range(1,1+left_lane_count)))
		lane_vector *= t_direction
		left_lane_id = list(lane_vector)

		lane_vector = np.array(list(range(1,1+right_lane_count)))
		lane_vector *= (-1*t_direction)
		right_lane_id = list(lane_vector)

		return left_lane_id, right_lane_id

	def get_succesor_lane_id(self, junction_id, polyline_id, left_lane_count, right_lane_count):
		start_jct, end_jct = self.link_data.get_junction_id(polyline_id[0])
		if start_jct == junction_id and polyline_id[1] == 0:
			t_direction = 1
		elif end_jct == junction_id and polyline_id[1] == 1:
			t_direction = -1
		else:
			t_direction = -1

		lane_vector = np.array(list(range(1,1+left_lane_count)))
		lane_vector *= t_direction
		left_lane_id = list(lane_vector)

		lane_vector = np.array(list(range(1,1+right_lane_count)))
		lane_vector *= (-1*t_direction)
		right_lane_id = list(lane_vector)

		return left_lane_id, right_lane_id
    
	def get_center_offset(self, polyline_lane):
		if polyline_lane[3] == 0:
			return 0.0
		else:
			diff_lane_count = polyline_lane[1] - polyline_lane[0]
			return polyline_lane[2]*diff_lane_count*0.5

	def get_junction_lane(self, junction_id, from_polyline, to_polyline, path, path_direction_variation,flag_branch,flag_merge):
		path_lane_count, path_lane_dict = self.get_path_lane(path)

		if from_polyline[0] in path_lane_dict.keys():
			predecessor_lane = path_lane_dict[from_polyline[0]]
		else:
			predecessor_lane = self.get_polyline_lane(from_polyline[0])

		if to_polyline[0] in path_lane_dict.keys():
			successor_lane = path_lane_dict[to_polyline[0]]
		else:
			successor_lane = self.get_polyline_lane(to_polyline[0])

		predecessor_left_id, predecessor_right_id = self.get_predecessor_lane_id(junction_id, from_polyline,predecessor_lane[0], predecessor_lane[1])
		successor_left_id, successor_right_id = self.get_succesor_lane_id(junction_id, to_polyline, successor_lane[0], successor_lane[1])

		lane_count = predecessor_lane[0]
		if lane_count > successor_lane[0]:
			lane_count = successor_lane[0]

		lane_linkage_list = self.get_junction_lane_linkage(path, lane_count, predecessor_left_id, successor_left_id, path_direction_variation)
		if lane_count > len(lane_linkage_list):
			lane_count = len(lane_linkage_list)

		if self.lane_shift:
			incoming_center_offset = self.get_center_offset(predecessor_lane)
			outgoing_center_offset = self.get_center_offset(successor_lane)
		else:
			incoming_center_offset = 0.0
			outgoing_center_offset = 0.0

		if flag_branch == 1:
			outgoing_center_offset = outgoing_center_offset * 2
		elif flag_branch == 0:
			outgoing_center_offset = 0.0

		if flag_merge == 1:
			incoming_center_offset = incoming_center_offset * 2
		elif flag_merge == 0:
			incoming_center_offset = 0.0

		if self.junction_lane_shift:
			diff_incoming_lane_count = abs(lane_linkage_list[0][0]) - 1
			diff_outgoing_lane_count = abs(lane_linkage_list[0][1]) - 1
			incoming_lane_offset = (diff_incoming_lane_count)*predecessor_lane[2]
			outgoing_lane_offset = (diff_outgoing_lane_count)*successor_lane[2]
		else:
			incoming_lane_offset = 0.0
			outgoing_lane_offset = 0.0

		point_offset = [[incoming_center_offset, outgoing_center_offset], [incoming_lane_offset, outgoing_lane_offset]]
		junction_lane = [lane_count, [predecessor_lane[2], successor_lane[2]], lane_linkage_list]

		return point_offset, junction_lane, path_lane_dict

	def get_junction_lane_parameter(self, target_index):
		lane_count = self.junction.df.at[target_index, "lane_count"]
		lane_linkage_list = self.junction.df.at[target_index, "lane_linkage"]
		lane_width = self.junction.df.at[target_index, "lane_width"]
		road_length = self.junction.df.at[target_index, "road_length"]
		
		lane_offset = [0.0, 0.0, 0.0, 0.0, 0.0]
		
		s_offset = 0
		a,b,c,d = self.get_lane_width_parameter(lane_width[0], lane_width[1], road_length)
		lane_width_parameter = [s_offset, a, b, c, d]
		lane_type ="driving"
		lane_level = "false"
		
		left_lane = []
		for lane_linkage in lane_linkage_list:
			if lane_linkage[2] == "constant":
				test_lane = [lane_type, lane_level, lane_width_parameter, [lane_linkage[0],lane_linkage[1]]]
			elif lane_linkage[2] == "decrease":
				s_offset = 0
				a,b,c,d = self.get_lane_width_parameter(lane_width[0], 0.0, road_length)
				lane_width_decrease = [s_offset, a, b, c, d]
				test_lane = [lane_type, lane_level, lane_width_decrease, [lane_linkage[0],lane_linkage[1]]]
			else:
				s_offset = 0
				a,b,c,d = self.get_lane_width_parameter(0.0, lane_width[1], road_length)
				lane_width_increase = [s_offset, a, b, c, d]
				test_lane = [lane_type, lane_level, lane_width_increase, [lane_linkage[0],lane_linkage[1]]]
				
			left_lane.append(test_lane)
		
		right_lane = []
		return lane_offset, left_lane, right_lane
		
	def get_junction_elevation(self,junction_id, from_polyline, to_polyline):
		from_elevation = self.road_elevation_dict[from_polyline[0]]
		start_jct, end_jct = self.link_data.get_junction_id(from_polyline[0])
		if start_jct == junction_id and from_polyline[1] == 0:
			from_part_rate = [0.0, from_elevation[1][0]]
			from_szlist = elevation_util.get_elevation_part(from_elevation[0], from_part_rate[0], from_part_rate[1])
			from_szlist = self.link_data.get_inverse_elevation(from_szlist)
		elif end_jct == junction_id and from_polyline[1] == 1:
			from_part_rate = [from_elevation[1][1], 1.0]
			from_szlist = elevation_util.get_elevation_part(from_elevation[0], from_part_rate[0], from_part_rate[1])
		else:
			pass
		
		from_junction = []
		for sz in from_szlist:
			from_junction.append([abs(sz[0]-from_szlist[0][0]), sz[1]])
		
		to_elevation = self.road_elevation_dict[to_polyline[0]]
		start_jct, end_jct = self.link_data.get_junction_id(to_polyline[0])
		if start_jct == junction_id and to_polyline[1] == 0:
			to_part_rate = [0.0, to_elevation[1][0]]
			to_szlist = elevation_util.get_elevation_part(to_elevation[0], to_part_rate[0], to_part_rate[1])
		elif end_jct == junction_id and to_polyline[1] == 1:
			to_part_rate = [to_elevation[1][1],1.0]
			to_szlist = elevation_util.get_elevation_part(to_elevation[0], to_part_rate[0], to_part_rate[1])
			to_szlist = self.link_data.get_inverse_elevation(to_szlist)
		else:
			pass
			
		to_junction = []
		for sz in to_szlist:
			to_junction.append([abs(sz[0]-to_szlist[0][0])+from_junction[-1][0], sz[1]])
			
		junction_elevation = from_junction
		junction_elevation.extend(to_junction)
		
		return junction_elevation
		
	def get_junction_elevation_parameter(self, target_index):
		junction_id = self.junction.df.at[target_index, "junction_id"]
		from_polyline = self.junction.df.at[target_index, "from_polyline"]
		to_polyline = self.junction.df.at[target_index, "to_polyline"]
		road_length = self.junction.df.at[target_index, "road_length"]
		
		road_szlist = self.get_junction_elevation(junction_id,from_polyline, to_polyline)
		a,b,c,d = parametric_cubic.get_curve(road_szlist)
		return [0,a[1],b[1]/(road_length),c[1]/(road_length**2),d[1]/(road_length**3)]
		
	def get_junction_road_xml(self):
		road_part_str = ""

		self.ng_data_list = []
		self.junction_road_dict = dict()
		self.junction_road_element_no = self.next_element_no
		print("Generates an XML string for the junction road of parts.")
		for target_index in tqdm(range(0, self.junction.df.shape[0])):
			predecessor, succesor = self.get_junction_linked_element(target_index)
			road_no = self.junction_road_element_no + target_index
			junction_id = self.junction.df.at[target_index, "junction_id"]
			junction_no = self.junction_dict[junction_id]
			lane_offset, left_lane, right_lane = self.get_junction_lane_parameter(target_index)
			speed = self.junction.df.at[target_index, "speed"]
			if speed is None:
				speed = []
			elevation_list = []
			if self.use_elevation:
				elevation = self.get_junction_elevation_parameter(target_index)
				elevation_list.append(elevation)
			else:
				elevation = [0,0,0,0,0]
				elevation_list.append(elevation)
			road_str, ng_data = open_drive_format.convert_road_part(self.junction.df.at[target_index,"df"], road_no, junction_no, predecessor, succesor, lane_offset, left_lane, right_lane, elevation_list, speed)
			road_part_str += road_str
			if not junction_no in self.junction_road_dict.keys():
				self.junction_road_dict[junction_no] = []
			self.junction_road_dict[junction_no].append([road_no, [predecessor,succesor], [lane_offset, left_lane, right_lane]])
			self.ng_data_list.extend(ng_data)
		return road_part_str

	def convert_junction(self):
		self.set_junction_data()
		self.junction.convert()
		
	def get_junction_xml(self):
		junction_str = ""
		print("Generates an XML string for the junction of parts.")
		for junction_no in tqdm(self.junction_road_dict.keys()):
			junction_str += open_drive_format.convert_junction_part(junction_no, self.junction_road_dict[junction_no])
		return junction_str

	def _build_geo_reference(self):
		"""Create PROJ string for geoReference header entry if origin is available."""
		try:
			lat = float(self.origin_point[0])
			lon = float(self.origin_point[1])
		except Exception:
			return None

		return (
			"+proj=tmerc "
			f"+lat_0={lat:.8f} "
			f"+lon_0={lon:.8f} "
			"+k=1 +x_0=0 +y_0=0 +datum=JGD2011 +units=m +no_defs"
		)

	def output_xml(self, file_path):
		road_part_str = self.get_road_part_xml()
		junction_road_str = self.get_junction_road_xml()
		junction_str = self.get_junction_xml()
		open_drive_str = road_part_str + junction_road_str + junction_str
		geo_reference = self._build_geo_reference()
		open_drive_format.output_xml(open_drive_str, file_path, geo_reference)
		
	def get_junction_path_df(self, junction_path ):
		point_df = pd.DataFrame(junction_path)
		point_df.columns = ["x","y","length"]
		return self.road.get_opendrive(point_df)
		
	def get_path_junction_point(self, path_df):
	
		x = path_df.at[0,"x"]
		y = path_df.at[0,"y"]
		direction = path_df.at[0,"initial_direction"]
		direction += 180
		if direction > 180:
			direction -= 360
		from_node_point = [[x,y],direction,0.0]

		point_size = len(path_df["x"])
		x = path_df.at[point_size-1,"x"]
		y = path_df.at[point_size-1,"y"]
		direction = path_df.at[point_size-1,"initial_direction"]
		to_node_point = [[x,y],direction,0.0]

		return from_node_point, to_node_point
		
	def check_uturn(self, from_polyline, to_polyline, junction_point):
		result = False
		diff_incoming_direction = link_util.normalize_direction(junction_point[0][1] - junction_point[1][1])
		is_uturn_direction_variation = abs(diff_incoming_direction) < 20.0
		if is_uturn_direction_variation:
			normal_link = link_util.get_link(junction_point[0][0], junction_point[0][1]-90.0, 10.0)
			outgoing_link = link_util.get_link(junction_point[1][0], junction_point[1][1], 10.0)
			exist_intersection, opposite_x, opposite_y = link_util.get_intersection(normal_link, outgoing_link)
			if exist_intersection:
				diff_x = normal_link[0][0] - opposite_x
				diff_y = normal_link[0][1] - opposite_y
				point_distance = math.sqrt(diff_x**2 + diff_y**2)
				from_road_width = self.link_data.road_dict[from_polyline[0]]["width"]
				to_road_width = self.link_data.road_dict[to_polyline[0]]["width"]
				distance_threshold = (from_road_width+to_road_width)
				result = (point_distance < distance_threshold)
		return result
		
	def get_path_direction_variation(self, path):
		last_variation = 0.0
		first_variation = 0.0
		path_direction_variation = dict()

		incoming_link = self.link_data.get_last_link(path[0][0], path[0][2])
		outgoing_link = self.link_data.get_first_link(path[-1][0], path[-1][2])
		total_variation = link_util.normalize_direction(outgoing_link[2] - incoming_link[2])

		valid_variation_count = 0
		for i in range(1, len(path)-1):
			previous_link = self.link_data.get_last_link(path[i-1][0], path[i-1][2])
			target_first_link = self.link_data.get_first_link(path[i][0], path[i][2])
			target_last_link = self.link_data.get_last_link(path[i][0], path[i][2])
			next_link = self.link_data.get_first_link(path[i+1][0], path[i+1][2])

			polyline_id = path[i][0]
			from_direction_variation = link_util.normalize_direction(target_first_link[2]-previous_link[2])
			to_direction_variation = link_util.normalize_direction(next_link[2]-target_last_link[2])

			is_from_valid = False
			is_to_valid = False

			if abs(math.sin(np.deg2rad(from_direction_variation))) > 0.3:
				is_from_valid = True
			if abs(math.sin(np.deg2rad(to_direction_variation))) > 0.3:
				is_to_valid = True

			path_direction_variation[polyline_id] = [from_direction_variation, to_direction_variation, is_from_valid, is_to_valid]

			if is_from_valid:
				if valid_variation_count == 0:
					first_variation = from_direction_variation
				
				valid_variation_count += 1
				if is_to_valid:
					last_variation = 0.0
				else:
					last_variation = from_direction_variation
					
			last_variation += to_direction_variation
		
		if valid_variation_count == 0:
			first_variation = last_variation
		
		return [total_variation, [first_variation, last_variation], valid_variation_count, path_direction_variation]

	def get_path_width(self, polyline_id, path_lane_dict):
		exist_data = False
		if polyline_id in path_lane_dict.keys():
			exist_data = True
			target_path_lane = path_lane_dict[polyline_id]
			left_lane_count = target_path_lane[0]
			right_lane_count = target_path_lane[1]
			lane_width = target_path_lane[2]
			oneway_code = target_path_lane[3]
			lane_count = left_lane_count;
			width = lane_width * lane_count
		return exist_data, width
		
	def get_path_center_offset(self, path, path_lane, point_offset, path_direction_variation):
		path_offset_dict = dict()

		incoming_polyline_id = path[0][0]
		path_offset_dict[incoming_polyline_id] = point_offset[0][0]

		for i in range(1, len(path)-1):
			polyline_node = path[i]
			polyline_id = polyline_node[0]
			order = polyline_node[2]
			exist_width, current_width = self.get_path_width(polyline_id, path_lane)          

			if exist_width:
				width = current_width
				target_path_lane = path_lane[polyline_id]
				oneway_code = target_path_lane[3]
			else:
				target_link = self.link_data.get_target(polyline_id)
				oneway_code = int(target_link["oneway_code"])
				left_lane_count, right_lane_count = self.link_data.get_lane_count(polyline_id, oneway_code)
				lane_count = left_lane_count;
				lane_width = self.link_data.get_lane_width(self.link_data.get_road_width(polyline_id), left_lane_count+right_lane_count)
				width = lane_count*lane_width            

			if polyline_id in path_direction_variation[3].keys():
				is_valid_from = path_direction_variation[3][polyline_id][2]
				is_valid_end = path_direction_variation[3][polyline_id][3]
				if is_valid_from == False and is_valid_end == False:
					previous_node = path[i-1]
					previous_id = previous_node[0]
					exist_previous, previous_width = self.get_path_width(previous_id, path_lane)
					if exist_previous == False:
						previous_width = width
					next_node = path[i+1]
					next_id = next_node[0]
					exist_next, next_width = self.get_path_width(next_id, path_lane)
					if exist_next == False:
						next_width = width
					width = (previous_width+next_width)*0.5                

			if order == 1:
				if oneway_code == 1:
					t_shift = (1.0*width*0.5)
				elif oneway_code == 2:
					t_shift = (-1.0*width*0.5)
				else:
					t_shift = 0.0
			else:
				if oneway_code == 1:
					t_shift = (-1.0*width*0.5)
				elif oneway_code == 2:
					t_shift = (1.0*width*0.5)
				else:
					t_shift = 0.0

			path_offset_dict[polyline_id] = t_shift 

		outgoing_polyline_id = path[-1][0]
		path_offset_dict[outgoing_polyline_id] = point_offset[0][1]

		return path_offset_dict  

	def get_path_lane_offset(self, junction_lane_count, path, path_lane_dict, path_direction_variation, initial_offset, end_offset):
	
		total_variation = path_direction_variation[0]
		first_variation = path_direction_variation[1][0]
		last_variation = path_direction_variation[1][1]
		lane_changeable_count = path_direction_variation[2]
		variation_dict = path_direction_variation[3]

		last_polyline_id = path[-2][0]
		outgoing_polyline_id = path[-1][0]
		if last_polyline_id in variation_dict.keys():
			direction_variation = variation_dict[last_polyline_id]
			if direction_variation[3]:
				change_outgoing_lane = True
			else:
				change_outgoing_lane = False
		else:
			incoming_link = self.link_data.get_last_link(path[0][0], path[0][2])
			outgoing_link = self.link_data.get_first_link(path[-1][0], path[-1][2])
			direction_variation = link_util.normalize_direction(outgoing_link[2]-incoming_link[2])
			if abs(math.sin(np.deg2rad(direction_variation))) > 0.3:
				change_outgoing_lane = True
			else:
				change_outgoing_lane = False
				
		path_lane_offset = dict()
		if lane_changeable_count == 0 and change_outgoing_lane == False:
			path_lane_offset[path[0][0]] = initial_offset
			previous_offset = (initial_offset + end_offset)*0.5
			change_outgoing_lane = True
			incoming_link = self.link_data.get_last_link(path[0][0], path[0][2])
			outgoing_link = self.link_data.get_first_link(path[-1][0], path[-1][2])
			incoming_point = incoming_link[1]
			outgoing_point = outgoing_link[0]
			
		else:
			path_lane_offset[path[0][0]] = initial_offset
			previous_offset = initial_offset
		
		change_offset_count = 0
		for i in range(1, len(path)-1):
			polyline_id = path[i][0]
			if polyline_id in path_lane_dict.keys() and polyline_id in variation_dict.keys():
				direction_variation = variation_dict[polyline_id]
				if direction_variation[2] == False:
					path_lane_offset[polyline_id] = previous_offset
				else:
					change_offset_count += 1
					if change_offset_count == lane_changeable_count: 
						if change_outgoing_lane == False:
							path_lane_offset[polyline_id] = end_offset
							previous_offset = end_offset
						else:
							lane_count = path_lane_dict[polyline_id][0]
							if last_variation < 0.0:
								path_lane_offset[polyline_id] = 0.0
								previous_offset = 0.0
							else:
								path_lane_offset[polyline_id] = 3.0*(lane_count - junction_lane_count)
								previous_offset = 3.0*(lane_count - junction_lane_count)
					else:
						if direction_variation[1] < 0.0:
							path_lane_offset[polyline_id] = 0.0
							previous_offset = 0.0
						else:
							lane_count = path_lane_dict[polyline_id][0]
							path_lane_offset[polyline_id] = 3.0*(lane_count - junction_lane_count)
							previous_offset = 3.0*(lane_count - junction_lane_count)
			else:
				path_lane_offset[polyline_id] = previous_offset
		  
		if change_outgoing_lane:
			path_lane_offset[outgoing_polyline_id] = end_offset
		else:
			path_lane_offset[outgoing_polyline_id] = previous_offset
		
		return path_lane_offset
		
	def get_path_polyline(self, path, path_offset_dict):

		path_polyline = []
		shifted_path_polyline = []
		shift_polyline_count = 0
		previous_shift = 0.0;
		for i in range(0, len(path)):
			polyline_node = path[i]
			polyline_id = polyline_node[0]
			order = polyline_node[2]
			
			if polyline_id in path_offset_dict.keys():
				t_shift = path_offset_dict[polyline_id]
				previous_shift = t_shift
			else:
				t_shift = previous_shift
			
			target_link = self.link_data.get_target(polyline_id)
			target_xy = target_link["xy"]
			xy_list = target_xy.to_list()[0]
			if abs(t_shift) > 0.1:
				shift_polyline_count += 1
			
			if order == 1:
				shift_xy = polyline_point_util.shift(xy_list, (-1.0*t_shift))
				path_polyline.append(polyline_point_util.inverse(xy_list))
				shifted_path_polyline.append(polyline_point_util.inverse(shift_xy))
			else:
				shift_xy = polyline_point_util.shift(xy_list, t_shift)    
				path_polyline.append(xy_list)
				shifted_path_polyline.append(shift_xy)
			
		return shift_polyline_count, path_polyline, shifted_path_polyline
    
	def get_path_scale(self, polyline_list, intersection_point_list):

		if len(polyline_list) < len(intersection_point_list):
			scale_count = len(polyline_list)
		else:
			scale_count = len(intersection_point_list)
			
		scale_list = []
		for i in range(0, scale_count):
			target_polyline = polyline_list[i]
			start_end_point = intersection_point_list[i]
			
			polyline_diff_x = target_polyline[-1][0] - target_polyline[0][0]
			polyline_diff_y = target_polyline[-1][1] - target_polyline[0][1]
			
			diff_x = start_end_point[1][0] - start_end_point[0][0]
			diff_y = start_end_point[1][1] - start_end_point[0][1]
			
			scale_list.append(math.sqrt(diff_x**2+diff_y**2)/math.sqrt(polyline_diff_x**2+polyline_diff_y**2))
			
		return scale_list
		
	def get_polyline_node_point_list(self, polyline_list):
		point_list = []
		start_node_point = polyline_list[0][0]

		for i in range(0, len(polyline_list)-1):
			from_polyline = polyline_list[i]
			to_polyline = polyline_list[i+1]

			from_link = link_util.node2link(from_polyline[-2], from_polyline[-1])
			to_link = link_util.node2link(to_polyline[0], to_polyline[1])
			diff_direction = abs(link_util.normalize_direction(to_link[2] - from_link[2]))

			if diff_direction > 20.0:
				find, index, point_distance, intersection_point = polyline_point_util.get_intersection_point(from_link, to_polyline)
				if find:
					point_list.append([start_node_point, intersection_point])
					start_node_point = intersection_point
				else:
					if i == 0:
						next_node_point = from_link[1] #link_util.get_midpoint(to_link[0], from_link[1])
					elif i == len(polyline_list)-2:
						next_node_point = to_link[0]
					else:
						next_node_point = link_util.get_midpoint(to_link[0], from_link[1]) #from_link[1]
					point_list.append([start_node_point, next_node_point])
					start_node_point = next_node_point

			else:
				if i == 0:
					next_node_point = from_link[1]
				elif i == len(polyline_list)-2:
					next_node_point = to_link[0]
				else:
					next_node_point = from_link[1]
					next_node_point = link_util.get_midpoint(to_link[0], from_link[1]) #from_link[1]
				point_list.append([start_node_point, next_node_point])
				start_node_point = next_node_point

		point_list.append([start_node_point, polyline_list[-1][-1]])

		return point_list

	def get_intersection_range(self, path_polyline ):
		incoming_polyline = path_polyline[0]
		outgoing_polyline = path_polyline[-1]
		incoming_link = link_util.node2link(incoming_polyline[-2], incoming_polyline[-1])
		outgoing_link = link_util.node2link(outgoing_polyline[0], outgoing_polyline[1])
		first_polyline = path_polyline[1]
		first_link = link_util.node2link(first_polyline[0], first_polyline[1])
		last_polyline = path_polyline[-2]
		last_link = link_util.node2link(last_polyline[-2], last_polyline[-1])
		diff_first_direction = link_util.normalize_direction(first_link[2] - incoming_link[2])
		
		if abs(diff_first_direction) < 20.0 and len(path_polyline) > 2:
			length_first_polyline = polyline_point_util.get_length(first_polyline)
			if length_first_polyline < 3.5*3.0:
				start_index = 2
			else:
				start_index = 1
		else:
			start_index = 1
		
		diff_outgoing_direction = link_util.normalize_direction(outgoing_link[2] - last_link[2])
		if abs(diff_outgoing_direction) < 20.0 and len(path_polyline) > 3:
			length_last_polyline = polyline_point_util.get_length(last_polyline)
			if length_last_polyline < 3.5*3.0:
				end_index = len(path_polyline)-3
			else:
				end_index = len(path_polyline)-2
		else:
			end_index = len(path_polyline)-2
		
		return [start_index, end_index]
		
	def get_delete_distance(self, path, path_polyline, intersection_range):
		incoming_polyline = path_polyline[0]
		outgoing_polyline = path_polyline[-1]
		incoming_link = link_util.node2link(incoming_polyline[-2], incoming_polyline[-1])
		outgoing_link = link_util.node2link(outgoing_polyline[0], outgoing_polyline[1])
		
		first_polyline = path_polyline[intersection_range[0]]
		first_link = link_util.node2link(first_polyline[0], first_polyline[1])
		
		last_polyline = path_polyline[intersection_range[1]]
		last_link = link_util.node2link(last_polyline[-2], last_polyline[-1])
		
		first_direction_variation = link_util.normalize_direction(first_link[2] - incoming_link[2])
		last_direction_variation = link_util.normalize_direction(outgoing_link[2] - last_link[2])
		
		incoming_road_width = self.link_data.get_left_side_road_width(path[0][0])+5.0
		outgoing_road_width = self.link_data.get_left_side_road_width(path[-1][0])+5.0
		
		start_delete_distance, max_start_delete_distance = self.calculate_delete_distance(incoming_road_width, first_direction_variation)
		end_delete_distance, max_end_delete_distance = self.calculate_delete_distance(outgoing_road_width, last_direction_variation)
		
		if intersection_range[0] == 1 and len(first_polyline) > 1:
			first_polyline_link = []
			for i in range(0, len(first_polyline)-1):
				link = link_util.node2link(first_polyline[i], first_polyline[i+1])
				first_polyline_link.append(link)
			
			first_polyline_direction_variation = 0.0
			for i in range(0, len(first_polyline_link)-1):
				diff_direction = link_util.normalize_direction(first_polyline_link[i+1][2] - first_polyline_link[i][2])
				first_polyline_direction_variation += diff_direction
				
			if abs(first_polyline_direction_variation) > 10.0:
				delete_link_length = 0.0
				for i in range( 0, len(first_polyline_link)):
					link = first_polyline_link[i]
					diff_direction = link_util.normalize_direction(link[2]-incoming_link[2])
					if abs(diff_direction) < 10.0:
						link_length = link_util.get_distance(link[0],link[1])
						if delete_link_length+link_length < 3.5*2.5*100.0:
							delete_link_length += link_length
						else:
							delete_link_length = 3.5*2.5*100.0
							break
					else:
						if i != 0:
							delete_link_length += link_util.get_distance(link[0],link[1])*0.3
						break
				start_delete_distance += delete_link_length
				
		last_polyline_link = []
		for i in range(0, len(last_polyline)-1):
			link = link_util.node2link(last_polyline[i], last_polyline[i+1])
			last_polyline_link.append(link)
		
		last_polyline_direction_variation = 0.0
		for i in range(0, len(last_polyline_link)-1):
			diff_direction = link_util.normalize_direction(last_polyline_link[i+1][2] - last_polyline_link[i][2])
			last_polyline_direction_variation += diff_direction
		if abs(last_polyline_direction_variation) > 10.0:
			if intersection_range[1] == len(path_polyline)-2 and len(last_polyline) > 1:
				delete_link_length = 0.0
				last_index = len(last_polyline_link)-1
				for i in range( 0, len(last_polyline_link)):
					target_index = last_index - i
					link = last_polyline_link[target_index]
					diff_direction = link_util.normalize_direction(link[2]-outgoing_link[2])
					if abs(diff_direction) < 10.0:
						link_length = link_util.get_distance(link[0],link[1])
						if delete_link_length+link_length < 3.5*2.5:
							delete_link_length += link_length
						else:
							delete_link_length = 3.5*2.5
							break
					else:
						if i != 0:
							delete_link_length += link_util.get_distance(link[0],link[1])*0.3
						break
				end_delete_distance += delete_link_length
				
		if start_delete_distance < 2.0:
			start_delete_distance = 2.0
		if max_start_delete_distance < start_delete_distance:
			max_start_delete_distance = start_delete_distance
				
		if end_delete_distance < 2.0:
			end_delete_distance = 2.0
		if max_end_delete_distance < end_delete_distance:
			max_end_delete_distance = end_delete_distance
		
		diff_start_delete_distance = max_start_delete_distance - start_delete_distance
		diff_end_delete_distance = max_end_delete_distance - end_delete_distance
		
		if intersection_range[0] == intersection_range[1]:
			polyline_length = polyline_point_util.get_length(first_polyline)
			remain_length = polyline_length - (start_delete_distance+end_delete_distance)
			if remain_length > diff_start_delete_distance+diff_end_delete_distance+1.0:
				start_delete_distance += diff_start_delete_distance
				end_delete_distance += diff_end_delete_distance
			elif remain_length > 2.0:
				start_delete_distance += (remain_length-1.0)*(diff_start_delete_distance/(diff_start_delete_distance+diff_end_delete_distance))
				end_delete_distance += (remain_length-1.0)*(diff_end_delete_distance/(diff_start_delete_distance+diff_end_delete_distance))
		else:
			first_polyline_length = polyline_point_util.get_length(first_polyline)
			last_polyline_length = polyline_point_util.get_length(last_polyline)
			remain_start_length = first_polyline_length - start_delete_distance
			remain_last_length = last_polyline_length - end_delete_distance
			if  remain_start_length > diff_start_delete_distance+1.0:
				start_delete_distance += diff_start_delete_distance
			elif remain_start_length > 2.0:
				start_delete_distance += (remain_start_length - 1.0)
			if  remain_last_length > diff_end_delete_distance+1.0:
				end_delete_distance += diff_end_delete_distance
			elif remain_last_length > 2.0:
				end_delete_distance += (remain_last_length - 1.0)
		
		return [start_delete_distance, end_delete_distance]
		
	def calculate_delete_distance(self, road_width, direction_variation):
		radian_diff = abs(np.deg2rad(direction_variation))
		if radian_diff > math.pi*0.5:
			min_distance = 2.0*math.sin(radian_diff) - 2.0/math.tan(radian_diff)
			max_distance = road_width*math.sin(radian_diff) - road_width/math.tan(radian_diff)
		else:
			min_distance = 2.0*math.sin(radian_diff)
			max_distance = road_width*math.sin(radian_diff)
		return min_distance, max_distance
		
	def trimming_path(self, path, path_polyline, incoming_direction, outgoing_direction):
		intersection_start_index = 1
		first_polyline = path_polyline[1]
		first_link = link_util.node2link(first_polyline[0], first_polyline[1])
		last_polyline = path_polyline[-2]
		last_link = link_util.node2link(last_polyline[-2], last_polyline[-1])

		diff_incoming_direction = link_util.normalize_direction(first_link[2] - incoming_direction)
		if abs(diff_incoming_direction) < 20.0 and len(path_polyline) > 3:
			length_first_polyline = polyline_point_util.get_length(first_polyline)
			if length_first_polyline < 3.5*2.5:
				intersection_start_index = 2
			else:
				intersection_start_index = 1
		else:
			intersection_start_index = 1

		diff_outgoing_direction = link_util.normalize_direction(outgoing_direction - last_link[2])

		if abs(diff_outgoing_direction) < 20.0 and len(path_polyline) > 3:
			length_last_polyline = polyline_point_util.get_length(last_polyline)
			if length_last_polyline < 3.5*3.0:
				intersection_end_index = len(path_polyline)-3
			else:
				intersection_end_index = len(path_polyline)-2
		else:
			intersection_end_index = len(path_polyline)-2

		intersection_range = [intersection_start_index, intersection_end_index]

		start_polyline = path_polyline[intersection_start_index]
		start_link = link_util.node2link(start_polyline[0], start_polyline[1])

		end_polyline = path_polyline[intersection_end_index]
		end_link = link_util.node2link(end_polyline[-2], end_polyline[-1])

		junction_direction_variation = abs(link_util.normalize_direction(outgoing_direction - incoming_direction))
		start_direction_variation = link_util.normalize_direction(start_link[2] - incoming_direction)
		end_direction_variation = link_util.normalize_direction(outgoing_direction - end_link[2])

		incoming_road_width = self.link_data.get_left_side_road_width(path[0][0])+5.0
		start_delete_distance, max_start_delete_distance = self.calculate_delete_distance(incoming_road_width, start_direction_variation)
		first_polyline_length = polyline_point_util.get_length(start_polyline)
			
		if intersection_start_index == 1 and len(start_polyline) > 1:
		
			start_polyline_link = []
			for i in range(0, len(start_polyline)-1):
				link = link_util.node2link(start_polyline[i], start_polyline[i+1])
				start_polyline_link.append(link)
			
			start_polyline_direction_variation = 0.0
			for i in range(0, len(start_polyline_link)-1):
				diff_direction = link_util.normalize_direction(start_polyline_link[i+1][2] - start_polyline_link[i][2])
				start_polyline_direction_variation += diff_direction
				
			if abs(start_polyline_direction_variation) > 10.0:
				delete_link_length = 0.0
				for i in range( 0, len(start_polyline)-1):
					link = link_util.node2link(start_polyline[i], start_polyline[i+1])
					diff_direction = link_util.normalize_direction(link[2]-incoming_direction)
					if abs(diff_direction) < 10.0:
						link_length = link_util.get_distance(link[0],link[1])
						if delete_link_length+link_length < 3.5*2.5*100.0:
							delete_link_length += link_length
						else:
							delete_link_length = 3.5*2.5*100.0
							break
					else:
						if i != 0:
							delete_link_length += link_util.get_distance(link[0],link[1])*0.3
						break
				start_delete_distance += delete_link_length
		    
		if start_delete_distance < 2.0:
			start_delete_distance = 2.0
			if max_start_delete_distance < start_delete_distance:
				max_start_delete_distance = 2.0
		
		outgoing_road_width = self.link_data.get_left_side_road_width(path[-1][0])+5.0
		last_polyline_length = polyline_point_util.get_length(end_polyline)
		end_delete_distance, max_end_delete_distance = self.calculate_delete_distance(outgoing_road_width, end_direction_variation)
		end_polyline_link = []
		for i in range(0, len(end_polyline)-1):
			link = link_util.node2link(end_polyline[i], end_polyline[i+1])
			end_polyline_link.append(link)
		
		end_polyline_direction_variation = 0.0
		for i in range(0, len(end_polyline_link)-1):
			diff_direction = link_util.normalize_direction(end_polyline_link[i+1][2] - end_polyline_link[i][2])
			end_polyline_direction_variation += diff_direction
			
		if abs(end_polyline_direction_variation) > 10.0:
			if intersection_end_index == len(path_polyline)-2 and len(end_polyline) > 1:
				delete_link_length = 0.0
				for i in range( 0, len(end_polyline)-1):
					target_index = len(end_polyline)-(i+2)
					link = link_util.node2link(end_polyline[target_index], end_polyline[target_index+1])
					diff_direction = link_util.normalize_direction(link[2]-outgoing_direction)
					if abs(diff_direction) < 10.0:
						link_length = link_util.get_distance(link[0],link[1])
						if delete_link_length+link_length < 3.5*2.5:
							delete_link_length += link_length
						else:
							delete_link_length = 3.5*2.5
							break
					else:
						if i != 0:
							delete_link_length += link_util.get_distance(link[0],link[1])*0.3
						break
				end_delete_distance += delete_link_length
		    
		if end_delete_distance < 2.0:
			end_delete_distance = 2.0
			if max_end_delete_distance < end_delete_distance:
				max_end_delete_distance = 2.0

		diff_start_delete_distance = max_start_delete_distance - start_delete_distance
		diff_end_delete_distance = max_end_delete_distance - end_delete_distance
		if intersection_end_index == intersection_start_index:
			remain_length = first_polyline_length - (start_delete_distance+end_delete_distance)
			if remain_length > diff_start_delete_distance+diff_end_delete_distance+1.0:
				start_delete_distance += diff_start_delete_distance
				end_delete_distance += diff_end_delete_distance
			elif remain_length > 2.0:
				start_delete_distance += (remain_length-1.0)*(diff_start_delete_distance/(diff_start_delete_distance+diff_end_delete_distance))
				end_delete_distance += (remain_length-1.0)*(diff_end_delete_distance/(diff_start_delete_distance+diff_end_delete_distance))
			remain_length = first_polyline_length - (start_delete_distance+end_delete_distance)
		else:
			remain_start_length = first_polyline_length - start_delete_distance
			remain_last_length = last_polyline_length - end_delete_distance
			if  remain_start_length > diff_start_delete_distance+1.0:
				start_delete_distance += diff_start_delete_distance
			elif remain_start_length > 2.0:
				start_delete_distance += (remain_start_length - 1.0)
			if  remain_last_length > diff_end_delete_distance+1.0:
				end_delete_distance += diff_end_delete_distance
			elif remain_last_length > 2.0:
				end_delete_distance += (remain_last_length - 1.0)
		
		
		delete_length = [start_delete_distance, end_delete_distance]

		return intersection_range, delete_length 
		
	def get_sampling_path_point(self, path_point, delete_distance):
		sampling_interval = 0.1
		restruction_path_point = self.sampling(self.restruction_point(path_point, sampling_interval),sampling_interval*0.1)

		start_delete_count = int(delete_distance[0]/sampling_interval)
		end_delete_count = int(delete_distance[1]/sampling_interval)

		if (len(restruction_path_point) < start_delete_count+end_delete_count+2):
			start_delete_count = start_delete_count - 1
			end_delete_count = end_delete_count - 1
			
		target_point_list = []
		for i in range(start_delete_count, len(restruction_path_point)-end_delete_count):
			target_point_list.append(restruction_path_point[i])
		sampling_path_point = self.sampling(target_point_list, 3.5)
		return sampling_path_point
		
	def get_path_polyline_point(self, path, path_offset):
		shift_polyline_count, path_polyline, shifted_path_polyline = self.get_path_polyline(path, path_offset)
		
		node_point_list = self.get_polyline_node_point_list(shifted_path_polyline)
		
		if shift_polyline_count > 0:
			result_path_polyline = []
			for i in range(0, len(shifted_path_polyline)):
				result_path_polyline.append(polyline_point_util.reconstruction(shifted_path_polyline[i], node_point_list[i]))
		else:
			result_path_polyline = path_polyline
		
		polyline_range = self.get_intersection_range(path_polyline)
		delete_distance = self.get_delete_distance(path, result_path_polyline, polyline_range)
		
		shift = [0.0, 0.0]
		if self.lane_shift:
			path_point = polyline_point_util.get_point_list(result_path_polyline, polyline_range, shift)
		else:
			path_point = polyline_point_util.get_point_list(path_polyline, polyline_range, shift)

		total_polyline_length = 0.0
		for i in range(0, len(path_point)-1):
			total_polyline_length += link_util.get_distance(path_point[i], path_point[i+1])
			
		polyline_count = polyline_range[1]-polyline_range[0]+1
		if polyline_count > 0 and total_polyline_length > (delete_distance[0]+delete_distance[1])+0.25:
			valid_path = True
		else:
			valid_path = False
		
		return valid_path, path_point, delete_distance