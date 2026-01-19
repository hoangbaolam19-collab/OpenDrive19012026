import numpy as np
import math
from scipy.special import fresnel

def rotate(rad, x, y):
    rotation_matrix = np.array([[np.cos(rad), -np.sin(rad)], [np.sin(rad), np.cos(rad)]])
    rotated_result = np.dot(rotation_matrix, np.array([x, y]))
    return rotated_result[0], rotated_result[1]

def get(start_curvature, end_curvature, length):

	d_curvature = (end_curvature - start_curvature) / length
	if d_curvature == 0:
		d_curvature = 1e-16
		
	start_point = start_curvature / d_curvature
	end_point = end_curvature / d_curvature

	a = 1.0/math.sqrt(abs(d_curvature))
	a *= math.sqrt(np.pi)

	start_length = start_point/a
	end_length = (start_point + length)/a
		
	point_count = int(length / 0.01)
	if point_count < 2:
		point_count = 2
	l = np.linspace(start_length, end_length, point_count)
	
	clothoid_point = fresnel(l)
	
	x = clothoid_point[1] - clothoid_point[1][0]
	y = clothoid_point[0] - clothoid_point[0][0]
	
	x *= a
	y *= a
	
	if d_curvature < 0:
		y *= -1
	
	start_direction = start_point * start_point * d_curvature * 0.5;
	end_direction = end_point*end_point*d_curvature*0.5

	return x, y, start_direction, end_direction
	
def road2clothoid( road_data_df, clothoid_point ):
	
	initial_direction = road_data_df["initial_direction"][clothoid_point]
	start_radius = road_data_df["radius"][clothoid_point]
	end_radius = road_data_df["radius"][clothoid_point+1]
	length = road_data_df["length"][clothoid_point]
	
	start_curvature = 1/start_radius
	end_curvature = 1/end_radius
	
	x_point, y_point, start_direction, end_direction = get(start_curvature, end_curvature, length)
	
	rotation_angle = np.deg2rad(initial_direction) - start_direction;
	x_result, y_result = rotate(rotation_angle, x_point, y_point)
	
	x_result += road_data_df["x"][clothoid_point]
	y_result += road_data_df["y"][clothoid_point]
	
	return x_result, y_result, length, initial_direction, np.rad2deg(end_direction+rotation_angle)

def get_zero_cuvature_point(start_radius, end_radius, length, initial_direction, initial_point):

	start_curvature = 1/start_radius
	end_curvature = 1/end_radius

	d_curvature = (end_curvature - start_curvature) / length
	if d_curvature == 0:
		d_curvature = 1e-16
		
	start_point = start_curvature / d_curvature
	
	a = 1.0/math.sqrt(abs(d_curvature))
	a *= math.sqrt(np.pi)

	start_length = start_point/a
	
	l = np.linspace(start_length, 0, 3)
	clothoid_point = fresnel(l)
	
	x_point = clothoid_point[1] - clothoid_point[1][0]
	y_point = clothoid_point[0] - clothoid_point[0][0]
	
	x_point *= a
	y_point *= a
	
	start_direction = start_point * start_point * d_curvature * 0.5;
	rotation_angle = np.deg2rad(initial_direction) - start_direction;
	x_result, y_result = rotate(rotation_angle, x_point, y_point)
	
	x_result += initial_point[0]
	y_result += initial_point[1]
	end_direction = np.rad2deg(rotation_angle)
	if end_direction > 180:
		end_direction -= 360
	if end_direction < -180:
		end_direction += 360

	return abs(start_point), x_result[-1], y_result[-1], end_direction
	
def get_clothoid_point( start_radius, end_radius, length, t ):

	start_curvature = 1/start_radius
	end_curvature = 1/end_radius

	d_curvature = (end_curvature - start_curvature) / length
	if d_curvature == 0:
		d_curvature = 1e-16
		
	start_point = start_curvature / d_curvature
	end_point = end_curvature / d_curvature

	a = 1.0/math.sqrt(abs(d_curvature))
	a *= math.sqrt(np.pi)
	
	start_length = start_point/a
	end_length = (start_point + t)/a
	l = np.linspace(start_length, end_length, 3)
	clothoid_point = fresnel(l)
	
	x_point = clothoid_point[1] - clothoid_point[1][0]
	y_point = clothoid_point[0] - clothoid_point[0][0]
	
	x_point *= a
	y_point *= a
	
	if d_curvature < 0:
		y_point *= -1	
	
	start_direction = start_point * start_point * d_curvature * 0.5;
	end_direction = (start_point + t)*(start_point + t)*d_curvature*0.5
	end_direction -= start_direction
	rotation_angle =  - start_direction;
	x_result, y_result = rotate(rotation_angle, x_point, y_point)
	
	return x_result[-1], y_result[-1], end_direction