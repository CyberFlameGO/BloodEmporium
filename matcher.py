import math
import os.path

import cv2
import cv2.cv2
import networkx as nx
import numpy as np
from pyvis.network import Network

from mergedbase import MergedBase
from node import Node
from utils.distance_util import circles_are_overlapping, line_close_to_circle, get_endpoints

'''
Offerings | Killer + Survivor | Hexagon | C:/Program Files (x86)/Steam/steamapps/common/Dead by Daylight/DeadByDaylight/Content/UI/Icons/Favors
Addons    | Killer + Survivor | Square  | C:/Program Files (x86)/Steam/steamapps/common/Dead by Daylight/DeadByDaylight/Content/UI/Icons/ItemAddons
Items     | Survivor          | Square  | C:/Program Files (x86)/Steam/steamapps/common/Dead by Daylight/DeadByDaylight/Content/UI/Icons/Items
Perks     | Killer + Survivor | Diamond | C:/Program Files (x86)/Steam/steamapps/common/Dead by Daylight/DeadByDaylight/Content/UI/Icons/Perks
'''

'''
cv2.IMREAD_COLOR
cv2.IMREAD_GRAYSCALE
cv2.IMREAD_UNCHANGED
'''

# TODO mystery boxes in assets folder

class HoughTransform:
    def __init__(self, path_to_image, c_blur=11, param1=10, param2=45, l_blur=5,
                 canny_min=85, canny_max=40, threshold=30, max_line_length=25):
        '''
        identifies all the nodes and connections in the image, as well as the origin
        '''
        self.image_gray = cv2.imread(path_to_image, cv2.IMREAD_GRAYSCALE)
        self.image_r = cv2.split(cv2.imread(path_to_image, cv2.IMREAD_UNCHANGED))[2]

        self.__output = self.image_gray.copy()
        self.__output_validated = self.image_gray.copy()

        self.__run_hough_circle(c_blur, param1, param2)
        self.__match_origin()
        self.__run_hough_line(l_blur, canny_min, canny_max, threshold, max_line_length)
        self.__validate_all()

        cv2.imshow("output", self.__output)
        cv2.imshow("output_validated", self.__output_validated)
        # cv2.imshow("edges", self.edges)
        cv2.waitKey(0)

    def get_valid_circles(self):
        '''
        :return: {((x, y), r, colour): id}
        '''
        return self.valid_circles

    def get_connections(self):
        '''
        :return: [circle, circle]
        '''
        return self.connections

    def get_origin(self):
        '''
        :return: (x, y)
        '''
        return self.origin_position

    def __run_hough_circle(self, c_blur, param1, param2):
        '''
        identify all nodes (circles) in image
        '''

        blurred_image = cv2.GaussianBlur(self.image_gray, (c_blur, c_blur), sigmaX=0, sigmaY=0) # circles

        # TODO minDist, minRadius and maxRadius will need to scale from UI size

        # detect circles in the image
        circles = cv2.HoughCircles(blurred_image, cv2.HOUGH_GRADIENT, dp=1, minDist=80,
                                   param1=param1, param2=param2, minRadius=7, maxRadius=50)

        self.circles = [] # ((x, y), r, colour)
        if circles is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.round(circles[0, :]).astype("int")

            # loop over the (x, y) coordinates and radius of the circles
            for (x, y, r) in circles:
                cv2.circle(self.__output, (x, y), r, 255, 1)
                cv2.rectangle(self.__output, (x - 5, y - 5), (x + 5, y + 5), 255, -1)

                # remove the node from the edges graph
                self.circles.append(((x, y), r, "yellow")) # TODO need to read colour from image

    def __match_origin(self):
        matches = []

        height, width = self.image_r.shape
        crop_ratio = 3
        cropped = self.image_r[math.floor(height / crop_ratio):math.floor((crop_ratio - 1) * height / crop_ratio),
                               math.floor(width / crop_ratio):math.floor((crop_ratio - 1) * width / crop_ratio)]

        dim = 40 # TODO adjust based on resolution and UI
        radius = math.floor(dim / 2)
        for subdir, dirs, files in os.walk("assets"):
            for file in files:
                if "origin" in file:

                    image = cv2.split(cv2.imread(os.path.join(subdir, file), cv2.IMREAD_UNCHANGED))
                    template = cv2.resize(image[2], (dim, dim), interpolation=cv2.INTER_AREA)
                    template_alpha = cv2.resize(image[3], (dim, dim), interpolation=cv2.INTER_AREA) # for masking
                    result = cv2.matchTemplate(cropped, template, cv2.TM_CCORR_NORMED, mask=template_alpha)

                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    matches.append((file, min_val, max_val, min_loc, max_loc))

        origin_type, _, _, _, top_left = max(matches, key=lambda match: match[2])

        centre = (math.floor(top_left[0] + radius + width / crop_ratio), math.floor(top_left[1] + radius + height / crop_ratio))
        cv2.circle(self.__output_validated, centre, radius, 255, 4)
        self.circles.append((centre, radius, "yellow"))
        self.origin_position = centre

    def __run_hough_line(self, l_blur, canny_min, canny_max, threshold, max_line_length):
        '''
        identify all connections (lines) in image
        '''

        base_l = cv2.GaussianBlur(self.image_gray, (l_blur, l_blur), sigmaX=0, sigmaY=0) # lines
        self.edges = cv2.Canny(base_l, canny_min, canny_max)

        for (x, y), r, colour in self.circles:
            # remove the node from the edges graph
            cv2.circle(self.edges, (x, y), 1, 0, math.floor(r / 1.9) + 55) # tweak size of circle removal

        # TODO minLineLength will need to scale from UI size

        lines = cv2.HoughLinesP(self.edges, rho=1, theta=np.pi / 180, threshold=threshold, minLineLength=25, maxLineGap=max_line_length)

        self.lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(self.__output, (x1, y1), (x2, y2), 255, 5)
                self.lines.append(((x1, y1), (x2, y2)))

    def __validate_all(self):
        # validate lines by removing those that do not join two circles; add the connected nodes to edge list
        # validate circles by removing those which are not joined by lines
        self.valid_circles = {}
        self.connections = []
        for line in self.lines:
            circle1, circle2 = get_endpoints(line, self.circles)
            if circle1 is not None and circle2 is not None and \
                    (circle1, circle2) not in self.connections and (circle2, circle1) not in self.connections:
                self.connections.append((circle1, circle2))
                self.valid_circles[circle1] = "unassigned"
                self.valid_circles[circle2] = "unassigned"

                # draw the line
                (x1, y1), (x2, y2) = line
                cv2.line(self.__output_validated, (x1, y1), (x2, y2), 255, 5)

        for (x, y), r, _ in self.valid_circles.keys():
            # draw the circle in the output image, then draw a rectangle
            # corresponding to the center of the circle
            cv2.circle(self.__output_validated, (x, y), r, 255, 1)
            cv2.rectangle(self.__output_validated, (x - 5, y - 5), (x + 5, y + 5), 255, -1)

