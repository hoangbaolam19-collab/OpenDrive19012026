import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt

from opendrive.submodule import clothoid
from opendrive.submodule import circle
from opendrive.submodule import line


def get_parametric_cubic_parameter(start_radius, end_radius, length):

	p0_x, p0_y, start_direction = clothoid.get_clothoid_point(start_radius, end_radius, length, 0)
	p3_x, p3_y, end_direction = clothoid.get_clothoid_point(start_radius, end_radius, length, length)
	point_length = length*0.25
	if point_length > 5.0:
		point_length = 5.0
		
	p1_x = p0_x + math.cos(start_direction)*point_length
	p1_y = p0_y + math.sin(start_direction)*point_length
	p2_x = p3_x - math.cos(end_direction)*point_length
	p2_y = p3_y - math.sin(end_direction)*point_length
	
	p0 = np.array([p0_x,p0_y])
	p1 = np.array([p1_x,p1_y])
	p2 = np.array([p2_x,p2_y])
	p3 = np.array([p3_x,p3_y])

	a = p0
	b = -3*p0 + 3*p1
	c = 3*p0 - 6*p1 + 3*p2
	d = -1*p0 + 3*p1 - 3*p2 + p3
	
	return a,b,c,d

def convert(road_data_df):

	open_drive_format_df = road_data_df.copy()

	data_size = open_drive_format_df.shape[0]
	open_drive_data_point_x = []
	open_drive_data_point_y = []
	
	for i in range(0, data_size-1):
		if open_drive_format_df.at[i,"type"] == "arc":
			end_point = i + 1
			result_x, result_y,arc_length,start_direction,end_direction = circle.road2arc(open_drive_format_df,i)
			open_drive_format_df.at[i,"initial_direction"]= start_direction
			open_drive_format_df.at[end_point,"initial_direction"]= end_direction
			open_drive_format_df.at[end_point,"x"] = result_x[-1]
			open_drive_format_df.at[end_point,"y"]= result_y[-1]
			open_drive_format_df.at[i,"length"] = arc_length
			open_drive_data_point_x.append(result_x)
			open_drive_data_point_y.append(result_y)
		elif open_drive_format_df.at[i,"type"] == "spiral" or open_drive_format_df.at[i,"type"] == "parametric_cubic":
			start_point = i
			end_point = i + 1
			result_x, result_y, result_L, start_direction, end_direction = clothoid.road2clothoid(open_drive_format_df, i)
			open_drive_format_df.at[end_point,"x"] = result_x[len(result_x)-1]
			open_drive_format_df.at[end_point,"y"]= result_y[len(result_x)-1]
			open_drive_format_df.at[start_point,"length"] = result_L
			open_drive_format_df.at[end_point,"initial_direction"]= end_direction
			open_drive_data_point_x.append(result_x)
			open_drive_data_point_y.append(result_y)
		elif open_drive_format_df.at[i,"type"] == "line":
			line_point = i
			end_point = i+1
			result_x, result_y, result_L, direction = line.road2line(open_drive_format_df, line_point)
			open_drive_format_df.at[line_point,"length"] = result_L
			open_drive_format_df.at[line_point,"initial_direction"]= direction
			open_drive_format_df.at[end_point,"initial_direction"]= direction
			open_drive_format_df.at[end_point,"x"] = result_x[-1]
			open_drive_format_df.at[end_point,"y"]= result_y[-1]
			open_drive_data_point_x.append(result_x)
			open_drive_data_point_y.append(result_y)
		
	return open_drive_data_point_x, open_drive_data_point_y, open_drive_format_df

def radius2curvature(radius):
	radius_max = 1e+12
	if abs(radius) > radius_max:
		return 0
	else:
		return 1/radius

def get_road_linkage_str(elementId, elementType, contactPoint):
	linkage_str = ""
	elemantType_str = "elementType=" + "\""+ elementType + "\" "
	elementId_str = "elementId="+ "\""+ elementId + "\""
	linkage_str += elemantType_str
	linkage_str += elementId_str
	if elementType == "road":
		contactPoint_str = " contactPoint="+ "\"" + contactPoint + "\""
		linkage_str += contactPoint_str
	return linkage_str
	
def get_predecessor_part(elementId, elementType, contactPoint):
	predecessor_part = "<predecessor "
	predecessor_part += get_road_linkage_str(elementId, elementType, contactPoint)
	predecessor_part += " />\n"
	return predecessor_part

