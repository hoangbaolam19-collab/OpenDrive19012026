import pandas as pd
import numpy as np
import math

def direction_variation2variation_type(direction_variation):
	
	if abs(direction_variation) > 160:
		variation_type = "uturn"
	elif direction_variation < 0.0:
		variation_type = "right_turn"
	elif direction_variation > 0.0:
		variation_type = "left_turn"
	else:
		variation_type = "straight"
	return variation_type

def get_relative_left_turn_count(direction_variation, direction_variation_df):
	return len((direction_variation_df[direction_variation_df["direction_variation"]>direction_variation]))
	
def get_relative_right_turn_count(direction_variation, direction_variation_df):
	return len((direction_variation_df[direction_variation_df["direction_variation"]<direction_variation]))

def get_incoming_1lane(direction_variation, direction_variation_df):
	relative_straight_count = len(direction_variation_df[abs(direction_variation_df["direction_variation"])<abs(direction_variation)-7.0])
	if relative_straight_count == 0:
		if direction_variation > -20.0:
			variation_type = "straight"
		else:
			left_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"] > 0]))
			if left_turn_count == 0:
				variation_type = "straight"
			else:
				variation_type = direction_variation2variation_type(direction_variation)
	else:
		variation_type = direction_variation2variation_type(direction_variation)
	    
	lane_index = [0]
	    
	return variation_type, lane_index

def get_incoming_2lane(direction_variation, direction_variation_df):
	relative_straight_count = len(direction_variation_df[abs(direction_variation_df["direction_variation"])<abs(direction_variation)-7.0])
	if relative_straight_count == 0:
		if direction_variation > -20.0:
			variation_type = "straight"
		else:
			left_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"] > 0]))
			if left_turn_count == 0:
				variation_type = "straight"
			else:
				variation_type = direction_variation2variation_type(direction_variation)
	else:
		variation_type = direction_variation2variation_type(direction_variation)
	    
	if variation_type == "straight":
		lane_index = [0,1]
	elif variation_type == "left_turn":
		relative_right_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"]<direction_variation]))
		if relative_right_turn_count > 0:
			lane_index = [1]
		else:
			lane_index = [0,1]         
	elif variation_type == "right_turn":
		another_type_count = len((direction_variation_df[direction_variation_df["variation_type"]!="right_turn"]))
		right_turn_count = len((direction_variation_df[direction_variation_df["variation_type"]=="right_turn"]))
		relative_left_turn_count  = len((direction_variation_df[direction_variation_df["direction_variation"]>direction_variation]))
		if relative_left_turn_count > 0:            
			lane_index = [0]
		else:
			lane_index = [0,1]
	else:
		lane_index = [0]
	    
	return variation_type, lane_index
	
def get_incoming_4lane(direction_variation, direction_variation_df):
	relative_straight_count = len(direction_variation_df[abs(direction_variation_df["direction_variation"])<abs(direction_variation)-7.0])
	if relative_straight_count == 0:
		if direction_variation > -20.0:
			variation_type = "straight"
		else:
			left_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"] > 0]))
			if left_turn_count == 0:
				variation_type = "straight"
			else:
				variation_type = direction_variation2variation_type(direction_variation)
	else:
		variation_type = direction_variation2variation_type(direction_variation)
	    
	if variation_type == "straight":
		relative_right_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"]<direction_variation-7.0]))
		valid_right_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"]<-15.0]))
		if relative_right_turn_count > 0 and valid_right_turn_count > 0:
			lane_index = [1,2,3]
		else:
			lane_index = [0,1,2,3]         
	elif variation_type == "left_turn":
		relative_right_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"]<direction_variation]))
		if relative_right_turn_count > 0:
			lane_index = [3]
		else:
			lane_index = [0,1,2,3]         
	elif variation_type == "right_turn":
		another_type_count = len((direction_variation_df[direction_variation_df["variation_type"]!="right_turn"]))
		right_turn_count = len((direction_variation_df[direction_variation_df["variation_type"]=="right_turn"]))
		relative_left_turn_count  = len((direction_variation_df[direction_variation_df["direction_variation"]>direction_variation]))
		if relative_left_turn_count > 0:            
			lane_index = [0]
		else:
			lane_index = [0,1,2,3]
	else:
		lane_index = [0]
	    
	return variation_type, lane_index
	