class Matcher:
    def __init__(self, image, nodes_connections, merged_base):
        # match each node of graph to an unlockable
        # TODO: if red we need to brighten it and enlarge by ~1.3333

        valid_circles = nodes_connections.get_valid_circles()
        connections = nodes_connections.get_connections()
        origin = nodes_connections.get_origin()

        # validate lines by removing those that do not join two circles; add the connected nodes to edge list
        # validate circles by removing those which are not joined by lines

        # match circles
        names = merged_base.names
        images = merged_base.images

        i = 0
        nodes = []
        for circle in valid_circles.keys():
            (x, y), r, colour = circle
            if (x, y) == origin:
                valid_circles[circle] = "ORIGIN"
                continue

            unlockable = image[y-r:y+r, x-r:x+r]

            # assuming our hough circle matching is accurate, we can use the radius to determine the resize factor
            # to be used on the unlockable

            height, width = unlockable.shape

            # apply template matching
            output = images.copy()
            result = cv2.matchTemplate(output, unlockable, cv2.TM_CCORR_NORMED)

            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            top_left = max_loc
            bottom_right = (top_left[0] + width, top_left[1] + height)

            output = output[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]

            match_name = names[math.floor((bottom_right[1] - 50) / 100)]
            node_id = f"{i}_{match_name}"
            nodes.append(Node(node_id, match_name, 9999, (x, y), True, False, False).get_tuple())
            valid_circles[circle] = node_id

            i += 1

            # cv2.imshow("unlockable from screen", unlockable)
            # cv2.imshow(f"matched unlockable", output)
            # cv2.waitKey(0)

        # cv2.destroyAllWindows()

        nodes.append(Node("ORIGIN", "ORIGIN", 9999, origin, True, False, False).get_tuple())

        # actual edges joining circles
        edges = []
        for (circle1, circle2) in connections:
            edges.append((valid_circles[circle1], valid_circles[circle2]))

        # construct networkx graph
        self.graph = nx.Graph()
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)

        net = Network(notebook=True, height=1080, width=1920)
        net.from_nx(self.graph)

        net.show("matcher.html")



        '''dim = 50

        np.set_printoptions(threshold=np.inf)
        template = cv2.imread(path_example, cv2.IMREAD_GRAYSCALE)
        template = cv2.resize(template, (dim, dim), interpolation=cv2.INTER_AREA) # configure in config, should be some default according to resolutions; diff for square vs hexagon vs diamond
        template_alpha = cv2.resize(cv2.split(cv2.imread(path_example, cv2.IMREAD_UNCHANGED))[3], (dim, dim), interpolation=cv2.INTER_AREA) # for masking

        base = cv2.imread(path_base, cv2.IMREAD_GRAYSCALE)

        height, width = template.shape

        # apply template matching
        output = base.copy()
        method = "cv2.TM_CCORR_NORMED"
        result = cv2.matchTemplate(output, template, eval(method), mask=template_alpha)

        single_match = True

        if single_match:
            # single match
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            top_left = max_loc
            bottom_right = (top_left[0] + width, top_left[1] + height)
            cv2.rectangle(output, top_left, bottom_right, 255, 2) # 255 = white; 2 = thickness
        else:
            # multiple matches
            threshold = 0.95 # larger value = better match / fit
            loc = np.where(result >= threshold)

            matches = []
            for top_left in zip(*loc[::-1]):
                bottom_right = (top_left[0] + width, top_left[1] + height)
                if not any([close_proximity_circle_to_circle(tl, top_left) and close_proximity_circle_to_circle(br, bottom_right) for (tl, br) in matches]):
                    matches.append((top_left, bottom_right))
                    cv2.rectangle(output, top_left, bottom_right, 255, 2) # 255 = white; 2 = thickness

        cv2.imshow(method, output)
        cv2.waitKey(0)

        cv2.imshow('Image', template)
        cv2.imshow('Base', base)
        cv2.waitKey(0)
        cv2.destroyAllWindows()'''

class CircleMatcher:
    @staticmethod
    def match(path_base, c_blur, param1, param2):
        base = cv2.imread(path_base, cv2.IMREAD_GRAYSCALE)
        base_c = cv2.GaussianBlur(base, (c_blur, c_blur), sigmaX=0, sigmaY=0) # circles

        height, width = base.shape
        output = np.zeros((height, width), np.uint8)

        # detect circles in the image
        circles = cv2.HoughCircles(base_c, cv2.HOUGH_GRADIENT, dp=1, minDist=80, param1=param1, param2=param2,
                                   minRadius=7, maxRadius=50)

        # circles = []
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                cv2.circle(output, (x, y), r, 255, 10)
                # circles.append((x, y, r))

        return output