def get_successor_part(elementId, elementType, contactPoint):
	successor_part = "<successor "
	successor_part += get_road_linkage_str(elementId, elementType, contactPoint)
	successor_part += " />\n"
	return successor_part

def get_geometry_parametric_cubic(a,b,c,d):
	aU_str = "aU=\""+str(a[0])+"\" "
	bU_str = "bU=\""+str(b[0])+"\" "
	cU_str = "cU=\""+str(c[0])+"\" "
	dU_str = "dU=\""+str(d[0])+"\" "
	aV_str = "aV=\""+str(a[1])+"\" "
	bV_str = "bV=\""+str(b[1])+"\" "
	cV_str = "cV=\""+str(c[1])+"\" "
	dV_str = "dV=\""+str(d[1])+"\" "
	pRange_str = "pRange=\"normalized\" "
	
	parametric_cubic_part = "<paramPoly3 "
	parametric_cubic_part += aU_str
	parametric_cubic_part += bU_str
	parametric_cubic_part += cU_str
	parametric_cubic_part += dU_str
	parametric_cubic_part += aV_str
	parametric_cubic_part += bV_str
	parametric_cubic_part += cV_str
	parametric_cubic_part += dV_str
	parametric_cubic_part += pRange_str
	parametric_cubic_part += "/>\n"
	return parametric_cubic_part
	
def get_geometry_spiral(start_radius, end_radius):
	curvStart_data = "curvStart=\"" + str(radius2curvature(start_radius)) + "\" "
	curvEnd_data = "curvEnd=\"" + str(radius2curvature(end_radius)) + "\" "
	curvature_data = curvStart_data + curvEnd_data
	spiral_part = "\t<spiral " + curvature_data + "/>\n"
	return spiral_part

def get_geometry_arc(radius):
	curvature_data =  "curvature=\"" + str(radius2curvature(radius)) + "\""
	arc_part = "<arc " + curvature_data + "/>\n"
	return arc_part

def get_geometry_line():
	return "\t<line />\n"

def get_center_lane(lanes_part_tab):
	tab = "\t"
	lane_part_tab = lanes_part_tab + tab
	link_part_tab = lane_part_tab + tab

	center_lane_str = lanes_part_tab
	center_lane_str += "<center>\n"
	center_lane_str += (lane_part_tab)
	center_lane_str += "<lane id=\"0\" type=\"none\" level=\"false\">\n"
	center_lane_str += (link_part_tab)
	center_lane_str += "<link>\n"
	center_lane_str += (link_part_tab)
	center_lane_str += "</link>\n"
	center_lane_str += (link_part_tab)
	center_lane_str += get_lane_roadMark(link_part_tab, "solid")
	center_lane_str += (lane_part_tab)
	center_lane_str += "</lane>\n"
	center_lane_str += lanes_part_tab
	center_lane_str += "</center>\n"

	return center_lane_str

def get_lane_width(width):
    
	offset_str = "sOffset=\""+str(width[0])+"\" "
	a_str = "a=\"" + str(width[1]) + "\" "
	b_str = "b=\"" + str(width[2]) + "\" "
	c_str = "c=\"" + str(width[3]) + "\" "
	d_str = "d=\"" + str(width[4]) + "\" />"
	lane_width = "<width "
	lane_width += offset_str
	lane_width += a_str
	lane_width += b_str
	lane_width += c_str
	lane_width += d_str
	lane_width += "\n"

	return lane_width

def get_lane_roadMark(roadMark_part_tab, type):
	
	roadMark_part = "<roadMark "
	roadMark_part += "sOffset=\"0.0000000000000000e+00\" "
	roadMark_part += "type=\"" + type + "\" "
	roadMark_part += "weight=\"standard\" "
	roadMark_part += "color=\"standard\" "
	roadMark_part += "width=\"1.2000000000000000e-01\" "
	
	if type == "solid":
		roadMark_part += "laneChange=\"none\" "
	else:
		roadMark_part += "laneChange=\"both\" "
		
	roadMark_part += "height=\"2.0000000000000000e-02\">\n"
	
	# Add type information
	roadMark_part += roadMark_part_tab
	roadMark_part += "\t<type name=\"" + type + "\" width=\"1.2000000000000000e-01\">\n"
	roadMark_part += roadMark_part_tab
	roadMark_part += "\t\t<line "
	
	if type == "solid":
		roadMark_part += "length=\"0.0000000000000000e+00\" space=\"0.0000000000000000e+00\" "
		roadMark_part += "tOffset=\"0.0000000000000000e+00\" sOffset=\"0.0000000000000000e+00\" "
		roadMark_part += "rule=\"no passing\" width=\"1.2000000000000000e-01\" />\n"
	else:
		roadMark_part += "length=\"4.0000000000000000e+00\" space=\"8.0000000000000000e+00\" "
		roadMark_part += "tOffset=\"0.0000000000000000e+00\" sOffset=\"0.0000000000000000e+00\" "
		roadMark_part += "rule=\"caution\" width=\"1.2000000000000000e-01\" />\n"
	
	roadMark_part += roadMark_part_tab
	roadMark_part += "\t</type>\n"
	roadMark_part += roadMark_part_tab
	roadMark_part += "</roadMark>"
	roadMark_part += "\n"

	return roadMark_part

