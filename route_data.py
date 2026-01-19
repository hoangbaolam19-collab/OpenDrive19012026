class NodeData:
    """Base class for node data structures in road network."""

    def __init__(self):
        self.meshcode = 0
        self.nodeno = 0
        self.coordinate = {"lat": 0, "lon": 0}
        self.obj_link_data_list = []


class LinkData:
    """Base class for link data structures in road network."""

    def __init__(self):
        self.meshcode = 0  #
        self.linkno = 0
        self.snodeno = 0
        self.enodeno = 0
        self.lanecnt = 0
        self.width = 3.5
        self.maxspeed = 0
        self.center = []
        self.roadelevation = []  #
        self.road_name = 0  #
        self.link_code = 0  #
        self.closest = {"lat": 0, "lon": 0}  #
        self.op = 0  #


class BranchData(NodeData):
    """Class representing branch junctions in road network."""

    def __init__(self):
        super().__init__()
        self.starting_point = {"lat": 0, "lon": 0}  #
        self.starting_border = {"lat": 0, "lon": 0}  #
        self.border = []  #
        self.border_length = "non"
        self.branch_direction = "non"
        self.road_gradient = 0
        self.curvature = []


class MergeData(NodeData):
    """Class representing merge junctions in road network."""

    def __init__(self):
        super().__init__()
        self.starting_point = {"lat": 0, "lon": 0}
        self.starting_border = {"lat": 0, "lon": 0}
        self.border = []
        self.border_length = "non"
        self.merge_direction = "non"  # 0 : left, 1 : right
        self.road_gradient = 0
        self.curvature = []


class RouteData(LinkData):
    """Class representing route data in road network."""

    def __init__(self):
        super().__init__()
        self.lane_transform_direction = "non"
        self.starting_point = {"lat": 0, "lon": 0}
        self.road_gradient = 0
        self.curvature = []
        self.obj_line_data_list = []
        self.line = []
