import numpy as np
import pandas as pd
import math

from opendrive.submodule import clothoid
from opendrive.submodule import link_util

def rotate(rad, x, y):
	rotation_matrix = np.array([[np.cos(rad), -np.sin(rad)], [np.sin(rad), np.cos(rad)]])
	rotated_result = np.dot(rotation_matrix, np.array([x, y]))
	return rotated_result[0], rotated_result[1]
	
def get_connection_line( link_a_list, link_b_list ):
	start_line_direction = link_a_list[2]
	end_line_direction = link_b_list[2]
	
	direction_variation = link_util.normalize_direction(end_line_direction - start_line_direction)
	
	center_x = link_a_list[1][0]
	center_y = link_a_list[1][1]
	
	rot_link_a_x = [link_a_list[0][0]-center_x, link_a_list[1][0]-center_x]
	rot_link_a_y = [link_a_list[0][1]-center_y, link_a_list[1][1]-center_y]
	
	rot_link_b_x = [link_b_list[0][0]-center_x, link_b_list[1][0]-center_x]
	rot_link_b_y = [link_b_list[0][1]-center_y, link_b_list[1][1]-center_y]
	
	rot_link_a_x, rot_link_a_y = rotate(-np.deg2rad(start_line_direction), rot_link_a_x, rot_link_a_y)
	rot_link_b_x, rot_link_b_y = rotate(-np.deg2rad(start_line_direction), rot_link_b_x, rot_link_b_y)
	
	n=1
	start_curvature = 0
	curvature_radius = 20
	
	if direction_variation < 0:
	    curvature_radius *= -1
	    
	end_curvature = 1/curvature_radius
	end_direction = np.deg2rad(direction_variation*0.5)	    
	 
	diff_curvature = end_curvature - start_curvature
	length = (end_direction*diff_curvature)/(end_curvature*end_curvature*0.5)
	
	x,y,start_direction,end_direction = clothoid.get(start_curvature, end_curvature, length)

	y_t = y*-1
	x_t = x
	
	rotation_angle = np.pi-end_direction*(2)
	x_t, y_t = rotate(-rotation_angle, x_t, y_t)

	line_end_x = x_t[-1] - x[-1]
	line_end_y = y_t[-1] - y[-1]

	x_t -= line_end_x
	y_t -= line_end_y

	start_point_x = rot_link_a_x[0]
	start_point_y = rot_link_a_y[0]
	end_point_x = rot_link_b_x[1]
	end_point_y = rot_link_b_y[1]
	
	diff_x = x_t[0] - x[0]
	diff_y = y_t[0] - y[0]
	
	diff_x_line = end_point_x - start_point_x
	diff_y_line = end_point_y - start_point_y
	
	n = math.sqrt(diff_x_line**2 + diff_y_line**2)/math.sqrt(diff_x**2 + diff_y**2)

	x *= n
	y *= n
	x_t *= n
	y_t *= n
	length *= n
	curvature_radius *= n

	x += start_point_x
	x_t += start_point_x
	
	x, y = rotate(np.deg2rad(start_line_direction), x, y)
	x_t, y_t = rotate(np.deg2rad(start_line_direction), x_t, y_t )

	x += center_x
	y += center_y
	x_t += center_x
	y_t += center_y
	
	x_list = x.tolist()
	y_list = y.tolist()
	
	x_t_list = []
	y_t_list = []
	point_size = len(x_t)
	for i in range(0, point_size):
		x_t_list.append(x_t[point_size-(i+1)])
		y_t_list.append(y_t[point_size-(i+1)])
	
	connect_direction = link_util.normalize_direction(start_line_direction + direction_variation*0.5)
	
	return x_list,y_list,x_t_list,y_t_list,length, curvature_radius, connect_direction
	
def devide2link(link):
    length = link_util.get_distance(link[0], link[1])
    center_x = (link[0][0]+link[1][0])*0.5
    center_y = (link[0][1]+link[1][1])*0.5
    link1 = link_util.node2link(link[0], [center_x, center_y])
    link2 = link_util.node2link([center_x, center_y], link[1])
    return link1, link2
    
def devide_link( in_link, out_link, devide_point ):
	
	in_link_length = link_util.get_distance(in_link[0], in_link[1])
	
	devided_in_link = []
	if in_link_length > devide_point :
		in_link_angle = np.deg2rad(in_link[2])
		devide_point_x = in_link[1][0] - math.cos(in_link_angle)*devide_point
		devide_point_y = in_link[1][1] - math.sin(in_link_angle)*devide_point 
		
		first_in_link = [[in_link[0][0], in_link[0][1]],[devide_point_x,devide_point_y],np.rad2deg(in_link_angle)]
		second_in_link = [[devide_point_x,devide_point_y],[in_link[1][0], in_link[1][1]],np.rad2deg(in_link_angle)]
		
		devided_in_link = [first_in_link, second_in_link]
	else:
		devided_in_link = [in_link]
		
	out_link_length = link_util.get_distance(out_link[0], out_link[1])
	devided_out_link = []
	if out_link_length > devide_point:
		out_link_angle = np.deg2rad(out_link[2])
		devide_point_x = out_link[0][0] + math.cos(out_link_angle)*devide_point
		devide_point_y = out_link[0][1] + math.sin(out_link_angle)*devide_point 
		
		first_out_link = [[out_link[0][0], out_link[0][1]],[devide_point_x,devide_point_y],np.rad2deg(out_link_angle)]
		second_out_link = [[devide_point_x,devide_point_y],[out_link[1][0], out_link[1][1]],np.rad2deg(out_link_angle)]
		devided_out_link = [first_out_link, second_out_link]
	else:
		devided_out_link = [out_link]
	
	return devided_in_link, devided_out_link #[first_in_link, second_in_link], [first_out_link, second_out_link]

