import math
import copy
import numpy as np
from tqdm import tqdm

from common_extract import CommonExtract
from route_extract import RouteExtract
from route_data import LinkData, MergeData
from itsumo_navi import ItsumoNaviData
from detail_navi import DetailNaviData
from submodule import vincenty_method as vm
from submodule import ajust


class MergeExtract:
    """
    A class for extracting and processing merge sections from road network data.

    This class handles the identification, extraction, and processing of road merge points,
    including coordinate transformations, elevation calculations, and geometric analysis.

    Attributes:
        node_ls (list): List of NodeData objects containing merge center node information
        meshcode (str): Secondary mesh code for area identification
        junction_flag (int): Flag to select between merge (0) or branch (1) section
        path (str): Relative path to folder for saving data
        error_log (list): Log for recording processing errors
    """

    def __init__(self, meshcode, junction_flag, path):
        self.node_ls = []  # List of NodeData objects containing merge center node information
        self.meshcode = meshcode  # Secondary mesh code
        self.junction_flag = junction_flag  # Flag to select between merge (0) or branch (1) section
        self.path = path  # Relative path to folder for saving data
        self.error_log = []

    def road_shp(self):
        """
        Convert DetailNaviData DBF files to CSV format and process coordinate data.

        This method performs one-time initialization by:
        1. Converting DBF files to CSV format
        2. Converting coordinate units from seconds to degrees/minutes/seconds
        """
        # Convert DetailNaviData dbf files to csv format - only needs to be run once
        detail_df = DetailNaviData(self.meshcode, self.path)
        detail_df.dbf_to_csv()  # Convert dbf files to csv
        detail_df.data_forming()  # Convert units from seconds to degrees/minutes/seconds for lat/lon files

    def make_merge_extract(self, operating_time, latlon):
        """
        Extract and process merge sections from the road network.

        Args:
            operating_time: Time of operation for data processing
            latlon (list): Reference coordinates [latitude, longitude] for coordinate conversion

        Returns:
            None. Results are stored in node_ls attribute.
        """
        # Initialize and load required data
        detail_df = DetailNaviData(self.meshcode, self.path)
        merge_exist = detail_df.load_turnoff()
        if merge_exist == "NotFound":
            self.error_log.append(f"{self.meshcode} : There is no merge")
            return

        # Load additional data
        detail_df.load_node()
        detail_df.load_oneway()
        detail_df.load_enterexit()
        detail_df.load_maxspeed()

        # Get merge nodes
        junc = CommonExtract(self.meshcode, self.path, self.junction_flag)
        df_junc_node = junc.judge_junction(detail_df.df_all["oneway"], detail_df.df_all["turnoff"])

        # Process each merge node
        for i in tqdm(range(len(df_junc_node))):
            # Create node data object and get basic node info
            node_data = MergeData()
            dic_node = self.combine_node(df_junc_node["nodeno"][i], detail_df.df_all["node"], detail_df.df_all["turnoff"])

            # Set node properties
            self._set_basic_node_info(node_data, dic_node, latlon)

            # Process links and determine merge properties
            link_ls = self._process_node_links(dic_node, detail_df)
            node_data.obj_link_data_list, node_data.merge_direction = self.determine_link(node_data, link_ls, detail_df.df_all, detail_df.path, operating_time)

            # Process border and calculate merge attributes
            node_data.border, node_data.border_length = self.border_correction(node_data, dic_node["border"])
            self._calculate_merge_environment(node_data)

            self.node_ls.append(node_data)

    def _set_basic_node_info(self, node_data, dic_node, latlon):
        """
        Set basic properties for a merge node.
        """
        node_data.meshcode = dic_node["meshcode"]
        node_data.nodeno = dic_node["nodeno"]
        node_data.starting_point["lat"] = latlon[0]
        node_data.starting_point["lon"] = latlon[1]
        node_data.starting_border["lat"] = dic_node["border"][0][0]
        node_data.starting_border["lon"] = dic_node["border"][0][1]
        node_data.coordinate["lat"] = dic_node["lat"]
        node_data.coordinate["lon"] = dic_node["lon"]

    def _process_node_links(self, dic_node, detail_df):
        """
        Process links connected to the merge node.
        """
        link_ls = []
        for linkno in dic_node["linkno"]:
            link_data = LinkData()
            dic_link = self.combine_link(linkno, detail_df.df_all["oneway"], detail_df.df_all["enterexit"], detail_df.df_all["maxspeed"])

            link_data.meshcode = dic_link["meshcode"]
            link_data.linkno = dic_link["linkno"]
            link_data.snodeno = dic_link["snodeno"]
            link_data.enodeno = dic_link["enodeno"]
            link_data.lanecnt = dic_link["lanecnt"]
            link_data.maxspeed = dic_link["maxspeed"]
            link_ls.append(link_data)

        return link_ls

    def _calculate_merge_environment(self, node_data):
        """
        Calculate merge environment attributes (gradient and curvature).
        """
        # Calculate road gradient
        link_index = node_data.merge_direction
        link = node_data.obj_link_data_list[link_index]

        if len(link.center) > 50:
            vertical_distance = link.center[-1]["elevation"] - link.center[-50]["elevation"]
            horizontal_distance = math.sqrt((link.center[-1]["x"] - link.center[-50]["x"]) ** 2 + (link.center[-1]["y"] - link.center[-50]["y"]) ** 2)
            node_data.road_gradient = vertical_distance * 100 / horizontal_distance

        # Calculate road curvature
        extraction_range = 10
        point_for_fitting = 10
        xy_center_ls = copy.deepcopy(link.center)

        # Find point closest to origin
        dist_center = [(p["x"] ** 2 + p["y"] ** 2) for p in xy_center_ls]
        index_min = dist_center.index(min(dist_center))
        xy_center_ls = xy_center_ls[: index_min + 1]

        # Calculate curvature if enough points available
        if len(xy_center_ls) > 10:
            r_ls = []
            num_segments = min(extraction_range, int(len(xy_center_ls) / 10))

            for j in range(num_segments):
                x_in = [xy_center_ls[-(j * 10 + k) - 1]["x"] for k in range(point_for_fitting)]
                y_in = [xy_center_ls[-(j * 10 + k) - 1]["y"] for k in range(point_for_fitting)]
                r_optimized = ajust.fitting_circle(x_in, y_in)
                r_ls.append(r_optimized)

            node_data.curvature = r_ls

    def combine_node(self, df_junc, df_node, df_turnoff):
        """
        Extract and combine node data for merge sections.

        Args:
            df_junc: Junction node identifier
            df_node: DataFrame containing node coordinate data
            df_turnoff: DataFrame containing merge boundary data

        Returns:
            dict: Dictionary containing:
                - meshcode: Area identifier with 'Z' prefix
                - nodeno: Node number
                - lat: Latitude coordinate
                - lon: Longitude coordinate
                - linkno: List of connected link numbers
                - border: List of border coordinates
        """
        # Labels for turnoff border coordinates
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

        # Extract node numbers from NODE file for merge center point
        # (3 data points with different link numbers are extracted since nodes overlap at merge center)
        df_same_node = df_node[df_node["nodeno"] == df_junc].reset_index(drop=True)

        # Extract merge boundary line coordinates from TURNOFF_BORDER
        border_ls = []
        df_same_turnoff = df_turnoff[df_turnoff["nodeno"] == df_junc].reset_index(drop=True)

        # Extract link numbers from the extracted data
        linkno_ls = []
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

        # node_ls += [node_data]

        return dic_data

    def combine_link(self, linkno, df_oneway, df_enterexit, df_maxspeed):
        """
        Extract and process data for links connected to merge nodes.

        Args:
            linkno: Link identifier number
            df_oneway: DataFrame containing one-way road data
            df_enterexit: DataFrame containing merge/exit lane information

        Returns:
            dict: Dictionary containing:
                - meshcode: Area identifier
                - linkno: Link number
                - snodeno: Start node number
                - enodeno: End node number
                - lanecnt: Number of lanes
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

        if sum(df_enterexit["snodeno"] == link_snodeno) == 1:
            lanecnt = df_enterexit[df_enterexit["snodeno"] == link_snodeno]["slanecnt"].reset_index(drop=True)
            link_lanecnt = lanecnt[0]
        elif sum(df_enterexit["snodeno"] == link_snodeno) > 1:
            slinks = df_enterexit[df_enterexit["snodeno"] == link_snodeno]
            lanecnt = slinks[slinks["tnodeno"] == link_enodeno]["slanecnt"].reset_index(drop=True)
            link_lanecnt = lanecnt[0]

        elif sum(df_enterexit["tnodeno"] == link_snodeno) == 2:
            lanecnt = df_enterexit[df_enterexit["tnodeno"] == link_snodeno]["elanecnt"].reset_index(drop=True)
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
        Classify and process link connections at merge points.

        This method:
        1. Identifies post-merge mainline and gets JSON data
        2. Classifies remaining links as acceleration lane and pre-merge mainline
        3. Processes coordinates and attributes
        4. Determines merge direction

        Args:
            node_data: NodeData object containing merge point information
            link_ls: List of LinkData objects for connected links
            df_all: Dictionary of DataFrames containing road network data
            db_path: Path to database files
            operating_time: Time of operation

        Returns:
            tuple: (result, merge_direction) where:
                - result: List of processed LinkData objects [left, right, post-merge]
                - merge_direction: Integer indicating merge direction (0=left, 1=right)
        """
        # Step 1: Initialize containers and identify post-merge mainline
        determined_link, determined_json, uncateg = self._identify_post_merge(node_data, link_ls, db_path, df_all)

        # Step 2: Classify remaining links
        determined_link, determined_json = self._classify_remaining_links(uncateg, df_all["node"], df_all["enterexit"], determined_link, determined_json)

        # Step 3: Process coordinates and attributes
        determined_link = self._process_link_coordinates(determined_link, determined_json, node_data)

        # Step 4: Calculate merge direction and return result
        result, merge_direction = self._calculate_merge_direction(determined_link, node_data)

        return result, merge_direction

    def _identify_post_merge(self, node_data, link_ls, db_path, df_all):
        """
        Identify post-merge mainline and load JSON data.
        """
        determined_link = {"0": 0, "1": 0, "2": 0}
        determined_json = {"0": 0, "1": 0, "2": 0}
        uncateg = {"link": [], "json": []}

        # Load JSON data
        Itumo = ItsumoNaviData(db_path, self.junction_flag, node_data.meshcode, node_data.nodeno)
        Itumo.road_json(df_all)

        # Identify post-merge mainline from LinkData
        for i in range(len(link_ls)):
            if link_ls[i].snodeno == node_data.nodeno:
                determined_link["2"] = link_ls[i]
            else:
                uncateg["link"].append(link_ls[i])

        # Identify post-merge mainline from JSON data
        j_elatlon_ls = []
        for j_link in Itumo.json_data["item"][0]:
            j_elatlon_ls.append([j_link["link"]["line"][-2], j_link["link"]["line"][-1]])

        # Compare endpoints to identify post-merge mainline
        if j_elatlon_ls[0] == j_elatlon_ls[1]:
            determined_json["2"] = Itumo.json_data["item"][0][2]
            uncateg["json"].extend([Itumo.json_data["item"][0][0], Itumo.json_data["item"][0][1]])
        elif j_elatlon_ls[0] == j_elatlon_ls[2]:
            determined_json["2"] = Itumo.json_data["item"][0][1]
            uncateg["json"].extend([Itumo.json_data["item"][0][0], Itumo.json_data["item"][0][2]])
        else:
            determined_json["2"] = Itumo.json_data["item"][0][0]
            uncateg["json"].extend([Itumo.json_data["item"][0][1], Itumo.json_data["item"][0][2]])

        return determined_link, determined_json, uncateg

    def _classify_remaining_links(self, uncateg, df_node, df_enterexit, determined_link, determined_json):
        """
        Classify remaining links based on various criteria.
        """
        # Get start node coordinates
        snode = df_node[df_node["nodeno"] == uncateg["link"][0].snodeno].reset_index(drop=True)
        latlon_snode = [snode["y"][0], snode["x"][0]]

        # Calculate minimum distances to match links with JSON data
        dis_min = []
        for j_ls in uncateg["json"]:
            dis_ls = []
            for j_latlon in j_ls["link"]["adas"]["roadelevation"]:
                dis = vm.coord2XY(latlon_snode[0], latlon_snode[1], j_latlon["lat"], j_latlon["lon"])
                dis_ls.append(dis[2])
            dis_min.append(min(dis_ls))

        # Swap JSON data if needed based on distances
        if dis_min[0] > dis_min[1]:
            uncateg["json"] = [uncateg["json"][1], uncateg["json"][0]]

        # Calculate scores for classification
        score0, score1 = self._calculate_scores(uncateg, df_enterexit)

        # Assign links based on scores
        if score0 > score1:
            determined_link["0"], determined_json["0"] = uncateg["link"][1], uncateg["json"][1]
            determined_link["1"], determined_json["1"] = uncateg["link"][0], uncateg["json"][0]
        elif score0 < score1:
            determined_link["0"], determined_json["0"] = uncateg["link"][0], uncateg["json"][0]
            determined_link["1"], determined_json["1"] = uncateg["link"][1], uncateg["json"][1]
        else:
            determined_link["0"], determined_json["0"] = uncateg["link"][0], uncateg["json"][0]
            determined_link["1"], determined_json["1"] = uncateg["link"][1], uncateg["json"][1]

        return determined_link, determined_json

    def _calculate_scores(self, uncateg, df_enterexit):
        """
        Calculate scores for link classification based on lane count, position, and speed.
        """
        score0 = score1 = 0

        # Get lane information
        link0_enterexit = df_enterexit[(df_enterexit["snodeno"] == uncateg["link"][0].snodeno) & (df_enterexit["tnodeno"] == uncateg["link"][0].enodeno)].reset_index(drop=True)

        link1_enterexit = df_enterexit[(df_enterexit["snodeno"] == uncateg["link"][1].snodeno) & (df_enterexit["tnodeno"] == uncateg["link"][1].enodeno)].reset_index(drop=True)

        # Score based on lane count
        if uncateg["link"][0].lanecnt > uncateg["link"][1].lanecnt:
            score0 += 2
        elif uncateg["link"][0].lanecnt < uncateg["link"][1].lanecnt:
            score1 += 2

        # Score based on lane position matching
        elaneinfo = list(link0_enterexit["elaneinfo"][0])
        elane_index = np.where(np.array(elaneinfo) == "1")[0]
        slaneinfo0 = list(link0_enterexit["slaneinfo"][0])
        slaneinfo1 = list(link1_enterexit["slaneinfo"][0])

        index0 = np.where(np.array(slaneinfo0) == "1")[0]
        index1 = np.where(np.array(slaneinfo1) == "1")[0]

        lane_match0 = list(set(elane_index) & set(index0))
        lane_match1 = list(set(elane_index) & set(index1))

        # Update scores based on lane matching
        score0, score1 = self._update_lane_match_scores(score0, score1, elane_index, lane_match0, lane_match1)

        # Score based on speed limits
        score0, score1 = self._update_speed_scores(uncateg, score0, score1)

        return score0, score1

    def _update_lane_match_scores(self, score0, score1, elane_index, match0, match1):
        """
        Update scores based on lane position matching.
        """
        if len(elane_index) == len(match0):
            score0 += 3
        elif len(elane_index) > len(match0) and len(match0) != 0:
            score0 += 1

        if len(elane_index) == len(match1):
            score1 += 3
        elif len(elane_index) > len(match1) and len(match1) != 0:
            score1 += 1

        return score0, score1

    def _update_speed_scores(self, uncateg, score0, score1):
        """
        Update scores based on speed limits.
        """
        maxspeed0 = uncateg["json"][0]["link"]["adas"].get("maxspeedFront", [{"limit": 60}])[0]["limit"]
        maxspeed1 = uncateg["json"][1]["link"]["adas"].get("maxspeedFront", [{"limit": 60}])[0]["limit"]

        if maxspeed0 > maxspeed1:
            score0 += 1
        elif maxspeed0 < maxspeed1:
            score1 += 1

        return score0, score1

    def _calculate_merge_direction(self, determined_link, node_data):
        """
        Calculate merge direction based on vector cross product.
        """
        # Calculate vectors for merge point and connected links
        xy2 = vm.coord2XY(
            node_data.starting_point["lat"],
            node_data.starting_point["lon"],
            determined_link["2"].line[0],
            determined_link["2"].line[1],
        )

        xy0 = vm.coord2XY(
            node_data.starting_point["lat"],
            node_data.starting_point["lon"],
            determined_link["0"].line[-4],
            determined_link["0"].line[-3],
        )

        xy1 = vm.coord2XY(
            node_data.starting_point["lat"],
            node_data.starting_point["lon"],
            determined_link["1"].line[-4],
            determined_link["1"].line[-3],
        )

        # Calculate vectors and cross product
        vector_acceleration = [xy0[0] - xy2[0], xy0[1] - xy2[1]]
        vector_main = [xy1[0] - xy2[0], xy1[1] - xy2[1]]

        cross_product = vector_acceleration[0] * vector_main[1] - vector_acceleration[1] * vector_main[0]

        # Determine merge direction based on cross product
        if cross_product > 0:
            merge_direction = 0
            result = [determined_link["0"], determined_link["1"], determined_link["2"]]
        elif cross_product < 0:
            merge_direction = 1
            result = [determined_link["1"], determined_link["0"], determined_link["2"]]
        else:
            merge_direction = 0
            result = [determined_link["0"], determined_link["1"], determined_link["2"]]
            self.error_log.append(f"{self.meshcode}_{node_data.nodeno} : Cross product is zero")

        return result, merge_direction

    def extract_road_center(self, xyzdist_ls, nodeno, num):
        """
        Process and correct road center point coordinates.

        This method:
        1. Culls excess points using specified spacing
        2. Applies B-spline smoothing for point groups > 3 points
        3. Handles interpolation for shorter segments

        Args:
            xyzdist_ls: List of [x,y,z,distance] coordinates
            nodeno: Node identifier number
            num: Link index number

        Returns:
            tuple: (x_adjusted, y_adjusted, z_adjusted) containing processed coordinates
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

    def border_correction(self, node_data, border_node):
        """
        Process and correct merge boundary line coordinates.

        This method:
        1. Converts boundary coordinates to XY system
        2. Generates evenly spaced points along boundary
        3. Calculates and assigns elevation values
        4. Computes cubic polynomial parameters for OpenDrive format

        Args:
            node_data (object): NodeData object containing merge information
            border_node: List of border node coordinates

        Returns:
            tuple: (border_coordinate, border_length) where:
                - border_coordinate: List of processed boundary points with elevation
                - border_length: Total length of the merge boundary line
        """
        link_ls = node_data.obj_link_data_list
        merge_direction = node_data.merge_direction
        # TURNOFF_BORDERの道路中心点をxy座標に変換
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

        # 合流境界線を補正、1 m 間隔で点群を生成
        if len(x_border_ls) > 1:
            ops_border = ajust.fitting_border(x_border_ls, y_border_ls)
            for j in range(len(ops_border[0])):
                xy_border += [[ops_border[0][j], ops_border[1][j]]]
        else:
            for j in range(len(x_border_ls)):
                xy_border += [[x_border_ls[j], y_border_ls[j]]]

        # 各合流境界線のノードについて最も近い合流前本線ノードの標高を付与
        xyz_border = []
        if merge_direction == 0:
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

        elif merge_direction == 1:
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

        # OpenDrive化時に用いる、z方向の三次多項式近似のパラメータを求める
        border_coordinate = []
        for j in range(len(xyz_border)):
            x_ls, y_ls, z_ls = [], [], []
            # border属性に入れる辞書型を定義
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

            # 合流境界線の末端以外
            if j > 0 and len(xyz_border) - 2 > j:
                for k in range(4):
                    x_ls += [xyz_border[j - 1 + k][0]]
                    y_ls += [xyz_border[j - 1 + k][1]]
                    z_ls += [xyz_border[j - 1 + k][2]]
                s_position = 1
            # 合流境界線の始点
            elif j == 0:
                for k in range(4):
                    x_ls += [xyz_border[j + k][0]]
                    y_ls += [xyz_border[j + k][1]]
                    z_ls += [xyz_border[j + k][2]]
                s_position = 0
            # 合流境界線の終点の前
            elif j == len(xyz_border) - 2:
                for k in range(4):
                    x_ls += [xyz_border[j - 4 + k][0]]
                    y_ls += [xyz_border[j - 4 + k][1]]
                    z_ls += [xyz_border[j - 4 + k][2]]
                s_position = 2
            # 合流境界線の終点
            elif j == len(xyz_border) - 1:
                for k in range(4):
                    x_ls += [xyz_border[j - 4 + k][0]]
                    y_ls += [xyz_border[j - 4 + k][1]]
                    z_ls += [xyz_border[j - 4 + k][2]]
                s_position = 3

            # 合流境界線ノードが3点以上の場合は多項式近似が可能
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

        # 合流境界線の長さを計算。各点群の間隔を合計する
        dis = 0
        for j in range(len(border_coordinate) - 1):
            xyz_0 = border_coordinate[j]
            xyz_1 = border_coordinate[j + 1]
            dis_one = math.sqrt((xyz_1["x"] - xyz_0["x"]) ** 2 + (xyz_1["y"] - xyz_0["y"]) ** 2 + (xyz_1["elevation"] - xyz_0["elevation"]) ** 2)
            dis = dis + dis_one
        border_length = dis

        return border_coordinate, border_length

    def _process_link_coordinates(self, determined_link, determined_json, node_data):
        """
        Process coordinates and attributes for each link.

        This method:
        1. Updates road elevation points
        2. Converts coordinates to XY system
        3. Calculates elevation parameters
        4. Sets link attributes (maxspeed, road name, etc.)

        Args:
            determined_link: Dictionary of classified LinkData objects
            determined_json: Dictionary of corresponding JSON data
            node_data: NodeData object containing merge information

        Returns:
            dict: Updated determined_link with processed coordinates and attributes
        """
        for i in range(len(determined_link)):
            # Update endpoint coordinates
            determined_json[str(i)]["link"]["adas"]["roadelevation"][0]["lat"] = determined_json[str(i)]["link"]["line"][0]
            determined_json[str(i)]["link"]["adas"]["roadelevation"][0]["lon"] = determined_json[str(i)]["link"]["line"][1]
            determined_json[str(i)]["link"]["adas"]["roadelevation"][-1]["lat"] = determined_json[str(i)]["link"]["line"][-2]
            determined_json[str(i)]["link"]["adas"]["roadelevation"][-1]["lon"] = determined_json[str(i)]["link"]["line"][-1]

            # Extract coordinates
            lon, lat, elevation = [], [], []
            xyzdist_ls = []
            for lonlat_json in determined_json[str(i)]["link"]["adas"]["roadelevation"]:
                lat.append(lonlat_json["lat"])
                lon.append(lonlat_json["lon"])
                elevation.append(lonlat_json["elevation"])

            # Process coordinates based on link type
            if i < 2:  # For acceleration lane and pre-merge mainline
                xyzdist_ls = self._process_regular_link_coordinates(lat, lon, elevation, node_data)
            else:  # For post-merge mainline
                xyzdist_ls = self._process_post_merge_coordinates(lat, lon, elevation, node_data, determined_json)

            # Process road center points and calculate elevation parameters
            road_center_x, road_center_y, road_center_z = self.extract_road_center(xyzdist_ls, node_data.nodeno, i)

            # Create road center point list with coordinates
            road_center_xyz = [[road_center_x[j], road_center_y[j], road_center_z[j]] for j in range(len(road_center_x))]

            # Calculate elevation parameters for each point
            determined_link[str(i)].center = self._calculate_elevation_parameters(road_center_x, road_center_y, road_center_z, road_center_xyz)

            # Set link attributes
            if determined_link[str(i)].maxspeed is None:
                route_extractor = RouteExtract()
                determined_link[str(i)].maxspeed = route_extractor._get_maxspeed(determined_json[str(i)])
            determined_link[str(i)].road_name = determined_json[str(i)]["link"]["generalRoadName1"]
            determined_link[str(i)].line = determined_json[str(i)]["link"]["line"]
            determined_link[str(i)].roadelevation = determined_json[str(i)]["link"]["adas"]["roadelevation"]

        return determined_link

    def _process_regular_link_coordinates(self, lat, lon, elevation, node_data):
        """
        Process coordinates for acceleration lane and pre-merge mainline.
        """
        xyzdist_ls = []
        for j in range(len(lon)):
            xy = vm.coord2XY(
                node_data.starting_point["lat"],
                node_data.starting_point["lon"],
                lat[j],
                lon[j],
            )

            if j == 0:
                dist = vm.coord2XY(lat[j], lon[j], lat[j], lon[j])
            else:
                dist = vm.coord2XY(lat[j - 1], lon[j - 1], lat[j], lon[j])

            xyzdist_ls.append([xy[0], xy[1], elevation[j], dist[2]])

        return xyzdist_ls

    def _process_post_merge_coordinates(self, lat, lon, elevation, node_data, determined_json):
        """
        Process coordinates for post-merge mainline.
        """
        xyzdist_ls = []

        # Use pre-merge mainline endpoint as starting point
        before_merge_lat = determined_json["1"]["link"]["adas"]["roadelevation"][-1]["lat"]
        before_merge_lon = determined_json["1"]["link"]["adas"]["roadelevation"][-1]["lon"]
        before_merge_elev = determined_json["1"]["link"]["adas"]["roadelevation"][-1]["elevation"]

        # Add starting point
        xy = vm.coord2XY(
            node_data.starting_point["lat"],
            node_data.starting_point["lon"],
            before_merge_lat,
            before_merge_lon,
        )
        xyzdist_ls.append([xy[0], xy[1], before_merge_elev, 0])

        # Process remaining points
        for j in range(len(lon)):
            xy = vm.coord2XY(
                node_data.starting_point["lat"],
                node_data.starting_point["lon"],
                lat[j],
                lon[j],
            )

            if j == 0:
                dist = vm.coord2XY(before_merge_lat, before_merge_lon, lat[j], lon[j])
            else:
                dist = vm.coord2XY(lat[j - 1], lon[j - 1], lat[j], lon[j])

            xyzdist_ls.append([xy[0], xy[1], elevation[j], dist[2]])

        return xyzdist_ls

    def _calculate_elevation_parameters(self, road_center_x, road_center_y, road_center_z, road_center_xyz):
        """
        Calculate elevation parameters for each point using cubic polynomial fitting.
        """
        center_points = []

        for j in range(len(road_center_xyz)):
            dic_latlonelev = {
                "x": 0,
                "y": 0,
                "elevation": 0,
                "elev_param": {"s": 0, "a": 0, "b": 0, "c": 0, "d": 0},
            }

            if j > 0 and len(road_center_xyz) - 2 > j:
                x_ls = road_center_x[j - 1: j + 3]
                y_ls = road_center_y[j - 1: j + 3]
                z_ls = road_center_z[j - 1: j + 3]
                s_position = 1
            elif j == 0:
                x_ls = road_center_x[j: j + 4]
                y_ls = road_center_y[j: j + 4]
                z_ls = road_center_z[j: j + 4]
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
                optimized_elev_param, optimized_elev_param_s = ajust.fitting_3D_elev(x_ls, y_ls, z_ls, s_position)
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

            center_points.append(dic_latlonelev)

        return center_points
