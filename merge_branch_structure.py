import pandas as pd
import math

from submodule import ajust


class MergeBranchStructure:
    def __init__(self):
        self.df_polyline_2 = []

    # Edit the location data of connected road segments so that they match in reality.
    def make_df_polyline_combine(self, merge, branch, index_merge, index_branch):

        # region Merge

        merge_offset_list = merge.df_lane_info["offset"].tolist()

        merge_id_list = merge.df_polyline["ID"].tolist()
        merge_x_list = merge.df_polyline["x"].tolist()
        merge_y_list = merge.df_polyline["y"].tolist()
        merge_z_list = merge.df_polyline["elev"].tolist()

        merge_z_s_list = merge.df_polyline["length"].tolist()
        merge_z_a_list = merge.df_polyline["elev_a"].tolist()
        merge_z_b_list = merge.df_polyline["elev_b"].tolist()
        merge_z_c_list = merge.df_polyline["elev_c"].tolist()
        merge_z_d_list = merge.df_polyline["elev_d"].tolist()

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
        merge_id_num_1 = len(merge_id_list_1) + len(merge_id_list_4) + len(merge_id_list_0)
        merge_id_num_2 = len(merge_id_list_2) + len(merge_id_list_1) + len(merge_id_list_4) + len(merge_id_list_0)
        merge_id_num_3 = len(merge_id_list_3) + len(merge_id_list_2) + len(merge_id_list_1) + len(merge_id_list_4) + len(merge_id_list_0)
        merge_id_num_5 = len(merge_id_list)

        hdg_start_main_merge = merge.df_polyline["hdg"].tolist()[0]
        hdg_start_sub_merge = merge.df_polyline["hdg"].tolist()[merge_id_num_2]

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
        merge_z_param_list_4.extend(merge_z_param_list[merge_id_num_0:merge_id_num_4])
        merge_z_param_list_1.extend(merge_z_param_list[merge_id_num_4:merge_id_num_1])
        merge_z_param_list_2.extend(merge_z_param_list[merge_id_num_1:merge_id_num_2])
        merge_z_param_list_3.extend(merge_z_param_list[merge_id_num_2:merge_id_num_3])
        merge_z_param_list_5.extend(merge_z_param_list[merge_id_num_3:merge_id_num_5])

        # plt.plot(merge_x_list_0,merge_y_list_0,marker='o',label='0')
        # plt.plot(merge_x_list_4,merge_y_list_4,marker='o',label='4')
        # plt.plot(merge_x_list_1,merge_y_list_1,marker='o',label='1')
        # plt.plot(merge_x_list_2,merge_y_list_2,marker='o',label='2')
        # plt.plot(merge_x_list_3,merge_y_list_3,marker='o',label='3')
        # plt.plot(merge_x_list_5,merge_y_list_5,marker='o',label='5')

        # endregion

        ########################################################

        # region Branch

        branch_offset_list = branch.df_lane_info["offset"].tolist()
        hdg_start_main_branch = branch.df_polyline["hdg"].tolist()[0]

        branch_id_list = branch.df_polyline["ID"].tolist()
        branch_x_list = branch.df_polyline["x"].tolist()
        branch_y_list = branch.df_polyline["y"].tolist()
        branch_z_list = branch.df_polyline["elev"].tolist()

        branch_z_s_list = branch.df_polyline["length"].tolist()
        branch_z_a_list = branch.df_polyline["elev_a"].tolist()
        branch_z_b_list = branch.df_polyline["elev_b"].tolist()
        branch_z_c_list = branch.df_polyline["elev_c"].tolist()
        branch_z_d_list = branch.df_polyline["elev_d"].tolist()

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
        branch_id_num_4 = len(branch_id_list_2) + len(branch_id_list_1) + len(branch_id_list_4)
        branch_id_num_0 = len(branch_id_list_2) + len(branch_id_list_1) + len(branch_id_list_4) + len(branch_id_list_0)
        branch_id_num_5 = len(branch_id_list_2) + len(branch_id_list_1) + len(branch_id_list_4) + len(branch_id_list_0) + len(branch_id_list_5)
        branch_id_num_3 = len(branch_id_list)

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
        branch_z_param_list_1.extend(branch_z_param_list[branch_id_num_2:branch_id_num_1])
        branch_z_param_list_4.extend(branch_z_param_list[branch_id_num_1:branch_id_num_4])
        branch_z_param_list_0.extend(branch_z_param_list[branch_id_num_4:branch_id_num_0])
        branch_z_param_list_5.extend(branch_z_param_list[branch_id_num_0:branch_id_num_5])
        branch_z_param_list_3.extend(branch_z_param_list[branch_id_num_5:branch_id_num_3])

        # plt.plot(branch_x_list_0,branch_y_list_0,marker='o',label='0')
        # plt.plot(branch_x_list_4,branch_y_list_4,marker='o',label='4')
        # plt.plot(branch_x_list_1,branch_y_list_1,marker='o',label='1')
        # plt.plot(branch_x_list_2,branch_y_list_2,marker='o',label='2')
        # plt.plot(branch_x_list_3,branch_y_list_3,marker='o',label='3')
        # plt.plot(branch_x_list_5,branch_y_list_5,marker='o',label='5')

        # plt.legend()
        # plt.show()

        # endregion

        ########################################################

        if index_branch == 1 and index_merge == 0:

            try:

                # raise ValueError("DDDDDDDDDDDDDDDD")

                merge_x_list_3.pop(-1)
                merge_y_list_3.pop(-1)
                branch_x_list_4.pop(-1)
                branch_y_list_4.pop(-1)

                x_curve1 = branch_x_list_4 + branch_x_list_0
                y_curve1 = branch_y_list_4 + branch_y_list_0
                x_curve2 = merge_x_list_3 + merge_x_list_5
                y_curve2 = merge_y_list_3 + merge_y_list_5

                start_point = (branch_x_list_0[0], branch_y_list_0[0])
                end_point = (merge_x_list_3[-1], merge_y_list_3[-1])

                for i in range(len(branch_offset_list) - 1, -1, -1):
                    if branch_offset_list[i] != 0:
                        offset_branch_0 = branch_offset_list[i]
                        break

                offset = -offset_branch_0

                x_curve1, y_curve1, x_curve2, y_curve2 = ajust.make_combine_road_data(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset)

                ########################################################

                merge_id_list_3_new = []
                merge_x_list_3_new = []
                merge_y_list_3_new = []
                merge_z_list_3_new = []
                merge_z_param_list_3_new = []

                merge_id_list_5_new = []
                merge_x_list_5_new = []
                merge_y_list_5_new = []
                merge_z_list_5_new = []
                merge_z_param_list_5_new = []

                id_num3 = len(x_curve2) - 3
                id_num5 = 3

                merge_id_list_3_new = [3] * int(id_num3)
                merge_x_list_3_new.extend(x_curve2[0:id_num3])
                merge_y_list_3_new.extend(y_curve2[0:id_num3])
                merge_z_list_3_new = merge_z_list_3[(len(merge_z_list_3) - len(merge_x_list_3_new)): len(merge_z_list_3)]
                merge_z_param_list_3_new = merge_z_param_list_3[(len(merge_z_list_3) - len(merge_x_list_3_new)): len(merge_z_list_3)]

                merge_id_list_5_new = [5] * int(id_num5)
                merge_x_list_5_new.extend(x_curve2[id_num3: len(x_curve2)])
                merge_y_list_5_new.extend(y_curve2[id_num3: len(x_curve2)])
                merge_z_list_5_new = merge_z_list_5
                merge_z_param_list_5_new = merge_z_param_list_5

                merge_id_list_5_new.insert(0, 5)
                merge_x_list_5_new.insert(0, merge_x_list_3_new[-1])
                merge_y_list_5_new.insert(0, merge_y_list_3_new[-1])

                # plt.plot(merge_x_list_3_new,merge_y_list_3_new,marker='o',label='33')
                # plt.plot(merge_x_list_5_new,merge_y_list_5_new,marker='o',label='55')

                branch_id_list_0_new = []
                branch_x_list_0_new = []
                branch_y_list_0_new = []
                branch_z_list_0_new = []
                branch_z_param_list_0_new = []

                branch_id_list_4_new = []
                branch_x_list_4_new = []
                branch_y_list_4_new = []
                branch_z_list_4_new = []
                branch_z_param_list_4_new = []

                id_num0 = len(x_curve1) - 3
                id_num4 = 3

                branch_id_list_0_new = [0] * int(id_num0)
                branch_x_list_0_new.extend(x_curve1[id_num4: len(x_curve1)])
                branch_y_list_0_new.extend(y_curve1[id_num4: len(x_curve1)])
                branch_z_list_0_new = branch_z_list_0[0: len(branch_x_list_0_new)]
                branch_z_param_list_0_new = branch_z_param_list_0[0: len(branch_x_list_0_new)]

                branch_id_list_4_new = [4] * int(id_num4)
                branch_x_list_4_new.extend(x_curve1[0:id_num4])
                branch_y_list_4_new.extend(y_curve1[0:id_num4])
                branch_z_list_4_new = branch_z_list_4
                branch_z_param_list_4_new = branch_z_param_list_4

                branch_id_list_4_new.insert(0, 4)
                branch_x_list_4_new.insert(len(branch_x_list_4_new), branch_x_list_0_new[0])
                branch_y_list_4_new.insert(len(branch_y_list_4_new), branch_y_list_0_new[0])

                branch_z_list_0_new[-1] = merge_z_list_3_new[0]
                branch_z_param_list_0_new[-1] = merge_z_param_list_3_new[0]

                # plt.plot(branch_x_list_4_new,branch_y_list_4_new,marker='o',label='44')
                # plt.plot(branch_x_list_0_new,branch_y_list_0_new,marker='o',label='00')

                # plt.legend()

                merge_id_list_3 = merge_id_list_3_new
                merge_x_list_3 = merge_x_list_3_new
                merge_y_list_3 = merge_y_list_3_new
                merge_z_list_3 = merge_z_list_3_new
                merge_z_param_list_3 = merge_z_param_list_3_new

                merge_id_list_5 = merge_id_list_5_new
                merge_x_list_5 = merge_x_list_5_new
                merge_y_list_5 = merge_y_list_5_new
                merge_z_list_5 = merge_z_list_5_new
                merge_z_param_list_5 = merge_z_param_list_5_new

                branch_id_list_0 = branch_id_list_0_new
                branch_x_list_0 = branch_x_list_0_new
                branch_y_list_0 = branch_y_list_0_new
                branch_z_list_0 = branch_z_list_0_new
                branch_z_param_list_0 = branch_z_param_list_0_new

                branch_id_list_4 = branch_id_list_4_new
                branch_x_list_4 = branch_x_list_4_new
                branch_y_list_4 = branch_y_list_4_new
                branch_z_list_4 = branch_z_list_4_new
                branch_z_param_list_4 = branch_z_param_list_4_new

            except Exception as error:

                print("except: index_merge == 0 and index_branch == 1", error)

                start_point = (branch_x_list_4[0], branch_y_list_4[0], branch_z_list_4[0])
                end_point = (merge_x_list_5[-1], merge_y_list_5[-1], merge_z_list_5[-1])

                for i in range(len(branch_offset_list) - 1, -1, -1):
                    if branch_offset_list[i] != 0:
                        offset_branch_0 = branch_offset_list[i]
                        break

                offset = -offset_branch_0

                if error.args[0] == 1:
                    print("This is a serious error that requires changing the road data to connect the road correctly. XXXXXXXXXX")

                x_curve1, y_curve1, z_curve1, z_param_curve1, x_curve2, y_curve2, z_curve2, z_param_curve2 = ajust.make_new_combine_road_data(start_point, end_point, offset)

                ########################################################

                merge_id_list_3_new = []
                merge_x_list_3_new = []
                merge_y_list_3_new = []
                merge_z_list_3_new = []
                merge_z_param_list_3_new = []

                merge_id_list_5_new = []
                merge_x_list_5_new = []
                merge_y_list_5_new = []
                merge_z_list_5_new = []
                merge_z_param_list_5_new = []

                id_num3 = len(x_curve2) - 3
                id_num5 = 3

                merge_id_list_3_new = [3] * int(id_num3)
                merge_x_list_3_new.extend(x_curve2[0:id_num3])
                merge_y_list_3_new.extend(y_curve2[0:id_num3])
                merge_z_list_3_new.extend(z_curve2[0:id_num3])
                merge_z_param_list_3_new.extend(z_param_curve2[0:id_num3])

                merge_id_list_5_new = [5] * int(id_num5)
                merge_x_list_5_new.extend(x_curve2[id_num3: len(x_curve2)])
                merge_y_list_5_new.extend(y_curve2[id_num3: len(x_curve2)])
                merge_z_list_5_new.extend(z_curve2[id_num3: len(x_curve2)])
                merge_z_param_list_5_new.extend(z_param_curve2[id_num3: len(x_curve2)])

                merge_id_list_5_new.insert(0, 5)
                merge_x_list_5_new.insert(0, merge_x_list_3_new[-1])
                merge_y_list_5_new.insert(0, merge_y_list_3_new[-1])
                merge_z_list_5_new.insert(0, merge_z_list_3_new[-1])
                merge_z_param_list_5_new.insert(0, merge_z_param_list_3_new[-1])

                # plt.plot(merge_x_list_3_new,merge_y_list_3_new,marker='o',label='33')
                # plt.plot(merge_x_list_5_new,merge_y_list_5_new,marker='o',label='55')

                branch_id_list_0_new = []
                branch_x_list_0_new = []
                branch_y_list_0_new = []
                branch_z_list_0_new = []
                branch_z_param_list_0_new = []

                branch_id_list_4_new = []
                branch_x_list_4_new = []
                branch_y_list_4_new = []
                branch_z_list_4_new = []
                branch_z_param_list_4_new = []

                id_num0 = len(x_curve1) - 3
                id_num4 = 3

                branch_id_list_0_new = [0] * int(id_num0)
                branch_x_list_0_new.extend(x_curve1[id_num4: len(x_curve1)])
                branch_y_list_0_new.extend(y_curve1[id_num4: len(x_curve1)])
                branch_z_list_0_new.extend(z_curve1[id_num4: len(x_curve1)])
                branch_z_param_list_0_new.extend(z_param_curve1[id_num4: len(x_curve1)])

                branch_id_list_4_new = [4] * int(id_num4)
                branch_x_list_4_new.extend(x_curve1[0:id_num4])
                branch_y_list_4_new.extend(y_curve1[0:id_num4])
                branch_z_list_4_new.extend(z_curve1[0:id_num4])
                branch_z_param_list_4_new.extend(z_param_curve1[0:id_num4])

                branch_id_list_4_new.insert(0, 4)
                branch_x_list_4_new.insert(len(branch_x_list_4_new), branch_x_list_0_new[0])
                branch_y_list_4_new.insert(len(branch_y_list_4_new), branch_y_list_0_new[0])
                branch_z_list_4_new.insert(len(branch_z_list_4_new), branch_z_list_0_new[0])
                branch_z_param_list_4_new.insert(len(branch_z_param_list_4_new), branch_z_param_list_0_new[0])

                branch_z_list_0_new[-1] = merge_z_list_3_new[0]
                branch_z_param_list_0_new[-1] = merge_z_param_list_3_new[0]

                # plt.plot(branch_x_list_4_new,branch_y_list_4_new,marker='o',label='44')
                # plt.plot(branch_x_list_0_new,branch_y_list_0_new,marker='o',label='00')

                # plt.legend()

                merge_id_list_3 = merge_id_list_3_new
                merge_x_list_3 = merge_x_list_3_new
                merge_y_list_3 = merge_y_list_3_new
                merge_z_list_3 = merge_z_list_3_new
                merge_z_param_list_3 = merge_z_param_list_3_new

                merge_id_list_5 = merge_id_list_5_new
                merge_x_list_5 = merge_x_list_5_new
                merge_y_list_5 = merge_y_list_5_new
                merge_z_list_5 = merge_z_list_5_new
                merge_z_param_list_5 = merge_z_param_list_5_new

                branch_id_list_0 = branch_id_list_0_new
                branch_x_list_0 = branch_x_list_0_new
                branch_y_list_0 = branch_y_list_0_new
                branch_z_list_0 = branch_z_list_0_new
                branch_z_param_list_0 = branch_z_param_list_0_new

                branch_id_list_4 = branch_id_list_4_new
                branch_x_list_4 = branch_x_list_4_new
                branch_y_list_4 = branch_y_list_4_new
                branch_z_list_4 = branch_z_list_4_new
                branch_z_param_list_4 = branch_z_param_list_4_new

        elif index_branch == 0 and index_merge == 1:

            try:

                merge_x_list_0.pop(-1)
                merge_y_list_0.pop(-1)
                branch_x_list_5.pop(-1)
                branch_y_list_5.pop(-1)

                x_curve2 = merge_x_list_0 + merge_x_list_4
                y_curve2 = merge_y_list_0 + merge_y_list_4
                x_curve1 = branch_x_list_5 + branch_x_list_3
                y_curve1 = branch_y_list_5 + branch_y_list_3

                start_point = (x_curve1[0], y_curve1[0])
                end_point = (x_curve2[-1], y_curve2[-1])

                offset = merge_offset_list[0]

                x_curve1, y_curve1, x_curve2, y_curve2 = ajust.make_combine_road_data(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset)

                ########################################################

                merge_id_list_0_new = []
                merge_x_list_0_new = []
                merge_y_list_0_new = []
                merge_z_list_0_new = []
                merge_z_param_list_0_new = []

                merge_id_list_4_new = []
                merge_x_list_4_new = []
                merge_y_list_4_new = []
                merge_z_list_4_new = []
                merge_z_param_list_4_new = []

                id_num0 = len(x_curve2) - 3
                id_num4 = 3

                merge_id_list_0_new = [0] * int(id_num0)
                merge_x_list_0_new.extend(x_curve2[0:id_num0])
                merge_y_list_0_new.extend(y_curve2[0:id_num0])
                merge_z_list_0_new = merge_z_list_0[(len(merge_z_list_0) - len(merge_x_list_0_new)): len(merge_z_list_0)]
                merge_z_param_list_0_new = merge_z_param_list_0[(len(merge_z_list_0) - len(merge_x_list_0_new)): len(merge_z_list_0)]

                merge_id_list_4_new = [4] * int(id_num4)
                merge_x_list_4_new.extend(x_curve2[id_num0: len(x_curve2)])
                merge_y_list_4_new.extend(y_curve2[id_num0: len(x_curve2)])
                merge_z_list_4_new = merge_z_list_4
                merge_z_param_list_4_new = merge_z_param_list_4

                merge_id_list_4_new.insert(0, 4)
                merge_x_list_4_new.insert(0, merge_x_list_0_new[-1])
                merge_y_list_4_new.insert(0, merge_y_list_0_new[-1])

                # plt.plot(merge_x_list_0_new,merge_y_list_0_new,marker='o',label='00')
                # plt.plot(merge_x_list_4_new,merge_y_list_4_new,marker='o',label='44')

                branch_id_list_3_new = []
                branch_x_list_3_new = []
                branch_y_list_3_new = []
                branch_z_list_3_new = []
                branch_z_param_list_3_new = []

                branch_id_list_5_new = []
                branch_x_list_5_new = []
                branch_y_list_5_new = []
                branch_z_list_5_new = []
                branch_z_param_list_5_new = []

                id_num3 = len(x_curve1) - 3
                id_num5 = 3

                branch_id_list_3_new = [3] * int(id_num3)
                branch_x_list_3_new.extend(x_curve1[id_num5: len(x_curve1)])
                branch_y_list_3_new.extend(y_curve1[id_num5: len(x_curve1)])
                branch_z_list_3_new = branch_z_list_3[0: len(branch_x_list_3_new)]
                branch_z_param_list_3_new = branch_z_param_list_3[0: len(branch_x_list_3_new)]

                branch_id_list_5_new = [5] * int(id_num5)
                branch_x_list_5_new.extend(x_curve1[0:id_num5])
                branch_y_list_5_new.extend(y_curve1[0:id_num5])
                branch_z_list_5_new = branch_z_list_5
                branch_z_param_list_5_new = branch_z_param_list_5

                branch_id_list_5_new.insert(0, 5)
                branch_x_list_5_new.insert(len(branch_x_list_5_new), branch_x_list_3_new[0])
                branch_y_list_5_new.insert(len(branch_y_list_5_new), branch_y_list_3_new[0])

                branch_z_list_3_new[-1] = merge_z_list_0_new[0]
                branch_z_param_list_3_new[-1] = merge_z_param_list_0_new[0]

                # plt.plot(branch_x_list_5_new,branch_y_list_5_new,marker='o',label='55')
                # plt.plot(branch_x_list_3_new,branch_y_list_3_new,marker='o',label='33')

                # plt.legend()

                merge_id_list_0 = merge_id_list_0_new
                merge_x_list_0 = merge_x_list_0_new
                merge_y_list_0 = merge_y_list_0_new
                merge_z_list_0 = merge_z_list_0_new
                merge_z_param_list_0 = merge_z_param_list_0_new

                merge_id_list_4 = merge_id_list_4_new
                merge_x_list_4 = merge_x_list_4_new
                merge_y_list_4 = merge_y_list_4_new
                merge_z_list_4 = merge_z_list_4_new
                merge_z_param_list_4 = merge_z_param_list_4_new

                branch_id_list_3 = branch_id_list_3_new
                branch_x_list_3 = branch_x_list_3_new
                branch_y_list_3 = branch_y_list_3_new
                branch_z_list_3 = branch_z_list_3_new
                branch_z_param_list_3 = branch_z_param_list_3_new

                branch_id_list_5 = branch_id_list_5_new
                branch_x_list_5 = branch_x_list_5_new
                branch_y_list_5 = branch_y_list_5_new
                branch_z_list_5 = branch_z_list_5_new
                branch_z_param_list_5 = branch_z_param_list_5_new

            except Exception as error:

                print("except: index_merge == 1 and index_branch == 0", error)

                start_point = (branch_x_list_5[0], branch_y_list_5[0], branch_z_list_5[0])
                end_point = (merge_x_list_4[-1], merge_y_list_4[-1], merge_z_list_4[-1])

                offset = merge_offset_list[0]

                if error.args[0] == 1:
                    print("This is a serious error that requires changing the road data to connect the road correctly.")
                    dist_list_branch_1 = []
                    for i in range(len(branch_x_list_1)):
                        dist_list_branch_1.append((branch_x_list_1[i] - end_point[0]) ** 2 + (branch_y_list_1[i] - end_point[1]) ** 2)
                    min_id_branch_1 = dist_list_branch_1.index(min(dist_list_branch_1))

                    if min_id_branch_1 - 100 > 3:
                        min_id_branch_1 = min_id_branch_1 - 100
                    else:
                        min_id_branch_1 = 3

                    for i in range(len(branch_x_list_1) - min_id_branch_1):
                        branch_x_list_1.pop(-1)
                        branch_y_list_1.pop(-1)
                        branch_z_list_1.pop(-1)
                        branch_z_param_list_1.pop(-1)
                        branch_id_list_1.pop(-1)

                    branch_x_list_4_0 = branch_x_list_4[:-1] + branch_x_list_0
                    branch_y_list_4_0 = branch_y_list_4[:-1] + branch_y_list_0

                    # dist_x = -branch_x_list_4_0[0] + branch_x_list_1[-1]
                    # dist_y = -branch_y_list_4_0[0] + branch_y_list_1[-1]

                    # for i in range(len(branch_x_list_4_0)):
                    #     branch_x_list_4_0[i] = branch_x_list_4_0[i] + (dist_x / (len(branch_x_list_4_0) - 1)) * (
                    #         len(branch_x_list_4_0) - 1 - i
                    #     )
                    #     branch_y_list_4_0[i] = branch_y_list_4_0[i] + (dist_y / (len(branch_y_list_4_0) - 1)) * (
                    #         len(branch_y_list_4_0) - 1 - i
                    #     )

                    branch_x_list_4_0, branch_y_list_4_0 = ajust.rotate_polyline((branch_x_list_1[-1], branch_y_list_1[-1]), (branch_x_list_4_0, branch_y_list_4_0), False)

                    branch_z_list_4[0] = branch_z_list_1[-1]

                    # plt.plot(branch_x_list_4_0,branch_y_list_4_0,linestyle='--',color='blue')

                    branch_x_list_0 = []
                    branch_y_list_0 = []
                    branch_x_list_4 = []
                    branch_y_list_4 = []

                    branch_x_list_0.extend(branch_x_list_4_0[3: len(branch_x_list_4_0)])
                    branch_y_list_0.extend(branch_y_list_4_0[3: len(branch_y_list_4_0)])

                    branch_x_list_4.extend(branch_x_list_4_0[0:3])
                    branch_y_list_4.extend(branch_y_list_4_0[0:3])

                    branch_x_list_4.insert(len(branch_x_list_4), branch_x_list_0[0])
                    branch_y_list_4.insert(len(branch_y_list_4), branch_y_list_0[0])

                    # plt.plot(branch_x_list_4,branch_y_list_4,marker='o',label='4')
                    # plt.plot(branch_x_list_0,branch_y_list_0,marker='o',label='0')

                    branch_x_list_5_3 = branch_x_list_5[:-1] + branch_x_list_3
                    branch_y_list_5_3 = branch_y_list_5[:-1] + branch_y_list_3

                    # dist_x = -branch_x_list_5_3[0] + branch_x_list_1[-1]
                    # dist_y = -branch_y_list_5_3[0] + branch_y_list_1[-1]

                    # for i in range(len(branch_x_list_5_3)):
                    #     branch_x_list_5_3[i] = branch_x_list_5_3[i] + (dist_x / (len(branch_x_list_5_3) - 1)) * (
                    #         len(branch_x_list_5_3) - 1 - i
                    #     )
                    #     branch_y_list_5_3[i] = branch_y_list_5_3[i] + (dist_y / (len(branch_y_list_5_3) - 1)) * (
                    #         len(branch_y_list_5_3) - 1 - i
                    #     )

                    branch_x_list_5_3, branch_y_list_5_3 = ajust.rotate_polyline((branch_x_list_1[-1], branch_y_list_1[-1]), (branch_x_list_5_3, branch_y_list_5_3), False)

                    branch_z_list_5[0] = branch_z_list_1[-1]

                    # plt.plot(branch_x_list_5_3,branch_y_list_5_3,linestyle='--',color='blue')

                    branch_x_list_3 = []
                    branch_y_list_3 = []
                    branch_x_list_5 = []
                    branch_y_list_5 = []

                    branch_x_list_3.extend(branch_x_list_5_3[3: len(branch_x_list_5_3)])
                    branch_y_list_3.extend(branch_y_list_5_3[3: len(branch_y_list_5_3)])

                    branch_x_list_5.extend(branch_x_list_5_3[0:3])
                    branch_y_list_5.extend(branch_y_list_5_3[0:3])

                    branch_x_list_5.insert(len(branch_x_list_5), branch_x_list_3[0])
                    branch_y_list_5.insert(len(branch_y_list_5), branch_y_list_3[0])

                    # plt.plot(branch_x_list_5,branch_y_list_5,marker='o',label='5')
                    # plt.plot(branch_x_list_3,branch_y_list_3,marker='o',label='3')

                    start_point = (branch_x_list_5[0], branch_y_list_5[0], branch_z_list_5[0])
                    end_point = (merge_x_list_4[-1], merge_y_list_4[-1], merge_z_list_4[-1])

                x_curve1, y_curve1, z_curve1, z_param_curve1, x_curve2, y_curve2, z_curve2, z_param_curve2 = ajust.make_new_combine_road_data(start_point, end_point, offset)

                ########################################################

                merge_id_list_0_new = []
                merge_id_list_4_new = []
                merge_x_list_0_new = []
                merge_x_list_4_new = []
                merge_y_list_0_new = []
                merge_y_list_4_new = []
                merge_z_list_0_new = []
                merge_z_list_4_new = []
                merge_z_param_list_0_new = []
                merge_z_param_list_4_new = []

                id_num0 = len(x_curve2) - 3
                id_num4 = len(x_curve2) - id_num0
                merge_id_list_0_new = [0] * int(id_num0)
                merge_id_list_4_new = [4] * int(id_num4)

                merge_x_list_4_new.extend(x_curve2[id_num0: len(x_curve2)])
                merge_y_list_4_new.extend(y_curve2[id_num0: len(y_curve2)])
                merge_z_list_4_new.extend(z_curve2[id_num0: len(z_curve2)])
                merge_z_param_list_4_new.extend(z_param_curve2[id_num0: len(z_curve2)])

                merge_x_list_0_new.extend(x_curve2[0:id_num0])
                merge_y_list_0_new.extend(y_curve2[0:id_num0])
                merge_z_list_0_new.extend(z_curve2[0:id_num0])
                merge_z_param_list_0_new.extend(z_param_curve2[0:id_num0])

                merge_id_list_4_new.insert(0, 4)
                merge_x_list_4_new.insert(0, merge_x_list_0_new[-1])
                merge_y_list_4_new.insert(0, merge_y_list_0_new[-1])
                merge_z_list_4_new.insert(0, merge_z_list_0_new[-1])
                merge_z_param_list_4_new.insert(0, merge_z_param_list_0_new[-1])

                # plt.plot(merge_x_list_0_new,merge_y_list_0_new,marker='o',label='00')
                # plt.plot(merge_x_list_4_new,merge_y_list_4_new,marker='o',label='44')

                branch_id_list_3_new = []
                branch_x_list_3_new = []
                branch_y_list_3_new = []
                branch_z_list_3_new = []
                branch_z_param_list_3_new = []

                branch_id_list_5_new = []
                branch_x_list_5_new = []
                branch_y_list_5_new = []
                branch_z_list_5_new = []
                branch_z_param_list_5_new = []

                id_num3 = len(x_curve1) - 3
                id_num5 = len(x_curve1) - id_num3

                branch_id_list_3_new = [3] * int(id_num3)
                branch_x_list_3_new.extend(x_curve1[id_num5: len(x_curve1)])
                branch_y_list_3_new.extend(y_curve1[id_num5: len(x_curve1)])
                branch_z_list_3_new.extend(z_curve1[id_num5: len(x_curve1)])
                branch_z_param_list_3_new.extend(z_param_curve1[id_num5: len(x_curve1)])

                branch_id_list_5_new = [5] * int(id_num5)
                branch_x_list_5_new.extend(x_curve1[0:id_num5])
                branch_y_list_5_new.extend(y_curve1[0:id_num5])
                branch_z_list_5_new.extend(z_curve1[0:id_num5])
                branch_z_param_list_5_new.extend(z_param_curve1[0:id_num5])

                branch_id_list_5_new.insert(0, 5)
                branch_x_list_5_new.insert(len(branch_x_list_5_new), branch_x_list_3_new[0])
                branch_y_list_5_new.insert(len(branch_y_list_5_new), branch_y_list_3_new[0])
                branch_z_list_5_new.insert(len(branch_z_list_5_new), branch_z_list_3_new[0])
                branch_z_param_list_5_new.insert(len(branch_z_param_list_5_new), branch_z_param_list_3_new[0])

                # plt.plot(branch_x_list_5_new,branch_y_list_5_new,marker='o',label='55')
                # plt.plot(branch_x_list_3_new,branch_y_list_3_new,marker='o',label='33')

                # plt.legend()

                merge_id_list_0 = merge_id_list_0_new
                merge_x_list_0 = merge_x_list_0_new
                merge_y_list_0 = merge_y_list_0_new
                merge_z_list_0 = merge_z_list_0_new
                merge_z_param_list_0 = merge_z_param_list_0_new

                merge_id_list_4 = merge_id_list_4_new
                merge_x_list_4 = merge_x_list_4_new
                merge_y_list_4 = merge_y_list_4_new
                merge_z_list_4 = merge_z_list_4_new
                merge_z_param_list_4 = merge_z_param_list_4_new

                branch_id_list_3 = branch_id_list_3_new
                branch_x_list_3 = branch_x_list_3_new
                branch_y_list_3 = branch_y_list_3_new
                branch_z_list_3 = branch_z_list_3_new
                branch_z_param_list_3 = branch_z_param_list_3_new

                branch_id_list_5 = branch_id_list_5_new
                branch_x_list_5 = branch_x_list_5_new
                branch_y_list_5 = branch_y_list_5_new
                branch_z_list_5 = branch_z_list_5_new
                branch_z_param_list_5 = branch_z_param_list_5_new

        elif index_merge == 2 and index_branch == 2:

            try:

                # raise ValueError("DDDDDDDDDDDDDDDD")

                merge_x_list_1.pop(-1)
                merge_y_list_1.pop(-1)
                branch_x_list_2.pop(-1)
                branch_y_list_2.pop(-1)

                x_curve1 = merge_x_list_1 + merge_x_list_2
                y_curve1 = merge_y_list_1 + merge_y_list_2
                x_curve2 = branch_x_list_2 + branch_x_list_1
                y_curve2 = branch_y_list_2 + branch_y_list_1

                start_point = (merge_x_list_1[0], merge_y_list_1[0])
                end_point = (branch_x_list_1[-1], branch_y_list_1[-1])

                offset_branch_2 = branch_offset_list[0]

                for i in range(len(merge_offset_list) - 1, -1, -1):
                    if merge_offset_list[i] != 0:
                        offset_merge_2 = merge_offset_list[i]
                        break

                offset = offset_branch_2 - offset_merge_2

                x_curve1, y_curve1, x_curve2, y_curve2 = ajust.make_combine_road_data(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset)

                ########################################################

                branch_id_list_1_new = []
                branch_x_list_1_new = []
                branch_y_list_1_new = []
                branch_z_list_1_new = []
                branch_z_param_list_1_new = []

                branch_id_list_2_new = []
                branch_x_list_2_new = []
                branch_y_list_2_new = []
                branch_z_list_2_new = []
                branch_z_param_list_2_new = []

                z_curve2 = []
                z_param_curve2 = []

                if len(x_curve2) == len(branch_x_list_2) + len(branch_x_list_1):
                    id_num1 = len(branch_x_list_1)
                    id_num2 = len(branch_x_list_2)
                else:
                    id_num1 = int(round(len(x_curve2) / 2, 0))
                    id_num2 = len(x_curve2) - id_num1

                branch_z_list_2.pop(-1)
                branch_z_list_2_1 = branch_z_list_2 + branch_z_list_1
                z_curve2.extend(branch_z_list_2_1[(len(branch_z_list_2_1) - len(x_curve2)): len(branch_z_list_2_1)])

                branch_z_param_list_2.pop(-1)
                branch_z_param_list_1_2 = branch_z_param_list_2 + branch_z_param_list_1
                z_param_curve2.extend(branch_z_param_list_1_2[(len(branch_z_list_2_1) - len(x_curve2)): len(branch_z_list_2_1)])

                branch_id_list_1_new = [1] * int(id_num1)
                branch_x_list_1_new.extend(x_curve2[id_num2: len(x_curve2)])
                branch_y_list_1_new.extend(y_curve2[id_num2: len(x_curve2)])
                branch_z_list_1_new.extend(z_curve2[id_num2: len(x_curve2)])
                branch_z_param_list_1_new.extend(z_param_curve2[id_num2: len(x_curve2)])

                branch_id_list_2_new = [2] * int(id_num2)
                branch_x_list_2_new.extend(x_curve2[0:id_num2])
                branch_y_list_2_new.extend(y_curve2[0:id_num2])
                branch_z_list_2_new.extend(z_curve2[0:id_num2])
                branch_z_param_list_2_new.extend(z_param_curve2[0:id_num2])

                branch_id_list_2_new.insert(0, 2)
                branch_x_list_2_new.insert(len(branch_x_list_2_new), branch_x_list_1_new[0])
                branch_y_list_2_new.insert(len(branch_y_list_2_new), branch_y_list_1_new[0])
                branch_z_list_2_new.insert(len(branch_z_list_2_new), branch_z_list_1_new[0])
                branch_z_param_list_2_new.insert(len(branch_z_param_list_2_new), branch_z_param_list_1_new[0])

                # plt.plot(branch_x_list_1_new,branch_y_list_1_new,marker='o',label='111')
                # plt.plot(branch_x_list_2_new,branch_y_list_2_new,marker='o',label='222')

                merge_id_list_1_new = []
                merge_x_list_1_new = []
                merge_y_list_1_new = []
                merge_z_list_1_new = []
                merge_z_param_list_1_new = []

                merge_id_list_2_new = []
                merge_x_list_2_new = []
                merge_y_list_2_new = []
                merge_z_list_2_new = []
                merge_z_param_list_2_new = []

                z_curve1 = []
                z_param_curve1 = []

                if len(x_curve1) == len(merge_x_list_2) + len(merge_x_list_1):
                    id_num1 = len(merge_x_list_1)
                    id_num2 = len(merge_x_list_2)
                else:
                    id_num1 = int(round(len(x_curve1) / 2, 0))
                    id_num2 = len(x_curve1) - id_num1

                merge_z_list_1.pop(-1)
                merge_z_list_1_2 = merge_z_list_1 + merge_z_list_2
                z_curve1.extend(merge_z_list_1_2[0: len(x_curve1)])

                merge_z_param_list_1.pop(-1)
                merge_z_param_list_1_2 = merge_z_param_list_1 + merge_z_param_list_2
                z_param_curve1.extend(merge_z_param_list_1_2[0: len(x_curve1)])

                merge_id_list_1_new = [1] * int(id_num1)
                merge_x_list_1_new.extend(x_curve1[0:id_num1])
                merge_y_list_1_new.extend(y_curve1[0:id_num1])
                merge_z_list_1_new.extend(z_curve1[0:id_num1])
                merge_z_param_list_1_new.extend(z_param_curve1[0:id_num1])

                merge_id_list_2_new = [2] * int(id_num2)
                merge_x_list_2_new.extend(x_curve1[id_num1: len(x_curve1)])
                merge_y_list_2_new.extend(y_curve1[id_num1: len(x_curve1)])
                merge_z_list_2_new.extend(z_curve1[id_num1: len(x_curve1)])
                merge_z_param_list_2_new.extend(z_param_curve1[id_num1: len(x_curve1)])

                merge_id_list_1_new.insert(0, 1)
                merge_x_list_1_new.insert(len(merge_x_list_1_new), merge_x_list_2_new[0])
                merge_y_list_1_new.insert(len(merge_y_list_1_new), merge_y_list_2_new[0])
                merge_z_list_1_new.insert(len(merge_z_list_1_new), merge_z_list_2_new[0])
                merge_z_param_list_1_new.insert(len(merge_z_param_list_1_new), merge_z_param_list_2_new[0])

                merge_z_list_2_new[-1] = branch_z_list_2_new[0]
                merge_z_param_list_2_new[-1] = branch_z_param_list_2_new[0]

                # plt.plot(merge_x_list_1_new,merge_y_list_1_new,marker='o',label='11')
                # plt.plot(merge_x_list_2_new,merge_y_list_2_new,marker='o',label='22')

                # plt.legend()
                # plt.show()

                merge_id_list_1 = merge_id_list_1_new
                merge_x_list_1 = merge_x_list_1_new
                merge_y_list_1 = merge_y_list_1_new
                merge_z_list_1 = merge_z_list_1_new
                merge_z_param_list_1 = merge_z_param_list_1_new

                merge_id_list_2 = merge_id_list_2_new
                merge_x_list_2 = merge_x_list_2_new
                merge_y_list_2 = merge_y_list_2_new
                merge_z_list_2 = merge_z_list_2_new
                merge_z_param_list_2 = merge_z_param_list_2_new

                branch_id_list_1 = branch_id_list_1_new
                branch_x_list_1 = branch_x_list_1_new
                branch_y_list_1 = branch_y_list_1_new
                branch_z_list_1 = branch_z_list_1_new
                branch_z_param_list_1 = branch_z_param_list_1_new

                branch_id_list_2 = branch_id_list_2_new
                branch_x_list_2 = branch_x_list_2_new
                branch_y_list_2 = branch_y_list_2_new
                branch_z_list_2 = branch_z_list_2_new
                branch_z_param_list_2 = branch_z_param_list_2_new

            except Exception as error:

                print("except: index_merge == 2 and index_branch == 2", error)

                start_point = (merge_x_list_1[0], merge_y_list_1[0], merge_z_list_1[0])
                end_point = (branch_x_list_1[-1], branch_y_list_1[-1], branch_z_list_1[-1])

                offset_branch_2 = branch_offset_list[0]

                for i in range(len(merge_offset_list) - 1, -1, -1):
                    if merge_offset_list[i] != 0:
                        offset_merge_2 = merge_offset_list[i]
                        break

                offset = offset_branch_2 - offset_merge_2

                if error.args[0] == 1:
                    print("This is a serious error that requires changing the road data to connect the road correctly. XXXXXXXXXX")

                x_curve1, y_curve1, z_curve1, z_param_curve1, x_curve2, y_curve2, z_curve2, z_param_curve2 = ajust.make_new_combine_road_data(start_point, end_point, offset)

                ########################################################

                branch_id_list_1_new = []
                branch_x_list_1_new = []
                branch_y_list_1_new = []
                branch_z_list_1_new = []
                branch_z_param_list_1_new = []

                branch_id_list_2_new = []
                branch_x_list_2_new = []
                branch_y_list_2_new = []
                branch_z_list_2_new = []
                branch_z_param_list_2_new = []

                if len(x_curve2) == len(branch_x_list_2) + len(branch_x_list_1):
                    id_num1 = len(branch_x_list_1)
                    id_num2 = len(branch_x_list_2)
                else:
                    id_num1 = int(round(len(x_curve2) / 2, 0))
                    id_num2 = len(x_curve2) - id_num1

                branch_id_list_1_new = [1] * int(id_num1)
                branch_x_list_1_new.extend(x_curve2[id_num2: len(x_curve2)])
                branch_y_list_1_new.extend(y_curve2[id_num2: len(x_curve2)])
                branch_z_list_1_new.extend(z_curve2[id_num2: len(x_curve2)])
                branch_z_param_list_1_new.extend(z_param_curve2[id_num2: len(x_curve2)])

                branch_id_list_2_new = [2] * int(id_num2)
                branch_x_list_2_new.extend(x_curve2[0:id_num2])
                branch_y_list_2_new.extend(y_curve2[0:id_num2])
                branch_z_list_2_new.extend(z_curve2[0:id_num2])
                branch_z_param_list_2_new.extend(z_param_curve2[0:id_num2])

                branch_id_list_2_new.insert(0, 2)
                branch_x_list_2_new.insert(len(branch_x_list_2_new), branch_x_list_1_new[0])
                branch_y_list_2_new.insert(len(branch_y_list_2_new), branch_y_list_1_new[0])
                branch_z_list_2_new.insert(len(branch_z_list_2_new), branch_z_list_1_new[0])
                branch_z_param_list_2_new.insert(len(branch_z_param_list_2_new), branch_z_param_list_1_new[0])

                # plt.plot(branch_x_list_1_new,branch_y_list_1_new,marker='o',label='111')
                # plt.plot(branch_x_list_2_new,branch_y_list_2_new,marker='o',label='222')

                merge_id_list_1_new = []
                merge_x_list_1_new = []
                merge_y_list_1_new = []
                merge_z_list_1_new = []
                merge_z_param_list_1_new = []

                merge_id_list_2_new = []
                merge_x_list_2_new = []
                merge_y_list_2_new = []
                merge_z_list_2_new = []
                merge_z_param_list_2_new = []

                if len(x_curve1) == len(merge_x_list_2) + len(merge_x_list_1):
                    id_num1 = len(merge_x_list_1)
                    id_num2 = len(merge_x_list_2)
                else:
                    id_num1 = int(round(len(x_curve1) / 2, 0))
                    id_num2 = len(x_curve1) - id_num1

                merge_id_list_1_new = [1] * int(id_num1)
                merge_x_list_1_new.extend(x_curve1[0:id_num1])
                merge_y_list_1_new.extend(y_curve1[0:id_num1])
                merge_z_list_1_new.extend(z_curve1[0:id_num1])
                merge_z_param_list_1_new.extend(z_param_curve1[0:id_num1])

                merge_id_list_2_new = [2] * int(id_num2)
                merge_x_list_2_new.extend(x_curve1[id_num1: len(x_curve1)])
                merge_y_list_2_new.extend(y_curve1[id_num1: len(x_curve1)])
                merge_z_list_2_new.extend(z_curve1[id_num1: len(x_curve1)])
                merge_z_param_list_2_new.extend(z_param_curve1[id_num1: len(x_curve1)])

                merge_id_list_1_new.insert(0, 1)
                merge_x_list_1_new.insert(len(merge_x_list_1_new), merge_x_list_2_new[0])
                merge_y_list_1_new.insert(len(merge_y_list_1_new), merge_y_list_2_new[0])
                merge_z_list_1_new.insert(len(merge_z_list_1_new), merge_z_list_2_new[0])
                merge_z_param_list_1_new.insert(len(merge_z_param_list_1_new), merge_z_param_list_2_new[0])

                merge_z_list_2_new[-1] = branch_z_list_2_new[0]
                merge_z_param_list_2_new[-1] = branch_z_param_list_2_new[0]

                ########################################################

                merge_id_list_1 = merge_id_list_1_new
                merge_x_list_1 = merge_x_list_1_new
                merge_y_list_1 = merge_y_list_1_new
                merge_z_list_1 = merge_z_list_1_new
                merge_z_param_list_1 = merge_z_param_list_1_new

                merge_id_list_2 = merge_id_list_2_new
                merge_x_list_2 = merge_x_list_2_new
                merge_y_list_2 = merge_y_list_2_new
                merge_z_list_2 = merge_z_list_2_new
                merge_z_param_list_2 = merge_z_param_list_2_new

                branch_id_list_1 = branch_id_list_1_new
                branch_x_list_1 = branch_x_list_1_new
                branch_y_list_1 = branch_y_list_1_new
                branch_z_list_1 = branch_z_list_1_new
                branch_z_param_list_1 = branch_z_param_list_1_new

                branch_id_list_2 = branch_id_list_2_new
                branch_x_list_2 = branch_x_list_2_new
                branch_y_list_2 = branch_y_list_2_new
                branch_z_list_2 = branch_z_list_2_new
                branch_z_param_list_2 = branch_z_param_list_2_new

        elif index_branch == 0 and index_merge == 0:

            try:

                merge_x_list_3.pop(-1)
                merge_y_list_3.pop(-1)
                branch_x_list_5.pop(-1)
                branch_y_list_5.pop(-1)

                x_curve2 = merge_x_list_3 + merge_x_list_5
                y_curve2 = merge_y_list_3 + merge_y_list_5
                x_curve1 = branch_x_list_5 + branch_x_list_3
                y_curve1 = branch_y_list_5 + branch_y_list_3

                start_point = (branch_x_list_5[0], branch_y_list_5[0])
                end_point = (merge_x_list_5[-1], merge_y_list_5[-1])

                offset = 0

                x_curve1, y_curve1, x_curve2, y_curve2 = ajust.make_combine_road_data(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset)

                ########################################################

                branch_id_list_3_new = []
                branch_x_list_3_new = []
                branch_y_list_3_new = []
                branch_z_list_3_new = []
                branch_z_param_list_3_new = []

                branch_id_list_5_new = []
                branch_x_list_5_new = []
                branch_y_list_5_new = []
                branch_z_list_5_new = []
                branch_z_param_list_5_new = []

                z_curve1 = []
                z_param_curve1 = []

                id_num3 = len(x_curve1) - 3
                id_num5 = len(x_curve1) - id_num3

                branch_z_list_5.pop(-1)
                branch_z_list_5_3 = branch_z_list_5 + branch_z_list_3
                z_curve1.extend(branch_z_list_5_3[0: len(x_curve1)])

                branch_z_param_list_5.pop(-1)
                branch_z_param_list_5_3 = branch_z_param_list_5 + branch_z_param_list_3
                z_param_curve1.extend(branch_z_param_list_5_3[0: len(x_curve1)])

                branch_id_list_3_new = [3] * int(id_num3)
                branch_x_list_3_new.extend(x_curve1[id_num5: len(x_curve1)])
                branch_y_list_3_new.extend(y_curve1[id_num5: len(x_curve1)])
                branch_z_list_3_new.extend(z_curve1[id_num5: len(x_curve1)])
                branch_z_param_list_3_new.extend(z_param_curve1[id_num5: len(x_curve1)])

                branch_id_list_5_new = [5] * int(id_num5)
                branch_x_list_5_new.extend(x_curve1[0:id_num5])
                branch_y_list_5_new.extend(y_curve1[0:id_num5])
                branch_z_list_5_new.extend(z_curve1[0:id_num5])
                branch_z_param_list_5_new.extend(z_param_curve1[0:id_num5])

                branch_id_list_5_new.insert(0, 5)
                branch_x_list_5_new.insert(len(branch_x_list_5_new), branch_x_list_3_new[0])
                branch_y_list_5_new.insert(len(branch_y_list_5_new), branch_y_list_3_new[0])
                branch_z_list_5_new.insert(len(branch_z_list_5_new), branch_z_list_3_new[0])
                branch_z_param_list_5_new.insert(len(branch_z_param_list_5_new), branch_z_param_list_3_new[0])

                # plt.plot(branch_x_list_3_new,branch_y_list_3_new,marker='o',label='111')
                # plt.plot(branch_x_list_5_new,branch_y_list_5_new,marker='o',label='222')

                merge_id_list_3_new = []
                merge_x_list_3_new = []
                merge_y_list_3_new = []
                merge_z_list_3_new = []
                merge_z_param_list_3_new = []

                merge_id_list_5_new = []
                merge_x_list_5_new = []
                merge_y_list_5_new = []
                merge_z_list_5_new = []
                merge_z_param_list_5_new = []

                z_curve2 = []
                z_param_curve2 = []

                id_num3 = len(x_curve2) - 4
                id_num5 = 4

                merge_z_list_3.pop(-1)
                merge_z_list_3_5 = merge_z_list_3 + merge_z_list_5
                z_curve2.extend(merge_z_list_3_5[(len(merge_z_list_3_5) - len(x_curve2)): len(merge_z_list_3_5)])

                merge_z_param_list_3.pop(-1)
                merge_z_param_list_3_5 = merge_z_param_list_3 + merge_z_param_list_5
                z_param_curve2.extend(merge_z_param_list_3_5[(len(merge_z_list_3_5) - len(x_curve2)): len(merge_z_list_3_5)])

                merge_id_list_3_new = [3] * int(id_num3)
                merge_x_list_3_new.extend(x_curve2[0:id_num3])
                merge_y_list_3_new.extend(y_curve2[0:id_num3])
                merge_z_list_3_new.extend(z_curve2[0:id_num3])
                merge_z_param_list_3_new.extend(z_param_curve2[0:id_num3])

                merge_id_list_5_new = [5] * int(id_num5)
                merge_x_list_5_new.extend(x_curve2[id_num3: len(x_curve2)])
                merge_y_list_5_new.extend(y_curve2[id_num3: len(x_curve2)])
                merge_z_list_5_new.extend(z_curve2[id_num3: len(x_curve2)])
                merge_z_param_list_5_new.extend(z_param_curve2[id_num3: len(x_curve2)])

                merge_id_list_3_new.insert(0, 3)
                merge_x_list_3_new.insert(len(merge_x_list_3_new), merge_x_list_5_new[0])
                merge_y_list_3_new.insert(len(merge_y_list_3_new), merge_y_list_5_new[0])
                merge_z_list_3_new.insert(len(merge_z_list_3_new), merge_z_list_5_new[0])
                merge_z_param_list_3_new.insert(len(merge_z_param_list_3_new), merge_z_param_list_5_new[0])

                # plt.plot(merge_x_list_3_new,merge_y_list_3_new,marker='o',label='33')
                # plt.plot(merge_x_list_5_new,merge_y_list_5_new,marker='o',label='55')

                # plt.legend()
                # plt.show()

                merge_id_list_3 = merge_id_list_3_new
                merge_x_list_3 = merge_x_list_3_new
                merge_y_list_3 = merge_y_list_3_new
                merge_z_list_3 = merge_z_list_3_new
                merge_z_param_list_3 = merge_z_param_list_3_new

                merge_id_list_5 = merge_id_list_5_new
                merge_x_list_5 = merge_x_list_5_new
                merge_y_list_5 = merge_y_list_5_new
                merge_z_list_5 = merge_z_list_5_new
                merge_z_param_list_5 = merge_z_param_list_5_new

                branch_id_list_3 = branch_id_list_3_new
                branch_x_list_3 = branch_x_list_3_new
                branch_y_list_3 = branch_y_list_3_new
                branch_z_list_3 = branch_z_list_3_new
                branch_z_param_list_3 = branch_z_param_list_3_new

                branch_id_list_5 = branch_id_list_5_new
                branch_x_list_5 = branch_x_list_5_new
                branch_y_list_5 = branch_y_list_5_new
                branch_z_list_5 = branch_z_list_5_new
                branch_z_param_list_5 = branch_z_param_list_5_new

            except Exception as error:

                print("except: index_merge == 0 and index_branch == 0", error)

                start_point = (branch_x_list_5[0], branch_y_list_5[0], branch_z_list_5[0])
                end_point = (merge_x_list_5[-1], merge_y_list_5[-1], merge_z_list_5[-1])

                offset = 0

                if error.args[0] == 1:
                    print("This is a serious error that requires changing the road data to connect the road correctly. XXXXXXXXXX")

                x_curve1, y_curve1, z_curve1, z_param_curve1, x_curve2, y_curve2, z_curve2, z_param_curve2 = ajust.make_new_combine_road_data(start_point, end_point, offset)

                ########################################################

                branch_id_list_3_new = []
                branch_x_list_3_new = []
                branch_y_list_3_new = []
                branch_z_list_3_new = []
                branch_z_param_list_3_new = []

                branch_id_list_5_new = []
                branch_x_list_5_new = []
                branch_y_list_5_new = []
                branch_z_list_5_new = []
                branch_z_param_list_5_new = []

                id_num3 = len(x_curve1) - 3
                id_num5 = len(x_curve1) - id_num3

                branch_id_list_3_new = [3] * int(id_num3)
                branch_x_list_3_new.extend(x_curve1[id_num5: len(x_curve1)])
                branch_y_list_3_new.extend(y_curve1[id_num5: len(x_curve1)])
                branch_z_list_3_new.extend(z_curve1[id_num5: len(x_curve1)])
                branch_z_param_list_3_new.extend(z_param_curve1[id_num5: len(x_curve1)])

                branch_id_list_5_new = [5] * int(id_num5)
                branch_x_list_5_new.extend(x_curve1[0:id_num5])
                branch_y_list_5_new.extend(y_curve1[0:id_num5])
                branch_z_list_5_new.extend(z_curve1[0:id_num5])
                branch_z_param_list_5_new.extend(z_param_curve1[0:id_num5])

                branch_id_list_5_new.insert(0, 5)
                branch_x_list_5_new.insert(len(branch_x_list_5_new), branch_x_list_3_new[0])
                branch_y_list_5_new.insert(len(branch_y_list_5_new), branch_y_list_3_new[0])
                branch_z_list_5_new.insert(len(branch_z_list_5_new), branch_z_list_3_new[0])
                branch_z_param_list_5_new.insert(len(branch_z_param_list_5_new), branch_z_param_list_3_new[0])

                # plt.plot(branch_x_list_3_new,branch_y_list_3_new,marker='o',label='111')
                # plt.plot(branch_x_list_5_new,branch_y_list_5_new,marker='o',label='222')

                merge_id_list_3_new = []
                merge_x_list_3_new = []
                merge_y_list_3_new = []
                merge_z_list_3_new = []
                merge_z_param_list_3_new = []

                merge_id_list_5_new = []
                merge_x_list_5_new = []
                merge_y_list_5_new = []
                merge_z_list_5_new = []
                merge_z_param_list_5_new = []

                id_num3 = len(x_curve2) - 4
                id_num5 = 4

                merge_id_list_3_new = [3] * int(id_num3)
                merge_x_list_3_new.extend(x_curve2[0:id_num3])
                merge_y_list_3_new.extend(y_curve2[0:id_num3])
                merge_z_list_3_new.extend(z_curve2[0:id_num3])
                merge_z_param_list_3_new.extend(z_param_curve2[0:id_num3])

                merge_id_list_5_new = [5] * int(id_num5)
                merge_x_list_5_new.extend(x_curve2[id_num3: len(x_curve2)])
                merge_y_list_5_new.extend(y_curve2[id_num3: len(x_curve2)])
                merge_z_list_5_new.extend(z_curve2[id_num3: len(x_curve2)])
                merge_z_param_list_5_new.extend(z_param_curve2[id_num3: len(x_curve2)])

                merge_id_list_3_new.insert(0, 3)
                merge_x_list_3_new.insert(len(merge_x_list_3_new), merge_x_list_5_new[0])
                merge_y_list_3_new.insert(len(merge_y_list_3_new), merge_y_list_5_new[0])
                merge_z_list_3_new.insert(len(merge_z_list_3_new), merge_z_list_5_new[0])
                merge_z_param_list_3_new.insert(len(merge_z_param_list_3_new), merge_z_param_list_5_new[0])

                # plt.plot(merge_x_list_3_new,merge_y_list_3_new,marker='o',label='33')
                # plt.plot(merge_x_list_5_new,merge_y_list_5_new,marker='o',label='55')

                # plt.legend()
                # plt.show()

                merge_id_list_3 = merge_id_list_3_new
                merge_x_list_3 = merge_x_list_3_new
                merge_y_list_3 = merge_y_list_3_new
                merge_z_list_3 = merge_z_list_3_new
                merge_z_param_list_3 = merge_z_param_list_3_new

                merge_id_list_5 = merge_id_list_5_new
                merge_x_list_5 = merge_x_list_5_new
                merge_y_list_5 = merge_y_list_5_new
                merge_z_list_5 = merge_z_list_5_new
                merge_z_param_list_5 = merge_z_param_list_5_new

                branch_id_list_3 = branch_id_list_3_new
                branch_x_list_3 = branch_x_list_3_new
                branch_y_list_3 = branch_y_list_3_new
                branch_z_list_3 = branch_z_list_3_new
                branch_z_param_list_3 = branch_z_param_list_3_new

                branch_id_list_5 = branch_id_list_5_new
                branch_x_list_5 = branch_x_list_5_new
                branch_y_list_5 = branch_y_list_5_new
                branch_z_list_5 = branch_z_list_5_new
                branch_z_param_list_5 = branch_z_param_list_5_new

        elif index_branch == 1 and index_merge == 1:

            try:

                merge_x_list_0.pop(-1)
                merge_y_list_0.pop(-1)
                branch_x_list_4.pop(-1)
                branch_y_list_4.pop(-1)

                x_curve1 = branch_x_list_4 + branch_x_list_0
                y_curve1 = branch_y_list_4 + branch_y_list_0
                x_curve2 = merge_x_list_0 + merge_x_list_4
                y_curve2 = merge_y_list_0 + merge_y_list_4

                start_point = (branch_x_list_4[0], branch_y_list_4[0])
                end_point = (merge_x_list_4[-1], merge_y_list_4[-1])

                offset_merge_0 = merge_offset_list[0]

                for i in range(len(branch_offset_list) - 1, -1, -1):
                    if branch_offset_list[i] != 0:
                        offset_branch_0 = branch_offset_list[i]
                        break

                offset = offset_merge_0 - offset_branch_0

                x_curve1, y_curve1, x_curve2, y_curve2 = ajust.make_combine_road_data(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset)

                ########################################################

                branch_id_list_0_new = []
                branch_x_list_0_new = []
                branch_y_list_0_new = []
                branch_z_list_0_new = []
                branch_z_param_list_0_new = []

                branch_id_list_4_new = []
                branch_x_list_4_new = []
                branch_y_list_4_new = []
                branch_z_list_4_new = []
                branch_z_param_list_4_new = []

                z_curve1 = []
                z_param_curve1 = []

                id_num0 = len(x_curve1) - 3
                id_num4 = len(x_curve1) - id_num0

                branch_z_list_4.pop(-1)
                branch_z_list_4_0 = branch_z_list_4 + branch_z_list_0
                z_curve1.extend(branch_z_list_4_0[0: len(x_curve1)])

                branch_z_param_list_4.pop(-1)
                branch_z_param_list_4_0 = branch_z_param_list_4 + branch_z_param_list_0
                z_param_curve1.extend(branch_z_param_list_4_0[0: len(x_curve1)])

                branch_id_list_0_new = [0] * int(id_num0)
                branch_x_list_0_new.extend(x_curve1[id_num4: len(x_curve1)])
                branch_y_list_0_new.extend(y_curve1[id_num4: len(x_curve1)])
                branch_z_list_0_new.extend(z_curve1[id_num4: len(x_curve1)])
                branch_z_param_list_0_new.extend(z_param_curve1[id_num4: len(x_curve1)])

                branch_id_list_4_new = [4] * int(id_num4)
                branch_x_list_4_new.extend(x_curve1[0:id_num4])
                branch_y_list_4_new.extend(y_curve1[0:id_num4])
                branch_z_list_4_new.extend(z_curve1[0:id_num4])
                branch_z_param_list_4_new.extend(z_param_curve1[0:id_num4])

                branch_id_list_4_new.insert(0, 4)
                branch_x_list_4_new.insert(len(branch_x_list_4_new), branch_x_list_0_new[0])
                branch_y_list_4_new.insert(len(branch_y_list_4_new), branch_y_list_0_new[0])
                branch_z_list_4_new.insert(len(branch_z_list_4_new), branch_z_list_0_new[0])
                branch_z_param_list_4_new.insert(len(branch_z_param_list_4_new), branch_z_param_list_0_new[0])

                # plt.plot(branch_x_list_0_new,branch_y_list_0_new,marker='o',label='000')
                # plt.plot(branch_x_list_4_new,branch_y_list_4_new,marker='o',label='444')

                merge_id_list_0_new = []
                merge_x_list_0_new = []
                merge_y_list_0_new = []
                merge_z_list_0_new = []
                merge_z_param_list_0_new = []

                merge_id_list_4_new = []
                merge_x_list_4_new = []
                merge_y_list_4_new = []
                merge_z_list_4_new = []
                merge_z_param_list_4_new = []

                z_curve2 = []
                z_param_curve2 = []

                id_num0 = len(x_curve2) - 4
                id_num4 = 4

                merge_z_list_0.pop(-1)
                merge_z_list_0_4 = merge_z_list_0 + merge_z_list_4
                z_curve2.extend(merge_z_list_0_4[(len(merge_z_list_0_4) - len(x_curve2)): len(merge_z_list_0_4)])

                merge_z_param_list_0.pop(-1)
                merge_z_param_list_0_4 = merge_z_param_list_0 + merge_z_param_list_4
                z_param_curve2.extend(merge_z_param_list_0_4[(len(merge_z_list_0_4) - len(x_curve2)): len(merge_z_list_0_4)])

                merge_id_list_0_new = [0] * int(id_num0)
                merge_x_list_0_new.extend(x_curve2[0:id_num0])
                merge_y_list_0_new.extend(y_curve2[0:id_num0])
                merge_z_list_0_new.extend(z_curve2[0:id_num0])
                merge_z_param_list_0_new.extend(z_param_curve2[0:id_num0])

                merge_id_list_4_new = [4] * int(id_num4)
                merge_x_list_4_new.extend(x_curve2[id_num0: len(x_curve2)])
                merge_y_list_4_new.extend(y_curve2[id_num0: len(x_curve2)])
                merge_z_list_4_new.extend(z_curve2[id_num0: len(x_curve2)])
                merge_z_param_list_4_new.extend(z_param_curve2[id_num0: len(x_curve2)])

                merge_id_list_0_new.insert(0, 0)
                merge_x_list_0_new.insert(len(merge_x_list_0_new), merge_x_list_4_new[0])
                merge_y_list_0_new.insert(len(merge_y_list_0_new), merge_y_list_4_new[0])
                merge_z_list_0_new.insert(len(merge_z_list_0_new), merge_z_list_4_new[0])
                merge_z_param_list_0_new.insert(len(merge_z_param_list_0_new), merge_z_param_list_4_new[0])

                # plt.plot(merge_x_list_0_new,merge_y_list_0_new,marker='o',label='00')
                # plt.plot(merge_x_list_4_new,merge_y_list_4_new,marker='o',label='44')

                # plt.legend()
                # plt.show()

                merge_id_list_0 = merge_id_list_0_new
                merge_x_list_0 = merge_x_list_0_new
                merge_y_list_0 = merge_y_list_0_new
                merge_z_list_0 = merge_z_list_0_new
                merge_z_param_list_0 = merge_z_param_list_0_new

                merge_id_list_4 = merge_id_list_4_new
                merge_x_list_4 = merge_x_list_4_new
                merge_y_list_4 = merge_y_list_4_new
                merge_z_list_4 = merge_z_list_4_new
                merge_z_param_list_4 = merge_z_param_list_4_new

                branch_id_list_0 = branch_id_list_0_new
                branch_x_list_0 = branch_x_list_0_new
                branch_y_list_0 = branch_y_list_0_new
                branch_z_list_0 = branch_z_list_0_new
                branch_z_param_list_0 = branch_z_param_list_0_new

                branch_id_list_4 = branch_id_list_4_new
                branch_x_list_4 = branch_x_list_4_new
                branch_y_list_4 = branch_y_list_4_new
                branch_z_list_4 = branch_z_list_4_new
                branch_z_param_list_4 = branch_z_param_list_4_new

            except Exception as error:

                print("except: index_merge == 1 and index_branch == 1", error)

                start_point = (branch_x_list_4[0], branch_y_list_4[0], branch_z_list_4[0])
                end_point = (merge_x_list_4[-1], merge_y_list_4[-1], merge_z_list_4[-1])

                offset_merge_0 = merge_offset_list[0]

                for i in range(len(branch_offset_list) - 1, -1, -1):
                    if branch_offset_list[i] != 0:
                        offset_branch_0 = branch_offset_list[i]
                        break

                offset = offset_merge_0 - offset_branch_0

                if error.args[0] == 1:
                    print("This is a serious error that requires changing the road data to connect the road correctly. XXXXXXXXXX")

                x_curve1, y_curve1, z_curve1, z_param_curve1, x_curve2, y_curve2, z_curve2, z_param_curve2 = ajust.make_new_combine_road_data(start_point, end_point, offset)

                ########################################################

                branch_id_list_0_new = []
                branch_x_list_0_new = []
                branch_y_list_0_new = []
                branch_z_list_0_new = []
                branch_z_param_list_0_new = []

                branch_id_list_4_new = []
                branch_x_list_4_new = []
                branch_y_list_4_new = []
                branch_z_list_4_new = []
                branch_z_param_list_4_new = []

                id_num0 = len(x_curve1) - 3
                id_num4 = len(x_curve1) - id_num0

                branch_id_list_0_new = [0] * int(id_num0)
                branch_x_list_0_new.extend(x_curve1[id_num4: len(x_curve1)])
                branch_y_list_0_new.extend(y_curve1[id_num4: len(x_curve1)])
                branch_z_list_0_new.extend(z_curve1[id_num4: len(x_curve1)])
                branch_z_param_list_0_new.extend(z_param_curve1[id_num4: len(x_curve1)])

                branch_id_list_4_new = [4] * int(id_num4)
                branch_x_list_4_new.extend(x_curve1[0:id_num4])
                branch_y_list_4_new.extend(y_curve1[0:id_num4])
                branch_z_list_4_new.extend(z_curve1[0:id_num4])
                branch_z_param_list_4_new.extend(z_param_curve1[0:id_num4])

                branch_id_list_4_new.insert(0, 4)
                branch_x_list_4_new.insert(len(branch_x_list_4_new), branch_x_list_0_new[0])
                branch_y_list_4_new.insert(len(branch_y_list_4_new), branch_y_list_0_new[0])
                branch_z_list_4_new.insert(len(branch_z_list_4_new), branch_z_list_0_new[0])
                branch_z_param_list_4_new.insert(len(branch_z_param_list_4_new), branch_z_param_list_0_new[0])

                # plt.plot(branch_x_list_0_new,branch_y_list_0_new,marker='o',label='000')
                # plt.plot(branch_x_list_4_new,branch_y_list_4_new,marker='o',label='444')

                merge_id_list_0_new = []
                merge_x_list_0_new = []
                merge_y_list_0_new = []
                merge_z_list_0_new = []
                merge_z_param_list_0_new = []

                merge_id_list_4_new = []
                merge_x_list_4_new = []
                merge_y_list_4_new = []
                merge_z_list_4_new = []
                merge_z_param_list_4_new = []

                id_num0 = len(x_curve2) - 4
                id_num4 = 4

                merge_id_list_0_new = [0] * int(id_num0)
                merge_x_list_0_new.extend(x_curve2[0:id_num0])
                merge_y_list_0_new.extend(y_curve2[0:id_num0])
                merge_z_list_0_new.extend(z_curve2[0:id_num0])
                merge_z_param_list_0_new.extend(z_param_curve2[0:id_num0])

                merge_id_list_4_new = [4] * int(id_num4)
                merge_x_list_4_new.extend(x_curve2[id_num0: len(x_curve2)])
                merge_y_list_4_new.extend(y_curve2[id_num0: len(x_curve2)])
                merge_z_list_4_new.extend(z_curve2[id_num0: len(x_curve2)])
                merge_z_param_list_4_new.extend(z_param_curve2[id_num0: len(x_curve2)])

                merge_id_list_0_new.insert(0, 0)
                merge_x_list_0_new.insert(len(merge_x_list_0_new), merge_x_list_4_new[0])
                merge_y_list_0_new.insert(len(merge_y_list_0_new), merge_y_list_4_new[0])
                merge_z_list_0_new.insert(len(merge_z_list_0_new), merge_z_list_4_new[0])
                merge_z_param_list_0_new.insert(len(merge_z_param_list_0_new), merge_z_param_list_4_new[0])

                # plt.plot(merge_x_list_0_new,merge_y_list_0_new,marker='o',label='00')
                # plt.plot(merge_x_list_4_new,merge_y_list_4_new,marker='o',label='44')

                # plt.legend()
                # plt.show()

                merge_id_list_0 = merge_id_list_0_new
                merge_x_list_0 = merge_x_list_0_new
                merge_y_list_0 = merge_y_list_0_new
                merge_z_list_0 = merge_z_list_0_new
                merge_z_param_list_0 = merge_z_param_list_0_new

                merge_id_list_4 = merge_id_list_4_new
                merge_x_list_4 = merge_x_list_4_new
                merge_y_list_4 = merge_y_list_4_new
                merge_z_list_4 = merge_z_list_4_new
                merge_z_param_list_4 = merge_z_param_list_4_new

                branch_id_list_0 = branch_id_list_0_new
                branch_x_list_0 = branch_x_list_0_new
                branch_y_list_0 = branch_y_list_0_new
                branch_z_list_0 = branch_z_list_0_new
                branch_z_param_list_0 = branch_z_param_list_0_new

                branch_id_list_4 = branch_id_list_4_new
                branch_x_list_4 = branch_x_list_4_new
                branch_y_list_4 = branch_y_list_4_new
                branch_z_list_4 = branch_z_list_4_new
                branch_z_param_list_4 = branch_z_param_list_4_new

        else:
            self.df_polyline_2 += [merge.df_polyline]
            self.df_polyline_2 += [branch.df_polyline]
            print("merge - branch not yet paired", index_merge, index_branch)
            return

        if index_merge == 2 and index_branch == 2:

            # region 111111111111

            main_id_list = merge_id_list_0 + merge_id_list_4 + merge_id_list_1 + merge_id_list_2
            main_x_list = merge_x_list_0 + merge_x_list_4 + merge_x_list_1 + merge_x_list_2
            main_y_list = merge_y_list_0 + merge_y_list_4 + merge_y_list_1 + merge_y_list_2
            main_z_list = merge_z_list_0 + merge_z_list_4 + merge_z_list_1 + merge_z_list_2
            main_z_param_list = merge_z_param_list_0 + merge_z_param_list_4 + merge_z_param_list_1 + merge_z_param_list_2
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
            sub_df_polyline, sub_hdg_list_merge = ajust.add_curvature_info(sub_df_polyline, hdg_start_sub_merge)

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
                    sub_df_polyline["hdg"] = [x + 2 * math.pi for x in sub_df_polyline["hdg"]]
                elif base_hdg < base_hdg_sub:
                    sub_df_polyline["hdg"] = [x - 2 * math.pi for x in sub_df_polyline["hdg"]]
                else:
                    pass

            out_df = pd.concat([main_df_polyline, sub_df_polyline])
            self.df_polyline_2 += [out_df.reset_index(drop=True)]

            # endregion

            # region 222222222222

            main_id_list = branch_id_list_2 + branch_id_list_1 + branch_id_list_4 + branch_id_list_0
            main_x_list = branch_x_list_2 + branch_x_list_1 + branch_x_list_4 + branch_x_list_0
            main_y_list = branch_y_list_2 + branch_y_list_1 + branch_y_list_4 + branch_y_list_0
            main_z_list = branch_z_list_2 + branch_z_list_1 + branch_z_list_4 + branch_z_list_0
            main_z_param_list = branch_z_param_list_2 + branch_z_param_list_1 + branch_z_param_list_4 + branch_z_param_list_0
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

            main_df_polyline, main_hdg_list_branch = ajust.add_curvature_info(main_df_polyline, main_hdg_list_merge[-2])
            sub_df_polyline, sub_hdg_list_branch = ajust.add_curvature_info(sub_df_polyline)

            # （根本的な解決が必要な箇所）
            # 本線と加速車線でラジアン方位(hdg)の値が意味的には同じだが異なる（例：１degと361degの関係）←これがOpenDriveとして読み込ませる際に悪さをする
            # 以下はその一時対応

            # 本線の合流差路中心のラジアン方位を抽出する
            # base_hdg_id = 22
            base_hdg_id = len(branch_id_list_2 + branch_id_list_1) + 1
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

        else:

            # region 222222222222

            main_id_list = branch_id_list_2 + branch_id_list_1 + branch_id_list_4 + branch_id_list_0
            main_x_list = branch_x_list_2 + branch_x_list_1 + branch_x_list_4 + branch_x_list_0
            main_y_list = branch_y_list_2 + branch_y_list_1 + branch_y_list_4 + branch_y_list_0
            main_z_list = branch_z_list_2 + branch_z_list_1 + branch_z_list_4 + branch_z_list_0
            main_z_param_list = branch_z_param_list_2 + branch_z_param_list_1 + branch_z_param_list_4 + branch_z_param_list_0
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
            sub_df_polyline, sub_hdg_list_branch = ajust.add_curvature_info(sub_df_polyline)

            # （根本的な解決が必要な箇所）
            # 本線と加速車線でラジアン方位(hdg)の値が意味的には同じだが異なる（例：１degと361degの関係）←これがOpenDriveとして読み込ませる際に悪さをする
            # 以下はその一時対応

            # 本線の合流差路中心のラジアン方位を抽出する
            # base_hdg_id = 22
            base_hdg_id = len(branch_id_list_2 + branch_id_list_1) + 1
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

            out_df_branch = pd.concat([main_df_polyline, sub_df_polyline])
            # self.df_polyline_2 += [out_df.reset_index(drop=True)]
            # endregion

            # region 111111111111

            main_id_list = merge_id_list_0 + merge_id_list_4 + merge_id_list_1 + merge_id_list_2
            main_x_list = merge_x_list_0 + merge_x_list_4 + merge_x_list_1 + merge_x_list_2
            main_y_list = merge_y_list_0 + merge_y_list_4 + merge_y_list_1 + merge_y_list_2
            main_z_list = merge_z_list_0 + merge_z_list_4 + merge_z_list_1 + merge_z_list_2
            main_z_param_list = merge_z_param_list_0 + merge_z_param_list_4 + merge_z_param_list_1 + merge_z_param_list_2
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

            if index_branch == 0 and index_merge == 0:
                main_df_polyline, main_hdg_list_merge = ajust.add_curvature_info(main_df_polyline, hdg_start_main_merge)
                sub_df_polyline, sub_hdg_list_merge = ajust.add_curvature_info(sub_df_polyline, sub_hdg_list_branch[-2])
            elif index_branch == 0 and index_merge == 1:
                main_df_polyline, main_hdg_list_merge = ajust.add_curvature_info(main_df_polyline, sub_hdg_list_branch[-2])
                sub_df_polyline, sub_hdg_list_merge = ajust.add_curvature_info(sub_df_polyline, hdg_start_sub_merge)
            elif index_branch == 1 and index_merge == 0:
                main_df_polyline, main_hdg_list_merge = ajust.add_curvature_info(main_df_polyline, hdg_start_main_merge)
                sub_df_polyline, sub_hdg_list_merge = ajust.add_curvature_info(sub_df_polyline, main_hdg_list_branch[-2])
            elif index_branch == 1 and index_merge == 1:
                main_df_polyline, main_hdg_list_merge = ajust.add_curvature_info(main_df_polyline, main_hdg_list_branch[-2])
                sub_df_polyline, sub_hdg_list_merge = ajust.add_curvature_info(sub_df_polyline, hdg_start_sub_merge)

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
                    sub_df_polyline["hdg"] = [x + 2 * math.pi for x in sub_df_polyline["hdg"]]
                elif base_hdg < base_hdg_sub:
                    sub_df_polyline["hdg"] = [x - 2 * math.pi for x in sub_df_polyline["hdg"]]
                else:
                    pass

            out_df_merge = pd.concat([main_df_polyline, sub_df_polyline])
            self.df_polyline_2 += [out_df_merge.reset_index(drop=True)]

            self.df_polyline_2 += [out_df_branch.reset_index(drop=True)]

            # endregion
