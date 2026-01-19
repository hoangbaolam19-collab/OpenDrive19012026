import math
import pandas as pd

from submodule import curvature_culc_func as ccf


class MainLaneStructure:
    """
    A class to handle the structure of main lanes in a road network.
    
    Attributes:
        df_lane_info (list): List containing lane information
        df_polyline (list): List containing polyline geometry
        error_is (str): Error status, "None" if no errors
    """
    def __init__(self):
        self.df_lane_info = []
        self.df_polyline = []
        self.error_is = "None"

    def make_mainlane_structure(self, obj_node_data):
        """
        Create main lane structure from node data.
        
        Args:
            obj_node_data: Object containing node data
        """
        self.make_df_polyline(obj_node_data)
        if self.error_is == "None":
            self.make_df_lane_info(obj_node_data)

    def make_route_structure(
        self,
        obj_node_data,
        lane_offset_start,
        lane_offset_end,
        lane_count_start,
        lane_count_end,
    ):
        """
        Create route structure with specified lane configurations.
        
        Args:
            obj_node_data: Object containing node data
            lane_offset_start (float): Starting offset for lanes
            lane_offset_end (float): Ending offset for lanes
            lane_count_start (int): Number of lanes at start
            lane_count_end (int): Number of lanes at end
        """
        self.make_df_polyline(obj_node_data)
        if self.error_is == "None":
            self.make_df_lane_route_info(
                obj_node_data,
                lane_offset_start,
                lane_offset_end,
                lane_count_start,
                lane_count_end,
            )

    def make_df_polyline(self, obj_node_data):
        """
        Create polyline DataFrame from node data.
        
        Args:
            obj_node_data: Object containing node data
        """
        main_id_list = []
        main_x_list = []
        main_y_list = []
        main_z_list = []
        main_z_param_list = []

        for i in range(len(obj_node_data)):
            x_list = []
            y_list = []
            z_list = []
            z_param_list = []

            if len(obj_node_data[i].center) == 0:
                self.error_is = "main road's points number is not enough"
                return

            if i != 0:
                x_center = obj_node_data[i - 1].center[-1]["x"]
                y_center = obj_node_data[i - 1].center[-1]["y"]
                z_center = obj_node_data[i - 1].center[-1]["elevation"]
                z_param_center = obj_node_data[i - 1].center[-1]["elev_param"]
                # Calculate relative distance and direction
                x_list.append(x_center)
                y_list.append(y_center)
                z_list.append(z_center)
                z_param_list.append(z_param_center)

            for j in range(len(obj_node_data[i].center)):
                x_center = obj_node_data[i].center[j]["x"]
                y_center = obj_node_data[i].center[j]["y"]
                z_center = obj_node_data[i].center[j]["elevation"]
                z_param_center = obj_node_data[i].center[j]["elev_param"]
                # Calculate relative distance and direction
                x_list.append(x_center)
                y_list.append(y_center)
                z_list.append(z_center)
                z_param_list.append(z_param_center)

            main_id_list += [i] * len(x_list)
            main_x_list += x_list
            main_y_list += y_list
            main_z_list += z_list
            main_z_param_list += z_param_list

        # Extract elevation parameters
        main_z_s_list = [x["s"] for x in main_z_param_list]
        main_z_a_list = [x["a"] for x in main_z_param_list]
        main_z_b_list = [x["b"] for x in main_z_param_list]
        main_z_c_list = [x["c"] for x in main_z_param_list]
        main_z_d_list = [x["d"] for x in main_z_param_list]

        if len(main_id_list) <= 2:
            self.error_is = "main road's points number is not enough"
            return

        # Create DataFrame dictionary
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

        main_df_polyline = pd.DataFrame(data=main_df_polyline_dict)
        main_df_polyline = self.add_curvature_info(main_df_polyline)
        out_df = pd.concat([main_df_polyline])
        self.df_polyline = out_df.reset_index(drop=True)

    def make_df_lane_info(self, obj_node_data):
        """
        Create lane information DataFrame for basic road structure.
        
        Creates a DataFrame containing lane information including:
        - Road IDs and connections
        - Lane properties (width, type, direction)
        - Lane change permissions
        - Speed limits
        
        Args:
            obj_node_data: Object containing node data
        """
        road_id_list = []
        p_road_type_list = []
        road_predecessor_id_list = []
        p_contact_point_list = []
        s_road_type_list = []
        road_successor_id_list = []
        s_contact_point_list = []
        offset_list = []
        lane_change_list = []
        direction_list = []
        lane_id_list = []
        lane_predecessor_list = []
        lane_successor_list = []
        lane_width_list = []
        type_list = []
        length_list = []
        space_list = []
        speed_list = []
        unit_list = []

        main_lane_num = 1

        for i in range(len(obj_node_data)):
            main_lane_width = obj_node_data[i].width
            main_lane_maxspeed = obj_node_data[i].maxspeed

            road_id_list += [i] * (main_lane_num + 1)

            if i == 0:
                p_road_type_list += [""] * (main_lane_num + 1)
            else:
                p_road_type_list += ["road"] * (main_lane_num + 1)

            if i == 0:
                road_predecessor_id_list += [""] * (main_lane_num + 1)
            else:
                road_predecessor_id_list += [i - 1] * (main_lane_num + 1)

            if i == 0:
                p_contact_point_list += [""] * (main_lane_num + 1)
            else:
                p_contact_point_list += ["end"] * (main_lane_num + 1)

            if i == len(obj_node_data) - 1:
                s_road_type_list += [""] * (main_lane_num + 1)
            else:
                s_road_type_list += ["road"] * (main_lane_num + 1)

            if i == len(obj_node_data) - 1:
                road_successor_id_list += [""] * (main_lane_num + 1)
            else:
                road_successor_id_list += [i + 1] * (main_lane_num + 1)

            if i == len(obj_node_data) - 1:
                s_contact_point_list += [""] * (main_lane_num + 1)
            else:
                s_contact_point_list += ["start"] * (main_lane_num + 1)

            offset_list += [0 * main_lane_num] * (main_lane_num + 1)

            lane_change_list_0 = ["none"]
            for j in range(main_lane_num - 1):
                lane_change_list_0.append("both")
            lane_change_list_0.append("none")

            lane_change_list += lane_change_list_0

            direction_list += ["left"] * (main_lane_num) + ["center"]

            lane_id_list_0 = []
            for j in range(main_lane_num + 1):
                lane_id_list_0.append(main_lane_num - j)

            lane_id_list += lane_id_list_0

            if i == 0:
                lane_predecessor_list += [""] * (main_lane_num + 1)
            else:
                lane_predecessor_list_1 = []
                for j in range(main_lane_num):
                    lane_predecessor_list_1.append(main_lane_num - j)
                lane_predecessor_list_1.append("")

                lane_predecessor_list += lane_predecessor_list_1

            if i == len(obj_node_data) - 1:
                lane_successor_list += [""] * (main_lane_num + 1)
            else:
                lane_successor_list_0 = []
                for j in range(main_lane_num):
                    lane_successor_list_0.insert(0, j + 1)
                lane_successor_list_0.append("")

                lane_successor_list += lane_successor_list_0

            lane_width_list += [main_lane_width] * main_lane_num + [0.125]

            type_list_0 = ["solid"]
            for j in range(main_lane_num - 1):
                type_list_0.append("broken")
            type_list_0.append("solid")

            type_list += type_list_0

            length_list_0 = [10]
            for j in range(main_lane_num - 1):
                length_list_0.append(5)
            length_list_0.append(10)

            length_list += length_list_0

            space_list_0 = [0]
            for j in range(main_lane_num - 1):
                space_list_0.append(5)
            space_list_0.append(0)

            space_list += space_list_0

            speed_list += [main_lane_maxspeed] * (main_lane_num + 1)

            unit_list += ["km/h"] * (main_lane_num + 1)

        # Set up DataFrame dictionary
        df_laneinfo_dict = dict(
            road_id=road_id_list,
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

        self.df_lane_info = pd.DataFrame(data=df_laneinfo_dict)

    def make_df_lane_route_info(
        self,
        obj_node_data,
        lane_offset_start,
        lane_offset_end,
        lane_count_start,
        lane_count_end,
    ):
        """
        Create lane information DataFrame for complex route structures.
        
        Creates a DataFrame containing detailed lane information for routes with:
        - Variable lane counts
        - Lane transitions
        - Complex offset configurations
        - Lane width variations
        
        Args:
            obj_node_data: Object containing node data
            lane_offset_start (float): Starting offset for lanes
            lane_offset_end (float): Ending offset for lanes
            lane_count_start (int): Number of lanes at start
            lane_count_end (int): Number of lanes at end
            
        Notes:
            Handles various lane transition scenarios:
            - Equal lane counts
            - Lane additions/reductions
            - Gradual transitions over distance
        """
        road_id_list = []
        p_road_type_list = []
        road_predecessor_id_list = []
        p_contact_point_list = []
        s_road_type_list = []
        road_successor_id_list = []
        s_contact_point_list = []
        offset_a_list = []
        offset_b_list = []
        offset_c_list = []
        offset_d_list = []
        lane_change_list = []
        direction_list = []
        lane_id_list = []
        lane_predecessor_list = []
        lane_successor_list = []
        lane_width_a_list = []
        lane_width_b_list = []
        type_list = []
        length_list = []
        space_list = []
        speed_list = []
        unit_list = []

        # lane_count_start = 4
        # lane_count_end = 4
        # lane_offset_start = 0
        # lane_offset_end = 0

        if lane_count_start == lane_count_end and lane_count_start != 0:
            main_lane_num = lane_count_start - 1
        elif lane_count_start == 0 and lane_count_end != 0:
            main_lane_num = lane_count_end - 1
        elif lane_count_end == 0 and lane_count_start != 0:
            main_lane_num = lane_count_start - 1
        elif (
            lane_count_end != 0
            and lane_count_start != 0
            and lane_count_start != lane_count_end
        ):
            print("WARNING: The main line has a variable number of lanes")
            if lane_count_start > lane_count_end:
                main_lane_num = lane_count_start - 1
            elif lane_count_start < lane_count_end:
                main_lane_num = lane_count_end - 1
        else:
            print("the main line has no connection to any junction.")
            main_lane_num = 1

        for i in range(len(obj_node_data)):
            main_lane_width = obj_node_data[i].width
            main_lane_maxspeed = obj_node_data[i].maxspeed

            road_id_list += [i] * (main_lane_num + 1)

            if i == 0:
                p_road_type_list += [""] * (main_lane_num + 1)
            else:
                p_road_type_list += ["road"] * (main_lane_num + 1)

            if i == 0:
                road_predecessor_id_list += [""] * (main_lane_num + 1)
            else:
                road_predecessor_id_list += [i - 1] * (main_lane_num + 1)

            if i == 0:
                p_contact_point_list += [""] * (main_lane_num + 1)
            else:
                p_contact_point_list += ["end"] * (main_lane_num + 1)

            if i == len(obj_node_data) - 1:
                s_road_type_list += [""] * (main_lane_num + 1)
            else:
                s_road_type_list += ["road"] * (main_lane_num + 1)

            if i == len(obj_node_data) - 1:
                road_successor_id_list += [""] * (main_lane_num + 1)
            else:
                road_successor_id_list += [i + 1] * (main_lane_num + 1)

            if i == len(obj_node_data) - 1:
                s_contact_point_list += [""] * (main_lane_num + 1)
            else:
                s_contact_point_list += ["start"] * (main_lane_num + 1)

            s_length = self.df_polyline[self.df_polyline["ID"] == i][
                "length"
            ].sum()

            if (
                lane_offset_end != 0 and lane_offset_start != 0
            ) or lane_offset_start == lane_offset_end:
                offset_a_list += [
                    lane_offset_start
                    + ((lane_offset_end - lane_offset_start) * i)
                    / (len(obj_node_data))
                ] * (main_lane_num + 1)

                offset_b_list += [
                    (
                        (lane_offset_end - lane_offset_start)
                        / ((s_length) * len(obj_node_data))
                    )
                ] * (main_lane_num + 1)

                offset_c_list += [0 * main_lane_num] * (main_lane_num + 1)

                offset_d_list += [0 * main_lane_num] * (main_lane_num + 1)

            elif lane_offset_end != 0 and lane_offset_start == 0:
                offset_a_list += [lane_offset_end] * (main_lane_num + 1)

                offset_b_list += [0 * main_lane_num] * (main_lane_num + 1)

                offset_c_list += [0 * main_lane_num] * (main_lane_num + 1)

                offset_d_list += [0 * main_lane_num] * (main_lane_num + 1)

            elif lane_offset_end == 0 and lane_offset_start != 0:
                offset_a_list += [lane_offset_start] * (main_lane_num + 1)

                offset_b_list += [0 * main_lane_num] * (main_lane_num + 1)

                offset_c_list += [0 * main_lane_num] * (main_lane_num + 1)

                offset_d_list += [0 * main_lane_num] * (main_lane_num + 1)

            if (
                lane_count_end != 0
                and lane_count_start != 0
                and lane_count_start == lane_count_end + 1
            ):
                lane_width_a_list += (
                    [
                        main_lane_width * (lane_count_start - lane_count_end)
                        - (
                            (lane_count_start - lane_count_end)
                            * main_lane_width
                            * i
                        )
                        / len(obj_node_data)
                    ]
                    + [main_lane_width] * (main_lane_num - 1)
                    + [0.125]
                )
                lane_width_b_list += (
                    [
                        (
                            (
                                (-lane_count_start + lane_count_end)
                                * main_lane_width
                            )
                            / len(obj_node_data)
                        )
                        / (s_length)
                    ]
                    + [0] * (main_lane_num - 1)
                    + [0]
                )

            elif (
                lane_count_end != 0
                and lane_count_start != 0
                and lane_count_start == lane_count_end + 2
            ):
                if len(obj_node_data) > 1 and i < round(
                    len(obj_node_data) / 2, 0
                ):
                    lane_width_a_list += (
                        [
                            main_lane_width
                            - (main_lane_width * i)
                            / round(len(obj_node_data) / 2, 0)
                        ]
                        + [main_lane_width] * (main_lane_num - 1)
                        + [0.125]
                    )
                    lane_width_b_list += (
                        [
                            (
                                ((-1) * main_lane_width)
                                / round(len(obj_node_data) / 2, 0)
                            )
                            / (s_length)
                        ]
                        + [0] * (main_lane_num - 1)
                        + [0]
                    )

                elif len(obj_node_data) > 1 and i >= round(
                    len(obj_node_data) / 2, 0
                ):
                    lane_width_a_list += (
                        [0]
                        + [
                            main_lane_width
                            - (
                                main_lane_width
                                * (i - round(len(obj_node_data) / 2, 0))
                            )
                            / (
                                len(obj_node_data)
                                - round(len(obj_node_data) / 2, 0)
                            )
                        ]
                        + [main_lane_width] * (main_lane_num - 2)
                        + [0.125]
                    )
                    lane_width_b_list += (
                        [0]
                        + [
                            (
                                ((-1) * main_lane_width)
                                / (
                                    len(obj_node_data)
                                    - round(len(obj_node_data) / 2, 0)
                                )
                            )
                            / (s_length)
                        ]
                        + [0] * (main_lane_num - 2)
                        + [0]
                    )

                else:
                    lane_width_a_list += (
                        [
                            main_lane_width
                            - (main_lane_width * i) / len(obj_node_data)
                        ]
                        + [
                            main_lane_width
                            - (main_lane_width * i) / len(obj_node_data)
                        ]
                        + [main_lane_width] * (main_lane_num - 2)
                        + [0.125]
                    )
                    lane_width_b_list += (
                        [
                            (((-1) * main_lane_width) / len(obj_node_data))
                            / (s_length)
                        ]
                        + [
                            (((-1) * main_lane_width) / len(obj_node_data))
                            / (s_length)
                        ]
                        + [0] * (main_lane_num - 2)
                        + [0]
                    )

            elif (
                lane_count_end != 0
                and lane_count_start != 0
                and lane_count_start == lane_count_end - 1
            ):
                lane_width_a_list += (
                    [
                        (
                            (-lane_count_start + lane_count_end)
                            * main_lane_width
                            * i
                        )
                        / len(obj_node_data)
                    ]
                    + [main_lane_width] * (main_lane_num - 1)
                    + [0.125]
                )
                lane_width_b_list += (
                    [
                        (
                            (
                                (-lane_count_start + lane_count_end)
                                * main_lane_width
                            )
                            / len(obj_node_data)
                        )
                        / (s_length)
                    ]
                    + [0] * (main_lane_num - 1)
                    + [0]
                )

            elif (
                lane_count_end != 0
                and lane_count_start != 0
                and lane_count_start == lane_count_end - 2
            ):
                if len(obj_node_data) > 1 and i < round(
                    len(obj_node_data) / 2, 0
                ):
                    lane_width_a_list += (
                        [0]
                        + [
                            (main_lane_width * i)
                            / round(len(obj_node_data) / 2, 0)
                        ]
                        + [main_lane_width] * (main_lane_num - 2)
                        + [0.125]
                    )
                    lane_width_b_list += (
                        [0]
                        + [
                            (
                                (main_lane_width)
                                / round(len(obj_node_data) / 2, 0)
                            )
                            / (s_length)
                        ]
                        + [0] * (main_lane_num - 2)
                        + [0]
                    )

                elif len(obj_node_data) > 1 and i >= round(
                    len(obj_node_data) / 2, 0
                ):
                    lane_width_a_list += (
                        [
                            (
                                main_lane_width
                                * (i - round(len(obj_node_data) / 2, 0))
                            )
                            / (
                                len(obj_node_data)
                                - round(len(obj_node_data) / 2, 0)
                            )
                        ]
                        + [main_lane_width] * (main_lane_num - 1)
                        + [0.125]
                    )
                    lane_width_b_list += (
                        [
                            (
                                (main_lane_width)
                                / (
                                    len(obj_node_data)
                                    - round(len(obj_node_data) / 2, 0)
                                )
                            )
                            / (s_length)
                        ]
                        + [0] * (main_lane_num - 1)
                        + [0]
                    )

                else:
                    lane_width_a_list += (
                        [(main_lane_width * i) / len(obj_node_data)]
                        + [(main_lane_width * i) / len(obj_node_data)]
                        + [main_lane_width] * (main_lane_num - 2)
                        + [0.125]
                    )
                    lane_width_b_list += (
                        [((main_lane_width) / len(obj_node_data)) / (s_length)]
                        + [
                            ((main_lane_width) / len(obj_node_data))
                            / (s_length)
                        ]
                        + [0] * (main_lane_num - 2)
                        + [0]
                    )

            else:
                lane_width_a_list += [main_lane_width] * main_lane_num + [0.125]
                lane_width_b_list += [0] * main_lane_num + [0]

            lane_change_list_0 = ["none"]
            for j in range(main_lane_num - 1):
                lane_change_list_0.append("both")
            lane_change_list_0.append("none")

            lane_change_list += lane_change_list_0

            direction_list += ["left"] * (main_lane_num) + ["center"]

            lane_id_list_0 = []
            for j in range(main_lane_num + 1):
                lane_id_list_0.append(main_lane_num - j)

            lane_id_list += lane_id_list_0

            if i == 0:
                lane_predecessor_list += [""] * (main_lane_num + 1)
            else:
                lane_predecessor_list_1 = []
                for j in range(main_lane_num):
                    lane_predecessor_list_1.append(main_lane_num - j)
                lane_predecessor_list_1.append("")

                lane_predecessor_list += lane_predecessor_list_1

            if i == len(obj_node_data) - 1:
                lane_successor_list += [""] * (main_lane_num + 1)
            else:
                lane_successor_list_0 = []
                for j in range(main_lane_num):
                    lane_successor_list_0.insert(0, j + 1)
                lane_successor_list_0.append("")

                lane_successor_list += lane_successor_list_0

            type_list_0 = ["solid"]
            for j in range(main_lane_num - 1):
                type_list_0.append("broken")
            type_list_0.append("solid")

            type_list += type_list_0

            length_list_0 = [10]
            for j in range(main_lane_num - 1):
                length_list_0.append(5)
            length_list_0.append(10)

            length_list += length_list_0

            space_list_0 = [0]
            for j in range(main_lane_num - 1):
                space_list_0.append(5)
            space_list_0.append(0)

            space_list += space_list_0

            speed_list += [main_lane_maxspeed] * (main_lane_num + 1)

            unit_list += ["km/h"] * (main_lane_num + 1)

        # Set up DataFrame dictionary
        df_laneinfo_dict = dict(
            road_id=road_id_list,
            p_road_type=p_road_type_list,
            road_predecessor_id=road_predecessor_id_list,
            p_contact_point=p_contact_point_list,
            s_road_type=s_road_type_list,
            road_successor_id=road_successor_id_list,
            s_contact_point=s_contact_point_list,
            offset_a=offset_a_list,
            offset_b=offset_b_list,
            offset_c=offset_c_list,
            offset_d=offset_d_list,
            lane_change=lane_change_list,
            direction=direction_list,
            lane_id=lane_id_list,
            lane_predecessor=lane_predecessor_list,
            lane_successor=lane_successor_list,
            lane_width_a=lane_width_a_list,
            lane_width_b=lane_width_b_list,
            type=type_list,
            length=length_list,
            space=space_list,
            speed=speed_list,
            unit=unit_list,
        )

        self.df_lane_info = pd.DataFrame(data=df_laneinfo_dict)

    def add_curvature_info(self, imp_df):
        """
        Add curvature information to the polyline data.
        
        Calculates and adds the following information for each point:
        - Curvature radius and center
        - Heading angles
        - Shape type (arc/line/spiral)
        
        Args:
            imp_df (pd.DataFrame): Input DataFrame with polyline data containing X,Y coordinates
            
        Returns:
            pd.DataFrame: DataFrame with added curvature information including:
                - ID: Point identifier
                - x,y: Coordinates
                - curvature_radius: Radius of curvature
                - cx,cy: Center of curvature coordinates
                - curvature: 1/radius
                - hdg: Heading angle
                - elev: Elevation data
                - shape: Road segment shape type
        """
        o_list = []  # List for creating DataFrame
        iter = len(imp_df)  # Number of iterations
        length = [20, 10, 0]

        # Calculate curvature for each point
        for i in range(1, iter - 1):
            for j in length:
                r, cx, cy = ccf.culc_curveture(imp_df["X"], imp_df["Y"], i, j)
                rr = 1 / r
                if j < abs(r):
                    o_list.append([
                        int(imp_df["ID"][i]),
                        imp_df["X"][i],
                        imp_df["Y"][i],
                        r, cx, cy, rr
                    ])
                    break

        # Copy curvature for start and end points
        o_list.insert(0, [
            int(imp_df["ID"][0]),
            imp_df["X"][0],
            imp_df["Y"][0],
            o_list[0][3],
            o_list[0][4],
            o_list[0][5],
            o_list[0][6],
        ])
        
        o_list.append([
            int(imp_df["ID"][iter - 1]),
            imp_df["X"][iter - 1],
            imp_df["Y"][iter - 1],
            o_list[-1][3],
            o_list[-1][4],
            o_list[-1][5],
            o_list[-1][6],
        ])

        # Calculate heading angles
        hdg_list = []
        for i in range(len(o_list)):
            tmp_rad = math.atan2(
                o_list[i][2] - o_list[i][5], 
                o_list[i][1] - o_list[i][4]
            )
            # Reverse direction if curvature is negative
            if o_list[i][3] < 0:
                tmp_rad = tmp_rad + math.pi
            # 90 degree offset to convert from center angle to road direction
            rad = tmp_rad + math.pi / 2
            hdg_list.append(rad)

        # Add heading angles and elevation data
        for i in range(len(o_list)):
            o_list[i].extend([hdg_list[i]])
            o_list[i].append(imp_df["elev"][i])
            o_list[i].append(imp_df["elev_a"][i])
            o_list[i].append(imp_df["elev_b"][i])
            o_list[i].append(imp_df["elev_c"][i])
            o_list[i].append(imp_df["elev_d"][i])
            o_list[i].append(imp_df["elev_s"][i])

        # Determine shape type for each segment
        for i in range(int(len(o_list)) - 1):
            shape = (
                "arc" if o_list[i][3] == o_list[i + 1][3]
                else "line" if abs(o_list[i][3]) > 5000
                else "spiral"
            )
            o_list[i].extend([shape])

        # Create and format output DataFrame
        o_df = pd.DataFrame(o_list)
        o_df = o_df.rename(
            columns={
                0: "ID",
                1: "x",
                2: "y",
                3: "curvature_radius",
                4: "cx",
                5: "cy",
                6: "curvature",
                7: "hdg",
                8: "elev",
                9: "elev_a",
                10: "elev_b",
                11: "elev_c",
                12: "elev_d",
                13: "length",
                14: "shape",
            }
        )

        return o_df