def get_lane_str(lanes_part_tab, lane_list, t_direction):
	tab = "\t"
	lane_part_tab = lanes_part_tab + tab
	link_part_tab = lane_part_tab + tab
	roadMark_part_tab = lane_part_tab + tab
	linkage_part_tab = link_part_tab+tab
	
	lane_str = lanes_part_tab
	if t_direction > 0:
		lane_str += "<left>\n"
	else:
		lane_str += "<right>\n"
	    
	for i in range(0,len(lane_list)):
		id_str = "id=\"" + str(t_direction*(i+1)) + "\" "
		type_str = "type=\"" + lane_list[i][0] + "\" "
		level_str = "level=\"" + lane_list[i][1] + "\">"

		width = lane_list[i][2]

		lane_part = lane_part_tab
		lane_part += "<lane "
		lane_part += id_str
		lane_part += type_str
		lane_part += level_str
		lane_part += "\n"
		
		lane_part += (link_part_tab)
		lane_part += "<link>\n"
		
		linkage = lane_list[i][3]
		if len(linkage) == 2:
			predecessor = linkage[0]
			if predecessor != 0:
				predecessor_str = linkage_part_tab
				predecessor_str += "<predecessor id=\"" + str(predecessor) + "\" />\n"
				lane_part += predecessor_str
			successor = linkage[1]
			if successor != 0:
				successor_str = linkage_part_tab
				successor_str += "<successor id=\"" + str(successor) + "\" />\n"
				lane_part += successor_str
				
		lane_part += (link_part_tab)
		lane_part += "</link>\n"

		lane_part += link_part_tab
		lane_part += get_lane_width(width)

		lane_part += roadMark_part_tab
		if i == len(lane_list)-1:
			lane_part += get_lane_roadMark(roadMark_part_tab, "solid")
		else:
			lane_part += get_lane_roadMark(roadMark_part_tab, "broken")

		lane_part += lane_part_tab
		lane_part += "</lane>\n"

		lane_str += lane_part
	    
	lane_str += lanes_part_tab

	if t_direction > 0:
		lane_str += "</left>\n"
	else:
		lane_str += "</right>\n"
	return lane_str

def get_lane_offset_part(offset_parameter):
	s_str = "s=\""+str(offset_parameter[0])+"\" "
	a_str = "a=\""+str(offset_parameter[1])+"\" "
	b_str = "b=\""+str(offset_parameter[2])+"\" "
	c_str = "c=\""+str(offset_parameter[3])+"\" "
	d_str = "d=\""+str(offset_parameter[4])+"\" "

	lane_offset_str = "<laneOffset "
	lane_offset_str += s_str
	lane_offset_str += a_str
	lane_offset_str += b_str
	lane_offset_str += c_str
	lane_offset_str += d_str
	lane_offset_str += "/>\n"

	return lane_offset_str

def get_elevation_part_str(elevation_parameter):
	s_str = "s=\""+str(elevation_parameter[0])+"\" "
	a_str = "a=\""+str(elevation_parameter[1])+"\" "
	b_str = "b=\""+str(elevation_parameter[2])+"\" "
	c_str = "c=\""+str(elevation_parameter[3])+"\" "
	d_str = "d=\""+str(elevation_parameter[4])+"\" "
	elevation_part = "<elevation "
	elevation_part += s_str
	elevation_part += a_str
	elevation_part += b_str
	elevation_part += c_str
	elevation_part += d_str
	elevation_part += "/>\n"
	
	return elevation_part
	
def get_elevation_profile_str( elevation_tab, elevation_parameter_list ):
	tab ="\t"
	
	elevation_profile = elevation_tab
	elevation_profile += "<elevationProfile>\n"
	for i in range(0, len(elevation_parameter_list)):
		elevation_part = (elevation_tab+tab)
		elevation_part += get_elevation_part_str(elevation_parameter_list[i])
		elevation_profile += elevation_part
	elevation_profile += elevation_tab
	elevation_profile += "</elevationProfile>\n"
	
	return elevation_profile