def get_line( in_link, out_link, start_turning_point ):

	in_link_list, out_link_list = devide_link( in_link, out_link, start_turning_point)
	if len(in_link_list) > 1:
		target_in_link = 1
	else:
		target_in_link = 0
		
	x_in,y_in,x_out,y_out, spiral_length, radius, connect_direction = get_connection_line(in_link_list[target_in_link], out_link_list[0])

	line_list = []
	result_x = []
	result_y = []
	if target_in_link == 1:
		diff_x = in_link_list[0][1][0] - in_link_list[0][0][0]
		diff_y = in_link_list[0][1][1] - in_link_list[0][0][1]
		length = math.sqrt(diff_x**2+diff_y**2)
		result_x.append(in_link_list[0][0][0])
		result_y.append(in_link_list[0][0][1])
		line_list.append(["line", in_link_list[0][0][0], in_link_list[0][0][1], in_link_list[0][2], 1e+16, length])
		line_list.append(["spiral", in_link_list[1][0][0], in_link_list[1][0][1], in_link_list[target_in_link][2], 1e+16, spiral_length])
		line_list.append(["spiral", x_in[-1], y_in[-1], connect_direction, radius, spiral_length])
	else:
		line_list.append(["spiral", in_link_list[0][0][0], in_link_list[0][0][1], in_link_list[target_in_link][2], 1e+16, spiral_length])
		line_list.append(["spiral", x_in[-1], y_in[-1], connect_direction, radius, spiral_length])
		
	
	result_x.extend(x_in)
	result_y.extend(y_in)
	result_x.extend(x_out)
	result_y.extend(y_out)
	
	if len(out_link_list) > 1:
		diff_x = out_link_list[1][1][0] - out_link_list[1][0][0]
		diff_y = out_link_list[1][1][1] - out_link_list[1][0][1]
		length = math.sqrt(diff_x**2+diff_y**2)
		line_list.append(["line", x_out[-1],y_out[-1],out_link_list[0][2],1e+16, length])
		line_list.append(["end",out_link_list[1][1][0], out_link_list[1][1][1],out_link_list[1][2], 1e+16, 0])
		result_x.append(out_link_list[1][1][0])
		result_y.append(out_link_list[1][1][1])
	else:
		line_list.append(["end",out_link_list[0][1][0], out_link_list[0][1][1],out_link_list[0][2], 1e+16, 0])
	
	return result_x, result_y, line_list

def get_start_node( end_x, end_y, direction, length):
	start_x = end_x - length*math.cos(np.deg2rad(direction))
	start_y = end_y - length*math.sin(np.deg2rad(direction))
	
	return start_x, start_y
	
def get_leadin_link(point1, point2):
	length = 20

	end_x = point1[0][0]
	end_y = point1[0][1]
	point1_direction = link_util.normalize_direction(point1[1])
		
	start1_x, start1_y = get_start_node(end_x, end_y, point1_direction, length)

	end_x = point2[0][0]
	end_y = point2[0][1]
	point2_direction = link_util.normalize_direction(point2[1])
		
	start2_x, start2_y = get_start_node(end_x, end_y, point2_direction, length)

	link1 = link_util.get_link([start1_x,start1_y], point1_direction, length)
	link2 = link_util.get_link([start2_x,start2_y], point2_direction, length)
		
	exist_point, intersection_x, intersection_y = link_util.get_intersection(link1, link2)
	if exist_point:
		intersection_direction1 = link_util.get_direction(link1[1], [intersection_x,intersection_y])
		intersection_direction2 = link_util.get_direction(link2[1], [intersection_x,intersection_y])
		if abs(point1_direction - intersection_direction1) > 90.0:
			if abs(point2_direction - intersection_direction2) > 90.0:
				junction_type = 2
			else:
				junction_type = 1
		else:
			if abs(point2_direction - intersection_direction2) > 90.0:
				junction_type = 1
			else:
				junction_type = 0
	else:
		junction_type = 1
		
	return junction_type, link1, link2, [intersection_x, intersection_y]
	

