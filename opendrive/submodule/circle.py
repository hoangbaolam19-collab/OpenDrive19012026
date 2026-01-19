import numpy as np
import math

def point2center( point1_x, point1_y, point2_x, point2_y, r ):
	point_x = (point1_x+point2_x)*0.5
	point_y = (point1_y+point2_y)*0.5

	R = r**2
	diff_x = point2_x - point_x
	diff_y = point2_y - point_y
	a = diff_x**2 + diff_y**2
	c1_x = 0
	c1_y = 0
	c2_x = 0
	c2_y = 0

	if R >= a:
		d = math.sqrt(R/a - 1.0)
		dx = d * diff_y
		dy = d * diff_x

		c1_x = point_x + dx
		c1_y = point_y - dy

		c2_x = point_x - dx
		c2_y = point_y + dy
		
	return c1_x,c1_y,c2_x,c2_y

def get_center( x, y, r, tangential_direction):
	
	if r > 0:
		center_direction = np.deg2rad(tangential_direction + 90.0)
	else:
		center_direction = np.deg2rad(tangential_direction - 90.0)
	
	cx = abs(r)*math.cos(center_direction) + x
	cy = abs(r)*math.sin(center_direction) + y
	
	return cx,cy

def get_length( r, initial_direction, end_direction):
	
	diff_angle = np.deg2rad(end_direction) - np.deg2rad(initial_direction)
	if diff_angle > np.pi:
		diff_angle -= (2.0*np.pi)
	elif diff_angle < -np.pi:
		diff_angle += (2.0*np.pi)
	
	return abs(r*diff_angle)

def calc_tangential_direction( x, y, cx, cy ):
	diff_x = x - cx
	diff_y = y - cy
	direction = math.atan2(diff_y, diff_x)
	direction += math.pi*0.5
	return direction
	
def get_start_point(radius_list, extremum_point, extremum_radius, threshold_diff_radius):

	find = False
	arc_start_point = extremum_point
	
	for i in range(1,extremum_point):
		if( abs(radius_list[extremum_point-i] - extremum_radius) < threshold_diff_radius):
			arc_start_point = extremum_point-i
			find = True
		else:
			break
	
	return find, arc_start_point
	
def get_end_point(radius_list, extremum_point, extremum_radius, threshold_diff_radius):

	find = False
	arc_end_point = extremum_point
	
	for i in range(extremum_point+1,len(radius_list)-1):
		if( abs(radius_list[i] - extremum_radius) < threshold_diff_radius):
			arc_end_point = i
			find = True
		else:
			break
	
	return find, arc_end_point
	
def get_mean_radius(radius_list, start_point, end_point):
	
	mean_radius = 0
	count = end_point - start_point + 1
	for i in range(start_point, end_point+1):
		mean_radius += radius_list[i]
		
	mean_radius /= count
	
	return mean_radius
	
def get_arc_part(road_data_df, threshold_diff_radius = 20):
	
	radius_list = road_data_df['radius'].to_list()
	exist_arc = False
	extremum = []
	for i in range(1,len(radius_list) - 1):
		diff_previous = radius_list[i] - radius_list[i-1]
		diff_next = radius_list[i+1] - radius_list[i]
		if diff_previous*diff_next < 0:
			extremum.append(i)
	
	arc_part_list = []
	next_start_point = 0
	for i in range(0,len(extremum)):
		extremum_point = extremum[i]
		radius = radius_list[extremum_point]
		if extremum_point >= next_start_point:
			start_find, start_point = get_start_point(radius_list, extremum_point, radius, threshold_diff_radius)
			end_find, end_point = get_end_point(radius_list, extremum_point, radius, threshold_diff_radius)
			
			if start_point < next_start_point:
				start_point = next_start_point
			
			if start_find and end_find:
				mean_radius = get_mean_radius(radius_list, start_point, end_point)
				start_direction = road_data_df.at[start_point,"initial_direction"]
				end_direction = road_data_df.at[end_point,"initial_direction"]
				arc_length = get_length(mean_radius, start_direction, end_direction)
				arc_part_list.append([start_point,end_point,mean_radius,arc_length])
				next_start_point = end_point+1
				exist_arc = True

	return exist_arc, arc_part_list


def get_circle( center_x, center_y, radius ):
	theta = np.linspace(0, 2 * np.pi, 100)
	circle_x = radius * np.sin(theta)
	circle_y = radius * np.cos(theta)
	circle_x += center_x
	circle_y += center_y
	
	return circle_x,circle_y
	
def get_arc( center_x, center_y, radius, start_angle, end_angle ):
	n_points = 100
	theta = np.linspace((np.pi*0.5 - start_angle), (np.pi*0.5 - end_angle) ,n_points)
	arc_x = radius * np.sin(theta)
	arc_y = radius * np.cos(theta)
	arc_x += center_x
	arc_y += center_y

	return arc_x,arc_y

def road2arc( road_data_df, arc_point ):
	
	start_point_x = road_data_df["x"][arc_point]
	start_point_y = road_data_df["y"][arc_point]
	radius = road_data_df["radius"][arc_point]
	arc_length = road_data_df["length"][arc_point]
	tangential_direction = road_data_df["initial_direction"][arc_point]
	end_direction = tangential_direction + np.rad2deg(arc_length/radius)
		
	center_x, center_y = get_center(start_point_x,start_point_y, radius, tangential_direction)
	
	start_angle = tangential_direction
	end_angle = end_direction
	
	if radius > 0:
		start_angle -= 90
		end_angle -= 90
	else:
		start_angle += 90
		end_angle += 90
	
	arc_x,arc_y = get_arc(center_x,center_y,abs(radius),np.deg2rad(start_angle),np.deg2rad(end_angle))
	
	return arc_x,arc_y,arc_length,tangential_direction,end_direction
	
def road2circle_center( roaddata_df, target_point ):
	
	start_point_x = roaddata_df["x"][target_point]
	start_point_y = roaddata_df["y"][target_point]
	radius = roaddata_df["r"][target_point]
	tangential_direction = roaddata_df["initial_direction"][target_point]
	
	center_x, center_y = get_center(start_point_x,start_point_y, radius, tangential_direction)
	
	return center_x, center_y
