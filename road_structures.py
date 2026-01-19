import sys
import pandas as pd
from tqdm import tqdm
from geopy.distance import geodesic
import matplotlib.pyplot as plt
from typing import List, Dict, Optional

sys.path.append("../")
sys.path.append("submodule")

# Local imports
from submodule import vincenty_method as vm
from submodule import curvature_culc_func as ccf
from navimap import NaviMap
from merge_structure import MergeStructure
from branch_structure import BranchStructure
from merge_branch_structure import MergeBranchStructure
from mainlane_structure import MainLaneStructure


class RoadStructures:
    """Class to manage and process road structures from navigation map data."""

    def __init__(self):
        """Initialize RoadStructures with empty lists and NaviMap instance."""
        self.obj_navi_map = NaviMap()  # Initialize NaviMap instance
        self.str_obj_mainlane_list: List = []
        self.str_obj_branch_list: List = []
        self.str_obj_merge_list: List = []
        self.connect_merge_branch_list: List = []
        self._connect_branch_branch_index_ls: List = []
        self._connect_merge_merge_index_ls: List = []
        self._index: List = []

    def make_road_structures(self, latlon_range: List[float], road_condition: str, highway_only: bool, data_path: str, meshcode: str) -> None:
        """
        Create road structures based on specified parameters.

        Args:
            latlon_range: List of latitude/longitude bounds
            road_condition: Type of road condition to process
            highway_only: Whether to process only highways
        """
        self.obj_navi_map.make_navi_map(latlon_range, road_condition, highway_only, data_path, meshcode)

        if road_condition == "mainlane":
            self._process_mainlane()
        elif road_condition == "route":
            self._process_route()

    def _process_mainlane(self):
        """Process mainlane road structures"""
        # Initialize road structure objects for each node
        for i in range(len(self.obj_navi_map.obj_node_combine_data_list)):
            self.str_obj_mainlane_list.append(MainLaneStructure())

        print("Generate the road structure for the mainlane.")
        # Create road structure for each node in obj_node_list
        for i in tqdm(range(len(self.str_obj_mainlane_list))):
            self.str_obj_mainlane_list[i].make_mainlane_structure(self.obj_navi_map.obj_node_combine_data_list[i])

        self._remove_error_mainlanes()

    def _remove_error_mainlanes(self):
        """Remove mainlane structures with errors"""
        for i in range(len(self.str_obj_mainlane_list) - 1, -1, -1):
            if self.str_obj_mainlane_list[i].error_is != "None":
                self.str_obj_mainlane_list.pop(i)
                self.obj_navi_map.obj_node_combine_data_list.pop(i)

    def _process_route(self):
        """Process route structures including branches and merges"""

        self._process_branch_structures()
        self._process_branch_connections()
        self._process_merge_structures()
        self._process_merge_connections()
        self._process_branch_merge_connections()
        self._search_merge_and_branch_lists()
        self._remove_coinciding_main_lines()     
        self._process_mainlane_connections() 

    def _process_branch_structures(self):
        """Initialize and process branch structures"""
        # Initialize branch structures
        for i in range(len(self.obj_navi_map.obj_node_data_branch_list)):
            self.str_obj_branch_list.append(BranchStructure())

        print("Generate the road structure for the branch.")
        # Create branch structure for each element
        for i in tqdm(range(len(self.str_obj_branch_list))):
            self.str_obj_branch_list[i].make_branch_structure(self.obj_navi_map.obj_node_data_branch_list[i])

        self._remove_error_branches()

    def _remove_error_branches(self):
        """Remove branch structures with errors"""
        for i in range(len(self.str_obj_branch_list) - 1, -1, -1):
            if self.str_obj_branch_list[i].error_is != "None":
                meshcode = self.obj_navi_map.obj_node_data_branch_list[i].meshcode
                nodeno = self.obj_navi_map.obj_node_data_branch_list[i].nodeno
                print(f"{nodeno} in {meshcode} has error: {self.str_obj_branch_list[i].error_is}")
                self.str_obj_branch_list.pop(i)
                self.obj_navi_map.obj_node_data_branch_list.pop(i)

    def _process_branch_connections(self):
        """Process connections between branch structures"""
        connect_list, connect_branch_branch_index_ls = self._find_branch_connections()
        str_obj_connect_branch_list = self._create_branch_connections(connect_branch_branch_index_ls)
        self._update_branch_connections(str_obj_connect_branch_list, connect_list, connect_branch_branch_index_ls)

    def _find_branch_connections(self) -> List:
        """Find connections between branch structures"""
        connect_branch_branch_index_ls = []
        connect_list = []
        for i, list_i in enumerate(self.obj_navi_map.obj_node_data_branch_list):
            for k, list_k in enumerate(self.obj_navi_map.obj_node_data_branch_list):
                for l in range(2):
                    if [list_i.obj_link_data_list[l].line[0],
                        list_i.obj_link_data_list[l].line[1],
                    ] == [
                        list_k.obj_link_data_list[2].line[0],
                        list_k.obj_link_data_list[2].line[1],
                    ] and [
                        list_i.obj_link_data_list[l].line[-2],
                        list_i.obj_link_data_list[l].line[-1],
                    ] == [
                        list_k.obj_link_data_list[2].line[-2],
                        list_k.obj_link_data_list[2].line[-1],
                    ]:
                        connect_list += [[list_i,list_k]]
                        connect_branch_branch_index_ls += [[i, k, l]]
                        # print("connect_branch_branch_index_ls = ",i,k,l)

                    elif list_i.obj_link_data_list[l].linkno == list_k.obj_link_data_list[2].linkno and list_i.meshcode == list_k.meshcode:
                        # print("branch - branch (linkno)", i, k, l)
                        connect_list += [[list_i,list_k]]
                        connect_branch_branch_index_ls += [[i, k, l]]

        self._connect_branch_branch_index_ls = connect_branch_branch_index_ls

        return connect_list, connect_branch_branch_index_ls

    def _create_branch_connections(self, connect_branch_branch_index_ls: List) -> List:
        """Create new branch structures for connected branches"""
        str_obj_connect_branch_list = []
        print("If there is a connection, the branches will be merged.")

        for _ in range(len(connect_branch_branch_index_ls)):
            str_obj_connect_branch_list.append(BranchStructure())

        return str_obj_connect_branch_list

    def _update_branch_connections(self, str_obj_connect_branch_list: List, connect_list: List, connect_branch_branch_index_ls: List):
        """Update branch structures with connection information"""
        for i in tqdm(range(len(str_obj_connect_branch_list))):
            self._process_single_branch_connection(str_obj_connect_branch_list[i], connect_list[i], connect_branch_branch_index_ls[i])

    def _process_single_branch_connection(self, connect_branch: BranchStructure, connect_list: List, connect_branch_branch_index_ls: List):
        """Process a single branch connection"""
        i, k, l = connect_branch_branch_index_ls
        connect_branch.make_df_polyline_combine(self.str_obj_branch_list[i], self.str_obj_branch_list[k], l)

        self._update_branch_lane_info(connect_branch, connect_list, connect_branch_branch_index_ls)

    def _update_branch_lane_info(self, connect_branch: BranchStructure, connect_list: List, connect_branch_branch_index_ls: List):
        """Update lane information for connected branches"""
        i, k, l = connect_branch_branch_index_ls
        if l == 0:
            self._update_branch_lane_info_case_0(connect_branch, connect_list, connect_branch_branch_index_ls)
        else:
            self._update_branch_lane_info_case_1(connect_branch, connect_list, connect_branch_branch_index_ls)

    def _update_branch_lane_info_case_0(self, connect_branch: BranchStructure, connect_list: List, connect_branch_branch_index_ls: List):
        """Update lane information for case 0 of branch connection"""
        for j in range(len(self.obj_navi_map.obj_node_data_branch_list)):
            if self.obj_navi_map.obj_node_data_branch_list[j].nodeno == connect_list[0].nodeno:
                self.str_obj_branch_list[j].df_polyline = connect_branch.df_polyline_2[0]
                self.str_obj_branch_list[connect_branch_branch_index_ls[0]].df_lane_info.at[
                    self.str_obj_branch_list[connect_branch_branch_index_ls[0]].df_lane_info[self.str_obj_branch_list[connect_branch_branch_index_ls[0]].df_lane_info["road_id"] == 3].index[0],
                    "road_successor_id",
                ] = (
                    "1" + str(connect_branch_branch_index_ls[1]) + "2"
                )

            elif self.obj_navi_map.obj_node_data_branch_list[j].nodeno == connect_list[1].nodeno:
                self.str_obj_branch_list[j].df_polyline = connect_branch.df_polyline_2[1]
                self.str_obj_branch_list[connect_branch_branch_index_ls[1]].df_lane_info.at[
                    self.str_obj_branch_list[connect_branch_branch_index_ls[1]].df_lane_info[self.str_obj_branch_list[connect_branch_branch_index_ls[1]].df_lane_info["road_id"] == 2].index[0],
                    "road_predecessor_id",
                ] = (
                    "1" + str(connect_branch_branch_index_ls[0]) + "3"
                )

    def _update_branch_lane_info_case_1(self, connect_branch: BranchStructure, connect_list: List, connect_branch_branch_index_ls: List):
        """Update lane information for case 1 of branch connection"""
        for j in range(len(self.obj_navi_map.obj_node_data_branch_list)):
            if self.obj_navi_map.obj_node_data_branch_list[j].nodeno == connect_list[0].nodeno:
                self.str_obj_branch_list[j].df_polyline = connect_branch.df_polyline_2[0]
                self.str_obj_branch_list[connect_branch_branch_index_ls[0]].df_lane_info.at[
                    self.str_obj_branch_list[connect_branch_branch_index_ls[0]].df_lane_info[self.str_obj_branch_list[connect_branch_branch_index_ls[0]].df_lane_info["road_id"] == 3].index[0],
                    "road_successor_id",
                ] = (
                    "1" + str(connect_branch_branch_index_ls[1]) + "2"
                )
            elif self.obj_navi_map.obj_node_data_branch_list[j].nodeno == connect_list[1].nodeno:
                self.str_obj_branch_list[j].df_polyline = connect_branch.df_polyline_2[1]
                self.str_obj_branch_list[connect_branch_branch_index_ls[1]].df_lane_info.at[
                    self.str_obj_branch_list[connect_branch_branch_index_ls[1]].df_lane_info[self.str_obj_branch_list[connect_branch_branch_index_ls[1]].df_lane_info["road_id"] == 2].index[0],
                    "road_predecessor_id",
                ] = (
                    "1" + str(connect_branch_branch_index_ls[0]) + "0"
                )

    def _process_merge_structures(self):
        """Initialize and process merge structures"""
        # Initialize merge structures
        for i in range(len(self.obj_navi_map.obj_node_data_merge_list)):
            self.str_obj_merge_list.append(MergeStructure())

        print("Generate the road structure for the merge.")
        # Create merge structure for each element
        for i in tqdm(range(len(self.str_obj_merge_list))):
            self.str_obj_merge_list[i].make_merge_structure(self.obj_navi_map.obj_node_data_merge_list[i])

        self._remove_error_merges()

    def _remove_error_merges(self):
        """Remove merge structures with errors"""
        for i in range(len(self.str_obj_merge_list) - 1, -1, -1):
            if self.str_obj_merge_list[i].error_is != "None":
                meshcode = self.obj_navi_map.obj_node_data_merge_list[i].meshcode
                nodeno = self.obj_navi_map.obj_node_data_merge_list[i].nodeno
                print(f"{nodeno} in {meshcode} has error: {self.str_obj_merge_list[i].error_is}")
                self.str_obj_merge_list.pop(i)
                self.obj_navi_map.obj_node_data_merge_list.pop(i)

    def _process_merge_connections(self):
        """Process connections between merge structures"""
        connect_list, connect_merge_merge_index_ls = self._find_merge_connections()
        str_obj_connect_merge_list = self._create_merge_connections(connect_merge_merge_index_ls)
        self._update_merge_connections(str_obj_connect_merge_list, connect_list, connect_merge_merge_index_ls)

    def _find_merge_connections(self) -> List:
        """Find connections between merge structures"""
        connect_merge_merge_index_ls = []
        connect_list = []
        for k, list_k in enumerate(self.obj_navi_map.obj_node_data_merge_list):
            for i, list_i in enumerate(self.obj_navi_map.obj_node_data_merge_list):
                for l in range(2):
                    if [
                        list_i.obj_link_data_list[l].line[0],
                        list_i.obj_link_data_list[l].line[1],
                    ] == [
                        list_k.obj_link_data_list[2].line[0],
                        list_k.obj_link_data_list[2].line[1],
                    ] and [
                        list_i.obj_link_data_list[l].line[-2],
                        list_i.obj_link_data_list[l].line[-1],
                    ] == [
                        list_k.obj_link_data_list[2].line[-2],
                        list_k.obj_link_data_list[2].line[-1],
                    ]:
                        connect_list += [[list_k,list_i]]
                        connect_merge_merge_index_ls += [[k, i, l]]
                        # print("connect_merge_merge_index_ls = ",k,i,l)

                    # elif list_i.obj_link_data_list[l].linkno == list_k.obj_link_data_list[2].linkno and list_i.meshcode == list_k.meshcode:
                    elif [
                        list_i.obj_link_data_list[l].line[0],
                        list_i.obj_link_data_list[l].line[1],
                    ] == [
                        list_k.obj_link_data_list[2].line[-2],
                        list_k.obj_link_data_list[2].line[-1],
                    ]:
                        # print("merge - merge (linkno)", k,i,l)
                        connect_list += [[list_k,list_i]]
                        connect_merge_merge_index_ls += [[k, i, l]]

        self._connect_merge_merge_index_ls = connect_merge_merge_index_ls

        return connect_list, connect_merge_merge_index_ls

    def _create_merge_connections(self, connect_merge_merge_index_ls: List) -> List:
        """Create new merge structures for connected merges"""
        str_obj_connect_merge_list = []
        print("If there is a connection, the merges will be merged.")

        for _ in range(len(connect_merge_merge_index_ls)):
            str_obj_connect_merge_list.append(MergeStructure())

        return str_obj_connect_merge_list

    def _update_merge_connections(self, str_obj_connect_merge_list: List, connect_list: List, connect_merge_merge_index_ls: List):
        """Update merge structures with connection information"""
        for i in tqdm(range(len(str_obj_connect_merge_list))):
            self._process_single_merge_connection(str_obj_connect_merge_list[i], connect_list[i], connect_merge_merge_index_ls[i])

    def _process_single_merge_connection(self, connect_merge: MergeStructure, connect_list: List, connect_merge_merge_index_ls: List):
        """Process a single merge connection"""
        k, i, l = connect_merge_merge_index_ls
        connect_merge.make_df_polyline_combine(self.str_obj_merge_list[k], self.str_obj_merge_list[i], l)

        self._update_merge_lane_info(connect_merge, connect_list, connect_merge_merge_index_ls)

    def _update_merge_lane_info(self, connect_merge: MergeStructure, connect_list: List, connect_merge_merge_index_ls: List):
        """Update lane information for connected merges"""
        k, i, l = connect_merge_merge_index_ls
        if l == 0:
            self._update_merge_lane_info_case_0(connect_merge, connect_list, connect_merge_merge_index_ls)
        else:
            self._update_merge_lane_info_case_1(connect_merge, connect_list, connect_merge_merge_index_ls)

    def _update_merge_lane_info_case_0(self, connect_merge: MergeStructure, connect_list: List, connect_merge_merge_index_ls: List):
        """Update lane information for case 0 of merge connection"""
        k, i, l = connect_merge_merge_index_ls
        for j in range(len(self.obj_navi_map.obj_node_data_merge_list)):
            if self.obj_navi_map.obj_node_data_merge_list[j].nodeno == connect_list[0].nodeno:
                self.str_obj_merge_list[j].df_polyline = connect_merge.df_polyline_2[0]
                self.str_obj_merge_list[k].df_lane_info.at[
                    self.str_obj_merge_list[k].df_lane_info[self.str_obj_merge_list[k].df_lane_info["road_id"] == 2].index[0],
                    "road_successor_id",
                ] = (
                    "2" + str(i) + "3"
                )

            elif self.obj_navi_map.obj_node_data_merge_list[j].nodeno == connect_list[1].nodeno:
                self.str_obj_merge_list[j].df_polyline = connect_merge.df_polyline_2[1]
                self.str_obj_merge_list[i].df_lane_info.at[
                    self.str_obj_merge_list[i].df_lane_info[self.str_obj_merge_list[i].df_lane_info["road_id"] == 3].index[0],
                    "road_predecessor_id",
                ] = (
                    "2" + str(k) + "2"
                )

    def _update_merge_lane_info_case_1(self, connect_merge: MergeStructure, connect_list: List, connect_merge_merge_index_ls: List):
        """Update lane information for case 1 of merge connection"""
        k, i, l = connect_merge_merge_index_ls
        for j in range(len(self.obj_navi_map.obj_node_data_merge_list)):
            if self.obj_navi_map.obj_node_data_merge_list[j].nodeno == connect_list[0].nodeno:
                self.str_obj_merge_list[j].df_polyline = connect_merge.df_polyline_2[0]
                self.str_obj_merge_list[k].df_lane_info.at[
                    self.str_obj_merge_list[k].df_lane_info[self.str_obj_merge_list[k].df_lane_info["road_id"] == 2].index[0],
                    "road_successor_id",
                ] = (
                    "2" + str(i) + "0"
                )

            elif self.obj_navi_map.obj_node_data_merge_list[j].nodeno == connect_list[1].nodeno:
                self.str_obj_merge_list[j].df_polyline = connect_merge.df_polyline_2[1]
                self.str_obj_merge_list[i].df_lane_info.at[
                    self.str_obj_merge_list[i].df_lane_info[self.str_obj_merge_list[i].df_lane_info["road_id"] == 0].index[0],
                    "road_predecessor_id",
                ] = (
                    "2" + str(k) + "2"
                )

    def _process_branch_merge_connections(self):
        """Process connections between branch and merge structures"""
        index = self._find_branch_merge_connections()
        self._index = index
        str_obj_connect_merge_branch_list = self._create_branch_merge_connections(index)
        self._update_branch_merge_connections(str_obj_connect_merge_branch_list, index)

    def _find_branch_merge_connections(self) -> List:
        """Find connections between branch and merge structures"""
        connect_merge_merge_index_ls = self._connect_merge_merge_index_ls
        connect_branch_branch_index_ls = self._connect_branch_branch_index_ls

        index = []
        for i in range(len(self.obj_navi_map.obj_node_data_merge_list)):
            flag = True
            for j in range(len(self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list)):
                index_ = []
                for k in range(len(self.obj_navi_map.obj_node_data_branch_list)):
                    for l in range(len(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list)):
                        # flag = True
                        if (round(self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[j].line[0],6) == round(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[0],6)
                            and round(self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[j].line[1],6) == round(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[1],6)
                            and round(self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[j].line[-2],6) == round(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[-2],6)
                            and round(self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[j].line[-1],6) == round(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[-1],6)
                        ):
                            flag = False
                            # print("merge - branch", i, j, k, l)
                            index_ += [i, j, k, l]
                            index += [index_]

                        elif self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[j].linkno == self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].linkno and self.obj_navi_map.obj_node_data_merge_list[i].meshcode == self.obj_navi_map.obj_node_data_branch_list[k].meshcode:
                            flag = False
                            # print("merge - branch (linkno)", i, j, k, l)
                            index_ += [i, j, k, l]
                            index += [index_]
                        elif flag:
                            if (self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[j].line[0] == self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[-2]
                                and self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[j].line[1] == self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[-1]
                                and j!=2 and l!=2
                            ):
                                for s in range(len(connect_merge_merge_index_ls)):
                                    if i==connect_merge_merge_index_ls[s][1]:
                                        flag = False
                                        break

                                for x in range(len(connect_branch_branch_index_ls)):
                                    if k==connect_branch_branch_index_ls[x][0]:
                                        flag = False
                                        break

                                if flag:
                                    # print("merge - branch (linkno1)", i, j, k, l)
                                    index_ += [i, j, k, l]
                                    index += [index_]
                            elif (self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[j].line[-2] == self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[0]
                                and self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[j].line[-1] == self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[1]
                                and j==2 and l==2
                            ):
                                for s in range(len(connect_merge_merge_index_ls)):
                                    if i==connect_merge_merge_index_ls[s][0]:
                                        flag = False
                                        break

                                for x in range(len(connect_branch_branch_index_ls)):
                                    if k==connect_branch_branch_index_ls[x][1]:
                                        flag = False
                                        break

                                if flag:
                                    # print("merge - branch (linkno2)", i, j, k, l)
                                    index_ += [i, j, k, l]
                                    index += [index_]


        return index

    def _create_branch_merge_connections(self, index: List) -> List:
        """Create new structures for connected branch and merge"""
        str_obj_connect_merge_branch_list = []
        print("If there is a connection, the merge and branch will be merged.")

        for _ in range(len(index)):
            str_obj_connect_merge_branch_list.append(MergeBranchStructure())

        return str_obj_connect_merge_branch_list

    def _update_branch_merge_connections(self, str_obj_connect_merge_branch_list: List, index: List):
        """Update branch and merge structures with connection information"""
        for i in tqdm(range(len(str_obj_connect_merge_branch_list))):
            if self.str_obj_merge_list[index[i][0]].error_is == "None" and self.str_obj_branch_list[index[i][2]].error_is == "None":
                str_obj_connect_merge_branch_list[i].make_df_polyline_combine(
                    self.str_obj_merge_list[index[i][0]],
                    self.str_obj_branch_list[index[i][2]],
                    index[i][1],
                    index[i][3],
                )

                self.str_obj_merge_list[index[i][0]].df_polyline = str_obj_connect_merge_branch_list[i].df_polyline_2[0]

                self.str_obj_branch_list[index[i][2]].df_polyline = str_obj_connect_merge_branch_list[i].df_polyline_2[1]

                if index[i][1] == 0 and index[i][3] == 1:
                    self.str_obj_merge_list[index[i][0]].df_lane_info.at[
                        self.str_obj_merge_list[index[i][0]].df_lane_info[self.str_obj_merge_list[index[i][0]].df_lane_info["road_id"] == 3].index[0],
                        "road_predecessor_id",
                    ] = (
                        "1" + str(index[i][2]) + "0"
                    )
                    self.str_obj_branch_list[index[i][2]].df_lane_info.at[
                        self.str_obj_branch_list[index[i][2]].df_lane_info[self.str_obj_branch_list[index[i][2]].df_lane_info["road_id"] == 0].index[0],
                        "road_successor_id",
                    ] = (
                        "2" + str(index[i][0]) + "3"
                    )

                elif index[i][1] == 1 and index[i][3] == 0:
                    self.str_obj_merge_list[index[i][0]].df_lane_info.at[
                        self.str_obj_merge_list[index[i][0]].df_lane_info[self.str_obj_merge_list[index[i][0]].df_lane_info["road_id"] == 0].index[0],
                        "road_predecessor_id",
                    ] = (
                        "1" + str(index[i][2]) + "3"
                    )
                    self.str_obj_branch_list[index[i][2]].df_lane_info.at[
                        self.str_obj_branch_list[index[i][2]].df_lane_info[self.str_obj_branch_list[index[i][2]].df_lane_info["road_id"] == 3].index[0],
                        "road_successor_id",
                    ] = (
                        "2" + str(index[i][0]) + "0"
                    )

                elif index[i][1] == 0 and index[i][3] == 0:
                    self.str_obj_merge_list[index[i][0]].df_lane_info.at[
                        self.str_obj_merge_list[index[i][0]].df_lane_info[self.str_obj_merge_list[index[i][0]].df_lane_info["road_id"] == 3].index[0],
                        "road_predecessor_id",
                    ] = (
                        "1" + str(index[i][2]) + "3"
                    )
                    self.str_obj_branch_list[index[i][2]].df_lane_info.at[
                        self.str_obj_branch_list[index[i][2]].df_lane_info[self.str_obj_branch_list[index[i][2]].df_lane_info["road_id"] == 3].index[0],
                        "road_successor_id",
                    ] = (
                        "2" + str(index[i][0]) + "3"
                    )

                elif index[i][1] == 1 and index[i][3] == 1:
                    self.str_obj_merge_list[index[i][0]].df_lane_info.at[
                        self.str_obj_merge_list[index[i][0]].df_lane_info[self.str_obj_merge_list[index[i][0]].df_lane_info["road_id"] == 0].index[0],
                        "road_predecessor_id",
                    ] = (
                        "1" + str(index[i][2]) + "0"
                    )
                    self.str_obj_branch_list[index[i][2]].df_lane_info.at[
                        self.str_obj_branch_list[index[i][2]].df_lane_info[self.str_obj_branch_list[index[i][2]].df_lane_info["road_id"] == 0].index[0],
                        "road_successor_id",
                    ] = (
                        "2" + str(index[i][0]) + "0"
                    )

                elif index[i][1] == 2 and index[i][3] == 2:
                    self.str_obj_merge_list[index[i][0]].df_lane_info.at[
                        self.str_obj_merge_list[index[i][0]].df_lane_info[self.str_obj_merge_list[index[i][0]].df_lane_info["road_id"] == 2].index[0],
                        "road_successor_id",
                    ] = (
                        "1" + str(index[i][2]) + "2"
                    )
                    self.str_obj_branch_list[index[i][2]].df_lane_info.at[
                        self.str_obj_branch_list[index[i][2]].df_lane_info[self.str_obj_branch_list[index[i][2]].df_lane_info["road_id"] == 2].index[0],
                        "road_predecessor_id",
                    ] = (
                        "2" + str(index[i][0]) + "2"
                    )

    def _search_merge_and_branch_lists(self):
        """Search for merge and branch lists that join together without overlapping."""
        index = self._index

        branchID2_list = self._get_branchID2_list(index)
        branchID2_index_ls = self._get_branchID2_index_ls(branchID2_list)
        self.connect_merge_branch_list.append(branchID2_index_ls)

        mergeID2_list = self._get_mergeID2_list(index)
        mergeID2_index_ls = self._get_mergeID2_index_ls(mergeID2_list)
        self.connect_merge_branch_list.append(mergeID2_index_ls)

        branchID0_list = self._get_branchID0_list(index)
        branchID0_index_ls = self._get_branchID0_index_ls(branchID0_list)
        self.connect_merge_branch_list.append(branchID0_index_ls)

        mergeID0_list = self._get_mergeID0_list(index)
        mergeID0_index_ls = self._get_mergeID0_index_ls(mergeID0_list)
        self.connect_merge_branch_list.append(mergeID0_index_ls)

    def _get_branchID2_list(self, index):
        branchID2_list = [self._connect_branch_branch_index_ls[i][1] for i in range(len(self._connect_branch_branch_index_ls))]
        branchID2_list += [index[i][2] for i in range(len(index)) if index[i][3] == 2]
        return branchID2_list

    def _get_branchID2_index_ls(self, branchID2_list):
        branchID2_index_ls = []
        for i in range(len(self.obj_navi_map.obj_node_data_branch_list)):
            for k in range(len(self.obj_navi_map.obj_node_data_branch_list)):
                if k not in branchID2_list:
                    if self._lines_match(self.obj_navi_map.obj_node_data_branch_list[i].obj_link_data_list[0].line[-2:], self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[2].line[:2]):
                        branchID2_index_ls.append(k)
        return branchID2_index_ls

    def _get_mergeID2_list(self, index):
        mergeID2_list = [self._connect_merge_merge_index_ls[i][0] for i in range(len(self._connect_merge_merge_index_ls))]
        mergeID2_list += [index[i][0] for i in range(len(index)) if index[i][1] == 2]
        return mergeID2_list

    def _get_mergeID2_index_ls(self, mergeID2_list):
        mergeID2_index_ls = []
        for k in range(len(self.obj_navi_map.obj_node_data_merge_list)):
            for i in range(len(self.obj_navi_map.obj_node_data_merge_list)):
                if k not in mergeID2_list:
                    if self._lines_match(self.obj_navi_map.obj_node_data_merge_list[i].obj_link_data_list[0].line[:2], self.obj_navi_map.obj_node_data_merge_list[k].obj_link_data_list[2].line[-2:]):
                        mergeID2_index_ls.append(k)
        return mergeID2_index_ls

    def _get_branchID0_list(self, index):
        branchID0_list = [self._connect_branch_branch_index_ls[i][0] for i in range(len(self._connect_branch_branch_index_ls)) if self._connect_branch_branch_index_ls[i][2] == 1]
        branchID0_list += [index[i][2] for i in range(len(index)) if index[i][3] == 1]
        return branchID0_list

    def _get_branchID0_index_ls(self, branchID0_list):
        branchID0_index_ls = []
        for i in range(len(self.obj_navi_map.obj_node_data_branch_list)):
            for k in range(len(self.obj_navi_map.obj_node_data_merge_list)):
                if i not in branchID0_list:
                    if self._lines_match(self.obj_navi_map.obj_node_data_branch_list[i].obj_link_data_list[1].line[-2:], self.obj_navi_map.obj_node_data_merge_list[k].obj_link_data_list[0].line[:2]):
                        branchID0_index_ls.append(i)
        return branchID0_index_ls

    def _get_mergeID0_list(self, index):
        mergeID0_list = [self._connect_merge_merge_index_ls[i][1] for i in range(len(self._connect_merge_merge_index_ls)) if self._connect_merge_merge_index_ls[i][2] == 1]
        mergeID0_list += [index[i][0] for i in range(len(index)) if index[i][1] == 1]
        return mergeID0_list

    def _get_mergeID0_index_ls(self, mergeID0_list):
        mergeID0_index_ls = []
        for i in range(len(self.obj_navi_map.obj_node_data_branch_list)):
            for k in range(len(self.obj_navi_map.obj_node_data_merge_list)):
                if k not in mergeID0_list:
                    if self._lines_match(self.obj_navi_map.obj_node_data_branch_list[i].obj_link_data_list[0].line[-2:], self.obj_navi_map.obj_node_data_merge_list[k].obj_link_data_list[1].line[:2]):
                        mergeID0_index_ls.append(k)
        return mergeID0_index_ls

    def _lines_match(self, line1, line2):
        return round(line1[0], 6) == round(line2[0], 6) and round(line1[1], 6) == round(line2[1], 6)

    def _remove_coinciding_main_lines(self):
        """Remove the main line that coincides with the Branch or Merge that exists on the route."""
        self._remove_coinciding_lines(self.obj_navi_map.obj_node_data_branch_list)
        self._remove_coinciding_lines(self.obj_navi_map.obj_node_data_merge_list)
        self._group_consecutive_main_lines()

    def _remove_coinciding_lines(self, data_list):
        """Remove lines in obj_node_combine_data_list that coincide with lines in the given data_list."""
        for i in range(len(self.obj_navi_map.obj_node_combine_data_list) - 1, -1, -1):
            for j in range(len(self.obj_navi_map.obj_node_combine_data_list[i]) - 1, -1, -1):
                if self._line_coincides(self.obj_navi_map.obj_node_combine_data_list[i][j], data_list):
                    self.obj_navi_map.obj_node_combine_data_list[i].pop(j)

    def _line_coincides(self, combine_line, data_list):
        """Check if a line in obj_node_combine_data_list coincides with any line in the given data_list."""
        for data in data_list:
            for link in data.obj_link_data_list:
                if round(combine_line.line[0], 6) == round(link.line[0], 6) and round(combine_line.line[1], 6) == round(link.line[1], 6):
                    return True
        return False

    def _group_consecutive_main_lines(self):
        """Group main lines that follow each other together."""
        combine_data_list = self.obj_navi_map.obj_node_combine_data_list
        self.obj_navi_map.obj_node_combine_data_list = []

        for segment in combine_data_list:
            inx = 0
            for i in range(len(segment)):
                if i == (len(segment) - 1):
                    self.obj_navi_map.obj_node_combine_data_list.append(segment[inx:])
                elif segment[i].line[-2] != segment[i + 1].line[0] or segment[i].line[-1] != segment[i + 1].line[1]:
                    self.obj_navi_map.obj_node_combine_data_list.append(segment[inx : i + 1])
                    inx = i + 1

    def _process_mainlane_connections(self):
        """
        Process connections between mainlane and branch/merge structures.
        If there is a connection, the mainlane and the branch (or merge) will be merged.
        """
        index_connect_start = []
        index_connect_end = []
        print("If there is a connection, the mainlane and the branch (or merge) will be merged.")

        # Find connections at the start of mainlane
        for i in range(len(self.obj_navi_map.obj_node_combine_data_list)):
            for k in range(len(self.obj_navi_map.obj_node_data_branch_list)):
                if len(index_connect_start) == (i + 1):
                    break
                for l in range(len(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list)):
                    if round(self.obj_navi_map.obj_node_combine_data_list[i][0].line[0], 6) == round(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[-2], 6) and round(
                        self.obj_navi_map.obj_node_combine_data_list[i][0].line[1], 6
                    ) == round(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[-1], 6):
                        index_connect_start.append([i, 1, k, l])
                        break

            for k in range(len(self.obj_navi_map.obj_node_data_merge_list)):
                if len(index_connect_start) == (i + 1):
                    break
                for l in range(len(self.obj_navi_map.obj_node_data_merge_list[k].obj_link_data_list)):
                    if round(self.obj_navi_map.obj_node_combine_data_list[i][0].line[0], 6) == round(self.obj_navi_map.obj_node_data_merge_list[k].obj_link_data_list[l].line[-2], 6) and round(
                        self.obj_navi_map.obj_node_combine_data_list[i][0].line[1], 6
                    ) == round(self.obj_navi_map.obj_node_data_merge_list[k].obj_link_data_list[l].line[-1], 6):
                        index_connect_start.append([i, 2, k, l])
                        break

            if len(index_connect_start) != (i + 1):
                index_connect_start.append([i, 0])

        # Find connections at the end of mainlane
        for i in range(len(self.obj_navi_map.obj_node_combine_data_list)):
            for k in range(len(self.obj_navi_map.obj_node_data_branch_list)):
                if len(index_connect_end) == (i + 1):
                    break
                for l in range(len(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list)):
                    if round(self.obj_navi_map.obj_node_combine_data_list[i][-1].line[-2], 6) == round(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[0], 6) and round(
                        self.obj_navi_map.obj_node_combine_data_list[i][-1].line[-1], 6
                    ) == round(self.obj_navi_map.obj_node_data_branch_list[k].obj_link_data_list[l].line[1], 6):
                        index_connect_end.append([i, 1, k, l])
                        break

            for k in range(len(self.obj_navi_map.obj_node_data_merge_list)):
                if len(index_connect_end) == (i + 1):
                    break
                for l in range(len(self.obj_navi_map.obj_node_data_merge_list[k].obj_link_data_list)):
                    if round(self.obj_navi_map.obj_node_combine_data_list[i][-1].line[-2], 6) == round(self.obj_navi_map.obj_node_data_merge_list[k].obj_link_data_list[l].line[0], 6) and round(
                        self.obj_navi_map.obj_node_combine_data_list[i][-1].line[-1], 6
                    ) == round(self.obj_navi_map.obj_node_data_merge_list[k].obj_link_data_list[l].line[1], 6):
                        index_connect_end.append([i, 2, k, l])
                        break

            if len(index_connect_end) != (i + 1):
                index_connect_end.append([i, 0])

        # Initialize mainlane structures
        for i in range(len(self.obj_navi_map.obj_node_combine_data_list)):
            self.str_obj_mainlane_list.append(MainLaneStructure())

        print("Generate the road structure for the mainlane.")
        for i in tqdm(range(len(self.str_obj_mainlane_list))):
            lane_count_start = 0
            lane_offset_start = 0
            lane_count_end = 0
            lane_offset_end = 0

            # Process connections at the start of mainlane
            if index_connect_start[i][1] == 1:
                branch = self.str_obj_branch_list[index_connect_start[i][2]]
                if branch.error_is == "None":
                    offset_list_start = branch.df_lane_info["offset"].tolist()
                    road_id_list_start = branch.df_lane_info["road_id"].tolist()
                    road_id_start = [3, 0, 2][index_connect_start[i][3]]
                    lane_count_start = road_id_list_start.count(road_id_start)
                    lane_offset_start = offset_list_start[road_id_list_start.index(road_id_start)]
                    branch.df_lane_info.at[
                        branch.df_lane_info[branch.df_lane_info["road_id"] == road_id_start].index[0],
                        "road_successor_id",
                    ] = f"3{i}0"

            elif index_connect_start[i][1] == 2:
                merge = self.str_obj_merge_list[index_connect_start[i][2]]
                if merge.error_is == "None":
                    offset_list_start = merge.df_lane_info["offset"].tolist()
                    road_id_list_start = merge.df_lane_info["road_id"].tolist()
                    road_id_start = [3, 0, 2][index_connect_start[i][3]]
                    lane_count_start = road_id_list_start.count(road_id_start)
                    lane_offset_start = offset_list_start[road_id_list_start.index(road_id_start)]
                    merge.df_lane_info.at[
                        merge.df_lane_info[merge.df_lane_info["road_id"] == road_id_start].index[0],
                        "road_successor_id",
                    ] = f"3{i}0"

            # Process connections at the end of mainlane
            if index_connect_end[i][1] == 1:
                branch = self.str_obj_branch_list[index_connect_end[i][2]]
                if branch.error_is == "None":
                    offset_list_end = branch.df_lane_info["offset"].tolist()
                    road_id_list_end = branch.df_lane_info["road_id"].tolist()
                    road_id_end = [3, 0, 2][index_connect_end[i][3]]
                    lane_count_end = road_id_list_end.count(road_id_end)
                    lane_offset_end = offset_list_end[road_id_list_end.index(road_id_end)]
                    branch.df_lane_info.at[
                        branch.df_lane_info[branch.df_lane_info["road_id"] == road_id_end].index[0],
                        "road_predecessor_id",
                    ] = f"3{i}{len(self.obj_navi_map.obj_node_combine_data_list[i]) - 1}"

            elif index_connect_end[i][1] == 2:
                merge = self.str_obj_merge_list[index_connect_end[i][2]]
                if merge.error_is == "None":
                    offset_list_end = merge.df_lane_info["offset"].tolist()
                    road_id_list_end = merge.df_lane_info["road_id"].tolist()
                    road_id_end = [3, 0, 2][index_connect_end[i][3]]
                    lane_count_end = road_id_list_end.count(road_id_end)
                    lane_offset_end = offset_list_end[road_id_list_end.index(road_id_end)]
                    merge.df_lane_info.at[
                        merge.df_lane_info[merge.df_lane_info["road_id"] == road_id_end].index[0],
                        "road_predecessor_id",
                    ] = f"3{i}{len(self.obj_navi_map.obj_node_combine_data_list[i]) - 1}"

            # Create route structure for mainlane
            self.str_obj_mainlane_list[i].make_route_structure(
                self.obj_navi_map.obj_node_combine_data_list[i],
                lane_offset_start,
                lane_offset_end,
                lane_count_start,
                lane_count_end,
            )

            # Update lane information for mainlane
            if lane_count_start != 0 and self.str_obj_mainlane_list[i].error_is == "None":
                self.str_obj_mainlane_list[i].df_lane_info.at[
                    self.str_obj_mainlane_list[i].df_lane_info[self.str_obj_mainlane_list[i].df_lane_info["road_id"] == 0].index[0],
                    "road_predecessor_id",
                ] = f"{index_connect_start[i][1]}{index_connect_start[i][2]}{road_id_start}"
            if lane_count_end != 0 and self.str_obj_mainlane_list[i].error_is == "None":
                self.str_obj_mainlane_list[i].df_lane_info.at[
                    self.str_obj_mainlane_list[i].df_lane_info[self.str_obj_mainlane_list[i].df_lane_info["road_id"] == (len(self.obj_navi_map.obj_node_combine_data_list[i]) - 1)].index[0],
                    "road_successor_id",
                ] = f"{index_connect_end[i][1]}{index_connect_end[i][2]}{road_id_end}"

        # Remove mainlane structures with errors
        for i in range(len(self.str_obj_mainlane_list) - 1, -1, -1):
            if self.str_obj_mainlane_list[i].error_is != "None":
                print(self.str_obj_mainlane_list[i].error_is)
                self.str_obj_mainlane_list.pop(i)
                self.obj_navi_map.obj_node_combine_data_list.pop(i)
