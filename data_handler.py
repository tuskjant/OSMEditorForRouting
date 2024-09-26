import os
from qgis.core import Qgis
import subprocess
from .database_functions import *

class DataHandler:
    def __init__(self, iface):
        self.iface = iface

    def run_command(self, command):
        """Method to run a subprocess"""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout = stdout.decode('cp1252')
        stderr = stderr.decode('cp1252')
        return stdout, stderr

    def convert_to_pbf(self, dbparameters, pbf_folder, osmosis_folder):
        """Method for exporting from database to pbf files"""
        if not pbf_folder or not osmosis_folder:
            return

        host = dbparameters["host"]
        port = dbparameters["port"]
        user = dbparameters["user"]
        password = dbparameters["password"]
        database = dbparameters["dbname"]
        schema = dbparameters["schema"]

        if (
            database is not None
            and user is not None
            and password is not None
        ):
            try:
                command = f'cd /d "{osmosis_folder}" && osmosis --read-pgsql host={host} database={database} user={user} password={password} postgresSchema={schema} --dataset-dump --write-pbf file={os.path.join(pbf_folder,"output.osm.pbf")}'
                stdout, stderr = self.run_command(command)
                print("Output", stdout)
                print("Errors", stderr)
                self.iface.messageBar().pushMessage(
                    "Info", "Database converted to pbf file", Qgis.Success, 10
                )
            except:
                self.iface.messageBar().pushMessage(
                    "Error",
                    "An error ocurred while converting to pbf",
                    Qgis.Warning,
                    10,
                )
        else:
            self.iface.messageBar().pushMessage(
                "Warning", "Missing database parameters in settings", Qgis.Warning, 10
            )
            return

    def load_pbf(self, dbparameters, pbf_file, osmosis_folder):

        host = dbparameters["host"]
        port = dbparameters["port"]
        user = dbparameters["user"]
        password = dbparameters["password"]
        database = dbparameters["dbname"]
        schema = dbparameters["schema"]

        # Try to create new db using settings
        db_created = create_db(dbparameters)
        if not db_created:
            self.iface.messageBar().pushMessage(
                "Warning", "Can not create the database", Qgis.Warning, 10
            )
            return

        # Connect to database
        connection, cursor = connect_to_database(dbparameters)
        if connection is None or cursor is None:
            self.iface.messageBar().pushMessage(
                "Warning", "Can not connect to the database", Qgis.Warning, 10
            )
            return

        # Create extensions
        extension_created = create_extensions(connection, cursor)
        if not extension_created:
            self.iface.messageBar().pushMessage(
                "Warning", "Can not create extensions", Qgis.Warning, 10
            )
            return

        # Get osmosis script path
        osmosis_bin_folder = osmosis_folder
        if not osmosis_bin_folder:
            return
        osmosis_path = os.path.dirname(osmosis_bin_folder)
        osmosis_script_path = os.path.join(osmosis_path, "script")

        # Create database schema and tables
        schema_script = os.path.join(osmosis_script_path, "pgsnapshot_schema_0.6.sql")
        schema_executed = execute_sql_file(connection, cursor, schema_script)
        if not schema_executed:
            self.iface.messageBar().pushMessage(
                "Warning", "Can not create database schema and tables", Qgis.Warning, 10
            )
            return

        # Add geometry
        bbox_script = os.path.join(
            osmosis_script_path, "pgsnapshot_schema_0.6_bbox.sql"
        )
        line_script = os.path.join(
            osmosis_script_path, "pgsnapshot_schema_0.6_linestring.sql"
        )
        bbox_executed = execute_sql_file(connection, cursor, bbox_script)
        line_executed = execute_sql_file(connection, cursor, line_script)
        if not bbox_executed or not line_executed:
            self.iface.messageBar().pushMessage(
                "Warning", "Can not create geometry in tables", Qgis.Warning, 10
            )
            return

        # Execute osmosis pbf -> pgsql
        try:
            command = f'cd /d "{osmosis_bin_folder}" && osmosis --read-pbf "{pbf_file}" --write-pgsql host={host} database={database} user={user} password={password} postgresSchema={schema}'
            stdout, stderr = self.run_command(command)
            print("Output", stdout)
            print("Errors", stderr)
            self.iface.messageBar().pushMessage(
                "Info", "Pbf file loaded to database", Qgis.Success, 10
            )
        except:
            self.iface.messageBar().pushMessage(
                "Error", "An error ocurred while loading pbf file", Qgis.Warning, 10
            )

    def convert_osm_to_pbf(self, osm_file, pbf_folder, osmosis_folder):
        new_pbf_file_name = os.path.splitext(os.path.basename(osm_file))[0] + ".osm.pbf"
        try:
            command = f'cd /d "{osmosis_folder}" && osmosis --read-xml {osm_file} --write-pbf file={os.path.join(pbf_folder, new_pbf_file_name)}'

            stdout, stderr = self.run_command(command)
            print("Output", stdout)
            print("Errors", stderr)
            self.iface.messageBar().pushMessage(
                "Info", "osm file converted to pbf file", Qgis.Success, 10
            )
        except:
            self.iface.messageBar().pushMessage(
                "Error",
                "An error ocurred while converting to pbf",
                Qgis.Warning,
                10,
            )

    def prepare_osrm_data(self, pbf_file, docker_path, osrm_docker_image):
        name_pbf = os.path.splitext(os.path.basename(pbf_file))[0]
        name2_pbf = os.path.splitext(os.path.basename(name_pbf))[0]  # double extension .osm.pbf
        osrm_data_folder = os.path.dirname(pbf_file)
        try:
            command = (
                f'"{docker_path}" run -t -v "{osrm_data_folder}":/data {osrm_docker_image} osrm-extract -p /opt/car.lua /data/{name_pbf}.pbf && '
                f'"{docker_path}" run -t -v "{osrm_data_folder}":/data {osrm_docker_image} osrm-partition /data/{name2_pbf}.osrm && '
                f'"{docker_path}" run -t -v "{osrm_data_folder}":/data {osrm_docker_image} osrm-customize /data/{name2_pbf}.osrm'
            )
            stdout, stderr = self.run_command(command)
            print("Output", stdout)
            print("Errors", stderr)
            self.iface.messageBar().pushMessage(
                "Info", "Osrm files created", Qgis.Success, 10
            )
        except:
            self.iface.messageBar().pushMessage(
                "Error",
                "An error ocurred while preparing osrm files",
                Qgis.Warning,
                10,
            )

    