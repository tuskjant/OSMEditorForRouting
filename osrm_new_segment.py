class NewSegment:
    def __init__(self, segment_layer):
        self.geometry = self.extract_geometry(segment_layer)
        self.new_id = self.extract_id()
        self.road_type = "primary"
        self.direction = "both-ways"
        self.max_speed = ""
        self.reversed = False
    
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
        pass