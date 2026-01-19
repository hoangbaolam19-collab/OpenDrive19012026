import pandas as pd
import numpy as np
import math

from scipy import interpolate
import matplotlib.pyplot as plt

from opendrive.submodule import clothoid
from opendrive.submodule import circle
from opendrive.submodule import line

def B_spline(x, y, S):
	n = len(x)
	if n > 3:
		t=np.linspace(0,1,n-2,endpoint=True)
		t=np.append([0,0,0],t)
		t=np.append(t,[1,1,1])
		tck=[t,[x,y],3]
	elif n == 3:
		t= [0,0,0,1,1,1]
		tck=[t,[x,y],2]
	elif n == 2:
		t = [0,0,0,1,1,1]
		tck=[t,[x,y],1]
		
	u3=np.linspace(0,1,n*S,endpoint=True)
	result = interpolate.splev(u3,tck)
	
	return result

def B_spline_interpolate(road_point_df, S=1):

	x = road_point_df["x"].values.tolist()
	y = road_point_df["y"].values.tolist()

	x = np.array(x)
	y = np.array(y)
	
	b_spline_point = B_spline(x, y, S)
	b_spline_point_df = pd.DataFrame(b_spline_point).T
	b_spline_point_df.columns = ["x","y"]
	
	return b_spline_point_df

def calc_curvature( point_x, point_y, calc_point ):
	diff_prev_x = point_x[calc_point] - point_x[calc_point-1]
	diff_prev_y = point_y[calc_point] - point_y[calc_point-1]
	diff_next_x = point_x[calc_point+1] - point_x[calc_point]
	diff_next_y = point_y[calc_point+1] - point_y[calc_point]
	
	prev_angle = math.atan2( diff_prev_y, diff_prev_x)
	next_angle = math.atan2( diff_next_y, diff_next_x)
	
	diff_x = point_x[calc_point+1] - point_x[calc_point-1]
	diff_y = point_y[calc_point+1] - point_y[calc_point-1]
	prev_length = math.sqrt(diff_prev_x**2+diff_prev_y**2)
	next_length = math.sqrt(diff_next_x**2 + diff_next_y**2)
	length = math.sqrt(diff_prev_x**2+diff_prev_y**2) + math.sqrt(diff_next_x**2 + diff_next_y**2)
	if length < 0.001:
		length = 0.001
		
	diff_angle = abs(next_angle - prev_angle)
	if diff_angle > np.pi:
		diff_angle -= (np.pi*2)
	elif diff_angle < -np.pi:
		diff_angle += (np.pi*2)
	
	mid_point_x = (point_x[calc_point+1] + point_x[calc_point-1])*0.5
	mid_point_y = (point_y[calc_point+1] + point_y[calc_point-1])*0.5
	
	tangential_vector = np.array([point_x[calc_point+1] - point_x[calc_point-1],point_y[calc_point+1] - point_y[calc_point-1]])
	normal_vector = np.array([point_x[calc_point] - mid_point_x, point_y[calc_point] - mid_point_y])
	
	cross_product = np.cross(normal_vector,tangential_vector)
	curvature = abs(diff_angle)/(length*0.5)
		
	if cross_product < 0:
		curvature *= -1
	
	return curvature

def point2spiral(road_point_df):
	x = []
	y = []
	x = road_point_df["x"].to_list()
	y = road_point_df["y"].to_list()
	
	iter_size = len(x)
	road_data_list = []

	data_type = "spiral"
	total_length = 0.0
	curvature_radius = 1e+16
	diff_x = x[1] - x[0]
	diff_y = y[1] - y[0]
	length = math.sqrt(diff_x**2 + diff_y**2)    
	direction = np.rad2deg(math.atan2(diff_y,diff_x))

	road_data_list.append([data_type,x[0],y[0],direction,curvature_radius,length])

	previous_x = x[0]
	previous_y = y[0]
	previous_length = length
	for i in range(1, iter_size-1):
	
		curvature = calc_curvature(x,y,i)
		if abs(curvature) > 0:
			curvature_radius = 1/curvature
		else:
			curvature_radius = 1e+16
			
		diff_next_x = x[i+1] - x[i]
		diff_next_y = y[i+1] - y[i]
		length = math.sqrt(diff_next_x**2 + diff_next_y**2)
		total_length += previous_length
		direction = np.rad2deg(math.atan2(diff_next_y, diff_next_x))
		
		previous_x = x[i]
		previous_y = y[i]
		previous_length = length
		road_data_list.append([data_type,x[i], y[i], direction, curvature_radius, length])
		
	diff_x = x[iter_size-1] - previous_x
	diff_y = y[iter_size-1] - previous_y
	data_type = "end"
	curvature_radius = 1e+16
	distance = 0
	direction = np.rad2deg(math.atan2(diff_y,diff_x))
	total_length += previous_length
	road_data_list.append([data_type,x[iter_size-1],y[iter_size-1],direction,curvature_radius,length])
	
	road_data_df = pd.DataFrame(road_data_list)
	road_data_df.columns = ["type","x","y","initial_direction","radius","length"]
	
	return road_data_df

