import math


class Resolution:
    '''
    the following constants scale from this resolution
    - 3840x2160 (4k)
    - UI scale 100
    '''
    __width = 3840
    __height = 2160
    __ui_scale = 100

    # node sizes
    __threshold_radius = 69
    __large_node_outer_radius = 82
    __large_node_inner_radius = 69
    __small_node_outer_radius = 62
    __small_node_inner_radius = 52

    # hough circles
    __gaussian_c = 10
    __bilateral_c = 15
    __min_dist = 170
    __min_radius = 15
    __max_radius = 105

    # origin
    __origin_dim = 96

    # hough lines
    __line_length = 54

    # template matching
    __items_addons = 115
    __offerings = 144
    __perks = 144

    def __init__(self, width, height, ui_scale):
        self.width = width
        self.height = height
        self.ui_scale = ui_scale

    def print(self):
        print(f"{self.width}x{self.height} @ {self.ui_scale}% UI Scale")

    def ratio(self):
        return self.width / Resolution.__width * self.ui_scale / Resolution.__ui_scale

    # node sizes
    @staticmethod
    def additional_radius(radius):
        return round(Resolution.__large_node_outer_radius / Resolution.__large_node_inner_radius * radius - radius)

    def threshold_radius(self):
        return round(Resolution.__threshold_radius * self.ratio())

    def large_node_outer_radius(self):
        return round(Resolution.__large_node_outer_radius * self.ratio())

    def large_node_inner_radius(self):
        return round(Resolution.__large_node_inner_radius * self.ratio())

    def small_node_outer_radius(self):
        return round(Resolution.__small_node_outer_radius * self.ratio())

    def small_node_inner_radius(self):
        return round(Resolution.__small_node_inner_radius * self.ratio())

    # hough circles
    def gaussian_c(self):
        c = (Resolution.__gaussian_c * self.ratio())
        ceil = math.ceil(c)
        floor = math.floor(c)
        if ceil % 2 == 1:
            return ceil
        if floor % 2 == 1:
            return floor
        return floor + 1

    def bilateral_c(self):
        return round(Resolution.__bilateral_c * self.ratio())

    def min_dist(self):
        return round(Resolution.__min_dist * self.ratio())

    def min_radius(self):
        return round(Resolution.__min_radius * self.ratio())

    def max_radius(self):
        return round(Resolution.__max_radius * self.ratio())

    # origin
    def origin_dim(self):
        return round(Resolution.__origin_dim * self.ratio())

    # hough lines
    def line_length(self):
        return round(Resolution.__line_length * self.ratio())

    # template matching
    def items_addons(self):
        return round(Resolution.__items_addons * self.ratio())

    def offerings(self):
        return round(Resolution.__offerings * self.ratio())

    def perks(self):
        return round(Resolution.__perks * self.ratio())
