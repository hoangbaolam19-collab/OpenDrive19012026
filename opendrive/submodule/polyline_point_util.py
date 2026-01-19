import pandas as pd
import numpy as np
import math

from opendrive.submodule import link_util

def first_direction( polyline_point, order ):
	if order == 0:
		return link_util.get_direction( polyline_point[0], polyline_point[1] )
	else:
		return link_util.get_direction( polyline_point[-1], polyline_point[-2] )
		
def last_direction( polyline_point, order ):
	if order == 0:
		return link_util.get_direction( polyline_point[-2], polyline_point[-1] )
	else:
		return link_util.get_direction( polyline_point[1], polyline_point[0] )

def travel_direction( polyline_point, order ):
	if order == 0:
		return link_util.get_direction( polyline_point[0], polyline_point[-1] )
	else:
		return link_util.get_direction( polyline_point[-1], polyline_point[0] )

def shift(polyline, t_shift):
	shifted_polyline = []
	for i in range(0, len(polyline)-1):
		direction = link_util.get_direction(polyline[i], polyline[i+1])
		shift_x, shift_y = link_util.shift_point(polyline[i][0], polyline[i][1], direction+90, t_shift)
		shifted_polyline.append([shift_x, shift_y])
	
	direction = link_util.get_direction(polyline[-2], polyline[-1])
	shift_x, shift_y = link_util.shift_point(polyline[-1][0], polyline[-1][1], direction+90, t_shift)
	shifted_polyline.append([shift_x, shift_y])
	
	return shifted_polyline

def inverse(polyline):
	point_count = len(polyline)
	inverse_polyline = []
	for j in range(0,point_count):
		inverse_polyline.append([polyline[point_count-(j+1)][0], polyline[point_count-(j+1)][1]])
	return inverse_polyline

def reconstruction_test(polyline_list, rate_list):

	original_scale_list = []
	rescale_list = []
	original_start_x = polyline_list[0][0][0]
	original_start_y = polyline_list[0][0][1]
	rescale_start_x = original_start_x
	rescale_start_y = original_start_y

	for i in range(0, len(polyline_list)):
		original_point = []
		scaling_point = []
		for path_point in polyline_list[i]:
			point_x = path_point[0] - polyline_list[i][0][0]
			point_y = path_point[1] - polyline_list[i][0][1]
			original_point.append([point_x + original_start_x, point_y + original_start_y])
			scaling_point.append([point_x*rate_list[i] + rescale_start_x, point_y*rate_list[i] + rescale_start_y])
		original_scale_list.append(original_point)
		rescale_list.append(scaling_point)

		original_start_x = original_point[-1][0]
		original_start_y = original_point[-1][1]
		rescale_start_x = scaling_point[-1][0]
		rescale_start_y = scaling_point[-1][1]

	return original_scale_list, rescale_list
	
def reconstruction(polyline, node_point):
	start_x = node_point[0][0]
	start_y = node_point[0][1]
	end_x = node_point[1][0]
	end_y = node_point[1][1]
	
	polyline_start_x = polyline[0][0]
	polyline_start_y = polyline[0][1]
	polyline_end_x = polyline[-1][0]
	polyline_end_y = polyline[-1][1]
	
	diff_start_x = start_x - polyline_start_x
	diff_start_y = start_y - polyline_start_y
	diff_end_x = end_x - polyline_end_x
	diff_end_y = end_y - polyline_end_y

	polyline_length = get_length(polyline)
	previous_point = polyline[0]
	point_distance = 0.0
	result_polyline = []
	for polyline_point in polyline:
		point_distance += link_util.get_distance(previous_point, polyline_point)
		point_rate = point_distance/polyline_length
		point_x = polyline_point[0] + diff_start_x*(1.0 - point_rate) + diff_end_x*point_rate
		point_y = polyline_point[1] + diff_start_y*(1.0 - point_rate) + diff_end_y*point_rate
		result_polyline.append([point_x, point_y])
		previous_point = polyline_point
	return result_polyline
	
def get_point_list(polyline_list, target_range, shift):
	point_list = []
	for i in range(target_range[0], target_range[1]+1):
		for polyline_point in polyline_list[i]:
			point_x = polyline_point[0] + shift[0]
			point_y = polyline_point[1] + shift[1]
			point_list.append([point_x, point_y])
	return point_list

def get_length(polyline):
	length = 0.0
	for i in range(0, len(polyline)-1):
		length += link_util.get_distance(polyline[i], polyline[i+1])
	return length
	
def rescale(polyline, scale):
	origin_x = polyline[0][0]
	origin_y = polyline[0][1]
	scaling_polyline = []
	for path_point in polyline:
		point_x = path_point[0] - origin_x
		point_y = path_point[1] - origin_y
		scaling_polyline.append([point_x*scale + origin_x, point_y*scale + origin_y])
	
	return scaling_polyline

def rotate(polyline, rotate_direction, center_x, center_y):
	point_x = []
	point_y = []
	rotate_radian = np.deg2rad(rotate_direction)
	for polyline_point in polyline:
		point_x.append(polyline_point[0] - center_x)
		point_y.append(polyline_point[1] - center_y)

	rotated_x, rotated_y = link_util.rotate_point(rotate_radian, point_x, point_y)

	rotated_x += center_x
	rotated_y += center_y

	rotated_polyline = []
	for i in range(0, len(rotated_x)):
		rotated_polyline.append([rotated_x[i], rotated_y[i]])

	return rotated_polyline
	
	
def get_intersection_point(link, polyline):
	find = False
	target_index = 0
	min_diff_point = 200.0
	result_distance = 0.0
	result_x = 0.0
	result_y = 0.0
	
	for i in range(0, len(polyline)-1):
		polyline_link = [polyline[i], polyline[i+1]]
		exist_point, intersection_point_x, intersection_point_y = link_util.get_intersection(link, polyline_link)
		if exist_point:
			diff_x = link[0][0] - intersection_point_x
			diff_y = link[0][1] - intersection_point_y
			intersection_point_distance = math.sqrt(diff_x**2 + diff_y**2)
			if intersection_point_distance < min_diff_point:
				find = True
				result_x = intersection_point_x
				result_y = intersection_point_y
				result_distance = intersection_point_distance
				target_index = i
				min_diff_point = intersection_point_distance
				
				if intersection_point_distance < 10.0:
					break
				else:
					diff_start_x = intersection_point_x - polyline[i][0]
					diff_end_x = intersection_point_x - polyline[i+1][0]
					diff_start_y = intersection_point_y - polyline[i][1]
					diff_end_y = intersection_point_y - polyline[i+1][1]
					if diff_start_x*diff_end_x <= 0.0:
						break
					if diff_start_y*diff_end_y <= 0.0:
						break
	return find, target_index, result_distance, [result_x, result_y]