def convert_road_part(open_drive_format_df, road_no, junction_no, predecessor, succesor, lane_offset, left_lane, right_lane, elevation, speed):

	ng_data_list = []
	
	tab = "\t"
	road_part_tab = tab
	segment_count = open_drive_format_df.shape[0] - 1
	open_drive_format_str = ""
	
	total_length = 0
	
	for point_index in range(0,segment_count):
		length = open_drive_format_df.at[point_index,"length"]
		total_length += length
	if total_length > 0:
		road_part = road_part_tab + "<"
		road_id = "road id=\"" + str(road_no) + "\" "
		junction = "junction=\"" + str(junction_no) + "\" "
		road_length = "length=\"" + str(total_length) + "\" "
		road_name = "name=\"Road " + str(road_no) + "\" "
		road_rule = "rule=\"LHT\""
		
		road_part += (road_id + junction + road_length + road_name + road_rule +">")

		open_drive_format_str += (road_part+"\n")

		link_part_tab = road_part_tab+tab
		link_part = link_part_tab + "<link>\n"
		open_drive_format_str += link_part
		predecessor_part_tab = link_part_tab + tab
		elementId = str(predecessor[0])
		elementType = predecessor[1]
		contact_point = predecessor[2]
		    
		if elementType != "none":
			predecessor_part = predecessor_part_tab
			predecessor_part += get_predecessor_part(elementId, elementType, contact_point)
			open_drive_format_str += predecessor_part

		successor_part_tab = link_part_tab + tab
		elementId = str(succesor[0])
		elementType = succesor[1]
		contact_point = succesor[2]
		 
		if elementType != "none":
			successor_part = successor_part_tab
			successor_part += get_successor_part(elementId, elementType, contact_point)
			open_drive_format_str += successor_part

		open_drive_format_str += link_part_tab+"</link>\n"

		for i in range(len(speed)):
			type_part_tab = road_part_tab+tab
			type_part = type_part_tab + "<type "
			type_part += "s=\"" + str(speed[i][1]) + "\" type=\"town\">\n"
			open_drive_format_str += type_part

			speed_part_tab = type_part_tab + tab
			speed_part = speed_part_tab + "<speed "
			speed_part += "max=\"" + str(abs(speed[i][0])) + "\" unit=\"km/h\" />\n"
			open_drive_format_str += speed_part

			open_drive_format_str += type_part_tab+"</type>\n"


		plan_view_tab = road_part_tab+tab
		plan_view = plan_view_tab + "<planView>\n"
		open_drive_format_str += plan_view
			
		s = 0
		for point_index in range(0,segment_count):
			data_type = open_drive_format_df.at[point_index,"type"]
			x = open_drive_format_df.at[point_index,"x"]
			y = open_drive_format_df.at[point_index,"y"]
			hdg = open_drive_format_df.at[point_index,"initial_direction"]
			length = open_drive_format_df.at[point_index,"length"]
			start_radius = open_drive_format_df.at[point_index,"radius"]
			end_radius = open_drive_format_df.at[point_index+1,"radius"]
			
			if length > 0:
				geometry_data_tab = plan_view_tab+tab
				
				s_str = "s=\"" + str(s) + "\" "
				x_str = "x=\"" + str(x) + "\" "
				y_str = "y=\"" + str(y) + "\" "
				hdg_str = "hdg=\"" + str(np.deg2rad(hdg)) +  "\" "
				length_str = "length=\"" + str(length) + "\""
				
				geometry_data = geometry_data_tab + "<geometry "+ s_str + x_str + y_str + hdg_str + length_str + ">\n"
				open_drive_format_str += geometry_data
				
				if data_type == "spiral":
					spiral_part = geometry_data_tab
					spiral_part += get_geometry_spiral(start_radius, end_radius)
					open_drive_format_str += spiral_part
				elif data_type == "arc":
					arc_part = geometry_data_tab
					arc_part += get_geometry_arc(start_radius)
					open_drive_format_str += arc_part
				elif data_type == "line":
					line_part = geometry_data_tab
					line_part += get_geometry_line()
					open_drive_format_str += line_part
				elif data_type == "parametric_cubic":
					a,b,c,d = get_parametric_cubic_parameter(start_radius, end_radius, length)
					parametric_part = geometry_data_tab
					parametric_part += get_geometry_parametric_cubic(a,b,c,d)
					open_drive_format_str += parametric_part

				s += length

				open_drive_format_str += (geometry_data_tab+"</geometry>\n")
		
		open_drive_format_str += (plan_view_tab + "</planView>\n")
	
		elevation_profile_tab = road_part_tab+tab
		open_drive_format_str += get_elevation_profile_str(elevation_profile_tab, elevation)
	
		lanes_part_tab = road_part_tab+tab
		lane_offset_tab = lanes_part_tab+tab
		lane_section_tab = lanes_part_tab+tab
		lane_part_tab = lane_section_tab+tab
		
		lanes_str = lanes_part_tab
		lanes_str += "<lanes>\n"
		lanes_str += lane_offset_tab
		lanes_str += get_lane_offset_part(lane_offset)
		
		lanes_str += lane_section_tab
		lanes_str += "<laneSection s=\"0.0\">\n"
		
		if len(left_lane) > 0:
			t_direction = 1
			lanes_str += get_lane_str(lane_part_tab, left_lane, t_direction)
		lanes_str += get_center_lane(lane_part_tab)
		if len(right_lane) > 0:
			t_direction = -1
			lanes_str += get_lane_str(lane_part_tab, right_lane, t_direction)

		lanes_str += lane_section_tab
		lanes_str += "</laneSection>\n"
		
		lanes_str += lanes_part_tab
		lanes_str += "</lanes>\n"
		
		open_drive_format_str += lanes_str
		
		open_drive_format_str += (road_part_tab + "</road>\n")
	else:
		ng_data_list.append(open_drive_format_df)
	    
	return open_drive_format_str, ng_data_list
	
