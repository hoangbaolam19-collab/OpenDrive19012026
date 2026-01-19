import math
import numpy as np
import pandas as pd

from submodule import ajust


class BranchStructure:
    """
    A class to handle branch/merge road structures.
    
    Attributes:
        df_junction (list): Junction data
        df_lane_info (list): Lane information data
        df_polyline (list): Polyline geometry data
        df_polyline_2 (list): Additional polyline geometry data
        error_is (str): Error status indicator
    """

    def __init__(self):
        self.df_junction = []
        self.df_lane_info = []
        self.df_polyline = []
        self.df_polyline_2 = []
        self.error_is = "None"

    def make_branch_structure(self, obj_node_data):
        """
        Create the complete branch structure from node data.
        
        Args:
            obj_node_data: Object containing node and road data
        """
        self.make_df_polyline(obj_node_data)
        if self.error_is == "None":
            self.make_df_junction(obj_node_data)
        if self.error_is == "None":
            self.make_df_lane_info(obj_node_data)

    def make_df_polyline(self, obj_node_data):
        """
        Create polyline DataFrame for branch structure.
        
        Processes road geometry data to create polylines for:
        - Merge section (ID:1)
        - Post-merge mainline (ID:0/4)
        - Pre-merge mainline (ID:2)
        - Acceleration lane (ID:3/5)
        
        Args:
            obj_node_data: Object containing node and road data
        """
        # region Create merge section (ID:1)

        # Lấy các giá trị cơ bản
        x_base = obj_node_data.border[-1]["x"]
        y_base = obj_node_data.border[-1]["y"]
        z_base = obj_node_data.border[-1]["elevation"]
        z_param_base = obj_node_data.border[-1]["elev_param"]

        base = [x_base, y_base, z_base, z_param_base]

        list_1, min_id_border, min_id_border_2 = self.create_road_ID1_branch(obj_node_data)

        [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1] = list_1

        # endregion

        # region 分岐後の本線部(ID:0 or ID:4)

        list_0, list_4, list_1, base, flag04 = self.create_road_ID04_branch(obj_node_data, base, min_id_border, list_1)

        [x_base, y_base, z_base, z_param_base] = base
        [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1] = list_1

        [id_list_0, x_list_0, y_list_0, z_list_0, z_param_list_0] = list_0
        [id_list_4, x_list_4, y_list_4, z_list_4, z_param_list_4] = list_4

        # endregion

        # region 分岐前の本線部(ID:2)

        list_2, list_1 = self.create_road_ID2_branch(obj_node_data, min_id_border_2, list_1)

        [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1] = list_1
        [id_list_2, x_list_2, y_list_2, z_list_2, z_param_list_2] = list_2

        # endregion

        # region 加速車線(ID:3 or 5)

        list_3, list_5, list_1, base, flag35 = self.create_road_ID35_branch(obj_node_data, base, min_id_border, list_1, flag04)

        [x_base, y_base, z_base, z_param_base] = base
        [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1] = list_1

        [id_list_3, x_list_3, y_list_3, z_list_3, z_param_list_3] = list_3
        [id_list_5, x_list_5, y_list_5, z_list_5, z_param_list_5] = list_5

        if flag35 and flag04 is False:

            # region 分岐後の本線部(ID:0 or ID:4)

            list_0, list_4, _list_1, _base, _flag04 = self.create_road_ID04_branch(obj_node_data, base, min_id_border, list_1, False)

            [id_list_0, x_list_0, y_list_0, z_list_0, z_param_list_0] = list_0
            [id_list_4, x_list_4, y_list_4, z_list_4, z_param_list_4] = list_4

            # endregion

            # region 分岐前の本線部(ID:2)

            list_2, list_1_ = self.create_road_ID2_branch(obj_node_data, min_id_border_2, list_1, False)

            [id_list_2, x_list_2, y_list_2, z_list_2, z_param_list_2] = list_2

            # endregion

        # endregion

        ########################################################

        # region make df polyline

        main_id_list = id_list_2 + id_list_1 + id_list_4 + id_list_0
        main_x_list = x_list_2 + x_list_1 + x_list_4 + x_list_0
        main_y_list = y_list_2 + y_list_1 + y_list_4 + y_list_0
        main_z_list = z_list_2 + z_list_1 + z_list_4 + z_list_0
        main_z_param_list = z_param_list_2 + z_param_list_1 + z_param_list_4 + z_param_list_0
        main_z_s_list = [x["s"] for x in main_z_param_list]
        main_z_a_list = main_z_list
        main_z_b_list = [x["b"] for x in main_z_param_list]
        main_z_c_list = [x["c"] for x in main_z_param_list]
        main_z_d_list = [x["d"] for x in main_z_param_list]

        sub_id_list = id_list_5 + id_list_3
        sub_x_list = x_list_5 + x_list_3
        sub_y_list = y_list_5 + y_list_3
        sub_z_list = z_list_5 + z_list_3
        sub_z_param_list = z_param_list_5 + z_param_list_3
        sub_z_s_list = [x["s"] for x in sub_z_param_list]
        sub_z_a_list = sub_z_list
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

        main_df_polyline, main_hdg_list_branch = ajust.add_curvature_info(main_df_polyline)
        sub_df_polyline, sub_hdg_list_branch = ajust.add_curvature_info(sub_df_polyline)

        # （根本的な解決が必要な箇所）
        # 本線と加速車線でラジアン方位(hdg)の値が意味的には同じだが異なる（例：１degと361degの関係）←これがOpenDriveとして読み込ませる際に悪さをする
        # 以下はその一時対応

        # 本線の合流差路中心のラジアン方位を抽出する
        # base_hdg_id = 22
        base_hdg_id = len(id_list_2 + id_list_1) + 1
        base_hdg = main_df_polyline["hdg"][base_hdg_id]  # サンプルの差路中心
        base_hdg_sub_id = 0  # 加速車線の末尾＝差路中心
        base_hdg_sub = sub_df_polyline["hdg"][base_hdg_sub_id]

        # 180度以上方位に差がある＝ラジアン方位のスケールが違う。その場合は比較結果で場合分けして+-piを適用する
        if math.pi <= abs(base_hdg - base_hdg_sub):
            if base_hdg > base_hdg_sub:
                sub_df_polyline["hdg"] = [x + 2 * math.pi for x in sub_df_polyline["hdg"]]
            elif base_hdg < base_hdg_sub:
                sub_df_polyline["hdg"] = [x - 2 * math.pi for x in sub_df_polyline["hdg"]]
            else:
                pass

        out_df = pd.concat([main_df_polyline, sub_df_polyline])
        self.df_polyline = out_df.reset_index(drop=True)

        # self.df_polyline.to_csv(r'AutoXodr\input_data\test\test_curvature_out.csv')
        # endregion

    def make_df_polyline_combine(self, branch_1, branch_2, connect_index):
        """
        Combine and adjust polyline data from two branch structures.
        
        Args:
            branch_1: First branch structure
            branch_2: Second branch structure
            connect_index: Index indicating connection point
        """

        # region Branch 1

        branch_1_offset_list = branch_1.df_lane_info["offset"].tolist()
        hdg_start_main_1 = branch_1.df_polyline["hdg"].tolist()[0]

        branch_1_id_list = branch_1.df_polyline["ID"].tolist()
        branch_1_x_list = branch_1.df_polyline["x"].tolist()
        branch_1_y_list = branch_1.df_polyline["y"].tolist()
        branch_1_z_list = branch_1.df_polyline["elev"].tolist()

        branch_1_z_s_list = branch_1.df_polyline["length"].tolist()
        branch_1_z_a_list = branch_1.df_polyline["elev_a"].tolist()
        branch_1_z_b_list = branch_1.df_polyline["elev_b"].tolist()
        branch_1_z_c_list = branch_1.df_polyline["elev_c"].tolist()
        branch_1_z_d_list = branch_1.df_polyline["elev_d"].tolist()

        branch_1_z_param_list = [
            {"s": s, "a": a, "b": b, "c": c, "d": d}
            for s, a, b, c, d in zip(
                branch_1_z_s_list,
                branch_1_z_a_list,
                branch_1_z_b_list,
                branch_1_z_c_list,
                branch_1_z_d_list,
            )
        ]

        id_list_2 = []
        id_list_1 = []
        id_list_4 = []
        id_list_0 = []
        id_list_5 = []
        id_list_3 = []

        x_list_2 = []
        x_list_1 = []
        x_list_4 = []
        x_list_0 = []
        x_list_5 = []
        x_list_3 = []

        y_list_2 = []
        y_list_1 = []
        y_list_4 = []
        y_list_0 = []
        y_list_5 = []
        y_list_3 = []

        z_list_2 = []
        z_list_1 = []
        z_list_4 = []
        z_list_0 = []
        z_list_5 = []
        z_list_3 = []

        z_param_list_2 = []
        z_param_list_1 = []
        z_param_list_4 = []
        z_param_list_0 = []
        z_param_list_5 = []
        z_param_list_3 = []

        for i in range(len(branch_1_id_list)):
            if branch_1_id_list[i] == 0:
                id_list_0 += [0]
            elif branch_1_id_list[i] == 1:
                id_list_1 += [1]
            elif branch_1_id_list[i] == 2:
                id_list_2 += [2]
            elif branch_1_id_list[i] == 3:
                id_list_3 += [3]
            elif branch_1_id_list[i] == 4:
                id_list_4 += [4]
            elif branch_1_id_list[i] == 5:
                id_list_5 += [5]

        id_num_2 = len(id_list_2)
        id_num_1 = len(id_list_2) + len(id_list_1)
        id_num_4 = len(id_list_2) + len(id_list_1) + len(id_list_4)
        id_num_0 = len(id_list_2) + len(id_list_1) + len(id_list_4) + len(id_list_0)
        id_num_5 = len(id_list_2) + len(id_list_1) + len(id_list_4) + len(id_list_0) + len(id_list_5)
        id_num_3 = len(branch_1_id_list)

        x_list_2.extend(branch_1_x_list[0:id_num_2])
        x_list_1.extend(branch_1_x_list[id_num_2:id_num_1])
        x_list_4.extend(branch_1_x_list[id_num_1:id_num_4])
        x_list_0.extend(branch_1_x_list[id_num_4:id_num_0])
        x_list_5.extend(branch_1_x_list[id_num_0:id_num_5])
        x_list_3.extend(branch_1_x_list[id_num_5:id_num_3])

        y_list_2.extend(branch_1_y_list[0:id_num_2])
        y_list_1.extend(branch_1_y_list[id_num_2:id_num_1])
        y_list_4.extend(branch_1_y_list[id_num_1:id_num_4])
        y_list_0.extend(branch_1_y_list[id_num_4:id_num_0])
        y_list_5.extend(branch_1_y_list[id_num_0:id_num_5])
        y_list_3.extend(branch_1_y_list[id_num_5:id_num_3])

        z_list_2.extend(branch_1_z_list[0:id_num_2])
        z_list_1.extend(branch_1_z_list[id_num_2:id_num_1])
        z_list_4.extend(branch_1_z_list[id_num_1:id_num_4])
        z_list_0.extend(branch_1_z_list[id_num_4:id_num_0])
        z_list_5.extend(branch_1_z_list[id_num_0:id_num_5])
        z_list_3.extend(branch_1_z_list[id_num_5:id_num_3])

        z_param_list_2.extend(branch_1_z_param_list[0:id_num_2])
        z_param_list_1.extend(branch_1_z_param_list[id_num_2:id_num_1])
        z_param_list_4.extend(branch_1_z_param_list[id_num_1:id_num_4])
        z_param_list_0.extend(branch_1_z_param_list[id_num_4:id_num_0])
        z_param_list_5.extend(branch_1_z_param_list[id_num_0:id_num_5])
        z_param_list_3.extend(branch_1_z_param_list[id_num_5:id_num_3])

        # endregion

        ########################################################

        # region Branch 2

        branch_2_offset_list = branch_2.df_lane_info["offset"].tolist()

        branch_2_id_list = branch_2.df_polyline["ID"].tolist()
        branch_2_x_list = branch_2.df_polyline["x"].tolist()
        branch_2_y_list = branch_2.df_polyline["y"].tolist()
        branch_2_z_list = branch_2.df_polyline["elev"].tolist()

        branch_2_z_s_list = branch_2.df_polyline["length"].tolist()
        branch_2_z_a_list = branch_2.df_polyline["elev_a"].tolist()
        branch_2_z_b_list = branch_2.df_polyline["elev_b"].tolist()
        branch_2_z_c_list = branch_2.df_polyline["elev_c"].tolist()
        branch_2_z_d_list = branch_2.df_polyline["elev_d"].tolist()

        branch_2_z_param_list = [
            {"s": s, "a": a, "b": b, "c": c, "d": d}
            for s, a, b, c, d in zip(
                branch_2_z_s_list,
                branch_2_z_a_list,
                branch_2_z_b_list,
                branch_2_z_c_list,
                branch_2_z_d_list,
            )
        ]

        id_list_8 = []
        id_list_7 = []
        id_list_10 = []
        id_list_6 = []
        id_list_11 = []
        id_list_9 = []

        x_list_8 = []
        x_list_7 = []
        x_list_10 = []
        x_list_6 = []
        x_list_11 = []
        x_list_9 = []

        y_list_8 = []
        y_list_7 = []
        y_list_10 = []
        y_list_6 = []
        y_list_11 = []
        y_list_9 = []

        z_list_8 = []
        z_list_7 = []
        z_list_10 = []
        z_list_6 = []
        z_list_11 = []
        z_list_9 = []

        z_param_list_8 = []
        z_param_list_7 = []
        z_param_list_10 = []
        z_param_list_6 = []
        z_param_list_11 = []
        z_param_list_9 = []

        for i in range(len(branch_2_id_list)):
            if branch_2_id_list[i] == 0:
                id_list_6 += [0]
            elif branch_2_id_list[i] == 1:
                id_list_7 += [1]
            elif branch_2_id_list[i] == 2:
                id_list_8 += [2]
            elif branch_2_id_list[i] == 3:
                id_list_9 += [3]
            elif branch_2_id_list[i] == 4:
                id_list_10 += [4]
            elif branch_2_id_list[i] == 5:
                id_list_11 += [5]

        id_num_2 = len(id_list_8)
        id_num_1 = len(id_list_8) + len(id_list_7)
        id_num_4 = len(id_list_8) + len(id_list_7) + len(id_list_10)
        id_num_0 = len(id_list_8) + len(id_list_7) + len(id_list_10) + len(id_list_6)
        id_num_5 = len(id_list_8) + len(id_list_7) + len(id_list_10) + len(id_list_6) + len(id_list_11)
        id_num_3 = len(branch_2_id_list)

        x_list_8.extend(branch_2_x_list[0:id_num_2])
        x_list_7.extend(branch_2_x_list[id_num_2:id_num_1])
        x_list_10.extend(branch_2_x_list[id_num_1:id_num_4])
        x_list_6.extend(branch_2_x_list[id_num_4:id_num_0])
        x_list_11.extend(branch_2_x_list[id_num_0:id_num_5])
        x_list_9.extend(branch_2_x_list[id_num_5:id_num_3])

        y_list_8.extend(branch_2_y_list[0:id_num_2])
        y_list_7.extend(branch_2_y_list[id_num_2:id_num_1])
        y_list_10.extend(branch_2_y_list[id_num_1:id_num_4])
        y_list_6.extend(branch_2_y_list[id_num_4:id_num_0])
        y_list_11.extend(branch_2_y_list[id_num_0:id_num_5])
        y_list_9.extend(branch_2_y_list[id_num_5:id_num_3])

        z_list_8.extend(branch_2_z_list[0:id_num_2])
        z_list_7.extend(branch_2_z_list[id_num_2:id_num_1])
        z_list_10.extend(branch_2_z_list[id_num_1:id_num_4])
        z_list_6.extend(branch_2_z_list[id_num_4:id_num_0])
        z_list_11.extend(branch_2_z_list[id_num_0:id_num_5])
        z_list_9.extend(branch_2_z_list[id_num_5:id_num_3])

        z_param_list_8.extend(branch_2_z_param_list[0:id_num_2])
        z_param_list_7.extend(branch_2_z_param_list[id_num_2:id_num_1])
        z_param_list_10.extend(branch_2_z_param_list[id_num_1:id_num_4])
        z_param_list_6.extend(branch_2_z_param_list[id_num_4:id_num_0])
        z_param_list_11.extend(branch_2_z_param_list[id_num_0:id_num_5])
        z_param_list_9.extend(branch_2_z_param_list[id_num_5:id_num_3])

        # endregion

        ########################################################

        if connect_index == 0:

            try:

                x_list_5.pop(-1)
                y_list_5.pop(-1)
                x_list_8.pop(-1)
                y_list_8.pop(-1)

                x_curve1 = x_list_5 + x_list_3
                y_curve1 = y_list_5 + y_list_3
                x_curve2 = x_list_8 + x_list_7
                y_curve2 = y_list_8 + y_list_7

                start_point = (x_list_3[0], y_list_3[0])
                end_point = (x_list_8[-1], y_list_8[-1])

                offset = branch_2_offset_list[0]

                x_curve1, y_curve1, x_curve2, y_curve2 = ajust.make_combine_road_data(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset)

                ########################################################

                id_list_3_new = []
                x_list_3_new = []
                y_list_3_new = []
                z_list_3_new = []
                z_param_list_3_new = []

                id_list_5_new = []
                x_list_5_new = []
                y_list_5_new = []
                z_list_5_new = []
                z_param_list_5_new = []

                id_num0 = len(x_curve1) - 3
                id_num1 = len(x_curve1) - id_num0

                id_list_3_new = [3] * int(id_num0)
                x_list_3_new.extend(x_curve1[id_num1: id_num0 + id_num1])
                y_list_3_new.extend(y_curve1[id_num1: id_num0 + id_num1])
                z_list_3_new = z_list_3[0: len(x_list_3_new)]
                z_param_list_3_new = z_param_list_3[0: len(x_list_3_new)]

                id_list_5_new = [5] * int(id_num1)
                x_list_5_new.extend(x_curve1[0:id_num1])
                y_list_5_new.extend(y_curve1[0:id_num1])
                z_list_5_new = z_list_5
                z_param_list_5_new = z_param_list_5

                id_list_5_new.insert(0, 5)
                x_list_5_new.insert(3, x_list_3_new[0])
                y_list_5_new.insert(3, y_list_3_new[0])

                id_list_7_new = []
                x_list_7_new = []
                y_list_7_new = []
                z_list_7_new = []
                z_param_list_7_new = []

                id_list_8_new = []
                x_list_8_new = []
                y_list_8_new = []
                z_list_8_new = []
                z_param_list_8_new = []

                id_num7 = len(x_list_7)
                id_num8 = len(x_curve2) - id_num7

                if id_num8 < 0:
                    print("id_num8 = ", id_num8)
                    raise ValueError("This is a special case")

                id_list_7_new = [1] * int(id_num7)
                x_list_7_new.extend(x_curve2[id_num8: len(x_curve2)])
                y_list_7_new.extend(y_curve2[id_num8: len(x_curve2)])
                z_list_7_new = z_list_7
                z_param_list_7_new = z_param_list_7

                id_list_8_new = [2] * int(id_num8)
                x_list_8_new.extend(x_curve2[0:id_num8])
                y_list_8_new.extend(y_curve2[0:id_num8])

                id_list_8_new.insert(0, 2)
                x_list_8_new.insert(len(x_list_8_new), x_list_7_new[0])
                y_list_8_new.insert(len(y_list_8_new), y_list_7_new[0])

                z_list_8_new = z_list_8[(len(z_list_8) - len(x_list_8_new)): len(z_list_8)]
                z_param_list_8_new = z_param_list_8[(len(z_list_8) - len(x_list_8_new)): len(z_list_8)]

                # plt.legend()

                id_list_3 = id_list_3_new
                x_list_3 = x_list_3_new
                y_list_3 = y_list_3_new
                z_list_3 = z_list_3_new
                z_param_list_3 = z_param_list_3_new

                id_list_5 = id_list_5_new
                x_list_5 = x_list_5_new
                y_list_5 = y_list_5_new
                z_list_5 = z_list_5_new
                z_param_list_5 = z_param_list_5_new

                id_list_7 = id_list_7_new
                x_list_7 = x_list_7_new
                y_list_7 = y_list_7_new
                z_list_7 = z_list_7_new
                z_param_list_7 = z_param_list_7_new

                id_list_8 = id_list_8_new
                x_list_8 = x_list_8_new
                y_list_8 = y_list_8_new
                z_list_8 = z_list_8_new
                z_param_list_8 = z_param_list_8_new

            except Exception as error:

                print("except (brach - branch): connect_index == 0", error)

                start_point = (x_list_5[0], y_list_5[0], z_list_5[0])
                end_point = (x_list_7[-1], y_list_7[-1], z_list_7[-1])

                offset = branch_2_offset_list[0]

                if error.args[0] == 1:
                    print("This is a serious error that requires changing the road data to connect the road correctly. XXXXXXXXXX")

                x_curve1, y_curve1, z_curve1, z_param_curve1, x_curve2, y_curve2, z_curve2, z_param_curve2 = ajust.make_new_combine_road_data(start_point, end_point, offset)

                ########################################################

                id_list_8_new = []
                x_list_8_new = []
                y_list_8_new = []
                z_list_8_new = []
                z_param_list_8_new = []

                id_list_7_new = []
                x_list_7_new = []
                y_list_7_new = []
                z_list_7_new = []
                z_param_list_7_new = []

                id_num8 = 2
                id_num7 = len(x_curve2) - id_num8

                id_list_8_new = [2] * int(id_num8)
                x_list_8_new.extend(x_curve2[0:id_num8])
                y_list_8_new.extend(y_curve2[0:id_num8])
                z_list_8_new.extend(z_curve2[0:id_num8])
                z_param_list_8_new.extend(z_param_curve2[0:id_num8])

                id_list_7_new = [1] * int(id_num7)
                x_list_7_new.extend(x_curve2[id_num8: len(x_curve2)])
                y_list_7_new.extend(y_curve2[id_num8: len(x_curve2)])
                z_list_7_new.extend(z_curve2[id_num8: len(x_curve2)])
                z_param_list_7_new.extend(z_param_curve2[id_num8: len(x_curve2)])

                id_list_7_new.insert(0, 1)
                x_list_7_new.insert(0, x_list_8_new[-1])
                y_list_7_new.insert(0, y_list_8_new[-1])
                z_list_7_new.insert(0, z_list_8_new[-1])
                z_param_list_7_new.insert(0, z_param_list_8_new[-1])

                id_list_3_new = []
                x_list_3_new = []
                y_list_3_new = []
                z_list_3_new = []
                z_param_list_3_new = []

                id_list_5_new = []
                x_list_5_new = []
                y_list_5_new = []
                z_list_5_new = []
                z_param_list_5_new = []

                id_num3 = len(x_curve1) - 3
                id_num5 = 3

                id_list_5_new = [5] * int(id_num5)
                x_list_5_new.extend(x_curve1[0:id_num5])
                y_list_5_new.extend(y_curve1[0:id_num5])
                z_list_5_new.extend(z_curve1[0:id_num5])
                z_param_list_5_new.extend(z_param_curve1[0:id_num5])

                id_list_3_new = [3] * int(id_num3)
                x_list_3_new.extend(x_curve1[id_num5: len(x_curve1)])
                y_list_3_new.extend(y_curve1[id_num5: len(x_curve1)])
                z_list_3_new.extend(z_curve1[id_num5: len(x_curve1)])
                z_param_list_3_new.extend(z_param_curve1[id_num5: len(x_curve1)])

                id_list_5_new.insert(0, 5)
                x_list_5_new.insert(len(x_list_5_new), x_list_3_new[0])
                y_list_5_new.insert(len(y_list_5_new), y_list_3_new[0])
                z_list_5_new.insert(len(z_list_5_new), z_list_3_new[0])
                z_param_list_5_new.insert(len(z_param_list_5_new), z_param_list_3_new[0])

                id_list_3 = id_list_3_new
                x_list_3 = x_list_3_new
                y_list_3 = y_list_3_new
                z_list_3 = z_list_3_new
                z_param_list_3 = z_param_list_3_new

                id_list_5 = id_list_5_new
                x_list_5 = x_list_5_new
                y_list_5 = y_list_5_new
                z_list_5 = z_list_5_new
                z_param_list_5 = z_param_list_5_new

                id_list_7 = id_list_7_new
                x_list_7 = x_list_7_new
                y_list_7 = y_list_7_new
                z_list_7 = z_list_7_new
                z_param_list_7 = z_param_list_7_new

                id_list_8 = id_list_8_new
                x_list_8 = x_list_8_new
                y_list_8 = y_list_8_new
                z_list_8 = z_list_8_new
                z_param_list_8 = z_param_list_8_new

        else:

            try:

                x_list_4.pop(-1)
                y_list_4.pop(-1)
                x_list_8.pop(-1)
                y_list_8.pop(-1)

                x_curve1 = x_list_4 + x_list_0
                y_curve1 = y_list_4 + y_list_0
                x_curve2 = x_list_8 + x_list_7
                y_curve2 = y_list_8 + y_list_7

                start_point = (x_list_0[0], y_list_0[0])
                end_point = (x_list_8[-1], y_list_8[-1])

                for i in range(len(branch_1_offset_list) - 1, -1, -1):
                    if branch_1_offset_list[i] != 0:
                        offset = branch_2_offset_list[0] - branch_1_offset_list[i]
                        break

                x_curve1, y_curve1, x_curve2, y_curve2 = ajust.make_combine_road_data(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset)

                ########################################################

                id_list_0_new = []
                x_list_0_new = []
                y_list_0_new = []
                z_list_0_new = []
                z_param_list_0_new = []

                id_list_4_new = []
                x_list_4_new = []
                y_list_4_new = []
                z_list_4_new = []
                z_param_list_4_new = []

                id_num0 = len(x_curve1) - 3
                id_num4 = len(x_curve1) - id_num0

                id_list_0_new = [0] * int(id_num0)
                x_list_0_new.extend(x_curve1[id_num4: id_num0 + id_num4])
                y_list_0_new.extend(y_curve1[id_num4: id_num0 + id_num4])
                z_list_0_new = z_list_0[0: len(x_list_0_new)]
                z_param_list_0_new = z_param_list_0[0: len(x_list_0_new)]

                id_list_4_new = [4] * int(id_num4)
                x_list_4_new.extend(x_curve1[0:id_num4])
                y_list_4_new.extend(y_curve1[0:id_num4])
                z_list_4_new = z_list_4
                z_param_list_4_new = z_param_list_4

                id_list_4_new.insert(0, 4)
                x_list_4_new.insert(3, x_list_0_new[0])
                y_list_4_new.insert(3, y_list_0_new[0])

                id_list_7_new = []
                x_list_7_new = []
                y_list_7_new = []
                z_list_7_new = []
                z_param_list_7_new = []

                id_list_8_new = []
                x_list_8_new = []
                y_list_8_new = []
                z_list_8_new = []
                z_param_list_8_new = []

                id_num7 = len(x_list_7)
                id_num8 = len(x_curve2) - id_num7

                if id_num8 < 0:
                    print("id_num8 = ", id_num8)
                    raise ValueError("This is a special case")

                id_list_7_new = [1] * int(id_num7)
                x_list_7_new.extend(x_curve2[id_num8: len(x_curve2)])
                y_list_7_new.extend(y_curve2[id_num8: len(x_curve2)])
                z_list_7_new = z_list_7
                z_param_list_7_new = z_param_list_7

                id_list_8_new = [2] * int(id_num8)
                x_list_8_new.extend(x_curve2[0:id_num8])
                y_list_8_new.extend(y_curve2[0:id_num8])

                id_list_8_new.insert(0, 2)
                x_list_8_new.insert(len(x_list_8_new), x_list_7_new[0])
                y_list_8_new.insert(len(y_list_8_new), y_list_7_new[0])

                z_list_8_new = z_list_8[(len(z_list_8) - len(x_list_8_new)): len(z_list_8)]
                z_param_list_8_new = z_param_list_8[(len(z_list_8) - len(x_list_8_new)): len(z_list_8)]

                id_list_0 = id_list_0_new
                x_list_0 = x_list_0_new
                y_list_0 = y_list_0_new
                z_list_0 = z_list_0_new
                z_param_list_0 = z_param_list_0_new

                id_list_4 = id_list_4_new
                x_list_4 = x_list_4_new
                y_list_4 = y_list_4_new
                z_list_4 = z_list_4_new
                z_param_list_4 = z_param_list_4_new

                id_list_7 = id_list_7_new
                x_list_7 = x_list_7_new
                y_list_7 = y_list_7_new
                z_list_7 = z_list_7_new
                z_param_list_7 = z_param_list_7_new

                id_list_8 = id_list_8_new
                x_list_8 = x_list_8_new
                y_list_8 = y_list_8_new
                z_list_8 = z_list_8_new
                z_param_list_8 = z_param_list_8_new

            except Exception as error:

                print("except (brach - branch): connect_index == 1", error)

                start_point = (x_list_4[0], y_list_4[0], z_list_4[0])
                end_point = (x_list_7[-1], y_list_7[-1], z_list_7[-1])

                for i in range(len(branch_1_offset_list) - 1, -1, -1):
                    if branch_1_offset_list[i] != 0:
                        offset = branch_2_offset_list[0] - branch_1_offset_list[i]
                        break

                if error.args[0] == 1:
                    print("This is a serious error that requires changing the road data to connect the road correctly. XXXXXXXXXX")

                x_curve1, y_curve1, z_curve1, z_param_curve1, x_curve2, y_curve2, z_curve2, z_param_curve2 = ajust.make_new_combine_road_data(start_point, end_point, offset)

                ########################################################

                id_list_8_new = []
                x_list_8_new = []
                y_list_8_new = []
                z_list_8_new = []
                z_param_list_8_new = []

                id_list_7_new = []
                x_list_7_new = []
                y_list_7_new = []
                z_list_7_new = []
                z_param_list_7_new = []

                id_num8 = 2
                id_num7 = len(x_curve2) - id_num8

                id_list_8_new = [2] * int(id_num8)
                x_list_8_new.extend(x_curve2[0:id_num8])
                y_list_8_new.extend(y_curve2[0:id_num8])
                z_list_8_new.extend(z_curve2[0:id_num8])
                z_param_list_8_new.extend(z_param_curve2[0:id_num8])

                id_list_7_new = [1] * int(id_num7)
                x_list_7_new.extend(x_curve2[id_num8: len(x_curve2)])
                y_list_7_new.extend(y_curve2[id_num8: len(x_curve2)])
                z_list_7_new.extend(z_curve2[id_num8: len(x_curve2)])
                z_param_list_7_new.extend(z_param_curve2[id_num8: len(x_curve2)])

                id_list_7_new.insert(0, 1)
                x_list_7_new.insert(0, x_list_8_new[-1])
                y_list_7_new.insert(0, y_list_8_new[-1])
                z_list_7_new.insert(0, z_list_8_new[-1])
                z_param_list_7_new.insert(0, z_param_list_8_new[-1])

                id_list_0_new = []
                x_list_0_new = []
                y_list_0_new = []
                z_list_0_new = []
                z_param_list_0_new = []

                id_list_4_new = []
                x_list_4_new = []
                y_list_4_new = []
                z_list_4_new = []
                z_param_list_4_new = []

                id_num0 = len(x_curve1) - 3
                id_num4 = 3

                id_list_4_new = [4] * int(id_num4)
                x_list_4_new.extend(x_curve1[0:id_num4])
                y_list_4_new.extend(y_curve1[0:id_num4])
                z_list_4_new.extend(z_curve1[0:id_num4])
                z_param_list_4_new.extend(z_param_curve1[0:id_num4])

                id_list_0_new = [0] * int(id_num0)
                x_list_0_new.extend(x_curve1[id_num4: len(x_curve1)])
                y_list_0_new.extend(y_curve1[id_num4: len(x_curve1)])
                z_list_0_new.extend(z_curve1[id_num4: len(x_curve1)])
                z_param_list_0_new.extend(z_param_curve1[id_num4: len(x_curve1)])

                id_list_4_new.insert(0, 4)
                x_list_4_new.insert(len(x_list_4_new), x_list_0_new[0])
                y_list_4_new.insert(len(y_list_4_new), y_list_0_new[0])
                z_list_4_new.insert(len(z_list_4_new), z_list_0_new[0])
                z_param_list_4_new.insert(len(z_param_list_4_new), z_param_list_0_new[0])

                id_list_0 = id_list_0_new
                x_list_0 = x_list_0_new
                y_list_0 = y_list_0_new
                z_list_0 = z_list_0_new
                z_param_list_0 = z_param_list_0_new

                id_list_4 = id_list_4_new
                x_list_4 = x_list_4_new
                y_list_4 = y_list_4_new
                z_list_4 = z_list_4_new
                z_param_list_4 = z_param_list_4_new

                id_list_7 = id_list_7_new
                x_list_7 = x_list_7_new
                y_list_7 = y_list_7_new
                z_list_7 = z_list_7_new
                z_param_list_7 = z_param_list_7_new

                id_list_8 = id_list_8_new
                x_list_8 = x_list_8_new
                y_list_8 = y_list_8_new
                z_list_8 = z_list_8_new
                z_param_list_8 = z_param_list_8_new

        ########################################################

        # region 111111111111

        main_id_list = id_list_2 + id_list_1 + id_list_4 + id_list_0
        main_x_list = x_list_2 + x_list_1 + x_list_4 + x_list_0
        main_y_list = y_list_2 + y_list_1 + y_list_4 + y_list_0
        main_z_list = z_list_2 + z_list_1 + z_list_4 + z_list_0
        main_z_param_list = z_param_list_2 + z_param_list_1 + z_param_list_4 + z_param_list_0
        main_z_s_list = [x["s"] for x in main_z_param_list]
        main_z_a_list = main_z_list
        main_z_b_list = [x["b"] for x in main_z_param_list]
        main_z_c_list = [x["c"] for x in main_z_param_list]
        main_z_d_list = [x["d"] for x in main_z_param_list]

        sub_id_list = id_list_5 + id_list_3
        sub_x_list = x_list_5 + x_list_3
        sub_y_list = y_list_5 + y_list_3
        sub_z_list = z_list_5 + z_list_3
        sub_z_param_list = z_param_list_5 + z_param_list_3
        sub_z_s_list = [x["s"] for x in sub_z_param_list]
        sub_z_a_list = sub_z_list
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

        main_df_polyline, main_hdg_list_1 = ajust.add_curvature_info(main_df_polyline, hdg_start_main_1)
        sub_df_polyline, sub_hdg_list_1 = ajust.add_curvature_info(sub_df_polyline)

        # （根本的な解決が必要な箇所）
        # 本線と加速車線でラジアン方位(hdg)の値が意味的には同じだが異なる（例：１degと361degの関係）←これがOpenDriveとして読み込ませる際に悪さをする
        # 以下はその一時対応

        # 本線の合流差路中心のラジアン方位を抽出する
        # base_hdg_id = 22
        base_hdg_id = len(id_list_2 + id_list_1) + 1
        base_hdg = main_df_polyline["hdg"][base_hdg_id]  # サンプルの差路中心
        base_hdg_sub_id = 0  # 加速車線の末尾＝差路中心
        base_hdg_sub = sub_df_polyline["hdg"][base_hdg_sub_id]

        # 180度以上方位に差がある＝ラジアン方位のスケールが違う。その場合は比較結果で場合分けして+-piを適用する
        if math.pi <= abs(base_hdg - base_hdg_sub):
            if base_hdg > base_hdg_sub:
                sub_df_polyline["hdg"] = [x + 2 * math.pi for x in sub_df_polyline["hdg"]]
            elif base_hdg < base_hdg_sub:
                sub_df_polyline["hdg"] = [x - 2 * math.pi for x in sub_df_polyline["hdg"]]
            else:
                pass

        out_df = pd.concat([main_df_polyline, sub_df_polyline])
        self.df_polyline_2 += [out_df.reset_index(drop=True)]
        # endregion

        # region 222222222222
        main_id_list = id_list_8 + id_list_7 + id_list_10 + id_list_6
        main_x_list = x_list_8 + x_list_7 + x_list_10 + x_list_6
        main_y_list = y_list_8 + y_list_7 + y_list_10 + y_list_6
        main_z_list = z_list_8 + z_list_7 + z_list_10 + z_list_6
        main_z_param_list = z_param_list_8 + z_param_list_7 + z_param_list_10 + z_param_list_6
        main_z_s_list = [x["s"] for x in main_z_param_list]
        main_z_a_list = main_z_list
        main_z_b_list = [x["b"] for x in main_z_param_list]
        main_z_c_list = [x["c"] for x in main_z_param_list]
        main_z_d_list = [x["d"] for x in main_z_param_list]

        sub_id_list = id_list_11 + id_list_9
        sub_x_list = x_list_11 + x_list_9
        sub_y_list = y_list_11 + y_list_9
        sub_z_list = z_list_11 + z_list_9
        sub_z_param_list = z_param_list_11 + z_param_list_9
        sub_z_s_list = [x["s"] for x in sub_z_param_list]
        sub_z_a_list = sub_z_list
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

        if connect_index == 0:
            main_df_polyline, main_hdg_list_2 = ajust.add_curvature_info(main_df_polyline, sub_hdg_list_1[-2])
        else:
            main_df_polyline, main_hdg_list_2 = ajust.add_curvature_info(main_df_polyline, main_hdg_list_1[-2])

        sub_df_polyline, sub_hdg_list_2 = ajust.add_curvature_info(sub_df_polyline)

        # （根本的な解決が必要な箇所）
        # 本線と加速車線でラジアン方位(hdg)の値が意味的には同じだが異なる（例：１degと361degの関係）←これがOpenDriveとして読み込ませる際に悪さをする
        # 以下はその一時対応

        # 本線の合流差路中心のラジアン方位を抽出する
        # base_hdg_id = 22
        base_hdg_id = len(id_list_7 + id_list_8) + 1
        base_hdg = main_df_polyline["hdg"][base_hdg_id]  # サンプルの差路中心
        base_hdg_sub_id = 0  # 加速車線の末尾＝差路中心
        base_hdg_sub = sub_df_polyline["hdg"][base_hdg_sub_id]

        # 180度以上方位に差がある＝ラジアン方位のスケールが違う。その場合は比較結果で場合分けして+-piを適用する
        if math.pi <= abs(base_hdg - base_hdg_sub):
            if base_hdg > base_hdg_sub:
                sub_df_polyline["hdg"] = [x + 2 * math.pi for x in sub_df_polyline["hdg"]]
            elif base_hdg < base_hdg_sub:
                sub_df_polyline["hdg"] = [x - 2 * math.pi for x in sub_df_polyline["hdg"]]
            else:
                pass

        out_df = pd.concat([main_df_polyline, sub_df_polyline])
        self.df_polyline_2 += [out_df.reset_index(drop=True)]
        # endregion

    def make_df_junction(self, obj_node_data):
        """
        Create junction DataFrame for OpenDRIVE format.
        
        Creates junction connections between:
        - Mainline lanes
        - Acceleration lanes
        - Connecting roads
        
        Args:
            obj_node_data: Object containing node and road data
        """
        # ジャンクションの数は本線レーン数+加速車線のレーン数
        main_lane_num = obj_node_data.obj_link_data_list[1].lanecnt
        sub_lane_num = obj_node_data.obj_link_data_list[0].lanecnt
        junction_lane_num = main_lane_num + sub_lane_num
        junction_id_list = [6] * (junction_lane_num * 2)

        # コネクションIDを設定
        conection_id_list = [0] * main_lane_num
        conection_id_list.extend([1] * sub_lane_num)
        conection_id_list.extend([2] * main_lane_num)
        conection_id_list.extend([3] * sub_lane_num)

        # incomingRoadを設定
        incoming_road_list = [0] * main_lane_num
        incoming_road_list.extend([3] * sub_lane_num)
        incoming_road_list.extend([1] * (sub_lane_num + main_lane_num))

        # connectingRoadを設定
        connecting_road_list = [4] * main_lane_num
        connecting_road_list.extend([5] * sub_lane_num)
        connecting_road_list.extend([4] * main_lane_num)
        connecting_road_list.extend([5] * sub_lane_num)

        # contactPointの設定
        contactPoint_list = ["end"] * junction_lane_num
        contactPoint_list.extend(["start"] * junction_lane_num)

        # lanelinkfromの設定
        lanelink_from_list = []
        for i in range(main_lane_num):
            lanelink_from_list.append(i + 1)
        for i in range(sub_lane_num):
            lanelink_from_list.append(i + 1)

        for i in range(main_lane_num):
            lanelink_from_list.append(i + 1)
        for i in range(sub_lane_num):
            lanelink_from_list.append(i + 1)

        # lanelink_toの設定
        lanelink_to_list = []
        for i in range(main_lane_num):
            lanelink_to_list.append(i + 1)
        for i in range(sub_lane_num):
            lanelink_to_list.append(i + 1)

        for i in range(junction_lane_num):
            lanelink_to_list.append(i + 1)

        # データフレームの辞書設定
        df_junction_dict = dict(
            junction_id=junction_id_list,
            connection_id=conection_id_list,
            incoming_road=incoming_road_list,
            connecting_road=connecting_road_list,
            contact_point=contactPoint_list,
            lanelink_from=lanelink_from_list,
            lanelink_to=lanelink_to_list,
        )

        # データフレームの生成
        self.df_junction = pd.DataFrame(data=df_junction_dict)
        # データフレームへ曲率情報を付与
        # print(self.df_junction)
        # self.df_junction.to_csv(r'AutoXodr\input_data\test\test_junction.csv')

    def make_df_lane_info(self, obj_node_data):
        main_lane_num0 = obj_node_data.obj_link_data_list[1].lanecnt
        main_lane_num1 = obj_node_data.obj_link_data_list[2].lanecnt
        sub_lane_num = obj_node_data.obj_link_data_list[0].lanecnt

        main_lane_width0 = obj_node_data.obj_link_data_list[1].width
        main_lane_width1 = obj_node_data.obj_link_data_list[2].width
        sub_lane_width = obj_node_data.obj_link_data_list[0].width

        main_lane_maxspeed0 = obj_node_data.obj_link_data_list[1].maxspeed
        main_lane_maxspeed1 = obj_node_data.obj_link_data_list[2].maxspeed
        sub_lane_maxspeed = obj_node_data.obj_link_data_list[0].maxspeed

        road_id_list_0 = [0] * (main_lane_num0 + 1)
        road_id_list_4 = [4] * (main_lane_num0 + 1)
        road_id_list_1 = [1] * (main_lane_num0 + sub_lane_num + 1)
        road_id_list_2 = [2] * (main_lane_num1 + 1)
        road_id_list_3 = [3] * (sub_lane_num + 1)
        road_id_list_5 = [5] * (sub_lane_num + 1)

        junction_id_list_0 = [-1] * (main_lane_num0 + 1)
        junction_id_list_4 = [6] * (main_lane_num0 + 1)
        junction_id_list_1 = [-1] * (main_lane_num0 + sub_lane_num + 1)
        junction_id_list_2 = [-1] * (main_lane_num1 + 1)
        junction_id_list_3 = [-1] * (sub_lane_num + 1)
        junction_id_list_5 = [6] * (sub_lane_num + 1)

        p_road_type_list_0 = ["junction"] * (main_lane_num0 + 1)
        p_road_type_list_4 = ["road"] * (main_lane_num0 + 1)
        p_road_type_list_1 = ["road"] * (main_lane_num0 + sub_lane_num + 1)
        p_road_type_list_2 = [""] * (main_lane_num1 + 1)
        p_road_type_list_3 = ["junction"] * (sub_lane_num + 1)
        p_road_type_list_5 = ["road"] * (sub_lane_num + 1)

        road_predecessor_id_list_0 = [6] * (main_lane_num0 + 1)
        road_predecessor_id_list_4 = [1] * (main_lane_num0 + 1)
        road_predecessor_id_list_1 = [2] * (main_lane_num0 + sub_lane_num + 1)
        road_predecessor_id_list_2 = [""] * (main_lane_num1 + 1)
        road_predecessor_id_list_3 = [6] * (sub_lane_num + 1)
        road_predecessor_id_list_5 = [1] * (sub_lane_num + 1)

        p_contact_point_list_0 = [""] * (main_lane_num0 + 1)
        p_contact_point_list_4 = ["end"] * (main_lane_num0 + 1)
        p_contact_point_list_1 = ["end"] * (main_lane_num0 + sub_lane_num + 1)
        p_contact_point_list_2 = [""] * (main_lane_num1 + 1)
        p_contact_point_list_3 = [""] * (sub_lane_num + 1)
        p_contact_point_list_5 = ["end"] * (sub_lane_num + 1)

        s_road_type_list_0 = [""] * (main_lane_num0 + 1)
        s_road_type_list_4 = ["road"] * (main_lane_num0 + 1)
        s_road_type_list_1 = ["junction"] * (main_lane_num0 + sub_lane_num + 1)
        s_road_type_list_2 = ["road"] * (main_lane_num1 + 1)
        s_road_type_list_3 = [""] * (sub_lane_num + 1)
        s_road_type_list_5 = ["road"] * (sub_lane_num + 1)

        road_successor_id_list_0 = [""] * (main_lane_num0 + 1)
        road_successor_id_list_4 = [0] * (main_lane_num0 + 1)
        road_successor_id_list_1 = [6] * (main_lane_num0 + sub_lane_num + 1)
        road_successor_id_list_2 = [1] * (main_lane_num1 + 1)
        road_successor_id_list_3 = [""] * (sub_lane_num + 1)
        road_successor_id_list_5 = [3] * (sub_lane_num + 1)

        s_contact_point_list_0 = [""] * (main_lane_num0 + 1)
        s_contact_point_list_4 = ["start"] * (main_lane_num0 + 1)
        s_contact_point_list_1 = [""] * (main_lane_num0 + sub_lane_num + 1)
        s_contact_point_list_2 = ["start"] * (main_lane_num1 + 1)
        s_contact_point_list_3 = [""] * (sub_lane_num + 1)
        s_contact_point_list_5 = ["start"] * (sub_lane_num + 1)

        offset_list_0 = [-main_lane_width0 * main_lane_num0] * (main_lane_num0 + 1)
        offset_list_4 = [-main_lane_width0 * main_lane_num0] * (main_lane_num0 + 1)
        offset_list_1 = [-main_lane_width1 * main_lane_num0] * (main_lane_num0 + sub_lane_num + 1)

        if obj_node_data.branch_direction == 0:
            offset_list_2 = [-main_lane_width1 * main_lane_num0] * (main_lane_num1 + 1)
        else:
            offset_list_2 = [-main_lane_width1 * (main_lane_num0 - (main_lane_num0 + sub_lane_num - main_lane_num1))] * (main_lane_num1 + 1)

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

        lane_successor_list_2 = []
        if obj_node_data.branch_direction == 0:
            for i in range(main_lane_num1):
                lane_successor_list_2.insert(0, i + 1)
        else:
            for i in range(main_lane_num1):
                lane_successor_list_2.append(sub_lane_num + main_lane_num0 - i)
        lane_successor_list_2.append("")

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
        if obj_node_data.branch_direction == 0:
            for i in range(main_lane_num1):
                lane_predecessor_list_1[main_lane_num0 + sub_lane_num - 1 - i] = i + 1
        else:
            for i in range(main_lane_num1):
                lane_predecessor_list_1[i] = main_lane_num1 - i
        lane_predecessor_list_1.append("")

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
        speed_list_0 = [main_lane_maxspeed0] * (main_lane_num0 + 1)
        speed_list_4 = [main_lane_maxspeed0] * (main_lane_num0 + 1)
        speed_list_1 = [main_lane_maxspeed1] * (main_lane_num0 + sub_lane_num + 1)
        speed_list_2 = [main_lane_maxspeed1] * (main_lane_num1 + 1)
        speed_list_3 = [sub_lane_maxspeed] * (sub_lane_num + 1)
        speed_list_5 = [sub_lane_maxspeed] * (sub_lane_num + 1)

        unit_list_0 = ["km/h"] * (main_lane_num0 + 1)
        unit_list_4 = ["km/h"] * (main_lane_num0 + 1)
        unit_list_1 = ["km/h"] * (main_lane_num0 + sub_lane_num + 1)
        unit_list_2 = ["km/h"] * (main_lane_num1 + 1)
        unit_list_3 = ["km/h"] * (sub_lane_num + 1)
        unit_list_5 = ["km/h"] * (sub_lane_num + 1)

        road_id_list = road_id_list_2 + road_id_list_1 + road_id_list_4 + road_id_list_0 + road_id_list_5 + road_id_list_3
        junction_id_list = junction_id_list_2 + junction_id_list_1 + junction_id_list_4 + junction_id_list_0 + junction_id_list_5 + junction_id_list_3
        p_road_type_list = p_road_type_list_2 + p_road_type_list_1 + p_road_type_list_4 + p_road_type_list_0 + p_road_type_list_5 + p_road_type_list_3
        road_predecessor_id_list = (
            road_predecessor_id_list_2 + road_predecessor_id_list_1 + road_predecessor_id_list_4 + road_predecessor_id_list_0 + road_predecessor_id_list_5 + road_predecessor_id_list_3
        )
        p_contact_point_list = p_contact_point_list_2 + p_contact_point_list_1 + p_contact_point_list_4 + p_contact_point_list_0 + p_contact_point_list_5 + p_contact_point_list_3
        s_road_type_list = s_road_type_list_2 + s_road_type_list_1 + s_road_type_list_4 + s_road_type_list_0 + s_road_type_list_5 + s_road_type_list_3
        road_successor_id_list = road_successor_id_list_2 + road_successor_id_list_1 + road_successor_id_list_4 + road_successor_id_list_0 + road_successor_id_list_5 + road_successor_id_list_3
        s_contact_point_list = s_contact_point_list_2 + s_contact_point_list_1 + s_contact_point_list_4 + s_contact_point_list_0 + s_contact_point_list_5 + s_contact_point_list_3
        offset_list = offset_list_2 + offset_list_1 + offset_list_4 + offset_list_0 + offset_list_5 + offset_list_3
        lane_change_list = lane_change_list_2 + lane_change_list_1 + lane_change_list_4 + lane_change_list_0 + lane_change_list_5 + lane_change_list_3
        direction_list = direction_list_2 + direction_list_1 + direction_list_4 + direction_list_0 + direction_list_5 + direction_list_3
        lane_id_list = lane_id_list_2 + lane_id_list_1 + lane_id_list_4 + lane_id_list_0 + lane_id_list_5 + lane_id_list_3
        lane_predecessor_list = lane_predecessor_list_2 + lane_predecessor_list_1 + lane_predecessor_list_4 + lane_predecessor_list_0 + lane_predecessor_list_5 + lane_predecessor_list_3
        lane_successor_list = lane_successor_list_2 + lane_successor_list_1 + lane_successor_list_4 + lane_successor_list_0 + lane_successor_list_5 + lane_successor_list_3
        lane_width_list = lane_width_list_2 + lane_width_list_1 + lane_width_list_4 + lane_width_list_0 + lane_width_list_5 + lane_width_list_3
        type_list = type_list_2 + type_list_1 + type_list_4 + type_list_0 + type_list_5 + type_list_3
        length_list = length_list_2 + length_list_1 + length_list_4 + length_list_0 + length_list_5 + length_list_3
        space_list = space_list_2 + space_list_1 + space_list_4 + space_list_0 + space_list_5 + space_list_3
        speed_list = speed_list_2 + speed_list_1 + speed_list_4 + speed_list_0 + speed_list_5 + speed_list_3
        unit_list = unit_list_2 + unit_list_1 + unit_list_4 + unit_list_0 + unit_list_5 + unit_list_3

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
        self.df_lane_info = pd.DataFrame(data=df_laneinfo_dict)
        # データフレームへ曲率情報を付与
        # print(self.df_lane_info)
        # self.df_lane_info.to_csv(r'AutoXodr\input_data\test\test_road_lane_info.csv')

    def split_into_2_road_branch(self, x_list_tmp, y_list_tmp, z_list_tmp, z_param_list_tmp, x_base, y_base, z_base):
        """
        Split road data into two branches.
        
        Args:
            x_list_tmp: List of x coordinates
            y_list_tmp: List of y coordinates
            z_list_tmp: List of z coordinates
            z_param_list_tmp: List of elevation parameters
            x_base: Base x coordinate
            y_base: Base y coordinate
            z_base: Base z coordinate
            
        Returns:
            tuple: Two lists containing road data for each branch:
                  [x_list_0, y_list_0, z_list_0, z_param_list_0],
                  [x_list_4, y_list_4, z_list_4, z_param_list_4]
        """
        # ID:0とID:4の振り分け
        x_list_0 = []
        x_list_4 = []
        y_list_0 = []
        y_list_4 = []
        z_list_0 = []
        z_list_4 = []
        z_param_list_0 = []
        z_param_list_4 = []

        id_num0 = len(x_list_tmp) - 3
        id_num1 = len(x_list_tmp) - id_num0

        x_list_0.extend(x_list_tmp[id_num1: id_num0 + id_num1])
        x_list_4.extend(x_list_tmp[0:id_num1])
        y_list_0.extend(y_list_tmp[id_num1: id_num0 + id_num1])
        y_list_4.extend(y_list_tmp[0:id_num1])
        z_list_0.extend(z_list_tmp[id_num1: id_num0 + id_num1])
        z_list_4.extend(z_list_tmp[0:id_num1])
        z_param_list_0.extend(z_param_list_tmp[id_num1: id_num0 + id_num1])
        z_param_list_4.extend(z_param_list_tmp[0:id_num1])

        if len(x_list_0) < 2 or len(x_list_4) < 2:
            raise ValueError("Right side road's points number is not enough")

        x_list_4.insert(3, x_list_0[0])
        y_list_4.insert(3, y_list_0[0])
        z_list_4.insert(3, z_list_0[0])

        p0 = np.array([x_list_4[3], y_list_4[3]])
        p1 = np.array([x_list_4[2], y_list_4[2]])

        # ID4の道路の最初の点から次の点までの距離を求め格納する
        add_s = np.linalg.norm(p0 - p1)

        z_param_list_4.insert(3, z_param_list_0[0].copy())
        z_param_list_4[3]["s"] = add_s
        x_list_4[0] = x_base
        y_list_4[0] = y_base
        z_list_4[0] = z_base

        # 道路の終点は長さが0
        z_param_list_0[-1]["s"] = 0
        z_param_list_4[-1]["s"] = 0

        return [x_list_0, y_list_0, z_list_0, z_param_list_0], [x_list_4, y_list_4, z_list_4, z_param_list_4]

    def create_road_ID1_branch(self, obj_node_data):
        """
        Create merge section (ID:1) of the branch structure.
        
        Args:
            obj_node_data: Object containing node and road data
            
        Returns:
            tuple: List containing road data and minimum border indices:
                  [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1],
                  min_id_border, min_id_border_2
        """
        # Khởi tạo các danh sách
        x_list_1 = []
        y_list_1 = []
        z_list_1 = []
        z_param_list_1 = []

        # Khởi tạo danh sách khoảng cách
        dist_list_1_04 = []
        dist_list_1_35 = []
        dist_list_1_2 = []
        n = 12

        # Xử lý từng điểm trong border
        for i in range(len(obj_node_data.border)):
            x_center = obj_node_data.border[i]["x"]
            y_center = obj_node_data.border[i]["y"]
            z_center = obj_node_data.border[i]["elevation"]
            z_param_center = obj_node_data.border[i]["elev_param"]

            center = np.array([x_center, y_center, z_center])

            # Xác định tọa độ cơ sở cho các danh sách liên kết
            if len(obj_node_data.obj_link_data_list[1].center) < n:
                base_04 = np.array([obj_node_data.obj_link_data_list[1].center[0]["x"], obj_node_data.obj_link_data_list[1].center[0]["y"], obj_node_data.obj_link_data_list[1].center[0]["elevation"]])
            else:
                base_04 = np.array(
                    [obj_node_data.obj_link_data_list[1].center[-n]["x"], obj_node_data.obj_link_data_list[1].center[-n]["y"], obj_node_data.obj_link_data_list[1].center[-n]["elevation"]]
                )

            if len(obj_node_data.obj_link_data_list[0].center) < n:
                base_35 = np.array([obj_node_data.obj_link_data_list[0].center[0]["x"], obj_node_data.obj_link_data_list[0].center[0]["y"], obj_node_data.obj_link_data_list[0].center[0]["elevation"]])
            else:
                base_35 = np.array(
                    [obj_node_data.obj_link_data_list[0].center[-n]["x"], obj_node_data.obj_link_data_list[0].center[-n]["y"], obj_node_data.obj_link_data_list[0].center[-n]["elevation"]]
                )

            base_2 = np.array([obj_node_data.obj_link_data_list[2].center[-1]["x"], obj_node_data.obj_link_data_list[2].center[-1]["y"], obj_node_data.obj_link_data_list[2].center[-1]["elevation"]])

            # Tính toán khoảng cách
            dist_04 = np.linalg.norm(center - base_04)
            dist_list_1_04.append(dist_04)

            dist_35 = np.linalg.norm(center - base_35)
            dist_list_1_35.append(dist_35)

            dist_2 = np.linalg.norm(center - base_2)
            dist_list_1_2.append(dist_2)

            # Thêm tọa độ và tham số vào danh sách
            x_list_1.append(x_center)
            y_list_1.append(y_center)
            z_list_1.append(z_center)
            z_param_list_1.append(z_param_center)

        # Tìm chỉ số của điểm gần nhất trong các danh sách khoảng cách
        min_id_border_04 = dist_list_1_04.index(min(dist_list_1_04))
        min_id_border_35 = dist_list_1_35.index(min(dist_list_1_35))
        min_id_border_2 = dist_list_1_2.index(min(dist_list_1_2))

        # Đảm bảo min_id_border_2 không phải là chỉ số cuối cùng
        if min_id_border_2 == len(x_list_1) - 1:
            min_id_border_2 = len(x_list_1) - 3

        # Tính toán chỉ số border nhỏ nhất
        min_id_border = min(min_id_border_04, min_id_border_35)

        # Tạo danh sách ID
        id_list_1 = [1] * len(x_list_1)

        # Trả về kết quả
        return [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1], min_id_border, min_id_border_2

    def create_road_ID04_branch(self, obj_node_data, base, min_id_border, list_1, flag=True):
        """
        Create post-merge mainline sections (ID:0/4).
        
        Args:
            obj_node_data: Object containing node and road data
            base: Base coordinates and parameters
            min_id_border: Minimum border index
            list_1: Merge section data
            flag: Processing flag (default: True)
            
        Returns:
            tuple: Lists containing road data for sections 0 and 4, updated list_1,
                  base coordinates, and flag04 status
        """

        [x_base, y_base, z_base, z_param_base] = base

        [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1] = list_1

        # Khởi tạo các danh sách tạm thời
        x_list_tmp = []
        y_list_tmp = []
        z_list_tmp = []
        z_param_list_tmp = []

        dist_list_tmp = []

        # Tính toán khoảng cách từ các điểm đến cơ sở
        for i in range(len(obj_node_data.obj_link_data_list[1].center)):
            x_center = obj_node_data.obj_link_data_list[1].center[i]["x"]
            y_center = obj_node_data.obj_link_data_list[1].center[i]["y"]
            z_center = obj_node_data.obj_link_data_list[1].center[i]["elevation"]
            z_param_center = obj_node_data.obj_link_data_list[1].center[i]["elev_param"]

            center = np.array([x_center, y_center, z_center])
            base = np.array([x_base, y_base, z_base])
            dist = np.linalg.norm(center - base)

            dist_list_tmp.append(dist)
            x_list_tmp.append(x_center)
            y_list_tmp.append(y_center)
            z_list_tmp.append(z_center)
            z_param_list_tmp.append(z_param_center)

        min_id = dist_list_tmp.index(min(dist_list_tmp))

        flag04 = False

        if (len(x_list_tmp) - min_id) < 5 and flag:
            flag04 = True
            min_id = 1

            if min_id_border == 0:
                # Cập nhật cơ sở từ danh sách link_data_list[2]
                x_base = obj_node_data.obj_link_data_list[2].center[-1]["x"]
                y_base = obj_node_data.obj_link_data_list[2].center[-1]["y"]
                z_base = obj_node_data.obj_link_data_list[2].center[-1]["elevation"]
                z_param_base = obj_node_data.obj_link_data_list[2].center[-1]["elev_param"]

                len_list_1 = len(x_list_1)
                x_list_1 = []
                y_list_1 = []
                z_list_1 = []
                z_param_list_1 = []

                for i in range(max(0, len(obj_node_data.obj_link_data_list[2].center) - len_list_1), len(obj_node_data.obj_link_data_list[2].center)):
                    x_center = obj_node_data.obj_link_data_list[2].center[i]["x"]
                    y_center = obj_node_data.obj_link_data_list[2].center[i]["y"]
                    z_center = obj_node_data.obj_link_data_list[2].center[i]["elevation"]
                    z_param_center = obj_node_data.obj_link_data_list[2].center[i]["elev_param"]

                    x_list_1.append(x_center)
                    y_list_1.append(y_center)
                    z_list_1.append(z_center)
                    z_param_list_1.append(z_param_center)
            else:
                # Cập nhật cơ sở từ danh sách x_list_1
                x_base = x_list_1[min_id_border]
                y_base = y_list_1[min_id_border]
                z_base = z_list_1[min_id_border]
                z_param_base = z_param_list_1[min_id_border]

                x_list_1 = x_list_1[: min_id_border + 1]
                y_list_1 = y_list_1[: min_id_border + 1]
                z_list_1 = z_list_1[: min_id_border + 1]
                z_param_list_1 = z_param_list_1[: min_id_border + 1]

            # Tính toán lại khoảng cách với cơ sở mới
            dist_list_tmp = []
            for i in range(len(obj_node_data.obj_link_data_list[1].center)):
                x_center = obj_node_data.obj_link_data_list[1].center[i]["x"]
                y_center = obj_node_data.obj_link_data_list[1].center[i]["y"]
                z_center = obj_node_data.obj_link_data_list[1].center[i]["elevation"]
                z_param_center = obj_node_data.obj_link_data_list[1].center[i]["elev_param"]

                center = np.array([x_center, y_center, z_center])
                base = np.array([x_base, y_base, z_base])
                dist = np.linalg.norm(center - base)

                dist_list_tmp.append(dist)

            min_id = dist_list_tmp.index(min(dist_list_tmp))

            if (len(x_list_tmp) - min_id) < 5:
                min_id = 1

        # Cắt các điểm trước min_id từ danh sách
        for i in range(min_id - 1):
            x_list_tmp.pop(0)
            y_list_tmp.pop(0)
            z_list_tmp.pop(0)
            z_param_list_tmp.pop(0)

        if len(x_list_tmp) < 2:
            raise ValueError("Right side road's points number is not enough")

        # Xoay polyline và điều chỉnh độ cao
        x_list_tmp, y_list_tmp = ajust.rotate_polyline((x_base, y_base), (x_list_tmp, y_list_tmp), False)

        if len(z_list_tmp) > 1:
            d = (z_base - z_list_tmp[0]) / (len(z_list_tmp) - 1)
            for i in range(len(z_list_tmp)):
                z_list_tmp[i] = z_list_tmp[i] + d * (len(z_list_tmp) - 1 - i)

        # Phân chia dữ liệu thành 2 nhánh đường
        list_0, list_4 = self.split_into_2_road_branch(x_list_tmp, y_list_tmp, z_list_tmp, z_param_list_tmp, x_base, y_base, z_base)

        [x_list_0, y_list_0, z_list_0, z_param_list_0] = list_0
        [x_list_4, y_list_4, z_list_4, z_param_list_4] = list_4

        id_list_1 = [1] * len(x_list_1)
        id_list_0 = [0] * len(x_list_0)
        id_list_4 = [4] * len(x_list_4)

        return (
            [id_list_0, x_list_0, y_list_0, z_list_0, z_param_list_0],
            [id_list_4, x_list_4, y_list_4, z_list_4, z_param_list_4],
            [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1],
            [x_base, y_base, z_base, z_param_base],
            flag04,
        )

    def create_road_ID2_branch(self, obj_node_data, min_id_border_2, list_1, flag=True):
        """
        Create pre-merge mainline section (ID:2).
        
        Args:
            obj_node_data: Object containing node and road data
            min_id_border_2: Minimum border index for section 2
            list_1: Merge section data
            flag: Processing flag (default: True)
            
        Returns:
            tuple: Lists containing road data for section 2 and updated list_1
        """

        [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1] = list_1

        # Khởi tạo các danh sách và biến cơ bản
        x_list_2 = []
        y_list_2 = []
        z_list_2 = []
        z_param_list_2 = []

        x_border_start = x_list_1[0]
        y_border_start = y_list_1[0]
        z_border_start = z_list_1[0]
        z_param_border_start = z_param_list_1[0]

        if flag:
            x_border_start_new = x_list_1[min_id_border_2]
            y_border_start_new = y_list_1[min_id_border_2]
            z_border_start_new = z_list_1[min_id_border_2]
            z_param_border_start_new = z_param_list_1[min_id_border_2]

        else:
            x_border_start_new = x_list_1[0]
            y_border_start_new = y_list_1[0]
            z_border_start_new = z_list_1[0]
            z_param_border_start_new = z_param_list_1[0]

        dist_list_tmp = []
        dist_list_tmp_new = []

        # Tính toán khoảng cách và lưu vào danh sách
        for i in range(len(obj_node_data.obj_link_data_list[2].center)):
            x_center = obj_node_data.obj_link_data_list[2].center[i]["x"]
            y_center = obj_node_data.obj_link_data_list[2].center[i]["y"]
            z_center = obj_node_data.obj_link_data_list[2].center[i]["elevation"]
            z_param_center = obj_node_data.obj_link_data_list[2].center[i]["elev_param"]

            center = np.array([x_center, y_center, z_center])
            border_start = np.array([x_border_start, y_border_start, z_border_start])
            border_start_new = np.array([x_border_start_new, y_border_start_new, z_border_start_new])

            dist = np.linalg.norm(center - border_start)
            dist_new = np.linalg.norm(center - border_start_new)

            dist_list_tmp.append(dist)
            dist_list_tmp_new.append(dist_new)

            x_list_2.append(x_center)
            y_list_2.append(y_center)
            z_list_2.append(z_center)
            z_param_list_2.append(z_param_center)

        min_id = dist_list_tmp.index(min(dist_list_tmp))
        min_id_new = dist_list_tmp_new.index(min(dist_list_tmp_new))

        if min_id < 10 and flag:
            min_id = min_id_new

            # Cập nhật danh sách x_list_1, y_list_1, z_list_1, z_param_list_1 và cơ sở
            x_list_1 = x_list_1[min_id_border_2:]
            y_list_1 = y_list_1[min_id_border_2:]
            z_list_1 = z_list_1[min_id_border_2:]
            z_param_list_1 = z_param_list_1[min_id_border_2:]

            id_list_1 = [1] * len(x_list_1)

            x_border_start = x_border_start_new
            y_border_start = y_border_start_new
            z_border_start = z_border_start_new
            z_param_border_start = z_param_border_start_new

        # Cắt các điểm không cần thiết
        for i in range(len(x_list_2) - min_id):
            x_list_2.pop(-1)
            y_list_2.pop(-1)
            z_list_2.pop(-1)
            z_param_list_2.pop(-1)

        if len(x_list_2) < 2:
            raise ValueError("1 main road's points number is not enough")

        # Xoay polyline và điều chỉnh độ cao
        x_list_2, y_list_2 = ajust.rotate_polyline((x_border_start, y_border_start), (x_list_2, y_list_2), True)

        z_list_2[-1] = z_list_1[0]

        id_list_2 = [2] * len(x_list_2)

        return [id_list_2, x_list_2, y_list_2, z_list_2, z_param_list_2], [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1]

    def create_road_ID35_branch(self, obj_node_data, base, min_id_border, list_1, flag04):
        """
        Create acceleration lane sections (ID:3/5).
        
        Args:
            obj_node_data: Object containing node and road data
            base: Base coordinates and parameters
            min_id_border: Minimum border index
            list_1: Merge section data
            flag04: Status flag from ID:0/4 processing
            
        Returns:
            tuple: Lists containing road data for sections 3 and 5, updated list_1,
                  base coordinates, and flag35 status
        """

        [x_base, y_base, z_base, z_param_base] = base
        [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1] = list_1

        x_list_tmp = []
        y_list_tmp = []
        z_list_tmp = []
        z_param_list_tmp = []
        dist_list_tmp = []

        for i in range(len(obj_node_data.obj_link_data_list[0].center)):
            x_center = obj_node_data.obj_link_data_list[0].center[i]["x"]
            y_center = obj_node_data.obj_link_data_list[0].center[i]["y"]
            z_center = obj_node_data.obj_link_data_list[0].center[i]["elevation"]
            z_param_center = obj_node_data.obj_link_data_list[0].center[i]["elev_param"]
            # 相対距離と方位を求める
            center = np.array([x_center, y_center, z_center])
            base = np.array([x_base, y_base, z_base])
            dist = np.linalg.norm(center - base)
            # dist=(x_center-x_base)**2 + (y_center -y_base)**2
            dist_list_tmp.append(dist)
            x_list_tmp.append(x_center)
            y_list_tmp.append(y_center)
            z_list_tmp.append(z_center)
            z_param_list_tmp.append(z_param_center)

        min_id = dist_list_tmp.index(min(dist_list_tmp))

        flag35 = False

        if (len(x_list_tmp) - min_id) < 5:
            flag35 = True

            min_id = 1

            if flag04 is False:

                if min_id_border == 0:

                    x_base = obj_node_data.obj_link_data_list[2].center[-1]["x"]
                    y_base = obj_node_data.obj_link_data_list[2].center[-1]["y"]
                    z_base = obj_node_data.obj_link_data_list[2].center[-1]["elevation"]
                    z_param_base = obj_node_data.obj_link_data_list[2].center[-1]["elev_param"]

                    len_list_1 = len(x_list_1)
                    x_list_1 = []
                    y_list_1 = []
                    z_list_1 = []
                    z_param_list_1 = []

                    for i in range(max(0, len(obj_node_data.obj_link_data_list[2].center) - len_list_1), len(obj_node_data.obj_link_data_list[2].center)):
                        x_center = obj_node_data.obj_link_data_list[2].center[i]["x"]
                        y_center = obj_node_data.obj_link_data_list[2].center[i]["y"]
                        z_center = obj_node_data.obj_link_data_list[2].center[i]["elevation"]
                        z_param_center = obj_node_data.obj_link_data_list[2].center[i]["elev_param"]

                        x_list_1.append(x_center)
                        y_list_1.append(y_center)
                        z_list_1.append(z_center)
                        z_param_list_1.append(z_param_center)
                else:
                    if len(x_list_1) - 1 < min_id_border:
                        min_id_border = 4

                        x_base = x_list_1[min_id_border]
                        y_base = y_list_1[min_id_border]
                        z_base = z_list_1[min_id_border]
                        z_param_base = z_param_list_1[min_id_border]

                        x_list_1 = x_list_1[: min_id_border + 1]
                        y_list_1 = y_list_1[: min_id_border + 1]
                        z_list_1 = z_list_1[: min_id_border + 1]
                        z_param_list_1 = z_param_list_1[: min_id_border + 1]

                    else:

                        x_base = x_list_1[min_id_border]
                        y_base = y_list_1[min_id_border]
                        z_base = z_list_1[min_id_border]
                        z_param_base = z_param_list_1[min_id_border]

                        x_list_1 = x_list_1[: min_id_border + 1]
                        y_list_1 = y_list_1[: min_id_border + 1]
                        z_list_1 = z_list_1[: min_id_border + 1]
                        z_param_list_1 = z_param_list_1[: min_id_border + 1]

                id_list_1 = [1] * len(x_list_1)

            dist_list_tmp = []

            for i in range(len(obj_node_data.obj_link_data_list[0].center)):
                x_center = obj_node_data.obj_link_data_list[0].center[i]["x"]
                y_center = obj_node_data.obj_link_data_list[0].center[i]["y"]
                z_center = obj_node_data.obj_link_data_list[0].center[i]["elevation"]
                z_param_center = obj_node_data.obj_link_data_list[0].center[i]["elev_param"]
                # 相対距離と方位を求める
                center = np.array([x_center, y_center, z_center])
                base = np.array([x_base, y_base, z_base])
                dist = np.linalg.norm(center - base)
                # dist=(x_center-x_base)**2 + (y_center -y_base)**2
                dist_list_tmp.append(dist)

            min_id = dist_list_tmp.index(min(dist_list_tmp))
            if (len(x_list_tmp) - min_id) < 5:
                min_id = 1

        # 最近傍点含め点列からカット(改善の予知あり)
        for i in range(min_id - 1):
            x_list_tmp.pop(0)
            y_list_tmp.pop(0)
            z_list_tmp.pop(0)
            z_param_list_tmp.pop(0)

        if len(x_list_tmp) < 2:
            print("left side road's points number is not enough")
            return

        x_list_tmp, y_list_tmp = ajust.rotate_polyline((x_base, y_base), (x_list_tmp, y_list_tmp), False)

        if len(z_list_tmp) > 1:
            d = (z_base - z_list_tmp[0]) / (len(z_list_tmp) - 1)
            for i in range(len(z_list_tmp)):
                z_list_tmp[i] = z_list_tmp[i] + d * (len(z_list_tmp) - 1 - i)

        list_3, list_5 = self.split_into_2_road_branch(x_list_tmp, y_list_tmp, z_list_tmp, z_param_list_tmp, x_base, y_base, z_base)

        [x_list_3, y_list_3, z_list_3, z_param_list_3] = list_3

        [x_list_5, y_list_5, z_list_5, z_param_list_5] = list_5

        id_list_3 = [3] * len(x_list_3)
        id_list_5 = [5] * len(x_list_5)
        id_list_1 = [1] * len(x_list_1)

        return (
            [id_list_3, x_list_3, y_list_3, z_list_3, z_param_list_3],
            [id_list_5, x_list_5, y_list_5, z_list_5, z_param_list_5],
            [id_list_1, x_list_1, y_list_1, z_list_1, z_param_list_1],
            [x_base, y_base, z_base, z_param_base],
            flag35,
        )
