import numpy as np
import math

def get_line_direction( start_point, end_point, x_list, y_list ):
		
	diff_point_x = x_list[end_point] - x_list[start_point]
	diff_point_y = y_list[end_point] - y_list[start_point]
	
	return np.rad2deg(math.atan2(diff_point_y, diff_point_x))

def get_line_length( start_point, end_point, length_list ):
	
	result = 0
	for i in range(start_point, end_point):
		result += length_list[i]

	return result

def get_direction_variation( start_point, end_point, direction_list):
	
	result = 0
	for i in range(start_point, end_point):
		diff_direction = direction_list[end_point] - direction_list[start_point]
		if diff_direction > 180:
			diff_direction -= 360
		elif diff_direction < -180:
			diff_direction += 360
		
		result += diff_direction
		
	return result

def get_line_part(road_data_df, radius_theshold = 3000, diff_angle_threshold = 0.5):

	radius_list = road_data_df['radius'].to_list()
	direction_list = road_data_df['initial_direction'].to_list()
	x_list = road_data_df['x'].to_list()
	y_list = road_data_df['y'].to_list()
	length_list = road_data_df['length'].to_list()
	
	line_flag = False
	line_part_list = []
	exist_line = False
	next_start_point = 0
	for i in range(0, len(radius_list) - 1):
		if abs(radius_list[i]) > radius_theshold and abs(radius_list[i+1]) > radius_theshold:
			if line_flag:
				start_line_direction = get_line_direction(start_point, start_point+1, x_list, y_list)
				end_line_direction = get_line_direction(start_point, i+1, x_list, y_list)
				diff_line_direction = end_line_direction - start_line_direction
				direction_variation = get_direction_variation(start_point, i, direction_list)
				if diff_line_direction > 180:
					diff_line_direction -= 360
				elif diff_line_direction < -180:
					diff_line_direction += 360
				if abs(diff_line_direction) < diff_angle_threshold and abs(direction_variation) < diff_angle_threshold:
					end_point = i
					line_flag = True
				else:
					exist_line = True
					line_length = get_line_length( start_point, end_point, length_list )
					line_part_list.append([start_point,end_point, line_length])
					line_flag = False
					next_start_point = end_point+2
					
			elif i >= next_start_point:
				start_point = i
				end_point = i+1
				diff_line_direction = 0
				if end_point < len(radius_list)-1:
					start_line_direction = get_line_direction(start_point, end_point, x_list, y_list)
					end_line_direction = get_line_direction(end_point, end_point+1, x_list, y_list)
					diff_line_direction = end_line_direction - start_line_direction
				else:
					previous_point = i-1
					start_line_direction = get_line_direction(start_point, end_point, x_list, y_list)
					previous_line_direction = get_line_direction(previous_point, start_point, x_list, y_list)
					diff_line_direction = previous_line_direction - start_line_direction
					
				if diff_line_direction > 180:
					diff_line_direction -= 360
				elif diff_line_direction < -180:
					diff_line_direction += 360
				if abs(diff_line_direction) < diff_angle_threshold:
					line_flag = True
					next_start_point = end_point+2
		
		elif line_flag:
			exist_line = True
			end_point = i
			next_start_point = end_point+2
			line_length = get_line_length( start_point, end_point, length_list )
			line_part_list.append([start_point,end_point,line_length])
			line_flag = False
	
	if line_flag:
		exist_line = True
		end_point = len(radius_list) - 1
		line_length = get_line_length( start_point, end_point, length_list )
		line_part_list.append([start_point, end_point, line_length])
	
	return exist_line,line_part_list


def road2line(road_df, line_point):

	start_point_x = road_df["x"][line_point]
	start_point_y = road_df["y"][line_point]
	length = road_df["length"][line_point]
	direction = np.deg2rad(road_df["initial_direction"][line_point])
	
	line_end_point_x = length*math.cos(direction) + start_point_x
	line_end_point_y = length*math.sin(direction) + start_point_y

	return [start_point_x, line_end_point_x],[start_point_y,line_end_point_y],length,np.rad2deg(direction)