def get_junction_connect_str(connection_tab, connection_id, incoming_road, connecting_road, contact_point, lane_from, lane_to):
	tab = "\t"
	
	id_str = "id=\"" + str(connection_id) + "\" "
	incoming_str = "incomingRoad=\"" + str(incoming_road) +"\" "
	connecting_str = "connectingRoad=\"" + str(connecting_road) + "\" "
	contact_str = "contactPoint=\"" + contact_point + "\""
	lane_from_str = "from=\"" + str(lane_from) + "\" "
	lane_to_str = "to=\"" + str(lane_to) + "\""
	
	connection_str = connection_tab
	
	connection_str += "<connection "
	connection_str += id_str
	connection_str += incoming_str
	connection_str += connecting_str
	connection_str += contact_str
	connection_str += ">\n"
	
	lane_link_tab = connection_tab + tab
	lane_link_str = lane_link_tab
	lane_link_str += "<laneLink "
	lane_link_str += lane_from_str
	lane_link_str += lane_to_str
	lane_link_str += " />\n"
	
	connection_str += lane_link_str
	connection_str += connection_tab
	connection_str += "</connection>\n"
	
	return connection_str
		
def convert_junction_part(junction_no, junction_road_list):
	tab = "\t"
	junction_tab = tab
	junction_id_str = "id=\"" + str(junction_no) + "\" "
	junction_name_str = "name=\"junction" + str(junction_no) + "\""
	
	junction_str = junction_tab
	junction_str += "<junction "
	junction_str += junction_id_str
	junction_str += junction_name_str
	junction_str += ">\n"
	
	connection_tab = junction_tab + tab
	connection_id = 0
	for junction_road in junction_road_list:
		connecting_road_no = junction_road[0]
		road_linkage = junction_road[1]
		predecessor = road_linkage[0]
		incoming_road_no = predecessor[0]
		lane = junction_road[2]
		lane_offset = lane[0]
		left_lane = lane[1]

		if predecessor[1] == "road" and len(left_lane) > 0:
			for i in range(0, len(left_lane)):
				contact_point = "start"
				lane_linkage = left_lane[i][3]
				lane_to = 1+i
				lane_from = lane_linkage[0]
				connection_str = get_junction_connect_str(connection_tab, connection_id, incoming_road_no, connecting_road_no, contact_point, lane_from, lane_to)
				junction_str += connection_str
		
				connection_id += 1
		
	junction_str += junction_tab
	junction_str += "</junction>\n"
	
	return junction_str	

