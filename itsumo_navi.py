import json
import os
import shutil

from submodule import oauth_call_func
from submodule import vincenty_method as vm


class ItsumoNaviData:
    def __init__(self, path, flag=3, meshcode=0, nodeno=0):
        """
        Initialize the ItsumoNaviData class.

        Parameters:
        path (str): The path to the directory containing JSON data.
        flag (int): The type of data to process (0: confluence, 1: diversion, 2: mainlane, 3: route).
        meshcode (int): The mesh code for the data.
        nodeno (int): The node number for the data.
        """
        self.path = path
        self.meshcode = meshcode
        self.nodeno = nodeno
        self.json_data = 0
        if flag == 0:
            self.flag = "confluence"
        elif flag == 1:
            self.flag = "diversion"
        elif flag == 2:
            self.flag = "mainlane"
        elif flag == 3:
            self.flag = "route"

    def road_json(self, df_all):
        """
        Load and process the saved JSON file for road data.

        Parameters:
        df_all (DataFrame): DataFrame containing all node data.
        """
        # Load saved JSON file
        if os.path.isfile(self.path + r"\JSON\\" + self.flag + "\\" + self.meshcode + "_" + str(self.nodeno) + "_" + self.flag + ".json"):
            file = open(self.path + r"\JSON\\" + self.flag + "\\" + self.meshcode + "_" + str(self.nodeno) + "_" + self.flag + ".json")
            json_str = json.load(file)
            file.close()

            if len(json_str["item"][0]) > 3 and self.flag != "mainlane":
                df_node = df_all["node"]
                node_data = df_node[df_node["nodeno"] == self.nodeno].reset_index(drop=True)
                if self.flag == "diversion":
                    self.extract_branch_json(node_data)
                else:
                    self.extract_merge_json(node_data)

                file = open(self.path + r"\JSON\\" + self.flag + "\\" + self.meshcode + "_" + str(self.nodeno) + "_" + self.flag + ".json")
                json_str = json.load(file)
                file.close()

            elif len(json_str["item"][0]) < 3 and self.flag != "mainlane":
                df_node = df_all["node"]
                node_data = df_node[df_node["nodeno"] == self.nodeno].reset_index(drop=True)

                self.get_json_file(node_data)

                file = open(self.path + r"\JSON\\" + self.flag + "\\" + self.meshcode + "_" + str(self.nodeno) + "_" + self.flag + ".json")
                json_str = json.load(file)
                file.close()

            elif len(json_str["item"][0]) > 2 and self.flag == "mainlane":
                df_node = df_all["node"]
                node_data = df_node[df_node["nodeno"] == self.nodeno].reset_index(drop=True)
                self.extract_mainlane_json(node_data)

            elif len(json_str["item"][0]) < 2 and self.flag == "mainlane":
                df_node = df_all["node"]
                node_data = df_node[df_node["nodeno"] == self.nodeno].reset_index(drop=True)

                self.get_json_file(node_data)

                file = open(self.path + r"\JSON\\" + self.flag + "\\" + self.meshcode + "_" + str(self.nodeno) + "_" + self.flag + ".json")
                json_str = json.load(file)
                file.close()

            self.json_data = json_str

        else:
            df_node = df_all["node"]
            node_data = df_node[df_node["nodeno"] == self.nodeno].reset_index(drop=True)

            self.get_json_file(node_data)

            file = open(self.path + r"\JSON\\" + self.flag + "\\" + self.meshcode + "_" + str(self.nodeno) + "_" + self.flag + ".json")
            json_str = json.load(file)
            self.json_data = json_str
            file.close()

    def get_json_file(self, node_data):
        """
        Generate a JSON file from latitude and longitude data.

        Parameters:
        node_data (DataFrame): DataFrame containing node data for a specific node.
        """
        search_point_str = [str(n) for n in [node_data["y"][0], node_data["x"][0]]]
        search_point = ",".join(search_point_str)
        json_text = oauth_call_func.drive_route_multi(search_point)
        # temp = repr(node_data["y"][0]) + "," + repr(node_data["x"][0])
        # json_text = oauth_call_func.drive_route_multi(temp[:-1])
        if not os.path.isdir(self.path + r"\JSON\\preparation"):
            os.mkdir(self.path + r"\JSON\\preparation")

        if not os.path.isdir(self.path + r"\JSON\\" + self.flag):
            os.makedirs(self.path + r"\JSON\\" + self.flag, exist_ok=True)

        with open(
            self.path + r"\JSON\\" + self.flag + r"\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(json_text, f)

        file = open(self.path + r"\JSON\\" + self.flag + r"\Z" + node_data["meshcode"][0] + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json")

        a = json.load(file)
        b = json.loads(a)

        file.close()

        with open(
            self.path + r"\JSON\\" + self.flag + r"\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(b, f)

        if len(b["item"][0]) != 3 and self.flag != "mainlane":
            shutil.copy2(
                self.path + r"\JSON\\" + self.flag + r"\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
                self.path + r"\JSON\preparation\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
            )
            if self.flag == "diversion":
                self.extract_branch_json(node_data)
            else:
                self.extract_merge_json(node_data)

        elif self.flag == "mainlane":
            shutil.copy2(
                self.path + r"\JSON\\" + self.flag + r"\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
                self.path + r"\JSON\preparation\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
            )
            self.extract_mainlane_json(node_data)

    def extract_mainlane_json(self, node_data):
        """
        Extract main lane JSON data.

        Parameters:
        node_data (DataFrame): DataFrame containing node data for a specific node.
        """
        file = open(self.path + r"\JSON\preparation\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json")

        json_data = json.load(file)
        file.close()

        for i in range(len(json_data["item"][0]) - 1, -1, -1):
            if json_data["item"][0][i]["link"]["roadType"]["code"] != "1" and json_data["item"][0][i]["link"]["roadType"]["code"] != "0":
                json_data["item"][0].pop(i)

        with open(
            self.path + r"\JSON\preparation\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(json_data, f)

        center_latlon_ls = []
        mainlane_link_index_ls = []
        for j in range(len(json_data["item"][0])):
            point = 0
            link_index_ls = [j]
            for k in range(len(json_data["item"][0])):
                if j == k:
                    continue
                if [
                    json_data["item"][0][j]["link"]["line"][-2],
                    json_data["item"][0][j]["link"]["line"][-1],
                ] == [
                    json_data["item"][0][k]["link"]["line"][0],
                    json_data["item"][0][k]["link"]["line"][1],
                ]:
                    point += 1
                    link_index_ls += [k]

            if point == 1:
                center_latlon_ls += [
                    [
                        json_data["item"][0][j]["link"]["line"][-2],
                        json_data["item"][0][j]["link"]["line"][-1],
                    ]
                ]
                mainlane_link_index_ls += [link_index_ls]

        if len(center_latlon_ls) >= 2:
            mainlane_json_data = {"item": [[]]}
            center_lat = node_data["y"][0]
            center_lon = node_data["x"][0]

            # plt.plot(center_lat, center_lon, marker="o", label='center - ' + str(node_data["nodeno"][0])  )

            dist_ls = []
            for j in range(len(center_latlon_ls)):
                dist_ls += [
                    vm.coord2XY(
                        center_lat,
                        center_lon,
                        center_latlon_ls[j][0],
                        center_latlon_ls[j][1],
                    )[2]
                ]

            min_index = dist_ls.index(min(dist_ls))

            for j in range(len(mainlane_link_index_ls[0])):
                mainlane_json_data["item"][0] += [json_data["item"][0][mainlane_link_index_ls[min_index][j]]]

            x_list1 = []
            y_list1 = []
            for i in range(len(json_data["item"][0][mainlane_link_index_ls[min_index][0]]["link"]["adas"]["roadelevation"])):
                x_center = json_data["item"][0][mainlane_link_index_ls[min_index][0]]["link"]["adas"]["roadelevation"][i]["lat"]
                y_center = json_data["item"][0][mainlane_link_index_ls[min_index][0]]["link"]["adas"]["roadelevation"][i]["lon"]
                x_list1.append(x_center)
                y_list1.append(y_center)

            x_list2 = []
            y_list2 = []
            for i in range(len(json_data["item"][0][mainlane_link_index_ls[min_index][1]]["link"]["adas"]["roadelevation"])):
                x_center = json_data["item"][0][mainlane_link_index_ls[min_index][1]]["link"]["adas"]["roadelevation"][i]["lat"]
                y_center = json_data["item"][0][mainlane_link_index_ls[min_index][1]]["link"]["adas"]["roadelevation"][i]["lon"]
                x_list2.append(x_center)
                y_list2.append(y_center)

            # plt.plot(x_list1, y_list1, marker="+", label='0-'+ str(mainlane_link_index_ls[min_index][0]))
            # plt.plot(x_list2, y_list2, marker="+", label='1-'+ str(mainlane_link_index_ls[min_index][1]))
            # plt.legend()

            for j in range(len(mainlane_link_index_ls)):
                x_list1 = []
                y_list1 = []
                for i in range(len(json_data["item"][0][mainlane_link_index_ls[j][0]]["link"]["adas"]["roadelevation"])):
                    x_center = json_data["item"][0][mainlane_link_index_ls[j][0]]["link"]["adas"]["roadelevation"][i]["lat"]
                    y_center = json_data["item"][0][mainlane_link_index_ls[j][0]]["link"]["adas"]["roadelevation"][i]["lon"]
                    x_list1.append(x_center)
                    y_list1.append(y_center)

                x_list2 = []
                y_list2 = []
                for i in range(len(json_data["item"][0][mainlane_link_index_ls[j][1]]["link"]["adas"]["roadelevation"])):
                    x_center = json_data["item"][0][mainlane_link_index_ls[j][1]]["link"]["adas"]["roadelevation"][i]["lat"]
                    y_center = json_data["item"][0][mainlane_link_index_ls[j][1]]["link"]["adas"]["roadelevation"][i]["lon"]
                    x_list2.append(x_center)
                    y_list2.append(y_center)

                # plt.plot(x_list1, y_list1, linestyle='--', label='0-'+ str(mainlane_link_index_ls[j][0]))
                # plt.plot(x_list2, y_list2, linestyle='--', label='1-'+ str(mainlane_link_index_ls[j][1]))
                # plt.legend()
                # plt.show()

        elif len(center_latlon_ls) == 1:
            mainlane_json_data = {"item": [[]]}
            for j in range(len(mainlane_link_index_ls[0])):
                mainlane_json_data["item"][0] += [json_data["item"][0][mainlane_link_index_ls[0][j]]]

        else:
            print("No data found. Nodeno = ", node_data["nodeno"][0])
            return

        with open(
            self.path + r"\JSON\\" + self.flag + r"\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(mainlane_json_data, f)

    def extract_branch_json(self, node_data):
        """
        Extract branch JSON data.

        Parameters:
        node_data (DataFrame): DataFrame containing node data for a specific node.
        """
        file = open(self.path + r"\JSON\preparation\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json")

        json_data = json.load(file)
        file.close()

        center_latlon_ls = []
        branch_link_index_ls = []
        for j in range(len(json_data["item"][0])):
            point = 0
            link_index_ls = [j]
            for k in range(len(json_data["item"][0])):
                if j == k:
                    continue
                if [
                    json_data["item"][0][j]["link"]["line"][-2],
                    json_data["item"][0][j]["link"]["line"][-1],
                ] == [
                    json_data["item"][0][k]["link"]["line"][0],
                    json_data["item"][0][k]["link"]["line"][1],
                ]:
                    point += 1
                    link_index_ls += [k]

                if point == 2:
                    point = 0
                    center_latlon_ls += [
                        [
                            json_data["item"][0][j]["link"]["line"][-2],
                            json_data["item"][0][j]["link"]["line"][-1],
                        ]
                    ]
                    branch_link_index_ls += [link_index_ls]

        if len(center_latlon_ls) >= 2:
            branch_json_data = {"item": [[]]}
            center_lat = node_data["y"][0]
            center_lon = node_data["x"][0]

            dist_ls = []
            for j in range(len(center_latlon_ls)):
                dist_ls += [
                    vm.coord2XY(
                        center_lat,
                        center_lon,
                        center_latlon_ls[j][0],
                        center_latlon_ls[j][1],
                    )[2]
                ]

            min_index = dist_ls.index(min(dist_ls))

            for j in range(len(branch_link_index_ls[min_index])):
                branch_json_data["item"][0] += [json_data["item"][0][branch_link_index_ls[min_index][j]]]

        else:
            branch_json_data = {"item": [[]]}
            for j in range(len(branch_link_index_ls[0])):
                branch_json_data["item"][0] += [json_data["item"][0][branch_link_index_ls[0][j]]]

        with open(
            self.path + r"\JSON\\" + self.flag + r"\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(branch_json_data, f)

    def extract_merge_json(self, node_data):
        """
        Extract merge JSON data.

        Parameters:
        node_data (DataFrame): DataFrame containing node data for a specific node.
        """
        file = open(self.path + r"\JSON\preparation\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json")

        json_data = json.load(file)
        file.close()

        center_latlon_ls = []
        merge_link_index_ls = []
        for j in range(len(json_data["item"][0])):
            point = 0
            link_index_ls = [j]
            for k in range(len(json_data["item"][0])):
                if j == k:
                    continue
                if [
                    json_data["item"][0][j]["link"]["line"][0],
                    json_data["item"][0][j]["link"]["line"][1],
                ] == [
                    json_data["item"][0][k]["link"]["line"][-2],
                    json_data["item"][0][k]["link"]["line"][-1],
                ]:
                    point += 1
                    link_index_ls += [k]

                if point == 2:
                    point = 0
                    center_latlon_ls += [
                        [
                            json_data["item"][0][j]["link"]["line"][0],
                            json_data["item"][0][j]["link"]["line"][1],
                        ]
                    ]
                    merge_link_index_ls += [link_index_ls]

        if len(center_latlon_ls) >= 2:
            merge_json_data = {"item": [[]]}
            center_lat = node_data["y"][0]
            center_lon = node_data["x"][0]

            dist_ls = []
            for j in range(len(center_latlon_ls)):
                dist_ls += [
                    vm.coord2XY(
                        center_lat,
                        center_lon,
                        center_latlon_ls[j][0],
                        center_latlon_ls[j][1],
                    )[2]
                ]

            min_index = dist_ls.index(min(dist_ls))

            for j in range(len(merge_link_index_ls[min_index])):
                merge_json_data["item"][0] += [json_data["item"][0][merge_link_index_ls[min_index][j]]]

        else:
            merge_json_data = {"item": [[]]}
            for j in range(len(merge_link_index_ls[0])):
                merge_json_data["item"][0] += [json_data["item"][0][merge_link_index_ls[0][j]]]

        with open(
            self.path + r"\JSON\\" + self.flag + r"\Z" + str(node_data["meshcode"][0]) + "_" + str(node_data["nodeno"][0]) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(merge_json_data, f)

    def route_json(self, latlon, type):
        """
        Load and process the saved JSON file for route data.

        Parameters:
        latlon (tuple): Tuple containing latitude and longitude.
        type (int): The type of route data.
        """
        if os.path.isfile(
            self.path + r"\JSON\\" + self.flag + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + str(latlon[2]) + "_" + str(latlon[3]) + "_" + str(type) + "_" + self.flag + ".json"
        ):
            file = open(self.path + r"\JSON\\" + self.flag + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + str(latlon[2]) + "_" + str(latlon[3]) + "_" + str(type) + "_" + self.flag + ".json")
            json_str = json.load(file)
            file.close()

            self.json_data = json_str

        else:
            self.get_route_json_file(latlon, type)

            file = open(self.path + r"\JSON\\" + self.flag + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + str(latlon[2]) + "_" + str(latlon[3]) + "_" + str(type) + "_" + self.flag + ".json")
            json_str = json.load(file)
            file.close()
            self.json_data = json_str

    def get_route_json_file(self, latlon, type):
        """
        Generate a route JSON file.

        Parameters:
        latlon (tuple): Tuple containing latitude and longitude.
        type (int): The type of route data.
        """
        json_text = oauth_call_func.drive_route3(latlon, type)

        if not os.path.isdir(self.path + r"\JSON\\" + self.flag):
            os.makedirs(self.path + r"\JSON\\" + self.flag, exist_ok=True)

        with open(
            self.path + r"\JSON\\" + self.flag + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + str(latlon[2]) + "_" + str(latlon[3]) + "_" + str(type) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(json_text, f)

        file = open(self.path + r"\JSON\\" + self.flag + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + str(latlon[2]) + "_" + str(latlon[3]) + "_" + str(type) + "_" + self.flag + ".json")

        a = json.load(file)
        b = json.loads(a)

        file.close()

        with open(
            self.path + r"\JSON\\" + self.flag + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + str(latlon[2]) + "_" + str(latlon[3]) + "_" + str(type) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(b, f)

    def road_json_final(self, latlon, line):
        """
        Load and process the final road JSON file.

        Parameters:
        latlon (tuple): Tuple containing latitude and longitude.
        line (list): List containing line data.
        """
        if os.path.isfile(
            self.path + r"\JSON\\" + self.flag + "_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
        ):
            file = open(
                self.path + r"\JSON\\" + self.flag + "_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
            )

            json_str = json.load(file)
            file.close()

            if "item" in json_str and len(json_str["item"][0]) > 1:
                json_str = 0
                print("No data roadelevation found. latlon = ", line[0],line[1],line[-2],line[-1])
            else:
                print("Data roadelevation found. latlon = ", line[0],line[1],line[-2],line[-1])
                # print(line[0],line[1],line[-2],line[-1])

            self.json_data = json_str

        else:
            self.get_json_file_final(latlon, line)

            file = open(
                self.path + r"\JSON\\" + self.flag + "_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
            )
            json_str = json.load(file)
            file.close()

            if "item" in json_str and len(json_str["item"][0]) > 1:
                json_str = 0

            self.json_data = json_str

    def get_json_file_final(self, latlon, line):
        """
        Generate the final JSON file from latitude and longitude.

        Parameters:
        latlon (tuple): Tuple containing latitude and longitude.
        line (list): List containing line data.
        """
        temp = repr(latlon[0]) + "," + repr(latlon[1])

        json_text = oauth_call_func.drive_route_multi(temp[:-1])

        if not os.path.isdir(self.path + r"\JSON\\preparation_new"):
            os.mkdir(self.path + r"\JSON\\preparation_new")

        if not os.path.isdir(self.path + r"\JSON\\" + self.flag + "_new"):
            os.mkdir(self.path + r"\JSON\\" + self.flag + "_new")

        with open(
            self.path + r"\JSON\\" + self.flag + "_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(json_text, f)

        file = open(
            self.path + r"\JSON\\" + self.flag + "_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
        )

        a = json.load(file)
        b = json.loads(a)

        file.close()

        with open(
            self.path + r"\JSON\\" + self.flag + "_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(b, f)

        shutil.copy2(
            self.path + r"\JSON\\" + self.flag + "_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
            self.path + r"\JSON\\preparation_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
        )
        self.extract_line_json_final(latlon, line)

    def extract_line_json_final(self, latlon, line):
        """
        Extract final line JSON data.

        Parameters:
        latlon (tuple): Tuple containing latitude and longitude.
        line (list): List containing line data.
        """
        file = open(
            self.path + r"\JSON\\preparation_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
        )

        json_data = json.load(file)
        file.close()

        mainlane_link_index_ls = []
        for j in range(len(json_data["item"][0])):
            if [
                round(json_data["item"][0][j]["link"]["line"][0], 6),
                round(json_data["item"][0][j]["link"]["line"][1], 6),
                round(json_data["item"][0][j]["link"]["line"][-2], 6),
                round(json_data["item"][0][j]["link"]["line"][-1], 6),
            ] == [
                round(line[0], 6),
                round(line[1], 6),
                round(line[-2], 6),
                round(line[-1], 6),
            ]:
                mainlane_link_index_ls += [j]

        if len(mainlane_link_index_ls) >= 1:
            self.json_data = json_data["item"][0][mainlane_link_index_ls[0]]
            print("Data roadelevation found. latlon = ", line[0],line[1],line[-2],line[-1])

        else:
            print("No data roadelevation found. latlon = ", line[0],line[1],line[-2],line[-1])
            return

        with open(
            self.path + r"\JSON\\" + self.flag + "_new" + "\\" + str(latlon[0]) + "_" + str(latlon[1]) + "_" + self.flag + ".json",
            "w",
        ) as f:
            json.dump(self.json_data, f)