def point2line(road_point_df):
	x = []
	y = []
	x = road_point_df["x"].to_list()
	y = road_point_df["y"].to_list()
	
	iter_size = len(x)
	road_data_list = []

	data_type = "line"
	total_length = 0.0
	curvature_radius = 1e+16
	diff_x = x[1] - x[0]
	diff_y = y[1] - y[0]
	length = math.sqrt(diff_x**2 + diff_y**2)    
	direction = np.rad2deg(math.atan2(diff_y,diff_x))

	road_data_list.append([data_type,x[0],y[0],direction,curvature_radius,length])

	previous_x = x[0]
	previous_y = y[0]
	previous_length = length
	for i in range(1, iter_size-1):
		diff_next_x = x[i+1] - x[i]
		diff_next_y = y[i+1] - y[i]
		length = math.sqrt(diff_next_x**2 + diff_next_y**2)
		total_length += previous_length
		direction = np.rad2deg(math.atan2(diff_next_y, diff_next_x))
		
		previous_x = x[i]
		previous_y = y[i]
		previous_length = length
		road_data_list.append([data_type,x[i], y[i], direction, curvature_radius, length])
		
	diff_x = x[iter_size-1] - previous_x
	diff_y = y[iter_size-1] - previous_y
	data_type = "end"
	curvature_radius = 1e+16
	distance = 0
	direction = np.rad2deg(math.atan2(diff_y,diff_x))
	total_length += previous_length
	road_data_list.append([data_type,x[iter_size-1],y[iter_size-1],direction,curvature_radius,length])
	
	road_data_df = pd.DataFrame(road_data_list)
	road_data_df.columns = ["type","x","y","initial_direction","radius","length"]
	
	return road_data_df

def spiral2arc(road_data_df, threshold_diff_radius):

	exist_arc,arc_part_list = circle.get_arc_part(road_data_df, threshold_diff_radius)
	
	if exist_arc:
		for i in range(0,len(arc_part_list)):
			arc_start = arc_part_list[i][0]
			arc_end = arc_part_list[i][1]
			radius = arc_part_list[i][2]
			length = arc_part_list[i][3]
			road_data_df.at[arc_start,"type"] = "arc"
			road_data_df.at[arc_start,"radius"] = radius
			road_data_df.at[arc_start,"length"] = length
			road_data_df.at[arc_end,"radius"] = radius
			road_data_df = road_data_df.drop(range(arc_start+1,arc_end))
			
		road_data_df = road_data_df.reset_index(drop=True)
	
	return road_data_df
	
def spiral2line(road_data_df, threshold_radius, threshold_diff_angle):
	
	line_exist,line_part_list = line.get_line_part(road_data_df, threshold_radius, threshold_diff_angle)

	if line_exist:
		for i in range(len(line_part_list)):
			line_start = line_part_list[i][0]
			line_end = line_part_list[i][1]
			
			road_data_df.at[line_start,"type"] = "line"
			road_data_df.at[line_start,"radius"] = 1e+16
			road_data_df.at[line_start,"length"] = line_part_list[i][2]
			road_data_df.at[line_end,"radius"] = 1e+16
			road_data_df = road_data_df.drop(range(line_start+1,line_end))
			
		road_data_df = road_data_df.reset_index(drop=True)
	
	return road_data_df
	
def spiral2parametric_cubic(road_data_df):
	for i in range(0, road_data_df.shape[0]-1):
		if road_data_df.at[i, "type"] == "spiral":
			road_data_df.at[i,"type"] = "parametric_cubic"
	return road_data_df
	
def devide_spiral( road_data_df ):
	devide_target_index = []
	for i in range(0,road_data_df.shape[0]-1):
		if road_data_df.at[i, "type"] == "spiral":
			start_radius = road_data_df.at[i,"radius"]
			end_radius = road_data_df.at[i+1,"radius"]
			if start_radius*end_radius < 0 and abs(start_radius) < 1e+12 and abs(end_radius) < 1e+12:
				devide_target_index.append(i)
				
	df_segment_list = []
	new_road_df = pd.DataFrame()

	if len(devide_target_index) > 0:
		start_index = 0
		target_index = 0
		for i in range(0, len(devide_target_index)):
			target_index = devide_target_index[i]
			new_road_df = pd.concat([new_road_df, road_data_df.iloc[start_index:target_index+1]])
			start_point = [road_data_df["x"][target_index], road_data_df["y"][target_index]]
			initial_direction = road_data_df["initial_direction"][target_index]
			R1 = road_data_df["radius"][target_index]
			R2 = road_data_df["radius"][target_index+1]
			length = road_data_df["length"][target_index]
			zero_length, zero_point_x, zero_point_y, end_direction = clothoid.get_zero_cuvature_point(R1,R2,length, initial_direction, start_point)
			new_df = pd.DataFrame([["spiral",zero_point_x,zero_point_y,end_direction,1e+16,length - zero_length]])
			new_df.columns = road_data_df.columns
			new_road_df.at[target_index,"length"] = zero_length
			new_road_df = pd.concat([new_road_df, new_df])
			start_index = target_index+1
		
		start_index = target_index+1
		new_road_df = pd.concat([new_road_df,road_data_df.iloc[start_index:]],ignore_index=True)
	else:
		new_road_df = road_data_df
		
	return new_road_df
