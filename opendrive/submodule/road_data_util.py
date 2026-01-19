import json
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

def get_roadwidth( code, lane ):
	if code == 0:
		width = 3.0
		width = 2.0
	elif code == 1:
		width = 4.5
		width = 4.0
	elif code == 2:
		width = 9.5
		width = 7.5
	elif code == 3:
		width = 13.0
		if lane*2.5 > width:
			width = lane*2.5
	else:
		width = lane*2.5
		
	return width
    
def get_road_data(j_data):
	road_data_list = []
	for link_list in j_data["item"]:
		for link_data in link_list:
			code = link_data["link"]["code"]
			polyline = link_data["link"]["line"]
			lane = link_data["link"]["numberOfLanes"]
			width = get_roadwidth(link_data["link"]["roadWidth"], lane)
			order = link_data["link"]["order"]
			code = link_data["link"]["code"]
			link_length = link_data["link"]["distance"]
			is_highway = link_data["link"]["limitedHighway"]
			one_way_code = link_data["link"]["onewayCode"]
			roadelevation = link_data["link"]["adas"]["roadelevation"]
			roadelevation_list = []
			for element in roadelevation:
				roadelevation_list.append([element["lat"],element["lon"],float(element["elevation"])/1000.0])
			road_data_list.append([code, order, polyline, lane, width, link_length, one_way_code, is_highway, roadelevation_list])
	
	road_data_df = pd.DataFrame(road_data_list)
	road_data_df.columns = ["code","order", "polyline", "lane", "width", "length", "oneway_code", "is_highway", "elevation"]

	return road_data_df
    
def get_merged_road_data(j_data_list,highway_only = True):
	registered_code = set()
	road_data_list = []
	duplicated_road_list = []
	print("Merge and classify road data.") 
	for j_data in tqdm(j_data_list):
		for link_list in j_data["item"]:
			for link_data in link_list:
				code = link_data["link"]["code"]
				polyline = link_data["link"]["line"]
				lane = link_data["link"]["numberOfLanes"]
				width = get_roadwidth(link_data["link"]["roadWidth"], lane)
				order = link_data["link"]["order"]
				code = link_data["link"]["code"]
				link_length = link_data["link"]["distance"]
				is_highway = link_data["link"]["limitedHighway"]
				one_way_code = link_data["link"]["onewayCode"]
				roadType = link_data["link"]["roadType"]["code"]
				roadelevation = link_data["link"]["adas"]["roadelevation"]
				default_speed = -100 if roadType in ['0', '1'] else -60
				adas_data = link_data.get("link", {}).get("adas", {})
				maxspeed_list = adas_data.get("maxspeedFront", [{"limit": default_speed}])
				if isinstance(maxspeed_list, list) and len(maxspeed_list) > 0:
					speed = maxspeed_list[0].get("limit", default_speed)
				else:
					speed = default_speed
				roadelevation_list = []
				for element in roadelevation:
					roadelevation_list.append([element["lat"],element["lon"],float(element["elevation"])/1000.0])
				if highway_only:
					if roadType == '0' or  roadType == '1':
						if not code in registered_code:    
		
							road_data_list.append([order, polyline, lane, width, link_length, one_way_code, is_highway, roadelevation_list,roadType,speed])
							registered_code.add(code)
						else:
							duplicated_road_list.append([order, polyline, lane, width, link_length, one_way_code, is_highway, roadelevation_list,roadType,speed])
				else:
					if not code in registered_code:    
	
						road_data_list.append([order, polyline, lane, width, link_length, one_way_code, is_highway, roadelevation_list,roadType,speed])
						registered_code.add(code)
					else:
						duplicated_road_list.append([order, polyline, lane, width, link_length, one_way_code, is_highway, roadelevation_list,roadType,speed])
		road_data_df = []
		duplicated_road_df = []
		if len(road_data_list) > 0:
			road_data_df = pd.DataFrame(road_data_list)
			road_data_df.columns = ["order", "polyline", "lane", "width", "length", "oneway_code", "is_highway", "elevation","roadType","speed"]
		if len(duplicated_road_list) > 0:
			duplicated_road_df = pd.DataFrame(duplicated_road_list)
			duplicated_road_df.columns = ["order", "polyline", "lane", "width", "length", "oneway_code", "is_highway", "elevation","roadType","speed"]
	return road_data_df, duplicated_road_df


def get_merged_multipoint_road_data(j_data):
	registered_code = set()
	road_data_list = []
	duplicated_road_list = []

	for j_data_item in j_data["item"]:
		for link_data in j_data_item:
			code = link_data["link"]["code"]
			polyline = link_data["link"]["line"]
			lane = link_data["link"]["numberOfLanes"]
			width = get_roadwidth(link_data["link"]["roadWidth"], lane)
			order = link_data["link"]["order"]
			link_length = link_data["link"]["distance"]
			is_highway = link_data["link"]["limitedHighway"]
			one_way_code = link_data["link"]["onewayCode"]
			roadelevation = link_data["link"]["adas"]["roadelevation"]
			roadelevation_list = []
			for element in roadelevation:
				roadelevation_list.append([element["lat"],element["lon"],float(element["elevation"])/1000.0])
			if not code in registered_code:    
				road_data_list.append([order, polyline, lane, width, link_length, one_way_code, is_highway, roadelevation_list,code])
				registered_code.add(code)
			else:
				duplicated_road_list.append([order, polyline, lane, width, link_length, one_way_code, is_highway, roadelevation_list,code])
		road_data_df = []
		duplicated_road_df = []
		if len(road_data_list) > 0:
			road_data_df = pd.DataFrame(road_data_list)
			road_data_df.columns = ["order", "polyline", "lane", "width", "length", "oneway_code", "is_highway", "elevation","code"]
		if len(duplicated_road_list) > 0:
			duplicated_road_df = pd.DataFrame(duplicated_road_list)
			duplicated_road_df.columns = ["order", "polyline", "lane", "width", "length", "oneway_code", "is_highway", "elevation","code"]
	return road_data_df, duplicated_road_df