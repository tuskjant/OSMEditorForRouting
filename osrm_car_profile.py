import re
import os

class CarProfile:
    lua_file = os.path.join(os.path.dirname(__file__), "car.lua")

    def __init__(self):
        with open(self.lua_file, 'r') as file:
            self.lua_content = file.read()

    def get_access_tag_whitelist(self):
        pattern = r"access_tag_whitelist\s*=\s*Set\s*\{([^}]+)\}"
        access_tag_whitelist = self.get_data_list(pattern)
        return access_tag_whitelist

    def get_access_tag_blacklist(self):
        pattern = r"access_tag_blacklist\s*=\s*Set\s*\{([^}]+)\}"
        access_tag_blacklist = self.get_data_list(pattern)
        return access_tag_blacklist

    def get_speeds(self):
        pattern = r"speeds\s*=\s*Sequence\s*\{\s*highway\s*=\s*\{([^}]+)\}"
        speeds = self.get_data_dict(pattern)
        return speeds

    def get_data_list(self, pattern):
        matches = re.search(pattern, self.lua_content, re.DOTALL)
        if matches:
            whitelist_str = matches.group(1).strip()

            access_tag_whitelist = [
                tag.strip().strip("'") for tag in whitelist_str.split(",")
            ]
            return access_tag_whitelist
        else:
            return []

    def get_data_dict(self, pattern):
        matches = re.search(pattern, self.lua_content, re.DOTALL)
        highway_speeds = {}
        if matches:
            highway_speeds_str = matches.group(1).strip()

            for line in highway_speeds_str.splitlines():
                key_value = re.split(r"\s*=\s*", line.strip())
                if len(key_value) == 2:
                    cleaned_value = re.sub(r"[^\d]", "", key_value[1])
                    highway_speeds[key_value[0]] = int(cleaned_value)

        return highway_speeds
