import numpy as np
import pandas as pd
import math

def get_point( link ):
	point_x = [link[0][0], link[1][0]]
	point_y = [link[0][1], link[1][1]]

	return point_x, point_y
	
def rotate_point(rad, x, y):
	rotation_matrix = np.array([[np.cos(rad), -np.sin(rad)], [np.sin(rad), np.cos(rad)]])
	rotated_result = np.dot(rotation_matrix, np.array([x, y]))
	return rotated_result[0], rotated_result[1]
    
def rotate_link( rad, link, center_x, center_y ):
	line_x, line_y = get_point(link)
	line_x[0] -= center_x
	line_x[1] -= center_x
	line_y[0] -= center_y
	line_y[1] -= center_y
	rotated_x, rotated_y = rotate_point(rad, line_x, line_y)
	rotated_x += center_x
	rotated_y += center_y

	return rotated_x, rotated_y

def get_distance( start_node, end_node ):
	diff_x = end_node[0] - start_node[0]
	diff_y = end_node[1] - start_node[1]
	
	return math.sqrt(diff_x**2+diff_y**2)

def get_direction( start_node, end_node ):
	diff_x = end_node[0] - start_node[0]
	diff_y = end_node[1] - start_node[1]
	return np.rad2deg(math.atan2(diff_y, diff_x))
	
def get_direction_variation( node1, node2, node3 ):
	return normalize_direction( get_direction(node2, node3) - get_direction(node1, node2) )
	
def get_diff( start_direction, end_direction ):
	diff_direction = end_direction - start_direction
	if diff_direction > 180:
		diff_direction -= 360
	if diff_direction < -180:
		diff_direction += 360
	return diff_direction
	
def normalize_direction( direction ):
	rotate_count = int(abs(direction / 360))+1
	normalized_direction = direction
	for i in range(0, rotate_count):
		if normalized_direction > 180:
			normalized_direction -= 360
		if normalized_direction < -180:
			normalized_direction += 360
			 
	return normalized_direction
	
def inverse_direction(direction):
	return normalize_direction(direction+180.0)
	
def get_node_point(node_a, node_b, target_length):
	link_angle = np.deg2rad(get_direction(node_a, node_b))
	point_x = node_a[0] + math.cos(link_angle)*target_length
	point_y = node_a[1] + math.sin(link_angle)*target_length 

	return [point_x, point_y]
	
def reposition(previous_node, target_node, next_node, target_length):
	diff_x = target_node[0] - previous_node[0]
	diff_y = target_node[1] - previous_node[1]
	length_previous = math.sqrt(diff_x**2 + diff_y**2)

	result_node = target_node
	if target_length > length_previous:
		result_node = get_node_point(target_node, next_node, target_length - length_previous)
	else:
		result_node = get_node_point(previous_node, target_node, target_length)
	return result_node
    
def add_node( polyline, target_node, insert_index):
	new_polyline = []
	for i in range(0, len(polyline)):
		if i == insert_index:
			new_polyline.append(target_node)
		new_polyline.append(polyline[i])
	
	return new_polyline

def replace_node( polyline, target_node, target_index ):
	new_polyline = []
	for i in range(0, len(polyline)):
		if i == target_index:
			new_polyline.append(target_node)
		else:
			new_polyline.append(polyline[i])
	    
	return new_polyline
	
def remove_node( polyline, target_index):
	new_polyline = []
	for i in range(0, len(polyline)):
		if not i == target_index:
			new_polyline.append(polyline[i])
	    
	return new_polyline	
	
def get_line_parameter( start_node, end_node ):

	diff_x = end_node[0] - start_node[0]
	diff_y = end_node[1] - start_node[1]
	a = 0
	b = 0
	isValid = False
	if abs(diff_x) > 0:
		isValid = True
		a = diff_y/diff_x
		b = start_node[1] - a*start_node[0]
		
	return isValid, a, b
	
def line_parameter2intersection( a, b, c, d):
    x = (d-b)/(a-c)
    y = (a*d-b*c)/(a-c)

    return x,y
	
def get_intersection(link_a, link_b):

	isValid_a, a,b = get_line_parameter( link_a[0], link_a[1] )
	isValid_b, c,d = get_line_parameter( link_b[0], link_b[1] )

	exist_intersection = False
	x = 0
	y = 0

	if isValid_a and isValid_b:
		if abs(a-c) > 0:
			exist_intersection = True
			x,y = line_parameter2intersection(a, b, c, d)
	elif isValid_a:
		exist_intersection = True
		x = link_b[0][0]
		y = a*x + b
	elif isValid_b:
		exist_intersection = True
		x = link_a[0][0]
		y = a*x + b

	return exist_intersection, x, y
	
def get_link( start_node, direction, length ):

	rad_direction = np.deg2rad(direction)
	end_x = start_node[0] + math.cos(rad_direction)*length
	end_y = start_node[1] + math.sin(rad_direction)*length

	link = [start_node, [end_x, end_y], direction]

	return link
	
def node2link( start_node, end_node ):
	link = [start_node, end_node, get_direction(start_node, end_node)]
	
	return link
	
def calc_turning_point(source_width, target_width, direction_variation):
	radian_diff = abs(np.deg2rad(direction_variation))
		
	if radian_diff > math.pi*0.5:
		result = target_width/math.sin(radian_diff) - source_width/math.tan(radian_diff)
	else:
		if radian_diff < math.pi*0.25 and radian_diff > 0.35:
			result = target_width/math.sin(radian_diff)
		else:
			result = target_width*math.sin(radian_diff)

	return result

def shift_point(point_x, point_y, direction, distance):
	result_x = point_x + distance*math.cos(np.deg2rad(direction))
	result_y = point_y + distance*math.sin(np.deg2rad(direction))
	return result_x, result_y
	
def get_midpoint(node_a, node_b):
	midpoint_x = (node_a[0]+node_b[0])*0.5
	midpoint_y = (node_a[1]+node_b[1])*0.5
	return [midpoint_x, midpoint_y]