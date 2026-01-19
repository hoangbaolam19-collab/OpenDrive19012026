import pandas as pd
import numpy as np
import math

def get_parameter(p0,p1,p2,p3):
	a = p0
	b = -3*p0 + 3*p1
	c = 3*p0 - 6*p1 + 3*p2
	d = -1*p0 + 3*p1 - 3*p2 + p3

	return a,b,c,d
	
def get_curve(point_list):
	if len(point_list) > 3:
		p0 = np.array(point_list[0])
		p1 = np.array(point_list[1])
		p2 = np.array(point_list[-2])
		p3 = np.array(point_list[-1])
		a,b,c,d = get_parameter(p0,p1,p2,p3)
		
	elif len(point_list) == 3:
		p0 = np.array(point_list[0])
		pm = np.array(point_list[1])
		p3 = np.array(point_list[2])
		p1 = (p0 + pm)*0.5
		p2 = (pm + p3)*0.5
		
		a,b,c,d = get_parameter(p0,p1,p2,p3)
		
	elif len(point_list) == 2:
		p0 = np.array(point_list[0])
		p1 = np.array(point_list[1])
		diff = p1 - p0
		length = math.sqrt(diff[0]**2+diff[1]**2)
		a = p0
		b = [1*length,diff[1]/diff[0]*length]
		c = np.array([0,0])
		d = np.array([0,0])
	elif len(point_list) == 1:
		a = np.array(point_list[0])
		b = np.array([0,0])
		c = np.array([0,0])
		d = np.array([0,0])
	else:
		a = np.array([0,0])
		b = np.array([0,0])
		c = np.array([0,0])
		d = np.array([0,0])
	
	return a,b,c,d
	
def get_point(a,b,c,d):
	t = np.linspace(0,1,10)
	point_x = a[0] + b[0]*t + c[0]*(t**2) +d[0]*(t**3)
	point_y = a[1] + b[1]*t + c[1]*(t**2) +d[1]*(t**3)
	
	return point_x, point_y