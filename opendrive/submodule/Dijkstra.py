import numpy as np
import pandas as pd
import math
import heapq

class DijkstraNode(object):
	def __init__(self, node_id, cost ):
		self.id = node_id
		self.cost = cost
		self.next = []
		self.state = 3
		self.total_cost = 1e+16
		self.previous = 0xFFFF
		
	def __lt__(self, other):
		return self.total_cost < other.total_cost

class Dijkstra(object):
	
	def __init__(self, start_polyline):
	
		start_node = DijkstraNode(start_polyline[0], start_polyline[1])
		self.open_list = []
		self.close_list = dict()
		self.node_dict = dict()
		
		self.open_list.append(start_node)
		heapq.heapify(self.open_list)
		
		self.node_dict[start_node.id] = start_polyline
		self.top_node = start_node
		
	def get_next(self, next_polyline_list ):
		next_node_list = []
		for i in range(0, len(next_polyline_list)):
			next_node = DijkstraNode(next_polyline_list[i][0], next_polyline_list[i][1])
			next_node_list.append(next_node)
			self.node_dict[next_node.id] = next_polyline_list[i]
		
		return next_node_list
		
	def pop_node(self):
		result = False
		
		if len(self.open_list) > 0:
			self.top_node = heapq.heappop(self.open_list)
			result = True
			
		result_node = self.node_dict[self.top_node.id]
		return result, result_node
		
	def update(self, next_list):
		
		next_node_list = self.get_next(next_list)
		for i in range(0, len(next_node_list)):
			self.top_node.next.append(next_node_list[i].id)
			next_node_list[i].state = 2
			next_node_list[i].total_cost = self.top_node.total_cost + next_node_list[i].cost
			next_node_list[i].previous = self.top_node.id
			heapq.heappush(self.open_list, next_node_list[i])
			
		self.close_list[self.top_node.id] = self.top_node
		
	def get_path(self):
		result = []
		result.append(self.node_dict[self.top_node.id])
		previous_id = self.top_node.previous
		
		for i in range( 0, len(self.close_list)):
			if previous_id in self.close_list.keys():
				current_id = previous_id
				result.insert(0, self.node_dict[current_id])
				previous_id = self.close_list[current_id].previous
			else:
				break
		
		return result