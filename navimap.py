import datetime
from merge_extract import MergeExtract
from branch_extract import BranchExtract
from route_extract import RouteExtract


class NaviMap:
    def __init__(self):
        self.obj_node_data_list = []  # List of NodeData (merge center node information)
        self.obj_node_data_branch_list = []  # List of branch node data
        self.obj_node_data_merge_list = []  # List of merge node data
        self.obj_node_combine_data_list = []  # Combined node data list
        self.obj_line_data_list = []  # List of line data
        self.meshcode = []  # Secondary mesh code
        self.extract_flag = 0  

        now_time = datetime.datetime.now()
        self.operating_time = now_time.strftime("%Y-%m-%d_%H-%M")
        self.error_log = []

    def make_navi_map(self, latlon, extract_flag, highway_only, data_path, meshcode):
        self.latlon = latlon
        self.meshcode = meshcode
        self.extract_flag = extract_flag
        self.data_path = data_path

        if self.extract_flag == "mainlane":
            self._extract_mainlane(data_path, latlon, highway_only)
        elif self.extract_flag == "route":
            self._extract_route(data_path, latlon, highway_only)

    def _extract_mainlane(self, data_path, latlon, highway_only):
        route = RouteExtract(data_path)
        route.make_route_extract(self.operating_time, latlon, highway_only)
        self.obj_node_combine_data_list += route.mainlane_combine_ls
        self.error_log += route.error_log

    def _extract_route(self, data_path, latlon, highway_only):
        print("Extracting mainline information.")
        route = RouteExtract(data_path)
        route.make_route_extract(self.operating_time, latlon, highway_only)
        self.obj_node_combine_data_list += route.mainlane_combine_ls
        self.obj_line_data_list += route.line_ls
        self.error_log += route.error_log

        print("Extracting branch information.")
        self._extract_branch(data_path, latlon)

        print("Extracting merge information.")
        self._extract_merge(data_path, latlon)

        self._remove_unrelated_branches()
        self._remove_unrelated_merges()

    def _extract_branch(self, data_path, latlon):
        for mesh in self.meshcode:
            print("meshcode = ", mesh)
            branch = BranchExtract(mesh, 1, data_path)
            branch.make_branch_extract(self.operating_time, latlon)
            self._remove_invalid_nodes(branch.node_ls)
            self.obj_node_data_branch_list += branch.node_ls
            self.error_log += branch.error_log

    def _extract_merge(self, data_path, latlon):
        for mesh in self.meshcode:
            print("meshcode = ", mesh)
            merge = MergeExtract(mesh, 0, data_path)
            merge.make_merge_extract(self.operating_time, latlon)
            self._remove_invalid_nodes(merge.node_ls)
            self.obj_node_data_merge_list += merge.node_ls
            self.error_log += merge.error_log

    def _remove_invalid_nodes(self, node_list):
        error_ls = [j for j, node in enumerate(node_list) if len(node.border) < 3]
        for j in reversed(error_ls):
            node_list.pop(j)

    def _remove_unrelated_branches(self):
        self._remove_unrelated_nodes(self.obj_node_data_branch_list)

    def _remove_unrelated_merges(self):
        self._remove_unrelated_nodes(self.obj_node_data_merge_list)

    def _remove_unrelated_nodes(self, node_data_list):
        for i in range(len(node_data_list) - 1, -1, -1):
            if not self._is_node_related(node_data_list[i]):
                node_data_list.pop(i)

    def _is_node_related(self, node):
        for link in node.obj_link_data_list:
            for line in self.obj_line_data_list:
                if (round(link.line[0], 6) == round(line[0], 6) and
                    round(link.line[1], 6) == round(line[1], 6)):
                    return True
        return False

