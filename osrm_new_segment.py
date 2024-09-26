from datetime import datetime
from qgis.core import QgsWkbTypes, QgsGeometry
from .database_functions import *

class NewSegment:
    def __init__(self, segment_layer):
        self.geometry = self.extract_geometry(segment_layer)
        self.new_id = self.extract_id()
        self.road_type = "primary"
        self.direction = "both-ways"
        self.max_speed = ""

    def extract_geometry(self, layer):
        geometries = []

        provider = layer.dataProvider()
        features = provider.getFeatures()

        for feature in features:
            geometry = feature.geometry()
            geometries.append(geometry)

        return geometries[0]

    def get_table_data(self):
        return [self.new_id, self.road_type, self.direction, self.max_speed]

    def extract_id(self):
        return "1"

    def create_tags(self):
        tags = {}
        tags["highway"] = self.road_type
        if self.direction == "one-way":
            tags["oneway"] = "yes"
        elif self.direction == "both-ways":
            tags["oneway"] = "no"
        if self.max_speed != "0" and self.max_speed != "":
            tags["maxspeed"] = self.max_speed 
        tags["osrmcreated"] = "yes" 
        tags_string = ", ".join(f"{key}=>{value}" for key, value in tags.items())
        return tags_string

    def create_gen_attributes(self):
        attributes = {}
        attributes["version"] = 1
        attributes["user_id"] = 99999999
        now = datetime.now()
        attributes["tstamp"] = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        attributes["changeset_id"] = 999999999
        return attributes

    def extract_geometry_nodes(self):
        # Extract qgis nodes wkt from qgis line
        qgs_nodes = []
        if self.geometry.type() != QgsWkbTypes.LineGeometry:
            return False
        coords = self.geometry.asPolyline()
        qgs_nodes.extend(coords)

        # Create qgis geometry WKT
        wkt_nodes = []
        for qgs_node in qgs_nodes:
            wkt = f"POINT({qgs_node.x()} {qgs_node.y()})"
            wkt_nodes.append(wkt)
        return wkt_nodes

    def create_nodes_bd(self, id_node_max):
        gen_attributes = self.create_gen_attributes()
        nodes = self.extract_geometry_nodes()
        if not nodes:
            return False
        max_id = id_node_max
        nodes_bd = []
        for node in nodes[1:]:  # Don't use first node, first node = existing node
            node_attributes = gen_attributes.copy()
            max_id += 1
            node_attributes["id"] = max_id
            node_attributes["tags"] = "osrmcreated=>yes"
            node_attributes["geom"] = node
            nodes_bd.append(node_attributes)
        return nodes_bd  # List with all nodes attributes as dict

    def create_way_nodes_bd(self, id_node_max, id_way, connected_node_id):
        nodes = self.extract_geometry_nodes()
        if not nodes:
            return False

        way_nodes_bd = []
        seq = 0

        # First node is existing node, get data from database
        first_node = {
            "way_id": id_way + 1,
            "node_id": connected_node_id,
            "sequence_id": seq
        }
        way_nodes_bd.append(first_node)

        # Rest of nodes
        max_id = id_node_max
        seq += 1
        for node in nodes[1:]:  # Don't use first node, first node = existing node
            node_attributes = {}
            node_attributes["way_id"] = id_way + 1
            max_id += 1
            node_attributes["node_id"] = max_id
            node_attributes["sequence_id"] = seq
            seq += 1
            way_nodes_bd.append(node_attributes)
        return way_nodes_bd

    def create_ways_bd(self, id_node_max, id_way, connected_node_id):
        # create list of nodes
        nodes = self.extract_geometry_nodes()
        if not nodes:
            return False
        num_nodes = len(nodes)
        list_nodes = []
        list_nodes.append(connected_node_id)
        list_nodes.extend([i for i in range(id_node_max + 1, id_node_max + 1 + num_nodes - 1)])

        ways_bd = []
        attributes = self.create_gen_attributes()
        attributes["nodes"] = list_nodes
        attributes["linestring"] = self.geometry.asWkt()
        attributes["tags"] = self.create_tags()
        bboxgeometry = QgsGeometry.fromRect(self.geometry.boundingBox())
        bboxWkt = bboxgeometry.asWkt()
        attributes["bbox"] = bboxWkt
        attributes["id"] = id_way + 1

        ways_bd.append(attributes)
        return ways_bd

    def create_user_bd(self):
        user_bd = []
        osrm_user = {"id": 99999999,
                     "name": "osrm_editor"}
        user_bd.append(osrm_user)
        return user_bd
