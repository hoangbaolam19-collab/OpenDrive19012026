import pandas as pd
from xml.etree.ElementTree import Element, SubElement, ElementTree
import datetime
from tqdm import tqdm

import math
import numpy as np
from submodule import curvature_culc_func as ccf
from submodule import ajust


class OpenDriveXml:
    def __init__(self):
        self.xodr_xml = []

    def make_mainlane_xml_combine(self, str_obj_list):
        # ヘッダの中身作成
        now = datetime.datetime(2022, 9, 22, 13, 37, 24, 613012)
        timestamp = (
            str(now.year)
            + "-"
            + str(now.month)
            + "-"
            + str(now.day)
            + "T"
            + str(now.hour)
            + ":"
            + str(now.minute)
            + ":"
            + str(now.second)
        )

        root = Element("OpenDRIVE")
        header = Element(
            "header",
            {
                "revMajor": "1",
                "revMinor": "6",
                "name": "test",
                "version": "1",
                "date": timestamp,
                "north": "2.5e+2",
                "south": "-2.5e+2",
                "east": "2.5e+2",
                "west": "-2.5e+2",
                "vendor": "Zenrin-Datacom",
            },
        )
        root.append(header)

        for l in range(len(str_obj_list)):
            df_polyline = str_obj_list[l].df_polyline
            df_lane_info = str_obj_list[l].df_lane_info

            road_num = len(df_polyline)

            road_id_num = df_lane_info["road_id"].iloc[-1] + 1
            # print("road_id_num = ", road_id_num)

            road_id = []
            for i in range(road_id_num):
                road_id.append(i)

            road = [""] * road_id_num
            link = [""] * road_id_num * 8
            predecessor_road = [""] * road_id_num * 8
            successor_road = [""] * road_id_num * 8
            predecessor_link = [""] * road_id_num * 8
            successor_link = [""] * road_id_num * 8
            type = [""] * road_id_num * 8
            speed = [""] * road_id_num
            planView = [""] * road_id_num
            elevationProfile = [""] * road_id_num
            lateralProfile = [""] * road_id_num
            superelevation = [""] * road_id_num
            lanes = [""] * road_id_num
            shape = [""] * road_id_num
            laneOffset = [""] * road_id_num
            laneSection = [""] * road_id_num
            lane_tag = [""] * road_id_num * 6
            lane = [""] * road_id_num * 7
            width = [""] * road_id_num * 7
            roadMark = [""] * road_id_num * 7
            speed = [""] * road_id_num * 7
            userData = [""] * road_id_num * 7
            vectorLane = [""] * road_id_num * 7
            geometry = [""] * road_num
            elevation = [""] * road_num
            line = [""] * road_num
            line_s = [""] * road_num
            arc = [""] * road_num
            spiral = [""] * road_num
            junction = [""] * 70
            connection = [""] * 70
            laneLink = [""] * 70

            ########
            # ここからRoad構築
            ########

            for i in road_id:
                # ここでは、該当のRoadIDのタイプを確認
                road_index = df_lane_info[df_lane_info["road_id"] == i].index[0]
                jnc_t = df_lane_info.iat[road_index, 1]
                road_length = format(
                    df_polyline[df_polyline["ID"] == i]["length"].sum(), ".8E"
                )
                # ここから作成
                road[i] = Element(
                    "road",
                    {
                        "name": "Road " + "0" + str(l) + str(i),
                        "length": road_length,
                        "id": "0" + str(l) + str(i),
                        "junction": str(jnc_t),
                    },
                )
                root.append(road[i])
                link[i] = SubElement(road[i], "link")
                type[i] = SubElement(
                    road[i], "type", {"s": "0.0e+0", "type": "town"}
                )
                planView[i] = SubElement(road[i], "planView")
                elevationProfile[i] = SubElement(road[i], "elevationProfile")
                lateralProfile[i] = SubElement(road[i], "lateralProfile")
                lanes[i] = SubElement(road[i], "lanes")
                speed[i] = SubElement(
                    type[i], "speed", {"max": "40", "unit": "km/h"}
                )
                superelevation[i] = SubElement(
                    lateralProfile[i],
                    "superelevation",
                    {"s": "0", "a": "0", "b": "0", "c": "0", "d": "0"},
                )
                shape[i] = SubElement(
                    lateralProfile[i],
                    "shape",
                    {
                        "s": "0",
                        "t": "0",
                        "a": "0",
                        "b": "0",
                        "c": "0",
                        "d": "0",
                    },
                )

            ########
            # リンクの接続
            ########

            successor_road[0] = SubElement(
                link[0],
                "successor",
                {
                    "elementType": "road",
                    "elementId": "0" + str(l) + "1",
                    "contactPoint": "start",
                },
            )

            if road_id_num > 2:
                for i in range(1, road_id_num - 1):
                    successor_road[i] = SubElement(
                        link[i],
                        "successor",
                        {
                            "elementType": "road",
                            "elementId": "0" + str(l) + str(i + 1),
                            "contactPoint": "start",
                        },
                    )
                    predecessor_road[i] = SubElement(
                        link[i],
                        "predecessor",
                        {
                            "elementType": "road",
                            "elementId": "0" + str(l) + str(i - 1),
                            "contactPoint": "end",
                        },
                    )

            predecessor_road[road_id_num - 1] = SubElement(
                link[road_id_num - 1],
                "predecessor",
                {
                    "elementType": "road",
                    "elementId": "0" + str(l) + str(road_id_num - 2),
                    "contactPoint": "end",
                },
            )

            ########
            # 繰り返し部分
            ########

            node_number = 0  # ノード位置の通し番号
            tag_number = 0  # レーン一の情報
            lane_number = 0  # レーンの通し番号
            link_number = 6  # レーンのリンクの通し番号

            for i in road_id:
                df_bool = df_polyline["ID"] == i
                idx = df_polyline[df_polyline["ID"] == i].index[0]
                s = 0
                iter = df_bool.sum()
                #
                for j in range(iter - 1):
                    if df_polyline["length"][idx] != "":
                        geometry[node_number] = SubElement(
                            planView[i],
                            "geometry",
                            {
                                "s": format(s, ".8E"),
                                "x": format(df_polyline["x"][idx], ".8E"),
                                "y": format(df_polyline["y"][idx], ".8E"),
                                "hdg": format(df_polyline["hdg"][idx], ".8E"),
                                "length": format(
                                    df_polyline["length"][idx], ".8E"
                                ),
                            },
                        )
                        # Roadの形状を判定して、入力内容を選定
                        if df_polyline["shape"][idx] == "spiral":
                            spiral[idx] = SubElement(
                                geometry[node_number],
                                "spiral",
                                {
                                    "curvStart": format(
                                        df_polyline["curvature"][idx], ".8E"
                                    ),
                                    "curvEnd": format(
                                        df_polyline["curvature"][idx + 1], ".8E"
                                    ),
                                },
                            )
                        elif df_polyline["shape"][idx] == "arc":
                            arc[idx] = SubElement(
                                geometry[node_number],
                                "arc",
                                {
                                    "curvature": format(
                                        df_polyline["curvature"][idx], ".8E"
                                    )
                                },
                            )
                        else:
                            line_s[idx] = SubElement(
                                geometry[node_number], "line"
                            )
                        # elevation[node_number] = SubElement(elevationProfile[i],"elevation",{"s":format(s,'.8E'),"a":"0","b":"0","c":"0","d":"0"})
                        elevation[node_number] = SubElement(
                            elevationProfile[i],
                            "elevation",
                            {
                                "s": format(s, ".8E"),
                                "a": format(df_polyline["elev_a"][idx], ".8E"),
                                "b": format(df_polyline["elev_b"][idx], ".8E"),
                                "c": format(df_polyline["elev_c"][idx], ".8E"),
                                "d": format(df_polyline["elev_d"][idx], ".8E"),
                            },
                        )
                    s = s + df_polyline["length"][idx]
                    idx = idx + 1
                    node_number = node_number + 1

            ########
            # レーンの部分
            ########

            for i in road_id:
                temp_tag = ""
                # テーブルからレーンの情報の位置を抽出
                idx = df_lane_info[df_lane_info["road_id"] == i].index[0]
                df_bool = df_lane_info["road_id"] == i
                iter = df_bool.sum()
                # まずはlaneOffsetとlaneSectionを定義

                laneOffset[i] = SubElement(
                    lanes[i],
                    "laneOffset",
                    {
                        "s": "0",
                        "a": str(df_lane_info["offset"][idx]),
                        "b": "0",
                        "c": "0",
                        "d": "0",
                    },
                )
                laneSection[i] = SubElement(
                    lanes[i], "laneSection", {"s": "0", "singleSide": "false"}
                )
                # ここからレーンのタグを作成
                for j in range(iter):
                    if temp_tag == df_lane_info["direction"][idx + j]:
                        None
                    else:
                        tag_number = tag_number + 1
                        temp_tag = df_lane_info["direction"][idx + j]
                        lane_tag[tag_number] = SubElement(
                            laneSection[i], df_lane_info["direction"][idx + j]
                        )
                    # ここからレーン内の詳細の記載
                    if temp_tag == "center":
                        lane[lane_number] = SubElement(
                            lane_tag[tag_number],
                            "lane",
                            {"id": "0", "type": "none", "level": "false"},
                        )
                    # センター以外の部分
                    else:
                        # print(len(link),link_number,len(lane),lane_number)
                        lane[lane_number] = SubElement(
                            lane_tag[tag_number],
                            "lane",
                            {
                                "id": str(df_lane_info["lane_id"][idx + j]),
                                "type": "driving",
                                "level": "false",
                            },
                        )
                        link[link_number] = SubElement(
                            lane[lane_number], "link"
                        )
                        # リンクの前後のレーンがあった時に反映
                        if df_lane_info["lane_predecessor"][idx + j] != "":
                            predecessor_link[link_number] = SubElement(
                                link[link_number],
                                "predecessor",
                                {
                                    "id": str(
                                        int(
                                            df_lane_info["lane_predecessor"][
                                                idx + j
                                            ]
                                        )
                                    )
                                },
                            )

                        if df_lane_info["lane_successor"][idx + j] != "":
                            successor_link[link_number] = SubElement(
                                link[link_number],
                                "successor",
                                {
                                    "id": str(
                                        int(
                                            df_lane_info["lane_successor"][
                                                idx + j
                                            ]
                                        )
                                    )
                                },
                            )
                        # 幅を設定

                        width[lane_number] = SubElement(
                            lane[lane_number],
                            "width",
                            {
                                "sOffset": "0",
                                "a": str(df_lane_info["lane_width"][idx + j]),
                                "b": "0",
                                "c": "0",
                                "d": "0",
                            },
                        )
                    # jのループが終わったので、tag_numberを更新
                    # jのループが終わったので、tag_numberを更新
                    # ここから共通部分
                    roadMark[lane_number] = SubElement(
                        lane[lane_number],
                        "roadMark",
                        {
                            "sOffset": "0",
                            "type": str(df_lane_info["type"][idx + j]),
                            "material": "standard",
                            "color": "white",
                            "width": "0.125",
                            "laneChange": str(
                                df_lane_info["lane_change"][idx + j]
                            ),
                        },
                    )
                    type[lane_number] = SubElement(
                        roadMark[lane_number],
                        "type",
                        {"name": str(df_lane_info["type"][idx + j])},
                    )
                    line[lane_number] = SubElement(
                        type[lane_number],
                        "line",
                        {
                            "length": "1.0e+1",
                            "space": "0.0e+0",
                            "width": "1.50e-1",
                            "sOffset": "0.0e+0",
                            "tOffset": "0.0e+0",
                        },
                    )
                    userData[lane_number] = SubElement(
                        lane[lane_number], "userData", {"code": "vectorLane"}
                    )
                    vectorLane[lane_number] = SubElement(
                        userData[lane_number],
                        "vectorLane",
                        {
                            "sOffset": "0.0000000000000000e+0",
                            "travelDir": "forward",
                        },
                    )
                    lane_number = lane_number + 1
                    link_number = link_number + 1

            ########
            # ジャンクションの部分
            ########

            tag_number = -1  # タグ番号
            tag_number_c = -1

            temp_tag = ""
            temp_tag_c = ""

        tree = ElementTree(root)

        self.indent(root)
        self.xodr_xml = tree
        # tree.write("openDRIVE_data.xodr", encoding="utf-8", xml_declaration=True)

    def make_route_xml(
        self, str_obj_mainlane_list, str_obj_branch_list, str_obj_merge_list, connect_merge_branch_list
    ):
        # ヘッダの中身作成
        now = datetime.datetime(2022, 9, 22, 13, 37, 24, 613012)
        timestamp = (
            str(now.year)
            + "-"
            + str(now.month)
            + "-"
            + str(now.day)
            + "T"
            + str(now.hour)
            + ":"
            + str(now.minute)
            + ":"
            + str(now.second)
        )

        root = Element("OpenDRIVE")
        header = Element(
            "header",
            {
                "revMajor": "1",
                "revMinor": "6",
                "name": "test",
                "version": "1",
                "date": timestamp,
                "north": "2.5e+2",
                "south": "-2.5e+2",
                "east": "2.5e+2",
                "west": "-2.5e+2",
                "vendor": "Zenrin-Datacom",
            },
        )
        root.append(header)

        print("Create branch xml data, branch ID will start with number 1.")
        for l in tqdm(range(len(str_obj_branch_list))):
            df_polyline = str_obj_branch_list[l].df_polyline
            df_junction = str_obj_branch_list[l].df_junction
            df_lane_info = str_obj_branch_list[l].df_lane_info

            df_polyline, df_junction, df_lane_info = change_branch_data(df_polyline, df_junction, df_lane_info)

            road_num = len(df_polyline)  # 道路を構成する中心点群ノードの数をカウント

            road_id = [0, 1, 2, 3, 4, 5, 6]

            road             = [""] * 7
            link             = [""] * 7 * 8
            predecessor_road = [""] * 7 * 8
            successor_road   = [""] * 7 * 8
            predecessor_link = [""] * 7 * 8
            successor_link   = [""] * 7 * 8
            type             = [""] * 7 * 8
            speed            = [""] * 7
            planView         = [""] * 7
            elevationProfile = [""] * 7
            lateralProfile   = [""] * 7
            superelevation   = [""] * 7
            lanes            = [""] * 7
            shape            = [""] * 7
            laneOffset       = [""] * 7
            laneSection      = [""] * 7
            lane_tag         = [""] * 7 * 7
            lane             = [""] * 7 * 8
            width            = [""] * 7 * 8
            roadMark         = [""] * 7 * 8
            speed            = [""] * 7 * 8
            userData         = [""] * 7 * 8
            vectorLane       = [""] * 7 * 8
            geometry         = [""] * road_num
            elevation        = [""] * road_num
            line             = [""] * road_num
            line_s           = [""] * road_num
            arc              = [""] * road_num
            spiral           = [""] * road_num
            junction         = [""] * 70
            connection       = [""] * 70
            laneLink         = [""] * 70

            ########
            # ここからRoad構築
            ########

            for i in road_id:
                # ここでは、該当のRoadIDのタイプを確認
                road_index = df_lane_info[df_lane_info["road_id"] == i].index[0]
                jnc_t = df_lane_info.iat[road_index, 1]
                # road_length = format(
                #     df_polyline[df_polyline["ID"] == i]["length"].sum(), ".8E"
                # )

                df_bool = df_polyline["ID"] == i
                idx     = df_polyline[df_polyline["ID"]  == i].index[0]
                s       = 0
                iter = df_bool.sum()
                for j in range(iter-1):
                    s = s + df_polyline["length"][idx]
                    idx = idx + 1
                road_length = format(s, ".8E")

                # ここから作成
                if i == 4 or i == 5:
                    road[i] = Element(
                        "road",
                        {
                            "name": "Road " + "1" + str(l) + str(i),
                            "length": road_length,
                            "id": "1" + str(l) + str(i),
                            "junction": "1" + str(l) + "7",
                        },
                    )
                else:
                    road[i] = Element(
                        "road",
                        {
                            "name": "Road " + "1" + str(l) + str(i),
                            "length": road_length,
                            "id": "1" + str(l) + str(i),
                            "junction": "-1",
                        },
                    )
                root.append(road[i])
                link[i] = SubElement(road[i], "link")
                type[i] = SubElement(
                    road[i], "type", {"s": "0.0e+0", "type": "town"}
                )
                planView[i] = SubElement(road[i], "planView")
                elevationProfile[i] = SubElement(road[i], "elevationProfile")
                lateralProfile[i] = SubElement(road[i], "lateralProfile")
                lanes[i] = SubElement(road[i], "lanes")
                speed[i] = SubElement(
                    type[i], "speed", {"max": "40", "unit": "km/h"}
                )
                superelevation[i] = SubElement(
                    lateralProfile[i],
                    "superelevation",
                    {"s": "0", "a": "0", "b": "0", "c": "0", "d": "0"},
                )
                shape[i] = SubElement(
                    lateralProfile[i],
                    "shape",
                    {
                        "s": "0",
                        "t": "0",
                        "a": "0",
                        "b": "0",
                        "c": "0",
                        "d": "0",
                    },
                )

            ########
            # リンクの接続
            ########

            predecessor_road[0] = SubElement(
                link[0],
                "predecessor",
                {"elementType": "junction", "elementId": "1" + str(l) + "7"},
            )

            if (str(df_lane_info["road_successor_id"][df_lane_info[df_lane_info["road_id"] == 0].index[0]])!= ""):
                successor_road[0] = SubElement(
                    link[0],
                    "successor",
                    {
                        "elementType": "road",
                        "elementId": str(
                            df_lane_info["road_successor_id"][
                                df_lane_info[
                                    df_lane_info["road_id"] == 0
                                ].index[0]
                            ]
                        ),
                        "contactPoint": "start",
                    },
                )

            predecessor_road[1] = SubElement(
                link[1],
                "predecessor",
                {
                    "elementType": "road",
                    "elementId": "1" + str(l) + "6",
                    "contactPoint": "end",
                },
            )
            successor_road[1] = SubElement(
                link[1],
                "successor",
                {"elementType": "junction", "elementId": "1" + str(l) + "7"},
            )

            if (str(df_lane_info["road_predecessor_id"][df_lane_info[df_lane_info["road_id"] == 2].index[0]])!= ""):
                predecessor_road[2] = SubElement(
                    link[2],
                    "predecessor",
                    {
                        "elementType": "road",
                        "elementId": str(
                            df_lane_info["road_predecessor_id"][
                                df_lane_info[
                                    df_lane_info["road_id"] == 2
                                ].index[0]
                            ]
                        ),
                        "contactPoint": "end",
                    },
                )

            successor_road[2] = SubElement(
                link[2],
                "successor",
                {
                    "elementType": "road",
                    "elementId": "1" + str(l) + "6",
                    "contactPoint": "start",
                },
            )

            predecessor_road[3] = SubElement(
                link[3],
                "predecessor",
                {"elementType": "junction", "elementId": "1" + str(l) + "7"},
            )

            if (str(df_lane_info["road_successor_id"][df_lane_info[df_lane_info["road_id"] == 3].index[0]])!= ""):
                successor_road[3] = SubElement(
                    link[3],
                    "successor",
                    {
                        "elementType": "road",
                        "elementId": str(
                            df_lane_info["road_successor_id"][
                                df_lane_info[
                                    df_lane_info["road_id"] == 3
                                ].index[0]
                            ]
                        ),
                        "contactPoint": "start",
                    },
                )

            predecessor_road[4] = SubElement(
                link[4],
                "predecessor",
                {
                    "elementType": "road",
                    "elementId": "1" + str(l) + "1",
                    "contactPoint": "end",
                },
            )
            successor_road[4] = SubElement(
                link[4],
                "successor",
                {
                    "elementType": "road",
                    "elementId": "1" + str(l) + "0",
                    "contactPoint": "start",
                },
            )

            predecessor_road[5] = SubElement(
                link[5],
                "predecessor",
                {
                    "elementType": "road",
                    "elementId": "1" + str(l) + "1",
                    "contactPoint": "end",
                },
            )
            successor_road[5] = SubElement(
                link[5],
                "successor",
                {
                    "elementType": "road",
                    "elementId": "1" + str(l) + "3",
                    "contactPoint": "start",
                },
            )

            predecessor_road[6]  = SubElement(link[6],"predecessor",{"elementType":"road","elementId":"1" + str(l) + "2","contactPoint":"end"})
            successor_road[6]  = SubElement(link[6],"successor",{"elementType":"road","elementId":"1" + str(l) + "1","contactPoint":"start"})


            ########
            # 繰り返し部分
            ########

            node_number = 0  # ノード位置の通し番号
            tag_number = 0  # レーン一の情報
            lane_number = 0  # レーンの通し番号
            link_number = 7  # レーンのリンクの通し番号

            for i in road_id:
                df_bool = df_polyline["ID"] == i
                idx = df_polyline[df_polyline["ID"] == i].index[0]
                s = 0
                iter = df_bool.sum()
                #
                for j in range(iter - 1):
                    if df_polyline["length"][idx] != "":
                        geometry[node_number] = SubElement(
                            planView[i],
                            "geometry",
                            {
                                "s": format(s, ".8E"),
                                "x": format(df_polyline["x"][idx], ".8E"),
                                "y": format(df_polyline["y"][idx], ".8E"),
                                "hdg": format(df_polyline["hdg"][idx], ".8E"),
                                "length": format(
                                    df_polyline["length"][idx], ".8E"
                                ),
                            },
                        )
                        # Roadの形状を判定して、入力内容を選定
                        if df_polyline["shape"][idx] == "spiral":
                            spiral[idx] = SubElement(
                                geometry[node_number],
                                "spiral",
                                {
                                    "curvStart": format(
                                        df_polyline["curvature"][idx], ".8E"
                                    ),
                                    "curvEnd": format(
                                        df_polyline["curvature"][idx + 1], ".8E"
                                    ),
                                },
                            )
                        elif df_polyline["shape"][idx] == "arc":
                            arc[idx] = SubElement(
                                geometry[node_number],
                                "arc",
                                {
                                    "curvature": format(
                                        df_polyline["curvature"][idx], ".8E"
                                    )
                                },
                            )
                        else:
                            line_s[idx] = SubElement(
                                geometry[node_number], "line"
                            )
                        # elevation[node_number] = SubElement(elevationProfile[i],"elevation",{"s":format(s,'.8E'),"a":"0","b":"0","c":"0","d":"0"})
                        elevation[node_number] = SubElement(
                            elevationProfile[i],
                            "elevation",
                            {
                                "s": format(s, ".8E"),
                                "a": format(df_polyline["elev_a"][idx], ".8E"),
                                "b": format(df_polyline["elev_b"][idx], ".8E"),
                                "c": format(df_polyline["elev_c"][idx], ".8E"),
                                "d": format(df_polyline["elev_d"][idx], ".8E"),
                            },
                        )
                    s = s + df_polyline["length"][idx]
                    idx = idx + 1
                    node_number = node_number + 1

            ########
            # レーンの部分
            ########
            lanOffset1 = df_lane_info["offset"][
                df_lane_info[df_lane_info["road_id"] == 1].index[0]
            ]
            lanOffset2 = df_lane_info["offset"][
                df_lane_info[df_lane_info["road_id"] == 2].index[0]
            ]
            df_bool1 = df_lane_info["road_id"] == 1
            iter1 = df_bool1.sum()
            df_bool2 = df_lane_info["road_id"] == 2
            iter2 = df_bool2.sum()
            w1 = df_lane_info["lane_width"][
                df_lane_info[df_lane_info["road_id"] == 1].index[0]
            ]
            s1 = df_polyline[df_polyline["ID"] == 1]["length"].sum()
            for i in road_id:
                temp_tag = ""
                # テーブルからレーンの情報の位置を抽出
                idx = df_lane_info[df_lane_info["road_id"] == i].index[0]
                df_bool = df_lane_info["road_id"] == i
                iter = df_bool.sum()
                # まずはlaneOffsetとlaneSectionを定義
                if (
                    lanOffset1 != lanOffset2
                    and int(iter1 - iter2) == 1
                    and i == 1
                ):
                    o1 = lanOffset1 - lanOffset2
                    c1 = (3 * o1) / (s1 / 5) ** 2
                    d1 = (-2 * o1) / (s1 / 5) ** 3
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(lanOffset2),
                            "b": "0",
                            "c": str(c1),
                            "d": str(d1),
                        },
                    )
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": str(s1 / 5),
                            "a": str(lanOffset1),
                            "b": "0",
                            "c": "0",
                            "d": "0",
                        },
                    )
                elif (
                    lanOffset1 != lanOffset2
                    and int(iter1 - iter2) == 2
                    and i == 1
                ):
                    o1 = lanOffset1 - lanOffset2
                    b1 = o1 / s1
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(lanOffset2),
                            "b": str(b1),
                            "c": "0",
                            "d": "0",
                        },
                    )

                elif l in connect_merge_branch_list[2] and i == 0:
                    a0 = df_lane_info["offset"][idx]
                    s0 = df_polyline[df_polyline["ID"] == 0]["length"].sum()
                    b0 = -a0 / s0
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(a0),
                            "b": str(b0),
                            "c": "0",
                            "d": "0",
                        },
                    )

                elif l in connect_merge_branch_list[0] and i == 2:
                    a2 = 0
                    s2 = df_polyline[df_polyline["ID"] == 2]["length"].sum()
                    b2 = df_lane_info["offset"][idx] / s2
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(a2),
                            "b": str(b2),
                            "c": "0",
                            "d": "0",
                        },
                    )   

                else:
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(df_lane_info["offset"][idx]),
                            "b": "0",
                            "c": "0",
                            "d": "0",
                        },
                    )

                laneSection[i] = SubElement(
                    lanes[i], "laneSection", {"s": "0", "singleSide": "false"}
                )
                # ここからレーンのタグを作成
                for j in range(iter):
                    if temp_tag == df_lane_info["direction"][idx + j]:
                        None
                    else:
                        tag_number = tag_number + 1
                        temp_tag = df_lane_info["direction"][idx + j]
                        lane_tag[tag_number] = SubElement(
                            laneSection[i], df_lane_info["direction"][idx + j]
                        )
                    # ここからレーン内の詳細の記載
                    if temp_tag == "center":
                        lane[lane_number] = SubElement(
                            lane_tag[tag_number],
                            "lane",
                            {"id": "0", "type": "none", "level": "false"},
                        )
                    # センター以外の部分
                    else:
                        # print(len(link),link_number,len(lane),lane_number)
                        lane[lane_number] = SubElement(
                            lane_tag[tag_number],
                            "lane",
                            {
                                "id": str(df_lane_info["lane_id"][idx + j]),
                                "type": "driving",
                                "level": "false",
                            },
                        )
                        link[link_number] = SubElement(
                            lane[lane_number], "link"
                        )
                        # リンクの前後のレーンがあった時に反映
                        if df_lane_info["lane_predecessor"][idx + j] != "":
                            predecessor_link[link_number] = SubElement(
                                link[link_number],
                                "predecessor",
                                {
                                    "id": str(
                                        int(
                                            df_lane_info["lane_predecessor"][
                                                idx + j
                                            ]
                                        )
                                    )
                                },
                            )

                        if df_lane_info["lane_successor"][idx + j] != "":
                            successor_link[link_number] = SubElement(
                                link[link_number],
                                "successor",
                                {
                                    "id": str(
                                        int(
                                            df_lane_info["lane_successor"][
                                                idx + j
                                            ]
                                        )
                                    )
                                },
                            )
                        # 幅を設定
                        if (
                            lanOffset1 == lanOffset2
                            and int(iter1 - iter2) == 1
                            and i == 1
                            and j == 0
                        ):
                            c1 = (3 * w1) / (s1 / 5) ** 2
                            d1 = (-2 * w1) / (s1 / 5) ** 3
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": "0",
                                    "a": "0",
                                    "b": "0",
                                    "c": str(c1),
                                    "d": str(d1),
                                },
                            )
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": str(s1 / 5),
                                    "a": str(w1),
                                    "b": "0",
                                    "c": "0",
                                    "d": "0",
                                },
                            )

                        elif (
                            lanOffset1 != lanOffset2
                            and int(iter1 - iter2) == 1
                            and i == 1
                            and j == int(iter1 - 2)
                        ):
                            w1 = df_lane_info["lane_width"][idx + j]
                            c1 = (3 * w1) / (s1 / 5) ** 2
                            d1 = (-2 * w1) / (s1 / 5) ** 3
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": "0",
                                    "a": "0",
                                    "b": "0",
                                    "c": str(c1),
                                    "d": str(d1),
                                },
                            )
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": str(s1 / 5),
                                    "a": str(w1),
                                    "b": "0",
                                    "c": "0",
                                    "d": "0",
                                },
                            )

                        elif (
                            lanOffset1 == lanOffset2
                            and int(iter1 - iter2) == 2
                            and i == 1
                            and (j == 0 or j == 1)
                        ):
                            if j == 0:
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": "0",
                                        "a": "0",
                                        "b": "0",
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                                b1 = 2 * w1 / s1
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": str(s1 / 2),
                                        "a": "0",
                                        "b": str(b1),
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                            elif j == 1:
                                b1 = 2 * w1 / s1
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": "0",
                                        "a": "0",
                                        "b": str(b1),
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": str(s1 / 2),
                                        "a": str(w1),
                                        "b": "0",
                                        "c": "0",
                                        "d": "0",
                                    },
                                )

                        elif (
                            lanOffset1 != lanOffset2
                            and int(iter1 - iter2) == 2
                            and i == 1
                            and (j == int(iter1 - 2) or j == int(iter1 - 3))
                        ):
                            if j == int(iter1 - 2):
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": "0",
                                        "a": "0",
                                        "b": "0",
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                                b1 = 2 * w1 / s1
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": str(s1 / 2),
                                        "a": "0",
                                        "b": str(b1),
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                            elif j == int(iter1 - 3):
                                b1 = 2 * w1 / s1
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": "0",
                                        "a": "0",
                                        "b": str(b1),
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": str(s1 / 2),
                                        "a": str(w1),
                                        "b": "0",
                                        "c": "0",
                                        "d": "0",
                                    },
                                )

                        else:
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": "0",
                                    "a": str(
                                        df_lane_info["lane_width"][idx + j]
                                    ),
                                    "b": "0",
                                    "c": "0",
                                    "d": "0",
                                },
                            )
                    # jのループが終わったので、tag_numberを更新
                    # ここから共通部分
                    roadMark[lane_number] = SubElement(
                        lane[lane_number],
                        "roadMark",
                        {
                            "sOffset": "0",
                            "type": str(df_lane_info["type"][idx + j]),
                            "material": "standard",
                            "color": "white",
                            "width": "0.125",
                            "laneChange": str(
                                df_lane_info["lane_change"][idx + j]
                            ),
                        },
                    )
                    type[lane_number] = SubElement(
                        roadMark[lane_number],
                        "type",
                        {"name": str(df_lane_info["type"][idx + j])},
                    )
                    line[lane_number] = SubElement(
                        type[lane_number],
                        "line",
                        {
                            "length": "1.0e+1",
                            "space": "0.0e+0",
                            "width": "1.50e-1",
                            "sOffset": "0.0e+0",
                            "tOffset": "0.0e+0",
                        },
                    )
                    userData[lane_number] = SubElement(
                        lane[lane_number], "userData", {"code": "vectorLane"}
                    )
                    vectorLane[lane_number] = SubElement(
                        userData[lane_number],
                        "vectorLane",
                        {
                            "sOffset": "0.0000000000000000e+0",
                            "travelDir": "forward",
                        },
                    )
                    lane_number = lane_number + 1
                    link_number = link_number + 1

            ########
            # ジャンクションの部分
            ########

            tag_number = -1  # タグ番号
            tag_number_c = -1

            temp_tag = ""
            temp_tag_c = ""

            for i in range(len(df_junction)):
                # junctionについての設定
                if temp_tag == df_junction["junction_id"][i]:
                    None
                else:
                    tag_number = tag_number + 1
                    temp_tag = df_junction["junction_id"][i]
                    junction[tag_number] = Element(
                        "junction",
                        {
                            "name": "junction "
                            + "1"
                            + str(l)
                            + str(df_junction["junction_id"][i]),
                            "id": "1"
                            + str(l)
                            + str(df_junction["junction_id"][i]),
                        },
                    )
                    root.append(junction[tag_number])
                # Connectionについての設定
                if temp_tag_c == df_junction["connection_id"][i]:
                    None
                else:
                    tag_number_c = tag_number_c + 1
                    temp_tag_c = df_junction["connection_id"][i]
                    connection[tag_number_c] = SubElement(
                        junction[tag_number],
                        "connection",
                        {
                            "id": str(df_junction["connection_id"][i]),
                            "incomingRoad": "1"
                            + str(l)
                            + str(df_junction["incoming_road"][i]),
                            "connectingRoad": "1"
                            + str(l)
                            + str(df_junction["connecting_road"][i]),
                            "contactPoint": str(
                                df_junction["contact_point"][i]
                            ),
                        },
                    )
                laneLink[i] = SubElement(
                    connection[tag_number_c],
                    "laneLink",
                    {
                        "from": str(df_junction["lanelink_from"][i]),
                        "to": str(df_junction["lanelink_to"][i]),
                    },
                )

        print("Create merge xml data, merge ID will start with number 2.")
        for l in tqdm(range(len(str_obj_merge_list))):
            df_polyline = str_obj_merge_list[l].df_polyline
            df_junction = str_obj_merge_list[l].df_junction
            df_lane_info = str_obj_merge_list[l].df_lane_info

            df_polyline, df_junction, df_lane_info = change_merge_data(df_polyline, df_junction, df_lane_info)

            road_num = len(df_polyline)  # 道路を構成する中心点群ノードの数をカウント

            road_id = [0, 1, 2, 3, 4, 5, 6]

            road             = [""] * 7
            link             = [""] * 7 * 8
            predecessor_road = [""] * 7 * 8
            successor_road   = [""] * 7 * 8
            predecessor_link = [""] * 7 * 8
            successor_link   = [""] * 7 * 8
            type             = [""] * 7 * 8
            speed            = [""] * 7
            planView         = [""] * 7
            elevationProfile = [""] * 7
            lateralProfile   = [""] * 7
            superelevation   = [""] * 7
            lanes            = [""] * 7
            shape            = [""] * 7
            laneOffset       = [""] * 7
            laneSection      = [""] * 7
            lane_tag         = [""] * 7 * 7
            lane             = [""] * 7 * 8
            width            = [""] * 7 * 8
            roadMark         = [""] * 7 * 8
            speed            = [""] * 7 * 8
            userData         = [""] * 7 * 8
            vectorLane       = [""] * 7 * 8
            geometry         = [""] * road_num
            elevation        = [""] * road_num
            line             = [""] * road_num
            line_s           = [""] * road_num
            arc              = [""] * road_num
            spiral           = [""] * road_num
            junction         = [""] * 70
            connection       = [""] * 70
            laneLink         = [""] * 70

            ########
            # ここからRoad構築
            ########

            for i in road_id:
                # ここでは、該当のRoadIDのタイプを確認
                road_index = df_lane_info[df_lane_info["road_id"] == i].index[0]
                jnc_t = df_lane_info.iat[road_index, 1]
                # road_length = format(
                #     df_polyline[df_polyline["ID"] == i]["length"].sum(), ".8E"
                # )

                df_bool = df_polyline["ID"] == i
                idx     = df_polyline[df_polyline["ID"]  == i].index[0]
                s       = 0
                iter = df_bool.sum()
                for j in range(iter-1):
                    s = s + df_polyline["length"][idx]
                    idx = idx + 1
                road_length = format(s, ".8E")

                # ここから作成
                if i == 4 or i == 5:
                    road[i] = Element(
                        "road",
                        {
                            "name": "Road " + "2" + str(l) + str(i),
                            "length": road_length,
                            "id": "2" + str(l) + str(i),
                            "junction": "2" + str(l) + "7",
                        },
                    )
                else:
                    road[i] = Element(
                        "road",
                        {
                            "name": "Road " + "2" + str(l) + str(i),
                            "length": road_length,
                            "id": "2" + str(l) + str(i),
                            "junction": "-1",
                        },
                    )
                root.append(road[i])
                link[i] = SubElement(road[i], "link")
                type[i] = SubElement(
                    road[i], "type", {"s": "0.0e+0", "type": "town"}
                )
                planView[i] = SubElement(road[i], "planView")
                elevationProfile[i] = SubElement(road[i], "elevationProfile")
                lateralProfile[i] = SubElement(road[i], "lateralProfile")
                lanes[i] = SubElement(road[i], "lanes")
                speed[i] = SubElement(
                    type[i], "speed", {"max": "40", "unit": "km/h"}
                )
                superelevation[i] = SubElement(
                    lateralProfile[i],
                    "superelevation",
                    {"s": "0", "a": "0", "b": "0", "c": "0", "d": "0"},
                )
                shape[i] = SubElement(
                    lateralProfile[i],
                    "shape",
                    {
                        "s": "0",
                        "t": "0",
                        "a": "0",
                        "b": "0",
                        "c": "0",
                        "d": "0",
                    },
                )

            ########
            # リンクの接続
            ########

            successor_road[0] = SubElement(
                link[0],
                "successor",
                {"elementType": "junction", "elementId": "2" + str(l) + "7"},
            )

            if (str(df_lane_info["road_predecessor_id"][df_lane_info[df_lane_info["road_id"] == 0].index[0]])!= ""):
                predecessor_road[0] = SubElement(
                    link[0],
                    "predecessor",
                    {
                        "elementType": "road",
                        "elementId": str(
                            df_lane_info["road_predecessor_id"][
                                df_lane_info[
                                    df_lane_info["road_id"] == 0
                                ].index[0]
                            ]
                        ),
                        "contactPoint": "end",
                    },
                )

            predecessor_road[1] = SubElement(
                link[1],
                "predecessor",
                {"elementType": "junction", "elementId": "2" + str(l) + "7"},
            )
            successor_road[1] = SubElement(
                link[1],
                "successor",
                {
                    "elementType": "road",
                    "elementId": "2" + str(l) + "6",
                    "contactPoint": "start",
                },
            )

            predecessor_road[2] = SubElement(
                link[2],
                "predecessor",
                {
                    "elementType": "road",
                    "elementId": "2" + str(l) + "6",
                    "contactPoint": "end",
                },
            )

            if (str(df_lane_info["road_successor_id"][df_lane_info[df_lane_info["road_id"] == 2].index[0]])!= ""):
                successor_road[2] = SubElement(
                    link[2],
                    "successor",
                    {
                        "elementType": "road",
                        "elementId": str(
                            df_lane_info["road_successor_id"][
                                df_lane_info[
                                    df_lane_info["road_id"] == 2
                                ].index[0]
                            ]
                        ),
                        "contactPoint": "start",
                    },
                )

            if (str(df_lane_info["road_predecessor_id"][df_lane_info[df_lane_info["road_id"] == 3].index[0]])!= ""):
                predecessor_road[3] = SubElement(
                    link[3],
                    "predecessor",
                    {
                        "elementType": "road",
                        "elementId": str(
                            df_lane_info["road_predecessor_id"][
                                df_lane_info[
                                    df_lane_info["road_id"] == 3
                                ].index[0]
                            ]
                        ),
                        "contactPoint": "end",
                    },
                )

            successor_road[3] = SubElement(
                link[3],
                "successor",
                {"elementType": "junction", "elementId": "2" + str(l) + "7"},
            )

            predecessor_road[4] = SubElement(
                link[4],
                "predecessor",
                {
                    "elementType": "road",
                    "elementId": "2" + str(l) + "0",
                    "contactPoint": "end",
                },
            )
            successor_road[4] = SubElement(
                link[4],
                "successor",
                {
                    "elementType": "road",
                    "elementId": "2" + str(l) + "1",
                    "contactPoint": "start",
                },
            )

            predecessor_road[5] = SubElement(
                link[5],
                "predecessor",
                {
                    "elementType": "road",
                    "elementId": "2" + str(l) + "3",
                    "contactPoint": "end",
                },
            )
            successor_road[5] = SubElement(
                link[5],
                "successor",
                {
                    "elementType": "road",
                    "elementId": "2" + str(l) + "1",
                    "contactPoint": "start",
                },
            )

            predecessor_road[6]  = SubElement(link[6],"predecessor",{"elementType":"road","elementId":"2" + str(l) + "1","contactPoint":"end"})
            successor_road[6]  = SubElement(link[6],"successor",{"elementType":"road","elementId":"2" + str(l) + "2","contactPoint":"start"})

            ########
            # 繰り返し部分
            ########

            node_number = 0  # ノード位置の通し番号
            tag_number = 0  # レーン一の情報
            lane_number = 0  # レーンの通し番号
            link_number = 7  # レーンのリンクの通し番号

            for i in road_id:
                df_bool = df_polyline["ID"] == i
                idx = df_polyline[df_polyline["ID"] == i].index[0]
                s = 0
                iter = df_bool.sum()
                #
                for j in range(iter - 1):
                    if df_polyline["length"][idx] != "":
                        geometry[node_number] = SubElement(
                            planView[i],
                            "geometry",
                            {
                                "s": format(s, ".8E"),
                                "x": format(df_polyline["x"][idx], ".8E"),
                                "y": format(df_polyline["y"][idx], ".8E"),
                                "hdg": format(df_polyline["hdg"][idx], ".8E"),
                                "length": format(
                                    df_polyline["length"][idx], ".8E"
                                ),
                            },
                        )
                        # Roadの形状を判定して、入力内容を選定
                        if df_polyline["shape"][idx] == "spiral":
                            spiral[idx] = SubElement(
                                geometry[node_number],
                                "spiral",
                                {
                                    "curvStart": format(
                                        df_polyline["curvature"][idx], ".8E"
                                    ),
                                    "curvEnd": format(
                                        df_polyline["curvature"][idx + 1], ".8E"
                                    ),
                                },
                            )
                        elif df_polyline["shape"][idx] == "arc":
                            arc[idx] = SubElement(
                                geometry[node_number],
                                "arc",
                                {
                                    "curvature": format(
                                        df_polyline["curvature"][idx], ".8E"
                                    )
                                },
                            )
                        else:
                            line_s[idx] = SubElement(
                                geometry[node_number], "line"
                            )
                        # elevation[node_number] = SubElement(elevationProfile[i],"elevation",{"s":format(s,'.8E'),"a":"0","b":"0","c":"0","d":"0"})
                        elevation[node_number] = SubElement(
                            elevationProfile[i],
                            "elevation",
                            {
                                "s": format(s, ".8E"),
                                "a": format(df_polyline["elev_a"][idx], ".8E"),
                                "b": format(df_polyline["elev_b"][idx], ".8E"),
                                "c": format(df_polyline["elev_c"][idx], ".8E"),
                                "d": format(df_polyline["elev_d"][idx], ".8E"),
                            },
                        )
                    s = s + df_polyline["length"][idx]
                    idx = idx + 1
                    node_number = node_number + 1

            ########
            # レーンの部分
            ########
            lanOffset1 = df_lane_info["offset"][
                df_lane_info[df_lane_info["road_id"] == 1].index[0]
            ]
            lanOffset2 = df_lane_info["offset"][
                df_lane_info[df_lane_info["road_id"] == 2].index[0]
            ]
            df_bool1 = df_lane_info["road_id"] == 1
            iter1 = df_bool1.sum()
            df_bool2 = df_lane_info["road_id"] == 2
            iter2 = df_bool2.sum()
            x = int(iter1 - iter2)
            w1 = df_lane_info["lane_width"][
                df_lane_info[df_lane_info["road_id"] == 1].index[0]
            ]
            s1 = df_polyline[df_polyline["ID"] == 1]["length"].sum()

            for i in road_id:
                temp_tag = ""
                # テーブルからレーンの情報の位置を抽出
                idx = df_lane_info[df_lane_info["road_id"] == i].index[0]
                df_bool = df_lane_info["road_id"] == i
                iter = df_bool.sum()
                # まずはlaneOffsetとlaneSectionを定義
                if lanOffset1 != lanOffset2 and x == 1 and i == 1:
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(lanOffset1),
                            "b": "0",
                            "c": "0",
                            "d": "0",
                        },
                    )
                    o1 = lanOffset1 - lanOffset2
                    c1 = (-3 * o1) / (s1 / 5) ** 2
                    d1 = (2 * o1) / (s1 / 5) ** 3
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": str((4 * s1 / 5)),
                            "a": str(lanOffset1),
                            "b": "0",
                            "c": str(c1),
                            "d": str(d1),
                        },
                    )

                elif lanOffset1 != lanOffset2 and x == 2 and i == 1:
                    o1 = lanOffset1 - lanOffset2
                    b1 = -o1 / s1
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(lanOffset1),
                            "b": str(b1),
                            "c": "0",
                            "d": "0",
                        },
                    ) 

                elif l in connect_merge_branch_list[1] and i == 2:
                    a2 = df_lane_info["offset"][idx]
                    s2 = df_polyline[df_polyline["ID"] == 2]["length"].sum()
                    b2 = -a2 / s2
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(a2),
                            "b": str(b2),
                            "c": "0",
                            "d": "0",
                        },
                    )

                elif l in connect_merge_branch_list[3] and i == 0:
                    a0 = 0
                    s0 = df_polyline[df_polyline["ID"] == 0]["length"].sum()
                    b0 = df_lane_info["offset"][idx] / s0
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(a0),
                            "b": str(b0),
                            "c": "0",
                            "d": "0",
                        },
                    )                     

                else:
                    laneOffset[i] = SubElement(
                        lanes[i],
                        "laneOffset",
                        {
                            "s": "0",
                            "a": str(df_lane_info["offset"][idx]),
                            "b": "0",
                            "c": "0",
                            "d": "0",
                        },
                    )
                laneSection[i] = SubElement(
                    lanes[i], "laneSection", {"s": "0", "singleSide": "false"}
                )
                # ここからレーンのタグを作成
                for j in range(iter):
                    if temp_tag == df_lane_info["direction"][idx + j]:
                        None
                    else:
                        tag_number = tag_number + 1
                        temp_tag = df_lane_info["direction"][idx + j]
                        lane_tag[tag_number] = SubElement(
                            laneSection[i], df_lane_info["direction"][idx + j]
                        )
                    # ここからレーン内の詳細の記載
                    if temp_tag == "center":
                        lane[lane_number] = SubElement(
                            lane_tag[tag_number],
                            "lane",
                            {"id": "0", "type": "none", "level": "false"},
                        )
                    # センター以外の部分
                    else:
                        # print(len(link),link_number,len(lane),lane_number)
                        lane[lane_number] = SubElement(
                            lane_tag[tag_number],
                            "lane",
                            {
                                "id": str(df_lane_info["lane_id"][idx + j]),
                                "type": "driving",
                                "level": "false",
                            },
                        )
                        link[link_number] = SubElement(
                            lane[lane_number], "link"
                        )
                        # リンクの前後のレーンがあった時に反映
                        if df_lane_info["lane_predecessor"][idx + j] != "":
                            predecessor_link[link_number] = SubElement(
                                link[link_number],
                                "predecessor",
                                {
                                    "id": str(
                                        int(
                                            df_lane_info["lane_predecessor"][
                                                idx + j
                                            ]
                                        )
                                    )
                                },
                            )
                        if df_lane_info["lane_successor"][idx + j] != "":
                            successor_link[link_number] = SubElement(
                                link[link_number],
                                "successor",
                                {
                                    "id": str(
                                        int(
                                            df_lane_info["lane_successor"][
                                                idx + j
                                            ]
                                        )
                                    )
                                },
                            )
                        # 幅を設定
                        if (
                            lanOffset1 == lanOffset2
                            and x == 1
                            and i == 1
                            and j == 0
                        ):
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": "0",
                                    "a": str(w1),
                                    "b": "0",
                                    "c": "0",
                                    "d": "0",
                                },
                            )
                            c1 = (-3 * w1) / (s1 / 5) ** 2
                            d1 = (2 * w1) / (s1 / 5) ** 3
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": str(4 * s1 / 5),
                                    "a": str(w1),
                                    "b": "0",
                                    "c": str(c1),
                                    "d": str(d1),
                                },
                            )

                        elif (
                            lanOffset1 != lanOffset2
                            and x == 1
                            and i == 1
                            and j == int(iter1 - 2)
                        ):
                            w1 = df_lane_info["lane_width"][idx + j]
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": "0",
                                    "a": str(w1),
                                    "b": "0",
                                    "c": "0",
                                    "d": "0",
                                },
                            )
                            c1 = (-3 * w1) / (s1 / 5) ** 2
                            d1 = (2 * w1) / (s1 / 5) ** 3
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": str(4 * s1 / 5),
                                    "a": str(w1),
                                    "b": "0",
                                    "c": str(c1),
                                    "d": str(d1),
                                },
                            )

                        elif (
                            lanOffset1 == lanOffset2
                            and x == 2
                            and i == 1
                            and (j == 0 or j == 1)
                        ):
                            if j == 0:
                                b1 = -2 * w1 / s1
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": "0",
                                        "a": str(w1),
                                        "b": str(b1),
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": str(s1 / 2),
                                        "a": "0",
                                        "b": "0",
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                            elif j == 1:
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": "0",
                                        "a": str(w1),
                                        "b": "0",
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                                b1 = -2 * w1 / s1
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": str(s1 / 2),
                                        "a": str(w1),
                                        "b": str(b1),
                                        "c": "0",
                                        "d": "0",
                                    },
                                )

                        elif (
                            lanOffset1 != lanOffset2
                            and x == 2
                            and i == 1
                            and (j == int(iter1 - 2) or j == int(iter1 - 3))
                        ):
                            if j == int(iter1 - 2):
                                b1 = -2 * w1 / s1
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": "0",
                                        "a": str(w1),
                                        "b": str(b1),
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": str(s1 / 2),
                                        "a": "0",
                                        "b": "0",
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                            elif j == int(iter1 - 3):
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": "0",
                                        "a": str(w1),
                                        "b": "0",
                                        "c": "0",
                                        "d": "0",
                                    },
                                )
                                b1 = -2 * w1 / s1
                                width[lane_number] = SubElement(
                                    lane[lane_number],
                                    "width",
                                    {
                                        "sOffset": str(s1 / 2),
                                        "a": str(w1),
                                        "b": str(b1),
                                        "c": "0",
                                        "d": "0",
                                    },
                                )

                        else:
                            width[lane_number] = SubElement(
                                lane[lane_number],
                                "width",
                                {
                                    "sOffset": "0",
                                    "a": str(
                                        df_lane_info["lane_width"][idx + j]
                                    ),
                                    "b": "0",
                                    "c": "0",
                                    "d": "0",
                                },
                            )

                    # jのループが終わったので、tag_numberを更新
                    # ここから共通部分
                    roadMark[lane_number] = SubElement(
                        lane[lane_number],
                        "roadMark",
                        {
                            "sOffset": "0",
                            "type": str(df_lane_info["type"][idx + j]),
                            "material": "standard",
                            "color": "white",
                            "width": "0.125",
                            "laneChange": str(
                                df_lane_info["lane_change"][idx + j]
                            ),
                        },
                    )
                    type[lane_number] = SubElement(
                        roadMark[lane_number],
                        "type",
                        {"name": str(df_lane_info["type"][idx + j])},
                    )
                    line[lane_number] = SubElement(
                        type[lane_number],
                        "line",
                        {
                            "length": "1.0e+1",
                            "space": "0.0e+0",
                            "width": "1.50e-1",
                            "sOffset": "0.0e+0",
                            "tOffset": "0.0e+0",
                        },
                    )
                    userData[lane_number] = SubElement(
                        lane[lane_number], "userData", {"code": "vectorLane"}
                    )
                    vectorLane[lane_number] = SubElement(
                        userData[lane_number],
                        "vectorLane",
                        {
                            "sOffset": "0.0000000000000000e+0",
                            "travelDir": "forward",
                        },
                    )
                    lane_number = lane_number + 1
                    link_number = link_number + 1

            ########
            # ジャンクションの部分
            ########

            tag_number = -1  # タグ番号
            tag_number_c = -1

            temp_tag = ""
            temp_tag_c = ""

            for i in range(len(df_junction)):
                # junctionについての設定
                if temp_tag == df_junction["junction_id"][i]:
                    None
                else:
                    tag_number = tag_number + 1
                    temp_tag = df_junction["junction_id"][i]
                    junction[tag_number] = Element(
                        "junction",
                        {
                            "name": "junction "
                            + "2"
                            + str(l)
                            + str(df_junction["junction_id"][i]),
                            "id": "2"
                            + str(l)
                            + str(df_junction["junction_id"][i]),
                        },
                    )
                    root.append(junction[tag_number])
                # Connectionについての設定
                if temp_tag_c == df_junction["connection_id"][i]:
                    None
                else:
                    tag_number_c = tag_number_c + 1
                    temp_tag_c = df_junction["connection_id"][i]
                    connection[tag_number_c] = SubElement(
                        junction[tag_number],
                        "connection",
                        {
                            "id": str(df_junction["connection_id"][i]),
                            "incomingRoad": "2"
                            + str(l)
                            + str(df_junction["incoming_road"][i]),
                            "connectingRoad": "2"
                            + str(l)
                            + str(df_junction["connecting_road"][i]),
                            "contactPoint": str(
                                df_junction["contact_point"][i]
                            ),
                        },
                    )
                laneLink[i] = SubElement(
                    connection[tag_number_c],
                    "laneLink",
                    {
                        "from": str(df_junction["lanelink_from"][i]),
                        "to": str(df_junction["lanelink_to"][i]),
                    },
                )

        print("Create mainlane xml data, mainlane ID will start with number 3.")
        for l in tqdm(range(len(str_obj_mainlane_list))):
            df_polyline = str_obj_mainlane_list[l].df_polyline
            df_lane_info = str_obj_mainlane_list[l].df_lane_info

            road_num = len(df_polyline)

            road_id_num = df_lane_info["road_id"].iloc[-1] + 1
            # print("road_id_num = ", road_id_num)

            road_id = []
            for i in range(road_id_num):
                road_id.append(i)

            road = [""] * road_id_num
            link = [""] * road_id_num * 8
            predecessor_road = [""] * road_id_num * 8
            successor_road = [""] * road_id_num * 8
            predecessor_link = [""] * road_id_num * 8
            successor_link = [""] * road_id_num * 8
            type = [""] * road_id_num * 8
            speed = [""] * road_id_num
            planView = [""] * road_id_num
            elevationProfile = [""] * road_id_num
            lateralProfile = [""] * road_id_num
            superelevation = [""] * road_id_num
            lanes = [""] * road_id_num
            shape = [""] * road_id_num
            laneOffset = [""] * road_id_num
            laneSection = [""] * road_id_num
            lane_tag = [""] * road_id_num * 6
            lane = [""] * road_id_num * 7
            width = [""] * road_id_num * 7
            roadMark = [""] * road_id_num * 7
            speed = [""] * road_id_num * 7
            userData = [""] * road_id_num * 7
            vectorLane = [""] * road_id_num * 7
            geometry = [""] * road_num
            elevation = [""] * road_num
            line = [""] * road_num
            line_s = [""] * road_num
            arc = [""] * road_num
            spiral = [""] * road_num
            junction = [""] * 70
            connection = [""] * 70
            laneLink = [""] * 70

            ########
            # ここからRoad構築
            ########

            for i in road_id:
                # ここでは、該当のRoadIDのタイプを確認
                road_index = df_lane_info[df_lane_info["road_id"] == i].index[0]
                jnc_t = df_lane_info.iat[road_index, 1]
                road_length = format(
                    df_polyline[df_polyline["ID"] == i]["length"].sum(), ".8E"
                )
                # ここから作成
                road[i] = Element(
                    "road",
                    {
                        "name": "Road " + "3" + str(l) + str(i),
                        "length": road_length,
                        "id": "3" + str(l) + str(i),
                        "junction": "-1",
                    },
                )
                root.append(road[i])
                link[i] = SubElement(road[i], "link")
                type[i] = SubElement(
                    road[i], "type", {"s": "0.0e+0", "type": "town"}
                )
                planView[i] = SubElement(road[i], "planView")
                elevationProfile[i] = SubElement(road[i], "elevationProfile")
                lateralProfile[i] = SubElement(road[i], "lateralProfile")
                lanes[i] = SubElement(road[i], "lanes")
                speed[i] = SubElement(
                    type[i], "speed", {"max": "40", "unit": "km/h"}
                )
                superelevation[i] = SubElement(
                    lateralProfile[i],
                    "superelevation",
                    {"s": "0", "a": "0", "b": "0", "c": "0", "d": "0"},
                )
                shape[i] = SubElement(
                    lateralProfile[i],
                    "shape",
                    {
                        "s": "0",
                        "t": "0",
                        "a": "0",
                        "b": "0",
                        "c": "0",
                        "d": "0",
                    },
                )

            ########
            # リンクの接続
            ########

            if road_id_num != 1:
                if (
                    str(
                        df_lane_info["road_predecessor_id"][
                            df_lane_info[df_lane_info["road_id"] == 0].index[0]
                        ]
                    )
                    != ""
                ):
                    predecessor_road[0] = SubElement(
                        link[0],
                        "predecessor",
                        {
                            "elementType": "road",
                            "elementId": str(
                                df_lane_info["road_predecessor_id"][
                                    df_lane_info[
                                        df_lane_info["road_id"] == 0
                                    ].index[0]
                                ]
                            ),
                            "contactPoint": "end",
                        },
                    )

                successor_road[0] = SubElement(
                    link[0],
                    "successor",
                    {
                        "elementType": "road",
                        "elementId": "3" + str(l) + "1",
                        "contactPoint": "start",
                    },
                )

                if road_id_num > 2:
                    for i in range(1, road_id_num - 1):
                        successor_road[i] = SubElement(
                            link[i],
                            "successor",
                            {
                                "elementType": "road",
                                "elementId": "3" + str(l) + str(i + 1),
                                "contactPoint": "start",
                            },
                        )
                        predecessor_road[i] = SubElement(
                            link[i],
                            "predecessor",
                            {
                                "elementType": "road",
                                "elementId": "3" + str(l) + str(i - 1),
                                "contactPoint": "end",
                            },
                        )

                predecessor_road[road_id_num - 1] = SubElement(
                    link[road_id_num - 1],
                    "predecessor",
                    {
                        "elementType": "road",
                        "elementId": "3" + str(l) + str(road_id_num - 2),
                        "contactPoint": "end",
                    },
                )

                if (
                    str(
                        df_lane_info["road_successor_id"][
                            df_lane_info[
                                df_lane_info["road_id"] == road_id_num - 1
                            ].index[0]
                        ]
                    )
                    != ""
                ):
                    successor_road[road_id_num - 1] = SubElement(
                        link[road_id_num - 1],
                        "successor",
                        {
                            "elementType": "road",
                            "elementId": str(
                                df_lane_info["road_successor_id"][
                                    df_lane_info[
                                        df_lane_info["road_id"]
                                        == road_id_num - 1
                                    ].index[0]
                                ]
                            ),
                            "contactPoint": "start",
                        },
                    )

            else:
                if (
                    str(
                        df_lane_info["road_predecessor_id"][
                            df_lane_info[df_lane_info["road_id"] == 0].index[0]
                        ]
                    )
                    != ""
                ):
                    predecessor_road[0] = SubElement(
                        link[0],
                        "predecessor",
                        {
                            "elementType": "road",
                            "elementId": str(
                                df_lane_info["road_predecessor_id"][
                                    df_lane_info[
                                        df_lane_info["road_id"] == 0
                                    ].index[0]
                                ]
                            ),
                            "contactPoint": "end",
                        },
                    )

                if (
                    str(
                        df_lane_info["road_successor_id"][
                            df_lane_info[df_lane_info["road_id"] == 0].index[0]
                        ]
                    )
                    != ""
                ):
                    successor_road[0] = SubElement(
                        link[0],
                        "successor",
                        {
                            "elementType": "road",
                            "elementId": str(
                                df_lane_info["road_successor_id"][
                                    df_lane_info[
                                        df_lane_info["road_id"] == 0
                                    ].index[0]
                                ]
                            ),
                            "contactPoint": "start",
                        },
                    )

            ########
            # 繰り返し部分
            ########

            node_number = 0  # ノード位置の通し番号
            tag_number = 0  # レーン一の情報
            lane_number = 0  # レーンの通し番号
            link_number = 0  # レーンのリンクの通し番号

            for i in road_id:
                df_bool = df_polyline["ID"] == i
                idx = df_polyline[df_polyline["ID"] == i].index[0]
                s = 0
                iter = df_bool.sum()
                #
                for j in range(iter - 1):
                    if df_polyline["length"][idx] != "":
                        geometry[node_number] = SubElement(
                            planView[i],
                            "geometry",
                            {
                                "s": format(s, ".8E"),
                                "x": format(df_polyline["x"][idx], ".8E"),
                                "y": format(df_polyline["y"][idx], ".8E"),
                                "hdg": format(df_polyline["hdg"][idx], ".8E"),
                                "length": format(
                                    df_polyline["length"][idx], ".8E"
                                ),
                            },
                        )
                        # Roadの形状を判定して、入力内容を選定
                        if df_polyline["shape"][idx] == "spiral":
                            spiral[idx] = SubElement(
                                geometry[node_number],
                                "spiral",
                                {
                                    "curvStart": format(
                                        df_polyline["curvature"][idx], ".8E"
                                    ),
                                    "curvEnd": format(
                                        df_polyline["curvature"][idx + 1], ".8E"
                                    ),
                                },
                            )
                        elif df_polyline["shape"][idx] == "arc":
                            arc[idx] = SubElement(
                                geometry[node_number],
                                "arc",
                                {
                                    "curvature": format(
                                        df_polyline["curvature"][idx], ".8E"
                                    )
                                },
                            )
                        else:
                            line_s[idx] = SubElement(
                                geometry[node_number], "line"
                            )
                        # elevation[node_number] = SubElement(elevationProfile[i],"elevation",{"s":format(s,'.8E'),"a":"0","b":"0","c":"0","d":"0"})
                        elevation[node_number] = SubElement(
                            elevationProfile[i],
                            "elevation",
                            {
                                "s": format(s, ".8E"),
                                "a": format(df_polyline["elev_a"][idx], ".8E"),
                                "b": format(df_polyline["elev_b"][idx], ".8E"),
                                "c": format(df_polyline["elev_c"][idx], ".8E"),
                                "d": format(df_polyline["elev_d"][idx], ".8E"),
                            },
                        )
                    s = s + df_polyline["length"][idx]
                    idx = idx + 1
                    node_number = node_number + 1

            ########
            # レーンの部分
            ########

            for i in road_id:
                temp_tag = ""
                # テーブルからレーンの情報の位置を抽出
                idx = df_lane_info[df_lane_info["road_id"] == i].index[0]
                df_bool = df_lane_info["road_id"] == i
                iter = df_bool.sum()
                # まずはlaneOffsetとlaneSectionを定義

                laneOffset[i] = SubElement(
                    lanes[i],
                    "laneOffset",
                    {
                        "s": "0",
                        "a": str(df_lane_info["offset_a"][idx]),
                        "b": str(df_lane_info["offset_b"][idx]),
                        "c": str(df_lane_info["offset_c"][idx]),
                        "d": str(df_lane_info["offset_d"][idx]),
                    },
                )
                laneSection[i] = SubElement(
                    lanes[i], "laneSection", {"s": "0", "singleSide": "false"}
                )
                # ここからレーンのタグを作成
                for j in range(iter):
                    if temp_tag == df_lane_info["direction"][idx + j]:
                        None
                    else:
                        tag_number = tag_number + 1
                        temp_tag = df_lane_info["direction"][idx + j]
                        lane_tag[tag_number] = SubElement(
                            laneSection[i], df_lane_info["direction"][idx + j]
                        )
                    # ここからレーン内の詳細の記載
                    if temp_tag == "center":
                        lane[lane_number] = SubElement(
                            lane_tag[tag_number],
                            "lane",
                            {"id": "0", "type": "none", "level": "false"},
                        )
                    # センター以外の部分
                    else:
                        # print(len(link),link_number,len(lane),lane_number)
                        lane[lane_number] = SubElement(
                            lane_tag[tag_number],
                            "lane",
                            {
                                "id": str(df_lane_info["lane_id"][idx + j]),
                                "type": "driving",
                                "level": "false",
                            },
                        )
                        link[link_number] = SubElement(
                            lane[lane_number], "link"
                        )
                        # リンクの前後のレーンがあった時に反映
                        if df_lane_info["lane_predecessor"][idx + j] != "":
                            predecessor_link[link_number] = SubElement(
                                link[link_number],
                                "predecessor",
                                {
                                    "id": str(
                                        int(
                                            df_lane_info["lane_predecessor"][
                                                idx + j
                                            ]
                                        )
                                    )
                                },
                            )

                        if df_lane_info["lane_successor"][idx + j] != "":
                            successor_link[link_number] = SubElement(
                                link[link_number],
                                "successor",
                                {
                                    "id": str(
                                        int(
                                            df_lane_info["lane_successor"][
                                                idx + j
                                            ]
                                        )
                                    )
                                },
                            )
                        # 幅を設定

                        width[lane_number] = SubElement(
                            lane[lane_number],
                            "width",
                            {
                                "sOffset": "0",
                                "a": str(df_lane_info["lane_width_a"][idx + j]),
                                "b": str(df_lane_info["lane_width_b"][idx + j]),
                                "c": "0",
                                "d": "0",
                            },
                        )
                    # jのループが終わったので、tag_numberを更新
                    # jのループが終わったので、tag_numberを更新
                    # ここから共通部分
                    roadMark[lane_number] = SubElement(
                        lane[lane_number],
                        "roadMark",
                        {
                            "sOffset": "0",
                            "type": str(df_lane_info["type"][idx + j]),
                            "material": "standard",
                            "color": "white",
                            "width": "0.125",
                            "laneChange": str(
                                df_lane_info["lane_change"][idx + j]
                            ),
                        },
                    )
                    type[lane_number] = SubElement(
                        roadMark[lane_number],
                        "type",
                        {"name": str(df_lane_info["type"][idx + j])},
                    )
                    line[lane_number] = SubElement(
                        type[lane_number],
                        "line",
                        {
                            "length": "1.0e+1",
                            "space": "0.0e+0",
                            "width": "1.50e-1",
                            "sOffset": "0.0e+0",
                            "tOffset": "0.0e+0",
                        },
                    )
                    userData[lane_number] = SubElement(
                        lane[lane_number], "userData", {"code": "vectorLane"}
                    )
                    vectorLane[lane_number] = SubElement(
                        userData[lane_number],
                        "vectorLane",
                        {
                            "sOffset": "0.0000000000000000e+0",
                            "travelDir": "forward",
                        },
                    )
                    lane_number = lane_number + 1
                    link_number = link_number + 1

            ########
            # ジャンクションの部分
            ########

            tag_number = -1  # タグ番号
            tag_number_c = -1

            temp_tag = ""
            temp_tag_c = ""

        tree = ElementTree(root)

        self.indent(root)
        self.xodr_xml = tree
        # tree.write("openDRIVE_data.xodr", encoding="utf-8", xml_declaration=True)

    # 作成したxmlのrootを成形する関数#
    def indent(self, elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

            pass


def change_branch_data(df_polyline, df_junction, df_lane_info):

# region Branch 

    branch_id_list = df_polyline["ID"].tolist()
    branch_x_list = df_polyline["x"].tolist()
    branch_y_list = df_polyline["y"].tolist()
    branch_z_list = df_polyline["elev"].tolist()

    branch_z_s_list = df_polyline["length"].tolist()
    branch_z_a_list = df_polyline["elev_a"].tolist()
    branch_z_b_list = df_polyline["elev_b"].tolist()
    branch_z_c_list = df_polyline["elev_c"].tolist()
    branch_z_d_list = df_polyline["elev_d"].tolist()

    branch_z_param_list = [
        {"s": s, "a": a, "b": b, "c": c, "d": d}
        for s, a, b, c, d in zip(
            branch_z_s_list,
            branch_z_a_list,
            branch_z_b_list,
            branch_z_c_list,
            branch_z_d_list,
        )
    ]

    branch_id_list_2 = []
    branch_id_list_1 = []
    branch_id_list_4 = []
    branch_id_list_0 = []
    branch_id_list_5 = []
    branch_id_list_3 = []

    branch_x_list_2 = []
    branch_x_list_1 = []
    branch_x_list_4 = []
    branch_x_list_0 = []
    branch_x_list_5 = []
    branch_x_list_3 = []

    branch_y_list_2 = []
    branch_y_list_1 = []
    branch_y_list_4 = []
    branch_y_list_0 = []
    branch_y_list_5 = []
    branch_y_list_3 = []

    branch_z_list_2 = []
    branch_z_list_1 = []
    branch_z_list_4 = []
    branch_z_list_0 = []
    branch_z_list_5 = []
    branch_z_list_3 = []

    branch_z_param_list_2 = []
    branch_z_param_list_1 = []
    branch_z_param_list_4 = []
    branch_z_param_list_0 = []
    branch_z_param_list_5 = []
    branch_z_param_list_3 = []

    for i in range(len(branch_id_list)):
        if branch_id_list[i] == 0:
            branch_id_list_0 += [0]
        elif branch_id_list[i] == 1:
            branch_id_list_1 += [1]
        elif branch_id_list[i] == 2:
            branch_id_list_2 += [2]
        elif branch_id_list[i] == 3:
            branch_id_list_3 += [3]
        elif branch_id_list[i] == 4:
            branch_id_list_4 += [4]
        elif branch_id_list[i] == 5:
            branch_id_list_5 += [5]

    branch_id_num_2 = len(branch_id_list_2)
    branch_id_num_1 = len(branch_id_list_2) + len(branch_id_list_1)
    branch_id_num_4 = (
        len(branch_id_list_2)
        + len(branch_id_list_1)
        + len(branch_id_list_4)
    )
    branch_id_num_0 = (
        len(branch_id_list_2)
        + len(branch_id_list_1)
        + len(branch_id_list_4)
        + len(branch_id_list_0)
    )
    branch_id_num_5 = (
        len(branch_id_list_2)
        + len(branch_id_list_1)
        + len(branch_id_list_4)
        + len(branch_id_list_0)
        + len(branch_id_list_5)
    )
    branch_id_num_3 = len(branch_id_list)
    
    hdg_start_main_branch = df_polyline["hdg"].tolist()[0]
    hdg_start_sub_branch = df_polyline["hdg"].tolist()[branch_id_num_1-1]

    branch_x_list_2.extend(branch_x_list[0:branch_id_num_2])
    branch_x_list_1.extend(branch_x_list[branch_id_num_2:branch_id_num_1])
    branch_x_list_4.extend(branch_x_list[branch_id_num_1:branch_id_num_4])
    branch_x_list_0.extend(branch_x_list[branch_id_num_4:branch_id_num_0])
    branch_x_list_5.extend(branch_x_list[branch_id_num_0:branch_id_num_5])
    branch_x_list_3.extend(branch_x_list[branch_id_num_5:branch_id_num_3])

    branch_y_list_2.extend(branch_y_list[0:branch_id_num_2])
    branch_y_list_1.extend(branch_y_list[branch_id_num_2:branch_id_num_1])
    branch_y_list_4.extend(branch_y_list[branch_id_num_1:branch_id_num_4])
    branch_y_list_0.extend(branch_y_list[branch_id_num_4:branch_id_num_0])
    branch_y_list_5.extend(branch_y_list[branch_id_num_0:branch_id_num_5])
    branch_y_list_3.extend(branch_y_list[branch_id_num_5:branch_id_num_3])

    branch_z_list_2.extend(branch_z_list[0:branch_id_num_2])
    branch_z_list_1.extend(branch_z_list[branch_id_num_2:branch_id_num_1])
    branch_z_list_4.extend(branch_z_list[branch_id_num_1:branch_id_num_4])
    branch_z_list_0.extend(branch_z_list[branch_id_num_4:branch_id_num_0])
    branch_z_list_5.extend(branch_z_list[branch_id_num_0:branch_id_num_5])
    branch_z_list_3.extend(branch_z_list[branch_id_num_5:branch_id_num_3])

    branch_z_param_list_2.extend(branch_z_param_list[0:branch_id_num_2])
    branch_z_param_list_1.extend(
        branch_z_param_list[branch_id_num_2:branch_id_num_1]
    )
    branch_z_param_list_4.extend(
        branch_z_param_list[branch_id_num_1:branch_id_num_4]
    )
    branch_z_param_list_0.extend(
        branch_z_param_list[branch_id_num_4:branch_id_num_0]
    )
    branch_z_param_list_5.extend(
        branch_z_param_list[branch_id_num_0:branch_id_num_5]
    )
    branch_z_param_list_3.extend(
        branch_z_param_list[branch_id_num_5:branch_id_num_3]
    )

    # endregion

# region 合流部作成（ID:6)

    x_list_tmp = branch_x_list_1
    y_list_tmp = branch_y_list_1 
    z_list_tmp = branch_z_list_1
    z_param_list_tmp = branch_z_param_list_1
    
    branch_id_list_6 = []
    branch_x_list_6 = []
    branch_y_list_6 = []
    branch_z_list_6 = []
    branch_z_param_list_6 = []

    branch_id_list_1 = []
    branch_x_list_1 = []
    branch_y_list_1 = []
    branch_z_list_1 = []
    branch_z_param_list_1 = []

    id_num1 = len(x_list_tmp) - 1
    id_num6 = 1
    branch_id_list_1 = [1]*int(id_num1)
    branch_id_list_6 = [6]*int(id_num6)

    branch_x_list_1.extend(x_list_tmp[id_num6:len(x_list_tmp)])
    branch_y_list_1.extend(y_list_tmp[id_num6:len(x_list_tmp)])
    branch_z_list_1.extend(z_list_tmp[id_num6:len(x_list_tmp)])
    branch_z_param_list_1.extend(z_param_list_tmp[id_num6:len(x_list_tmp)])

    branch_x_list_6.extend(x_list_tmp[0:id_num6])
    branch_y_list_6.extend(y_list_tmp[0:id_num6])
    branch_z_list_6.extend(z_list_tmp[0:id_num6])
    branch_z_param_list_6.extend(z_param_list_tmp[0:id_num6])

    branch_id_list_6.insert(1,6)
    branch_x_list_6.insert(1,branch_x_list_1[0])
    branch_y_list_6.insert(1,branch_y_list_1[0]) 
    branch_z_list_6.insert(1,branch_z_list_1[0]) 
    branch_z_param_list_6.insert(1,branch_z_param_list_1[0].copy())
    
    p0 = np.array([branch_x_list_6[1],branch_y_list_6[1]])
    p1 = np.array([branch_x_list_6[0],branch_y_list_6[0]])     
    add_s = np.linalg.norm(p0-p1)
    branch_z_param_list_6[1]['s'] = add_s

    branch_z_param_list_1[-1]['s'] = 0
    branch_z_param_list_6[-1]['s'] = 0

#endregion



    
    branch_id_list_0.insert(0, 0)
    branch_x_list_0.insert(0, branch_x_list_4[-2])
    branch_y_list_0.insert(0, branch_y_list_4[-2])
    branch_z_list_0.insert(0, branch_z_list_4[-2])
    branch_z_param_list_0.insert(0, branch_z_param_list_4[-2])

    branch_id_list_0.insert(0, 0)
    branch_x_list_0.insert(0, branch_x_list_4[-3])
    branch_y_list_0.insert(0, branch_y_list_4[-3])
    branch_z_list_0.insert(0, branch_z_list_4[-3])
    branch_z_param_list_0.insert(0, branch_z_param_list_4[-3])

    branch_id_list_4.pop(-1)
    branch_x_list_4.pop(-1)
    branch_y_list_4.pop(-1)
    branch_z_list_4.pop(-1)
    branch_z_param_list_4.pop(-1)

    branch_id_list_4.pop(-1)
    branch_x_list_4.pop(-1)
    branch_y_list_4.pop(-1)
    branch_z_list_4.pop(-1)
    branch_z_param_list_4.pop(-1)



    branch_id_list_3.insert(0, 3)
    branch_x_list_3.insert(0, branch_x_list_5[-2])
    branch_y_list_3.insert(0, branch_y_list_5[-2])
    branch_z_list_3.insert(0, branch_z_list_5[-2])
    branch_z_param_list_3.insert(0, branch_z_param_list_5[-2])

    branch_id_list_3.insert(0, 3)
    branch_x_list_3.insert(0, branch_x_list_5[-3])
    branch_y_list_3.insert(0, branch_y_list_5[-3])
    branch_z_list_3.insert(0, branch_z_list_5[-3])
    branch_z_param_list_3.insert(0, branch_z_param_list_5[-3])

    branch_id_list_5.pop(-1)
    branch_x_list_5.pop(-1)
    branch_y_list_5.pop(-1)
    branch_z_list_5.pop(-1)
    branch_z_param_list_5.pop(-1)

    branch_id_list_5.pop(-1)
    branch_x_list_5.pop(-1)
    branch_y_list_5.pop(-1)
    branch_z_list_5.pop(-1)
    branch_z_param_list_5.pop(-1)






    ########################################################

# region 222222222222

    main_id_list = (
        branch_id_list_2
        + branch_id_list_6
        + branch_id_list_1
        + branch_id_list_4
        + branch_id_list_0
    )
    main_x_list = (
        branch_x_list_2
        + branch_x_list_6
        + branch_x_list_1
        + branch_x_list_4
        + branch_x_list_0
    )
    main_y_list = (
        branch_y_list_2
        + branch_y_list_6
        + branch_y_list_1
        + branch_y_list_4
        + branch_y_list_0
    )
    main_z_list = (
        branch_z_list_2
        + branch_z_list_6
        + branch_z_list_1
        + branch_z_list_4
        + branch_z_list_0
    )
    main_z_param_list = (
        branch_z_param_list_2
        + branch_z_param_list_6
        + branch_z_param_list_1
        + branch_z_param_list_4
        + branch_z_param_list_0
    )
    main_z_s_list = [x["s"] for x in main_z_param_list]
    main_z_a_list = [x["a"] for x in main_z_param_list]
    main_z_b_list = [x["b"] for x in main_z_param_list]
    main_z_c_list = [x["c"] for x in main_z_param_list]
    main_z_d_list = [x["d"] for x in main_z_param_list]

    sub_id_list = branch_id_list_5 + branch_id_list_3
    sub_x_list = branch_x_list_5 + branch_x_list_3
    sub_y_list = branch_y_list_5 + branch_y_list_3
    sub_z_list = branch_z_list_5 + branch_z_list_3
    sub_z_param_list = branch_z_param_list_5 + branch_z_param_list_3
    sub_z_s_list = [x["s"] for x in sub_z_param_list]
    sub_z_a_list = [x["a"] for x in sub_z_param_list]
    sub_z_b_list = [x["b"] for x in sub_z_param_list]
    sub_z_c_list = [x["c"] for x in sub_z_param_list]
    sub_z_d_list = [x["d"] for x in sub_z_param_list]

    # データフレームの辞書設定
    main_df_polyline_dict = dict(
        ID=main_id_list,
        X=main_x_list,
        Y=main_y_list,
        elev=main_z_list,
        elev_s=main_z_s_list,
        elev_a=main_z_a_list,
        elev_b=main_z_b_list,
        elev_c=main_z_c_list,
        elev_d=main_z_d_list,
    )

    sub_df_polyline_dict = dict(
        ID=sub_id_list,
        X=sub_x_list,
        Y=sub_y_list,
        elev=sub_z_list,
        elev_s=sub_z_s_list,
        elev_a=sub_z_a_list,
        elev_b=sub_z_b_list,
        elev_c=sub_z_c_list,
        elev_d=sub_z_d_list,
    )

    main_df_polyline = pd.DataFrame(data=main_df_polyline_dict)
    sub_df_polyline = pd.DataFrame(data=sub_df_polyline_dict)

    # main_df_polyline = pd.read_csv(r"AutoXodr\input_data\main_road.csv")
    # sub_df_polyline = pd.read_csv(r"AutoXodr\input_data\sub_road.csv")

    main_df_polyline, main_hdg_list_branch = ajust.add_curvature_info(main_df_polyline, hdg_start_main_branch)
    sub_df_polyline, sub_hdg_list_branch = ajust.add_curvature_info(sub_df_polyline, hdg_start_sub_branch)

    # （根本的な解決が必要な箇所）
    # 本線と加速車線でラジアン方位(hdg)の値が意味的には同じだが異なる（例：１degと361degの関係）←これがOpenDriveとして読み込ませる際に悪さをする
    # 以下はその一時対応

    # 本線の合流差路中心のラジアン方位を抽出する
    # base_hdg_id = 22
    base_hdg_id = len(branch_id_list_2 + branch_id_list_6 + branch_id_list_1) + 1
    base_hdg = main_df_polyline["hdg"][base_hdg_id]  # サンプルの差路中心
    base_hdg_sub_id = 0  # 加速車線の末尾＝差路中心
    base_hdg_sub = sub_df_polyline["hdg"][base_hdg_sub_id]

    # 180度以上方位に差がある＝ラジアン方位のスケールが違う。その場合は比較結果で場合分けして+-piを適用する
    if math.pi <= abs(base_hdg - base_hdg_sub):
        if base_hdg > base_hdg_sub:
            sub_df_polyline["hdg"] = [
                x + 2 * math.pi for x in sub_df_polyline["hdg"]
            ]
        elif base_hdg < base_hdg_sub:
            sub_df_polyline["hdg"] = [
                x - 2 * math.pi for x in sub_df_polyline["hdg"]
            ]
        else:
            pass

    out_df = pd.concat([main_df_polyline, sub_df_polyline])
    df_polyline_new = out_df.reset_index(drop=True)
# endregion


    df_junction["junction_id"] = df_junction["junction_id"] + 1

    df_junction_new = df_junction


    branch_id_list = df_lane_info["road_id"].tolist()

    branch_id_list_2 = []
    branch_id_list_1 = []
    branch_id_list_4 = []
    branch_id_list_0 = []
    branch_id_list_5 = []
    branch_id_list_3 = []


    for i in range(len(branch_id_list)):
        if branch_id_list[i] == 0:
            branch_id_list_0 += [0]
        elif branch_id_list[i] == 1:
            branch_id_list_1 += [1]
        elif branch_id_list[i] == 2:
            branch_id_list_2 += [2]
        elif branch_id_list[i] == 3:
            branch_id_list_3 += [3]
        elif branch_id_list[i] == 4:
            branch_id_list_4 += [4]
        elif branch_id_list[i] == 5:
            branch_id_list_5 += [5]

    main_lane_num0 = len(branch_id_list_0) - 1
    main_lane_num1 = len(branch_id_list_2) - 1
    sub_lane_num = len(branch_id_list_3) - 1

    branch_id_num_2 = len(branch_id_list_2)
    branch_id_num_1 = len(branch_id_list_2) + len(branch_id_list_1)
    branch_id_num_4 = len(branch_id_list_2) + len(branch_id_list_1)+ len(branch_id_list_4)
    branch_id_num_0 = len(branch_id_list_2) + len(branch_id_list_1) + len(branch_id_list_4) + len(branch_id_list_0)
    branch_id_num_5 = len(branch_id_list_2) + len(branch_id_list_1) + len(branch_id_list_4) + len(branch_id_list_0) + len(branch_id_list_5)
    branch_id_num_3 = len(branch_id_list)

    branch_offset_list = df_lane_info["offset"].tolist()

    if branch_offset_list[branch_id_num_2-1] == branch_offset_list[branch_id_num_1-1]:
        branch_direction = 0
    else:
        branch_direction = 1

    df_lane_info_new = make_df_lane_info_branch(main_lane_num0, main_lane_num1, sub_lane_num, branch_direction)

    return df_polyline_new, df_junction_new, df_lane_info_new

def change_merge_data(df_polyline, df_junction, df_lane_info):

# region Merge

    merge_id_list = df_polyline["ID"].tolist()
    merge_x_list = df_polyline["x"].tolist()
    merge_y_list = df_polyline["y"].tolist()
    merge_z_list = df_polyline["elev"].tolist()

    merge_z_s_list = df_polyline["length"].tolist()
    merge_z_a_list = df_polyline["elev_a"].tolist()
    merge_z_b_list = df_polyline["elev_b"].tolist()
    merge_z_c_list = df_polyline["elev_c"].tolist()
    merge_z_d_list = df_polyline["elev_d"].tolist()

    merge_z_param_list = [
        {"s": s, "a": a, "b": b, "c": c, "d": d}
        for s, a, b, c, d in zip(
            merge_z_s_list,
            merge_z_a_list,
            merge_z_b_list,
            merge_z_c_list,
            merge_z_d_list,
        )
    ]

    merge_id_list_0 = []
    merge_id_list_4 = []
    merge_id_list_1 = []
    merge_id_list_2 = []
    merge_id_list_3 = []
    merge_id_list_5 = []

    merge_x_list_0 = []
    merge_x_list_4 = []
    merge_x_list_1 = []
    merge_x_list_2 = []
    merge_x_list_3 = []
    merge_x_list_5 = []

    merge_y_list_0 = []
    merge_y_list_4 = []
    merge_y_list_1 = []
    merge_y_list_2 = []
    merge_y_list_3 = []
    merge_y_list_5 = []

    merge_z_list_0 = []
    merge_z_list_4 = []
    merge_z_list_1 = []
    merge_z_list_2 = []
    merge_z_list_3 = []
    merge_z_list_5 = []

    merge_z_param_list_0 = []
    merge_z_param_list_4 = []
    merge_z_param_list_1 = []
    merge_z_param_list_2 = []
    merge_z_param_list_3 = []
    merge_z_param_list_5 = []

    for i in range(len(merge_id_list)):
        if merge_id_list[i] == 0:
            merge_id_list_0 += [0]
        elif merge_id_list[i] == 1:
            merge_id_list_1 += [1]
        elif merge_id_list[i] == 2:
            merge_id_list_2 += [2]
        elif merge_id_list[i] == 3:
            merge_id_list_3 += [3]
        elif merge_id_list[i] == 4:
            merge_id_list_4 += [4]
        elif merge_id_list[i] == 5:
            merge_id_list_5 += [5]

    merge_id_num_0 = len(merge_id_list_0)
    merge_id_num_4 = len(merge_id_list_4) + len(merge_id_list_0)
    merge_id_num_1 = (
        len(merge_id_list_1) + len(merge_id_list_4) + len(merge_id_list_0)
    )
    merge_id_num_2 = (
        len(merge_id_list_2)
        + len(merge_id_list_1)
        + len(merge_id_list_4)
        + len(merge_id_list_0)
    )
    merge_id_num_3 = (
        len(merge_id_list_3)
        + len(merge_id_list_2)
        + len(merge_id_list_1)
        + len(merge_id_list_4)
        + len(merge_id_list_0)
    )
    merge_id_num_5 = len(merge_id_list)

    hdg_start_main_merge = df_polyline["hdg"].tolist()[0]
    hdg_start_sub_merge = df_polyline["hdg"].tolist()[merge_id_num_2]
    hdg_end_sub_merge = df_polyline["hdg"].tolist()[merge_id_num_4]

    merge_x_list_0.extend(merge_x_list[0:merge_id_num_0])
    merge_x_list_4.extend(merge_x_list[merge_id_num_0:merge_id_num_4])
    merge_x_list_1.extend(merge_x_list[merge_id_num_4:merge_id_num_1])
    merge_x_list_2.extend(merge_x_list[merge_id_num_1:merge_id_num_2])
    merge_x_list_3.extend(merge_x_list[merge_id_num_2:merge_id_num_3])
    merge_x_list_5.extend(merge_x_list[merge_id_num_3:merge_id_num_5])

    merge_y_list_0.extend(merge_y_list[0:merge_id_num_0])
    merge_y_list_4.extend(merge_y_list[merge_id_num_0:merge_id_num_4])
    merge_y_list_1.extend(merge_y_list[merge_id_num_4:merge_id_num_1])
    merge_y_list_2.extend(merge_y_list[merge_id_num_1:merge_id_num_2])
    merge_y_list_3.extend(merge_y_list[merge_id_num_2:merge_id_num_3])
    merge_y_list_5.extend(merge_y_list[merge_id_num_3:merge_id_num_5])

    merge_z_list_0.extend(merge_z_list[0:merge_id_num_0])
    merge_z_list_4.extend(merge_z_list[merge_id_num_0:merge_id_num_4])
    merge_z_list_1.extend(merge_z_list[merge_id_num_4:merge_id_num_1])
    merge_z_list_2.extend(merge_z_list[merge_id_num_1:merge_id_num_2])
    merge_z_list_3.extend(merge_z_list[merge_id_num_2:merge_id_num_3])
    merge_z_list_5.extend(merge_z_list[merge_id_num_3:merge_id_num_5])

    merge_z_param_list_0.extend(merge_z_param_list[0:merge_id_num_0])
    merge_z_param_list_4.extend(
        merge_z_param_list[merge_id_num_0:merge_id_num_4]
    )
    merge_z_param_list_1.extend(
        merge_z_param_list[merge_id_num_4:merge_id_num_1]
    )
    merge_z_param_list_2.extend(
        merge_z_param_list[merge_id_num_1:merge_id_num_2]
    )
    merge_z_param_list_3.extend(
        merge_z_param_list[merge_id_num_2:merge_id_num_3]
    )
    merge_z_param_list_5.extend(
        merge_z_param_list[merge_id_num_3:merge_id_num_5]
    )

    x_list_tmp = merge_x_list_1
    y_list_tmp = merge_y_list_1 
    z_list_tmp = merge_z_list_1
    z_param_list_tmp = merge_z_param_list_1
    
    merge_id_list_6 = []
    merge_x_list_6 = []
    merge_y_list_6 = []
    merge_z_list_6 = []
    merge_z_param_list_6 = []

    merge_id_list_1 = []
    merge_x_list_1 = []
    merge_y_list_1 = []
    merge_z_list_1 = []
    merge_z_param_list_1 = []

    id_num1 = len(x_list_tmp) - 1
    id_num6 = 1
    merge_id_list_1 = [1]*int(id_num1)
    merge_id_list_6 = [6]*int(id_num6)

    merge_x_list_1.extend(x_list_tmp[0:id_num1])
    merge_y_list_1.extend(y_list_tmp[0:id_num1])
    merge_z_list_1.extend(z_list_tmp[0:id_num1])
    merge_z_param_list_1.extend(z_param_list_tmp[0:id_num1])

    merge_x_list_6.extend(x_list_tmp[id_num1:id_num1+id_num6])
    merge_y_list_6.extend(y_list_tmp[id_num1:id_num1+id_num6])
    merge_z_list_6.extend(z_list_tmp[id_num1:id_num1+id_num6])
    merge_z_param_list_6.extend(z_param_list_tmp[id_num1:id_num1+id_num6])

    merge_x_list_6.insert(0,merge_x_list_1[-1])
    merge_y_list_6.insert(0,merge_y_list_1[-1]) 
    merge_z_list_6.insert(0,merge_z_list_1[-1]) 
    
    p0 = np.array([merge_x_list_6[0],merge_y_list_6[0]])
    p1 = np.array([merge_x_list_6[1],merge_y_list_6[1]])
    
    add_s = np.linalg.norm(p0-p1)
    merge_z_param_list_6.insert(0,merge_z_param_list_1[-1].copy())
    merge_z_param_list_6[0]['s'] = add_s

    merge_z_param_list_1[-1]['s'] = 0
    merge_z_param_list_6[-1]['s'] = 0

    merge_id_list_6.insert(0,6)



    merge_id_list_0.insert(0, 0)
    merge_x_list_0.insert(len(merge_x_list_0), merge_x_list_4[1])
    merge_y_list_0.insert(len(merge_y_list_0), merge_y_list_4[1])
    merge_z_list_0.insert(len(merge_z_list_0), merge_z_list_4[1])
    merge_z_param_list_0.insert(len(merge_z_param_list_0), merge_z_param_list_4[1])

    merge_id_list_0.insert(0, 0)
    merge_x_list_0.insert(len(merge_x_list_0), merge_x_list_4[2])
    merge_y_list_0.insert(len(merge_y_list_0), merge_y_list_4[2])
    merge_z_list_0.insert(len(merge_z_list_0), merge_z_list_4[2])
    merge_z_param_list_0.insert(len(merge_z_param_list_0), merge_z_param_list_4[2])

    merge_id_list_4.pop(0)
    merge_x_list_4.pop(0)
    merge_y_list_4.pop(0)
    merge_z_list_4.pop(0)
    merge_z_param_list_4.pop(0)

    merge_id_list_4.pop(0)
    merge_x_list_4.pop(0)
    merge_y_list_4.pop(0)
    merge_z_list_4.pop(0)
    merge_z_param_list_4.pop(0)



    merge_id_list_3.insert(0, 3)
    merge_x_list_3.insert(len(merge_x_list_3), merge_x_list_5[1])
    merge_y_list_3.insert(len(merge_y_list_3), merge_y_list_5[1])
    merge_z_list_3.insert(len(merge_z_list_3), merge_z_list_5[1])
    merge_z_param_list_3.insert(len(merge_z_param_list_3), merge_z_param_list_5[1])

    merge_id_list_3.insert(0, 3)
    merge_x_list_3.insert(len(merge_x_list_3), merge_x_list_5[2])
    merge_y_list_3.insert(len(merge_y_list_3), merge_y_list_5[2])
    merge_z_list_3.insert(len(merge_z_list_3), merge_z_list_5[2])
    merge_z_param_list_3.insert(len(merge_z_param_list_3), merge_z_param_list_5[2])

    merge_id_list_5.pop(0)
    merge_x_list_5.pop(0)
    merge_y_list_5.pop(0)
    merge_z_list_5.pop(0)
    merge_z_param_list_5.pop(0)

    merge_id_list_5.pop(0)
    merge_x_list_5.pop(0)
    merge_y_list_5.pop(0)
    merge_z_list_5.pop(0)
    merge_z_param_list_5.pop(0)

    # endregion

    ########################################################

# region 222222222222

    main_id_list = (
        merge_id_list_0
        + merge_id_list_4
        + merge_id_list_1
        + merge_id_list_6
        + merge_id_list_2
    )
    main_x_list = (
        merge_x_list_0
        + merge_x_list_4
        + merge_x_list_1
        + merge_x_list_6
        + merge_x_list_2
    )
    main_y_list = (
        merge_y_list_0
        + merge_y_list_4
        + merge_y_list_1
        + merge_y_list_6
        + merge_y_list_2
    )
    main_z_list = (
        merge_z_list_0
        + merge_z_list_4
        + merge_z_list_1
        + merge_z_list_6
        + merge_z_list_2
    )
    main_z_param_list = (
        merge_z_param_list_0
        + merge_z_param_list_4
        + merge_z_param_list_1
        + merge_z_param_list_6
        + merge_z_param_list_2
    )
    main_z_s_list = [x["s"] for x in main_z_param_list]
    main_z_a_list = [x["a"] for x in main_z_param_list]
    main_z_b_list = [x["b"] for x in main_z_param_list]
    main_z_c_list = [x["c"] for x in main_z_param_list]
    main_z_d_list = [x["d"] for x in main_z_param_list]

    sub_id_list = merge_id_list_3 + merge_id_list_5
    sub_x_list = merge_x_list_3 + merge_x_list_5
    sub_y_list = merge_y_list_3 + merge_y_list_5
    sub_z_list = merge_z_list_3 + merge_z_list_5
    sub_z_param_list = merge_z_param_list_3 + merge_z_param_list_5
    sub_z_s_list = [x["s"] for x in sub_z_param_list]
    sub_z_a_list = [x["a"] for x in sub_z_param_list]
    sub_z_b_list = [x["b"] for x in sub_z_param_list]
    sub_z_c_list = [x["c"] for x in sub_z_param_list]
    sub_z_d_list = [x["d"] for x in sub_z_param_list]

    # データフレームの辞書設定
    mian_df_polyline_dict = dict(
        ID=main_id_list,
        X=main_x_list,
        Y=main_y_list,
        elev=main_z_list,
        elev_s=main_z_s_list,
        elev_a=main_z_a_list,
        elev_b=main_z_b_list,
        elev_c=main_z_c_list,
        elev_d=main_z_d_list,
    )

    sub_df_polyline_dict = dict(
        ID=sub_id_list,
        X=sub_x_list,
        Y=sub_y_list,
        elev=sub_z_list,
        elev_s=sub_z_s_list,
        elev_a=sub_z_a_list,
        elev_b=sub_z_b_list,
        elev_c=sub_z_c_list,
        elev_d=sub_z_d_list,
    )

    main_df_polyline = pd.DataFrame(data=mian_df_polyline_dict)
    sub_df_polyline = pd.DataFrame(data=sub_df_polyline_dict)

    # main_df_polyline = pd.read_csv(r"AutoXodr\input_data\main_road.csv")
    # sub_df_polyline = pd.read_csv(r"AutoXodr\input_data\sub_road.csv")

    main_df_polyline, main_hdg_list_merge = ajust.add_curvature_info(main_df_polyline, hdg_start_main_merge)
    sub_df_polyline, sub_hdg_list_merge= ajust.add_curvature_info(sub_df_polyline, hdg_start_sub_merge, hdg_end_sub_merge)

    # （根本的な解決が必要な箇所）
    # 本線と加速車線でラジアン方位(hdg)の値が意味的には同じだが異なる（例：１degと361degの関係）←これがOpenDriveとして読み込ませる際に悪さをする
    # 以下はその一時対応

    # 本線の合流差路中心のラジアン方位を抽出する
    # base_hdg_id = 22
    base_hdg_id = len(merge_id_list_0 + merge_id_list_4) + 1
    base_hdg = main_df_polyline["hdg"][base_hdg_id]  # サンプルの差路中心
    base_hdg_sub_id = len(sub_df_polyline["hdg"]) - 1  # 加速車線の末尾＝差路中心
    base_hdg_sub = sub_df_polyline["hdg"][base_hdg_sub_id]

    # 180度以上方位に差がある＝ラジアン方位のスケールが違う。その場合は比較結果で場合分けして+-piを適用する
    if math.pi <= abs(base_hdg - base_hdg_sub):
        if base_hdg > base_hdg_sub:
            sub_df_polyline["hdg"] = [
                x + 2 * math.pi for x in sub_df_polyline["hdg"]
            ]
        elif base_hdg < base_hdg_sub:
            sub_df_polyline["hdg"] = [
                x - 2 * math.pi for x in sub_df_polyline["hdg"]
            ]
        else:
            pass

    out_df = pd.concat([main_df_polyline, sub_df_polyline])
    df_polyline_new =  out_df.reset_index(drop=True)
# endregion


    df_junction["junction_id"] = df_junction["junction_id"] + 1

    df_junction_new = df_junction


    merge_id_list = df_lane_info["road_id"].tolist()

    merge_id_list_0 = []
    merge_id_list_4 = []
    merge_id_list_1 = []
    merge_id_list_2 = []
    merge_id_list_3 = []
    merge_id_list_5 = []

    for i in range(len(merge_id_list)):
        if merge_id_list[i] == 0:
            merge_id_list_0 += [0]
        elif merge_id_list[i] == 1:
            merge_id_list_1 += [1]
        elif merge_id_list[i] == 2:
            merge_id_list_2 += [2]
        elif merge_id_list[i] == 3:
            merge_id_list_3 += [3]
        elif merge_id_list[i] == 4:
            merge_id_list_4 += [4]
        elif merge_id_list[i] == 5:
            merge_id_list_5 += [5]

    main_lane_num0 = len(merge_id_list_0) - 1
    main_lane_num1 = len(merge_id_list_2) - 1
    sub_lane_num = len(merge_id_list_3) - 1

    merge_id_num_0 = len(merge_id_list_0)
    merge_id_num_4 = len(merge_id_list_4) + len(merge_id_list_0)
    merge_id_num_1 = len(merge_id_list_1) + len(merge_id_list_4) + len(merge_id_list_0)
    merge_id_num_2 = len(merge_id_list_2) + len(merge_id_list_1) + len(merge_id_list_4) + len(merge_id_list_0)
    merge_id_num_3 = len(merge_id_list_3) + len(merge_id_list_2) + len(merge_id_list_1) + len(merge_id_list_4) + len(merge_id_list_0)
    merge_id_num_5 = len(merge_id_list)

    merge_offset_list = df_lane_info["offset"].tolist()

    if merge_offset_list[merge_id_num_2-1] == merge_offset_list[merge_id_num_1-1]:
        merge_direction = 0
    else:
        merge_direction = 1

    df_lane_info_new = make_df_lane_info_merge(main_lane_num0, main_lane_num1, sub_lane_num, merge_direction)

    return df_polyline_new, df_junction_new, df_lane_info_new

def make_df_lane_info_branch(main_lane_num0, main_lane_num1, sub_lane_num, branch_direction):

    main_lane_width0 = 3.5
    main_lane_width1 = 3.5
    sub_lane_width = 3.5

    road_id_list_0 = [0] * (main_lane_num0 + 1)
    road_id_list_4 = [4] * (main_lane_num0 + 1)
    road_id_list_1 = [1] * (main_lane_num0 + sub_lane_num + 1)
    road_id_list_6 = [6] * (main_lane_num1 + 1)
    road_id_list_2 = [2] * (main_lane_num1 + 1)
    road_id_list_3 = [3] * (sub_lane_num + 1)
    road_id_list_5 = [5] * (sub_lane_num + 1)

    junction_id_list_0 = [-1] * (main_lane_num0 + 1)
    junction_id_list_4 = [7] * (main_lane_num0 + 1)
    junction_id_list_1 = [-1] * (main_lane_num0 + sub_lane_num + 1)
    junction_id_list_6 = [-1] * (main_lane_num1 + 1)
    junction_id_list_2 = [-1] * (main_lane_num1 + 1)
    junction_id_list_3 = [-1] * (sub_lane_num + 1)
    junction_id_list_5 = [7] * (sub_lane_num + 1)

    p_road_type_list_0 = [""] * (main_lane_num0 + 1)
    p_road_type_list_4 = [""] * (main_lane_num0 + 1)
    p_road_type_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    p_road_type_list_6 = [""] * (main_lane_num1 + 1)
    p_road_type_list_2 = [""] * (main_lane_num1 + 1)
    p_road_type_list_3 = [""] * (sub_lane_num + 1)
    p_road_type_list_5 = [""] * (sub_lane_num + 1)

    road_predecessor_id_list_0 = [""] * (main_lane_num0 + 1)
    road_predecessor_id_list_4 = [""] * (main_lane_num0 + 1)
    road_predecessor_id_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    road_predecessor_id_list_6 = [""] * (main_lane_num1 + 1)
    road_predecessor_id_list_2 = [""] * (main_lane_num1 + 1)
    road_predecessor_id_list_3 = [""] * (sub_lane_num + 1)
    road_predecessor_id_list_5 = [""] * (sub_lane_num + 1)

    p_contact_point_list_0 = [""] * (main_lane_num0 + 1)
    p_contact_point_list_4 = [""] * (main_lane_num0 + 1)
    p_contact_point_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    p_contact_point_list_6 = [""] * (main_lane_num1 + 1)
    p_contact_point_list_2 = [""] * (main_lane_num1 + 1)
    p_contact_point_list_3 = [""] * (sub_lane_num + 1)
    p_contact_point_list_5 = [""] * (sub_lane_num + 1)

    s_road_type_list_0 = [""] * (main_lane_num0 + 1)
    s_road_type_list_4 = [""] * (main_lane_num0 + 1)
    s_road_type_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    s_road_type_list_6 = [""] * (main_lane_num1 + 1)
    s_road_type_list_2 = [""] * (main_lane_num1 + 1)
    s_road_type_list_3 = [""] * (sub_lane_num + 1)
    s_road_type_list_5 = [""] * (sub_lane_num + 1)

    road_successor_id_list_0 = [""] * (main_lane_num0 + 1)
    road_successor_id_list_4 = [""] * (main_lane_num0 + 1)
    road_successor_id_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    road_successor_id_list_6 = [""] * (main_lane_num1 + 1)
    road_successor_id_list_2 = [""] * (main_lane_num1 + 1)
    road_successor_id_list_3 = [""] * (sub_lane_num + 1)
    road_successor_id_list_5 = [""] * (sub_lane_num + 1)

    s_contact_point_list_0 = [""] * (main_lane_num0 + 1)
    s_contact_point_list_4 = [""] * (main_lane_num0 + 1)
    s_contact_point_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    s_contact_point_list_6 = [""] * (main_lane_num1 + 1)
    s_contact_point_list_2 = [""] * (main_lane_num1 + 1)
    s_contact_point_list_3 = [""] * (sub_lane_num + 1)
    s_contact_point_list_5 = [""] * (sub_lane_num + 1)

    offset_list_0 = [-main_lane_width0 * main_lane_num0] * (
        main_lane_num0 + 1
    )
    offset_list_4 = [-main_lane_width0 * main_lane_num0] * (
        main_lane_num0 + 1
    )
    offset_list_1 = [-main_lane_width1 * main_lane_num0] * (
        main_lane_num0 + sub_lane_num + 1
    )

    if branch_direction == 0:
        offset_list_2 = [-main_lane_width1 * main_lane_num0] * (
            main_lane_num1 + 1
        )
    else:
        offset_list_2 = [
            -main_lane_width1
            * (
                main_lane_num0
                - (main_lane_num0 + sub_lane_num - main_lane_num1)
            )
        ] * (main_lane_num1 + 1)

    offset_list_6 = offset_list_2

    offset_list_3 = [0] * (sub_lane_num + 1)
    offset_list_5 = [0] * (sub_lane_num + 1)

    #
    lane_change_list_0 = ["none"]
    for i in range(main_lane_num0 - 1):
        lane_change_list_0.append("both")
    lane_change_list_0.append("none")

    lane_change_list_4 = ["none"]
    for i in range(main_lane_num0 - 1):
        lane_change_list_4.append("both")
    lane_change_list_4.append("none")

    lane_change_list_1 = ["none"]
    for i in range(main_lane_num0 + sub_lane_num - 1):
        lane_change_list_1.append("both")
    lane_change_list_1.append("none")

    lane_change_list_6 = ["none"]
    for i in range(main_lane_num1 - 1):
        lane_change_list_6.append("both")
    lane_change_list_6.append("none")

    lane_change_list_2 = ["none"]
    for i in range(main_lane_num1 - 1):
        lane_change_list_2.append("both")
    lane_change_list_2.append("none")

    lane_change_list_3 = ["none"]
    for i in range(sub_lane_num - 1):
        lane_change_list_3.append("both")
    lane_change_list_3.append("none")

    lane_change_list_5 = ["none"]
    for i in range(sub_lane_num - 1):
        lane_change_list_5.append("both")
    lane_change_list_5.append("none")

    direction_list_0 = ["left"] * (main_lane_num0) + ["center"]
    direction_list_4 = ["left"] * (main_lane_num0) + ["center"]
    direction_list_1 = ["left"] * (main_lane_num0 + sub_lane_num) + ["center"]
    direction_list_6 = ["left"] * (main_lane_num1) + ["center"]
    direction_list_2 = ["left"] * (main_lane_num1) + ["center"]
    direction_list_3 = ["left"] * (sub_lane_num) + ["center"]
    direction_list_5 = ["left"] * (sub_lane_num) + ["center"]

    #
    lane_id_list_0 = []
    for i in range(main_lane_num0 + 1):
        lane_id_list_0.append(main_lane_num0 - i)

    lane_id_list_4 = []
    for i in range(main_lane_num0 + 1):
        lane_id_list_4.append(main_lane_num0 - i)

    lane_id_list_1 = []
    for i in range(main_lane_num0 + sub_lane_num + 1):
        lane_id_list_1.append(main_lane_num0 + sub_lane_num - i)

    lane_id_list_6 = []
    for i in range(main_lane_num1 + 1):
        lane_id_list_6.append(main_lane_num1 - i)

    lane_id_list_2 = []
    for i in range(main_lane_num1 + 1):
        lane_id_list_2.append(main_lane_num1 - i)

    lane_id_list_3 = []
    for i in range(sub_lane_num + 1):
        lane_id_list_3.append(sub_lane_num - i)

    lane_id_list_5 = []
    for i in range(sub_lane_num + 1):
        lane_id_list_5.append(sub_lane_num - i)

    # 一時敵に格納
    lane_successor_list_0 = [""] * (main_lane_num0 + 1)

    lane_successor_list_4 = []
    for i in range(main_lane_num0):
        lane_successor_list_4.append(main_lane_num0 - i)
    lane_successor_list_4.append("")

    lane_successor_list_1 = []
    for i in range(sub_lane_num):
        lane_successor_list_1.append(sub_lane_num - i)
    for i in range(main_lane_num0):
        lane_successor_list_1.append(main_lane_num0 - i)
    lane_successor_list_1.append("")

    lane_successor_list_6 = []
    if branch_direction == 0:
        for i in range(main_lane_num1):
            lane_successor_list_6.insert(0, i + 1)
    else:
        for i in range(main_lane_num1):
            lane_successor_list_6.append(sub_lane_num + main_lane_num0 - i)
    lane_successor_list_6.append("")

    lane_successor_list_2 = []
    for i in range(main_lane_num1):
        lane_successor_list_2.insert(0,i+1)
    lane_successor_list_2.append('')

    lane_successor_list_3 = [""] * (sub_lane_num + 1)

    lane_successor_list_5 = []
    for i in range(sub_lane_num):
        lane_successor_list_5.append(sub_lane_num - i)
    lane_successor_list_5.append("")

    lane_predecessor_list_0 = []
    for i in range(main_lane_num0):
        lane_predecessor_list_0.append(main_lane_num0 - i)
    lane_predecessor_list_0.append("")

    lane_predecessor_list_4 = []
    for i in range(main_lane_num0):
        lane_predecessor_list_4.append(main_lane_num0 - i)
    lane_predecessor_list_4.append("")

    lane_predecessor_list_1 = [""] * (main_lane_num0 + sub_lane_num)
    if branch_direction == 0:
        for i in range(main_lane_num1):
            lane_predecessor_list_1[
                main_lane_num0 + sub_lane_num - 1 - i
            ] = (i + 1)
    else:
        for i in range(main_lane_num1):
            lane_predecessor_list_1[i] = main_lane_num1 - i
    lane_predecessor_list_1.append("")

    lane_predecessor_list_6 = ['']*(main_lane_num1)
    for i in range(main_lane_num1):
            lane_predecessor_list_6[main_lane_num1-1-i] = i+1
    lane_predecessor_list_6.append('')

    lane_predecessor_list_2 = [""] * (main_lane_num1 + 1)

    lane_predecessor_list_3 = []
    for i in range(sub_lane_num):
        lane_predecessor_list_3.append(sub_lane_num - i)
    lane_predecessor_list_3.append("")

    lane_predecessor_list_5 = []
    for i in range(sub_lane_num):
        lane_predecessor_list_5.append(main_lane_num0 + sub_lane_num - i)
    lane_predecessor_list_5.append("")

    #
    lane_width_list_0 = [main_lane_width0] * main_lane_num0 + [0.125]
    lane_width_list_4 = [main_lane_width0] * main_lane_num0 + [0.125]
    lane_width_list_1 = [main_lane_width1] * (main_lane_num0 + sub_lane_num) + [0.125]
    lane_width_list_6 = [main_lane_width1] * main_lane_num1 + [0.125]
    lane_width_list_2 = [main_lane_width1] * main_lane_num1 + [0.125]
    lane_width_list_3 = [sub_lane_width] * sub_lane_num + [0.125]
    lane_width_list_5 = [sub_lane_width] * sub_lane_num + [0.125]

    #
    type_list_0 = ["solid"]
    for i in range(main_lane_num0 - 1):
        type_list_0.append("broken")
    type_list_0.append("solid")

    type_list_4 = ["solid"]
    for i in range(main_lane_num0 - 1):
        type_list_4.append("broken")
    type_list_4.append("solid")

    type_list_1 = ["solid"]
    for i in range(main_lane_num0 + sub_lane_num - 1):
        type_list_1.append("broken")
    type_list_1.append("solid")

    type_list_6 = ["solid"]
    for i in range(main_lane_num1 - 1):
        type_list_6.append("broken")
    type_list_6.append("solid")

    type_list_2 = ["solid"]
    for i in range(main_lane_num1 - 1):
        type_list_2.append("broken")
    type_list_2.append("solid")

    type_list_3 = ["solid"]
    for i in range(sub_lane_num - 1):
        type_list_3.append("broken")
    type_list_3.append("solid")

    type_list_5 = ["solid"]
    for i in range(sub_lane_num - 1):
        type_list_5.append("broken")
    type_list_5.append("solid")

    #
    length_list_0 = [10]
    for i in range(main_lane_num0 - 1):
        length_list_0.append(5)
    length_list_0.append(10)

    length_list_4 = [10]
    for i in range(main_lane_num0 - 1):
        length_list_4.append(5)
    length_list_4.append(10)

    length_list_1 = [10]
    for i in range(main_lane_num0 + sub_lane_num - 1):
        length_list_1.append(5)
    length_list_1.append(10)

    length_list_6 = [10]
    for i in range(main_lane_num1 - 1):
        length_list_6.append(5)
    length_list_6.append(10)

    length_list_2 = [10]
    for i in range(main_lane_num1 - 1):
        length_list_2.append(5)
    length_list_2.append(10)

    length_list_3 = [10]
    for i in range(sub_lane_num - 1):
        length_list_3.append(5)
    length_list_3.append(10)

    length_list_5 = [10]
    for i in range(sub_lane_num - 1):
        length_list_5.append(5)
    length_list_5.append(10)

    #
    space_list_0 = [0]
    for i in range(main_lane_num0 - 1):
        space_list_0.append(5)
    space_list_0.append(0)

    space_list_4 = [0]
    for i in range(main_lane_num0 - 1):
        space_list_4.append(5)
    space_list_4.append(0)

    space_list_1 = [0]
    for i in range(main_lane_num0 + sub_lane_num - 1):
        space_list_1.append(5)
    space_list_1.append(0)

    space_list_6 = [0]
    for i in range(main_lane_num1 - 1):
        space_list_6.append(5)
    space_list_6.append(0)

    space_list_2 = [0]
    for i in range(main_lane_num1 - 1):
        space_list_2.append(5)
    space_list_2.append(0)

    space_list_3 = [0]
    for i in range(sub_lane_num - 1):
        space_list_3.append(5)
    space_list_3.append(0)

    space_list_5 = [0]
    for i in range(sub_lane_num - 1):
        space_list_5.append(5)
    space_list_5.append(0)

    # 五藤さんと要相談
    speed_list_0 = [80] * (main_lane_num0 + 1)
    speed_list_4 = [80] * (main_lane_num0 + 1)
    speed_list_1 = [80] * (main_lane_num0 + sub_lane_num + 1)
    speed_list_6 = [80] * (main_lane_num1 + 1)
    speed_list_2 = [80] * (main_lane_num1 + 1)
    speed_list_3 = [80] * (sub_lane_num + 1)
    speed_list_5 = [80] * (sub_lane_num + 1)

    unit_list_0 = ["km/h"] * (main_lane_num0 + 1)
    unit_list_4 = ["km/h"] * (main_lane_num0 + 1)
    unit_list_1 = ["km/h"] * (main_lane_num0 + sub_lane_num + 1)
    unit_list_6 = ["km/h"] * (main_lane_num1 + 1)
    unit_list_2 = ["km/h"] * (main_lane_num1 + 1)
    unit_list_3 = ["km/h"] * (sub_lane_num + 1)
    unit_list_5 = ["km/h"] * (sub_lane_num + 1)

    road_id_list = (
        road_id_list_2
        + road_id_list_6
        + road_id_list_1
        + road_id_list_4
        + road_id_list_0
        + road_id_list_5
        + road_id_list_3
    )
    junction_id_list = (
        junction_id_list_2
        + junction_id_list_6
        + junction_id_list_1
        + junction_id_list_4
        + junction_id_list_0
        + junction_id_list_5
        + junction_id_list_3
    )
    p_road_type_list = (
        p_road_type_list_2
        + p_road_type_list_6
        + p_road_type_list_1
        + p_road_type_list_4
        + p_road_type_list_0
        + p_road_type_list_5
        + p_road_type_list_3
    )
    road_predecessor_id_list = (
        road_predecessor_id_list_2
        + road_predecessor_id_list_6
        + road_predecessor_id_list_1
        + road_predecessor_id_list_4
        + road_predecessor_id_list_0
        + road_predecessor_id_list_5
        + road_predecessor_id_list_3
    )
    p_contact_point_list = (
        p_contact_point_list_2
        + p_contact_point_list_6
        + p_contact_point_list_1
        + p_contact_point_list_4
        + p_contact_point_list_0
        + p_contact_point_list_5
        + p_contact_point_list_3
    )
    s_road_type_list = (
        s_road_type_list_2
        + s_road_type_list_6
        + s_road_type_list_1
        + s_road_type_list_4
        + s_road_type_list_0
        + s_road_type_list_5
        + s_road_type_list_3
    )
    road_successor_id_list = (
        road_successor_id_list_2
        + road_successor_id_list_6
        + road_successor_id_list_1
        + road_successor_id_list_4
        + road_successor_id_list_0
        + road_successor_id_list_5
        + road_successor_id_list_3
    )
    s_contact_point_list = (
        s_contact_point_list_2
        + s_contact_point_list_6
        + s_contact_point_list_1
        + s_contact_point_list_4
        + s_contact_point_list_0
        + s_contact_point_list_5
        + s_contact_point_list_3
    )
    offset_list = (
        offset_list_2
        + offset_list_6
        + offset_list_1
        + offset_list_4
        + offset_list_0
        + offset_list_5
        + offset_list_3
    )
    lane_change_list = (
        lane_change_list_2
        + lane_change_list_6
        + lane_change_list_1
        + lane_change_list_4
        + lane_change_list_0
        + lane_change_list_5
        + lane_change_list_3
    )
    direction_list = (
        direction_list_2
        + direction_list_6
        + direction_list_1
        + direction_list_4
        + direction_list_0
        + direction_list_5
        + direction_list_3
    )
    lane_id_list = (
        lane_id_list_2
        + lane_id_list_6
        + lane_id_list_1
        + lane_id_list_4
        + lane_id_list_0
        + lane_id_list_5
        + lane_id_list_3
    )
    lane_predecessor_list = (
        lane_predecessor_list_2
        + lane_predecessor_list_6
        + lane_predecessor_list_1
        + lane_predecessor_list_4
        + lane_predecessor_list_0
        + lane_predecessor_list_5
        + lane_predecessor_list_3
    )
    lane_successor_list = (
        lane_successor_list_2
        + lane_successor_list_6
        + lane_successor_list_1
        + lane_successor_list_4
        + lane_successor_list_0
        + lane_successor_list_5
        + lane_successor_list_3
    )
    lane_width_list = (
        lane_width_list_2
        + lane_width_list_6
        + lane_width_list_1
        + lane_width_list_4
        + lane_width_list_0
        + lane_width_list_5
        + lane_width_list_3
    )
    type_list = (
        type_list_2
        + type_list_6
        + type_list_1
        + type_list_4
        + type_list_0
        + type_list_5
        + type_list_3
    )
    length_list = (
        length_list_2
        + length_list_6
        + length_list_1
        + length_list_4
        + length_list_0
        + length_list_5
        + length_list_3
    )
    space_list = (
        space_list_2
        + space_list_6
        + space_list_1
        + space_list_4
        + space_list_0
        + space_list_5
        + space_list_3
    )
    speed_list = (
        speed_list_2
        + speed_list_6
        + speed_list_1
        + speed_list_4
        + speed_list_0
        + speed_list_5
        + speed_list_3
    )
    unit_list = (
        unit_list_2
        + unit_list_6
        + unit_list_1
        + unit_list_4
        + unit_list_0
        + unit_list_5
        + unit_list_3
    )

    """
    print(len(road_id_list))
    print(len(junction_id_list))
    print(len(p_road_type_list))
    print(len(road_predecessor_id_list))
    print(len(s_road_type_list))
    print(len(road_successor_id_list))
    print(len(s_contact_point_list))
    print(len(offset_list))
    print(len(lane_change_list))
    print(len(direction_list))
    print(len(lane_id_list))
    print(len(lane_predecessor_list))
    print(len(lane_successor_list))
    print(len(lane_width_list))
    print(len(type_list))
    print(len(length_list))
    print(len(space_list))
    print(len(speed_list))
    print(len(unit_list))
    """

    # データフレームの辞書設定
    df_laneinfo_dict = dict(
        road_id=road_id_list,
        junction_id=junction_id_list,
        p_road_type=p_road_type_list,
        road_predecessor_id=road_predecessor_id_list,
        p_contact_point=p_contact_point_list,
        s_road_type=s_road_type_list,
        road_successor_id=road_successor_id_list,
        s_contact_point=s_contact_point_list,
        offset=offset_list,
        lane_change=lane_change_list,
        direction=direction_list,
        lane_id=lane_id_list,
        lane_predecessor=lane_predecessor_list,
        lane_successor=lane_successor_list,
        lane_width=lane_width_list,
        type=type_list,
        length=length_list,
        space=space_list,
        speed=speed_list,
        unit=unit_list,
    )

    # データフレームの生成
    df_lane_info = pd.DataFrame(data=df_laneinfo_dict)
    # データフレームへ曲率情報を付与
    # print(self.df_lane_info)
    # self.df_lane_info.to_csv(r'AutoXodr\input_data\test\test_road_lane_info.csv')

    return df_lane_info

def make_df_lane_info_merge(main_lane_num0, main_lane_num1, sub_lane_num, merge_direction):

    main_lane_width0 = 3.5
    main_lane_width1 = 3.5
    sub_lane_width = 3.5

    road_id_list_0 = [0]*(main_lane_num0+1)
    road_id_list_4 = [4]*(main_lane_num0+1)
    road_id_list_1 = [1]*(main_lane_num0+sub_lane_num+1)
    road_id_list_6 = [6]*(main_lane_num1+1)
    road_id_list_2 = [2]*(main_lane_num1+1)
    road_id_list_3 = [3]*(sub_lane_num+1)
    road_id_list_5 = [5]*(sub_lane_num+1)

    junction_id_list_0 = [-1]*(main_lane_num0+1)
    junction_id_list_4 = [7]*(main_lane_num0+1)
    junction_id_list_1 = [-1]*(main_lane_num0+sub_lane_num+1)
    junction_id_list_6 = [-1]*(main_lane_num1+1)
    junction_id_list_2 = [-1]*(main_lane_num1+1)
    junction_id_list_3 = [-1]*(sub_lane_num+1)
    junction_id_list_5 = [7]*(sub_lane_num+1)

    p_road_type_list_0 = [""] * (main_lane_num0 + 1)
    p_road_type_list_4 = [""] * (main_lane_num0 + 1)
    p_road_type_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    p_road_type_list_6 = [""] * (main_lane_num1 + 1)
    p_road_type_list_2 = [""] * (main_lane_num1 + 1)
    p_road_type_list_3 = [""] * (sub_lane_num + 1)
    p_road_type_list_5 = [""] * (sub_lane_num + 1)

    road_predecessor_id_list_0 = [""] * (main_lane_num0 + 1)
    road_predecessor_id_list_4 = [""] * (main_lane_num0 + 1)
    road_predecessor_id_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    road_predecessor_id_list_6 = [""] * (main_lane_num1 + 1)
    road_predecessor_id_list_2 = [""] * (main_lane_num1 + 1)
    road_predecessor_id_list_3 = [""] * (sub_lane_num + 1)
    road_predecessor_id_list_5 = [""] * (sub_lane_num + 1)

    p_contact_point_list_0 = [""] * (main_lane_num0 + 1)
    p_contact_point_list_4 = [""] * (main_lane_num0 + 1)
    p_contact_point_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    p_contact_point_list_6 = [""] * (main_lane_num1 + 1)
    p_contact_point_list_2 = [""] * (main_lane_num1 + 1)
    p_contact_point_list_3 = [""] * (sub_lane_num + 1)
    p_contact_point_list_5 = [""] * (sub_lane_num + 1)

    s_road_type_list_0 = [""] * (main_lane_num0 + 1)
    s_road_type_list_4 = [""] * (main_lane_num0 + 1)
    s_road_type_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    s_road_type_list_6 = [""] * (main_lane_num1 + 1)
    s_road_type_list_2 = [""] * (main_lane_num1 + 1)
    s_road_type_list_3 = [""] * (sub_lane_num + 1)
    s_road_type_list_5 = [""] * (sub_lane_num + 1)

    road_successor_id_list_0 = [""] * (main_lane_num0 + 1)
    road_successor_id_list_4 = [""] * (main_lane_num0 + 1)
    road_successor_id_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    road_successor_id_list_6 = [""] * (main_lane_num1 + 1)
    road_successor_id_list_2 = [""] * (main_lane_num1 + 1)
    road_successor_id_list_3 = [""] * (sub_lane_num + 1)
    road_successor_id_list_5 = [""] * (sub_lane_num + 1)

    s_contact_point_list_0 = [""] * (main_lane_num0 + 1)
    s_contact_point_list_4 = [""] * (main_lane_num0 + 1)
    s_contact_point_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
    s_contact_point_list_6 = [""] * (main_lane_num1 + 1)
    s_contact_point_list_2 = [""] * (main_lane_num1 + 1)
    s_contact_point_list_3 = [""] * (sub_lane_num + 1)
    s_contact_point_list_5 = [""] * (sub_lane_num + 1)


    offset_list_0 = [-main_lane_width0 * main_lane_num0] * (
        main_lane_num0 + 1
    )
    offset_list_4 = [-main_lane_width0 * main_lane_num0] * (
        main_lane_num0 + 1
    )
    offset_list_1 = [-main_lane_width1 * main_lane_num0] * (
        main_lane_num0 + sub_lane_num + 1
    )
    if merge_direction == 0:
        offset_list_2 = [-main_lane_width1 * main_lane_num0] * (
            main_lane_num1 + 1
        )
    else:
        offset_list_2 = [
            -main_lane_width1
            * (
                main_lane_num0
                - (main_lane_num0 + sub_lane_num - main_lane_num1)
            )
        ] * (main_lane_num1 + 1)

    offset_list_6 = offset_list_2

    offset_list_3 = [0] * (sub_lane_num + 1)
    offset_list_5 = [0] * (sub_lane_num + 1)






    #
    lane_change_list_0 = ["none"]
    for i in range(main_lane_num0 - 1):
        lane_change_list_0.append("both")
    lane_change_list_0.append("none")

    lane_change_list_4 = ["none"]
    for i in range(main_lane_num0 - 1):
        lane_change_list_4.append("both")
    lane_change_list_4.append("none")

    lane_change_list_1 = ["none"]
    for i in range(main_lane_num0 + sub_lane_num - 1):
        lane_change_list_1.append("both")
    lane_change_list_1.append("none")

    lane_change_list_6=['none']
    for i in range(main_lane_num1-1):
        lane_change_list_6.append('both')
    lane_change_list_6.append('none')

    lane_change_list_2 = ["none"]
    for i in range(main_lane_num1 - 1):
        lane_change_list_2.append("both")
    lane_change_list_2.append("none")

    lane_change_list_3 = ["none"]
    for i in range(sub_lane_num - 1):
        lane_change_list_3.append("both")
    lane_change_list_3.append("none")

    lane_change_list_5 = ["none"]
    for i in range(sub_lane_num - 1):
        lane_change_list_5.append("both")
    lane_change_list_5.append("none")

    direction_list_0 = ["left"] * (main_lane_num0) + ["center"]
    direction_list_4 = ["left"] * (main_lane_num0) + ["center"]
    direction_list_1 = ["left"] * (main_lane_num0 + sub_lane_num) + [
        "center"
    ]
    direction_list_6 = ['left']*(main_lane_num1)+['center']
    direction_list_2 = ["left"] * (main_lane_num1) + ["center"]
    direction_list_3 = ["left"] * (sub_lane_num) + ["center"]
    direction_list_5 = ["left"] * (sub_lane_num) + ["center"]

    #
    lane_id_list_0 = []
    for i in range(main_lane_num0 + 1):
        lane_id_list_0.append(main_lane_num0 - i)

    lane_id_list_4 = []
    for i in range(main_lane_num0 + 1):
        lane_id_list_4.append(main_lane_num0 - i)

    lane_id_list_1 = []
    for i in range(main_lane_num0 + sub_lane_num + 1):
        lane_id_list_1.append(main_lane_num0 + sub_lane_num - i)

    lane_id_list_6=[]
    for i in range(main_lane_num1+1):
        lane_id_list_6.append(main_lane_num1-i)

    lane_id_list_2 = []
    for i in range(main_lane_num1 + 1):
        lane_id_list_2.append(main_lane_num1 - i)

    lane_id_list_3 = []
    for i in range(sub_lane_num + 1):
        lane_id_list_3.append(sub_lane_num - i)

    lane_id_list_5 = []
    for i in range(sub_lane_num + 1):
        lane_id_list_5.append(sub_lane_num - i)

    # 一時敵に格納
    lane_predecessor_list_0 = [""] * (main_lane_num0 + 1)

    lane_predecessor_list_4 = []
    for i in range(main_lane_num0):
        lane_predecessor_list_4.append(main_lane_num0 - i)
    lane_predecessor_list_4.append("")

    lane_predecessor_list_1 = []
    for i in range(sub_lane_num):
        lane_predecessor_list_1.append(sub_lane_num - i)
    for i in range(main_lane_num0):
        lane_predecessor_list_1.append(main_lane_num0 - i)
    lane_predecessor_list_1.append("")

    lane_predecessor_list_6 = []
    if merge_direction == 0:
        for i in range(main_lane_num1):
            lane_predecessor_list_6.insert(0,i+1)
    else:
        for i in range(main_lane_num1):
            lane_predecessor_list_6.append(sub_lane_num+main_lane_num0-i)
    lane_predecessor_list_6.append('')

    lane_predecessor_list_2 = []
    for i in range(main_lane_num1):
        lane_predecessor_list_2.insert(0,i+1)
    lane_predecessor_list_2.append('')

    lane_predecessor_list_3 = [""] * (sub_lane_num + 1)

    lane_predecessor_list_5 = []
    for i in range(sub_lane_num):
        lane_predecessor_list_5.append(sub_lane_num - i)
    lane_predecessor_list_5.append("")

    lane_successor_list_0 = []
    for i in range(main_lane_num0):
        lane_successor_list_0.append(main_lane_num0 - i)
    lane_successor_list_0.append("")

    lane_successor_list_4 = []
    for i in range(main_lane_num0):
        lane_successor_list_4.append(main_lane_num0 - i)
    lane_successor_list_4.append("")

    lane_successor_list_1 = [""] * (main_lane_num0 + sub_lane_num)
    if merge_direction == 0:
        for i in range(main_lane_num1):
            lane_successor_list_1[main_lane_num0 + sub_lane_num - 1 - i] = (
                i + 1
            )
    else:
        for i in range(main_lane_num1):
            lane_successor_list_1[i] = main_lane_num1 - i
    lane_successor_list_1.append("")

    lane_successor_list_6 = ['']*(main_lane_num1)
    for i in range(main_lane_num1):
            lane_successor_list_6[main_lane_num1-1-i] = i+1
    lane_successor_list_6.append('')

    lane_successor_list_2 = [""] * (main_lane_num1 + 1)

    lane_successor_list_3 = []
    for i in range(sub_lane_num):
        lane_successor_list_3.append(sub_lane_num - i)
    lane_successor_list_3.append("")

    lane_successor_list_5 = []
    for i in range(sub_lane_num):
        lane_successor_list_5.append(main_lane_num0 + sub_lane_num - i)
    lane_successor_list_5.append("")

    #
    lane_width_list_0 = [main_lane_width0] * main_lane_num0 + [0.125]
    lane_width_list_4 = [main_lane_width0] * main_lane_num0 + [0.125]
    lane_width_list_1 = [main_lane_width1] * (
        main_lane_num0 + sub_lane_num
    ) + [0.125]
    lane_width_list_6 = [main_lane_width1]*(main_lane_num1) + [0.125]
    lane_width_list_2 = [main_lane_width1] * main_lane_num1 + [0.125]
    lane_width_list_3 = [sub_lane_width] * sub_lane_num + [0.125]
    lane_width_list_5 = [sub_lane_width] * sub_lane_num + [0.125]

    #
    type_list_0 = ["solid"]
    for i in range(main_lane_num0 - 1):
        type_list_0.append("broken")
    type_list_0.append("solid")

    type_list_4 = ["solid"]
    for i in range(main_lane_num0 - 1):
        type_list_4.append("broken")
    type_list_4.append("solid")

    type_list_1 = ["solid"]
    for i in range(main_lane_num0 + sub_lane_num - 1):
        type_list_1.append("broken")
    type_list_1.append("solid")

    type_list_6=['solid']
    for i in range(main_lane_num1-1):
        type_list_6.append('broken')
    type_list_6.append('solid')

    type_list_2 = ["solid"]
    for i in range(main_lane_num1 - 1):
        type_list_2.append("broken")
    type_list_2.append("solid")

    type_list_3 = ["solid"]
    for i in range(sub_lane_num - 1):
        type_list_3.append("broken")
    type_list_3.append("solid")

    type_list_5 = ["solid"]
    for i in range(sub_lane_num - 1):
        type_list_5.append("broken")
    type_list_5.append("solid")

    #
    length_list_0 = [10]
    for i in range(main_lane_num0 - 1):
        length_list_0.append(5)
    length_list_0.append(10)

    length_list_4 = [10]
    for i in range(main_lane_num0 - 1):
        length_list_4.append(5)
    length_list_4.append(10)

    length_list_1 = [10]
    for i in range(main_lane_num0 + sub_lane_num - 1):
        length_list_1.append(5)
    length_list_1.append(10)

    length_list_6=[10]
    for i in range(main_lane_num1-1):
        length_list_6.append(5)
    length_list_6.append(10)

    length_list_2 = [10]
    for i in range(main_lane_num1 - 1):
        length_list_2.append(5)
    length_list_2.append(10)

    length_list_3 = [10]
    for i in range(sub_lane_num - 1):
        length_list_3.append(5)
    length_list_3.append(10)

    length_list_5 = [10]
    for i in range(sub_lane_num - 1):
        length_list_5.append(5)
    length_list_5.append(10)

    #
    space_list_0 = [0]
    for i in range(main_lane_num0 - 1):
        space_list_0.append(5)
    space_list_0.append(0)

    space_list_4 = [0]
    for i in range(main_lane_num0 - 1):
        space_list_4.append(5)
    space_list_4.append(0)

    space_list_1 = [0]
    for i in range(main_lane_num0 + sub_lane_num - 1):
        space_list_1.append(5)
    space_list_1.append(0)

    space_list_6=[0]
    for i in range(main_lane_num1-1):
        space_list_6.append(5)
    space_list_6.append(0)

    space_list_2 = [0]
    for i in range(main_lane_num1 - 1):
        space_list_2.append(5)
    space_list_2.append(0)

    space_list_3 = [0]
    for i in range(sub_lane_num - 1):
        space_list_3.append(5)
    space_list_3.append(0)

    space_list_5 = [0]
    for i in range(sub_lane_num - 1):
        space_list_5.append(5)
    space_list_5.append(0)

    # 五藤さんと要相談
    speed_list_0 = [80] * (main_lane_num0 + 1)
    speed_list_4 = [80] * (main_lane_num0 + 1)
    speed_list_1 = [80] * (main_lane_num0 + sub_lane_num + 1)
    speed_list_6 = [80] * (main_lane_num1 + 1)
    speed_list_2 = [80] * (main_lane_num1 + 1)
    speed_list_3 = [80] * (sub_lane_num + 1)
    speed_list_5 = [80] * (sub_lane_num + 1)

    unit_list_0 = ["km/h"] * (main_lane_num0 + 1)
    unit_list_4 = ["km/h"] * (main_lane_num0 + 1)
    unit_list_1 = ["km/h"] * (main_lane_num0 + sub_lane_num + 1)
    unit_list_6 = ['km/h'] * (main_lane_num1 + 1)
    unit_list_2 = ["km/h"] * (main_lane_num1 + 1)
    unit_list_3 = ["km/h"] * (sub_lane_num + 1)
    unit_list_5 = ["km/h"] * (sub_lane_num + 1)

    road_id_list = (
        road_id_list_0
        + road_id_list_4
        + road_id_list_1
        + road_id_list_6
        + road_id_list_2
        + road_id_list_3
        + road_id_list_5
    )
    junction_id_list = (
        junction_id_list_0
        + junction_id_list_4
        + junction_id_list_1
        + junction_id_list_6
        + junction_id_list_2
        + junction_id_list_3
        + junction_id_list_5
    )
    p_road_type_list = (
        p_road_type_list_0
        + p_road_type_list_4
        + p_road_type_list_1
        + p_road_type_list_6
        + p_road_type_list_2
        + p_road_type_list_3
        + p_road_type_list_5
    )
    road_predecessor_id_list = (
        road_predecessor_id_list_0
        + road_predecessor_id_list_4
        + road_predecessor_id_list_1
        + road_predecessor_id_list_6
        + road_predecessor_id_list_2
        + road_predecessor_id_list_3
        + road_predecessor_id_list_5
    )
    p_contact_point_list = (
        p_contact_point_list_0
        + p_contact_point_list_4
        + p_contact_point_list_1
        + p_contact_point_list_6
        + p_contact_point_list_2
        + p_contact_point_list_3
        + p_contact_point_list_5
    )
    s_road_type_list = (
        s_road_type_list_0
        + s_road_type_list_4
        + s_road_type_list_1
        + s_road_type_list_6
        + s_road_type_list_2
        + s_road_type_list_3
        + s_road_type_list_5
    )
    road_successor_id_list = (
        road_successor_id_list_0
        + road_successor_id_list_4
        + road_successor_id_list_1
        + road_successor_id_list_6
        + road_successor_id_list_2
        + road_successor_id_list_3
        + road_successor_id_list_5
    )
    s_contact_point_list = (
        s_contact_point_list_0
        + s_contact_point_list_4
        + s_contact_point_list_1
        + s_contact_point_list_6
        + s_contact_point_list_2
        + s_contact_point_list_3
        + s_contact_point_list_5
    )
    offset_list = (
        offset_list_0
        + offset_list_4
        + offset_list_1
        + offset_list_6
        + offset_list_2
        + offset_list_3
        + offset_list_5
    )
    lane_change_list = (
        lane_change_list_0
        + lane_change_list_4
        + lane_change_list_1
        + lane_change_list_6
        + lane_change_list_2
        + lane_change_list_3
        + lane_change_list_5
    )
    direction_list = (
        direction_list_0
        + direction_list_4
        + direction_list_1
        + direction_list_6
        + direction_list_2
        + direction_list_3
        + direction_list_5
    )
    lane_id_list = (
        lane_id_list_0
        + lane_id_list_4
        + lane_id_list_1
        + lane_id_list_6
        + lane_id_list_2
        + lane_id_list_3
        + lane_id_list_5
    )
    lane_predecessor_list = (
        lane_predecessor_list_0
        + lane_predecessor_list_4
        + lane_predecessor_list_1
        + lane_predecessor_list_6
        + lane_predecessor_list_2
        + lane_predecessor_list_3
        + lane_predecessor_list_5
    )
    lane_successor_list = (
        lane_successor_list_0
        + lane_successor_list_4
        + lane_successor_list_1
        + lane_successor_list_6
        + lane_successor_list_2
        + lane_successor_list_3
        + lane_successor_list_5
    )
    lane_width_list = (
        lane_width_list_0
        + lane_width_list_4
        + lane_width_list_1
        + lane_width_list_6
        + lane_width_list_2
        + lane_width_list_3
        + lane_width_list_5
    )
    type_list = (
        type_list_0
        + type_list_4
        + type_list_1
        + type_list_6
        + type_list_2
        + type_list_3
        + type_list_5
    )
    length_list = (
        length_list_0
        + length_list_4
        + length_list_1
        + length_list_6
        + length_list_2
        + length_list_3
        + length_list_5
    )
    space_list = (
        space_list_0
        + space_list_4
        + space_list_1
        + space_list_6
        + space_list_2
        + space_list_3
        + space_list_5
    )
    speed_list = (
        speed_list_0
        + speed_list_4
        + speed_list_1
        + speed_list_6
        + speed_list_2
        + speed_list_3
        + speed_list_5
    )
    unit_list = (
        unit_list_0
        + unit_list_4
        + unit_list_1
        + unit_list_6
        + unit_list_2
        + unit_list_3
        + unit_list_5
    )

    """
    print(len(road_id_list))
    print(len(junction_id_list))
    print(len(p_road_type_list))
    print(len(road_predecessor_id_list))
    print(len(s_road_type_list))
    print(len(road_successor_id_list))
    print(len(s_contact_point_list))
    print(len(offset_list))
    print(len(lane_change_list))
    print(len(direction_list))
    print(len(lane_id_list))
    print(len(lane_predecessor_list))
    print(len(lane_successor_list))
    print(len(lane_width_list))
    print(len(type_list))
    print(len(length_list))
    print(len(space_list))
    print(len(speed_list))
    print(len(unit_list))
    """

    # データフレームの辞書設定
    df_laneinfo_dict = dict(
        road_id=road_id_list,
        junction_id=junction_id_list,
        p_road_type=p_road_type_list,
        road_predecessor_id=road_predecessor_id_list,
        p_contact_point=p_contact_point_list,
        s_road_type=s_road_type_list,
        road_successor_id=road_successor_id_list,
        s_contact_point=s_contact_point_list,
        offset=offset_list,
        lane_change=lane_change_list,
        direction=direction_list,
        lane_id=lane_id_list,
        lane_predecessor=lane_predecessor_list,
        lane_successor=lane_successor_list,
        lane_width=lane_width_list,
        type=type_list,
        length=length_list,
        space=space_list,
        speed=speed_list,
        unit=unit_list,
    )

    # データフレームの生成
    df_lane_info = pd.DataFrame(data=df_laneinfo_dict)
    # データフレームへ曲率情報を付与
    # print(self.df_lane_info)
    # self.df_lane_info.to_csv(r'AutoXodr\input_data\test\test_road_lane_info.csv')
    
    return df_lane_info