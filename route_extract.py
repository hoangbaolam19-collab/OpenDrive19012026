import glob
import numpy as np
from tqdm import tqdm

from route_data import RouteData
from itsumo_navi import ItsumoNaviData
from submodule import vincenty_method as vm
from submodule import ajust


class RouteExtract:
    def __init__(self, path=r""):
        """
        Initialize the RouteExtract class.

        Parameters:
        path (str): The path to the directory containing route data.
        """
        self.line_ls = []
        self.mainlane_ls = []
        self.mainlane_combine_ls = []
        self.error_log = []
        self.path = path

    def make_route_extract(self, operating_time, latlon, highway_only):
        """
        Extract and objectify main lanes from route data.

        Parameters:
        operating_time (str): The operating time for route extraction.
        latlon (tuple): Latitude and longitude of the starting point.
        highway_only (bool): Flag to determine if only highways should be considered.
        """
        starting_point = self._initialize_starting_point(latlon)

        self.line_ls = self.determine_line(self.path, latlon, highway_only)
        self._populate_mainlane_list(self.path, operating_time, starting_point)
        self._remove_empty_mainlanes()
        self._combine_consecutive_road_segments()

    def _initialize_starting_point(self, latlon):
        """
        Initialize the starting point with latitude and longitude.

        Parameters:
        latlon (tuple): Latitude and longitude.

        Returns:
        dict: A dictionary with 'lat' and 'lon' keys.
        """
        return {"lat": latlon[0], "lon": latlon[1]}

    def _populate_mainlane_list(self, db_path, operating_time, starting_point):
        """
        Populate the main lane list with route data.

        Parameters:
        db_path (str): The path to the database file.
        operating_time (str): The operating time for route extraction.
        starting_point (dict): The starting point with latitude and longitude.
        """
        for line in tqdm(self.line_ls):
            latlon_start = [line[0], line[1]]
            link = self.determine_link(line, db_path, operating_time, latlon_start, starting_point)
            if link is not None:
                self.mainlane_ls.append(link)

    def _remove_empty_mainlanes(self):
        """
        Remove empty entries from the main lane list.
        """
        self.mainlane_ls = [lane for lane in self.mainlane_ls if lane is not None]

    def _combine_consecutive_road_segments(self):
        """
        Combine consecutive road segments into a single list.
        """
        mainlane_ls_index = self._get_mainlane_indices()
        for i in range(len(mainlane_ls_index)):
            start_idx = mainlane_ls_index[i]
            end_idx = mainlane_ls_index[i + 1] if i < len(mainlane_ls_index) - 1 else len(self.mainlane_ls)
            self.mainlane_combine_ls.append(self.mainlane_ls[start_idx:end_idx])

    def _get_mainlane_indices(self):
        """
        Get indices of main lanes that are not consecutive.

        Returns:
        list: A list of indices where main lanes are not consecutive.
        """
        indices = [0]
        for i in range(1, len(self.mainlane_ls)):
            if not self._are_segments_consecutive(self.mainlane_ls[i - 1], self.mainlane_ls[i]):
                indices.append(i)
        return indices

    def _are_segments_consecutive(self, prev_segment, current_segment):
        """
        Check if two segments are consecutive.

        Parameters:
        prev_segment (object): The previous road segment.
        current_segment (object): The current road segment.

        Returns:
        bool: True if segments are consecutive, False otherwise.
        """
        return [
            round(current_segment.line[0], 6),
            round(current_segment.line[1], 6),
        ] == [
            round(prev_segment.line[-2], 6),
            round(prev_segment.line[-1], 6),
        ]

    def determine_link(self, line, db_path, operating_time, latlon, starting_point):
        """
        Find road elevation data from the selected route's "line" data.

        Parameters:
        line (list): The line data for the route.
        db_path (str): The path to the database file.
        operating_time (str): The operating time for route extraction.
        latlon (list): Latitude and longitude of the starting point.
        starting_point (dict): The starting point with latitude and longitude.

        Returns:
        RouteData: An object containing route data.
        """
        Itsumo = ItsumoNaviData(db_path)
        Itsumo.road_json_final(latlon, line)

        if Itsumo.json_data == 0:
            return

        determined_json = Itsumo.json_data
        determined_link = RouteData()

        self._set_roadelevation_coordinates(determined_json)
        xyzdist_ls = self._calculate_xyzdist(determined_json, starting_point)

        road_center_x, road_center_y, road_center_z = self.extract_road_center(xyzdist_ls)
        road_center_xyz = list(zip(road_center_x, road_center_y, road_center_z))

        self._set_elevation_parameters(road_center_x, road_center_y, road_center_z, road_center_xyz, determined_link)

        determined_link.maxspeed = self._get_maxspeed(determined_json)
        determined_link.road_name = determined_json["link"]["generalRoadName1"]
        determined_link.link_code = determined_json["link"]["code"]
        determined_link.line = determined_json["link"]["line"]
        determined_link.roadelevation = determined_json["link"]["adas"]["roadelevation"]
        determined_link.closest = {
            "lat": determined_json["link"]["line"][-2],
            "lon": determined_json["link"]["line"][-1]
        }

        return determined_link

    def _set_roadelevation_coordinates(self, determined_json):
        """Set the start and end coordinates for road elevation."""
        determined_json["link"]["adas"]["roadelevation"][0]["lat"] = determined_json["link"]["line"][0]
        determined_json["link"]["adas"]["roadelevation"][0]["lon"] = determined_json["link"]["line"][1]
        determined_json["link"]["adas"]["roadelevation"][-1]["lat"] = determined_json["link"]["line"][-2]
        determined_json["link"]["adas"]["roadelevation"][-1]["lon"] = determined_json["link"]["line"][-1]

    def _calculate_xyzdist(self, determined_json, starting_point):
        """Calculate the xyz distance list from the determined JSON data."""
        lon, lat, elevation = zip(*[
            (lonlat_json["lon"], lonlat_json["lat"], lonlat_json["elevation"])
            for lonlat_json in determined_json["link"]["adas"]["roadelevation"]
        ])

        xyzdist_ls = []
        for j in range(len(lon)):
            xy = vm.coord2XY(starting_point["lat"], starting_point["lon"], lat[j], lon[j])
            dist = vm.coord2XY(lat[j - 1], lon[j - 1], lat[j], lon[j]) if j > 0 else vm.coord2XY(lat[j], lon[j], lat[j], lon[j])
            xyzdist_ls.append([xy[0], xy[1], elevation[j], dist[2]])

        return xyzdist_ls

    def _set_elevation_parameters(self, road_center_x, road_center_y, road_center_z, road_center_xyz, determined_link):
        """Set the elevation parameters for the determined link."""
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

            determined_link.center.append(dic_latlonelev)

    def _get_maxspeed(self, determined_json):
        """Get the maximum speed from the determined JSON data."""
        maxspeed_data = determined_json.get("link", {}).get("adas", {}).get("maxspeedFront")
        roadType_code = determined_json.get("link", {}).get("roadType", {}).get("code")

        if roadType_code in ["0", "1"]:
            if isinstance(maxspeed_data, list) and maxspeed_data and "limit" in maxspeed_data[0]:
                return maxspeed_data[0]["limit"]
            else:
                return -100
        else:
            if isinstance(maxspeed_data, list) and maxspeed_data and "limit" in maxspeed_data[0]:
                return maxspeed_data[0]["limit"]
            else:
                return -60

    def extract_road_center(self, xyzdist_ls):
        """
        Extract the road center coordinates using B-spline fitting.

        Parameters:
        xyzdist_ls (list): A list of coordinates and distances.

        Returns:
        tuple: Adjusted x, y, and z coordinates.
        """
        span = 20
        if len(xyzdist_ls) > 5:
            cull_xyzdist = ajust.input_match(xyzdist_ls, span)
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

        # for cases 14214, 14258, 2120, 13443.
        # Initially len(xyzdist_ls) > 5 but after using the ajust.input_match(xyzdist_ls,span) function len(cull_xyzdist) <= 3.
        # resulting in a score of less than 3. less than the number of points from the input data xyzdist_ls.
        # so ignore function ajust.input_match
        elif len(xyzdist_ls) > 3 and len(cull_xyzdist) <= 3:
            cull_xyzdist = xyzdist_ls
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
            for i in range(len(cull_xyzdist)):
                x_ajusted += [cull_xyzdist[i][0]]
                y_ajusted += [cull_xyzdist[i][1]]
                z_ajusted += [cull_xyzdist[i][2] / 1000]

        return x_ajusted, y_ajusted, z_ajusted

    def determine_line(self, db_path, latlon, highway_only):
        """
        Identify selected route data from ItsumoNAVIAPI.

        Parameters:
        db_path (str): The path to the database file.
        latlon (tuple): Latitude and longitude of the starting point.
        operating_time (str): The operating time for route extraction.
        highway_only (bool): Flag to determine if only highways should be considered.

        Returns:
        list: A list of line data for the selected route.
        """
        determine_line_all_raw, determine_line_all, distance_line = [], [], []

        for k in range(5):
            Itumo = ItsumoNaviData(db_path)
            Itumo.route_json(latlon, k)

            links = Itumo.json_data["route"]["link"]
            determined_line_raw = [link["line"]["latlon"] for link in links]

            # Filter out non-highway roads
            links = [link for link in links if link["roadType"] in ["都市高速道路", "高速道路"]]

            if not links:
                determine_line_all_raw.append(determined_line_raw)
                continue

            determined_line = [link["line"]["latlon"] for link in links]
            distance_line_sum = sum(link["distance"] for link in links)

            determine_line_all_raw.append(determined_line_raw)
            determine_line_all.append(determined_line)
            distance_line.append(distance_line_sum)

        if not distance_line:
            max_index = 0
            if highway_only:
                error_msg = ("highway_only is enabled, but the specified route does not include any highways, so the road model cannot be generated.")
                raise ValueError(error_msg)
            return determine_line_all_raw[max_index]
        else:
            max_index = distance_line.index(max(distance_line))
            return determine_line_all[max_index] if highway_only else determine_line_all_raw[max_index]
