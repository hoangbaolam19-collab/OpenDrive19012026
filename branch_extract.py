import math
import copy

import numpy as np
from tqdm import tqdm

from common_extract import CommonExtract
from route_extract import RouteExtract
from route_data import LinkData, BranchData
from itsumo_navi import ItsumoNaviData
from detail_navi import DetailNaviData
from submodule import vincenty_method as vm
from submodule import ajust


class BranchExtract:
    """
    A class to extract and process branch/merge sections from road network data.

    This class handles the extraction and processing of branch/merge sections from detailed
    navigation map data, including coordinate conversions, link classifications, and
    geometric calculations.

    Attributes:
        node_ls (list): List of NodeData objects containing branch center node information
        meshcode (str): Secondary mesh code for the target area
        junction_flag (int): Flag to select between merge (0) or branch (1) section
        path (str): Relative path to folder for saving data
        error_log (list): List of error messages during processing
    """

    def __init__(self, meshcode, junction_flag, path):
        """
        Initialize BranchExtract with mesh code, junction type and data path.

        Args:
            meshcode (str): Secondary mesh code for the target area
            junction_flag (int): Flag to select between merge (0) or branch (1) section
            path (str): Relative path to folder for saving data
        """
        self.node_ls = []  # List of NodeData (branch center node information)
        self.meshcode = meshcode  # Secondary mesh code
        self.junction_flag = junction_flag  # Flag to select between merge or branch section
        self.path = path  # Relative path to folder for saving data
        self.error_log = []

    def road_shp(self):
        """
        Convert DetailNaviData dbf files to csv format and process coordinate data.

        Converts database files to CSV format and transforms coordinate units from
        seconds to degrees/minutes/seconds for files containing latitude/longitude information.
        """
        # Convert DetailNaviData dbf files to csv. Only needs to be run once if already converted
        detail_df = DetailNaviData(self.meshcode, self.path)
        detail_df.dbf_to_csv()  # Convert dbf files to csv
        detail_df.data_forming()  # Convert units (seconds -> degrees/minutes/seconds) for files with latitude/longitude info

    def make_branch_extract(self, operating_time, latlon):
        """
        Extract and process branch section data from the road network.

        Args:
            operating_time (str): Time of data extraction
            latlon (tuple): Reference latitude and longitude coordinates (lat, lon)

        This method performs the following operations:
        1. Loads and processes detailed map data
        2. Identifies branch/merge nodes
        3. Creates LinkData objects for connected links
        4. Classifies links into acceleration lanes and mainlines
        5. Calculates geometric properties (elevation, gradient, curvature)
        """
        # Initialize and load data
        detail_df = DetailNaviData(self.meshcode, self.path)
        junc = CommonExtract(self.meshcode, self.path, self.junction_flag)

        # Load required data files
        if not self._load_map_data(detail_df):
            return

        # Get node numbers for branch/merge sections
        df_junc_node = junc.judge_junction(detail_df.df_all["oneway"], detail_df.df_all["turnoff"])

        # Process each node
        for i in tqdm(range(len(df_junc_node))):
            node_data = self._process_node(df_junc_node["nodeno"][i], detail_df, latlon, operating_time)
            if node_data:
                self.node_ls.append(node_data)

    def _load_map_data(self, detail_df):
        """Load all required map data files"""
        branch_exist = detail_df.load_turnoff()
        if branch_exist == "NotFound":
            self.error_log.append(f"{self.meshcode} : There is no branch")
            return False
        
        detail_df.load_node()
        detail_df.load_oneway()
        detail_df.load_enterexit()
        detail_df.load_maxspeed()
        return True

    def _process_node(self, node_no, detail_df, latlon, operating_time):
        """Process a single node's data including links and geometric properties"""
        # Create node data and get basic info
        node_data = BranchData()
        dic_node = self.combine_node(node_no, detail_df.df_all["node"], detail_df.df_all["turnoff"])
        
        # Set node basic attributes
        self._set_node_attributes(node_data, dic_node, latlon)
        
        # Process links
        link_ls = self._process_links(dic_node["linkno"], detail_df)
        
        # Determine link classifications and branch direction
        node_data.obj_link_data_list, node_data.branch_direction = self.determine_link(
            node_data, link_ls, detail_df.df_all, detail_df.path, operating_time
        )

        # Process border and calculate geometric properties
        node_data.border, node_data.border_length = self.border_correction(node_data, dic_node["border"])
        self._calculate_geometry(node_data)
        
        return node_data

    def _set_node_attributes(self, node_data, dic_node, latlon):
        """Set basic node attributes from dictionary data"""
        node_data.meshcode = dic_node["meshcode"]
        node_data.nodeno = dic_node["nodeno"]
        node_data.starting_point["lat"] = latlon[0]
        node_data.starting_point["lon"] = latlon[1]
        node_data.starting_border["lat"] = dic_node["border"][0][0]
        node_data.starting_border["lon"] = dic_node["border"][0][1]
        node_data.coordinate["lat"] = dic_node["lat"]
        node_data.coordinate["lon"] = dic_node["lon"]

    def _process_links(self, linkno_ls, detail_df):
        """Process and create LinkData objects for all links"""
        link_ls = []
        for linkno in linkno_ls:
            link_data = LinkData()
            dic_link = self.combine_link(linkno, detail_df.df_all["oneway"], detail_df.df_all["enterexit"], detail_df.df_all["maxspeed"])
            
            # Set link attributes
            link_data.meshcode = dic_link["meshcode"]
            link_data.linkno = dic_link["linkno"]
            link_data.snodeno = dic_link["snodeno"]
            link_data.enodeno = dic_link["enodeno"]
            link_data.lanecnt = dic_link["lanecnt"]
            link_data.maxspeed = dic_link["maxspeed"]
            link_ls.append(link_data)
        
        return link_ls

    def _calculate_geometry(self, node_data):
        """Calculate road gradient and curvature"""
        # Calculate road gradient
        if node_data.branch_direction in [0, 1]:
            link = node_data.obj_link_data_list[node_data.branch_direction]
            if len(link.center) > 50:
                node_data.road_gradient = self._calculate_gradient(link)

        # Calculate road curvature
        extraction_range = 10
        point_for_fitting = 10
        
        # Get center points
        xy_center_ls = copy.deepcopy(node_data.obj_link_data_list[node_data.branch_direction].center)
        dist_center = [(xy["x"]**2 + xy["y"]**2) for xy in xy_center_ls]
        index_min = dist_center.index(min(dist_center))
        xy_center_ls = xy_center_ls[index_min:]

        # Calculate curvature using circle fitting
        len_center = len(xy_center_ls)
        if len_center > 10:
            r_ls = []
            iterations = extraction_range if len_center > 100 else int(len_center / 10)
            
            for j in range(iterations):
                x_in = [xy_center_ls[-(j * 10 + k) - 1]["x"] for k in range(point_for_fitting)]
                y_in = [xy_center_ls[-(j * 10 + k) - 1]["y"] for k in range(point_for_fitting)]
                r_optimized = ajust.fitting_circle(x_in, y_in)
                r_ls.append(r_optimized)
                
            node_data.curvature = r_ls

    def _calculate_gradient(self, link):
        """Calculate road gradient for a link"""
        vertical_distance = link.center[0]["elevation"] - link.center[49]["elevation"]
        horizontal_distance = math.sqrt(
            (link.center[0]["x"] - link.center[49]["x"]) ** 2 +
            (link.center[0]["y"] - link.center[49]["y"]) ** 2
        )
        return vertical_distance * 100 / horizontal_distance

    def combine_node(self, df_junc, df_node, df_turnoff):
        """
        Combine node information from different data sources.

        Args:
            df_junc: Junction node number
            df_node: DataFrame containing node information
            df_turnoff: DataFrame containing turnoff boundary information

        Returns:
            dict: Combined node data including meshcode, node number, coordinates,
                 link numbers and border information
        """
        # Get latitude/longitude for node numbers corresponding to branch/merge sections from NODE file
        # Used for TURNOFF_BORDER data extraction
        turn_off_label = [
            "ido1",
            "keido1",
            "ido2",
            "keido2",
            "ido3",
            "keido3",
            "ido4",
            "keido4",
            "ido5",
            "keido5",
        ]

        # Get node numbers for branch/merge sections from NODE file
        # Note: Since branch/merge sections overlap at the center point, 3 data with different link numbers are extracted
        df_same_node = df_node[df_node["nodeno"] == df_junc].reset_index(drop=True)
        # Extract latitude/longitude information from TRUNOFF_BORDER
        border_ls = []
        df_same_turnoff = df_turnoff[df_turnoff["nodeno"] == df_junc].reset_index(drop=True)
        for j in range(len(df_same_turnoff)):
            for k in range(5):
                if df_same_turnoff[turn_off_label[2 * k]][j] != 0 and df_same_turnoff[turn_off_label[2 * k + 1]][j] != 0:
                    border_ls += [
                        [
                            df_same_turnoff[turn_off_label[2 * k]][j],
                            df_same_turnoff[turn_off_label[2 * k + 1]][j],
                        ]
                    ]
                else:
                    break

        # Extract link numbers from extracted data
        linkno_ls = []
        for j in range(len(df_same_node)):
            linkno_ls += [df_same_node["linkno"][j]]

        dic_data = {
            "meshcode": "Z" + str(df_same_node["meshcode"][0]),
            "nodeno": df_same_node["nodeno"][0],
            "lat": df_same_node["y"][0],
            "lon": df_same_node["x"][0],
            "linkno": linkno_ls,
            "border": border_ls,
        }

        return dic_data

    def combine_link(self, linkno, df_oneway, df_enterexit, df_maxspeed):
        """
        Extract and combine link data for a given link number.

        Args:
            linkno: Link number to process
            df_oneway: DataFrame containing one-way road information
            df_enterexit: DataFrame containing entrance/exit information

        Returns:
            dict: Combined link data including meshcode, link numbers, node numbers,
                 and lane count
        """
        link_node = df_oneway[df_oneway["linkno"] == linkno].reset_index(drop=True)

        link_meshcode = link_node["meshcode"][0]
        link_no = link_node["linkno"][0]
        link_snodeno = link_node["snodeno"][0]
        link_enodeno = link_node["enodeno"][0]  
        filtered_df = df_maxspeed[df_maxspeed["linkno"] == linkno].reset_index(drop=True)
        if not filtered_df.empty:
            link_maxspeed = filtered_df["maxspeed"][0]
        else:
            link_maxspeed = None
        # print('snodeno', link_snodeno)

        if sum(df_enterexit["enodeno"] == link_enodeno) == 1:
            lanecnt = df_enterexit[df_enterexit["enodeno"] == link_enodeno]["elanecnt"].reset_index(drop=True)
            link_lanecnt = lanecnt[0]

        elif sum(df_enterexit["enodeno"] == link_enodeno) > 1:
            elinks = df_enterexit[df_enterexit["enodeno"] == link_enodeno]
            lanecnt = elinks[elinks["tnodeno"] == link_snodeno]["elanecnt"].reset_index(drop=True)
            link_lanecnt = lanecnt[0]

        elif sum(df_enterexit["tnodeno"] == link_enodeno) == 2:
            lanecnt = df_enterexit[df_enterexit["tnodeno"] == link_enodeno]["slanecnt"].reset_index(drop=True)
            link_lanecnt = lanecnt[0]

        dic_data = {
            "meshcode": link_meshcode,
            "linkno": link_no,
            "snodeno": link_snodeno,
            "enodeno": link_enodeno,
            "lanecnt": link_lanecnt,
            "maxspeed": link_maxspeed,
        }

        return dic_data

    def determine_link(self, node_data, link_ls, df_all, db_path, operating_time):
        """
        Main function to classify and process link connections at branch/merge points.
        
        Args:
            node_data: NodeData object containing branch node information
            link_ls: List of LinkData objects
            df_all: Dictionary of all DataFrames
            db_path: Path to database
            operating_time: Time of operation
        
        Returns:
            tuple: (list of classified LinkData objects, branch direction)
        """
        
        # Step 1: Get pre-branch mainline and JSON data
        determined_link, determined_json, uncateg = self._classify_pre_branch_mainline(
            node_data, link_ls, db_path, df_all
        )
        
        # Step 2: Pair and classify remaining links
        determined_link, determined_json = self._classify_remaining_links(
            uncateg, df_all["node"], df_all["enterexit"], determined_link, determined_json
        )
        
        # Step 3: Process coordinates and attributes
        determined_link = self._process_link_coordinates(determined_link, determined_json, node_data)
        
        # Step 4: Calculate branch direction
        result, branch_direction = self._calculate_branch_direction(
            determined_link, node_data
        )
        
        return result, branch_direction

    def _initialize_containers(self):
        """Initialize containers for link and JSON data"""
        return (
            {"0": 0, "1": 0, "2": 0},
            {"0": 0, "1": 0, "2": 0}
        )

    def _classify_pre_branch_mainline(self, node_data, link_ls, db_path, df_all):
        """
        Classify pre-branch mainline and get corresponding JSON data.
        
        Returns:
            tuple: (determined_link, determined_json, uncategorized)
        """
        determined_link, determined_json = self._initialize_containers()
        uncateg = {"link": [], "json": []}
        
        # Load navigation data
        navi_data = ItsumoNaviData(db_path, self.junction_flag, node_data.meshcode, node_data.nodeno)
        navi_data.road_json(df_all)
        
        # Classify pre-branch mainline
        for link in link_ls:
            if link.enodeno == node_data.nodeno:
                determined_link["2"] = link
            else:
                uncateg["link"].append(link)
        
        # Match JSON data with pre-branch mainline
        determined_json["2"], uncateg["json"] = self._match_json_data(navi_data.json_data["item"][0])
        
        return determined_link, determined_json, uncateg

    def _match_json_data(self, json_data):
        """Match JSON data with pre-branch mainline based on coordinates"""
        j_elatlon_ls = [[j["link"]["line"][0], j["link"]["line"][1]] for j in json_data]
        
        if j_elatlon_ls[0] == j_elatlon_ls[1]:
            return json_data[2], [json_data[0], json_data[1]]
        elif j_elatlon_ls[0] == j_elatlon_ls[2]:
            return json_data[1], [json_data[0], json_data[2]]
        else:
            return json_data[0], [json_data[1], json_data[2]]

    def _classify_remaining_links(self, uncateg, df_node, df_enterexit, determined_link, determined_json):
        """
        Classify remaining links based on various criteria.
        """
        # Pair links with JSON data based on distance
        uncateg = self._pair_links_with_json(uncateg, df_node)
        
        # Calculate scores for classification
        score0, score1 = self._calculate_link_scores(uncateg, df_enterexit)
        
        # Assign links based on scores
        return self._assign_links_based_on_scores(score0, score1, uncateg, determined_link, determined_json)

    def _pair_links_with_json(self, uncateg, df_node):
        """
        Pair unclassified links with JSON data based on minimum distance.
        
        Args:
            uncateg (dict): Dictionary containing unclassified links and JSON data
            df_node (DataFrame): DataFrame containing node information
            
        Returns:
            dict: Updated uncateg dictionary with JSON data paired to links based on distance
        """
        enode = df_node[df_node["nodeno"] == uncateg["link"][0].enodeno].reset_index(drop=True)
        latlon_enode = [enode["y"][0], enode["x"][0]]
        
        # Calculate minimum distances
        distances = self._calculate_minimum_distances(uncateg["json"], latlon_enode)
        
        # Swap JSON data if needed based on distances
        if distances[0] > distances[1]:
            uncateg["json"] = [uncateg["json"][1], uncateg["json"][0]]
        
        return uncateg

    def _calculate_link_scores(self, uncateg, df_enterexit):
        """
        Calculate scores for link classification based on multiple criteria.
        Returns tuple of scores for both links.
        """
        score0 = 0
        score1 = 0
        link0_enterexit0 = df_enterexit[
            df_enterexit["enodeno"] == uncateg["link"][0].enodeno
        ].reset_index(drop=True)

        link0_enterexit = link0_enterexit0[
            link0_enterexit0["tnodeno"] == uncateg["link"][0].snodeno
        ].reset_index(drop=True)

        link1_enterexit1 = df_enterexit[
            df_enterexit["enodeno"] == uncateg["link"][1].enodeno
        ].reset_index(drop=True)

        link1_enterexit = link1_enterexit1[
            link1_enterexit1["tnodeno"] == uncateg["link"][0].snodeno
        ].reset_index(drop=True)

        ##車線数を比較、多い方に+2。同じ場合は0
        lanecnt0 = uncateg["link"][0].lanecnt
        lanecnt1 = uncateg["link"][1].lanecnt

        if lanecnt0 > lanecnt1:
            score0 += 2
        elif lanecnt0 < lanecnt1:
            score1 += 2

        ##合流前後の車線位置を比較、全一致+3、一部一致+1、一致なし0
        slaneinfo = list(link0_enterexit["slaneinfo"][0])
        slane_index = np.where(np.array(slaneinfo) == "1")[0]
        elaneinfo0 = list(link0_enterexit["elaneinfo"][0])
        index0 = np.where(np.array(elaneinfo0) == "1")[0]
        elaneinfo1 = list(link1_enterexit["elaneinfo"][0])
        index1 = np.where(np.array(elaneinfo1) == "1")[0]

        lane_match0 = list(set(slane_index) & set(index0))
        lane_match1 = list(set(slane_index) & set(index1))

        if len(slane_index) == len(lane_match0):
            score0 += 3
        elif len(slane_index) > len(lane_match0) & len(lane_match0) != 0:
            score0 += 1

        if len(slane_index) == len(lane_match1):
            score1 += 3
        elif len(slane_index) > len(lane_match1) & len(lane_match1) != 0:
            score1 += 1

        ##jsonデータの最高速度を比較、高い方に+2、同じ場合0
        if uncateg["json"][0]["link"]["adas"].get("maxspeedFront")!= None:
            maxspeedq0 = uncateg["json"][0]["link"]["adas"]["maxspeedFront"][0]["limit"]
        else:
            maxspeedq0 = 40
        if uncateg["json"][1]["link"]["adas"].get("maxspeedFront")!= None:
            maxspeedq1 = uncateg["json"][1]["link"]["adas"]["maxspeedFront"][0]["limit"]
        else:
            maxspeedq1 = 40

        if maxspeedq0 > maxspeedq1:
            score0 += 1
        elif maxspeedq0 < maxspeedq1:
            score1 += 1
        
        return score0, score1

    def _get_lane_info(self, uncateg, df_enterexit):
        """Extract lane information for scoring"""
        link0_enterexit = df_enterexit[
            (df_enterexit["enodeno"] == uncateg["link"][0].enodeno) &
            (df_enterexit["tnodeno"] == uncateg["link"][0].snodeno)
        ].reset_index(drop=True)
        
        link1_enterexit = df_enterexit[
            (df_enterexit["enodeno"] == uncateg["link"][1].enodeno) &
            (df_enterexit["tnodeno"] == uncateg["link"][1].snodeno)
        ].reset_index(drop=True)
        
        return {
            "slaneinfo": list(link0_enterexit["slaneinfo"][0]),
            "elaneinfo0": list(link0_enterexit["elaneinfo"][0]),
            "elaneinfo1": list(link1_enterexit["elaneinfo"][0])
        }

    def _score_lane_counts(self, lanecnt0, lanecnt1, score0, score1):
        """Score based on lane counts"""
        if lanecnt0 > lanecnt1:
            score0 += 2
        elif lanecnt0 < lanecnt1:
            score1 += 2
        return score0, score1

    def _score_lane_matching(self, lane_info, score0, score1):
        """Score based on lane position matching"""
        slane_index = np.where(np.array(lane_info["slaneinfo"]) == "1")[0]
        index0 = np.where(np.array(lane_info["elaneinfo0"]) == "1")[0]
        index1 = np.where(np.array(lane_info["elaneinfo1"]) == "1")[0]
        
        match0 = len(set(slane_index) & set(index0))
        match1 = len(set(slane_index) & set(index1))
        
        score0 = self._update_match_score(match0, len(slane_index), score0)
        score1 = self._update_match_score(match1, len(slane_index), score1)
        
        return score0, score1

    def _update_match_score(self, matches, total, score):
        """Update score based on lane matching"""
        if matches == total:
            return score + 3
        elif matches > 0:
            return score + 1
        return score

    def _assign_links_based_on_scores(self, score0, score1, uncateg, determined_link, determined_json):
        """Assign links to determined_link based on calculated scores"""
        if score0 > score1:
            determined_link["0"] = uncateg["link"][1]
            determined_json["0"] = uncateg["json"][1]
            determined_link["1"] = uncateg["link"][0]
            determined_json["1"] = uncateg["json"][0]
        else:
            determined_link["0"] = uncateg["link"][0]
            determined_json["0"] = uncateg["json"][0]
            determined_link["1"] = uncateg["link"][1]
            determined_json["1"] = uncateg["json"][1]
        
        return determined_link, determined_json

    def _calculate_branch_direction(self, determined_link, node_data):
        """Calculate branch direction based on vector cross product"""
        # Get coordinates
        xy2 = self._get_xy_coordinates(determined_link["2"], node_data, -2)
        xy0 = self._get_xy_coordinates(determined_link["0"], node_data, 2)
        xy1 = self._get_xy_coordinates(determined_link["1"], node_data, 2)
        
        # Calculate vectors
        vector_acceleration = [-xy0[0] + xy2[0], -xy0[1] + xy2[1]]
        vector_main = [-xy1[0] + xy2[0], -xy1[1] + xy2[1]]
        
        # Calculate cross product
        outer_product = (vector_acceleration[0] * vector_main[1] - 
                        vector_acceleration[1] * vector_main[0])
        
        return self._determine_result(outer_product, determined_link, node_data)

    def _get_xy_coordinates(self, link, node_data, index):
        """Get XY coordinates for a link at specified index"""
        return vm.coord2XY(
            node_data.starting_point["lat"],
            node_data.starting_point["lon"],
            link.line[index],
            link.line[index + 1]
        )

    def _determine_result(self, outer_product, determined_link, node_data):
        """Determine branch direction based on cross product"""
        if outer_product < 0:
            branch_direction = 0
            result = [
                determined_link["0"],
                determined_link["1"],
                determined_link["2"],
            ]
        elif outer_product > 0:
            branch_direction = 1
            result = [
                determined_link["1"],
                determined_link["0"],
                determined_link["2"],
            ]
        else:
            branch_direction = 0
            result = [
                determined_link["0"],
                determined_link["1"],
                determined_link["2"],
            ]
            self.error_log += [self.meshcode + "_" + str(node_data.nodeno) + " : Cross product is zero"]
        
        return result, branch_direction

    def extract_road_center(self, xyzdist_ls, nodeno, num):
        """
        Extract and process road center line coordinates.

        Args:
            xyzdist_ls: List of coordinate points [x,y,z,distance]
            nodeno: Node number
            num: Link number identifier

        Returns:
            tuple: (x_adjusted, y_adjusted, z_adjusted) Processed center line coordinates
        """
        span = 20
        if len(xyzdist_ls) > 5:
            cull_xyzdist = ajust.input_match(xyzdist_ls, span)
            if len(cull_xyzdist) < 4:
                cull_xyzdist = xyzdist_ls
        else:
            cull_xyzdist = xyzdist_ls

        x_ls, y_ls, z_ls = [], [], []
        if len(cull_xyzdist) > 3:
            for i in range(len(cull_xyzdist)):
                x_ls += [cull_xyzdist[i][0]]
                y_ls += [cull_xyzdist[i][1]]
                z_ls += [cull_xyzdist[i][2] / 1000]
            result = ajust.B_spline(x_ls, y_ls, z_ls)
            result[0] = np.append(result[0], [cull_xyzdist[-1][0]])
            result[1] = np.append(result[1], [cull_xyzdist[-1][1]])
            result[2] = np.append(result[2], [cull_xyzdist[-1][2] / 1000])
            x_ajusted = result[0]
            y_ajusted = result[1]
            z_ajusted = result[2]

        else:
            x_ajusted, y_ajusted, z_ajusted = [], [], []

            x_ajusted += [cull_xyzdist[0][0]]
            y_ajusted += [cull_xyzdist[0][1]]
            z_ajusted += [cull_xyzdist[0][2] / 1000]

            x_ajusted += [cull_xyzdist[-1][0]]
            y_ajusted += [cull_xyzdist[-1][1]]
            z_ajusted += [cull_xyzdist[-1][2] / 1000]

            n = int(math.sqrt((x_ajusted[1] - x_ajusted[0]) ** 2 + (y_ajusted[1] - y_ajusted[0]) ** 2))
            if n < 5:
                n = 5

            x_ajusted = ajust.interpolate_to_5(x_ajusted, n)
            y_ajusted = ajust.interpolate_to_5(y_ajusted, n)
            z_ajusted = ajust.interpolate_to_5(z_ajusted, n)

        return x_ajusted, y_ajusted, z_ajusted  # ,x_op,y_op,z_op

    def border_correction(self, node_data: object, border_node):
        """
        Process and correct branch boundary line coordinates.

        Args:
            node_data: NodeData object containing branch information
            border_node: List of border node coordinates

        Returns:
            tuple: (border_coordinate, border_length)
                border_coordinate: List of processed border points with elevation parameters
                border_length: Total length of the border line

        This method:
        1. Converts coordinates to XY system
        2. Corrects boundary line points
        3. Calculates elevation parameters for OpenDRIVE format
        4. Computes total border length
        """
        link_ls = node_data.obj_link_data_list
        branch_direction = node_data.branch_direction
        # Convert TURNOFF_BORDER road center points to xy coordinates
        xy_border = []
        x_border_ls, y_border_ls = [], []
        for j in range(len(border_node)):
            x_border, y_border, dist, azim = vm.coord2XY(
                node_data.starting_point["lat"],
                node_data.starting_point["lon"],
                border_node[j][0],
                border_node[j][1],
            )
            x_border_ls += [x_border]
            y_border_ls += [y_border]

        # Correct branch boundary line
        if len(x_border_ls) > 1:
            ops_border = ajust.fitting_border(x_border_ls, y_border_ls)
            for j in range(len(ops_border[0])):
                xy_border += [[ops_border[0][j], ops_border[1][j]]]
        else:
            for j in range(len(x_border_ls)):
                xy_border += [[x_border_ls[j], y_border_ls[j]]]

        xyz_border = []
        if branch_direction == 0:
            road_xyz = link_ls[0].center + link_ls[2].center

            dist_ls_0 = []
            for k in range(len(road_xyz)):
                dist = (road_xyz[k]["x"] - xy_border[0][0]) ** 2 + (road_xyz[k]["y"] - xy_border[0][1]) ** 2
                dist_ls_0 += [dist]
            min_id_0 = dist_ls_0.index(min(dist_ls_0))

            for j in range(len(xy_border)):
                dist_ls = []
                for k in range(min_id_0, len(road_xyz)):
                    dist = (road_xyz[k]["x"] - xy_border[j][0]) ** 2 + (road_xyz[k]["y"] - xy_border[j][1]) ** 2
                    dist_ls += [dist]
                min_id = dist_ls.index(min(dist_ls))

                xyz_border += [
                    [
                        xy_border[j][0],
                        xy_border[j][1],
                        road_xyz[min_id + min_id_0]["elevation"],
                    ]
                ]

            inx = []
            for i in range(len(xyz_border) - 1):
                if xyz_border[i][2] == xyz_border[i + 1][2]:
                    inx += [i]

            if len(inx) > 1:
                result = []
                current_sequence = []
                if len(inx) > 0:
                    current_sequence = [inx[0]]

                for i in range(1, len(inx)):
                    if inx[i] == inx[i - 1] + 1:
                        current_sequence.append(inx[i])
                    else:
                        if len(current_sequence) > 2:
                            result.append(current_sequence.copy())

                        current_sequence = [inx[i]]

                if len(current_sequence) > 2:
                    result.append(current_sequence.copy())

                for i in range(len(result)):
                    d = (xyz_border[result[i][0] - 1][2] - xyz_border[result[i][-1] + 1][2]) / (result[i][-1] - result[i][0] + 1)
                    for j in range(result[i][0], result[i][-1] + 1):
                        xyz_border[j][2] = xyz_border[j][2] + d * (result[i][-1] - j)

        elif branch_direction == 1:
            road_xyz = link_ls[1].center + link_ls[2].center

            dist_ls_0 = []
            for k in range(len(road_xyz)):
                dist = (road_xyz[k]["x"] - xy_border[0][0]) ** 2 + (road_xyz[k]["y"] - xy_border[0][1]) ** 2
                dist_ls_0 += [dist]
            min_id_0 = dist_ls_0.index(min(dist_ls_0))

            for j in range(len(xy_border)):
                dist_ls = []
                for k in range(min_id_0, len(road_xyz)):
                    dist = (road_xyz[k]["x"] - xy_border[j][0]) ** 2 + (road_xyz[k]["y"] - xy_border[j][1]) ** 2
                    dist_ls += [dist]
                min_id = dist_ls.index(min(dist_ls))

                xyz_border += [
                    [
                        xy_border[j][0],
                        xy_border[j][1],
                        road_xyz[min_id + min_id_0]["elevation"],
                    ]
                ]

            inx = []
            for i in range(len(xyz_border) - 1):
                if xyz_border[i][2] == xyz_border[i + 1][2]:
                    inx += [i]

            if len(inx) > 1:
                result = []
                current_sequence = [inx[0]]

                for i in range(1, len(inx)):
                    if inx[i] == inx[i - 1] + 1:
                        current_sequence.append(inx[i])
                    else:
                        if len(current_sequence) > 2:
                            result.append(current_sequence.copy())

                        current_sequence = [inx[i]]

                if len(current_sequence) > 2:
                    result.append(current_sequence.copy())

                for i in range(len(result)):
                    d = (xyz_border[result[i][0] - 1][2] - xyz_border[result[i][-1] + 1][2]) / (result[i][-1] - result[i][0] + 1)
                    for j in range(result[i][0], result[i][-1] + 1):
                        xyz_border[j][2] = xyz_border[j][2] + d * (result[i][-1] - j)

        # Calculate parameters for cubic polynomial approximation in z direction for OpenDrive
        border_coordinate = []
        for j in range(len(xyz_border)):
            x_ls, y_ls, z_ls = [], [], []
            # Define dictionary type to put in border attribute
            dic_latlonelev = {
                "x": 0,
                "y": 0,
                "elevation": 0,
                "elev_param": {"s": 0, "a": 0, "b": 0, "c": 0, "d": 0},
            }

            if len(xyz_border) < 4:
                dic_latlonelev["x"] = xyz_border[j][0]
                dic_latlonelev["y"] = xyz_border[j][1]
                dic_latlonelev["elevation"] = xyz_border[j][2]
                dic_latlonelev["elev_param"]["s"] = 1
                dic_latlonelev["elev_param"]["a"] = xyz_border[j][2]
                dic_latlonelev["elev_param"]["b"] = 0
                dic_latlonelev["elev_param"]["c"] = 0
                dic_latlonelev["elev_param"]["d"] = 0

                border_coordinate += [dic_latlonelev]
                continue

            if j > 0 and len(xyz_border) - 2 > j:
                for k in range(4):
                    x_ls += [xyz_border[j - 1 + k][0]]
                    y_ls += [xyz_border[j - 1 + k][1]]
                    z_ls += [xyz_border[j - 1 + k][2]]
                s_position = 1

            elif j == 0:
                for k in range(4):
                    x_ls += [xyz_border[j + k][0]]
                    y_ls += [xyz_border[j + k][1]]
                    z_ls += [xyz_border[j + k][2]]
                s_position = 0

            elif j == len(xyz_border) - 2:
                for k in range(4):
                    x_ls += [xyz_border[j - 4 + k][0]]
                    y_ls += [xyz_border[j - 4 + k][1]]
                    z_ls += [xyz_border[j - 4 + k][2]]
                s_position = 2

            elif j == len(xyz_border) - 1:
                for k in range(4):
                    x_ls += [xyz_border[j - 4 + k][0]]
                    y_ls += [xyz_border[j - 4 + k][1]]
                    z_ls += [xyz_border[j - 4 + k][2]]
                s_position = 3

            if len(x_ls) > 3:
                (
                    optimized_elev_param,
                    optimized_elev_param_s,
                ) = ajust.fitting_3D_elev(x_ls, y_ls, z_ls, s_position)

                dic_latlonelev["elev_param"]["s"] = optimized_elev_param_s
                dic_latlonelev["elev_param"]["a"] = optimized_elev_param[0]
                dic_latlonelev["elev_param"]["b"] = optimized_elev_param[1]
                dic_latlonelev["elev_param"]["c"] = optimized_elev_param[2]
                dic_latlonelev["elev_param"]["d"] = optimized_elev_param[3]

            dic_latlonelev["x"] = xyz_border[j][0]
            dic_latlonelev["y"] = xyz_border[j][1]
            dic_latlonelev["elevation"] = xyz_border[j][2]

            border_coordinate += [dic_latlonelev]

        dis = 0
        for j in range(len(border_coordinate) - 1):
            xyz_0 = border_coordinate[j]
            xyz_1 = border_coordinate[j + 1]
            dis_one = math.sqrt((xyz_1["x"] - xyz_0["x"]) ** 2 + (xyz_1["y"] - xyz_0["y"]) ** 2 + (xyz_1["elevation"] - xyz_0["elevation"]) ** 2)
            dis = dis + dis_one
        border_length = dis

        return border_coordinate, border_length

    def _calculate_minimum_distances(self, json_list, latlon_enode):
        """
        Calculate minimum distances between JSON road points and reference node.
        
        Args:
            json_list (list): List of JSON objects containing road data
            latlon_enode (list): Reference node coordinates [lat, lon]
        
        Returns:
            list: List of minimum distances for each JSON object
        """
        distances = []
        
        for json_obj in json_list:
            min_distance = float('inf')
            
            # Get all road elevation points from JSON
            road_points = json_obj["link"]["adas"]["roadelevation"]
            
            # Calculate distance to each point and find minimum
            for point in road_points:
                dist = self._calculate_point_distance(
                    latlon_enode,
                    [point["lat"], point["lon"]]
                )
                min_distance = min(min_distance, dist)
                
            distances.append(min_distance)
        
        return distances

    def _calculate_point_distance(self, point1, point2):
        """
        Calculate Euclidean distance between two points using vincenty method.
        
        Args:
            point1 (list): First point coordinates [lat, lon]
            point2 (list): Second point coordinates [lat, lon]
        
        Returns:
            float: Distance between points
        """
        result = vm.coord2XY(
            point1[0], point1[1],
            point2[0], point2[1]
        )
        return result[2]  # Return distance component

    def _score_speed_limits(self, json_list, score0, score1):
        """
        Calculate scores based on speed limits from JSON data.
        
        Args:
            json_list (list): List of JSON objects containing road data
            score0 (int): Current score for first link
            score1 (int): Current score for second link
        
        Returns:
            tuple: Updated scores (score0, score1)
        """
        # Get speed limits, default to DEFAULT_SPEED if not specified
        DEFAULT_SPEED = 60
        
        speed0 = json_list[0]["link"]["adas"].get("maxspeedFront", [{"limit": DEFAULT_SPEED}])[0]["limit"]
        speed1 = json_list[1]["link"]["adas"].get("maxspeedFront", [{"limit": DEFAULT_SPEED}])[0]["limit"]
        
        # Add points to score based on speed comparison
        if speed0 > speed1:
            score0 += 1
        elif speed0 < speed1:
            score1 += 1
        
        return score0, score1

    def _process_link_coordinates(self, determined_link, determined_json, node_data):
        """
        Process coordinates and attributes for each link.
        
        Args:
            determined_link (dict): Dictionary of classified links
            determined_json (dict): Dictionary of corresponding JSON data
            node_data (NodeData): Node data object containing reference coordinates
            
        Returns:
            dict: Updated determined_link with processed coordinates and attributes
        """
        for i in range(len(determined_link)):
            determined_json[str(i)]["link"]["adas"]["roadelevation"][0]["lat"] = determined_json[str(i)]["link"]["line"][0]
            determined_json[str(i)]["link"]["adas"]["roadelevation"][0]["lon"] = determined_json[str(i)]["link"]["line"][1]

            determined_json[str(i)]["link"]["adas"]["roadelevation"][-1]["lat"] = determined_json[str(i)]["link"]["line"][-2]
            determined_json[str(i)]["link"]["adas"]["roadelevation"][-1]["lon"] = determined_json[str(i)]["link"]["line"][-1]

            lon, lat, elevation = [], [], []
            xyzdist_ls = []
            for lonlat_json in determined_json[str(i)]["link"]["adas"]["roadelevation"]:
                lat += [lonlat_json["lat"]]
                lon += [lonlat_json["lon"]]
                elevation += [lonlat_json["elevation"]]

            if i < 2:
                # 緯度経度をnode_dataに保存されている基準点を中心にxy座標へ変換
                for j in range(len(lon)):
                    # x,y,dist,azim = vm.coord2XY(lat[0],lon[0],lat[j],lon[j])
                    xy = vm.coord2XY(
                        node_data.starting_point["lat"],
                        node_data.starting_point["lon"],
                        lat[j],
                        lon[j],
                    )

                    if j == 0:
                        dist = vm.coord2XY(lat[j], lon[j], lat[j], lon[j])
                    else:
                        dist = vm.coord2XY(
                            lat[j - 1], lon[j - 1], lat[j], lon[j]
                        )

                    xyzdist_ls += [[xy[0], xy[1], elevation[j], dist[2]]]

            else:
                for j in range(len(lon)):
                    # x,y,dist,azim = vm.coord2XY(lat[0],lon[0],lat[j],lon[j])
                    xy = vm.coord2XY(
                        node_data.starting_point["lat"],
                        node_data.starting_point["lon"],
                        lat[j],
                        lon[j],
                    )

                    if j == 0:
                        dist = vm.coord2XY(lat[j], lon[j], lat[j], lon[j])
                    else:
                        dist = vm.coord2XY(
                            lat[j - 1], lon[j - 1], lat[j], lon[j]
                        )

                    xyzdist_ls += [[xy[0], xy[1], elevation[j], dist[2]]]

                after_branch_lat = determined_json[str(1)]["link"]["adas"]["roadelevation"][0]["lat"]
                after_branch_lon = determined_json[str(1)]["link"]["adas"]["roadelevation"][0]["lon"]
                after_branch_elev = determined_json[str(1)]["link"]["adas"]["roadelevation"][0]["elevation"]
                xy = vm.coord2XY(
                    node_data.starting_point["lat"],
                    node_data.starting_point["lon"],
                    after_branch_lat,
                    after_branch_lon,
                )
                dist = vm.coord2XY(
                    lat[-1], lon[-1], after_branch_lat, after_branch_lon
                )
                xyzdist_ls += [[xy[0], xy[1], after_branch_elev, dist[2]]]

            # 道路中心点群の間引きと補正

            (
                road_center_x,
                road_center_y,
                road_center_z,
            ) = self.extract_road_center(xyzdist_ls, node_data.nodeno, i)

            road_center_xyz = []

            for j in range(len(road_center_x)):
                road_center_xyz += [
                    [road_center_x[j], road_center_y[j], road_center_z[j]]
                ]

            # OpenDrive化時に用いる、z方向の三次多項式近似のパラメータを求める
            for j in range(len(road_center_xyz)):
                dic_latlonelev = {
                    "x": 0,
                    "y": 0,
                    "elevation": 0,
                    "elev_param": {"s": 0, "a": 0, "b": 0, "c": 0, "d": 0},
                }
                if j > 0 and len(road_center_xyz) - 2 > j:
                    x_ls = road_center_x[j - 1 : j + 3]
                    y_ls = road_center_y[j - 1 : j + 3]
                    z_ls = road_center_z[j - 1 : j + 3]
                    s_position = 1
                elif j == 0:
                    x_ls = road_center_x[j : j + 4]
                    y_ls = road_center_y[j : j + 4]
                    z_ls = road_center_z[j : j + 4]
                    s_position = 0
                elif j == len(road_center_xyz) - 2:
                    x_ls = road_center_x[-4:]
                    y_ls = road_center_y[-4:]
                    z_ls = road_center_z[-4:]
                    s_position = 2
                elif j == len(road_center_xyz) - 1:
                    x_ls = road_center_x[-4:]
                    y_ls = road_center_y[-4:]
                    z_ls = road_center_z[-4:]
                    s_position = 3

                if len(x_ls) > 3:
                    (
                        optimized_elev_param,
                        optimized_elev_param_s,
                    ) = ajust.fitting_3D_elev(x_ls, y_ls, z_ls, s_position)

                    dic_latlonelev["elev_param"]["s"] = optimized_elev_param_s
                    dic_latlonelev["elev_param"]["a"] = optimized_elev_param[0]
                    dic_latlonelev["elev_param"]["b"] = optimized_elev_param[1]
                    dic_latlonelev["elev_param"]["c"] = optimized_elev_param[2]
                    dic_latlonelev["elev_param"]["d"] = optimized_elev_param[3]

                else:
                    dic_latlonelev["elev_param"]["s"] = 1
                    dic_latlonelev["elev_param"]["a"] = road_center_z[j]
                    dic_latlonelev["elev_param"]["b"] = 0
                    dic_latlonelev["elev_param"]["c"] = 0
                    dic_latlonelev["elev_param"]["d"] = 0

                dic_latlonelev["x"] = road_center_xyz[j][0]
                dic_latlonelev["y"] = road_center_xyz[j][1]
                dic_latlonelev["elevation"] = road_center_xyz[j][2]

                determined_link[str(i)].center += [dic_latlonelev]
            optimized_center_xy = []

            if determined_link[str(i)].maxspeed is None:
                route_extractor = RouteExtract()
                determined_link[str(i)].maxspeed = route_extractor._get_maxspeed(determined_json[str(i)])

            determined_link[str(i)].road_name = determined_json[str(i)]["link"]["generalRoadName1"]

            determined_link[str(i)].line = determined_json[str(i)]["link"]["line"]
            determined_link[str(i)].roadelevation = determined_json[str(i)]["link"]["adas"]["roadelevation"]
          
        return determined_link