def get_path_link( leadin_link1, leadin_link2):
	connect_line = [leadin_link1[1],leadin_link2[1]]
	direction_line1 = np.deg2rad(leadin_link1[2])
	direction_line2 = np.deg2rad(leadin_link2[2])
	
	point_length = link_util.get_distance(leadin_link2[1], leadin_link1[1])
	point_length *= 0.25
			
	sx = leadin_link1[1][0] + math.cos(direction_line1)*point_length
	sy = leadin_link1[1][1] + math.sin(direction_line1)*point_length
	ex = leadin_link2[1][0] + math.cos(direction_line2)*point_length
	ey = leadin_link2[1][1] + math.sin(direction_line2)*point_length
	
	rotation_center_x = (leadin_link1[1][0] + leadin_link2[1][0])*0.5
	rotation_center_y = (leadin_link1[1][1] + leadin_link2[1][1])*0.5

	rotated_connect_line = [[sx,sy],[ex,ey]]

	exist_point, c1x, c1y = link_util.get_intersection(leadin_link1, rotated_connect_line)
	link1 = link_util.node2link(leadin_link1[1], [c1x,c1y])
	link2 = link_util.node2link([c1x,c1y],[rotation_center_x, rotation_center_y])

	exist_point, c2x,c2y = link_util.get_intersection(leadin_link2, rotated_connect_line)
	link3 = link_util.node2link([rotation_center_x, rotation_center_y], [c2x,c2y])
	link4 = link_util.node2link([c2x,c2y], leadin_link2[1])

	return link1, link2, link3, link4

def get_uturn_link( leadin_link1, leadin_link2):
	connect_line = [leadin_link1[1],leadin_link2[1]]
	direction_line1 = np.deg2rad(leadin_link1[2])
	direction_line2 = np.deg2rad(leadin_link2[2])
	
	sx = leadin_link1[1][0] + math.cos(direction_line1)*10
	sy = leadin_link1[1][1] + math.sin(direction_line1)*10
	ex = leadin_link2[1][0] + math.cos(direction_line2)*10
	ey = leadin_link2[1][1] + math.sin(direction_line2)*10
	
	rotation_center_x = (sx + ex)*0.5
	rotation_center_y = (sy + ey)*0.5

	rotated_connect_line = [[sx,sy],[ex,ey]]

	exist_point, c1x, c1y = link_util.get_intersection(leadin_link1, rotated_connect_line)
	link1 = link_util.node2link(leadin_link1[1], [c1x,c1y])
	link2 = link_util.node2link([c1x,c1y],[rotation_center_x, rotation_center_y])

	exist_point, c2x,c2y = link_util.get_intersection(leadin_link2, rotated_connect_line)
	link3 = link_util.node2link([rotation_center_x, rotation_center_y], [c2x,c2y])
	link4 = link_util.node2link([c2x,c2y], leadin_link2[1])

	return link1, link2, link3, link4

def get_turn_link(junction_point1, junction_point2, intersection_point ):
	link1 = link_util.node2link(junction_point1[0], intersection_point) #], link_util.get_direction(junction_point1[0], intersection_point)]
	link2 = link_util.node2link(intersection_point, junction_point2[0]) #], link_util.get_direction(intersection_point, junction_point2[0])]
	
	return link1, link2

def link2line( link1, link2 ):
	start_turn_point = link_util.get_distance(link1[0], link1[1])
	distance_cr = link_util.get_distance(link2[0], link2[1])
	if start_turn_point > distance_cr:
		start_turn_point = distance_cr
		
	return get_line(link1, link2, start_turn_point)

def get_intersection_line( junction_point1, junction_point2 ):
	
	junction_type, leadin_link1, leadin_link2, intersection_point = get_leadin_link(junction_point1, junction_point2)

	if junction_type == 1:
		link1, link2, link3, link4 = get_path_link(leadin_link1, leadin_link2)
		link2_1, link2_2 = devide2link(link2)
		link3_1, link3_2 = devide2link(link3)
		connect_line1_x, connect_line1_y, connect_line1 = link2line(link1, link2_1)
		connect_line2_x, connect_line2_y, connect_line2 = link2line(link2_2, link3_1)
		connect_line3_x, connect_line3_y, connect_line3 = link2line(link3_2, link4)
		result = connect_line1
		result.extend(connect_line2)
		result.extend(connect_line3)
		result_x = connect_line1_x
		result_x.extend(connect_line2_x)
		result_x.extend(connect_line3_x)
		result_y = connect_line1_y
		result_y.extend(connect_line2_y)
		result_y.extend(connect_line3_y)
	elif junction_type == 2:
		link1, link2, link3, link4 = get_uturn_link(leadin_link1, leadin_link2)
		connect_line1_x, connect_line1_y, connect_line1 = link2line(link1, link2)
		connect_line2_x, connect_line2_y, connect_line2 = link2line(link3, link4)
		result = connect_line1
		result.extend(connect_line2)
		result_x = connect_line1_x
		result_x.extend(connect_line2_x)
		result_y = connect_line1_y
		result_y.extend(connect_line2_y)
	else:
		link1, link2 = get_turn_link(junction_point1, junction_point2, intersection_point)
		result_x, result_y, result = link2line(link1, link2)
	
	result_df = pd.DataFrame(result)
	result_df.columns = ["type","x","y","initial_direction","radius","length"]
	
	return result_x, result_y, result_df