def output_xml(road_part_str, file_path, geo_reference=None):
	total_length = 0
	open_drive_format_str = "<?xml version='1.0' encoding='utf-8'?>\n"
	open_drive_format_str += "<OpenDRIVE>\n"
	tab = "\t"
	
	header_line = "<header date=\"2022-9-22T13:37:24\" east=\"2.5e+3\" name=\"test\" north=\"2.5e+3\" revMajor=\"1\" revMinor=\"6\" south=\"-2.5e+3\" vendor=\"Zenrin-Datacom\" version=\"1\" west=\"-2.5e+3\">"
	open_drive_format_str += tab + header_line + "\n"
	if geo_reference:
		open_drive_format_str += tab + tab + "<geoReference><![CDATA[\n"
		open_drive_format_str += tab + tab + geo_reference + "\n"
		open_drive_format_str += tab + tab + "]]></geoReference>\n"
	open_drive_format_str += tab + "</header>\n"

	open_drive_format_str += road_part_str
	
	open_drive_format_str += "</OpenDRIVE>"
	
	f = open(file_path, 'w')
	f.write(open_drive_format_str)
	f.close()
	
def output_xml4viewer(open_drive_format_df, start_index, end_index, file_path, geo_reference=None):

	total_length = 0
	open_drive_format_str = "<?xml version='1.0' encoding='utf-8'?>\n"
	open_drive_format_str += "<OpenDRIVE>\n"
	tab = "\t"
	
	header_line = "<header date=\"2022-9-22T13:37:24\" east=\"2.5e+3\" name=\"test\" north=\"2.5e+3\" revMajor=\"1\" revMinor=\"6\" south=\"-2.5e+3\" vendor=\"Zenrin-Datacom\" version=\"1\" west=\"-2.5e+3\">"
	open_drive_format_str += tab + header_line + "\n"
	if geo_reference:
		open_drive_format_str += tab + tab + "<geoReference><![CDATA[\n"
		open_drive_format_str += tab + tab + geo_reference + "\n"
		open_drive_format_str += tab + tab + "]]></geoReference>\n"
	open_drive_format_str += tab + "</header>\n"

	for point_index in range(start_index,end_index-1):
		data_type = open_drive_format_df.at[point_index,"type"]
		x = open_drive_format_df.at[point_index,"x"]
		y = open_drive_format_df.at[point_index,"y"]
		hdg = open_drive_format_df.at[point_index,"initial_direction"]
		length = open_drive_format_df.at[point_index,"length"]

		road_part_tab = (tab+tab)
		road_part = road_part_tab + "<"
		road_id = "road id=\"" + str(point_index) + "\" "
		junction = "junction=\"-1\" "
		road_length = "length=\"" + str(length) + "\" "
		road_name = "name=\"Road " + str(point_index) + "\""
		road_part += (road_id + junction + road_length + road_name +">")

		open_drive_format_str += (road_part+"\n")

		start_radius = open_drive_format_df.at[point_index,"radius"]
		end_radius = open_drive_format_df.at[point_index+1,"radius"]

		total_length += length

		plan_view_tab = road_part_tab+tab
		plan_view = plan_view_tab + "<planView>\n"
		open_drive_format_str += plan_view

		geometry_data_tab = plan_view_tab

		x_data = "x=\"" + str(x) + "\" "
		y_data = "y=\"" + str(y) + "\" "
		hdg_data = "hdg=\"" + str(np.deg2rad(hdg)) +  "\" "
		length_data = "length=\"" + str(length) + "\" "

		geometry_data = geometry_data_tab + "<geometry s=\"0.0\" " + x_data + y_data + hdg_data + length_data + ">\n"
		open_drive_format_str += geometry_data
		
		if data_type == "spiral":
			curvStart_data = "curvStart=\"" + str(radius2curvature(start_radius)) + "\" "
			curvEnd_data = "curvEnd=\"" + str(radius2curvature(end_radius)) + "\" "
			curvature_data = curvStart_data + curvEnd_data
			spiral_part = geometry_data_tab + "<spiral " + curvature_data + "/>\n"
			open_drive_format_str += spiral_part
		elif data_type == "arc":
			curvature_data =  "curvature=\"" + str(radius2curvature(start_radius)) + "\""
			arc_part = geometry_data_tab + "<arc " + curvature_data + "/>\n"
			open_drive_format_str += arc_part
		elif data_type == "line":
			line_data = geometry_data_tab + "<line/>\n"
			open_drive_format_str += line_data
        
		open_drive_format_str += (geometry_data_tab+"</geometry>\n")
		open_drive_format_str += (plan_view_tab + "</planView>\n")
		open_drive_format_str += (road_part_tab + "</road>\n")
		
	open_drive_format_str += "</OpenDRIVE>"
	
	f = open(file_path, 'w')
	f.write(open_drive_format_str)
	f.close()