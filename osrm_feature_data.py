from .osrm_car_profile import CarProfile 
from qgis.core import Qgis
import re

class OsrmFeatureData:
    tags_field_name = "tags"

    def __init__(self, feature, iface):
        self.iface = iface
        self.feature = feature
        self.osrm_car_profile = CarProfile()
        self.tags_value = feature[self.tags_field_name]
        self.id = feature["id"]
        self.name = self.tags_value["name"] if "name" in self.tags_value.keys() else ""

    def get_tags_data(self, data_option):
        if data_option == "access":
            access = self.tags_value["access"] if "access" in self.tags_value.keys() else None
            vehicle = self.tags_value["vehicle"] if "vehicle" in self.tags_value.keys() else None
            motor_vehicle = self.tags_value["motor_vehicle"] if "motor_vehicle" in self.tags_value.keys() else None
            motor_car = self.tags_value["motor_car"] if "motor_car" in self.tags_value.keys() else None
            return {"access": access, "vehicle": vehicle, "motor_vehicle": motor_vehicle, "motor_car": motor_car}
        elif data_option == "oneway":
            one_way = self.tags_value["oneway"] if "oneway" in self.tags_value.keys() else None
            highway = self.tags_value["highway"] if "highway" in self.tags_value.keys() else None
            junction = self.tags_value["junction"] if "junction" in self.tags_value.keys() else None
            return {"oneway": one_way, "highway": highway, "junction": junction}
        elif data_option == "speed":
            max_speed = self.tags_value["maxspeed"] if "maxspeed" in self.tags_value.keys() else None
            highway = self.tags_value["highway"] if "highway" in self.tags_value.keys() else None
            return {"maxspeed": max_speed, "highway": highway}

    def extract_access_value(self):
        # check access tag
        tags_data = self.get_tags_data("access")
        access = tags_data["access"]
        # get access whitelist and blacklist
        if access is not None:
            access_whitelist = self.osrm_car_profile.get_access_tag_whitelist()
            access_access_tag = True if access in access_whitelist else False
        else: # if no Access tag then is permited access
            access_access_tag = True

        # check vehicle, motor_vehicle, motorcar tags- following access.feature file from osrm
        vehicles_access_tags_blacklist = ["no"]
        vehicle_access_tag = False if tags_data["vehicle"] in vehicles_access_tags_blacklist else True
        motor_vehicle_access_tag = False if tags_data["motor_vehicle"] in vehicles_access_tags_blacklist else True
        motor_car_access_tag = False if tags_data["motor_car"] in vehicles_access_tags_blacklist else True

        # return circulation combining access values
        if access_access_tag and vehicle_access_tag and motor_vehicle_access_tag and motor_car_access_tag:
            return "yes"
        else:
            return "no"

    def extract_oneway(self):
        # Oneway restriction following oneway.feature file from osrm
        tags_data = self.get_tags_data("oneway")
        if tags_data["junction"] is not None:
            junction_tag = True if tags_data["junction"] in ["roundabout"] else False
        else:
            junction_tag = False
        if tags_data["highway"] is not None:
            highway_tag = True if tags_data["highway"] in ["motorway"] else False
        else:
            highway_tag = False
        if tags_data["oneway"] is not None:
            one_way_tag = True if tags_data["oneway"] in ["yes", "motor_vehicle=yes", "vehicle=yes", "motorcar=yes"] else False
        else:
            one_way_tag = False
        if junction_tag or highway_tag or one_way_tag:
            return "yes"
        else:
            return "no"

    def extract_max_speed(self):
        # Max speed following maxspeed.feature file from osrm and car.lua
        # Speed limits from surface not take into account
        tags_data = self.get_tags_data("speed")
        highway = tags_data["highway"]
        speeds = self.osrm_car_profile.get_speeds()
        maxspeed_in_tag = self.get_tag_maxspeed(tags_data["maxspeed"])
        if maxspeed_in_tag is not None:
            return maxspeed_in_tag
        else:
            return speeds[highway] if highway in speeds.keys() else ""

    def get_tag_maxspeed(self, data):
        """Convert values of maxspeed tag into km/h or None"""
        num_pattern = re.compile(r'^(\d+)\s?$')
        mph_pattern = re.compile(r'^(\d+)\s?mph')
        knots_pattern = re.compile(r'^(\d+)\s?knots')
        walk_pattern = re.compile(r'^walk')

        if data is None:
            return None
        elif num_pattern.match(data):
            return int(num_pattern.match(data).group(1))
        elif mph_pattern.match(data): # convert mph to kmh
            return int(mph_pattern.match(data).group(1)) * 1.60934
        elif knots_pattern.match(data): # convert knots to kmh
            return int(knots_pattern.match(data).group(1)) * 1.852
        elif walk_pattern.match(data): # walk speed = 15km/h
            return 15
        else:
            return None

    def extract_edited(self):
        edited = "yes" if "osrmedited" in self.tags_value.keys() else "no"
        return edited

    def get_table_row(self):
        return [
            f"{self.id}",
            self.name,
            self.extract_access_value(),
            self.extract_oneway(),
            f"{self.extract_max_speed()}",
            self.extract_edited(),
        ]

    def change_access(self, option):
        """Change tags to allow or deny access. Option must be 'restrict_access' or 'allow_access' """
        tags_data = self.get_tags_data("access")
        if option == "restrict_access":
            if self.extract_access_value() == "no":
                return # restrict circulation in a segment already restricted
            elif self.extract_access_value() == "yes":
                self.tags_value["access"] = "no"

        elif option == "allow_access":
            if self.extract_access_value() == "yes":
                return
            elif self.extract_access_value() == "no":
                self.tags_value["access"] = "yes"
                if "vehicle" in tags_data.keys() and tags_data["vehicle"] is not None:
                    del self.tags_value["vehicle"]
                if "motor-vehicle" in tags_data.keys() and tags_data["motor_vehicle"] is not None:
                    del self.tags_value["motor_vehicle"]
                if "motor-car" in tags_data.keys() and tags_data["motor_car"] is not None:
                    del self.tags_value["motor_car"]
        # Update tags values of feature and save previous values
        self.feature[self.tags_field_name] = self.tags_value 
        self.change_edited("edit", tags_data)

    def change_one_way(self, option):
        """Change tags to set one way restriction or allow both ways circulation. Option must be 'oneway' or 'bothways' """
        tags_data = self.get_tags_data("oneway")

        if option == "oneway":
            if self.extract_oneway() == "yes":
                return #oneway in a segment already one way
            elif self.extract_oneway() == "no":
                self.tags_value["oneway"] ="yes"

        elif option == "bothways":
            if self.extract_oneway() == "no":
                return
            elif self.extract_oneway() == "yes":
                # case roundabout only oneway permited
                if "junction" in tags_data.keys() and tags_data["junction"] == "roundabout":
                    self.iface.messageBar().pushMessage(
                        "Warning", f"feature id:{self.id} is a roundabout. Only oneway permitted", Qgis.Warning, 10
                    )
                    return 
                # case motorway, change to primary
                elif "highway" in tags_data.keys() and tags_data["highway"] == "motorway":
                    self.tags_value["highway"] = "primary"
                # case tag oneway -> change tag to no
                if "oneway" in tags_data.keys() and tags_data["oneway"] == "yes":
                    self.tags_value["oneway"] = "no"

        # Update tags values of feature and save previous values
        self.feature[self.tags_field_name] = self.tags_value
        self.change_edited("edit", tags_data)

    def change_speed(self, speed):
        """ Change max speed. If selected speed is higher than speed limit for a way, an alert is shown and no changes apply.
        Speed limits for way extracted from car lua can differ from real speed limits for a way"""
        tags_data = self.get_tags_data("speed")

        # Speed depending on way type
        highway = tags_data["highway"]
        speeds = self.osrm_car_profile.get_speeds()
        highway_speed = speeds[highway] if highway in speeds.keys() else ""

        # Speed depending on maxspeed tag
        maxspeed_in_tag = self.get_tag_maxspeed(tags_data["maxspeed"])
        
        # If selected speed is higher than speed limit for a way, an alert is shown and no changes apply
        if speed > highway_speed:
            self.iface.messageBar().pushMessage(
                        "Warning", f"feature id:{self.id} can't increase the speed to {speed}", Qgis.Warning, 10
                    )
            return 
        else:
            self.tags_value["maxspeed"] = speed

        # Update tags values of feature and save previous values(only for maxspeed)
        tags_data_speed = {key: tags_data[key] for key in tags_data if key == "maxspeed"}
        self.feature[self.tags_field_name] = self.tags_value
        self.change_edited("edit", tags_data_speed)

    def change_direction(self):
        direction = (self.tags_value["direction"] if "direction" in self.tags_value.keys() else None)
        tags_data = {"direction": direction}

        if tags_data["direction"] == "reversed":
            self.tags_value["direction"] = "normal"
        else:
            self.tags_value["direction"] = "reversed"

        # Update tags values of feature and save previous values
        self.feature[self.tags_field_name] = self.tags_value
        self.change_edited("edit", tags_data)

    def osrmedited_to_string(self, data_dict):
        data_string = "|".join([f"{k}=>NULL" if v is None else f"{k}=>{v}" for k, v in data_dict.items()])
        return data_string

    def osrmedited_to_dict(self, data_string):
        edited_data_dict = {}
        for pair in data_string.split('|'):
            key, value = pair.split('=>')
            edited_data_dict[key] = None if value == "NULL" else value
        return edited_data_dict

    def change_edited(self, option, data):
        """Edit or undo edition of segment, option must be 'edit' or 'undo'"""
        # Get previous values of edited data from osrmedited tag
        edited_data = self.tags_value["osrmedited"] if "osrmedited" in self.tags_value.keys() else None
        if edited_data:
            edited_data_dict = self.osrmedited_to_dict(edited_data)
        else:
            edited_data_dict = None

        # When option is edit:
        #   if it has not been edited before -> save previous values to osrmedited and to hstore data
        #   else -> add necessary values
        if option == "edit":
            if edited_data_dict:
                for tag in data.keys():
                    if tag not in edited_data_dict.keys():
                        edited_data_dict[tag] = data[tag]
                self.tags_value["osrmedited"] = self.osrmedited_to_string(edited_data_dict)
            else:
                data_string = self.osrmedited_to_string(data)
                self.tags_value["osrmedited"] = data_string

        # When option is undo:
        # ╠  if it has been edited before -> recover values from osrmedited tag
        #   else -> nothing to do (no edited - no undo)
        elif option == "undo":
            if edited_data_dict:
                for tag in edited_data_dict.keys():
                    if edited_data_dict[tag] is not None:  # Recover in case there was a value before
                        self.tags_value[tag] = edited_data_dict[tag]
                    else:   #delete current tag in case no previous value exist
                        if tag in self.tags_value.keys():
                            del self.tags_value[tag]
                del self.tags_value["osrmedited"]
            else:
                # no previously data edited, nothing to do
                pass

        # Update tags values of feature
        self.feature[self.tags_field_name] = self.tags_value