def get_outgoing_1lane(direction_variation, direction_variation_df):
	relative_straight_count = len(direction_variation_df[abs(direction_variation_df["direction_variation"])<abs(direction_variation)-7.0])
	if relative_straight_count == 0:
		if direction_variation > -20.0:
			variation_type = "straight"
		else:
			left_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"] > 0]))
			if left_turn_count == 0:
				variation_type = "straight"
			else:
				variation_type = direction_variation2variation_type(direction_variation)
	else:
		variation_type = direction_variation2variation_type(direction_variation)
	    
	lane_index = [0]
	    
	return variation_type, lane_index
	
def get_outgoing_2lane(direction_variation, direction_variation_df):
	relative_straight_count = len(direction_variation_df[abs(direction_variation_df["direction_variation"])<abs(direction_variation)-7.0])
	if relative_straight_count == 0:
		if direction_variation > -20.0:
			variation_type = "straight"
		else:
			left_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"] > 0]))
			if left_turn_count == 0:
				variation_type = "straight"
			else:
				variation_type = direction_variation2variation_type(direction_variation)
	else:
		variation_type = direction_variation2variation_type(direction_variation)
	    
	if variation_type == "straight":
		lane_index = [0,1]
	elif variation_type == "left_turn":
		relative_right_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"]<direction_variation]))
		lane_index = [0,1]         
	elif variation_type == "right_turn":
		another_type_count = len((direction_variation_df[direction_variation_df["variation_type"]!="right_turn"]))
		right_turn_count = len((direction_variation_df[direction_variation_df["variation_type"]=="right_turn"]))
		relative_left_turn_count  = len((direction_variation_df[direction_variation_df["direction_variation"]>direction_variation]))
		if relative_left_turn_count > 0:            
			lane_index = [0]
		else:
			lane_index = [0,1]
	else:
		lane_index = [0]
	    
	return variation_type, lane_index
	
def get_outgoing_4lane(direction_variation, direction_variation_df):
	relative_straight_count = len(direction_variation_df[abs(direction_variation_df["direction_variation"])<abs(direction_variation)-7.0])
	if relative_straight_count == 0:
		if direction_variation > -20.0:
			variation_type = "straight"
		else:
			left_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"] > 0]))
			if left_turn_count == 0:
				variation_type = "straight"
			else:
				variation_type = direction_variation2variation_type(direction_variation)
	else:
		variation_type = direction_variation2variation_type(direction_variation)
	    
	if variation_type == "straight":
		lane_index = [0,1,2,3]         
	elif variation_type == "left_turn":
		relative_right_turn_count = len((direction_variation_df[direction_variation_df["direction_variation"]<direction_variation]))
		if relative_right_turn_count > 0:
			lane_index = [3]
		else:
			lane_index = [0,1,2,3]         
	elif variation_type == "right_turn":
		another_type_count = len((direction_variation_df[direction_variation_df["variation_type"]!="right_turn"]))
		right_turn_count = len((direction_variation_df[direction_variation_df["variation_type"]=="right_turn"]))
		relative_left_turn_count  = len((direction_variation_df[direction_variation_df["direction_variation"]>direction_variation]))
		relative_right_turn_count  = len((direction_variation_df[direction_variation_df["direction_variation"]<direction_variation]))
		if relative_left_turn_count > 0:
			if relative_right_turn_count == 0:
				lane_index = [0]
			else:
				lane_index = [0,1]
		else:
			lane_index = [0,1,2,3]
	else:
		lane_index = [0]
	    
	return variation_type, lane_index
	
def get_incoming_lane_index(incoming_lane_count, direction_variation, direction_variation_df):
	
	if incoming_lane_count < 2:
		return get_incoming_1lane(direction_variation, direction_variation_df)
	elif incoming_lane_count == 2:
		return get_incoming_2lane(direction_variation, direction_variation_df)
	elif incoming_lane_count > 2:
		return get_incoming_4lane(direction_variation, direction_variation_df)
		
def get_outgoing_lane_index(outgoing_lane_count, direction_variation, direction_variation_df):
	if outgoing_lane_count < 2:
		return get_outgoing_1lane(direction_variation, direction_variation_df)
	elif outgoing_lane_count == 2:
		return get_outgoing_2lane(direction_variation, direction_variation_df)
	elif outgoing_lane_count > 2:
		return get_outgoing_4lane(direction_variation, direction_variation_df)
	