import pandas as pd
import numpy as np
import math

def get_gradient(elevation_list):
	
	gradient_list = []
	for i in range(0,len(elevation_list)-1):
		diff_x = elevation_list[i+1][0] - elevation_list[i][0]
		diff_y = elevation_list[i+1][1] - elevation_list[i][1]
		distance = math.sqrt(diff_x**2+diff_y**2)
		diff_h = elevation_list[i+1][2] - elevation_list[i][2]
		gradient = np.rad2deg(atan2(diff_h,distance))
		gradient_list.append([distance, gradient])
		
	return gradient_list
	
def get_szlist(elevation_list):

	previous_x = elevation_list[0][0]
	previous_y = elevation_list[0][1]
	
	szlist = []
	s = 0
	for i in range(0,len(elevation_list)):
		current_x = elevation_list[i][0]
		current_y = elevation_list[i][1]
		
		diff_x = current_x - previous_x
		diff_y = current_y - previous_y
		
		s += math.sqrt(diff_x**2+diff_y**2)
		z = elevation_list[i][2]
		szlist.append([s,z])
		
		previous_x = current_x
		previous_y = current_y
		
	return szlist
	
def get_point(szlist):
	slist=[]
	zlist=[]
	for sz in szlist:
		slist.append(sz[0])
		zlist.append(sz[1])
	return slist, zlist
	
def get_elevation_part(szlist, start_rate, end_rate):
	length = szlist[-1][0] - szlist[0][0]
	start_point = szlist[0][0] + length*start_rate
	end_point = szlist[0][0] + length*end_rate
	start_index = 0
	end_index = 0
	
	for i in range(0,len(szlist)):
		if start_point < szlist[i][0]:
			break
		start_index = i
	for i in range(0,len(szlist)):
		if end_point < szlist[i][0]:
			break
		end_index = i
			
	elevation_part = []
	for i in range(start_index, end_index+1):
		elevation_part.append(szlist[i])
		
	return elevation_part
	